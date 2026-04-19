# Hal yang Belum Selesai dan Catatan Pengembangan Terakhir

Dokumen ini merangkum bagian yang belum selesai dari pengembangan terakhir AI RAG Local.

---

## 1. Status Terakhir yang Sudah Berhasil

Berikut bagian yang sudah berhasil berjalan:

- environment Python aktif;
- folder kerja dan `.env` sudah terbaca;
- Magika file router berjalan;
- OpenDataLoader PDF parser berjalan;
- text parser berjalan;
- FastEmbed menghasilkan embedding;
- Chroma menyimpan chunk;
- SQLite FTS5 dibangun;
- Mini Graph dibangun;
- Hybrid Retrieval berjalan;
- Context Compressor membuat evidence pack;
- Ollama RAG model berhasil menjawab;
- Verifier berjalan;
- Answer Quality DB aktif;
- Quality report berjalan.

---

## 2. Masalah yang Masih Terlihat

### 2.1 Quality evaluator masih bisa false pass

Beberapa jawaban masih lolos quality score meskipun secara makna ada role leakage. Contoh:

- Magika disebut terlalu melebar ke seluruh pipeline;
- Chroma disebut terkait parser/filetype/term penting;
- verifier keyword-based masih bisa menganggap jawaban supported karena banyak kata cocok.

Diperlukan:

- role-aware evaluator yang lebih kuat;
- issue tag yang lebih spesifik;
- refiner otomatis;
- feedback manual yang lebih terstruktur.

---

### 2.2 `component_roles.json` belum matang

File ini harus berkembang dari waktu ke waktu. Namun update harus dikontrol.

Belum selesai:

- mekanisme proposal update rule;
- validasi rule sebelum diterapkan;
- riwayat perubahan role rule;
- pemisahan allowed claim, forbidden claim, dan warning claim;
- auto-suggestion dari bad answer.

Prinsip:

```text
bad answer
→ detect issue
→ propose rule update
→ review
→ update component_roles.json
```

Jangan langsung auto-update rule tanpa kontrol.

---

### 2.3 Feedback manusia masih minimal

Masalah:

- manusia kadang hanya memberi label `good` atau `bad`;
- catatan feedback bisa kurang deskriptif;
- corrected answer belum selalu tersedia.

Belum selesai:

- auto feedback note berbasis issue tags;
- form feedback yang memaksa kategori masalah;
- corrected-answer assistant;
- quality feedback dashboard.

---

### 2.4 Auto Refiner belum final

Kebutuhan:

```text
jawaban awal
→ issue tags
→ refiner
→ jawaban perbaikan
→ verifier
→ quality evaluator
```

Belum selesai:

- deterministic refiner final;
- LLM refiner opsional;
- refiner untuk query umum;
- refiner untuk role-specific answer;
- fallback jika refiner gagal.

---

### 2.5 Quality good answers collection belum dibuat

Belum ada collection khusus:

```text
quality_good_answers
```

Fungsi masa depan:

- menyimpan contoh jawaban bagus;
- mengambil contoh untuk prompt few-shot;
- membantu model kecil meniru format jawaban yang benar.

Kriteria data masuk:

```text
supported=True
quality_pass=True
artifact_like=False
issue_tags=[]
feedback_label=good
```

---

### 2.6 Model general 4B belum tersedia

Validator menunjukkan mode general belum siap jika model belum ada di Ollama.

Belum selesai:

- import Qwen 4B;
- Modelfile general;
- model validation;
- OK test;
- arithmetic test;
- answer_query test;
- benchmark terhadap RAG 1.5B.

Default tetap:

```env
RAG_MODEL_MODE=rag
```

---

### 2.7 Parser dokumen belum lengkap

Saat ini fokus masih PDF dan teks.

Belum selesai:

- DOCX parser;
- XLSX parser;
- PPTX parser;
- HTML parser;
- log parser;
- source-code parser berbasis fungsi/class;
- OCR untuk PDF scan.

---

### 2.8 Chunking masih sederhana

Chunking masih berbasis karakter.

Belum selesai:

- heading-aware chunking;
- semantic chunking;
- code-aware chunking;
- page-aware chunking;
- table-aware chunking;
- chunk scoring.

---

### 2.9 Verifier masih keyword-based

Verifier belum benar-benar memahami entailment.

Risiko:

- jawaban salah tetapi banyak kata cocok bisa dianggap supported;
- jawaban benar tetapi paraphrase bisa mendapat score rendah.

Belum selesai:

- claim extraction;
- evidence alignment per claim;
- contradiction detection;
- optional LLM judge;
- numeric consistency check.

---

### 2.10 Belum ada test suite

Belum ada automated test formal.

Perlu dibuat:

```text
tests/test_router.py
tests/test_parser.py
tests/test_chunking.py
tests/test_retrieval.py
tests/test_compressor.py
tests/test_verifier.py
tests/test_quality.py
tests/test_model_client.py
```

---

### 2.11 Belum ada CLI terpadu

Saat ini command masih tersebar.

Belum selesai:

```bash
raglocal ingest
raglocal ask "query"
raglocal quality-report
raglocal model-validate
```

---

## 3. Bug/Issue yang Perlu Dicek Ulang

### 3.1 Quality report fallback flag

Pastikan `fallback_used` disimpan setelah fallback/refiner final selesai.

### 3.2 Artifact-like false positive/false negative

Cek ulang:

- `answer_quality.py`
- `answer_evaluator.py`
- `component_roles.json`

### 3.3 Role leakage pada Magika dan Chroma

Pastikan jawaban berikut dianggap salah:

```text
Magika melakukan embedding
Magika menyimpan ke Chroma
Chroma melakukan embedding
Chroma melakukan parsing
Chroma menghasilkan jawaban
```

Pastikan jawaban berikut dianggap benar:

```text
Magika berfungsi sebagai file router
Chroma berfungsi sebagai vector database
```

---

## 4. Prioritas Berikutnya

Urutan paling aman:

1. finalisasi `component_roles.json`;
2. finalisasi `answer_evaluator.py`;
3. tambahkan `answer_refiner.py`;
4. tambahkan `auto_feedback.py`;
5. simpan corrected answer;
6. buat quality_good_answers collection;
7. baru pasang Qwen 4B general.

---

## 5. Definisi Selesai untuk Tahap Berikutnya

Pengembangan tahap berikutnya dianggap selesai jika:

- query fungsi Magika menghasilkan role yang tepat;
- query fungsi Chroma menghasilkan role yang tepat;
- quality report menunjukkan `Artifact=False`;
- issue tags kosong untuk jawaban yang benar;
- feedback bisa menyimpan label dan corrected answer;
- bad answer bisa menghasilkan proposal perbaikan;
- jawaban bagus bisa disimpan sebagai contoh.

---

## 6. Catatan Strategis

Menambah model kecil memang membutuhkan banyak komponen pendukung. Namun ini bukan kelemahan semata. Dengan pipeline ini, sistem menjadi:

- lebih hemat resource;
- lebih dapat diaudit;
- tidak terlalu bergantung pada model besar;
- bisa diperbaiki bertahap melalui quality memory;
- siap dibandingkan dengan model 4B tanpa membuang fondasi yang sudah dibuat.
