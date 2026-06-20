from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    database_url: str = "sqlite:///./digital_human.db"
    storage_root: Path = Path("storage")
    cors_origins: list[str] = ["http://localhost:5173"]
    enable_wav2lip: bool = True
    wav2lip_root: Path = PROJECT_ROOT / "models" / "Wav2Lip"
    wav2lip_checkpoint_path: Path = (
        PROJECT_ROOT / "models" / "Wav2Lip" / "checkpoints" / "wav2lip_gan.pth"
    )
    wav2lip_face_detector_path: Path = Path(
        PROJECT_ROOT
        / "models"
        / "Wav2Lip"
        / "face_detection"
        / "detection"
        / "sfd"
        / "s3fd.pth"
    )
    wav2lip_default_face_path: Path = PROJECT_ROOT / "models" / "default-presenter.mp4"
    wav2lip_python_path: Path | None = None
    wav2lip_timeout_seconds: int = 1800

    model_config = SettingsConfigDict(env_prefix="DHVP_", env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()
