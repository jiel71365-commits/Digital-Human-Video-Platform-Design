from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from app.models import TaskInputMode


@dataclass(frozen=True)
class ScriptResult:
    script_text: str
    structured_segments: list[dict[str, Any]]
    estimated_duration_seconds: float


@dataclass(frozen=True)
class AudioResult:
    audio_path: Path
    duration_seconds: float
    timing: list[dict[str, Any]]


@dataclass(frozen=True)
class RenderResult:
    video_path: Path
    duration_seconds: float
    technical_log: str


@dataclass(frozen=True)
class PostProcessResult:
    final_video_path: Path
    cover_path: Path
    technical_log: str


class LLMProvider(Protocol):
    def prepare_script(
        self,
        task_id: int,
        input_mode: TaskInputMode,
        raw_input: str,
    ) -> ScriptResult:
        raise NotImplementedError


class TTSProvider(Protocol):
    def synthesize(self, task_id: int, script_text: str, voice_key: str) -> AudioResult:
        raise NotImplementedError


class AvatarRenderer(Protocol):
    def render(
        self,
        task_id: int,
        audio_path: Path,
        profile_key: str,
        script_text: str = "",
    ) -> RenderResult:
        raise NotImplementedError


class PostProcessor(Protocol):
    def process(
        self,
        task_id: int,
        raw_video_path: Path,
        script_text: str,
        template_key: str = "default",
    ) -> PostProcessResult:
        raise NotImplementedError
