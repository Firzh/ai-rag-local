# DEVELOPMENT_PLAN.md — AI RAG Local

> Updated roadmap after v2.2.  
> Current direction: keep local RAG stable, treat Gemini API as a limited daily resource, and shift v2.3 toward a mini data acquisition agent for expanding local knowledge.

---

## 0. Current Baseline

### v2.1.1 — Local RAG Benchmark + Hybrid Qwen Judge Baseline

Status: **Done**

Core outcomes:

- `qwen3:4b-instruct` validated as the active `general` local model.
- RAG positive query passed.
- False-premise correction passed.
- Out-of-scope abstention passed.
- Safe abstention is treated as a valid quality outcome.
- Hybrid Qwen judge was tested through Ollama OpenAI-compatible `/v1`.
- `rag_regression_bench` passed the local baseline.
- `model_smoke_bench` intentionally keeps raw arithmetic failure visible to prove that small LLM arithmetic must not be trusted without a deterministic tool.

Key lesson:

> Local RAG is reliable when evidence exists, but it must explicitly refuse or abstain when local documents do not support the answer.

---

### v2.2 — Deterministic Calculator and Gemini API Foundation

Status: **Done / Committed**

Core outcomes:

- Added deterministic arithmetic tool: `safe_calculator`.
- Added `math_guard` before the normal RAG retrieval path.
- Arithmetic-like queries are routed to tool-only execution.
- `17 * 23 = ?` returns `391`.
- `2^8 = ?` and `2**8 = ?` return `256`.
- Calculator output uses:
  - `verifier_mode=tool_only`
  - `quality_score=1.0`
  - `quality_pass=True`
- `rag_regression_bench` passed `6/6`.
- Gemini API was validated through the existing `openai_compatible` provider path.
- `.env` holds the active Gemini configuration but must never be committed.

Important note:

> Gemini is useful as an external generation provider, but its free-tier limit must be treated as a scarce daily resource.

Observed Gemini limit context:

- RPM: approximately `5`
- TPM: approximately `250K`
- RPD: approximately `20`

This makes request-count conservation more important than token optimization at the current stage.

---

## 1. Roadmap Summary

| Version | Focus                                                                | Status               |
| ------- | -------------------------------------------------------------------- | -------------------- |
| v2.1.1  | Local benchmark baseline + hybrid Qwen judge                         | Done                 |
| v2.2    | Deterministic calculator + Gemini API foundation                     | Done                 |
| v2.2.1  | Robust API error handling + fallback policy                          | Next                 |
| v2.2.2  | Quota-aware execution, usage tracker, daily warning, cache           | Planned              |
| v2.3    | Mini web data acquisition agent for local knowledge expansion        | Redirected / Planned |
| v2.4    | Provider benchmark and NVIDIA NIM exploration                        | Deferred             |
| v2.5    | Corpus growth, data quality scoring, and semi-automated ingestion QA | Future               |

---

## 2. v2.2.1 — Robust Provider Handling

### Goal

Make API-backed generation safe, readable, and non-crashing when the external provider fails.

Gemini must be treated as a limited, failure-prone external provider. The system must still be useful when Gemini returns API errors, rate-limit errors, or daily quota exhaustion.

### Problems to Solve

Current limitations:

1. API errors can still surface as raw exceptions.
2. HTTP error categories are not normalized.
3. The system has no clear fallback policy when Gemini fails.
4. Gemini RPD exhaustion is not yet handled gracefully.
5. Users do not receive a clear message such as:

```text
Kuota Gemini harian habis, jawaban hanya berdasarkan retrieval lokal.
```

### Required Behavior

#### 2.2.1-A — Provider Error Classification

Classify external API failures into stable internal categories:

| HTTP Status | Internal Error Type                 | Meaning                                          |
| ----------: | ----------------------------------- | ------------------------------------------------ |
|         400 | `bad_request`                       | Bad payload, wrong model name, malformed request |
|         401 | `auth_error`                        | Invalid API key                                  |
|         403 | `auth_error` or `permission_denied` | Key valid but not allowed                        |
|         404 | `model_not_found`                   | Model unavailable for endpoint/key               |
|         408 | `timeout`                           | Request timed out                                |
|         429 | `rate_limited`                      | RPM, TPM, or RPD exceeded                        |
|         500 | `provider_unavailable`              | Provider internal issue                          |
|         502 | `provider_unavailable`              | Gateway issue                                    |
|         503 | `provider_unavailable`              | Temporarily unavailable                          |
|         504 | `provider_unavailable`              | Gateway timeout                                  |

The CLI must not show only a raw traceback for expected provider failures.

Expected user-facing message:

```text
Provider error: rate_limited
Provider: openai_compatible
Model: gemini-3-flash-preview
Action: fallback ke model lokal atau local-only retrieval.
```

---

#### 2.2.1-B — Fallback Policy

Default fallback order:

1. **Arithmetic query**
   - Route to `safe_calculator`.
   - Do not call Gemini or any LLM.

2. **RAG query + API provider healthy**
   - Use configured API provider, currently Gemini via `openai_compatible`.

3. **RAG query + API provider fails**
   - If enabled, fallback to local Ollama.
   - If local model is unavailable, fallback to local-only answer from retrieval evidence.
   - Never crash on expected provider failures.

4. **No evidence**
   - Return safe abstention:
     ```text
     Dokumen lokal belum cukup mendukung jawaban.
     ```

5. **RPD exhausted**
   - Return:
     ```text
     Kuota Gemini harian habis, jawaban hanya berdasarkan retrieval lokal.
     ```

---

#### 2.2.1-C — Local-Only Retrieval Answer

When API generation is unavailable, local-only mode should still produce a minimal grounded answer from the evidence pack.

Minimum acceptable behavior:

- Use evidence facts/quotes assembled by `ContextCompressor`.
- If evidence is sufficient, produce a short extractive answer.
- If evidence is weak, produce a safe abstention.
- Mark metadata:
  - `llm_provider=local_only`
  - `llm_model=extractive_fallback`
  - `fallback_reason=<error_type>`

Example:

```text
Gemini tidak tersedia saat ini. Jawaban berikut hanya berdasarkan retrieval lokal:
Magika berfungsi sebagai file router, sedangkan Chroma berfungsi sebagai vector database.
```

---

### Proposed Files

See `V2_2_1_IMPLEMENTATION_PLAN.md` for detailed per-file implementation.

Expected changes:

```text
app/llm/provider_errors.py        # new
app/llm/fallback_policy.py        # new
app/answer_query.py               # modify
app/llm/clients.py                # modify
app/config.py                     # modify
app/rag_regression_bench.py       # modify
README.md                         # update after test
CHANGELOG.md                      # update after test
UNFINISHED.md                     # update after test
```

---

### Proposed Environment Variables

```env
# Provider fallback
RAG_ENABLE_LLM_FALLBACK=true
RAG_FALLBACK_PROVIDER=ollama
RAG_ENABLE_LOCAL_ONLY_ON_RATE_LIMIT=true
RAG_PROVIDER_ERROR_VERBOSE=true

# External provider timeout
RAG_LLM_TIMEOUT_SECONDS=120

# Rate-limit messaging
RAG_RATE_LIMIT_MESSAGE_ENABLED=true
```

---

### Acceptance Criteria

v2.2.1 is considered complete when:

1. Gemini 400/401/403/404/429 errors no longer crash the app with raw traceback.
2. A 429 error produces a human-readable rate-limit message.
3. On provider failure, the system can fallback to:
   - local Ollama, or
   - local-only retrieval answer.
4. Calculator queries remain tool-only and never call Gemini.
5. `answer_query` records fallback metadata in the answer JSON.
6. `rag_regression_bench` still passes.
7. A simulated provider failure test is available.

---

## 3. v2.2.2 — Quota-Aware Execution

### Goal

Treat Gemini API as a scarce daily resource.

The system must track API usage locally, warn before limit exhaustion, cache repeated questions, and avoid unnecessary API calls.

### Why This Matters

The current Gemini 3 Flash free-tier style usage has low RPD. From the observed dashboard:

```text
RPM: 3 / 5 peak observed
TPM: 2.28K / 250K peak observed
RPD: 6 / 20 peak observed
```

The primary risk is **daily request exhaustion**, not token exhaustion.

---

### Required Features

#### A. Local Daily Request Counter

Create local usage tracking.

Minimum recorded fields:

```text
created_at
provider
model
request_type
query_hash
success
status_code
error_type
input_tokens
output_tokens
total_tokens
latency_ms
fallback_used
cache_hit
```

Recommended storage:

```text
data/quality/api_usage.sqlite3
```

---

#### B. Cache Repeated Questions

Add query answer cache to reduce RPD usage.

Minimum cache behavior:

- Normalize query.
- Hash query + provider + evidence fingerprint.
- Return cached answer when valid.
- TTL default: 24 hours.
- Do not cache failed provider errors as valid answers.
- Do not call Gemini when exact valid cache exists.

Suggested config:

```env
RAG_API_CACHE_ENABLED=true
RAG_API_CACHE_TTL_HOURS=24
```

---

#### C. Daily Warning Threshold

Given Gemini RPD around 20, use conservative thresholds:

```env
RAG_GEMINI_RPD_LIMIT=20
RAG_API_DAILY_REQUEST_WARN=15
RAG_API_DAILY_REQUEST_HARD_WARN=18
RAG_API_DISABLE_ON_RPD_EXCEEDED=true
```

Expected warning:

```text
Warning: penggunaan Gemini hari ini 15/20 request.
Disarankan gunakan cache atau model lokal untuk query non-kritis.
```

Expected hard-limit message:

```text
Kuota Gemini harian habis, jawaban hanya berdasarkan retrieval lokal.
```

---

#### D. Usage Report CLI

Add:

```bash
python -m app.api_usage_report
```

Expected output:

```text
API usage today
---------------
Provider         : openai_compatible
Model            : gemini-3-flash-preview
Requests         : 6/20
Errors           : 1
Cache hits       : 2
Fallbacks        : 1
Estimated tokens : 2.28K / 250K
Status           : safe
```

---

### Proposed Files

```text
app/usage/__init__.py             # new
app/usage/api_usage_store.py      # new
app/api_usage_report.py           # new
app/cache/__init__.py             # new
app/cache/query_cache.py          # new
app/answer_query.py               # modify
app/llm/clients.py                # modify
app/config.py                     # modify
```

---

### Acceptance Criteria

v2.2.2 is complete when:

1. Each external API call is logged locally.
2. Usage report shows current-day provider usage.
3. Repeated exact query can be answered from cache.
4. When usage reaches warning threshold, CLI prints a warning.
5. When usage reaches hard threshold, Gemini is skipped.
6. Calculator queries do not count as Gemini API usage.
7. Fallback events are counted.

---

## 4. v2.3 — Mini Data Acquisition Agent

### Redirected Goal

v2.3 is redirected away from provider benchmarking.

New objective:

> Build a small agent that collects relevant internet data, saves it locally, and ingests it into the RAG knowledge base.

### Why

The system is increasingly accurate when evidence exists. The main limitation is not answer generation but **local data coverage**.

If the Chroma collection lacks the information, the system correctly abstains. Therefore, the next major value is to help it gather relevant data.

---

### Proposed Flow

Future command:

```bash
python -m app.web_ingest_agent "topik atau kebutuhan data"
```

Expected flow:

1. Search web for candidate sources.
2. Filter sources by domain/relevance.
3. Fetch selected pages.
4. Extract readable text.
5. Save as local documents.
6. Run ingest.
7. Report number of documents and chunks added.

Expected output:

```text
Found 8 candidate pages
Accepted 3 sources
Saved 3 documents to data/inbox/web/
Ingested 41 chunks into Chroma
```

---

### Proposed Files

```text
app/web_agent/__init__.py
app/web_agent/search_client.py
app/web_agent/fetcher.py
app/web_agent/cleaner.py
app/web_agent/source_policy.py
app/web_ingest_agent.py
```

---

### Key Design Rules

1. Do not blindly ingest everything from the internet.
2. Store source URL and fetch timestamp.
3. Prefer official documentation and stable sources.
4. Avoid low-quality or duplicate sources.
5. Add a source policy for allowed/blocked domains.
6. Every internet-ingested document must be traceable.

---

## 5. Deferred Work

### NVIDIA NIM

Status: **Deferred**

NVIDIA NIM remains a candidate endpoint or future fine-tuning/inference option. It should not be the immediate focus until:

- local corpus is larger,
- Chroma contains enough useful data,
- provider fallback and usage tracking are stable.

### Provider Benchmark

Status: **Deferred**

Provider benchmark across Ollama, Gemini, Qwen API, OpenAI API, and NVIDIA NIM is postponed until v2.3 mini data agent improves the corpus.

---

## 6. Current Priority

Immediate next work:

```text
v2.2.1 — Robust API error handling and fallback
```

Then:

```text
v2.2.2 — Quota-aware execution and cache
```

Then:

```text
v2.3 — Mini data acquisition agent
```
