# Spesifikasi Lengkap AI RAG Local

Dokumen ini menjelaskan spesifikasi teknis proyek **AI RAG Local**, termasuk tujuan sistem, arsitektur, modul, dependensi, data flow, konfigurasi, command-line interface, dan batasan implementasi.

---

## 1. Ringkasan Sistem

AI RAG Local adalah sistem Retrieval-Augmented Generation berbasis dokumen lokal. Sistem memproses dokumen dari folder lokal, membuat representasi chunk dan embedding, melakukan retrieval hybrid, menyusun evidence pack, mengirim konteks ke model lokal, memverifikasi jawaban, lalu menyimpan hasil dan kualitas jawaban.

Desain utama:

```text
Local-first
Lightweight
Modular
Evidence-grounded
Quality-aware
```

---

## 2. Target Perangkat

Spesifikasi awal yang menjadi target pengembangan:

| Komponen | Target |
|---|---|
| CPU | Intel i3 12th Gen atau setara |
| GPU | GTX 1650 4 GB, opsional |
| RAM | 32 GB direkomendasikan |
| OS | Windows 10/11 |
| Python | 3.12 direkomendasikan |
| Java | 11+ untuk parser PDF |
| Runtime LLM | Ollama |

Model kecil tetap digunakan dengan bantuan Context Compression, Verifier, dan Quality Layer.

---

## 3. Dependensi Utama

Dependensi utama:

| Package | Fungsi |
|---|---|
| `chromadb` | Vector database lokal |
| `fastembed` | Embedding lokal berbasis ONNX |
| `magika` | Deteksi tipe file |
| `opendataloader-pdf` | Parsing PDF |
| `python-dotenv` | Membaca `.env` |
| `requests` | HTTP client untuk Ollama/OpenAI-compatible server |
| `rich` | Output terminal |
| `tqdm` | Progress bar |

Dependensi tidak wajib pada tahap awal:

- `torch`
- `transformers`
- `sentence-transformers`
- `langchain`
- `paddleocr`
- `docling`
- `mineru`
- `neo4j`

---

## 4. Konfigurasi `.env`

### 4.1 Direktori

```env
RAG_PROJECT_DIR=F:\AI-Models\ai-rag-local
RAG_INBOX_DIR=F:\AI-Models\ai-rag-local\data\inbox
RAG_PARSED_DIR=F:\AI-Models\ai-rag-local\data\parsed
RAG_CHROMA_DIR=F:\AI-Models\ai-rag-local\data\chroma
RAG_CACHE_DIR=F:\AI-Models\ai-rag-local\data\cache
RAG_LOG_DIR=F:\AI-Models\ai-rag-local\data\logs
RAG_GRAPH_DIR=F:\AI-Models\ai-rag-local\data\graph
RAG_INDEXES_DIR=F:\AI-Models\ai-rag-local\data\indexes
RAG_SUMMARIES_DIR=F:\AI-Models\ai-rag-local\data\summaries
RAG_MEMORY_DIR=F:\AI-Models\ai-rag-local\data\memory
RAG_EVIDENCE_DIR=F:\AI-Models\ai-rag-local\data\evidence
RAG_ANSWERS_DIR=F:\AI-Models\ai-rag-local\data\answers
RAG_QUALITY_DIR=F:\AI-Models\ai-rag-local\data\quality
RAG_QUALITY_DB=F:\AI-Models\ai-rag-local\data\quality\answer_quality.sqlite3
```

### 4.2 Model

```env
RAG_LLM_PROVIDER=ollama
RAG_OLLAMA_BASE_URL=http://127.0.0.1:11434
RAG_MODEL_MODE=rag
RAG_OLLAMA_MODEL_RAG=qwen-rag-1.5b:latest
RAG_OLLAMA_MODEL_CODER=qwen-coder-1.5b:latest
RAG_OLLAMA_MODEL_GENERAL=qwen-general:4b:latest
RAG_LLM_TEMPERATURE=0.1
RAG_LLM_MAX_TOKENS=350
RAG_OLLAMA_KEEP_ALIVE=0
RAG_ANSWER_MAX_CHARS=1200
RAG_USE_EXTRACTIVE_FALLBACK=true
```

### 4.3 Retrieval dan compression

```env
RAG_COLLECTION=rag_multilingual_minilm_l12_v2_384
RAG_EMBED_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
RAG_BATCH_SIZE=32
RAG_CHUNK_SIZE=900
RAG_CHUNK_OVERLAP=120
RAG_TOP_K=6
RAG_VECTOR_TOP_K=6
RAG_FTS_TOP_K=8
RAG_RERANK_TOP_K=5
RAG_MAX_CONTEXT_CHARS=6000
RAG_COMPRESS_MAX_FACTS=8
RAG_COMPRESS_MAX_QUOTES=5
RAG_COMPRESS_MAX_QUOTE_CHARS=450
RAG_DISTANCE_CUTOFF=0.82
RAG_SCORE_CUTOFF=0.30
```

### 4.4 Graph dan quality

```env
RAG_ENABLE_GRAPH=true
RAG_GRAPH_HOPS=1
RAG_GRAPH_MAX_TERMS=12
RAG_GRAPH_MAX_RESULTS=10
RAG_ENABLE_QUALITY_STORE=true
RAG_USE_QUALITY_EXAMPLES=false
```

---

## 5. Data Flow Detail

### 5.1 Ingestion

```text
data/inbox/*
→ app.router.FileRouter
→ parser berdasarkan route
→ parsed text disimpan ke data/parsed
→ chunking
→ embedding
→ Chroma upsert
→ SQLite FTS upsert
→ manifest update
```

### 5.2 Retrieval

```text
User query
→ embedding query
→ Chroma vector search
→ SQLite FTS5 keyword search
→ Mini Graph neighbor expansion
→ Candidate merge
→ Heuristic reranker
→ Top chunks
```

### 5.3 Compression

```text
Retrieved chunks
→ important facts
→ important quotes
→ sources
→ uncertainty
→ evidence pack
```

### 5.4 Answer generation

```text
Evidence pack
→ prompt builder
→ Ollama chat API
→ raw answer
→ postprocess
→ verifier
→ fallback/refiner jika perlu
→ quality evaluator
→ save answer
```

---

## 6. Modul Utama

### 6.1 `app/config.py`

Membaca environment variable dan membuat direktori kerja. Memilih model aktif berdasarkan `RAG_MODEL_MODE`.

### 6.2 `app/router.py`

Menggunakan Magika untuk deteksi tipe file dan routing ke parser.

### 6.3 `app/parsers/`

- `pdf_parser.py`: OpenDataLoader PDF.
- `text_parser.py`: file teks biasa.

### 6.4 `app/chunking.py`

Melakukan pembersihan teks dan chunking berbasis ukuran karakter dengan overlap.

### 6.5 `app/embeddings/fastembedder.py`

Wrapper FastEmbed untuk embedding dokumen dan query.

### 6.6 `app/db/chroma_store.py`

Wrapper Chroma PersistentClient.

### 6.7 `app/db/fts_store.py`

SQLite FTS5 untuk pencarian keyword dan BM25.

### 6.8 `app/graph/mini_graph.py`

Mini graph berbasis JSONL untuk relasi:

- document;
- chunk;
- parser;
- filetype;
- page;
- term.

### 6.9 `app/hybrid_retrieval.py`

Menggabungkan vector search, FTS, graph expansion, dan reranking.

### 6.10 `app/compression/context_compressor.py`

Menyusun evidence pack yang pendek dan relevan.

### 6.11 `app/llm/clients.py`

Client untuk Ollama dan OpenAI-compatible API.

### 6.12 `app/verification/verifier.py`

Memeriksa kecocokan jawaban dengan evidence pack.

### 6.13 `app/answer_quality.py` dan `app/answer_evaluator.py`

Mendeteksi artifact, role confusion, issue tags, dan quality score.

### 6.14 `app/quality_store.py`

SQLite database untuk menyimpan kualitas jawaban dan feedback.

---

## 7. Database dan File Output

### 7.1 Chroma

Lokasi:

```text
data/chroma/
```

Collection default:

```text
rag_multilingual_minilm_l12_v2_384
```

### 7.2 FTS5

Lokasi:

```text
data/indexes/fts.sqlite3
```

Tabel:

- `chunks`
- `chunk_fts`

### 7.3 Quality DB

Lokasi:

```text
data/quality/answer_quality.sqlite3
```

Tabel:

- `answer_quality`
- `quality_feedback`

### 7.4 Evidence

Lokasi:

```text
data/evidence/*.evidence.json
```

### 7.5 Answers

Lokasi:

```text
data/answers/*.answer.json
data/answers/*.answer.md
```

### 7.6 Graph

Lokasi:

```text
data/graph/nodes.jsonl
data/graph/edges.jsonl
data/graph/graph_summary.json
```

---

## 8. CLI Commands

### Setup dan validasi

```bash
python -m app.validate_models
python -m app.show_model_mode
python -m app.stats
```

### Ingestion

```bash
python -m app.ingest
python -m app.rebuild_fts
python -m app.build_graph
```

### Retrieval test

```bash
python -m app.query_db "query"
python -m app.hybrid_query "query"
python -m app.evidence_query "query"
```

### Answer generation

```bash
python -m app.answer_query "query"
python -m app.answer_query --dry-run "query"
```

### Quality

```bash
python -m app.quality_report
python -m app.eval_answer_quality
python -m app.add_quality_feedback 1 good --note "Catatan"
```

---

## 9. Model Strategy

### 9.1 RAG Model

Model kecil khusus RAG:

```text
qwen-rag-1.5b:latest
```

Fungsi:

- menjawab evidence pack pendek;
- menghasilkan jawaban ringkas;
- dibantu fallback dan verifier.

### 9.2 Coder Model

```text
qwen-coder-1.5b:latest
```

Fungsi:

- coding;
- debugging;
- refactoring;
- explanation.

### 9.3 General Model

```text
qwen-general:4b:latest
```

Status:

- disiapkan sebagai target;
- belum wajib aktif;
- harus lolos model validation sebelum dipakai.

---

## 10. Quality Strategy

Quality tidak sepenuhnya diserahkan ke LLM. Sistem menggunakan kombinasi:

1. verifier berbasis evidence;
2. role rules dalam `component_roles.json`;
3. issue tags;
4. quality score;
5. fallback/refiner;
6. feedback manual;
7. rencana future: quality good answer collection.

Model kecil tidak “belajar” dengan update bobot. Yang belajar adalah sistem melalui:

```text
quality DB
feedback
corrected answer
role rules
few-shot examples
```

---

## 11. Batasan Saat Ini

- Parser PDF belum dioptimalkan untuk dokumen scan/OCR.
- Chunking masih berbasis karakter, belum semantic/heading-aware.
- Verifier masih keyword-based.
- Quality evaluator belum memakai LLM judge.
- Good answer retrieval belum aktif.
- Model general 4B belum menjadi mode default.
- API/server web belum tersedia.
- Unit test belum lengkap.

---

## 12. Risiko Teknis

| Risiko | Dampak | Mitigasi |
|---|---|---|
| Model kecil melantur | Jawaban tidak stabil | Evidence compression + verifier + fallback |
| Role confusion | Komponen disebut melakukan tugas yang salah | component_roles + evaluator |
| Retrieval noise | Dokumen tidak relevan masuk konteks | reranker + cutoff |
| Quality false positive | Jawaban benar dianggap salah | feedback + evaluator update |
| Quality false negative | Jawaban salah dianggap benar | role rules + refiner |
| Data folder terlalu besar | Repository berat | `.gitignore` ketat |

---

## 13. Kriteria Stabil

Sistem dianggap stabil untuk tahap lokal awal jika:

1. `python -m app.validate_models` menunjukkan RAG dan coder model tersedia;
2. `python -m app.ingest` tidak membuat duplikasi;
3. `python -m app.hybrid_query` mengambil chunk relevan;
4. `python -m app.answer_query` menghasilkan jawaban supported;
5. `python -m app.quality_report` tidak menunjukkan artifact-like untuk query dasar;
6. jawaban disimpan di `data/answers`;
7. quality record disimpan di `data/quality/answer_quality.sqlite3`.
