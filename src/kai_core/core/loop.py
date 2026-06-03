import time
import logging
from src.kai_core.input.audio_buffer import AudioBuffer
from src.kai_core.input.video_buffer import VideoBuffer
from src.kai_core.memory.context import ContextManager
from src.kai_core.agent.llm_client import LLMAgent
from src.kai_core.utils.media import encode_audio_bytes, encode_video_file


class MainLoop:
    def __init__(
        self,
        tick_interval: float,
        audio_buffer: AudioBuffer,
        video_buffer: VideoBuffer,
        context_manager: ContextManager,
        agent: LLMAgent,
    ):
        self.tick_interval = tick_interval
        self.audio_buffer = audio_buffer
        self.video_buffer = video_buffer
        self.context_manager = context_manager
        self.agent = agent

    def run(self):
        logging.info(
            f"Starting main execution loop. Tick interval: {self.tick_interval}s"
        )

        while True:
            # Wait for buffers to accumulate data before processing
            time.sleep(self.tick_interval)

            # loop_start = time.time()

            # 1. Extract Media
            audio_data = self.audio_buffer.get_and_clear_chunk()
            video_filepath = self.video_buffer.get_and_clear_chunk()

            audio_uri = encode_audio_bytes(
                audio_data, self.audio_buffer.rate, self.audio_buffer.channels
            )
            video_uri = encode_video_file(video_filepath)

            # 2. Retrieve Context
            current_context = self.context_manager.get_formatted_context()

            # 3. Query LLM
            logging.info("Querying LLM with current context and multimodal chunks...")
            response = self.agent.query(current_context, audio_uri, video_uri)

            if response:
                # 4. Update Context & Output
                self.context_manager.update(
                    response.transcript_append, response.visual_update
                )

                print(f"\n[context]: {self.context_manager.get_formatted_context()}\n")

                if response.should_answer and response.answer_text:
                    print(f"\n[k.ai]: {response.answer_text}\n")
                    self.context_manager.append_ai_response(response.answer_text)
