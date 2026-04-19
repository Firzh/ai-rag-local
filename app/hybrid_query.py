import sys
from rich.console import Console

from app.hybrid_retrieval import HybridRetriever


console = Console()


def main() -> None:
    if len(sys.argv) < 2:
        console.print('[yellow]Gunakan:[/yellow] python -m app.hybrid_query "pertanyaan Anda"')
        return

    query = " ".join(sys.argv[1:])

    retriever = HybridRetriever()
    chunks = retriever.retrieve(query)

    console.print(f"\n[bold]Hybrid query:[/bold] {query}\n")

    for i, chunk in enumerate(chunks, start=1):
        console.print(f"[bold cyan]Result {i}[/bold cyan]")
        console.print(f"Source file : {chunk.metadata.get('source_name')}")
        console.print(f"Parser      : {chunk.metadata.get('parser')}")
        console.print(f"Chunk index : {chunk.metadata.get('chunk_index')}")
        console.print(f"Retrieval   : {chunk.source}")
        console.print(f"Score       : {chunk.score:.4f}")

        if chunk.distance is not None:
            console.print(f"Distance    : {chunk.distance:.4f}")

        if chunk.bm25_score is not None:
            console.print(f"BM25        : {chunk.bm25_score:.4f}")

        console.print(chunk.document[:700])
        console.print("-" * 80)

    context = retriever.build_context(query)

    console.print("\n[bold green]Final Context Preview[/bold green]\n")
    console.print(context[:3000])


if __name__ == "__main__":
    main()