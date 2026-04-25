# Changelog

## v2.1.1 — Hybrid Qwen Judge Integration

Status: integration baseline passed.

### Added

- Documented Qwen judge integration through Ollama OpenAI-compatible `/v1`.
- Documented runtime env for enabling semantic judge and verification audit.
- Added roadmap notes for Qwen Cloud API, OpenAI API, and provider abstraction.
- Added roadmap notes for deterministic calculator tooling.

### Verified

Observed judge configuration:

```text
RAG_QWEN_JUDGE_ENABLED=true
RAG_VERIFICATION_AUDIT_ENABLED=true
RAG_QWEN_JUDGE_BASE_URL=http://127.0.0.1:11434/v1
RAG_QWEN_JUDGE_MODEL=qwen3:4b-instruct
```

Observed integration results:

```text
positive evidence    : qwen_judge supported=True, confidence=0.95
false premise        : qwen_judge supported=True, confidence=0.99
out-of-scope abstain : qwen_judge supported=True, confidence=0.90
rag_regression_bench : SUMMARY 4/4 passed with judge enabled
```

### Design Notes

- Qwen judge is usable as an optional semantic verifier.
- Local keyword verifier remains mandatory.
- `hybrid_strict` remains the safer final-verdict mode.
- Qwen Cloud API is not yet integrated; this milestone only verifies local Qwen through Ollama `/v1`.
- Arithmetic remains unsafe without deterministic tool support.

## v2.1 — General 4B Baseline and Regression Benchmarks

Status: local baseline passed.

### Added

- Added `app/model_smoke_bench.py` for model-level smoke benchmark.
- Added `app/rag_regression_bench.py` for RAG-level regression benchmark.
- Added safe abstention handling in answer quality evaluation.
- Added documentation for Qwen3 4B general mode baseline.
- Added documentation for arithmetic weakness and tool-deterministic requirement.

### Changed

- Updated model strategy: `qwen3:4b-instruct` is the preferred `general` answer generation model for baseline v2.1.
- Kept `qwen-rag-1.5b:latest` as lightweight RAG comparison mode, not the preferred answer generator.
- Updated quality strategy so safe abstention can pass quality even when local keyword verifier marks the answer as unsupported.
- Updated development roadmap: Model General 4B baseline is no longer unfinished; Qwen judge integration is the next phase.

### Verified

Baseline command group:

```bash
python -m compileall app
python -m app.show_model_mode
python -m app.validate_models
python -m app.model_smoke_bench
python -m app.rag_regression_bench
python -m app.quality_report
```

Observed baseline:

```text
Model mode: general
Selected Ollama model: qwen3:4b-instruct
model_smoke_bench: 4/5 passed
rag_regression_bench: 4/4 passed
```

### Known Limitations

- Arithmetic remains unsafe without deterministic tool support.
- Qwen judge is still optional and default OFF.
- Formal `tests/` suite is not yet implemented.
- Parser expansion for DOCX/XLSX/PPTX is not yet implemented.

### Removed / Deprecated

- `README_STAGE_A_C.md` is deprecated. Its content has been absorbed into `SPECIFICATION.md`, `DEVELOPMENT_PLAN.md`, and `UNFINISHED.md`.
