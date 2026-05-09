## Dokumentasi pengembangan

Dokumentasi detail dipisahkan dari README agar status implementasi, batas scope, dan rencana pengembangan tidak tercampur dengan panduan cepat.

| Dokumen | Fungsi |
|---|---|
| `docs/DOCS_INDEX.md` | Peta seluruh dokumentasi teknis repo |
| `docs/IMPLEMENTATION_STATUS.md` | Status fitur yang sudah selesai, pending, dan belum boleh dianggap tersedia |
| `docs/DEVELOPMENT_PLAN.md` | Rencana implementasi bertahap setelah L4 export foundation |
| `docs/RAG_BOUNDARY.md` | Batas scope `ai-rag-local` sebagai RAG lokal utama |
| `docs/KAGGLE_HANDOFF_CONTRACT.md` | Kontrak export/import dengan `rag-to-kaggle` |
| `docs/SANDBOX_COMPARE_SCOPE.md` | Scope L5 old Chroma vs sandbox compare |
| `docs/RUNTIME_GUARDS.md` | Parser Guard, Identity Guard, Graph Guard, Compressor Guard, dan Evidence Gate |
| `docs/TEST_PLAN.md` | Smoke test, regression, boundary test, dan promotion test |
| `docs/DOCS_MAINTENANCE_POLICY.md` | Kebijakan update dokumentasi, termasuk aturan 9+1 commit |

Catatan maintenance: setiap 9 commit implementasi, commit ke-10 wajib dipakai untuk update dokumentasi. Perubahan kontrak data, boundary, atau safety gate tetap wajib didokumentasikan segera walaupun belum mencapai commit ke-10.
