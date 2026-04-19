# Answer: bagaimana pipeline AI RAG lokal?

## Jawaban

Pipeline AI RAG lokal memakai Magika sebagai file router, OpenDataLoader PDF sebagai parser PDF, FastEmbed sebagai embedder, dan Chroma sebagai vector database. Pipeline utamanya adalah file masuk, deteksi tipe file, parsing, chunking, embedding, penyimpanan ke Chroma, retrieval, lalu jawaban dari model Qwen. (sumber: project-notes.md, chunk 0)

## Verifikasi

- Supported: True
- Support ratio: 0.8621

## Provider

- Provider: ollama
- Model: qwen-rag-1.5b:latest