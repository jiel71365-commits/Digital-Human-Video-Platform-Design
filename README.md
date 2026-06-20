# Digital Human Video Platform

This repository contains the design and MVP implementation for a digital human video generation platform.

The MVP proves the first full workflow with mock providers:

- Create a video task from topic, existing script, or reference material.
- Generate or normalize a script.
- Produce a mock TTS artifact.
- Produce a mock avatar-rendered artifact.
- Produce a mock final MP4 artifact path and cover artifact.
- Review tasks, logs, profiles, voices, and generated assets in a Web UI.

Real cloud LLM, TTS, LiveTalking, and livestream integrations are planned as provider replacements after this skeleton.
The backend now includes a Wav2Lip renderer adapter: when local Wav2Lip files are present it tries
real lip-sync rendering first, and when they are missing or fail it falls back to the local preview
renderer so tasks still produce a playable MP4.

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

### Optional Wav2Lip Runtime

Large model files are intentionally kept out of Git under `models/`.

Default expected local files:

- `models/Wav2Lip/inference.py`
- `models/Wav2Lip/checkpoints/wav2lip_gan.pth`
- `models/Wav2Lip/face_detection/detection/sfd/s3fd.pth`
- `models/default-presenter.mp4`

Prepare these assets with:

```powershell
python scripts/setup_wav2lip.py
```

Runtime settings can be overridden with `DHVP_` environment variables:

- `DHVP_ENABLE_WAV2LIP=false` disables Wav2Lip and always uses the local preview renderer.
- `DHVP_WAV2LIP_ROOT`
- `DHVP_WAV2LIP_CHECKPOINT_PATH`
- `DHVP_WAV2LIP_FACE_DETECTOR_PATH`
- `DHVP_WAV2LIP_DEFAULT_FACE_PATH`
- `DHVP_WAV2LIP_PYTHON_PATH` points the adapter to a separate Python environment if needed.

The original Wav2Lip open-source repo targets old Python dependencies. On modern Python,
`audio.py` may need the current `librosa.filters.mel(...)` keyword-argument call, and Windows
may need its final ffmpeg call to run through `shell=True`. Those compatibility edits should be
applied in the ignored local `models/Wav2Lip` directory, not committed to this repository.

Runtime readiness is exposed at `GET /api/runtime/wav2lip`. The response reports whether
Wav2Lip is enabled, whether all local files are available, which renderer will be used, and which
requirements are missing.

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
