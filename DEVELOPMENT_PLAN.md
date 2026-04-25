# Development Plan

## Development Principle

Every feature must be measurable. A change is considered stable only when it has a repeatable command and a clear pass/fail result.

## Completed Milestones

### v2.1.1 — Local RAG Benchmark and Hybrid Qwen Judge Baseline

Completed:

- `qwen3:4b-instruct` validated as the local `general` model.
- Positive evidence query passed.
- False-premise correction passed.
- Out-of-scope abstention passed.
- Quality evaluator supports safe abstention.
- Hybrid Qwen judge integration tested through local Ollama OpenAI-compatible `/v1`.
- Verifier audit records local and semantic verifier runs.

### v2.2 — Deterministic Calculator and Gemini API Foundation

Final v2.2 scope:

1. Add deterministic calculator tool.
2. Route arithmetic-like queries before normal RAG retrieval.
3. Extend RAG regression with arithmetic cases.
4. Keep external API experimentation generic through `openai_compatible`.
5. Document Gemini API as the next API candidate.
6. Keep NVIDIA NIM as future endpoint/fine-tuning candidate.

Implemented files:

```text
app/tools/__init__.py
app/tools/calculator.py
app/math_guard.py
app/answer_query.py
app/rag_regression_bench.py
```

Verified:

```text
17 * 23 = ?  -> 391
2^8 = ?      -> 256
2**8 = ?     -> 256
rag_regression_bench -> 6/6 passed
```

## Next Steps

### 1. Commit v2.2

```bash
git commit -m "Add v2.2 calculator tool and Gemini API foundation"
```

### 2. Gemini API Live Test

After selecting model and setting key:

```bash
export RAG_LLM_PROVIDER=openai_compatible
export RAG_OPENAI_COMPAT_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
export RAG_OPENAI_COMPAT_MODEL="YOUR_GEMINI_MODEL"
export RAG_OPENAI_COMPAT_API_KEY="YOUR_GEMINI_API_KEY"

python -m app.answer_query "Apa fungsi Magika dan Chroma dalam pipeline RAG lokal ini?"
python -m app.answer_query "17 * 23 = ?"
```

Success criteria:

- RAG answer uses Gemini through OpenAI-compatible provider.
- Arithmetic answer still uses `safe_calculator`.
- No API key is printed.

### 3. Provider Benchmark

After Gemini model selection, compare:

```text
local Ollama
Gemini API
NVIDIA NIM when ready
Qwen API if needed
```

Metrics:

```text
latency
quality_score
support_ratio
artifact_like
abstention_like
error rate
quota/cost suitability
```

## Future Milestones

### v2.3 — Provider Selection and Fallback Policy

Candidate features:

- provider benchmark script;
- quota-aware routing;
- local fallback;
- provider metadata in answer records.

### v2.4 — Retrieval and Corpus Growth

Candidate features:

- larger Chroma corpus;
- more domain-specific test cases;
- improved reranking;
- stronger out-of-scope detection.

### v2.5 — NVIDIA NIM Evaluation

NIM should be evaluated after the Chroma corpus has enough representative data and the target model is chosen.

## Rules

1. Never trust raw LLM arithmetic for final answers.
2. Keep local baseline green before testing cloud APIs.
3. Never commit API keys.
4. Do not commit generated answer/evidence/benchmark JSON unless intentionally archiving an experiment.
5. Every provider must pass the same regression tests.
