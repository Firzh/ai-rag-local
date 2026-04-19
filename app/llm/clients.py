from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import requests

from app.config import settings


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
            raise LLMClientError(
                f"Gagal menghubungi Ollama di {url}. "
                f"Pastikan Ollama berjalan dan base URL benar."
            ) from exc

        if response.status_code >= 400:
            raise LLMClientError(
                f"Ollama error {response.status_code}: {response.text}"
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
            raise LLMClientError(
                f"Gagal menghubungi OpenAI-compatible server di {url}."
            ) from exc

        if response.status_code >= 400:
            raise LLMClientError(
                f"OpenAI-compatible server error {response.status_code}: {response.text}"
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