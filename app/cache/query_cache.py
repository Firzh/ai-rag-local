from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.config import settings


@dataclass
class CachedAnswer:
    query: str
    answer: str
    provider: str
    model: str
    record: dict[str, Any]
    created_at: str
    expires_at: str


def normalize_query(query: str) -> str:
    return " ".join(query.strip().lower().split())


def query_hash(query: str) -> str:
    normalized = normalize_query(query)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class QueryCache:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or settings.api_usage_db
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS query_cache (
                    query_hash TEXT PRIMARY KEY,
                    normalized_query TEXT NOT NULL,
                    original_query TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    record_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
                """
            )

    def get(self, query: str) -> CachedAnswer | None:
        if not settings.api_cache_enabled:
            return None

        qh = query_hash(query)
        now = utc_now().isoformat()

        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM query_cache
                WHERE query_hash = ?
                  AND expires_at > ?
                """,
                (qh, now),
            ).fetchone()

        if row is None:
            return None

        return CachedAnswer(
            query=row["original_query"],
            answer=row["answer"],
            provider=row["provider"],
            model=row["model"],
            record=json.loads(row["record_json"]),
            created_at=row["created_at"],
            expires_at=row["expires_at"],
        )

    def set(
        self,
        *,
        query: str,
        answer: str,
        provider: str,
        model: str,
        record: dict[str, Any],
        ttl_hours: int | None = None,
    ) -> None:
        if not settings.api_cache_enabled:
            return

        ttl_hours = ttl_hours or settings.api_cache_ttl_hours
        now = utc_now()
        expires = now + timedelta(hours=ttl_hours)

        normalized = normalize_query(query)
        qh = query_hash(query)

        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO query_cache (
                    query_hash,
                    normalized_query,
                    original_query,
                    answer,
                    provider,
                    model,
                    record_json,
                    created_at,
                    expires_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    qh,
                    normalized,
                    query,
                    answer,
                    provider,
                    model,
                    json.dumps(record, ensure_ascii=False),
                    now.isoformat(),
                    expires.isoformat(),
                ),
            )