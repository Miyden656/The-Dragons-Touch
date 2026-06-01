"""Tests for analysis/political_archetypes.py — the Section-3 political classifier.

Drives the classifier with hand-built PoliticalSignalProfile fixtures (Counter +
flags) so it runs with no data and lets us aim a deck at a specific archetype's
verbatim gate. Verifies gate firing, role assignment, suppression of the generic
'Politics' theme, modifier-only handling, warnings, and defensive empty input.
"""
from __future__ import annotations

from collections import Counter

from _test_helpers import TestRun

from analysis.political_archetypes import (
    ARCHETYPES_BY_KEY,
    POLITICAL_ARCHETYPES,
    PoliticalArchetypeSummary,
    classify_political_archetypes,
)
from analysis.political_signals import PoliticalSignalProfile
from reports.sections.political_section import build_political_report_section


def _profile(counts: dict, flags: dict | None = None, signals_by_card: dict | None = None):
    base_flags = {"has_clear_win_path": True, "has_proactive_win_path": True,
                  "has_clear_inevitability_engine": True}
    base_flags.update(flags or {})
    return PoliticalSignalProfile(
        counts=Counter(counts), flags=base_flags,
        signals_by_card=signals_by_card or {}, commander_text="",
    )


def main() -> None:
    t = TestRun("test_political_archetypes")

    # --- catalog integrity ---
    t.true("catalog has ~42 archetypes", len(POLITICAL_ARCHETYPES) >= 42)
    keys = [a.key for a in POLITICAL_ARCHETYPES]
    t.eq("keys are unique", len(keys), len(set(keys)))
    t.true("every gate is callable", all(callable(a.gate) for a in POLITICAL_ARCHETYPES))
    t.true("sections present", all(a.section.startswith("3.") for a in POLITICAL_ARCHETYPES))

    # --- Group Hug primary (3.7 gate) ---
    hug = classify_political_archetypes(_profile(
        {"group_draw": 4, "hug_payoff": 2, "win_condition": 1},
        signals_by_card={"Howling Mine": ["group_draw"], "Rites of Flourishing": ["group_draw", "group_ramp"]},
    ))
    t.true("group hug is political", hug.is_political)
    t.eq("group hug primary", hug.primary.key, "group_hug")
    t.eq("group hug gate passed", hug.primary.gate_passed, True)
    t.true("group hug example cards attributed", len(hug.primary.example_cards) >= 1)
    t.true("group hug kingmaker warning", any("Kingmaker" in w for w in hug.warnings))
    # §3.50 replacement categories + §3.49 cut guidance attached
    t.true("group hug has replacement categories", len(hug.primary.replacement_categories) >= 3)
    t.true("group hug replacement is category text", "More asymmetrical payoff" in hug.primary.replacement_categories)
    t.true("political deck has §3.49 cut guidance", bool(hug.cut_guidance.get("do_not_auto_cut")))
    t.true("cut guidance has raise-pressure list", bool(hug.cut_guidance.get("raise_cut_pressure")))

    # --- Group Slug primary (3.8 gate, no win-path needed) ---
    slug = classify_political_archetypes(_profile(
        {"table_damage": 5, "drain_payoff": 2, "protection": 2}, flags={"has_clear_win_path": False},
    ))
    t.eq("group slug primary", slug.primary.key, "group_slug")

    # --- Goad / Forced Combat primary (3.11 gate) ---
    goad = classify_political_archetypes(_profile({"goad": 4, "combat_payoff": 3, "win_condition": 1}))
    t.eq("forced combat primary", goad.primary.key, "forced_combat")
    t.eq("forced combat table dependency", goad.table_dependency, "medium")

    # --- Monarch via commander support (3.15 gate) ---
    monarch = classify_political_archetypes(_profile(
        {"crown_defense": 3, "win_condition": 1}, flags={"commander_supports_monarch": True},
    ))
    t.eq("monarch primary via commander", monarch.primary.key, "monarch")
    t.true("monarch commander support", monarch.primary.commander_support in {"moderate", "strong"})

    # --- Voting primary (3.14 gate) ---
    vote = classify_political_archetypes(_profile({"vote": 4, "vote_payoff": 2, "win_condition": 1}))
    t.eq("voting primary", vote.primary.key, "voting")

    # --- Suppression: specific archetype beats generic Politics (3.6) ---
    both = classify_political_archetypes(_profile({
        "vote": 4, "vote_payoff": 2, "win_condition": 1,
        "political_choice": 4, "political_payoff": 2,  # generic deal_politics also eligible
    }))
    t.true("specific beats generic: primary not generic", not ARCHETYPES_BY_KEY[both.primary.key].generic)
    deal = next((d for d in both.detected if d.key == "deal_politics"), None)
    t.true("generic politics demoted out of primary", deal is None or deal.role != "primary")

    # --- Board Reset Politics (3.39 gate). Needs a real parity-breaker — a plain
    # pile of wraths is not "political" and must NOT promote (component guard). ---
    reset = classify_political_archetypes(_profile(
        {"board_wipe": 4, "break_parity": 2, "recursion": 3, "win_condition": 1}))
    t.eq("board reset primary", reset.primary.key, "board_reset_politics")
    t.eq("board reset salt risk high", reset.salt_risk, "high")
    t.true("board reset salt warning", any("Salt" in w for w in reset.warnings))

    # --- Reputation modifier (3.48) from high-threat commander ---
    rep = classify_political_archetypes(_profile(
        {}, flags={"commander_has_high_threat_reputation": True}))
    t.eq("reputation modifier high", rep.reputation_modifier, "high")
    t.true("reputation warning present", any("Reputation" in w for w in rep.warnings))
    modifier = next((d for d in rep.detected if d.key == "reputation"), None)
    t.true("reputation listed as modifier", modifier is not None and modifier.role == "modifier")

    # --- gate that needs a win path: fails without it ---
    no_win_hug = classify_political_archetypes(_profile(
        {"group_draw": 4, "hug_payoff": 2}, flags={"has_clear_win_path": False}))
    t.true("group hug NOT primary without win path",
           no_win_hug.primary is None or no_win_hug.primary.key != "group_hug")

    # --- a thin theme is suppressed, not promoted ---
    thin = classify_political_archetypes(_profile({"goad": 1}))
    t.true("single goad card -> not political", not thin.is_political)

    # --- defensive: empty profile never raises ---
    empty = classify_political_archetypes(_profile({}))
    t.true("empty -> summary", isinstance(empty, PoliticalArchetypeSummary))
    t.eq("empty -> not political", empty.is_political, False)
    t.eq("empty -> no primary", empty.primary, None)
    t.eq("empty -> reputation none", empty.reputation_modifier, "none")

    junk = classify_political_archetypes(PoliticalSignalProfile(counts=Counter(), flags={}, signals_by_card={}))
    t.true("missing flags did not crash", isinstance(junk, PoliticalArchetypeSummary))

    # --- report section: renders for a political deck, '' for non-political ---
    section = build_political_report_section({"political_summary": hug})
    t.in_set("report: section heading", "## Political / Pod Archetypes", section)
    t.in_set("report: strategy read subsection", "### Political Strategy Read", section)
    t.in_set("report: primary axis named", "Group Hug", section)
    t.in_set("report: cut & replacement guidance subsection", "### Political Cut & Replacement Guidance", section)
    t.in_set("report: replacement category rendered", "More asymmetrical payoff", section)
    t.eq("report: non-political deck -> no section",
         build_political_report_section({"political_summary": empty}), "")
    t.eq("report: missing summary -> no section", build_political_report_section({}), "")

    t.report_and_exit()


if __name__ == "__main__":
    main()
