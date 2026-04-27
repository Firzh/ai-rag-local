from __future__ import annotations

import argparse

from rich.console import Console
from rich.table import Table

from app.exporters.l1_jsonl_export import export_l1_chunks_jsonl


console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export approved staged documents into L1 JSONL chunks for Kaggle."
    )
    parser.add_argument(
        "--input",
        default="data/web_staging/approved",
        help="Input folder berisi .txt dan .metadata.json approved.",
    )
    parser.add_argument(
        "--output",
        default="outputs/l1_chunks.jsonl",
        help="Output JSONL path.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=900,
        help="Target karakter per chunk.",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=120,
        help="Overlap karakter antar chunk.",
    )
    parser.add_argument(
    "--min-chunk-chars",
    type=int,
    default=80,
    help="Minimal karakter chunk yang diekspor. Chunk lebih pendek akan dilewati jika dokumen punya lebih dari satu chunk.",),
    args = parser.parse_args()

    result = export_l1_chunks_jsonl(
        input_dir=args.input,
        output_path=args.output,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        min_chunk_chars=args.min_chunk_chars,
    )

    table = Table(title="L1 JSONL Export Result")
    table.add_column("Metric")
    table.add_column("Value")

    table.add_row("Input dir", str(result.input_dir))
    table.add_row("Output", str(result.output_path))
    table.add_row("Documents", str(result.document_count))
    table.add_row("Chunks", str(result.chunk_count))

    console.print(table)

    if result.chunk_count == 0:
        console.print("[yellow]Tidak ada chunk diekspor. Pastikan input berisi approved .txt files.[/yellow]")
    else:
        console.print("[green]L1 JSONL export completed.[/green]")


if __name__ == "__main__":
    main()