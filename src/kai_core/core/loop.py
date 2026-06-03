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
            time.sleep(self.tick_interval)
            loop_start = time.time()

            # 1. Extract Media Chunks from Buffers
            audio_data = self.audio_buffer.get_and_clear_chunk()
            video_filepath = self.video_buffer.get_and_clear_chunk()

            audio_uri = encode_audio_bytes(
                audio_data, self.audio_buffer.rate, self.audio_buffer.channels
            )
            video_uri = encode_video_file(video_filepath)

            # 2. Step 1: Decode Multimodal Modalities
            transcript = ""
            vision = ""
            if audio_uri or video_uri:
                logging.info("Executing Step 1: Decoding input buffers...")
                decode_res = self.agent.decode_inputs(audio_uri, video_uri)
                if decode_res:
                    transcript = decode_res.transcript
                    vision = decode_res.vision

                    logging.info(
                        f"\n--- [State: Decoding] ---\n"
                        f"Transcript : {transcript}\n"
                        f"Vision     : {vision}\n"
                        f"-------------------------"
                    )

            if transcript.strip():
                self.context_manager.append_user_transcript(transcript)

            # 3. Step 2: Update Application Scene Description History
            current_context = self.context_manager.get_formatted_context()
            logging.info("Executing Step 2: Running context update compilation...")
            context_res = self.agent.update_context(current_context, transcript, vision)

            if context_res:
                self.context_manager.set_scene_description(
                    context_res.new_scene_description
                )

                logging.info(
                    f"\n--- [State: Context] ---\n"
                    f"Scene          : {context_res.new_scene_description}\n"
                    f"Should Answer  : {context_res.should_answer}\n"
                    f"Dialogue       :\n{self.context_manager.get_dialogue_string()}\n"
                    f"------------------------"
                )

                # 4. Step 3: Conditional Evaluation Loop for Agent Responses
                if context_res.should_answer:
                    logging.info(
                        "Executing Step 3: Assertion positive. Generating conversational block..."
                    )

                    scene_desc = self.context_manager.scene_description
                    dialogue = self.context_manager.get_dialogue_string()

                    answer_res = self.agent.generate_answer(scene_desc, dialogue)

                    if answer_res and answer_res.answer:
                        print(f"\n[AI Agent]: {answer_res.answer}\n")
                        self.context_manager.append_ai_response(answer_res.answer)

            elapsed = time.time() - loop_start
            logging.debug(
                f"Tick pipeline execution completed in {elapsed:.4f} seconds."
            )
