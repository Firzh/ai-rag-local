from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console

from app.config import settings
from app.answer_postprocess import clean_answer
from app.answer_quality import is_answer_artifact_like
from app.answer_evaluator import evaluate_answer_quality
from app.cache.query_cache import QueryCache, query_hash
from app.compression.context_compressor import ContextCompressor
from app.extractive_answer import build_extractive_answer
from app.llm.clients import get_llm_client, LLMClientError, LLMProviderError
from app.llm.fallback_policy import try_ollama_fallback, human_action_message
from app.llm.provider_errors import ERROR_RATE_LIMITED
from app.math_guard import try_calculate_query
from app.prompt_builder import build_system_prompt, build_user_prompt
from app.quality_store import AnswerQualityStore
from app.usage.api_usage_store import ApiUsageStore
from app.verification.verifier import EvidenceVerifier
from app.verification.llm_judge import QwenJudgeVerifier
from app.verification.combined_verifier import combine_verification_results

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

def handle_calculator_query(query: str) -> bool:
    calc_result = try_calculate_query(query)

    if calc_result is None:
        return False

    final_answer = f"Hasil {calc_result.expression} = {calc_result.result}."

    verification = {
        "supported": True,
        "support_ratio": 1.0,
        "matched_terms": ["calculator", calc_result.expression, calc_result.result],
        "notes": ["Jawaban dihitung oleh deterministic calculator tool."],
        "verifier_mode": "tool_only",
        "local": {
            "supported": True,
            "support_ratio": 1.0,
            "matched_terms": ["calculator", calc_result.expression, calc_result.result],
            "notes": ["Deterministic calculator result."],
        },
        "llm_judge": {
            "verifier": "qwen_judge",
            "available": False,
            "supported": None,
            "confidence": 0.0,
            "notes": ["Qwen judge tidak digunakan untuk calculator tool."],
        },
        "tool": {
            "name": "safe_calculator",
            "expression": calc_result.expression,
            "result": calc_result.result,
        },
    }

    quality = {
        "artifact_like": False,
        "abstention_like": False,
        "issue_tags": [],
        "quality_score": 1.0,
        "quality_pass": True,
        "tool_used": "safe_calculator",
    }

    quality_id = None

    if settings.enable_quality_store:
        quality_store = AnswerQualityStore()
        quality_id = quality_store.insert_answer_record(
            query=query,
            answer=final_answer,
            evidence_path="",
            verification=verification,
            artifact_like=False,
            quality_score=1.0,
            issue_tags=[],
            metadata={
                "llm_provider": "tool",
                "llm_model": "safe_calculator",
                "tool_name": "safe_calculator",
                "expression": calc_result.expression,
                "result": calc_result.result,
            },
        )

        if settings.verification_audit_enabled:
            quality_store.insert_verification_run(
                query=query,
                answer=final_answer,
                verifier_name="deterministic_calculator",
                verdict=verification,
                answer_quality_id=quality_id,
                metadata={"stage": "tool", "tool_name": "safe_calculator"},
            )

    record = {
        "query": query,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "answer": final_answer,
        "raw_answer": final_answer,
        "verification": verification,
        "evidence_path": "",
        "evidence_pack": {},
        "llm_provider": "tool",
        "llm_model": "safe_calculator",
        "quality": quality,
        "quality_id": quality_id,
    }

    json_path, md_path = save_answer_record(record)

    console.print(f"\n[bold]Query:[/bold] {query}")
    console.print("[green]Tool used:[/green] safe_calculator")
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

    return True

def provider_error_to_dict(exc: LLMProviderError | None) -> dict | None:
    if exc is None:
        return None

    return {
        "provider": exc.info.provider,
        "model": exc.info.model,
        "error_type": exc.info.error_type,
        "status_code": exc.info.status_code,
        "message": exc.info.message,
        "raw_excerpt": exc.info.raw_excerpt,
    }


def print_provider_error(exc: LLMProviderError) -> None:
    console.print("\n[bold red]Provider API error[/bold red]")
    console.print(f"[yellow]Type:[/yellow] {exc.info.error_type}")
    console.print(f"[yellow]Status:[/yellow] {exc.info.status_code}")
    console.print(f"[yellow]Provider:[/yellow] {exc.info.provider}")
    console.print(f"[yellow]Model:[/yellow] {exc.info.model}")

    if settings.provider_error_verbose and exc.info.message:
        console.print(f"[yellow]Message:[/yellow] {exc.info.message}")

    console.print(f"[yellow]Action:[/yellow] {human_action_message(exc)}")

def active_usage_provider_model() -> tuple[str, str]:
    provider = settings.llm_provider.lower().strip()

    if provider == "openai_compatible":
        return "openai_compatible", settings.openai_compat_model

    if provider == "ollama":
        return "ollama", settings.ollama_model

    return provider, settings.ollama_model

def handle_cached_query(query: str) -> bool:
    if not settings.api_cache_enabled:
        return False

    cache = QueryCache()
    cached = cache.get(query)

    if cached is None:
        return False

    usage_provider, usage_model = active_usage_provider_model()

    ApiUsageStore().record_call(
        provider=usage_provider,
        model=usage_model,
        success=True,
        cache_hit=True,
        query_hash=query_hash(query),
        metadata={
            "source": "query_cache",
            "cached_provider": cached.provider,
            "cached_model": cached.model,
            "cache_created_at": cached.created_at,
            "cache_expires_at": cached.expires_at,
        },
    )

    record = {
        **cached.record,
        "query": query,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "cache_hit": True,
        "cache_provider": cached.provider,
        "cache_model": cached.model,
        "cache_counted_as_provider": usage_provider,
        "cache_counted_as_model": usage_model,
        "cache_created_at": cached.created_at,
        "cache_expires_at": cached.expires_at,
    }

    json_path, md_path = save_answer_record(record)

    console.print(f"\n[bold]Query:[/bold] {query}")
    console.print("[green]Cache hit:[/green] query_cache")
    console.print(f"[green]Cache counted as:[/green] {usage_provider} / {usage_model}")
    console.print("\n[bold green]Answer[/bold green]\n")
    console.print(cached.answer)
    console.print(f"\n[green]Saved answer JSON:[/green] {json_path}")
    console.print(f"[green]Saved answer MD:[/green] {md_path}")

    return True

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="*", help="Pertanyaan pengguna")
    parser.add_argument("--dry-run", action="store_true", help="Hanya tampilkan prompt tanpa memanggil LLM")
    args = parser.parse_args()

    query = " ".join(args.query).strip()

    if not query:
        console.print('[yellow]Gunakan:[/yellow] python -m app.answer_query "pertanyaan Anda"')
        return

    if handle_calculator_query(query):
        return
    
    if handle_cached_query(query):
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

    provider_error: LLMProviderError | None = None
    fallback_used = False
    fallback_message = ""
    fallback_reason = ""

    try:
        client = get_llm_client()
        result = client.generate(system_prompt=system_prompt, user_prompt=user_prompt)

    except LLMProviderError as exc:
        provider_error = exc
        print_provider_error(exc)

        fallback = try_ollama_fallback(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            original_error=exc,
        )

        fallback_message = fallback.message
        fallback_reason = fallback.reason

        if fallback.used and fallback.result is not None:
            result = fallback.result
            fallback_used = True
            console.print(f"[green]Fallback used:[/green] {settings.fallback_provider}")
            console.print(f"[green]Fallback reason:[/green] {fallback.reason}")
        else:
            if (
                exc.info.error_type == ERROR_RATE_LIMITED
                and settings.local_only_on_rate_limit
            ):
                fallback_answer = build_extractive_answer(evidence_pack)
                fallback_answer = clean_answer(fallback_answer, evidence_pack=evidence_pack)

                result = type(
                    "ToolFallbackResult",
                    (),
                    {
                        "text": fallback_answer,
                        "provider": "local_only",
                        "model": "extractive_fallback",
                        "raw": {},
                    },
                )()

                fallback_used = True
                fallback_message = "Kuota Gemini harian habis, jawaban hanya berdasarkan retrieval lokal."
                fallback_reason = "rate_limited_local_only"

                console.print("[yellow]Kuota Gemini harian habis, jawaban hanya berdasarkan retrieval lokal.[/yellow]")

            else:
                console.print(f"[red]Fallback not used:[/red] {fallback.reason}")
                console.print("\n[yellow]Gunakan --dry-run untuk cek prompt tanpa memanggil model.[/yellow]")
                return
            
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

    if provider_error is not None or fallback_used:
        verification = {
            **verification,
            "provider_error": provider_error_to_dict(provider_error),
            "fallback_used": fallback_used,
            "fallback_provider": settings.fallback_provider if fallback_used else None,
            "fallback_reason": fallback_reason,
            "fallback_message": fallback_message,
        }

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
                "provider_error": provider_error_to_dict(provider_error),
                "fallback_used": fallback_used,
                "fallback_provider": settings.fallback_provider if fallback_used else None,
                "fallback_reason": fallback_reason,
                "fallback_message": fallback_message,
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
                    "fallback_used": bool(local_verification.get("fallback_used", False)) or fallback_used,
                    "provider_fallback_used": fallback_used,
                    "provider_error": provider_error_to_dict(provider_error),
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
                    "provider_fallback_used": fallback_used,
                    "provider_error": provider_error_to_dict(provider_error),
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
        "provider_error": provider_error_to_dict(provider_error),
        "fallback_used": fallback_used,
        "fallback_provider": settings.fallback_provider if fallback_used else None,
        "fallback_reason": fallback_reason,
        "fallback_message": fallback_message,
        "quality": quality,
        "quality_id": quality_id,
    }

    if (
        settings.api_cache_enabled
        and result.provider in {"openai_compatible", "local_only", "ollama"}
        and quality.get("quality_pass")
    ):
        QueryCache().set(
            query=query,
            answer=final_answer,
            provider=result.provider,
            model=result.model,
            record=record,
        )

    json_path, md_path = save_answer_record(record)

    console.print("\n[bold green]Answer[/bold green]\n")
    console.print(final_answer)

    console.print("\n[bold]Verification[/bold]")
    console.print(verification)

    if provider_error is not None:
        console.print("\n[bold yellow]Provider Error[/bold yellow]")
        console.print(provider_error_to_dict(provider_error))

    if fallback_used:
        console.print("\n[bold green]Provider Fallback[/bold green]")
        console.print(
            {
                "fallback_used": fallback_used,
                "fallback_provider": settings.fallback_provider,
                "fallback_reason": fallback_reason,
                "fallback_message": fallback_message,
            }
        )

    console.print("\n[bold]Quality[/bold]")
    console.print(quality)
    if quality_id is not None:
        console.print(f"[green]Quality record ID:[/green] {quality_id}")

    console.print(f"\n[green]Saved answer JSON:[/green] {json_path}")
    console.print(f"[green]Saved answer MD:[/green] {md_path}")


if __name__ == "__main__":
    main()
