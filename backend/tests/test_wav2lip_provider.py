import subprocess
import wave
from pathlib import Path

import pytest

from app.providers.base import RenderResult
from app.providers.wav2lip import Wav2LipRenderer
from app.storage import TaskStorage


def test_wav2lip_renderer_falls_back_when_prerequisites_are_missing(tmp_path: Path) -> None:
    storage = TaskStorage(tmp_path)
    audio_path = _write_wav(storage.artifact_path(1, "audio", "speech.wav"))
    fallback = RecordingFallbackRenderer(storage)
    renderer = Wav2LipRenderer(
        storage=storage,
        fallback_renderer=fallback,
        wav2lip_root=tmp_path / "missing-wav2lip",
        checkpoint_path=tmp_path / "missing-checkpoint.pth",
        face_detector_path=tmp_path / "missing-s3fd.pth",
        default_face_path=tmp_path / "missing-face.mp4",
    )

    result = renderer.render(
        task_id=1,
        audio_path=audio_path,
        profile_key="wav2lip",
        script_text="hello",
    )

    assert result.video_path == tmp_path / "tasks" / "1" / "render" / "fallback.mp4"
    assert result.video_path.exists()
    assert result.duration_seconds == pytest.approx(1.0)
    assert fallback.calls == [
        {
            "task_id": 1,
            "audio_path": audio_path,
            "profile_key": "wav2lip",
            "script_text": "hello",
        }
    ]
    assert "wav2lip fallback" in result.technical_log
    assert "missing Wav2Lip inference.py" in result.technical_log
    assert "fallback render ok" in result.technical_log


def test_wav2lip_renderer_invokes_external_inference_when_ready(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    storage = TaskStorage(tmp_path)
    wav2lip_root = tmp_path / "models" / "Wav2Lip"
    inference_path = wav2lip_root / "inference.py"
    checkpoint_path = wav2lip_root / "checkpoints" / "wav2lip_gan.pth"
    face_detector_path = wav2lip_root / "face_detection" / "detection" / "sfd" / "s3fd.pth"
    face_path = tmp_path / "default-presenter.mp4"
    audio_path = _write_wav(storage.artifact_path(2, "audio", "speech.wav"))
    for path in [inference_path, checkpoint_path, face_detector_path, face_path]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"placeholder")
    fallback = RecordingFallbackRenderer(storage)
    calls: list[dict[str, object]] = []

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        check: bool,
        capture_output: bool,
        text: bool,
        env: dict[str, str],
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        calls.append(
            {
                "command": command,
                "cwd": cwd,
                "check": check,
                "capture_output": capture_output,
                "text": text,
                "env": env,
                "timeout": timeout,
            }
        )
        outfile = Path(command[command.index("--outfile") + 1])
        outfile.parent.mkdir(parents=True, exist_ok=True)
        outfile.write_bytes(b"wav2lip mp4")
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    monkeypatch.setattr("app.providers.wav2lip.subprocess.run", fake_run)
    renderer = Wav2LipRenderer(
        storage=storage,
        fallback_renderer=fallback,
        wav2lip_root=wav2lip_root,
        checkpoint_path=checkpoint_path,
        face_detector_path=face_detector_path,
        default_face_path=face_path,
        python_path=Path("C:/custom/python.exe"),
        timeout_seconds=123,
    )

    result = renderer.render(
        task_id=2,
        audio_path=audio_path,
        profile_key="wav2lip",
        script_text="hello",
    )

    assert result.video_path == tmp_path / "tasks" / "2" / "render" / "raw-video.mp4"
    assert result.video_path.read_bytes() == b"wav2lip mp4"
    assert result.duration_seconds == pytest.approx(1.0)
    assert result.technical_log == "wav2lip render ok"
    assert fallback.calls == []
    assert len(calls) == 1
    call = calls[0]
    command = call["command"]
    assert isinstance(command, list)
    assert command[0] == "C:\\custom\\python.exe"
    assert Path(command[1]).is_absolute()
    assert Path(command[3]).is_absolute()
    assert Path(command[5]).is_absolute()
    assert Path(command[7]).is_absolute()
    assert Path(command[9]).is_absolute()
    assert command[1:] == [
        str(inference_path),
        "--checkpoint_path",
        str(checkpoint_path),
        "--face",
        str(face_path),
        "--audio",
        str(audio_path),
        "--outfile",
        str(result.video_path),
        "--static",
        "True",
        "--fps",
        "24",
    ]
    assert call["cwd"] == wav2lip_root
    assert call["timeout"] == 123
    env = call["env"]
    assert isinstance(env, dict)
    assert "PATH" in env
    ffmpeg_shim = tmp_path / "ffmpeg-bin" / "ffmpeg.exe"
    assert ffmpeg_shim.exists()
    assert Path(env["PATH"].split(";")[0]).is_absolute()
    assert env["PATH"].startswith(str(ffmpeg_shim.parent))


def test_wav2lip_renderer_resolves_relative_artifact_paths_for_subprocess(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    storage = TaskStorage(Path("relative-storage"))
    wav2lip_root = Path("models/Wav2Lip")
    inference_path = wav2lip_root / "inference.py"
    checkpoint_path = wav2lip_root / "checkpoints" / "wav2lip_gan.pth"
    face_detector_path = wav2lip_root / "face_detection" / "detection" / "sfd" / "s3fd.pth"
    face_path = Path("models/default-presenter.mp4")
    audio_path = _write_wav(storage.artifact_path(3, "audio", "speech.wav"))
    for path in [inference_path, checkpoint_path, face_detector_path, face_path]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"placeholder")
    commands: list[list[str]] = []

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        check: bool,
        capture_output: bool,
        text: bool,
        env: dict[str, str],
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        outfile = Path(command[command.index("--outfile") + 1])
        outfile.parent.mkdir(parents=True, exist_ok=True)
        outfile.write_bytes(b"wav2lip mp4")
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    monkeypatch.setattr("app.providers.wav2lip.subprocess.run", fake_run)
    renderer = Wav2LipRenderer(
        storage=storage,
        fallback_renderer=RecordingFallbackRenderer(storage),
        wav2lip_root=wav2lip_root,
        checkpoint_path=checkpoint_path,
        face_detector_path=face_detector_path,
        default_face_path=face_path,
    )

    result = renderer.render(
        task_id=3,
        audio_path=audio_path,
        profile_key="wav2lip",
        script_text="hello",
    )

    command = commands[0]
    assert Path(command[1]).is_absolute()
    assert Path(command[3]).is_absolute()
    assert Path(command[5]).is_absolute()
    assert Path(command[7]).is_absolute()
    assert Path(command[9]).is_absolute()
    assert result.video_path == Path("relative-storage/tasks/3/render/raw-video.mp4")
    env_path = Wav2LipRenderer(
        storage=storage,
        fallback_renderer=RecordingFallbackRenderer(storage),
        wav2lip_root=wav2lip_root,
        checkpoint_path=checkpoint_path,
        face_detector_path=face_detector_path,
        default_face_path=face_path,
    )._subprocess_env()["PATH"]
    assert Path(env_path.split(";")[0]).is_absolute()


def test_wav2lip_renderer_fallback_log_includes_subprocess_output_when_output_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    storage = TaskStorage(tmp_path)
    wav2lip_root = tmp_path / "models" / "Wav2Lip"
    inference_path = wav2lip_root / "inference.py"
    checkpoint_path = wav2lip_root / "checkpoints" / "wav2lip_gan.pth"
    face_detector_path = wav2lip_root / "face_detection" / "detection" / "sfd" / "s3fd.pth"
    face_path = tmp_path / "default-presenter.mp4"
    audio_path = _write_wav(storage.artifact_path(4, "audio", "speech.wav"))
    for path in [inference_path, checkpoint_path, face_detector_path, face_path]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"placeholder")
    fallback = RecordingFallbackRenderer(storage)

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        check: bool,
        capture_output: bool,
        text: bool,
        env: dict[str, str],
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, stdout="model ok", stderr="ffmpeg failed")

    monkeypatch.setattr("app.providers.wav2lip.subprocess.run", fake_run)
    renderer = Wav2LipRenderer(
        storage=storage,
        fallback_renderer=fallback,
        wav2lip_root=wav2lip_root,
        checkpoint_path=checkpoint_path,
        face_detector_path=face_detector_path,
        default_face_path=face_path,
    )

    result = renderer.render(
        task_id=4,
        audio_path=audio_path,
        profile_key="wav2lip",
        script_text="hello",
    )

    assert "Wav2Lip did not create raw-video.mp4" in result.technical_log
    assert "model ok" in result.technical_log
    assert "ffmpeg failed" in result.technical_log
    assert fallback.calls


class RecordingFallbackRenderer:
    def __init__(self, storage: TaskStorage) -> None:
        self.storage = storage
        self.calls: list[dict[str, object]] = []

    def render(
        self,
        task_id: int,
        audio_path: Path,
        profile_key: str,
        script_text: str = "",
    ) -> RenderResult:
        self.calls.append(
            {
                "task_id": task_id,
                "audio_path": audio_path,
                "profile_key": profile_key,
                "script_text": script_text,
            }
        )
        video_path = self.storage.artifact_path(task_id, "render", "fallback.mp4")
        video_path.write_bytes(b"fallback")
        return RenderResult(
            video_path=video_path,
            duration_seconds=1.0,
            technical_log="fallback render ok",
        )


def _write_wav(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16_000)
        audio.writeframes(b"\0\0" * 16_000)
    return path
