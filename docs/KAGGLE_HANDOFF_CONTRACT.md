# KAGGLE_HANDOFF_CONTRACT.md — Kontrak ai-rag-local ke rag-to-kaggle

Tanggal update: 2026-05-09
Target repo sumber: `Firzh/ai-rag-local` / `rag-lc`
Target repo evaluator: `Firzh/rag-to-kaggle`

Dokumen ini mendefinisikan kontrak handoff antara `ai-rag-local` dan `rag-to-kaggle`. Kontrak ini mencegah hasil eksperimen Kaggle dianggap sebagai hasil production-ready.

## 1. Prinsip handoff

1. `ai-rag-local` adalah pemilik data production/staging lokal.
2. `rag-to-kaggle` adalah pipeline eksperimen, audit, dan evaluator.
3. Pertukaran utama menggunakan file, bukan akses langsung ke Chroma utama.
4. Hasil Kaggle kembali sebagai report/risk label/rekomendasi.
5. Promote ke Chroma utama hanya terjadi di `ai-rag-local` setelah compare dan regression lokal.

## 2. Arah data keluar dari ai-rag-local

```text
ai-rag-local
  -> approved JSONL export
  -> Chroma existing JSONL export
  -> manifest
  -> benchmark queries
  -> baseline metrics
  -> rag-to-kaggle
```

File yang boleh dikirim:

```text
exports/approved_chunks.jsonl
exports/chroma_existing_export.jsonl
exports/manifest.json
exports/benchmark_queries.jsonl
exports/baseline_metrics.json
```

## 3. Kontrak JSONL minimal

```json
{
  "doc_id": "dokumen_001",
  "text": "Isi chunk"
}
```

## 4. Kontrak JSONL yang disarankan

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
    "url": "https://example.com/artikel",
    "domain": "example.com",
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

## 5. Manifest wajib

Setiap export harus punya manifest agar hasil audit tidak mencampur model, collection, atau schema berbeda.

```json
{
  "project": "ai-rag-local",
  "export_type": "approved_chunks|chroma_existing_export",
  "schema_version": "rag_jsonl_contract_v1",
  "collection_name": "rag_multilingual_minilm_l12_v2_384",
  "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
  "chunker": "chunking_v2",
  "created_at": "2026-05-09T00:00:00Z",
  "source_repo": "Firzh/ai-rag-local",
  "target_repo": "Firzh/rag-to-kaggle"
}
```

## 6. Output yang boleh kembali dari rag-to-kaggle

```text
reports/kaggle_eval_summary.json
reports/retrieval_eval_by_query.jsonl
reports/chunk_risk_labels.jsonl
reports/geometry_audit_summary.json
reports/recommended_runtime_policy.json
reports/failed_cases.jsonl
reports/evaluation_report.md
```

Makna output:

| Output | Boleh dipakai untuk | Tidak boleh dipakai untuk |
|---|---|---|
| `risk_labels.jsonl` | Menandai chunk/cluster berisiko | Menghapus chunk asli otomatis |
| `recommended_params.json` | Kandidat konfigurasi | Override config production otomatis |
| `failed_cases.jsonl` | Regression dan debugging | Menyimpulkan semua retrieval gagal |
| `geometry_audit_summary.json` | Risk label, guard policy | GAC production langsung |
| `benchmark_report.json` | Bahan L5 compare | Promote otomatis |

## 7. Output yang tidak boleh diterima sebagai final

```text
Chroma baru siap production
centroid sebagai pengganti chunk asli
promotion decision final dari Kaggle
config production override otomatis
notebook metric sebagai satu-satunya dasar promote
```

## 8. Alur aman import hasil Kaggle

```text
rag-to-kaggle report
  -> import report ke ai-rag-local
  -> build local sandbox collection bila perlu
  -> run old-vs-sandbox compare
  -> run local regression
  -> inspect failed cases
  -> promote guard
  -> owner approval
  -> promote jika aman
```

## 9. Red flags

Handoff harus ditolak bila:

```text
manifest hilang
schema_version tidak cocok
embedding_model tidak cocok
collection_name tidak jelas
chunk_hash hilang pada data yang akan dibandingkan
source/doc_id hilang
approval_status tidak jelas
file berasal dari output Kaggle tanpa report evaluasi
```

## 10. Aturan maintenance

Perubahan pada kontrak JSONL, manifest, output report, atau promotion flow harus memperbarui dokumen ini. Dalam siklus normal, setiap 9 commit implementasi diikuti commit ke-10 untuk dokumentasi.
