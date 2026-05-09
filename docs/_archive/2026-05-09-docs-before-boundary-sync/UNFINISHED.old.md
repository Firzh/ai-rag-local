# UNFINISHED.md

Status: **updated sampai L4 + post-L4 pipeline contract tests**
Tanggal update: 2026-05-06

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
- L4a approved staged docs to L1 JSONL export.
- L4b Chroma collection JSONL export foundation.
- Post-L4 pipeline contract tests.

---

## Selesai pada post-L4 test commit

### Pipeline contract tests

Files:

```text
tests/conftest.py
tests/test_pipeline_contract.py
```

Cakupan:

- static compile contract untuk `app/**/*.py`;
- raw HTML → staging → quality gate → approved → L1 JSONL;
- quarantine document tidak ikut export;
- L1 exporter output kompatibel dengan JSONL importer;
- importer menerima `doc_id` sebagai alias `document_id`;
- quality gate membuat output directory walaupun semua dokumen masuk quarantine.

Verified:

```bash
python -m pytest -q tests/test_pipeline_contract.py
```

Expected:

```text
4 passed
```

---

## Belum selesai / pending

### L4a.1 - Chunking boundary refinement

Tujuan:

- mencegah chunk dimulai dari tengah kata;
- mengurangi overlap kasar;
- mencegah title-only chunk ikut export;
- menjaga `chunk_index` tetap berurutan;
- menjaga metadata `original_chunk_index` tetap tersedia.

Acceptance criteria:

```text
[ ] l1_jsonl_export_smoke passed
[ ] test_pipeline_contract.py passed
[ ] rag_regression_bench tetap 6/6 passed
[ ] tidak ada title-only chunk pada export sample
[ ] tidak ada chunk yang jelas dimulai dari tengah kata
```

### L5 - Compare Chroma lama vs sandbox

Tujuan:

- bandingkan old collection dan sandbox collection;
- catat top-k result, score, source, dan response quality;
- pastikan import JSONL ke sandbox tidak menurunkan retrieval;
- jadikan hasil compare sebagai syarat sebelum promote.

Usulan file:

```text
app/chroma/compare.py
app/commands/compare_chroma_collections.py
app/benchmarks/chroma_compare_smoke.py
```

### L6 - Collection promote guard

Ditahan sampai:

1. quality gate lulus;
2. JSONL export/import stabil;
3. compare lama-vs-sandbox menunjukkan hasil aman;
4. regression RAG tidak turun;
5. human owner menyetujui promote.

### v2.3 - Mini scraper agent

Ditunda sampai:

- Kaggle hook jelas;
- kontrak export/import stabil;
- compare pipeline tersedia;
- promote guard tersedia.

---

## Risiko yang perlu diawasi

1. **Boundary chunk belum ideal**
   
   L1 export sudah stabil, tetapi beberapa chunk masih berisiko mulai dari potongan kata atau frasa. Ini masuk backlog L4a.1.

2. **Kaggle bukan backend produksi**
   
   Kaggle hanya lab eksperimen. Hasil Kaggle harus kembali ke sandbox lokal, bukan langsung ke Chroma utama.

3. **Importer fleksibel harus tetap menjaga ID unik**
   
   `doc_id` boleh dipakai sebagai alias, tetapi Chroma tetap butuh ID unik per chunk. Pola aman adalah `doc_id:chunk_index`.

4. **Quality gate masih rule-based**
   
   Rule saat ini cukup untuk mencegah data paling buruk. Belum ada near-duplicate detection, semantic quality scoring, atau boilerplate ratio yang lebih rinci.

5. **Chroma export bersifat audit**
   
   Export collection lama tidak boleh dianggap sebagai promote path. Output-nya hanya bahan audit dan compare.

---

## Checklist sebelum L5

```text
[x] L1 committed
[x] L2a committed
[x] L2b committed
[x] L3 committed
[x] L4a L1 JSONL export committed
[x] L4b Chroma JSONL export foundation committed
[x] Post-L4 contract tests committed
[ ] Jalankan ulang smoke test L4a
[ ] Jalankan ulang smoke test L4b
[ ] Jalankan contract test
[ ] Jalankan regression bench lokal
[ ] Desain schema compare lama-vs-sandbox
[ ] Buat compare command
[ ] Buat compare smoke test
```
