"""Phase 1 (Deck Coach Workbench) tests: build_coach_view restructures the engine
analysis dict into a persona-voiced, structured coach surface.

Synthetic + fast (no Scryfall, no Ollama): stand-in objects use the SAME attribute
names as the real engine dataclasses, so a wrong attribute name shows up as missing
output. Covers: section extraction, persona voicing, the no-invention guard (every
card named in the view came from the input), the cut-down/build-up ordering toggle,
two personas producing different voice, and empty/garbage safety. Run via run_all.py.
"""
from __future__ import annotations

from collections import Counter
from types import SimpleNamespace as NS

from _test_helpers import TestRun

from ai.coach.coach_view import (
    DIRECTION_BUILD_UP,
    DIRECTION_CUT_DOWN,
    build_coach_view,
)


def _sample_analysis() -> dict:
    role_entries = [
        NS(card_name="Sol Ring", quantity=1, detected_roles=["ramp"], mana_value=1),
        NS(card_name="Krenko, Mob Boss", quantity=1, detected_roles=["commander"], mana_value=4),
        NS(card_name="Random Dragon", quantity=1, detected_roles=["beater"], mana_value=6),
    ]
    return {
        "version_label": "TEST v1.6",
        "runtime_config": NS(review_direction="cut_down"),
        "parsed_deck": NS(commander_name="Krenko, Mob Boss", deck_card_count=100),
        "command_zone": NS(
            commander_name="Krenko, Mob Boss",
            commander_names=["Krenko, Mob Boss"],
            companion_names=[],
            command_zone_rule_detected="basic_legendary_creature",
            commander_color_identity=["R"],
            commander_color_identity_text="Mono-Red",
        ),
        "legality": NS(
            deck_size_legal=True, expected_deck_size=100, has_any_issues=False,
            banned_cards=[], banned_commanders=[], color_identity_violations=[],
            cards_not_found=[], illegal_duplicate_cards=[],
        ),
        "role_summary": NS(
            role_counts=Counter({"Ramp": 10, "Lands": 36}),
            type_counts=Counter({"Creature": 30}),
            card_roles=role_entries, unknown_cards=[],
        ),
        "strategy_summary": NS(
            primary_strategy="Goblins / Tokens", secondary_strategy="Aristocrats",
            confidence="high", warnings=[], core_synergy_packages=["Goblin token engine"],
            candidates=[],
        ),
        "plan_fit_summary": NS(
            strong_synergy_cards=[NS(card_name="Krenko, Mob Boss")],
            possible_off_plan_cards=[NS(card_name="Random Dragon", reasons=["off-theme"])],
        ),
        "possible_cuts": NS(
            required_cut_candidates=[],
            optional_cut_candidates=[
                NS(card_name="Random Dragon", cut_confidence="medium",
                   cut_type="off-plan", reasons=["does not support goblins"]),
            ],
            # Intentionally also listed below in playtest_first to test cross-tier dedup.
            manual_review_candidates=[
                NS(card_name="Goblin Bombardment", cut_confidence="low",
                   cut_type="manual_review", reasons=["context-dependent"]),
            ],
            playtest_first_candidates=[
                NS(card_name="Goblin Bombardment", cut_confidence="low",
                   cut_type="playtest", reasons=["context-dependent"]),
            ],
            protected_from_cut=[
                NS(card_name="Krenko, Mob Boss", cut_confidence="n/a",
                   cut_type="protected", reasons=["commander"]),
            ],
            notes=[],
        ),
        "protected_cards": [
            NS(card_name="Skullclamp", protection_level="high", reasons=["card-draw engine"]),
        ],
        "replacement_needs": NS(
            priority_categories=["More targeted removal"],
            need_details=[NS(category="targeted_removal", priority="High", reason="too few answers")],
        ),
        "replacement_candidates": NS(
            top_ranked_candidates=[
                NS(card_name="Chaos Warp", replacement_category="targeted_removal",
                   matched_needs=["targeted_removal"], owned_status="not_owned",
                   confidence="High", why_it_fits="universal answer",
                   why_to_be_careful="random outcome"),
            ],
            candidates=[],
        ),
        "collection_candidates": NS(
            candidate_matching_active=False, strong_candidates=[], possible_candidates=[],
        ),
    }


def _all_card_names(view) -> set[str]:
    names: set[str] = set()
    for c in view.cuts + view.protects + view.add_cards:
        if c.card:
            names.add(c.card)
    return names


def main() -> None:
    t = TestRun("ai_coach_view")
    analysis = _sample_analysis()

    view = build_coach_view(analysis, philosophy_key="pet_card", guide_presentation="feminine")

    # --- persona resolves through the engine registry (not invented) ---
    t.eq("persona key", view.persona.get("key"), "pet_card")
    t.eq("persona label", view.persona.get("label"), "Pet Card")
    t.true("named guide resolved", bool(view.persona.get("guide_name")))
    t.true("persona tone present", bool(view.persona.get("tone")))

    # --- framing: opinion, your call ---
    t.true("disclaimer says opinion", "opinion" in view.disclaimer.lower())
    t.true("opening has pilot authority", "in charge" in view.opening.lower())

    # --- deck plan ---
    t.eq("plan primary", view.deck_plan.get("primary_strategy"), "Goblins / Tokens")
    t.eq("plan secondary", view.deck_plan.get("secondary_strategy"), "Aristocrats")
    t.in_set("synergy package surfaced", "Goblin token engine", view.deck_plan.get("synergy_packages"))

    # --- cuts: engine reasons preserved + voiced, deduped across tiers ---
    t.eq("two cuts after cross-tier dedup", len(view.cuts), 2)
    cut = view.cuts[0]
    t.eq("optional cut leads", cut.card, "Random Dragon")
    t.eq("cut tier", cut.tier, "optional")
    t.in_set("engine reason preserved", "does not support goblins", cut.engine_reasons)
    t.true("cut voiced note present", bool(cut.voiced_note))
    # Goblin Bombardment is in BOTH manual_review and playtest_first; appears once,
    # at its higher tier (manual review).
    bombardment = [c for c in view.cuts if c.card == "Goblin Bombardment"]
    t.eq("duplicate-tier card shown once", len(bombardment), 1)
    t.eq("kept at higher tier", bombardment[0].tier, "manual review")

    # --- protects: dedup across both protected lists ---
    protect_names = {c.card for c in view.protects}
    t.in_set("commander protected", "Krenko, Mob Boss", protect_names)
    t.in_set("skullclamp protected", "Skullclamp", protect_names)
    t.eq("two protects, no dupes", len(view.protects), 2)
    t.true("protect voiced note present", bool(view.protects[0].voiced_note))

    # --- adds: category direction + engine-verified card with caution ---
    t.eq("one add direction", len(view.add_directions), 1)
    t.eq("direction category", view.add_directions[0].category, "targeted_removal")
    t.true("direction voiced", bool(view.add_directions[0].voiced_note))
    t.eq("one add card", len(view.add_cards), 1)
    t.eq("add card name", view.add_cards[0].card, "Chaos Warp")
    t.eq("add card caution preserved", view.add_cards[0].caution, "random outcome")

    # --- NO-INVENTION GUARD: every card named came from the input deck/engine ---
    input_names = {
        "Sol Ring", "Krenko, Mob Boss", "Random Dragon", "Skullclamp", "Chaos Warp",
        "Goblin Bombardment",
    }
    t.true("no invented cards", _all_card_names(view).issubset(input_names))

    # --- direction governs ordering only (same data) ---
    cut_down = build_coach_view(analysis, philosophy_key="pet_card", direction=DIRECTION_CUT_DOWN)
    build_up = build_coach_view(analysis, philosophy_key="pet_card", direction=DIRECTION_BUILD_UP)
    t.eq("cut_down direction", cut_down.direction, DIRECTION_CUT_DOWN)
    t.eq("build_up direction", build_up.direction, DIRECTION_BUILD_UP)
    t.eq("same cut count both directions", len(cut_down.cuts), len(build_up.cuts))
    cd_text, bu_text = cut_down.to_text(), build_up.to_text()
    # Compare the SECTION HEADER positions (not the framing line, which mentions
    # both "cutting" and "build up").
    t.true("cut_down leads with cutting",
           cd_text.index("would look at cutting") < cd_text.index("would build up"))
    t.true("build_up leads with building",
           bu_text.index("would build up") < bu_text.index("would look at cutting"))

    # --- Phase 2: reframed() flips direction WITHOUT recomputing card data ---
    flipped = cut_down.reframed(DIRECTION_BUILD_UP)
    t.eq("reframed flips direction", flipped.direction, DIRECTION_BUILD_UP)
    t.true("reframed reuses cut data (same objects)", flipped.cuts is cut_down.cuts)
    t.eq("reframed matches a fresh build_up text", flipped.to_text(), build_up.to_text())
    t.true("reframed updates the framing line", "build-up mode" in flipped.direction_frame)
    t.true("reframe to same direction is a no-op", cut_down.reframed(DIRECTION_CUT_DOWN) is cut_down)

    # --- two personas produce DIFFERENT voice (the checkpoint, in code) ---
    spike = build_coach_view(analysis, philosophy_key="competitive_closer")
    pet = build_coach_view(analysis, philosophy_key="pet_card")
    t.true("personas differ in cut voice", spike.cuts[0].voiced_note != pet.cuts[0].voiced_note)
    t.true("default direction is cut_down from runtime_config", pet.direction == DIRECTION_CUT_DOWN)

    # --- to_dict round-trips structure ---
    d = view.to_dict()
    t.in_set("to_dict has cuts", "cuts", d)
    t.eq("to_dict cut card", d["cuts"][0]["card"], "Random Dragon")
    t.eq("to_dict schema", d["meta"].get("schema"), "coach_view/v1")

    # --- empty / garbage safety: valid empty view, never raises ---
    empty = build_coach_view(None, philosophy_key="balanced_unknown")
    t.eq("empty cuts", empty.cuts, [])
    t.eq("empty adds", empty.add_cards, [])
    t.true("empty still renders text", bool(empty.to_text()))
    garbage = build_coach_view({"possible_cuts": object(), "strategy_summary": 42},
                               philosophy_key="not_a_real_key")
    t.true("garbage degrades to balanced", garbage.persona.get("key") == "balanced_unknown")
    t.true("garbage renders", bool(garbage.to_text()))

    # --- oversize deck: required-cut context + reframed build-up section ---
    oversize_analysis = _sample_analysis()
    oversize_analysis["parsed_deck"] = NS(commander_name="Krenko, Mob Boss", deck_card_count=155)
    oversize_analysis["cut_pressure"] = NS(required_cuts=55)
    oversize_analysis["possible_cuts"] = NS(
        required_cut_candidates=[
            NS(card_name="Random Dragon", cut_confidence="medium", cut_type="off-plan",
               reasons=["off-theme"]),
        ],
        optional_cut_candidates=[], manual_review_candidates=[], playtest_first_candidates=[],
        protected_from_cut=[], notes=[],
    )
    ov = build_coach_view(oversize_analysis, philosophy_key="pet_card")
    t.true("cut_summary oversize", ov.cut_summary.get("oversize") is True)
    t.eq("cut_summary required_needed", ov.cut_summary.get("required_needed"), 55)
    t.eq("cut_summary over_by", ov.cut_summary.get("over_by"), 55)
    t.eq("cut_summary confident", ov.cut_summary.get("confident_candidates"), 1)
    # The required tier is softened to a candidate label, not a mandate.
    t.eq("required tier relabeled", ov.cuts[0].tier, "required-cut candidate")
    ov_text = ov.to_text()
    t.true("cut section has oversize context", "needs about 55 cuts" in ov_text)
    t.true("not per-card mandate wording", "not per-card mandates" in ov_text)
    # The build-up section is reframed to role gaps (you're trimming, not adding).
    t.true("adds reframed to role gaps", "Role gaps" in ov_text)
    t.true("adds reframe explains trimming", "isn't about adding cards yet" in ov_text)

    # A legal-size deck keeps the normal build-up framing.
    t.true("legal deck not oversize", build_coach_view(_sample_analysis(), philosophy_key="pet_card").cut_summary.get("oversize") is False)

    t.report_and_exit()


if __name__ == "__main__":
    main()
