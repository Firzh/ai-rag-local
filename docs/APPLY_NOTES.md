# APPLY_NOTES.md

Pembaruan dokumen untuk progress sampai **v2.2.3 L3**.

## Files

Copy file berikut ke root repo:

```text
README.md
DEVELOPMENT_PLAN.md
SPECIFICATION.md
UNFINISHED.md
CHANGELOG.md
```

## Command copy contoh Git Bash

Jika file hasil download berada di folder `_docs_update`:

```bash
cp _docs_update/README.md README.md
cp _docs_update/DEVELOPMENT_PLAN.md DEVELOPMENT_PLAN.md
cp _docs_update/SPECIFICATION.md SPECIFICATION.md
cp _docs_update/UNFINISHED.md UNFINISHED.md
cp _docs_update/CHANGELOG.md CHANGELOG.md
```

## Sanity check

```bash
git diff -- README.md DEVELOPMENT_PLAN.md SPECIFICATION.md UNFINISHED.md CHANGELOG.md
```

## Commit title

```bash
git add README.md DEVELOPMENT_PLAN.md SPECIFICATION.md UNFINISHED.md CHANGELOG.md
git commit -m "Update docs for v2.2.3 local RAG quality progress"
```
