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
    if _contains_any(text, TUTOR_PHRASES):
        roles.add("tutor")
    if _contains_any(text, CARD_SELECTION_PHRASES):
        roles.add("card_selection")
    if _contains_any(text, COUNTERSPELL_PHRASES):
        roles.add("counterspell")
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
    # v0.9.3: Dragon-specific replacement needs require Dragon-specific evidence.
    # Generic creatures, generic token makers, and broad typal support should not
    # satisfy "More Dragon density" or "More Dragon payoff" by themselves.
    if has_type_on_any_face(card, "Dragon"):
        roles.add("dragon_card")
    if "changeling" in text or "is every creature type" in text or "are every creature type" in text:
        roles.add("all_creature_types")
    if "dragon token" in text or "dragon tokens" in text:
        roles.update({"dragon_token_production", "token_production", "typal_or_theme_support"})
    if (
        "dragon you control" in text
        or "dragons you control" in text
        or "dragon spells you cast" in text
        or "whenever a dragon" in text
        or "dragon card" in text
        or "dragon cards" in text
    ):
        roles.update({"dragon_typal_support", "typal_or_theme_support"})
    if (
        "token that's a copy" in text
        or "tokens that are copies" in text
        or "copy of target creature" in text
        or "copy target creature" in text
        or "copy target permanent" in text
        or "create a token that's a copy" in text
    ):
        roles.update({"copy_token_payoff", "token_production"})
    if _contains_any(text, ARTIFACT_CONTEXT_PHRASES):
        roles.add("artifact_context_dependent")

    # Common typal/payoff words. This is intentionally broad but never enough by
    # itself to make a card a strong collection recommendation.
    if any(word in text for word in ["dragon", "vampire", "dinosaur", "artifact creature", "creature type"]):
        roles.add("typal_or_theme_support")
    if any(word in text for word in ["copy", "double", "damage to each opponent", "win the game"]):
        roles.add("finisher_or_payoff")

    return sorted(roles)
