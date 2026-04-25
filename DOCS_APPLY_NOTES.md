# Documentation Update Apply Notes — v2.1

## Files to replace

Copy these downloaded files into the repository root:

```text
README.md
DEVELOPMENT_PLAN.md
SPECIFICATION.md
UNFINISHED.md
CHANGELOG.md
```

## File to remove

Remove the obsolete stage patch note:

```bash
git rm README_STAGE_A_C.md
```

Reason: the A-C patch note was transitional. Its useful content is now consolidated into the main documentation.

## Files not to commit

Do not commit local output artifacts unless intentionally creating fixtures:

```text
data/answers/*.answer.json
data/answers/*.answer.md
data/evidence/*.evidence.json
data/quality/model_smoke_bench-*.json
data/quality/rag_regression_bench-*.json
```

Keep the database only if it is intentionally tracked:

```text
data/quality/answer_quality.sqlite3
```

## Suggested git cleanup before adding docs

```bash
git restore data/answers data/evidence env_qwen_patch.sample
rm -f .env.qwen-patch.sample
rm -f data/quality/model_smoke_bench-*.json
rm -f data/quality/rag_regression_bench-*.json
```

## Suggested git add

```bash
git add README.md DEVELOPMENT_PLAN.md SPECIFICATION.md UNFINISHED.md CHANGELOG.md

git add app/answer_evaluator.py app/model_smoke_bench.py app/rag_regression_bench.py

git rm README_STAGE_A_C.md
```

## Suggested commit message

```bash
git commit -m "Document v2.1 local RAG benchmark baseline"
```

If you want code and documentation split into two commits:

```bash
git add app/answer_evaluator.py app/model_smoke_bench.py app/rag_regression_bench.py
git commit -m "Add local model and RAG regression benchmarks"

git add README.md DEVELOPMENT_PLAN.md SPECIFICATION.md UNFINISHED.md CHANGELOG.md
git rm README_STAGE_A_C.md
git commit -m "Document v2.1 local RAG baseline"
```
