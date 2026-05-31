"""Review and approve training candidates, one at a time (interactive).

The generator produces UNAPPROVED candidates; this is the quick keep/toss pass
that turns them into training data. For each candidate you see the commander,
mode, question, and answer, then press a key:

    k  keep   (mark approved -> goes into training)
    r  reject (drop it from the corpus)
    s  skip   (leave unapproved, decide later)
    q  quit   (save decisions so far and exit)

    py -3 -m ai.cli.review_corpus              # review unapproved candidates
    py -3 -m ai.cli.review_corpus --all        # also re-review already-approved ones

A .bak of the corpus is written before changes. The decision logic lives in
ai/training/corpus.apply_review_decisions (pure + tested); this file is just the
prompt loop.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from ai.training.corpus import (  # noqa: E402
    apply_review_decisions,
    default_corpus_path,
    load_corpus,
    write_corpus,
)


def _short(text: str, width: int) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= width else text[: width - 1] + "…"


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass

    parser = argparse.ArgumentParser(description="Review/approve training candidates")
    parser.add_argument("--path", type=str, default="")
    parser.add_argument("--all", action="store_true", help="Also review already-approved records")
    args = parser.parse_args(argv)

    path = Path(args.path) if args.path else default_corpus_path()
    loaded = load_corpus(path)
    if not loaded.exists:
        print(f"Corpus not found: {path}")
        return 0

    # Indices to review: unapproved by default, or everything with --all.
    review_idx = [
        i for i, r in enumerate(loaded.records)
        if args.all or r.get("approved") is not True
    ]
    if not review_idx:
        print("Nothing to review — no unapproved candidates. (Use --all to re-review approved ones.)")
        return 0

    print(f"Reviewing {len(review_idx)} candidate(s) in {path}")
    print("Keys:  [k]eep   [r]eject   [s]kip   [q]uit-and-save\n")

    decisions: dict = {}
    for n, idx in enumerate(review_idx, start=1):
        rec = loaded.records[idx]
        print(f"--- {n}/{len(review_idx)} ---")
        print(f"  commander : {rec.get('commander', '')}")
        print(f"  mode      : {rec.get('mode', '')}   persona: {rec.get('persona', '')}   "
              f"source: {rec.get('source', 'panel')}   approved: {rec.get('approved')}")
        print(f"  Q: {_short(rec.get('question', ''), 110)}")
        print(f"  A: {_short(rec.get('answer', ''), 600)}")
        try:
            choice = input("  keep/reject/skip/quit [k/r/s/q]? ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n(input closed)")
            break
        if choice in ("q", "quit"):
            break
        if choice in ("k", "keep"):
            decisions[idx] = "keep"
            print("  -> kept\n")
        elif choice in ("r", "reject"):
            decisions[idx] = "reject"
            print("  -> rejected\n")
        else:
            print("  -> skipped\n")

    if not decisions:
        print("No decisions made; corpus unchanged.")
        return 0

    backup = path.with_suffix(path.suffix + ".bak")
    write_corpus(backup, loaded.records)
    updated, summary = apply_review_decisions(loaded.records, decisions)
    write_corpus(path, updated)
    print(f"\nDone. kept {summary['kept']}, rejected {summary['rejected']}, "
          f"{summary['remaining']} record(s) remain.")
    print(f"Backup of the original: {backup}")
    print("Package approved data for training:  py -3 -m ai.cli.prepare_training_data --with-facts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
