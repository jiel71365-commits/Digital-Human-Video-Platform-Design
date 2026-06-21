from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlmodel import Session

from app.config import get_settings
from app.database import get_session
from app.models import DigitalHumanProfile
from app.schemas import (
    DigitalHumanRead,
    GenerationStepLogRead,
    MediaAssetRead,
    RendererRuntimeStatuses,
    ScriptDraftRead,
    TaskCreate,
    TaskDetail,
    TaskRead,
    TemplateRead,
    VoiceRead,
    Wav2LipRuntimeStatus,
)
from app.services.runtime_status import get_musetalk_runtime_status, get_wav2lip_runtime_status
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


@router.post("/digital-humans/{profile_id}/source-media", response_model=DigitalHumanRead)
def upload_digital_human_source_media(
    profile_id: int,
    file: UploadFile,
    session: SessionDep,
    service: TaskServiceDep,
) -> DigitalHumanRead:
    if not _is_supported_source_media(file.filename or "", file.content_type):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Unsupported source media type",
        )
    profile = service.update_digital_human_source_media(
        session,
        profile_id,
        file.filename or "source-media",
        file.file,
    )
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Digital human not found")
    return DigitalHumanRead.from_model(profile)


@router.get("/digital-humans/{profile_id}/source-media")
def get_digital_human_source_media(
    profile_id: int,
    session: SessionDep,
) -> FileResponse:
    profile = session.get(DigitalHumanProfile, profile_id)
    if profile is None or profile.source_media_path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source media not found")
    path = Path(profile.source_media_path)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source media not found")
    return FileResponse(path)


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


@router.get("/runtime/wav2lip", response_model=Wav2LipRuntimeStatus)
def get_wav2lip_runtime() -> Wav2LipRuntimeStatus:
    return get_wav2lip_runtime_status(get_settings())


@router.get("/runtime/renderers", response_model=RendererRuntimeStatuses)
def get_renderer_runtimes() -> RendererRuntimeStatuses:
    settings = get_settings()
    musetalk = get_musetalk_runtime_status(settings)
    wav2lip = get_wav2lip_runtime_status(settings)
    active_renderer = (
        "musetalk" if musetalk.available else "wav2lip" if wav2lip.available else "fallback"
    )
    return RendererRuntimeStatuses(
        active_renderer=active_renderer,
        renderers={
            "musetalk": musetalk,
            "wav2lip": wav2lip,
        },
    )


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
        assets=[
            MediaAssetRead.from_model(asset, _public_artifact_url(asset.file_path))
            for asset in assets
        ],
        logs=[GenerationStepLogRead.from_model(log) for log in logs],
    )


@router.get("/artifacts/{task_id}/{group}/{filename}")
def get_artifact(
    task_id: int,
    group: str,
    filename: str,
    service: TaskServiceDep,
) -> FileResponse:
    try:
        artifact_path = service.storage.artifact_path(task_id, group, filename)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found",
        ) from exc

    if not artifact_path.exists() or not artifact_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    return FileResponse(artifact_path)


def _public_artifact_url(file_path: str) -> str | None:
    parts = file_path.replace("\\", "/").split("/")
    try:
        task_index = parts.index("tasks")
    except ValueError:
        return None
    artifact_parts = parts[task_index + 1 :]
    if len(artifact_parts) != 3:
        return None
    task_id, group, filename = artifact_parts
    return f"/api/artifacts/{task_id}/{group}/{filename}"


def _is_supported_source_media(filename: str, content_type: str | None) -> bool:
    suffix = Path(filename).suffix.lower()
    if suffix not in {".mp4", ".mov", ".jpg", ".jpeg", ".png"}:
        return False
    if content_type is None:
        return True
    return content_type.startswith("video/") or content_type.startswith("image/")
