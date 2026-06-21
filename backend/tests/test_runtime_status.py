from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.services.runtime_status import get_musetalk_runtime_status, get_wav2lip_runtime_status


def test_wav2lip_runtime_status_reports_missing_requirements(tmp_path: Path) -> None:
    settings = Settings(
        enable_wav2lip=True,
        wav2lip_root=tmp_path / "models" / "Wav2Lip",
        wav2lip_checkpoint_path=tmp_path / "models" / "Wav2Lip" / "checkpoints" / "wav2lip_gan.pth",
        wav2lip_face_detector_path=tmp_path
        / "models"
        / "Wav2Lip"
        / "face_detection"
        / "detection"
        / "sfd"
        / "s3fd.pth",
        wav2lip_default_face_path=tmp_path / "models" / "default-presenter.mp4",
    )

    status = get_wav2lip_runtime_status(settings)

    assert status.enabled is True
    assert status.available is False
    assert status.active_renderer == "fallback"
    assert status.missing_requirements == [
        "models/Wav2Lip/inference.py",
        "models/Wav2Lip/checkpoints/wav2lip_gan.pth",
        "models/Wav2Lip/face_detection/detection/sfd/s3fd.pth",
        "models/default-presenter.mp4",
    ]
    assert status.model_paths["checkpoint"].endswith("wav2lip_gan.pth")
    assert status.setup_command == "python scripts/setup_wav2lip.py"


def test_wav2lip_runtime_status_reports_available_runtime(tmp_path: Path) -> None:
    wav2lip_root = tmp_path / "models" / "Wav2Lip"
    settings = Settings(
        enable_wav2lip=True,
        wav2lip_root=wav2lip_root,
        wav2lip_checkpoint_path=wav2lip_root / "checkpoints" / "wav2lip_gan.pth",
        wav2lip_face_detector_path=wav2lip_root
        / "face_detection"
        / "detection"
        / "sfd"
        / "s3fd.pth",
        wav2lip_default_face_path=tmp_path / "models" / "default-presenter.mp4",
    )
    for path in [
        wav2lip_root / "inference.py",
        settings.wav2lip_checkpoint_path,
        settings.wav2lip_face_detector_path,
        settings.wav2lip_default_face_path,
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"placeholder")

    status = get_wav2lip_runtime_status(settings)

    assert status.enabled is True
    assert status.available is True
    assert status.active_renderer == "wav2lip"
    assert status.missing_requirements == []


def test_runtime_wav2lip_endpoint_returns_status(
    client: TestClient,
    tmp_path: Path,
    monkeypatch,
) -> None:
    settings = Settings(
        enable_wav2lip=False,
        wav2lip_root=tmp_path / "models" / "Wav2Lip",
        wav2lip_checkpoint_path=tmp_path / "models" / "Wav2Lip" / "checkpoints" / "wav2lip_gan.pth",
        wav2lip_face_detector_path=tmp_path
        / "models"
        / "Wav2Lip"
        / "face_detection"
        / "detection"
        / "sfd"
        / "s3fd.pth",
        wav2lip_default_face_path=tmp_path / "models" / "default-presenter.mp4",
    )
    monkeypatch.setattr("app.api.routes.get_settings", lambda: settings)

    response = client.get("/api/runtime/wav2lip")

    assert response.status_code == 200
    assert response.json() == {
        "enabled": False,
        "available": False,
        "active_renderer": "fallback",
        "missing_requirements": [
            "Wav2Lip disabled by settings",
            "models/Wav2Lip/inference.py",
            "models/Wav2Lip/checkpoints/wav2lip_gan.pth",
            "models/Wav2Lip/face_detection/detection/sfd/s3fd.pth",
            "models/default-presenter.mp4",
        ],
        "model_paths": {
            "root": str(settings.wav2lip_root),
            "inference": str(settings.wav2lip_root / "inference.py"),
            "checkpoint": str(settings.wav2lip_checkpoint_path),
            "face_detector": str(settings.wav2lip_face_detector_path),
            "default_face": str(settings.wav2lip_default_face_path),
        },
        "setup_command": "python scripts/setup_wav2lip.py",
    }


def test_runtime_renderers_endpoint_returns_musetalk_and_wav2lip_statuses(
    client: TestClient,
    tmp_path: Path,
    monkeypatch,
) -> None:
    settings = Settings(
        enable_musetalk=False,
        musetalk_root=tmp_path / "models" / "MuseTalk",
        musetalk_model_root=tmp_path / "models" / "MuseTalk" / "models",
        enable_wav2lip=False,
        wav2lip_root=tmp_path / "models" / "Wav2Lip",
        wav2lip_checkpoint_path=tmp_path / "models" / "Wav2Lip" / "checkpoints" / "wav2lip_gan.pth",
        wav2lip_face_detector_path=tmp_path
        / "models"
        / "Wav2Lip"
        / "face_detection"
        / "detection"
        / "sfd"
        / "s3fd.pth",
        wav2lip_default_face_path=tmp_path / "models" / "default-presenter.mp4",
    )
    monkeypatch.setattr("app.api.routes.get_settings", lambda: settings)

    response = client.get("/api/runtime/renderers")

    assert response.status_code == 200
    payload = response.json()
    assert payload["active_renderer"] == "fallback"
    assert set(payload["renderers"]) == {"musetalk", "wav2lip"}
    assert payload["renderers"]["musetalk"]["setup_command"] == "python scripts/setup_musetalk.py"
    assert payload["renderers"]["wav2lip"]["setup_command"] == "python scripts/setup_wav2lip.py"


def test_musetalk_runtime_status_reports_missing_requirements(
    tmp_path: Path,
    monkeypatch,
) -> None:
    settings = Settings(
        enable_musetalk=True,
        musetalk_root=tmp_path / "models" / "MuseTalk",
        musetalk_model_root=tmp_path / "models" / "MuseTalk" / "models",
    )
    monkeypatch.setattr(
        "app.services.runtime_status._missing_python_modules",
        lambda python, modules: ["mmpose"],
    )

    status = get_musetalk_runtime_status(settings)

    assert status.enabled is True
    assert status.available is False
    assert status.active_renderer == "fallback"
    assert status.missing_requirements == [
        "models/MuseTalk/scripts/inference.py",
        "models/MuseTalk/models/musetalkV15/unet.pth",
        "models/MuseTalk/models/musetalkV15/musetalk.json",
        "models/MuseTalk/models/sd-vae/config.json",
        "models/MuseTalk/models/whisper/config.json",
        "models/MuseTalk/models/dwpose/dw-ll_ucoco_384.pth",
            "models/MuseTalk/models/face-parse-bisent/79999_iter.pth",
            "models/MuseTalk/models/syncnet/latentsync_syncnet.pt",
            "MuseTalk python missing modules: mmpose",
        ]
    assert status.setup_command == "python scripts/setup_musetalk.py"


def test_musetalk_runtime_status_reports_available_runtime(
    tmp_path: Path,
    monkeypatch,
) -> None:
    musetalk_root = tmp_path / "models" / "MuseTalk"
    model_root = musetalk_root / "models"
    settings = Settings(
        enable_musetalk=True,
        musetalk_root=musetalk_root,
        musetalk_model_root=model_root,
    )
    for path in [
        musetalk_root / "scripts" / "inference.py",
        model_root / "musetalkV15" / "unet.pth",
        model_root / "musetalkV15" / "musetalk.json",
        model_root / "sd-vae" / "config.json",
        model_root / "whisper" / "config.json",
        model_root / "dwpose" / "dw-ll_ucoco_384.pth",
        model_root / "face-parse-bisent" / "79999_iter.pth",
        model_root / "syncnet" / "latentsync_syncnet.pt",
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"placeholder")
    monkeypatch.setattr(
        "app.services.runtime_status._missing_python_modules",
        lambda python, modules: [],
    )

    status = get_musetalk_runtime_status(settings)

    assert status.enabled is True
    assert status.available is True
    assert status.active_renderer == "musetalk"
    assert status.missing_requirements == []


def test_musetalk_runtime_status_checks_default_python_dependencies(
    tmp_path: Path,
    monkeypatch,
) -> None:
    musetalk_root = tmp_path / "models" / "MuseTalk"
    model_root = musetalk_root / "models"
    settings = Settings(
        enable_musetalk=True,
        musetalk_root=musetalk_root,
        musetalk_model_root=model_root,
    )
    for path in [
        musetalk_root / "scripts" / "inference.py",
        model_root / "musetalkV15" / "unet.pth",
        model_root / "musetalkV15" / "musetalk.json",
        model_root / "sd-vae" / "config.json",
        model_root / "whisper" / "config.json",
        model_root / "dwpose" / "dw-ll_ucoco_384.pth",
        model_root / "face-parse-bisent" / "79999_iter.pth",
        model_root / "syncnet" / "latentsync_syncnet.pt",
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"placeholder")
    observed_python_paths: list[Path] = []

    def fake_missing_python_modules(python: Path, modules: list[str]) -> list[str]:
        observed_python_paths.append(python)
        return ["mmpose"]

    monkeypatch.setattr(
        "app.services.runtime_status._missing_python_modules",
        fake_missing_python_modules,
    )

    status = get_musetalk_runtime_status(settings)

    assert observed_python_paths
    assert status.available is False
    assert status.missing_requirements == ["MuseTalk python missing modules: mmpose"]


def test_musetalk_runtime_status_requires_runtime_dependencies(
    tmp_path: Path,
    monkeypatch,
) -> None:
    musetalk_root = tmp_path / "models" / "MuseTalk"
    model_root = musetalk_root / "models"
    python_path = tmp_path / "venv" / "Scripts" / "python.exe"
    settings = Settings(
        enable_musetalk=True,
        musetalk_root=musetalk_root,
        musetalk_model_root=model_root,
        musetalk_python_path=python_path,
    )
    for path in [
        musetalk_root / "scripts" / "inference.py",
        model_root / "musetalkV15" / "unet.pth",
        model_root / "musetalkV15" / "musetalk.json",
        model_root / "sd-vae" / "config.json",
        model_root / "whisper" / "config.json",
        model_root / "dwpose" / "dw-ll_ucoco_384.pth",
        model_root / "face-parse-bisent" / "79999_iter.pth",
        model_root / "syncnet" / "latentsync_syncnet.pt",
        python_path,
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"placeholder")
    monkeypatch.setattr(
        "app.services.runtime_status._missing_python_modules",
        lambda python, modules: ["mmcv", "mmpose"],
    )

    status = get_musetalk_runtime_status(settings)

    assert status.available is False
    assert status.active_renderer == "fallback"
    assert status.missing_requirements == ["MuseTalk python missing modules: mmcv, mmpose"]
