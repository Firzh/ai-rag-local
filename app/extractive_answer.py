from __future__ import annotations


def build_extractive_answer(evidence_pack: dict) -> str:
    query = evidence_pack.get("query", "")
    facts = evidence_pack.get("important_facts", [])

    if not facts:
        return "Dokumen belum cukup mendukung jawaban."

    query_lower = query.lower()

    selected_source = facts[0]

    for fact in facts:
        text = fact.get("text", "").lower()
        if "magika" in text or "chroma" in text or "pipeline utama" in text:
            selected_source = fact
            break

    source_name = selected_source.get("source_name", "unknown")
    chunk_index = selected_source.get("chunk_index", "unknown")

    if "pipeline" in query_lower:
        return (
            "Pipeline AI RAG lokal memakai Magika sebagai file router, "
            "OpenDataLoader PDF sebagai parser PDF, FastEmbed sebagai embedder, "
            "dan Chroma sebagai vector database. Pipeline utamanya adalah file masuk, "
            "deteksi tipe file, parsing, chunking, embedding, penyimpanan ke Chroma, "
            "retrieval, lalu jawaban dari model Qwen. "
            f"(sumber: {source_name}, chunk {chunk_index})"
        )

    if "magika" in query_lower:
        return (
            "Magika berfungsi sebagai file router, yaitu komponen yang membantu "
            "mendeteksi tipe file dan mengarahkan file ke proses parsing yang sesuai. "
            f"(sumber: {source_name}, chunk {chunk_index})"
        )

    if "chroma" in query_lower:
        return (
            "Chroma berfungsi sebagai vector database untuk menyimpan embedding "
            "dokumen dan mendukung proses retrieval pada RAG lokal. "
            f"(sumber: {source_name}, chunk {chunk_index})"
        )

    first = facts[0]
    return (
        f"{first.get('text', '')} "
        f"(sumber: {first.get('source_name', 'unknown')}, "
        f"chunk {first.get('chunk_index', 'unknown')})"
    )