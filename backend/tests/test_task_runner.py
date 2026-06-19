from pathlib import Path
from typing import runtime_checkable

from app.models import TaskInputMode
from app.providers.base import (
    AvatarRenderer,
    LLMProvider,
    PostProcessor,
    TTSProvider,
)
from app.providers.mock import (
    MockAvatarRenderer,
    MockLLMProvider,
    MockPostProcessor,
    MockTTSProvider,
)
from app.storage import TaskStorage


def test_task_storage_creates_task_directories_and_sanitizes_artifacts(tmp_path: Path) -> None:
    storage = TaskStorage(tmp_path)

    task_dir = storage.task_dir(12)
    artifact = storage.artifact_path(12, "audio/../unsafe", "speech\\take.txt")

    assert task_dir == tmp_path / "tasks" / "12"
    assert task_dir.exists()
    assert artifact == tmp_path / "tasks" / "12" / "audio_.._unsafe" / "speech_take.txt"
    assert artifact.parent.exists()


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

    assert audio.audio_path == tmp_path / "tasks" / "12" / "audio" / "speech.txt"
    assert audio.audio_path.read_text(encoding="utf-8").startswith("voice=default")
    assert audio.duration_seconds == script.estimated_duration_seconds
    assert audio.timing == [
        {"start": 0.0, "end": audio.duration_seconds, "text": script.script_text}
    ]

    assert raw_video.video_path == tmp_path / "tasks" / "12" / "render" / "raw-video.txt"
    assert "profile=default-presenter" in raw_video.video_path.read_text(encoding="utf-8")
    assert raw_video.duration_seconds == audio.duration_seconds

    assert final.final_video_path == tmp_path / "tasks" / "12" / "final" / "final-video.mp4"
    assert final.cover_path == tmp_path / "tasks" / "12" / "final" / "cover.txt"
    assert "template=default-vertical" in final.final_video_path.read_text(encoding="utf-8")
    assert "cover for task 12" in final.cover_path.read_text(encoding="utf-8")


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
