# Changelog

## v2.2 — Deterministic Calculator and Gemini API Foundation

### Added

- Added deterministic `safe_calculator` tool for arithmetic queries.
- Added `math_guard` routing before normal RAG retrieval.
- Added calculator regression cases for multiplication and exponentiation.
- Documented Gemini API usage through the existing OpenAI-compatible provider.
- Documented NVIDIA NIM as a future OpenAI-compatible endpoint candidate.

### Changed

- Arithmetic-like queries are answered by a deterministic tool instead of raw LLM generation.
- Calculator answers use:
  - `verifier_mode=tool_only`
  - `quality_score=1.0`
  - `quality_pass=True`
  - `tool_used=safe_calculator`
- External API experimentation should use:
  - `RAG_OPENAI_COMPAT_BASE_URL`
  - `RAG_OPENAI_COMPAT_MODEL`
  - `RAG_OPENAI_COMPAT_API_KEY`

### Verified

- Local Ollama baseline passes `rag_regression_bench` with `6/6`.
- `17 * 23 = ?` returns `391`.
- `2^8 = ?` returns `256`.
- `2**8 = ?` returns `256`.
- Raw model smoke benchmark remains intentionally stricter and keeps arithmetic as a known raw-LLM weakness.

### Pending

- Gemini API live test after model selection.
- NVIDIA NIM endpoint test after corpus size and model choice are ready.
- Provider benchmark across local Ollama, Gemini API, and NVIDIA NIM.
- Quota-aware provider routing.

## v2.1.1 — Local RAG Benchmark and Hybrid Qwen Judge Baseline

### Added

- Added local model smoke benchmark.
- Added RAG regression benchmark.
- Added safe abstention handling in answer quality evaluation.
- Documented Qwen judge hybrid verification through an OpenAI-compatible local endpoint.

### Verified

- `qwen3:4b-instruct` is available and valid as the `general` local model.
- Positive RAG evidence case passed.
- False-premise correction passed.
- Out-of-scope abstention passed.
- Hybrid Qwen judge integration worked with confidence-bearing audit records.

### Known Limitation

- Raw LLM arithmetic remained unreliable and required deterministic tooling, addressed in v2.2.
