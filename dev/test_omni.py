import base64
import requests
import json
import sys
import subprocess
import os


def separate_streams(input_path: str, video_out: str, audio_out: str) -> None:
    """Uses FFmpeg to extract a silent video stream and a WAV audio stream."""
    if not os.path.exists(input_path):
        print(f"Error: Could not find file at {input_path}")
        sys.exit(1)

    audio_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        audio_out,
    ]

    video_cmd = ["ffmpeg", "-y", "-i", input_path, "-c", "copy", "-an", video_out]

    try:
        # Execute FFmpeg commands, suppressing standard output
        subprocess.run(
            audio_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        subprocess.run(
            video_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        print(
            "Error: FFmpeg execution failed. Ensure it is installed and added to PATH."
        )
        sys.exit(1)
    except FileNotFoundError:
        print("Error: FFmpeg not found. Please install FFmpeg.")
        sys.exit(1)


def encode_file_to_base64(file_path: str, mime_type: str) -> str:
    """Reads a file and returns a base64 data URI."""
    try:
        with open(file_path, "rb") as f:
            encoded_string = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime_type};base64,{encoded_string}"
    except FileNotFoundError:
        print(f"Error: Could not find file at {file_path}")
        sys.exit(1)


def main():
    # Configuration
    model_id = "google/gemma-4-E4B-it"
    input_video_path = "assets/vid/03.mp4"
    endpoint_url = "http://localhost:30000/v1/chat/completions"

    # Temporary file paths
    temp_video_path = "tmp/silent_video.mp4"
    temp_audio_path = "tmp/extracted_audio.wav"

    # 1. Separate the media streams
    separate_streams(input_video_path, temp_video_path, temp_audio_path)

    # 2. Encode streams to base64 URIs
    video_uri = encode_file_to_base64(temp_video_path, "video/mp4")
    audio_uri = encode_file_to_base64(temp_audio_path, "audio/wav")

    # 3. Construct the multi-modal payload
    payload = {
        "model": model_id,
        "messages": [
            {
                "role": "system",
                "content": "Du bist Schauspielperson in einer Theater-Produktion.",
            },
            {
                "role": "user",
                "content": [
                    {"type": "video_url", "video_url": {"url": video_uri}},
                    {"type": "audio_url", "audio_url": {"url": audio_uri}},
                    {
                        "type": "text",
                        "text": "1) Fasse die im Video sichtbare Situation kurz zusammen. 2) Transkribiere das Gesagte im Audio jeweils der betreffenden Person zugeordnet.",
                    },
                ],
            },
        ],
        "max_tokens": 512,
        "temperature": 0.7,
    }

    headers = {
        "Content-Type": "application/json",
    }

    # 4. Request the generation from the Chat Completions endpoint
    response = requests.post(endpoint_url, headers=headers, json=payload)

    # 5. Output handling
    if response.status_code == 200:
        response_data = response.json()
        try:
            content = response_data["choices"][0]["message"]["content"]
            print("\n--- Model Response ---\n")
            print(content)
        except KeyError:
            print("Error parsing expected JSON structure. Raw response:")
            print(json.dumps(response_data, indent=2))
    else:
        print(f"Request failed with status {response.status_code}: {response.text}")

    # 6. Cleanup temporary files
    # for tmp_file in [temp_video_path, temp_audio_path]:
    #     if os.path.exists(tmp_file):
    #         os.remove(tmp_file)


if __name__ == "__main__":
    main()
