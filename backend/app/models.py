from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class ProfileStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class TaskInputMode(StrEnum):
    TOPIC = "topic"
    EXISTING_SCRIPT = "existing_script"
    REFERENCE_VIDEO = "reference_video"


class TaskState(StrEnum):
    DRAFT = "draft"
    QUEUED = "queued"
    SCRIPT_READY = "script_ready"
    AUDIO_READY = "audio_ready"
    RENDERED = "rendered"
    POST_PROCESSED = "post_processed"
    COMPLETED = "completed"
    FAILED = "failed"


class StepStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class DigitalHumanProfile(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    preview_image_path: str | None = None
    source_media_path: str | None = None
    default_aspect_ratio: str = "9:16"
    renderer_adapter_key: str = "mock-avatar"
    status: ProfileStatus = ProfileStatus.ACTIVE
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class VoiceProfile(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    provider_key: str = "mock-tts"
    voice_key: str = "default"
    style_tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    preview_audio_path: str | None = None
    is_default: bool = False
    status: ProfileStatus = ProfileStatus.ACTIVE
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class PostProcessTemplate(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    subtitle_style: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    bgm_path: str | None = None
    intro_media_path: str | None = None
    outro_media_path: str | None = None
    cover_strategy: str = "first_frame"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class VideoTask(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    input_mode: TaskInputMode
    raw_input: str
    digital_human_profile_id: int = Field(foreign_key="digitalhumanprofile.id")
    voice_profile_id: int = Field(foreign_key="voiceprofile.id")
    post_process_template_id: int = Field(foreign_key="postprocesstemplate.id")
    current_state: TaskState = TaskState.DRAFT
    failed_step: str | None = None
    final_video_path: str | None = None
    cover_path: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ScriptDraft(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="videotask.id", index=True)
    version: int = 1
    script_text: str
    structured_segments: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSON),
    )
    estimated_duration_seconds: float = 0
    source_mode: str
    created_at: datetime = Field(default_factory=utc_now)


class MediaAsset(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="videotask.id", index=True)
    asset_type: str
    file_path: str
    duration_seconds: float | None = None
    asset_metadata: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)


class GenerationStepLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="videotask.id", index=True)
    step_name: str
    status: StepStatus
    started_at: datetime = Field(default_factory=utc_now)
    finished_at: datetime | None = None
    duration_seconds: float | None = None
    error_code: str | None = None
    user_message: str | None = None
    technical_log: str | None = None
