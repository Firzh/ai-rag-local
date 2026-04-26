from __future__ import annotations

from rich.console import Console
from rich.table import Table

from app.config import settings
from app.usage.api_usage_store import ApiUsageStore


console = Console()


def main() -> None:
    store = ApiUsageStore()
    summary = store.summary_today(
        provider=settings.api_quota_provider,
        model=settings.api_quota_model,
    )
    level = store.warning_level(
        provider=settings.api_quota_provider,
        model=settings.api_quota_model,
    )

    table = Table(title="API Usage Today")
    table.add_column("Metric")
    table.add_column("Value")

    table.add_row("Usage date", summary.usage_date)
    table.add_row("Provider", summary.provider)
    table.add_row("Model", summary.model)
    table.add_row("Requests", f"{summary.requests_total}/{settings.api_rpd_limit}")
    table.add_row("Success", str(summary.requests_success))
    table.add_row("Errors", str(summary.requests_error))
    table.add_row("Rate limited", str(summary.rate_limited_count))
    table.add_row("Auth errors", str(summary.auth_error_count))
    table.add_row("Input tokens", str(summary.input_tokens))
    table.add_row("Output tokens", str(summary.output_tokens))
    table.add_row("Total tokens", f"{summary.total_tokens}/{settings.api_tpm_limit}")
    table.add_row("Cache hits", str(summary.cache_hits))
    table.add_row("Fallbacks", str(summary.fallback_count))
    table.add_row("Status", level)

    console.print(table)

    if level == "warning":
        console.print("[yellow]Warning: pemakaian API harian mulai mendekati batas.[/yellow]")
    elif level == "hard_warning":
        console.print("[bold yellow]Hard warning: sisa request harian sangat sedikit.[/bold yellow]")
    elif level == "exceeded":
        console.print("[bold red]Kuota harian lokal tercapai. Gunakan fallback lokal/Ollama.[/bold red]")


if __name__ == "__main__":
    main()