# DEVELOPMENT_PLAN.md

Status: **updated sampai L4 + post-L4 pipeline contract tests**
Tanggal update: 2026-05-06
Target repo: `Firzh/ai-rag-local` / `rag-lc`
Relasi project: `rag-to-kaggle` sebagai lab eksperimen data dan evaluasi

---

## 1. Arah pengembangan

Arah pengembangan saat ini bukan lagi sekadar memperbanyak provider LLM. Fokus utama adalah memperkuat kualitas data lokal, menstabilkan kontrak JSONL, dan memastikan setiap tahap pipeline bisa diuji sebagai rangkaian script yang saling terhubung.

Prinsip utama:

1. `rag-lc` adalah sistem utama.
2. Kaggle dipakai sebagai lab eksperimen, bukan runtime produksi.
3. Data web tidak boleh langsung masuk Chroma utama.
4. Parser, chunking, metadata, quality gate, export, import, dan benchmark harus punya kontrak yang jelas.
5. Setiap perubahan harus punya smoke test, contract test, atau regression check yang sesuai.
6. Promote ke Chroma utama ditahan sampai compare lama-vs-sandbox aman.

---

## 2. Progress sampai saat ini

### v2.2 - Calculator dan Gemini API foundation

Selesai:

- `safe_calculator` untuk arithmetic query.
- `math_guard` sebelum RAG retrieval.
- Gemini API via existing OpenAI-compatible provider.
- Query aritmatika tidak lagi bergantung pada LLM.
- Regression sudah memasukkan calculator cases.

### v2.2.1 - API error handling dan Ollama fallback

Selesai:

- Klasifikasi provider error: `bad_request`, `auth_error`, `model_not_found`, `rate_limited`, `provider_unavailable`, dan `network_error`.
- Fallback ke Ollama jika provider API gagal sesuai policy.
- Error Gemini `API_KEY_INVALID` diklasifikasi sebagai `auth_error`.
- Rate limit lokal/API bisa memicu fallback.
- Metadata fallback disimpan dalam record jawaban.

### v2.2.2 - Quota-aware API usage dan query cache

Selesai:

- Local API usage tracker berbasis SQLite.
- Report harian via `python -m app.api_usage_report`.
- Cache query sama agar tidak menghabiskan RPD Gemini.
- Cache accounting sudah memisahkan API request sungguhan dan cache hit.
- Local RPD preflight bisa memblok request API sebelum memanggil Gemini.
- Fallback tetap jalan saat local RPD limit tercapai.

### Reorganisasi `app/`

Selesai:

- Script dan command dipindahkan ke package lebih rapi: `app/benchmarks/`, `app/reports/`, `app/maintenance/`, `app/queries/`, dan `app/commands/`.
- Root wrapper tetap dipertahankan untuk command penting.

### v2.2.3 L1 - Chunking V2 foundation

Selesai:

- `app/rag/chunking_v2.py`
- `app/benchmarks/chunking_v2_smoke.py`

Fungsi utama:

- `clean_text_v2`
- `split_sections`
- `chunk_sections`
- `chunk_text_v2`

Metadata chunk:

- `chunk_index`
- `section_title`
- `section_index`
- `chunker`
- `char_count`
- `token_estimate`
- `document_hash`
- `chunk_hash`

### v2.2.3 L2a - HTML parser foundation

Selesai:

- `app/parsers/html_parser.py`
- `app/benchmarks/html_parser_smoke.py`

Kemampuan:

- membersihkan `script`, `style`, `nav`, `footer`, `header`, `aside`, dan noise HTML dasar;
- mengambil title, description, canonical URL, domain;
- menghasilkan `ParsedDocument(text, metadata)`;
- metadata parser menggunakan `html_parser_v1`.

### v2.2.3 L2b - HTML staging pipeline

Selesai:

- `app/staging/web_staging.py`
- `app/commands/parse_web_staging.py`
- `app/benchmarks/web_staging_smoke.py`

Output:

```text
data/web_staging/parsed_text/*.txt
data/web_staging/parsed_text/*.metadata.json
data/web_staging/parsed_text/manifest.jsonl
```

Jalur ini belum masuk Chroma. Ini disengaja agar data web melewati quality gate dulu.

### v2.2.3 L3 - Quality gate untuk staged web data

Selesai:

- `app/quality/quality_gate.py`
- `app/commands/run_quality_gate.py`
- `app/benchmarks/quality_gate_smoke.py`

Rule minimal:

- tolak teks kosong;
- tolak teks terlalu pendek;
- tolak potensi API key/token/password;
- tolak rasio simbol terlalu tinggi;
- tolak metadata wajib yang kosong;
- tolak web data tanpa URL/domain.

Output:

```text
data/web_staging/approved/
data/web_staging/quarantine/
data/audits/quality_gate_report.csv
```

### L4a - Export approved staged docs to L1 JSONL

Selesai:

- `app/exporters/l1_jsonl_export.py`
- `app/commands/export_l1_chunks.py`
- `app/benchmarks/l1_jsonl_export_smoke.py`

Tujuan:

- membawa staged data yang sudah approved ke format JSONL;
- menjaga satu baris JSON per chunk;
- membawa `doc_id`, `text`, source metadata, dan chunk metadata;
- menjaga agar Chroma utama tidak disentuh langsung.

Command target:

```bash
python -m app.commands.export_l1_chunks \
  --input data/web_staging/approved \
  --output outputs/l1_chunks.jsonl
```

### L4b - Chroma collection JSONL export foundation

Selesai:

- `app/exporters/chroma_jsonl_export.py`
- `app/commands/export_chroma_collection.py`
- `app/benchmarks/chroma_jsonl_export_smoke.py`

Tujuan:

- mengekspor collection Chroma existing ke JSONL untuk audit;
- memberi bahan compare lama-vs-sandbox pada L5;
- tidak menimpa Chroma utama;
- tidak menjalankan promote otomatis.

Command target:

```bash
python -m app.commands.export_chroma_collection \
  --collection rag_local \
  --output outputs/chroma_collection_export.jsonl
```

### Post-L4 - Pipeline contract test hardening

Selesai:

- `tests/conftest.py`
- `tests/test_pipeline_contract.py`
- patch `app/importers/jsonl_collection_importer.py`
- patch `app/quality/quality_gate.py`

Tujuan:

- memastikan output script sebelumnya bisa dipakai oleh script berikutnya;
- menangkap mismatch schema `doc_id` dan `document_id`;
- memastikan `quality_gate` membuat folder `approved` dan `quarantine` walaupun salah satunya kosong;
- memastikan dokumen quarantine tidak ikut export;
- memastikan metadata web tetap terbawa sampai JSONL.

Verified:

```bash
python -m pytest -q tests/test_pipeline_contract.py
```

Expected:

```text
4 passed
```

---

## 3. Kontrak pipeline saat ini

Jalur aman web data:

```text
raw_html
→ html_parser
→ parsed_text + metadata
→ quality_gate
→ approved / quarantine
→ l1_jsonl_export
→ jsonl_collection_importer
→ Chroma sandbox
→ regression / compare
→ promote jika aman
```

Jalur audit Chroma existing:

```text
Chroma existing collection
→ chroma_jsonl_export
→ JSONL audit
→ compare lama-vs-sandbox
```

---

## 4. Kontrak JSONL

Format minimal:

```json
{
  "doc_id": "dokumen_001",
  "text": "Isi chunk"
}
```

Format disarankan:

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

Catatan kontrak importer:

- Importer menerima `document_id` atau `doc_id`.
- Jika hanya ada `doc_id`, importer membuat ID unik per chunk memakai `doc_id:chunk_index` jika `chunk_index` tersedia.
- Jika `chunk_index` tidak tersedia, importer boleh memakai `doc_id:chunk_hash` jika metadata menyediakan `chunk_hash`.
- `doc_id` saja hanya fallback terakhir.

---

## 5. Roadmap terdekat

### Selesai

```text
[x] L1 chunking_v2 foundation
[x] L2a HTML parser foundation
[x] L2b HTML staging pipeline
[x] L3 quality gate
[x] L4a approved staged docs to L1 JSONL
[x] L4b Chroma collection JSONL export foundation
[x] Post-L4 pipeline contract tests
```

### Berikutnya

```text
[ ] L4a.1 chunking boundary refinement
[ ] L5 compare old Chroma vs sandbox/new corpus
[ ] L6 collection promote guard
[ ] v2.3 mini scraper agent, setelah Kaggle hook jelas
```

---

## 6. Test baseline sebelum patch berikutnya

```bash
python -m compileall app
python -m app.benchmarks.chunking_v2_smoke
python -m app.benchmarks.html_parser_smoke
python -m app.benchmarks.web_staging_smoke
python -m app.benchmarks.quality_gate_smoke
python -m app.benchmarks.l1_jsonl_export_smoke
python -m app.benchmarks.chroma_jsonl_export_smoke
python -m pytest -q tests/test_pipeline_contract.py

export RAG_LLM_PROVIDER=ollama
export RAG_MODEL_MODE=general
export RAG_QWEN_JUDGE_ENABLED=false
export RAG_VERIFICATION_AUDIT_ENABLED=false
python -m app.rag_regression_bench
```

Expected minimal untuk contract test:

```text
4 passed
```

Expected regression lokal:

```text
SUMMARY: 6/6 passed
```

---

## 7. L4a.1 Backlog - Chunking V2 boundary refinement

Status: backlog teknis setelah L4a JSONL export.

Tujuan refinement:

- Chunk tidak dimulai dari tengah kata.
- Chunk tidak berakhir di tengah kata jika masih ada batas aman.
- Overlap tidak menyebabkan pengulangan frasa yang terlalu terlihat.
- Title-only chunk tidak diekspor sebagai chunk mandiri.
- Heading tetap dipertahankan sebagai metadata, bukan selalu sebagai chunk teks terpisah.
- Anti-loop guard tetap aman.

Acceptance criteria:

- `python -m app.benchmarks.l1_jsonl_export_smoke` lulus.
- `python -m pytest -q tests/test_pipeline_contract.py` tetap lulus.
- `python -m app.rag_regression_bench` tetap `6/6 passed`.
- Export JSONL tidak membawa title-only chunk.
- Exported `chunk_index` berurutan mulai dari 0.
- `metadata.original_chunk_index` tetap tersimpan.
- Tidak ada chunk yang jelas dimulai dari tengah kata pada smoke sample.
- Tidak ada overlap yang menduplikasi frasa secara kasar pada smoke sample.
