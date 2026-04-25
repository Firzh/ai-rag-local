# Rencana Pengembangan Lanjutan AI RAG Local

Dokumen ini menjelaskan arah pengembangan lanjutan proyek setelah baseline lokal v2.1 berhasil berjalan. Fokus pengembangan tetap sama: membuat RAG lokal yang ringan, dapat diaudit, dan stabil pada perangkat pribadi, tanpa langsung bergantung pada model besar.

---

## 1. Prinsip Pengembangan

Pengembangan tidak diarahkan langsung ke model besar. Prioritasnya adalah memperkuat sistem pendukung agar model kecil maupun model 4B dapat menjawab lebih grounded.

Prinsip utama:

```text
retrieval lebih bersih
context lebih pendek
jawaban lebih grounded
quality lebih terukur
abstention lebih aman
feedback lebih berguna
benchmark bisa diulang
model mode lebih fleksibel
```

Setiap perubahan besar harus bisa diuji dengan minimal:

```bash
python -m app.validate_models
python -m app.model_smoke_bench
python -m app.rag_regression_bench
python -m app.quality_report
```

---

## 2. Baseline v2.1

Baseline v2.1 menetapkan bahwa `qwen3:4b-instruct` sudah layak digunakan sebagai model `general` untuk answer generation berbasis evidence, dengan catatan tidak digunakan untuk kalkulasi numerik tanpa tool deterministik.

Status baseline:

| Area | Status |
|---|---|
| Model mode `general` | Lulus |
| Model aktif | `qwen3:4b-instruct` |
| Availability test | Lulus |
| Model smoke benchmark | 4/5 lulus |
| RAG regression benchmark | 4/4 lulus |
| Safe abstention evaluator | Lulus |
| Verification audit store | Lulus |
| Qwen judge aktif | Belum diuji, default OFF |
| Arithmetic reasoning | Belum aman tanpa tool |

Implikasi keputusan:

```env
RAG_MODEL_MODE=general
RAG_OLLAMA_MODEL_GENERAL=qwen3:4b-instruct
RAG_QWEN_JUDGE_ENABLED=false
RAG_VERIFICATION_AUDIT_ENABLED=false
```

---

## 3. Roadmap Prioritas

### Tahap 1 — Stabilization

Status: selesai untuk baseline lokal awal.

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
- [x] Ollama answer model
- [x] Local verifier
- [x] Quality Store
- [x] Verification audit store
- [x] Safe abstention evaluator
- [x] Model smoke benchmark
- [x] RAG regression benchmark
- [ ] Quality report dengan issue trend
- [ ] Refiner final

---

### Tahap 2 — Model General 4B Baseline

Status: selesai sebagai baseline awal.

Hasil:

- `qwen3:4b-instruct` tersedia di Ollama;
- mode `general` berhasil memilih model tersebut;
- model lulus instruction test, grounding Magika/Chroma, acronym safety, dan anti-artifact label;
- model gagal arithmetic test sehingga numeric reasoning harus diarahkan ke tool deterministik;
- RAG regression test lulus 4/4 pada query positive evidence, false premise, pipeline order, dan out-of-scope guard.

Catatan:

- `qwen-rag-1.5b:latest` tetap dipertahankan sebagai mode ringan dan pembanding;
- `qwen3:4b-instruct` dipakai sebagai model general utama pada baseline v2.1;
- jangan menghapus mode `rag` karena tetap berguna untuk pembandingan latency dan regression.

---

### Tahap 3 — Qwen Judge Integration Test

Status: berikutnya.

Tujuan: menguji verifier LLM opsional tanpa mengganggu local verifier.

Langkah aman:

1. pastikan baseline lokal lulus dengan Qwen judge OFF;
2. aktifkan audit terlebih dahulu;
3. aktifkan Qwen judge pada query kecil;
4. bandingkan verdict local verifier vs Qwen judge;
5. pastikan jika Qwen judge gagal, pipeline fallback ke local verifier;
6. jangan jadikan Qwen judge wajib sebelum stabil.

Command awal:

```bash
export RAG_MODEL_MODE=general
export RAG_VERIFICATION_AUDIT_ENABLED=true
export RAG_QWEN_JUDGE_ENABLED=true
python -m app.answer_query "Apakah Chroma adalah parser PDF?"
```

Kriteria lulus:

- local verifier tetap berjalan;
- Qwen judge tercatat di `answer_verification_runs`;
- jika Qwen judge tidak tersedia, pipeline tidak crash;
- quality report tetap bisa dibaca.

---

### Tahap 4 — Quality Memory

Status: belum selesai.

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
abstention_like=False
feedback_label=good
```

Catatan: abstention yang aman boleh lulus quality, tetapi tidak otomatis menjadi contoh good answer untuk semua query karena fungsi utamanya adalah guardrail, bukan style factual answer.

---

### Tahap 5 — Quality Good Answer Retrieval

Status: belum selesai.

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

Aturan:

- Jangan campur `quality_good_answers` dengan collection dokumen utama.
- Quality collection hanya untuk style dan pattern jawaban, bukan sumber fakta.
- Jawaban final tetap wajib mengutip evidence dari dokumen sumber.

---

### Tahap 6 — Refiner

Status: belum selesai.

Tujuan: memperbaiki jawaban yang quality-nya rendah tanpa menambah fakta baru.

Alur:

```text
answer awal
→ issue tags
→ evidence pack
→ deterministic refiner / LLM refiner
→ refined answer
→ verifier
→ quality evaluator
```

Refiner harus dibatasi:

- tidak boleh menambah fakta baru;
- hanya boleh menulis ulang berdasarkan evidence;
- wajib menghapus issue tags;
- wajib menyertakan sumber;
- harus bisa menolak bila evidence tidak cukup.

Prioritas:

```text
deterministic refiner dahulu
LLM refiner hanya opsional
```

---

### Tahap 7 — Parser Expansion

Status: belum selesai.

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
- jangan langsung kirim dokumen mentah ke LLM;
- parser baru harus masuk regression test minimal dengan satu fixture kecil.

---

### Tahap 8 — Better Chunking

Status: belum selesai.

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

### Tahap 9 — Evaluation Suite

Status: sebagian selesai.

Sudah ada:

```text
app/model_smoke_bench.py
app/rag_regression_bench.py
```

Perlu ditambah ke test formal:

```text
tests/
├── test_router.py
├── test_parser.py
├── test_chunking.py
├── test_retrieval.py
├── test_evidence.py
├── test_answer_quality.py
├── test_model_client.py
└── test_rag_regression.py
```

Target evaluasi:

- retrieval precision;
- answer groundedness;
- role correctness;
- false-premise correction;
- out-of-scope abstention;
- latency;
- memory usage;
- context size;
- fallback rate;
- quality pass rate.

---

### Tahap 10 — CLI/Orchestrator

Status: belum selesai.

Saat ini command masih tersebar. Buat CLI tunggal:

```bash
python -m app.main ingest
python -m app.main ask "query"
python -m app.main evidence "query"
python -m app.main quality report
python -m app.main model validate
python -m app.main bench model
python -m app.main bench rag
```

Atau pakai Typer:

```bash
raglocal ingest
raglocal ask "query"
raglocal quality-report
raglocal bench-model
raglocal bench-rag
```

---

### Tahap 11 — Local API / UI

Status: belum dimulai.

Setelah CLI stabil:

- FastAPI local server;
- simple web UI;
- drag-and-drop dokumen;
- daftar indexed files;
- evidence viewer;
- answer quality dashboard;
- manual feedback form.

---

## 4. Rencana Quality Learning

Quality learning bukan fine-tuning. Sistem belajar melalui:

1. issue tags;
2. role rules;
3. corrected answer;
4. feedback label;
5. good answer retrieval;
6. prompt examples;
7. evaluator refinement;
8. regression benchmark.

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

## 5. Rencana Fine-tuning

Fine-tuning belum prioritas.

Fine-tuning hanya dipertimbangkan jika:

- minimal ada 500–1000 pasangan query/evidence/good answer;
- format data konsisten;
- quality pass tinggi;
- hardware dan runtime mendukung;
- baseline RAG + quality memory sudah tidak cukup.

Sebelum itu, gunakan:

```text
RAG + quality memory + few-shot examples + regression benchmark
```

---

## 6. Target Milestone

### Milestone A — Stable Local RAG

Status: selesai.

- model lokal tersedia;
- jawaban dasar supported;
- quality report bersih;
- feedback dapat disimpan;
- safe abstention bekerja.

### Milestone B — General Model Baseline

Status: selesai untuk baseline awal.

- Qwen 4B aktif;
- mode switch stabil;
- benchmark RAG 1.5B vs 4B tersedia;
- regression benchmark lulus.

### Milestone C — Qwen Judge and Quality Memory

Status: berikutnya.

- Qwen judge aktif secara opsional;
- audit verifier stabil;
- good answer collection aktif;
- prompt dapat mengambil contoh jawaban bagus.

### Milestone D — Document Expansion

Status: belum selesai.

- DOCX, XLSX, PPTX, HTML parser;
- semantic/heading-aware chunking;
- metadata lebih kaya.

### Milestone E — Local Productization

Status: belum dimulai.

- CLI tunggal;
- local API;
- UI sederhana;
- dokumentasi final;
- packaging lokal.
