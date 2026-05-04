from __future__ import annotations

import argparse
from typing import Any

import chromadb
from rich.console import Console
from rich.table import Table

from app.config import settings
from app.embeddings.fastembedder import FastEmbedder


console = Console()


MODE_TO_NOTE_TYPE = {
    "all": None,
    "kanji": "Kanji",
    "vocab": "Word",
    "word": "Word",
    "grammar": "Grammar",
}


def build_where(
    *,
    mode: str,
    maturity: str | None,
    expression: str | None,
    deck_contains: str | None,
) -> dict[str, Any] | None:
    clauses: list[dict[str, Any]] = []

    note_type = MODE_TO_NOTE_TYPE.get(mode)
    if note_type:
        clauses.append({"note_type": note_type})

    if maturity:
        clauses.append({"maturity_level": maturity})

    if expression:
        clauses.append({"expression": expression})

    # Chroma where does not support contains reliably for string fields across versions.
    # deck_contains will be applied after retrieval as a soft post-filter.
    if not clauses:
        return None

    if len(clauses) == 1:
        return clauses[0]

    return {"$and": clauses}


def print_results(result: dict[str, Any], *, limit: int, deck_contains: str | None = None) -> None:
    ids = result.get("ids", [[]])[0] or []
    docs = result.get("documents", [[]])[0] or []
    metas = result.get("metadatas", [[]])[0] or []
    distances = result.get("distances", [[]])[0] or []

    shown = 0

    for idx, doc_id in enumerate(ids):
        meta = metas[idx] if idx < len(metas) else {}
        doc = docs[idx] if idx < len(docs) else ""
        distance = distances[idx] if idx < len(distances) else None

        if deck_contains:
            deck = str(meta.get("deck", ""))
            if deck_contains.lower() not in deck.lower():
                continue

        shown += 1

        console.print("\n" + "=" * 90)
        console.print(f"[bold]Rank:[/bold] {shown}")
        console.print(f"[bold]ID:[/bold] {doc_id}")

        if distance is not None:
            console.print(f"[bold]Distance:[/bold] {distance}")

        console.print(f"[bold]Expression:[/bold] {meta.get('expression')}")
        console.print(f"[bold]Reading:[/bold] {meta.get('reading')}")
        console.print(f"[bold]Note type:[/bold] {meta.get('note_type')}")
        console.print(f"[bold]Maturity:[/bold] {meta.get('maturity_level')} ({meta.get('maturity_score')})")
        console.print(f"[bold]Interval days:[/bold] {meta.get('interval_days')}")
        console.print(f"[bold]Review count:[/bold] {meta.get('review_count')}")
        console.print(f"[bold]Deck:[/bold] {meta.get('deck')}")
        console.print("[bold]Preview:[/bold]")
        console.print(str(doc)[:900])

        if shown >= limit:
            break

    if shown == 0:
        console.print("[yellow]Tidak ada hasil setelah filter.[/yellow]")


def exact_lookup(
    *,
    collection,
    mode: str,
    maturity: str | None,
    expression: str | None,
    deck_contains: str | None,
    limit: int,
) -> None:
    where = build_where(
        mode=mode,
        maturity=maturity,
        expression=expression,
        deck_contains=deck_contains,
    )

    result = collection.get(
        where=where,
        include=["documents", "metadatas"],
        limit=limit * 5 if deck_contains else limit,
    )

    wrapped = {
        "ids": [result.get("ids", [])],
        "documents": [result.get("documents", [])],
        "metadatas": [result.get("metadatas", [])],
        "distances": [[]],
    }

    print_results(wrapped, limit=limit, deck_contains=deck_contains)


def semantic_query(
    *,
    collection,
    query: str,
    mode: str,
    maturity: str | None,
    expression: str | None,
    deck_contains: str | None,
    limit: int,
) -> None:
    where = build_where(
        mode=mode,
        maturity=maturity,
        expression=expression,
        deck_contains=deck_contains,
    )

    embedder = FastEmbedder()
    query_embedding = embedder.embed_documents([query])[0]

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=limit * 5 if deck_contains else limit,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    print_results(result, limit=limit, deck_contains=deck_contains)


def summarize_collection(collection) -> None:
    table = Table(title="Anki Collection Summary")
    table.add_column("Field")
    table.add_column("Value")

    table.add_row("Collection count", str(collection.count()))
    table.add_row("Collection", collection.name)

    console.print(table)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Query dedicated Anki Japanese Learning Chroma collection."
    )

    parser.add_argument("--collection", default="anki_japanese_learning")
    parser.add_argument("--query", default="")
    parser.add_argument(
        "--mode",
        choices=sorted(MODE_TO_NOTE_TYPE.keys()),
        default="all",
        help="Mode filter: kanji, vocab, grammar, atau all.",
    )
    parser.add_argument(
        "--maturity",
        choices=["new", "learning", "young", "growing", "mature", "fragile", "overdue", "unknown"],
        default=None,
    )
    parser.add_argument("--expression", default=None)
    parser.add_argument("--deck-contains", default=None)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--summary", action="store_true")

    args = parser.parse_args()

    client = chromadb.PersistentClient(path=str(settings.chroma_dir))
    collection = client.get_collection(name=args.collection)

    if args.summary:
        summarize_collection(collection)
        return

    if args.expression and not args.query:
        exact_lookup(
            collection=collection,
            mode=args.mode,
            maturity=args.maturity,
            expression=args.expression,
            deck_contains=args.deck_contains,
            limit=args.limit,
        )
        return

    if not args.query:
        console.print("[red]Isi --query atau --expression.[/red]")
        return

    semantic_query(
        collection=collection,
        query=args.query,
        mode=args.mode,
        maturity=args.maturity,
        expression=args.expression,
        deck_contains=args.deck_contains,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
