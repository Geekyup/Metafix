from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    bot_token: str
    redis_url: str = "redis://localhost:6379/0"
    temp_dir: Path = Path("/tmp/tgmeta")
    max_file_size: int = 20 * 1024 * 1024
    proxy: str | None = None
    session_ttl: int = 3600


settings = Settings()