# AI RAG Local

AI RAG Local adalah proyek **Retrieval-Augmented Generation lokal** untuk menjalankan tanya jawab berbasis dokumen di komputer pribadi. Sistem dirancang ringan, modular, dan dapat diaudit melalui pipeline lokal: file routing, parsing, chunking, embedding, vector search, keyword search, mini graph, context compression, evidence pack, answer generation, verifier, dan answer quality store.

Repository: `Firzh/ai-rag-local`  
Target awal: Windows + Python virtual environment + Ollama lokal.

---

## 1. Tujuan Proyek

Tujuan utama proyek ini adalah membangun sistem RAG lokal yang:

1. membaca dokumen lokal dari folder kerja;
2. memecah dokumen menjadi chunk;
3. membuat embedding lokal;
4. menyimpan embedding ke Chroma;
5. mendukung retrieval hybrid melalui vector search, SQLite FTS5, dan mini graph;
6. menyusun evidence pack pendek melalui context compression;
7. mengirim evidence pack ke model lokal;
8. memverifikasi jawaban terhadap evidence;
9. menyimpan catatan kualitas jawaban untuk pengembangan lanjutan;
10. menyediakan benchmark lokal agar perubahan model, prompt, dan verifier bisa diuji ulang.

Proyek ini tidak diarahkan untuk langsung bergantung pada model besar. Model kecil dan model 4B dipakai secara bertahap, dengan penguatan pada retrieval, verifier, quality evaluator, dan regression benchmark.

---

## 2. Status Baseline v2.1

Baseline v2.1 menetapkan `qwen3:4b-instruct` sebagai model general yang lolos evaluasi awal untuk answer generation berbasis evidence.

Status terakhir:

| Area | Status |
|---|---|
| Model mode `general` | Lulus |
| Model aktif | `qwen3:4b-instruct` |
| RAG model ringan | `qwen-rag-1.5b:latest` |
| Coder model | `qwen-coder-1.5b:latest` |
| Model availability validation | Lulus |
| Model smoke benchmark | 4/5 lulus |
| RAG regression benchmark | 4/4 lulus |
| Safe abstention quality | Lulus |
| Qwen judge | Tersedia sebagai opsi, masih default OFF |
| Arithmetic reasoning | Belum aman tanpa tool deterministik |

Catatan penting: model lokal kecil dan 4B tidak boleh dipercaya untuk kalkulasi numerik. Tes `17 * 23` masih gagal pada model 4B maupun 1.5B, sehingga perhitungan harus diarahkan ke tool deterministik seperti Python/calculator layer.

---

## 3. Arsitektur Ringkas

```text
File masuk
→ File Router: Magika
→ Parser: OpenDataLoader PDF / parser teks
→ Chunking
→ Embedding: FastEmbed
→ Vector DB: Chroma PersistentClient
→ Keyword Search: SQLite FTS5 / BM25
→ Mini Graph JSONL
→ Hybrid Retrieval
→ Reranker
→ Context Compressor
→ Evidence Pack
→ Local LLM via Ollama
→ Verifier
→ Answer Quality Evaluator
→ Answer Quality Store
→ Saved Answer
```

---

## 4. Komponen Utama

| Komponen | Fungsi |
|---|---|
| Magika | Mendeteksi tipe file dan menentukan routing parser |
| OpenDataLoader PDF | Memproses PDF menjadi teks/markdown/json |
| Text Parser | Membaca TXT, Markdown, source code, dan file teks lain |
| FastEmbed | Membuat embedding lokal berbasis ONNX |
| ChromaDB | Menyimpan dan mengambil embedding dokumen |
| SQLite FTS5 | Pencarian keyword/BM25 ringan |
| Mini Graph | Memetakan relasi dokumen, chunk, parser, filetype, dan term |
| Context Compressor | Mengubah retrieval mentah menjadi evidence pack pendek |
| Ollama | Runtime model lokal |
| Local Verifier | Mengecek apakah jawaban didukung evidence |
| Qwen Judge | Verifier LLM opsional, default OFF |
| Answer Evaluator | Mendeteksi artifact, role confusion, dan safe abstention |
| Quality Store | Menyimpan kualitas jawaban, feedback, dan audit verifier |
| Model Smoke Bench | Benchmark singkat untuk model aktif |
| RAG Regression Bench | Benchmark regression untuk positive query, false premise, pipeline recall, dan out-of-scope guard |

---

## 5. Struktur Folder

```text
ai-rag-local/
├── app/
│   ├── compression/
│   ├── db/
│   ├── embeddings/
│   ├── graph/
│   ├── llm/
│   ├── memory/
│   ├── parsers/
│   ├── verification/
│   ├── answer_query.py
│   ├── answer_quality.py
│   ├── answer_evaluator.py
│   ├── answer_postprocess.py
│   ├── hybrid_retrieval.py
│   ├── ingest.py
│   ├── model_smoke_bench.py
│   ├── rag_regression_bench.py
│   ├── quality_store.py
│   ├── quality_report.py
│   ├── show_model_mode.py
│   └── validate_models.py
├── data/
│   ├── inbox/
│   ├── parsed/
│   ├── chroma/
│   ├── indexes/
│   ├── graph/
│   ├── evidence/
│   ├── answers/
│   ├── quality/
│   ├── memory/
│   └── logs/
├── .env.sample
├── .gitignore
├── DEVELOPMENT_PLAN.md
├── SPECIFICATION.md
├── UNFINISHED.md
├── Modelfile.rag
└── requirements.txt
```

`data/` berisi data kerja lokal. Jangan commit database, cache, index, evidence, jawaban hasil eksperimen, atau output benchmark kecuali memang sedang membuat fixture resmi.

---

## 6. Kebutuhan Sistem

Minimum yang disarankan:

| Komponen | Rekomendasi |
|---|---|
| OS | Windows 10/11 |
| Python | 3.12 direkomendasikan |
| Java | 11+ untuk OpenDataLoader PDF |
| RAM | 16 GB minimum, 32 GB direkomendasikan |
| GPU | Opsional; GTX 1650 4 GB cukup untuk eksperimen model kecil |
| Runtime model | Ollama lokal |

Gunakan virtual environment. Hindari instalasi dependency Python secara global.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

Untuk Git Bash:

```bash
source .venv/Scripts/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

---

## 7. Setup Environment

Salin `.env.sample` menjadi `.env`, lalu sesuaikan path dan model.

```bash
cp .env.sample .env
```

Baseline v2.1:

```env
RAG_LLM_PROVIDER=ollama
RAG_OLLAMA_BASE_URL=http://127.0.0.1:11434

RAG_MODEL_MODE=general
RAG_OLLAMA_MODEL_RAG=qwen-rag-1.5b:latest
RAG_OLLAMA_MODEL_CODER=qwen-coder-1.5b:latest
RAG_OLLAMA_MODEL_GENERAL=qwen3:4b-instruct
RAG_OLLAMA_MODEL=

RAG_LLM_TEMPERATURE=0.1
RAG_LLM_MAX_TOKENS=350
RAG_ANSWER_MAX_CHARS=1200

RAG_QWEN_JUDGE_ENABLED=false
RAG_VERIFICATION_AUDIT_ENABLED=false
```

`RAG_OLLAMA_MODEL` adalah override langsung. Biarkan kosong jika ingin memakai role-based model selection melalui `RAG_MODEL_MODE`.

---

## 8. Setup Model Ollama

Pastikan model tersedia di Ollama:

```bash
ollama list
```

Model yang dipakai pada baseline v2.1:

```text
qwen3:4b-instruct
qwen-rag-1.5b:latest
qwen-coder-1.5b:latest
```

Validasi:

```bash
python -m app.show_model_mode
python -m app.validate_models
```

Target:

```text
Model mode: general
Selected Ollama model: qwen3:4b-instruct
selected | qwen3:4b-instruct | YES
general  | qwen3:4b-instruct | YES
```

---

## 9. Cara Menggunakan

### 9.1 Menambahkan dokumen

Letakkan dokumen ke folder:

```text
data/inbox/
```

Format awal yang didukung:

- `.pdf`
- `.txt`
- `.md`
- file teks/kode sederhana

### 9.2 Ingest dokumen

```bash
python -m app.ingest
```

### 9.3 Bangun index tambahan

```bash
python -m app.rebuild_fts
python -m app.build_graph
```

### 9.4 Cek retrieval

```bash
python -m app.hybrid_query "apa isi dokumen ini?"
```

### 9.5 Buat evidence pack

```bash
python -m app.evidence_query "apa itu RAG lokal?"
```

### 9.6 Tanya jawab penuh

```bash
python -m app.answer_query "apa itu RAG lokal?"
```

### 9.7 Dry-run prompt dan evidence

```bash
python -m app.answer_query "apa itu RAG lokal?" --dry-run
```

### 9.8 Cek kualitas jawaban

```bash
python -m app.quality_report
```

---

## 10. Mode Model

Mode model dikendalikan melalui `.env` atau environment variable shell.

```env
RAG_MODEL_MODE=general
```

| Mode | Model | Fungsi |
|---|---|---|
| `rag` | `qwen-rag-1.5b:latest` | Model ringan untuk eksperimen RAG pendek |
| `coder` | `qwen-coder-1.5b:latest` | Bantuan coding/debugging |
| `general` | `qwen3:4b-instruct` | Model general 4B untuk answer generation utama baseline v2.1 |

Cek mode aktif:

```bash
python -m app.show_model_mode
```

Switch sementara di Git Bash:

```bash
export RAG_MODEL_MODE=general
python -m app.show_model_mode
```

---

## 11. Quality Layer

Quality layer digunakan untuk mengatasi keterbatasan model lokal. Sistem menyimpan riwayat kualitas jawaban ke SQLite:

```text
data/quality/answer_quality.sqlite3
```

Quality layer memeriksa:

- apakah jawaban didukung evidence;
- apakah jawaban menyalin label prompt;
- apakah ada role confusion;
- apakah sumber dicantumkan;
- apakah jawaban out-of-scope melakukan safe abstention;
- apakah fallback/refiner digunakan;
- apakah jawaban layak dijadikan contoh baik.

Safe abstention adalah jawaban yang menolak mengarang ketika dokumen tidak menyediakan informasi. Contoh yang benar:

```text
Tidak ada informasi tentang presiden Indonesia saat ini dalam dokumen proyek ini.
```

Feedback manual:

```bash
python -m app.add_quality_feedback 3 good --note "Jawaban sudah benar."
```

---

## 12. Benchmark Lokal

### 12.1 Model smoke benchmark

Benchmark ini menguji kepatuhan instruksi, arithmetic weakness, grounding Magika/Chroma, acronym safety, dan artifact labels.

```bash
python -m app.model_smoke_bench
```

Baseline v2.1 dengan `qwen3:4b-instruct`:

```text
SUMMARY: 4/5 passed
```

Satu kegagalan yang diketahui adalah arithmetic. Ini bukan blocker untuk RAG, tetapi menjadi batasan penting.

### 12.2 RAG regression benchmark

Benchmark ini menguji positive evidence, false premise, pipeline recall, dan out-of-scope guard.

```bash
python -m app.rag_regression_bench
```

Baseline v2.1:

```text
SUMMARY: 4/4 passed
```

---

## 13. Status Saat Ini

Sudah berjalan:

- parser PDF dan teks;
- embedding lokal;
- Chroma vector store;
- SQLite FTS5;
- Mini Graph;
- hybrid retrieval;
- context compression;
- evidence pack;
- Ollama answer model;
- local verifier;
- answer quality store;
- verification audit store;
- safe abstention evaluator;
- model smoke benchmark;
- RAG regression benchmark;
- quality report.

Belum final:

- Qwen judge integration test aktif;
- quality good answers collection;
- LLM-based answer refiner;
- parser DOCX/XLSX/PPTX;
- CLI terpadu;
- local API/UI;
- numeric/tool-use layer untuk kalkulasi.

Lihat `DEVELOPMENT_PLAN.md` dan `UNFINISHED.md` untuk pengembangan berikutnya.

---

## 14. Troubleshooting

### Model tidak ditemukan

```text
Ollama error 404: model not found
```

Cek:

```bash
ollama list
python -m app.validate_models
```

Pastikan nama model di `.env` sama persis dengan nama di `ollama list`.

### `.env` sudah benar tetapi config masih lama

Cek environment aktif:

```bash
python -c "import os; print(os.getenv('RAG_MODEL_MODE')); print(os.getenv('RAG_OLLAMA_MODEL_GENERAL')); print(os.getenv('RAG_OLLAMA_MODEL'))"
```

Jika shell masih menyimpan nilai lama, bersihkan:

```bash
unset RAG_MODEL_MODE
unset RAG_OLLAMA_MODEL_GENERAL
unset RAG_OLLAMA_MODEL
```

Lalu jalankan ulang:

```bash
python -c "from app.config import settings; print(settings.model_mode, settings.ollama_model)"
```

### Jawaban model melantur

Jalankan:

```bash
python -m app.model_smoke_bench
python -m app.rag_regression_bench
```

Jika regression gagal, cek evidence pack:

```bash
python -m app.answer_query "query Anda" --dry-run
```

### Retrieval mengambil dokumen tidak relevan

Jalankan:

```bash
python -m app.hybrid_query "query Anda"
```

Parameter yang bisa disesuaikan:

```env
RAG_SCORE_CUTOFF=0.30
RAG_DISTANCE_CUTOFF=0.82
RAG_RERANK_TOP_K=5
```

---

## 15. Lisensi

Belum ditentukan. Tambahkan file `LICENSE` sebelum repository dipublikasikan lebih luas.
