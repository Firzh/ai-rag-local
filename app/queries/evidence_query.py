import sys
from rich.console import Console

from app.compression.context_compressor import ContextCompressor


console = Console()


def main() -> None:
    if len(sys.argv) < 2:
        console.print('[yellow]Gunakan:[/yellow] python -m app.evidence_query "pertanyaan Anda"')
        return

    query = " ".join(sys.argv[1:])

    compressor = ContextCompressor()
    evidence = compressor.build_evidence_pack(query)
    path = compressor.save_evidence_pack(evidence)
    prompt_context = compressor.to_prompt_context(evidence)

    console.print(f"\n[bold]Evidence query:[/bold] {query}")
    console.print(f"[green]Saved evidence:[/green] {path}\n")
    console.print("[bold green]Compressed Evidence Pack[/bold green]\n")
    console.print(prompt_context)


if __name__ == "__main__":
    main()