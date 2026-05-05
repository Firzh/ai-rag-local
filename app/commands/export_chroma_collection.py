from __future__ import annotations

import argparse

from app.config import settings
from app.exporters.chroma_jsonl_export import export_chroma_collection_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export Chroma collection ke JSONL."
    )
    parser.add_argument(
        "--chroma-dir",
        default=str(settings.chroma_dir),
        help="Folder Chroma lokal.",
    )
    parser.add_argument(
        "--collection",
        default=settings.collection_name,
        help="Nama collection Chroma yang akan diekspor.",
    )
    parser.add_argument(
        "--output",
        default="data/exports/chroma_collection.jsonl",
        help="Path output JSONL.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Jumlah record per batch.",
    )
    parser.add_argument(
        "--include-embeddings",
        action="store_true",
        help="Sertakan vector embedding dalam JSONL.",
    )

    args = parser.parse_args()

    result = export_chroma_collection_jsonl(
        chroma_dir=args.chroma_dir,
        collection_name=args.collection,
        output_path=args.output,
        batch_size=args.batch_size,
        include_embeddings=args.include_embeddings,
    )

    print("Chroma JSONL export completed")
    print(f"Chroma dir        : {result.chroma_dir}")
    print(f"Collection        : {result.collection_name}")
    print(f"Output            : {result.output_path}")
    print(f"Total collection  : {result.total_count}")
    print(f"Exported records  : {result.exported_count}")
    print(f"Include embeddings: {result.include_embeddings}")


if __name__ == "__main__":
    main()
