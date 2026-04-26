# ai-rag-local / rag-lc

Status update: **v2.2.3 Local RAG Quality Foundation sampai L3**  
Tanggal update: 2026-04-26

Repository ini diarahkan sebagai RAG lokal utama. Prinsip pengembangan saat ini adalah memperkuat kualitas data lokal sebelum integrasi yang lebih dalam dengan pipeline Kaggle dan mini data acquisition agent.

## Status ringkas

| Area | Status |
|---|---|
| Calculator deterministic | Selesai pada v2.2 |
| Gemini via OpenAI-compatible provider | Selesai sebagai fondasi API eksternal |
| API error handling + Ollama fallback | Selesai pada v2.2.1 |
| API usage tracker + query cache | Selesai pada v2.2.2 |
| Reorganisasi struktur `app/` | Selesai |
| L1 Chunking V2 foundation | Selesai |
| L2a HTML parser foundation | Selesai |
| L2b HTML staging pipeline | Selesai |
| L3 Quality gate untuk staged web data | Selesai |
| L4 Export JSONL / Chroma export untuk Kaggle | Belum mulai |
| L5 Chroma compare lama vs sandbox | Belum mulai |
| L6 Collection promote | Ditahan sampai benchmark lama-vs-baru aman |

## Prinsip arsitektur saat ini

`rag-lc` tetap menjadi sistem utama untuk ingestion lokal, retrieval, verification, dan answer generation. Kaggle diposisikan sebagai lab eksperimen untuk audit data, parameter chunking, embedding batch, retrieval evaluation, dan eksperimen ringan sebelum hasilnya diimpor ulang ke environment lokal.

Pipeline data web tidak boleh langsung masuk ke Chroma utama. Jalur aman yang dipakai:

```text
raw_html
→ html_parser
→ parsed_text + metadata
→ quality_gate
→ approved / quarantine
→ export / sandbox
→ benchmark
→ promote jika aman
```

## Perintah penting

Regression lokal:

```bash
export RAG_LLM_PROVIDER=ollama
export RAG_MODEL_MODE=general
export RAG_QWEN_JUDGE_ENABLED=false
export RAG_VERIFICATION_AUDIT_ENABLED=false

python -m app.rag_regression_bench
```

Smoke tests:

```bash
python -m app.benchmarks.chunking_v2_smoke
python -m app.benchmarks.html_parser_smoke
python -m app.benchmarks.web_staging_smoke
python -m app.benchmarks.quality_gate_smoke
```

Cleanup generated outputs:

```bash
python -m app.maintenance.cleanup_generated_outputs --yes
```

## Catatan

Jika ingin melanjutkan ke Kaggle, jangan kirim Chroma utama secara langsung. Gunakan export JSONL dan import balik ke collection sandbox lokal terlebih dahulu.
