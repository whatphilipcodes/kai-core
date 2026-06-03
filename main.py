import logging
from src.kai_core.config import settings
from src.kai_core.core.loop import MainLoop
from src.kai_core.input.audio_buffer import AudioBuffer
from src.kai_core.input.video_buffer import VideoBuffer
from src.kai_core.memory.context import ContextManager
from src.kai_core.agent.llm_client import LLMAgent

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


def main() -> None:
    logging.info("Initializing Kai Core System...")

    audio_buffer = AudioBuffer(
        rate=settings.audio.rate,
        channels=settings.audio.channels,
        chunk_size=settings.audio.chunk_size,
    )
    video_buffer = VideoBuffer(
        camera_index=settings.video.camera_index, fps=settings.video.fps
    )

    context_manager = ContextManager(
        max_history_length=settings.memory.max_history_length
    )
    llm_agent = LLMAgent(
        base_url=settings.llm.base_url,
        api_key=settings.llm.api_key,
        model_id=settings.llm.model_id,
    )

    loop = MainLoop(
        tick_interval=settings.system.tick_interval,
        audio_buffer=audio_buffer,
        video_buffer=video_buffer,
        context_manager=context_manager,
        agent=llm_agent,
    )

    try:
        audio_buffer.start()
        video_buffer.start()
        loop.run()
    except KeyboardInterrupt:
        logging.info("Shutdown initiated via console.")
    finally:
        audio_buffer.stop()
        video_buffer.stop()


if __name__ == "__main__":
    main()
