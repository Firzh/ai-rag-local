from __future__ import annotations

import re


STOPWORDS = {
    "adalah", "yang", "dan", "atau", "dari", "untuk", "pada", "dalam",
    "ini", "itu", "dengan", "sebagai", "oleh", "ke", "di", "lalu",
    "maka", "agar", "akan", "bisa", "dapat", "secara", "berdasarkan",
    "the", "and", "or", "from", "with", "for", "this", "that", "into",
    "are", "was", "were", "been", "have", "has", "had",
}


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\u00C0-\u024F\u1E00-\u1EFF\s]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


class EvidenceVerifier:
    def verify_answer(self, answer: str, evidence_pack: dict) -> dict:
        evidence_text_parts = []

        for fact in evidence_pack.get("important_facts", []):
            evidence_text_parts.append(fact.get("text", ""))

        for quote in evidence_pack.get("important_quotes", []):
            evidence_text_parts.append(quote.get("quote", ""))

        evidence_text = normalize(" ".join(evidence_text_parts))
        answer_text = normalize(answer)

        answer_terms = {
            term for term in answer_text.split()
            if len(term) >= 4 and term not in STOPWORDS
        }

        if not answer_terms:
            return {
                "supported": False,
                "support_ratio": 0.0,
                "matched_terms": [],
                "notes": ["Jawaban terlalu pendek atau hanya berisi stopword."],
            }

        matched = {
            term for term in answer_terms
            if term in evidence_text
        }

        support_ratio = len(matched) / max(len(answer_terms), 1)

        notes = []

        if not evidence_pack.get("important_facts") and not evidence_pack.get("important_quotes"):
            notes.append("Evidence pack kosong atau sangat lemah.")

        if support_ratio < 0.35:
            notes.append("Banyak istilah dalam jawaban tidak ditemukan pada evidence pack.")

        return {
            "supported": support_ratio >= 0.35,
            "support_ratio": round(support_ratio, 4),
            "matched_terms": sorted(matched),
            "notes": notes,
        }