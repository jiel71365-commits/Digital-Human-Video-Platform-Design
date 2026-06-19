from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./digital_human.db"
    storage_root: Path = Path("storage")
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(env_prefix="DHVP_", env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()
