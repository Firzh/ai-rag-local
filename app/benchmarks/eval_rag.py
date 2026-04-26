from __future__ import annotations

from rich.console import Console

from app.compression.context_compressor import ContextCompressor
from app.hybrid_retrieval import HybridRetriever


console = Console()


TEST_QUERIES = [
    "apa itu RAG lokal?",
    "bagaimana pipeline AI RAG lokal?",
    "apa fungsi Magika dalam proyek ini?",
    "apa fungsi Chroma dalam proyek ini?",
]


def main() -> None:
    retriever = HybridRetriever()
    compressor = ContextCompressor()

    for query in TEST_QUERIES:
        console.print("\n" + "=" * 90)
        console.print(f"[bold]Query:[/bold] {query}")

        chunks = retriever.retrieve(query)
        console.print(f"[bold]Retrieved chunks:[/bold] {len(chunks)}")

        for i, chunk in enumerate(chunks, start=1):
            console.print(
                f"{i}. {chunk.metadata.get('source_name')} | "
                f"chunk={chunk.metadata.get('chunk_index')} | "
                f"source={chunk.source} | "
                f"score={chunk.score:.4f} | "
                f"distance={chunk.distance}"
            )

        evidence = compressor.build_evidence_pack(query)

        console.print("[bold]Evidence sources:[/bold]")
        for source in evidence["sources"]:
            console.print(
                f"- {source['source_name']} | chunk={source['chunk_index']} | "
                f"score={source['score']}"
            )

        console.print("[bold]Uncertainty:[/bold]")
        if evidence["uncertainty"]:
            for item in evidence["uncertainty"]:
                console.print(f"- {item}")
        else:
            console.print("- None")


if __name__ == "__main__":
    main()