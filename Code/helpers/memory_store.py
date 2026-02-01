import json
from pathlib import Path
from typing import Optional

from schemas.session_summary import SessionSummary


class MemoryStore:
    """
    Memory store for session summaries.
    """

    def __init__(self, base_dir: str = "memory_storage"):
        self.base_path = Path(base_dir)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_session_path(self, session_id: str) -> Path:
        return self.base_path / f"{session_id}.json"

    def save_summary(self, session_id: str, summary: SessionSummary) -> None:
        """
        Persist SessionSummary for a session.
        """
        path = self._get_session_path(session_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary.model_dump(), f, ensure_ascii=False, indent=2)

    def load_summary(self, session_id: str) -> Optional[SessionSummary]:
        """
        Load SessionSummary for a session if exists.
        """
        path = self._get_session_path(session_id)
        if not path.exists():
            return None

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return SessionSummary(**data)

    def delete_summary(self, session_id: str) -> None:
        """
        Remove stored summary for a session.
        """
        path = self._get_session_path(session_id)
        if path.exists():
            path.unlink()

    def list_summaries(self) -> list[str]:
        """
        List all session IDs with stored summaries.
        """
        return [p.stem for p in self.base_path.glob("*.json")]
    