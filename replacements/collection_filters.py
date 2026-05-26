"""Collection candidate matching for The Dragon's Touch.

v0.6.6.6 lock scope:
- Integrate Collection Pull quality into report/prompt guidance.
- Keep owned-card recommendations honest: candidates are review candidates, not automatic swaps.
- Track collection gaps per replacement category using stricter strong-fit evidence.
- Cap artifact-context-dependent cards at Possible unless the deck actually supports artifact context.
- Add early swap-guidance labels for owned candidates without forcing exact one-for-one swaps.
- Apply a light philosophy-aware replacement bias to candidate presentation and ordering.
- Add replacement-bias visibility counters and examples for QA.
- Add role-alias cleanup so non-Commander-Exploiter lenses can match real role tags.
- Keep collection-only honesty: philosophy can nudge candidates, but cannot force bad recommendations.
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

def _card_color_identity(card: dict[str, Any]) -> list[str]:
    return list(card.get("color_identity", []) or [])

def _is_color_legal(card: dict[str, Any], commander_colors: set[str]) -> bool:
    return set(_card_color_identity(card)).issubset(commander_colors)

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

def _is_artifact_context_dependent(card: dict[str, Any], role_set: set[str]) -> bool:
    if "artifact_context_dependent" in role_set:
        return True
    if not has_type_on_any_face(card, "Artifact"):
        return False
    text = _card_text(card)
    return _contains_any(text, ARTIFACT_CONTEXT_PHRASES)

def _deck_has_artifact_context(primary_strategy: str, secondary_strategy: str, strategy_roles: set[str]) -> bool:
    joined = f"{primary_strategy} {secondary_strategy}".lower()
    return any(token in joined for token in ["artifact", "vehicle", "equipment"]) or "artifact" in strategy_roles or "artifact_token_synergy" in strategy_roles

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
