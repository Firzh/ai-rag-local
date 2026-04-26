from __future__ import annotations

import argparse
from pathlib import Path

from rich.console import Console
from rich.table import Table

from app.staging.web_staging import (
    ensure_web_staging_dirs,
    parse_raw_html_dir_to_staging,
    parse_raw_html_to_staging,
)


console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse raw HTML files into web staging parsed_text outputs."
    )
    parser.add_argument(
        "--input",
        required=False,
        default="data/web_staging/raw_html",
        help="File HTML atau folder raw_html. Default: data/web_staging/raw_html",
    )
    parser.add_argument(
        "--output",
        required=False,
        default="data/web_staging/parsed_text",
        help="Folder output parsed text. Default: data/web_staging/parsed_text",
    )
    parser.add_argument(
        "--url",
        default="",
        help="URL sumber jika input adalah satu file.",
    )
    parser.add_argument(
        "--fetched-at",
        default="",
        help="Timestamp fetch ISO-8601 jika input adalah satu file.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Timpa output dengan nama sama.",
    )
    args = parser.parse_args()

    ensure_web_staging_dirs()

    input_path = Path(args.input)
    output_dir = Path(args.output)

    if input_path.is_file():
        results = [
            parse_raw_html_to_staging(
                input_path,
                output_dir=output_dir,
                url=args.url,
                fetched_at=args.fetched_at,
                overwrite=args.overwrite,
            )
        ]
    else:
        results = parse_raw_html_dir_to_staging(
            input_path,
            output_dir=output_dir,
            overwrite=args.overwrite,
        )

    table = Table(title="Web Staging Parse Result")
    table.add_column("Source")
    table.add_column("Text chars")
    table.add_column("Domain")
    table.add_column("Title")
    table.add_column("Output")

    for result in results:
        table.add_row(
            result.source_path.name,
            str(result.text_chars),
            str(result.metadata.get("domain", "")),
            str(result.metadata.get("title", ""))[:50],
            str(result.text_path),
        )

    console.print(table)
    console.print(f"[green]Parsed HTML files:[/green] {len(results)}")


if __name__ == "__main__":
    main()