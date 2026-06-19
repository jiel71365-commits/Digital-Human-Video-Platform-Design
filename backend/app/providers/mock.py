from pathlib import Path

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
        path = self.storage.artifact_path(task_id, "audio", "speech.txt")
        duration = _estimate_duration(script_text)
        path.write_text(
            f"voice={voice_key}\nduration={duration}\n{script_text}\n",
            encoding="utf-8",
        )
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
    ) -> RenderResult:
        path = self.storage.artifact_path(task_id, "render", "raw-video.txt")
        duration = _duration_from_audio_artifact(audio_path)
        path.write_text(
            (
                f"profile={profile_key}\n"
                f"audio={audio_path.as_posix()}\n"
                f"duration={duration}\n"
                f"script={script_text}\n"
            ),
            encoding="utf-8",
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
        final_path = self.storage.artifact_path(task_id, "final", "final-video.mp4")
        cover_path = self.storage.artifact_path(task_id, "final", "cover.txt")
        final_path.write_text(
            (
                f"template={template_key}\n"
                f"raw_video={raw_video_path.as_posix()}\n"
                f"script={script_text}\n"
            ),
            encoding="utf-8",
        )
        cover_path.write_text(f"cover for task {task_id}\n", encoding="utf-8")
        return PostProcessResult(
            final_video_path=final_path,
            cover_path=cover_path,
            technical_log="mock post-process ok",
        )


def _estimate_duration(script_text: str) -> float:
    return round(max(len(script_text), 1) / 5.5, 2)


def _duration_from_audio_artifact(audio_path: Path) -> float:
    if not audio_path.exists():
        return 3.0

    for line in audio_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("duration="):
            return float(line.removeprefix("duration="))

    return 3.0
