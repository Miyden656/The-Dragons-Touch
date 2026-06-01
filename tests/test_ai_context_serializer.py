"""Phase 3 tests: the context serializer turns the engine analysis dict into a
compact, engine-verified CommanderAIContext.

Primary test is synthetic (fast, no Scryfall): it builds stand-in objects whose
attribute names match the REAL engine dataclasses, so a wrong attribute name in
the serializer shows up as missing output. Plus a no-invention guard and an
empty-input safety check. Run via tests/run_all.py.
"""
from __future__ import annotations

import json
from collections import Counter
from types import SimpleNamespace as NS

from _test_helpers import TestRun

from ai.context.context_serializer import serialize_context
from ai.schemas.ai_context import CommanderAIRequest
from analysis.multiplayer_signal import MultiplayerValueSummary
from analysis.political_archetypes import DetectedPoliticalArchetype, PoliticalArchetypeSummary


def _sample_analysis() -> dict:
    role_entries = [
        NS(card_name="Sol Ring", quantity=1, detected_roles=["ramp", "mana_rock"],
           mana_value=1, card_types=["Artifact"]),
        NS(card_name="Goblin Bombardment", quantity=1,
           detected_roles=["win_condition", "sacrifice_outlet"], mana_value=2,
           card_types=["Enchantment"]),
        NS(card_name="Krenko, Mob Boss", quantity=1, detected_roles=["commander"],
           mana_value=4, card_types=["Creature"]),
    ]
    return {
        "version_label": "TEST v1.6",
        "runtime_config": NS(intended_bracket="Bracket 3 - Strong Casual"),
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
            role_counts=Counter({"Ramp": 10, "Lands": 36, "Removal": 5}),
            type_counts=Counter({"Creature": 30, "Artifact": 12}),
            card_roles=role_entries, unknown_cards=[],
        ),
        "strategy_summary": NS(
            primary_strategy="Goblins / Tokens", secondary_strategy="Aristocrats",
            confidence="high", warnings=[], core_synergy_packages=["Goblin token engine"],
            candidates=[NS(name="Goblins", score=40, layer="primary",
                           commander_support="heavy", gate_passed=True)],
        ),
        "plan_fit_summary": NS(
            strong_synergy_cards=[NS(card_name="Krenko, Mob Boss")],
            possible_off_plan_cards=[NS(card_name="Random Dragon", reasons=["off-theme"])],
        ),
        "bracket_summary": NS(
            estimated_bracket="Bracket 3", pressure_level="moderate",
            pressure_cards=[NS(card_name="Mana Crypt", pressure_type="fast_mana",
                               reason="adds bracket pressure")],
            notes=["Some pressure cards present"],
        ),
        "multiplayer_summary": MultiplayerValueSummary(
            sweeper_count=1, spot_removal_count=4, counterspell_count=2,
            total_interaction=7, instant_speed_interaction_count=3,
            interaction_reach_band="balanced",
            table_wide_pressure_count=3, single_target_pressure_count=1,
            reach_band="table_wide",
            goad_count=2, pillowfort_count=1, political_presence_band="moderate",
            threat_density=8, archenemy_risk_band="high",
            creature_count=30, recursion_count=2, protection_count=3,
            creature_reliance_band="high", wipe_resilience_band="fragile",
            facts=["Board wipes: 1 - each can answer all three opponents' boards at once."],
            example_cards={"sweepers": ["Goblin Bombardment"], "threats": ["Mana Crypt"]},
            confidence="medium",
        ),
        "political_summary": PoliticalArchetypeSummary(
            is_political=True,
            primary=DetectedPoliticalArchetype(
                key="group_slug", name="Group Slug", section="3.8", axis="punish normal game actions",
                role="primary", confidence="medium", score=70, commander_support="strong",
                gate_passed=True, incentive_present=True, protection_present=True,
                payoff_present=True, inevitability_present=True,
                evidence=["5 core political signal(s)"], example_cards=["Goblin Bombardment"],
            ),
            secondary=None, detected=[],
            reputation_modifier="none", table_dependency="low", salt_risk="medium",
            political_density=7, confidence="medium",
            warnings=["Salt risk: this deck uses effects that may create table frustration."],
        ),
        "possible_cuts": NS(
            required_cut_candidates=[],
            optional_cut_candidates=[NS(card_name="Random Dragon", cut_confidence="medium",
                                        cut_type="off-plan", reasons=["does not support goblins"])],
            manual_review_candidates=[], playtest_first_candidates=[],
            protected_from_cut=[NS(card_name="Krenko, Mob Boss", cut_confidence="n/a",
                                   cut_type="protected", reasons=["commander"])],
            notes=[],
        ),
        "protected_cards": [NS(card_name="Skullclamp", protection_level="high",
                               reasons=["card-draw engine"])],
        "replacement_needs": NS(
            priority_categories=["More targeted removal"],
            need_details=[NS(category="targeted_removal", priority="High",
                             reason="too few answers")],
        ),
        "replacement_candidates": NS(
            top_ranked_candidates=[NS(card_name="Chaos Warp",
                                      replacement_category="targeted_removal",
                                      matched_needs=["targeted_removal"],
                                      owned_status="not_owned", confidence="High",
                                      why_it_fits="universal answer",
                                      why_to_be_careful="random outcome")],
            candidates=[],
        ),
        "collection_candidates": NS(
            candidate_matching_active=True,
            strong_candidates=[NS(card_name="Goblin Chieftain", quantity_owned=1,
                                  confidence="High", matched_needs=["go_wide"],
                                  reason="owned goblin lord")],
            possible_candidates=[],
        ),
        "collection_summary": NS(loaded=True, active=True, ready_for_matching=True,
                                 total_cards=500, unique_cards=300, found_cards=480,
                                 not_found_cards=["Some Misspelled Card"]),
        "philosophy_context": {
            "key": "pet_card", "label": "Pet Card", "guide_name": "Mia",
            "guide_role": "The Pet Card Mentor", "core_question": "Which cards matter to you?",
            "rules_summary": "Protect beloved cards.",
            "protect_bias": ["pet cards", "signature cards"],
            "review_bias": ["pure value cards"], "replacement_bias": ["synergy over raw power"],
        },
    }


def main() -> None:
    t = TestRun("ai_context_serializer")
    analysis = _sample_analysis()
    req = CommanderAIRequest(
        user_text="What should I cut?", mode="cut_review",
        pet_cards=("Goblin Bombardment",), constraints=("keep it mono-red",),
    )
    ctx = serialize_context(analysis, req, guide_style="Strategist")

    # --- commander / deck ---
    t.eq("commander name", ctx.commander.get("commander"), "Krenko, Mob Boss")
    t.eq("color identity", ctx.commander.get("color_identity"), ["R"])
    t.eq("decklist length", len(ctx.decklist), 3)
    names = {c["name"] for c in ctx.decklist}
    t.true("Sol Ring in decklist", "Sol Ring" in names)
    sol = next(c for c in ctx.decklist if c["name"] == "Sol Ring")
    t.eq("Sol Ring roles preserved", sol["roles"], ["ramp", "mana_rock"])
    t.true("role_counts sorted desc", ctx.commander["role_counts"].get("Lands") == 36)

    # --- legality ---
    t.eq("deck size legal", ctx.legality.get("deck_size_legal"), True)
    t.eq("no banned cards", ctx.legality.get("banned_cards"), [])

    # --- strategy + win conditions ---
    t.eq("primary strategy", ctx.strategy.get("primary_strategy"), "Goblins / Tokens")
    t.eq("confidence", ctx.strategy.get("confidence"), "high")
    t.eq("candidate parsed", ctx.strategy["candidates"][0]["name"], "Goblins")
    t.true("off-plan card surfaced", ctx.strategy["possible_off_plan_cards"][0]["card"] == "Random Dragon")
    t.true("win condition detected from role tag", "Goblin Bombardment" in ctx.win_conditions)

    # --- bracket ---
    t.eq("estimated bracket", ctx.bracket.get("estimated_bracket"), "Bracket 3")
    t.eq("intended bracket from runtime_config", ctx.bracket.get("intended_bracket"), "Bracket 3 - Strong Casual")
    t.eq("pressure card", ctx.bracket["pressure_cards"][0]["card"], "Mana Crypt")

    # --- multiplayer / pod value (the additive 4-player signal) ---
    t.eq("mp sweepers", ctx.multiplayer["interaction"]["sweepers"], 1)
    t.eq("mp spot removal", ctx.multiplayer["interaction"]["spot_removal"], 4)
    t.eq("mp interaction band", ctx.multiplayer["interaction"]["reach_band"], "balanced")
    t.eq("mp table reach band", ctx.multiplayer["table_reach"]["band"], "table_wide")
    t.eq("mp goad count", ctx.multiplayer["politics"]["goad"], 2)
    t.eq("mp archenemy risk", ctx.multiplayer["archenemy"]["risk_band"], "high")
    t.eq("mp wipe resilience", ctx.multiplayer["resilience"]["wipe_resilience"], "fragile")
    t.true("mp facts surfaced", len(ctx.multiplayer["facts"]) >= 1)
    t.eq("mp example cards grouped", ctx.multiplayer["example_cards"]["sweepers"], ["Goblin Bombardment"])

    # --- political archetypes (the additive Section-3 classifier) ---
    t.eq("political is_political", ctx.political["is_political"], True)
    t.eq("political primary name", ctx.political["primary"]["name"], "Group Slug")
    t.eq("political primary role", ctx.political["primary"]["role"], "primary")
    t.eq("political primary section", ctx.political["primary"]["section"], "3.8")
    t.eq("political no secondary", ctx.political["secondary"], None)
    t.eq("political table dependency", ctx.political["table_dependency"], "low")
    t.eq("political salt risk", ctx.political["salt_risk"], "medium")
    t.eq("political density carried", ctx.political["political_density"], 7)
    t.true("political warnings surfaced", len(ctx.political["warnings"]) >= 1)
    t.eq("political example card", ctx.political["primary"]["example_cards"], ["Goblin Bombardment"])

    # --- cuts ---
    t.eq("optional cut card", ctx.cuts["optional_cuts"][0]["card"], "Random Dragon")
    t.eq("optional cut reason kept", ctx.cuts["optional_cuts"][0]["reasons"], ["does not support goblins"])
    # protected cards live in their OWN top-level section, NOT under cuts
    t.eq("protected-from-cut card", ctx.protected["protected_from_cut"][0]["card"], "Krenko, Mob Boss")
    t.eq("protected card entry", ctx.protected["protected_cards"][0]["card"], "Skullclamp")
    t.true("cuts block has NO protected_from_cut key", "protected_from_cut" not in ctx.cuts)
    t.true("cuts block has NO protected_cards key", "protected_cards" not in ctx.cuts)

    # --- replacements ---
    t.eq("priority category", ctx.replacements["priority_categories"], ["More targeted removal"])
    t.eq("candidate card", ctx.replacements["candidates"][0]["card"], "Chaos Warp")
    t.eq("candidate careful note kept", ctx.replacements["candidates"][0]["why_to_be_careful"], "random outcome")
    t.eq("collection candidate", ctx.replacements["collection_candidates"][0]["card"], "Goblin Chieftain")

    # --- collection ---
    t.eq("collection loaded", ctx.collection.get("loaded"), True)
    t.eq("collection totals", ctx.collection.get("total_cards"), 500)

    # --- persona (reused from engine, not invented) ---
    t.eq("persona key", ctx.persona.get("key"), "pet_card")
    t.eq("persona guide name", ctx.persona.get("guide_name"), "Mia")
    t.eq("persona protect bias preserved", ctx.persona.get("protect_bias"), ["pet cards", "signature cards"])

    # --- request fields ---
    t.eq("mode normalized", ctx.mode, "cut_review")
    t.eq("guide style normalized", ctx.guide_style, "strategist")
    t.eq("pet cards passed through (user-provided only)", ctx.pet_cards, ["Goblin Bombardment"])
    t.eq("constraints passed through", ctx.user_constraints, ["keep it mono-red"])

    # --- combo not run -> honest uncertainty ---
    t.eq("combo unavailable", ctx.combo.get("available"), False)
    t.true("uncertainty notes combo not run", any("Combo awareness was not run" in u for u in ctx.uncertainties))
    t.true("no false 'no collection' uncertainty", not any("No collection was loaded" in u for u in ctx.uncertainties))

    # --- JSON round-trip ---
    payload_json = ctx.to_json()
    reloaded = json.loads(payload_json)
    t.true("to_json is valid JSON", isinstance(reloaded, dict))
    t.eq("json carries commander", reloaded["commander"]["commander"], "Krenko, Mob Boss")

    # --- NO INVENTION: every card name in output came from the inputs ---
    input_names = {
        "Sol Ring", "Goblin Bombardment", "Krenko, Mob Boss", "Random Dragon",
        "Mana Crypt", "Skullclamp", "Chaos Warp", "Goblin Chieftain",
    }
    leaked = ctx.all_card_names() - input_names
    t.eq("no invented card names in context", leaked, set())

    # --- EMPTY INPUT: no crash, empty + flagged ---
    empty = serialize_context({}, CommanderAIRequest(user_text="hi"))
    t.eq("empty -> no decklist", empty.decklist, [])
    t.eq("empty -> no card names", empty.all_card_names(), set())
    t.true("empty -> flagged as unverified",
           any("No analysis context" in u for u in empty.uncertainties))
    t.true("empty -> still valid JSON", isinstance(json.loads(empty.to_json()), dict))

    # --- DEFENSIVE: garbage objects don't crash ---
    junk = serialize_context({"parsed_deck": object(), "role_summary": None,
                              "strategy_summary": 12345})
    t.true("garbage input did not crash", isinstance(junk.to_payload(), dict))

    t.report_and_exit()


if __name__ == "__main__":
    main()
