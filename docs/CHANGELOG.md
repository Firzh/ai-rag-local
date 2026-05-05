# CHANGELOG.md

## L4 + Post-L4 pipeline contract hardening

Tanggal update: 2026-05-06

### Added

- Added L1 JSONL export foundation for approved staged documents.
- Added Chroma collection JSONL export foundation for audit and compare preparation.
- Added `app/benchmarks/chroma_jsonl_export_smoke.py`.
- Added `app/commands/export_chroma_collection.py`.
- Added `app/exporters/chroma_jsonl_export.py`.
- Added `tests/conftest.py` for stable local test imports.
- Added `tests/test_pipeline_contract.py` for contract-level pipeline verification.

### Changed

- JSONL importer now accepts `doc_id` as an alias for `document_id`.
- JSONL importer preserves unique chunk IDs by resolving `doc_id:chunk_index` when `document_id` is missing.
- Quality gate now creates `approved` and `quarantine` output directories even when all documents are quarantined.
- Documentation now reflects L4 export status and post-L4 contract test coverage.

### Verified

- `python -m pytest -q tests/test_pipeline_contract.py` passed with `4 passed`.
- Contract test verifies raw HTML to staging, quality gate, L1 JSONL export, and importer compatibility.
- Contract test verifies quarantine output does not enter JSONL export.
- Contract test verifies `doc_id` based export can be accepted by the importer.

### Notes

- L4 JSONL export is a bridge and audit layer, not a direct promote mechanism.
- Chroma main collection must not be overwritten from JSONL without L5 compare and L6 promote guard.
- Next recommended work is L4a.1 chunking boundary refinement, then L5 Chroma old-vs-sandbox compare.

---

## v2.2.3 - Local RAG Quality Foundation sampai L3

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

- L1 does not yet write JSONL directly in this stage.
- L2 does not yet ingest HTML into Chroma.
- L3 does not yet promote data into Chroma.
- L4 should create JSONL export for `rag-to-kaggle`.
