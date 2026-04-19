from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.config import settings


class Historian:
    def __init__(self) -> None:
        settings.memory_dir.mkdir(parents=True, exist_ok=True)

        self.decisions_path = settings.memory_dir / "project_decisions.md"
        self.session_notes_path = settings.memory_dir / "session_notes.md"
        self.rag_memory_path = settings.memory_dir / "rag_memory.md"

        self._ensure_files()

    def _ensure_files(self) -> None:
        for path, title in [
            (self.decisions_path, "# Project Decisions\n"),
            (self.session_notes_path, "# Session Notes\n"),
            (self.rag_memory_path, "# RAG Memory\n"),
        ]:
            if not path.exists():
                path.write_text(title + "\n", encoding="utf-8")

    def append_decision(self, text: str) -> None:
        self._append(self.decisions_path, text)

    def append_session_note(self, text: str) -> None:
        self._append(self.session_notes_path, text)

    def append_rag_memory(self, text: str) -> None:
        self._append(self.rag_memory_path, text)

    def _append(self, path: Path, text: str) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        with path.open("a", encoding="utf-8") as f:
            f.write(f"\n## {timestamp}\n\n{text.strip()}\n")