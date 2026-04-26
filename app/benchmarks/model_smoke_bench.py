from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from time import perf_counter

from app.config import settings
from app.llm.clients import get_llm_client


@dataclass
class BenchCase:
    name: str
    system: str
    user: str
    expected_all: list[str] = field(default_factory=list)
    expected_any: list[str] = field(default_factory=list)
    forbidden_any: list[str] = field(default_factory=list)
    exact_text: str | None = None
    known_risk: str | None = None


CASES = [
    BenchCase(
        name="instruction_ok",
        system="Jawab hanya dengan teks: OK. Jangan tambah penjelasan.",
        user="Tes koneksi.",
        exact_text="OK",
    ),
    BenchCase(
        name="arithmetic_known_weakness",
        system="Jawab hanya angka akhir. Jangan tampilkan langkah.",
        user="17 * 23 = ?",
        expected_all=["391"],
        forbidden_any=["401", "481"],
        known_risk="LLM lokal kecil tidak boleh dipercaya untuk kalkulasi tanpa tool deterministik.",
    ),
    BenchCase(
        name="context_grounding_magika_chroma",
        system=(
            "Konteks proyek: Magika adalah file router. "
            "FastEmbed adalah embedder. "
            "Chroma adalah vector database. "
            "Jawab hanya berdasarkan konteks ini. Jangan memakai pengetahuan luar."
        ),
        user="Apa fungsi Magika dan Chroma?",
        expected_all=["magika", "file router", "chroma", "vector database"],
        forbidden_any=["magika adalah embedder", "chroma adalah parser"],
    ),
    BenchCase(
        name="rag_acronym_safety",
        system=(
            "Dalam konteks proyek ini, RAG berarti Retrieval Augmented Generation "
            "berbasis dokumen lokal. Jangan gunakan arti lain dari singkatan RAG."
        ),
        user="Sebutkan dua komponen RAG lokal.",
        expected_any=["retrieval", "dokumen", "embedding", "vector", "database", "chroma"],
        forbidden_any=[
            "Relational Algebra",
            "Relational Algebra for Graphs",
            "Vertex Set",
            "Edge Set",
            "analisis graf",
            "topologis",
        ],
    ),
    BenchCase(
        name="anti_artifact_labels",
        system=(
            "Jawab langsung isi jawaban. Jangan menulis label seperti "
            "SYSTEM, USER, PROMPT, INSTRUKSI, EVIDENCE, atau CONTEXT."
        ),
        user="Sebutkan dua komponen RAG lokal.",
        expected_any=["dokumen", "retrieval", "embedding", "vector", "database", "model"],
        forbidden_any=["SYSTEM", "USER", "PROMPT", "INSTRUKSI", "EVIDENCE", "CONTEXT"],
    ),
]


def normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def case_passed(case: BenchCase, text: str) -> bool:
    normalized = normalize(text)

    if case.exact_text is not None:
        cleaned = text.strip().rstrip(".")
        if cleaned.lower() != case.exact_text.lower():
            return False

    for token in case.expected_all:
        if token.lower() not in normalized:
            return False

    if case.expected_any:
        if not any(token.lower() in normalized for token in case.expected_any):
            return False

    for token in case.forbidden_any:
        if token.lower() in normalized:
            return False

    return True


def main() -> None:
    client = get_llm_client()
    output_dir = Path("data/quality")
    output_dir.mkdir(parents=True, exist_ok=True)

    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = output_dir / f"model_smoke_bench-{settings.model_mode}-{run_id}.json"

    results = []

    print("Model smoke benchmark")
    print(f"mode      = {settings.model_mode}")
    print(f"model     = {settings.ollama_model}")
    print(f"provider  = {settings.llm_provider}")
    print(f"temp      = {settings.llm_temperature}")
    print(f"max_tokens= {settings.llm_max_tokens}")
    print("-" * 80)

    for case in CASES:
        t0 = perf_counter()
        result = client.generate(case.system, case.user)
        elapsed = perf_counter() - t0

        text = result.text.strip()
        passed = case_passed(case, text)

        raw = result.raw or {}
        eval_count = raw.get("eval_count")
        eval_duration = raw.get("eval_duration")

        tok_per_sec = None
        if eval_count and eval_duration:
            tok_per_sec = eval_count / (eval_duration / 1_000_000_000)

        row = {
            "case": asdict(case),
            "mode": settings.model_mode,
            "configured_model": settings.ollama_model,
            "actual_model": result.model,
            "elapsed_sec": round(elapsed, 4),
            "eval_count": eval_count,
            "tok_per_sec": round(tok_per_sec, 4) if tok_per_sec else None,
            "passed": passed,
            "text": text,
        }
        results.append(row)

        print(f"CASE={case.name}")
        print(f"actual_model={result.model}")
        print(f"elapsed_sec={elapsed:.2f}")
        print(f"eval_count={eval_count}")
        print(f"tok_per_sec={tok_per_sec:.2f}" if tok_per_sec else "tok_per_sec=None")
        print(f"pass={passed}")
        if case.known_risk:
            print(f"known_risk={case.known_risk}")
        print("text=", text[:700].replace("\n", " "))
        print("-" * 80)

    summary = {
        "run_id": run_id,
        "mode": settings.model_mode,
        "configured_model": settings.ollama_model,
        "provider": settings.llm_provider,
        "temperature": settings.llm_temperature,
        "max_tokens": settings.llm_max_tokens,
        "passed": sum(1 for r in results if r["passed"]),
        "total": len(results),
        "results": results,
    }

    output_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"SUMMARY: {summary['passed']}/{summary['total']} passed")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()