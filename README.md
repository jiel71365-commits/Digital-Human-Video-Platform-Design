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
.\.venv\Scripts\Activate.ps1
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

cd ..\frontend
npm test
npm run build
```
