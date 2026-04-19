from pathlib import Path
import json
import re

from app.config import settings


def safe_name(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "_", name)
    return cleaned.strip("_")


def save_parsed_document(
    source_name: str,
    text: str,
    metadata: dict,
) -> tuple[str, str]:
    stem = safe_name(Path(source_name).stem)

    text_path = settings.parsed_dir / f"{stem}.parsed.md"
    meta_path = settings.parsed_dir / f"{stem}.metadata.json"

    text_path.parent.mkdir(parents=True, exist_ok=True)

    text_path.write_text(text, encoding="utf-8")

    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return str(text_path), str(meta_path)