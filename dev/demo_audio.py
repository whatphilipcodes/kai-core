import pyaudio
import numpy as np
import base64
import io
import wave
import json
import re
from openai import OpenAI
from pydantic import BaseModel
from collections import deque

# ==========================================
# Configuration
# ==========================================
FS = 16000
CHANNELS = 1
CHUNK_SIZE = 1024
E_THRESH = 0.02
T_SILENCE = 1.5
T_MAX = 30.0
T_PRE_RECORD = 0.5  # Seconds of audio to keep before VAD triggers

REQUIRED_SILENCE_CHUNKS = int((FS / CHUNK_SIZE) * T_SILENCE)
MAX_CHUNKS = int((FS / CHUNK_SIZE) * T_MAX)
PRE_RECORD_CHUNKS = int((FS / CHUNK_SIZE) * T_PRE_RECORD)

MODEL_ID = "google/gemma-4-12B-it-qat-w4a16-ct"
client = OpenAI(base_url="http://localhost:30000/v1", api_key="EMPTY")

# Persistent Conversation History
conversation_history = []


# ==========================================
# Structured Output Schema
# ==========================================
class AgentResponse(BaseModel):
    transcript: str
    answer: str
    user_emotion: str  # Renamed to strictly bind to the user's input


def calculate_rms(data: bytes) -> float:
    audio_data = np.frombuffer(data, dtype=np.float32)
    return float(np.sqrt(np.mean(audio_data**2)))


def process_and_send(frames: list):
    global conversation_history
    print("\n[System] Packaging audio and querying Gemma 4...")

    # Encode Audio
    raw_data = b"".join(frames)
    audio_np = np.frombuffer(raw_data, dtype=np.float32)
    audio_np = np.clip(audio_np, -1.0, 1.0)
    audio_int16 = (audio_np * 32767).astype(np.int16)

    wav_io = io.BytesIO()
    with wave.open(wav_io, "wb") as wav_file:
        wav_file.setnchannels(CHANNELS)
        wav_file.setsampwidth(2)
        wav_file.setframerate(FS)
        wav_file.writeframes(audio_int16.tobytes())

    base64_audio = base64.b64encode(wav_io.getvalue()).decode("utf-8")
    audio_uri = f"data:audio/wav;base64,{base64_audio}"

    # Explicitly instruct the model to analyze the INPUT audio for the user's emotion
    system_message = {
        "role": "system",
        "content": (
            "Du bist eine Schauspielperson. Reagiere auf die Nuancen im Audio. "
            "Du MUSST zwingend im JSON-Format antworten. "
            "Analysiere die Tonalität der EINGEHENDEN Stimme des Users und klassifiziere SEINE/IHRE Emotion in exakt einem Wort (z.B. wütend, fröhlich, gestresst). "
            'Nutze exakt diese Struktur: {"transcript": "<was der user gesagt hat>", "answer": "<deine antwort in direkter Rede>", "user_emotion": "<emotion_des_users>"}'
        ),
    }

    messages = [system_message] + conversation_history
    messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Höre genau hin und antworte im geforderten JSON-Format:",
                },
                {"type": "audio_url", "audio_url": {"url": audio_uri}},
            ],
        }
    )

    full_response_text = ""
    print("\n--- Model JSON Stream ---")

    try:
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=messages,
            stream=True,
            temperature=0.4,
            max_tokens=512,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "agent_response",
                    "schema": AgentResponse.model_json_schema(),
                },
            },
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response_text += content
                print(content, end="", flush=True)

        print("\n---------------------------")
        parse_and_update_history(full_response_text)

    except Exception as e:
        print(f"\n[Error]: {e}")


def parse_and_update_history(raw_text: str):
    """Safely parses the JSON output to update history with text-only states."""
    global conversation_history

    try:
        clean_text = raw_text.strip()
        clean_text = re.sub(r"^```(?:json)?\s*", "", clean_text, flags=re.IGNORECASE)
        clean_text = re.sub(r"\s*```$", "", clean_text)

        data = json.loads(clean_text)

        transcript = data.get("transcript", "")
        answer = data.get("answer", "")
        emotion = data.get("user_emotion", "")

        # Append pure text to history for context preservation, embedding the emotion
        if transcript:
            user_content = f"[{emotion}] {transcript}" if emotion else transcript
            conversation_history.append({"role": "user", "content": user_content})
        if answer:
            conversation_history.append({"role": "assistant", "content": answer})

        # Enforce history limit
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]

    except json.JSONDecodeError:
        print("\n[Warning]: Model failed to output valid JSON. History update skipped.")
        print(f"Failed Payload: {raw_text}")


def main_loop():
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paFloat32,
        channels=CHANNELS,
        rate=FS,
        input=True,
        frames_per_buffer=CHUNK_SIZE,
    )

    print(f"Hybrid JSON Multiturn System Active. Listening... (Threshold: {E_THRESH})")

    is_recording = False
    audio_frames = []
    silence_chunks = 0

    # Ring buffer for pre-recording audio chunks
    ring_buffer = deque(maxlen=PRE_RECORD_CHUNKS)

    try:
        while True:
            data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            rms = calculate_rms(data)

            if not is_recording:
                # Constantly update the ring buffer with background audio
                ring_buffer.append(data)

                if rms > E_THRESH:
                    is_recording = True
                    # Initialize recording frames with the pre-record buffer
                    audio_frames = list(ring_buffer)
                    silence_chunks = 0
                    ring_buffer.clear()
            else:
                audio_frames.append(data)
                if rms < E_THRESH:
                    silence_chunks += 1
                else:
                    silence_chunks = 0

                if (
                    silence_chunks >= REQUIRED_SILENCE_CHUNKS
                    or len(audio_frames) >= MAX_CHUNKS
                ):
                    stream.stop_stream()
                    process_and_send(audio_frames)

                    # Reset state
                    is_recording = False
                    audio_frames = []
                    silence_chunks = 0
                    ring_buffer.clear()

                    stream.start_stream()
                    print(f"\nListening... (Threshold: {E_THRESH})")

    except KeyboardInterrupt:
        print("\nShutdown initiated.")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()


if __name__ == "__main__":
    main_loop()
