from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class RagCase:
    name: str
    query: str
    expected_all: list[str] = field(default_factory=list)
    expected_any: list[str] = field(default_factory=list)
    forbidden_any: list[str] = field(default_factory=list)


CASES = [
    RagCase(
        name="positive_magika_chroma",
        query="Apa fungsi Magika dan Chroma dalam pipeline RAG lokal ini?",
        expected_all=["magika", "file router", "chroma", "vector database"],
        forbidden_any=[
            "magika adalah embedder",
            "chroma adalah parser",
            "relational algebra",
            "vertex set",
            "edge set",
        ],
    ),
    RagCase(
        name="false_premise_chroma_parser",
        query="Apakah Chroma adalah parser PDF?",
        expected_all=["chroma bukan parser", "vector database"],
        expected_any=["opendataloader", "parser pdf"],
        forbidden_any=[
            "chroma adalah parser pdf",
            "chroma merupakan parser pdf",
            "chroma digunakan sebagai parser pdf",
        ],
    ),
    RagCase(
        name="positive_pipeline_order",
        query="Sebutkan urutan pipeline utama dalam proyek RAG lokal ini.",
        expected_any=["deteksi tipe", "parsing", "chunking", "embedding", "chroma", "retrieval"],
        forbidden_any=[
            "relational algebra",
            "vertex set",
            "edge set",
            "relevance accuracy grit",
        ],
    ),
    RagCase(
        name="out_of_scope_guard",
        query="Siapa presiden Indonesia saat ini menurut dokumen proyek ini?",
        expected_any=[
            "dokumen belum cukup",
            "evidence belum cukup",
            "tidak cukup",
            "tidak tersedia",
            "tidak ditemukan",
            "tidak ada informasi",
            "tidak ada data",
            "tidak memuat informasi",
        ],
        forbidden_any=[
            "presiden indonesia adalah",
            "prabowo",
            "joko widodo",
            "jokowi",
        ],
    ),
        RagCase(
        name="calculator_arithmetic_tool",
        query="17 * 23 = ?",
        expected_all=["391"],
        forbidden_any=["401", "481"],
    ),
        RagCase(
        name="calculator_power_tool",
        query="2^8 = ?",
        expected_all=["256"],
        forbidden_any=["dokumen belum cukup", "tidak cukup", "401", "481"],
    ),
]


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def extract_answer(stdout: str) -> str:
    match = re.search(
        r"Answer\s+(.*?)(?:\nVerification|\nQuality|\nSaved answer JSON|$)",
        stdout,
        flags=re.DOTALL,
    )
    if not match:
        return stdout.strip()
    return match.group(1).strip()


def extract_quality(stdout: str) -> dict:
    artifact_like = None
    quality_pass = None
    quality_score = None

    artifact_match = re.search(r"'artifact_like':\s*(True|False)", stdout)
    if artifact_match:
        artifact_like = artifact_match.group(1) == "True"

    pass_match = re.search(r"'quality_pass':\s*(True|False)", stdout)
    if pass_match:
        quality_pass = pass_match.group(1) == "True"

    score_match = re.search(r"'quality_score':\s*([0-9.]+)", stdout)
    if score_match:
        quality_score = float(score_match.group(1))

    return {
        "artifact_like": artifact_like,
        "quality_pass": quality_pass,
        "quality_score": quality_score,
    }


def passed(case: RagCase, answer: str, stdout: str) -> tuple[bool, list[str]]:
    failures: list[str] = []
    text = normalize(answer)

    for token in case.expected_all:
        if token.lower() not in text:
            failures.append(f"missing expected_all: {token}")

    if case.expected_any:
        if not any(token.lower() in text for token in case.expected_any):
            failures.append(f"missing expected_any: {case.expected_any}")

    for token in case.forbidden_any:
        if token.lower() in text:
            failures.append(f"contains forbidden_any: {token}")

    if "'artifact_like': True" in stdout:
        failures.append("artifact_like=True")

    return len(failures) == 0, failures


def run_case(case: RagCase) -> dict:
    completed = subprocess.run(
        [sys.executable, "-m", "app.answer_query", case.query],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=os.environ.copy(),
    )

    answer = extract_answer(completed.stdout)
    quality = extract_quality(completed.stdout)
    ok, failures = passed(case, answer, completed.stdout)

    return {
        "case": asdict(case),
        "returncode": completed.returncode,
        "passed": ok and completed.returncode == 0,
        "failures": failures,
        "answer": answer,
        "quality": quality,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def main() -> None:
    output_dir = Path("data/quality")
    output_dir.mkdir(parents=True, exist_ok=True)

    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    mode = os.getenv("RAG_MODEL_MODE", "")
    output_path = output_dir / f"rag_regression_bench-{mode or 'env'}-{run_id}.json"

    print("RAG regression benchmark")
    print(f"RAG_MODEL_MODE={os.getenv('RAG_MODEL_MODE')}")
    print(f"RAG_QWEN_JUDGE_ENABLED={os.getenv('RAG_QWEN_JUDGE_ENABLED')}")
    print(f"RAG_VERIFICATION_AUDIT_ENABLED={os.getenv('RAG_VERIFICATION_AUDIT_ENABLED')}")
    print("-" * 80)

    results = []

    for case in CASES:
        result = run_case(case)
        results.append(result)

        print(f"CASE={case.name}")
        print(f"query={case.query}")
        print(f"returncode={result['returncode']}")
        print(f"pass={result['passed']}")
        print(f"quality={result['quality']}")
        if result["failures"]:
            print("failures=", result["failures"])
        print("answer=", result["answer"][:700].replace("\n", " "))
        print("-" * 80)

    summary = {
        "run_id": run_id,
        "mode": mode,
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