import os
import shutil
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

from app.providers.base import AvatarRenderer, RenderResult
from app.providers.mock import _duration_from_audio_artifact
from app.storage import TaskStorage


class Wav2LipRenderer:
    def __init__(
        self,
        *,
        storage: TaskStorage,
        fallback_renderer: AvatarRenderer,
        wav2lip_root: Path,
        checkpoint_path: Path,
        face_detector_path: Path,
        default_face_path: Path,
        python_path: Path | None = None,
        enabled: bool = True,
        timeout_seconds: int = 1800,
    ) -> None:
        self.storage = storage
        self.fallback_renderer = fallback_renderer
        self.wav2lip_root = wav2lip_root
        self.checkpoint_path = checkpoint_path
        self.face_detector_path = face_detector_path
        self.default_face_path = default_face_path
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
        face_path = source_media_path or self.default_face_path
        missing_reason = self._missing_prerequisite(audio_path, face_path)
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
        inference_path = self.wav2lip_root / "inference.py"
        output_arg = output_path.resolve()
        wav2lip_root_arg = self.wav2lip_root.resolve()
        command = [
            str(self.python_path or sys.executable),
            str(inference_path.resolve()),
            "--checkpoint_path",
            str(self.checkpoint_path.resolve()),
            "--face",
            str(face_path.resolve()),
            "--audio",
            str(audio_path.resolve()),
            "--outfile",
            str(output_arg),
            "--fps",
            "24",
        ]
        if _is_image_face_media(face_path):
            command.extend(["--static", "True"])
        try:
            completed = subprocess.run(
                command,
                cwd=wav2lip_root_arg,
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
                f"Wav2Lip subprocess failed: {exc}",
                source_media_path,
            )

        if completed.returncode != 0:
            error = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
            return self._fallback(
                task_id,
                audio_path,
                profile_key,
                script_text,
                f"Wav2Lip exited with code {completed.returncode}: {error}",
                source_media_path,
            )
        if not output_path.exists():
            return self._fallback(
                task_id,
                audio_path,
                profile_key,
                script_text,
                f"Wav2Lip did not create raw-video.mp4: {_completed_output(completed)}",
                source_media_path,
            )

        return RenderResult(
            video_path=output_path,
            duration_seconds=_duration_from_audio_artifact(audio_path),
            technical_log="wav2lip render ok",
        )

    def _missing_prerequisite(self, audio_path: Path, face_path: Path) -> str | None:
        inference_path = self.wav2lip_root / "inference.py"
        checks = [
            (self.enabled, "Wav2Lip disabled by settings"),
            (inference_path.exists(), f"missing Wav2Lip inference.py: {inference_path}"),
            (self.checkpoint_path.exists(), f"missing Wav2Lip checkpoint: {self.checkpoint_path}"),
            (
                self.face_detector_path.exists(),
                f"missing Wav2Lip face detector: {self.face_detector_path}",
            ),
            (face_path.exists(), f"missing Wav2Lip face media: {face_path}"),
            (audio_path.exists(), f"missing audio artifact: {audio_path}"),
        ]
        for ok, reason in checks:
            if not ok:
                return reason
        return None

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
            technical_log=f"wav2lip fallback: {reason}; {result.technical_log}",
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


def _completed_output(completed: subprocess.CompletedProcess[str]) -> str:
    parts = []
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    if stdout:
        parts.append(f"stdout={stdout[-1000:]}")
    if stderr:
        parts.append(f"stderr={stderr[-1000:]}")
    return "; ".join(parts) or "no subprocess output"


def _is_image_face_media(path: Path) -> bool:
    return path.suffix.lower() in {".jpg", ".jpeg", ".png"}
