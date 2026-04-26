# SPECIFICATION.md

Status: **updated sampai v2.2.3 L3**  
Tanggal update: 2026-04-26

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

Arithmetic query ditangani oleh deterministic calculator tool, bukan raw LLM. Output calculator memakai:

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
    base_metadata: dict | None = None
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

---

## 9. Kaggle bridge contract

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
  "source_type": "web|local_file",
  "parser": "html_parser_v1|pdf_parser|text_parser",
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
    "chunker": "chunking_v2"
  }
}
```

---

## 10. Generated outputs

Generated runtime outputs tidak boleh ikut commit:

```text
data/answers/
data/evidence/
data/web_staging/
data/audits/
data/quality/*.json
data/quality/*.sqlite3
```

Gunakan:

```bash
python -m app.maintenance.cleanup_generated_outputs --yes
```
