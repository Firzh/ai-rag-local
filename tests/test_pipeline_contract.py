import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from app.staging.web_staging import parse_raw_html_to_staging
from app.quality.quality_gate import run_quality_gate
from app.exporters.l1_jsonl_export import export_l1_chunks_jsonl
from app.importers.jsonl_collection_importer import validate_records


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_all_app_python_files_compile():
    app_dir = Path("app")
    assert app_dir.exists(), "Folder app tidak ditemukan. Jalankan pytest dari root repo."

    failures = []

    for path in sorted(app_dir.rglob("*.py")):
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            failures.append(
                {
                    "path": str(path),
                    "stderr": result.stderr,
                }
            )

    assert not failures, failures


def test_web_pipeline_contract_from_raw_html_to_l1_jsonl(tmp_path):
    raw_dir = tmp_path / "raw_html"
    parsed_dir = tmp_path / "parsed_text"
    approved_dir = tmp_path / "approved"
    quarantine_dir = tmp_path / "quarantine"
    report_path = tmp_path / "quality_gate_report.csv"
    output_path = tmp_path / "outputs" / "l1_chunks.jsonl"

    raw_dir.mkdir(parents=True)

    html_path = raw_dir / "pipeline.html"
    html_path.write_text(
        """
        <!doctype html>
        <html>
          <head>
            <title>Kontrak Pipeline RAG Lokal</title>
            <meta name="description" content="Dokumen uji kontrak pipeline RAG lokal">
          </head>
          <body>
            <header>Menu utama yang harus dibuang</header>
            <nav>Home | Pricing | Login</nav>

            <main>
              <h1>Kontrak Pipeline RAG Lokal</h1>
              <p>
                Kaggle digunakan sebagai lab eksperimen untuk audit chunking,
                embedding batch, retrieval evaluation, dan eksperimen ringan.
              </p>
              <p>
                Data web harus melewati staging dan quality gate sebelum masuk
                Chroma sandbox agar Chroma utama tidak menerima data mentah.
              </p>
              <p>
                Metadata sumber seperti URL, domain, parser, approval status,
                dan quality gate status harus tetap terbawa sampai JSONL.
              </p>
            </main>

            <footer>Copyright dan link sosial yang harus dibuang</footer>
          </body>
        </html>
        """,
        encoding="utf-8",
    )

    staging_result = parse_raw_html_to_staging(
        html_path,
        output_dir=parsed_dir,
        url="https://example.com/kontrak-pipeline-rag",
        fetched_at="2026-04-26T00:00:00Z",
        overwrite=True,
    )

    assert staging_result.text_path.exists()
    assert staging_result.metadata_path.exists()

    parsed_text = staging_result.text_path.read_text(encoding="utf-8")
    parsed_metadata = json.loads(staging_result.metadata_path.read_text(encoding="utf-8"))

    assert "Kaggle digunakan sebagai lab eksperimen" in parsed_text
    assert "Data web harus melewati staging" in parsed_text
    assert "Home | Pricing" not in parsed_text
    assert "Copyright dan link sosial" not in parsed_text

    assert parsed_metadata["source_type"] == "web"
    assert parsed_metadata["domain"] == "example.com"
    assert parsed_metadata["parser"] == "html_parser_v1"
    assert parsed_metadata["staging_status"] == "parsed"
    assert parsed_metadata["document_hash"]
    assert parsed_metadata["content_hash"]

    gate_results = run_quality_gate(
        input_dir=parsed_dir,
        report_path=report_path,
        approved_dir=approved_dir,
        quarantine_dir=quarantine_dir,
        min_chars=80,
        max_symbol_ratio=0.35,
        copy_outputs=True,
    )

    assert len(gate_results) == 1
    assert gate_results[0].status == "approved"
    assert report_path.exists()

    approved_texts = list(approved_dir.glob("*.txt"))
    assert len(approved_texts) == 1

    export_result = export_l1_chunks_jsonl(
        input_dir=approved_dir,
        output_path=output_path,
        chunk_size=220,
        overlap=40,
        min_chunk_chars=80,
    )

    assert output_path.exists()
    assert export_result.document_count == 1
    assert export_result.chunk_count >= 1

    records = read_jsonl(output_path)
    assert records

    first = records[0]

    assert first["text"].strip()
    assert first["title"] == "Kontrak Pipeline RAG Lokal"
    assert first["source"] == "https://example.com/kontrak-pipeline-rag"
    assert first["source_type"] == "web"
    assert first["parser"] == "html_parser_v1"
    assert first["chunk_index"] == 0

    assert first["metadata"]["url"] == "https://example.com/kontrak-pipeline-rag"
    assert first["metadata"]["domain"] == "example.com"
    assert first["metadata"]["approval_status"] == "approved"
    assert first["metadata"]["quality_gate_status"] == "approved"
    assert first["metadata"]["chunk_hash"]
    assert first["metadata"]["document_hash"]


def test_quarantine_document_is_not_exported(tmp_path):
    parsed_dir = tmp_path / "parsed_text"
    approved_dir = tmp_path / "approved"
    quarantine_dir = tmp_path / "quarantine"
    output_path = tmp_path / "outputs" / "l1_chunks.jsonl"

    parsed_dir.mkdir(parents=True)

    bad_text = parsed_dir / "secret_doc.txt"
    bad_meta = parsed_dir / "secret_doc.metadata.json"

    bad_text.write_text(
        "Dokumen ini harus ditolak karena mengandung API_KEY=AIzaSyDUMMYDUMMYDUMMYDUMMYDUMMYDUMMY "
        "dan tidak boleh masuk export JSONL atau Chroma.",
        encoding="utf-8",
    )

    bad_meta.write_text(
        json.dumps(
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
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    results = run_quality_gate(
        input_dir=parsed_dir,
        approved_dir=approved_dir,
        quarantine_dir=quarantine_dir,
        report_path=tmp_path / "report.csv",
        min_chars=80,
        copy_outputs=True,
    )

    assert results[0].status == "quarantine"
    assert not list(approved_dir.glob("*.txt"))

    export_result = export_l1_chunks_jsonl(
        input_dir=approved_dir,
        output_path=output_path,
    )

    assert export_result.document_count == 0
    assert export_result.chunk_count == 0

    if output_path.exists():
        assert "AIza" not in output_path.read_text(encoding="utf-8")


def test_l1_export_output_is_importer_compatible(tmp_path):
    approved_dir = tmp_path / "approved"
    output_path = tmp_path / "outputs" / "l1_chunks.jsonl"
    approved_dir.mkdir(parents=True)

    text_path = approved_dir / "approved_doc.txt"
    meta_path = approved_dir / "approved_doc.metadata.json"

    text_path.write_text(
        "Dokumen approved untuk menguji kompatibilitas schema JSONL antara exporter L1 dan importer Chroma. "
        "Record hasil export harus bisa diterima langsung oleh validate_records pada importer.",
        encoding="utf-8",
    )

    meta_path.write_text(
        json.dumps(
            {
                "source_type": "web",
                "source_name": "approved_doc.html",
                "source_path": "data/web_staging/raw_html/approved_doc.html",
                "url": "https://example.com/approved-doc",
                "domain": "example.com",
                "title": "Approved Doc",
                "parser": "html_parser_v1",
                "approval_status": "approved",
                "quality_gate_status": "approved",
                "document_hash": "doc-hash-approved",
                "content_hash": "content-hash-approved",
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    export_l1_chunks_jsonl(
        input_dir=approved_dir,
        output_path=output_path,
        chunk_size=220,
        overlap=40,
        min_chunk_chars=80,
    )

    records = read_jsonl(output_path)

    # Ini harus lolos jika kontrak exporter dan importer sudah sinkron.
    validate_records(records)