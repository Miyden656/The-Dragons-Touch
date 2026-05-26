"""Card role tagging engine.

Round 5 cleanup goal:
- Move card-level role classification out of the monolith.
- Keep this module focused on *what cards do*, not whether they should be cut.
- Return structured role entries that later strategy/cut/report modules can use.

This is intentionally a checkpoint implementation: it preserves the major role
vocabulary and many of the legacy text heuristics, but later cleanup rounds can
continue moving the remaining edge-case repairs from the monolith.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from data.card_lookup import (
    get_face_aware_major_types,
    get_full_oracle_text,
    normalize_text,
)
from legality.commander_detection import CommandZoneSummary
from parsing.deck_parser import ParsedDeck

NON_TRIBAL_REFERENCE_WORDS = {
    "time", "times", "turn", "turns", "phase", "phases", "combat", "card", "cards",
    "spell", "spells", "token", "tokens", "counter", "counters", "damage", "life", "mana",
    "artifact", "creature", "permanent", "opponent", "player", "construct",
}

KNOWN_CREATURE_TYPES = set("""
advisor aetherborn ally angel antelope ape archer archon army artificer assassin assembly-worker avatar badger barbarian bard basilisk bat bear beast berserker bird boar cat centaur cleric construct crab crocodile cyclops demon detective devil dinosaur djinn dog dragon drake drone druid dryad dwarf elder eldrazi elemental elephant elf elk faerie fish fox fractal frog fungus giant gnome goat goblin god golem gorgon gremlin griffin halfling horror horse human hydra illusion imp incarnation inkling insect knight kobold kor kraken leviathan lizard masticore merfolk minion minotaur mole monk monkey mouse mutant myr mystic naga nightmare ninja noble octopus ogre ooze orc otter ouphe ox pegasus pest phoenix phyrexian pirate plant rabbit raccoon ranger rat rebel rhino robot rogue salamander samurai saproling satyr scarecrow scout scorpion serpent servo shade shaman shapeshifter shark skeleton sliver snake soldier spawn specter sphinx spider spirit squirrel survivor thopter thrull tiefling treefolk troll turtle unicorn vampire vedalken warrior weird werewolf whale wizard wolf worm wraith wurm zombie doctor time lord
""".split())

ROLE_TAG_DISPLAY_ORDER = [
    "ramp", "mana_rock", "mana_dork", "mana_source", "card_draw", "card_advantage",
    "card_selection", "targeted_removal", "board_wipe", "counterspell", "protection",
    "recursion", "graveyard_enabler", "self_mill", "discard_outlet", "sacrifice_outlet",
    "free_sacrifice_outlet", "death_trigger_payoff", "token_maker", "anthem", "tutor",
    "cost_reducer", "mana_doubler", "tribal_payoff", "tribal_dependency", "typal_density_piece",
    "synergy_piece", "extra_combat", "combat_synergy", "attack_trigger_payoff", "damage_payoff",
    "sacrifice_payoff", "artifact_payoff", "counter_synergy", "equipment_synergy", "aura_synergy",
    "go_tall_support", "spell_payoff", "spell_recursion_possible", "blink_flicker", "etb_value",
    "ltb_value", "landfall", "landfall_payoff", "extra_land_play", "lands_matter", "land_aura_ramp", "enchant_land_ramp", "mana_infrastructure", "land_token",
    "artifact_token_synergy", "treasure_synergy", "clue_synergy", "food_synergy", "lifegain_payoff",
    "lifedrain_payoff", "toughness_payoff", "defender_payoff", "high_toughness", "activated_ability_synergy",
    "mana_sink", "trigger_amplifier", "etb_amplifier", "copy_amplifier", "commander_payoff_amplifier", "big_moment_enabler", "cheat_into_play", "copy_clone_value", "dragon_typal", "dragon_copy_value", "mutate", "mutate_payoff",
    "cast_from_outside_hand", "nonhand_casting", "foretell", "plot", "suspend_synergy", "adventure_synergy",
    "draw_punisher", "forced_draw", "wheel", "group_slug", "table_damage", "punisher",
    "fast_mana", "efficient_tutor", "free_interaction", "high_bracket_pressure", "bracket_pressure",
    "combo_piece_possible", "win_condition", "manual_review",
]
NON_TRIBAL_REFERENCE_WORDS = {
    "time", "times", "turn", "turns", "phase", "phases", "combat", "card", "cards",
    "spell", "spells", "token", "tokens", "counter", "counters", "damage", "life", "mana",
    "artifact", "creature", "permanent", "opponent", "player", "construct",
}
KNOWN_CREATURE_TYPES = set("""
advisor aetherborn ally angel antelope ape archer archon army artificer assassin assembly-worker avatar badger barbarian bard basilisk bat bear beast berserker bird boar cat centaur cleric construct crab crocodile cyclops demon detective devil dinosaur djinn dog dragon drake drone druid dryad dwarf elder eldrazi elemental elephant elf elk faerie fish fox fractal frog fungus giant gnome goat goblin god golem gorgon gremlin griffin halfling horror horse human hydra illusion imp incarnation inkling insect knight kobold kor kraken leviathan lizard masticore merfolk minion minotaur mole monk monkey mouse mutant myr mystic naga nightmare ninja noble octopus ogre ooze orc otter ouphe ox pegasus pest phoenix phyrexian pirate plant rabbit raccoon ranger rat rebel rhino robot rogue salamander samurai saproling satyr scarecrow scout scorpion serpent servo shade shaman shapeshifter shark skeleton sliver snake soldier spawn specter sphinx spider spirit squirrel survivor thopter thrull tiefling treefolk troll turtle unicorn vampire vedalken warrior weird werewolf whale wizard wolf worm wraith wurm zombie doctor time lord
""".split())
ROLE_TAG_DISPLAY_ORDER = [
    "ramp", "mana_rock", "mana_dork", "mana_source", "card_draw", "card_advantage",
    "card_selection", "targeted_removal", "board_wipe", "counterspell", "protection",
    "recursion", "graveyard_enabler", "self_mill", "discard_outlet", "sacrifice_outlet",
    "free_sacrifice_outlet", "death_trigger_payoff", "token_maker", "anthem", "tutor",
    "cost_reducer", "mana_doubler", "tribal_payoff", "tribal_dependency", "typal_density_piece",
    "synergy_piece", "extra_combat", "combat_synergy", "attack_trigger_payoff", "damage_payoff",
    "sacrifice_payoff", "artifact_payoff", "counter_synergy", "equipment_synergy", "aura_synergy",
    "go_tall_support", "spell_payoff", "spell_recursion_possible", "blink_flicker", "etb_value",
    "ltb_value", "landfall", "landfall_payoff", "extra_land_play", "lands_matter", "land_aura_ramp", "enchant_land_ramp", "mana_infrastructure", "land_token",
    "artifact_token_synergy", "treasure_synergy", "clue_synergy", "food_synergy", "lifegain_payoff",
    "lifedrain_payoff", "toughness_payoff", "defender_payoff", "high_toughness", "activated_ability_synergy",
    "mana_sink", "trigger_amplifier", "etb_amplifier", "copy_amplifier", "commander_payoff_amplifier", "big_moment_enabler", "cheat_into_play", "copy_clone_value", "dragon_typal", "dragon_copy_value", "mutate", "mutate_payoff",
    "cast_from_outside_hand", "nonhand_casting", "foretell", "plot", "suspend_synergy", "adventure_synergy",
    "draw_punisher", "forced_draw", "wheel", "group_slug", "table_damage", "punisher",
    "fast_mana", "efficient_tutor", "free_interaction", "high_bracket_pressure", "bracket_pressure",
    "combo_piece_possible", "win_condition", "manual_review",
]

def singularize(word: str) -> str:
    word = word.strip("()[]{}.,:;").lower()
    if word.endswith("ies"):
        return word[:-3] + "y"
    if word.endswith("s"):
        return word[:-1]
    return word

def get_creature_subtypes(type_line: str) -> set[str]:
    subtypes: set[str] = set()
    for face in type_line.split("//"):
        face = face.strip()
        if "Creature" not in face or "—" not in face:
            continue
        for subtype in face.split("—", 1)[1].strip().split():
            if subtype.strip():
                subtypes.add(subtype.strip())
    return subtypes

def get_referenced_creature_types(oracle_text: str) -> set[str]:
    refs: set[str] = set()
    for word in normalize_text(oracle_text).split():
        singular = singularize(word)
        if singular in KNOWN_CREATURE_TYPES and singular not in NON_TRIBAL_REFERENCE_WORDS:
            refs.add(singular.title())
    return refs

def get_tribal_dependency_types(oracle_text: str) -> set[str]:
    text = normalize_text(oracle_text)
    found: set[str] = set()
    for ctype in get_referenced_creature_types(oracle_text):
        lower = ctype.lower()
        plural = lower + "s"
        phrases = [
            f"control a {lower}", f"control an {lower}", f"control another {lower}",
            f"as long as you control a {lower}", f"as long as you control an {lower}",
            f"control one or more {plural}", f"{plural} you control", f"{lower}s you control",
            f"other {plural}", f"other {lower}s", f"whenever a {lower}",
            f"whenever another {lower}", f"whenever one or more {plural}",
            f"for each {lower}", f"for each {plural}",
        ]
        if any(p in text for p in phrases):
            found.add(ctype)
    return found

def get_tribal_payoff_types(oracle_text: str) -> set[str]:
    text = normalize_text(oracle_text)
    found: set[str] = set()
    for ctype in get_referenced_creature_types(oracle_text):
        lower = ctype.lower()
        plural = lower + "s"
        phrases = [
            f"{plural} you control get", f"{lower}s you control get", f"other {plural} you control",
            f"other {lower}s you control", f"whenever a {lower} you control", f"whenever another {lower}",
            f"whenever one or more {plural}", f"for each {lower}", f"for each {plural}",
            "chosen type", "creature type",
        ]
        if any(p in text for p in phrases):
            found.add(ctype)
    return found

def _has_any(text: str, phrases: list[str] | tuple[str, ...]) -> bool:
    return any(phrase in text for phrase in phrases)

def _is_only_land(type_line: str) -> bool:
    tl = type_line.lower()
    return "land" in tl and all(t not in tl for t in ["creature", "artifact", "enchantment", "instant", "sorcery", "battle", "planeswalker"])

def _is_enchant_land_ramp(type_line: str, text: str) -> bool:
    """Detect Aura-based land ramp such as Utopia Sprawl and Wild Growth.

    These cards often use wording like "enchanted land/Forest is tapped for
    mana, its controller adds an additional ..." which older generic mana
    detection can miss because it says "adds" instead of "add".
    """
    tl = type_line.lower()
    if "enchantment" not in tl or "aura" not in tl:
        return False

    has_land_enchant_clause = any(phrase in text for phrase in (
        "enchant land",
        "enchant forest",
        "enchant plains",
        "enchant island",
        "enchant swamp",
        "enchant mountain",
    ))
    if not has_land_enchant_clause:
        return False

    enchanted_land_reference = any(phrase in text for phrase in (
        "enchanted land",
        "enchanted forest",
        "enchanted plains",
        "enchanted island",
        "enchanted swamp",
        "enchanted mountain",
    ))
    mana_boost_reference = any(phrase in text for phrase in (
        "is tapped for mana",
        "adds an additional",
        "add an additional",
        "has \"{t}: add",
        "has '{t}: add",
        "has “{t}: add",
        "has ‘{t}: add",
    ))
    return enchanted_land_reference and mana_boost_reference
