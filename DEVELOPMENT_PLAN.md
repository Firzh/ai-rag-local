# Rencana Pengembangan Lanjutan AI RAG Local

Dokumen ini menjelaskan arah pengembangan lanjutan proyek setelah pipeline RAG lokal dasar berhasil berjalan.

---

## 1. Prinsip Pengembangan

Pengembangan tidak diarahkan langsung ke model besar. Prioritasnya adalah memperkuat sistem pendukung agar model kecil maupun model 4B dapat menjawab lebih stabil.

Prinsip utama:

```text
retrieval lebih bersih
context lebih pendek
jawaban lebih grounded
quality lebih terukur
feedback lebih berguna
model mode lebih fleksibel
```

---

## 2. Roadmap Prioritas

## Tahap 1 — Stabilization

Status: sedang berjalan.

Target:

- memastikan model RAG 1.5B stabil;
- memperbaiki answer quality evaluator;
- mengurangi role confusion;
- membuat feedback manual mudah dipakai;
- memastikan jawaban dasar lolos quality check.

Checklist:

- [x] File router dengan Magika
- [x] PDF parser dengan OpenDataLoader PDF
- [x] Text parser
- [x] FastEmbed
- [x] Chroma
- [x] SQLite FTS5
- [x] Mini Graph
- [x] Hybrid retrieval
- [x] Context compressor
- [x] Evidence pack
- [x] Ollama RAG model
- [x] Verifier
- [x] Quality Store
- [ ] Role-aware deterministic refiner final
- [ ] Auto-feedback final
- [ ] Quality report dengan issue trend

---

## Tahap 2 — Quality Memory

Tujuan: membuat sistem belajar dari jawaban bagus dan buruk tanpa fine-tuning.

Fitur:

1. menyimpan jawaban bagus;
2. menyimpan jawaban buruk;
3. menyimpan corrected answer;
4. menyimpan issue tags;
5. mengambil contoh jawaban bagus untuk query mirip.

Output yang diharapkan:

```text
data/quality/answer_quality.sqlite3
collection: quality_good_answers
```

Kriteria jawaban yang boleh masuk quality-good collection:

```text
supported=True
quality_pass=True
issue_tags=[]
artifact_like=False
feedback_label=good
```

---

## Tahap 3 — Quality Good Answer Retrieval

Tujuan: memberi contoh jawaban bagus ke prompt agar model kecil meniru format yang benar.

Alur:

```text
User query
→ search quality_good_answers
→ ambil 1–2 contoh relevan
→ masukkan ke prompt sebagai style/example
→ generate answer
→ verifier + quality evaluator
```

Catatan:

- Jangan campur quality_good_answers dengan collection dokumen utama.
- Quality collection hanya untuk style dan pattern jawaban, bukan sumber fakta.
- Jawaban final tetap harus mengutip evidence dari dokumen sumber.

---

## Tahap 4 — LLM Refiner Opsional

Tujuan: memperbaiki jawaban yang quality-nya rendah.

Alur:

```text
answer awal
→ issue tags
→ evidence pack
→ LLM refiner
→ refined answer
→ verifier
→ quality evaluator
```

Refiner harus dibatasi:

- tidak boleh menambah fakta baru;
- hanya boleh menulis ulang berdasarkan evidence;
- wajib menghapus issue tags;
- wajib menyertakan sumber.

Default yang disarankan:

```text
deterministic refiner dahulu
LLM refiner hanya opsional
```

---

## Tahap 5 — Model General 4B

Tujuan: menambahkan model general yang lebih natural tanpa merusak mode RAG 1.5B.

Langkah:

1. install/import Qwen 4B ke Ollama;
2. buat model tag `qwen-general:4b:latest`;
3. validasi dengan `python -m app.validate_models`;
4. tes instruksi pendek `OK`;
5. tes aritmetika pendek;
6. tes `answer_query` dasar;
7. bandingkan output RAG 1.5B vs general 4B.

Jangan langsung mengganti default:

```env
RAG_MODEL_MODE=rag
```

tetap dipakai sampai 4B lolos evaluasi.

---

## Tahap 6 — Parser Expansion

Tambahkan parser baru:

| Format | Rencana |
|---|---|
| DOCX | `python-docx` atau parser ringan |
| XLSX/CSV | parser tabel + row chunking |
| PPTX | ekstraksi teks slide |
| HTML | parser HTML ke markdown |
| log/error | parser khusus log stacktrace |
| source code | chunking berbasis fungsi/class |
| image/scan PDF | OCR opsional, bukan default |

Prinsip:

- parser menyimpan hasil ke `data/parsed`;
- output parser harus punya metadata;
- jangan langsung kirim dokumen mentah ke LLM.

---

## Tahap 7 — Better Chunking

Chunking saat ini masih berbasis karakter. Pengembangan berikutnya:

1. heading-aware chunking;
2. page-aware chunking untuk PDF;
3. code-aware chunking;
4. table-aware chunking;
5. semantic chunking ringan;
6. chunk quality scoring.

Metadata chunk minimal:

```json
{
  "source_name": "...",
  "source_path": "...",
  "page": 1,
  "heading": "...",
  "chunk_index": 0,
  "chunk_hash": "...",
  "document_hash": "...",
  "parser": "..."
}
```

---

## Tahap 8 — Evaluation Suite

Tambahkan test suite lokal:

```text
tests/
├── test_router.py
├── test_parser.py
├── test_chunking.py
├── test_retrieval.py
├── test_evidence.py
├── test_answer_quality.py
└── test_model_client.py
```

Target evaluasi:

- retrieval precision;
- answer groundedness;
- role correctness;
- latency;
- memory usage;
- context size;
- fallback rate;
- quality pass rate.

---

## Tahap 9 — CLI/Orchestrator

Saat ini command masih tersebar. Buat CLI tunggal:

```bash
python -m app.main ingest
python -m app.main ask "query"
python -m app.main evidence "query"
python -m app.main quality report
python -m app.main model validate
```

Atau pakai Typer:

```bash
raglocal ingest
raglocal ask "query"
raglocal quality-report
```

---

## Tahap 10 — Local API / UI

Setelah CLI stabil:

- FastAPI local server;
- simple web UI;
- drag-and-drop dokumen;
- daftar indexed files;
- evidence viewer;
- answer quality dashboard;
- manual feedback form.

---

## 3. Rencana Quality Learning

Quality learning bukan fine-tuning. Sistem belajar melalui:

1. issue tags;
2. role rules;
3. corrected answer;
4. feedback label;
5. good answer retrieval;
6. prompt examples;
7. evaluator refinement.

Alur masa depan:

```text
Jawaban buruk
→ issue tags
→ corrected answer
→ simpan feedback
→ jika sudah good, masuk quality_good_answers
→ dipakai sebagai example untuk query mirip
```

---

## 4. Rencana Fine-tuning

Belum prioritas. Fine-tuning hanya dipertimbangkan jika:

- minimal ada 500–1000 pasangan query/evidence/good answer;
- format data konsisten;
- quality pass tinggi;
- hardware dan runtime mendukung.

Sebelum itu, gunakan:

```text
RAG + quality memory + few-shot examples
```

---

## 5. Target Milestone

### Milestone A — Stable Local RAG

- model RAG 1.5B stabil;
- jawaban dasar supported;
- quality report bersih;
- feedback dapat disimpan.

### Milestone B — Adaptive Quality Memory

- good answer collection aktif;
- prompt dapat mengambil contoh jawaban bagus;
- model kecil lebih konsisten.

### Milestone C — General Model Comparison

- Qwen 4B aktif;
- mode switch stabil;
- benchmark RAG 1.5B vs 4B.

### Milestone D — Document Expansion

- DOCX, XLSX, PPTX, HTML parser;
- semantic chunking;
- metadata lebih kaya.

### Milestone E — Local Productization

- CLI tunggal;
- local API;
- UI sederhana;
- dokumentasi final.
