"""Phase 3 (Deck Coach Workbench) tests: the steering wheel.

The user's picks (keep / cut / add / note) translate into the EXISTING user-intent
channels and steer the Commander Guide WITHOUT changing the prompt format. The
headless checkpoint: serialize a context from a picks-derived request and confirm
the Guide context reflects the chosen target (keeps as pet_cards, cut/add as
declared constraints). Synthetic + fast. Run via run_all.py.
"""
from __future__ import annotations

from types import SimpleNamespace as NS

from _test_helpers import TestRun

from ai.coach.coach_picks import (
    CoachPicks,
    build_request,
    picks_to_request_inputs,
    picks_to_runtime_overlay,
)
from ai.context.context_serializer import serialize_context
from ai.schemas.ai_context import MODE_CUT_REVIEW


def _minimal_analysis() -> dict:
    # No runtime_config -> pilot intent is empty, so ctx.pet_cards / user_constraints
    # come purely from the picks-derived request. That is exactly what we want to prove.
    return {
        "version_label": "TEST v1.6",
        "parsed_deck": NS(commander_name="Krenko, Mob Boss", deck_card_count=100),
        "command_zone": NS(
            commander_name="Krenko, Mob Boss",
            commander_names=["Krenko, Mob Boss"],
            commander_color_identity=["R"],
        ),
    }


def main() -> None:
    t = TestRun("ai_coach_picks")

    picks = CoachPicks(
        keep=["Sol Ring", "Skullclamp", "Sol Ring"],  # dup on purpose
        cut=["Random Dragon", "Lone Wolf"],
        add=["Chaos Warp"],
        note="lean harder into goblins",
    )

    # --- model basics ---
    t.true("not empty", not picks.is_empty())
    t.true("empty picks is_empty", CoachPicks().is_empty())
    round_trip = CoachPicks.from_dict(picks.to_dict())
    t.eq("round-trips keep (deduped)", round_trip.keep, ["Sol Ring", "Skullclamp"])
    t.eq("round-trips note", round_trip.note, "lean harder into goblins")

    # --- translate into request inputs (the existing intent channels) ---
    inputs = picks_to_request_inputs(picks)
    t.eq("keeps -> pet_cards (deduped)", inputs["pet_cards"], ("Sol Ring", "Skullclamp"))
    cons = inputs["constraints"]
    t.true("cut intent phrased", any(c.startswith("Planning to cut:") and "Random Dragon" in c for c in cons))
    t.true("add intent phrased", any(c.startswith("Considering adding:") and "Chaos Warp" in c for c in cons))
    t.in_set("note carried as constraint", "lean harder into goblins", cons)

    # --- build_request: a ready CommanderAIRequest with mode fallback ---
    req = build_request(picks, user_text="What should I change?", mode=MODE_CUT_REVIEW)
    t.eq("request mode", req.mode, MODE_CUT_REVIEW)
    t.eq("request pet_cards", req.pet_cards, ("Sol Ring", "Skullclamp"))
    t.true("request carries cut intent", any("Random Dragon" in c for c in req.constraints))
    bad_mode = build_request(picks, mode="not_a_mode")
    t.eq("bad mode falls back to commander_review", bad_mode.mode, "commander_review")

    # --- runtime overlay: keys a refined analysis run recognises as intent ---
    overlay = picks_to_runtime_overlay(picks)
    t.eq("overlay protects keeps", overlay["protected_cards"], ["Sol Ring", "Skullclamp"])
    t.true("overlay declares cut/add intent",
           any("Random Dragon" in c for c in overlay["declared_constraints"]))

    # --- ★ CHECKPOINT: the Guide context reflects the chosen target ---
    ctx = serialize_context(_minimal_analysis(), req)
    t.in_set("ctx pet_cards has Sol Ring", "Sol Ring", ctx.pet_cards)
    t.in_set("ctx pet_cards has Skullclamp", "Skullclamp", ctx.pet_cards)
    t.true("ctx constraints reflect cut target",
           any("Random Dragon" in c for c in ctx.user_constraints))
    t.true("ctx constraints reflect add target",
           any("Chaos Warp" in c for c in ctx.user_constraints))
    t.in_set("ctx constraints carry the note", "lean harder into goblins", ctx.user_constraints)
    # The picks did NOT invent a new prompt field — they rode the existing channels.
    t.eq("mode unchanged by picks", ctx.mode, MODE_CUT_REVIEW)

    # --- empty picks are a clean no-op ---
    empty_inputs = picks_to_request_inputs(CoachPicks())
    t.eq("empty -> no pet_cards", empty_inputs["pet_cards"], ())
    t.eq("empty -> no constraints", empty_inputs["constraints"], ())
    t.eq("empty overlay is empty", picks_to_runtime_overlay(CoachPicks()), {})

    t.report_and_exit()


if __name__ == "__main__":
    main()
