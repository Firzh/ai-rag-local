from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from app.rag.chunking_v2 import Chunk, chunk_text_v2, stable_hash


@dataclass(frozen=True)
class L1ExportResult:
    input_dir: Path
    output_path: Path
    document_count: int
    chunk_count: int


def metadata_path_for_text(text_path: Path) -> Path:
    return text_path.with_suffix(".metadata.json")


def load_metadata_for_text(text_path: Path) -> dict[str, Any]:
    metadata_path = metadata_path_for_text(text_path)

    if not metadata_path.exists():
        return {}

    try:
        return json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def iter_text_files(input_dir: str | Path) -> Iterable[Path]:
    input_dir = Path(input_dir)

    if not input_dir.exists():
        raise FileNotFoundError(f"Input dir tidak ditemukan: {input_dir}")

    yield from sorted(input_dir.glob("*.txt"))


def normalize_source(metadata: dict[str, Any], text_path: Path) -> str:
    return str(
        metadata.get("url")
        or metadata.get("source")
        or metadata.get("source_path")
        or metadata.get("source_name")
        or text_path.name
    )


def normalize_doc_id(metadata: dict[str, Any], text: str) -> str:
    return str(
        metadata.get("doc_id")
        or metadata.get("document_hash")
        or stable_hash(text)
    )


def build_base_metadata(metadata: dict[str, Any], text_path: Path, text: str) -> dict[str, Any]:
    source = normalize_source(metadata, text_path)
    doc_id = normalize_doc_id(metadata, text)

    return {
        "doc_id": doc_id,
        "title": str(metadata.get("title") or text_path.stem),
        "source": source,
        "source_type": str(metadata.get("source_type") or "local_file"),
        "parser": str(metadata.get("parser") or "unknown_parser"),
        "page": metadata.get("page"),
        "url": metadata.get("url"),
        "domain": metadata.get("domain"),
        "source_name": metadata.get("source_name") or text_path.name,
        "source_path": metadata.get("source_path") or str(text_path),
        "approval_status": metadata.get("approval_status"),
        "quality_gate_status": metadata.get("quality_gate_status"),
    }


def chunk_to_jsonl_record(
    *,
    chunk: Chunk,
    base_metadata: dict[str, Any],
    exported_chunk_index: int,
) -> dict[str, Any]:
    chunk_metadata = dict(chunk.metadata)

    original_chunk_index = chunk_metadata.get("chunk_index")
    section_title = str(chunk_metadata.get("section_title") or "")
    heading_path = str(chunk_metadata.get("heading_path") or section_title or "Untitled")

    chunk_metadata["original_chunk_index"] = original_chunk_index
    chunk_metadata["chunk_index"] = exported_chunk_index
    chunk_metadata["heading_path"] = heading_path
    chunk_metadata["chunking_version"] = (
        chunk_metadata.get("chunking_version")
        or chunk_metadata.get("chunker")
        or "chunking_v2"
    )

    return {
        "doc_id": base_metadata["doc_id"],
        "title": base_metadata["title"],
        "source": base_metadata["source"],
        "source_type": base_metadata["source_type"],
        "parser": base_metadata["parser"],
        "page": base_metadata.get("page"),
        "chunk_index": exported_chunk_index,
        "text": chunk.text,
        "metadata": {
            **chunk_metadata,
            "url": base_metadata.get("url"),
            "domain": base_metadata.get("domain"),
            "source_name": base_metadata.get("source_name"),
            "source_path": base_metadata.get("source_path"),
            "approval_status": base_metadata.get("approval_status"),
            "quality_gate_status": base_metadata.get("quality_gate_status"),
        },
    }

def export_l1_chunks_jsonl(
    *,
    input_dir: str | Path,
    output_path: str | Path = "outputs/l1_chunks.jsonl",
    chunk_size: int = 900,
    overlap: int = 120,
    min_chunk_chars: int = 80,
) -> L1ExportResult:
    input_dir = Path(input_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    document_count = 0
    chunk_count = 0

    with output_path.open("w", encoding="utf-8") as f:
        for text_path in iter_text_files(input_dir):
            text = text_path.read_text(encoding="utf-8", errors="replace").strip()

            if not text:
                continue

            metadata = load_metadata_for_text(text_path)
            base_metadata = build_base_metadata(metadata, text_path, text)

            chunks = chunk_text_v2(
                text,
                chunk_size=chunk_size,
                overlap=overlap,
                base_metadata=base_metadata,
            )

            if not chunks:
                continue

            exported_records: list[dict[str, Any]] = []
            exported_chunk_index = 0

            for chunk in chunks:
                if len(chunk.text.strip()) < min_chunk_chars and len(chunks) > 1:
                    continue

                record = chunk_to_jsonl_record(
                    chunk=chunk,
                    base_metadata=base_metadata,
                    exported_chunk_index=exported_chunk_index,
                )
                exported_records.append(record)
                exported_chunk_index += 1

            if not exported_records:
                continue

            document_count += 1

            for record in exported_records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                chunk_count += 1

    return L1ExportResult(
        input_dir=input_dir,
        output_path=output_path,
        document_count=document_count,
        chunk_count=chunk_count,
    )