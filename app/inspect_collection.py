from rich.console import Console

from app.db.chroma_store import ChromaStore
from app.config import settings


console = Console()


def main() -> None:
    store = ChromaStore()

    console.print(f"[bold]Collection:[/bold] {settings.collection_name}")
    console.print(f"[bold]Embedding model:[/bold] {settings.embed_model}")
    console.print(f"[bold]Total records:[/bold] {store.count()}")

    result = store.collection.peek(limit=5)

    ids = result.get("ids", [])
    documents = result.get("documents", [])
    metadatas = result.get("metadatas", [])

    for i, item_id in enumerate(ids):
        console.print("\n" + "-" * 80)
        console.print(f"[cyan]ID:[/cyan] {item_id}")
        console.print(f"[cyan]Source:[/cyan] {metadatas[i].get('source_name')}")
        console.print(f"[cyan]Parser:[/cyan] {metadatas[i].get('parser')}")
        console.print(f"[cyan]Chunk index:[/cyan] {metadatas[i].get('chunk_index')}")
        console.print(documents[i][:800])


if __name__ == "__main__":
    main()