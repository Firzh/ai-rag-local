# AI RAG Local

Local Retrieval-Augmented Generation (RAG) pipeline for document-based answering with local-first components, measurable regression tests, quality evaluation, and optional OpenAI-compatible API experimentation.

## Current Baseline: v2.2

The v2.2 baseline keeps local Ollama as the default stable path and adds deterministic arithmetic handling through `safe_calculator`.

Confirmed in v2.2:

- `qwen3:4b-instruct` remains the local `general` answer model.
- Arithmetic-like queries are routed to `safe_calculator` before RAG retrieval or LLM generation.
- Local RAG regression now includes six cases and passes `6/6`.
- Gemini API experimentation should use the existing `openai_compatible` provider.
- NVIDIA NIM is kept as a future OpenAI-compatible endpoint candidate after corpus and model selection are mature.

## Core Pipeline

```text
file input
→ routing
→ parsing
→ chunking
→ embedding
→ Chroma vector storage
→ hybrid retrieval
→ context compression
→ answer generation
→ verification
→ quality evaluation
→ persistence
```

## Default Local Configuration

```env
RAG_LLM_PROVIDER=ollama
RAG_MODEL_MODE=general

RAG_OLLAMA_MODEL_RAG=qwen-rag-1.5b:latest
RAG_OLLAMA_MODEL_CODER=qwen-coder-1.5b:latest
RAG_OLLAMA_MODEL_GENERAL=qwen3:4b-instruct
RAG_OLLAMA_MODEL=

RAG_QWEN_JUDGE_ENABLED=false
RAG_VERIFICATION_AUDIT_ENABLED=false
```

Validate:

```bash
python -m app.show_model_mode
python -m app.validate_models
```

## Deterministic Calculator Tool

Raw LLM arithmetic is not trusted for final answers. v2.2 routes arithmetic-like queries through `safe_calculator`.

Examples:

```bash
python -m app.answer_query "17 * 23 = ?"
python -m app.answer_query "2^8 = ?"
python -m app.answer_query "2**8 = ?"
```

Expected:

```text
Hasil 17*23 = 391.
Hasil 2**8 = 256.
```

Calculator answers use:

```text
verifier_mode = tool_only
quality_score = 1.0
quality_pass = True
tool_used = safe_calculator
```

## Gemini API Foundation

Gemini API should be tested through the existing OpenAI-compatible provider.

```bash
export RAG_LLM_PROVIDER=openai_compatible
export RAG_OPENAI_COMPAT_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
export RAG_OPENAI_COMPAT_MODEL="YOUR_GEMINI_MODEL"
export RAG_OPENAI_COMPAT_API_KEY="YOUR_GEMINI_API_KEY"
```

Then test:

```bash
python -m app.answer_query "Apa fungsi Magika dan Chroma dalam pipeline RAG lokal ini?"
python -m app.answer_query "17 * 23 = ?"
```

Expected behavior:

- document-based RAG uses the configured API provider;
- arithmetic still uses `safe_calculator`;
- API keys are never printed.

## NVIDIA NIM Future Path

NVIDIA NIM should also be treated as an OpenAI-compatible candidate endpoint, not as a separate custom client until evidence shows it needs special handling.

Future test configuration:

```bash
export RAG_LLM_PROVIDER=openai_compatible
export RAG_OPENAI_COMPAT_BASE_URL=https://integrate.api.nvidia.com/v1
export RAG_OPENAI_COMPAT_MODEL="YOUR_NVIDIA_NIM_MODEL"
export RAG_OPENAI_COMPAT_API_KEY="YOUR_NVIDIA_API_KEY"
```

## Regression Tests

```bash
export RAG_MODEL_MODE=general
export RAG_LLM_PROVIDER=ollama
export RAG_QWEN_JUDGE_ENABLED=false
export RAG_VERIFICATION_AUDIT_ENABLED=false

python -m compileall app
python -m app.rag_regression_bench
```

Expected:

```text
SUMMARY: 6/6 passed
```

Raw model smoke benchmark remains intentionally stricter:

```bash
python -m app.model_smoke_bench
```

Expected local result remains `4/5 passed` because raw model arithmetic is intentionally kept as a known weakness.
