import subprocess
import wave
from pathlib import Path
from typing import runtime_checkable

import cv2
import imageio_ffmpeg
import pytest
from sqlalchemy import event
from sqlmodel import Session, select

from app.models import (
    DigitalHumanProfile,
    GenerationStepLog,
    MediaAsset,
    PostProcessTemplate,
    ScriptDraft,
    StepStatus,
    TaskInputMode,
    TaskState,
    VideoTask,
    VoiceProfile,
)
from app.providers.base import (
    AudioResult,
    AvatarRenderer,
    LLMProvider,
    PostProcessor,
    RenderResult,
    TTSProvider,
)
from app.providers.mock import (
    MockAvatarRenderer,
    MockLLMProvider,
    MockPostProcessor,
    MockTTSProvider,
)
from app.seed import seed_defaults
from app.services.task_runner import TaskRunner
from app.storage import TaskStorage


def test_task_storage_creates_task_directories_and_artifact_paths(tmp_path: Path) -> None:
    storage = TaskStorage(tmp_path)

    task_dir = storage.task_dir(12)
    artifact = storage.artifact_path(12, "audio", "speech.txt")

    assert task_dir == tmp_path / "tasks" / "12"
    assert task_dir.exists()
    assert artifact == tmp_path / "tasks" / "12" / "audio" / "speech.txt"
    assert artifact.parent.exists()


@pytest.mark.parametrize(
    ("group", "filename"),
    [
        ("..", "x.txt"),
        ("audio/../unsafe", "x.txt"),
        ("audio//unsafe", "x.txt"),
        ("audio\\..\\unsafe", "x.txt"),
        ("audio\\\\unsafe", "x.txt"),
        ("audio", "../x.txt"),
        ("audio", "..\\x.txt"),
        ("", "x.txt"),
        ("   ", "x.txt"),
        (".", "x.txt"),
        ("audio", ""),
        ("audio", "   "),
        ("audio", "."),
    ],
)
def test_task_storage_rejects_unsafe_artifact_path_segments(
    tmp_path: Path,
    group: str,
    filename: str,
) -> None:
    storage = TaskStorage(tmp_path)

    with pytest.raises(ValueError, match="Invalid artifact"):
        storage.artifact_path(12, group, filename)


def test_mock_providers_create_artifacts(tmp_path: Path) -> None:
    storage = TaskStorage(tmp_path)
    llm = MockLLMProvider()
    tts = MockTTSProvider(storage)
    avatar = MockAvatarRenderer(storage)
    post_processor = MockPostProcessor(storage)

    script = llm.prepare_script(
        task_id=12,
        input_mode=TaskInputMode.TOPIC,
        raw_input="  夏季防晒新品  ",
    )
    audio = tts.synthesize(task_id=12, script_text=script.script_text, voice_key="default")
    raw_video = avatar.render(
        task_id=12,
        script_text=script.script_text,
        audio_path=audio.audio_path,
        profile_key="default-presenter",
    )
    final = post_processor.process(
        task_id=12,
        raw_video_path=raw_video.video_path,
        script_text=script.script_text,
        template_key="default-vertical",
    )

    assert "夏季防晒新品" in script.script_text
    assert script.estimated_duration_seconds > 0
    assert script.structured_segments == [{"index": 1, "text": script.script_text}]

    assert audio.audio_path == tmp_path / "tasks" / "12" / "audio" / "speech.wav"
    assert _wav_duration(audio.audio_path) > 0
    assert audio.duration_seconds == pytest.approx(_wav_duration(audio.audio_path), abs=0.01)
    assert audio.timing == [
        {"start": 0.0, "end": audio.duration_seconds, "text": script.script_text}
    ]

    assert raw_video.video_path == tmp_path / "tasks" / "12" / "render" / "raw-video.mp4"
    assert _video_dimensions(raw_video.video_path) == (720, 1280)
    assert raw_video.duration_seconds == pytest.approx(audio.duration_seconds, abs=0.1)

    assert final.final_video_path == tmp_path / "tasks" / "12" / "final" / "final-video.mp4"
    assert final.cover_path == tmp_path / "tasks" / "12" / "final" / "cover.jpg"
    assert final.final_video_path.exists()
    assert final.final_video_path.stat().st_size > 0
    assert _video_dimensions(final.final_video_path) == (720, 1280)
    assert _ffmpeg_probe_output(final.final_video_path).count("Audio:") >= 1
    assert final.cover_path.exists()


def test_mock_post_processor_creates_playable_mp4(tmp_path: Path) -> None:
    storage = TaskStorage(tmp_path)
    tts = MockTTSProvider(storage)
    avatar = MockAvatarRenderer(storage)
    audio = tts.synthesize(
        task_id=12,
        script_text="Playable local video test.",
        voice_key="default",
    )
    raw_video = avatar.render(
        task_id=12,
        audio_path=audio.audio_path,
        profile_key="default-presenter",
        script_text="Playable local video test.",
    )
    post_processor = MockPostProcessor(storage)

    result = post_processor.process(
        task_id=12,
        raw_video_path=raw_video.video_path,
        script_text="Playable local video test.",
        template_key="default-vertical",
    )

    capture = cv2.VideoCapture(str(result.final_video_path))
    try:
        assert capture.isOpened()
        assert int(capture.get(cv2.CAP_PROP_FRAME_COUNT)) > 0
        assert int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)) == 720
        assert int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) == 1280
        assert "Audio:" in _ffmpeg_probe_output(result.final_video_path)
    finally:
        capture.release()


def test_mock_tts_provider_falls_back_when_sapi_writes_empty_wav(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    storage = TaskStorage(tmp_path)

    def write_empty_wav(path: Path, script_text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(16_000)

    monkeypatch.setattr("app.providers.mock._write_sapi_wav", write_empty_wav)

    result = MockTTSProvider(storage).synthesize(
        task_id=13,
        script_text="SAPI can silently produce an empty wav.",
        voice_key="default",
    )

    assert result.audio_path == tmp_path / "tasks" / "13" / "audio" / "speech.wav"
    assert result.duration_seconds > 0
    assert _wav_duration(result.audio_path) > 0
    assert result.timing == [
        {"start": 0.0, "end": result.duration_seconds, "text": result.timing[0]["text"]}
    ]


def test_mock_avatar_renderer_rejects_missing_audio_artifact(tmp_path: Path) -> None:
    renderer = MockAvatarRenderer(TaskStorage(tmp_path))

    with pytest.raises(FileNotFoundError, match="Audio artifact does not exist"):
        renderer.render(
            task_id=12,
            audio_path=tmp_path / "missing-speech.txt",
            profile_key="default-presenter",
            script_text="script",
        )


def test_mock_post_processor_rejects_missing_raw_video_artifact(tmp_path: Path) -> None:
    post_processor = MockPostProcessor(TaskStorage(tmp_path))

    with pytest.raises(FileNotFoundError, match="Raw video artifact does not exist"):
        post_processor.process(
            task_id=12,
            raw_video_path=tmp_path / "missing-raw-video.txt",
            script_text="script",
            template_key="default-vertical",
        )


def test_mock_llm_normalizes_existing_script_and_generates_chinese_prompts() -> None:
    llm = MockLLMProvider()

    existing_script = llm.prepare_script(
        task_id=1,
        input_mode=TaskInputMode.EXISTING_SCRIPT,
        raw_input="  第一行\r\n\r\n 第二行  ",
    )
    topic_script = llm.prepare_script(
        task_id=2,
        input_mode=TaskInputMode.TOPIC,
        raw_input="智能水杯",
    )
    reference_script = llm.prepare_script(
        task_id=3,
        input_mode=TaskInputMode.REFERENCE_VIDEO,
        raw_input="竞品视频链接",
    )

    assert existing_script.script_text == "第一行 第二行"
    assert "围绕智能水杯" in topic_script.script_text
    assert "参考竞品视频链接" in reference_script.script_text


def test_mock_providers_satisfy_provider_protocols(tmp_path: Path) -> None:
    runtime_llm = runtime_checkable(LLMProvider)
    runtime_tts = runtime_checkable(TTSProvider)
    runtime_avatar = runtime_checkable(AvatarRenderer)
    runtime_post_processor = runtime_checkable(PostProcessor)

    storage = TaskStorage(tmp_path)

    assert isinstance(MockLLMProvider(), runtime_llm)
    assert isinstance(MockTTSProvider(storage), runtime_tts)
    assert isinstance(MockAvatarRenderer(storage), runtime_avatar)
    assert isinstance(MockPostProcessor(storage), runtime_post_processor)


def test_task_runner_completes_existing_script_task(session: Session, tmp_path: Path) -> None:
    task = _create_valid_task(session, raw_input="A complete script for the MVP.")
    task_id = _require_task_id(task)
    observed_states: list[TaskState] = []

    def capture_state_transition(
        observed_session: Session,
        _flush_context: object,
        _instances: object,
    ) -> None:
        for obj in observed_session.dirty:
            if isinstance(obj, VideoTask) and obj.id == task_id:
                observed_states.append(obj.current_state)

    event.listen(session, "before_flush", capture_state_transition)
    storage = TaskStorage(tmp_path)
    runner = TaskRunner(
        storage=storage,
        llm_provider=MockLLMProvider(),
        tts_provider=MockTTSProvider(storage),
        avatar_renderer=MockAvatarRenderer(storage),
        post_processor=MockPostProcessor(storage),
    )

    try:
        runner.run_task(session, task_id)
    finally:
        event.remove(session, "before_flush", capture_state_transition)
    session.refresh(task)

    scripts = session.exec(select(ScriptDraft).where(ScriptDraft.task_id == task_id)).all()
    assets = session.exec(select(MediaAsset).where(MediaAsset.task_id == task_id)).all()
    logs = session.exec(
        select(GenerationStepLog)
        .where(GenerationStepLog.task_id == task_id)
        .order_by(GenerationStepLog.id)
    ).all()
    assets_by_type = {asset.asset_type: asset for asset in assets}

    assert observed_states == [
        TaskState.QUEUED,
        TaskState.SCRIPT_READY,
        TaskState.AUDIO_READY,
        TaskState.RENDERED,
        TaskState.POST_PROCESSED,
        TaskState.COMPLETED,
    ]
    assert task.current_state == TaskState.COMPLETED
    assert task.failed_step is None
    assert task.final_video_path == str(
        tmp_path / "tasks" / str(task_id) / "final" / "final-video.mp4"
    )
    assert task.cover_path == str(tmp_path / "tasks" / str(task_id) / "final" / "cover.jpg")

    assert len(scripts) == 1
    assert scripts[0].script_text == "A complete script for the MVP."
    assert scripts[0].source_mode == TaskInputMode.EXISTING_SCRIPT.value

    assert len(assets) == 4
    assert set(assets_by_type) == {"audio", "raw_video", "final_video", "cover"}
    assert assets_by_type["audio"].file_path == str(
        tmp_path / "tasks" / str(task_id) / "audio" / "speech.wav"
    )
    assert assets_by_type["raw_video"].file_path == str(
        tmp_path / "tasks" / str(task_id) / "render" / "raw-video.mp4"
    )
    assert assets_by_type["final_video"].file_path == task.final_video_path
    assert assets_by_type["cover"].file_path == task.cover_path

    assert [log.step_name for log in logs] == ["script", "tts", "avatar_render", "post_process"]
    assert [log.status for log in logs] == [StepStatus.SUCCEEDED] * 4
    for log in logs:
        assert log.started_at is not None
        assert log.finished_at is not None
        assert log.duration_seconds is not None
        assert log.duration_seconds >= 0
        assert log.technical_log


def test_task_runner_passes_digital_human_source_media_to_avatar_renderer(
    session: Session,
    tmp_path: Path,
) -> None:
    task = _create_valid_task(session, raw_input="A script with custom presenter media.")
    task_id = _require_task_id(task)
    human = session.get(DigitalHumanProfile, task.digital_human_profile_id)
    assert human is not None
    source_media_path = tmp_path / "presenter.mp4"
    source_media_path.write_bytes(b"presenter")
    human.source_media_path = str(source_media_path)
    session.add(human)
    session.commit()
    storage = TaskStorage(tmp_path)
    avatar_renderer = RecordingAvatarRenderer(storage)
    runner = TaskRunner(
        storage=storage,
        llm_provider=MockLLMProvider(),
        tts_provider=MockTTSProvider(storage),
        avatar_renderer=avatar_renderer,
        post_processor=MockPostProcessor(storage),
    )

    runner.run_task(session, task_id)

    assert avatar_renderer.calls == [
        {
            "task_id": task_id,
            "profile_key": "mock-avatar",
            "source_media_path": source_media_path,
        }
    ]


def test_task_runner_raises_value_error_for_missing_task(tmp_path: Path, session: Session) -> None:
    storage = TaskStorage(tmp_path)
    runner = TaskRunner(
        storage=storage,
        llm_provider=MockLLMProvider(),
        tts_provider=MockTTSProvider(storage),
        avatar_renderer=MockAvatarRenderer(storage),
        post_processor=MockPostProcessor(storage),
    )

    with pytest.raises(ValueError, match="Task 404 does not exist"):
        runner.run_task(session, 404)


def test_task_runner_marks_task_failed_when_provider_raises(
    session: Session,
    tmp_path: Path,
) -> None:
    task = _create_valid_task(session, raw_input="A script that cannot be voiced.")
    task_id = _require_task_id(task)
    storage = TaskStorage(tmp_path)
    runner = TaskRunner(
        storage=storage,
        llm_provider=MockLLMProvider(),
        tts_provider=FailingTTSProvider(),
        avatar_renderer=MockAvatarRenderer(storage),
        post_processor=MockPostProcessor(storage),
    )

    with pytest.raises(RuntimeError, match="tts provider unavailable"):
        runner.run_task(session, task_id)
    session.refresh(task)

    logs = session.exec(
        select(GenerationStepLog)
        .where(GenerationStepLog.task_id == task_id)
        .order_by(GenerationStepLog.id)
    ).all()
    failed_log = logs[-1]

    assert task.current_state == TaskState.FAILED
    assert task.failed_step == "tts"
    assert [log.step_name for log in logs] == ["script", "tts"]
    assert logs[0].status == StepStatus.SUCCEEDED
    assert failed_log.step_name == "tts"
    assert failed_log.status == StepStatus.FAILED
    assert failed_log.finished_at is not None
    assert failed_log.duration_seconds is not None
    assert failed_log.error_code == "tts_failed"
    assert failed_log.user_message == "tts step failed"
    assert "tts provider unavailable" in (failed_log.technical_log or "")


def test_task_runner_rerun_clears_previous_outputs_and_failed_step(
    session: Session,
    tmp_path: Path,
) -> None:
    task = _create_valid_task(session, raw_input="A script that succeeds on retry.")
    task_id = _require_task_id(task)
    storage = TaskStorage(tmp_path)
    failing_runner = TaskRunner(
        storage=storage,
        llm_provider=MockLLMProvider(),
        tts_provider=FailingTTSProvider(),
        avatar_renderer=MockAvatarRenderer(storage),
        post_processor=MockPostProcessor(storage),
    )

    with pytest.raises(RuntimeError, match="tts provider unavailable"):
        failing_runner.run_task(session, task_id)
    session.refresh(task)

    assert task.current_state == TaskState.FAILED
    assert task.failed_step == "tts"

    successful_runner = TaskRunner(
        storage=storage,
        llm_provider=MockLLMProvider(),
        tts_provider=MockTTSProvider(storage),
        avatar_renderer=MockAvatarRenderer(storage),
        post_processor=MockPostProcessor(storage),
    )

    successful_runner.run_task(session, task_id)
    session.refresh(task)

    scripts = session.exec(select(ScriptDraft).where(ScriptDraft.task_id == task_id)).all()
    assets = session.exec(select(MediaAsset).where(MediaAsset.task_id == task_id)).all()
    logs = session.exec(
        select(GenerationStepLog)
        .where(GenerationStepLog.task_id == task_id)
        .order_by(GenerationStepLog.id)
    ).all()

    assert task.current_state == TaskState.COMPLETED
    assert task.failed_step is None
    assert task.final_video_path == str(
        tmp_path / "tasks" / str(task_id) / "final" / "final-video.mp4"
    )
    assert task.cover_path == str(tmp_path / "tasks" / str(task_id) / "final" / "cover.jpg")
    assert len(scripts) == 1
    assert len(assets) == 4
    assert len(logs) == 4
    assert [log.step_name for log in logs] == ["script", "tts", "avatar_render", "post_process"]
    assert [log.status for log in logs] == [StepStatus.SUCCEEDED] * 4


class FailingTTSProvider:
    def synthesize(self, task_id: int, script_text: str, voice_key: str) -> AudioResult:
        raise RuntimeError("tts provider unavailable")


class RecordingAvatarRenderer:
    def __init__(self, storage: TaskStorage) -> None:
        self.storage = storage
        self.calls: list[dict[str, object]] = []

    def render(
        self,
        task_id: int,
        audio_path: Path,
        profile_key: str,
        script_text: str = "",
        source_media_path: Path | None = None,
    ) -> RenderResult:
        self.calls.append(
            {
                "task_id": task_id,
                "profile_key": profile_key,
                "source_media_path": source_media_path,
            }
        )
        return MockAvatarRenderer(self.storage).render(
            task_id=task_id,
            audio_path=audio_path,
            profile_key=profile_key,
            script_text=script_text,
        )


def _create_valid_task(
    session: Session,
    raw_input: str,
    input_mode: TaskInputMode = TaskInputMode.EXISTING_SCRIPT,
) -> VideoTask:
    seed_defaults(session)
    human = session.exec(select(DigitalHumanProfile)).first()
    voice = session.exec(select(VoiceProfile)).first()
    template = session.exec(select(PostProcessTemplate)).first()
    assert human is not None
    assert human.id is not None
    assert voice is not None
    assert voice.id is not None
    assert template is not None
    assert template.id is not None

    task = VideoTask(
        input_mode=input_mode,
        raw_input=raw_input,
        digital_human_profile_id=human.id,
        voice_profile_id=voice.id,
        post_process_template_id=template.id,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def _require_task_id(task: VideoTask) -> int:
    assert task.id is not None
    return task.id


def _wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as audio:
        return audio.getnframes() / audio.getframerate()


def _video_dimensions(path: Path) -> tuple[int, int]:
    capture = cv2.VideoCapture(str(path))
    try:
        assert capture.isOpened()
        return (
            int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        )
    finally:
        capture.release()


def _ffmpeg_probe_output(path: Path) -> str:
    completed = subprocess.run(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-i", str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stderr
