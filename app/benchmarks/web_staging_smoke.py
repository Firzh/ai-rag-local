from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from rich.console import Console

from app.staging.web_staging import parse_raw_html_to_staging


console = Console()


SAMPLE_HTML = """
<!doctype html>
<html>
<head>
  <title>Pipeline RAG Lokal dan Kaggle</title>
  <meta name="description" content="Dokumen uji staging web untuk RAG lokal.">
  <link rel="canonical" href="https://example.com/rag-kaggle">
  <script>secret_tracking()</script>
</head>
<body>
  <header>Menu utama</header>
  <main>
    <article>
      <h1>Pipeline RAG Lokal dan Kaggle</h1>
      <p>Kaggle digunakan sebagai lab eksperimen, bukan backend produksi.</p>
      <p>Data web harus masuk staging sebelum quality gate dan Chroma sandbox.</p>
    </article>
  </main>
  <footer>Copyright dan link sosial.</footer>
</body>
</html>
"""


def main() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        html_path = root / "sample.html"
        output_dir = root / "parsed_text"

        html_path.write_text(SAMPLE_HTML, encoding="utf-8")

        result = parse_raw_html_to_staging(
            html_path,
            output_dir=output_dir,
            url="https://example.com/rag-kaggle",
            fetched_at="2026-04-26T00:00:00Z",
            overwrite=True,
        )

        text = result.text_path.read_text(encoding="utf-8")
        metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
        manifest = output_dir / "manifest.jsonl"

        console.print("[bold]Parsed text[/bold]")
        console.print(text)
        console.print("\n[bold]Metadata[/bold]")
        console.print(metadata)

        assert result.text_path.exists()
        assert result.metadata_path.exists()
        assert manifest.exists()

        assert "Kaggle digunakan sebagai lab eksperimen" in text
        assert "Data web harus masuk staging" in text
        assert "secret_tracking" not in text
        assert "Copyright dan link sosial" not in text

        assert metadata["source_type"] == "web"
        assert metadata["domain"] == "example.com"
        assert metadata["parser"] == "html_parser_v1"
        assert metadata["staging_status"] == "parsed"
        assert metadata["raw_html_path"]
        assert metadata["parsed_text_path"]
        assert metadata["metadata_path"]
        assert metadata["document_hash"]
        assert metadata["content_hash"]

    console.print("[green]web_staging smoke passed[/green]")


if __name__ == "__main__":
    main()