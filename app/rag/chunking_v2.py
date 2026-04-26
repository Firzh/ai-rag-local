from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Section:
    title: str
    text: str
    index: int


@dataclass(frozen=True)
class Chunk:
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


_HEADING_PATTERNS = [
    re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$"),
    re.compile(r"^\s{0,3}(BAB\s+[IVXLC\d]+\.?\s+.+?)\s*$", re.IGNORECASE),
    re.compile(r"^\s{0,3}(\d+(?:\.\d+)*\.?\s+.+?)\s*$"),
]


def stable_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def estimate_tokens(text: str) -> int:
    # Estimasi kasar untuk bahasa Indonesia/Inggris.
    # Cukup untuk metadata awal tanpa dependency tokenizer.
    words = re.findall(r"\S+", text)
    return max(1, int(len(words) * 1.3)) if text.strip() else 0


def clean_text_v2(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.strip() for line in text.split("\n")]
    cleaned = "\n".join(lines)
    return cleaned.strip()


def detect_heading(line: str) -> str | None:
    stripped = line.strip()

    if not stripped:
        return None

    for pattern in _HEADING_PATTERNS:
        match = pattern.match(stripped)
        if match:
            return match.group(1).strip()

    # Heading pendek berbentuk title-case / uppercase tanpa tanda akhir.
    if (
        4 <= len(stripped) <= 90
        and not stripped.endswith((".", ",", ";", ":"))
        and len(stripped.split()) <= 12
        and (stripped.isupper() or stripped.istitle())
    ):
        return stripped

    return None


def split_sections(text: str) -> list[Section]:
    text = clean_text_v2(text)

    if not text:
        return []

    sections: list[Section] = []
    current_title = "Untitled"
    current_lines: list[str] = []
    section_index = 0

    for line in text.split("\n"):
        heading = detect_heading(line)

        if heading and current_lines:
            section_text = "\n".join(current_lines).strip()
            if section_text:
                sections.append(
                    Section(
                        title=current_title,
                        text=section_text,
                        index=section_index,
                    )
                )
                section_index += 1

            current_title = heading
            current_lines = []
            continue

        if heading and not current_lines:
            current_title = heading
            continue

        current_lines.append(line)

    final_text = "\n".join(current_lines).strip()
    if final_text:
        sections.append(
            Section(
                title=current_title,
                text=final_text,
                index=section_index,
            )
        )

    if not sections and text:
        return [Section(title="Untitled", text=text, index=0)]

    return sections


def split_paragraphs(text: str) -> list[str]:
    parts = re.split(r"\n\s*\n", text.strip())
    paragraphs = []

    for part in parts:
        normalized = re.sub(r"\s+", " ", part).strip()
        if normalized:
            paragraphs.append(normalized)

    return paragraphs


def _apply_overlap(previous_text: str, overlap_chars: int) -> str:
    if overlap_chars <= 0:
        return ""

    previous_text = previous_text.strip()
    if not previous_text:
        return ""

    return previous_text[-overlap_chars:].strip()


def chunk_sections(
    sections: list[Section],
    target_chars: int,
    overlap_chars: int,
) -> list[Chunk]:
    if target_chars <= 100:
        raise ValueError("target_chars terlalu kecil. Gunakan minimal > 100.")

    chunks: list[Chunk] = []
    chunk_index = 0

    for section in sections:
        paragraphs = split_paragraphs(section.text)
        buffer: list[str] = []
        buffer_len = 0
        previous_chunk_text = ""

        for paragraph in paragraphs:
            paragraph_len = len(paragraph)

            # Paragraf sangat panjang dipecah secara konservatif.
            if paragraph_len > target_chars:
                if buffer:
                    chunk_text = "\n\n".join(buffer).strip()
                    chunks.append(
                        Chunk(
                            text=chunk_text,
                            metadata={
                                "chunk_index": chunk_index,
                                "section_title": section.title,
                                "section_index": section.index,
                            },
                        )
                    )
                    chunk_index += 1
                    previous_chunk_text = chunk_text
                    buffer = []
                    buffer_len = 0

                start = 0
                while start < paragraph_len:
                    end = min(start + target_chars, paragraph_len)
                    part = paragraph[start:end].strip()

                    if part:
                        overlap_text = _apply_overlap(previous_chunk_text, overlap_chars)
                        chunk_text = (
                            f"{overlap_text}\n\n{part}".strip()
                            if overlap_text
                            else part
                        )

                        chunks.append(
                            Chunk(
                                text=chunk_text,
                                metadata={
                                    "chunk_index": chunk_index,
                                    "section_title": section.title,
                                    "section_index": section.index,
                                },
                            )
                        )
                        chunk_index += 1
                        previous_chunk_text = chunk_text

                    start = end - overlap_chars if overlap_chars > 0 else end
                    if start <= 0 or start >= paragraph_len:
                        break

                continue

            next_len = buffer_len + paragraph_len + 2

            if buffer and next_len > target_chars:
                chunk_text = "\n\n".join(buffer).strip()
                chunks.append(
                    Chunk(
                        text=chunk_text,
                        metadata={
                            "chunk_index": chunk_index,
                            "section_title": section.title,
                            "section_index": section.index,
                        },
                    )
                )
                chunk_index += 1
                previous_chunk_text = chunk_text

                overlap_text = _apply_overlap(previous_chunk_text, overlap_chars)
                buffer = [overlap_text, paragraph] if overlap_text else [paragraph]
                buffer_len = sum(len(x) for x in buffer)
            else:
                buffer.append(paragraph)
                buffer_len = next_len

        if buffer:
            chunk_text = "\n\n".join([x for x in buffer if x.strip()]).strip()
            if chunk_text:
                chunks.append(
                    Chunk(
                        text=chunk_text,
                        metadata={
                            "chunk_index": chunk_index,
                            "section_title": section.title,
                            "section_index": section.index,
                        },
                    )
                )
                chunk_index += 1

    return chunks


def enrich_chunk_metadata(
    chunk: Chunk,
    *,
    base_metadata: dict[str, Any],
    document_hash: str,
    chunker_name: str = "chunking_v2",
) -> Chunk:
    metadata = {
        **base_metadata,
        **chunk.metadata,
    }

    text = chunk.text.strip()
    metadata.update(
        {
            "chunker": chunker_name,
            "char_count": len(text),
            "token_estimate": estimate_tokens(text),
            "document_hash": document_hash,
            "chunk_hash": stable_hash(text),
        }
    )

    return Chunk(text=text, metadata=metadata)


def chunk_text_v2(
    text: str,
    chunk_size: int = 900,
    overlap: int = 120,
    base_metadata: dict | None = None,
) -> list[Chunk]:
    base_metadata = dict(base_metadata or {})
    cleaned = clean_text_v2(text)

    if not cleaned:
        return []

    document_hash = stable_hash(cleaned)
    sections = split_sections(cleaned)
    raw_chunks = chunk_sections(
        sections=sections,
        target_chars=chunk_size,
        overlap_chars=overlap,
    )

    enriched: list[Chunk] = []
    for chunk in raw_chunks:
        if not chunk.text.strip():
            continue

        enriched.append(
            enrich_chunk_metadata(
                chunk,
                base_metadata=base_metadata,
                document_hash=document_hash,
            )
        )

    return enriched