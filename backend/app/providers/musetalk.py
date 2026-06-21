import os
import shutil
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

from app.providers.base import AvatarRenderer, RenderResult
from app.providers.mock import _duration_from_audio_artifact
from app.storage import TaskStorage


class MuseTalkRenderer:
    def __init__(
        self,
        *,
        storage: TaskStorage,
        fallback_renderer: AvatarRenderer,
        musetalk_root: Path,
        model_root: Path,
        python_path: Path | None = None,
        enabled: bool = True,
        timeout_seconds: int = 1800,
    ) -> None:
        self.storage = storage
        self.fallback_renderer = fallback_renderer
        self.musetalk_root = musetalk_root
        self.model_root = model_root
        self.python_path = python_path
        self.enabled = enabled
        self.timeout_seconds = timeout_seconds

    def render(
        self,
        task_id: int,
        audio_path: Path,
        profile_key: str,
        script_text: str = "",
        source_media_path: Path | None = None,
    ) -> RenderResult:
        if source_media_path is None:
            return self._fallback(
                task_id,
                audio_path,
                profile_key,
                script_text,
                "missing digital human source media for MuseTalk",
                source_media_path,
            )
        missing_reason = self._missing_prerequisite(audio_path, source_media_path)
        if missing_reason is not None:
            return self._fallback(
                task_id,
                audio_path,
                profile_key,
                script_text,
                missing_reason,
                source_media_path,
            )

        output_path = self.storage.artifact_path(task_id, "render", "raw-video.mp4")
        config_path = self._write_inference_config(
            task_id=task_id,
            audio_path=audio_path,
            source_media_path=source_media_path,
        )
        result_dir = output_path.parent / "musetalk-result"
        result_dir.mkdir(parents=True, exist_ok=True)
        command = [
            str(self.python_path or sys.executable),
            "-m",
            "scripts.inference",
            "--inference_config",
            str(config_path),
            "--result_dir",
            str(result_dir),
            "--version",
            "v15",
        ]

        try:
            completed = subprocess.run(
                command,
                cwd=self.musetalk_root,
                check=False,
                capture_output=True,
                text=True,
                env=self._subprocess_env(),
                timeout=self.timeout_seconds,
            )
        except Exception as exc:
            return self._fallback(
                task_id,
                audio_path,
                profile_key,
                script_text,
                f"MuseTalk subprocess failed: {exc}",
                source_media_path,
            )

        if completed.returncode != 0:
            error = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
            return self._fallback(
                task_id,
                audio_path,
                profile_key,
                script_text,
                f"MuseTalk exited with code {completed.returncode}: {error}",
                source_media_path,
            )

        generated_video = _latest_mp4(result_dir)
        if generated_video is None:
            return self._fallback(
                task_id,
                audio_path,
                profile_key,
                script_text,
                f"MuseTalk did not create an mp4: {_completed_output(completed)}",
                source_media_path,
            )
        shutil.copyfile(generated_video, output_path)
        return RenderResult(
            video_path=output_path,
            duration_seconds=_duration_from_audio_artifact(audio_path),
            technical_log="musetalk render ok",
        )

    def _missing_prerequisite(self, audio_path: Path, source_media_path: Path) -> str | None:
        inference_path = self.musetalk_root / "scripts" / "inference.py"
        checks = [
            (self.enabled, "MuseTalk disabled by settings"),
            (inference_path.exists(), f"missing MuseTalk inference package: {inference_path}"),
            (
                (self.model_root / "musetalkV15" / "unet.pth").exists(),
                f"missing MuseTalk unet: {self.model_root / 'musetalkV15' / 'unet.pth'}",
            ),
            (
                (self.model_root / "musetalkV15" / "musetalk.json").exists(),
                f"missing MuseTalk config: {self.model_root / 'musetalkV15' / 'musetalk.json'}",
            ),
            (
                (self.model_root / "sd-vae" / "config.json").exists(),
                f"missing MuseTalk VAE: {self.model_root / 'sd-vae'}",
            ),
            (
                (self.model_root / "whisper" / "config.json").exists(),
                f"missing MuseTalk whisper: {self.model_root / 'whisper'}",
            ),
            (
                (self.model_root / "dwpose" / "dw-ll_ucoco_384.pth").exists(),
                f"missing MuseTalk dwpose: {self.model_root / 'dwpose'}",
            ),
            (
                (self.model_root / "face-parse-bisent" / "79999_iter.pth").exists(),
                f"missing MuseTalk face parser: {self.model_root / 'face-parse-bisent'}",
            ),
            (
                (self.model_root / "syncnet" / "latentsync_syncnet.pt").exists(),
                f"missing MuseTalk syncnet: {self.model_root / 'syncnet'}",
            ),
            (source_media_path.exists(), f"missing source media: {source_media_path}"),
            (audio_path.exists(), f"missing audio artifact: {audio_path}"),
        ]
        for ok, reason in checks:
            if not ok:
                return reason
        return None

    def _write_inference_config(
        self,
        *,
        task_id: int,
        audio_path: Path,
        source_media_path: Path,
    ) -> Path:
        config_dir = self.storage.artifact_path(task_id, "render", "raw-video.mp4").parent
        config_path = config_dir / "musetalk-config" / f"task-{task_id}.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        video_path = source_media_path.resolve().as_posix()
        audio = audio_path.resolve().as_posix()
        config_path.write_text(
            "\n".join(
                [
                    "task_0:",
                    f"  video_path: {video_path}",
                    f"  audio_path: {audio}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        return config_path

    def _fallback(
        self,
        task_id: int,
        audio_path: Path,
        profile_key: str,
        script_text: str,
        reason: str,
        source_media_path: Path | None = None,
    ) -> RenderResult:
        result = self.fallback_renderer.render(
            task_id=task_id,
            audio_path=audio_path,
            profile_key=profile_key,
            script_text=script_text,
            source_media_path=source_media_path,
        )
        return RenderResult(
            video_path=result.video_path,
            duration_seconds=result.duration_seconds,
            technical_log=f"musetalk fallback: {reason}; {result.technical_log}",
        )

    def _subprocess_env(self) -> dict[str, str]:
        env = os.environ.copy()
        ffmpeg_dir = self._ensure_ffmpeg_shim()
        env["PATH"] = f"{ffmpeg_dir}{os.pathsep}{env.get('PATH', '')}"
        return env

    def _ensure_ffmpeg_shim(self) -> Path:
        ffmpeg_source = Path(imageio_ffmpeg.get_ffmpeg_exe())
        ffmpeg_dir = self.storage.root / "ffmpeg-bin"
        ffmpeg_dir.mkdir(parents=True, exist_ok=True)
        ffmpeg_shim = ffmpeg_dir / "ffmpeg.exe"
        if not ffmpeg_shim.exists() or ffmpeg_shim.stat().st_size != ffmpeg_source.stat().st_size:
            shutil.copyfile(ffmpeg_source, ffmpeg_shim)
        return ffmpeg_dir.resolve()


def _latest_mp4(path: Path) -> Path | None:
    candidates = [item for item in path.rglob("*.mp4") if item.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda item: item.stat().st_mtime)


def _completed_output(completed: subprocess.CompletedProcess[str]) -> str:
    parts = []
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    if stdout:
        parts.append(f"stdout={stdout[-1000:]}")
    if stderr:
        parts.append(f"stderr={stderr[-1000:]}")
    return "; ".join(parts) or "no subprocess output"
