# Backend

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
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
