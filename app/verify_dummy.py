import json
import sys
from pathlib import Path
from rich.console import Console

from app.config import settings
from app.verification.verifier import EvidenceVerifier


console = Console()


def list_available_evidence() -> None:
    files = sorted(settings.evidence_dir.glob("*.evidence.json"))

    if not files:
        console.print("[yellow]Belum ada evidence file di data/evidence.[/yellow]")
        console.print(
            '[cyan]Buat dulu dengan:[/cyan] '
            'python -m app.evidence_query "pertanyaan Anda"'
        )
        return

    console.print("[bold]Evidence file yang tersedia:[/bold]")
    for file in files:
        console.print(f"- {file}")


def main() -> None:
    if len(sys.argv) < 3:
        console.print(
            '[yellow]Gunakan:[/yellow] '
            'python -m app.verify_dummy path_evidence.json "jawaban dummy"'
        )
        list_available_evidence()
        return

    path = Path(sys.argv[1])
    answer = " ".join(sys.argv[2:])

    if not path.exists():
        console.print(f"[red]Evidence file tidak ditemukan:[/red] {path}")
        list_available_evidence()
        return

    with path.open("r", encoding="utf-8") as f:
        evidence = json.load(f)

    verifier = EvidenceVerifier()
    result = verifier.verify_answer(answer, evidence)

    console.print(result)


if __name__ == "__main__":
    main()