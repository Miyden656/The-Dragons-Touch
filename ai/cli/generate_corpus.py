"""Mass-generate training candidates from a folder of decklists (headless).

Runs every deck through a few question types with the local model, auto-discards
anything the safety net flags, and appends the survivors to the corpus as
UNAPPROVED candidates for a human to skim and approve later. This is how the
corpus gets to hundreds of examples without hand-authoring.

    py -3 -m ai.cli.generate_corpus --limit 3            # try 3 decks first (recommended)
    py -3 -m ai.cli.generate_corpus                      # all decks in Decklists/
    py -3 -m ai.cli.generate_corpus --decks-dir Decklists --personas balanced_unknown,pet_card
    py -3 -m ai.cli.generate_corpus --model qwen2.5:7b --limit 10

Then review what it produced:
    py -3 -m ai.cli.manage_corpus --stats
    py -3 -m ai.cli.manage_corpus --show 5

Long-running (each prompt is a real model call ~5-10s). Safe to leave running on
the desktop; prints progress per deck. Candidates are approved=False, so they
stay OUT of the training set until you approve them.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from ai.commander_ai_config import from_settings  # noqa: E402
from ai.commander_ai_service import CommanderAIService  # noqa: E402
from ai.training.corpus import default_corpus_path  # noqa: E402
from ai.training.generate import (  # noqa: E402
    DEFAULT_PROMPT_PLAN,
    append_candidates,
    generate_for_deck,
)


def _load_config():
    try:
        from ui.services.user_settings import load_app_settings
        return from_settings(load_app_settings())
    except Exception:  # noqa: BLE001
        return from_settings({})


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass

    parser = argparse.ArgumentParser(description="Generate training candidates from decklists")
    parser.add_argument("--decks-dir", type=str, default="Decklists", help="Folder of .txt decklists")
    parser.add_argument("--limit", type=int, default=0, metavar="N", help="Only process the first N decks (0 = all)")
    parser.add_argument("--personas", type=str, default="balanced_unknown", help="Comma-separated philosophy keys")
    parser.add_argument("--model", type=str, default="", help="Override the model (default: configured)")
    parser.add_argument("--out", type=str, default="", help="Corpus file to append to (default: Outputs/commander_ai_training_data.jsonl)")
    args = parser.parse_args(argv)

    config = _load_config()
    if args.model:
        config = replace(config, model=args.model)
    config = replace(config, enabled=True)

    import main as app_main
    _cards, lookup, err = app_main.load_scryfall_or_none()
    if err or not lookup:
        print(f"Cannot generate: Scryfall data not loaded ({err}). Settings -> Data Setup.")
        return 0

    service = CommanderAIService(config, scryfall_lookup=lookup)
    avail = service.is_available()
    if not avail.ok:
        print(f"Local model not reachable: {avail.message}")
        return 0

    deck_dir = Path(args.decks_dir)
    decks = sorted(deck_dir.glob("*.txt"))
    if args.limit > 0:
        decks = decks[: args.limit]
    if not decks:
        print(f"No .txt decklists found in {deck_dir}")
        return 0

    personas = [p.strip() for p in args.personas.split(",") if p.strip()] or ["balanced_unknown"]
    out_path = Path(args.out) if args.out else default_corpus_path()

    total_plan = len(decks) * len(personas) * len(DEFAULT_PROMPT_PLAN)
    print(f"Generating from {len(decks)} deck(s) x {len(personas)} persona(s) x "
          f"{len(DEFAULT_PROMPT_PLAN)} prompts = up to {total_plan} candidates")
    print(f"Model: {config.model} | output: {out_path}")
    print("(safety-flagged answers are auto-dropped; survivors saved as unapproved candidates)\n")

    totals = {"generated": 0, "kept": 0, "dropped": 0, "errors": 0, "decks": 0}
    for i, deck in enumerate(decks, start=1):
        for persona in personas:
            try:
                kept, stats = generate_for_deck(
                    deck, service=service, scryfall_lookup=lookup,
                    persona=persona, prompt_plan=DEFAULT_PROMPT_PLAN,
                )
            except Exception as exc:  # noqa: BLE001 - a bad deck must not abort the batch
                totals["errors"] += 1
                print(f"  [{i}/{len(decks)}] {deck.name} ({persona}) — ERROR: {exc}")
                continue
            if kept:
                append_candidates(out_path, kept)
            totals["generated"] += stats["generated"]
            totals["kept"] += stats["kept"]
            totals["dropped"] += stats["dropped"]
            print(f"  [{i}/{len(decks)}] {deck.name} ({persona}) — kept {stats['kept']}, dropped {stats['dropped']}")
        totals["decks"] += 1

    print(f"\nDone. {totals['kept']} candidate(s) kept, {totals['dropped']} dropped, "
          f"{totals['errors']} deck error(s).")
    print(f"Review them:  py -3 -m ai.cli.manage_corpus --stats")
    print(f"They are UNAPPROVED — approve the good ones before training.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
