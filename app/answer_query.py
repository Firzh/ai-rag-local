from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console

from app.config import settings
from app.compression.context_compressor import ContextCompressor
from app.prompt_builder import build_system_prompt, build_user_prompt
from app.llm.clients import get_llm_client, LLMClientError
from app.verification.verifier import EvidenceVerifier
from app.verification.llm_judge import QwenJudgeVerifier
from app.verification.combined_verifier import combine_verification_results
from app.answer_postprocess import clean_answer
from app.extractive_answer import build_extractive_answer
from app.answer_quality import is_answer_artifact_like
from app.answer_evaluator import evaluate_answer_quality
from app.quality_store import AnswerQualityStore


console = Console()


def safe_filename(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_\-]+", "_", text.lower())
    cleaned = cleaned.strip("_")
    return cleaned[:80] or "answer"


def save_answer_record(record: dict) -> tuple[Path, Path]:
    settings.answers_dir.mkdir(parents=True, exist_ok=True)

    base = safe_filename(record["query"])
    json_path = settings.answers_dir / f"{base}.answer.json"
    md_path = settings.answers_dir / f"{base}.answer.md"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)

    local_verification = record["verification"].get("local", {})
    llm_judge = record["verification"].get("llm_judge", {})

    lines = []
    lines.append(f"# Answer: {record['query']}")
    lines.append("")
    lines.append("## Jawaban")
    lines.append("")
    lines.append(record["answer"])
    lines.append("")
    lines.append("## Verifikasi")
    lines.append("")
    lines.append(f"- Final supported: {record['verification'].get('supported')}")
    lines.append(f"- Verifier mode: {record['verification'].get('verifier_mode')}")
    lines.append(f"- Local support ratio: {local_verification.get('support_ratio')}")
    lines.append(f"- Qwen judge available: {llm_judge.get('available')}")
    lines.append(f"- Qwen judge supported: {llm_judge.get('supported')}")
    lines.append(f"- Qwen judge confidence: {llm_judge.get('confidence')}")
    lines.append(f"- Fallback used: {record['verification'].get('fallback_used', False)}")
    lines.append("")
    lines.append("## Provider")
    lines.append("")
    lines.append(f"- Provider: {record['llm_provider']}")
    lines.append(f"- Model: {record['llm_model']}")

    md_path.write_text("\n".join(lines), encoding="utf-8")

    return json_path, md_path


def run_fallback_if_needed(
    query: str,
    answer: str,
    evidence_pack: dict,
    verifier: EvidenceVerifier,
) -> tuple[str, dict]:
    local_verification = verifier.verify_answer(answer, evidence_pack)
    artifact_like = is_answer_artifact_like(answer, query)

    if not settings.use_extractive_fallback:
        return answer, local_verification

    if local_verification.get("supported") and not artifact_like:
        return answer, local_verification

    fallback_answer = build_extractive_answer(evidence_pack)
    fallback_answer = clean_answer(fallback_answer, evidence_pack=evidence_pack)
    fallback_verification = verifier.verify_answer(fallback_answer, evidence_pack)

    if fallback_verification.get("supported"):
        fallback_verification = {
            **fallback_verification,
            "fallback_used": True,
            "fallback_reason": "LLM answer unsupported or artifact-like. Extractive fallback selected.",
        }
        return fallback_answer, fallback_verification

    return answer, local_verification


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="*", help="Pertanyaan pengguna")
    parser.add_argument("--dry-run", action="store_true", help="Hanya tampilkan prompt tanpa memanggil LLM")
    args = parser.parse_args()

    query = " ".join(args.query).strip()

    if not query:
        console.print('[yellow]Gunakan:[/yellow] python -m app.answer_query "pertanyaan Anda"')
        return

    compressor = ContextCompressor()
    evidence_pack = compressor.build_evidence_pack(query)
    evidence_path = compressor.save_evidence_pack(evidence_pack)
    evidence_context = compressor.to_prompt_context(evidence_pack)

    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(evidence_context)

    console.print(f"\n[bold]Query:[/bold] {query}")
    console.print(f"[green]Evidence saved:[/green] {evidence_path}")

    if args.dry_run:
        console.print("\n[bold cyan]SYSTEM PROMPT[/bold cyan]\n")
        console.print(system_prompt)
        console.print("\n[bold cyan]USER PROMPT[/bold cyan]\n")
        console.print(user_prompt)
        return

    try:
        client = get_llm_client()
        result = client.generate(system_prompt=system_prompt, user_prompt=user_prompt)
    except LLMClientError as exc:
        console.print(f"[red]LLM error:[/red] {exc}")
        console.print("\n[yellow]Gunakan --dry-run untuk cek prompt tanpa memanggil model.[/yellow]")
        return

    verifier = EvidenceVerifier()
    llm_judge = QwenJudgeVerifier()

    cleaned_answer = clean_answer(result.text, evidence_pack=evidence_pack)
    final_answer, local_verification = run_fallback_if_needed(
        query=query,
        answer=cleaned_answer,
        evidence_pack=evidence_pack,
        verifier=verifier,
    )

    llm_verification = llm_judge.verify_answer(
        query=query,
        answer=final_answer,
        evidence_pack=evidence_pack,
    )

    verification = combine_verification_results(
        local_verification=local_verification,
        llm_verification=llm_verification,
    )

    quality = evaluate_answer_quality(
        query=query,
        answer=final_answer,
        verification=verification,
    )

    quality_id = None
    if settings.enable_quality_store:
        quality_store = AnswerQualityStore()
        quality_id = quality_store.insert_answer_record(
            query=query,
            answer=final_answer,
            evidence_path=str(evidence_path),
            verification=verification,
            artifact_like=quality["artifact_like"],
            quality_score=quality["quality_score"],
            issue_tags=quality["issue_tags"],
            metadata={
                "llm_provider": result.provider,
                "llm_model": result.model,
                "raw_answer_preview": result.text[:500],
                "qwen_judge_enabled": settings.qwen_judge_enabled,
            },
        )

        if settings.verification_audit_enabled:
            quality_store.insert_verification_run(
                query=query,
                answer=final_answer,
                verifier_name="local_keyword_verifier",
                verdict=local_verification,
                answer_quality_id=quality_id,
                metadata={
                    "stage": "final",
                    "fallback_used": bool(local_verification.get("fallback_used", False)),
                },
            )
            quality_store.insert_verification_run(
                query=query,
                answer=final_answer,
                verifier_name="qwen_judge",
                verdict=llm_verification,
                answer_quality_id=quality_id,
                metadata={
                    "stage": "final",
                    "enabled": settings.qwen_judge_enabled,
                },
            )

    record = {
        "query": query,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "answer": final_answer,
        "raw_answer": result.text,
        "verification": verification,
        "evidence_path": str(evidence_path),
        "evidence_pack": evidence_pack,
        "llm_provider": result.provider,
        "llm_model": result.model,
        "quality": quality,
        "quality_id": quality_id,
    }

    json_path, md_path = save_answer_record(record)

    console.print("\n[bold green]Answer[/bold green]\n")
    console.print(final_answer)

    console.print("\n[bold]Verification[/bold]")
    console.print(verification)

    console.print("\n[bold]Quality[/bold]")
    console.print(quality)
    if quality_id is not None:
        console.print(f"[green]Quality record ID:[/green] {quality_id}")

    console.print(f"\n[green]Saved answer JSON:[/green] {json_path}")
    console.print(f"[green]Saved answer MD:[/green] {md_path}")


if __name__ == "__main__":
    main()
