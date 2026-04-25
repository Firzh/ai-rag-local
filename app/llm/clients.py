from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any

import requests

from app.config import settings
from app.llm.provider_errors import (
    ERROR_NETWORK,
    ERROR_RATE_LIMITED,
    ProviderErrorInfo,
    classify_http_status,
    classify_provider_payload,
    extract_error_message,
    safe_excerpt,
)
from app.usage.api_usage_store import ApiUsageStore


@dataclass
class LLMResult:
    text: str
    provider: str
    model: str
    raw: dict[str, Any]


class LLMClientError(RuntimeError):
    pass


class BaseLLMClient:
    def generate(self, system_prompt: str, user_prompt: str) -> LLMResult:
        raise NotImplementedError
    
class LLMProviderError(LLMClientError):
    def __init__(self, info: ProviderErrorInfo) -> None:
        self.info = info

        status = f"HTTP {info.status_code}" if info.status_code else "no HTTP status"
        message = (
            f"{info.provider} provider error ({info.error_type}, {status}) "
            f"for model {info.model}: {info.message}"
        )

        super().__init__(message)

class OllamaClient(BaseLLMClient):
    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResult:
        url = f"{self.base_url}/api/chat"

        messages = []

        if system_prompt and system_prompt.strip():
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt.strip(),
                }
            )

        messages.append(
            {
                "role": "user",
                "content": user_prompt.strip(),
            }
        )

        payload = {
            "model": self.model,
            "stream": False,
            "keep_alive": settings.ollama_keep_alive,
            "options": {
                "temperature": settings.llm_temperature,
                "num_predict": settings.llm_max_tokens,
                "top_p": 0.8,
                "repeat_penalty": 1.18,
                "num_ctx": 4096,
                "stop": [
                    "\n\n\n",
                    "User:",
                    "Pengguna:",
                    "SYSTEM",
                    "USER PROMPT",
                ],
            },
            "messages": messages,
        }

        try:
            response = requests.post(url, json=payload, timeout=300)
        except requests.RequestException as exc:
            raise LLMProviderError(
                ProviderErrorInfo(
                    provider="ollama",
                    model=self.model,
                    error_type=ERROR_NETWORK,
                    status_code=None,
                    message=str(exc),
                    raw_excerpt=safe_excerpt(str(exc)),
                )
            ) from exc

        if response.status_code >= 400:
            error_type = classify_http_status(response.status_code)
            raise LLMProviderError(
                ProviderErrorInfo(
                    provider="ollama",
                    model=self.model,
                    error_type=error_type,
                    status_code=response.status_code,
                    message=response.text,
                    raw_excerpt=safe_excerpt(response.text),
                )
            )

        data = response.json()
        message = data.get("message", {})
        text = message.get("content", "")

        if not text.strip():
            raise LLMClientError(f"Ollama tidak mengembalikan teks. Response: {data}")

        return LLMResult(
            text=text.strip(),
            provider="ollama",
            model=self.model,
            raw=data,
        )


class OpenAICompatibleClient(BaseLLMClient):
    def __init__(self) -> None:
        self.base_url = settings.openai_compat_base_url.rstrip("/")
        self.model = settings.openai_compat_model
        self.api_key = settings.openai_compat_api_key
        self.provider_name = "openai_compatible"

    def _chat_completions_url(self) -> str:
        if self.base_url.endswith("/chat/completions"):
            return self.base_url
        return f"{self.base_url}/chat/completions"

    def _record_usage_success(
        self,
        *,
        usage_store: ApiUsageStore,
        status_code: int,
        latency_ms: float,
        data: dict[str, Any],
    ) -> None:
        usage = data.get("usage", {}) if isinstance(data, dict) else {}

        usage_store.record_call(
            provider=self.provider_name,
            model=self.model,
            success=True,
            status_code=status_code,
            latency_ms=latency_ms,
            input_tokens=int(usage.get("prompt_tokens") or 0),
            output_tokens=int(usage.get("completion_tokens") or 0),
            total_tokens=int(usage.get("total_tokens") or 0),
            metadata={"stage": "success"},
        )

    def _record_usage_error(
        self,
        *,
        usage_store: ApiUsageStore,
        status_code: int | None,
        error_type: str,
        latency_ms: float | None,
        raw_excerpt: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        merged_metadata = {
            "stage": "error",
            "raw_excerpt": raw_excerpt,
        }
        if metadata:
            merged_metadata.update(metadata)

        usage_store.record_call(
            provider=self.provider_name,
            model=self.model,
            success=False,
            status_code=status_code,
            error_type=error_type,
            latency_ms=latency_ms,
            metadata=merged_metadata,
        )

    def _raise_provider_error(
        self,
        *,
        error_type: str,
        status_code: int | None,
        message: str,
        raw_excerpt: str = "",
    ) -> None:
        raise LLMProviderError(
            ProviderErrorInfo(
                provider=self.provider_name,
                model=self.model,
                error_type=error_type,
                status_code=status_code,
                message=message,
                raw_excerpt=raw_excerpt,
            )
        )

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResult:
        url = self._chat_completions_url()
        usage_store = ApiUsageStore()

        if (
            settings.api_quota_enabled
            and settings.api_disable_on_rpd_exceeded
            and self.provider_name == settings.api_quota_provider
            and self.model == settings.api_quota_model
            and usage_store.rpd_exceeded(provider=self.provider_name, model=self.model)
        ):
            self._record_usage_error(
                usage_store=usage_store,
                status_code=None,
                error_type=ERROR_RATE_LIMITED,
                latency_ms=0.0,
                raw_excerpt="Local RPD limit reached before API call.",
                metadata={"stage": "preflight_rpd_limit"},
            )
            self._raise_provider_error(
                error_type=ERROR_RATE_LIMITED,
                status_code=None,
                message="Kuota API harian lokal sudah mencapai batas RPD.",
                raw_excerpt="Local RPD limit reached before API call.",
            )

        messages = []
        if system_prompt and system_prompt.strip():
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt.strip(),
                }
            )

        messages.append(
            {
                "role": "user",
                "content": user_prompt.strip(),
            }
        )

        payload = {
            "model": self.model,
            "temperature": settings.llm_temperature,
            "max_tokens": settings.llm_max_tokens,
            "messages": messages,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        t0 = perf_counter()

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=300)
        except requests.RequestException as exc:
            latency_ms = (perf_counter() - t0) * 1000
            self._record_usage_error(
                usage_store=usage_store,
                status_code=None,
                error_type=ERROR_NETWORK,
                latency_ms=latency_ms,
                raw_excerpt=safe_excerpt(str(exc)),
                metadata={"stage": "network_error"},
            )
            self._raise_provider_error(
                error_type=ERROR_NETWORK,
                status_code=None,
                message=str(exc),
                raw_excerpt=safe_excerpt(str(exc)),
            )

        latency_ms = (perf_counter() - t0) * 1000

        if response.status_code >= 400:
            try:
                payload_json = response.json()
            except Exception:
                payload_json = None

            error_type = classify_provider_payload(response.status_code, payload_json)
            message = extract_error_message(payload_json, response.text)
            raw_excerpt = safe_excerpt(response.text)

            self._record_usage_error(
                usage_store=usage_store,
                status_code=response.status_code,
                error_type=error_type,
                latency_ms=latency_ms,
                raw_excerpt=raw_excerpt,
                metadata={"stage": "http_error"},
            )
            self._raise_provider_error(
                error_type=error_type,
                status_code=response.status_code,
                message=message,
                raw_excerpt=raw_excerpt,
            )

        data = response.json()

        try:
            text = data["choices"][0]["message"]["content"]
        except Exception as exc:
            self._record_usage_error(
                usage_store=usage_store,
                status_code=response.status_code,
                error_type="invalid_response",
                latency_ms=latency_ms,
                raw_excerpt=safe_excerpt(str(data)),
                metadata={"stage": "invalid_response"},
            )
            raise LLMClientError(
                f"Response OpenAI-compatible tidak sesuai format: {data}"
            ) from exc

        if not str(text).strip():
            self._record_usage_error(
                usage_store=usage_store,
                status_code=response.status_code,
                error_type="empty_response",
                latency_ms=latency_ms,
                raw_excerpt=safe_excerpt(str(data)),
                metadata={"stage": "empty_response"},
            )
            raise LLMClientError("OpenAI-compatible server tidak mengembalikan teks.")

        self._record_usage_success(
            usage_store=usage_store,
            status_code=response.status_code,
            latency_ms=latency_ms,
            data=data,
        )

        return LLMResult(
            text=str(text).strip(),
            provider=self.provider_name,
            model=self.model,
            raw=data,
        )


def get_llm_client() -> BaseLLMClient:
    provider = settings.llm_provider.lower().strip()

    if provider == "ollama":
        return OllamaClient()

    if provider in {"openai", "openai_compatible", "llama_cpp", "lmstudio"}:
        return OpenAICompatibleClient()

    raise LLMClientError(
        f"Provider LLM tidak dikenal: {settings.llm_provider}. "
        f"Gunakan 'ollama' atau 'openai_compatible'."
    )