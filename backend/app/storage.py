from pathlib import Path


class TaskStorage:
    def __init__(self, root: Path) -> None:
        self.root = root

    def task_dir(self, task_id: int) -> Path:
        path = self.root / "tasks" / str(task_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def artifact_path(self, task_id: int, group: str, filename: str) -> Path:
        safe_group = self._sanitize(group)
        safe_filename = self._sanitize(filename)
        task_dir = self.task_dir(task_id)
        path = task_dir / safe_group / safe_filename
        self._ensure_within_task_dir(task_dir, path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def digital_human_source_media_path(self, profile_id: int, suffix: str) -> Path:
        safe_suffix = suffix.lower()
        if safe_suffix not in {".mp4", ".mov", ".jpg", ".jpeg", ".png"}:
            raise ValueError(f"Unsupported source media suffix: {suffix!r}")
        path = self.root / "digital-humans" / str(profile_id) / f"source-media{safe_suffix}"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _sanitize(value: str) -> str:
        sanitized = value.strip()
        if sanitized in {"", ".", ".."} or "/" in sanitized or "\\" in sanitized:
            raise ValueError(f"Invalid artifact path segment: {value!r}")
        return sanitized

    @staticmethod
    def _ensure_within_task_dir(task_dir: Path, path: Path) -> None:
        resolved_task_dir = task_dir.resolve()
        resolved_path = path.resolve()
        if resolved_path != resolved_task_dir and resolved_task_dir not in resolved_path.parents:
            raise ValueError(f"Invalid artifact path outside task directory: {path}")
