from rich.console import Console

from app.db.chroma_store import ChromaStore
from app.db.fts_store import FTSStore


console = Console()


def main() -> None:
    chroma = ChromaStore()
    fts = FTSStore()

    count = chroma.count()

    if count == 0:
        console.print("[yellow]Chroma kosong. Tidak ada data untuk FTS.[/yellow]")
        return

    result = chroma.collection.get(
        include=["documents", "metadatas"],
        limit=count,
        offset=0,
    )

    ids = result.get("ids", [])
    documents = result.get("documents", [])
    metadatas = result.get("metadatas", [])

    fts.upsert_chunks(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
    )

    console.print(f"[green]FTS rebuilt.[/green] Records: {fts.count()}")


if __name__ == "__main__":
    main()