import re

from app.rag.chunking_v2 import chunk_text_v2


TOKEN_RE = re.compile(r"^kata\d{3}$")


def test_long_paragraph_window_keeps_tokens_whole():
    text = " ".join(f"kata{i:03d}" for i in range(180))

    chunks = chunk_text_v2(text, chunk_size=155, overlap=43)

    assert len(chunks) > 2
    for chunk in chunks:
        tokens = re.findall(r"\S+", chunk.text)
        assert tokens
        assert all(TOKEN_RE.match(token) for token in tokens), chunk.text


def test_long_paragraph_chunks_keep_sequential_indices():
    text = " ".join(f"kata{i:03d}" for i in range(140))

    chunks = chunk_text_v2(text, chunk_size=140, overlap=50)

    assert len(chunks) > 1
    assert [chunk.metadata["chunk_index"] for chunk in chunks] == list(range(len(chunks)))
    assert all(chunk.metadata["chunker"] == "chunking_v2" for chunk in chunks)


def test_l1_export_skips_title_only_chunk_but_keeps_original_index(monkeypatch, tmp_path):
    import json

    from app.exporters import l1_jsonl_export as exporter
    from app.rag.chunking_v2 import Chunk

    approved_dir = tmp_path / "approved"
    output_path = tmp_path / "outputs" / "l1_chunks.jsonl"
    approved_dir.mkdir(parents=True)

    (approved_dir / "approved_doc.txt").write_text(
        "Ringkasan Pipeline\n\n"
        "Isi substantif dokumen menjelaskan bahwa data web harus melewati parser, "
        "quality gate, approved export, dan sandbox compare sebelum promosi aman.",
        encoding="utf-8",
    )

    def fake_chunk_text_v2(*args, **kwargs):
        return [
            Chunk(
                text="Ringkasan Pipeline",
                metadata={
                    "chunk_index": 0,
                    "section_title": "Ringkasan Pipeline",
                    "section_index": 0,
                    "chunker": "chunking_v2",
                    "document_hash": "doc-hash",
                    "chunk_hash": "title-hash",
                },
            ),
            Chunk(
                text=(
                    "Isi substantif dokumen menjelaskan bahwa data web harus melewati "
                    "parser, quality gate, approved export, dan sandbox compare sebelum "
                    "promosi aman."
                ),
                metadata={
                    "chunk_index": 1,
                    "section_title": "Ringkasan Pipeline",
                    "section_index": 0,
                    "chunker": "chunking_v2",
                    "document_hash": "doc-hash",
                    "chunk_hash": "body-hash",
                },
            ),
        ]

    monkeypatch.setattr(exporter, "chunk_text_v2", fake_chunk_text_v2)

    result = exporter.export_l1_chunks_jsonl(
        input_dir=approved_dir,
        output_path=output_path,
        chunk_size=220,
        overlap=40,
        min_chunk_chars=20,
    )

    records = [
        json.loads(line)
        for line in output_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert result.document_count == 1
    assert result.chunk_count == 1
    assert len(records) == 1
    assert records[0]["chunk_index"] == 0
    assert records[0]["metadata"]["chunk_index"] == 0
    assert records[0]["metadata"]["original_chunk_index"] == 1
    assert "Isi substantif dokumen" in records[0]["text"]
    assert "Ringkasan Pipeline" not in records[0]["text"]


def test_l1_export_keeps_single_title_only_document(tmp_path):
    import json

    from app.exporters.l1_jsonl_export import export_l1_chunks_jsonl

    approved_dir = tmp_path / "approved"
    output_path = tmp_path / "outputs" / "l1_chunks.jsonl"
    approved_dir.mkdir(parents=True)

    (approved_dir / "title_only.txt").write_text("Ringkasan Pipeline", encoding="utf-8")

    result = export_l1_chunks_jsonl(
        input_dir=approved_dir,
        output_path=output_path,
        chunk_size=220,
        overlap=40,
        min_chunk_chars=1,
    )

    records = [
        json.loads(line)
        for line in output_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert result.document_count == 1
    assert result.chunk_count == 1
    assert len(records) == 1
    assert records[0]["text"] == "Ringkasan Pipeline"
