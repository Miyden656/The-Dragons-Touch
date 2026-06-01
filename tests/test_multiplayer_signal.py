"""Tests for analysis/multiplayer_signal.py — the additive 4-player pod-value signal.

Uses synthetic CardRoleEntry fixtures + a synthetic scryfall_lookup so the test
runs with no downloaded data (no SKIP). Verifies the grounded counts, the
qualitative bands, and the no-crash/defensive behaviour on empty input.
"""
from __future__ import annotations

from collections import Counter

from _test_helpers import TestRun

from analysis.multiplayer_signal import MultiplayerValueSummary, build_multiplayer_summary
from analysis.role_tags import CardRoleEntry, RoleAnalysisSummary
from reports.sections.multiplayer_section import build_multiplayer_report_section

MAJOR_TYPES = ("Creature", "Instant", "Sorcery", "Artifact", "Enchantment", "Land", "Planeswalker", "Battle")


def _entry(name, roles, *, qty=1, type_line="Sorcery"):
    return CardRoleEntry(
        card_name=name,
        quantity=qty,
        found_in_scryfall=True,
        detected_roles=list(roles),
        type_line=type_line,
    )


def _summary(entries):
    role_counts: Counter = Counter()
    type_counts: Counter = Counter()
    for e in entries:
        role_counts.update({tag: e.quantity for tag in e.detected_roles})
        for t in MAJOR_TYPES:
            if t in (e.type_line or ""):
                type_counts[t] += e.quantity
    return RoleAnalysisSummary(
        card_roles=list(entries),
        role_counts=role_counts,
        type_counts=type_counts,
        card_role_tags_by_card={e.card_name: e.detected_roles for e in entries},
        unknown_cards=[],
    )


def _lookup(*pairs):
    """pairs of (name, oracle_text) -> scryfall_lookup keyed by lowercase name."""
    return {name.lower(): {"name": name, "oracle_text": oracle} for name, oracle in pairs}


def main() -> None:
    t = TestRun("test_multiplayer_signal")

    # --- Control shell: real sweeper coverage + counters + instant-speed removal.
    control = _summary([
        _entry("Wrath of God", ["board_wipe"], type_line="Sorcery"),
        _entry("Damnation", ["board_wipe"], type_line="Sorcery"),
        _entry("Toxic Deluge", ["board_wipe"], type_line="Sorcery"),
        _entry("Swords to Plowshares", ["targeted_removal"], type_line="Instant"),
        _entry("Path to Exile", ["targeted_removal"], type_line="Instant"),
        _entry("Beast Within", ["targeted_removal"], type_line="Instant"),
        _entry("Vindicate", ["targeted_removal"], type_line="Sorcery"),
        _entry("Generous Gift", ["targeted_removal"], type_line="Instant"),
        _entry("Counterspell", ["counterspell"], type_line="Instant"),
        _entry("Swan Song", ["counterspell"], type_line="Instant"),
    ])
    ms = build_multiplayer_summary(control, None, None, None)
    t.eq("control: sweepers counted", ms.sweeper_count, 3)
    t.eq("control: spot removal counted", ms.spot_removal_count, 5)
    t.eq("control: counterspells counted", ms.counterspell_count, 2)
    t.eq("control: total interaction", ms.total_interaction, 10)
    # 3 board wipes -> "wide" interaction reach.
    t.eq("control: interaction band wide", ms.interaction_reach_band, "wide")
    # Instant-speed detected from type_line even with no scryfall_lookup:
    # 5 instants (3 STP/Path/BeastWithin/Generous? -> 4 instant removal + 2 counters = 6).
    t.eq("control: instant-speed interaction (type_line)", ms.instant_speed_interaction_count, 6)
    t.in_set("control: sweeper examples present", "Wrath of God", ms.example_cards.get("sweepers", []))

    # --- Go-wide creature deck: no wipes, creature-heavy, thin recursion -> fragile.
    creatures = [_entry(f"Creature {i}", ["synergy_piece"], type_line="Creature") for i in range(30)]
    creatures.append(_entry("Sol Ring", ["fast_mana", "mana_rock"], type_line="Artifact"))
    creatures.append(_entry("Beast Within", ["targeted_removal"], type_line="Instant"))
    gowide = _summary(creatures)
    ms2 = build_multiplayer_summary(gowide, None, None, None)
    t.eq("go-wide: zero sweepers", ms2.sweeper_count, 0)
    t.eq("go-wide: interaction band narrow", ms2.interaction_reach_band, "narrow")
    t.eq("go-wide: creature reliance high", ms2.creature_reliance_band, "high")
    t.eq("go-wide: wipe resilience fragile", ms2.wipe_resilience_band, "fragile")

    # --- Group-slug deck: table-wide pressure dominates.
    slug = _summary([
        _entry("Goblin Bombardment", ["table_damage", "damage_payoff"], type_line="Enchantment"),
        _entry("Bishop of Wings", ["group_slug"], type_line="Creature"),
        _entry("Underworld Dreams", ["draw_punisher", "table_damage", "punisher"], type_line="Enchantment"),
        _entry("Blood Artist", ["lifedrain_payoff"], type_line="Creature"),
        _entry("Witty Lone Striker", ["damage_payoff"], type_line="Creature"),
    ])
    ms3 = build_multiplayer_summary(slug, None, None, None)
    t.true("slug: table-wide pressure counted", ms3.table_wide_pressure_count >= 3)
    t.eq("slug: reach band table_wide", ms3.reach_band, "table_wide")

    # --- Single-target only: damage payoff with no table-wide tags.
    single = _summary([
        _entry("Fireball", ["damage_payoff", "win_condition"], type_line="Sorcery"),
        _entry("Banefire", ["damage_payoff"], type_line="Sorcery"),
    ])
    ms4 = build_multiplayer_summary(single, None, None, None)
    t.eq("single-target: reach band single_target", ms4.reach_band, "single_target")

    # --- Political oracle scan (goad + pillowfort) via synthetic scryfall_lookup.
    pol_entries = _summary([
        _entry("Disrupt Decorum", ["synergy_piece"], type_line="Sorcery"),
        _entry("Marisi, Breaker of the Coil", ["synergy_piece"], type_line="Creature"),
        _entry("Ghostly Prison", ["synergy_piece"], type_line="Enchantment"),
        _entry("Propaganda", ["synergy_piece"], type_line="Enchantment"),
    ])
    pol_lookup = _lookup(
        ("Disrupt Decorum", "Goad all creatures your opponents control."),
        ("Marisi, Breaker of the Coil", "Whenever Marisi deals combat damage, goad each creature."),
        ("Ghostly Prison", "Creatures can't attack you unless their controller pays {2} for each creature."),
        ("Propaganda", "Creatures can't attack you unless their controller pays {2} for each creature."),
    )
    ms5 = build_multiplayer_summary(pol_entries, None, None, pol_lookup)
    t.eq("political: goad detected", ms5.goad_count, 2)
    t.eq("political: pillowfort detected", ms5.pillowfort_count, 2)
    t.true("political: presence band not none", ms5.political_presence_band in {"light", "moderate", "strong"})

    # --- Archenemy / threat density blends bracket pressure-card list.
    class _Bracket:
        pressure_cards = [object(), object(), object(), object(), object()]
    threaty = _summary([
        _entry("Demonic Tutor", ["tutor", "high_bracket_pressure"], type_line="Sorcery"),
        _entry("Thassa's Oracle", ["combo_piece_possible", "win_condition"], type_line="Creature"),
    ])
    ms6 = build_multiplayer_summary(threaty, None, _Bracket(), None)
    t.true("archenemy: threat density includes bracket cards", ms6.threat_density >= 5)
    t.eq("archenemy: risk band medium+", ms6.archenemy_risk_band, "high")

    # --- Defensive: empty / None inputs never raise, return safe defaults.
    empty = build_multiplayer_summary(None, None, None, None)
    t.true("empty: returns summary", isinstance(empty, MultiplayerValueSummary))
    t.eq("empty: zero interaction", empty.total_interaction, 0)
    t.eq("empty: reach none", empty.reach_band, "none")
    t.true("empty: facts still produced", len(empty.facts) >= 1)

    # --- Facts are plain strings, never empty for a real deck.
    t.true("control: facts produced", len(ms.facts) >= 4)
    t.true("control: facts are strings", all(isinstance(f, str) for f in ms.facts))

    # --- Report section: renders headings for a real summary, '' when absent.
    section = build_multiplayer_report_section({"multiplayer_summary": ms})
    t.in_set("report: has section heading", "## Multiplayer / Pod Value", section)
    t.in_set("report: has interaction subsection", "### Interaction Profile", section)
    t.in_set("report: has pod notes", "### Pod Notes", section)
    t.eq("report: empty context -> no section", build_multiplayer_report_section({}), "")
    t.eq("report: None summary -> no section",
         build_multiplayer_report_section({"multiplayer_summary": None}), "")

    t.report_and_exit()


if __name__ == "__main__":
    main()
