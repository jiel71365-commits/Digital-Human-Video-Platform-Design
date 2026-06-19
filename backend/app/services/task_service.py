from pathlib import Path

from sqlmodel import Session, select

from app.models import (
    DigitalHumanProfile,
    GenerationStepLog,
    MediaAsset,
    PostProcessTemplate,
    ScriptDraft,
    TaskState,
    VideoTask,
    VoiceProfile,
)
from app.providers.mock import (
    MockAvatarRenderer,
    MockLLMProvider,
    MockPostProcessor,
    MockTTSProvider,
)
from app.schemas import TaskCreate
from app.services.task_runner import TaskRunner
from app.storage import TaskStorage


class InvalidTaskReferencesError(ValueError):
    def __init__(self, fields: list[str]) -> None:
        self.fields = fields
        super().__init__("Invalid task references")


class TaskRunError(RuntimeError):
    def __init__(
        self,
        *,
        task_id: int,
        message: str,
        current_state: TaskState,
        failed_step: str | None,
        error: str,
    ) -> None:
        self.task_id = task_id
        self.message = message
        self.current_state = current_state
        self.failed_step = failed_step
        self.error = error
        super().__init__(message)


class TaskService:
    def __init__(self, storage_root: Path) -> None:
        self.storage = TaskStorage(storage_root)
        self.runner = TaskRunner(
            storage=self.storage,
            llm_provider=MockLLMProvider(),
            tts_provider=MockTTSProvider(self.storage),
            avatar_renderer=MockAvatarRenderer(self.storage),
            post_processor=MockPostProcessor(self.storage),
        )

    def create_and_run(self, session: Session, payload: TaskCreate) -> VideoTask:
        self._validate_references(session, payload)
        task = VideoTask(**payload.model_dump())
        session.add(task)
        session.commit()
        session.refresh(task)
        task_id = self._require_task_id(task)
        try:
            self.runner.run_task(session, task_id)
        except Exception as exc:
            raise self._task_run_error(session, task_id, exc) from exc
        session.refresh(task)
        return task

    def list_tasks(self, session: Session) -> list[VideoTask]:
        return list(session.exec(select(VideoTask).order_by(VideoTask.created_at.desc())).all())

    def get_task_detail(
        self,
        session: Session,
        task_id: int,
    ) -> tuple[VideoTask, ScriptDraft | None, list[MediaAsset], list[GenerationStepLog]] | None:
        task = session.get(VideoTask, task_id)
        if task is None:
            return None
        script = session.exec(
            select(ScriptDraft)
            .where(ScriptDraft.task_id == task_id)
            .order_by(ScriptDraft.version.desc(), ScriptDraft.id.desc())
        ).first()
        assets = list(
            session.exec(
                select(MediaAsset)
                .where(MediaAsset.task_id == task_id)
                .order_by(MediaAsset.id)
            ).all()
        )
        logs = list(
            session.exec(
                select(GenerationStepLog)
                .where(GenerationStepLog.task_id == task_id)
                .order_by(GenerationStepLog.id)
            ).all()
        )
        return task, script, assets, logs

    def list_humans(self, session: Session) -> list[DigitalHumanProfile]:
        return list(
            session.exec(select(DigitalHumanProfile).order_by(DigitalHumanProfile.id)).all()
        )

    def list_voices(self, session: Session) -> list[VoiceProfile]:
        return list(session.exec(select(VoiceProfile).order_by(VoiceProfile.id)).all())

    def list_templates(self, session: Session) -> list[PostProcessTemplate]:
        return list(
            session.exec(select(PostProcessTemplate).order_by(PostProcessTemplate.id)).all()
        )

    @staticmethod
    def _validate_references(session: Session, payload: TaskCreate) -> None:
        invalid_fields: list[str] = []
        if session.get(DigitalHumanProfile, payload.digital_human_profile_id) is None:
            invalid_fields.append("digital_human_profile_id")
        if session.get(VoiceProfile, payload.voice_profile_id) is None:
            invalid_fields.append("voice_profile_id")
        if session.get(PostProcessTemplate, payload.post_process_template_id) is None:
            invalid_fields.append("post_process_template_id")
        if invalid_fields:
            raise InvalidTaskReferencesError(invalid_fields)

    @staticmethod
    def _task_run_error(session: Session, task_id: int, exc: Exception) -> TaskRunError:
        session.rollback()
        task = session.get(VideoTask, task_id)
        if task is None:
            return TaskRunError(
                task_id=task_id,
                message="Task pipeline failed",
                current_state=TaskState.FAILED,
                failed_step=None,
                error=str(exc),
            )
        if task.current_state != TaskState.FAILED:
            task.current_state = TaskState.FAILED
            task.failed_step = task.failed_step or "unknown"
            session.add(task)
            session.commit()
            session.refresh(task)
        return TaskRunError(
            task_id=task_id,
            message="Task pipeline failed",
            current_state=task.current_state,
            failed_step=task.failed_step,
            error=str(exc),
        )

    @staticmethod
    def _require_task_id(task: VideoTask) -> int:
        if task.id is None:
            raise ValueError("Task must be persisted before running")
        return task.id
