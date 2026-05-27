"""Commander-text scoring for Bin B deck builder (Item 3 v1.5.41).

Reads the selected commander's oracle text and identifies which abilities the
commander has — token creation, ETB triggers, attack triggers, creature-dies
triggers, mana doubling, lifegain payoffs, etc. From that shape, derives a set
of "amplifier role tags" — card roles that *multiply* the commander's ability.

The deck builder then boosts cards whose role tags intersect this amplifier set
so the picked deck feels built specifically for that commander instead of being
a generic strategy-template fill.

Examples:
- Miirym, Sentinel Wyrm ("create a token copy of each nontoken Dragon that
  enters") amplifies on: token-makers, copy/clone effects, trigger doublers,
  ETB doublers, Dragon typal payoffs.
- Edric, Spymaster of Trest ("whenever a creature deals combat damage to one
  of your opponents") amplifies on: evasion, unblockable, attack triggers,
  combat synergy.
- Atraxa, Praetors' Voice ("proliferate at end of turn") amplifies on: +1/+1
  counter producers, planeswalkers, infect, loyalty counters.

Boundaries:
- Reads from the commander's Scryfall card data only.
- Does NOT change card role tags.
- Returns a *set of amplifier tags* — the builder decides how to use them.
"""
from __future__ import annotations

from typing import Any


# Each pattern: a phrase in oracle text (lowercase substring) + the role tags
# it implies for amplifier behavior. When the commander's oracle text contains
# the phrase, those tags become "preferred" for deck-picking.
COMMANDER_TEXT_PATTERNS: tuple[tuple[str, set[str]], ...] = (
    # Token creation by the commander.
    ("create a token", {"anthem", "go_wide_token_engine", "token_maker", "copy_clone_value", "trigger_amplifier"}),
    ("create a creature token", {"anthem", "go_wide_token_engine", "token_maker", "copy_clone_value"}),
    ("create a token copy", {"copy_clone_value", "trigger_amplifier", "etb_amplifier", "token_maker"}),
    ("treasure token", {"treasure_synergy", "ramp", "mana_rock", "artifact_token_synergy"}),

    # ETB triggers (commander does something when other creatures enter).
    ("enters the battlefield", {"etb_value", "blink_flicker", "etb_amplifier", "copy_amplifier", "trigger_amplifier"}),
    ("enters under your control", {"etb_value", "blink_flicker", "etb_amplifier"}),
    ("whenever another creature enters", {"etb_value", "blink_flicker", "etb_amplifier", "trigger_amplifier"}),

    # Attack / combat triggers.
    ("whenever a creature attacks", {"go_wide_token_engine", "anthem", "attack_trigger_payoff", "combat_synergy", "token_maker"}),
    ("whenever you attack", {"go_wide_token_engine", "anthem", "attack_trigger_payoff", "combat_synergy"}),
    ("attacks each combat", {"go_wide_token_engine", "anthem", "extra_combat"}),
    ("attacks alone", {"go_tall_support", "voltron", "equipment_synergy"}),
    ("deals combat damage", {"evasion_support", "attack_trigger_payoff", "combat_synergy", "damage_payoff"}),
    ("deals damage to a player", {"evasion_support", "attack_trigger_payoff", "damage_payoff", "draw_punisher"}),

    # Death / sacrifice triggers.
    ("whenever a creature dies", {"sacrifice_outlet", "free_sacrifice_outlet", "death_trigger_payoff", "token_maker", "recursion"}),
    ("whenever another creature dies", {"sacrifice_outlet", "free_sacrifice_outlet", "death_trigger_payoff", "token_maker"}),
    ("when you sacrifice", {"sacrifice_outlet", "free_sacrifice_outlet", "sacrifice_payoff", "token_maker"}),
    ("sacrifice a creature", {"sacrifice_outlet", "free_sacrifice_outlet", "sacrifice_payoff", "death_trigger_payoff"}),

    # Spell triggers (spellslinger commanders).
    ("whenever you cast an instant", {"spell_payoff", "card_draw", "card_advantage", "copy_amplifier"}),
    ("whenever you cast a sorcery", {"spell_payoff", "card_draw", "card_advantage", "copy_amplifier"}),
    ("whenever you cast a noncreature spell", {"spell_payoff", "card_draw", "cost_reducer"}),
    ("whenever you cast a spell", {"spell_payoff", "card_draw", "cost_reducer", "copy_amplifier"}),
    ("copy that spell", {"copy_amplifier", "spell_payoff"}),

    # Mana / ramp commanders.
    ("add one mana of any color", {"ramp", "mana_rock", "mana_source", "extra_land_play"}),
    ("twice that much mana", {"mana_doubler", "ramp", "big_mana_payoff", "mana_sink"}),
    ("double the amount", {"mana_doubler", "trigger_amplifier", "anthem"}),

    # Lands matter.
    ("whenever a land enters", {"landfall", "landfall_payoff", "extra_land_play", "lands_matter"}),
    ("landfall", {"landfall", "landfall_payoff", "extra_land_play", "lands_matter"}),
    ("an additional land", {"extra_land_play", "lands_matter", "landfall"}),
    ("play lands from", {"extra_land_play", "lands_matter"}),

    # +1/+1 counters / proliferate / mutate.
    ("+1/+1 counter", {"counter_synergy", "go_tall_support", "anthem"}),
    ("proliferate", {"counter_synergy", "go_tall_support"}),
    ("put a +1/+1 counter", {"counter_synergy", "go_tall_support", "trigger_amplifier"}),
    ("mutate", {"mutate", "mutate_payoff", "etb_value", "blink_flicker"}),

    # Graveyard / recursion commanders.
    ("return target creature card from your graveyard", {"recursion", "graveyard_enabler", "self_mill", "discard_outlet"}),
    ("from your graveyard to the battlefield", {"recursion", "graveyard_enabler", "self_mill"}),
    ("milled this turn", {"self_mill", "graveyard_enabler", "recursion"}),
    ("put the top", {"self_mill", "graveyard_enabler", "card_selection"}),

    # Lifegain / lifedrain.
    ("whenever you gain life", {"lifegain_payoff", "lifedrain_payoff"}),
    ("lifelink", {"lifegain_payoff", "evasion_support", "combat_synergy"}),
    ("each opponent loses", {"lifedrain_payoff", "damage_payoff", "death_trigger_payoff"}),

    # Card draw / draw triggers.
    ("whenever you draw a card", {"card_advantage", "card_draw", "wheel", "draw_punisher"}),
    ("whenever an opponent draws", {"draw_punisher", "group_slug", "wheel", "punisher"}),
    ("draw an additional card", {"card_advantage", "card_draw", "wheel"}),

    # Equipment / Voltron.
    ("equipped creature", {"equipment_synergy", "voltron", "go_tall_support", "evasion_support", "protection"}),
    ("attach", {"equipment_synergy", "voltron"}),

    # Artifact synergy.
    ("whenever an artifact", {"artifact_payoff", "artifact_token_synergy", "treasure_synergy"}),
    ("whenever you cast an artifact", {"artifact_payoff", "cost_reducer", "treasure_synergy"}),

    # Enchantment synergy.
    ("whenever an enchantment", {"aura_synergy", "enchantment", "enchant_land_ramp"}),
    ("whenever you cast an enchantment", {"aura_synergy", "enchantment"}),

    # Tribal text.
    ("creatures you control of the chosen type", {"typal_density_piece", "tribal_payoff", "anthem"}),
    ("other creatures you control", {"anthem", "go_wide_token_engine", "combat_synergy"}),

    # Big creatures / Voltron commanders.
    ("commander damage", {"voltron", "go_tall_support", "evasion_support", "protection", "equipment_synergy"}),
    ("when your commander deals", {"voltron", "go_tall_support", "evasion_support", "attack_trigger_payoff"}),
    ("doubled", {"trigger_amplifier", "mana_doubler", "copy_amplifier"}),

    # Group / politics.
    ("each opponent", {"group_slug", "table_damage", "lifedrain_payoff", "draw_punisher"}),
)


# Common Dragon-typal commanders give a Dragon-flavored boost. Similar patterns
# apply for other creature types if the commander's text references them.
TYPE_REFERENCED_AMPLIFIERS: dict[str, set[str]] = {
    "dragon": {"dragon_typal", "dragon_card", "dragon_copy_value"},
    "elf": {"typal_density_piece", "tribal_payoff"},
    "goblin": {"typal_density_piece", "tribal_payoff"},
    "zombie": {"typal_density_piece", "tribal_payoff", "graveyard_enabler"},
    "spirit": {"typal_density_piece", "tribal_payoff"},
    "merfolk": {"typal_density_piece", "tribal_payoff"},
    "vampire": {"typal_density_piece", "tribal_payoff", "lifegain_payoff"},
    "wizard": {"typal_density_piece", "tribal_payoff", "spell_payoff"},
    "warrior": {"typal_density_piece", "tribal_payoff", "combat_synergy"},
    "soldier": {"typal_density_piece", "tribal_payoff", "anthem"},
    "knight": {"typal_density_piece", "tribal_payoff", "combat_synergy"},
    "human": {"typal_density_piece", "tribal_payoff"},
    "angel": {"typal_density_piece", "tribal_payoff", "evasion_support"},
    "demon": {"typal_density_piece", "tribal_payoff", "lifedrain_payoff"},
    "beast": {"typal_density_piece", "tribal_payoff"},
    "cat": {"typal_density_piece", "tribal_payoff"},
    "dwarf": {"typal_density_piece", "tribal_payoff"},
    "treefolk": {"typal_density_piece", "tribal_payoff", "high_toughness"},
    "fungus": {"typal_density_piece", "tribal_payoff", "token_maker"},
    "horror": {"typal_density_piece", "tribal_payoff"},
    "eldrazi": {"typal_density_piece", "tribal_payoff", "big_mana_payoff", "mana_sink"},
}


def commander_amplifier_tags(commander_scryfall_card: dict[str, Any] | None) -> set[str]:
    """Return the set of role tags amplified by this commander's ability.

    Reads the commander's oracle text (handles double-faced cards) and matches
    against the COMMANDER_TEXT_PATTERNS table. Also picks up creature-type
    references from the type line.
    """
    if not commander_scryfall_card:
        return set()

    # Combine oracle text from both faces (DFCs / split / modal-DFCs).
    text_parts: list[str] = []
    if commander_scryfall_card.get("oracle_text"):
        text_parts.append(str(commander_scryfall_card["oracle_text"]))
    for face in commander_scryfall_card.get("card_faces") or []:
        if isinstance(face, dict) and face.get("oracle_text"):
            text_parts.append(str(face["oracle_text"]))
    text = " ".join(text_parts).lower()

    type_line = str(commander_scryfall_card.get("type_line") or "").lower()

    amplifiers: set[str] = set()

    for phrase, tags in COMMANDER_TEXT_PATTERNS:
        if phrase in text:
            amplifiers.update(tags)

    # Creature type amplifiers: if the commander's type line lists a creature
    # type AND the oracle text references that type, the commander is typal.
    for creature_type, type_tags in TYPE_REFERENCED_AMPLIFIERS.items():
        if creature_type in type_line and creature_type in text:
            amplifiers.update(type_tags)

    return amplifiers


def commander_amplifier_summary(commander_scryfall_card: dict[str, Any] | None) -> str:
    """One-line human-readable description of what this commander amplifies.

    Used in the deck report to explain why certain cards were preferred.
    """
    tags = commander_amplifier_tags(commander_scryfall_card)
    if not tags:
        return "No amplifier signals detected from this commander's oracle text."
    # Translate raw tag IDs to friendlier labels for the report.
    friendly_map = {
        "token_maker": "token makers",
        "go_wide_token_engine": "go-wide token engines",
        "copy_clone_value": "copy/clone effects",
        "trigger_amplifier": "trigger doublers",
        "etb_amplifier": "ETB doublers",
        "etb_value": "ETB-trigger creatures",
        "blink_flicker": "blink/flicker effects",
        "attack_trigger_payoff": "attack-trigger payoffs",
        "combat_synergy": "combat synergy",
        "evasion_support": "evasion / unblockable",
        "anthem": "anthems",
        "go_tall_support": "go-tall buffs",
        "extra_combat": "extra combat steps",
        "voltron": "Voltron/Equipment lines",
        "equipment_synergy": "equipment synergy",
        "sacrifice_outlet": "sacrifice outlets",
        "free_sacrifice_outlet": "free sacrifice outlets",
        "death_trigger_payoff": "death-trigger payoffs",
        "spell_payoff": "spellslinger payoffs",
        "card_draw": "card draw",
        "card_advantage": "card advantage",
        "cost_reducer": "cost reducers",
        "copy_amplifier": "spell-copying",
        "ramp": "ramp",
        "mana_doubler": "mana doublers",
        "mana_rock": "mana rocks",
        "mana_source": "mana sources",
        "extra_land_play": "extra land drops",
        "landfall": "landfall triggers",
        "landfall_payoff": "landfall payoffs",
        "lands_matter": "lands-matter cards",
        "counter_synergy": "+1/+1 counter synergy",
        "mutate": "mutate enablers",
        "mutate_payoff": "mutate payoffs",
        "recursion": "recursion",
        "graveyard_enabler": "graveyard fillers",
        "self_mill": "self-mill",
        "discard_outlet": "discard outlets",
        "lifegain_payoff": "lifegain payoffs",
        "lifedrain_payoff": "lifedrain payoffs",
        "wheel": "wheels",
        "draw_punisher": "draw punishers",
        "group_slug": "group slug",
        "table_damage": "table damage",
        "punisher": "punisher effects",
        "artifact_payoff": "artifact payoffs",
        "artifact_token_synergy": "artifact-token synergy",
        "treasure_synergy": "Treasure synergy",
        "aura_synergy": "aura synergy",
        "enchantment": "enchantment synergy",
        "enchant_land_ramp": "enchant-land ramp",
        "typal_density_piece": "typal density",
        "tribal_payoff": "tribal payoffs",
        "dragon_typal": "Dragon typal",
        "dragon_card": "Dragons",
        "dragon_copy_value": "Dragon copy value",
        "big_mana_payoff": "big-mana payoffs",
        "mana_sink": "mana sinks",
        "high_toughness": "high-toughness creatures",
        "protection": "protection",
    }
    readable = [friendly_map.get(t, t.replace("_", " ")) for t in sorted(tags)]
    # Deduplicate while preserving order.
    seen: list[str] = []
    for label in readable:
        if label not in seen:
            seen.append(label)
    if len(seen) > 8:
        shown = seen[:8]
        return f"Commander amplifies: {', '.join(shown)}, and {len(seen) - 8} more."
    return f"Commander amplifies: {', '.join(seen)}."
