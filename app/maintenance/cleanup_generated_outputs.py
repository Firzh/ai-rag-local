from __future__ import annotations

import argparse
from pathlib import Path

from rich.console import Console
from rich.table import Table

from app.config import settings


console = Console()


DEFAULT_PATTERNS = [
    "data/answers/*.answer.json",
    "data/answers/*.answer.md",
    "data/evidence/*.evidence.json",
    "data/quality/rag_regression_bench-*.json",
    "data/quality/model_smoke_bench-*.json",
    "data/web_staging/**/*",
    "data/audits/*.csv",
    "outputs/*.jsonl",
]


PROTECTED_PATTERNS = [
    "data/quality/answer_quality.sqlite3",
    "data/quality/api_usage.sqlite3",
]


def resolve_matches(patterns: list[str]) -> list[Path]:
    root = Path.cwd()
    matches: list[Path] = []

    for pattern in patterns:
        matches.extend(root.glob(pattern))

    unique = sorted(set(path.resolve() for path in matches if path.is_file()))
    return unique


def is_protected(path: Path) -> bool:
    protected = {p.resolve() for p in resolve_matches(PROTECTED_PATTERNS)}
    return path.resolve() in protected


def cleanup_generated_outputs(*, dry_run: bool) -> int:
    files = [path for path in resolve_matches(DEFAULT_PATTERNS) if not is_protected(path)]

    table = Table(title="Generated Output Cleanup")
    table.add_column("Action")
    table.add_column("File")

    if not files:
        console.print("[green]Tidak ada generated output yang perlu dibersihkan.[/green]")
        return 0

    deleted_count = 0

    for path in files:
        relative = path.relative_to(Path.cwd())

        if dry_run:
            table.add_row("would delete", str(relative))
            continue

        path.unlink(missing_ok=True)
        deleted_count += 1
        table.add_row("deleted", str(relative))

    console.print(table)

    if dry_run:
        console.print(
            "\n[yellow]Dry-run mode. Jalankan dengan --yes untuk benar-benar menghapus.[/yellow]"
        )
    else:
        console.print(f"\n[green]Deleted files:[/green] {deleted_count}")

    return deleted_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clean generated answer/evidence/benchmark outputs without touching SQLite quality databases."
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Benar-benar hapus file. Tanpa flag ini hanya dry-run.",
    )
    args = parser.parse_args()

    # Touch settings import intentionally, so command runs from the same app config context.
    _ = settings

    cleanup_generated_outputs(dry_run=not args.yes)


if __name__ == "__main__":
    main()

