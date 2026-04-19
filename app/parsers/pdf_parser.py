from pathlib import Path
from dataclasses import dataclass
import json
import re

import opendataloader_pdf

from app.config import settings


@dataclass
class ParsedPDF:
    source_path: str
    source_name: str
    parser: str
    text: str
    metadata: dict


def safe_name(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "_", name)
    return cleaned.strip("_")


def find_first_file(directory: Path, suffixes: tuple[str, ...]) -> Path | None:
    for suffix in suffixes:
        files = sorted(directory.rglob(f"*{suffix}"))
        if files:
            return files[0]
    return None


def extract_text_from_json_value(value) -> list[str]:
    texts: list[str] = []

    if isinstance(value, dict):
        content = value.get("content")
        element_type = value.get("type")

        if isinstance(content, str) and content.strip():
            if element_type in {
                "heading",
                "paragraph",
                "list",
                "table",
                "caption",
                "text",
            } or element_type is None:
                texts.append(content.strip())

        for child_value in value.values():
            texts.extend(extract_text_from_json_value(child_value))

    elif isinstance(value, list):
        for item in value:
            texts.extend(extract_text_from_json_value(item))

    return texts


def read_json_as_text(json_path: Path) -> str:
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    texts = extract_text_from_json_value(data)
    return "\n\n".join(texts).strip()


def parse_pdf(path: str | Path) -> ParsedPDF:
    file_path = Path(path).resolve()

    if not file_path.exists():
        raise FileNotFoundError(f"PDF tidak ditemukan: {file_path}")

    if file_path.suffix.lower() != ".pdf":
        raise ValueError(f"Bukan file PDF: {file_path}")

    output_dir = settings.parsed_dir / "pdf" / safe_name(file_path.stem)
    output_dir.mkdir(parents=True, exist_ok=True)

    opendataloader_pdf.convert(
        input_path=[str(file_path)],
        output_dir=str(output_dir),
        format="json,markdown",
        quiet=True,
        markdown_page_separator="\n\n--- PAGE %page-number% ---\n\n",
    )

    markdown_path = find_first_file(output_dir, (".md", ".markdown"))
    json_path = find_first_file(output_dir, (".json",))

    text = ""

    if markdown_path and markdown_path.exists():
        text = markdown_path.read_text(encoding="utf-8", errors="ignore").strip()

    elif json_path and json_path.exists():
        text = read_json_as_text(json_path)

    if not text:
        raise RuntimeError(
            f"OpenDataLoader selesai, tetapi tidak ada teks yang berhasil dibaca dari: {file_path}"
        )

    return ParsedPDF(
        source_path=str(file_path),
        source_name=file_path.name,
        parser="opendataloader_pdf",
        text=text,
        metadata={
            "source_path": str(file_path),
            "source_name": file_path.name,
            "file_ext": ".pdf",
            "parser": "opendataloader_pdf",
            "parsed_output_dir": str(output_dir),
            "parsed_markdown_path": str(markdown_path) if markdown_path else "",
            "parsed_json_path": str(json_path) if json_path else "",
        },
    )