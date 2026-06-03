"""Pilot-intent plumbing: the intake-window inputs flow into the report + AI guide.

Covers analysis/pilot_intent.py (model, known_themes, report block), the serializer
merge (run-config intent -> AI context), and the user-prompt rendering. Presentation-
only; no model calls. Run via tests/run_all.py.
"""
from __future__ import annotations

from types import SimpleNamespace as NS

from _test_helpers import TestRun

from analysis.pilot_intent import (
    PilotIntent,
    known_themes,
    pilot_intent_from_runtime_config,
    render_pilot_intent_report_block,
)
from ai.context.context_serializer import serialize_context
from ai.schemas.ai_context import CommanderAIContext, CommanderAIRequest
from ai.commander_ai_prompts import build_user_prompt


def main() -> None:
    t = TestRun("pilot_intent")

    # --- known_themes() is sourced from the engine taxonomy (UI dropdowns) ---
    themes = known_themes()
    t.true("known_themes returns the engine archetypes", len(themes) >= 20)
    t.true("known_themes are human-readable labels", "Aristocrats / Sacrifice Value" in themes)

    # --- normalization: strings, comma lists, and lists all coerce cleanly ---
    i = pilot_intent_from_runtime_config(NS(
        pet_cards="Goblin Bombardment, Sol Ring",        # comma string
        declared_constraints=("Budget: $5/card",),       # tuple
        rescue_cards=["Coat of Arms"],                   # list
        hybrid_themes=("Tokens / Go-Wide Combat", "Aristocrats / Sacrifice Value"),
        theme_intent="spooky graveyard goblins",
    ))
    t.eq("pet cards parsed from comma string", i.pet_cards, ("Goblin Bombardment", "Sol Ring"))
    t.eq("rescue cards parsed from list", i.rescue_cards, ("Coat of Arms",))
    t.eq("theme intent kept as text", i.theme_intent, "spooky graveyard goblins")
    t.eq("protected = pet + rescue, deduped",
         i.protected_cards, ("Goblin Bombardment", "Sol Ring", "Coat of Arms"))

    # --- empty intent renders nothing; populated renders all sections ---
    t.eq("empty intent -> empty report block", render_pilot_intent_report_block(PilotIntent()), "")
    block = render_pilot_intent_report_block(i)
    t.true("report block has the header", "## Pilot Intent" in block)
    t.true("report block lists pet cards", "never cut): Goblin Bombardment" in block)
    t.true("report block lists rescue target", "Coat of Arms" in block)
    t.true("report block lists constraint", "Budget: $5/card" in block)
    t.true("report block lists hybrid themes", "Tokens / Go-Wide Combat + Aristocrats" in block)
    t.true("report block lists vibe", "spooky graveyard goblins" in block)

    # --- serializer merges run-config intent into the AI context ---
    rc = NS(pet_cards=("Goblin Bombardment",), declared_constraints=("Budget: $5/card",),
            rescue_cards=("Coat of Arms",),
            hybrid_themes=("Tokens / Go-Wide Combat", "Aristocrats / Sacrifice Value"),
            theme_intent="spooky graveyard goblins")
    ctx = serialize_context({"runtime_config": rc}, CommanderAIRequest(pet_cards=("Krenko, Mob Boss",)))
    t.true("serializer merges request + config pet cards",
           "Krenko, Mob Boss" in ctx.pet_cards and "Goblin Bombardment" in ctx.pet_cards)
    t.eq("serializer carries rescue cards", ctx.rescue_cards, ["Coat of Arms"])
    t.eq("serializer carries theme intent", ctx.theme_intent, "spooky graveyard goblins")

    # --- the new intent renders into the user prompt for the guide ---
    up = build_user_prompt(ctx)
    t.true("user prompt has rescue-target block", "Rescue target" in up and "Coat of Arms" in up)
    t.true("user prompt has themes-to-bridge block", "Themes to bridge" in up)
    t.true("user prompt has theme/vibe block", "spooky graveyard goblins" in up)

    # --- no intent -> no blocks, no crash ---
    bare = build_user_prompt(CommanderAIContext(mode="commander_review"))
    t.true("no intent -> no rescue block", "Rescue target" not in bare)
    t.true("empty runtime config -> empty intent",
           pilot_intent_from_runtime_config(None).is_empty)

    # --- never-cut enforcement: pilot-protected cards move out of cut buckets ---
    from analysis.pilot_intent import apply_pilot_protection_to_cuts
    cuts_obj = NS(
        required_cut_candidates=[NS(card_name="Sol Ring")],
        optional_cut_candidates=[NS(card_name="Goblin Bombardment"), NS(card_name="Divination")],
        manual_review_candidates=[],
        playtest_first_candidates=[NS(card_name="Coat of Arms")],
        protected_from_cut=[NS(card_name="Krenko, Mob Boss")],
        notes=[],
    )
    filtered = apply_pilot_protection_to_cuts(cuts_obj, ("Goblin Bombardment", "Coat of Arms"))
    opt_names = [_entry_name(e) for e in filtered.optional_cut_candidates]
    pt_names = [_entry_name(e) for e in filtered.playtest_first_candidates]
    prot_names = [_entry_name(e) for e in filtered.protected_from_cut]
    t.true("protected card removed from optional cuts", "Goblin Bombardment" not in opt_names)
    t.true("non-protected card stays in optional cuts", "Divination" in opt_names)
    t.true("protected card removed from playtest cuts", "Coat of Arms" not in pt_names)
    t.true("moved cards now appear as protected",
           "Goblin Bombardment" in prot_names and "Coat of Arms" in prot_names)
    t.true("a 'pilot-protected' note was added",
           any("Pilot-protected" in n for n in filtered.notes))
    # nothing to move -> same object back
    t.true("no protected names -> unchanged",
           apply_pilot_protection_to_cuts(cuts_obj, ()) is cuts_obj)

    t.report_and_exit()


def _entry_name(e) -> str:
    return str(getattr(e, "card_name", "") or "")


if __name__ == "__main__":
    main()
