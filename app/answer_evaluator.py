from __future__ import annotations

import json
import re
from typing import Any

from app.config import settings
from app.answer_quality import is_answer_artifact_like


def load_component_roles() -> dict[str, Any]:
    path = settings.quality_dir / "component_roles.json"

    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def detect_format_issues(answer: str) -> list[str]:
    issues = []
    lower = answer.lower()

    if "kutipan pendek penting" in lower:
        issues.append("format:copied_quote_label")

    if "fakta penting:" in lower:
        issues.append("format:copied_fact_label")

    if "sumber relevan:" in lower:
        issues.append("format:copied_source_label")

    if "(sumber:" not in lower:
        issues.append("format:missing_source")

    if len(answer) > 1200:
        issues.append("format:too_long")

    if re.search(r"\b1\.\s+.+\b2\.\s+", answer):
        issues.append("format:numbered_overexpansion")

    return issues


def find_role_violations(answer: str, query: str) -> list[str]:
    roles = load_component_roles()
    answer_lower = answer.lower()
    query_lower = query.lower()

    issues = []

    for component, rule in roles.items():
        component_lower = component.lower()

        if component_lower not in answer_lower and component_lower not in query_lower:
            continue

        for forbidden in rule.get("forbidden_claims", []):
            forbidden_lower = forbidden.lower()

            if forbidden_lower in answer_lower:
                issues.append(f"role_confusion:{component}:{forbidden}")

    return issues


def calculate_quality_score(
    verification: dict[str, Any],
    artifact_like: bool,
    issue_tags: list[str],
) -> float:
    supported = bool(verification.get("supported"))
    support_ratio = float(verification.get("support_ratio", 0.0))

    # Support ratio dari verifier berbasis keyword tidak selalu mewakili kualitas.
    # Jadi supported=True + no issue tetap diberi skor layak.
    if supported:
        score = 0.75
    else:
        score = 0.25

    # Tambahkan bonus bertahap dari support ratio.
    score += min(0.20, support_ratio * 0.20)

    if artifact_like:
        score -= 0.20

    if issue_tags:
        score -= min(0.35, 0.07 * len(issue_tags))

    return max(0.0, min(1.0, round(score, 4)))


def evaluate_answer_quality(
    query: str,
    answer: str,
    verification: dict[str, Any],
) -> dict[str, Any]:
    artifact_like = is_answer_artifact_like(answer, query)

    issue_tags = []
    issue_tags.extend(detect_format_issues(answer))
    issue_tags.extend(find_role_violations(answer, query))

    quality_score = calculate_quality_score(
        verification=verification,
        artifact_like=artifact_like,
        issue_tags=issue_tags,
    )

    quality_pass = (
        bool(verification.get("supported"))
        and not artifact_like
        and not issue_tags
        and quality_score >= 0.70
    )

    return {
        "artifact_like": artifact_like,
        "issue_tags": issue_tags,
        "quality_score": quality_score,
        "quality_pass": quality_pass,
    }