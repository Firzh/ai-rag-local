from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from rich.console import Console
from rich.table import Table

from app.parsers.html_parser import extract_main_text, parse_html_file


console = Console()


SAMPLE_HTML = """
<!doctype html>
<html>
<head>
  <title>ChromaDB sebagai Vector Database</title>
  <meta name="description" content="Artikel singkat tentang fungsi ChromaDB dalam RAG lokal.">
  <link rel="canonical" href="https://example.com/chromadb-rag">
  <style>
    body { font-family: sans-serif; }
  </style>
  <script>
    tracking_code();
  </script>
</head>
<body>
  <header>Logo | Login | Register</header>
  <nav>Home | Pricing | About</nav>

  <main>
    <article>
      <h1>ChromaDB sebagai Vector Database</h1>
      <p>ChromaDB digunakan untuk menyimpan embedding dan melakukan retrieval dokumen.</p>

      <h2>Peran Magika</h2>
      <p>Magika berfungsi sebagai file router untuk mendeteksi tipe file sebelum parsing.</p>

      <ul>
        <li>File masuk</li>
        <li>Parsing</li>
        <li>Chunking</li>
        <li>Embedding</li>
      </ul>

      <table>
        <tr><th>Komponen</th><th>Fungsi</th></tr>
        <tr><td>Chroma</td><td>Vector database</td></tr>
      </table>
    </article>
  </main>

  <aside>Related posts dan iklan.</aside>
  <footer>Copyright 2026</footer>
</body>
</html>
"""


def main() -> None:
    text = extract_main_text(SAMPLE_HTML)

    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "sample.html"
        path.write_text(SAMPLE_HTML, encoding="utf-8")

        parsed = parse_html_file(
            path,
            url="https://example.com/chromadb-rag",
            fetched_at="2026-04-26T00:00:00Z",
        )

    table = Table(title="HTML Parser Smoke Test")
    table.add_column("Field")
    table.add_column("Value")

    table.add_row("Title", str(parsed.metadata.get("title")))
    table.add_row("URL", str(parsed.metadata.get("url")))
    table.add_row("Domain", str(parsed.metadata.get("domain")))
    table.add_row("Parser", str(parsed.metadata.get("parser")))
    table.add_row("Text chars", str(len(parsed.text)))
    table.add_row("Content hash", str(parsed.metadata.get("content_hash"))[:12])
    table.add_row("Document hash", str(parsed.metadata.get("document_hash"))[:12])

    console.print(table)
    console.print("\n[bold]Extracted text preview[/bold]\n")
    console.print(parsed.text[:800])

    assert "ChromaDB digunakan untuk menyimpan embedding" in parsed.text
    assert "Magika berfungsi sebagai file router" in parsed.text
    assert "tracking_code" not in parsed.text
    assert "Home | Pricing" not in parsed.text
    assert "Copyright 2026" not in parsed.text
    assert parsed.metadata["domain"] == "example.com"
    assert parsed.metadata["parser"] == "html_parser_v1"
    assert parsed.metadata["content_hash"]
    assert parsed.metadata["document_hash"]

    console.print("[green]html_parser smoke passed[/green]")


if __name__ == "__main__":
    main()