# CHANGELOG.md

## v2.2.3 — Local RAG Quality Foundation sampai L3

Tanggal update: 2026-04-26

### Added

- Added `app/rag/chunking_v2.py`.
- Added `app/benchmarks/chunking_v2_smoke.py`.
- Added `app/parsers/html_parser.py`.
- Added `app/benchmarks/html_parser_smoke.py`.
- Added `app/staging/web_staging.py`.
- Added `app/commands/parse_web_staging.py`.
- Added `app/benchmarks/web_staging_smoke.py`.
- Added `app/quality/quality_gate.py`.
- Added `app/commands/run_quality_gate.py`.
- Added `app/benchmarks/quality_gate_smoke.py`.

### Changed

- Web data processing now follows staging-first direction:
  ```text
  raw_html → parsed_text + metadata → quality_gate → approved/quarantine
  ```
- Generated output cleanup now covers answer/evidence/benchmark/staging/audit outputs.
- Development direction now prioritizes local RAG data quality before scraper agent and Kaggle import/export automation.

### Verified

- `chunking_v2_smoke` passed.
- `html_parser_smoke` passed.
- `web_staging_smoke` passed.
- `quality_gate_smoke` passed.
- `rag_regression_bench` remains `6/6 passed` under local Ollama baseline.

### Notes

- L1 does not yet write JSONL directly.
- L2 does not yet ingest HTML into Chroma.
- L3 does not yet promote data into Chroma.
- L4 should create JSONL export for `rag-to-kaggle`.
