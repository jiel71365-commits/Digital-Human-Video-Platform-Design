from fastapi.testclient import TestClient
from sqlmodel import Session

from app.seed import seed_defaults


def test_create_task_runs_pipeline_and_returns_completed_task(
    client: TestClient,
    session: Session,
) -> None:
    seed_defaults(session)

    response = client.post(
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
    assert payload["final_video_path"].endswith("final-video.mp4")
    assert payload["cover_path"].endswith("cover.txt")

    detail_response = client.get(f"/api/tasks/{payload['id']}")
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


def test_list_profiles_voices_templates_and_tasks(
    client: TestClient,
    session: Session,
) -> None:
    seed_defaults(session)

    humans_response = client.get("/api/digital-humans")
    voices_response = client.get("/api/voices")
    templates_response = client.get("/api/post-process-templates")
    tasks_response = client.get("/api/tasks")

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


def test_get_missing_task_returns_404(client: TestClient) -> None:
    response = client.get("/api/tasks/404")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"
