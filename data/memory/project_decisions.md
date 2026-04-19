# Project Decisions


## 2026-04-18T10:54:43.973415+00:00

- Runtime awal difokuskan pada parser, embedder, Chroma, FTS5, Mini Graph, dan Context Compressor.
- Model Qwen general belum disambungkan sampai evidence pack stabil.
- SQLite FTS5 dipakai sebagai keyword/BM25 retrieval ringan.
- Context Compressor dipakai untuk mengurangi raw context sebelum dikirim ke LLM.

## 2026-04-18T10:56:12.791821+00:00

- Runtime awal difokuskan pada parser, embedder, Chroma, FTS5, Mini Graph, dan Context Compressor.
- Model Qwen general belum disambungkan sampai evidence pack stabil.
- SQLite FTS5 dipakai sebagai keyword/BM25 retrieval ringan.
- Context Compressor dipakai untuk mengurangi raw context sebelum dikirim ke LLM.
