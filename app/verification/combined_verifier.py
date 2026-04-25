from __future__ import annotations

from typing import Any


def combine_verification_results(
    local_verification: dict[str, Any],
    llm_verification: dict[str, Any] | None = None,
) -> dict[str, Any]:
    llm_verification = llm_verification or {}
    llm_available = bool(llm_verification.get("available", False))

    local_supported = bool(local_verification.get("supported", False))
    final_supported = local_supported
    verifier_mode = "local_only"
    notes = list(local_verification.get("notes", []))

    if llm_available:
        llm_supported = bool(llm_verification.get("supported", False))
        final_supported = local_supported and llm_supported
        verifier_mode = "hybrid_strict"
        notes.extend(llm_verification.get("notes", []))

        if local_supported and not llm_supported:
            notes.append("Semantic judge menolak jawaban walau lexical verifier mendukung.")
        elif not local_supported and llm_supported:
            notes.append("Semantic judge mendukung, tetapi lexical verifier tidak cukup kuat. Verdict akhir tetap unsupported.")
    else:
        notes.extend(llm_verification.get("notes", []))

    combined = {
        "supported": final_supported,
        "support_ratio": float(local_verification.get("support_ratio", 0.0)),
        "matched_terms": list(local_verification.get("matched_terms", [])),
        "notes": notes,
        "verifier_mode": verifier_mode,
        "local": local_verification,
        "llm_judge": llm_verification,
    }

    if "fallback_used" in local_verification:
        combined["fallback_used"] = bool(local_verification.get("fallback_used", False))

    if "fallback_reason" in local_verification:
        combined["fallback_reason"] = local_verification.get("fallback_reason")

    return combined
