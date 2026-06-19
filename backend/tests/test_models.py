from sqlmodel import Session, select

from app.models import (
    DigitalHumanProfile,
    PostProcessTemplate,
    TaskState,
    VideoTask,
    VoiceProfile,
)
from app.seed import seed_defaults


def test_seed_defaults_creates_profile_voice_and_template(session: Session) -> None:
    seed_defaults(session)

    humans = session.exec(select(DigitalHumanProfile)).all()
    voices = session.exec(select(VoiceProfile)).all()
    templates = session.exec(select(PostProcessTemplate)).all()

    assert len(humans) == 1
    assert humans[0].name == "Default Presenter"
    assert humans[0].renderer_adapter_key == "mock-avatar"

    assert len(voices) == 1
    assert voices[0].name == "Default Voice"
    assert voices[0].provider_key == "mock-tts"

    assert len(templates) == 1
    assert templates[0].name == "Default Vertical Video"
    assert templates[0].cover_strategy == "first_frame"


def test_video_task_defaults_to_draft(session: Session) -> None:
    task = VideoTask(
        input_mode="existing_script",
        raw_input="Hello from a test script.",
        digital_human_profile_id=1,
        voice_profile_id=1,
        post_process_template_id=1,
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    assert task.id is not None
    assert task.current_state == TaskState.DRAFT
    assert task.failed_step is None
