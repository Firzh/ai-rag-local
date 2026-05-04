# Anki Japanese Learning Integration for ai-rag-local

Dokumen ini menjelaskan pemasangan, import, verifikasi, dan penggunaan collection Anki di `ai-rag-local`.

Integrasi ini memakai alur:

```text
Anki-Japanese-Learning
→ export JSONL rag-ready
→ ai-rag-local
→ import ke Chroma collection khusus
→ query mode kanji, vocab, grammar, dan maturity
```

Collection Anki dibuat terpisah dari collection utama.

```text
anki_japanese_learning
```

Collection utama `rag_multilingual_minilm_l12_v2_384` tidak disentuh.

---

## 1. Struktur Folder

Struktur kerja yang dipakai:

```text
AI-Models/
├── Anki-Japanese-Learning/
│   └── data/
│       └── rag_ready/
│           └── anki_japanese_learning.jsonl
│
└── ai-rag-local/
    ├── app/
    │   ├── importers/
    │   │   ├── __init__.py
    │   │   └── jsonl_collection_importer.py
    │   └── commands/
    │       └── query_anki_collection.py
    ├── data/
    │   └── chroma/
    └── docs/
```

---

## 2. File yang Ditambahkan di `ai-rag-local`

File utama:

```text
app/importers/jsonl_collection_importer.py
app/importers/__init__.py
app/commands/query_anki_collection.py
```

Fungsi file:

| File | Fungsi |
|---|---|
| `app/importers/jsonl_collection_importer.py` | Import JSONL rag-ready ke Chroma collection khusus |
| `app/importers/__init__.py` | Menjadikan `app.importers` sebagai Python package |
| `app/commands/query_anki_collection.py` | Query collection Anki dengan mode `kanji`, `vocab`, `grammar`, dan `maturity` |

---

## 3. Prasyarat

Aktifkan environment `ai-rag-local`:

```bash
cd /f/AI-Models/ai-rag-local
source .venv/Scripts/activate
```

Pastikan file JSONL dari project Anki sudah ada:

```bash
ls ../Anki-Japanese-Learning/data/rag_ready/anki_japanese_learning.jsonl
```

File tersebut dibuat dari project:

```text
/f/AI-Models/Anki-Japanese-Learning
```

---

## 4. Validasi Importer

Cek command importer:

```bash
python -m app.importers.jsonl_collection_importer --help
```

Importer mendukung opsi berikut:

```text
--source
--collection
--persist-dir
--batch-size
--reset-collection
--dry-run
--list
--peek
--peek-limit
```

---

## 5. Dry Run Import

Dry run hanya memvalidasi file JSONL. Data belum ditulis ke Chroma.

```bash
python -m app.importers.jsonl_collection_importer \
  --source ../Anki-Japanese-Learning/data/rag_ready/anki_japanese_learning.jsonl \
  --collection anki_japanese_learning \
  --dry-run
```

Target hasil:

```text
OK Source JSONL valid
Records: 760
Target collection: anki_japanese_learning
DRY RUN selesai. Tidak ada data yang ditulis ke Chroma.
```

---

## 6. Import ke Collection Anki

Import pertama sebaiknya memakai `--reset-collection`.

Command ini hanya menghapus collection target `anki_japanese_learning`. Collection utama tidak disentuh.

```bash
python -m app.importers.jsonl_collection_importer \
  --source ../Anki-Japanese-Learning/data/rag_ready/anki_japanese_learning.jsonl \
  --collection anki_japanese_learning \
  --reset-collection
```

Target hasil:

```text
Import selesai.
Collection: anki_japanese_learning
Imported/upserted records: 760
Total records in collection: 760
```

---

## 7. Jika FastEmbed Error

Jika muncul error seperti:

```text
Local file sizes do not match the metadata
model_optimized.onnx failed. File doesn't exist
```

maka cache FastEmbed rusak atau download model tidak lengkap.

Hapus cache:

```bash
python - <<'PY'
import shutil
import tempfile
from pathlib import Path

cache = Path(tempfile.gettempdir()) / "fastembed_cache"
print("Deleting:", cache)
shutil.rmtree(cache, ignore_errors=True)
print("DONE")
PY
```

Test embedding ulang:

```bash
python - <<'PY'
from app.embeddings.fastembedder import FastEmbedder

embedder = FastEmbedder()
vec = embedder.embed_documents(["test embedding untuk anki japanese learning"])

print("EMBED OK")
print("Vector count:", len(vec))
print("Vector dimension:", len(vec[0]))
PY
```

Target:

```text
EMBED OK
Vector count: 1
Vector dimension: 384
```

Setelah itu, ulangi import.

---

## 8. Verifikasi Collection

List semua collection:

```bash
python -m app.importers.jsonl_collection_importer --list
```

Target:

```text
anki_japanese_learning             760
rag_multilingual_minilm_l12_v2_384   existing_count
```

Peek isi collection Anki:

```bash
python -m app.importers.jsonl_collection_importer \
  --collection anki_japanese_learning \
  --peek \
  --peek-limit 5
```

Target:

```text
Collection: anki_japanese_learning
Count: 760
```

---

## 9. Query Collection Anki

Gunakan command:

```bash
python -m app.commands.query_anki_collection
```

### 9.1 Summary

```bash
python -m app.commands.query_anki_collection --summary
```

### 9.2 Exact Lookup Kanji

```bash
python -m app.commands.query_anki_collection \
  --mode kanji \
  --expression 国 \
  --limit 5
```

Target:

```text
Expression: 国
Reading: コク
くに
Meaning: country
```

### 9.3 Semantic Search Kanji

```bash
python -m app.commands.query_anki_collection \
  --mode kanji \
  --query "国 country くに" \
  --limit 5
```

### 9.4 Semantic Search Vocab

```bash
python -m app.commands.query_anki_collection \
  --mode vocab \
  --query "foreign country" \
  --limit 5
```

Target atas biasanya:

```text
外国 / がいこく
Meaning: foreign country
```

### 9.5 Semantic Search Grammar

```bash
python -m app.commands.query_anki_collection \
  --mode grammar \
  --query "want to verb" \
  --limit 5
```

Untuk grammar pendek, exact lookup sering lebih stabil:

```bash
python -m app.commands.query_anki_collection \
  --mode grammar \
  --expression "〜たい" \
  --limit 5
```

### 9.6 Query Berdasarkan Maturity

Kartu baru:

```bash
python -m app.commands.query_anki_collection \
  --maturity new \
  --query "basic japanese vocabulary" \
  --limit 10
```

Vocab baru:

```bash
python -m app.commands.query_anki_collection \
  --mode vocab \
  --maturity new \
  --query "basic japanese vocabulary" \
  --limit 10
```

Kanji mature:

```bash
python -m app.commands.query_anki_collection \
  --mode kanji \
  --maturity mature \
  --query "basic japanese kanji" \
  --limit 10
```

---

## 10. Mode Query

| Mode | Metadata filter | Fungsi |
|---|---|---|
| `kanji` | `note_type = Kanji` | Cari kartu Kanji |
| `vocab` | `note_type = Word` | Cari kosakata |
| `word` | `note_type = Word` | Alias untuk `vocab` |
| `grammar` | `note_type = Grammar` | Cari pola grammar |
| `all` | tanpa note type filter | Cari semua data Anki |

---

## 11. Metadata Penting

Setiap record Chroma memiliki metadata:

```text
source
source_type
source_path
source_document_id
chroma_collection
deck
note_type
note_id
card_id
expression
reading
tags
maturity_level
maturity_score
interval_days
review_count
lapse_count
embedding_model
imported_at
```

Metadata ini dipakai untuk filter, audit, dan pembuatan latihan.

---

## 12. Re-export dari Anki

Jika data Anki berubah, lakukan export ulang dari folder `Anki-Japanese-Learning`:

```bash
cd /f/AI-Models/Anki-Japanese-Learning
source .venv/Scripts/activate

python scripts/run_pipeline.py \
  --manifest manifests/anki_japanese_n5_all.yaml \
  > logs/pipeline.log 2>&1

tail -n 80 logs/pipeline.log
```

Lalu kembali ke `ai-rag-local` untuk import ulang:

```bash
cd /f/AI-Models/ai-rag-local
source .venv/Scripts/activate

python -m app.importers.jsonl_collection_importer \
  --source ../Anki-Japanese-Learning/data/rag_ready/anki_japanese_learning.jsonl \
  --collection anki_japanese_learning \
  --reset-collection
```

---

## 13. Batasan Saat Ini

1. Collection Anki masih hanya berisi N5 all:
   - Kanji N5
   - Vocab N5
   - Grammar N5

2. Data vocab masih bisa terlihat panjang pada field `Expression`, karena source deck membawa komponen kanji dan maknanya.

3. Satu note Kanji bisa memiliki dua card, sehingga exact lookup dapat menampilkan dua record untuk kanji yang sama.

4. Query semantic grammar pendek kadang tidak menaruh pola target di Rank 1. Exact lookup lebih disarankan untuk grammar pattern yang sudah diketahui.

---

## 14. Command Aman untuk Commit

Cek status:

```bash
git status --short
```

Tambahkan hanya file Anki integration:

```bash
git add \
  app/importers/__init__.py \
  app/importers/jsonl_collection_importer.py \
  app/commands/query_anki_collection.py \
  docs/ANKI_JAPANESE_LEARNING_INTEGRATION.md
```

Jangan tambahkan data runtime:

```text
data/answers/
data/chroma/
data/cache/
```

Jangan tambahkan file lain yang bukan bagian Anki jika tidak ingin masuk commit ini:

```text
app/benchmarks/chroma_jsonl_export_smoke.py
app/commands/export_chroma_collection.py
app/exporters/chroma_jsonl_export.py
```

Commit:

```bash
git commit -m "feat(anki): add JSONL importer and query command"
```

Alternatif commit title:

```bash
git commit -m "feat(anki): import Anki JSONL into dedicated Chroma collection"
```

---

## 15. Ringkasan Operasional

Export dari Anki:

```bash
cd /f/AI-Models/Anki-Japanese-Learning
source .venv/Scripts/activate
python scripts/run_pipeline.py --manifest manifests/anki_japanese_n5_all.yaml
```

Import ke RAG:

```bash
cd /f/AI-Models/ai-rag-local
source .venv/Scripts/activate
python -m app.importers.jsonl_collection_importer \
  --source ../Anki-Japanese-Learning/data/rag_ready/anki_japanese_learning.jsonl \
  --collection anki_japanese_learning \
  --reset-collection
```

Query:

```bash
python -m app.commands.query_anki_collection \
  --mode kanji \
  --query "国 country くに" \
  --limit 5
```
