from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlmodel import Session

from app.api.routes import get_task_service
from app.database import get_session
from app.main import create_app
from app.models import TaskState, VideoTask
from app.seed import seed_defaults
from app.services.task_service import TaskService


@pytest.fixture
def api_storage_root(tmp_path: Path) -> Path:
    return tmp_path / "api-storage"


@pytest.fixture
def api_client(
    test_engine: Engine,
    api_storage_root: Path,
) -> Generator[TestClient, None, None]:
    app = create_app(run_startup_db=False)

    def override_get_session() -> Generator[Session, None, None]:
        with Session(test_engine) as session:
            yield session

    def override_get_task_service() -> TaskService:
        return TaskService(api_storage_root)

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_task_service] = override_get_task_service
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_create_task_runs_pipeline_and_returns_completed_task(
    api_client: TestClient,
    api_storage_root: Path,
    session: Session,
) -> None:
    seed_defaults(session)

    response = api_client.post(
        "/api/tasks",
        json={
            "input_mode": "existing_script",
            "raw_input": "This script should become a mock video.",
            "digital_human_profile_id": 1,
            "voice_profile_id": 1,
            "post_process_template_id": 1,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["current_state"] == "completed"
    assert payload["final_video_path"].startswith(str(api_storage_root))
    assert payload["final_video_path"].endswith("final-video.mp4")
    assert payload["cover_path"].endswith("cover.jpg")

    detail_response = api_client.get(f"/api/tasks/{payload['id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["task"]["id"] == payload["id"]
    assert detail["task"]["current_state"] == "completed"
    assert detail["script"]["script_text"] == "This script should become a mock video."
    assert [log["step_name"] for log in detail["logs"]] == [
        "script",
        "tts",
        "avatar_render",
        "post_process",
    ]
    assert [log["status"] for log in detail["logs"]] == ["succeeded"] * 4
    assert {asset["asset_type"] for asset in detail["assets"]} == {
        "audio",
        "raw_video",
        "final_video",
        "cover",
    }
    assets_by_type = {asset["asset_type"]: asset for asset in detail["assets"]}
    assert assets_by_type["audio"]["public_url"].startswith("/api/artifacts/")
    assert assets_by_type["final_video"]["public_url"].startswith("/api/artifacts/")
    assert assets_by_type["cover"]["public_url"].startswith("/api/artifacts/")

    video_response = api_client.get(assets_by_type["final_video"]["public_url"])
    assert video_response.status_code == 200
    assert video_response.headers["content-type"].startswith("video/mp4")
    assert len(video_response.content) > 0

    cover_response = api_client.get(assets_by_type["cover"]["public_url"])
    assert cover_response.status_code == 200
    assert cover_response.headers["content-type"].startswith("image/jpeg")


def test_list_profiles_voices_templates_and_tasks(
    api_client: TestClient,
    session: Session,
) -> None:
    seed_defaults(session)

    humans_response = api_client.get("/api/digital-humans")
    voices_response = api_client.get("/api/voices")
    templates_response = api_client.get("/api/post-process-templates")
    tasks_response = api_client.get("/api/tasks")

    assert humans_response.status_code == 200
    assert voices_response.status_code == 200
    assert templates_response.status_code == 200
    assert tasks_response.status_code == 200

    humans = humans_response.json()
    voices = voices_response.json()
    templates = templates_response.json()
    tasks = tasks_response.json()

    assert humans[0]["name"] == "Default Presenter"
    assert humans[0]["status"] == "active"
    assert voices[0]["name"] == "Default Voice"
    assert voices[0]["style_tags"] == ["neutral", "mandarin"]
    assert templates[0]["name"] == "Default Vertical Video"
    assert templates[0]["subtitle_style"] == {"font_size": 42, "position": "bottom"}
    assert tasks == []


def test_create_task_rejects_invalid_reference_ids(
    api_client: TestClient,
    session: Session,
) -> None:
    seed_defaults(session)

    response = api_client.post(
        "/api/tasks",
        json={
            "input_mode": "existing_script",
            "raw_input": "This task references missing profiles.",
            "digital_human_profile_id": 101,
            "voice_profile_id": 102,
            "post_process_template_id": 103,
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == {
        "message": "Invalid task references",
        "fields": [
            "digital_human_profile_id",
            "voice_profile_id",
            "post_process_template_id",
        ],
    }
    assert api_client.get("/api/tasks").json() == []


def test_create_task_rejects_whitespace_raw_input(
    api_client: TestClient,
    session: Session,
) -> None:
    seed_defaults(session)

    response = api_client.post(
        "/api/tasks",
        json={
            "input_mode": "existing_script",
            "raw_input": "   \r\n\t  ",
            "digital_human_profile_id": 1,
            "voice_profile_id": 1,
            "post_process_template_id": 1,
        },
    )

    assert response.status_code == 422
    assert api_client.get("/api/tasks").json() == []


def test_create_task_returns_task_context_when_runner_fails(
    api_client: TestClient,
    api_storage_root: Path,
    session: Session,
) -> None:
    seed_defaults(session)

    failing_service = TaskService(api_storage_root)
    failing_service.runner = FailingRunner()
    api_client.app.dependency_overrides[get_task_service] = lambda: failing_service

    response = api_client.post(
        "/api/tasks",
        json={
            "input_mode": "existing_script",
            "raw_input": "This task fails during the mock pipeline.",
            "digital_human_profile_id": 1,
            "voice_profile_id": 1,
            "post_process_template_id": 1,
        },
    )

    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/json")
    detail = response.json()["detail"]
    assert detail == {
        "task_id": 1,
        "message": "Task pipeline failed",
        "current_state": "failed",
        "failed_step": "post_process",
        "error": "post processor unavailable",
    }


def test_get_missing_task_returns_404(api_client: TestClient) -> None:
    response = api_client.get("/api/tasks/404")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


class FailingRunner:
    def run_task(self, session: Session, task_id: int) -> None:
        task = session.get(VideoTask, task_id)
        assert task is not None
        task.current_state = TaskState.FAILED
        task.failed_step = "post_process"
        session.add(task)
        session.commit()
        raise RuntimeError("post processor unavailable")
