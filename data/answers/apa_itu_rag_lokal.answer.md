# Answer: apa itu RAG lokal?

## Jawaban

RAG lokal adalah sistem retrieval augmented generation berbasis dokumen lokal. Proyek ini menggunakan Magika sebagai file router, OpenDataLoader PDF sebagai parser PDF, FastEmbed sebagai embedder, dan Chroma sebagai vector database. Pipeline utama mengikuti file masuk, deteksi tipe file, parsing, chunking, embedding, penyimpanan ke Chroma, retrieval, lalu jawaban dari model Qwen. (sumber: test-rag.txt, chunk 0)

## Verifikasi

- Supported: True
- Support ratio: 0.8857

## Provider

- Provider: ollama
- Model: qwen-rag-1.5b:latest