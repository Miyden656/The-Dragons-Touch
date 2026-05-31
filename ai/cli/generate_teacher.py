"""Generate GOLD training examples with a strong teacher model (headless).

Knowledge distillation: Claude (the teacher) answers the same grounded prompts
the local layer assembles, and we save those answers as approved, safety-checked
gold training data. The local qwen2.5:7b is later fine-tuned to imitate them.

    setx ANTHROPIC_API_KEY "sk-ant-..."      # once, then reopen the terminal
    py -3 -m ai.cli.generate_teacher --limit 2          # try 2 decks first
    py -3 -m ai.cli.generate_teacher                    # all decks in Decklists/
    py -3 -m ai.cli.generate_teacher --personas balanced_unknown,pet_card

Needs ANTHROPIC_API_KEY (console.anthropic.com) — this calls the paid Claude API.
Each gold answer costs roughly $0.10-0.20; the tool prints the running total so
there are no surprises. Survivors are saved approved=True (already curated by
the teacher + the safety net); review them anytime with manage_corpus.
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
from ai.training.corpus import default_corpus_path  # noqa: E402
from ai.training.generate import DEFAULT_PROMPT_PLAN, append_candidates  # noqa: E402
from ai.training.teacher import TEACHER_MODEL, TeacherClient, generate_teacher_for_deck  # noqa: E402


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

    parser = argparse.ArgumentParser(description="Generate gold training examples with a teacher model")
    parser.add_argument("--decks-dir", type=str, default="Decklists")
    parser.add_argument("--limit", type=int, default=0, metavar="N", help="Only the first N decks (0 = all)")
    parser.add_argument("--personas", type=str, default="balanced_unknown", help="Comma-separated philosophy keys")
    parser.add_argument("--model", type=str, default=TEACHER_MODEL, help=f"Teacher model (default {TEACHER_MODEL})")
    parser.add_argument("--out", type=str, default="", help="Corpus file to append to")
    parser.add_argument("--max-cost", type=float, default=0.0, metavar="USD", help="Stop once estimated spend exceeds this (0 = no cap)")
    args = parser.parse_args(argv)

    teacher = TeacherClient(model=args.model)
    if not teacher.available():
        print("ANTHROPIC_API_KEY is not set — this tool calls the paid Claude API.")
        print("  1. Get a key at https://console.anthropic.com (Settings -> API Keys).")
        print("  2. PowerShell:  setx ANTHROPIC_API_KEY \"sk-ant-...\"   (then reopen the terminal)")
        return 0

    config = _load_config()

    import main as app_main
    _cards, lookup, err = app_main.load_scryfall_or_none()
    if err or not lookup:
        print(f"Cannot generate: Scryfall data not loaded ({err}).")
        return 0

    decks = sorted(Path(args.decks_dir).glob("*.txt"))
    if args.limit > 0:
        decks = decks[: args.limit]
    if not decks:
        print(f"No .txt decklists found in {args.decks_dir}")
        return 0

    personas = [p.strip() for p in args.personas.split(",") if p.strip()] or ["balanced_unknown"]
    out_path = Path(args.out) if args.out else default_corpus_path()

    total_plan = len(decks) * len(personas) * len(DEFAULT_PROMPT_PLAN)
    print(f"TEACHER: {args.model} | {len(decks)} deck(s) x {len(personas)} persona(s) x "
          f"{len(DEFAULT_PROMPT_PLAN)} prompts = up to {total_plan} gold examples")
    print(f"Output: {out_path}  (gold answers saved approved=True, safety-verified)\n")

    totals = {"generated": 0, "kept": 0, "dropped": 0, "cost_usd": 0.0, "errors": 0}
    for i, deck in enumerate(decks, start=1):
        for persona in personas:
            if args.max_cost and totals["cost_usd"] >= args.max_cost:
                print(f"\nReached --max-cost ${args.max_cost:.2f} (spent ~${totals['cost_usd']:.2f}); stopping.")
                _summarize(totals, out_path)
                return 0
            try:
                kept, stats = generate_teacher_for_deck(
                    deck, teacher=teacher, config=config, scryfall_lookup=lookup,
                    persona=persona, prompt_plan=DEFAULT_PROMPT_PLAN,
                )
            except Exception as exc:  # noqa: BLE001
                totals["errors"] += 1
                print(f"  [{i}/{len(decks)}] {deck.name} ({persona}) — ERROR: {exc}")
                continue
            if kept:
                append_candidates(out_path, kept)
            for k in ("generated", "kept", "dropped", "cost_usd"):
                totals[k] += stats[k]
            print(f"  [{i}/{len(decks)}] {deck.name} ({persona}) — kept {stats['kept']}, "
                  f"dropped {stats['dropped']}, ~${stats['cost_usd']:.2f}  (running ~${totals['cost_usd']:.2f})")

    _summarize(totals, out_path)
    return 0


def _summarize(totals: dict, out_path) -> None:
    print(f"\nDone. {totals['kept']} gold example(s) kept, {totals['dropped']} dropped, "
          f"{totals['errors']} deck error(s).")
    print(f"Estimated spend: ~${totals['cost_usd']:.2f}")
    print(f"Saved (approved=True) to {out_path}")
    print("Package for training:  py -3 -m ai.cli.prepare_training_data --with-facts")


if __name__ == "__main__":
    raise SystemExit(main())
