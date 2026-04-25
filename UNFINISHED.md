# Unfinished Work

## Current State

v2.2 calculator functionality is ready and should be committed together with the updated documentation.

Completed but not yet committed in final v2.2:

- deterministic `safe_calculator`;
- `math_guard` routing before RAG;
- calculator regression cases;
- local regression result: `6/6 passed`.

## Pending

### 1. Gemini API Live Test

Pending because the model and API key are not finalized.

Planned test:

```bash
export RAG_LLM_PROVIDER=openai_compatible
export RAG_OPENAI_COMPAT_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
export RAG_OPENAI_COMPAT_MODEL="YOUR_GEMINI_MODEL"
export RAG_OPENAI_COMPAT_API_KEY="YOUR_GEMINI_API_KEY"

python -m app.answer_query "Apa fungsi Magika dan Chroma dalam pipeline RAG lokal ini?"
python -m app.answer_query "17 * 23 = ?"
```

Expected:

- RAG answer uses Gemini-compatible endpoint.
- Arithmetic answer uses `safe_calculator`.
- API key is not logged.

### 2. NVIDIA NIM Evaluation

NIM is not part of the v2.2 live baseline.

Future work:

- select NIM model;
- increase Chroma corpus;
- create domain-specific benchmark;
- test through OpenAI-compatible provider;
- compare quota, latency, and quality against local Ollama and Gemini API.

### 3. Provider Benchmark

Needed after Gemini/NIM model choices are known.

Metrics:

```text
latency
quality_score
support_ratio
artifact_like
abstention_like
provider error rate
quota/cost profile
```

### 4. Provider Routing Policy

Future routing policy:

```text
arithmetic              -> safe_calculator
small grounded RAG       -> local Ollama
higher quality synthesis -> Gemini API or selected endpoint
large/experimental       -> NIM or selected provider
fallback                 -> local Ollama
```

### 5. Advanced Calculator

Future calculator expansion may include:

- percentages;
- unit conversion;
- word problems;
- financial formulas;
- chained calculations.

## Not Pending

The following are not blockers:

- local qwen3 4B availability;
- positive RAG evidence;
- false-premise correction;
- out-of-scope abstention;
- quality pass for safe abstention;
- deterministic multiplication;
- deterministic exponentiation.
