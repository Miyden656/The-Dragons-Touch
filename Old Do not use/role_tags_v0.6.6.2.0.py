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
    "mana_sink", "copy_clone_value", "dragon_typal", "dragon_copy_value", "mutate", "mutate_payoff",
    "cast_from_outside_hand", "nonhand_casting", "foretell", "plot", "suspend_synergy", "adventure_synergy",
    "draw_punisher", "forced_draw", "wheel", "group_slug", "table_damage", "punisher",
    "fast_mana", "efficient_tutor", "free_interaction", "high_bracket_pressure", "bracket_pressure",
    "combo_piece_possible", "win_condition", "manual_review",
]

@dataclass(slots=True)
class CardRoleEntry:
    card_name: str
    quantity: int
    found_in_scryfall: bool
    mana_value: float | int | None = None
    card_types: list[str] = field(default_factory=list)
    color_identity: list[str] = field(default_factory=list)
    detected_roles: list[str] = field(default_factory=list)
    confidence: str = "medium"
    short_reason: str = ""
    type_line: str = ""

@dataclass(slots=True)
class RoleAnalysisSummary:
    card_roles: list[CardRoleEntry]
    role_counts: Counter[str]
    type_counts: Counter[str]
    card_role_tags_by_card: dict[str, list[str]]
    unknown_cards: list[str]


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


def infer_card_type_tags(card: dict[str, Any]) -> list[str]:
    return sorted(t.lower() for t in get_face_aware_major_types(card))


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


def infer_card_role_tags(card: dict[str, Any], commander_cards: list[dict[str, Any]] | None = None) -> list[str]:
    """Infer role tags from Scryfall-style card data.

    This function should stay card-text focused. It intentionally does not decide
    whether a role is primary, secondary, protected, or cuttable.
    """
    tags: set[str] = set()
    name = normalize_text(card.get("name", ""))
    type_line = card.get("type_line", "")
    oracle = get_full_oracle_text(card)
    text = normalize_text(type_line + "\n" + oracle)
    tl = type_line.lower()
    mv = card.get("cmc", 0) or 0

    # Basic card-type roles.
    tags.update(infer_card_type_tags(card))
    is_land = "land" in tl
    is_only_land = _is_only_land(type_line)
    if is_land:
        tags.add("mana_source")
        if "landfall" in text or "land enters" in text:
            tags.update(["landfall", "lands_matter"])

    # Mana / ramp.
    produces_mana = _has_any(text, ["add {", "add one mana", "add two mana", "add three mana", "add mana", "treasure token"])
    land_ramp = (
        "search your library for a basic land" in text
        or "search your library for a basic forest" in text
        or "search your library for a forest" in text
        or "search your library for a land card" in text
        or ("put" in text and "land" in text and "onto the battlefield" in text)
    )
    enchant_land_ramp = _is_enchant_land_ramp(type_line, text)
    if produces_mana and not is_only_land:
        tags.add("ramp")
    if land_ramp or "you may play an additional land" in text or "untap all lands" in text:
        tags.update(["ramp", "lands_matter"])
    if enchant_land_ramp:
        tags.update([
            "ramp",
            "mana_source",
            "mana_infrastructure",
            "land_aura_ramp",
            "enchant_land_ramp",
            "aura_synergy",
        ])
    if "artifact" in tl and produces_mana:
        tags.add("mana_rock")
    if "creature" in tl and produces_mana:
        tags.add("mana_dork")
    if produces_mana and mv <= 1 and not is_land:
        tags.update(["fast_mana", "bracket_pressure"])
    if _has_any(text, ["add {b}{b}{b}", "add {r}{r}{r}", "add three mana", "add four mana", "add five mana"]):
        tags.update(["ritual", "ramp", "fast_mana", "bracket_pressure"])
    if _has_any(text, ["double the amount of", "if you tap a permanent for mana", "whenever you tap a land for mana, add"]):
        tags.update(["mana_doubler", "ramp"])

    # Draw-punisher / wheels / group-slug support.
    if _has_any(text, ["whenever an opponent draws", "whenever a player draws", "draws a card", "draws their second card"]):
        if _has_any(text, ["deals 1 damage", "loses 1 life", "each opponent loses", "damage to that player"]):
            tags.update(["draw_punisher", "group_slug", "table_damage", "punisher", "damage_payoff", "synergy_piece"])
    if _has_any(text, ["each player discards their hand", "then draws seven", "draw seven cards", "wheel", "each player draws", "discard their hand, then draw"]):
        tags.update(["wheel", "forced_draw", "card_advantage", "draw_punisher"])
    if _has_any(text, ["opponent draws", "each opponent draws", "target opponent draws"]):
        tags.update(["forced_draw", "political_card"])

    # Card advantage and selection.
    if _has_any(text, ["draw a card", "draw two cards", "draw three cards", "draw cards", "draw that many cards"]):
        tags.update(["card_draw", "card_advantage"])
    if _has_any(text, ["look at the top", "scry", "surveil", "reveal the top", "top card of your library"]):
        tags.update(["card_selection", "topdeck_manipulation"])
    if _has_any(text, ["exile the top", "you may play that card", "you may cast that card", "until the end of your next turn"]):
        tags.update(["card_advantage", "cast_from_outside_hand", "nonhand_casting"])

    # Interaction.
    if _has_any(text, ["destroy target", "exile target", "return target", "deals damage to target", "fight target", "target creature gets -"]):
        tags.add("targeted_removal")
    if _has_any(text, ["destroy all", "exile all", "each creature", "all creatures", "each nonland permanent"]):
        tags.add("board_wipe")
    if "counter target" in text:
        tags.add("counterspell")
        if _has_any(text, ["without paying", "rather than pay", "if you control your commander"]):
            tags.update(["free_interaction", "bracket_pressure"])

    # Protection.
    if _has_any(text, ["hexproof", "indestructible", "phase out", "protection from", "prevent all damage", "ward", "can't be countered"]):
        tags.add("protection")
    if _has_any(text, ["your opponents can't cast spells this turn", "opponents can't cast spells this turn"]):
        tags.update(["protection", "combo_protection", "bracket_pressure"])

    # Graveyard / recursion.
    if _has_any(text, ["return target creature card", "return target card from your graveyard", "return a card from your graveyard", "return from your graveyard", "from your graveyard to the battlefield"]):
        tags.update(["recursion", "graveyard_enabler"])
    if _has_any(text, ["mill", "surveil", "put the top", "into your graveyard"]):
        tags.update(["self_mill", "graveyard_enabler"])
    if _has_any(text, ["discard a card", "discard your hand", "then discard"]):
        tags.update(["discard_outlet", "graveyard_enabler"])

    # Sacrifice / aristocrats.
    if _has_any(text, ["sacrifice a creature", "sacrifice another creature", "sacrifice a permanent", "sacrifice an artifact", "sacrifice a treasure"]):
        tags.add("sacrifice_outlet")
        if ":" in text and "sacrifice" in text:
            tags.add("free_sacrifice_outlet")
    if _has_any(text, ["whenever a creature dies", "whenever another creature dies", "whenever one or more creatures die", "whenever you sacrifice"]):
        tags.update(["death_trigger_payoff", "sacrifice_payoff", "synergy_piece"])
    if _has_any(text, ["each opponent loses", "opponents lose", "loses that much life", "opponent loses life"]):
        tags.update(["lifedrain_payoff", "damage_payoff"])

    # Tokens and artifacts.
    if "create" in text and "token" in text:
        tags.update(["token_maker", "synergy_piece"])
    if "treasure token" in text or "treasures" in text:
        tags.update(["treasure_synergy", "artifact_token_synergy", "ramp"])
    if "clue token" in text or "investigate" in text or "clues" in text:
        tags.update(["clue_synergy", "artifact_token_synergy", "card_advantage"])
    if "food token" in text or "foods" in text:
        tags.update(["food_synergy", "artifact_token_synergy", "lifegain_payoff"])
    if _has_any(text, ["artifact you control", "artifacts you control", "whenever an artifact", "artifact spell"]):
        tags.update(["artifact_payoff", "artifact_token_synergy", "synergy_piece"])

    # Combat / counters / Voltron-ish support.
    if _has_any(text, ["whenever", "attacks", "attacking", "combat damage"]):
        if "attack" in text or "combat damage" in text:
            tags.update(["combat_synergy", "attack_trigger_payoff"])
    if _has_any(text, ["additional combat", "extra combat", "after this phase"]):
        tags.update(["extra_combat", "combat_synergy", "win_condition"])
    if "+1/+1 counter" in text or "proliferate" in text:
        tags.update(["counter_synergy", "synergy_piece"])
    if "equipment" in tl or "equip" in text or "equipped creature" in text:
        tags.add("equipment_synergy")
    if "aura" in tl or "enchanted creature" in text:
        tags.add("aura_synergy")
    if _has_any(text, ["double strike", "trample", "flying", "menace", "unblockable", "can't be blocked"]):
        if "creature" in tl:
            tags.add("combat_synergy")
    if _has_any(text, ["power", "commander damage", "+x/+x", "+1/+1"]):
        tags.add("go_tall_support")

    # Spellslinger / cast triggers.
    if _has_any(text, ["whenever you cast an instant", "whenever you cast a sorcery", "whenever you cast or copy", "magecraft", "instant or sorcery spell", "noncreature spell"]):
        tags.update(["spell_payoff", "noncreature_spell_payoff", "cast_trigger", "synergy_piece"])
    if _has_any(text, ["copy target spell", "copy that spell", "copy it", "copy each spell"]):
        tags.update(["cast_copy_synergy", "spell_payoff", "combo_piece_possible"])
    if _has_any(text, ["flashback", "jump-start", "cast target instant", "cast target sorcery"]):
        tags.update(["spell_recursion_possible", "graveyard_enabler"])

    # Blink / ETB / LTB.
    if _has_any(text, ["enters the battlefield", "enter the battlefield", "when this creature enters", "whenever another creature enters"]):
        tags.add("etb_value")
    if _has_any(text, ["leaves the battlefield", "when it dies", "dies"]):
        tags.add("ltb_value")
    if _has_any(text, ["exile target creature you control, then return", "exile target permanent you control, then return", "return it to the battlefield", "return those cards to the battlefield", "blink", "flicker"]):
        tags.update(["blink_flicker", "exile_return", "synergy_piece"])

    # Lands / landfall.
    if _has_any(text, ["landfall", "whenever a land enters", "land enters the battlefield under your control"]):
        tags.update(["landfall", "landfall_payoff", "lands_matter", "synergy_piece"])
    if _has_any(text, ["play an additional land", "play lands from your graveyard", "land card from your graveyard"]):
        tags.update(["extra_land_play", "lands_matter", "landfall", "ramp"])
    if _has_any(text, ["rock artifact token", "artifact token named rock"]):
        tags.update(["rock_token_synergy", "land_token", "artifact_token_synergy", "landfall", "landfall_payoff", "token_maker"])

    # Lifegain / toughness / defenders.
    if _has_any(text, ["whenever you gain life", "if you would gain life", "gain twice that much life", "you gain life"]):
        tags.add("lifegain_payoff")
    if _has_any(text, ["defender", "wall"]):
        tags.add("wall_typal")
    if _has_any(text, ["creatures with defender", "walls you control", "assigns combat damage equal to its toughness", "equal to its toughness", "greatest toughness"]):
        tags.update(["defender_payoff", "toughness_payoff", "synergy_piece"])
    try:
        toughness_value = int(card.get("toughness", ""))
        power_value = int(card.get("power", "0")) if str(card.get("power", "0")).isdigit() else 0
        if toughness_value >= 4 and toughness_value > power_value:
            tags.add("high_toughness")
    except Exception:
        pass

    # Typal.
    subtypes = get_creature_subtypes(type_line)
    if subtypes:
        tags.add("creature_type_present")
        # Store generic density; specific subtype counts are handled in strategy modules later.
        if len(subtypes) > 0:
            tags.add("typal_density_piece")
    if get_tribal_dependency_types(oracle) or get_tribal_payoff_types(oracle):
        tags.update(["tribal_dependency", "tribal_payoff", "typal_payoff", "synergy_piece"])
    if "changeling" in text:
        tags.update(["typal_density_piece", "typal_enabler"])
    if "dragon" in tl or "dragon" in text:
        tags.add("dragon_typal")
    if _has_any(text, ["token that's a copy", "copy of target creature", "copy target creature", "enters as a copy"]):
        tags.update(["copy_clone_value", "combo_piece_possible", "synergy_piece"])
        if "dragon" in text or "dragon" in tl:
            tags.update(["dragon_copy_value", "dragon_typal"])

    # Activated ability / mana sinks.
    if _has_any(text, ["activated abilities", "activated ability", "activate abilities", "abilities cost", "copy target activated ability"]):
        tags.add("activated_ability_synergy")
    if _has_any(text, ["{x}", "x is", "x damage", "x cards", "spend this mana"]):
        tags.add("mana_sink")

    # Alternate casting / modern mechanics.
    if "adventure" in text or "on an adventure" in text:
        tags.update(["adventure_synergy", "modal_spell_synergy", "creature_spell_hybrid", "cast_from_outside_hand"])
    if "suspend" in text or "time counter" in text:
        tags.update(["suspend_synergy", "cast_from_outside_hand", "alternate_cost_interaction"])
    if "foretell" in text:
        tags.update(["foretell", "cast_from_outside_hand", "nonhand_casting", "alternate_cost_interaction"])
    if "plot" in text:
        tags.update(["plot", "cast_from_outside_hand", "nonhand_casting", "alternate_cost_interaction"])
    if _has_any(text, ["cast a spell from anywhere other than your hand", "cast a spell from exile", "cast it from exile", "cast from exile", "you may cast"]):
        if _has_any(text, ["exile", "graveyard", "top of your library", "foretell", "plot", "suspend", "adventure"]):
            tags.update(["cast_from_outside_hand", "nonhand_casting", "card_advantage"])
    if "mutate" in text or "mutates" in text or "mutated" in text:
        tags.update(["mutate", "creature_cast_trigger", "creature_combo_value", "synergy_piece"])
        if _has_any(text, ["whenever this creature mutates", "when this creature mutates"]):
            tags.add("mutate_payoff")
        if _has_any(text, ["mutate cost", "costs {1} less to mutate", "non-human creature"]):
            tags.add("mutate_enabler")

    # Tutors / combo / win markers.
    if "search your library" in text and "basic land" not in text:
        tags.add("tutor")
        if "for a card" in text:
            tags.update(["efficient_tutor", "bracket_pressure"])
        if _has_any(text, ["creature card", "artifact card", "enchantment card"]):
            tags.add("toolbox_support")
    if _has_any(text, ["you win the game", "each opponent loses the game", "loses the game"]):
        tags.update(["win_condition", "combo_piece_possible", "bracket_pressure"])

    # Manual review for unusual or custom-ish objects.
    if not card.get("name") or not type_line:
        tags.add("manual_review")

    return sorted(tags)


def summarize_role_reason(card: dict[str, Any], tags: list[str]) -> str:
    if not tags:
        return "No clear role tags detected from card text; manual review may be needed."
    priority = [tag for tag in ROLE_TAG_DISPLAY_ORDER if tag in tags]
    shown = priority[:4] if priority else tags[:4]
    return "Detected roles: " + ", ".join(shown) + "."


def build_role_analysis(
    parsed_deck: ParsedDeck,
    scryfall_lookup: dict[str, dict[str, Any]],
    command_zone: CommandZoneSummary | None = None,
) -> RoleAnalysisSummary:
    card_roles: list[CardRoleEntry] = []
    role_counts: Counter[str] = Counter()
    type_counts: Counter[str] = Counter()
    card_role_tags_by_card: dict[str, list[str]] = {}
    unknown_cards: list[str] = []
    commander_cards = command_zone.commander_cards_scryfall if command_zone else []

    for card_name, quantity in parsed_deck.unique_cards.items():
        card = scryfall_lookup.get(card_name.lower())
        if not card:
            unknown_cards.append(card_name)
            tags = ["manual_review"]
            entry = CardRoleEntry(
                card_name=card_name,
                quantity=quantity,
                found_in_scryfall=False,
                detected_roles=tags,
                confidence="low",
                short_reason="Card was not found in local Scryfall data.",
            )
            card_roles.append(entry)
            role_counts.update({tag: quantity for tag in tags})
            card_role_tags_by_card[card_name] = tags
            continue

        tags = infer_card_role_tags(card, commander_cards=commander_cards)
        card_types = sorted(get_face_aware_major_types(card))
        for card_type in card_types:
            type_counts[card_type] += quantity
        role_counts.update({tag: quantity for tag in tags})
        card_role_tags_by_card[card_name] = tags
        card_roles.append(CardRoleEntry(
            card_name=card_name,
            quantity=quantity,
            found_in_scryfall=True,
            mana_value=card.get("cmc"),
            card_types=card_types,
            color_identity=list(card.get("color_identity", []) or []),
            detected_roles=tags,
            confidence="medium" if tags else "low",
            short_reason=summarize_role_reason(card, tags),
            type_line=card.get("type_line", ""),
        ))

    return RoleAnalysisSummary(
        card_roles=card_roles,
        role_counts=role_counts,
        type_counts=type_counts,
        card_role_tags_by_card=card_role_tags_by_card,
        unknown_cards=unknown_cards,
    )


def top_role_counts(role_counts: Counter[str], limit: int = 15) -> list[tuple[str, int]]:
    return role_counts.most_common(limit)
