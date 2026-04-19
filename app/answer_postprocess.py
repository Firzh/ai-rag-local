from __future__ import annotations

import re

from app.config import settings


INSUFFICIENT_PHRASE = "Dokumen belum cukup mendukung jawaban."


def remove_markdown_heading(text: str) -> str:
    # Hapus heading di awal, contoh: "# AI RAG Lokal"
    text = re.sub(r"^\s*#{1,6}\s+[^\n]+", "", text).strip()

    # Hapus heading inline yang kadang terbawa dari evidence:
    # "# AI RAG Lokal Proyek ini memakai..."
    text = re.sub(
        r"^\s*#{1,6}\s*AI\s+RAG\s+Lokal\s*",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()

    return text


def remove_repeated_sentences(text: str) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    seen = set()
    cleaned = []

    for part in parts:
        key = re.sub(r"\s+", " ", part.lower()).strip()
        if not key:
            continue
        if key in seen:
            continue

        seen.add(key)
        cleaned.append(part.strip())

    return " ".join(cleaned).strip()


def strip_prompt_artifacts(text: str) -> str:
    artifacts = [
        "Jawaban akhir:",
        "Jawaban:",
        "Jawaban pertanyaan secara langsung:",
        "Kutipan pendek penting:",
        "Sumber:",
        "Tugas:",
    ]

    for artifact in artifacts:
        text = text.replace(artifact, "").strip()

    text = re.sub(r"^\s*[-*\d.]+\s*", "", text).strip()
    return text


def normalize_source_format(text: str) -> str:
    text = re.sub(r"\(\s*sumber\s*\)\s*", "", text, flags=re.IGNORECASE)

    text = re.sub(
        r"Sumber:\s*\(sumber:\s*([^()]+?),\s*chunk\s*([0-9]+)\)",
        r"(sumber: \1, chunk \2)",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\((?!sumber:)([^()]+?\.(?:txt|md|pdf|docx|json|csv)),\s*chunk\s*([0-9]+)\)",
        r"(sumber: \1, chunk \2)",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\(sumber:\s*sumber:\s*",
        "(sumber: ",
        text,
        flags=re.IGNORECASE,
    )

    return text.strip()


def remove_false_insufficient_phrase(text: str, evidence_pack: dict | None = None) -> str:
    if INSUFFICIENT_PHRASE not in text:
        return text

    if evidence_pack is None:
        return text

    has_facts = bool(evidence_pack.get("important_facts"))
    has_quotes = bool(evidence_pack.get("important_quotes"))
    has_uncertainty = bool(evidence_pack.get("uncertainty"))

    evidence_is_sufficient = (has_facts or has_quotes) and not has_uncertainty

    if not evidence_is_sufficient:
        return text

    remainder = text.replace(INSUFFICIENT_PHRASE, "").strip()

    if remainder:
        return remainder

    return text


def remove_quote_artifact(text: str) -> str:
    text = text.replace("Kutipan pendek penting:", "").strip()
    text = re.sub(r"\s*-\s*\"", " \"", text)
    return text.strip()


def ensure_single_source_suffix(text: str, evidence_pack: dict | None = None) -> str:
    if evidence_pack is None:
        return text

    if "(sumber:" in text.lower():
        return text

    sources = evidence_pack.get("sources", [])
    if not sources:
        return text

    source = sources[0]
    source_name = source.get("source_name", "unknown")
    chunk_index = source.get("chunk_index", "unknown")

    return f"{text} (sumber: {source_name}, chunk {chunk_index})"


def clean_answer(text: str, evidence_pack: dict | None = None) -> str:
    text = text.strip()

    text = remove_markdown_heading(text)
    text = strip_prompt_artifacts(text)
    text = normalize_source_format(text)
    text = remove_quote_artifact(text)
    text = remove_false_insufficient_phrase(text, evidence_pack=evidence_pack)

    text = re.sub(r"\s+", " ", text).strip()
    text = remove_markdown_heading(text)
    text = remove_repeated_sentences(text)
    text = normalize_source_format(text)
    text = ensure_single_source_suffix(text, evidence_pack=evidence_pack)

    if text.count(INSUFFICIENT_PHRASE) > 1:
        text = INSUFFICIENT_PHRASE

    if len(text) > settings.answer_max_chars:
        text = text[: settings.answer_max_chars].rsplit(" ", 1)[0].strip() + "..."

    return text