from __future__ import annotations

import argparse
from rich.console import Console

from app.quality_store import AnswerQualityStore


console = Console()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("answer_quality_id", type=int)
    parser.add_argument("label", choices=["good", "bad", "needs_fix"])
    parser.add_argument("--note", default="")
    parser.add_argument("--corrected", default="")

    args = parser.parse_args()

    store = AnswerQualityStore()
    store.add_feedback(
        answer_quality_id=args.answer_quality_id,
        feedback_label=args.label,
        feedback_note=args.note,
        corrected_answer=args.corrected,
    )

    console.print(
        f"[green]Feedback saved.[/green] "
        f"ID={args.answer_quality_id}, label={args.label}"
    )


if __name__ == "__main__":
    main()