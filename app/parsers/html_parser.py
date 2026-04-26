from __future__ import annotations

import hashlib
import html
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


PARSER_VERSION = "html_parser_v1"

_BLOCK_TAGS = {
    "article",
    "section",
    "main",
    "p",
    "div",
    "br",
    "li",
    "ul",
    "ol",
    "table",
    "thead",
    "tbody",
    "tr",
    "td",
    "th",
    "blockquote",
    "pre",
}

_HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

_DROP_TAGS = {
    "script",
    "style",
    "noscript",
    "nav",
    "footer",
    "header",
    "aside",
    "form",
    "button",
    "svg",
    "canvas",
    "iframe",
}

_DROP_CLASS_ID_MARKERS = (
    "cookie",
    "banner",
    "advert",
    "ads",
    "promo",
    "modal",
    "popup",
    "subscribe",
    "newsletter",
    "breadcrumb",
    "pagination",
    "share",
    "social",
    "sidebar",
    "menu",
    "navbar",
    "footer",
    "header",
)


@dataclass(frozen=True)
class ParsedDocument:
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_space(text: str) -> str:
    text = html.unescape(text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def guess_domain(url: str) -> str:
    if not url:
        return ""

    parsed = urlparse(url)
    if parsed.netloc:
        return parsed.netloc.lower()

    return ""


def _attrs_to_dict(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
    return {key.lower(): (value or "") for key, value in attrs}


def _is_noise_attrs(attrs: dict[str, str]) -> bool:
    combined = " ".join(
        [
            attrs.get("class", ""),
            attrs.get("id", ""),
            attrs.get("role", ""),
            attrs.get("aria-label", ""),
        ]
    ).lower()

    return any(marker in combined for marker in _DROP_CLASS_ID_MARKERS)


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.title_parts: list[str] = []
        self.meta_description = ""
        self.canonical_url = ""
        self.current_tag_stack: list[str] = []
        self.drop_depth = 0
        self.in_title = False

    def handle_starttag(self, tag: str, attrs_raw: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attrs = _attrs_to_dict(attrs_raw)

        if tag in _DROP_TAGS or _is_noise_attrs(attrs):
            self.drop_depth += 1

        self.current_tag_stack.append(tag)

        if tag == "title":
            self.in_title = True

        if tag == "meta":
            name = attrs.get("name", "").lower()
            prop = attrs.get("property", "").lower()
            content = attrs.get("content", "").strip()

            if content and name == "description":
                self.meta_description = content

            if content and prop == "og:description" and not self.meta_description:
                self.meta_description = content

            if content and prop == "og:url" and not self.canonical_url:
                self.canonical_url = content

        if tag == "link":
            rel = attrs.get("rel", "").lower()
            href = attrs.get("href", "").strip()

            if href and "canonical" in rel:
                self.canonical_url = href

        if self.drop_depth > 0:
            return

        if tag in _HEADING_TAGS:
            self.parts.append("\n\n")

        elif tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()

        if self.current_tag_stack:
            self.current_tag_stack.pop()

        if tag == "title":
            self.in_title = False

        if self.drop_depth > 0:
            if tag in _DROP_TAGS or self.drop_depth > 0:
                self.drop_depth = max(0, self.drop_depth - 1)
            return

        if tag in _HEADING_TAGS or tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        data = data.strip()

        if not data:
            return

        if self.in_title:
            self.title_parts.append(data)

        if self.drop_depth > 0:
            return

        if self.current_tag_stack and self.current_tag_stack[-1] in _HEADING_TAGS:
            self.parts.append(f"\n\n{data}\n")
        else:
            self.parts.append(data + " ")

    def title(self) -> str:
        return normalize_space(" ".join(self.title_parts))

    def text(self) -> str:
        raw = "".join(self.parts)
        lines = [line.strip() for line in raw.splitlines()]
        lines = [line for line in lines if line]
        return normalize_space("\n\n".join(lines))


def extract_main_text(html_text: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(html_text)
    parser.close()
    return parser.text()


def extract_web_metadata(
    html_text: str,
    source_path: str | Path,
    *,
    url: str = "",
    fetched_at: str = "",
) -> dict[str, Any]:
    parser = _HTMLTextExtractor()
    parser.feed(html_text)
    parser.close()

    source_path = Path(source_path)
    parsed_at = utc_now_iso()
    title = parser.title()
    canonical_url = url or parser.canonical_url
    domain = guess_domain(canonical_url)

    content_hash = stable_hash(html_text)
    text = extract_main_text(html_text)
    document_hash = stable_hash(text)

    return {
        "source_type": "web",
        "source_name": source_path.name,
        "source_path": str(source_path),
        "url": canonical_url,
        "domain": domain,
        "title": title,
        "description": normalize_space(parser.meta_description),
        "fetched_at": fetched_at,
        "parsed_at": parsed_at,
        "content_hash": content_hash,
        "document_hash": document_hash,
        "parser": PARSER_VERSION,
        "parser_version": PARSER_VERSION,
        "license_note": "public_web_page",
        "approval_status": "staged",
    }


def parse_html_file(
    path: str | Path,
    *,
    url: str = "",
    fetched_at: str = "",
    encoding: str = "utf-8",
) -> ParsedDocument:
    path = Path(path)

    html_text = path.read_text(encoding=encoding, errors="replace")
    text = extract_main_text(html_text)
    metadata = extract_web_metadata(
        html_text,
        source_path=path,
        url=url,
        fetched_at=fetched_at,
    )

    return ParsedDocument(text=text, metadata=metadata)