"""Collection candidate matching for The Dragon's Touch.

v0.6.4.3.4 scope:
- Harden replacement-category-to-role mapping after semantic gate testing.
- Prevent substring leakage such as ramp/mana cards matching evasion/trample.
- Prevent graveyard recursion/value cards from being tagged as board wipes.
- Keep broad combat/protection overlap from becoming a Strong owned-card recommendation by itself.
- Add a promotion gate so single-body beaters and generic colorless creatures stay Possible unless they are clearly deck-specific upgrades.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable

from data.card_lookup import (
    get_full_oracle_text,
    get_representative_nonland_mana_value,
    has_type_on_any_face,
    normalize_text,
)
from legality.companion_rules import check_card_against_companion


@dataclass(slots=True)
class CollectionCandidate:
    card_name: str
    quantity_owned: int
    confidence: str
    fit_type: str
    matched_needs: list[str] = field(default_factory=list)
    role_tags: list[str] = field(default_factory=list)
    reason: str = ""
    source_files: list[str] = field(default_factory=list)
    color_identity: list[str] = field(default_factory=list)
    mana_value: float | int | None = None
    warnings: list[str] = field(default_factory=list)
    quality_gate: str = ""


@dataclass(slots=True)
class CollectionRejectedCard:
    card_name: str
    quantity_owned: int
    reason: str


@dataclass(slots=True)
class CollectionCandidateSummary:
    active: bool = False
    mode: str = "none"
    candidate_matching_active: bool = False
    collection_loaded: bool = False
    total_owned_cards: int = 0
    unique_owned_cards: int = 0
    strong_candidates: list[CollectionCandidate] = field(default_factory=list)
    possible_candidates: list[CollectionCandidate] = field(default_factory=list)
    shakeup_candidates: list[CollectionCandidate] = field(default_factory=list)
    rejected_candidates: list[CollectionRejectedCard] = field(default_factory=list)
    no_strong_fit_categories: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    quality_gate_notes: list[str] = field(default_factory=list)
    strong_candidates_considered: int = 0
    strong_candidates_accepted: int = 0
    downgraded_to_possible: int = 0
    downgraded_to_shakeup: int = 0
    downgrade_reason_counts: list[tuple[str, int]] = field(default_factory=list)

    @property
    def candidates(self) -> list[str]:
        """Backward-compatible string list used by older report code."""
        return [candidate.card_name for candidate in self.strong_candidates]


RAMP_PHRASES = [
    "add {", "add one mana", "add two mana", "search your library for a land", "put a land card",
    "additional land", "play an additional land", "treasure token", "mana of any color", "mana in any combination",
]
DRAW_PHRASES = [
    "draw a card", "draw cards", "look at the top", "exile the top", "put it into your hand",
]
REMOVAL_PHRASES = [
    "destroy target", "exile target", "return target", "damage to target", "counter target",
    "tap target creature", "doesn't untap", "fight target", "target creature gets -", "target opponent sacrifices",
]
WIPE_PHRASES = [
    # Keep this list intentionally narrow. Do not include generic phrases like
    # "return all" because graveyard cards such as Splendid Reclamation return
    # all lands and are not board wipes.
    "destroy all creatures", "destroy all artifacts", "destroy all enchantments",
    "destroy all nonland permanents", "destroy all permanents",
    "exile all creatures", "exile all artifacts", "exile all enchantments",
    "exile all nonland permanents", "exile all permanents",
    "return all creatures", "return all nonland permanents", "return all permanents",
    "destroy each creature", "destroy each nonland permanent",
    "exile each creature", "exile each nonland permanent",
    "deals damage to each creature", "damage to each creature",
    "creatures get -", "all creatures get -",
]
PROTECTION_PHRASES = [
    "hexproof", "indestructible", "protection from", "prevent all damage", "phase out", "can't be countered",
    "regenerate", "ward", "shield counter",
]
TOKEN_PHRASES = [
    "create a", "create x", "create one", "create two", "token", "tokens", "populate", "copy token",
]
RECURSION_PHRASES = [
    "return target", "from your graveyard", "from a graveyard", "put target card", "reanimate",
]
GRAVEYARD_PHRASES = [
    "mill", "surveil", "discard", "graveyard", "escape", "flashback", "disturb", "unearth",
]
SPELL_PAYOFF_PHRASES = [
    "instant or sorcery", "noncreature spell", "whenever you cast", "copy target instant", "copy target sorcery",
]
EVASION_PHRASES = [
    "trample", "flying", "menace", "double strike", "first strike",
    "can't be blocked", "unblockable", "horsemanship",
]
COMBAT_PHRASES = [
    "trample", "haste", "double strike", "menace", "flying",
    "can't be blocked", "unblockable", "attacks", "combat damage",
]
COUNTER_PHRASES = ["+1/+1 counter", "proliferate", "counter on", "counters on"]
SACRIFICE_PHRASES = ["sacrifice", "dies", "whenever another creature dies", "death trigger"]
FINISHER_PHRASES = [
    "creatures you control get", "creature you control gets", "+x/+x", "double", "win the game",
    "damage to each opponent", "overwhelming", "trample", "can't be blocked",
]
NARROW_TYPAL_REQUIREMENT_PHRASES = [
    "human you control", "humans you control", "dragon you control", "dragons you control",
    "vampire you control", "dinosaurs you control", "artifact creature you control",
]

TEAM_WIDE_COMBAT_PHRASES = [
    "creatures you control", "creature you control gets", "each creature you control",
    "attacking creatures", "whenever one or more creatures you control", "creatures with power",
    "creatures you control have", "creatures you control gain",
]
LAND_PLAN_PHRASES = [
    "landfall", "whenever a land enters", "land enters the battlefield",
    "land card from your graveyard", "play an additional land", "additional land",
    "lands you control", "forests you control", "search your library for a land",
    "put a land card", "for each land you control",
]
BOARD_PROTECTION_PHRASES = [
    "creatures you control gain indestructible", "creatures you control have hexproof",
    "permanents you control gain", "permanents you control have",
    "creatures you control get", "prevent all damage",
]

BROAD_ROLES = {"artifact", "creature", "enchantment", "instant", "sorcery", "land", "mana_source", "combat_support"}
GENERIC_UTILITY_ROLES = {"ramp", "card_draw", "card_advantage", "targeted_removal", "protection"}
SPECIFIC_PLAN_ROLES = {
    "token_production", "evasion_support", "finisher_or_payoff", "counter_synergy",
    "sacrifice_synergy", "recursion", "graveyard_setup", "spell_payoff",
    "typal_or_theme_support", "board_wipe", "mana_doubler", "treasure_synergy",
    "team_wide_combat_support", "land_plan_support", "board_protection_specific",
}


@dataclass(frozen=True)
class CategoryNeed:
    direct: frozenset[str]
    support: frozenset[str] = frozenset()
    label: str = ""


def _card_name_key(name: object) -> str:
    return str(name).strip().lower()


def _contains_any(text: str, phrases: Iterable[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def _card_text(card: dict[str, Any]) -> str:
    return normalize_text(" ".join([
        str(card.get("name", "")),
        str(card.get("type_line", "")),
        get_full_oracle_text(card),
    ]))


def _card_color_identity(card: dict[str, Any]) -> list[str]:
    return list(card.get("color_identity", []) or [])


def _is_color_legal(card: dict[str, Any], commander_colors: set[str]) -> bool:
    return set(_card_color_identity(card)).issubset(commander_colors)


def _infer_collection_roles(card: dict[str, Any]) -> list[str]:
    text = _card_text(card)
    roles: set[str] = set()

    if has_type_on_any_face(card, "Land"):
        roles.update({"land", "mana_source"})
    if has_type_on_any_face(card, "Creature"):
        roles.add("creature")
    if has_type_on_any_face(card, "Artifact"):
        roles.add("artifact")
    if has_type_on_any_face(card, "Enchantment"):
        roles.add("enchantment")
    if has_type_on_any_face(card, "Instant"):
        roles.add("instant")
    if has_type_on_any_face(card, "Sorcery"):
        roles.add("sorcery")

    if _contains_any(text, RAMP_PHRASES):
        roles.update({"ramp", "mana_source"})
    if _contains_any(text, DRAW_PHRASES):
        roles.update({"card_draw", "card_advantage"})
    if _contains_any(text, REMOVAL_PHRASES):
        roles.add("targeted_removal")
    if _is_true_board_wipe_text(text):
        roles.add("board_wipe")
    if _contains_any(text, PROTECTION_PHRASES):
        roles.add("protection")
    if _contains_any(text, TEAM_WIDE_COMBAT_PHRASES):
        roles.add("team_wide_combat_support")
    if _contains_any(text, LAND_PLAN_PHRASES):
        roles.add("land_plan_support")
    if _contains_any(text, BOARD_PROTECTION_PHRASES):
        roles.add("board_protection_specific")
    if "treasure token" in text or "treasure tokens" in text:
        roles.update({"ramp", "mana_source", "treasure_synergy"})
    # Treat creature-token production as a deck-plan token role. Treasure, clue,
    # food, map, and other utility tokens are useful, but they should not satisfy
    # "More token production" for go-wide combat decks by themselves.
    if (
        "creature token" in text
        or "creature tokens" in text
        or "token that's a copy" in text
        or "tokens that are copies" in text
        or "copy token" in text
        or "populate" in text
    ):
        roles.add("token_production")
    if _contains_any(text, RECURSION_PHRASES):
        roles.add("recursion")
    if _contains_any(text, GRAVEYARD_PHRASES):
        roles.add("graveyard_setup")
    if _contains_any(text, SPELL_PAYOFF_PHRASES):
        roles.add("spell_payoff")
    if _contains_any(text, EVASION_PHRASES):
        roles.add("evasion_support")
    if _contains_any(text, COMBAT_PHRASES):
        roles.add("combat_support")
    if _contains_any(text, COUNTER_PHRASES):
        roles.add("counter_synergy")
    if _contains_any(text, SACRIFICE_PHRASES):
        roles.add("sacrifice_synergy")
    if _contains_any(text, FINISHER_PHRASES):
        roles.add("finisher_or_payoff")
    if _contains_any(text, NARROW_TYPAL_REQUIREMENT_PHRASES):
        roles.add("narrow_typal_requirement")

    # Common typal/payoff words. This is intentionally broad but never enough by
    # itself to make a card a strong collection recommendation.
    if any(word in text for word in ["dragon", "vampire", "dinosaur", "artifact creature", "creature type"]):
        roles.add("typal_or_theme_support")
    if any(word in text for word in ["copy", "double", "damage to each opponent", "win the game"]):
        roles.add("finisher_or_payoff")

    return sorted(roles)


def _is_true_board_wipe_text(text: str) -> bool:
    """Return True only for real mass-removal wording.

    This deliberately rejects graveyard/value phrases such as "return all land
    cards from your graveyard" and discard-storage cards that happen to use
    broad words like "return all".
    """
    if not _contains_any(text, WIPE_PHRASES):
        return False
    # These are common false-positive contexts from collection testing.
    false_positive_fragments = [
        "return all land cards from your graveyard",
        "return all land cards",
        "return all creature cards from your graveyard",
        "put all land cards",
        "exiled with",
        "bag of holding",
    ]
    if _contains_any(text, false_positive_fragments):
        return False
    # A true wipe should refer to a mass object class or all/each creatures.
    true_object_fragments = [
        "all creatures", "each creature", "all nonland permanents",
        "each nonland permanent", "all permanents", "all artifacts",
        "all enchantments", "damage to each creature", "creatures get -",
    ]
    return _contains_any(text, true_object_fragments)


def _category_role_needs(category: str) -> CategoryNeed:
    """Map replacement category text to direct/support roles.

    This intentionally avoids raw substring checks like "ramp" in "trample".
    Direct roles can justify stronger candidates. Support roles can make a card
    possible, but not strong by themselves.
    """
    cat = category.lower()

    if "evasion" in cat or "trample" in cat:
        # No support roles here. Ramp, generic creatures, or generic combat text
        # must not appear as matches for an evasion/trample need.
        return CategoryNeed(frozenset({"evasion_support"}), frozenset(), "evasion/trample")
    if "combat finisher" in cat or "finisher" in cat:
        return CategoryNeed(frozenset({"finisher_or_payoff", "evasion_support"}), frozenset({"combat_support", "token_production"}), "combat finisher")
    if "combat payoff" in cat or "combat" in cat:
        return CategoryNeed(frozenset({"finisher_or_payoff", "evasion_support", "token_production"}), frozenset({"combat_support"}), "combat payoff")
    if "table-stabilizing" in cat:
        return CategoryNeed(frozenset({"targeted_removal", "board_wipe"}), frozenset({"protection"}), "table-stabilizing interaction")
    if "targeted removal" in cat or "interaction" in cat or "answer" in cat:
        return CategoryNeed(frozenset({"targeted_removal"}), frozenset({"board_wipe"}), "targeted interaction")
    if "board wipe" in cat:
        return CategoryNeed(frozenset({"board_wipe"}), frozenset({"targeted_removal"}), "board wipe")
    if "board protection" in cat or "protection" in cat:
        return CategoryNeed(frozenset({"protection"}), frozenset({"evasion_support"}), "protection")
    if "token" in cat:
        return CategoryNeed(frozenset({"token_production"}), frozenset({"creature", "finisher_or_payoff"}), "token production")
    if "ramp" in cat or "mana" in cat:
        return CategoryNeed(frozenset({"ramp", "mana_source", "land"}), frozenset({"card_draw"}), "ramp/mana")
    if "draw" in cat or "card advantage" in cat or "selection" in cat:
        return CategoryNeed(frozenset({"card_draw", "card_advantage"}), frozenset({"recursion"}), "card advantage")
    if "typal" in cat or "tribal" in cat or "dragon" in cat or "on-type" in cat:
        return CategoryNeed(frozenset({"typal_or_theme_support", "creature"}), frozenset({"finisher_or_payoff"}), "typal")
    if "graveyard" in cat:
        return CategoryNeed(frozenset({"graveyard_setup", "recursion"}), frozenset({"card_draw"}), "graveyard")
    if "recursion" in cat:
        return CategoryNeed(frozenset({"recursion"}), frozenset({"graveyard_setup"}), "recursion")
    if "spell" in cat or "instant" in cat or "sorcery" in cat:
        return CategoryNeed(frozenset({"spell_payoff", "instant", "sorcery"}), frozenset({"card_draw", "targeted_removal"}), "spells")
    if "mutate" in cat:
        return CategoryNeed(frozenset({"creature", "protection"}), frozenset({"evasion_support"}), "mutate")
    if "sacrifice" in cat or "death" in cat:
        return CategoryNeed(frozenset({"sacrifice_synergy"}), frozenset({"token_production", "recursion"}), "sacrifice")
    if "counter" in cat:
        return CategoryNeed(frozenset({"counter_synergy"}), frozenset({"combat_support"}), "counters")
    return CategoryNeed(frozenset(), frozenset(), "unknown")


def _safe_direct_overlap(category: str, need: CategoryNeed, role_set: set[str]) -> set[str]:
    """Apply hard category gates so similar words cannot leak across roles."""
    cat = category.lower()
    overlap = role_set & set(need.direct)

    if "evasion" in cat or "trample" in cat:
        return overlap & {"evasion_support"}
    if "board wipe" in cat:
        return overlap & {"board_wipe"}
    if "token" in cat:
        return overlap & {"token_production"}
    if "combat finisher" in cat or "finisher" in cat:
        return overlap & {"finisher_or_payoff", "evasion_support"}
    if "combat payoff" in cat or "combat" in cat:
        return overlap & {"finisher_or_payoff", "evasion_support", "token_production"}
    if "ramp" in cat or ("mana" in cat and "trample" not in cat):
        return overlap & {"ramp", "mana_source", "land"}
    if "table-stabilizing" in cat or "targeted removal" in cat or "interaction" in cat or "answer" in cat:
        return overlap & {"targeted_removal", "board_wipe"}
    if "board protection" in cat or "protection" in cat:
        return overlap & {"protection"}
    return overlap


def _safe_support_overlap(category: str, need: CategoryNeed, role_set: set[str]) -> set[str]:
    """Support overlaps are deliberately conservative for noisy categories."""
    cat = category.lower()
    overlap = role_set & set(need.support)
    if "evasion" in cat or "trample" in cat:
        return set()
    if "board wipe" in cat:
        return set()
    if "token" in cat:
        # Generic creatures/finishers are not evidence that a card supplies tokens.
        return set()
    if "combat finisher" in cat or "combat payoff" in cat or "combat" in cat:
        # Generic combat text can be too noisy; keep it from counting as a match.
        return overlap & {"token_production"}
    return overlap


def _strong_category_allowed(category: str, role_set: set[str]) -> bool:
    """A final strong-candidate guardrail per replacement category."""
    cat = category.lower()
    if "evasion" in cat or "trample" in cat:
        return "evasion_support" in role_set
    if "board wipe" in cat:
        return "board_wipe" in role_set
    if "token" in cat:
        return "token_production" in role_set
    if "combat finisher" in cat or "finisher" in cat:
        return bool(role_set & {"finisher_or_payoff", "evasion_support"})
    if "combat payoff" in cat or "combat" in cat:
        return bool(role_set & {"finisher_or_payoff", "evasion_support", "token_production"})
    return True


def _strategy_bonus_roles(primary: str, secondary: str) -> set[str]:
    joined = f"{primary} {secondary}".lower()
    roles: set[str] = set()
    if any(token in joined for token in ["token", "go-wide", "go-tall"]):
        roles.update({"token_production", "finisher_or_payoff", "protection", "team_wide_combat_support"})
    if "combat" in joined or "voltron" in joined or "stompy" in joined:
        roles.update({"finisher_or_payoff", "evasion_support", "protection", "team_wide_combat_support"})
    if "landfall" in joined or "lands" in joined:
        roles.update({"ramp", "land", "mana_source", "token_production", "land_plan_support"})
    if "typal" in joined or "tribal" in joined or "dragon" in joined:
        roles.update({"typal_or_theme_support", "finisher_or_payoff"})
    if "spellslinger" in joined or "noncreature" in joined:
        roles.update({"instant", "sorcery", "spell_payoff", "card_draw", "targeted_removal"})
    if "graveyard" in joined:
        roles.update({"graveyard_setup", "recursion"})
    if "engine" in joined or "value" in joined:
        roles.update({"card_draw", "card_advantage", "recursion"})
    return roles


def _source_files_for_card(collection_summary: Any, card_name: str) -> list[str]:
    sources = getattr(collection_summary, "card_sources", {}) or {}
    return list(sources.get(card_name, []) or sources.get(_card_name_key(card_name), []) or [])


def _candidate_reason(matched_needs: list[str], roles: list[str], strategy_bonus: bool, quality_gate: str) -> str:
    if matched_needs:
        base = f"Matches owned-card role need(s): {', '.join(matched_needs[:4])}."
    else:
        base = "Does not directly satisfy a current replacement category."
    if strategy_bonus:
        base += " Has some overlap with the current primary/secondary strategy shape."
    if quality_gate:
        base += f" Quality gate: {quality_gate}."
    if roles:
        base += f" Detected collection roles: {', '.join(roles[:8])}."
    return base


def _make_candidate(
    card_name: str,
    quantity: int,
    confidence: str,
    fit_type: str,
    matched_needs: list[str],
    roles: list[str],
    reason: str,
    card: dict[str, Any],
    source_files: list[str],
    warnings: list[str] | None = None,
    quality_gate: str = "",
) -> CollectionCandidate:
    return CollectionCandidate(
        card_name=card_name,
        quantity_owned=quantity,
        confidence=confidence,
        fit_type=fit_type,
        matched_needs=matched_needs,
        role_tags=roles,
        reason=reason,
        source_files=source_files,
        color_identity=_card_color_identity(card),
        mana_value=get_representative_nonland_mana_value(card),
        warnings=warnings or [],
        quality_gate=quality_gate,
    )


def _is_generic_colorless_artifact(card: dict[str, Any], role_set: set[str]) -> bool:
    if _card_color_identity(card):
        return False
    if not has_type_on_any_face(card, "Artifact"):
        return False
    # Colorless artifacts can be useful, but in collection pull they should not
    # be promoted to Strong unless they solve a very specific role such as a real
    # board wipe, true token engine, or explicit land-plan support.
    if role_set & {"board_wipe", "token_production", "land_plan_support", "team_wide_combat_support"}:
        return False
    return True


def _is_generic_colorless_creature(card: dict[str, Any], role_set: set[str]) -> bool:
    if _card_color_identity(card):
        return False
    if not has_type_on_any_face(card, "Creature"):
        return False
    if role_set & {"board_wipe", "token_production", "land_plan_support", "team_wide_combat_support", "board_protection_specific"}:
        return False
    return True


def _is_standalone_beater(card: dict[str, Any], role_set: set[str]) -> bool:
    if not has_type_on_any_face(card, "Creature"):
        return False
    if not (role_set & {"combat_support", "evasion_support", "finisher_or_payoff", "protection"}):
        return False
    # If the card helps the whole board, makes tokens, draws cards, or directly
    # supports lands/commander infrastructure, it is more than a standalone body.
    if role_set & {"team_wide_combat_support", "token_production", "card_draw", "card_advantage", "land_plan_support", "board_protection_specific"}:
        return False
    return True


def _strong_promotion_allowed(
    card: dict[str, Any],
    role_set: set[str],
    matched_categories: list[str],
    primary_strategy: str,
    secondary_strategy: str,
) -> tuple[bool, str]:
    """Final gate for Strong Owned Candidates.

    The earlier gates answer: does the card match a role? This answers: is it
    deck-specific enough to be called a strong owned recommendation?
    """
    joined = f"{primary_strategy} {secondary_strategy}".lower()
    categories = " ".join(matched_categories).lower()

    if not matched_categories:
        return False, "no direct matched category"

    if _is_generic_colorless_creature(card, role_set):
        return False, "generic/colorless creature is capped at Possible without a deck-specific engine role"

    if _is_standalone_beater(card, role_set):
        return False, "standalone combat body is capped at Possible unless the pilot specifically wants more independent beaters"

    # Board wipes in non-control shells should usually be Possible, not Strong.
    if "board wipe" in categories and "control" not in joined:
        return False, "board wipe is a possible role fit but not a clear strategy-specific upgrade"

    # Protection is Strong only when it protects the board/commander plan, not
    # when the card mostly protects itself.
    if "protection" in categories and "board_protection_specific" not in role_set and "team_wide_combat_support" not in role_set:
        return False, "self-protection or generic protection is not enough for Strong"

    # Combat/evasion categories need board-wide payoff, token relevance, land-plan
    # relevance, or explicit card advantage. A lone efficient attacker is Possible.
    if any(token in categories for token in ["combat", "evasion", "trample", "finisher"]):
        if not (role_set & {"team_wide_combat_support", "token_production", "land_plan_support", "board_protection_specific", "card_draw", "card_advantage"}):
            return False, "combat/evasion card lacks board-wide or deck-engine relevance"

    # Landfall/Lands decks should prefer land-plan or token/go-tall cards over
    # generic combat bodies.
    if ("landfall" in joined or "lands" in joined) and any(token in categories for token in ["combat", "evasion", "trample", "finisher", "token"]):
        if not (role_set & {"land_plan_support", "token_production", "team_wide_combat_support", "card_draw", "card_advantage"}):
            return False, "lands-matter shell needs land-plan, token, card-flow, or board-wide evidence for Strong"

    return True, "passes strong promotion gate"


def _card_has_narrow_requirement(card: dict[str, Any]) -> bool:
    return "narrow_typal_requirement" in set(_infer_collection_roles(card))


def build_collection_candidate_summary(
    collection_summary: Any | None = None,
    replacement_needs: Any | None = None,
    parsed_deck: Any | None = None,
    command_zone: Any | None = None,
    legality: Any | None = None,
    scryfall_lookup: dict[str, dict[str, Any]] | None = None,
    strategy_summary: Any | None = None,
    runtime_config: Any | None = None,
) -> CollectionCandidateSummary:
    """Match owned cards to current deck needs without forcing bad recommendations."""
    scryfall_lookup = scryfall_lookup or {}
    mode = getattr(collection_summary, "mode", "none") if collection_summary else "none"
    active = mode != "none"
    loaded = bool(getattr(collection_summary, "loaded", False)) if collection_summary else False
    summary = CollectionCandidateSummary(
        active=active,
        mode=mode,
        candidate_matching_active=active and loaded,
        collection_loaded=loaded,
        total_owned_cards=getattr(collection_summary, "total_cards", 0) if collection_summary else 0,
        unique_owned_cards=getattr(collection_summary, "unique_cards", 0) if collection_summary else 0,
    )
    summary.quality_gate_notes.extend([
        "Strong candidates require a direct need match plus semantic strategy relevance.",
        "Support-only category overlap is not displayed as a matched deck need.",
        "Broad role overlap alone is capped at Possible or Shakeup.",
        "Generic/colorless artifacts and narrow typal cards are not promoted to Strong without a clear deck-specific reason.",
        "Role mapping hardening is active: evasion/trample, board wipe, token, and combat categories use exact semantic gates.",
        "Strong promotion gate is active: standalone beaters, generic colorless bodies, and self-protection cards are usually capped at Possible.",
    ])

    if not active:
        summary.notes.append("Collection mode is off; no owned-card candidate matching was performed.")
        return summary
    if not loaded:
        summary.notes.append("Collection mode is active, but no collection cards were loaded; no owned-card candidates are available.")
        return summary

    deck_cards = {_card_name_key(name) for name in (getattr(parsed_deck, "cards", []) or [])}
    commander_colors = set(getattr(command_zone, "commander_color_identity_set", set()) or set())
    if not commander_colors and command_zone:
        commander_colors = set(getattr(command_zone, "commander_color_identity", []) or [])

    priority_categories = list(getattr(replacement_needs, "priority_categories", []) or [])
    category_needs = {category: _category_role_needs(category) for category in priority_categories}
    strategy_roles = _strategy_bonus_roles(
        getattr(strategy_summary, "primary_strategy", ""),
        getattr(strategy_summary, "secondary_strategy", ""),
    )
    companion_names = list(getattr(command_zone, "companion_names", []) or [])

    strong: list[tuple[int, CollectionCandidate]] = []
    possible: list[tuple[int, CollectionCandidate]] = []
    shakeup: list[tuple[int, CollectionCandidate]] = []
    rejected: list[CollectionRejectedCard] = []
    strong_category_hits: Counter[str] = Counter()
    any_category_hits: Counter[str] = Counter()
    downgrade_reasons: Counter[str] = Counter()

    for card_name, quantity in (getattr(collection_summary, "card_quantities", {}) or {}).items():
        card = scryfall_lookup.get(_card_name_key(card_name))
        if not card:
            rejected.append(CollectionRejectedCard(card_name=card_name, quantity_owned=quantity, reason="Not found in Scryfall after collection resolution."))
            continue

        if _card_name_key(card_name) in deck_cards:
            rejected.append(CollectionRejectedCard(card_name=card_name, quantity_owned=quantity, reason="Already in the deck; not recommended as an addition/replacement in this MVP."))
            continue

        if commander_colors and not _is_color_legal(card, commander_colors):
            rejected.append(CollectionRejectedCard(card_name=card_name, quantity_owned=quantity, reason="Outside commander color identity."))
            continue

        companion_warnings: list[str] = []
        companion_blocked = False
        for companion_name in companion_names:
            violation, manual_review = check_card_against_companion(companion_name, card_name, card)
            if violation:
                companion_blocked = True
                rejected.append(CollectionRejectedCard(
                    card_name=card_name,
                    quantity_owned=quantity,
                    reason=f"Breaks confirmed companion restriction: {violation.get('reason')}",
                ))
                break
            if manual_review:
                companion_warnings.append(str(manual_review.get("reason", "Manual companion review required.")))
        if companion_blocked:
            continue

        roles = _infer_collection_roles(card)
        role_set = set(roles)
        matched_categories: list[str] = []
        support_categories: list[str] = []
        direct_hits = 0
        support_hits = 0
        score = 0

        for category, need in category_needs.items():
            direct_overlap = _safe_direct_overlap(category, need, role_set)
            support_overlap = _safe_support_overlap(category, need, role_set)
            if direct_overlap:
                matched_categories.append(category)
                any_category_hits[category] += 1
                direct_hits += len(direct_overlap)
                # Direct matches to specific plan roles are more meaningful than
                # direct matches to generic utility roles like ramp or removal.
                specific_direct = direct_overlap & SPECIFIC_PLAN_ROLES
                score += 4 + min(2, len(direct_overlap) - 1)
                if specific_direct:
                    score += 2
            elif support_overlap:
                # Support-only overlap may help a card appear as Possible, but it
                # should not be displayed as a satisfied deck need or close a gap.
                support_categories.append(category)
                any_category_hits[category] += 1
                support_hits += len(support_overlap)
                score += 1

        strategy_overlap_roles = role_set & strategy_roles
        strategy_specific_overlap = bool(strategy_overlap_roles & SPECIFIC_PLAN_ROLES)
        strategy_overlap = bool(strategy_overlap_roles)
        if strategy_specific_overlap:
            score += 3
        elif strategy_overlap:
            score += 1

        if role_set & GENERIC_UTILITY_ROLES:
            score += 1

        warnings: list[str] = list(companion_warnings)
        quality_gate_parts: list[str] = []
        cap_to_possible = False
        cap_to_shakeup = False
        semantic_strong_fit = False

        direct_specific_roles = role_set & SPECIFIC_PLAN_ROLES
        generic_only = bool(role_set & GENERIC_UTILITY_ROLES) and not direct_specific_roles

        if direct_hits == 0 and support_hits > 0:
            cap_to_possible = True
            quality_gate_parts.append("support-only overlap; not enough for a strong upgrade")
            downgrade_reasons["support_only"] += 1
        if not matched_categories and strategy_overlap:
            cap_to_shakeup = True
            quality_gate_parts.append("strategy-adjacent but does not directly match a current deck need")
            downgrade_reasons["strategy_adjacent_only"] += 1
        if _is_generic_colorless_artifact(card, role_set):
            cap_to_possible = True
            msg = "generic/colorless artifact fit needs pilot review before being treated as an upgrade"
            warnings.append(msg)
            quality_gate_parts.append(msg)
            downgrade_reasons["generic_colorless_artifact"] += 1
        if _is_generic_colorless_creature(card, role_set):
            cap_to_possible = True
            msg = "generic/colorless creature fit needs pilot review before being treated as an upgrade"
            warnings.append(msg)
            quality_gate_parts.append(msg)
            downgrade_reasons["generic_colorless_creature"] += 1
        if _is_standalone_beater(card, role_set) and matched_categories:
            cap_to_possible = True
            msg = "standalone combat body; possible role fit but not enough for Strong without pilot intent"
            warnings.append(msg)
            quality_gate_parts.append(msg)
            downgrade_reasons["standalone_beater"] += 1
        if "narrow_typal_requirement" in role_set:
            cap_to_possible = True
            msg = "card appears to require narrow typal/support context"
            warnings.append(msg)
            quality_gate_parts.append(msg)
            downgrade_reasons["narrow_requirement"] += 1
        if generic_only and matched_categories:
            cap_to_possible = True
            quality_gate_parts.append("generic utility role only; not enough for Strong without deck-specific synergy")
            downgrade_reasons["generic_utility_only"] += 1
        if not strategy_specific_overlap and direct_hits <= 1 and matched_categories:
            cap_to_possible = True
            quality_gate_parts.append("matches a role need but lacks specific strategy overlap")
            downgrade_reasons["weak_strategy_overlap"] += 1

        # A semantic strong fit requires a direct need match and at least one
        # specific deck-plan reason. This prevents broadly useful cards from
        # being presented as clear upgrades merely because they are playable.
        strong_allowed_categories = [category for category in matched_categories if _strong_category_allowed(category, role_set)]
        if matched_categories and not strong_allowed_categories:
            cap_to_possible = True
            quality_gate_parts.append("category-specific semantic gate failed")
            downgrade_reasons["category_semantic_gate_failed"] += 1

        if matched_categories and direct_hits >= 1 and (strategy_specific_overlap or direct_specific_roles) and strong_allowed_categories:
            semantic_strong_fit = True

        promotion_allowed, promotion_reason = _strong_promotion_allowed(
            card,
            role_set,
            matched_categories,
            getattr(strategy_summary, "primary_strategy", ""),
            getattr(strategy_summary, "secondary_strategy", ""),
        )
        if semantic_strong_fit and not promotion_allowed:
            cap_to_possible = True
            quality_gate_parts.append(promotion_reason)
            downgrade_reasons["strong_promotion_gate"] += 1
        elif semantic_strong_fit and promotion_allowed:
            quality_gate_parts.append(promotion_reason)

        quality_gate = "; ".join(dict.fromkeys(quality_gate_parts))
        if not quality_gate:
            quality_gate = "direct need match plus semantic strategy relevance" if semantic_strong_fit else "legal/role-relevant but not a proven upgrade"

        source_files = _source_files_for_card(collection_summary, card_name)
        reason = _candidate_reason(matched_categories, roles, strategy_specific_overlap, quality_gate)
        if support_categories and not matched_categories:
            reason += f" Support-only category overlap: {', '.join(support_categories[:3])}."

        if matched_categories and direct_hits >= 1 and score >= 8:
            summary.strong_candidates_considered += 1

        if matched_categories and direct_hits >= 1 and score >= 8 and semantic_strong_fit and not warnings and not cap_to_possible and not cap_to_shakeup:
            strong_matched_categories = [category for category in matched_categories if _strong_category_allowed(category, role_set)]
            for category in strong_matched_categories:
                strong_category_hits[category] += 1
            summary.strong_candidates_accepted += 1
            candidate = _make_candidate(card_name, quantity, "Strong", "Owned card directly supports a current deck need and the deck's specific plan", strong_matched_categories, roles, reason, card, source_files, quality_gate=quality_gate)
            strong.append((score, candidate))
        elif matched_categories and score >= 3 and not cap_to_shakeup:
            summary.downgraded_to_possible += 1
            candidate = _make_candidate(card_name, quantity, "Possible", "Owned card may fit current deck needs; pilot review recommended", matched_categories, roles, reason, card, source_files, warnings, quality_gate=quality_gate)
            possible.append((score, candidate))
        else:
            if score >= 2 or mode == "shakeup":
                summary.downgraded_to_shakeup += 1
                candidate = _make_candidate(card_name, quantity, "Shakeup only", "Best available / experiment, not a confirmed upgrade", matched_categories, roles, reason, card, source_files, warnings, quality_gate=quality_gate)
                shakeup.append((score, candidate))

    strong.sort(key=lambda item: (-item[0], item[1].card_name.lower()))
    possible.sort(key=lambda item: (-item[0], item[1].card_name.lower()))
    shakeup.sort(key=lambda item: (-item[0], item[1].card_name.lower()))

    summary.strong_candidates = [candidate for _, candidate in strong[:5]]
    summary.possible_candidates = [candidate for _, candidate in possible[:16]]
    summary.shakeup_candidates = [candidate for _, candidate in shakeup[:12]]
    summary.rejected_candidates = rejected[:50]
    summary.no_strong_fit_categories = [category for category in priority_categories if strong_category_hits[category] == 0]

    if summary.strong_candidates:
        summary.notes.append("Strong owned candidates passed the stricter quality gate for at least one current deck need.")
    else:
        summary.notes.append("No strong owned candidates found. The current collection may not contain cards that clearly improve this deck under the detected strategy, selected philosophy, color identity, companion restrictions, and replacement needs.")
        if mode == "only":
            summary.notes.append("Collection-only mode is active, so the report should not pretend outside cards are available from this collection.")
        elif mode == "prefer":
            summary.notes.append("Collection-preferred mode can still use outside-card suggestions later if the user wants upgrades beyond this collection.")
    if summary.possible_candidates:
        summary.notes.append("Possible owned candidates need pilot review before being treated as upgrades.")
    if summary.shakeup_candidates:
        summary.notes.append("Shakeup candidates are not guaranteed upgrades; they are the best available experiments from the selected collection pool.")
    if downgrade_reasons:
        summary.downgrade_reason_counts = list(downgrade_reasons.most_common())
        top_reasons = ", ".join(f"{reason}={count}" for reason, count in downgrade_reasons.most_common(4))
        summary.quality_gate_notes.append(f"Downgraded broad/uncertain collection matches: {top_reasons}.")
    if priority_categories and not strong_category_hits:
        summary.quality_gate_notes.append("No current replacement category received a strong owned-card fit after quality gating.")

    return summary
