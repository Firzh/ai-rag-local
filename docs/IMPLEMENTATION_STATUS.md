# IMPLEMENTATION_STATUS.md — ai-rag-local

Tanggal update: 2026-05-09
Target repo: `Firzh/ai-rag-local` / `rag-lc`

Dokumen ini menjadi sumber status implementasi. Tujuannya agar dokumentasi tidak memberi kesan bahwa fitur pending sudah tersedia.

## 1. Status ringkas saat ini

| Area | Status | Catatan |
|---|---|---|
| Calculator deterministic | Selesai | Fondasi query aritmatika deterministik |
| Gemini via OpenAI-compatible provider | Selesai | Fondasi API eksternal |
| API error handling + Ollama fallback | Selesai | Fallback lokal saat provider gagal |
| API usage tracker + query cache | Selesai | Mengurangi konsumsi request API |
| Reorganisasi struktur `app/` | Selesai | Command, benchmark, report, maintenance dipisah |
| L1 Chunking V2 foundation | Selesai | Fondasi chunking lokal |
| L2a HTML parser foundation | Selesai | Fondasi parser HTML |
| L2b HTML staging pipeline | Selesai | Jalur staged web data |
| L3 Quality gate staged web data | Selesai | Approved/quarantine untuk data web |
| L4a Approved staged docs to L1 JSONL | Selesai | Export approved staged docs ke kontrak L1 JSONL |
| L4b Chroma collection JSONL export | Selesai sebagai fondasi | Bahan audit dan compare, bukan compare final |
| Post-L4 pipeline contract tests | Selesai | Expected: `4 passed` |
| L4a.1 Chunking boundary refinement | Belum selesai | Patch terdekat sebelum L5 |
| L5 Old Chroma vs sandbox compare | Belum selesai | Masih planned/pending |
| L6 Collection promote guard | Belum selesai | Ditahan sampai L5 + regression aman |

## 2. Fitur yang sudah boleh dianggap tersedia

### 2.1 Export foundation

Fondasi export sudah tersedia pada dua arah:

```text
approved staged docs -> L1 JSONL export
Chroma existing collection -> JSONL export foundation
```

Makna status ini:

- Data approved dapat dikeluarkan dalam bentuk JSONL untuk audit atau handoff.
- Chroma existing dapat diekspor sebagai bahan audit/compare.
- Export Chroma bukan izin untuk promote otomatis.

### 2.2 Pipeline contract tests

Post-L4 contract tests sudah menjadi baseline safety. Test ini harus tetap berjalan sebelum perubahan L5/L6.

Expected:

```text
python -m pytest -q tests/test_pipeline_contract.py
4 passed
```

## 3. Fitur yang belum boleh dianggap tersedia

### 3.1 L5 Sandbox Compare

L5 belum selesai. Istilah `sandbox compare` dalam dokumentasi harus selalu ditulis sebagai planned/pending sampai command dan benchmark terkait tersedia.

Belum tersedia sebagai fitur final:

```text
old collection query benchmark
sandbox collection query benchmark
old-vs-sandbox diff report
failed query report
safe/unsafe promote recommendation
```

### 3.2 L6 Collection Promote Guard

L6 belum selesai. Tidak boleh ada alur yang langsung mengganti Chroma utama dari hasil Kaggle atau sandbox tanpa compare lokal dan regression.

Belum tersedia sebagai fitur final:

```text
promote command
approval gate
rollback manifest
promotion report
owner confirmation
```

### 3.3 Runtime guards lanjutan

Guard berikut belum dianggap final:

```text
Parser Guard lanjutan
Chunk Identity Guard
Retrieval Router berbasis intent
Graph Guard
Compressor Guard
Evidence Sufficiency Gate lanjutan
Geometry Audit runtime policy
```

## 4. Aturan penulisan status

Gunakan kata berikut secara konsisten:

| Status | Makna |
|---|---|
| `Selesai` | Sudah ada implementasi dan test minimal |
| `Selesai sebagai fondasi` | Sudah ada dasar, tetapi bukan fitur end-to-end |
| `Planned` / `Pending` | Direncanakan, belum boleh dipakai sebagai fitur tersedia |
| `Ditahan` | Sengaja belum dibuat karena menunggu gate sebelumnya |
| `Eksperimental` | Boleh diuji, tidak boleh menjadi default production |

## 5. Aturan dokumentasi 9+1 commit

Setiap 9 commit implementasi, commit ke-10 wajib memperbarui dokumentasi ini beserta dokumen terkait. Perubahan safety, kontrak data, atau boundary tetap wajib didokumentasikan segera walaupun belum mencapai commit ke-10.

<!-- L4A1_BOUNDARY_REFINEMENT_START -->
## L4a.1 Chunking Boundary Refinement

Status: implemented on the L4a.1 feature branch after contract tests pass. The
change becomes part of the main documentation source of truth after the PR is
merged.

Implemented behavior:

- long-paragraph chunk windows avoid starting from the middle of a token when a
  safe boundary exists;
- chunk window end prefers sentence or whitespace boundaries before hard-cut
  fallback;
- `title-only` chunks are skipped during L1 JSONL export when the same document
  still has substantive body chunks;
- exported `chunk_index` remains sequential after filtering;
- `metadata.original_chunk_index` preserves the source chunk index before export
  filtering.

Out of scope:

- no Chroma main write;
- no L5 old Chroma vs sandbox compare;
- no L6 promote guard;
- no geometry-aware consolidation;
- no Kaggle-side pipeline execution.
<!-- L4A1_BOUNDARY_REFINEMENT_END -->
