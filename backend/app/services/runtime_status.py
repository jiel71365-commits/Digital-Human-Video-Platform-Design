import subprocess
import sys
from pathlib import Path

from app.config import PROJECT_ROOT, Settings
from app.schemas import Wav2LipRuntimeStatus

WAV2LIP_SETUP_COMMAND = "python scripts/setup_wav2lip.py"
MUSETALK_SETUP_COMMAND = "python scripts/setup_musetalk.py"
MUSETALK_REQUIRED_MODULES = ["accelerate", "diffusers", "einops", "mmcv", "mmdet", "mmpose"]


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
        setup_command=WAV2LIP_SETUP_COMMAND,
    )


def get_musetalk_runtime_status(settings: Settings) -> Wav2LipRuntimeStatus:
    inference_path = settings.musetalk_root / "scripts" / "inference.py"
    requirements = [
        (inference_path, _display_path(inference_path)),
        (
            settings.musetalk_model_root / "musetalkV15" / "unet.pth",
            _display_path(settings.musetalk_model_root / "musetalkV15" / "unet.pth"),
        ),
        (
            settings.musetalk_model_root / "musetalkV15" / "musetalk.json",
            _display_path(settings.musetalk_model_root / "musetalkV15" / "musetalk.json"),
        ),
        (
            settings.musetalk_model_root / "sd-vae" / "config.json",
            _display_path(settings.musetalk_model_root / "sd-vae" / "config.json"),
        ),
        (
            settings.musetalk_model_root / "whisper" / "config.json",
            _display_path(settings.musetalk_model_root / "whisper" / "config.json"),
        ),
        (
            settings.musetalk_model_root / "dwpose" / "dw-ll_ucoco_384.pth",
            _display_path(settings.musetalk_model_root / "dwpose" / "dw-ll_ucoco_384.pth"),
        ),
        (
            settings.musetalk_model_root / "face-parse-bisent" / "79999_iter.pth",
            _display_path(
                settings.musetalk_model_root / "face-parse-bisent" / "79999_iter.pth"
            ),
        ),
        (
            settings.musetalk_model_root / "syncnet" / "latentsync_syncnet.pt",
            _display_path(settings.musetalk_model_root / "syncnet" / "latentsync_syncnet.pt"),
        ),
    ]
    missing = [label for path, label in requirements if not path.exists()]
    if not settings.enable_musetalk:
        missing.insert(0, "MuseTalk disabled by settings")
    python_path = settings.musetalk_python_path or Path(sys.executable)
    if not python_path.exists():
        missing.append(_display_path(python_path))
    else:
        missing_modules = _missing_python_modules(python_path, MUSETALK_REQUIRED_MODULES)
        if missing_modules:
            missing.append(f"MuseTalk python missing modules: {', '.join(missing_modules)}")
    available = settings.enable_musetalk and not missing
    return Wav2LipRuntimeStatus(
        enabled=settings.enable_musetalk,
        available=available,
        active_renderer="musetalk" if available else "fallback",
        missing_requirements=missing,
        model_paths={
            "root": str(settings.musetalk_root),
            "inference": str(inference_path),
            "model_root": str(settings.musetalk_model_root),
            "unet": str(settings.musetalk_model_root / "musetalkV15" / "unet.pth"),
            "config": str(settings.musetalk_model_root / "musetalkV15" / "musetalk.json"),
        },
        setup_command=MUSETALK_SETUP_COMMAND,
    )


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        parts = path.parts
        if "models" in parts:
            return Path(*parts[parts.index("models") :]).as_posix()
        return path.name


def _missing_python_modules(python_path: Path, modules: list[str]) -> list[str]:
    script = (
        "import importlib.util, sys; "
        f"missing=[m for m in {modules!r} if importlib.util.find_spec(m) is None]; "
        "print('\\n'.join(missing)); "
        "sys.exit(1 if missing else 0)"
    )
    completed = subprocess.run(
        [str(python_path), "-c", script],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if completed.returncode == 0:
        return []
    missing = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if missing:
        return missing
    return [f"dependency check failed: {(completed.stderr or 'unknown error').strip()}"]
