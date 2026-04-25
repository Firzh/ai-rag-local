# Hal yang Belum Selesai dan Catatan Pengembangan Terakhir

Dokumen ini merangkum bagian yang belum selesai dari pengembangan AI RAG Local setelah baseline v2.1.

---

## 1. Status Terakhir yang Sudah Berhasil

Bagian yang sudah berhasil berjalan:

- environment Python aktif;
- folder kerja dan `.env` terbaca;
- Magika file router berjalan;
- OpenDataLoader PDF parser berjalan;
- text parser berjalan;
- FastEmbed menghasilkan embedding;
- Chroma menyimpan chunk;
- SQLite FTS5 dibangun;
- Mini Graph dibangun;
- Hybrid Retrieval berjalan;
- Context Compressor membuat evidence pack;
- Ollama answer model berjalan;
- mode `general` memakai `qwen3:4b-instruct`;
- model validation lulus;
- Local Verifier berjalan;
- Answer Quality DB aktif;
- Verification Audit DB berjalan;
- Quality report berjalan;
- safe abstention evaluator berjalan;
- model smoke benchmark tersedia;
- RAG regression benchmark tersedia;
- RAG regression benchmark baseline v2.1 lulus 4/4.
- Qwen judge hybrid integration via Ollama `/v1` lulus.
- Regression benchmark dengan judge aktif lulus 4/4.

---

## 2. Masalah yang Masih Terlihat

### 2.1 Arithmetic reasoning belum aman

Model lokal kecil dan model 4B masih gagal pada tes aritmetika sederhana. Contoh `17 * 23` tidak dijawab benar.

Risiko:

- jawaban numerik salah tetapi terlihat meyakinkan;
- kalkulasi keuangan, statistik, atau teknis menjadi tidak dapat dipercaya bila langsung memakai LLM.

Diperlukan:

- calculator/Python tool layer;
- numeric intent detector;
- aturan bahwa query hitungan tidak boleh dijawab murni oleh LLM;
- regression test khusus numerik.

---

### 2.2 Qwen judge sudah lulus integration test, tetapi belum menjadi default wajib

Qwen judge sudah berhasil diaktifkan melalui Ollama OpenAI-compatible `/v1` dengan `qwen3:4b-instruct`. Audit DB sudah mencatat `qwen_judge` dengan confidence nonzero pada query positive evidence, false premise, dan out-of-scope abstention.

Yang masih belum selesai:

- timeout policy ketika judge lambat atau endpoint tidak tersedia;
- retry/backoff policy;
- provider abstraction agar judge bisa memakai Ollama, Qwen API cloud, atau OpenAI API;
- benchmark biaya/latency/kualitas untuk Qwen API vs OpenAI API;
- kalibrasi final verdict ketika semantic judge mendukung tetapi lexical verifier rendah.

Prinsip tetap:

```text
local verifier tetap baseline
qwen judge opsional
qwen judge tidak boleh membuat pipeline crash
hybrid_strict lebih aman daripada semantic-only verdict
```

---

### 2.3 Qwen API dan OpenAI API belum diabstraksikan

Saat ini yang sudah diuji adalah Qwen lokal melalui Ollama `/v1`, bukan Qwen Cloud API. Pengembangan berikutnya perlu membuat provider abstraction agar answer generator dan judge bisa berpindah antara local Ollama, Qwen API, dan OpenAI API.

Alasan prioritas Qwen API:

- limit harian relatif besar;
- biaya lebih ringan dibanding banyak skenario OpenAI API;
- cocok sebagai semantic judge eksternal bila model lokal kurang kuat.

OpenAI API tetap berguna sebagai pembanding kualitas dan fallback, tetapi tidak boleh menjadi ketergantungan wajib.

---

### 2.4 Quality evaluator masih perlu diperkuat


Safe abstention sudah ditangani, tetapi evaluator masih perlu diperluas untuk kasus lain.

Belum selesai:

- issue tag lebih spesifik untuk semantic drift;
- issue tag untuk acronym hijack;
- issue tag untuk numeric hallucination;
- score calibration berdasarkan tipe jawaban;
- tren issue di `quality_report`.

---

### 2.4 `component_roles.json` belum matang

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

### 2.5 Feedback manusia masih minimal

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

### 2.6 Auto Refiner belum final

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
- fallback jika refiner gagal;
- guard agar refiner tidak menambah fakta baru.

---

### 2.7 Quality good answers collection belum dibuat

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
abstention_like=False
issue_tags=[]
feedback_label=good
```

---

### 2.8 Parser dokumen belum lengkap

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

### 2.9 Chunking masih sederhana

Chunking masih berbasis karakter.

Belum selesai:

- heading-aware chunking;
- semantic chunking;
- code-aware chunking;
- page-aware chunking;
- table-aware chunking;
- chunk scoring.

---

### 2.10 Verifier masih keyword-based

Verifier belum benar-benar memahami entailment.

Risiko:

- jawaban salah tetapi banyak kata cocok bisa dianggap supported;
- jawaban benar tetapi paraphrase bisa mendapat score rendah;
- abstention dapat terlihat unsupported walaupun aman.

Belum selesai:

- claim extraction;
- evidence alignment per claim;
- contradiction detection;
- optional LLM judge active test;
- numeric consistency check.

---

### 2.11 Test suite formal belum ada

Sudah ada benchmark script:

```text
app/model_smoke_bench.py
app/rag_regression_bench.py
```

Belum selesai:

```text
tests/test_router.py
tests/test_parser.py
tests/test_chunking.py
tests/test_retrieval.py
tests/test_compressor.py
tests/test_verifier.py
tests/test_quality.py
tests/test_model_client.py
tests/test_rag_regression.py
```

---

### 2.12 Belum ada CLI terpadu

Saat ini command masih tersebar.

Belum selesai:

```bash
raglocal ingest
raglocal ask "query"
raglocal evidence "query"
raglocal quality-report
raglocal model-validate
raglocal bench-model
raglocal bench-rag
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
- `rag_regression_bench.py`

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

### 3.4 Acronym drift pada RAG

Pastikan model tidak menafsirkan RAG sebagai istilah lain seperti:

```text
Relational Algebra for Graphs
Relevance, Accuracy, and Grit
```

RAG dalam proyek ini harus berarti:

```text
Retrieval-Augmented Generation berbasis dokumen lokal
```

---

## 4. Prioritas Berikutnya

Urutan paling aman:

1. rapikan dokumentasi baseline v2.1;
2. commit `answer_evaluator.py`, `model_smoke_bench.py`, dan `rag_regression_bench.py`;
3. bersihkan output benchmark/evidence/answer yang tidak perlu dikomit;
4. dokumentasikan Qwen judge integration test yang sudah lulus;
5. finalisasi audit verifier behavior;
6. perluas issue tags untuk semantic drift dan numeric hallucination;
7. buat quality_good_answers collection;
8. desain deterministic refiner;
9. mulai parser DOCX/XLSX/PPTX setelah regression baseline stabil.

---

## 5. Definisi Selesai untuk Tahap Berikutnya

Tahap Qwen judge dianggap selesai jika:

- Qwen judge bisa diaktifkan melalui `.env`;
- local verifier tetap berjalan;
- verdict Qwen judge tersimpan di `answer_verification_runs`;
- jika Qwen judge gagal, pipeline fallback ke local verifier;
- `rag_regression_bench` tetap lulus;
- quality report tetap bersih.

Tahap quality memory dianggap selesai jika:

- feedback bisa menyimpan label, note, dan corrected answer;
- jawaban bagus bisa dipromosikan ke `quality_good_answers`;
- prompt bisa mengambil contoh jawaban bagus;
- contoh jawaban tidak dijadikan sumber fakta;
- regression benchmark tidak menurun.

---

## 6. Catatan Strategis

Menambah model kecil memang membutuhkan banyak komponen pendukung. Namun ini bukan kelemahan semata. Dengan pipeline ini, sistem menjadi:

- lebih hemat resource;
- lebih dapat diaudit;
- tidak terlalu bergantung pada model besar;
- bisa diperbaiki bertahap melalui quality memory;
- siap dibandingkan dengan model 4B;
- dapat diuji ulang melalui benchmark lokal.

Baseline v2.1 harus diperlakukan sebagai titik stabil sebelum menambah fitur baru. Perubahan berikutnya sebaiknya kecil, terukur, dan selalu diuji dengan `model_smoke_bench` serta `rag_regression_bench`.
