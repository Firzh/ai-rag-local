from __future__ import annotations

from rich.console import Console
from rich.table import Table

from app.rag.chunking_v2 import chunk_text_v2


console = Console()


SAMPLE_TEXT = """
# Pendahuluan

Magika berfungsi sebagai file router dalam pipeline RAG lokal. Komponen ini membantu mendeteksi tipe file sebelum proses parsing dilakukan.

Chroma digunakan sebagai vector database. Chroma menyimpan embedding dan membantu retrieval chunk dokumen yang relevan.

# Pipeline

Urutan pipeline utama adalah file masuk, deteksi tipe file, parsing, chunking, embedding, penyimpanan ke Chroma, retrieval, dan jawaban dari model.
"""


def main() -> None:
    chunks = chunk_text_v2(
        SAMPLE_TEXT,
        chunk_size=180,
        overlap=40,
        base_metadata={"source_name": "chunking_v2_smoke"},
    )

    table = Table(title="Chunking V2 Smoke Test")
    table.add_column("Index")
    table.add_column("Section")
    table.add_column("Chars")
    table.add_column("Tokens")
    table.add_column("Hash")

    for chunk in chunks:
        table.add_row(
            str(chunk.metadata["chunk_index"]),
            str(chunk.metadata["section_title"]),
            str(chunk.metadata["char_count"]),
            str(chunk.metadata["token_estimate"]),
            str(chunk.metadata["chunk_hash"])[:10],
        )

    console.print(table)

    assert chunks, "chunk_text_v2 tidak menghasilkan chunk."
    assert all(chunk.text.strip() for chunk in chunks), "Ada chunk kosong."
    assert all("chunk_hash" in chunk.metadata for chunk in chunks), "chunk_hash belum lengkap."
    assert all("document_hash" in chunk.metadata for chunk in chunks), "document_hash belum lengkap."
    assert all("section_title" in chunk.metadata for chunk in chunks), "section_title belum lengkap."

    console.print("[green]chunking_v2 smoke passed[/green]")


if __name__ == "__main__":
    main()