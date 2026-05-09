# RUNTIME_GUARDS.md — Parser, Identity, Graph, Compressor, and Evidence Guards

Tanggal update: 2026-05-09
Target repo: `Firzh/ai-rag-local` / `rag-lc`

Dokumen ini menjelaskan guard runtime yang perlu dibangun bertahap agar RAG tidak hanya mengambil teks yang mirip secara embedding, tetapi tetap menjaga identitas evidence.

## 1. Masalah yang ingin dicegah

RAG dapat gagal walaupun retrieval tampak berhasil karena:

```text
parser mengambil boilerplate
chunk kehilangan konteks
kata yang sama punya makna berbeda
graph memperluas seed yang salah
compressor memotong negasi atau syarat
evidence terlalu sedikit tetapi LLM tetap menjawab
metadata source hilang
angka/tanggal/nama berubah konteks
```

## 2. Parser Guard

### Tujuan

Menilai apakah chunk berasal dari parser yang cukup dipercaya.

### Metadata yang disarankan

```json
{
  "parser_trust_score": 0.82,
  "content_type": "paragraph|table|list|code|heading|reference|nav|footer|unknown",
  "is_boilerplate": false,
  "structure_score": 0.76,
  "parser_warnings": []
}
```

### Aturan awal

```text
nav/footer -> tidak menjadi evidence utama
table -> pakai table mode, jangan potong per kalimat
heading -> konteks, bukan evidence utama
reference -> hanya dipakai untuk query referensi
unknown + trust rendah -> evidence_status parser_untrusted
```

## 3. Chunk Identity Guard

### Tujuan

Melindungi chunk yang berisi fakta spesifik.

### Sinyal identity-critical

```text
angka
tanggal/tahun
nominal uang
kode/ID/env var
nama orang/organisasi
nomor pasal
versi/release
nilai konfigurasi
```

### Metadata yang disarankan

```json
{
  "identity_level": "low|medium|high",
  "has_numbers": true,
  "has_dates": true,
  "has_codes": false,
  "do_not_compress": true,
  "graph_expand_policy": "off|restricted|normal"
}
```

### Aturan awal

```text
identity_level=high -> no_prune
query angka/tanggal/kode -> graph off
query identitas -> FTS/exact lebih kuat
```

## 4. Retrieval Router

### Tujuan

Memilih mode retrieval berdasarkan jenis query.

| Query | Mode |
|---|---|
| angka/tanggal/kode | exact_first + graph_off |
| definisi | hybrid_balanced |
| relasi/alur/sebab-akibat | graph_relational terbatas |
| tabel | table_lookup |
| ringkasan | section_coverage |
| ambigu | conservative + warning |

## 5. Graph Guard

### Tujuan

Graph hanya dipakai saat graph benar-benar menambah evidence.

### Graph harus mati bila

```text
query mengandung angka spesifik
query mengandung tahun/tanggal
query mengandung kode/ID/pasal
seed score lemah
parser trust seed rendah
seed berasal dari source berbeda tanpa izin
query cukup dijawab oleh exact match
```

### Graph boleh aktif bila

```text
query meminta hubungan
query meminta alur pipeline
query meminta sebab-akibat
seed evidence kuat
metadata masih satu scope
hasil graph menambah fakta baru
```

### Output audit graph

```json
{
  "graph_used": true,
  "graph_seed_count": 3,
  "graph_added_count": 2,
  "graph_dropped_count": 5,
  "graph_drop_reasons": ["cross_source", "low_score"]
}
```

## 6. Compressor Guard

### Tujuan

Mencegah compressor menghilangkan syarat penting.

### Guard minimum

```text
negation_guard: jaga kalimat dengan tidak/bukan/kecuali
condition_guard: jaga kalimat dengan hanya/wajib/setelah/sebelum
neighbor_sentence_guard: ambil kalimat sebelum dan sesudah kalimat penting
table_guard: jangan potong tabel sebagai teks biasa
identity_guard: jangan pangkas angka/tanggal/kode
source_guard: pertahankan doc_id/source/chunk_index
```

### Contoh risiko

Tidak aman:

```text
Sistem boleh promote.
```

Aman:

```text
Sistem boleh promote hanya setelah compare lama-vs-baru dan regression lokal aman.
```

## 7. Evidence Sufficiency Gate

### Tujuan

Menentukan apakah evidence cukup untuk menjawab.

### Metrik minimum

```json
{
  "top_score": 0.71,
  "score_gap": 0.18,
  "evidence_count": 4,
  "source_count": 2,
  "parser_trust_min": 0.80,
  "identity_match": true,
  "graph_dependency_ratio": 0.25,
  "contradiction_flag": false,
  "evidence_status": "sufficient|weak|conflicting|parser_untrusted|compression_risky"
}
```

### Aturan jawaban

```text
evidence_status=sufficient -> jawab normal
evidence_status=weak -> jangan memaksa jawaban
evidence_status=conflicting -> tampilkan konflik
evidence_status=parser_untrusted -> beri warning atau minta re-parse
evidence_status=compression_risky -> pakai kutipan mentah lebih banyak
```

## 8. Geometry Audit sebagai risk label

Geometry audit tidak boleh langsung mengganti evidence asli. Untuk `ai-rag-local`, geometry cukup menjadi risk label:

```text
cluster_spread tinggi -> graph off / conservative compression
rho rendah -> jangan centroid
identity-critical cluster -> no_prune
small cluster -> jangan simpulkan geometri terlalu kuat
```

Full spectral experiment, visualisasi, dan GAC eksperimen besar masuk `rag-to-kaggle`, bukan runtime utama.

## 9. Urutan implementasi guard

```text
1. Identity Guard sederhana
2. Graph Guard untuk query identity-specific
3. Compressor Guard untuk negasi dan syarat
4. Evidence Sufficiency Gate
5. Parser Guard lanjutan
6. Retrieval Router intent-based
7. Geometry Audit risk labels
```

## 10. Aturan maintenance

Setiap guard baru harus menambah test case di `TEST_PLAN.md`. Setiap 9 commit implementasi, commit ke-10 wajib memperbarui dokumen ini.
