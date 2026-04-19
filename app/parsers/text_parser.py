from pathlib import Path
from dataclasses import dataclass


@dataclass
class ParsedDocument:
    source_path: str
    source_name: str
    parser: str
    text: str
    metadata: dict


def read_text_file(path: str | Path) -> ParsedDocument:
    file_path = Path(path)

    encodings = ["utf-8", "utf-8-sig", "cp1252", "latin-1"]
    text = None
    used_encoding = None

    for enc in encodings:
        try:
            text = file_path.read_text(encoding=enc)
            used_encoding = enc
            break
        except UnicodeDecodeError:
            continue

    if text is None:
        raise UnicodeDecodeError(
            "unknown",
            b"",
            0,
            1,
            f"Cannot decode file: {file_path}"
        )

    return ParsedDocument(
        source_path=str(file_path.resolve()),
        source_name=file_path.name,
        parser="text_parser",
        text=text,
        metadata={
            "source_path": str(file_path.resolve()),
            "source_name": file_path.name,
            "file_ext": file_path.suffix.lower(),
            "parser": "text_parser",
            "encoding": used_encoding,
        },
    )