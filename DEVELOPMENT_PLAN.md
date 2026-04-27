# DEVELOPMENT_PLAN.md

Status: **updated sampai v2.2.3 L3**  
Tanggal update: 2026-04-26  
Target repo: `Firzh/ai-rag-local` / `rag-lc`  
Relasi project: `rag-to-kaggle` sebagai lab eksperimen data dan evaluasi

---

## 1. Arah pengembangan

Arah pengembangan saat ini bukan lagi sekadar memperbanyak provider LLM, tetapi memperkuat kualitas data lokal sebelum Chroma diperluas. Gemini API tetap dipakai sebagai resource terbatas, sedangkan Ollama tetap menjadi fallback lokal. Pipeline Kaggle belum dijadikan backend produksi, melainkan lab untuk audit, eksperimen parameter, dan validasi kualitas data.

Prinsip utama:

1. `rag-lc` adalah sistem utama.
2. Kaggle dipakai sebagai lab eksperimen, bukan runtime produksi.
3. Data web tidak boleh langsung masuk Chroma utama.
4. Parser, chunking, metadata, dan quality gate harus kuat sebelum mini scraper agent berjalan penuh.
5. Setiap perubahan harus punya smoke test dan regression check.

---

## 2. Progress sampai saat ini

### v2.2 — Calculator dan Gemini API foundation

Selesai:

- `safe_calculator` untuk arithmetic query.
- `math_guard` sebelum RAG retrieval.
- Gemini API via existing OpenAI-compatible provider.
- Query aritmatika tidak lagi bergantung pada LLM.
- Regression sudah memasukkan calculator cases.

### v2.2.1 — API error handling dan Ollama fallback

Selesai:

- Klasifikasi provider error: `bad_request`, `auth_error`, `model_not_found`, `rate_limited`, `provider_unavailable`, dan `network_error`.
- Fallback ke Ollama jika provider API gagal sesuai policy.
- Error Gemini `API_KEY_INVALID` diklasifikasi sebagai `auth_error`.
- Rate limit lokal/API bisa memicu fallback.
- Metadata fallback disimpan dalam record jawaban.

### v2.2.2 — Quota-aware API usage dan query cache

Selesai:

- Local API usage tracker berbasis SQLite.
- Report harian via `python -m app.api_usage_report`.
- Cache query sama agar tidak menghabiskan RPD Gemini.
- Cache accounting sudah memisahkan API request sungguhan dan cache hit.
- Local RPD preflight bisa memblok request API sebelum memanggil Gemini.
- Fallback tetap jalan saat local RPD limit tercapai.

### Reorganisasi `app/`

Selesai:

- Script/command dipindahkan ke package lebih rapi: `app/benchmarks/`, `app/reports/`, `app/maintenance/`, `app/queries/`, dan `app/commands/`.
- Root wrapper tetap dipertahankan untuk command penting.

### v2.2.3 L1 — Chunking V2 foundation

Selesai:

- File:
  - `app/rag/chunking_v2.py`
  - `app/benchmarks/chunking_v2_smoke.py`
- Fungsi utama:
  - `clean_text_v2`
  - `split_sections`
  - `chunk_sections`
  - `chunk_text_v2`
- Metadata chunk:
  - `chunk_index`
  - `section_title`
  - `section_index`
  - `chunker`
  - `char_count`
  - `token_estimate`
  - `document_hash`
  - `chunk_hash`

Catatan: L1 belum otomatis menghasilkan JSONL. Untuk kebutuhan `rag-to-kaggle`, perlu export adapter agar output `Chunk(text, metadata)` dapat ditulis sebagai `l1_chunks.jsonl`.

### v2.2.3 L2a — HTML parser foundation

Selesai:

- File:
  - `app/parsers/html_parser.py`
  - `app/benchmarks/html_parser_smoke.py`
- Kemampuan:
  - membersihkan `script`, `style`, `nav`, `footer`, `header`, `aside`, dan noise HTML dasar;
  - mengambil title, description, canonical URL, domain;
  - menghasilkan `ParsedDocument(text, metadata)`;
  - metadata parser menggunakan `html_parser_v1`.

### v2.2.3 L2b — HTML staging pipeline

Selesai:

- File:
  - `app/staging/web_staging.py`
  - `app/commands/parse_web_staging.py`
  - `app/benchmarks/web_staging_smoke.py`
- Output:
  - `data/web_staging/parsed_text/*.txt`
  - `data/web_staging/parsed_text/*.metadata.json`
  - `data/web_staging/parsed_text/manifest.jsonl`
- Jalur ini belum masuk Chroma. Ini disengaja agar data web melewati quality gate dulu.

### v2.2.3 L3 — Quality gate untuk staged web data

Selesai:

- File:
  - `app/quality/quality_gate.py`
  - `app/commands/run_quality_gate.py`
  - `app/benchmarks/quality_gate_smoke.py`
- Rule minimal:
  - tolak teks kosong;
  - tolak teks terlalu pendek;
  - tolak potensi API key/token/password;
  - tolak rasio simbol terlalu tinggi;
  - tolak metadata wajib yang kosong;
  - tolak web data tanpa URL/domain.
- Output:
  - `approved`
  - `quarantine`
  - `quality_gate_report.csv`

---

## 3. Kontrak awal `rag-lc` → `rag-to-kaggle`

Format pertukaran direkomendasikan JSONL, satu baris per chunk.

Minimal wajib:

```json
{
  "doc_id": "dokumen_001",
  "text": "Isi chunk"
}
```

Format yang sangat disarankan:

```json
{
  "doc_id": "dokumen_001",
  "title": "Judul Dokumen",
  "source": "file_asal.pdf atau URL",
  "source_type": "local_file|web",
  "parser": "pdf_parser|text_parser|html_parser_v1",
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
    "chunker": "chunking_v2"
  }
}
```

Catatan:

- `doc_id`, `title`, `source`, `source_type`, `parser`, dan `page` datang dari parser/staging/base metadata.
- `chunk_index`, `section_title`, `section_index`, `char_count`, `token_estimate`, `document_hash`, `chunk_hash`, dan `chunker` datang dari `chunking_v2`.
- `heading_path` untuk saat ini bisa disamakan dengan `section_title` karena L1 belum membangun hierarki heading lengkap.

---

## 4. Analisis pengembangan L4+

### L4 — Export approved chunks to JSONL for `rag-to-kaggle`

Tujuan:

- menghasilkan file JSONL untuk audit Kaggle;
- membawa data approved dari staging ke `rag-to-kaggle`;
- menjaga agar Chroma utama tidak disentuh langsung.

Usulan file:

```text
app/exports/l1_jsonl_export.py
app/commands/export_l1_chunks.py
app/benchmarks/l1_export_smoke.py
```

Output:

```text
outputs/l1_chunks.jsonl
```

Command target:

```bash
python -m app.commands.export_l1_chunks \
  --input data/web_staging/approved \
  --output outputs/l1_chunks.jsonl
```

Prioritas L4 sebaiknya export dari `approved` staging terlebih dahulu karena sudah melewati parser dan quality gate. Export Chroma lama bisa dibuat setelah kontrak JSONL stabil.

### L4b — Export existing Chroma collection for audit

Tujuan:

- audit collection lama di Kaggle;
- tidak menimpa Chroma utama.

Usulan file:

```text
app/chroma/export.py
app/commands/export_chroma_collection.py
```

### L5 — Compare collection lama vs sandbox

Tujuan:

- membandingkan Chroma lama dengan Chroma sandbox hasil import;
- menjalankan query benchmark yang sama;
- melihat perubahan top-k retrieval dan kualitas jawaban.

Usulan file:

```text
app/chroma/compare.py
app/commands/compare_chroma_collections.py
```

### L6 — Collection promote

Ditahan sampai:

1. quality gate lulus;
2. export/import Kaggle stabil;
3. compare lama-vs-sandbox menunjukkan hasil aman;
4. regression RAG tidak turun.

Tidak boleh promote otomatis ke Chroma utama pada tahap awal.

---

## 5. Roadmap terdekat

### Selesai

```text
[x] L1 chunking_v2 foundation
[x] L2a HTML parser foundation
[x] L2b HTML staging pipeline
[x] L3 quality gate
```

### Berikutnya

```text
[ ] L4 export approved chunks to JSONL for rag-to-kaggle
[ ] L4b export existing Chroma chunks to JSONL for audit
[ ] L5 compare old collection vs sandbox collection
[ ] L6 collection promote guard
[ ] v2.3 mini scraper agent, setelah Kaggle hook jelas
```

---

## 6. Test baseline sebelum dan sesudah patch berikutnya

```bash
python -m compileall app
python -m app.benchmarks.chunking_v2_smoke
python -m app.benchmarks.html_parser_smoke
python -m app.benchmarks.web_staging_smoke
python -m app.benchmarks.quality_gate_smoke

export RAG_LLM_PROVIDER=ollama
export RAG_MODEL_MODE=general
export RAG_QWEN_JUDGE_ENABLED=false
export RAG_VERIFICATION_AUDIT_ENABLED=false
python -m app.rag_regression_bench
```

Expected:

```text
semua smoke passed
rag_regression_bench SUMMARY: 6/6 passed
```

---

## v2.2.3 L4a Follow-up — Chunking V2 Boundary Refinement Backlog

Status: backlog teknis setelah L4a JSONL export.

### Latar belakang

L4a `export_l1_chunks` sudah menghasilkan JSONL yang kompatibel untuk alur `rag-lc -> rag-to-kaggle`. Smoke test sudah lulus, anti-loop test sudah aman, dan regression benchmark tetap lulus. Namun hasil inspeksi JSONL menunjukkan masih ada isu kualitas chunk yang perlu diperbaiki sebelum data dipakai untuk audit retrieval skala lebih besar di Kaggle.

Temuan utama:

1. Beberapa chunk masih dapat dimulai dari potongan kata atau potongan frasa, misalnya `"Gate RAG Lokal"` alih-alih `"Quality Gate RAG Lokal"`.
2. Overlap masih dapat menghasilkan duplikasi yang terasa kasar, misalnya frasa `"Kaggle digunakan sebagai lab"` muncul sebagai overlap sebelum teks lanjutan.
3. Chunking sudah tidak infinite loop, tetapi boundary semantik belum ideal.

Catatan: isu ini tidak memblokir L4a karena exporter sudah menjalankan fungsi inti: menyaring chunk terlalu pendek, menormalisasi `chunk_index`, menyimpan `original_chunk_index`, dan menghasilkan JSONL dengan `doc_id`, `text`, serta metadata chunking. Refinement ini ditunda agar L4a tetap kecil dan mudah diuji.

### Tujuan refinement

Meningkatkan kualitas chunk sebelum export ke Kaggle tanpa mengubah kontrak JSONL.

Target:

- Chunk tidak dimulai dari tengah kata.
- Chunk tidak berakhir di tengah kata jika masih ada batas aman.
- Overlap tidak menyebabkan pengulangan frasa yang terlalu terlihat.
- Title-only chunk tidak diekspor sebagai chunk mandiri.
- Heading tetap dipertahankan sebagai metadata, bukan selalu sebagai chunk teks terpisah.
- Anti-loop guard tetap aman.

### Rencana teknis

#### 1. Safe boundary split

Tambahkan fungsi boundary yang lebih sadar kata dan kalimat:

- `_find_safe_window_end()`
- `_find_safe_window_start()`
- `_find_sentence_boundary()`

Urutan prioritas boundary:

1. Paragraf
2. Kalimat
3. Spasi antar kata
4. Hard character boundary sebagai fallback terakhir

#### 2. Overlap refinement

Overlap perlu dibuat lebih bersih:

- Hindari overlap yang dimulai dari tengah kata.
- Hindari overlap yang hanya berupa potongan frasa pendek.
- Hindari duplikasi penuh antara akhir chunk sebelumnya dan awal chunk berikutnya.
- Simpan overlap secukupnya untuk konteks, bukan mengulang terlalu agresif.

#### 3. Short chunk handling

Chunk pendek perlu diperlakukan sebagai berikut:

- Jika chunk pendek hanya heading/title, jangan diekspor sebagai chunk mandiri.
- Jika memungkinkan, gabungkan heading pendek dengan paragraf berikutnya.
- Exporter tetap memiliki `min_chunk_chars` sebagai safety layer.

#### 4. Metadata tetap kompatibel

Kontrak JSONL tidak berubah.

Field yang harus tetap ada:

- `doc_id`
- `text`
- `title`
- `source`
- `source_type`
- `parser`
- `page`
- `chunk_index`
- `metadata.section_title`
- `metadata.section_index`
- `metadata.heading_path`
- `metadata.document_hash`
- `metadata.chunk_hash`
- `metadata.chunker = chunking_v2`
- `metadata.chunking_version = chunking_v2`
- `metadata.original_chunk_index`

### Acceptance criteria

Refinement dianggap selesai jika:

- `python -m app.benchmarks.l1_jsonl_export_smoke` lulus.
- Anti-loop test tetap lulus.
- `python -m app.rag_regression_bench` tetap 6/6 passed.
- Export JSONL tidak membawa title-only chunk.
- Exported `chunk_index` berurutan mulai dari 0.
- `metadata.original_chunk_index` tetap tersimpan.
- Tidak ada chunk yang jelas dimulai dari tengah kata pada smoke sample.
- Tidak ada overlap yang menduplikasi frasa secara kasar pada smoke sample.

### Posisi roadmap

Refinement ini tidak wajib sebelum L4a commit. Masukkan sebagai pekerjaan lanjutan sebelum atau bersamaan dengan L4b/L5 jika hasil compare retrieval menunjukkan dampak negatif dari boundary chunk yang kasar.

Rekomendasi urutan:

1. L4a — Export approved staged docs to JSONL.
2. L4a.1 — Chunking boundary refinement.
3. L4b — Export existing Chroma collection for Kaggle audit.
4. L5 — Compare old Chroma vs sandbox/new corpus.

