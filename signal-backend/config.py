from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    elevenlabs_api_key: str = ""
    firecrawl_api_key: str = ""
    # When set, /api and /data require this token (Bearer header or ?token=).
    # Leave empty for local development.
    signal_api_token: str = ""
    claude_model: str = "claude-opus-4-8"
    elevenlabs_model: str = "eleven_multilingual_v2"
    storage_path: str = "./data"

    # Repo-root .env is read first so secrets can live in one place;
    # a local signal-backend/.env overrides it.
    model_config = {"env_file": ("../.env", ".env"), "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
