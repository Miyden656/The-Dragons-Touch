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

def _strong_fit_categories(categories: list[str], role_set: set[str]) -> list[str]:
    """Return categories this card can honestly close as a strong owned fit.

This is stricter than matched_needs. A card can be Possible for a category but
not close that category as solved by the selected collection.
"""
    strong: list[str] = []
    for category in categories:
        cat = category.lower()
        if "table-stabilizing" in cat or "targeted removal" in cat or "interaction" in cat or "answer" in cat:
            if role_set & {"targeted_removal", "board_wipe"}:
                strong.append(category)
            continue
        if "board protection" in cat:
            if role_set & {"board_protection_specific", "team_wide_combat_support"}:
                strong.append(category)
            continue
        if "protection" in cat:
            if role_set & {"board_protection_specific", "team_wide_combat_support"}:
                strong.append(category)
            continue
        if "evasion" in cat or "trample" in cat:
            if role_set & {"evasion_support", "team_wide_combat_support"}:
                strong.append(category)
            continue
        if "token" in cat:
            if "token_production" in role_set:
                strong.append(category)
            continue
        if "combat finisher" in cat or "finisher" in cat:
            if role_set & {"finisher_or_payoff", "team_wide_combat_support", "token_production"}:
                strong.append(category)
            continue
        if "combat payoff" in cat or "combat" in cat:
            if role_set & {"finisher_or_payoff", "team_wide_combat_support", "token_production"}:
                strong.append(category)
            continue
        if "board wipe" in cat:
            if "board_wipe" in role_set:
                strong.append(category)
            continue
        if _strong_category_allowed(category, role_set):
            strong.append(category)
    return strong

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

def _replacement_bias_matches(role_set: set[str], philosophy_context: dict[str, Any] | None) -> list[str]:
    """Return selected philosophy replacement-role buckets matched by this card.

    v0.6.6.6 locks these matches as a light presentation/order nudge only, exposes them to QA diagnostics, and relies on balanced-neutrality cleanup on the cut-bias side.
    It does not create Strong candidates without the existing direct need,
    semantic fit, quality gate, color identity, collection, and companion checks.
    """
    if not philosophy_context:
        return []
    bias_roles = list(philosophy_context.get("replacement_bias_roles", []) or [])
    matches: list[str] = []
    for bias_role in bias_roles:
        needed_roles = REPLACEMENT_BIAS_ROLE_TO_COLLECTION_ROLES.get(str(bias_role), set())
        if needed_roles and role_set & needed_roles:
            matches.append(str(bias_role))
    return list(dict.fromkeys(matches))

def _replacement_bias_note(philosophy_context: dict[str, Any] | None, matched_bias_roles: list[str]) -> str:
    if not matched_bias_roles or not philosophy_context:
        return ""
    label = str(philosophy_context.get("label", "selected philosophy"))
    return (
        f"Philosophy replacement fit: {label} slightly favors this candidate "
        f"because it matches replacement-bias role(s): {', '.join(matched_bias_roles[:4])}. "
        "This is a nudge only; normal collection fit, strategy fit, legality, and pilot intent still decide."
    )

def _replacement_bias_plain_explanation(philosophy_context: dict[str, Any] | None, matched_bias_roles: list[str]) -> str:
    if not matched_bias_roles or not philosophy_context:
        return ""
    label = str(philosophy_context.get("label", "selected philosophy"))
    roles = ", ".join(matched_bias_roles[:4])
    return f"This candidate matches the {label} replacement lens through: {roles}."

def _replacement_bias_still_not_automatic_text() -> str:
    return "Still not automatic because collection fit, strategy fit, quality gates, legality, companion rules, and pilot intent still decide the final recommendation."

def _v093_strict_strong_fit_needs(candidate: CollectionCandidate) -> list[str]:
    # v0.9.3 strict role gates for visible Strong owned candidates.
    roles = set(getattr(candidate, "role_tags", []) or [])
    filtered: list[str] = []

    for category in list(getattr(candidate, "strong_fit_needs", []) or getattr(candidate, "matched_needs", []) or []):
        cat = str(category).lower()

        if "dragon density" in cat:
            if roles & {"dragon_card", "dragon_token_production", "all_creature_types"}:
                filtered.append(category)
            continue

        if "dragon payoff" in cat:
            if roles & {"dragon_card", "dragon_typal_support", "dragon_token_production", "copy_token_payoff", "all_creature_types"}:
                filtered.append(category)
            continue

        if "copy-token payoff" in cat or "copy token payoff" in cat:
            if roles & {"copy_token_payoff", "dragon_token_production"}:
                filtered.append(category)
            continue

        if "commander protection" in cat:
            if roles & {"board_protection_specific", "commander_protection_specific"}:
                filtered.append(category)
            continue

        filtered.append(category)

    return list(dict.fromkeys(filtered))

def _v093_harden_visible_strong_candidates(
    strong: list[tuple[int, CollectionCandidate]],
    possible: list[tuple[int, CollectionCandidate]],
    summary: CollectionCandidateSummary,
    downgrade_reasons: Counter[str],
) -> list[tuple[int, CollectionCandidate]]:
    # Move overbroad Strong candidates to Possible before report visibility.
    hardened: list[tuple[int, CollectionCandidate]] = []

    for score, candidate in strong:
        original_strong_fits = list(getattr(candidate, "strong_fit_needs", []) or getattr(candidate, "matched_needs", []) or [])
        filtered = _v093_strict_strong_fit_needs(candidate)

        if filtered:
            candidate.strong_fit_needs = filtered
            candidate.matched_needs = [need for need in list(getattr(candidate, "matched_needs", []) or []) if need in filtered] or filtered
            hardened.append((score, candidate))
            continue

        candidate.confidence = "Possible"
        candidate.fit_type = "Owned card may fit current deck needs; pilot review recommended"
        candidate.strong_fit_needs = []
        candidate.matched_needs = original_strong_fits
        warning = "v0.9.3 strict category gate: broad role overlap was not enough for a visible Strong owned candidate."
        if warning not in candidate.warnings:
            candidate.warnings.append(warning)
        if candidate.quality_gate:
            if "v0.9.3 strict category gate" not in candidate.quality_gate:
                candidate.quality_gate += "; v0.9.3 strict category gate moved this from Strong to Possible"
        else:
            candidate.quality_gate = "v0.9.3 strict category gate moved this from Strong to Possible"
        possible.append((score, candidate))
        summary.downgraded_to_possible += 1
        downgrade_reasons["v0_9_3_strict_category_gate"] += 1

    return hardened
