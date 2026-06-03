import pyaudio
import threading
import logging


class AudioBuffer:
    def __init__(self, rate: int, channels: int, chunk_size: int):
        self.rate = rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.format = pyaudio.paInt16

        self.pyaudio_instance = pyaudio.PyAudio()
        self.stream = None

        self.buffer = []
        self.lock = threading.Lock()
        self.is_recording = False
        self.thread = None

    def start(self):
        self.stream = self.pyaudio_instance.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk_size,
        )
        self.is_recording = True
        self.thread = threading.Thread(target=self._record_loop, daemon=True)
        self.thread.start()
        logging.info("Audio buffer started.")

    def _record_loop(self):
        if self.stream is None:
            return

        while self.is_recording:
            try:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                with self.lock:
                    self.buffer.append(data)
            except Exception as e:
                logging.error(f"Audio read error: {e}")

    def get_and_clear_chunk(self) -> bytes:
        with self.lock:
            data = b"".join(self.buffer)
            self.buffer.clear()
        return data

    def stop(self):
        self.is_recording = False
        if self.thread:
            self.thread.join()
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.pyaudio_instance.terminate()
