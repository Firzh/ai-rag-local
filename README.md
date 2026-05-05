# ai-rag-local / rag-lc

Status update: L4 JSONL export foundation + post-L4 pipeline contract tests
Tanggal update: 2026-05-06

Repository ini diarahkan sebagai RAG lokal utama. Prinsip pengembangan saat ini adalah memperkuat kualitas data lokal, menjaga Chroma utama tetap aman, dan memakai JSONL sebagai jembatan audit menuju `rag-to-kaggle` atau sandbox lokal.

## Status ringkas

| Area | Status |
|---|---|
| Calculator deterministic | Selesai pada v2.2 |
| Gemini via OpenAI-compatible provider | Selesai sebagai fondasi API eksternal |
| API error handling + Ollama fallback | Selesai pada v2.2.1 |
| API usage tracker + query cache | Selesai pada v2.2.2 |
| Reorganisasi struktur `app/` | Selesai |
| L1 Chunking V2 foundation | Selesai |
| L2a HTML parser foundation | Selesai |
| L2b HTML staging pipeline | Selesai |
| L3 Quality gate untuk staged web data | Selesai |
| L4a Approved staged docs to L1 JSONL | Selesai |
| L4b Chroma collection JSONL export | Selesai sebagai fondasi audit |
| Post-L4 pipeline contract tests | Selesai, `4 passed` |
| L5 Chroma compare lama vs sandbox | Berikutnya |
| L6 Collection promote | Ditahan sampai benchmark lama-vs-baru aman |

## Prinsip arsitektur saat ini

`rag-lc` tetap menjadi sistem utama untuk ingestion lokal, retrieval, verification, dan answer generation. Kaggle diposisikan sebagai lab eksperimen untuk audit data, parameter chunking, embedding batch, retrieval evaluation, dan eksperimen ringan sebelum hasilnya diimpor ulang ke environment lokal.

Pipeline data web tidak boleh langsung masuk ke Chroma utama. Jalur aman yang dipakai:

```text
raw_html
→ html_parser
→ parsed_text + metadata
→ quality_gate
→ approved / quarantine
→ L1 JSONL export
→ sandbox import / Kaggle audit
→ benchmark
→ promote jika aman
```

Export Chroma lama juga tersedia untuk audit, tetapi bukan jalur promosi otomatis:

```text
Chroma existing collection
→ Chroma JSONL export
→ audit / compare
→ sandbox benchmark
```

## Kontrak JSONL

Kontrak minimal untuk pertukaran data adalah satu baris JSON per chunk.

```json
{
  "doc_id": "dokumen_001",
  "text": "Isi chunk"
}
```

Kontrak yang disarankan:

```json
{
  "doc_id": "dokumen_001",
  "title": "Judul Dokumen",
  "source": "file_asal.pdf atau URL",
  "source_type": "web|local_file|chroma",
  "parser": "html_parser_v1|pdf_parser|text_parser|chroma_export",
  "page": null,
  "chunk_index": 0,
  "text": "Isi chunk",
  "metadata": {
    "section_title": "Pendahuluan",
    "section_index": 0,
    "heading_path": "Pendahuluan",
    "char_count": 850,
    "token_estimate": 210,
    "document_hash": "sha256...",
    "chunk_hash": "sha256...",
    "chunker": "chunking_v2",
    "approval_status": "approved",
    "quality_gate_status": "approved"
  }
}
```

Importer JSONL sekarang menerima `document_id` atau `doc_id`. Jika hanya ada `doc_id`, importer membuat ID unik per chunk memakai pola `doc_id:chunk_index` jika `chunk_index` tersedia.

## Perintah penting

Regression lokal:

```bash
export RAG_LLM_PROVIDER=ollama
export RAG_MODEL_MODE=general
export RAG_QWEN_JUDGE_ENABLED=false
export RAG_VERIFICATION_AUDIT_ENABLED=false

python -m app.rag_regression_bench
```

Smoke tests:

```bash
python -m app.benchmarks.chunking_v2_smoke
python -m app.benchmarks.html_parser_smoke
python -m app.benchmarks.web_staging_smoke
python -m app.benchmarks.quality_gate_smoke
python -m app.benchmarks.l1_jsonl_export_smoke
python -m app.benchmarks.chroma_jsonl_export_smoke
```

Post-L4 contract tests:

```bash
python -m pytest -q tests/test_pipeline_contract.py
```

Expected:

```text
4 passed
```

Cleanup generated outputs:

```bash
python -m app.maintenance.cleanup_generated_outputs --yes
```

## Catatan

Jangan kirim Chroma utama langsung ke pipeline eksperimen. Gunakan JSONL dan sandbox lokal terlebih dahulu. Promote ke Chroma utama hanya boleh dilakukan setelah compare lama-vs-baru dan regression menunjukkan hasil aman.
