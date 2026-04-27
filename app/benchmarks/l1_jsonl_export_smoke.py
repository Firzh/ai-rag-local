from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from rich.console import Console

from app.exporters.l1_jsonl_export import export_l1_chunks_jsonl


console = Console()


def main() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        approved = root / "approved"
        output_path = root / "outputs" / "l1_chunks.jsonl"
        approved.mkdir(parents=True, exist_ok=True)

        text_path = approved / "quality_gate_rag_lokal.txt"
        metadata_path = approved / "quality_gate_rag_lokal.metadata.json"

        text_path.write_text(
            (
                "Quality Gate RAG Lokal\n\n"
                "Quality gate mencegah data web buruk langsung masuk ke Chroma utama. "
                "Data yang lolos masuk approved, sedangkan data bermasalah masuk quarantine. "
                "Kaggle digunakan sebagai lab eksperimen untuk audit chunking dan retrieval evaluation."
            ),
            encoding="utf-8",
        )

        metadata_path.write_text(
            json.dumps(
                {
                    "source_type": "web",
                    "source_name": "quality_gate_rag_lokal.html",
                    "source_path": "data/web_staging/raw_html/quality_gate_rag_lokal.html",
                    "url": "https://example.com/quality-gate-rag",
                    "domain": "example.com",
                    "title": "Quality Gate RAG Lokal",
                    "parser": "html_parser_v1",
                    "approval_status": "approved",
                    "quality_gate_status": "approved",
                    "document_hash": "doc-hash-existing",
                    "content_hash": "content-hash-existing",
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        result = export_l1_chunks_jsonl(
            input_dir=approved,
            output_path=output_path,
            chunk_size=180,
            overlap=40,
            min_chunk_chars=80,
        )

        lines = output_path.read_text(encoding="utf-8").splitlines()
        records = [json.loads(line) for line in lines]

        console.print(f"documents={result.document_count}, chunks={result.chunk_count}")
        console.print(records)

        assert output_path.exists()
        assert result.document_count == 1
        assert result.chunk_count >= 1
        assert records
        assert all(len(record["text"].strip()) >= 80 for record in records)

        first = records[0]

        assert [record["chunk_index"] for record in records] == list(range(len(records)))
        assert all(len(record["text"].strip()) >= 80 for record in records)
        assert "original_chunk_index" in first["metadata"]

        assert first["doc_id"]
        assert first["text"]
        assert first["title"] == "Quality Gate RAG Lokal"
        assert first["source"] == "https://example.com/quality-gate-rag"
        assert first["source_type"] == "web"
        assert first["parser"] == "html_parser_v1"
        assert first["chunk_index"] == 0
        assert first["metadata"]["section_title"]
        assert first["metadata"]["heading_path"]
        assert first["metadata"]["document_hash"]
        assert first["metadata"]["chunk_hash"]
        assert first["metadata"]["chunker"] == "chunking_v2"
        assert first["metadata"]["chunking_version"] == "chunking_v2"
        assert first["metadata"]["url"] == "https://example.com/quality-gate-rag"
        assert first["metadata"]["domain"] == "example.com"

    console.print("[green]l1_jsonl_export smoke passed[/green]")


if __name__ == "__main__":
    main()