# Answer: apa isi dokumen tentang <istilah unik yang pasti ada>

## Jawaban

Dokumen tentang RAG lokal adalah sistem retrieval augmented generation berbasis dokumen lokal. Proyek ini menggunakan Magika sebagai file router, OpenDataLoader PDF sebagai parser PDF, FastEmbed sebagai embedder, dan Chroma sebagai vector database. Pipeline utama adalah file masuk, deteksi tipe file, parsing, chunking, embedding, penyimpanan ke Chroma, retrieval, lalu jawaban dari model Qwen. Mini Graph Layer digunakan untuk memetakan hubungan antara dokumen, chunk, parser, filetype, dan term penting. (sumber: project-notes.md, chunk 0)

## Verifikasi

- Final supported: True
- Verifier mode: local_only
- Local support ratio: 0.8913
- Qwen judge available: False
- Qwen judge supported: None
- Qwen judge confidence: 0.0
- Fallback used: False

## Provider

- Provider: ollama
- Model: qwen-rag-1.5b:latest