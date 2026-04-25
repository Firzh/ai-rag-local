from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from app.config import settings


class AnswerQualityStore:
    def __init__(self) -> None:
        settings.quality_dir.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(settings.quality_db))
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        cur = self.conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS answer_quality (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            query TEXT NOT NULL,
            answer TEXT NOT NULL,
            evidence_path TEXT,
            supported INTEGER,
            support_ratio REAL,
            fallback_used INTEGER,
            artifact_like INTEGER,
            quality_score REAL,
            issue_tags_json TEXT,
            matched_terms_json TEXT,
            verification_json TEXT,
            metadata_json TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS quality_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            answer_quality_id INTEGER,
            feedback_label TEXT NOT NULL,
            feedback_note TEXT,
            corrected_answer TEXT,
            FOREIGN KEY(answer_quality_id) REFERENCES answer_quality(id)
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS answer_verification_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            answer_quality_id INTEGER,
            query TEXT NOT NULL,
            answer TEXT NOT NULL,
            verifier_name TEXT NOT NULL,
            supported INTEGER,
            confidence REAL,
            latency_ms REAL,
            verdict_json TEXT NOT NULL,
            metadata_json TEXT,
            FOREIGN KEY(answer_quality_id) REFERENCES answer_quality(id)
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS quality_promotions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            answer_quality_id INTEGER,
            promoted_to TEXT NOT NULL,
            promoted INTEGER NOT NULL,
            reason TEXT,
            metadata_json TEXT,
            FOREIGN KEY(answer_quality_id) REFERENCES answer_quality(id)
        )
        """)

        self.conn.commit()

    def insert_answer_record(
        self,
        query: str,
        answer: str,
        evidence_path: str,
        verification: dict[str, Any],
        artifact_like: bool,
        quality_score: float,
        issue_tags: list[str],
        metadata: dict[str, Any] | None = None,
    ) -> int:
        cur = self.conn.cursor()

        cur.execute(
            """
            INSERT INTO answer_quality (
                created_at, query, answer, evidence_path,
                supported, support_ratio, fallback_used, artifact_like,
                quality_score, issue_tags_json, matched_terms_json,
                verification_json, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                query,
                answer,
                evidence_path,
                1 if verification.get("supported") else 0,
                float(verification.get("support_ratio", 0.0)),
                1 if bool(verification.get("fallback_used", False)) else 0,
                1 if artifact_like else 0,
                float(quality_score),
                json.dumps(issue_tags, ensure_ascii=False),
                json.dumps(verification.get("matched_terms", []), ensure_ascii=False),
                json.dumps(verification, ensure_ascii=False),
                json.dumps(metadata or {}, ensure_ascii=False),
            ),
        )

        self.conn.commit()
        return int(cur.lastrowid)

    def insert_verification_run(
        self,
        query: str,
        answer: str,
        verifier_name: str,
        verdict: dict[str, Any],
        answer_quality_id: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        cur = self.conn.cursor()

        supported = verdict.get("supported")
        confidence = verdict.get("confidence")
        latency_ms = verdict.get("latency_ms")

        try:
            confidence = None if confidence is None else float(confidence)
        except (TypeError, ValueError):
            confidence = None

        try:
            latency_ms = None if latency_ms is None else float(latency_ms)
        except (TypeError, ValueError):
            latency_ms = None

        cur.execute(
            """
            INSERT INTO answer_verification_runs (
                created_at, answer_quality_id, query, answer, verifier_name,
                supported, confidence, latency_ms, verdict_json, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                answer_quality_id,
                query,
                answer,
                verifier_name,
                None if supported is None else (1 if bool(supported) else 0),
                confidence,
                latency_ms,
                json.dumps(verdict, ensure_ascii=False),
                json.dumps(metadata or {}, ensure_ascii=False),
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def log_promotion(
        self,
        promoted_to: str,
        promoted: bool,
        reason: str,
        answer_quality_id: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO quality_promotions (
                created_at, answer_quality_id, promoted_to, promoted,
                reason, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                answer_quality_id,
                promoted_to,
                1 if promoted else 0,
                reason,
                json.dumps(metadata or {}, ensure_ascii=False),
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def add_feedback(
        self,
        answer_quality_id: int,
        feedback_label: str,
        feedback_note: str = "",
        corrected_answer: str = "",
    ) -> None:
        cur = self.conn.cursor()

        cur.execute(
            """
            INSERT INTO quality_feedback (
                created_at, answer_quality_id, feedback_label,
                feedback_note, corrected_answer
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                answer_quality_id,
                feedback_label,
                feedback_note,
                corrected_answer,
            ),
        )

        self.conn.commit()

    def recent_records(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT * FROM answer_quality
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [dict(row) for row in rows]
