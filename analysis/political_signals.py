"""Political signal detection layer (Section 3 — Strategic & Board Politics).

WHY THIS EXISTS / WHAT IT IS
----------------------------
`rules/section_3_strategic_board_politics.md` defines ~42 political archetypes
(Group Hug, Group Slug, Goad, Pillowfort, Monarch, Voting, Curse, Donate, …),
each gated on counts of a shared POLITICAL SIGNAL VOCABULARY (group_draw,
gift_resource, goad, attack_tax, monarch, vote, curse, donate, …). None of that
vocabulary is produced by the engine today.

This module is the self-contained detector for that vocabulary. It is the
political analogue of `analysis/role_tags.py`, but DELIBERATELY SEPARATE:

- It does NOT add tags to role_tags.py and does NOT feed role_counts, so the
  v1.6 six-signal scoring chain (role -> strategy -> bracket -> cuts -> repl)
  stays byte-identical. This is an additive, parallel classification.
- It reuses a few already-computed role tags (board_wipe, targeted_removal,
  protection, recursion, win_condition, card_draw, tutor, card_selection) for the
  structural signals the role engine already gets right, and does its OWN oracle
  scans for everything political-specific.

Output: `build_political_signal_profile(...) -> PoliticalSignalProfile` carrying
a Counter of signal counts (by deck copy) + a dict of boolean engine flags
(has_clear_win_path, commander_supports_* …). The archetype classifier
(`analysis/political_archetypes.py`) consumes both.

Detection is pattern-based and intentionally conservative: an undetected signal
simply stays at 0, so a missed pattern can only fail to fire an archetype — it
can never fabricate one. Accuracy is iterative; the framework supports all 42
archetypes regardless of how sharp any single detector is.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from data.card_lookup import get_full_oracle_text, normalize_text


@dataclass(slots=True)
class PoliticalSignalProfile:
    counts: Counter  # political signal tag -> count (by deck copy / quantity)
    flags: dict[str, bool]  # engine booleans the gates reference
    signals_by_card: dict[str, list[str]]  # card name -> sorted political tags
    commander_text: str = ""


# --- Reused existing role tags (same concept, already computed by role_tags) ---
# Maps an engine role tag -> the political-vocabulary tag(s) it satisfies. Lets us
# lean on the role engine for the structural signals it already nails, without
# rescanning. (Counterspells are "visible interaction"/"control"; lifedrain is a
# drain/life-loss engine; etc.)
_REUSED_ROLE_TAGS: dict[str, tuple[str, ...]] = {
    "board_wipe": ("board_wipe", "board_reset"),
    "targeted_removal": ("targeted_removal",),
    "counterspell": ("visible_interaction", "control_piece"),
    "protection": ("protection",),
    "recursion": ("recursion",),
    "win_condition": ("win_condition",),
    "card_draw": ("card_draw",),
    "card_advantage": ("card_draw",),
    "tutor": ("tutor",),
    "card_selection": ("card_selection",),
    "table_damage": ("table_damage",),
    "punisher": ("punisher",),
    "draw_punisher": ("punisher",),
    "lifedrain_payoff": ("lifedrain", "drain_payoff", "life_loss_engine"),
    "combo_piece_possible": ("combo_piece",),
}


# --- Oracle-text patterns for the political vocabulary -----------------------
# tag -> tuple of normalized substrings; a card gets the tag if ANY substring is
# present in its (face-aware) oracle text. Grouped by Section 3.5 category.
_SIGNAL_PATTERNS: dict[str, tuple[str, ...]] = {
    # group resources / hug
    "group_draw": ("each player draws", "each player may draw", "players draw", "opponents draw a card", "each opponent draws"),
    "group_ramp": ("each player may put a land", "players add", "each player adds", "each player may search their library for a basic land", "lands onto the battlefield"),
    "gift_resource": ("target opponent gains control", "each opponent creates", "opponents create", "each player creates a token", "donate", "give to target player", "an opponent gains control"),
    "group_resource": ("each player", "each opponent"),
    "tablewide_acceleration": ("spells your opponents cast cost", "each player may cast", "players may play an additional land", "each player's spells cost"),
    "hug_payoff": ("whenever an opponent draws", "for each card drawn this turn", "whenever a player draws their second"),
    "asymmetrical_payoff": ("you draw a card for each", "whenever an opponent draws", "you gain that much", "whenever a player casts a spell, you"),
    # punishment / slug
    "life_loss_engine": ("each opponent loses", "each player loses", "loses 1 life", "loses 2 life", "lose life equal"),
    "drain_payoff": ("each opponent loses", "you gain that much life", "loses 1 life and you gain", "drain"),
    "lifedrain": ("each opponent loses", "you gain that much life"),
    "damage_amplifier": ("if a source would deal damage", "deals double", "that much damage plus", "deals that much damage plus", "would deal damage to a permanent or player, it deals"),
    "lifegain_buffer": ("whenever you gain life", "you gain", "gain 1 life", "gain 2 life"),
    "spell_punisher": ("whenever an opponent casts a spell", "whenever a player casts a spell", "casts a spell, that player"),
    "attack_punisher": ("whenever a creature attacks you", "whenever a creature attacks you or a planeswalker", "deals damage to a creature that attacked", "whenever a creature you control blocks"),
    "landfall_punisher": ("whenever a land enters the battlefield under an opponent", "whenever an opponent plays a land"),
    "choice_punisher": ("unless that player", "may choose. if they don't", "chooses one", "that player may", "unless its controller"),
    # chaos
    "random_effect": ("at random", "random", "choose a card at random"),
    "coin_flip": ("flip a coin",),
    "dice_roll": ("roll a", "roll two", "d20", "d6", "result of the die"),
    "chaos_effect": ("at random", "flip a coin", "roll a", "shuffles", "exchange control", "shuffle their hand"),
    "chaos_payoff": ("whenever you flip", "whenever you roll", "if you win the flip"),
    "permanent_swap": ("exchange control", "switch control"),
    # combat / goad
    "goad": ("goad",),
    "forced_attack": ("attacks each combat if able", "must attack", "all creatures attack", "creatures attack each combat if able", "attacks this turn if able"),
    "forced_combat": ("attacks each combat if able", "must attack", "goad", "creatures attack each combat if able"),
    "attack_elsewhere_incentive": ("attacks a player other than you", "attacks one of your opponents", "whenever a creature an opponent controls attacks another", "attacks a player other than you or a planeswalker"),
    "shared_combat_incentive": ("whenever a creature attacks", "creatures attack each combat if able", "whenever a player attacks"),
    "combat_payoff": ("whenever a creature you control deals combat damage", "whenever one or more creatures you control deal combat damage", "deals combat damage to a player"),
    "attack_reward": ("whenever a creature you control attacks", "whenever you attack", "whenever a creature attacks one of your opponents"),
    "attack_trigger": ("whenever a creature you control attacks", "whenever this creature attacks"),
    "saboteur": ("deals combat damage to a player", "whenever this creature deals combat damage to a player"),
    "forced_block": ("must be blocked", "all creatures able to block", "must block", "is blocked each combat if able"),
    "cant_block": ("can't block", "cannot block"),
    "combat_manipulation": ("must be blocked", "can't block", "must block", "attacks each combat if able", "goad", "must attack"),
    # pillowfort / fog / defense
    "attack_tax": ("creatures can't attack you unless", "attack you or a planeswalker you control unless", "costs {1} more to attack", "costs {2} more to attack", "for each creature attacking you"),
    "combat_prevention": ("prevent all combat damage this turn", "prevent all combat damage that would be dealt this turn", "creatures can't attack you", "can't attack you or planeswalkers you control"),
    "fort_protection": ("creatures can't attack you", "can't attack you unless", "can't attack you or a planeswalker", "whenever a creature attacks you"),
    "fog": ("prevent all combat damage this turn", "prevent all combat damage that would be dealt this turn", "prevent all damage that would be dealt this turn"),
    "rattlesnake": ("whenever a creature attacks you", "whenever a creature you control blocks", "deathtouch", "whenever a creature deals combat damage to you", "destroy that creature"),
    "damage_reflection": ("deals that much damage to that", "is dealt to you, that", "deals damage to you, it deals that much damage to its controller", "redirect"),
    "revenge_trigger": ("whenever a creature you control dies", "whenever you lose life", "whenever a creature you control is dealt damage", "whenever a permanent you control is put into a graveyard"),
    "anti_targeting": ("hexproof", "ward", "can't be the target of spells or abilities", "shroud", "protection from"),
    "board_protection": ("hexproof", "ward", "indestructible", "protection from", "shroud", "can't be the target"),
    "protected_win_condition": ("hexproof", "indestructible", "can't be the target"),
    # political / deals / votes / monarch / curse / bounty
    "political_choice": ("vote", "will of the council", "council's dilemma", "the tempted player", "secret council"),
    "deal_incentive": ("an opponent may pay", "tempting offer", "an opponent of your choice may", "unless an opponent pays", "if that player lets you"),
    "political_incentive": ("an opponent may pay", "the tempted player", "an opponent of your choice", "whenever an opponent attacks one of your other opponents"),
    "political_payoff": ("whenever an opponent attacks one of your", "whenever a creature an opponent controls attacks another", "for each opponent who attacked", "whenever a player votes", "whenever an opponent gains control"),
    "negotiated_removal": ("you may have target player sacrifice", "target opponent chooses", "you may have an opponent", "an opponent of your choice sacrifices"),
    "flexible_removal": ("destroy target permanent", "exile target permanent", "destroy target nonland permanent", "choose one", "choose two"),
    "vote": ("vote", "will of the council", "council's dilemma"),
    "vote_payoff": ("for each vote", "whenever you vote", "majority"),
    "monarch": ("become the monarch", "you become the monarch", "the monarch", "monarch"),
    "crown_defense": ("deathtouch", "whenever a creature you control blocks", "can't attack you"),
    "evasive_creature": ("flying", "menace", "can't be blocked", "shadow", "unblockable"),
    "curse": ("enchant player", "curse"),
    "curse_payoff": ("whenever an enchanted player", "enchanted player", "for each curse"),
    "enchantment_recursion": ("return target enchantment", "return an enchantment", "return target aura"),
    "enchantment_payoff": ("for each enchantment", "whenever an enchantment", "constellation", "enchantments you control"),
    "bounty": ("bounty", "put a bounty counter", "bounty counter"),
    "leader_punisher": ("player with the most", "player with the highest life", "opponent with the most"),
    "catch_up_mechanic": ("player with the fewest", "player with the least", "player with the lowest life total"),
    "parity_tool": ("no player can", "each player can't", "players can't cast", "each player can only cast", "players can cast only one", "each player skips"),
    "self_advancement": ("you draw a card", "you gain", "create a token"),
    "shared_enemy_incentive": ("attacks the player with", "opponent with the most", "player with the highest life total"),
    "symmetrical_rule": ("each player can't", "players can't", "each player may", "if a player would", "each player skips"),
    "rule_limiter": ("can't cast more than one", "each player can't", "players can't cast", "can cast only one"),
    "soft_lock": ("don't untap", "doesn't untap", "can't untap", "skip their", "tapped and doesn't untap"),
    "restriction": ("can't attack", "can't block", "can't cast", "can't activate", "don't untap"),
    "tax": ("costs {1} more", "costs {2} more", "spells cost", "abilities cost"),
    # theft / clone
    "theft": ("gain control of target", "gains control of target", "exchange control of", "gain control of all"),
    "clone_opponent": ("copy of target creature an opponent controls", "copy of target creature you don't control", "a copy of any creature, including one an opponent controls", "copy of target creature defending player controls"),
    "cast_opponent_card": ("from an opponent's graveyard", "from an opponent's library", "from an opponent's hand", "exile target card from an opponent", "cast it without paying its mana cost. if you don't"),
    "theft_payoff": ("sacrifice", "exile it", "whenever you gain control"),
    # donate / gift
    "donate": ("target player gains control", "another target player gains control", "gain control"),
    "bad_gift": ("target opponent gains control", "an opponent gains control of"),
    "resource_swap": ("exchange", "switch", "trade"),
    "donate_payoff": ("whenever an opponent gains control", "whenever you give"),
    "targeted_gift": ("target opponent gains control", "target player gains control", "an opponent gains control"),
    "gift_payoff": ("whenever a player gains control", "whenever an opponent"),
    "gift_resource_target": ("target player gains control",),
    # hate / police / anti-combo — punishment/restriction must be explicit, not
    # just any "whenever an opponent" or "spells cost" (those flood on value decks).
    "behavior_punisher": ("that player loses 2 life", "that player sacrifices a", "deals damage to that player equal", "an opponent loses 2 life", "that player discards"),
    "rule_enforcer": ("each player can't cast", "players can't cast spells", "can't cast more than one spell", "spells cost {1} more to cast", "spells cost {2} more to cast", "can't search their libraries", "each player skips their"),
    "anti_combo": ("can't search their library", "rule of law", "can't cast more than one spell", "creatures can't have their abilities activated", "players can't cast spells except during", "can't gain life", "damage can't be prevented"),
    "tutor_hate": ("can't search their library", "search their library, that player"),
    "graveyard_hate": ("exile target card from a graveyard", "exile all cards from", "cards in graveyards", "if a card would be put into a graveyard"),
    "visible_interaction": ("counter target", "destroy target", "exile target", "{t}: ", "tap target"),
    "control_piece": ("counter target", "destroy target", "return target", "tap target"),
    # archenemy / oppression
    "oppressive_effect": ("each opponent sacrifices", "each player sacrifices", "each opponent discards", "target player discards their hand", "each opponent loses"),
    "resilience": ("indestructible", "return it to the battlefield", "when this dies", "if this would die"),
    "fast_win": ("you win the game", "wins the game"),
    "fast_payoff": ("whenever", "at the beginning of"),
    "value_engine": ("at the beginning of your upkeep", "at the beginning of your end step", "at the beginning of each upkeep"),
    # combo / sandbag / hidden info
    # (combo_piece is also reused from the engine's combo_piece_possible role tag.)
    "combo_piece": ("untap target permanent", "create a token that's a copy of target", "you may cast it without paying"),
    "low_threat_value": ("prevent all combat damage", "you gain 2 life", "you gain 3 life", "can't lose the game", "you don't lose the game"),
    "instant_speed_interaction": ("flash", "counter target", "instant"),
    "proactive_pressure": ("you win the game", "each opponent loses", "deals damage to each opponent"),
    "voltron": ("equipped creature", "enchanted creature gets", "attach"),
    # life politics
    "life_manipulation": ("gain life", "lose life", "set your life total", "your life total becomes", "pay life"),
    "life_exchange": ("exchange life totals", "set your life total to", "your life total and target"),
    "life_payoff": ("whenever you gain life", "whenever you lose life", "for each life"),
    # hidden information
    "hidden_information": ("face down", "face-down", "morph", "disguise", "manifest", "cloak", "foretell"),
    "face_down": ("face down", "face-down", "morph", "manifest", "disguise", "cloak"),
    "hidden_payoff": ("turn it face up", "is turned face up", "whenever a permanent is turned face up"),
    # threat redistribution
    "threat_redirect": ("goad", "attacks a player other than you", "an opponent of your choice", "must attack"),
    # win/inevitability helpers
    "alternate_win_condition": ("you win the game", "wins the game"),
    "board_reset": ("destroy all", "exile all", "return all", "each player sacrifices all"),
    "break_parity": ("doesn't affect creatures you control", "except creatures you control", "except for creatures you control", "destroy all creatures except", "other than itself"),
    "mill": ("mills", "put the top", "into their graveyard from their library"),
}


def infer_political_signals(oracle: str, type_line: str = "") -> set[str]:
    """Return the political signal tags for one card's normalized oracle text."""
    tags: set[str] = set()
    text = oracle or ""
    for tag, patterns in _SIGNAL_PATTERNS.items():
        if any(p in text for p in patterns):
            tags.add(tag)
    tl = (type_line or "").lower()
    if "planeswalker" in tl:
        tags.add("planeswalker")
    if "aura" in tl and "enchant player" in text:
        tags.add("curse")
    return tags


# --- Commander-level boolean flags the gates reference -----------------------
_COMMANDER_FLAG_KEYWORDS: dict[str, tuple[str, ...]] = {
    "commander_supports_voting": ("vote", "will of the council", "council's dilemma"),
    "commander_supports_monarch": ("monarch",),
    "commander_supports_curses": ("curse", "enchant player"),
    "commander_supports_bounty": ("bounty",),
    "commander_supports_theft": ("gain control of target", "gains control of", "cast it from a graveyard"),
    "commander_supports_donate": ("gains control", "donate"),
    "commander_supports_gifting": ("target player gains control", "an opponent gains control"),
    "commander_supports_attack_elsewhere": ("attacks a player other than you", "goad", "attacks one of your opponents"),
    "commander_supports_hidden_information": ("face down", "face-down", "morph", "manifest", "disguise"),
    "commander_supports_reactive_play": ("flash", "instant", "counter target"),
    "commander_supports_board_reset": ("destroy all", "exile all", "return all"),
    "commander_breaks_parity": ("each player", "each opponent", "except", "doesn't affect you"),
    "commander_supports_politics": ("vote", "monarch", "goad", "bounty", "the tempted player", "will of the council"),
    "commander_supports_political_axis": ("vote", "monarch", "goad", "bounty", "the tempted player", "will of the council", "council's dilemma"),
}

# Commanders whose REPUTATION precedes them (3.48). Lowercased name fragments.
_HIGH_THREAT_COMMANDER_FRAGMENTS: tuple[str, ...] = (
    "thassa's oracle", "najeela", "kinnan", "tergrid", "winota", "yuriko",
    "urza", "grand arbiter", "korvold", "k'rrik", "edgar markov", "sheoldred",
    "the gitrog monster", "krark", "tivit", "rograkh",
)


def _commander_text(commander_cards: list[dict[str, Any]] | None) -> str:
    if not commander_cards:
        return ""
    parts = []
    for card in commander_cards:
        parts.append(get_full_oracle_text(card))
        parts.append(card.get("type_line", "") or "")
    return normalize_text("\n".join(parts))


def _commander_flags(commander_cards: list[dict[str, Any]] | None, text: str, counts: Counter) -> dict[str, bool]:
    flags: dict[str, bool] = {}
    for flag, keywords in _COMMANDER_FLAG_KEYWORDS.items():
        flags[flag] = bool(text) and any(k in text for k in keywords)

    names = " ".join((c.get("name", "") or "").lower() for c in (commander_cards or []))
    flags["commander_has_high_threat_reputation"] = any(
        frag in names for frag in _HIGH_THREAT_COMMANDER_FRAGMENTS
    )

    win = counts.get("win_condition", 0) + counts.get("alternate_win_condition", 0)
    flags["has_clear_win_path"] = win >= 1
    flags["has_proactive_win_path"] = win >= 1
    flags["has_clear_inevitability_engine"] = (
        counts.get("alternate_win_condition", 0) >= 1
        or counts.get("planeswalker", 0) >= 2
        or counts.get("combo_piece", 0) >= 2
        or counts.get("mill", 0) >= 3
    )
    return flags


def build_political_signal_profile(
    role_summary: Any,
    command_zone: Any = None,
    scryfall_lookup: dict | None = None,
) -> PoliticalSignalProfile:
    """Compute the political signal counts + engine flags for a deck.

    Reads defensively: missing inputs degrade to an empty profile rather than
    raising. Counts are by deck copy (quantity), matching the engine convention.
    """
    counts: Counter = Counter()
    signals_by_card: dict[str, list[str]] = {}
    card_roles = list(getattr(role_summary, "card_roles", None) or [])

    for entry in card_roles:
        name = getattr(entry, "card_name", "") or ""
        qty = int(getattr(entry, "quantity", 1) or 1)
        roles = set(getattr(entry, "detected_roles", None) or [])
        type_line = getattr(entry, "type_line", "") or ""

        tags: set[str] = set()
        # Reuse the role engine's structural signals.
        for role in roles:
            for political in _REUSED_ROLE_TAGS.get(role, ()):
                tags.add(political)

        # Our own political oracle scan.
        if getattr(entry, "found_in_scryfall", False) and scryfall_lookup:
            card = scryfall_lookup.get(name.lower())
            if card:
                oracle = ""
                try:
                    oracle = normalize_text(get_full_oracle_text(card))
                except Exception:
                    oracle = ""
                tags |= infer_political_signals(oracle, type_line)

        if tags:
            signals_by_card[name] = sorted(tags)
            counts.update({tag: qty for tag in tags})

    commander_cards = getattr(command_zone, "commander_cards_scryfall", None) if command_zone else None
    ctext = _commander_text(commander_cards)
    flags = _commander_flags(commander_cards, ctext, counts)

    return PoliticalSignalProfile(
        counts=counts,
        flags=flags,
        signals_by_card=signals_by_card,
        commander_text=ctext,
    )
