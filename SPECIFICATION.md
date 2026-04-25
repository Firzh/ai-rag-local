# Specification

## Purpose

This project implements a local-first RAG system with measurable answer quality, optional semantic verification, and deterministic tool routing for tasks that should not be delegated to a language model.

## Execution Modes

### Local Ollama

```env
RAG_LLM_PROVIDER=ollama
RAG_MODEL_MODE=general
RAG_OLLAMA_MODEL_GENERAL=qwen3:4b-instruct
```

### OpenAI-Compatible Provider

Generic provider mode for Gemini API, NVIDIA NIM, LM Studio, llama.cpp server, or other compatible endpoints.

```env
RAG_LLM_PROVIDER=openai_compatible
RAG_OPENAI_COMPAT_BASE_URL=<base-url>
RAG_OPENAI_COMPAT_MODEL=<model>
RAG_OPENAI_COMPAT_API_KEY=<api-key>
```

## Gemini API

Gemini should use the existing `openai_compatible` provider.

```env
RAG_OPENAI_COMPAT_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
```

No Gemini-specific client is required in v2.2.

## NVIDIA NIM

NVIDIA NIM is future work and should initially use the same OpenAI-compatible provider.

```env
RAG_OPENAI_COMPAT_BASE_URL=https://integrate.api.nvidia.com/v1
```

## Deterministic Calculator Tool

### Files

```text
app/tools/__init__.py
app/tools/calculator.py
app/math_guard.py
```

### Supported Initial Operations

```text
+
-
*
/
 //
%
**
parentheses
unary + and -
```

### Example Inputs

```text
17 * 23 = ?
2^8 = ?
2**8 = ?
berapa hasil 10 - 3?
```

### Example Outputs

```text
Hasil 17*23 = 391.
Hasil 2**8 = 256.
Hasil 10-3 = 7.
```

### Safety

The calculator uses restricted AST parsing and must not use unrestricted `eval`.

## Answer Query Flow

```text
read query
→ calculator guard
→ if arithmetic: safe_calculator answer
→ else: RAG retrieval and compression
→ prompt building
→ LLM generation
→ postprocess
→ verification
→ quality evaluation
→ persistence
```

Calculator routing must happen before `ContextCompressor()` to avoid unnecessary retrieval/API calls.

## Calculator Quality Semantics

Calculator answer verification:

```python
{
    "supported": True,
    "support_ratio": 1.0,
    "verifier_mode": "tool_only",
    "tool": {
        "name": "safe_calculator",
        "expression": "...",
        "result": "..."
    }
}
```

Calculator quality:

```python
{
    "artifact_like": False,
    "abstention_like": False,
    "issue_tags": [],
    "quality_score": 1.0,
    "quality_pass": True,
    "tool_used": "safe_calculator"
}
```

## Verification

### Local Verifier

Lexical evidence support checker.

### Qwen Judge

Optional semantic verifier.

```env
RAG_QWEN_JUDGE_ENABLED=true
RAG_VERIFICATION_AUDIT_ENABLED=true
RAG_QWEN_JUDGE_BASE_URL=http://127.0.0.1:11434/v1
RAG_QWEN_JUDGE_MODEL=qwen3:4b-instruct
RAG_QWEN_JUDGE_API_KEY=ollama
```

### Safe Abstention

An out-of-scope answer may pass quality if:

```text
artifact_like=False
abstention_like=True
issue_tags=[]
```

## Regression Benchmark

File:

```text
app/rag_regression_bench.py
```

Required cases:

```text
positive_magika_chroma
false_premise_chroma_parser
positive_pipeline_order
out_of_scope_guard
calculator_arithmetic_tool
calculator_power_tool
```

Required result:

```text
SUMMARY: 6/6 passed
```

## Files Not to Commit

```text
.env
data/answers/*.answer.json
data/answers/*.answer.md
data/evidence/*.evidence.json
data/quality/model_smoke_bench-*.json
data/quality/rag_regression_bench-*.json
API keys
```
