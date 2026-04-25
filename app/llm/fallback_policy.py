from __future__ import annotations

from dataclasses import dataclass

from app.config import settings
from app.llm.clients import LLMProviderError, LLMResult, OllamaClient
from app.llm.provider_errors import (
    ERROR_AUTH,
    ERROR_BAD_REQUEST,
    ERROR_MODEL_NOT_FOUND,
    ERROR_NETWORK,
    ERROR_PROVIDER_UNAVAILABLE,
    ERROR_RATE_LIMITED,
)


@dataclass
class FallbackResult:
    used: bool
    result: LLMResult | None
    reason: str
    message: str


def should_fallback(error: LLMProviderError) -> bool:
    if not settings.enable_llm_fallback:
        return False

    error_type = error.info.error_type

    if error_type == ERROR_RATE_LIMITED:
        return settings.fallback_on_rate_limit

    if error_type in {ERROR_NETWORK, ERROR_PROVIDER_UNAVAILABLE}:
        return settings.fallback_on_provider_unavailable

    if error_type in {ERROR_BAD_REQUEST, ERROR_AUTH, ERROR_MODEL_NOT_FOUND}:
        return settings.fallback_on_config_error

    return False


def human_action_message(error: LLMProviderError) -> str:
    error_type = error.info.error_type

    if error_type == ERROR_RATE_LIMITED:
        return "Kuota atau rate limit API tercapai. Sistem mencoba fallback ke model lokal."

    if error_type == ERROR_AUTH:
        return "API key tidak valid, tidak aktif, atau tidak memiliki izin."

    if error_type == ERROR_BAD_REQUEST:
        return "Request API tidak valid. Periksa model, endpoint, atau payload."

    if error_type == ERROR_MODEL_NOT_FOUND:
        return "Model tidak ditemukan atau tidak tersedia untuk API key ini."

    if error_type in {ERROR_NETWORK, ERROR_PROVIDER_UNAVAILABLE}:
        return "Provider API tidak tersedia. Sistem mencoba fallback ke model lokal."

    return "Terjadi error pada provider API."


def try_ollama_fallback(
    system_prompt: str,
    user_prompt: str,
    original_error: LLMProviderError,
) -> FallbackResult:
    if not should_fallback(original_error):
        return FallbackResult(
            used=False,
            result=None,
            reason=original_error.info.error_type,
            message=human_action_message(original_error),
        )

    if settings.fallback_provider.lower().strip() != "ollama":
        return FallbackResult(
            used=False,
            result=None,
            reason="fallback_provider_not_supported",
            message="Fallback provider selain Ollama belum didukung pada v2.2.1.",
        )

    try:
        client = OllamaClient()
        result = client.generate(system_prompt, user_prompt)

        return FallbackResult(
            used=True,
            result=result,
            reason=original_error.info.error_type,
            message=human_action_message(original_error),
        )

    except Exception as exc:
        return FallbackResult(
            used=False,
            result=None,
            reason="fallback_failed",
            message=f"Fallback ke Ollama gagal: {exc}",
        )