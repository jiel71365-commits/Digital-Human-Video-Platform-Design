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
        path = self.task_dir(task_id) / safe_group / safe_filename
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _sanitize(value: str) -> str:
        return value.strip().replace("\\", "_").replace("/", "_")
