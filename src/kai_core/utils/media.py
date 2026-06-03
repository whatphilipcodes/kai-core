import base64
import wave
import io
import os


def encode_audio_bytes(audio_bytes: bytes, rate: int, channels: int) -> str:
    if not audio_bytes:
        return ""

    wav_io = io.BytesIO()
    with wave.open(wav_io, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(rate)
        wav_file.writeframes(audio_bytes)

    encoded = base64.b64encode(wav_io.getvalue()).decode("utf-8")
    return f"data:audio/wav;base64,{encoded}"


def encode_video_file(filepath: str) -> str:
    if not filepath or not os.path.exists(filepath):
        return ""

    with open(filepath, "rb") as video_file:
        encoded = base64.b64encode(video_file.read()).decode("utf-8")

    os.remove(filepath)  # Clean up temp file immediately after encoding
    return f"data:video/mp4;base64,{encoded}"
