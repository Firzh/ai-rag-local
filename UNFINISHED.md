# UNFINISHED.md

Status: **updated sampai v2.2.3 L3**  
Tanggal update: 2026-04-26

---

## Selesai

- v2.2 deterministic calculator dan Gemini API foundation.
- v2.2.1 provider error handling dan Ollama fallback.
- v2.2.2 API usage tracker, local quota awareness, dan query cache.
- Reorganisasi struktur `app/`.
- v2.2.3 L1 chunking v2 foundation.
- v2.2.3 L2a HTML parser foundation.
- v2.2.3 L2b HTML staging pipeline.
- v2.2.3 L3 quality gate.

---

## Belum selesai / pending

### L4 — Export approved chunks to JSONL

Tujuan:

- membuat JSONL yang bisa dikirim ke `rag-to-kaggle`;
- format satu baris per chunk;
- membawa `doc_id`, `text`, source metadata, dan chunk metadata.

Usulan:

```text
app/exports/l1_jsonl_export.py
app/commands/export_l1_chunks.py
app/benchmarks/l1_export_smoke.py
```

Command target:

```bash
python -m app.commands.export_l1_chunks \
  --input data/web_staging/approved \
  --output outputs/l1_chunks.jsonl
```

### L4b — Export existing Chroma collection

Tujuan:

- audit collection lama di Kaggle;
- tidak menimpa Chroma utama.

Usulan:

```text
app/chroma/export.py
app/commands/export_chroma_collection.py
```

### L5 — Compare Chroma lama vs sandbox

Tujuan:

- bandingkan old collection dan sandbox collection;
- catat top-k result, score, source, dan response quality.

Usulan:

```text
app/chroma/compare.py
app/commands/compare_chroma_collections.py
```

### L6 — Collection promote

Ditahan sampai compare lama-vs-baru aman.

### v2.3 — Mini scraper agent

Ditunda sampai Kaggle hook dan kontrak export/import stabil.

---

## Risiko yang perlu diawasi

1. **Cache membuat benchmark kurang informatif**  
   Regression tetap pass, tetapi `quality=None` bisa muncul jika output dari cache tidak menampilkan blok quality.

2. **Heading path belum hierarkis**  
   L1 baru punya `section_title` dan `section_index`. Untuk saat ini, `heading_path` bisa disamakan dengan `section_title`.

3. **Parser HTML masih basic**  
   Parser saat ini memakai `html.parser` bawaan Python. Untuk artikel web kompleks, mungkin perlu `trafilatura`, `readability-lxml`, atau BeautifulSoup pada tahap berikutnya.

4. **Quality gate rule masih awal**  
   Rule sudah cukup untuk mencegah data paling buruk, tetapi belum menilai kualitas semantik, near-duplicate, atau boilerplate ratio secara mendalam.

5. **Kaggle bukan backend produksi**  
   Kaggle hanya lab eksperimen. Hasil Kaggle harus kembali ke sandbox lokal, bukan langsung ke Chroma utama.

---

## Checklist sebelum L4

```text
[x] L1 committed
[x] L2a committed
[x] L2b committed
[x] L3 committed
[ ] Tentukan final JSONL schema untuk l1_chunks.jsonl
[ ] Buat export adapter dari approved staged docs
[ ] Buat smoke test export
[ ] Pastikan cleanup menghapus outputs/ jika perlu
```
