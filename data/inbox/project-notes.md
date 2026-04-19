# AI RAG Lokal

Proyek ini memakai Magika sebagai file router, OpenDataLoader PDF sebagai parser PDF, FastEmbed sebagai embedder, dan Chroma sebagai vector database.

Pipeline utama adalah file masuk, deteksi tipe file, parsing, chunking, embedding, penyimpanan ke Chroma, retrieval, lalu jawaban dari model Qwen.

Mini Graph Layer digunakan untuk memetakan hubungan antara dokumen, chunk, parser, filetype, dan term penting.
