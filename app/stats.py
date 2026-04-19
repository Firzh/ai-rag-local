from collections import Counter
from rich.console import Console
from rich.table import Table

from app.db.chroma_store import ChromaStore
from app.db.manifest_store import ManifestStore
from app.config import settings


console = Console()


def main() -> None:
    store = ChromaStore()
    manifest = ManifestStore()

    console.print(f"[bold]Project:[/bold] {settings.project_dir}")
    console.print(f"[bold]Collection:[/bold] {settings.collection_name}")
    console.print(f"[bold]Embedding model:[/bold] {settings.embed_model}")
    console.print(f"[bold]Total Chroma records:[/bold] {store.count()}")

    files = manifest.all_files()

    table = Table(title="Indexed Files")
    table.add_column("File")
    table.add_column("Parser")
    table.add_column("Chunks", justify="right")
    table.add_column("Indexed At")

    parser_counter = Counter()

    for record in files.values():
        parser_counter[record.get("parser", "unknown")] += 1
        table.add_row(
            record.get("source_name", ""),
            record.get("parser", ""),
            str(record.get("chunks_count", 0)),
            record.get("indexed_at", ""),
        )

    console.print(table)

    parser_table = Table(title="Parser Summary")
    parser_table.add_column("Parser")
    parser_table.add_column("Files", justify="right")

    for parser, count in parser_counter.items():
        parser_table.add_row(parser, str(count))

    console.print(parser_table)


if __name__ == "__main__":
    main()