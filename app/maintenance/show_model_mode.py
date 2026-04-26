from __future__ import annotations

from rich.console import Console

from app.config import settings


console = Console()


def main() -> None:
    console.print(f"Model mode: {settings.model_mode}")
    console.print(f"Selected Ollama model: {settings.ollama_model}")
    console.print(f"RAG model: {settings.ollama_model_rag}")
    console.print(f"Coder model: {settings.ollama_model_coder}")
    console.print(f"General model: {settings.ollama_model_general}")


if __name__ == "__main__":
    main()