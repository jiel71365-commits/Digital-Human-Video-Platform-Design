from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.services.runtime_status import get_wav2lip_runtime_status


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
