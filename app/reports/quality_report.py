from __future__ import annotations

import json
from rich.console import Console
from rich.table import Table

from app.quality_store import AnswerQualityStore


console = Console()


def main() -> None:
    store = AnswerQualityStore()
    records = store.recent_records(limit=30)

    table = Table(title="Recent Answer Quality Records")
    table.add_column("ID", justify="right")
    table.add_column("Query")
    table.add_column("Supported")
    table.add_column("Fallback")
    table.add_column("Artifact")
    table.add_column("Score")
    table.add_column("Issues")

    for record in records:
        issues = json.loads(record.get("issue_tags_json") or "[]")

        table.add_row(
            str(record["id"]),
            record["query"][:40],
            str(bool(record["supported"])),
            str(bool(record["fallback_used"])),
            str(bool(record["artifact_like"])),
            str(record["quality_score"]),
            ", ".join(issues[:3]),
        )

    console.print(table)


if __name__ == "__main__":
    main()