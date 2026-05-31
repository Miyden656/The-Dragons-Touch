"""Card-name role-tag overrides (Item 6 Phase A, v1.5.44).

The keyword pattern matcher in analysis/role_tags.py is broad but unavoidably
misses cases where:

- The behavior is implicit in a mechanic that doesn't appear verbatim in oracle
  text (e.g., Cyclonic Rift's "wipe" only manifests under Overload, which the
  oracle text describes structurally rather than directly).
- The card is a famous EDH staple that every player knows is a combo piece,
  but the role tagger can't infer that from the oracle alone.
- A keyword fires false-positively against an unrelated phrase (e.g., a tutor
  that says "exile all cards from the top of your library" should NOT be a
  board_wipe — handled mostly by the pattern fixes, but a few residuals).

This module is the curated override layer. It runs AFTER pattern matching, so
it can both ADD missing tags and REMOVE incorrect ones. Card names are matched
case-insensitively against the canonical Scryfall name.

Boundaries:
- Override entries should be reserved for high-impact cards (EDH staples,
  popular combo pieces, cards we've confirmed are mis-tagged).
- Do NOT use this module to patch entire role categories — that belongs in the
  patterns. Use it for genuine edge cases.
- Override entries should include both `add` and `remove` lists when relevant,
  so the resulting tag set is correct, not just augmented.
"""
from __future__ import annotations

from typing import Iterable


# Each entry: {"add": [tags to add], "remove": [tags to remove]}.
# Card names use Scryfall's canonical form (case-insensitive lookup).
ROLE_TAG_OVERRIDES: dict[str, dict[str, list[str]]] = {
    # ----------------------------------------------------------------- Wipes
    # Cyclonic Rift's normal text says "target nonland permanent"; the wipe
    # is only via overload, which the oracle describes structurally.
    "cyclonic rift": {
        "add": ["board_wipe", "targeted_removal"],
        "remove": [],
    },
    # Pernicious Deed activates for X — tagger can miss it.
    "pernicious deed": {
        "add": ["board_wipe", "mana_sink"],
        "remove": [],
    },

    # ----------------------------------------------------------------- Tutors / combo finishers
    # Demonic Consultation: not a board wipe; it's a tutor that wins via Thoracle.
    "demonic consultation": {
        "add": ["tutor", "combo_piece_possible"],
        "remove": ["board_wipe"],
    },
    "tainted pact": {
        "add": ["tutor", "combo_piece_possible"],
        "remove": ["board_wipe"],
    },
    "thassa's oracle": {
        # already tagged combo_piece_possible+win_condition by patterns; just
        # ensure these stick if pattern logic changes.
        "add": ["combo_piece_possible", "win_condition"],
        "remove": [],
    },
    "demonic tutor": {
        "add": ["tutor", "efficient_tutor", "bracket_pressure"],
        "remove": [],
    },
    "vampiric tutor": {
        "add": ["tutor", "efficient_tutor", "bracket_pressure", "card_selection"],
        "remove": [],
    },
    "imperial seal": {
        "add": ["tutor", "efficient_tutor", "bracket_pressure", "card_selection"],
        "remove": [],
    },
    "enlightened tutor": {
        "add": ["tutor", "efficient_tutor", "bracket_pressure"],
        "remove": [],
    },
    "mystical tutor": {
        "add": ["tutor", "efficient_tutor", "bracket_pressure"],
        "remove": [],
    },
    "worldly tutor": {
        "add": ["tutor", "efficient_tutor", "bracket_pressure"],
        "remove": [],
    },

    # ----------------------------------------------------------------- Storm / graveyard combo enablers
    "lion's eye diamond": {
        "add": ["combo_piece_possible"],
        "remove": [],
    },
    "underworld breach": {
        "add": ["combo_piece_possible", "spell_recursion_possible", "graveyard_enabler"],
        "remove": [],
    },
    "yawgmoth's will": {
        "add": ["combo_piece_possible", "spell_recursion_possible", "graveyard_enabler"],
        "remove": [],
    },
    "past in flames": {
        "add": ["combo_piece_possible", "spell_recursion_possible", "graveyard_enabler"],
        "remove": [],
    },
    "mana vault": {
        "add": ["combo_piece_possible"],
        "remove": [],
    },
    "grim monolith": {
        "add": ["combo_piece_possible", "mana_rock", "ramp"],
        "remove": [],
    },
    "basalt monolith": {
        "add": ["combo_piece_possible", "mana_rock", "ramp"],
        "remove": [],
    },
    "rite of flame": {
        "add": ["ritual", "ramp", "fast_mana", "combo_piece_possible"],
        "remove": [],
    },
    "dark ritual": {
        "add": ["ritual", "ramp", "fast_mana", "bracket_pressure"],
        "remove": [],
    },
    "cabal ritual": {
        "add": ["ritual", "ramp", "fast_mana"],
        "remove": [],
    },
    "brain freeze": {
        # already combo_piece_possible from patterns; add explicit win_condition
        # since 0-mana storm killer.
        "add": ["combo_piece_possible", "win_condition", "spell_payoff"],
        "remove": [],
    },

    # ----------------------------------------------------------------- Sacrifice combo outlets
    "phyrexian altar": {
        "add": ["combo_piece_possible", "free_sacrifice_outlet", "sacrifice_outlet"],
        "remove": [],
    },
    "ashnod's altar": {
        "add": ["combo_piece_possible", "free_sacrifice_outlet", "sacrifice_outlet"],
        "remove": [],
    },
    "viscera seer": {
        "add": ["combo_piece_possible", "free_sacrifice_outlet", "sacrifice_outlet", "card_selection"],
        "remove": [],
    },
    "woe strider": {
        "add": ["combo_piece_possible", "free_sacrifice_outlet", "sacrifice_outlet"],
        "remove": [],
    },
    "carrion feeder": {
        "add": ["combo_piece_possible", "free_sacrifice_outlet", "sacrifice_outlet"],
        "remove": [],
    },

    # ----------------------------------------------------------------- Blink / flicker combo enablers
    "displacer kitten": {
        "add": ["combo_piece_possible", "blink_flicker", "synergy_piece"],
        "remove": [],
    },
    "emiel the blessed": {
        "add": ["combo_piece_possible", "blink_flicker"],
        "remove": [],
    },
    "eldrazi displacer": {
        "add": ["combo_piece_possible", "blink_flicker"],
        "remove": [],
    },
    "restoration angel": {
        "add": ["combo_piece_possible", "blink_flicker", "protection"],
        "remove": [],
    },
    "saffi eriksdotter": {
        "add": ["combo_piece_possible", "recursion"],
        "remove": [],
    },

    # ----------------------------------------------------------------- Library / draw engines
    "sensei's divining top": {
        "add": ["combo_piece_possible", "card_selection", "topdeck_manipulation"],
        "remove": [],
    },
    "necropotence": {
        "add": ["combo_piece_possible", "card_advantage", "card_draw", "bracket_pressure"],
        "remove": [],
    },
    "ad nauseam": {
        "add": ["combo_piece_possible", "card_advantage", "win_condition", "bracket_pressure"],
        "remove": [],
    },
    "rhystic study": {
        "add": ["card_advantage", "card_draw", "tax_effect"],
        "remove": [],
    },
    "smothering tithe": {
        "add": ["combo_piece_possible", "treasure_synergy", "tax_effect", "ramp"],
        "remove": [],
    },
    "mystic remora": {
        "add": ["card_advantage", "card_draw"],
        "remove": [],
    },
    "esper sentinel": {
        "add": ["card_draw", "card_advantage", "tax_effect"],
        "remove": [],
    },

    # ----------------------------------------------------------------- Doublers / amplifiers
    "doubling season": {
        "add": ["combo_piece_possible", "counter_synergy", "token_maker", "trigger_amplifier"],
        "remove": [],
    },
    "parallel lives": {
        "add": ["combo_piece_possible", "token_maker"],
        "remove": [],
    },
    "anointed procession": {
        "add": ["combo_piece_possible", "token_maker"],
        "remove": [],
    },

    # ----------------------------------------------------------------- Other combo staples
    "agatha's soul cauldron": {
        "add": ["combo_piece_possible", "synergy_piece", "graveyard_enabler"],
        "remove": [],
    },
    "emry, lurker of the loch": {
        "add": ["combo_piece_possible", "recursion", "graveyard_enabler", "self_mill"],
        "remove": [],
    },
    "worldgorger dragon": {
        "add": ["combo_piece_possible", "blink_flicker"],
        "remove": [],
    },
    "tormod's crypt": {
        # graveyard hate, not generic combo, but enables/breaks many combos
        "add": ["combo_piece_possible", "graveyard_hate"],
        "remove": [],
    },
    "triskelion": {
        "add": ["combo_piece_possible"],
        "remove": [],
    },
    "the one ring": {
        # iconic combo / value engine, often used to chain Spelldancer / wheels
        "add": ["combo_piece_possible", "protection", "card_advantage", "card_draw", "bracket_pressure"],
        "remove": [],
    },
    "birgi, god of storytelling // harnfel, horn of bounty": {
        "add": ["combo_piece_possible", "ritual", "mana_source"],
        "remove": [],
    },

    # ----------------------------------------------------------------- Equipment-as-protection that the patterns may have missed
    # Already caught by the shroud/totem armor patches, but keep these as a safety net.
    "lightning greaves": {
        "add": ["protection", "equipment_synergy"],
        "remove": [],
    },
    "swiftfoot boots": {
        "add": ["protection", "equipment_synergy"],
        "remove": [],
    },

    # ----------------------------------------------------------------- v1.6.2 Phase A: Devotion payoffs
    # Mono-color devotion staples — Gary, Heliod, Nykthos, Thassa Deep-Dwelling,
    # Erebos God of the Dead, Karametra's Acolyte, the older Omnath.
    "gray merchant of asphodel": {
        "add": ["devotion_payoff", "lifedrain_payoff", "etb_value", "win_condition"],
        "remove": [],
    },
    "heliod, sun-crowned": {
        "add": ["devotion_payoff", "lifegain_payoff", "combo_piece_possible", "counter_synergy"],
        "remove": [],
    },
    "nykthos, shrine to nyx": {
        "add": ["devotion_payoff", "mana_source", "ramp", "mana_doubler"],
        "remove": [],
    },
    "karametra's acolyte": {
        "add": ["devotion_payoff", "mana_dork", "ramp", "mana_source"],
        "remove": [],
    },
    "thassa, deep-dwelling": {
        "add": ["devotion_payoff", "blink_flicker", "etb_amplifier", "synergy_piece"],
        "remove": [],
    },
    "thassa, god of the sea": {
        "add": ["devotion_payoff", "evasion_support", "card_selection"],
        "remove": [],
    },
    "erebos, god of the dead": {
        "add": ["devotion_payoff", "card_draw", "card_advantage"],
        "remove": [],
    },
    "purphoros, god of the forge": {
        "add": ["devotion_payoff", "etb_value", "damage_payoff", "go_wide_token_engine"],
        "remove": [],
    },
    "omnath, locus of mana": {
        "add": ["devotion_payoff", "mana_sink", "ramp", "go_tall_support"],
        "remove": [],
    },

    # ----------------------------------------------------------------- v1.6.2 Phase A: Token doublers
    # The big four: Doubling Season, Anointed Procession, Parallel Lives,
    # Mondrak Glory Dominus. Plus the green-only Primal Vigor (also doubles
    # opponents' tokens), and the newer Ojer Taq Deepcrater (auto-flips).
    "doubling season": {
        "add": ["token_doubler", "token_maker", "counter_synergy", "synergy_piece"],
        "remove": [],
    },
    "anointed procession": {
        "add": ["token_doubler", "token_maker", "synergy_piece"],
        "remove": [],
    },
    "parallel lives": {
        "add": ["token_doubler", "token_maker", "synergy_piece"],
        "remove": [],
    },
    "mondrak, glory dominus": {
        "add": ["token_doubler", "token_maker", "synergy_piece", "go_wide_token_engine"],
        "remove": [],
    },
    "primal vigor": {
        # Doubles tokens AND +1/+1 counters. Symmetric — doubles opponents'
        # tokens too — but still a payoff for token commanders.
        "add": ["token_doubler", "token_maker", "counter_synergy", "synergy_piece"],
        "remove": [],
    },
    "adric, master of defense": {
        "add": ["token_doubler", "token_maker", "synergy_piece"],
        "remove": [],
    },
    "ojer taq, deepcrater // temple of civilization": {
        "add": ["token_doubler", "token_maker", "synergy_piece"],
        "remove": [],
    },

    # ----------------------------------------------------------------- v1.6.2 Phase A: Overrun finishers
    # One-shot win conditions for go-wide / typal decks. Distinguished from
    # anthems (which are ongoing) by "until end of turn" + decisive pump.
    "craterhoof behemoth": {
        "add": ["overrun_finisher", "win_condition", "etb_value", "combat_synergy", "tribal_payoff"],
        "remove": [],
    },
    "overwhelming stampede": {
        "add": ["overrun_finisher", "win_condition", "combat_synergy"],
        "remove": [],
    },
    "triumph of the hordes": {
        "add": ["overrun_finisher", "win_condition", "combat_synergy", "high_bracket_pressure"],
        "remove": [],
    },
    "pathbreaker ibex": {
        "add": ["overrun_finisher", "win_condition", "combat_synergy", "attack_trigger_payoff"],
        "remove": [],
    },
    "akroma's will": {
        "add": ["overrun_finisher", "win_condition", "protection", "combat_synergy"],
        "remove": [],
    },
    "finale of devastation": {
        "add": ["overrun_finisher", "win_condition", "tutor", "mana_sink"],
        "remove": [],
    },
    "trumpet blast": {
        "add": ["overrun_finisher", "combat_synergy"],
        "remove": [],
    },
    "end-raze forerunners": {
        "add": ["overrun_finisher", "win_condition", "etb_value", "combat_synergy"],
        "remove": [],
    },

    # ----------------------------------------------------------------- v1.6.2 Phase A: Untap engines
    # Repeatable activation enablers — critical for activated-ability
    # commanders (Aisha, Shorikai, Urza, Daretti).
    "voltaic key": {
        "add": ["untap_engine", "repeatable_activation", "activated_ability_synergy"],
        "remove": [],
    },
    "manifold key": {
        "add": ["untap_engine", "repeatable_activation", "activated_ability_synergy", "evasion_support"],
        "remove": [],
    },
    "aphetto alchemist": {
        "add": ["untap_engine", "repeatable_activation", "activated_ability_synergy"],
        "remove": [],
    },
    "pemmin's aura": {
        "add": ["untap_engine", "repeatable_activation", "activated_ability_synergy", "aura_synergy"],
        "remove": [],
    },
    "freed from the real": {
        "add": ["untap_engine", "repeatable_activation", "activated_ability_synergy", "aura_synergy", "combo_piece_possible"],
        "remove": [],
    },
    "thousand-year elixir": {
        "add": ["untap_engine", "repeatable_activation", "activated_ability_synergy"],
        "remove": [],
    },
    "magewright's stone": {
        "add": ["untap_engine", "repeatable_activation", "activated_ability_synergy"],
        "remove": [],
    },
    "puppet strings": {
        "add": ["untap_engine", "repeatable_activation"],
        "remove": [],
    },
    "kiora's follower": {
        "add": ["untap_engine", "repeatable_activation", "mana_dork", "ramp"],
        "remove": [],
    },
    "tidewater minion": {
        "add": ["untap_engine", "repeatable_activation", "combo_piece_possible"],
        "remove": [],
    },

    # ----------------------------------------------------------------- v1.6.2 Phase A: Uncounterable enablers
    # Stompy / Big Mana / Storm commanders care about making their key spells
    # uncounterable.
    "cavern of souls": {
        "add": ["uncounterable_enabler", "mana_source", "tribal_payoff", "synergy_piece"],
        "remove": [],
    },
    "allosaurus shepherd": {
        "add": ["uncounterable_enabler", "tribal_payoff", "protection"],
        "remove": [],
    },
    "boseiju, who endures": {
        "add": ["targeted_removal", "mana_source", "synergy_piece"],
        "remove": [],
    },
    "vexing shusher": {
        "add": ["uncounterable_enabler", "protection", "synergy_piece"],
        "remove": [],
    },
    "veil of summer": {
        "add": ["uncounterable_enabler", "protection", "card_draw", "free_interaction", "bracket_pressure"],
        "remove": [],
    },
    "city of solitude": {
        "add": ["uncounterable_enabler", "protection"],
        "remove": [],
    },
    "conqueror's flail": {
        "add": ["uncounterable_enabler", "equipment_synergy", "protection"],
        "remove": [],
    },
    "grand abolisher": {
        "add": ["uncounterable_enabler", "protection", "synergy_piece"],
        "remove": [],
    },
}


def _normalize_name(name: str) -> str:
    return " ".join(str(name or "").strip().casefold().split())


def apply_role_tag_overrides(card_name: str, tags: Iterable[str]) -> list[str]:
    """Apply override add/remove rules to a card's inferred tag set.

    Returns a sorted list of tags. If the card has no override entry, returns
    the input tags sorted (no change).
    """
    tag_set = set(tags or [])
    norm = _normalize_name(card_name)
    override = ROLE_TAG_OVERRIDES.get(norm)
    if override:
        for tag in override.get("add") or []:
            tag_set.add(tag)
        for tag in override.get("remove") or []:
            tag_set.discard(tag)
    return sorted(tag_set)


def override_summary() -> dict[str, int]:
    """Quick health check — how many overrides are loaded and what they touch."""
    adds = removes = 0
    for entry in ROLE_TAG_OVERRIDES.values():
        adds += len(entry.get("add") or [])
        removes += len(entry.get("remove") or [])
    return {
        "override_count": len(ROLE_TAG_OVERRIDES),
        "tag_additions": adds,
        "tag_removals": removes,
    }
