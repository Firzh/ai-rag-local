from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from rich.console import Console

from app.quality.quality_gate import run_quality_gate


console = Console()


def write_doc(
    directory: Path,
    stem: str,
    text: str,
    metadata: dict,
) -> None:
    text_path = directory / f"{stem}.txt"
    metadata_path = directory / f"{stem}.metadata.json"

    text_path.write_text(text, encoding="utf-8")
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def main() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        parsed = root / "parsed_text"
        approved = root / "approved"
        quarantine = root / "quarantine"
        report = root / "quality_gate_report.csv"
        parsed.mkdir(parents=True, exist_ok=True)

        write_doc(
            parsed,
            "good_web_doc",
            (
                "Kaggle digunakan sebagai lab eksperimen untuk audit chunking, "
                "embedding batch, dan retrieval evaluation. Data web harus melewati "
                "staging dan quality gate sebelum masuk Chroma sandbox."
            ),
            {
                "source_type": "web",
                "source_name": "good_web_doc.html",
                "source_path": "data/web_staging/raw_html/good_web_doc.html",
                "url": "https://example.com/good",
                "domain": "example.com",
                "title": "Good Web Doc",
                "document_hash": "doc-hash-good",
                "content_hash": "content-hash-good",
                "parser": "html_parser_v1",
                "approval_status": "staged",
            },
        )

        write_doc(
            parsed,
            "missing_url_doc",
            (
                "Dokumen ini membahas pipeline RAG lokal, tetapi metadata web tidak "
                "menyertakan URL dan domain sehingga harus masuk quarantine."
            ),
            {
                "source_type": "web",
                "source_name": "missing_url_doc.html",
                "source_path": "data/web_staging/raw_html/missing_url_doc.html",
                "title": "Missing URL Doc",
                "document_hash": "doc-hash-missing-url",
                "content_hash": "content-hash-missing-url",
                "parser": "html_parser_v1",
                "approval_status": "staged",
            },
        )

        write_doc(
            parsed,
            "secret_doc",
            (
                "Dokumen ini seharusnya ditolak karena mengandung API_KEY="
                "AIzaSyDUMMYDUMMYDUMMYDUMMYDUMMYDUMMY yang tidak boleh masuk Chroma."
            ),
            {
                "source_type": "web",
                "source_name": "secret_doc.html",
                "source_path": "data/web_staging/raw_html/secret_doc.html",
                "url": "https://example.com/secret",
                "domain": "example.com",
                "title": "Secret Doc",
                "document_hash": "doc-hash-secret",
                "content_hash": "content-hash-secret",
                "parser": "html_parser_v1",
                "approval_status": "staged",
            },
        )

        results = run_quality_gate(
            input_dir=parsed,
            report_path=report,
            approved_dir=approved,
            quarantine_dir=quarantine,
            min_chars=80,
            copy_outputs=True,
        )

        statuses = {result.text_path.stem: result.status for result in results}

        console.print(statuses)
        console.print(report.read_text(encoding="utf-8"))

        assert statuses["good_web_doc"] == "approved"
        assert statuses["missing_url_doc"] == "quarantine"
        assert statuses["secret_doc"] == "quarantine"

        assert (approved / "good_web_doc.txt").exists()
        assert (approved / "good_web_doc.metadata.json").exists()
        assert (quarantine / "missing_url_doc.txt").exists()
        assert (quarantine / "secret_doc.txt").exists()
        assert report.exists()

    console.print("[green]quality_gate smoke passed[/green]")


if __name__ == "__main__":
    main()