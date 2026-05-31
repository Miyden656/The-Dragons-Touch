"""Merge multiple training corpus files into one, de-duplicating (headless).

For pooling work between people: you and a collaborator each review a different
set of decks, then combine your two .jsonl files into one master corpus. Exact
duplicate records (same commander/mode/persona/question/answer) are dropped.

    py -3 -m ai.cli.merge_corpus mine.jsonl buddy.jsonl --out all_decks.jsonl
    py -3 -m ai.cli.merge_corpus a.jsonl b.jsonl c.jsonl --out combined.jsonl

Bad lines in any input are skipped (reported), never fatal. The output is a new
file — your inputs are left untouched.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from ai.training.corpus import load_corpus, merge_records, write_corpus  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass

    parser = argparse.ArgumentParser(description="Merge training corpus files (dedupe)")
    parser.add_argument("inputs", nargs="+", help="Two or more corpus .jsonl files to combine")
    parser.add_argument("--out", required=True, help="Output .jsonl file for the merged corpus")
    args = parser.parse_args(argv)

    lists: list[list[dict]] = []
    for p in args.inputs:
        loaded = load_corpus(p)
        if not loaded.exists:
            print(f"  (skip) not found: {p}")
            continue
        if loaded.parse_errors:
            print(f"  {p}: {len(loaded.parse_errors)} bad line(s) skipped")
        print(f"  {p}: {len(loaded.records)} record(s)")
        lists.append(loaded.records)

    if not lists:
        print("Nothing to merge.")
        return 0

    merged, report = merge_records(lists)
    out = Path(args.out)
    if out.resolve() in {Path(p).resolve() for p in args.inputs if Path(p).exists()}:
        print("Refusing to overwrite an input file — choose a different --out path.")
        return 1
    write_corpus(out, merged)
    print(f"\nMerged {report['inputs']} file(s): {report['total']} records -> "
          f"{report['merged']} after removing {report['removed_duplicate']} duplicate(s).")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
