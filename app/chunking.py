from dataclasses import dataclass
import re


@dataclass
class Chunk:
    text: str
    index: int
    metadata: dict


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(
    text: str,
    chunk_size: int = 900,
    overlap: int = 120,
    base_metadata: dict | None = None,
) -> list[Chunk]:
    if chunk_size <= overlap:
        raise ValueError("chunk_size harus lebih besar dari overlap")

    cleaned = clean_text(text)
    metadata = base_metadata or {}

    if not cleaned:
        return []

    chunks: list[Chunk] = []
    start = 0
    index = 0

    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        chunk = cleaned[start:end].strip()

        if chunk:
            chunks.append(
                Chunk(
                    text=chunk,
                    index=index,
                    metadata={
                        **metadata,
                        "chunk_index": index,
                        "chunk_size": len(chunk),
                    },
                )
            )
            index += 1

        if end >= len(cleaned):
            break

        start = end - overlap

    return chunks