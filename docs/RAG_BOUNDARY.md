# RAG_BOUNDARY.md — Batas Scope ai-rag-local

Tanggal update: 2026-05-09
Target repo: `Firzh/ai-rag-local` / `rag-lc`

Dokumen ini mendefinisikan batas tanggung jawab `ai-rag-local`. Tujuannya agar repo ini tidak berubah menjadi lab eksperimen Kaggle, crawler umum, atau sistem auto-promote tanpa pengaman.

## 1. Definisi peran

`ai-rag-local` adalah RAG lokal utama. Repo ini bertanggung jawab atas alur produksi/staging lokal dari data sampai jawaban berbasis evidence.

```text
local/web data
  -> parser
  -> quality gate
  -> approved/quarantine
  -> chunking
  -> Chroma/FTS/Graph
  -> retrieval
  -> reranker
  -> compressor
  -> evidence pack
  -> answer generation
  -> local regression
```

## 2. Yang termasuk scope ai-rag-local

| Area | Masuk scope? | Catatan |
|---|---:|---|
| Ingestion lokal | Ya | File lokal, staged data, approved corpus |
| HTML parser foundation | Ya | Parser lokal harus menghasilkan metadata yang bisa diaudit |
| Quality gate | Ya | Approved/quarantine tetap keputusan lokal |
| L1 JSONL export | Ya | Kontrak handoff ke sandbox/Kaggle |
| Chroma utama | Ya | Hanya `ai-rag-local` yang boleh mengontrol Chroma utama |
| Chroma JSONL export | Ya | Untuk audit/compare, bukan promote otomatis |
| FTS | Ya | Mendukung exact/lexical retrieval |
| Mini graph store | Ya | Evidence expansion lokal, bukan reasoning engine bebas |
| Hybrid retrieval | Ya | Runtime retrieval utama |
| Reranker | Ya | Memilih kandidat evidence |
| Context compressor | Ya | Harus extractive dan evidence-preserving |
| Evidence pack | Ya | Output wajib untuk jawaban berbasis sumber |
| Local sandbox compare | Ya | L5 planned, bukan Kaggle experiment |
| Promote guard | Ya | L6 planned, harus menahan perubahan Chroma utama |
| Regression lokal | Ya | Wajib sebelum promote |

## 3. Yang tidak termasuk scope ai-rag-local

| Area | Milik siapa? | Catatan |
|---|---|---|
| Kaggle notebook generation | `rag-to-kaggle` | Jangan masuk repo RAG utama |
| Upload/download Kaggle Dataset | `rag-to-kaggle` | Bukan runtime RAG |
| Embedding model sweep besar | `rag-to-kaggle` | Lokal hanya menerima rekomendasi setelah diuji |
| Chunking parameter sweep besar | `rag-to-kaggle` | Lokal hanya menerapkan kandidat yang lolos regression |
| Full spectral visualization | `rag-to-kaggle` | Lokal cukup risk label ringan |
| GAC production consolidation | Belum | Jangan mengganti chunk asli dengan centroid |
| Auto-promote dari Kaggle | Tidak boleh | Semua promote harus lokal dan gated |
| Shell/patch agent otomatis | Bukan scope saat ini | Ikuti pola dokumen dan manual review |

## 4. Boundary runtime

### 4.1 Graph tidak selalu aktif

Graph hanya boleh aktif bila query membutuhkan hubungan, alur, sebab-akibat, atau konteks multi-hop. Graph harus dimatikan atau dibatasi untuk query angka, tahun, kode, ID, nominal, pasal, nama spesifik, atau pertanyaan yang cukup dijawab dengan exact evidence.

### 4.2 Compressor tidak boleh menghilangkan identitas evidence

Compressor harus menjaga:

```text
negasi: tidak, bukan, kecuali
syarat: hanya, wajib, setelah, sebelum
angka: 2024, Rp75.000, top_k=6
kode: ID, pasal, SKU, env var
metadata: source, doc_id, chunk_index
```

### 4.3 Parser harus diperlakukan sebagai sumber risiko

Chunk dari parser rendah tidak boleh dipakai sebagai evidence final tanpa warning. Parser Guard harus membedakan konten utama, tabel, heading, daftar pustaka, nav/footer, dan boilerplate.

## 5. Boundary Chroma utama

Chroma utama tidak boleh ditulis dari:

```text
Kaggle output langsung
sandbox collection yang belum dibandingkan
geometry consolidation yang belum diuji
JSONL tanpa metadata minimum
chunk hasil parser untrusted
```

Chroma utama hanya boleh berubah setelah:

```text
1. data approved
2. sandbox collection dibangun
3. old-vs-sandbox compare berjalan
4. regression lokal berjalan
5. failed cases dievaluasi
6. promote guard lolos
7. owner approval diberikan
```

## 6. Boundary dengan rag-to-kaggle

`ai-rag-local` mengirim:

```text
approved_chunks.jsonl
chroma_existing_export.jsonl
manifest.json
benchmark_queries.jsonl
baseline_metrics.json
```

`ai-rag-local` menerima:

```text
benchmark_report.json
failed_queries.jsonl
risk_labels.jsonl
recommended_params.json
geometry_audit_summary.json
```

`ai-rag-local` tidak menerima sebagai final:

```text
Chroma production replacement
promotion decision
config override otomatis
centroid-only memory store
```

## 7. Aturan maintenance

Setiap 9 commit implementasi, commit ke-10 wajib memperbarui dokumen ini bila ada perubahan boundary. Perubahan yang menyentuh Chroma utama, JSONL contract, graph, compressor, sandbox compare, atau promote guard wajib didokumentasikan segera.
