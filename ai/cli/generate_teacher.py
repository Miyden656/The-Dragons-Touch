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
from ai.training.generate import (  # noqa: E402
    DEFAULT_PROMPT_PLAN,
    append_candidates,
    build_deck_analysis,
)
from ai.training.persona_affinity import (  # noqa: E402
    INTENT_PERSONAS,
    derive_personas_for_deck,
    intent_persona_sample,
)
from ai.training.teacher import (  # noqa: E402
    TEACHER_MODEL,
    TeacherClient,
    estimate_for_deck,
    generate_teacher_for_deck,
)


def _plan_items(decks, lookup, args) -> list[tuple]:
    """Build the (deck, persona) work list, honoring --deck-derived.

    Deck-derived: each deck contributes Balanced + its top 2 fit personas, plus
    the 4 intent personas across a sampled subset. Otherwise the flat --personas
    list. Derivation is engine-only (no API cost), so it is safe to run before
    the --estimate preview too."""
    if not args.deck_derived:
        flat = [p.strip() for p in args.personas.split(",") if p.strip()] or ["balanced_unknown"]
        return [(d, p) for d in decks for p in flat]

    items: list[tuple] = []
    for d in decks:
        try:
            analysis = build_deck_analysis(d, persona="balanced_unknown", scryfall_lookup=lookup)
            picks = [p.key for p in derive_personas_for_deck(analysis)]
        except Exception:  # noqa: BLE001 - fall back to baseline rather than skip the deck
            picks = ["balanced_unknown"]
        items += [(d, p) for p in picks]
    for d in intent_persona_sample(decks, args.intent_sample):
        items += [(d, p) for p in INTENT_PERSONAS]
    return items


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
    parser.add_argument("--personas", type=str, default="balanced_unknown", help="Comma-separated philosophy keys (ignored when --deck-derived)")
    parser.add_argument("--deck-derived", action="store_true",
                        help="Pick each deck's personas from its engine analysis (Balanced + top 2 fit) instead of --personas")
    parser.add_argument("--intent-sample", type=int, default=12, metavar="N",
                        help="With --deck-derived: also run the 4 intent personas across N sampled decks (0 = off)")
    parser.add_argument("--model", type=str, default=TEACHER_MODEL, help=f"Teacher model (default {TEACHER_MODEL})")
    parser.add_argument("--out", type=str, default="", help="Corpus file to append to")
    parser.add_argument("--max-cost", type=float, default=0.0, metavar="USD", help="Stop once estimated spend exceeds this (0 = no cap)")
    parser.add_argument("--estimate", action="store_true", help="Preview the cost WITHOUT calling the API or spending anything (no key needed)")
    args = parser.parse_args(argv)

    config = _load_config()

    # --estimate works with no key and spends nothing — run it before anything else.
    if args.estimate:
        return _estimate(args, config)

    teacher = TeacherClient(model=args.model)
    if not teacher.available():
        print("ANTHROPIC_API_KEY is not set — this tool calls the paid Claude API.")
        print("  1. Get a key at https://console.anthropic.com (Settings -> API Keys).")
        print("  2. PowerShell:  setx ANTHROPIC_API_KEY \"sk-ant-...\"   (then reopen the terminal)")
        print("\nTip: run with --estimate first to see the cost — it spends nothing and needs no key.")
        return 0

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

    out_path = Path(args.out) if args.out else default_corpus_path()
    work = _plan_items(decks, lookup, args)

    if args.deck_derived:
        sample = intent_persona_sample(decks, args.intent_sample)
        print(f"TEACHER (deck-derived): {args.model} | {len(decks)} deck(s) x (Balanced + top 2 fit) "
              f"+ {len(INTENT_PERSONAS)} intent x {len(sample)} sampled = {len(work)} (deck, persona) "
              f"pairs x {len(DEFAULT_PROMPT_PLAN)} prompts")
    else:
        print(f"TEACHER: {args.model} | {len(work)} (deck, persona) pair(s) x "
              f"{len(DEFAULT_PROMPT_PLAN)} prompts = up to {len(work) * len(DEFAULT_PROMPT_PLAN)} gold examples")
    print(f"Output: {out_path}  (gold answers saved approved=True, safety-verified)\n")

    totals = {"generated": 0, "kept": 0, "dropped": 0, "cost_usd": 0.0, "errors": 0}
    for deck, persona in work:
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
            print(f"  {deck.name} ({persona}) — ERROR: {exc}")
            continue
        if kept:
            append_candidates(out_path, kept)
        for k in ("generated", "kept", "dropped", "cost_usd"):
            totals[k] += stats[k]
        print(f"  {deck.name} ({persona}) — kept {stats['kept']}, "
              f"dropped {stats['dropped']}, ~${stats['cost_usd']:.2f}  (running ~${totals['cost_usd']:.2f})")

    _summarize(totals, out_path)
    return 0


def _estimate(args, config) -> int:
    """Cost preview — assembles prompts locally and prices them; spends nothing."""
    import main as app_main
    _cards, lookup, err = app_main.load_scryfall_or_none()
    if err or not lookup:
        print(f"Cannot estimate: Scryfall data not loaded ({err}).")
        return 0
    decks = sorted(Path(args.decks_dir).glob("*.txt"))
    if args.limit > 0:
        decks = decks[: args.limit]
    if not decks:
        print(f"No .txt decklists found in {args.decks_dir}")
        return 0
    work = _plan_items(decks, lookup, args)

    mode = "deck-derived" if args.deck_derived else "flat personas"
    print(f"COST PREVIEW (no API call, nothing spent) — {mode}: {len(work)} (deck, persona) "
          f"pair(s) x {len(DEFAULT_PROMPT_PLAN)} prompts")
    total = 0.0
    n = 0
    for deck, persona in work:
        try:
            cost, count = estimate_for_deck(
                deck, config=config, scryfall_lookup=lookup,
                persona=persona, prompt_plan=DEFAULT_PROMPT_PLAN,
            )
            total += cost
            n += count
        except Exception:  # noqa: BLE001 - skip un-estimable decks
            continue
    print(f"\nEstimated GOLD examples: ~{n}")
    print(f"Estimated MAX cost: ~${total:.2f}  (conservative — real cost is usually lower)")
    print(f"Per example: ~${(total / n):.3f}" if n else "")
    print("\nThis is a CEILING estimate. To stay safe:")
    print("  • Buy a small prepaid credit balance (e.g. $10) and leave auto-reload OFF —")
    print("    you can never be charged more than you prepaid.")
    print("  • Run a tiny batch first:  --limit 2")
    print("  • Cap a run:  --max-cost 5")
    return 0


def _summarize(totals: dict, out_path) -> None:
    print(f"\nDone. {totals['kept']} gold example(s) kept, {totals['dropped']} dropped, "
          f"{totals['errors']} deck error(s).")
    print(f"Estimated spend: ~${totals['cost_usd']:.2f}")
    print(f"Saved (approved=True) to {out_path}")
    print("Package for training:  py -3 -m ai.cli.prepare_training_data --with-facts")


if __name__ == "__main__":
    raise SystemExit(main())
