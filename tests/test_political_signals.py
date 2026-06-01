"""Tests for analysis/political_signals.py — the Section 3 political signal detector.

Synthetic CardRoleEntry fixtures + a synthetic scryfall_lookup so it runs with no
downloaded data. Verifies oracle-pattern detection of the political vocabulary,
the reuse of existing role tags, the commander boolean flags, and defensive
behaviour on empty input.
"""
from __future__ import annotations

from collections import Counter
from types import SimpleNamespace as NS

from _test_helpers import TestRun

from analysis.political_signals import (
    PoliticalSignalProfile,
    build_political_signal_profile,
    infer_political_signals,
)
from analysis.role_tags import CardRoleEntry, RoleAnalysisSummary


def _entry(name, roles=(), *, qty=1, type_line="Sorcery"):
    return CardRoleEntry(
        card_name=name,
        quantity=qty,
        found_in_scryfall=True,
        detected_roles=list(roles),
        type_line=type_line,
    )


def _summary(entries):
    return RoleAnalysisSummary(
        card_roles=list(entries),
        role_counts=Counter(),
        type_counts=Counter(),
        card_role_tags_by_card={e.card_name: e.detected_roles for e in entries},
        unknown_cards=[],
    )


def _lookup(pairs):
    return {name.lower(): {"name": name, "oracle_text": oracle, "type_line": tl}
            for name, oracle, tl in pairs}


def main() -> None:
    t = TestRun("test_political_signals")

    # --- direct oracle inference ---
    goad_tags = infer_political_signals("goad all creatures your opponents control.")
    t.in_set("goad detected", "goad", goad_tags)
    t.in_set("goad implies forced_combat", "forced_combat", goad_tags)

    hug_tags = infer_political_signals("at the beginning of your draw step, each player draws a card.")
    t.in_set("group_draw detected", "group_draw", hug_tags)

    fort_tags = infer_political_signals("creatures can't attack you unless their controller pays {2}.")
    t.in_set("attack_tax detected", "attack_tax", fort_tags)
    t.in_set("fort_protection detected", "fort_protection", fort_tags)

    monarch_tags = infer_political_signals("when this enters, you become the monarch.")
    t.in_set("monarch detected", "monarch", monarch_tags)

    vote_tags = infer_political_signals("will of the council — starting with you, each player votes.")
    t.in_set("vote detected", "vote", vote_tags)

    curse_tags = infer_political_signals("enchant player. at the beginning of enchanted player's upkeep, they lose 1 life.",
                                         type_line="Enchantment — Aura Curse")
    t.in_set("curse detected", "curse", curse_tags)

    pw_tags = infer_political_signals("+1: draw a card.", type_line="Legendary Planeswalker — Teferi")
    t.in_set("planeswalker from type line", "planeswalker", pw_tags)

    # --- full profile with reuse of role tags + counts by quantity ---
    entries = [
        _entry("Disrupt Decorum", type_line="Sorcery"),
        _entry("Propaganda", type_line="Enchantment"),
        _entry("Wrath of God", roles=["board_wipe"], type_line="Sorcery"),
        _entry("Counterspell", roles=["counterspell"], type_line="Instant"),
        _entry("Blood Artist", roles=["lifedrain_payoff"], type_line="Creature"),
        _entry("Thassa's Oracle", roles=["win_condition", "combo_piece_possible"], type_line="Creature"),
    ]
    lookup = _lookup([
        ("Disrupt Decorum", "goad all creatures your opponents control.", "Sorcery"),
        ("Propaganda", "creatures can't attack you unless their controller pays {2} for each creature.", "Enchantment"),
        ("Wrath of God", "destroy all creatures. they can't be regenerated.", "Sorcery"),
        ("Counterspell", "counter target spell.", "Instant"),
        ("Blood Artist", "whenever a creature dies, each opponent loses 1 life and you gain 1 life.", "Creature"),
        ("Thassa's Oracle", "when this enters, look at the top cards. you win the game if...", "Creature"),
    ])
    profile = build_political_signal_profile(_summary(entries), None, lookup)

    t.true("profile returned", isinstance(profile, PoliticalSignalProfile))
    t.true("goad counted from oracle", profile.counts.get("goad", 0) >= 1)
    t.true("attack_tax counted", profile.counts.get("attack_tax", 0) >= 1)
    # reuse: board_wipe role -> board_wipe + board_reset political tags
    t.true("reused board_wipe", profile.counts.get("board_wipe", 0) >= 1)
    t.true("reused board_reset from wipe", profile.counts.get("board_reset", 0) >= 1)
    # reuse: counterspell role -> visible_interaction + control_piece
    t.true("reused visible_interaction", profile.counts.get("visible_interaction", 0) >= 1)
    t.true("reused control_piece", profile.counts.get("control_piece", 0) >= 1)
    # reuse: lifedrain role -> drain/life_loss
    t.true("reused life_loss_engine", profile.counts.get("life_loss_engine", 0) >= 1)
    # win condition role reused
    t.true("reused win_condition", profile.counts.get("win_condition", 0) >= 1)
    t.in_set("signals_by_card carries goad card", "Disrupt Decorum", profile.signals_by_card)

    # --- quantity weighting ---
    qty_entries = [_entry("Mass Goad", qty=2)]
    qty_lookup = _lookup([("Mass Goad", "goad all creatures.", "Sorcery")])
    qprofile = build_political_signal_profile(_summary(qty_entries), None, qty_lookup)
    t.eq("counts by quantity", qprofile.counts.get("goad", 0), 2)

    # --- commander flags ---
    cmd = NS(commander_cards_scryfall=[{"name": "Queen Marchesa",
             "oracle_text": "when this enters, you become the monarch.",
             "type_line": "Legendary Creature"}])
    cprofile = build_political_signal_profile(_summary(entries), cmd, lookup)
    t.true("commander monarch flag", cprofile.flags.get("commander_supports_monarch"))
    t.true("has_clear_win_path from win_condition", cprofile.flags.get("has_clear_win_path"))
    t.true("no false bounty flag", not cprofile.flags.get("commander_supports_bounty"))

    # --- high-threat reputation ---
    villain = NS(commander_cards_scryfall=[{"name": "Tergrid, God of Fright",
                "oracle_text": "whenever an opponent sacrifices a nontoken permanent...",
                "type_line": "Legendary Creature"}])
    vprofile = build_political_signal_profile(_summary([]), villain, {})
    t.true("high-threat reputation flag", vprofile.flags.get("commander_has_high_threat_reputation"))

    # --- defensive: empty / None ---
    empty = build_political_signal_profile(None, None, None)
    t.true("empty -> profile", isinstance(empty, PoliticalSignalProfile))
    t.eq("empty -> no counts", sum(empty.counts.values()), 0)
    t.eq("empty -> win path false", empty.flags.get("has_clear_win_path"), False)

    t.report_and_exit()


if __name__ == "__main__":
    main()
