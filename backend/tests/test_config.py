from app.config import PROJECT_ROOT, Settings


def test_wav2lip_default_paths_are_project_root_relative() -> None:
    settings = Settings()

    assert settings.wav2lip_root == PROJECT_ROOT / "models" / "Wav2Lip"
    assert settings.wav2lip_checkpoint_path == (
        PROJECT_ROOT / "models" / "Wav2Lip" / "checkpoints" / "wav2lip_gan.pth"
    )
    assert settings.wav2lip_face_detector_path == (
        PROJECT_ROOT
        / "models"
        / "Wav2Lip"
        / "face_detection"
        / "detection"
        / "sfd"
        / "s3fd.pth"
    )
    assert settings.wav2lip_default_face_path == PROJECT_ROOT / "models" / "default-presenter.mp4"
