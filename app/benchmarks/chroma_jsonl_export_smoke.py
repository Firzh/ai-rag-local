from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import chromadb

from app.exporters.chroma_jsonl_export import export_chroma_collection_jsonl


def main() -> None:
    root = Path("data/tmp/chroma_jsonl_export_smoke") / uuid4().hex
    chroma_dir = root / "chroma"
    output_path = root / "exports" / "smoke_chroma_collection.jsonl"
    collection_name = "smoke_l4_chroma_export"

    client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    collection.add(
        ids=["doc-a-0", "doc-b-0"],
        documents=[
            "Kaggle dipakai sebagai lab eksperimen untuk audit data dan retrieval evaluation.",
            "Data web yang lolos quality gate boleh diekspor ke JSONL sebelum masuk sandbox.",
        ],
        metadatas=[
            {
                "source_type": "web",
                "source": "https://example.com/a",
                "title": "Dokumen A",
                "quality_gate_status": "approved",
            },
            {
                "source_type": "web",
                "source": "https://example.com/b",
                "title": "Dokumen B",
                "quality_gate_status": "approved",
            },
        ],
        embeddings=[
            [0.10, 0.20, 0.30, 0.40],
            [0.40, 0.30, 0.20, 0.10],
        ],
    )

    result = export_chroma_collection_jsonl(
        chroma_dir=chroma_dir,
        collection_name=collection_name,
        output_path=output_path,
        batch_size=1,
        include_embeddings=True,
    )

    lines = output_path.read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines]

    assert output_path.exists()
    assert result.total_count == 2
    assert result.exported_count == 2
    assert len(records) == 2
    assert {record["id"] for record in records} == {"doc-a-0", "doc-b-0"}
    assert all(record["collection"] == collection_name for record in records)
    assert all(record["text"].strip() for record in records)
    assert all(record["metadata"]["quality_gate_status"] == "approved" for record in records)
    assert all(isinstance(record.get("embedding"), list) for record in records)
    assert all(len(record["embedding"]) == 4 for record in records)

    print("chroma_jsonl_export smoke passed")
    print(f"smoke artifacts: {root}")


if __name__ == "__main__":
    main()
