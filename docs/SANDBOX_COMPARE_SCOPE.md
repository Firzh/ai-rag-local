# SANDBOX_COMPARE_SCOPE.md — Scope L5 Old Chroma vs Sandbox Compare

Tanggal update: 2026-05-09
Target repo: `Firzh/ai-rag-local` / `rag-lc`

Dokumen ini menjelaskan scope L5. Status saat ini: **belum implemented / planned**. Yang sudah ada hanya fondasi export JSONL dari approved staged docs dan Chroma existing.

## 1. Tujuan L5

L5 bertujuan membandingkan collection lama dengan sandbox collection sebelum ada promote ke Chroma utama.

```text
old Chroma collection
  -> benchmark queries
  -> old retrieval report

sandbox collection
  -> benchmark queries yang sama
  -> sandbox retrieval report

compare
  -> diff retrieval, score, source, metadata, failed cases
  -> promote recommendation
```

## 2. Masuk scope L5

| Komponen | Scope |
|---|---|
| Load benchmark queries | Ya |
| Query old collection | Ya |
| Query sandbox collection | Ya |
| Compare top-k result | Ya |
| Compare source/doc_id/chunk_index | Ya |
| Compare score/distance | Ya |
| Flag failed queries | Ya |
| Generate compare report | Ya |
| Recommend safe/unsafe | Ya, sebagai rekomendasi |

## 3. Tidak masuk scope L5

```text
- promote otomatis
- menulis ke Chroma utama
- menerima hasil Kaggle sebagai final
- menjalankan notebook Kaggle
- melakukan sweep embedding besar
- melakukan GAC production consolidation
- menghapus collection lama
```

## 4. Output L5 yang disarankan

```text
outputs/chroma_compare/compare_summary.json
outputs/chroma_compare/query_results.jsonl
outputs/chroma_compare/source_diff.jsonl
outputs/chroma_compare/failed_queries.jsonl
outputs/chroma_compare/promote_recommendation.md
```

## 5. Metrik minimum

| Metrik | Fungsi |
|---|---|
| `top1_same_source_rate` | Apakah sumber top-1 tetap konsisten |
| `topk_source_overlap` | Apakah top-k masih memuat sumber lama yang relevan |
| `metadata_retention_rate` | Apakah metadata penting tetap ada |
| `identity_query_success` | Apakah query angka/nama/tanggal/kode tetap berhasil |
| `failed_query_count` | Jumlah query yang turun kualitasnya |
| `score_gap_change` | Apakah sandbox membuat hasil makin ambigu |

## 6. Query wajib untuk L5

Benchmark harus mencakup:

```text
query definisi
query angka
query tanggal
query nama/kode
query tabel
query relasional
query ringkasan
query tidak ditemukan
query lintas dokumen
query dengan istilah ambigu
```

## 7. Syarat lulus L5

Sandbox boleh direkomendasikan untuk L6 bila:

```text
- failed_query_count tidak naik signifikan
- identity-critical queries tetap benar
- source/doc_id/chunk_index tidak hilang
- sandbox tidak menarik boilerplate sebagai top evidence
- metadata retention aman
- regression lokal tetap lulus
```

## 8. Hubungan L5 dengan rag-to-kaggle

`rag-to-kaggle` boleh menyediakan report eksternal, risk label, atau recommended params. Namun, L5 compare tetap harus berjalan di `ai-rag-local`. Hasil Kaggle tidak menggantikan L5.

## 9. Catatan maintenance

Dokumen ini harus diperbarui saat command L5 dibuat, output report berubah, atau metrik compare ditambah. Setiap 9 commit implementasi, commit ke-10 wajib mengecek dokumen ini.
