from pathlib import Path

from app.config import PROJECT_ROOT, Settings
from app.schemas import Wav2LipRuntimeStatus

SETUP_COMMAND = "python scripts/setup_wav2lip.py"


def get_wav2lip_runtime_status(settings: Settings) -> Wav2LipRuntimeStatus:
    inference_path = settings.wav2lip_root / "inference.py"
    requirements = [
        (inference_path, _display_path(inference_path)),
        (settings.wav2lip_checkpoint_path, _display_path(settings.wav2lip_checkpoint_path)),
        (settings.wav2lip_face_detector_path, _display_path(settings.wav2lip_face_detector_path)),
        (settings.wav2lip_default_face_path, _display_path(settings.wav2lip_default_face_path)),
    ]
    missing = [label for path, label in requirements if not path.exists()]
    if not settings.enable_wav2lip:
        missing.insert(0, "Wav2Lip disabled by settings")
    available = settings.enable_wav2lip and not missing
    return Wav2LipRuntimeStatus(
        enabled=settings.enable_wav2lip,
        available=available,
        active_renderer="wav2lip" if available else "fallback",
        missing_requirements=missing,
        model_paths={
            "root": str(settings.wav2lip_root),
            "inference": str(inference_path),
            "checkpoint": str(settings.wav2lip_checkpoint_path),
            "face_detector": str(settings.wav2lip_face_detector_path),
            "default_face": str(settings.wav2lip_default_face_path),
        },
        setup_command=SETUP_COMMAND,
    )


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        parts = path.parts
        if "models" in parts:
            return Path(*parts[parts.index("models") :]).as_posix()
        return path.name
