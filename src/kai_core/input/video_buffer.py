import cv2
import threading
import os
import time
import logging


class VideoBuffer:
    def __init__(self, camera_index: int, fps: int):
        self.camera_index = camera_index
        self.fps = fps
        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_AVFOUNDATION)

        if not self.cap.isOpened():
            logging.error(f"Could not open webcam {camera_index}")

        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.lock = threading.Lock()
        self.is_recording = False
        self.thread = None
        self.tmp_dir = os.path.join(os.getcwd(), "tmp")
        os.makedirs(self.tmp_dir, exist_ok=True)

        # Use H.264 which is required by vLLM's decoder
        self.fourcc = cv2.VideoWriter.fourcc(*"avc1")
        self.current_path = self._get_new_path()
        self.out = cv2.VideoWriter(
            self.current_path, self.fourcc, self.fps, (self.width, self.height)
        )

    def _get_new_path(self):
        return os.path.join(self.tmp_dir, f"chunk_{int(time.time() * 1000)}.mp4")

    def start(self):
        self.is_recording = True
        self.thread = threading.Thread(target=self._record_loop, daemon=True)
        self.thread.start()
        logging.info("Video buffer started.")

    def _record_loop(self):
        frame_time = 1.0 / self.fps
        while self.is_recording:
            loop_start = time.time()
            ret, frame = self.cap.read()

            if ret and frame is not None:
                with self.lock:
                    if self.out and self.out.isOpened():
                        self.out.write(frame)

            time_to_sleep = frame_time - (time.time() - loop_start)
            if time_to_sleep > 0:
                time.sleep(time_to_sleep)

    def get_and_clear_chunk(self) -> str:
        with self.lock:
            old_out = self.out
            chunk_path = self.current_path

            self.current_path = self._get_new_path()
            self.out = cv2.VideoWriter(
                self.current_path, self.fourcc, self.fps, (self.width, self.height)
            )

        # Offload the blocking release operation to avoid AVFoundation main-thread warnings
        if old_out:
            release_thread = threading.Thread(target=old_out.release)
            release_thread.start()
            release_thread.join()

        if not os.path.exists(chunk_path) or os.path.getsize(chunk_path) == 0:
            return ""

        return chunk_path

    def stop(self):
        self.is_recording = False
        if self.thread:
            self.thread.join()

        with self.lock:
            old_out = self.out
            self.out = None

        if old_out:
            release_thread = threading.Thread(target=old_out.release)
            release_thread.start()
            release_thread.join()

        self.cap.release()
