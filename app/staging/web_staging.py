from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import settings
from app.parsers.html_parser import ParsedDocument, parse_html_file


@dataclass(frozen=True)
class WebStagingResult:
    source_path: Path
    text_path: Path
    metadata_path: Path
    metadata: dict[str, Any]
    text_chars: int


def safe_stem(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_\-]+", "_", text.lower()).strip("_")
    return cleaned[:90] or "web_document"


def ensure_web_staging_dirs(base_dir: Path | None = None) -> dict[str, Path]:
    root = base_dir or Path("data/web_staging")

    dirs = {
        "root": root,
        "raw_html": root / "raw_html",
        "parsed_text": root / "parsed_text",
        "sanitized": root / "sanitized",
        "quarantine": root / "quarantine",
        "approved": root / "approved",
    }

    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)

    return dirs


def metadata_sidecar_path(path: Path) -> Path:
    return path.with_suffix(path.suffix + ".metadata.json")


def load_sidecar_metadata(path: Path) -> dict[str, Any]:
    sidecar = metadata_sidecar_path(path)

    if not sidecar.exists():
        return {}

    try:
        return json.loads(sidecar.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def append_manifest(manifest_path: Path, payload: dict[str, Any]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    with manifest_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def parse_raw_html_to_staging(
    html_path: str | Path,
    *,
    output_dir: str | Path | None = None,
    url: str = "",
    fetched_at: str = "",
    overwrite: bool = False,
) -> WebStagingResult:
    html_path = Path(html_path)

    if not html_path.exists():
        raise FileNotFoundError(f"HTML file tidak ditemukan: {html_path}")

    dirs = ensure_web_staging_dirs()
    parsed_dir = Path(output_dir) if output_dir else dirs["parsed_text"]
    parsed_dir.mkdir(parents=True, exist_ok=True)

    sidecar_metadata = load_sidecar_metadata(html_path)
    url = url or str(sidecar_metadata.get("url", ""))
    fetched_at = fetched_at or str(sidecar_metadata.get("fetched_at", ""))

    parsed: ParsedDocument = parse_html_file(
        html_path,
        url=url,
        fetched_at=fetched_at,
    )

    base_name = safe_stem(parsed.metadata.get("title") or html_path.stem)
    text_path = parsed_dir / f"{base_name}.txt"
    metadata_path = parsed_dir / f"{base_name}.metadata.json"

    if not overwrite:
        counter = 1
        original_text_path = text_path
        original_metadata_path = metadata_path

        while text_path.exists() or metadata_path.exists():
            text_path = original_text_path.with_name(f"{original_text_path.stem}_{counter}.txt")
            metadata_path = original_metadata_path.with_name(
                f"{original_metadata_path.stem}_{counter}.metadata.json"
            )
            counter += 1

    metadata = {
        **parsed.metadata,
        "raw_html_path": str(html_path),
        "parsed_text_path": str(text_path),
        "metadata_path": str(metadata_path),
        "staging_status": "parsed",
    }

    text_path.write_text(parsed.text, encoding="utf-8")
    write_json(metadata_path, metadata)

    append_manifest(
        parsed_dir / "manifest.jsonl",
        {
            "source_path": str(html_path),
            "text_path": str(text_path),
            "metadata_path": str(metadata_path),
            "document_hash": metadata.get("document_hash"),
            "content_hash": metadata.get("content_hash"),
            "url": metadata.get("url"),
            "domain": metadata.get("domain"),
            "title": metadata.get("title"),
            "parser": metadata.get("parser"),
            "staging_status": "parsed",
        },
    )

    return WebStagingResult(
        source_path=html_path,
        text_path=text_path,
        metadata_path=metadata_path,
        metadata=metadata,
        text_chars=len(parsed.text),
    )


def parse_raw_html_dir_to_staging(
    input_dir: str | Path,
    *,
    output_dir: str | Path | None = None,
    overwrite: bool = False,
) -> list[WebStagingResult]:
    input_dir = Path(input_dir)

    if not input_dir.exists():
        raise FileNotFoundError(f"Input dir tidak ditemukan: {input_dir}")

    html_files = sorted(
        [
            *input_dir.glob("*.html"),
            *input_dir.glob("*.htm"),
        ]
    )

    results: list[WebStagingResult] = []

    for path in html_files:
        results.append(
            parse_raw_html_to_staging(
                path,
                output_dir=output_dir,
                overwrite=overwrite,
            )
        )

    return results