from __future__ import annotations


def build_system_prompt() -> str:
    return (
        "Anda adalah asisten RAG lokal. "
        "Jawab hanya berdasarkan evidence pack. "
        "Jangan memakai pengetahuan luar. "
        "Jangan mengulang kalimat. "
        "Gunakan Bahasa Indonesia yang singkat, jelas, dan langsung."
    )


def build_user_prompt(evidence_context: str) -> str:
    return (
        f"{evidence_context}\n\n"
        "Format jawaban akhir:\n"
        "- Tulis jawaban dalam 1 paragraf singkat.\n"
        "- Jangan menyalin label seperti 'Fakta penting', 'Kutipan pendek penting', atau 'Sumber relevan'.\n"
        "- Sertakan sumber dengan format: (sumber: nama_file, chunk x).\n"
        "- Jangan menulis kesimpulan yang bertentangan dengan status evidence.\n"
    )