from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


def query_terms(query: str) -> set[str]:
    stop = {
        "apa", "itu", "yang", "dan", "atau", "dari", "untuk", "pada", "dalam",
        "bagaimana", "adalah", "ini", "the", "and", "for", "with", "what",
        "how", "why",
    }

    terms = re.findall(r"[A-Za-z0-9_][A-Za-z0-9_\-]{2,}", query.lower())
    return {term for term in terms if term not in stop}


def keyword_overlap_score(query: str, text: str, source_name: str = "") -> float:
    terms = query_terms(query)
    if not terms:
        return 0.0

    haystack = f"{source_name}\n{text}".lower()
    matched = sum(1 for term in terms if term in haystack)
    return matched / max(len(terms), 1)


@dataclass
class CandidateChunk:
    chroma_id: str
    document: str
    metadata: dict[str, Any]
    distance: float | None = None
    bm25_score: float | None = None
    source: str = "unknown"
    score: float = 0.0


class HeuristicReranker:
    def score_candidate(self, query: str, candidate: CandidateChunk) -> float:
        source_name = candidate.metadata.get("source_name", "")
        overlap = keyword_overlap_score(query, candidate.document, source_name)

        score = 0.0

        # Vector distance: semakin kecil semakin baik.
        if candidate.distance is not None:
            vector_score = max(0.0, 1.0 - float(candidate.distance))
            score += 0.65 * vector_score

        # FTS/BM25: score biasanya negatif/kecil; cukup beri bonus jika match.
        if candidate.bm25_score is not None:
            score += 0.20

        # Keyword overlap.
        score += 0.35 * overlap

        # Source boost.
        if candidate.source == "vector":
            score += 0.05
        elif candidate.source == "fts":
            score += 0.08
        elif candidate.source == "graph":
            score += 0.03

        return score

    def rerank(
        self,
        query: str,
        candidates: list[CandidateChunk],
        top_k: int,
        distance_cutoff: float | None = None,
        score_cutoff: float | None = None,
    ) -> list[CandidateChunk]:
        dedup: dict[str, CandidateChunk] = {}

        for candidate in candidates:
            existing = dedup.get(candidate.chroma_id)

            if existing is None:
                dedup[candidate.chroma_id] = candidate
                continue

            # Gabungkan sinyal dari beberapa retrieval source.
            if existing.distance is None or (
                candidate.distance is not None and candidate.distance < existing.distance
            ):
                existing.distance = candidate.distance

            if existing.bm25_score is None:
                existing.bm25_score = candidate.bm25_score

            if candidate.source not in existing.source:
                existing.source = f"{existing.source}+{candidate.source}"

        scored = []

        for candidate in dedup.values():
            if (
                distance_cutoff is not None
                and candidate.distance is not None
                and candidate.distance > distance_cutoff
                and candidate.bm25_score is None
            ):
                # Vector terlalu jauh dan tidak ada dukungan keyword.
                continue

            candidate.score = self.score_candidate(query, candidate)

            if score_cutoff is not None and candidate.score < score_cutoff:
                continue

            scored.append(candidate)

        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_k]