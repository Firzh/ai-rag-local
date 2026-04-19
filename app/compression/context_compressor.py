from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings
from app.hybrid_retrieval import HybridRetriever
from app.reranker import query_terms, CandidateChunk


def split_sentences(text: str) -> list[str]:
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return []

    parts = re.split(r"(?<=[.!?])\s+", text)
    return [part.strip() for part in parts if part.strip()]


def sentence_score(sentence: str, terms: set[str]) -> int:
    s = sentence.lower()
    return sum(1 for term in terms if term in s)


class ContextCompressor:
    def __init__(self) -> None:
        self.retriever = HybridRetriever()

    def extract_facts(self, query: str, chunks: list[CandidateChunk]) -> list[dict]:
        terms = query_terms(query)
        facts = []

        for chunk in chunks:
            sentences = split_sentences(chunk.document)

            scored_sentences = []
            for sentence in sentences:
                score = sentence_score(sentence, terms)
                if score > 0:
                    scored_sentences.append((score, sentence))

            scored_sentences.sort(key=lambda x: x[0], reverse=True)

            if not scored_sentences and chunk.score > 0.30:
                # fallback: pakai awal chunk jika tidak ada sentence match
                preview = chunk.document.strip()[:300]
                if preview:
                    scored_sentences.append((1, preview))

            for score, sentence in scored_sentences[:2]:
                facts.append(
                    {
                        "text": sentence[:settings.compress_max_quote_chars],
                        "source_name": chunk.metadata.get("source_name", "unknown"),
                        "parser": chunk.metadata.get("parser", "unknown"),
                        "chunk_index": chunk.metadata.get("chunk_index", "unknown"),
                        "retrieval": chunk.source,
                        "score": round(float(chunk.score), 4),
                    }
                )

        return facts[:settings.compress_max_facts]

    def extract_quotes(self, chunks: list[CandidateChunk]) -> list[dict]:
        quotes = []

        for chunk in chunks[:settings.compress_max_quotes]:
            text = chunk.document.strip()
            if not text:
                continue

            quotes.append(
                {
                    "quote": text[:settings.compress_max_quote_chars],
                    "source_name": chunk.metadata.get("source_name", "unknown"),
                    "chunk_index": chunk.metadata.get("chunk_index", "unknown"),
                    "retrieval": chunk.source,
                    "score": round(float(chunk.score), 4),
                }
            )

        return quotes

    def build_evidence_pack(self, query: str) -> dict:
        chunks = self.retriever.retrieve(query)
        facts = self.extract_facts(query, chunks)
        quotes = self.extract_quotes(chunks)

        sources = []
        seen_sources = set()

        for chunk in chunks:
            key = (
                chunk.metadata.get("source_name", "unknown"),
                chunk.metadata.get("chunk_index", "unknown"),
            )

            if key in seen_sources:
                continue

            seen_sources.add(key)

            sources.append(
                {
                    "source_name": key[0],
                    "chunk_index": key[1],
                    "parser": chunk.metadata.get("parser", "unknown"),
                    "retrieval": chunk.source,
                    "score": round(float(chunk.score), 4),
                    "distance": round(float(chunk.distance), 4) if chunk.distance is not None else None,
                    "bm25_score": round(float(chunk.bm25_score), 4) if chunk.bm25_score is not None else None,
                }
            )

        uncertainty = []

        if not chunks:
            uncertainty.append("Tidak ada chunk relevan yang ditemukan.")

        if chunks and chunks[0].score < 0.25:
            uncertainty.append("Skor kandidat tertinggi rendah; jawaban perlu dianggap tidak pasti.")

        if not facts:
            uncertainty.append("Tidak ada fakta eksplisit yang cocok langsung dengan query.")

        return {
            "query": query,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "sources": sources,
            "important_facts": facts,
            "important_quotes": quotes,
            "uncertainty": uncertainty,
            "llm_instruction": (
                "Jawab hanya berdasarkan evidence pack ini. "
                "Jika evidence tidak cukup, nyatakan bahwa dokumen belum cukup mendukung jawaban."
            ),
        }

    def save_evidence_pack(self, evidence_pack: dict) -> Path:
        settings.evidence_dir.mkdir(parents=True, exist_ok=True)

        safe_name = re.sub(r"[^a-zA-Z0-9_\-]+", "_", evidence_pack["query"].lower())
        safe_name = safe_name.strip("_")[:80] or "query"

        path = settings.evidence_dir / f"{safe_name}.evidence.json"

        with path.open("w", encoding="utf-8") as f:
            json.dump(evidence_pack, f, indent=2, ensure_ascii=False)

        return path

    def to_prompt_context(self, evidence_pack: dict) -> str:
        lines = []
        lines.append("Pertanyaan pengguna:")
        lines.append(evidence_pack["query"])
        lines.append("")
        lines.append("Sumber relevan:")

        for i, source in enumerate(evidence_pack["sources"], start=1):
            lines.append(
                f"{i}. {source['source_name']} | chunk {source['chunk_index']} | "
                f"retrieval={source['retrieval']} | score={source['score']}"
            )

        lines.append("")
        lines.append("Fakta penting:")

        for fact in evidence_pack["important_facts"]:
            lines.append(
                f"- {fact['text']} "
                f"(sumber: {fact['source_name']}, chunk {fact['chunk_index']})"
            )

        lines.append("")
        lines.append("Kutipan pendek penting:")

        for quote in evidence_pack["important_quotes"]:
            lines.append(
                f"- \"{quote['quote']}\" "
                f"(sumber: {quote['source_name']}, chunk {quote['chunk_index']})"
            )

        lines.append("")
        lines.append("Status evidence:")

        if evidence_pack["uncertainty"]:
            lines.append("Evidence belum sepenuhnya kuat.")
            lines.append("")
            lines.append("Ketidakpastian:")
            for item in evidence_pack["uncertainty"]:
                lines.append(f"- {item}")
            lines.append("")
            lines.append("Instruksi untuk LLM:")
            lines.append(
                "Jika fakta di atas tidak cukup untuk menjawab, tulis hanya: "
                "Dokumen belum cukup mendukung jawaban."
            )
        else:
            lines.append("Evidence cukup untuk menjawab pertanyaan.")
            lines.append("")
            lines.append("Instruksi untuk LLM:")
            lines.append(
                "Jawab langsung berdasarkan fakta penting dan kutipan pendek. "
                "Jangan menulis frasa 'Dokumen belum cukup mendukung jawaban' "
                "karena evidence sudah cukup."
            )

        return "\n".join(lines)