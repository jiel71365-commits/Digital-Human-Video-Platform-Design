import math
import subprocess
import wave
from pathlib import Path
from tempfile import NamedTemporaryFile

import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from app.models import TaskInputMode
from app.providers.base import AudioResult, PostProcessResult, RenderResult, ScriptResult
from app.storage import TaskStorage


class MockLLMProvider:
    def prepare_script(
        self,
        task_id: int,
        input_mode: TaskInputMode,
        raw_input: str,
    ) -> ScriptResult:
        normalized = " ".join(raw_input.split())
        if input_mode == TaskInputMode.TOPIC:
            script_text = (
                f"今天我们来介绍：围绕{normalized}的核心亮点。"
                "这条数字人口播视频会突出卖点、使用场景和行动建议。"
            )
        elif input_mode == TaskInputMode.REFERENCE_VIDEO:
            script_text = (
                f"参考{normalized}的内容节奏，改写成一条新的数字人口播文案。"
                "开头抓住痛点，中段说明价值，结尾引导立即了解。"
            )
        else:
            script_text = normalized

        duration = _estimate_duration(script_text)
        return ScriptResult(
            script_text=script_text,
            structured_segments=[{"index": 1, "text": script_text}],
            estimated_duration_seconds=duration,
        )


class MockTTSProvider:
    def __init__(self, storage: TaskStorage) -> None:
        self.storage = storage

    def synthesize(self, task_id: int, script_text: str, voice_key: str) -> AudioResult:
        path = self.storage.artifact_path(task_id, "audio", "speech.wav")
        duration = _estimate_duration(script_text)
        _write_sapi_or_tone_wav(path=path, script_text=script_text, duration_seconds=duration)
        duration = _duration_from_wav(path)
        return AudioResult(
            audio_path=path,
            duration_seconds=duration,
            timing=[{"start": 0.0, "end": duration, "text": script_text}],
        )


class MockAvatarRenderer:
    def __init__(self, storage: TaskStorage) -> None:
        self.storage = storage

    def render(
        self,
        task_id: int,
        audio_path: Path,
        profile_key: str,
        script_text: str = "",
        source_media_path: Path | None = None,
    ) -> RenderResult:
        duration = _duration_from_audio_artifact(audio_path)
        path = self.storage.artifact_path(task_id, "render", "raw-video.mp4")
        _write_silent_avatar_mp4(
            path=path,
            script_text=script_text,
            template_key=profile_key,
            duration_seconds=duration,
        )
        return RenderResult(
            video_path=path,
            duration_seconds=duration,
            technical_log="mock render ok",
        )


class MockPostProcessor:
    def __init__(self, storage: TaskStorage) -> None:
        self.storage = storage

    def process(
        self,
        task_id: int,
        raw_video_path: Path,
        script_text: str,
        template_key: str = "default",
    ) -> PostProcessResult:
        if not raw_video_path.exists():
            raise FileNotFoundError(f"Raw video artifact does not exist: {raw_video_path}")

        final_path = self.storage.artifact_path(task_id, "final", "final-video.mp4")
        cover_path = self.storage.artifact_path(task_id, "final", "cover.jpg")
        audio_path = _audio_path_for_raw_video(raw_video_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio artifact does not exist: {audio_path}")
        _mux_audio_video(
            raw_video_path=raw_video_path,
            audio_path=audio_path,
            output_path=final_path,
        )
        _write_cover_image(
            raw_video_path=raw_video_path,
            cover_path=cover_path,
            script_text=script_text,
            template_key=template_key,
        )
        return PostProcessResult(
            final_video_path=final_path,
            cover_path=cover_path,
            technical_log="mock post-process ok",
        )


def _estimate_duration(script_text: str) -> float:
    return round(max(len(script_text), 1) / 5.5, 2)


def _duration_from_audio_artifact(audio_path: Path) -> float:
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio artifact does not exist: {audio_path}")

    if audio_path.suffix.lower() == ".wav":
        return _duration_from_wav(audio_path)

    return 3.0


def _duration_from_wav(path: Path) -> float:
    with wave.open(str(path), "rb") as audio:
        return round(audio.getnframes() / audio.getframerate(), 2)


def _write_sapi_or_tone_wav(path: Path, script_text: str, duration_seconds: float) -> None:
    try:
        _write_sapi_wav(path, script_text)
    except Exception:
        _write_tone_wav(path=path, duration_seconds=duration_seconds)


def _write_sapi_wav(path: Path, script_text: str) -> None:
    import win32com.client  # type: ignore[import-untyped]

    stream = win32com.client.Dispatch("SAPI.SpFileStream")
    voice = win32com.client.Dispatch("SAPI.SpVoice")
    stream.Open(str(path.resolve()), 3, False)
    try:
        voice.AudioOutputStream = stream
        voice.Rate = 0
        voice.Volume = 100
        voice.Speak(script_text)
    finally:
        stream.Close()


def _write_tone_wav(*, path: Path, duration_seconds: float) -> None:
    sample_rate = 16_000
    frame_count = max(int(duration_seconds * sample_rate), sample_rate)
    amplitude = 9000
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate)
        frames = bytearray()
        for index in range(frame_count):
            envelope = 0.55 + 0.45 * math.sin(index / sample_rate * math.pi * 2)
            sample = int(amplitude * envelope * math.sin(2 * math.pi * 220 * index / sample_rate))
            frames.extend(sample.to_bytes(2, byteorder="little", signed=True))
        audio.writeframes(bytes(frames))


def _write_silent_avatar_mp4(
    *,
    path: Path,
    script_text: str,
    template_key: str,
    duration_seconds: float,
) -> None:
    with NamedTemporaryFile(suffix=".avi", delete=False) as temp:
        temp_path = Path(temp.name)
    try:
        _write_cv2_video(
            path=temp_path,
            script_text=script_text,
            template_key=template_key,
            duration_seconds=duration_seconds,
            fourcc_name="MJPG",
        )
        _run_ffmpeg(
            "-y",
            "-i",
            str(temp_path),
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(path),
        )
    finally:
        temp_path.unlink(missing_ok=True)


def _write_cv2_video(
    *,
    path: Path,
    script_text: str,
    template_key: str,
    duration_seconds: float,
    fourcc_name: str,
) -> None:
    width = 720
    height = 1280
    fps = 24
    frame_count = max(int(duration_seconds * fps), fps)
    fourcc = cv2.VideoWriter_fourcc(*fourcc_name)
    writer = cv2.VideoWriter(str(path), fourcc, fps, (width, height))
    if not writer.isOpened():
        raise RuntimeError(f"Could not open video writer for {path}")

    try:
        frames = _render_video_frames(
            width=width,
            height=height,
            frame_count=frame_count,
            script_text=script_text,
            template_key=template_key,
        )
        for frame in frames:
            writer.write(cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR))
    finally:
        writer.release()


def _render_video_frames(
    *,
    width: int,
    height: int,
    frame_count: int,
    script_text: str,
    template_key: str,
) -> list[Image.Image]:
    font_title = _load_font(42)
    font_body = _load_font(34)
    font_caption = _load_font(24)
    wrapped_script = _wrap_text(script_text, max_chars=18)
    frames: list[Image.Image] = []

    for index in range(frame_count):
        progress = index / max(frame_count - 1, 1)
        image = Image.new("RGB", (width, height), "#f5f7fb")
        draw = ImageDraw.Draw(image)

        accent_y = int(140 + 28 * np.sin(progress * np.pi * 2))
        draw.rounded_rectangle((80, 120, width - 80, 520), radius=42, fill="#1f4f46")
        draw.ellipse((220, accent_y, 500, accent_y + 280), fill="#e7f6f2")
        draw.ellipse((290, accent_y + 68, 430, accent_y + 208), fill="#26735f")
        draw.rectangle((300, accent_y + 215, 420, accent_y + 330), fill="#26735f")

        draw.text((80, 590), "Digital Human Video", font=font_title, fill="#172033")
        draw.text((80, 648), f"Template: {template_key}", font=font_caption, fill="#607086")
        y = 740
        for line in wrapped_script[:8]:
            draw.text((80, y), line, font=font_body, fill="#253449")
            y += 52

        bar_width = int((width - 160) * progress)
        draw.rounded_rectangle((80, 1140, width - 80, 1162), radius=11, fill="#dce3ee")
        draw.rounded_rectangle((80, 1140, 80 + bar_width, 1162), radius=11, fill="#26735f")
        draw.text((80, 1188), "Generated local MP4 preview", font=font_caption, fill="#607086")
        frames.append(image)

    return frames


def _audio_path_for_raw_video(raw_video_path: Path) -> Path:
    return raw_video_path.parents[1] / "audio" / "speech.wav"


def _mux_audio_video(*, raw_video_path: Path, audio_path: Path, output_path: Path) -> None:
    _run_ffmpeg(
        "-y",
        "-i",
        str(raw_video_path),
        "-i",
        str(audio_path),
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-shortest",
        str(output_path),
    )


def _write_cover_image(
    *,
    raw_video_path: Path,
    cover_path: Path,
    script_text: str,
    template_key: str,
) -> None:
    capture = cv2.VideoCapture(str(raw_video_path))
    try:
        ok, frame = capture.read()
    finally:
        capture.release()
    if ok:
        cv2.imwrite(str(cover_path), frame)
        return

    fallback = _render_video_frames(
        width=720,
        height=1280,
        frame_count=1,
        script_text=script_text,
        template_key=template_key,
    )[0]
    fallback.save(cover_path, format="JPEG", quality=92)


def _run_ffmpeg(*args: str) -> None:
    completed = subprocess.run(
        [imageio_ffmpeg.get_ffmpeg_exe(), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "ffmpeg command failed")


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap_text(text: str, max_chars: int) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return ["No script content"]
    return [normalized[index : index + max_chars] for index in range(0, len(normalized), max_chars)]
