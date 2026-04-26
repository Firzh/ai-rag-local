from app.memory.historian import Historian


def main() -> None:
    historian = Historian()

    historian.append_decision(
        """
- Runtime awal difokuskan pada parser, embedder, Chroma, FTS5, Mini Graph, dan Context Compressor.
- Model Qwen general belum disambungkan sampai evidence pack stabil.
- SQLite FTS5 dipakai sebagai keyword/BM25 retrieval ringan.
- Context Compressor dipakai untuk mengurangi raw context sebelum dikirim ke LLM.
"""
    )

    historian.append_rag_memory(
        """
Arsitektur saat ini:
File Router → Parser → Chunker → FastEmbed → Chroma → SQLite FTS5 → Mini Graph → Hybrid Retrieval → Reranker → Context Compressor → Evidence Pack → Verifier → LLM.
"""
    )

    print("Memory files updated.")


if __name__ == "__main__":
    main()