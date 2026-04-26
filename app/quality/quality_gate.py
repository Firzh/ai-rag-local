from __future__ import annotations

import csv
import json
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SECRET_PATTERNS = [
    re.compile(r"(?i)\b(api[_-]?key|secret|password|passwd|access[_-]?token|refresh[_-]?token)\b\s*[:=]\s*['\"]?[^'\"\s]{8,}"),
    re.compile(r"(?i)\bbearer\s+[a-z0-9._\-]{16,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),  # Google/Gemini style key prefix
    re.compile(r"sk-[0-9A-Za-z_\-]{20,}"),   # OpenAI style key prefix
]


REQUIRED_METADATA_FIELDS = [
    "source_type",
    "source_name",
    "source_path",
    "document_hash",
    "parser",
]


REQUIRED_WEB_FIELDS = [
    "url",
    "domain",
]


@dataclass(frozen=True)
class QualityIssue:
    rule: str
    severity: str
    message: str


@dataclass
class QualityGateResult:
    text_path: Path
    metadata_path: Path | None
    status: str
    text_chars: int
    symbol_ratio: float
    issues: list[QualityIssue] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def approved(self) -> bool:
        return self.status == "approved"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def metadata_path_for_text(text_path: Path) -> Path:
    return text_path.with_suffix(".metadata.json")


def load_metadata(text_path: Path) -> tuple[Path | None, dict[str, Any]]:
    metadata_path = metadata_path_for_text(text_path)

    if not metadata_path.exists():
        return None, {}

    try:
        return metadata_path, json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return metadata_path, {}


def symbol_ratio(text: str) -> float:
    stripped = text.strip()

    if not stripped:
        return 1.0

    symbols = sum(1 for ch in stripped if not ch.isalnum() and not ch.isspace())
    return round(symbols / max(1, len(stripped)), 4)


def contains_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def add_issue(issues: list[QualityIssue], rule: str, message: str, severity: str = "error") -> None:
    issues.append(QualityIssue(rule=rule, severity=severity, message=message))


def validate_text_and_metadata(
    *,
    text: str,
    metadata: dict[str, Any],
    min_chars: int = 80,
    max_symbol_ratio: float = 0.35,
) -> tuple[list[QualityIssue], float]:
    issues: list[QualityIssue] = []
    clean_text = text.strip()
    ratio = symbol_ratio(clean_text)

    if not clean_text:
        add_issue(issues, "empty_text", "Teks kosong.")

    if clean_text and len(clean_text) < min_chars:
        add_issue(
            issues,
            "too_short",
            f"Teks terlalu pendek: {len(clean_text)} karakter, minimal {min_chars}.",
        )

    if contains_secret(clean_text):
        add_issue(
            issues,
            "secret_detected",
            "Teks mengandung pola secret/API key/token/password.",
        )

    if ratio > max_symbol_ratio:
        add_issue(
            issues,
            "symbol_ratio_high",
            f"Rasio simbol terlalu tinggi: {ratio}, maksimal {max_symbol_ratio}.",
        )

    for field_name in REQUIRED_METADATA_FIELDS:
        if not str(metadata.get(field_name, "")).strip():
            add_issue(
                issues,
                "metadata_missing",
                f"Metadata wajib tidak ada atau kosong: {field_name}.",
            )

    if metadata.get("source_type") == "web":
        for field_name in REQUIRED_WEB_FIELDS:
            if not str(metadata.get(field_name, "")).strip():
                add_issue(
                    issues,
                    "web_metadata_missing",
                    f"Metadata web wajib tidak ada atau kosong: {field_name}.",
                )

    if metadata and metadata.get("approval_status") not in {"staged", "approved", "quarantine"}:
        add_issue(
            issues,
            "approval_status_unknown",
            "approval_status tidak standar; diharapkan staged/approved/quarantine.",
            severity="warning",
        )

    return issues, ratio


def evaluate_text_file(
    text_path: str | Path,
    *,
    min_chars: int = 80,
    max_symbol_ratio: float = 0.35,
) -> QualityGateResult:
    text_path = Path(text_path)
    text = text_path.read_text(encoding="utf-8", errors="replace")
    metadata_path, metadata = load_metadata(text_path)

    issues, ratio = validate_text_and_metadata(
        text=text,
        metadata=metadata,
        min_chars=min_chars,
        max_symbol_ratio=max_symbol_ratio,
    )

    has_error = any(issue.severity == "error" for issue in issues)
    status = "quarantine" if has_error else "approved"

    return QualityGateResult(
        text_path=text_path,
        metadata_path=metadata_path,
        status=status,
        text_chars=len(text.strip()),
        symbol_ratio=ratio,
        issues=issues,
        metadata=metadata,
    )


def update_metadata_for_gate(result: QualityGateResult) -> dict[str, Any]:
    metadata = dict(result.metadata)
    metadata.update(
        {
            "quality_gate_checked_at": utc_now_iso(),
            "quality_gate_status": result.status,
            "approval_status": result.status,
            "quality_gate_issue_count": len(result.issues),
            "quality_gate_issues": [
                {
                    "rule": issue.rule,
                    "severity": issue.severity,
                    "message": issue.message,
                }
                for issue in result.issues
            ],
        }
    )
    return metadata


def copy_result_to_status_dir(
    result: QualityGateResult,
    *,
    approved_dir: Path,
    quarantine_dir: Path,
) -> tuple[Path, Path | None]:
    target_dir = approved_dir if result.approved else quarantine_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    target_text = target_dir / result.text_path.name
    shutil.copy2(result.text_path, target_text)

    target_metadata: Path | None = None
    updated_metadata = update_metadata_for_gate(result)

    if result.metadata_path is not None:
        target_metadata = target_dir / result.metadata_path.name
    else:
        target_metadata = target_text.with_suffix(".metadata.json")

    target_metadata.write_text(
        json.dumps(updated_metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return target_text, target_metadata


def issue_summary(issues: list[QualityIssue]) -> str:
    if not issues:
        return ""

    return " | ".join(f"{issue.severity}:{issue.rule}:{issue.message}" for issue in issues)


def write_report(report_path: Path, results: list[QualityGateResult]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with report_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "text_path",
                "metadata_path",
                "status",
                "text_chars",
                "symbol_ratio",
                "issue_count",
                "issues",
                "source_type",
                "domain",
                "url",
                "title",
                "document_hash",
                "content_hash",
                "parser",
            ],
        )
        writer.writeheader()

        for result in results:
            metadata = result.metadata
            writer.writerow(
                {
                    "text_path": str(result.text_path),
                    "metadata_path": str(result.metadata_path or ""),
                    "status": result.status,
                    "text_chars": result.text_chars,
                    "symbol_ratio": result.symbol_ratio,
                    "issue_count": len(result.issues),
                    "issues": issue_summary(result.issues),
                    "source_type": metadata.get("source_type", ""),
                    "domain": metadata.get("domain", ""),
                    "url": metadata.get("url", ""),
                    "title": metadata.get("title", ""),
                    "document_hash": metadata.get("document_hash", ""),
                    "content_hash": metadata.get("content_hash", ""),
                    "parser": metadata.get("parser", ""),
                }
            )


def run_quality_gate(
    *,
    input_dir: str | Path,
    report_path: str | Path = "data/audits/quality_gate_report.csv",
    approved_dir: str | Path = "data/web_staging/approved",
    quarantine_dir: str | Path = "data/web_staging/quarantine",
    min_chars: int = 80,
    max_symbol_ratio: float = 0.35,
    copy_outputs: bool = True,
) -> list[QualityGateResult]:
    input_dir = Path(input_dir)
    report_path = Path(report_path)
    approved_dir = Path(approved_dir)
    quarantine_dir = Path(quarantine_dir)

    if not input_dir.exists():
        raise FileNotFoundError(f"Input dir tidak ditemukan: {input_dir}")

    text_files = sorted(input_dir.glob("*.txt"))
    results = [
        evaluate_text_file(
            path,
            min_chars=min_chars,
            max_symbol_ratio=max_symbol_ratio,
        )
        for path in text_files
    ]

    if copy_outputs:
        for result in results:
            copy_result_to_status_dir(
                result,
                approved_dir=approved_dir,
                quarantine_dir=quarantine_dir,
            )

    write_report(report_path, results)
    return results