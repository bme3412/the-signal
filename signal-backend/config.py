from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    elevenlabs_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"
    elevenlabs_model: str = "eleven_multilingual_v2"
    storage_path: str = "./data"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
