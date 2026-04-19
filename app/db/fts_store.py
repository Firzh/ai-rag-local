from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any

from app.config import settings


def tokenize_query(query: str) -> list[str]:
    terms = re.findall(r"[A-Za-z0-9_][A-Za-z0-9_\-]{2,}", query.lower())
    stop = {
        "apa", "itu", "yang", "dan", "atau", "dari", "untuk", "pada", "dalam",
        "bagaimana", "adalah", "ini", "the", "and", "for", "with", "what",
        "how", "why",
    }
    return [term for term in terms if term not in stop]


def build_fts_query(query: str) -> str:
    terms = tokenize_query(query)
    if not terms:
        return ""

    # OR lebih toleran untuk dokumen pendek dan query Bahasa Indonesia.
    return " OR ".join(f'"{term}"' for term in terms)


class FTSStore:
    def __init__(self) -> None:
        settings.indexes_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = settings.indexes_dir / "fts.sqlite3"
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        cur = self.conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            chroma_id TEXT PRIMARY KEY,
            document TEXT NOT NULL,
            metadata_json TEXT NOT NULL,
            source_name TEXT,
            source_path TEXT,
            parser TEXT,
            chunk_index INTEGER,
            document_hash TEXT
        )
        """)

        cur.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS chunk_fts
        USING fts5(
            chroma_id UNINDEXED,
            document,
            source_name,
            parser,
            tokenize='unicode61'
        )
        """)

        self.conn.commit()

    def upsert_chunks(
        self,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        cur = self.conn.cursor()

        for chroma_id, document, metadata in zip(ids, documents, metadatas):
            metadata = metadata or {}

            source_name = metadata.get("source_name", "")
            source_path = metadata.get("source_path", "")
            parser = metadata.get("parser", "")
            chunk_index = int(metadata.get("chunk_index", 0))
            document_hash = metadata.get("document_hash", "")

            cur.execute("DELETE FROM chunks WHERE chroma_id = ?", (chroma_id,))
            cur.execute("DELETE FROM chunk_fts WHERE chroma_id = ?", (chroma_id,))

            cur.execute(
                """
                INSERT INTO chunks (
                    chroma_id, document, metadata_json, source_name,
                    source_path, parser, chunk_index, document_hash
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chroma_id,
                    document,
                    json.dumps(metadata, ensure_ascii=False),
                    source_name,
                    source_path,
                    parser,
                    chunk_index,
                    document_hash,
                ),
            )

            cur.execute(
                """
                INSERT INTO chunk_fts (
                    chroma_id, document, source_name, parser
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    chroma_id,
                    document,
                    source_name,
                    parser,
                ),
            )

        self.conn.commit()

    def delete_by_document_hash(self, document_hash: str) -> None:
        cur = self.conn.cursor()

        rows = cur.execute(
            "SELECT chroma_id FROM chunks WHERE document_hash = ?",
            (document_hash,),
        ).fetchall()

        for row in rows:
            chroma_id = row["chroma_id"]
            cur.execute("DELETE FROM chunk_fts WHERE chroma_id = ?", (chroma_id,))

        cur.execute("DELETE FROM chunks WHERE document_hash = ?", (document_hash,))
        self.conn.commit()

    def search(self, query: str, top_k: int | None = None) -> list[dict[str, Any]]:
        fts_query = build_fts_query(query)
        if not fts_query:
            return []

        limit = top_k or settings.fts_top_k

        cur = self.conn.cursor()

        rows = cur.execute(
            """
            SELECT
                f.chroma_id,
                c.document,
                c.metadata_json,
                bm25(chunk_fts) AS bm25_score
            FROM chunk_fts f
            JOIN chunks c ON c.chroma_id = f.chroma_id
            WHERE chunk_fts MATCH ?
            ORDER BY bm25_score ASC
            LIMIT ?
            """,
            (fts_query, limit),
        ).fetchall()

        results = []

        for row in rows:
            results.append(
                {
                    "chroma_id": row["chroma_id"],
                    "document": row["document"],
                    "metadata": json.loads(row["metadata_json"]),
                    "bm25_score": float(row["bm25_score"]),
                    "source": "fts",
                }
            )

        return results

    def count(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS n FROM chunks").fetchone()
        return int(row["n"])

    def close(self) -> None:
        self.conn.close()