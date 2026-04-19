import json
from pathlib import Path
from datetime import datetime, timezone

from app.config import settings


class ManifestStore:
    def __init__(self) -> None:
        self.path = settings.cache_dir / "ingest_manifest.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> dict:
        if not self.path.exists():
            return {"files": {}}

        try:
            with self.path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"files": {}}

    def save(self) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def get(self, source_path: str) -> dict | None:
        return self.data.get("files", {}).get(source_path)

    def is_unchanged(self, source_path: str, document_hash: str) -> bool:
        record = self.get(source_path)
        if not record:
            return False
        return record.get("document_hash") == document_hash

    def update(
        self,
        source_path: str,
        source_name: str,
        document_hash: str,
        parser: str,
        chunks_count: int,
    ) -> None:
        self.data.setdefault("files", {})[source_path] = {
            "source_path": source_path,
            "source_name": source_name,
            "document_hash": document_hash,
            "parser": parser,
            "chunks_count": chunks_count,
            "indexed_at": datetime.now(timezone.utc).isoformat(),
        }
        self.save()

    def remove(self, source_path: str) -> None:
        self.data.setdefault("files", {}).pop(source_path, None)
        self.save()

    def all_files(self) -> dict:
        return self.data.get("files", {})