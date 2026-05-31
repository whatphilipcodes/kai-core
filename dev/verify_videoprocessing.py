import base64
import requests
import json
import sys


def encode_video_to_base64(video_path: str) -> str:
    """Reads a video file and returns a base64 data URI."""
    try:
        with open(video_path, "rb") as video_file:
            encoded_string = base64.b64encode(video_file.read()).decode("utf-8")
        # Ensure the mime type matches your video file format
        return f"data:video/mp4;base64,{encoded_string}"
    except FileNotFoundError:
        print(f"Error: Could not find file at {video_path}")
        sys.exit(1)


def main():
    # Configuration
    model_id = "google/gemma-4-E4B-it"
    video_path = "assets/vid/01_no_audio.mp4"
    endpoint_url = "http://localhost:30000/v1/chat/completions/render"

    # 1. Encode the video
    video_uri = encode_video_to_base64(video_path)

    # 2. Construct the standard payload
    payload = {
        "model": model_id,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "video_url", "video_url": {"url": video_uri}},
                    {
                        "type": "text",
                        "text": "Summarize what happens in this video.",
                    },
                ],
            }
        ],
    }

    headers = {
        "Content-Type": "application/json",
        # "Authorization": "Bearer YOUR_API_KEY" # Uncomment if your vLLM instance requires auth
    }

    # 3. Request the rendered output
    response = requests.post(endpoint_url, headers=headers, json=payload)

    # 4. Print the exact preprocessed payload sent to the model
    if response.status_code == 200:
        rendered_data = response.json()
        with open("tmp/response_log.txt", "a") as f:
            f.write(json.dumps(rendered_data, indent=2))
    else:
        print(f"Request failed with status {response.status_code}: {response.text}")


if __name__ == "__main__":
    main()
