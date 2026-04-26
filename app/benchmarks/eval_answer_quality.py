from __future__ import annotations

import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

from app.config import settings
from app.answer_quality import is_answer_artifact_like


console = Console()


def main() -> None:
    answer_files = sorted(settings.answers_dir.glob("*.answer.json"))

    if not answer_files:
        console.print("[yellow]Belum ada answer file.[/yellow]")
        return

    table = Table(title="Answer Quality Check")
    table.add_column("File")
    table.add_column("Query")
    table.add_column("Supported")
    table.add_column("Fallback")
    table.add_column("Artifact-like")

    for path in answer_files:
        with path.open("r", encoding="utf-8") as f:
            record = json.load(f)

        query = record.get("query", "")
        answer = record.get("answer", "")
        verification = record.get("verification", {})

        artifact = is_answer_artifact_like(answer, query)

        table.add_row(
            path.name,
            query,
            str(verification.get("supported")),
            str(verification.get("fallback_used", False)),
            str(artifact),
        )

    console.print(table)


if __name__ == "__main__":
    main()