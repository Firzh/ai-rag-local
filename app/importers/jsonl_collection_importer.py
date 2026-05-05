from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import chromadb
from rich.console import Console
from rich.table import Table
from tqdm import tqdm

from app.config import settings
from app.embeddings.fastembedder import FastEmbedder


console = Console()


REQUIRED_TOP_LEVEL_FIELDS = {"document_id", "text", "metadata"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    if not path.exists():
        raise FileNotFoundError(f"Source JSONL tidak ditemukan: {path}")

    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()

            if not line:
                continue

            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSON tidak valid di {path}:{line_no}: {exc}") from exc

            if not isinstance(obj, dict):
                raise ValueError(f"Baris JSONL harus object di {path}:{line_no}")

            records.append(obj)

    return records


def sanitize_metadata_value(value: Any) -> str | int | float | bool:
    """
    Chroma metadata harus scalar.
    List dan dict dikonversi ke JSON string agar aman.
    """
    if value is None:
        return ""

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return value

    if isinstance(value, str):
        return value

    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def sanitize_metadata(metadata: dict[str, Any]) -> dict[str, str | int | float | bool]:
    return {
        str(key): sanitize_metadata_value(value)
        for key, value in metadata.items()
    }


def validate_record(record: dict[str, Any], line_no: int) -> None:
    missing = REQUIRED_TOP_LEVEL_FIELDS - set(record.keys())
    if missing:
        raise ValueError(f"Record #{line_no} kurang field wajib: {sorted(missing)}")

    document_id = record.get("document_id")
    text = record.get("text")
    metadata = record.get("metadata")

    if not isinstance(document_id, str) or not document_id.strip():
        raise ValueError(f"Record #{line_no} document_id harus string dan tidak kosong")

    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"Record #{line_no} text harus string dan tidak kosong")

    if not isinstance(metadata, dict):
        raise ValueError(f"Record #{line_no} metadata harus object")

def resolve_document_id(record: dict) -> str:
    """
    Resolve ID record untuk Chroma.

    Prioritas:
    1. document_id jika tersedia
    2. doc_id + chunk_index jika tersedia
    3. doc_id + chunk_hash jika tersedia
    4. doc_id saja sebagai fallback terakhir
    """

    document_id = record.get("document_id")

    if document_id:
        return str(document_id)

    doc_id = record.get("doc_id")

    if not doc_id:
        raise ValueError("Record wajib memiliki document_id atau doc_id.")

    chunk_index = record.get("chunk_index")

    if chunk_index is not None:
        return f"{doc_id}:{chunk_index}"

    metadata = record.get("metadata") or {}
    chunk_hash = metadata.get("chunk_hash")

    if chunk_hash:
        return f"{doc_id}:{chunk_hash}"

    return str(doc_id)

def validate_records(records: list[dict]) -> None:
    if not records:
        raise ValueError("JSONL kosong. Tidak ada record untuk diimpor.")

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"Record index {index} bukan object/dict.")

        if not record.get("text"):
            raise ValueError(f"Record index {index} tidak memiliki field text.")

        if "metadata" not in record:
            raise ValueError(f"Record index {index} tidak memiliki field metadata.")

        if not isinstance(record["metadata"], dict):
            raise ValueError(f"Record index {index} field metadata harus berupa object/dict.")

        # Menerima document_id atau doc_id
        resolve_document_id(record)


def list_collections(client: chromadb.PersistentClient) -> list[str]:
    names: list[str] = []

    for collection in client.list_collections():
        if isinstance(collection, str):
            names.append(collection)
        else:
            names.append(collection.name)

    return sorted(names)


def print_collections(client: chromadb.PersistentClient) -> None:
    names = list_collections(client)

    table = Table(title="Chroma Collections")
    table.add_column("No.", justify="right")
    table.add_column("Collection")
    table.add_column("Count", justify="right")

    for idx, name in enumerate(names, 1):
        try:
            count = client.get_collection(name=name).count()
        except Exception:
            count = -1
        table.add_row(str(idx), name, str(count))

    console.print(table)


def build_chroma_payload(
    records: list[dict[str, Any]],
    source_path: Path,
    collection_name: str,
) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, Any]] = []

    imported_at = now_iso()
    resolved_source = str(source_path.resolve())

    for record in records:
        source_metadata = record.get("metadata", {}) or {}

        metadata = {
            **source_metadata,
            "source_type": "anki_jsonl",
            "source_path": resolved_source,
            "source_document_id": record["document_id"],
            "chroma_collection": collection_name,
            "embedding_model": settings.embed_model,
            "imported_at": imported_at,
        }

        documents.append(record["text"])
        metadatas.append(record["metadata"])
        ids.append(resolve_document_id(record))

    return ids, documents, metadatas


def batched(length: int, batch_size: int):
    for start in range(0, length, batch_size):
        end = min(start + batch_size, length)
        yield start, end


def import_jsonl_to_collection(
    *,
    source: Path,
    collection_name: str,
    persist_dir: Path,
    batch_size: int,
    reset_collection: bool,
    dry_run: bool,
) -> None:
    records = read_jsonl(source)
    validate_records(records)

    console.print(f"[green]OK[/green] Source JSONL valid: {source}")
    console.print(f"Records: {len(records)}")
    console.print(f"Target collection: [bold]{collection_name}[/bold]")
    console.print(f"Persist dir: {persist_dir}")

    if records:
        sample = records[0]
        console.print("\n[bold]Sample record[/bold]")
        console.print(f"document_id: {sample.get('document_id')}")
        console.print(f"text preview: {sample.get('text', '')[:240].replace(chr(10), ' | ')}")
        console.print(f"metadata keys: {sorted((sample.get('metadata') or {}).keys())}")

    if dry_run:
        console.print("\n[yellow]DRY RUN selesai. Tidak ada data yang ditulis ke Chroma.[/yellow]")
        return

    client = chromadb.PersistentClient(path=str(persist_dir))

    if reset_collection:
        existing = set(list_collections(client))
        if collection_name in existing:
            client.delete_collection(name=collection_name)
            console.print(f"[yellow]Deleted existing collection:[/yellow] {collection_name}")

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={
            "hnsw:space": "cosine",
            "embedding_model": settings.embed_model,
            "description": "Anki Japanese Learning collection imported from RAG-ready JSONL",
        },
    )

    ids, documents, metadatas = build_chroma_payload(
        records=records,
        source_path=source,
        collection_name=collection_name,
    )

    embedder = FastEmbedder()
    total = len(documents)

    for start, end in tqdm(
        list(batched(total, batch_size)),
        desc=f"Importing to {collection_name}",
    ):
        batch_ids = ids[start:end]
        batch_docs = documents[start:end]
        batch_meta = metadatas[start:end]
        batch_embeddings = embedder.embed_documents(batch_docs)

        collection.upsert(
            ids=batch_ids,
            documents=batch_docs,
            embeddings=batch_embeddings,
            metadatas=batch_meta,
        )

    console.print("\n[bold green]Import selesai.[/bold green]")
    console.print(f"Collection: {collection_name}")
    console.print(f"Imported/upserted records: {total}")
    console.print(f"Total records in collection: {collection.count()}")


def peek_collection(
    *,
    collection_name: str,
    persist_dir: Path,
    limit: int,
) -> None:
    client = chromadb.PersistentClient(path=str(persist_dir))
    collection = client.get_collection(name=collection_name)

    result = collection.peek(limit=limit)

    console.print(f"[bold]Collection:[/bold] {collection_name}")
    console.print(f"Count: {collection.count()}")

    ids = result.get("ids", []) or []
    docs = result.get("documents", []) or []
    metas = result.get("metadatas", []) or []

    for idx, doc_id in enumerate(ids):
        console.print("\n---")
        console.print(f"id: {doc_id}")

        if idx < len(docs):
            preview = str(docs[idx])[:500].replace("\n", " | ")
            console.print(f"document: {preview}")

        if idx < len(metas):
            console.print(f"metadata: {metas[idx]}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import RAG-ready JSONL into a dedicated Chroma collection."
    )

    parser.add_argument(
        "--source",
        default="../Anki-Japanese-Learning/data/rag_ready/anki_japanese_learning.jsonl",
        help="Path JSONL sumber.",
    )
    parser.add_argument(
        "--collection",
        default="anki_japanese_learning",
        help="Nama collection Chroma target.",
    )
    parser.add_argument(
        "--persist-dir",
        default=str(settings.chroma_dir),
        help="Direktori persist Chroma.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=settings.batch_size,
        help="Ukuran batch embedding dan upsert.",
    )
    parser.add_argument(
        "--reset-collection",
        action="store_true",
        help="Hapus collection target dulu sebelum import. Hanya collection target yang dihapus.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validasi JSONL tanpa menulis ke Chroma.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List semua collection Chroma lalu keluar.",
    )
    parser.add_argument(
        "--peek",
        action="store_true",
        help="Tampilkan sample isi collection target lalu keluar.",
    )
    parser.add_argument(
        "--peek-limit",
        type=int,
        default=5,
        help="Jumlah sample saat --peek.",
    )

    args = parser.parse_args()

    persist_dir = Path(args.persist_dir).resolve()
    source = Path(args.source).resolve()

    settings.ensure_dirs()
    persist_dir.mkdir(parents=True, exist_ok=True)

    if args.list:
        client = chromadb.PersistentClient(path=str(persist_dir))
        print_collections(client)
        return

    if args.peek:
        peek_collection(
            collection_name=args.collection,
            persist_dir=persist_dir,
            limit=args.peek_limit,
        )
        return

    import_jsonl_to_collection(
        source=source,
        collection_name=args.collection,
        persist_dir=persist_dir,
        batch_size=args.batch_size,
        reset_collection=args.reset_collection,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
