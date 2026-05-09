# APPLY_NOTES.md

Pembaruan dokumen untuk progress sampai **L4 + post-L4 pipeline contract tests**.

## Files

Copy file berikut ke root repo:

```text
README.md
docs/DEVELOPMENT_PLAN.md
docs/SPECIFICATION.md
docs/UNFINISHED.md
docs/CHANGELOG.md
docs/APPLY_NOTES.md
```

## Command copy contoh Git Bash

Jika file hasil download berada di folder `_docs_l4_post_test_update`:

```bash
cp _docs_l4_post_test_update/README.md README.md
cp _docs_l4_post_test_update/docs/DEVELOPMENT_PLAN.md docs/DEVELOPMENT_PLAN.md
cp _docs_l4_post_test_update/docs/SPECIFICATION.md docs/SPECIFICATION.md
cp _docs_l4_post_test_update/docs/UNFINISHED.md docs/UNFINISHED.md
cp _docs_l4_post_test_update/docs/CHANGELOG.md docs/CHANGELOG.md
cp _docs_l4_post_test_update/docs/APPLY_NOTES.md docs/APPLY_NOTES.md
```

## Sanity check

```bash
git diff -- README.md docs/DEVELOPMENT_PLAN.md docs/SPECIFICATION.md docs/UNFINISHED.md docs/CHANGELOG.md docs/APPLY_NOTES.md
```

## Verification

```bash
python -m pytest -q tests/test_pipeline_contract.py
```

Expected:

```text
4 passed
```

Opsional jika environment lokal lengkap:

```bash
python -m app.benchmarks.l1_jsonl_export_smoke
python -m app.benchmarks.chroma_jsonl_export_smoke
```

## Commit title

```bash
git add README.md docs/DEVELOPMENT_PLAN.md docs/SPECIFICATION.md docs/UNFINISHED.md docs/CHANGELOG.md docs/APPLY_NOTES.md
git commit -m "docs(l4): update post-L4 pipeline contract documentation"
```
