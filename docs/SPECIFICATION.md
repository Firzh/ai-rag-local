# SPECIFICATION.md

Status: **updated sampai L4 + post-L4 pipeline contract tests**
Tanggal update: 2026-05-06

---

## 1. Runtime RAG utama

`rag-lc` menjalankan RAG lokal dengan komponen utama:

```text
parser/staging
→ chunking
→ embedding
→ Chroma retrieval
→ prompt builder
→ LLM provider
→ verification
→ quality evaluation
→ answer record
```

Provider LLM yang aktif:

```text
ollama
openai_compatible
```

Gemini API dipakai melalui `openai_compatible`. Ollama tetap menjadi fallback lokal.

---

## 2. Deterministic calculator

Arithmetic query ditangani oleh deterministic calculator tool, bukan raw LLM.

Output calculator memakai:

```text
tool_used = safe_calculator
verifier_mode = tool_only
quality_score = 1.0
quality_pass = True
```

---

## 3. Provider error dan fallback

Provider error diklasifikasi menjadi:

```text
bad_request
auth_error
model_not_found
rate_limited
provider_unavailable
network_error
unknown_provider_error
```

Fallback policy:

```text
rate_limited / network / provider unavailable → boleh fallback sesuai env
auth_error / bad_request / model_not_found → tidak fallback secara default
```

---

## 4. Quota-aware API usage

Usage tracker menyimpan pemakaian API harian ke:

```text
data/quality/api_usage.sqlite3
```

Report:

```bash
python -m app.api_usage_report
```

Cache hit tidak dihitung sebagai request API eksternal.

---

## 5. Chunking V2

Modul:

```text
app/rag/chunking_v2.py
```

API utama:

```python
chunk_text_v2(
    text: str,
    chunk_size: int = 900,
    overlap: int = 120,
    base_metadata: dict | None = None,
) -> list[Chunk]
```

Metadata otomatis:

```text
chunk_index
section_title
section_index
chunker
char_count
token_estimate
document_hash
chunk_hash
```

---

## 6. HTML parser

Modul:

```text
app/parsers/html_parser.py
```

API utama:

```python
parse_html_file(path, url="", fetched_at="") -> ParsedDocument
extract_main_text(html_text: str) -> str
extract_web_metadata(html_text, source_path, url="", fetched_at="") -> dict
```

Metadata web:

```text
source_type = web
source_name
source_path
url
domain
title
description
fetched_at
parsed_at
content_hash
document_hash
parser = html_parser_v1
parser_version = html_parser_v1
license_note
approval_status = staged
```

---

## 7. Web staging

Modul:

```text
app/staging/web_staging.py
```

Command:

```bash
python -m app.commands.parse_web_staging --input data/web_staging/raw_html
```

Output:

```text
data/web_staging/parsed_text/*.txt
data/web_staging/parsed_text/*.metadata.json
data/web_staging/parsed_text/manifest.jsonl
```

---

## 8. Quality gate

Modul:

```text
app/quality/quality_gate.py
```

Command:

```bash
python -m app.commands.run_quality_gate \
  --input data/web_staging/parsed_text \
  --report data/audits/quality_gate_report.csv
```

Rule minimal:

```text
empty_text
too_short
secret_detected
symbol_ratio_high
metadata_missing
web_metadata_missing
approval_status_unknown
```

Output:

```text
data/web_staging/approved/
data/web_staging/quarantine/
data/audits/quality_gate_report.csv
```

Post-L4 contract:

- Jika `copy_outputs=True`, folder `approved` dan `quarantine` wajib dibuat walaupun salah satunya kosong.
- Dokumen quarantine tidak boleh diekspor ke JSONL.
- Report tetap dibuat untuk audit.

---

## 9. L1 JSONL export

Modul:

```text
app/exporters/l1_jsonl_export.py
```

Command:

```bash
python -m app.commands.export_l1_chunks \
  --input data/web_staging/approved \
  --output outputs/l1_chunks.jsonl
```

Tujuan:

- membaca `.txt` dan `.metadata.json` dari folder approved;
- menjalankan chunking v2;
- menulis satu baris JSON per chunk;
- menjaga `doc_id`, `text`, `chunk_index`, source metadata, dan chunk metadata.

---

## 10. Chroma collection JSONL export

Modul:

```text
app/exporters/chroma_jsonl_export.py
```

Command:

```bash
python -m app.commands.export_chroma_collection \
  --collection rag_local \
  --output outputs/chroma_collection_export.jsonl
```

Tujuan:

- mengekspor collection Chroma existing ke JSONL;
- menyediakan bahan audit dan compare;
- tidak menulis balik ke Chroma utama;
- tidak menjalankan promote otomatis.

Smoke test:

```bash
python -m app.benchmarks.chroma_jsonl_export_smoke
```

---

## 11. JSONL importer contract

Modul:

```text
app/importers/jsonl_collection_importer.py
```

Kontrak input wajib:

```text
text
metadata
```

ID record boleh memakai salah satu:

```text
document_id
doc_id
```

Resolusi ID:

1. Pakai `document_id` jika tersedia.
2. Jika tidak ada, pakai `doc_id:chunk_index` jika `chunk_index` tersedia.
3. Jika tidak ada, pakai `doc_id:chunk_hash` jika metadata menyediakan `chunk_hash`.
4. Pakai `doc_id` saja sebagai fallback terakhir.

Alasan:

- `doc_id` mewakili dokumen.
- Satu dokumen bisa menghasilkan banyak chunk.
- Chroma membutuhkan ID unik per record.

---

## 12. Kaggle bridge contract

Format pertukaran data ke `rag-to-kaggle` menggunakan JSONL, satu baris per chunk.

Wajib:

```json
{
  "doc_id": "...",
  "text": "..."
}
```

Disarankan:

```json
{
  "doc_id": "...",
  "title": "...",
  "source": "...",
  "source_type": "web|local_file|chroma",
  "parser": "html_parser_v1|pdf_parser|text_parser|chroma_export",
  "page": null,
  "chunk_index": 0,
  "text": "...",
  "metadata": {
    "section_title": "...",
    "section_index": 0,
    "heading_path": "...",
    "char_count": 850,
    "token_estimate": 210,
    "document_hash": "...",
    "chunk_hash": "...",
    "chunker": "chunking_v2",
    "approval_status": "approved",
    "quality_gate_status": "approved"
  }
}
```

---

## 13. Post-L4 contract tests

Files:

```text
tests/conftest.py
tests/test_pipeline_contract.py
```

Cakupan:

- compile check untuk file Python di `app/`;
- web pipeline contract dari raw HTML sampai L1 JSONL;
- quarantine contract agar dokumen secret tidak masuk export;
- importer compatibility contract untuk `doc_id` alias `document_id`.

Command:

```bash
python -m pytest -q tests/test_pipeline_contract.py
```

Expected:

```text
4 passed
```

---

## 14. Generated outputs

Generated runtime outputs tidak boleh ikut commit:

```text
data/answers/
data/evidence/
data/web_staging/
data/audits/
data/quality/*.json
data/quality/*.sqlite3
outputs/
```

Gunakan:

```bash
python -m app.maintenance.cleanup_generated_outputs --yes
```
