from __future__ import annotations

import requests
from rich.console import Console
from rich.table import Table

from app.config import settings


console = Console()


def fetch_ollama_models() -> list[str]:
    url = settings.ollama_base_url.rstrip("/") + "/api/tags"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as exc:
        console.print(f"[red]Gagal menghubungi Ollama:[/red] {exc}")
        return []

    data = response.json()
    models = data.get("models", [])

    return [model.get("name", "") for model in models if model.get("name")]


def main() -> None:
    available = fetch_ollama_models()

    table = Table(title="Ollama Model Mode Validation")
    table.add_column("Role")
    table.add_column("Configured Model")
    table.add_column("Available")

    rows = [
        ("selected", settings.ollama_model),
        ("rag", settings.ollama_model_rag),
        ("coder", settings.ollama_model_coder),
        ("general", settings.ollama_model_general),
    ]

    for role, model in rows:
        table.add_row(
            role,
            model,
            "YES" if model in available else "NO",
        )

    console.print(table)

    console.print("\n[bold]Available Ollama models:[/bold]")
    for model in available:
        console.print(f"- {model}")

    if settings.ollama_model not in available:
        console.print(
            f"\n[red]Model aktif tidak tersedia di Ollama:[/red] {settings.ollama_model}"
        )
    else:
        console.print(
            f"\n[green]Model aktif valid:[/green] {settings.ollama_model}"
        )


if __name__ == "__main__":
    main()