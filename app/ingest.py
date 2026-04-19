from pathlib import Path
import hashlib
from datetime import datetime, timezone

from rich.console import Console
from tqdm import tqdm

from app.config import settings
from app.router import FileRouter
from app.parsers.text_parser import read_text_file
from app.parsers.pdf_parser import parse_pdf
from app.chunking import chunk_text
from app.embeddings.fastembedder import FastEmbedder
from app.db.chroma_store import ChromaStore
from app.db.manifest_store import ManifestStore
from app.db.fts_store import FTSStore
from app.parsed_writer import save_parsed_document


console = Console()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def parse_by_route(path: Path, route: str):
    if route == "text":
        return read_text_file(path)

    if route == "pdf":
        return parse_pdf(path)

    raise ValueError(f"Unsupported route: {route}")


def ingest_file(
    path: Path,
    router: FileRouter,
    embedder: FastEmbedder,
    store: ChromaStore,
    manifest: ManifestStore,
    fts_store: FTSStore | None = None,
    force: bool = False,
) -> int:
    source_path = str(path.resolve())
    document_hash = sha256_file(path)

    old_record = manifest.get(source_path)

    if not force and manifest.is_unchanged(source_path, document_hash):
        console.print(f"[blue]SKIP unchanged:[/blue] {path.name}")
        return 0

    if old_record:
        old_hash = old_record.get("document_hash")
        if old_hash:
            store.delete_by_document_hash(old_hash)
            if fts_store is not None:
                fts_store.delete_by_document_hash(old_hash)
            console.print(f"[yellow]Deleted old chunks:[/yellow] {path.name}")

    route_result = router.route_file(path)

    if route_result.route == "unsupported":
        console.print(f"[yellow]SKIP unsupported:[/yellow] {path.name} | {route_result.mime_type}")
        return 0

    parsed = parse_by_route(path, route_result.route)

    parsed_text_path, parsed_meta_path = save_parsed_document(
        source_name=parsed.source_name,
        text=parsed.text,
        metadata={
            **parsed.metadata,
            "document_hash": document_hash,
            "file_type_label": route_result.label,
            "mime_type": route_result.mime_type,
            "magika_group": route_result.group,
            "embedding_model": settings.embed_model,
            "parsed_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    chunks = chunk_text(
        parsed.text,
        chunk_size=settings.chunk_size,
        overlap=settings.chunk_overlap,
        base_metadata={
            **parsed.metadata,
            "document_hash": document_hash,
            "file_type_label": route_result.label,
            "mime_type": route_result.mime_type,
            "magika_group": route_result.group,
            "embedding_model": settings.embed_model,
            "parsed_text_path": parsed_text_path,
            "parsed_meta_path": parsed_meta_path,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    if not chunks:
        console.print(f"[yellow]EMPTY:[/yellow] {path.name}")
        return 0

    texts = [chunk.text for chunk in chunks]
    embeddings = embedder.embed_documents(texts)

    ids = []
    metadatas = []

    for chunk in chunks:
        chunk_hash = sha256_text(chunk.text)
        chunk_id = sha256_text(
            f"{document_hash}:{chunk.index}:{chunk_hash}"
        )

        ids.append(chunk_id)
        metadatas.append({
            **chunk.metadata,
            "chunk_hash": chunk_hash,
        })

    store.upsert_chunks(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    if fts_store is not None:
        fts_store.upsert_chunks(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
        )

    manifest.update(
        source_path=source_path,
        source_name=path.name,
        document_hash=document_hash,
        parser=parsed.parser,
        chunks_count=len(chunks),
    )

    return len(chunks)


def main() -> None:
    settings.ensure_dirs()

    router = FileRouter()
    embedder = FastEmbedder()
    store = ChromaStore()
    manifest = ManifestStore()
    fts_store = FTSStore() if settings.enable_fts else None

    files = [
        p for p in settings.inbox_dir.rglob("*")
        if p.is_file()
    ]

    if not files:
        console.print(f"[yellow]Tidak ada file di inbox:[/yellow] {settings.inbox_dir}")
        return

    total_chunks = 0

    for path in tqdm(files, desc="Indexing files"):
        try:
            count = ingest_file(
                path=path,
                router=router,
                embedder=embedder,
                store=store,
                manifest=manifest,
                fts_store=fts_store,
                force=False,
            )
            total_chunks += count

            if count > 0:
                console.print(f"[green]OK:[/green] {path.name} → {count} chunks")

        except Exception as exc:
            console.print(f"[red]ERROR:[/red] {path.name} → {exc}")

    console.print(f"\n[bold green]Done.[/bold green] New chunks indexed: {total_chunks}")
    console.print(f"Collection: {settings.collection_name}")
    console.print(f"Total records in Chroma: {store.count()}")


if __name__ == "__main__":
    main()