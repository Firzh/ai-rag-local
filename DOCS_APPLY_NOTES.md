# Docs Apply Notes — v2.2

## Overwrite Current MD Files

If you download and extract `docs_v2_2_md_bundle.zip` in the repository root:

```bash
unzip docs_v2_2_md_bundle.zip -d _docs_v2_2
cp _docs_v2_2/docs_v2_2/README.md README.md
cp _docs_v2_2/docs_v2_2/DEVELOPMENT_PLAN.md DEVELOPMENT_PLAN.md
cp _docs_v2_2/docs_v2_2/SPECIFICATION.md SPECIFICATION.md
cp _docs_v2_2/docs_v2_2/UNFINISHED.md UNFINISHED.md
cp _docs_v2_2/docs_v2_2/CHANGELOG.md CHANGELOG.md
```

If you download the standalone files into the repository root:

```bash
cp README_v2_2.md README.md
cp DEVELOPMENT_PLAN_v2_2.md DEVELOPMENT_PLAN.md
cp SPECIFICATION_v2_2.md SPECIFICATION.md
cp UNFINISHED_v2_2.md UNFINISHED.md
cp CHANGELOG_v2_2.md CHANGELOG.md
```

## Cleanup Generated Outputs

```bash
rm -f data/quality/rag_regression_bench-general-*.json
rm -f data/quality/model_smoke_bench-*.json

rm -f data/answers/17_23.answer.json
rm -f data/answers/17_23.answer.md
rm -f data/answers/2_8.answer.json
rm -f data/answers/2_8.answer.md
rm -f data/answers/apa_fungsi_magika_dan_chroma_dalam_pipeline_rag_lokal_ini.answer.json
rm -f data/answers/apa_fungsi_magika_dan_chroma_dalam_pipeline_rag_lokal_ini.answer.md
rm -f data/answers/apakah_chroma_adalah_parser_pdf.answer.json
rm -f data/answers/apakah_chroma_adalah_parser_pdf.answer.md
rm -f data/answers/sebutkan_urutan_pipeline_utama_dalam_proyek_rag_lokal_ini.answer.json
rm -f data/answers/sebutkan_urutan_pipeline_utama_dalam_proyek_rag_lokal_ini.answer.md
rm -f data/answers/siapa_presiden_indonesia_saat_ini_menurut_dokumen_proyek_ini.answer.json
rm -f data/answers/siapa_presiden_indonesia_saat_ini_menurut_dokumen_proyek_ini.answer.md

rm -f data/evidence/apa_fungsi_magika_dan_chroma_dalam_pipeline_rag_lokal_ini.evidence.json
rm -f data/evidence/apakah_chroma_adalah_parser_pdf.evidence.json
rm -f data/evidence/sebutkan_urutan_pipeline_utama_dalam_proyek_rag_lokal_ini.evidence.json
rm -f data/evidence/siapa_presiden_indonesia_saat_ini_menurut_dokumen_proyek_ini.evidence.json
```

## Expected Git Status Before Commit

```text
M  README.md
M  DEVELOPMENT_PLAN.md
M  SPECIFICATION.md
M  UNFINISHED.md
M  CHANGELOG.md
M  app/answer_query.py
M  app/rag_regression_bench.py
A  app/math_guard.py
A  app/tools/__init__.py
A  app/tools/calculator.py
```

## Final Sanity Test

```bash
export RAG_MODEL_MODE=general
export RAG_LLM_PROVIDER=ollama
export RAG_QWEN_JUDGE_ENABLED=false
export RAG_VERIFICATION_AUDIT_ENABLED=false

python -m compileall app
python -m app.answer_query "17 * 23 = ?"
python -m app.answer_query "2^8 = ?"
python -m app.rag_regression_bench
```

Expected:

```text
Hasil 17*23 = 391.
Hasil 2**8 = 256.
SUMMARY: 6/6 passed
```

## Commit

```bash
git add README.md DEVELOPMENT_PLAN.md SPECIFICATION.md UNFINISHED.md CHANGELOG.md
git add app/answer_query.py app/rag_regression_bench.py app/math_guard.py app/tools/__init__.py app/tools/calculator.py

git commit -m "Add v2.2 calculator tool and Gemini API foundation"
```
