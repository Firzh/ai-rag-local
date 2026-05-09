# DOCS_INDEX.md — ai-rag-local Documentation Map

Tanggal update: 2026-05-09
Target repo: `Firzh/ai-rag-local` / `rag-lc`

Dokumen ini menjadi indeks dokumentasi teknis untuk `ai-rag-local`. README cukup memuat status ringkas dan tautan ke dokumen ini. Detail scope, status, boundary, testing, dan maintenance dipisahkan agar tidak membuat README terlalu berat.

## Peta dokumen

| Dokumen | Status | Fungsi |
|---|---|---|
| `IMPLEMENTATION_STATUS.md` | Wajib | Membedakan fitur selesai, pending, dan belum boleh dianggap tersedia |
| `DEVELOPMENT_PLAN.md` | Wajib | Menentukan urutan implementasi setelah L4 export foundation |
| `RAG_BOUNDARY.md` | Wajib | Menjaga `ai-rag-local` tetap sebagai RAG lokal utama, bukan lab eksperimen |
| `KAGGLE_HANDOFF_CONTRACT.md` | Wajib | Menentukan kontrak file dengan `rag-to-kaggle` |
| `SANDBOX_COMPARE_SCOPE.md` | Wajib sebelum L5 | Menjelaskan batas L5 old Chroma vs sandbox compare |
| `RUNTIME_GUARDS.md` | Wajib bertahap | Menjelaskan Parser Guard, Identity Guard, Graph Guard, Compressor Guard, dan Evidence Gate |
| `TEST_PLAN.md` | Wajib | Menentukan smoke test, regression test, dan promotion test |
| `DOCS_MAINTENANCE_POLICY.md` | Wajib | Mengatur pembaruan dokumentasi berkala, termasuk aturan 9+1 commit |
| `DOCS_MIGRATION_PLAN.md` | Opsional setelah migrasi | Panduan mengarsipkan/mengganti dokumen lama |

## Prinsip navigasi dokumentasi

1. README hanya memuat ringkasan dan link.
2. Status implementasi selalu dicek di `IMPLEMENTATION_STATUS.md`.
3. Batas scope RAG dan Kaggle selalu dicek di `RAG_BOUNDARY.md` dan `KAGGLE_HANDOFF_CONTRACT.md`.
4. Fitur pending tidak boleh ditulis sebagai fitur selesai.
5. Setiap perubahan kontrak JSONL, Chroma, sandbox, graph, compressor, atau promote harus mengubah dokumen terkait.

## Catatan penting

`ai-rag-local` adalah runtime RAG lokal. `rag-to-kaggle` adalah pipeline eksperimen/evaluator. Hasil Kaggle tidak boleh langsung memodifikasi Chroma utama. Semua hasil eksternal harus kembali sebagai report/risk label/recommended params, lalu diuji ulang secara lokal.
