from __future__ import annotations

import argparse

from rich.console import Console
from rich.table import Table

from app.quality.quality_gate import run_quality_gate


console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run quality gate for parsed web staging text before Chroma ingest."
    )
    parser.add_argument(
        "--input",
        default="data/web_staging/parsed_text",
        help="Folder input parsed_text.",
    )
    parser.add_argument(
        "--report",
        default="data/audits/quality_gate_report.csv",
        help="Path output CSV report.",
    )
    parser.add_argument(
        "--approved",
        default="data/web_staging/approved",
        help="Folder output approved.",
    )
    parser.add_argument(
        "--quarantine",
        default="data/web_staging/quarantine",
        help="Folder output quarantine.",
    )
    parser.add_argument(
        "--min-chars",
        type=int,
        default=80,
        help="Minimal karakter teks.",
    )
    parser.add_argument(
        "--max-symbol-ratio",
        type=float,
        default=0.35,
        help="Maksimal rasio simbol.",
    )
    parser.add_argument(
        "--no-copy",
        action="store_true",
        help="Hanya buat report, tidak copy ke approved/quarantine.",
    )
    args = parser.parse_args()

    results = run_quality_gate(
        input_dir=args.input,
        report_path=args.report,
        approved_dir=args.approved,
        quarantine_dir=args.quarantine,
        min_chars=args.min_chars,
        max_symbol_ratio=args.max_symbol_ratio,
        copy_outputs=not args.no_copy,
    )

    approved = sum(1 for result in results if result.status == "approved")
    quarantine = sum(1 for result in results if result.status == "quarantine")

    table = Table(title="Quality Gate Result")
    table.add_column("Metric")
    table.add_column("Value")

    table.add_row("Total", str(len(results)))
    table.add_row("Approved", str(approved))
    table.add_row("Quarantine", str(quarantine))
    table.add_row("Report", args.report)

    console.print(table)

    for result in results:
        if result.issues:
            console.print(f"[yellow]{result.text_path.name}[/yellow] -> {result.status}")
            for issue in result.issues:
                console.print(f"  - {issue.severity}:{issue.rule}: {issue.message}")


if __name__ == "__main__":
    main()