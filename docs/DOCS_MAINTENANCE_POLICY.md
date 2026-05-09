# DOCS_MAINTENANCE_POLICY.md — Kebijakan Maintenance Dokumentasi

Tanggal update: 2026-05-09
Target repo: `Firzh/ai-rag-local` / `rag-lc`

Dokumen ini mengatur kapan dokumentasi harus diperbarui.

## 1. Aturan 9+1 commit

Setiap 9 commit implementasi, commit ke-10 wajib menjadi commit dokumentasi.

```text
9 commit implementasi -> 1 commit dokumentasi
```

Commit implementasi mencakup:

```text
feat
fix
refactor
perf
test yang terkait fitur
pipeline/script perubahan behavior
```

Commit dokumentasi ke-10 minimal mengecek:

```text
README.md
DOCS_INDEX.md
IMPLEMENTATION_STATUS.md
DEVELOPMENT_PLAN.md
TEST_PLAN.md
RAG_BOUNDARY.md
KAGGLE_HANDOFF_CONTRACT.md
SANDBOX_COMPARE_SCOPE.md bila L5 berubah
RUNTIME_GUARDS.md bila guard berubah
```

## 2. Contoh siklus

```text
01 feat(rag): add chunk identity flag
02 test(rag): cover identity flag for numeric chunks
03 feat(rag): add graph seed gate
04 test(rag): block graph for numeric queries
05 feat(rag): add compressor negation guard
06 test(rag): preserve negation in evidence pack
07 feat(rag): add evidence sufficiency status
08 test(rag): block answer when evidence is weak
09 fix(rag): stabilize metadata propagation
10 docs(rag): update guard status and regression notes
```

## 3. Dokumentasi wajib segera, tidak menunggu commit ke-10

Perubahan berikut wajib didokumentasikan segera:

```text
JSONL contract berubah
manifest berubah
Chroma write path berubah
sandbox compare behavior berubah
promote guard berubah
parser approval/quarantine behavior berubah
graph expansion policy berubah
compressor behavior berubah
evidence sufficiency behavior berubah
security/privacy boundary berubah
```

## 4. Commit title dokumentasi

Default:

```text
docs(rag): update documentation after implementation batch
```

Untuk boundary:

```text
docs(rag): align boundary and handoff contract
```

Untuk status:

```text
docs(rag): refresh implementation status and roadmap
```

Untuk testing:

```text
docs(rag): update test plan and regression notes
```

## 5. Checklist commit dokumentasi

Sebelum commit dokumentasi:

```text
[ ] IMPLEMENTATION_STATUS.md membedakan selesai vs pending
[ ] DEVELOPMENT_PLAN.md sesuai roadmap terbaru
[ ] TEST_PLAN.md memuat test baru
[ ] RAG_BOUNDARY.md masih sesuai scope repo
[ ] KAGGLE_HANDOFF_CONTRACT.md sesuai kontrak terbaru
[ ] README tidak mengklaim fitur pending sebagai selesai
[ ] CHANGELOG atau release notes diperbarui bila perlu
```

## 6. Anti-pattern

Hindari:

```text
- menulis fitur planned sebagai implemented
- menaruh semua detail di README
- membiarkan DEVELOPMENT_PLAN tertinggal dari commit implementasi
- menghapus dokumen lama tanpa arsip saat migrasi besar
- menerima output Kaggle sebagai production-ready tanpa dokumentasi gate
```
