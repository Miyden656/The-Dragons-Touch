"""Companion rule helpers for The Dragon's Touch.

Patch Batch 7.2 scope:
- Detect official companion cards in companion/reference zones.
- Provide companion-intake wording for every official companion.
- Validate implemented companion restrictions when a companion is actually detected.
- Provide replacement-filter notes for reports/prompts.

Only Keruga's restriction is fully automated in this patch. All other official
companions have summaries and manual-review guidance so the report never implies
that an unsupported companion rule has been fully enforced.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, NamedTuple

from data.card_lookup import (
    get_full_oracle_text,
    get_representative_nonland_mana_value,
    has_type_on_any_face,
    normalize_text,
)


class CompanionProfile(NamedTuple):
    name: str
    restriction_summary: str
    recommendation_filter_summary: str
    implemented: bool = False
    manual_review_required: bool = True
    banned_as_companion: bool = False
    banned_as_companion_note: str = ""


COMPANION_PROFILES: dict[str, CompanionProfile] = {
    "gyruda, doom of depths": CompanionProfile(
        name="Gyruda, Doom of Depths",
        restriction_summary="Each nonland card in the starting deck must have an even mana value.",
        recommendation_filter_summary="Do not recommend nonland cards with odd mana values unless the pilot removes the Gyruda companion requirement.",
    ),
    "jegantha, the wellspring": CompanionProfile(
        name="Jegantha, the Wellspring",
        restriction_summary="No card in the starting deck may have more than one of the same mana symbol in its mana cost.",
        recommendation_filter_summary="Do not recommend cards with repeated mana symbols in their mana costs unless the pilot removes the Jegantha companion requirement.",
    ),
    "kaheera, the orphanguard": CompanionProfile(
        name="Kaheera, the Orphanguard",
        restriction_summary="Each creature card in the starting deck must be a Cat, Elemental, Nightmare, Dinosaur, or Beast.",
        recommendation_filter_summary="Do not recommend creature cards outside Kaheera's allowed creature types unless the pilot removes the Kaheera companion requirement.",
    ),
    "keruga, the macrosage": CompanionProfile(
        name="Keruga, the Macrosage",
        restriction_summary="Each nonland card in the starting deck must have mana value 3 or greater.",
        recommendation_filter_summary="Do not recommend nonland cards with mana value 0, 1, or 2 unless the pilot removes the Keruga companion requirement.",
        implemented=True,
        manual_review_required=False,
    ),
    "lurrus of the dream-den": CompanionProfile(
        name="Lurrus of the Dream-Den",
        restriction_summary="Each permanent card in the starting deck must have mana value 2 or less.",
        recommendation_filter_summary="Do not recommend permanent cards with mana value 3 or greater unless the pilot removes the Lurrus companion requirement.",
    ),
    "lutri, the spellchaser": CompanionProfile(
        name="Lutri, the Spellchaser",
        restriction_summary="Each nonland card in the starting deck must have a different name.",
        recommendation_filter_summary="Do not recommend duplicate nonland names unless the pilot removes the Lutri companion requirement.",
        banned_as_companion=True,
        banned_as_companion_note="Lutri is not legal as a companion/card in normal Commander under official Commander legality; treat any Lutri companion use as a house-rule/manual-review exception.",
    ),
    "obosh, the preypiercer": CompanionProfile(
        name="Obosh, the Preypiercer",
        restriction_summary="Each nonland card in the starting deck must have an odd mana value.",
        recommendation_filter_summary="Do not recommend nonland cards with even mana values unless the pilot removes the Obosh companion requirement.",
    ),
    "umori, the collector": CompanionProfile(
        name="Umori, the Collector",
        restriction_summary="Each nonland card in the starting deck must share a card type chosen for Umori.",
        recommendation_filter_summary="Do not recommend nonland cards that fail to share the chosen Umori card type unless the pilot removes the Umori companion requirement.",
    ),
    "yorion, sky nomad": CompanionProfile(
        name="Yorion, Sky Nomad",
        restriction_summary="The starting deck must contain at least twenty cards more than the minimum deck size.",
        recommendation_filter_summary="Yorion companion status is normally incompatible with a fixed 100-card Commander deck; manual/house-rule review is required before recommending around it.",
        banned_as_companion=True,
        banned_as_companion_note="Yorion's companion condition does not normally fit Commander deck-size rules. Treat Yorion companion use as manual/house-rule review unless the pilot states otherwise.",
    ),
    "zirda, the dawnwaker": CompanionProfile(
        name="Zirda, the Dawnwaker",
        restriction_summary="Each permanent card in the starting deck must have an activated ability.",
        recommendation_filter_summary="Do not recommend permanent cards without activated abilities unless the pilot removes the Zirda companion requirement.",
    ),
}


OFFICIAL_COMPANION_CARD_NAMES: set[str] = {profile.name for profile in COMPANION_PROFILES.values()}

# Backward-compatible public name used by report/debug helpers.
COMPANION_CARD_NAMES: set[str] = OFFICIAL_COMPANION_CARD_NAMES

IMPLEMENTED_COMPANION_RULES: set[str] = {
    key for key, profile in COMPANION_PROFILES.items() if profile.implemented
}


def get_companion_profile(companion_name: str) -> CompanionProfile | None:
    return COMPANION_PROFILES.get(str(companion_name).strip().lower())


def is_companion_card_name(name: object) -> bool:
    return str(name).strip().lower() in COMPANION_PROFILES


def companion_is_banned_as_companion(companion_name: str) -> bool:
    profile = get_companion_profile(companion_name)
    return bool(profile and profile.banned_as_companion)


def get_companion_banned_note(companion_name: str) -> str:
    profile = get_companion_profile(companion_name)
    if not profile or not profile.banned_as_companion:
        return ""
    return profile.banned_as_companion_note or f"{profile.name} requires manual companion legality review."


def card_has_companion_text(card: dict[str, Any] | None) -> bool:
    if not card:
        return False
    return "companion" in normalize_text(get_full_oracle_text(card))


def find_companion_names(
    card_names: Iterable[str],
    scryfall_lookup: dict[str, dict[str, Any]] | None = None,
) -> list[str]:
    """Return official or Scryfall-detected companion names from a list of names."""
    scryfall_lookup = scryfall_lookup or {}
    found: list[str] = []
    seen: set[str] = set()

    for raw_name in card_names:
        name = str(raw_name).strip()
        if not name:
            continue
        card = scryfall_lookup.get(name.lower())
        profile = get_companion_profile(name)
        is_companion = bool(profile) or card_has_companion_text(card)
        display_name = profile.name if profile else name
        if is_companion and display_name.lower() not in seen:
            found.append(display_name)
            seen.add(display_name.lower())
    return found


def companion_rule_is_implemented(companion_name: str) -> bool:
    profile = get_companion_profile(companion_name)
    return bool(profile and profile.implemented)


def get_companion_restriction_summary(companion_name: str) -> str:
    profile = get_companion_profile(companion_name)
    if profile:
        return f"{profile.name} restriction: {profile.restriction_summary}"
    return "Companion restriction exists, but this specific companion rule is not fully implemented yet; use manual review."


def get_companion_replacement_filter_note(companion_name: str) -> str:
    profile = get_companion_profile(companion_name)
    if profile:
        return f"{profile.name} recommendation filter: {profile.recommendation_filter_summary}"
    return "Replacement filter: only recommend cards that preserve the confirmed companion restriction; manual review required for this companion."


def get_companion_intake_lines(companion_name: str) -> list[str]:
    """Return report/prompt bullets for a possible or confirmed companion."""
    profile = get_companion_profile(companion_name)
    display = profile.name if profile else str(companion_name).strip()
    lines = [
        f"If {display} is confirmed as companion, apply:",
        f"- {display} legality validation",
        f"- {display} cut protection",
        f"- {display} replacement filter",
        f"- {get_companion_restriction_summary(display)}",
        f"- {get_companion_replacement_filter_note(display)}",
    ]
    if profile and not profile.implemented:
        lines.append("- Manual companion restriction review is required because this companion is not fully automated yet.")
    if profile and profile.banned_as_companion:
        lines.append(f"- Companion legality warning: {profile.banned_as_companion_note}")
    return lines


def _is_land_card(card: dict[str, Any]) -> bool:
    return has_type_on_any_face(card, "Land")


def check_card_against_companion(
    companion_name: str,
    card_name: str,
    card: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Return (violation, manual_review) for one card under one companion rule."""
    profile = get_companion_profile(companion_name)
    display = profile.name if profile else companion_name
    key = display.strip().lower()

    if profile and profile.banned_as_companion:
        return None, {
            "companion_name": display,
            "card_name": card_name,
            "reason": f"{display} needs companion legality review: {profile.banned_as_companion_note}",
        }

    if not card:
        return None, {
            "companion_name": display,
            "card_name": card_name,
            "reason": "Card was not found in Scryfall, so companion legality needs manual review.",
        }

    if key != "keruga, the macrosage":
        return None, {
            "companion_name": display,
            "card_name": card_name,
            "reason": "This companion restriction is not automated yet; manual companion-legality review required.",
        }

    if _is_land_card(card):
        return None, None

    mana_value = get_representative_nonland_mana_value(card)
    if mana_value is None:
        return None, {
            "companion_name": display,
            "card_name": card_name,
            "reason": "Could not determine nonland mana value for Keruga companion check.",
        }

    if mana_value < 3:
        return {
            "companion_name": display,
            "card_name": card_name,
            "mana_value": mana_value,
            "reason": "Keruga allows only lands and nonland cards with mana value 3 or greater in the starting deck.",
        }, None

    return None, None
