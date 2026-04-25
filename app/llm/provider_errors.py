from __future__ import annotations

from dataclasses import dataclass
from typing import Any


ERROR_BAD_REQUEST = "bad_request"
ERROR_AUTH = "auth_error"
ERROR_MODEL_NOT_FOUND = "model_not_found"
ERROR_RATE_LIMITED = "rate_limited"
ERROR_PROVIDER_UNAVAILABLE = "provider_unavailable"
ERROR_NETWORK = "network_error"
ERROR_UNKNOWN = "unknown_provider_error"


@dataclass
class ProviderErrorInfo:
    provider: str
    model: str
    error_type: str
    status_code: int | None = None
    message: str = ""
    raw_excerpt: str = ""


def classify_http_status(status_code: int) -> str:
    if status_code == 400:
        return ERROR_BAD_REQUEST

    if status_code in {401, 403}:
        return ERROR_AUTH

    if status_code == 404:
        return ERROR_MODEL_NOT_FOUND

    if status_code == 429:
        return ERROR_RATE_LIMITED

    if status_code in {500, 502, 503, 504}:
        return ERROR_PROVIDER_UNAVAILABLE

    return ERROR_UNKNOWN


def safe_excerpt(text: str, max_chars: int = 800) -> str:
    cleaned = " ".join(str(text).split())
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[:max_chars] + "..."


def extract_error_message(payload: Any, fallback_text: str = "") -> str:
    if isinstance(payload, list) and payload:
        return extract_error_message(payload[0], fallback_text)

    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if message:
                return str(message)

        message = payload.get("message")
        if message:
            return str(message)

    return safe_excerpt(fallback_text, max_chars=300)

def classify_provider_payload(status_code: int, payload: Any) -> str:
    text = str(payload).lower()

    auth_markers = [
        "api_key_invalid",
        "api key not valid",
        "invalid api key",
        "invalid_api_key",
        "unauthorized",
        "permission_denied",
        "access denied",
        "forbidden",
    ]

    rate_limit_markers = [
        "rate_limit",
        "rate limit",
        "quota",
        "too many requests",
        "resource_exhausted",
        "rpd",
        "rpm",
        "tpm",
    ]

    model_markers = [
        "model not found",
        "model_not_found",
        "not found for api version",
        "not supported",
        "unsupported model",
    ]

    if any(marker in text for marker in auth_markers):
        return ERROR_AUTH

    if any(marker in text for marker in rate_limit_markers):
        return ERROR_RATE_LIMITED

    if any(marker in text for marker in model_markers):
        return ERROR_MODEL_NOT_FOUND

    return classify_http_status(status_code)