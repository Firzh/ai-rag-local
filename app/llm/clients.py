from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import requests

from app.config import settings
from app.llm.provider_errors import (
    ProviderErrorInfo,
    classify_http_status,
    classify_provider_payload,
    extract_error_message,
    safe_excerpt,
    ERROR_NETWORK,
)


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

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResult:
        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": self.model,
            "temperature": settings.llm_temperature,
            "max_tokens": settings.llm_max_tokens,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=300)
        except requests.RequestException as exc:
            raise LLMProviderError(
                ProviderErrorInfo(
                    provider="openai_compatible",
                    model=self.model,
                    error_type=ERROR_NETWORK,
                    status_code=None,
                    message=str(exc),
                    raw_excerpt=safe_excerpt(str(exc)),
                )
            ) from exc

        if response.status_code >= 400:
            try:
                payload = response.json()
            except Exception:
                payload = None

            error_type = classify_provider_payload(response.status_code, payload)

            raise LLMProviderError(
                ProviderErrorInfo(
                    provider="openai_compatible",
                    model=self.model,
                    error_type=error_type,
                    status_code=response.status_code,
                    message=extract_error_message(payload, response.text),
                    raw_excerpt=safe_excerpt(response.text),
                )
            )

        data = response.json()

        try:
            text = data["choices"][0]["message"]["content"]
        except Exception as exc:
            raise LLMClientError(
                f"Response OpenAI-compatible tidak sesuai format: {data}"
            ) from exc

        return LLMResult(
            text=text.strip(),
            provider="openai_compatible",
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