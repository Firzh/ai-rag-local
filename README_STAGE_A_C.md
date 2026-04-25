Patch tahap A-C untuk ai-rag-local

Isi patch:
1. Perbaikan urutan final-save di app/answer_query.py
2. Audit verifier baru di SQLite melalui table answer_verification_runs dan quality_promotions
3. Semantic verifier opsional berbasis Qwen API melalui app/verification/llm_judge.py
4. Aggregator hybrid verifier di app/verification/combined_verifier.py
5. Tambahan konfigurasi env untuk Qwen judge dan audit verifier

Catatan implementasi:
- Generator utama tetap baseline lama. Qwen judge default OFF.
- Verdict hybrid bersifat strict saat Qwen judge aktif: local supported AND qwen supported.
- Jika Qwen judge nonaktif atau gagal dihubungi, pipeline jatuh kembali ke local verifier.
- Collection quality_good_answers belum dibuat pada tahap ini. Itu masuk tahap berikutnya.

Cara pakai singkat:
1. Salin file patch ke repo.
2. Tambahkan env dari env_qwen_patch.sample ke .env Anda.
3. Aktifkan Qwen judge jika endpoint sudah siap.
4. Jalankan smoke test ask seperti biasa.
