from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import TypeVar

from sqlmodel import Session, delete

from app.models import (
    DigitalHumanProfile,
    GenerationStepLog,
    MediaAsset,
    PostProcessTemplate,
    ScriptDraft,
    StepStatus,
    TaskState,
    VideoTask,
    VoiceProfile,
)
from app.providers.base import (
    AudioResult,
    AvatarRenderer,
    LLMProvider,
    PostProcessor,
    PostProcessResult,
    RenderResult,
    ScriptResult,
    TTSProvider,
)
from app.storage import TaskStorage

StepResult = TypeVar("StepResult")


class TaskRunner:
    def __init__(
        self,
        storage: TaskStorage,
        llm_provider: LLMProvider,
        tts_provider: TTSProvider,
        avatar_renderer: AvatarRenderer,
        post_processor: PostProcessor,
    ) -> None:
        self.storage = storage
        self.llm_provider = llm_provider
        self.tts_provider = tts_provider
        self.avatar_renderer = avatar_renderer
        self.post_processor = post_processor

    def run_task(self, session: Session, task_id: int) -> None:
        task = session.get(VideoTask, task_id)
        if task is None:
            raise ValueError(f"Task {task_id} does not exist")

        self._reset_task_outputs(session, task)
        self._transition_task(session, task, TaskState.QUEUED)

        script = self._run_step(
            session,
            task,
            "script",
            lambda: self._prepare_script(session, task),
        )
        audio = self._run_step(
            session,
            task,
            "tts",
            lambda: self._synthesize(session, task, script.script_text),
        )
        raw_video = self._run_step(
            session,
            task,
            "avatar_render",
            lambda: self._render_avatar(session, task, audio.audio_path, script.script_text),
        )
        self._run_step(
            session,
            task,
            "post_process",
            lambda: self._post_process(session, task, raw_video.video_path, script.script_text),
        )

        self._transition_task(session, task, TaskState.COMPLETED)

    def _run_step(
        self,
        session: Session,
        task: VideoTask,
        step_name: str,
        action: Callable[[], StepResult],
    ) -> StepResult:
        started = _utc_now()
        task_id = _task_id(task)
        log = GenerationStepLog(
            task_id=task_id,
            step_name=step_name,
            status=StepStatus.RUNNING,
            started_at=started,
        )
        session.add(log)
        session.commit()
        session.refresh(log)
        log_id = log.id

        try:
            result = action()
        except Exception as exc:
            finished = _utc_now()
            session.rollback()
            log = self._failure_log(session, log_id, task_id, step_name, started)
            task = session.get(VideoTask, task_id)
            if task is None:
                raise
            log.status = StepStatus.FAILED
            log.finished_at = finished
            log.duration_seconds = (finished - started).total_seconds()
            log.error_code = f"{step_name}_failed"
            log.user_message = f"{step_name} step failed"
            log.technical_log = str(exc)
            task.current_state = TaskState.FAILED
            task.failed_step = step_name
            task.updated_at = finished
            session.add(log)
            session.add(task)
            session.commit()
            raise

        finished = _utc_now()
        log.status = StepStatus.SUCCEEDED
        log.finished_at = finished
        log.duration_seconds = (finished - started).total_seconds()
        log.technical_log = self._technical_log(step_name, result)
        session.add(log)
        session.commit()
        return result

    def _prepare_script(self, session: Session, task: VideoTask) -> ScriptResult:
        result = self.llm_provider.prepare_script(
            task_id=_task_id(task),
            input_mode=task.input_mode,
            raw_input=task.raw_input,
        )
        session.add(
            ScriptDraft(
                task_id=_task_id(task),
                script_text=result.script_text,
                structured_segments=result.structured_segments,
                estimated_duration_seconds=result.estimated_duration_seconds,
                source_mode=task.input_mode.value,
            )
        )
        self._transition_task(session, task, TaskState.SCRIPT_READY, commit=False)
        session.commit()
        return result

    def _synthesize(self, session: Session, task: VideoTask, script_text: str) -> AudioResult:
        voice = session.get(VoiceProfile, task.voice_profile_id)
        voice_key = voice.voice_key if voice is not None else str(task.voice_profile_id)
        result = self.tts_provider.synthesize(
            task_id=_task_id(task),
            script_text=script_text,
            voice_key=voice_key,
        )
        session.add(
            MediaAsset(
                task_id=_task_id(task),
                asset_type="audio",
                file_path=_path_text(result.audio_path),
                duration_seconds=result.duration_seconds,
                asset_metadata={"timing": result.timing},
            )
        )
        self._transition_task(session, task, TaskState.AUDIO_READY, commit=False)
        session.commit()
        return result

    def _render_avatar(
        self,
        session: Session,
        task: VideoTask,
        audio_path: Path,
        script_text: str,
    ) -> RenderResult:
        human = session.get(DigitalHumanProfile, task.digital_human_profile_id)
        profile_key = (
            human.renderer_adapter_key if human is not None else str(task.digital_human_profile_id)
        )
        source_media_path = (
            Path(human.source_media_path)
            if human is not None and human.source_media_path is not None
            else None
        )
        result = self.avatar_renderer.render(
            task_id=_task_id(task),
            audio_path=audio_path,
            profile_key=profile_key,
            script_text=script_text,
            source_media_path=source_media_path,
        )
        session.add(
            MediaAsset(
                task_id=_task_id(task),
                asset_type="raw_video",
                file_path=_path_text(result.video_path),
                duration_seconds=result.duration_seconds,
            )
        )
        self._transition_task(session, task, TaskState.RENDERED, commit=False)
        session.commit()
        return result

    def _post_process(
        self,
        session: Session,
        task: VideoTask,
        raw_video_path: Path,
        script_text: str,
    ) -> PostProcessResult:
        template = session.get(PostProcessTemplate, task.post_process_template_id)
        template_key = template.name if template is not None else str(task.post_process_template_id)
        result = self.post_processor.process(
            task_id=_task_id(task),
            raw_video_path=raw_video_path,
            script_text=script_text,
            template_key=template_key,
        )
        session.add(
            MediaAsset(
                task_id=_task_id(task),
                asset_type="final_video",
                file_path=_path_text(result.final_video_path),
            )
        )
        session.add(
            MediaAsset(
                task_id=_task_id(task),
                asset_type="cover",
                file_path=_path_text(result.cover_path),
            )
        )
        task.final_video_path = _path_text(result.final_video_path)
        task.cover_path = _path_text(result.cover_path)
        self._transition_task(session, task, TaskState.POST_PROCESSED, commit=False)
        session.commit()
        return result

    def _transition_task(
        self,
        session: Session,
        task: VideoTask,
        state: TaskState,
        *,
        commit: bool = True,
    ) -> None:
        task.current_state = state
        task.updated_at = _utc_now()
        session.add(task)
        if commit:
            session.commit()

    def _reset_task_outputs(self, session: Session, task: VideoTask) -> None:
        task_id = _task_id(task)
        session.exec(delete(ScriptDraft).where(ScriptDraft.task_id == task_id))
        session.exec(delete(MediaAsset).where(MediaAsset.task_id == task_id))
        session.exec(delete(GenerationStepLog).where(GenerationStepLog.task_id == task_id))
        task.final_video_path = None
        task.cover_path = None
        task.failed_step = None

    @staticmethod
    def _failure_log(
        session: Session,
        log_id: int | None,
        task_id: int,
        step_name: str,
        started: datetime,
    ) -> GenerationStepLog:
        log = session.get(GenerationStepLog, log_id) if log_id is not None else None
        if log is not None:
            return log
        return GenerationStepLog(
            task_id=task_id,
            step_name=step_name,
            status=StepStatus.RUNNING,
            started_at=started,
        )

    @staticmethod
    def _technical_log(step_name: str, result: object) -> str:
        technical_log = getattr(result, "technical_log", None)
        if isinstance(technical_log, str) and technical_log:
            return technical_log
        return f"{step_name} completed"


def _task_id(task: VideoTask) -> int:
    if task.id is None:
        raise ValueError("Task must be persisted before running")
    return task.id


def _path_text(path: Path) -> str:
    return str(path)


def _utc_now() -> datetime:
    return datetime.now(UTC)
