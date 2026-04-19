import chromadb
from rich.console import Console

from app.config import settings
from pathlib import Path


console = Console()


def main() -> None:
    client = chromadb.PersistentClient(path=str(settings.chroma_dir))

    try:
        client.delete_collection(settings.collection_name)
        console.print(f"[green]Deleted collection:[/green] {settings.collection_name}")
    except Exception as exc:
        console.print(f"[yellow]Collection belum ada atau sudah terhapus:[/yellow] {exc}")

    collection = client.get_or_create_collection(
        name=settings.collection_name,
        metadata={
            "hnsw:space": "cosine",
            "embedding_model": settings.embed_model,
            "description": "Local RAG collection using FastEmbed multilingual MiniLM",
        },
    )

    manifest_path = settings.cache_dir / "ingest_manifest.json"
    if manifest_path.exists():
        manifest_path.unlink()
        console.print(f"[green]Deleted manifest:[/green] {manifest_path}")

    fts_path = settings.indexes_dir / "fts.sqlite3"
    if fts_path.exists():
        fts_path.unlink()
        console.print(f"[green]Deleted FTS index:[/green] {fts_path}")

    console.print(f"[green]Created collection:[/green] {collection.name}")
    console.print(f"Count: {collection.count()}")


if __name__ == "__main__":
    main()