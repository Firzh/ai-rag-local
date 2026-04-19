# AI RAG Local

**AI RAG Local** adalah proyek Retrieval-Augmented Generation lokal untuk menjalankan tanya jawab berbasis dokumen di komputer pribadi. Proyek ini dirancang agar tetap ringan pada perangkat terbatas, dengan fokus pada pipeline lokal: file routing, parsing, chunking, embedding, vector search, keyword search, graph ringan, context compression, answer generation, verifier, dan quality memory.

Repository: `Firzh/ai-rag-local`  
Target awal: Windows + Python virtual environment + Ollama lokal.

---

## 1. Tujuan Proyek

Tujuan utama proyek ini adalah membangun sistem RAG lokal yang:

1. dapat membaca dokumen lokal;
2. memecah dokumen menjadi chunk;
3. membuat embedding lokal;
4. menyimpan embedding ke Chroma;
5. mendukung pencarian hybrid melalui vector search dan SQLite FTS5;
6. membangun konteks pendek melalui Context Compression Layer;
7. mengirim evidence pack ke model lokal;
8. memverifikasi jawaban terhadap evidence;
9. menyimpan catatan kualitas jawaban untuk pengembangan lanjutan.

Proyek ini tidak dirancang untuk langsung bergantung pada model besar. Model kecil tetap dapat digunakan selama pipeline, verifier, dan quality layer mendukungnya.

---

## 2. Arsitektur Ringkas

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
→ Answer Quality Store
→ Saved Answer
```

---

## 3. Komponen Utama

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
| Verifier | Mengecek apakah jawaban didukung evidence |
| Quality Store | Menyimpan kualitas jawaban dan feedback |

---

## 4. Struktur Folder

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
│   ├── quality_store.py
│   ├── quality_report.py
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
├── Modelfile.rag
└── requirements.txt
```

`data/` berisi data kerja lokal dan sebaiknya tidak semua isinya dikomit ke GitHub, terutama database, cache, index, evidence, dan jawaban hasil eksperimen.

---

## 5. Kebutuhan Sistem

### Minimum yang disarankan

- OS: Windows 10/11
- Python: 3.12 direkomendasikan
- Java: 11+ untuk OpenDataLoader PDF
- RAM: 16 GB minimum, 32 GB direkomendasikan
- GPU: opsional; GTX 1650 4 GB cukup untuk eksperimen model kecil
- Ollama: untuk menjalankan model lokal

### Catatan Python

Gunakan virtual environment. Hindari instalasi global untuk dependency Python.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

---

## 6. Setup Environment

1. Clone repository:

```bash
git clone https://github.com/Firzh/ai-rag-local.git
cd ai-rag-local
```

2. Buat virtual environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependency:

```bash
pip install -r requirements.txt
```

4. Salin `.env.sample` menjadi `.env`:

```bash
cp .env.sample .env
```

5. Sesuaikan path di `.env`, terutama:

```env
RAG_PROJECT_DIR=F:\AI-Models\ai-rag-local
RAG_INBOX_DIR=F:\AI-Models\ai-rag-local\data\inbox
RAG_CHROMA_DIR=F:\AI-Models\ai-rag-local\data\chroma
RAG_OLLAMA_BASE_URL=http://127.0.0.1:11434
RAG_MODEL_MODE=rag
RAG_OLLAMA_MODEL_RAG=qwen-rag-1.5b:latest
RAG_OLLAMA_MODEL_CODER=qwen-coder-1.5b:latest
RAG_OLLAMA_MODEL_GENERAL=qwen-general:4b:latest
```

---

## 7. Setup Model Ollama

Model RAG dibuat sebagai turunan konfigurasi dari model coder yang sudah ada di Ollama. Ini bukan fine-tuning. `Modelfile.rag` hanya membuat custom tag dengan parameter, template, dan system prompt baru.

```bash
ollama create qwen-rag-1.5b -f Modelfile.rag
ollama list
```

Validasi model:

```bash
python -m app.validate_models
```

Tes koneksi model:

```bash
python -c "from app.llm.clients import get_llm_client; c=get_llm_client(); r=c.generate('Jawab hanya: OK.', 'Tes.'); print(r.text)"
```

Target output:

```text
OK.
```

---

## 8. Cara Menggunakan

### 8.1 Menambahkan dokumen

Letakkan dokumen ke folder:

```text
data/inbox/
```

Format yang sudah didukung awal:

- `.pdf`
- `.txt`
- `.md`
- file teks/kode sederhana

### 8.2 Index dokumen

```bash
python -m app.ingest
```

### 8.3 Bangun index tambahan

```bash
python -m app.rebuild_fts
python -m app.build_graph
```

### 8.4 Cek retrieval

```bash
python -m app.hybrid_query "apa isi dokumen ini?"
```

### 8.5 Buat evidence pack

```bash
python -m app.evidence_query "apa itu RAG lokal?"
```

### 8.6 Tanya jawab penuh

```bash
python -m app.answer_query "apa itu RAG lokal?"
```

### 8.7 Cek kualitas jawaban

```bash
python -m app.quality_report
```

---

## 9. Mode Model

Proyek mendukung mode model melalui `.env`:

```env
RAG_MODEL_MODE=rag
```

Mode yang dirancang:

| Mode | Model | Fungsi |
|---|---|---|
| `rag` | `qwen-rag-1.5b:latest` | Menjawab evidence pack pendek |
| `coder` | `qwen-coder-1.5b:latest` | Bantuan coding/debugging |
| `general` | `qwen-general:4b:latest` | Model general 4B, belum wajib aktif |

Cek mode aktif:

```bash
python -m app.show_model_mode
```

---

## 10. Quality Layer

Quality layer digunakan untuk mengatasi keterbatasan model kecil. Sistem menyimpan riwayat kualitas jawaban ke SQLite:

```text
data/quality/answer_quality.sqlite3
```

Quality layer memeriksa:

- apakah jawaban didukung evidence;
- apakah jawaban menyalin label prompt;
- apakah ada role confusion;
- apakah sumber dicantumkan;
- apakah fallback/refiner digunakan;
- apakah jawaban layak dijadikan contoh baik.

Feedback manual dapat ditambahkan:

```bash
python -m app.add_quality_feedback 3 good --note "Jawaban sudah benar."
```

---

## 11. Status Saat Ini

Sudah berjalan:

- parser PDF dan teks;
- embedding lokal;
- Chroma vector store;
- SQLite FTS5;
- Mini Graph;
- hybrid retrieval;
- context compression;
- evidence pack;
- Ollama RAG answer model;
- verifier;
- answer quality store;
- quality report.

Belum final:

- quality good answers collection;
- LLM-based answer refiner;
- model general 4B;
- parser DOCX/XLSX/PPTX;
- automated test suite;
- packaging CLI yang lebih rapi.

Lihat file `DEVELOPMENT_PLAN.md` dan `UNFINISHED.md` untuk pengembangan berikutnya.

---

## 12. Troubleshooting

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

### Jawaban model melantur

Cek template Ollama dan jalankan:

```bash
python -c "from app.llm.clients import get_llm_client; c=get_llm_client(); r=c.generate('Jawab hanya: OK.', 'Tes.'); print(r.text)"
```

Jika tidak menjawab `OK`, perbaiki `Modelfile.rag`, lalu jalankan ulang `ollama create`.

### Retrieval mengambil dokumen tidak relevan

Jalankan:

```bash
python -m app.hybrid_query "query Anda"
python -m app.eval_rag
```

Sesuaikan nilai:

```env
RAG_SCORE_CUTOFF=0.30
RAG_DISTANCE_CUTOFF=0.82
RAG_RERANK_TOP_K=5
```

---

## 13. Lisensi

Belum ditentukan. Tambahkan file `LICENSE` sebelum repository dipublikasikan lebih luas.
