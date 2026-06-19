from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.config import get_settings
from app.database import get_session
from app.schemas import (
    DigitalHumanRead,
    GenerationStepLogRead,
    MediaAssetRead,
    ScriptDraftRead,
    TaskCreate,
    TaskDetail,
    TaskRead,
    TemplateRead,
    VoiceRead,
)
from app.services.task_service import InvalidTaskReferencesError, TaskRunError, TaskService

router = APIRouter(prefix="/api")


def get_task_service() -> TaskService:
    return TaskService(get_settings().storage_root)


SessionDep = Annotated[Session, Depends(get_session)]
TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]


@router.get("/digital-humans", response_model=list[DigitalHumanRead])
def list_digital_humans(
    session: SessionDep,
    service: TaskServiceDep,
) -> list[DigitalHumanRead]:
    return [DigitalHumanRead.from_model(item) for item in service.list_humans(session)]


@router.get("/voices", response_model=list[VoiceRead])
def list_voices(
    session: SessionDep,
    service: TaskServiceDep,
) -> list[VoiceRead]:
    return [VoiceRead.from_model(item) for item in service.list_voices(session)]


@router.get("/post-process-templates", response_model=list[TemplateRead])
def list_templates(
    session: SessionDep,
    service: TaskServiceDep,
) -> list[TemplateRead]:
    return [TemplateRead.from_model(item) for item in service.list_templates(session)]


@router.get("/tasks", response_model=list[TaskRead])
def list_tasks(
    session: SessionDep,
    service: TaskServiceDep,
) -> list[TaskRead]:
    return [TaskRead.from_model(task) for task in service.list_tasks(session)]


@router.post("/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    session: SessionDep,
    service: TaskServiceDep,
) -> TaskRead:
    try:
        task = service.create_and_run(session, payload)
    except InvalidTaskReferencesError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"message": str(exc), "fields": exc.fields},
        ) from exc
    except TaskRunError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "task_id": exc.task_id,
                "message": exc.message,
                "current_state": exc.current_state.value,
                "failed_step": exc.failed_step,
                "error": exc.error,
            },
        ) from exc
    return TaskRead.from_model(task)


@router.get("/tasks/{task_id}", response_model=TaskDetail)
def get_task(
    task_id: int,
    session: SessionDep,
    service: TaskServiceDep,
) -> TaskDetail:
    detail = service.get_task_detail(session, task_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    task, script, assets, logs = detail
    return TaskDetail(
        task=TaskRead.from_model(task),
        script=ScriptDraftRead.from_model(script) if script is not None else None,
        assets=[MediaAssetRead.from_model(asset) for asset in assets],
        logs=[GenerationStepLogRead.from_model(log) for log in logs],
    )
