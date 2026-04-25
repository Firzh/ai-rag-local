from __future__ import annotations

import json
import re
import time
from typing import Any

import requests

from app.config import settings


class QwenJudgeVerifier:
    def __init__(self) -> None:
        self.enabled = settings.qwen_judge_enabled
        self.base_url = settings.qwen_judge_base_url.rstrip("/")
        self.model = settings.qwen_judge_model
        self.api_key = settings.qwen_judge_api_key

    def _build_evidence_text(self, evidence_pack: dict[str, Any]) -> str:
        lines: list[str] = []

        facts = evidence_pack.get("important_facts", [])[:8]
        quotes = evidence_pack.get("important_quotes", [])[:5]

        for i, fact in enumerate(facts, start=1):
            text = str(fact.get("text", "")).strip()
            source = str(fact.get("source_name", "")).strip()
            if not text:
                continue
            lines.append(f"FACT {i}: {text}")
            if source:
                lines.append(f"SOURCE {i}: {source}")

        for i, quote in enumerate(quotes, start=1):
            text = str(quote.get("quote", "")).strip()
            source = str(quote.get("source_name", "")).strip()
            if not text:
                continue
            short_quote = text[:450]
            lines.append(f"QUOTE {i}: {short_quote}")
            if source:
                lines.append(f"QUOTE_SOURCE {i}: {source}")

        return "\n".join(lines).strip()

    def _extract_json(self, text: str) -> dict[str, Any]:
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise ValueError("Response judge tidak mengandung JSON object.")

        return json.loads(match.group(0))

    def verify_answer(self, query: str, answer: str, evidence_pack: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled:
            return {
                "verifier": "qwen_judge",
                "available": False,
                "supported": None,
                "confidence": 0.0,
                "notes": ["Qwen judge nonaktif."],
            }

        evidence_text = self._build_evidence_text(evidence_pack)
        if not evidence_text:
            return {
                "verifier": "qwen_judge",
                "available": False,
                "supported": None,
                "confidence": 0.0,
                "notes": ["Evidence kosong. Qwen judge dilewati."],
            }

        system_prompt = (
            "Anda adalah semantic verifier untuk sistem RAG. "
            "Tugas Anda hanya menilai apakah jawaban didukung evidence. "
            "Jangan menulis ulang jawaban. Jangan menambah fakta baru. "
            "Balas hanya JSON valid."
        )

        user_prompt = f"""
Nilai jawaban berikut berdasarkan evidence yang diberikan.

Kriteria:
- supported=true hanya jika inti jawaban konsisten dengan evidence.
- contradiction=true jika ada klaim yang bertentangan dengan evidence.
- jika evidence tidak cukup, supported=false.
- confidence harus 0 sampai 1.
- Buat 1 sampai 5 claim_checks singkat.

Output JSON persis dengan skema berikut:
{{
  "supported": true,
  "confidence": 0.0,
  "contradiction": false,
  "missing_support": ["..."],
  "contradictions": ["..."],
  "claim_checks": [
    {{"claim": "...", "verdict": "supported|unsupported|contradicted", "reason": "..."}}
  ],
  "notes": ["..."]
}}

QUERY:
{query}

ANSWER:
{answer}

EVIDENCE:
{evidence_text}
""".strip()

        payload = {
            "model": self.model,
            "temperature": settings.qwen_judge_temperature,
            "max_tokens": settings.qwen_judge_max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}/chat/completions"
        started_at = time.perf_counter()

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=180)
            latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
        except requests.RequestException as exc:
            return {
                "verifier": "qwen_judge",
                "available": False,
                "supported": None,
                "confidence": 0.0,
                "latency_ms": None,
                "notes": [f"Gagal menghubungi Qwen judge: {exc}"],
            }

        if response.status_code >= 400:
            return {
                "verifier": "qwen_judge",
                "available": False,
                "supported": None,
                "confidence": 0.0,
                "latency_ms": latency_ms,
                "notes": [f"Qwen judge error {response.status_code}: {response.text[:400]}"],
            }

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed = self._extract_json(content)
        except Exception as exc:
            return {
                "verifier": "qwen_judge",
                "available": False,
                "supported": None,
                "confidence": 0.0,
                "latency_ms": latency_ms,
                "notes": [f"Response Qwen judge tidak valid: {exc}"],
                "raw": response.text[:1200],
            }

        confidence = parsed.get("confidence", 0.0)
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))

        supported = bool(parsed.get("supported", False))

        if confidence < settings.qwen_judge_confidence_threshold and supported:
            supported = False
            notes = list(parsed.get("notes", []))
            notes.append(
                "Confidence judge di bawah threshold sehingga verdict diturunkan menjadi unsupported."
            )
            parsed["notes"] = notes

        return {
            "verifier": "qwen_judge",
            "available": True,
            "supported": supported,
            "confidence": confidence,
            "contradiction": bool(parsed.get("contradiction", False)),
            "missing_support": list(parsed.get("missing_support", [])),
            "contradictions": list(parsed.get("contradictions", [])),
            "claim_checks": list(parsed.get("claim_checks", [])),
            "notes": list(parsed.get("notes", [])),
            "latency_ms": latency_ms,
            "model": self.model,
            "provider": "qwen_judge_api",
            "raw": parsed,
        }
