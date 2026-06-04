"""Headless demo for the Deck Coach Workbench data layer (Phase 1).

Loads a real decklist, runs the engine analysis, and prints the persona-voiced
coach view as readable text — the same CoachView the future workbench page renders
and the exporter writes. No Ollama needed (this is deterministic narration of
engine output, not an LLM answer).

    py -3 -m ai.cli.coach_view_demo --deck "Decklists/<file>.txt" --persona pet_card --direction cut_down
    py -3 -m ai.cli.coach_view_demo --deck "Decklists/<file>.txt" --persona competitive_closer --direction build_up

Checkpoint helper: --compare renders the SAME deck through two personas x both
directions back to back, so you can eyeball that the voice + framing actually shift.
    py -3 -m ai.cli.coach_view_demo --deck "Decklists/<file>.txt" --compare pet_card competitive_closer
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from ai.coach.coach_view import (  # noqa: E402
    DIRECTION_BUILD_UP,
    DIRECTION_CUT_DOWN,
    build_coach_view,
)


def _build_analysis(deck_path: Path, persona: str):
    import main
    from config import RuntimeConfig
    from parsing.deck_parser import parse_deck_file

    cards, lookup, err = main.load_scryfall_or_none()
    if err or not lookup:
        print(f"Cannot run coach view: Scryfall data not loaded ({err}).")
        return None
    if not deck_path.exists():
        print(f"Deck file not found: {deck_path}")
        return None

    parsed = parse_deck_file(deck_path, scryfall_lookup=lookup)
    runtime = RuntimeConfig(
        output_mode="normal", review_direction="both", build_up_config={},
        cut_depth_config={}, prompt_interaction_mode="guided",
        philosophy_key=persona, guide_preference="either",
        intended_bracket="Bracket 3", collection_mode="none",
    )
    analysis = main.build_analysis_context(parsed, runtime, lookup, None)
    return analysis, parsed


def _render(analysis, persona: str, presentation: str, direction: str) -> str:
    view = build_coach_view(
        analysis,
        philosophy_key=persona,
        guide_presentation=presentation,
        direction=direction,
    )
    banner = f"{'=' * 70}\n  PERSONA: {persona}  |  DIRECTION: {direction}  |  GUIDE: {view.persona.get('guide_name') or '(lens)'}\n{'=' * 70}"
    return banner + "\n\n" + view.to_text()


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass

    parser = argparse.ArgumentParser(description="Deck Coach Workbench data-layer demo")
    parser.add_argument("--deck", type=str, required=True)
    parser.add_argument("--persona", type=str, default="balanced_unknown")
    parser.add_argument("--presentation", type=str, default="either")
    parser.add_argument("--direction", type=str, default=DIRECTION_CUT_DOWN,
                        choices=[DIRECTION_CUT_DOWN, DIRECTION_BUILD_UP])
    parser.add_argument("--compare", nargs=2, metavar=("PERSONA_A", "PERSONA_B"), default=None,
                        help="Render two personas x both directions for the same deck.")
    args = parser.parse_args(argv)

    built = _build_analysis(Path(args.deck), args.persona if not args.compare else args.compare[0])
    if built is None:
        return 1
    analysis, parsed = built
    print(f"Deck: {parsed.commander_name} ({parsed.deck_card_count} cards)\n")

    if args.compare:
        for persona in args.compare:
            for direction in (DIRECTION_CUT_DOWN, DIRECTION_BUILD_UP):
                print(_render(analysis, persona, args.presentation, direction))
                print()
        return 0

    print(_render(analysis, args.persona, args.presentation, args.direction))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
