#!/usr/bin/env python3
"""Read retrieval-ready records using only the Python standard library."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", choices=("en", "la"), default="en")
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    path = root / "data" / f"retrieval_chunks.{args.language}.jsonl"
    shown = 0
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            print(json.dumps({
                "id": row["id"],
                "citation": row["canonical_citation"],
                "authority": row["authority_class"],
                "embedding_text": row["embedding_text"],
            }, ensure_ascii=False, indent=2))
            shown += 1
            if shown >= args.limit:
                break


if __name__ == "__main__":
    main()
