"""Test strategy profile differentiation (Bin B Item 6 Phase B, v1.5).

Covers:
- Curated profiles return strategy-specific tag sets
- Combo vs Voltron tag sets differ (no heavy overlap)
- Placeholder filter strips utility tags from non-curated strategies
- Utility-defining strategies (Control, Ramp, Pillowfort) keep their utility tags

Run from project root: py -3 tests/test_strategy_profile_differentiation.py
"""
from _test_helpers import TestRun


def main() -> None:
    t = TestRun("test_strategy_profile_differentiation")

    from strategy_knowledge.strategy_selector_catalog import role_tags_for_display_name
    from strategy_knowledge.strategy_role_tag_profiles import profile_count_summary

    # --- Curated count ---
    summary = profile_count_summary()
    t.true("46+ curated profiles loaded",
           summary["total_curated"] >= 46,
           f"got {summary['total_curated']}")

    # --- Combo profile is combo-shaped ---
    combo_tags = role_tags_for_display_name("[Macro] Combo")
    t.in_set("Combo includes combo_piece_possible", "combo_piece_possible", combo_tags)
    t.in_set("Combo includes win_condition", "win_condition", combo_tags)
    t.in_set("Combo includes efficient_tutor", "efficient_tutor", combo_tags)
    t.not_in_set("Combo does NOT include ramp (would starve Ramp bucket)",
                 "ramp", combo_tags)
    t.not_in_set("Combo does NOT include protection",
                 "protection", combo_tags)

    # --- Voltron profile is voltron-shaped ---
    voltron_tags = role_tags_for_display_name("[Mechanical] Voltron")
    t.in_set("Voltron includes equipment_synergy", "equipment_synergy", voltron_tags)
    t.in_set("Voltron includes aura_synergy", "aura_synergy", voltron_tags)
    t.in_set("Voltron includes go_tall_support", "go_tall_support", voltron_tags)
    t.not_in_set("Voltron does NOT include ramp", "ramp", voltron_tags)
    t.not_in_set("Voltron does NOT include card_draw", "card_draw", voltron_tags)

    # --- Combo and Voltron tag sets are mostly disjoint ---
    overlap = combo_tags & voltron_tags
    t.true("Combo and Voltron overlap is small (<=2 tags)",
           len(overlap) <= 2,
           f"overlap: {sorted(overlap)}")

    # --- Utility-defining strategies KEEP utility tags ---
    ramp_tags = role_tags_for_display_name("[Macro] Ramp / Big Mana")
    t.in_set("Ramp/Big Mana DOES include ramp (it IS the strategy)",
             "ramp", ramp_tags)
    t.in_set("Ramp/Big Mana DOES include mana_rock",
             "mana_rock", ramp_tags)

    control_tags = role_tags_for_display_name("[Macro] Control")
    t.in_set("Control DOES include board_wipe (it IS the strategy)",
             "board_wipe", control_tags)
    t.in_set("Control DOES include counterspell",
             "counterspell", control_tags)
    t.in_set("Control DOES include targeted_removal",
             "targeted_removal", control_tags)

    pillowfort_tags = role_tags_for_display_name("[Strategic] Pillowfort")
    t.in_set("Pillowfort DOES include protection (it IS the strategy)",
             "protection", pillowfort_tags)

    # --- Placeholder filter: non-curated strategy returns thematic tags WITHOUT utility tags ---
    non_curated = role_tags_for_display_name("[Niche] Adventures")
    t.true("Non-curated strategy returns at least one thematic tag",
           len(non_curated) > 0,
           f"got: {sorted(non_curated)}")
    utility_leaks = non_curated & {"ramp", "protection", "card_draw", "removal", "recursion", "board_wipe"}
    t.eq("Non-curated strategy does NOT leak utility-conflicting tags",
         utility_leaks, set())

    # --- Empty / bogus lookups ---
    t.eq("Empty string returns empty tag set",
         role_tags_for_display_name(""), set())
    t.eq("'Not selected yet' returns empty tag set",
         role_tags_for_display_name("Not selected yet"), set())
    t.eq("'None' returns empty tag set",
         role_tags_for_display_name("None"), set())

    t.report_and_exit()


if __name__ == "__main__":
    main()
