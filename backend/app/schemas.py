from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import (
    DigitalHumanProfile,
    GenerationStepLog,
    MediaAsset,
    PostProcessTemplate,
    ProfileStatus,
    ScriptDraft,
    StepStatus,
    TaskInputMode,
    TaskState,
    VideoTask,
    VoiceProfile,
)


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TaskCreate(BaseModel):
    input_mode: TaskInputMode
    raw_input: str = Field(min_length=1)
    digital_human_profile_id: int
    voice_profile_id: int
    post_process_template_id: int


class TaskRead(ApiModel):
    id: int
    input_mode: TaskInputMode
    raw_input: str
    digital_human_profile_id: int
    voice_profile_id: int
    post_process_template_id: int
    current_state: TaskState
    failed_step: str | None
    final_video_path: str | None
    cover_path: str | None

    @classmethod
    def from_model(cls, task: VideoTask) -> "TaskRead":
        return cls.model_validate(task)


class ScriptDraftRead(ApiModel):
    id: int
    task_id: int
    version: int
    script_text: str
    structured_segments: list[dict[str, Any]]
    estimated_duration_seconds: float
    source_mode: str

    @classmethod
    def from_model(cls, script: ScriptDraft) -> "ScriptDraftRead":
        return cls.model_validate(script)


class MediaAssetRead(ApiModel):
    id: int
    task_id: int
    asset_type: str
    file_path: str
    duration_seconds: float | None
    asset_metadata: dict[str, Any]

    @classmethod
    def from_model(cls, asset: MediaAsset) -> "MediaAssetRead":
        return cls.model_validate(asset)


class GenerationStepLogRead(ApiModel):
    id: int
    task_id: int
    step_name: str
    status: StepStatus
    started_at: datetime
    finished_at: datetime | None
    duration_seconds: float | None
    error_code: str | None
    user_message: str | None
    technical_log: str | None

    @classmethod
    def from_model(cls, log: GenerationStepLog) -> "GenerationStepLogRead":
        return cls.model_validate(log)


class TaskDetail(BaseModel):
    task: TaskRead
    script: ScriptDraftRead | None
    assets: list[MediaAssetRead]
    logs: list[GenerationStepLogRead]


class DigitalHumanRead(ApiModel):
    id: int
    name: str
    preview_image_path: str | None
    source_media_path: str | None
    default_aspect_ratio: str
    renderer_adapter_key: str
    status: ProfileStatus

    @classmethod
    def from_model(cls, profile: DigitalHumanProfile) -> "DigitalHumanRead":
        return cls.model_validate(profile)


class VoiceRead(ApiModel):
    id: int
    name: str
    provider_key: str
    voice_key: str
    style_tags: list[str]
    preview_audio_path: str | None
    is_default: bool
    status: ProfileStatus

    @classmethod
    def from_model(cls, profile: VoiceProfile) -> "VoiceRead":
        return cls.model_validate(profile)


class TemplateRead(ApiModel):
    id: int
    name: str
    subtitle_style: dict[str, Any]
    bgm_path: str | None
    intro_media_path: str | None
    outro_media_path: str | None
    cover_strategy: str

    @classmethod
    def from_model(cls, template: PostProcessTemplate) -> "TemplateRead":
        return cls.model_validate(template)
