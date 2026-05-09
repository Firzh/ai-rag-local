# DOCS_MIGRATION_PLAN.md — Panduan Migrasi Dokumentasi ai-rag-local

Tanggal update: 2026-05-09
Target repo: `Firzh/ai-rag-local` / `rag-lc`

Dokumen ini memandu migrasi dokumentasi lama ke struktur dokumentasi baru.

## 1. Prinsip migrasi

1. Jangan langsung menghapus dokumen lama sebelum backup.
2. Arsipkan dokumen lama ke `docs/_archive/<tanggal>/`.
3. Salin dokumen baru dari paket update.
4. Update README dengan blok dokumentasi baru.
5. Jalankan `git diff` sebelum commit.
6. Commit perubahan dokumentasi dalam satu commit yang jelas.

## 2. Dokumen baru

```text
docs/DOCS_INDEX.md
docs/IMPLEMENTATION_STATUS.md
docs/DEVELOPMENT_PLAN.md
docs/RAG_BOUNDARY.md
docs/KAGGLE_HANDOFF_CONTRACT.md
docs/SANDBOX_COMPARE_SCOPE.md
docs/RUNTIME_GUARDS.md
docs/TEST_PLAN.md
docs/DOCS_MAINTENANCE_POLICY.md
docs/DOCS_MIGRATION_PLAN.md
```

## 3. Dokumen lama yang perlu dicek

```text
docs/DEVELOPMENT_PLAN.md
docs/UNFINISHED.md
docs/CHANGELOG.md
README.md
```

Rekomendasi:

- `docs/DEVELOPMENT_PLAN.md` boleh diganti dengan versi baru setelah backup.
- `docs/UNFINISHED.md` sebaiknya diarsipkan jika isinya sudah dipindahkan ke `IMPLEMENTATION_STATUS.md` dan `DEVELOPMENT_PLAN.md`.
- `docs/CHANGELOG.md` jangan dihapus jika masih dipakai sebagai riwayat; cukup backup atau pertahankan.
- README di-update dengan blok link dokumentasi.

## 4. Command bash ringkas

```bash
# dari root repo ai-rag-local
STAMP="2026-05-09-docs-before-boundary-sync"
mkdir -p "docs/_archive/$STAMP"

# backup / move dokumen lama
[ -f docs/DEVELOPMENT_PLAN.md ] && mv docs/DEVELOPMENT_PLAN.md "docs/_archive/$STAMP/DEVELOPMENT_PLAN.old.md"
[ -f docs/UNFINISHED.md ] && mv docs/UNFINISHED.md "docs/_archive/$STAMP/UNFINISHED.old.md"
[ -f docs/CHANGELOG.md ] && cp docs/CHANGELOG.md "docs/_archive/$STAMP/CHANGELOG.backup.md"
[ -f README.md ] && cp README.md "docs/_archive/$STAMP/README.backup.md"

# copy dokumen baru dari folder paket
cp -v /path/to/ai-rag-local-docs-update/docs/*.md docs/
cp -v /path/to/ai-rag-local-docs-update/README_DOCS_BLOCK.md docs/README_DOCS_BLOCK.md

# cek hasil
git status --short
git diff -- docs README.md
```

## 5. Delete lama setelah aman

Jika ingin benar-benar menghapus dokumen lama dari working tree, lakukan setelah backup dan setelah isi lamanya dipindahkan.

```bash
# contoh: hapus file lama yang sudah diarsipkan
rm -f docs/UNFINISHED.md
```

Catatan: jika file lama sudah di-`mv` ke archive, tidak perlu `rm` lagi.

## 6. Commit title

```text
docs(rag): align boundary, status, and docs maintenance cadence
```
