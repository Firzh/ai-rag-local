from __future__ import annotations

import re


def has_raw_quote_artifact(text: str) -> bool:
    return text.count('"') >= 2


def has_numbered_overexpansion(text: str) -> bool:
    return bool(re.search(r"\b1\.\s+.+\b2\.\s+", text))


def is_answer_too_long(text: str, max_chars: int = 850) -> bool:
    return len(text.strip()) > max_chars


def is_pipeline_answer_noisy(text: str, query: str) -> bool:
    query_lower = query.lower()
    text_lower = text.lower()

    if "pipeline" not in query_lower:
        return False

    if text_lower.count("pipeline") >= 3:
        return True

    if has_raw_quote_artifact(text):
        return True

    if has_numbered_overexpansion(text):
        return True

    if is_answer_too_long(text, max_chars=750):
        return True

    return False


def is_magika_role_confused(text: str, query: str) -> bool:
    query_lower = query.lower()
    text_lower = text.lower()

    if "magika" not in query_lower:
        return False

    # Boleh:
    # - Magika sebagai file router
    # - mendeteksi tipe file
    # - mengarahkan file ke parser/proses parsing
    #
    # Tidak boleh:
    # - Magika melakukan parsing sendiri
    # - Magika membuat embedding
    # - Magika menyimpan ke Chroma
    # - Magika menghasilkan jawaban

    forbidden_patterns = [
        "magika melakukan parsing",
        "magika mem-parsing",
        "magika memproses pdf",
        "magika melakukan embedding",
        "magika membuat embedding",
        "magika menyimpan embedding",
        "magika menyimpan ke chroma",
        "magika sebagai vector database",
        "magika menghasilkan jawaban",
        "magika menjalankan model qwen",
    ]

    return any(pattern in text_lower for pattern in forbidden_patterns)


def is_chroma_role_confused(text: str, query: str) -> bool:
    query_lower = query.lower()
    text_lower = text.lower()

    if "chroma" not in query_lower:
        return False

    # Boleh:
    # - Chroma sebagai vector database
    # - menyimpan embedding / vektor
    # - mendukung retrieval
    #
    # Tidak boleh:
    # - Chroma melakukan parsing
    # - Chroma membuat embedding
    # - Chroma menjadi file router
    # - Chroma menghasilkan jawaban

    forbidden_patterns = [
        "chroma melakukan parsing",
        "chroma mem-parsing",
        "chroma membuat embedding",
        "chroma menghasilkan embedding",
        "chroma sebagai file router",
        "chroma menghasilkan jawaban",
        "chroma menjalankan model qwen",
    ]

    return any(pattern in text_lower for pattern in forbidden_patterns)


def is_answer_artifact_like(text: str, query: str) -> bool:
    lower = text.lower()

    markers = [
        "kutipan pendek penting",
        "jawaban pertanyaan secara langsung",
        "fakta penting:",
        "sumber relevan:",
        "dokumen belum cukup mendukung jawaban",
    ]

    if any(marker in lower for marker in markers):
        return True

    if is_pipeline_answer_noisy(text, query):
        return True

    if is_magika_role_confused(text, query):
        return True

    if is_chroma_role_confused(text, query):
        return True

    return False