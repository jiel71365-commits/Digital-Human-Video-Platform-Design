# Digital Human Video Platform MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first runnable MVP skeleton for the digital human video platform: FastAPI backend, SQLite persistence, serial mock generation pipeline, local storage, and a Web management UI.

**Architecture:** The MVP uses a Python FastAPI backend with SQLModel/SQLite, a serial in-process task runner, provider interfaces with mock implementations, and a React/Vite frontend. The first increment proves the full product workflow using generated placeholder artifacts so later plans can replace mock LLM, TTS, avatar rendering, and post-processing providers with real implementations.

**Tech Stack:** Python 3.11+, FastAPI, SQLModel, pytest, React, Vite, TypeScript, Vitest, Playwright-compatible browser UI, local filesystem storage.

---

## Scope

This plan implements the first executable increment of the approved design:

- Web backend.
- Database schema.
- Local storage layout.
- Task state machine.
- Provider interfaces.
- Mock LLM/TTS/avatar/post-processing providers.
- Serial task execution.
- REST API for profiles, voices, tasks, logs, and assets.
- Web UI for dashboard, task creation, profile lists, voice lists, and task detail.
- Automated tests for core backend behavior and frontend UI state.

This plan intentionally does not implement real cloud LLM, real TTS, real LiveTalking/Wav2Lip, FFmpeg composition, reference link crawling, or livestreaming. Those are later provider-replacement plans after this skeleton is stable.

## File Structure

Create this structure:

```text
backend/
  app/
    __init__.py
    main.py
    config.py
    database.py
    models.py
    schemas.py
    storage.py
    seed.py
    api/
      __init__.py
      routes.py
    providers/
      __init__.py
      base.py
      mock.py
    services/
      __init__.py
      task_runner.py
      task_service.py
  tests/
    conftest.py
    test_models.py
    test_task_runner.py
    test_api_tasks.py
  pyproject.toml
  README.md
frontend/
  index.html
  package.json
  tsconfig.json
  tsconfig.node.json
  vite.config.ts
  vitest.config.ts
  src/
    main.tsx
    App.tsx
    api.ts
    types.ts
    styles.css
    components/
      Layout.tsx
      StatusPill.tsx
      TaskForm.tsx
      TaskList.tsx
      TaskDetail.tsx
      ProfileList.tsx
      VoiceList.tsx
  tests/
    App.test.tsx
.gitignore
README.md
```

Responsibilities:

- `backend/app/models.py`: SQLModel database tables and enums.
- `backend/app/schemas.py`: API request/response models.
- `backend/app/storage.py`: safe local storage paths and artifact creation helpers.
- `backend/app/providers/base.py`: provider protocols and result dataclasses.
- `backend/app/providers/mock.py`: deterministic mock providers used by tests and MVP demo.
- `backend/app/services/task_runner.py`: serial pipeline state machine.
- `backend/app/services/task_service.py`: task creation, retry, listing, and profile lookup.
- `backend/app/api/routes.py`: FastAPI routes.
- `frontend/src/api.ts`: typed API client.
- `frontend/src/App.tsx`: top-level page state and routing-lite navigation.
- `frontend/src/components/*`: focused UI components.

## Task 1: Repository Scaffold And Backend Tooling

**Files:**
- Create: `.gitignore`
- Create: `README.md`
- Create: `backend/pyproject.toml`
- Create: `backend/README.md`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_health.py`

- [ ] **Step 1: Add root ignore rules**

Create `.gitignore`:

```gitignore
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.mypy_cache/
.venv/
venv/
node_modules/
dist/
coverage/
.env
.env.*
storage/
*.db
*.sqlite
```

- [ ] **Step 2: Add project README**

Create `README.md`:

```markdown
# Digital Human Video Platform

This repository contains the design and implementation for a digital human video generation platform.

The first runnable MVP focuses on:

- FastAPI backend.
- SQLite persistence.
- Serial video task pipeline.
- Mock LLM, TTS, avatar rendering, and post-processing providers.
- React Web management UI.

The current implementation phase does not include real livestreaming, real digital human rendering, real cloud LLM calls, or real TTS. Those integrations are designed as provider replacements.

## Documentation

- Design spec: `docs/superpowers/specs/2026-06-19-digital-human-video-platform-design.md`
- MVP plan: `docs/superpowers/plans/2026-06-19-digital-human-video-platform-mvp.md`
```

- [ ] **Step 3: Add backend package config**

Create `backend/pyproject.toml`:

```toml
[project]
name = "digital-human-video-platform-backend"
version = "0.1.0"
description = "FastAPI backend for the digital human video platform MVP."
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115.0",
  "uvicorn[standard]>=0.30.0",
  "sqlmodel>=0.0.22",
  "pydantic-settings>=2.4.0",
  "python-multipart>=0.0.9",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.2.0",
  "httpx>=0.27.0",
  "ruff>=0.6.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
```

- [ ] **Step 4: Add backend README**

Create `backend/README.md`:

```markdown
# Backend

## Setup

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -e ".[dev]"
```

## Run

```powershell
uvicorn app.main:app --reload
```

## Test

```powershell
pytest
```
```

- [ ] **Step 5: Create initial FastAPI app**

Create `backend/app/__init__.py`:

```python
"""Digital human video platform backend."""
```

Create `backend/app/main.py`:

```python
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="Digital Human Video Platform", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 6: Add test client fixture**

Create `backend/tests/conftest.py`:

```python
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
```

- [ ] **Step 7: Add health endpoint test**

Create `backend/tests/test_health.py`:

```python
from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 8: Install backend dependencies**

Run:

```powershell
cd backend
python -m pip install -e ".[dev]"
```

Expected: dependencies install without errors.

- [ ] **Step 9: Verify health endpoint manually**

Run:

```powershell
cd backend
python - <<'PY'
from fastapi.testclient import TestClient
from app.main import create_app

client = TestClient(create_app())
print(client.get("/health").json())
PY
```

Expected output:

```text
{'status': 'ok'}
```

- [ ] **Step 10: Run backend tests**

Run:

```powershell
cd backend
pytest -q
```

Expected: 1 passed.

- [ ] **Step 11: Commit scaffold**

Run:

```powershell
git add .gitignore README.md backend
git commit -m "feat: scaffold backend project"
```

## Task 2: Database Models And Seed Data

**Files:**
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/app/models.py`
- Create: `backend/app/seed.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/conftest.py`
- Create: `backend/tests/test_models.py`

- [ ] **Step 1: Write model tests first**

Create `backend/tests/test_models.py`:

```python
from sqlmodel import Session, select

from app.models import (
    DigitalHumanProfile,
    TaskState,
    VideoTask,
    VoiceProfile,
)
from app.seed import seed_defaults


def test_seed_defaults_creates_profile_voice_and_template(session: Session) -> None:
    seed_defaults(session)

    humans = session.exec(select(DigitalHumanProfile)).all()
    voices = session.exec(select(VoiceProfile)).all()

    assert len(humans) == 1
    assert humans[0].name == "Default Presenter"
    assert humans[0].renderer_adapter_key == "mock-avatar"

    assert len(voices) == 1
    assert voices[0].name == "Default Voice"
    assert voices[0].provider_key == "mock-tts"


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
cd backend
pytest tests/test_models.py -q
```

Expected: FAIL because `app.models`, `app.database`, and `app.seed` do not exist yet.

- [ ] **Step 3: Add settings**

Create `backend/app/config.py`:

```python
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./digital_human.db"
    storage_root: Path = Path("storage")
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(env_prefix="DHVP_", env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 4: Add database helpers**

Create `backend/app/database.py`:

```python
from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings


def make_engine(database_url: str | None = None):
    url = database_url or get_settings().database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


engine = make_engine()


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
```

- [ ] **Step 5: Add SQLModel tables**

Create `backend/app/models.py`:

```python
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class ProfileStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class TaskInputMode(StrEnum):
    TOPIC = "topic"
    EXISTING_SCRIPT = "existing_script"
    REFERENCE_VIDEO = "reference_video"


class TaskState(StrEnum):
    DRAFT = "draft"
    QUEUED = "queued"
    SCRIPT_READY = "script_ready"
    AUDIO_READY = "audio_ready"
    RENDERED = "rendered"
    POST_PROCESSED = "post_processed"
    COMPLETED = "completed"
    FAILED = "failed"


class StepStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class DigitalHumanProfile(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    preview_image_path: str | None = None
    source_media_path: str | None = None
    default_aspect_ratio: str = "9:16"
    renderer_adapter_key: str = "mock-avatar"
    status: ProfileStatus = ProfileStatus.ACTIVE
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class VoiceProfile(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    provider_key: str = "mock-tts"
    voice_key: str = "default"
    style_tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    preview_audio_path: str | None = None
    is_default: bool = False
    status: ProfileStatus = ProfileStatus.ACTIVE
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class PostProcessTemplate(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    subtitle_style: dict = Field(default_factory=dict, sa_column=Column(JSON))
    bgm_path: str | None = None
    intro_media_path: str | None = None
    outro_media_path: str | None = None
    cover_strategy: str = "first_frame"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class VideoTask(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    input_mode: TaskInputMode
    raw_input: str
    digital_human_profile_id: int
    voice_profile_id: int
    post_process_template_id: int
    current_state: TaskState = TaskState.DRAFT
    failed_step: str | None = None
    final_video_path: str | None = None
    cover_path: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ScriptDraft(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    task_id: int = Field(index=True)
    version: int = 1
    script_text: str
    structured_segments: list[dict] = Field(default_factory=list, sa_column=Column(JSON))
    estimated_duration_seconds: float = 0
    source_mode: str
    created_at: datetime = Field(default_factory=utc_now)


class MediaAsset(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    task_id: int = Field(index=True)
    asset_type: str
    file_path: str
    duration_seconds: float | None = None
    asset_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)


class GenerationStepLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    task_id: int = Field(index=True)
    step_name: str
    status: StepStatus
    started_at: datetime = Field(default_factory=utc_now)
    finished_at: datetime | None = None
    duration_seconds: float | None = None
    error_code: str | None = None
    user_message: str | None = None
    technical_log: str | None = None
```

- [ ] **Step 6: Add seed data**

Create `backend/app/seed.py`:

```python
from sqlmodel import Session, select

from app.models import DigitalHumanProfile, PostProcessTemplate, VoiceProfile


def seed_defaults(session: Session) -> None:
    if session.exec(select(DigitalHumanProfile)).first() is None:
        session.add(
            DigitalHumanProfile(
                name="Default Presenter",
                preview_image_path="/static/default-presenter.png",
                source_media_path="/static/default-presenter.mp4",
                renderer_adapter_key="mock-avatar",
            )
        )

    if session.exec(select(VoiceProfile)).first() is None:
        session.add(
            VoiceProfile(
                name="Default Voice",
                provider_key="mock-tts",
                voice_key="default",
                style_tags=["neutral", "mandarin"],
                is_default=True,
            )
        )

    if session.exec(select(PostProcessTemplate)).first() is None:
        session.add(
            PostProcessTemplate(
                name="Default Vertical Video",
                subtitle_style={"font_size": 42, "position": "bottom"},
                cover_strategy="first_frame",
            )
        )

    session.commit()
```

- [ ] **Step 7: Initialize database on app startup**

Modify `backend/app/main.py`:

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from sqlmodel import Session

from app.database import create_db_and_tables, engine
from app.seed import seed_defaults


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if app.state.run_startup_db:
        create_db_and_tables()
        with Session(engine) as session:
            seed_defaults(session)
    yield


def create_app(run_startup_db: bool = True) -> FastAPI:
    app = FastAPI(
        title="Digital Human Video Platform",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.run_startup_db = run_startup_db

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 8: Update test fixture to use in-memory database**

Replace `backend/tests/conftest.py`:

```python
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_session
from app.main import create_app


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(session: Session) -> Generator[TestClient, None, None]:
    app = create_app(run_startup_db=False)

    def override_get_session() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
```

- [ ] **Step 9: Run model tests**

Run:

```powershell
cd backend
pytest tests/test_models.py -q
```

Expected: 2 passed.

- [ ] **Step 10: Run lint**

Run:

```powershell
cd backend
ruff check .
```

Expected: all checks pass.

- [ ] **Step 11: Commit models**

Run:

```powershell
git add backend
git commit -m "feat: add backend data models"
```

## Task 3: Storage And Provider Contracts

**Files:**
- Create: `backend/app/storage.py`
- Create: `backend/app/providers/__init__.py`
- Create: `backend/app/providers/base.py`
- Create: `backend/app/providers/mock.py`
- Create: `backend/tests/test_task_runner.py`

- [ ] **Step 1: Write provider and storage tests first**

Create `backend/tests/test_task_runner.py`:

```python
from pathlib import Path

from app.models import TaskInputMode
from app.providers.mock import MockAvatarRenderer, MockLLMProvider, MockPostProcessor, MockTTSProvider
from app.storage import TaskStorage


def test_task_storage_creates_task_directories(tmp_path: Path) -> None:
    storage = TaskStorage(tmp_path)

    task_dir = storage.task_dir(12)
    artifact = storage.artifact_path(12, "audio", "speech.txt")

    assert task_dir == tmp_path / "tasks" / "12"
    assert artifact == tmp_path / "tasks" / "12" / "audio" / "speech.txt"
    assert artifact.parent.exists()


def test_mock_providers_create_artifacts(tmp_path: Path) -> None:
    storage = TaskStorage(tmp_path)
    llm = MockLLMProvider()
    tts = MockTTSProvider(storage)
    avatar = MockAvatarRenderer(storage)
    post = MockPostProcessor(storage)

    script = llm.prepare_script(
        task_id=1,
        input_mode=TaskInputMode.EXISTING_SCRIPT,
        raw_input="This is a short script.",
    )
    audio = tts.synthesize(task_id=1, script_text=script.script_text, voice_key="default")
    rendered = avatar.render(task_id=1, audio_path=audio.audio_path, profile_key="default")
    final = post.process(task_id=1, raw_video_path=rendered.video_path, script_text=script.script_text)

    assert script.script_text == "This is a short script."
    assert audio.audio_path.exists()
    assert rendered.video_path.exists()
    assert final.final_video_path.exists()
    assert final.cover_path.exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
cd backend
pytest tests/test_task_runner.py -q
```

Expected: FAIL because storage and provider modules do not exist.

- [ ] **Step 3: Add storage helper**

Create `backend/app/storage.py`:

```python
from pathlib import Path


class TaskStorage:
    def __init__(self, root: Path) -> None:
        self.root = root

    def task_dir(self, task_id: int) -> Path:
        path = self.root / "tasks" / str(task_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def artifact_path(self, task_id: int, group: str, filename: str) -> Path:
        safe_group = group.strip().replace("\\", "_").replace("/", "_")
        safe_filename = filename.strip().replace("\\", "_").replace("/", "_")
        path = self.task_dir(task_id) / safe_group / safe_filename
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
```

- [ ] **Step 4: Add provider package marker**

Create `backend/app/providers/__init__.py`:

```python
"""Provider interfaces and implementations."""
```

- [ ] **Step 5: Add provider contracts**

Create `backend/app/providers/base.py`:

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.models import TaskInputMode


@dataclass(frozen=True)
class ScriptResult:
    script_text: str
    structured_segments: list[dict]
    estimated_duration_seconds: float


@dataclass(frozen=True)
class AudioResult:
    audio_path: Path
    duration_seconds: float
    timing: list[dict]


@dataclass(frozen=True)
class RenderResult:
    video_path: Path
    duration_seconds: float
    technical_log: str


@dataclass(frozen=True)
class PostProcessResult:
    final_video_path: Path
    cover_path: Path
    technical_log: str


class LLMProvider(Protocol):
    def prepare_script(
        self,
        task_id: int,
        input_mode: TaskInputMode,
        raw_input: str,
    ) -> ScriptResult:
        raise NotImplementedError


class TTSProvider(Protocol):
    def synthesize(self, task_id: int, script_text: str, voice_key: str) -> AudioResult:
        raise NotImplementedError


class AvatarRenderer(Protocol):
    def render(self, task_id: int, audio_path: Path, profile_key: str) -> RenderResult:
        raise NotImplementedError


class PostProcessor(Protocol):
    def process(self, task_id: int, raw_video_path: Path, script_text: str) -> PostProcessResult:
        raise NotImplementedError
```

- [ ] **Step 6: Add deterministic mock providers**

Create `backend/app/providers/mock.py`:

```python
from pathlib import Path

from app.models import TaskInputMode
from app.providers.base import AudioResult, PostProcessResult, RenderResult, ScriptResult
from app.storage import TaskStorage


class MockLLMProvider:
    def prepare_script(
        self,
        task_id: int,
        input_mode: TaskInputMode,
        raw_input: str,
    ) -> ScriptResult:
        normalized = " ".join(raw_input.split())
        if input_mode == TaskInputMode.TOPIC:
            script_text = f"今天我们来介绍：{normalized}。它的核心亮点清晰，适合做一条简洁有力的口播视频。"
        elif input_mode == TaskInputMode.REFERENCE_VIDEO:
            script_text = f"参考素材的重点是：{normalized}。现在改写成一条新的数字人口播文案。"
        else:
            script_text = normalized

        words = max(len(script_text), 1)
        estimated_duration = round(words / 5.5, 2)
        return ScriptResult(
            script_text=script_text,
            structured_segments=[{"index": 1, "text": script_text}],
            estimated_duration_seconds=estimated_duration,
        )


class MockTTSProvider:
    def __init__(self, storage: TaskStorage) -> None:
        self.storage = storage

    def synthesize(self, task_id: int, script_text: str, voice_key: str) -> AudioResult:
        path = self.storage.artifact_path(task_id, "audio", "speech.txt")
        path.write_text(f"voice={voice_key}\n{script_text}\n", encoding="utf-8")
        duration = round(max(len(script_text), 1) / 5.5, 2)
        return AudioResult(
            audio_path=path,
            duration_seconds=duration,
            timing=[{"start": 0, "end": duration, "text": script_text}],
        )


class MockAvatarRenderer:
    def __init__(self, storage: TaskStorage) -> None:
        self.storage = storage

    def render(self, task_id: int, audio_path: Path, profile_key: str) -> RenderResult:
        path = self.storage.artifact_path(task_id, "render", "raw-video.txt")
        path.write_text(
            f"profile={profile_key}\naudio={audio_path.as_posix()}\n",
            encoding="utf-8",
        )
        return RenderResult(video_path=path, duration_seconds=3.0, technical_log="mock render ok")


class MockPostProcessor:
    def __init__(self, storage: TaskStorage) -> None:
        self.storage = storage

    def process(self, task_id: int, raw_video_path: Path, script_text: str) -> PostProcessResult:
        final_path = self.storage.artifact_path(task_id, "final", "final-video.mp4")
        cover_path = self.storage.artifact_path(task_id, "final", "cover.txt")
        final_path.write_text(
            f"raw_video={raw_video_path.as_posix()}\nscript={script_text}\n",
            encoding="utf-8",
        )
        cover_path.write_text("mock cover", encoding="utf-8")
        return PostProcessResult(
            final_video_path=final_path,
            cover_path=cover_path,
            technical_log="mock post-process ok",
        )
```

- [ ] **Step 7: Run provider tests**

Run:

```powershell
cd backend
pytest tests/test_task_runner.py -q
```

Expected: 2 passed.

- [ ] **Step 8: Run backend test suite**

Run:

```powershell
cd backend
pytest -q
```

Expected: all collected tests pass.

- [ ] **Step 9: Commit provider contracts**

Run:

```powershell
git add backend
git commit -m "feat: add storage and provider contracts"
```

## Task 4: Serial Task Runner

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/task_runner.py`
- Modify: `backend/tests/test_task_runner.py`

- [ ] **Step 1: Add task runner test**

Append to `backend/tests/test_task_runner.py`:

```python
from sqlmodel import Session

from app.models import (
    GenerationStepLog,
    MediaAsset,
    ScriptDraft,
    TaskState,
    VideoTask,
)
from app.providers.mock import MockAvatarRenderer, MockLLMProvider, MockPostProcessor, MockTTSProvider
from app.services.task_runner import TaskRunner
from app.storage import TaskStorage


def test_task_runner_completes_existing_script_task(session: Session, tmp_path: Path) -> None:
    task = VideoTask(
        input_mode=TaskInputMode.EXISTING_SCRIPT,
        raw_input="A complete script for the MVP.",
        digital_human_profile_id=1,
        voice_profile_id=1,
        post_process_template_id=1,
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    storage = TaskStorage(tmp_path)
    runner = TaskRunner(
        storage=storage,
        llm_provider=MockLLMProvider(),
        tts_provider=MockTTSProvider(storage),
        avatar_renderer=MockAvatarRenderer(storage),
        post_processor=MockPostProcessor(storage),
    )

    runner.run_task(session, task.id)
    session.refresh(task)

    scripts = session.query(ScriptDraft).filter(ScriptDraft.task_id == task.id).all()
    assets = session.query(MediaAsset).filter(MediaAsset.task_id == task.id).all()
    logs = session.query(GenerationStepLog).filter(GenerationStepLog.task_id == task.id).all()

    assert task.current_state == TaskState.COMPLETED
    assert task.final_video_path is not None
    assert task.cover_path is not None
    assert len(scripts) == 1
    assert {asset.asset_type for asset in assets} == {"audio", "raw_video", "final_video", "cover"}
    assert [log.step_name for log in logs] == ["script", "tts", "avatar_render", "post_process"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
cd backend
pytest tests/test_task_runner.py::test_task_runner_completes_existing_script_task -q
```

Expected: FAIL because `TaskRunner` does not exist.

- [ ] **Step 3: Add service package marker**

Create `backend/app/services/__init__.py`:

```python
"""Application services."""
```

- [ ] **Step 4: Implement serial task runner**

Create `backend/app/services/task_runner.py`:

```python
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session

from app.models import (
    GenerationStepLog,
    MediaAsset,
    ScriptDraft,
    StepStatus,
    TaskState,
    VideoTask,
)
from app.providers.base import AvatarRenderer, LLMProvider, PostProcessor, TTSProvider
from app.storage import TaskStorage


class TaskRunner:
    def __init__(
        self,
        storage: TaskStorage,
        llm_provider: LLMProvider,
        tts_provider: TTSProvider,
        avatar_renderer: AvatarRenderer,
        post_processor: PostProcessor,
    ) -> None:
        self.storage = storage
        self.llm_provider = llm_provider
        self.tts_provider = tts_provider
        self.avatar_renderer = avatar_renderer
        self.post_processor = post_processor

    def run_task(self, session: Session, task_id: int) -> None:
        task = session.get(VideoTask, task_id)
        if task is None:
            raise ValueError(f"Task {task_id} does not exist")

        task.current_state = TaskState.QUEUED
        task.updated_at = datetime.now(UTC)
        session.add(task)
        session.commit()

        script_text = self._run_step(
            session,
            task,
            "script",
            lambda: self._prepare_script(session, task),
        )
        audio_path = self._run_step(
            session,
            task,
            "tts",
            lambda: self._synthesize(session, task, script_text),
        )
        raw_video_path = self._run_step(
            session,
            task,
            "avatar_render",
            lambda: self._render_avatar(session, task, audio_path),
        )
        self._run_step(
            session,
            task,
            "post_process",
            lambda: self._post_process(session, task, raw_video_path, script_text),
        )

        task.current_state = TaskState.COMPLETED
        task.updated_at = datetime.now(UTC)
        session.add(task)
        session.commit()

    def _run_step(
        self,
        session: Session,
        task: VideoTask,
        step_name: str,
        action: Callable[[], object],
    ):
        started = datetime.now(UTC)
        log = GenerationStepLog(task_id=task.id, step_name=step_name, status=StepStatus.RUNNING)
        session.add(log)
        session.commit()
        session.refresh(log)

        try:
            result = action()
        except Exception as exc:
            finished = datetime.now(UTC)
            log.status = StepStatus.FAILED
            log.finished_at = finished
            log.duration_seconds = (finished - started).total_seconds()
            log.error_code = f"{step_name}_failed"
            log.user_message = f"{step_name} step failed"
            log.technical_log = str(exc)
            task.current_state = TaskState.FAILED
            task.failed_step = step_name
            task.updated_at = finished
            session.add(log)
            session.add(task)
            session.commit()
            raise

        finished = datetime.now(UTC)
        log.status = StepStatus.SUCCEEDED
        log.finished_at = finished
        log.duration_seconds = (finished - started).total_seconds()
        log.technical_log = f"{step_name} completed"
        session.add(log)
        session.commit()
        return result

    def _prepare_script(self, session: Session, task: VideoTask) -> str:
        result = self.llm_provider.prepare_script(
            task_id=task.id,
            input_mode=task.input_mode,
            raw_input=task.raw_input,
        )
        session.add(
            ScriptDraft(
                task_id=task.id,
                script_text=result.script_text,
                structured_segments=result.structured_segments,
                estimated_duration_seconds=result.estimated_duration_seconds,
                source_mode=task.input_mode.value,
            )
        )
        task.current_state = TaskState.SCRIPT_READY
        task.updated_at = datetime.now(UTC)
        session.add(task)
        session.commit()
        return result.script_text

    def _synthesize(self, session: Session, task: VideoTask, script_text: str) -> Path:
        result = self.tts_provider.synthesize(
            task_id=task.id,
            script_text=script_text,
            voice_key=str(task.voice_profile_id),
        )
        task.current_state = TaskState.AUDIO_READY
        task.updated_at = datetime.now(UTC)
        session.add(task)
        session.commit()
        return result.audio_path

    def _render_avatar(self, session: Session, task: VideoTask, audio_path: Path) -> Path:
        result = self.avatar_renderer.render(
            task_id=task.id,
            audio_path=audio_path,
            profile_key=str(task.digital_human_profile_id),
        )
        task.current_state = TaskState.RENDERED
        task.updated_at = datetime.now(UTC)
        session.add(task)
        session.commit()
        return result.video_path

    def _post_process(
        self,
        session: Session,
        task: VideoTask,
        raw_video_path: Path,
        script_text: str,
    ) -> None:
        result = self.post_processor.process(
            task_id=task.id,
            raw_video_path=raw_video_path,
            script_text=script_text,
        )
        assets = [
            MediaAsset(task_id=task.id, asset_type="audio", file_path=self._path(task.id, "audio", "speech.txt")),
            MediaAsset(task_id=task.id, asset_type="raw_video", file_path=raw_video_path.as_posix()),
            MediaAsset(task_id=task.id, asset_type="final_video", file_path=result.final_video_path.as_posix()),
            MediaAsset(task_id=task.id, asset_type="cover", file_path=result.cover_path.as_posix()),
        ]
        for asset in assets:
            session.add(asset)
        task.current_state = TaskState.POST_PROCESSED
        task.final_video_path = result.final_video_path.as_posix()
        task.cover_path = result.cover_path.as_posix()
        task.updated_at = datetime.now(UTC)
        session.add(task)
        session.commit()

    def _path(self, task_id: int, group: str, filename: str) -> str:
        return self.storage.artifact_path(task_id, group, filename).as_posix()
```

- [ ] **Step 5: Run focused task runner test**

Run:

```powershell
cd backend
pytest tests/test_task_runner.py::test_task_runner_completes_existing_script_task -q
```

Expected: 1 passed.

- [ ] **Step 6: Run backend tests**

Run:

```powershell
cd backend
pytest -q
```

Expected: all tests pass.

- [ ] **Step 7: Commit runner**

Run:

```powershell
git add backend
git commit -m "feat: add serial task runner"
```

## Task 5: REST API For Profiles, Voices, Tasks, Logs, And Retry

**Files:**
- Create: `backend/app/schemas.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/routes.py`
- Create: `backend/app/services/task_service.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_api_tasks.py`

- [ ] **Step 1: Write API tests first**

Create `backend/tests/test_api_tasks.py`:

```python
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

    detail = client.get(f"/api/tasks/{payload['id']}").json()
    assert detail["task"]["id"] == payload["id"]
    assert len(detail["logs"]) == 4
    assert detail["script"]["script_text"] == "This script should become a mock video."


def test_list_profiles_and_voices(client: TestClient, session: Session) -> None:
    seed_defaults(session)

    humans = client.get("/api/digital-humans").json()
    voices = client.get("/api/voices").json()
    templates = client.get("/api/post-process-templates").json()

    assert humans[0]["name"] == "Default Presenter"
    assert voices[0]["name"] == "Default Voice"
    assert templates[0]["name"] == "Default Vertical Video"
```

- [ ] **Step 2: Run API tests to verify they fail**

Run:

```powershell
cd backend
pytest tests/test_api_tasks.py -q
```

Expected: FAIL because API routes do not exist.

- [ ] **Step 3: Add API schemas**

Create `backend/app/schemas.py`:

```python
from pydantic import BaseModel, Field

from app.models import (
    DigitalHumanProfile,
    GenerationStepLog,
    MediaAsset,
    PostProcessTemplate,
    ScriptDraft,
    TaskInputMode,
    TaskState,
    VideoTask,
    VoiceProfile,
)


class TaskCreate(BaseModel):
    input_mode: TaskInputMode
    raw_input: str = Field(min_length=1)
    digital_human_profile_id: int
    voice_profile_id: int
    post_process_template_id: int


class TaskRead(BaseModel):
    id: int
    input_mode: TaskInputMode
    raw_input: str
    digital_human_profile_id: int
    voice_profile_id: int
    post_process_template_id: int
    current_state: TaskState
    failed_step: str | None
    final_video_path: str | None
    cover_path: str | None

    @classmethod
    def from_model(cls, task: VideoTask) -> "TaskRead":
        return cls.model_validate(task, from_attributes=True)


class TaskDetail(BaseModel):
    task: TaskRead
    script: ScriptDraft | None
    assets: list[MediaAsset]
    logs: list[GenerationStepLog]


class DigitalHumanRead(BaseModel):
    id: int
    name: str
    preview_image_path: str | None
    source_media_path: str | None
    default_aspect_ratio: str
    renderer_adapter_key: str
    status: str

    @classmethod
    def from_model(cls, profile: DigitalHumanProfile) -> "DigitalHumanRead":
        return cls.model_validate(profile, from_attributes=True)


class VoiceRead(BaseModel):
    id: int
    name: str
    provider_key: str
    voice_key: str
    style_tags: list[str]
    preview_audio_path: str | None
    is_default: bool
    status: str

    @classmethod
    def from_model(cls, profile: VoiceProfile) -> "VoiceRead":
        return cls.model_validate(profile, from_attributes=True)


class TemplateRead(BaseModel):
    id: int
    name: str
    subtitle_style: dict
    bgm_path: str | None
    intro_media_path: str | None
    outro_media_path: str | None
    cover_strategy: str

    @classmethod
    def from_model(cls, template: PostProcessTemplate) -> "TemplateRead":
        return cls.model_validate(template, from_attributes=True)
```

- [ ] **Step 4: Add API package marker**

Create `backend/app/api/__init__.py`:

```python
"""HTTP API routes."""
```

- [ ] **Step 5: Add task service**

Create `backend/app/services/task_service.py`:

```python
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
from app.providers.mock import MockAvatarRenderer, MockLLMProvider, MockPostProcessor, MockTTSProvider
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
        self.runner.run_task(session, task.id)
        session.refresh(task)
        return task

    def list_tasks(self, session: Session) -> list[VideoTask]:
        return list(session.exec(select(VideoTask).order_by(VideoTask.created_at.desc())).all())

    def get_task_detail(self, session: Session, task_id: int):
        task = session.get(VideoTask, task_id)
        if task is None:
            return None
        script = session.exec(select(ScriptDraft).where(ScriptDraft.task_id == task_id)).first()
        assets = list(session.exec(select(MediaAsset).where(MediaAsset.task_id == task_id)).all())
        logs = list(session.exec(select(GenerationStepLog).where(GenerationStepLog.task_id == task_id)).all())
        return task, script, assets, logs

    def list_humans(self, session: Session) -> list[DigitalHumanProfile]:
        return list(session.exec(select(DigitalHumanProfile)).all())

    def list_voices(self, session: Session) -> list[VoiceProfile]:
        return list(session.exec(select(VoiceProfile)).all())

    def list_templates(self, session: Session) -> list[PostProcessTemplate]:
        return list(session.exec(select(PostProcessTemplate)).all())
```

- [ ] **Step 6: Add API routes**

Create `backend/app/api/routes.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.config import get_settings
from app.database import get_session
from app.schemas import (
    DigitalHumanRead,
    TaskCreate,
    TaskDetail,
    TaskRead,
    TemplateRead,
    VoiceRead,
)
from app.services.task_service import TaskService

router = APIRouter(prefix="/api")


def get_task_service() -> TaskService:
    return TaskService(get_settings().storage_root)


@router.get("/digital-humans", response_model=list[DigitalHumanRead])
def list_digital_humans(
    session: Session = Depends(get_session),
    service: TaskService = Depends(get_task_service),
) -> list[DigitalHumanRead]:
    return [DigitalHumanRead.from_model(item) for item in service.list_humans(session)]


@router.get("/voices", response_model=list[VoiceRead])
def list_voices(
    session: Session = Depends(get_session),
    service: TaskService = Depends(get_task_service),
) -> list[VoiceRead]:
    return [VoiceRead.from_model(item) for item in service.list_voices(session)]


@router.get("/post-process-templates", response_model=list[TemplateRead])
def list_templates(
    session: Session = Depends(get_session),
    service: TaskService = Depends(get_task_service),
) -> list[TemplateRead]:
    return [TemplateRead.from_model(item) for item in service.list_templates(session)]


@router.get("/tasks", response_model=list[TaskRead])
def list_tasks(
    session: Session = Depends(get_session),
    service: TaskService = Depends(get_task_service),
) -> list[TaskRead]:
    return [TaskRead.from_model(task) for task in service.list_tasks(session)]


@router.post("/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    session: Session = Depends(get_session),
    service: TaskService = Depends(get_task_service),
) -> TaskRead:
    task = service.create_and_run(session, payload)
    return TaskRead.from_model(task)


@router.get("/tasks/{task_id}", response_model=TaskDetail)
def get_task(
    task_id: int,
    session: Session = Depends(get_session),
    service: TaskService = Depends(get_task_service),
) -> TaskDetail:
    detail = service.get_task_detail(session, task_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Task not found")
    task, script, assets, logs = detail
    return TaskDetail(task=TaskRead.from_model(task), script=script, assets=assets, logs=logs)
```

- [ ] **Step 7: Register routes and CORS**

Replace `backend/app/main.py`:

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from app.api.routes import router
from app.config import get_settings
from app.database import create_db_and_tables, engine
from app.seed import seed_defaults


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if app.state.run_startup_db:
        create_db_and_tables()
        with Session(engine) as session:
            seed_defaults(session)
    yield


def create_app(run_startup_db: bool = True) -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Digital Human Video Platform",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.run_startup_db = run_startup_db
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 8: Run API tests**

Run:

```powershell
cd backend
pytest tests/test_api_tasks.py -q
```

Expected: 2 passed.

- [ ] **Step 9: Run backend tests and lint**

Run:

```powershell
cd backend
pytest -q
ruff check .
```

Expected: all tests pass and lint passes.

- [ ] **Step 10: Commit API**

Run:

```powershell
git add backend
git commit -m "feat: add task management API"
```

## Task 6: Frontend Scaffold And API Client

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/vitest.config.ts`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/types.ts`
- Create: `frontend/src/api.ts`
- Create: `frontend/src/styles.css`
- Create: `frontend/src/App.tsx`
- Create: `frontend/tests/App.test.tsx`

- [ ] **Step 1: Add frontend package config**

Create `frontend/package.json`:

```json
{
  "name": "digital-human-video-platform-frontend",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite --host 0.0.0.0",
    "build": "tsc && vite build",
    "test": "vitest run"
  },
  "dependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "vite": "^5.4.0",
    "typescript": "^5.5.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "lucide-react": "^0.468.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.4.0",
    "@testing-library/react": "^15.0.0",
    "@testing-library/user-event": "^14.5.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "jsdom": "^25.0.0",
    "vitest": "^2.0.0"
  }
}
```

- [ ] **Step 2: Add Vite and TypeScript config**

Create `frontend/index.html`:

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Digital Human Video Platform</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Create `frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["DOM", "DOM.Iterable", "ES2020"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src", "tests"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

Create `frontend/tsconfig.node.json`:

```json
{
  "compilerOptions": {
    "composite": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts", "vitest.config.ts"]
}
```

Create `frontend/vite.config.ts`:

```ts
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
      "/health": "http://localhost:8000"
    }
  }
});
```

Create `frontend/vitest.config.ts`:

```ts
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: []
  }
});
```

- [ ] **Step 3: Add frontend types**

Create `frontend/src/types.ts`:

```ts
export type TaskInputMode = "topic" | "existing_script" | "reference_video";
export type TaskState =
  | "draft"
  | "queued"
  | "script_ready"
  | "audio_ready"
  | "rendered"
  | "post_processed"
  | "completed"
  | "failed";

export interface DigitalHumanProfile {
  id: number;
  name: string;
  preview_image_path: string | null;
  source_media_path: string | null;
  default_aspect_ratio: string;
  renderer_adapter_key: string;
  status: string;
}

export interface VoiceProfile {
  id: number;
  name: string;
  provider_key: string;
  voice_key: string;
  style_tags: string[];
  preview_audio_path: string | null;
  is_default: boolean;
  status: string;
}

export interface PostProcessTemplate {
  id: number;
  name: string;
  subtitle_style: Record<string, unknown>;
  bgm_path: string | null;
  intro_media_path: string | null;
  outro_media_path: string | null;
  cover_strategy: string;
}

export interface VideoTask {
  id: number;
  input_mode: TaskInputMode;
  raw_input: string;
  digital_human_profile_id: number;
  voice_profile_id: number;
  post_process_template_id: number;
  current_state: TaskState;
  failed_step: string | null;
  final_video_path: string | null;
  cover_path: string | null;
}

export interface ScriptDraft {
  id: number;
  task_id: number;
  version: number;
  script_text: string;
  structured_segments: Record<string, unknown>[];
  estimated_duration_seconds: number;
  source_mode: string;
}

export interface GenerationStepLog {
  id: number;
  task_id: number;
  step_name: string;
  status: string;
  duration_seconds: number | null;
  error_code: string | null;
  user_message: string | null;
  technical_log: string | null;
}

export interface MediaAsset {
  id: number;
  task_id: number;
  asset_type: string;
  file_path: string;
}

export interface TaskDetail {
  task: VideoTask;
  script: ScriptDraft | null;
  assets: MediaAsset[];
  logs: GenerationStepLog[];
}
```

- [ ] **Step 4: Add API client**

Create `frontend/src/api.ts`:

```ts
import type {
  DigitalHumanProfile,
  PostProcessTemplate,
  TaskDetail,
  TaskInputMode,
  VideoTask,
  VoiceProfile
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function listDigitalHumans(): Promise<DigitalHumanProfile[]> {
  return request("/api/digital-humans");
}

export function listVoices(): Promise<VoiceProfile[]> {
  return request("/api/voices");
}

export function listTemplates(): Promise<PostProcessTemplate[]> {
  return request("/api/post-process-templates");
}

export function listTasks(): Promise<VideoTask[]> {
  return request("/api/tasks");
}

export function getTask(taskId: number): Promise<TaskDetail> {
  return request(`/api/tasks/${taskId}`);
}

export function createTask(payload: {
  input_mode: TaskInputMode;
  raw_input: string;
  digital_human_profile_id: number;
  voice_profile_id: number;
  post_process_template_id: number;
}): Promise<VideoTask> {
  return request("/api/tasks", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
```

- [ ] **Step 5: Add minimal app and style**

Create `frontend/src/main.tsx`:

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./App";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

Create `frontend/src/App.tsx`:

```tsx
export function App() {
  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>数字人口播视频平台</h1>
          <p>批量口播视频生成 MVP</p>
        </div>
      </header>
      <section className="panel">
        <h2>工作台</h2>
        <p>后续任务会在这里接入后台 API、任务表单和成片记录。</p>
      </section>
    </main>
  );
}
```

Create `frontend/src/styles.css`:

```css
:root {
  font-family:
    Inter, "Microsoft YaHei", "PingFang SC", system-ui, -apple-system, BlinkMacSystemFont,
    "Segoe UI", sans-serif;
  color: #172033;
  background: #f5f7fb;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
}

button,
input,
select,
textarea {
  font: inherit;
}

.app-shell {
  min-height: 100vh;
}

.topbar {
  padding: 24px 32px;
  color: white;
  background: #1f4f46;
}

.topbar h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
}

.topbar p {
  margin: 6px 0 0;
  color: #d4eee7;
}

.panel {
  margin: 24px;
  padding: 20px;
  border: 1px solid #dce3ee;
  border-radius: 8px;
  background: white;
}
```

- [ ] **Step 6: Add smoke test**

Create `frontend/tests/App.test.tsx`:

```tsx
import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "../src/App";

describe("App", () => {
  it("renders the dashboard heading", () => {
    render(<App />);
    expect(screen.getByText("数字人口播视频平台")).toBeInTheDocument();
    expect(screen.getByText("工作台")).toBeInTheDocument();
  });
});
```

- [ ] **Step 7: Install frontend dependencies**

Run:

```powershell
cd frontend
npm install
```

Expected: install completes and creates `package-lock.json`.

- [ ] **Step 8: Run frontend test to verify setup**

Run:

```powershell
cd frontend
npm test
```

Expected: the smoke test passes.

- [ ] **Step 9: Run frontend build**

Run:

```powershell
cd frontend
npm run build
```

Expected: TypeScript and Vite build pass.

- [ ] **Step 10: Commit frontend scaffold**

Run:

```powershell
git add frontend
git commit -m "feat: scaffold frontend app"
```

## Task 7: Frontend Management UI

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/styles.css`
- Create: `frontend/src/components/Layout.tsx`
- Create: `frontend/src/components/StatusPill.tsx`
- Create: `frontend/src/components/TaskForm.tsx`
- Create: `frontend/src/components/TaskList.tsx`
- Create: `frontend/src/components/TaskDetail.tsx`
- Create: `frontend/src/components/ProfileList.tsx`
- Create: `frontend/src/components/VoiceList.tsx`
- Modify: `frontend/tests/App.test.tsx`

- [ ] **Step 1: Add UI component tests first**

Replace `frontend/tests/App.test.tsx`:

```tsx
import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { App } from "../src/App";

vi.mock("../src/api", () => ({
  listDigitalHumans: async () => [
    {
      id: 1,
      name: "Default Presenter",
      preview_image_path: null,
      source_media_path: null,
      default_aspect_ratio: "9:16",
      renderer_adapter_key: "mock-avatar",
      status: "active"
    }
  ],
  listVoices: async () => [
    {
      id: 1,
      name: "Default Voice",
      provider_key: "mock-tts",
      voice_key: "default",
      style_tags: ["neutral"],
      preview_audio_path: null,
      is_default: true,
      status: "active"
    }
  ],
  listTemplates: async () => [
    {
      id: 1,
      name: "Default Vertical Video",
      subtitle_style: {},
      bgm_path: null,
      intro_media_path: null,
      outro_media_path: null,
      cover_strategy: "first_frame"
    }
  ],
  listTasks: async () => [
    {
      id: 1,
      input_mode: "existing_script",
      raw_input: "A sample task",
      digital_human_profile_id: 1,
      voice_profile_id: 1,
      post_process_template_id: 1,
      current_state: "completed",
      failed_step: null,
      final_video_path: "storage/tasks/1/final/final-video.mp4",
      cover_path: "storage/tasks/1/final/cover.txt"
    }
  ],
  getTask: async () => ({
    task: {
      id: 1,
      input_mode: "existing_script",
      raw_input: "A sample task",
      digital_human_profile_id: 1,
      voice_profile_id: 1,
      post_process_template_id: 1,
      current_state: "completed",
      failed_step: null,
      final_video_path: "storage/tasks/1/final/final-video.mp4",
      cover_path: "storage/tasks/1/final/cover.txt"
    },
    script: {
      id: 1,
      task_id: 1,
      version: 1,
      script_text: "A sample task",
      structured_segments: [],
      estimated_duration_seconds: 3,
      source_mode: "existing_script"
    },
    assets: [],
    logs: []
  }),
  createTask: async () => ({
    id: 2,
    input_mode: "existing_script",
    raw_input: "Created",
    digital_human_profile_id: 1,
    voice_profile_id: 1,
    post_process_template_id: 1,
    current_state: "completed",
    failed_step: null,
    final_video_path: "storage/tasks/2/final/final-video.mp4",
    cover_path: "storage/tasks/2/final/cover.txt"
  })
}));

describe("App", () => {
  it("renders management UI sections", async () => {
    render(<App />);

    expect(await screen.findByText("新建视频任务")).toBeInTheDocument();
    expect((await screen.findAllByText("Default Presenter")).length).toBeGreaterThan(0);
    expect((await screen.findAllByText("Default Voice")).length).toBeGreaterThan(0);
    expect((await screen.findAllByText("A sample task")).length).toBeGreaterThan(0);
  });
});
```

- [ ] **Step 2: Run UI test to verify it fails**

Run:

```powershell
cd frontend
npm test
```

Expected: FAIL because components do not exist and current UI lacks the expected sections.

- [ ] **Step 3: Add layout component**

Create `frontend/src/components/Layout.tsx`:

```tsx
import type { ReactNode } from "react";
import { Clapperboard, MonitorPlay, UserRound, Volume2 } from "lucide-react";

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <MonitorPlay aria-hidden="true" />
          <span>数字人口播</span>
        </div>
        <nav>
          <a href="#tasks">
            <Clapperboard aria-hidden="true" />
            任务
          </a>
          <a href="#humans">
            <UserRound aria-hidden="true" />
            数字人
          </a>
          <a href="#voices">
            <Volume2 aria-hidden="true" />
            声音
          </a>
        </nav>
      </aside>
      <section className="workspace">{children}</section>
    </main>
  );
}
```

- [ ] **Step 4: Add status pill**

Create `frontend/src/components/StatusPill.tsx`:

```tsx
import type { TaskState } from "../types";

const labels: Record<TaskState, string> = {
  draft: "草稿",
  queued: "等待",
  script_ready: "文案完成",
  audio_ready: "音频完成",
  rendered: "渲染完成",
  post_processed: "后期完成",
  completed: "完成",
  failed: "失败"
};

export function StatusPill({ state }: { state: TaskState }) {
  return <span className={`status status-${state}`}>{labels[state]}</span>;
}
```

- [ ] **Step 5: Add task form**

Create `frontend/src/components/TaskForm.tsx`:

```tsx
import { useState } from "react";

import type {
  DigitalHumanProfile,
  PostProcessTemplate,
  TaskInputMode,
  VideoTask,
  VoiceProfile
} from "../types";

interface TaskFormProps {
  humans: DigitalHumanProfile[];
  voices: VoiceProfile[];
  templates: PostProcessTemplate[];
  onCreate: (payload: {
    input_mode: TaskInputMode;
    raw_input: string;
    digital_human_profile_id: number;
    voice_profile_id: number;
    post_process_template_id: number;
  }) => Promise<VideoTask>;
}

export function TaskForm({ humans, voices, templates, onCreate }: TaskFormProps) {
  const [inputMode, setInputMode] = useState<TaskInputMode>("existing_script");
  const [rawInput, setRawInput] = useState("这是一条用于验证 MVP 流水线的口播文案。");
  const [submitting, setSubmitting] = useState(false);

  const disabled = humans.length === 0 || voices.length === 0 || templates.length === 0 || submitting;

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    try {
      await onCreate({
        input_mode: inputMode,
        raw_input: rawInput,
        digital_human_profile_id: humans[0].id,
        voice_profile_id: voices[0].id,
        post_process_template_id: templates[0].id
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="panel task-form" onSubmit={submit}>
      <div className="panel-header">
        <h2>新建视频任务</h2>
      </div>
      <label>
        输入类型
        <select value={inputMode} onChange={(event) => setInputMode(event.target.value as TaskInputMode)}>
          <option value="existing_script">已有文案</option>
          <option value="topic">主题/商品资料</option>
          <option value="reference_video">对标视频资料</option>
        </select>
      </label>
      <label>
        输入内容
        <textarea value={rawInput} onChange={(event) => setRawInput(event.target.value)} rows={5} />
      </label>
      <div className="form-grid">
        <div>
          <strong>数字人</strong>
          <span>{humans[0]?.name ?? "无可用数字人"}</span>
        </div>
        <div>
          <strong>声音</strong>
          <span>{voices[0]?.name ?? "无可用声音"}</span>
        </div>
        <div>
          <strong>后期模板</strong>
          <span>{templates[0]?.name ?? "无可用模板"}</span>
        </div>
      </div>
      <button type="submit" disabled={disabled}>
        {submitting ? "生成中" : "生成视频"}
      </button>
    </form>
  );
}
```

- [ ] **Step 6: Add list components**

Create `frontend/src/components/TaskList.tsx`:

```tsx
import type { VideoTask } from "../types";
import { StatusPill } from "./StatusPill";

interface TaskListProps {
  tasks: VideoTask[];
  selectedTaskId: number | null;
  onSelect: (taskId: number) => void;
}

export function TaskList({ tasks, selectedTaskId, onSelect }: TaskListProps) {
  return (
    <section className="panel" id="tasks">
      <div className="panel-header">
        <h2>成片记录</h2>
        <span>{tasks.length} 条</span>
      </div>
      <div className="task-list">
        {tasks.map((task) => (
          <button
            className={task.id === selectedTaskId ? "task-row active" : "task-row"}
            key={task.id}
            type="button"
            onClick={() => onSelect(task.id)}
          >
            <span>{task.raw_input}</span>
            <StatusPill state={task.current_state} />
          </button>
        ))}
      </div>
    </section>
  );
}
```

Create `frontend/src/components/ProfileList.tsx`:

```tsx
import type { DigitalHumanProfile } from "../types";

export function ProfileList({ humans }: { humans: DigitalHumanProfile[] }) {
  return (
    <section className="panel" id="humans">
      <div className="panel-header">
        <h2>数字人形象</h2>
        <span>{humans.length} 个</span>
      </div>
      <div className="compact-list">
        {humans.map((human) => (
          <div key={human.id} className="compact-item">
            <strong>{human.name}</strong>
            <span>{human.renderer_adapter_key}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
```

Create `frontend/src/components/VoiceList.tsx`:

```tsx
import type { VoiceProfile } from "../types";

export function VoiceList({ voices }: { voices: VoiceProfile[] }) {
  return (
    <section className="panel" id="voices">
      <div className="panel-header">
        <h2>声音</h2>
        <span>{voices.length} 个</span>
      </div>
      <div className="compact-list">
        {voices.map((voice) => (
          <div key={voice.id} className="compact-item">
            <strong>{voice.name}</strong>
            <span>{voice.provider_key}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
```

- [ ] **Step 7: Add task detail**

Create `frontend/src/components/TaskDetail.tsx`:

```tsx
import type { TaskDetail as TaskDetailType } from "../types";
import { StatusPill } from "./StatusPill";

export function TaskDetail({ detail }: { detail: TaskDetailType | null }) {
  if (!detail) {
    return (
      <section className="panel detail-panel">
        <h2>任务详情</h2>
        <p>选择一条成片记录查看文案、日志和产物路径。</p>
      </section>
    );
  }

  return (
    <section className="panel detail-panel">
      <div className="panel-header">
        <h2>任务详情 #{detail.task.id}</h2>
        <StatusPill state={detail.task.current_state} />
      </div>
      <h3>生成文案</h3>
      <p className="script-box">{detail.script?.script_text ?? "暂无文案"}</p>
      <h3>产物</h3>
      <div className="compact-list">
        {detail.assets.map((asset) => (
          <div key={asset.id} className="compact-item">
            <strong>{asset.asset_type}</strong>
            <span>{asset.file_path}</span>
          </div>
        ))}
      </div>
      <h3>日志</h3>
      <div className="compact-list">
        {detail.logs.map((log) => (
          <div key={log.id} className="compact-item">
            <strong>{log.step_name}</strong>
            <span>{log.status}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
```

- [ ] **Step 8: Wire full App**

Replace `frontend/src/App.tsx`:

```tsx
import { useEffect, useState } from "react";

import {
  createTask,
  getTask,
  listDigitalHumans,
  listTasks,
  listTemplates,
  listVoices
} from "./api";
import { Layout } from "./components/Layout";
import { ProfileList } from "./components/ProfileList";
import { TaskDetail } from "./components/TaskDetail";
import { TaskForm } from "./components/TaskForm";
import { TaskList } from "./components/TaskList";
import { VoiceList } from "./components/VoiceList";
import type {
  DigitalHumanProfile,
  PostProcessTemplate,
  TaskDetail as TaskDetailType,
  VideoTask,
  VoiceProfile
} from "./types";

export function App() {
  const [humans, setHumans] = useState<DigitalHumanProfile[]>([]);
  const [voices, setVoices] = useState<VoiceProfile[]>([]);
  const [templates, setTemplates] = useState<PostProcessTemplate[]>([]);
  const [tasks, setTasks] = useState<VideoTask[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(null);
  const [detail, setDetail] = useState<TaskDetailType | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      const [nextHumans, nextVoices, nextTemplates, nextTasks] = await Promise.all([
        listDigitalHumans(),
        listVoices(),
        listTemplates(),
        listTasks()
      ]);
      setHumans(nextHumans);
      setVoices(nextVoices);
      setTemplates(nextTemplates);
      setTasks(nextTasks);
      const firstTask = nextTasks[0];
      if (firstTask && selectedTaskId === null) {
        setSelectedTaskId(firstTask.id);
      }
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    }
  }

  async function selectTask(taskId: number) {
    setSelectedTaskId(taskId);
    setDetail(await getTask(taskId));
  }

  useEffect(() => {
    void load();
  }, []);

  useEffect(() => {
    if (selectedTaskId !== null) {
      void selectTask(selectedTaskId);
    }
  }, [selectedTaskId]);

  return (
    <Layout>
      <header className="workspace-header">
        <div>
          <h1>工作台</h1>
          <p>单机串行生成数字人口播视频，当前使用 mock provider 验证完整流水线。</p>
        </div>
      </header>
      {error ? <div className="error-banner">{error}</div> : null}
      <div className="dashboard-grid">
        <TaskForm
          humans={humans}
          voices={voices}
          templates={templates}
          onCreate={async (payload) => {
            const created = await createTask(payload);
            await load();
            setSelectedTaskId(created.id);
            return created;
          }}
        />
        <TaskList tasks={tasks} selectedTaskId={selectedTaskId} onSelect={selectTask} />
        <TaskDetail detail={detail} />
        <ProfileList humans={humans} />
        <VoiceList voices={voices} />
      </div>
    </Layout>
  );
}
```

- [ ] **Step 9: Replace styles**

Replace `frontend/src/styles.css` with:

```css
:root {
  font-family:
    Inter, "Microsoft YaHei", "PingFang SC", system-ui, -apple-system, BlinkMacSystemFont,
    "Segoe UI", sans-serif;
  color: #172033;
  background: #f5f7fb;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
}

button,
input,
select,
textarea {
  font: inherit;
}

button {
  cursor: pointer;
}

.app-shell {
  display: grid;
  grid-template-columns: 240px 1fr;
  min-height: 100vh;
}

.sidebar {
  padding: 20px;
  color: white;
  background: #1f4f46;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 28px;
  font-size: 18px;
  font-weight: 700;
}

.brand svg,
.sidebar nav svg {
  width: 20px;
  height: 20px;
}

.sidebar nav {
  display: grid;
  gap: 8px;
}

.sidebar a {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 40px;
  padding: 8px 10px;
  border-radius: 8px;
  color: #e7f6f2;
  text-decoration: none;
}

.sidebar a:hover {
  background: rgba(255, 255, 255, 0.12);
}

.workspace {
  padding: 24px;
}

.workspace-header {
  margin-bottom: 20px;
}

.workspace-header h1 {
  margin: 0;
  font-size: 26px;
}

.workspace-header p {
  margin: 6px 0 0;
  color: #607086;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(320px, 420px) minmax(360px, 1fr);
  gap: 16px;
  align-items: start;
}

.panel {
  padding: 18px;
  border: 1px solid #dce3ee;
  border-radius: 8px;
  background: white;
}

.detail-panel {
  grid-row: span 2;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.panel h2,
.panel h3 {
  margin: 0;
}

.panel h3 {
  margin-top: 16px;
  margin-bottom: 8px;
  font-size: 15px;
}

.task-form {
  display: grid;
  gap: 14px;
}

label {
  display: grid;
  gap: 6px;
  color: #43546a;
  font-size: 14px;
  font-weight: 600;
}

select,
textarea {
  width: 100%;
  border: 1px solid #c9d4e5;
  border-radius: 8px;
  padding: 10px 12px;
  color: #172033;
  background: white;
}

textarea {
  resize: vertical;
}

.form-grid {
  display: grid;
  gap: 10px;
}

.form-grid div,
.compact-item {
  display: grid;
  gap: 4px;
  padding: 10px;
  border: 1px solid #e2e8f2;
  border-radius: 8px;
  background: #f8fafd;
}

.form-grid span,
.compact-item span {
  color: #607086;
  font-size: 13px;
  word-break: break-word;
}

.task-form button[type="submit"] {
  min-height: 42px;
  border: 0;
  border-radius: 8px;
  color: white;
  background: #26735f;
  font-weight: 700;
}

.task-form button[type="submit"]:disabled {
  cursor: not-allowed;
  background: #91a7a1;
}

.task-list,
.compact-list {
  display: grid;
  gap: 8px;
}

.task-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  min-height: 48px;
  padding: 10px 12px;
  border: 1px solid #e2e8f2;
  border-radius: 8px;
  color: #172033;
  background: #f8fafd;
  text-align: left;
}

.task-row span:first-child {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-row.active {
  border-color: #26735f;
  background: #eef8f5;
}

.status {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 64px;
  min-height: 26px;
  border-radius: 999px;
  padding: 3px 8px;
  font-size: 12px;
  font-weight: 700;
}

.status-completed {
  color: #17644f;
  background: #dff5ee;
}

.status-failed {
  color: #9b1c1c;
  background: #fde2e2;
}

.status-draft,
.status-queued,
.status-script_ready,
.status-audio_ready,
.status-rendered,
.status-post_processed {
  color: #4e5d78;
  background: #e9edf5;
}

.script-box {
  margin: 0;
  padding: 12px;
  border-radius: 8px;
  color: #253449;
  background: #f8fafd;
  line-height: 1.6;
}

.error-banner {
  margin-bottom: 16px;
  padding: 12px;
  border: 1px solid #f1b8b8;
  border-radius: 8px;
  color: #8c1d1d;
  background: #fff1f1;
}

@media (max-width: 900px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    position: sticky;
    top: 0;
    z-index: 1;
  }

  .sidebar nav {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 10: Run frontend tests and build**

Run:

```powershell
cd frontend
npm test
npm run build
```

Expected: tests and build pass.

- [ ] **Step 11: Commit management UI**

Run:

```powershell
git add frontend
git commit -m "feat: add management UI"
```

## Task 8: End-To-End Demo Verification

**Files:**
- Modify: `backend/README.md`
- Modify: `README.md`

- [ ] **Step 1: Update root README with full run instructions**

Replace `README.md`:

```markdown
# Digital Human Video Platform

This repository contains the design and MVP implementation for a digital human video generation platform.

The MVP proves the first full workflow with mock providers:

- Create a video task from topic, existing script, or reference material.
- Generate or normalize a script.
- Produce a mock TTS artifact.
- Produce a mock avatar-rendered artifact.
- Produce a mock final MP4 artifact path and cover artifact.
- Review tasks, logs, profiles, voices, and generated assets in a Web UI.

Real cloud LLM, TTS, LiveTalking/Wav2Lip, and FFmpeg integrations are planned as provider replacements after this skeleton.

## Documentation

- Design spec: `docs/superpowers/specs/2026-06-19-digital-human-video-platform-design.md`
- MVP plan: `docs/superpowers/plans/2026-06-19-digital-human-video-platform-mvp.md`

## Backend

```powershell
cd backend
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Backend URL: `http://localhost:8000`

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend URL: `http://localhost:5173`

## Verification

```powershell
cd backend
pytest -q
ruff check .

cd ..\\frontend
npm test
npm run build
```
```

- [ ] **Step 2: Update backend README with API endpoints**

Replace `backend/README.md`:

```markdown
# Backend

## Setup

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -e ".[dev]"
```

## Run

```powershell
uvicorn app.main:app --reload
```

## Test

```powershell
pytest
ruff check .
```

## Main Endpoints

- `GET /health`
- `GET /api/digital-humans`
- `GET /api/voices`
- `GET /api/post-process-templates`
- `GET /api/tasks`
- `POST /api/tasks`
- `GET /api/tasks/{task_id}`
```

- [ ] **Step 3: Run backend verification**

Run:

```powershell
cd backend
pytest -q
ruff check .
```

Expected: all tests and lint pass.

- [ ] **Step 4: Run frontend verification**

Run:

```powershell
cd frontend
npm test
npm run build
```

Expected: frontend tests and production build pass.

- [ ] **Step 5: Manual API smoke test**

Start backend:

```powershell
cd backend
uvicorn app.main:app --port 8000
```

In another terminal, run:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/tasks -ContentType "application/json" -Body '{"input_mode":"existing_script","raw_input":"这是一条手动验证的口播文案。","digital_human_profile_id":1,"voice_profile_id":1,"post_process_template_id":1}'
```

Expected: response contains `"current_state": "completed"` and a `final_video_path`.

- [ ] **Step 6: Manual Web smoke test**

Start frontend:

```powershell
cd frontend
npm run dev
```

Open `http://localhost:5173`.

Expected:

- The dashboard loads.
- Default Presenter appears.
- Default Voice appears.
- Creating a task adds a completed task.
- Selecting the task shows generated script, logs, and asset paths.

- [ ] **Step 7: Commit documentation and verified MVP**

Run:

```powershell
git add README.md backend/README.md
git commit -m "docs: add MVP run instructions"
```

## Self-Review Checklist

Spec coverage:

- Three input modes are represented in API and UI task creation.
- Digital human profiles, voices, templates, tasks, scripts, assets, and logs are modeled.
- Serial task execution is implemented by `TaskRunner`.
- Mock providers cover LLM, TTS, avatar rendering, and post-processing.
- Web UI covers dashboard, task creation, profile list, voice list, task list, and task detail.
- Failure logging is implemented in the runner, though a dedicated retry API is not included in this first executable increment.

Known follow-up plans:

- Add retry endpoint and failed-step restart semantics.
- Replace mock LLM with cloud LLM provider.
- Replace mock TTS with real TTS provider.
- Replace mock avatar renderer with LiveTalking/Wav2Lip adapter.
- Replace mock post-processing with FFmpeg implementation.
- Add reference video upload handling.
