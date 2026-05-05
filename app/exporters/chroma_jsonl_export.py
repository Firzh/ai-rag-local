from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb


@dataclass(frozen=True)
class ChromaJsonlExportResult:
    chroma_dir: Path
    collection_name: str
    output_path: Path
    total_count: int
    exported_count: int
    include_embeddings: bool


def _normalize_embedding(value: Any) -> list[float] | None:
    if value is None:
        return None

    if hasattr(value, "tolist"):
        value = value.tolist()

    return [float(item) for item in value]


def _build_record(
    *,
    item_id: str,
    document: str | None,
    metadata: dict[str, Any] | None,
    collection_name: str,
    embedding: Any | None = None,
    include_embeddings: bool = False,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "id": item_id,
        "collection": collection_name,
        "text": document or "",
        "metadata": metadata or {},
    }

    if include_embeddings:
        record["embedding"] = _normalize_embedding(embedding)

    return record


def export_chroma_collection_jsonl(
    *,
    chroma_dir: str | Path,
    collection_name: str,
    output_path: str | Path,
    batch_size: int = 100,
    include_embeddings: bool = False,
) -> ChromaJsonlExportResult:
    if batch_size <= 0:
        raise ValueError("batch_size harus lebih dari 0.")

    chroma_dir = Path(chroma_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = client.get_collection(name=collection_name)

    total_count = collection.count()
    exported_count = 0

    include = ["documents", "metadatas"]
    if include_embeddings:
        include.append("embeddings")

    with output_path.open("w", encoding="utf-8") as file:
        for offset in range(0, total_count, batch_size):
            batch = collection.get(
                limit=batch_size,
                offset=offset,
                include=include,
            )

            ids = batch.get("ids") or []
            documents = batch.get("documents") or []
            metadatas = batch.get("metadatas") or []
            embeddings = batch.get("embeddings") if include_embeddings else None

            for index, item_id in enumerate(ids):
                record = _build_record(
                    item_id=str(item_id),
                    document=documents[index] if index < len(documents) else "",
                    metadata=metadatas[index] if index < len(metadatas) else {},
                    collection_name=collection_name,
                    embedding=embeddings[index] if embeddings is not None else None,
                    include_embeddings=include_embeddings,
                )
                file.write(json.dumps(record, ensure_ascii=False) + "\n")
                exported_count += 1

    return ChromaJsonlExportResult(
        chroma_dir=chroma_dir,
        collection_name=collection_name,
        output_path=output_path,
        total_count=total_count,
        exported_count=exported_count,
        include_embeddings=include_embeddings,
    )
