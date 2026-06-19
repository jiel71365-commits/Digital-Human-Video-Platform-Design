import subprocess
import sys
import textwrap
from pathlib import Path

from fastapi import Depends
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.database import get_session
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
from app.seed import seed_defaults

SESSION_DEPENDENCY = Depends(get_session)


def test_create_db_and_tables_registers_models_without_prior_model_import(tmp_path: Path) -> None:
    db_path = tmp_path / "metadata.db"
    code = textwrap.dedent(
        f"""
        from sqlalchemy import inspect

        from app import database

        database.engine = database.make_engine("sqlite:///{db_path.as_posix()}")
        database.create_db_and_tables()
        print("\\n".join(sorted(inspect(database.engine).get_table_names())))
        """
    )

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=Path(__file__).parents[1],
        capture_output=True,
        check=True,
        text=True,
    )

    tables = set(result.stdout.splitlines())

    assert {
        "digitalhumanprofile",
        "generationsteplog",
        "mediaasset",
        "postprocesstemplate",
        "scriptdraft",
        "videotask",
        "voiceprofile",
    }.issubset(tables)


def test_client_dependency_override_uses_fresh_session_per_request(client) -> None:
    request_sessions: list[Session] = []

    @client.app.get("/session-identity")
    def session_identity(session: Session = SESSION_DEPENDENCY) -> dict[str, bool]:
        request_sessions.append(session)
        return {"ok": True}

    assert client.get("/session-identity").json() == {"ok": True}
    assert client.get("/session-identity").json() == {"ok": True}

    assert request_sessions[0] is not request_sessions[1]


def test_models_define_expected_foreign_keys(session: Session) -> None:
    inspector = inspect(session.get_bind())

    foreign_keys = {
        table: {
            (fk["constrained_columns"][0], fk["referred_table"], fk["referred_columns"][0])
            for fk in inspector.get_foreign_keys(table)
        }
        for table in (
            VideoTask.__tablename__,
            ScriptDraft.__tablename__,
            MediaAsset.__tablename__,
            GenerationStepLog.__tablename__,
        )
    }

    assert foreign_keys[VideoTask.__tablename__] == {
        ("digital_human_profile_id", DigitalHumanProfile.__tablename__, "id"),
        ("voice_profile_id", VoiceProfile.__tablename__, "id"),
        ("post_process_template_id", PostProcessTemplate.__tablename__, "id"),
    }
    assert foreign_keys[ScriptDraft.__tablename__] == {
        ("task_id", VideoTask.__tablename__, "id"),
    }
    assert foreign_keys[MediaAsset.__tablename__] == {
        ("task_id", VideoTask.__tablename__, "id"),
    }
    assert foreign_keys[GenerationStepLog.__tablename__] == {
        ("task_id", VideoTask.__tablename__, "id"),
    }


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
    seed_defaults(session)
    human = session.exec(select(DigitalHumanProfile)).one()
    voice = session.exec(select(VoiceProfile)).one()
    template = session.exec(select(PostProcessTemplate)).one()

    task = VideoTask(
        input_mode="existing_script",
        raw_input="Hello from a test script.",
        digital_human_profile_id=human.id,
        voice_profile_id=voice.id,
        post_process_template_id=template.id,
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    assert task.id is not None
    assert task.current_state == TaskState.DRAFT
    assert task.failed_step is None


def test_video_task_rejects_missing_parent_records(session: Session) -> None:
    task = VideoTask(
        input_mode="existing_script",
        raw_input="This task points at missing parent rows.",
        digital_human_profile_id=404,
        voice_profile_id=405,
        post_process_template_id=406,
    )
    session.add(task)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
    else:
        raise AssertionError("Expected missing parent rows to raise IntegrityError")
