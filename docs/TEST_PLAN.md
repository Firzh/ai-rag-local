# TEST_PLAN.md — ai-rag-local

Tanggal update: 2026-05-09
Target repo: `Firzh/ai-rag-local` / `rag-lc`

Dokumen ini mendefinisikan test yang perlu dijaga saat mengembangkan parser, chunking, export, sandbox compare, graph, compressor, dan promote guard.

## 1. Test baseline yang harus tetap berjalan

```bash
python -m pytest -q tests/test_pipeline_contract.py
```

Expected saat baseline L4:

```text
4 passed
```

Smoke tests yang perlu tetap tersedia:

```bash
python -m app.benchmarks.chunking_v2_smoke
python -m app.benchmarks.html_parser_smoke
python -m app.benchmarks.web_staging_smoke
python -m app.benchmarks.quality_gate_smoke
python -m app.benchmarks.l1_jsonl_export_smoke
python -m app.benchmarks.chroma_jsonl_export_smoke
```

Regression lokal:

```bash
export RAG_LLM_PROVIDER=ollama
export RAG_MODEL_MODE=general
export RAG_QWEN_JUDGE_ENABLED=false
export RAG_VERIFICATION_AUDIT_ENABLED=false
python -m app.rag_regression_bench
```

## 2. Test untuk L4a.1 Chunking boundary refinement

| Test | Tujuan |
|---|---|
| `test_chunk_not_start_mid_word` | Chunk tidak mulai dari tengah kata |
| `test_chunk_not_end_mid_word` | Chunk tidak berakhir di potongan kata |
| `test_title_only_chunk_filtered` | Title-only chunk tidak masuk export |
| `test_chunk_index_stable` | `chunk_index` tetap berurutan |
| `test_original_chunk_index_preserved` | Metadata transformasi tetap bisa dilacak |
| `test_overlap_not_duplicate_noise` | Overlap tidak membuat duplikasi berlebihan |

## 3. Test untuk L5 Sandbox Compare

| Test | Tujuan |
|---|---|
| `test_compare_loads_old_and_sandbox` | Dua collection bisa dibandingkan |
| `test_compare_uses_same_queries` | Old dan sandbox memakai query yang sama |
| `test_compare_reports_topk_overlap` | Overlap source/doc_id/chunk_index tercatat |
| `test_compare_flags_missing_metadata` | Metadata hilang menjadi warning/failure |
| `test_compare_flags_identity_query_failure` | Query angka/nama/tanggal gagal ditandai |
| `test_compare_outputs_failed_queries_jsonl` | Failed cases bisa diaudit |
| `test_compare_does_not_promote` | L5 tidak menulis ke Chroma utama |

## 4. Test untuk L6 Promote Guard

| Test | Tujuan |
|---|---|
| `test_promote_requires_compare_report` | Promote ditolak tanpa L5 report |
| `test_promote_requires_regression_pass` | Promote ditolak bila regression gagal |
| `test_promote_blocks_failed_identity_queries` | Query identity-critical gagal memblok promote |
| `test_promote_requires_owner_approval` | Promote butuh approval eksplisit |
| `test_promote_writes_manifest` | Promote menghasilkan manifest |
| `test_promote_has_rollback_plan` | Rollback metadata tersedia |

## 5. Test untuk Parser Guard

| Test | Skenario | Expected |
|---|---|---|
| `test_nav_footer_quarantined` | HTML navbar/footer | Tidak jadi evidence utama |
| `test_table_content_type_detected` | Tabel HTML/PDF | `content_type=table` |
| `test_low_trust_parser_warning` | Parser output kacau | `parser_untrusted` |
| `test_reference_not_main_evidence` | Daftar pustaka | Tidak dipakai kecuali query referensi |

## 6. Test untuk Identity Guard

| Test | Skenario | Expected |
|---|---|---|
| `test_numeric_chunk_identity_high` | Chunk berisi nominal/tahun | `identity_level=high` |
| `test_code_chunk_identity_high` | Chunk berisi env var/kode | `do_not_compress=true` |
| `test_identity_query_graph_off` | Query angka/tanggal | graph mati |
| `test_identity_query_exact_priority` | Query kode spesifik | FTS/exact diprioritaskan |

## 7. Test untuk Graph Guard

| Test | Skenario | Expected |
|---|---|---|
| `test_graph_off_for_numeric_query` | Query angka | graph mati |
| `test_graph_on_for_relational_query` | Query hubungan/alur | graph aktif terbatas |
| `test_graph_seed_low_score_rejected` | Seed lemah | graph tidak dipakai |
| `test_graph_cross_source_blocked` | Neighbor source berbeda | ditolak kecuali query lintas dokumen |
| `test_graph_noise_report_created` | Graph drop result | alasan tercatat |

## 8. Test untuk Compressor Guard

| Test | Skenario | Expected |
|---|---|---|
| `test_compressor_keeps_negation` | Kalimat berisi `tidak boleh` | negasi tidak hilang |
| `test_compressor_keeps_condition` | Kalimat berisi `hanya setelah` | syarat tetap ada |
| `test_compressor_keeps_neighbor_sentence` | Syarat di kalimat berikutnya | neighbor ikut masuk |
| `test_table_not_truncated_as_plain_text` | Tabel | header + row dijaga |
| `test_identity_chunk_no_prune` | Angka/tanggal/kode | no-prune |

## 9. Test untuk Evidence Sufficiency Gate

| Test | Skenario | Expected |
|---|---|---|
| `test_answer_blocked_when_evidence_weak` | Evidence kurang | tidak memaksa jawaban |
| `test_conflicting_evidence_flagged` | Dua sumber bertentangan | status conflicting |
| `test_parser_untrusted_blocks_final_claim` | Parser rendah | warning atau block |
| `test_graph_dependency_ratio_warning` | Evidence hanya dari graph | warning |
| `test_identity_match_required` | Query angka tetapi angka tidak muncul | jawaban ditahan |

## 10. Test untuk Kaggle handoff

| Test | Tujuan |
|---|---|
| `test_export_manifest_required` | Export tanpa manifest ditolak |
| `test_jsonl_minimum_contract` | `doc_id` + `text` diterima |
| `test_jsonl_recommended_metadata` | Metadata disimpan bila tersedia |
| `test_import_report_not_promote` | Report Kaggle tidak promote otomatis |
| `test_embedding_model_mismatch_rejected` | Model embedding mismatch ditandai |

## 11. Aturan maintenance test

Setiap fitur baru minimal menambah salah satu:

```text
unit test
smoke test
contract test
regression case
failed query fixture
```

Setiap 9 commit implementasi, commit ke-10 wajib memperbarui dokumen ini bila ada test baru, test berubah, atau coverage belum sinkron dengan fitur.

<!-- L4A1_BOUNDARY_REFINEMENT_START -->
## L4a.1 Chunking Boundary Contract Tests

Required checks for the L4a.1 patch:

```bash
python -m pytest -q tests/test_l4a1_chunk_boundary_contract.py -vv
python -m pytest -q tests/test_pipeline_contract.py
python -m app.benchmarks.chunking_v2_smoke
python -m app.benchmarks.l1_jsonl_export_smoke
git diff --check
```

Acceptance criteria:

- long paragraph chunks do not split synthetic `kataNNN` tokens;
- chunk metadata keeps sequential `chunk_index`;
- L1 export skips `title-only` chunks when body chunks exist;
- a single title-only document is not dropped;
- exported `chunk_index` remains sequential;
- `metadata.original_chunk_index` remains available after filtering;
- existing post-L4 pipeline contract tests still pass.
<!-- L4A1_BOUNDARY_REFINEMENT_END -->
