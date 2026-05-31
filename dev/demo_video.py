import cv2
import time
import base64
import threading
import os
from openai import OpenAI

# ==========================================
# Configuration
# ==========================================
API_BASE_URL = "http://localhost:30000/v1"
MODEL_ID = "google/gemma-4-E2B-it"
VIDEO_DURATION = 30.0
FPS = 15
CAMERA_INDEX = 0

client = OpenAI(base_url=API_BASE_URL, api_key="EMPTY")

TMP_DIR = os.path.join(os.getcwd(), "tmp")
os.makedirs(TMP_DIR, exist_ok=True)


def process_and_send_video(video_path: str):
    print(
        f"\n[System] Packaging video {os.path.basename(video_path)} and querying Gemma..."
    )

    if not os.path.exists(video_path):
        print(f"[Error] File not found: {video_path}")
        return

    try:
        with open(video_path, "rb") as video_file:
            encoded_string = base64.b64encode(video_file.read()).decode("utf-8")

        video_uri = f"data:video/mp4;base64,{encoded_string}"

        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
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
            max_tokens=1024,
            temperature=0.4,
        )
        print("\n--- Model Response ---")
        print(response.choices[0].message.content)
        print("----------------------\n")
    except Exception as e:
        print(f"\n[Error] Failed to process video: {e}")
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)
            print(f"[System] Deleted temporary file: {os.path.basename(video_path)}")


def main():
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_AVFOUNDATION)

    if not cap.isOpened():
        print(f"[Error] Could not open webcam at index {CAMERA_INDEX}.")
        return

    ret, test_frame = cap.read()
    if not ret or test_frame is None:
        print("[Error] Webcam opened, but failed to capture a test frame.")
        cap.release()
        return

    # Extract dimensions and strictly cast to int
    actual_height, actual_width = test_frame.shape[:2]
    actual_height = int(actual_height)
    actual_width = int(actual_width)
    print(
        f"[System] Camera initialized. Actual resolution: {actual_width}x{actual_height}"
    )

    # Switch to avc1 (H.264) codec for macOS compatibility
    fourcc = cv2.VideoWriter.fourcc(*"avc1")

    def get_new_video_path():
        return os.path.join(TMP_DIR, f"capture_{int(time.time())}.mp4")

    current_video_path = get_new_video_path()

    out = cv2.VideoWriter(
        current_video_path, fourcc, FPS, (actual_width, actual_height)
    )

    if not out.isOpened():
        print("[Error] VideoWriter failed to initialize with 'avc1'.")
        cap.release()
        return

    print(f"[System] Starting webcam stream. Saving temp files to: {TMP_DIR}")
    print("[System] Press 'q' in the video window to quit.")

    start_time = time.time()
    frame_time = 1.0 / FPS

    try:
        while True:
            loop_start = time.time()

            ret, frame = cap.read()
            if not ret or frame is None:
                print("[Error] Stream interrupted.")
                break

            cv2.imshow("Webcam Stream - Press 'q' to quit", frame)
            out.write(frame)

            elapsed_time = time.time() - start_time
            if elapsed_time >= VIDEO_DURATION:
                out.release()

                if (
                    os.path.exists(current_video_path)
                    and os.path.getsize(current_video_path) > 0
                ):
                    threading.Thread(
                        target=process_and_send_video, args=(current_video_path,)
                    ).start()
                else:
                    print(
                        f"[Error] Video file {current_video_path} is empty or missing."
                    )

                start_time = time.time()
                current_video_path = get_new_video_path()
                out = cv2.VideoWriter(
                    current_video_path, fourcc, FPS, (actual_width, actual_height)
                )

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            time_to_sleep = frame_time - (time.time() - loop_start)
            if time_to_sleep > 0:
                time.sleep(time_to_sleep)

    except KeyboardInterrupt:
        print("\n[System] Shutdown initiated via console.")
    finally:
        out.release()
        cap.release()
        cv2.destroyAllWindows()
        if os.path.exists(current_video_path):
            os.remove(current_video_path)
            print(
                f"[System] Cleaned up unused file: {os.path.basename(current_video_path)}"
            )


if __name__ == "__main__":
    main()
