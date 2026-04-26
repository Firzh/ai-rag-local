import sys
from rich.console import Console

from app.config import settings
from app.embeddings.fastembedder import FastEmbedder
from app.db.chroma_store import ChromaStore


console = Console()


def main() -> None:
    if len(sys.argv) < 2:
        console.print("[yellow]Gunakan:[/yellow] python -m app.query_db \"pertanyaan Anda\"")
        return

    query = " ".join(sys.argv[1:])

    embedder = FastEmbedder()
    store = ChromaStore()

    query_embedding = embedder.embed_query(query)
    result = store.query(query_embedding, top_k=settings.top_k)

    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    if not documents:
        console.print("[yellow]Tidak ada hasil retrieval.[/yellow]")
        return

    console.print(f"\n[bold]Query:[/bold] {query}\n")

    for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances), start=1):
        console.print(f"[bold cyan]Result {i}[/bold cyan]")
        console.print(f"Distance: {dist}")
        console.print(f"Source: {meta.get('source_name')}")
        console.print(f"Parser: {meta.get('parser')}")
        console.print(f"Chunk: {meta.get('chunk_index')}")
        console.print(doc[:700])
        console.print("-" * 80)


if __name__ == "__main__":
    main()