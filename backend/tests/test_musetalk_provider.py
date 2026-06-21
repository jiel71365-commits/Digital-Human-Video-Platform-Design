import subprocess
import wave
from pathlib import Path

import pytest

from app.providers.base import RenderResult
from app.providers.musetalk import MuseTalkRenderer
from app.storage import TaskStorage


def test_musetalk_renderer_falls_back_when_prerequisites_are_missing(tmp_path: Path) -> None:
    storage = TaskStorage(tmp_path)
    audio_path = _write_wav(storage.artifact_path(1, "audio", "speech.wav"))
    fallback = RecordingFallbackRenderer(storage)
    renderer = MuseTalkRenderer(
        storage=storage,
        fallback_renderer=fallback,
        musetalk_root=tmp_path / "missing-MuseTalk",
        model_root=tmp_path / "models" / "MuseTalk",
        python_path=Path("C:/custom/python.exe"),
    )

    result = renderer.render(
        task_id=1,
        audio_path=audio_path,
        profile_key="musetalk",
        script_text="hello",
        source_media_path=tmp_path / "presenter.mp4",
    )

    assert result.video_path == tmp_path / "tasks" / "1" / "render" / "fallback.mp4"
    assert result.duration_seconds == pytest.approx(1.0)
    assert fallback.calls == [
        {
            "task_id": 1,
            "audio_path": audio_path,
            "profile_key": "musetalk",
            "script_text": "hello",
            "source_media_path": tmp_path / "presenter.mp4",
        }
    ]
    assert "musetalk fallback" in result.technical_log
    assert "missing MuseTalk inference package" in result.technical_log


def test_musetalk_renderer_invokes_external_inference_when_ready(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    storage = TaskStorage(tmp_path)
    musetalk_root = tmp_path / "models" / "MuseTalk"
    model_root = musetalk_root / "models"
    source_media_path = tmp_path / "presenter.mp4"
    audio_path = _write_wav(storage.artifact_path(2, "audio", "speech.wav"))
    _write_required_musetalk_files(musetalk_root=musetalk_root, model_root=model_root)
    source_media_path.write_bytes(b"presenter")
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
        result_dir = Path(command[command.index("--result_dir") + 1])
        result_dir.mkdir(parents=True, exist_ok=True)
        (result_dir / "musetalk.mp4").write_bytes(b"musetalk mp4")
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    monkeypatch.setattr("app.providers.musetalk.subprocess.run", fake_run)
    renderer = MuseTalkRenderer(
        storage=storage,
        fallback_renderer=RecordingFallbackRenderer(storage),
        musetalk_root=musetalk_root,
        model_root=model_root,
        python_path=Path("C:/custom/python.exe"),
        timeout_seconds=123,
    )

    result = renderer.render(
        task_id=2,
        audio_path=audio_path,
        profile_key="musetalk",
        script_text="hello",
        source_media_path=source_media_path,
    )

    assert result.video_path == tmp_path / "tasks" / "2" / "render" / "raw-video.mp4"
    assert result.video_path.read_bytes() == b"musetalk mp4"
    assert result.duration_seconds == pytest.approx(1.0)
    assert result.technical_log == "musetalk render ok"
    assert len(calls) == 1
    call = calls[0]
    command = call["command"]
    assert isinstance(command, list)
    assert command[:3] == ["C:\\custom\\python.exe", "-m", "scripts.inference"]
    assert command[command.index("--inference_config") + 1].endswith("task-2.yaml")
    assert command[command.index("--result_dir") + 1] == str(
        tmp_path / "tasks" / "2" / "render" / "musetalk-result"
    )
    assert "--version" in command
    assert command[command.index("--version") + 1] == "v15"
    assert call["cwd"] == musetalk_root
    assert call["timeout"] == 123
    config_path = tmp_path / "tasks" / "2" / "render" / "musetalk-config" / "task-2.yaml"
    config_text = config_path.read_text(encoding="utf-8")
    assert str(source_media_path.resolve()).replace("\\", "/") in config_text
    assert str(audio_path.resolve()).replace("\\", "/") in config_text


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
        source_media_path: Path | None = None,
    ) -> RenderResult:
        self.calls.append(
            {
                "task_id": task_id,
                "audio_path": audio_path,
                "profile_key": profile_key,
                "script_text": script_text,
                "source_media_path": source_media_path,
            }
        )
        video_path = self.storage.artifact_path(task_id, "render", "fallback.mp4")
        video_path.write_bytes(b"fallback")
        return RenderResult(
            video_path=video_path,
            duration_seconds=1.0,
            technical_log="fallback render ok",
        )


def _write_required_musetalk_files(*, musetalk_root: Path, model_root: Path) -> None:
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


def _write_wav(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16_000)
        audio.writeframes(b"\0\0" * 16_000)
    return path
