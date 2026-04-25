from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None

from app.config import settings


PACIFIC_TZ = "America/Los_Angeles"


@dataclass
class ApiUsageSummary:
    usage_date: str
    provider: str
    model: str
    requests_total: int
    requests_success: int
    requests_error: int
    rate_limited_count: int
    auth_error_count: int
    total_tokens: int
    input_tokens: int
    output_tokens: int
    cache_hits: int
    fallback_count: int


def current_usage_date() -> str:
    now_utc = datetime.now(timezone.utc)

    if ZoneInfo is not None:
        try:
            return now_utc.astimezone(ZoneInfo(PACIFIC_TZ)).date().isoformat()
        except Exception:
            pass

    return now_utc.date().isoformat()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ApiUsageStore:
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
                CREATE TABLE IF NOT EXISTS api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    usage_date TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    status_code INTEGER,
                    error_type TEXT,
                    latency_ms REAL,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    cache_hit INTEGER DEFAULT 0,
                    fallback_used INTEGER DEFAULT 0,
                    query_hash TEXT,
                    metadata_json TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_api_usage_date_provider_model
                ON api_usage (usage_date, provider, model)
                """
            )

    def record_call(
        self,
        *,
        provider: str,
        model: str,
        success: bool,
        status_code: int | None = None,
        error_type: str | None = None,
        latency_ms: float | None = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        total_tokens: int = 0,
        cache_hit: bool = False,
        fallback_used: bool = False,
        query_hash: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        import json

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO api_usage (
                    created_at,
                    usage_date,
                    provider,
                    model,
                    success,
                    status_code,
                    error_type,
                    latency_ms,
                    input_tokens,
                    output_tokens,
                    total_tokens,
                    cache_hit,
                    fallback_used,
                    query_hash,
                    metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    utc_now_iso(),
                    current_usage_date(),
                    provider,
                    model,
                    1 if success else 0,
                    status_code,
                    error_type,
                    latency_ms,
                    int(input_tokens or 0),
                    int(output_tokens or 0),
                    int(total_tokens or 0),
                    1 if cache_hit else 0,
                    1 if fallback_used else 0,
                    query_hash,
                    json.dumps(metadata or {}, ensure_ascii=False),
                ),
            )

    def summary_today(
        self,
        *,
        provider: str | None = None,
        model: str | None = None,
    ) -> ApiUsageSummary:
        usage_date = current_usage_date()
        provider = provider or settings.api_quota_provider
        model = model or settings.api_quota_model

        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    SUM(CASE WHEN cache_hit = 0 THEN 1 ELSE 0 END) AS requests_total,
                    SUM(CASE WHEN success = 1 AND cache_hit = 0 THEN 1 ELSE 0 END) AS requests_success,
                    SUM(CASE WHEN success = 0 AND cache_hit = 0 THEN 1 ELSE 0 END) AS requests_error,
                    SUM(CASE WHEN error_type = 'rate_limited' AND cache_hit = 0 THEN 1 ELSE 0 END) AS rate_limited_count,
                    SUM(CASE WHEN error_type = 'auth_error' AND cache_hit = 0 THEN 1 ELSE 0 END) AS auth_error_count,
                    SUM(CASE WHEN cache_hit = 0 THEN input_tokens ELSE 0 END) AS input_tokens,
                    SUM(CASE WHEN cache_hit = 0 THEN output_tokens ELSE 0 END) AS output_tokens,
                    SUM(CASE WHEN cache_hit = 0 THEN total_tokens ELSE 0 END) AS total_tokens,
                    SUM(CASE WHEN cache_hit = 1 THEN 1 ELSE 0 END) AS cache_hits,
                    SUM(CASE WHEN fallback_used = 1 THEN 1 ELSE 0 END) AS fallback_count
                FROM api_usage
                WHERE usage_date = ?
                  AND provider = ?
                  AND model = ?
                """,
                (usage_date, provider, model),
            ).fetchone()

        return ApiUsageSummary(
            usage_date=usage_date,
            provider=provider,
            model=model,
            requests_total=int(row["requests_total"] or 0),
            requests_success=int(row["requests_success"] or 0),
            requests_error=int(row["requests_error"] or 0),
            rate_limited_count=int(row["rate_limited_count"] or 0),
            auth_error_count=int(row["auth_error_count"] or 0),
            input_tokens=int(row["input_tokens"] or 0),
            output_tokens=int(row["output_tokens"] or 0),
            total_tokens=int(row["total_tokens"] or 0),
            cache_hits=int(row["cache_hits"] or 0),
            fallback_count=int(row["fallback_count"] or 0),
        )

    def rpd_exceeded(self, *, provider: str | None = None, model: str | None = None) -> bool:
        if not settings.api_quota_enabled:
            return False

        summary = self.summary_today(provider=provider, model=model)
        return summary.requests_total >= settings.api_rpd_limit

    def warning_level(self, *, provider: str | None = None, model: str | None = None) -> str:
        summary = self.summary_today(provider=provider, model=model)

        if summary.requests_total >= settings.api_rpd_limit:
            return "exceeded"

        if summary.requests_total >= settings.api_daily_request_hard_warn:
            return "hard_warning"

        if summary.requests_total >= settings.api_daily_request_warn:
            return "warning"

        return "safe"