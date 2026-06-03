from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings


class SystemConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    tick_interval: float = 3.0


class LLMConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    base_url: str = "http://localhost:30000/v1"
    api_key: str = "EMPTY"
    model_id: str = "google/gemma-4-E4B-it"


class AudioConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024


class VideoConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    camera_index: int = 0
    fps: int = 10


class MemoryConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    max_history_length: int = 20


class GlobalConfig(BaseSettings):
    model_config = ConfigDict(frozen=True)
    system: SystemConfig = SystemConfig()
    llm: LLMConfig = LLMConfig()
    audio: AudioConfig = AudioConfig()
    video: VideoConfig = VideoConfig()
    memory: MemoryConfig = MemoryConfig()


settings = GlobalConfig()
