from pathlib import Path

from sqlmodel import Session, select

from app.models import (
    DigitalHumanProfile,
    GenerationStepLog,
    MediaAsset,
    PostProcessTemplate,
    ScriptDraft,
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
        task = VideoTask(**payload.model_dump())
        session.add(task)
        session.commit()
        session.refresh(task)
        self.runner.run_task(session, self._require_task_id(task))
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
    def _require_task_id(task: VideoTask) -> int:
        if task.id is None:
            raise ValueError("Task must be persisted before running")
        return task.id
