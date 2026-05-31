"""Build a fine-tune-ready dataset from the curated corpus (headless).

Reads Outputs/commander_ai_training_data.jsonl (the approved answers the
Commander Guide panel saves), cleans it (valid + deduped + approved), and writes
chat-format JSONL where each line is the EXACT inference-time prompt triple
(system + user) paired with the approved answer.

    py -3 -m ai.cli.prepare_training_data                       # -> Outputs/commander_ai_training_dataset.jsonl
    py -3 -m ai.cli.prepare_training_data --with-facts          # also rebuild the verified-card-facts block (loads Scryfall)
    py -3 -m ai.cli.prepare_training_data --in corpus.jsonl --out train.jsonl
    py -3 -m ai.cli.prepare_training_data --include-unapproved  # keep unapproved records too

The output is what Unsloth / Axolotl / LLaMA-Factory consume for QLoRA. See
ai/training/README.md for the end-to-end training recipe.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from ai.training.corpus import default_corpus_path, load_corpus  # noqa: E402
from ai.training.prepare_dataset import corpus_to_dataset, write_dataset  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass

    parser = argparse.ArgumentParser(description="Prepare a fine-tune dataset from the corpus")
    parser.add_argument("--in", dest="in_path", type=str, default="", help="Corpus JSONL (default: Outputs/commander_ai_training_data.jsonl)")
    parser.add_argument("--out", type=str, default="", help="Output dataset JSONL (default: alongside the corpus as commander_ai_training_dataset.jsonl)")
    parser.add_argument("--with-facts", action="store_true", help="Rebuild the verified-card-facts block per example (loads Scryfall)")
    parser.add_argument("--include-unapproved", action="store_true", help="Include records not marked approved")
    args = parser.parse_args(argv)

    in_path = Path(args.in_path) if args.in_path else default_corpus_path()
    out_path = Path(args.out) if args.out else in_path.with_name("commander_ai_training_dataset.jsonl")

    loaded = load_corpus(in_path)
    if not loaded.exists:
        print(f"Corpus not found: {in_path}")
        print("Use the Commander Guide's 'Save as training example' button to build it first.")
        return 0
    if loaded.parse_errors:
        print(f"Note: {len(loaded.parse_errors)} unparseable line(s) skipped (run manage_corpus --validate).")

    lookup = None
    if args.with_facts:
        import main as app_main

        _cards, lookup, err = app_main.load_scryfall_or_none()
        if err or not lookup:
            print(f"WARNING: --with-facts requested but Scryfall isn't loaded ({err}); facts blocks omitted.")
            lookup = None

    examples, report = corpus_to_dataset(
        loaded.records, scryfall_lookup=lookup, approved_only=not args.include_unapproved
    )
    if not examples:
        print("No training examples produced.")
        print(f"  {report}")
        return 0

    write_dataset(out_path, examples)
    print(f"Wrote {report['examples']} training example(s) -> {out_path}")
    print(f"  from {report['started']} record(s):")
    print(f"    dropped unapproved : {report['dropped_unapproved']}")
    print(f"    dropped invalid    : {report['dropped_invalid']}")
    print(f"    dropped duplicate  : {report['dropped_duplicate']}")
    print(f"    dropped unbuildable: {report['dropped_unbuildable']}")
    print(f"  verified-facts blocks: {'rebuilt (Scryfall)' if lookup else 'omitted (use --with-facts)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
