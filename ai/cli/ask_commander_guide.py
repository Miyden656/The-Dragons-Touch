"""Headless harness for the Commander AI layer.

Two modes:

1) Connectivity check (no deck):
       py -3 -m ai.cli.ask_commander_guide --check
       py -3 -m ai.cli.ask_commander_guide --prompt "Name three ramp staples."

2) Full deck answer (loads Scryfall, runs the real analysis pipeline, serializes
   context, assembles the prompt, and either calls Ollama or prints the prompt):
       py -3 -m ai.cli.ask_commander_guide --deck "Decklists/104. Izzet test.txt" --mode commander_review --prompt "What does this deck want to do?"
       py -3 -m ai.cli.ask_commander_guide --deck "Decklists/104. Izzet test.txt" --dry-run        # prints the assembled prompt, no Ollama

Flags:
    --deck PATH        Run a full deck answer for this decklist file.
    --mode MODE        Interaction mode (commander_review|cut_review|replacement|
                       build_from_collection|strategy_tutor|persona_coaching).
    --persona KEY      Philosophy key for the analysis (e.g. pet_card, curve_mana_discipline).
    --prompt TEXT      The user's question / request.
    --dry-run          Build + print the assembled system/user prompt; skip Ollama.
    --check            Only run the Ollama availability check.
    --model / --base-url / --temperature / --timeout / --stream / --guide-style
                       Per-run overrides of the persisted settings.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from ai.commander_ai_config import CommanderAIConfig, from_settings  # noqa: E402
from ai.commander_ai_service import CommanderAIService  # noqa: E402
from ai.ollama_client import OllamaClient  # noqa: E402
from ai.schemas.ai_context import ALL_MODES, CommanderAIRequest  # noqa: E402


_SMOKE_SYSTEM_PROMPT = (
    "You are The Dragon's Touch Commander Guide, a local MTG Commander assistant. "
    "Answer briefly and do not invent specific card facts you are unsure of."
)


def _load_config() -> CommanderAIConfig:
    try:
        from ui.services.user_settings import load_app_settings

        return from_settings(load_app_settings())
    except Exception as exc:  # noqa: BLE001
        print(f"(Could not load persisted settings: {exc!r}; using defaults.)")
        return from_settings({})


def _apply_overrides(config: CommanderAIConfig, args: argparse.Namespace) -> CommanderAIConfig:
    changes: dict[str, object] = {}
    if args.model:
        changes["model"] = args.model
    if args.base_url:
        changes["base_url"] = args.base_url
    if args.temperature is not None:
        changes["temperature"] = args.temperature
    if args.timeout is not None:
        changes["timeout_seconds"] = args.timeout
    if args.stream:
        changes["stream"] = True
    if args.guide_style:
        from ai.commander_ai_config import normalize_guide_style

        changes["guide_style"] = normalize_guide_style(args.guide_style)
    return replace(config, **changes) if changes else config


def _print_config(config: CommanderAIConfig) -> None:
    print("=== Commander AI ===")
    for label, value in (
        ("enabled", config.enabled), ("base_url", config.base_url), ("model", config.model),
        ("temperature", config.temperature), ("stream", config.stream),
        ("timeout_seconds", config.timeout_seconds), ("guide_style", config.guide_style),
        ("strict_fact_check", config.strict_fact_check),
    ):
        print(f"  {label:16}: {value}")
    print()


def _run_connectivity(client: OllamaClient, args: argparse.Namespace, config: CommanderAIConfig) -> int:
    avail = client.is_available()
    print(f"Availability: {'OK' if avail.ok else 'UNAVAILABLE'}")
    print(f"  {avail.message}")
    if not avail.ok or args.check or not args.prompt:
        return 0
    print(f"\nSending prompt: {args.prompt!r}\n" + "-" * 60)
    result = client.complete(_SMOKE_SYSTEM_PROMPT, args.prompt)
    print(result.text if result.ok else f"Request failed ({result.kind}): {result.error}")
    print("-" * 60)
    return 0


def _run_deck(args: argparse.Namespace, config: CommanderAIConfig) -> int:
    # Heavy imports are deferred to the deck path so --check stays light.
    import main
    from config import RuntimeConfig
    from parsing.deck_parser import parse_deck_file

    cards, lookup, err = main.load_scryfall_or_none()
    if err or not lookup:
        print(f"Cannot run deck answer: Scryfall data not loaded ({err}).")
        return 0

    deck_path = Path(args.deck)
    if not deck_path.exists():
        print(f"Deck file not found: {deck_path}")
        return 1

    parsed = parse_deck_file(deck_path, scryfall_lookup=lookup)
    print(f"Deck: {parsed.commander_name} ({parsed.deck_card_count} cards) | mode: {args.mode}\n")

    runtime = RuntimeConfig(
        output_mode="normal", review_direction="both", build_up_config={},
        cut_depth_config={}, prompt_interaction_mode="guided",
        philosophy_key=args.persona, guide_preference="either",
        intended_bracket="Bracket 3", collection_mode="none",
    )
    analysis = main.build_analysis_context(parsed, runtime, lookup, None)

    service = CommanderAIService(config, scryfall_lookup=lookup)
    request = CommanderAIRequest(user_text=args.prompt or "", mode=args.mode)

    if args.dry_run:
        ctx, messages = service.build(request, analysis)
        print("=== ASSEMBLED PROMPT (dry run — Ollama not called) ===\n")
        for m in messages:
            print(f"----- {m['role'].upper()} -----")
            print(m["content"])
            print()
        print(f"(uncertainties: {len(ctx.uncertainties)} | warnings: {len(ctx.warnings)})")
        return 0

    print("Contacting local model...\n" + "-" * 60)
    resp = service.answer(request, analysis)
    print(resp.text)
    print("-" * 60)
    if not resp.ok:
        print(f"({resp.error_kind})")
    elif not resp.safety_ok:
        print(f"[safety: {len(resp.safety_flags)} claim(s) flagged]")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Commander AI harness")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--prompt", type=str, default="")
    parser.add_argument("--deck", type=str, default="")
    parser.add_argument("--mode", type=str, default="commander_review", choices=ALL_MODES)
    parser.add_argument("--persona", type=str, default="balanced_unknown")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--model", type=str, default="")
    parser.add_argument("--base-url", type=str, default="")
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--timeout", type=int, default=None)
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--guide-style", type=str, default="")
    args = parser.parse_args(argv)

    config = _apply_overrides(_load_config(), args)
    _print_config(config)

    if args.deck:
        return _run_deck(args, config)
    return _run_connectivity(OllamaClient(config), args, config)


if __name__ == "__main__":
    raise SystemExit(main())
