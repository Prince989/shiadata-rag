"""
One-off migration: rename the accidental default collection to `theology`.

The 410 vectors in the collection literally named "langchain" are the two epubs
that used to sit loose in data/raw_epubs/ root. They landed there because
RetrievalPipeline constructed Chroma without a collection_name, and both
langchain_community and langchain_chroma default to "langchain".

Chroma can rename in place, so this costs zero embedding calls and no downtime.

Usage:
    python scripts/rename_collection.py            # dry run
    python scripts/rename_collection.py --apply
"""

import argparse
import sys
from pathlib import Path

# Allow `python scripts/rename_collection.py` from anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import chromadb

from core.paths import CHROMA_DIR

OLD_NAME = "langchain"
NEW_NAME = "theology"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Perform the rename")
    parser.add_argument("--from", dest="old", default=OLD_NAME)
    parser.add_argument("--to", dest="new", default=NEW_NAME)
    args = parser.parse_args()

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    existing = {c.name for c in client.list_collections()}
    print(f"Database : {CHROMA_DIR}")
    print(f"Existing : {sorted(existing)}")

    if args.old not in existing:
        if args.new in existing:
            print(f"Nothing to do: '{args.new}' already exists.")
            return 0
        print(f"ERROR: source collection '{args.old}' not found.", file=sys.stderr)
        return 1

    if args.new in existing:
        print(
            f"ERROR: '{args.new}' already exists. Refusing to merge -- "
            "resolve manually.",
            file=sys.stderr,
        )
        return 1

    source = client.get_collection(args.old)
    count = source.count()
    print(f"\nWould rename '{args.old}' ({count} vectors) -> '{args.new}'")

    if not args.apply:
        print("\nDry run. Re-run with --apply to perform the rename.")
        return 0

    source.modify(name=args.new)
    after = {c.name for c in client.list_collections()}
    print(f"Done. Collections now: {sorted(after)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
