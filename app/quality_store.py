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