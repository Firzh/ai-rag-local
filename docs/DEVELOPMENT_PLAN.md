# DEVELOPMENT_PLAN.md — ai-rag-local

Tanggal update: 2026-05-09
Target repo: `Firzh/ai-rag-local` / `rag-lc`
Relasi project: `rag-to-kaggle` sebagai pipeline eksperimen/evaluator

## 1. Arah pengembangan

Arah pengembangan `ai-rag-local` bukan memperluas eksperimen tanpa batas, tetapi memperkuat RAG lokal dengan guard yang jelas. Repo ini harus tetap menjadi pemilik ingestion lokal, parser, quality gate, retrieval, graph, compressor, evidence pack, regression lokal, sandbox compare lokal, dan promote guard.

`rag-to-kaggle` hanya menjadi pipeline eksternal untuk audit, eksperimen, dan evaluasi. Output dari `rag-to-kaggle` kembali sebagai report/risk label/recommended params, bukan sebagai Chroma production siap pakai.

## 2. Prinsip prioritas

1. Jangan ubah Chroma utama sebelum L5 compare dan L6 promote guard selesai.
2. Jangan jadikan Kaggle sebagai backend produksi.
3. Jangan jadikan geometry audit atau GAC sebagai replacement Chroma utama.
4. Jangan biarkan graph dan compressor memperbesar noise dari parser yang lemah.
5. Setiap implementasi harus punya test atau minimal smoke test.
6. Setiap 9 commit implementasi, commit ke-10 wajib dokumentasi.

## 3. Roadmap prioritas

### P0 — Dokumentasi dan boundary sync

Status: prioritas pertama.

Target:

```text
README link update
DOCS_INDEX.md
IMPLEMENTATION_STATUS.md
RAG_BOUNDARY.md
KAGGLE_HANDOFF_CONTRACT.md
DOCS_MAINTENANCE_POLICY.md
```

Tujuan:

- Dokumentasi tidak lagi memberi kesan L5/L6 sudah selesai.
- Boundary `ai-rag-local` vs `rag-to-kaggle` eksplisit.
- Aturan update dokumentasi 9+1 commit dicatat.

### P1 — L4a.1 Chunking boundary refinement

Status: planned.

Rasional:

L5 compare tidak ideal jika chunk masih dapat mulai/berakhir di tengah kata, title-only chunk ikut export, atau metadata chunk tidak stabil.

Scope:

```text
- cegah chunk mulai dari tengah kata
- cegah chunk berakhir di potongan kata
- kurangi overlap kasar
- cegah title-only chunk masuk export
- pastikan chunk_index tetap berurutan
- pertahankan original_chunk_index pada metadata bila ada transformasi
```

Out of scope:

```text
- eksperimen chunking besar di Kaggle
- dynamic chunker berbasis LLM
- automatic re-chunk seluruh Chroma utama
```

### P2 — L5 Old Chroma vs sandbox compare

Status: planned/pending.

Scope:

```text
old Chroma collection -> query benchmark -> old top-k report
sandbox collection -> query benchmark yang sama -> sandbox top-k report
compare -> diff retrieval, metadata, source, score, failed cases
```

Output:

```text
outputs/chroma_compare/compare_summary.json
outputs/chroma_compare/query_results.jsonl
outputs/chroma_compare/failed_queries.jsonl
outputs/chroma_compare/promote_recommendation.md
```

Out of scope:

```text
- promote otomatis
- import hasil Kaggle langsung ke Chroma utama
- GAC production consolidation
- embedding model sweep besar
```

### P3 — L6 Collection promote guard

Status: planned setelah L5 aman.

Scope:

```text
- baca compare report
- baca regression report
- cek failed queries
- cek metadata/source retention
- cek query angka/nama/tanggal/kode
- minta owner approval sebelum promote
- siapkan rollback manifest
```

Tidak boleh promote jika:

```text
- L5 belum ada
- regression belum jalan
- sandbox lebih buruk dari old collection
- metadata source hilang
- query identity-critical gagal
- owner belum approve
```

### P4 — Runtime guards bertahap

Status: planned bertahap.

Urutan aman:

```text
1. Chunk Identity Guard sederhana
2. Graph Guard untuk query angka/spesifik
3. Compressor Guard untuk negasi dan syarat
4. Evidence Sufficiency Gate
5. Parser Guard lanjutan
6. Retrieval Router berbasis intent
7. Geometry Audit sebagai risk label, bukan replacement engine
```

Catatan:

Runtime guards sebaiknya tidak dibuat terlalu besar sebelum L5, karena setiap guard harus dapat diuji dalam old-vs-sandbox compare dan regression lokal.

### P5 — Integrasi report dari rag-to-kaggle

Status: planned setelah handoff contract stabil.

`ai-rag-local` boleh menerima:

```text
risk_labels.jsonl
recommended_params.json
benchmark_report.json
failed_queries.jsonl
geometry_audit_summary.json
```

`ai-rag-local` tidak boleh menerima langsung:

```text
production Chroma replacement
centroid-only memory store
promotion decision final dari Kaggle
config override otomatis tanpa regression lokal
```

## 4. Catatan trade-off

### Parser Guard

Benefit: mengurangi noise sejak awal.
Trade-off: recall bisa turun karena chunk yang meragukan masuk quarantine.
Scope: masuk `ai-rag-local`.

### Chunk Identity Guard

Benefit: menjaga angka, tanggal, kode, nama, dan versi agar tidak hilang saat graph/compression.
Trade-off: konteks bisa lebih panjang dan graph lebih sering mati.
Scope: masuk `ai-rag-local`.

### Graph Guard

Benefit: graph hanya aktif saat query memang relasional.
Trade-off: eksplorasi relasi implisit bisa berkurang.
Scope: masuk `ai-rag-local`.

### Compressor Guard

Benefit: mencegah syarat, negasi, dan fakta angka terpotong.
Trade-off: token konteks naik.
Scope: masuk `ai-rag-local`.

### Geometry Audit

Benefit: memberi risk label pada cluster/chunk.
Trade-off: mahal, tidak selalu stabil untuk cluster kecil.
Scope: lightweight risk label di `ai-rag-local`, full experiment di `rag-to-kaggle`.

## 5. Aturan dokumentasi

Setiap 9 commit implementasi, commit ke-10 wajib memperbarui dokumentasi. Commit dokumentasi harus mengecek minimal:

```text
README.md
DOCS_INDEX.md
IMPLEMENTATION_STATUS.md
DEVELOPMENT_PLAN.md
TEST_PLAN.md
RAG_BOUNDARY.md / KAGGLE_HANDOFF_CONTRACT.md bila boundary berubah
```

<!-- L4A1_BOUNDARY_REFINEMENT_START -->
## L4a.1 Chunking Boundary Refinement

L4a.1 refines the L4a approved-docs-to-L1-JSONL path without entering L5
sandbox compare. The goal is to protect evidence identity before retrieval,
graph expansion, compressor pruning, or collection promotion uses the exported
chunks.

Patch scope:

- refine long paragraph splitting so chunk windows do not start from a broken
  token when a safe boundary exists;
- prefer sentence or whitespace end boundaries before falling back to hard cut;
- filter `title-only` chunks from L1 export only when body chunks still exist in
  the same document;
- preserve sequential exported `chunk_index`;
- preserve `metadata.original_chunk_index` for auditability.

Trade-off:

- precision and evidence cleanliness improve;
- some heading-only chunks disappear from L1 export when better body evidence
  exists;
- documents that only contain a title-like chunk are still preserved so quality
  gate or later review can decide.

The patch intentionally does not implement L5 sandbox compare, L6 promote guard,
graph guard, compressor guard, or geometry audit.
<!-- L4A1_BOUNDARY_REFINEMENT_END -->
