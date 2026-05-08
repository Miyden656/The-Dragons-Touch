"""Collection candidate matching for The Dragon's Touch.

v0.6.4.3 scope:
- Match owned cards from the loaded collection to replacement/addition needs.
- Respect Commander color identity.
- Exclude cards already in the deck unless duplicates are legal later.
- Respect implemented companion filters, especially Keruga.
- Refuse to force bad recommendations when no owned card actually fits.
- Provide a separate "shakeup" bucket for interesting but not clearly improving cards.
"""

from __future__ import annotations

from collections import Counter
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

    @property
    def candidates(self) -> list[str]:
        """Backward-compatible string list used by older report code."""
        return [candidate.card_name for candidate in self.strong_candidates]


RAMP_PHRASES = [
    "add {", "add one mana", "add two mana", "search your library for a land", "put a land card",
    "additional land", "play an additional land", "treasure token", "mana of any color", "mana in any combination",
]
DRAW_PHRASES = [
    "draw a card", "draw cards", "look at the top", "impulse draw", "exile the top", "put it into your hand",
]
REMOVAL_PHRASES = [
    "destroy target", "exile target", "return target", "deals", "damage to target", "counter target",
    "tap target", "doesn't untap", "fight target", "target creature gets -", "target opponent sacrifices",
]
WIPE_PHRASES = [
    "destroy all", "exile all", "return all", "each creature", "all creatures", "each opponent sacrifices",
]
PROTECTION_PHRASES = [
    "hexproof", "indestructible", "protection from", "prevent all damage", "phase out", "can't be countered",
    "regenerate", "ward", "shield counter",
]
TOKEN_PHRASES = [
    "create a", "create x", "token", "tokens", "populate", "copy token",
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
COMBAT_PHRASES = [
    "trample", "haste", "double strike", "menace", "flying", "can't be blocked", "attacks", "combat damage",
]
COUNTER_PHRASES = ["+1/+1 counter", "proliferate", "counter on", "counters on"]
SACRIFICE_PHRASES = ["sacrifice", "dies", "whenever another creature dies", "death trigger"]


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
    if _contains_any(text, WIPE_PHRASES):
        roles.add("board_wipe")
    if _contains_any(text, PROTECTION_PHRASES):
        roles.add("protection")
    if _contains_any(text, TOKEN_PHRASES):
        roles.add("token_production")
    if _contains_any(text, RECURSION_PHRASES):
        roles.add("recursion")
    if _contains_any(text, GRAVEYARD_PHRASES):
        roles.add("graveyard_setup")
    if _contains_any(text, SPELL_PAYOFF_PHRASES):
        roles.add("spell_payoff")
    if _contains_any(text, COMBAT_PHRASES):
        roles.add("combat_support")
    if _contains_any(text, COUNTER_PHRASES):
        roles.add("counter_synergy")
    if _contains_any(text, SACRIFICE_PHRASES):
        roles.add("sacrifice_synergy")

    # Common typal/payoff words. This is intentionally broad but only used for
    # candidate matching, not strategy detection.
    if any(word in text for word in ["dragon", "vampire", "dinosaur", "artifact creature", "creature type"]):
        roles.add("typal_or_theme_support")
    if any(word in text for word in ["win the game", "double", "copy", "damage to each opponent", "creatures you control get"]):
        roles.add("finisher_or_payoff")

    return sorted(roles)


def _category_role_needs(category: str) -> set[str]:
    cat = category.lower()
    needs: set[str] = set()
    if "ramp" in cat or "mana" in cat:
        needs.update({"ramp", "mana_source", "land"})
    if "draw" in cat or "card advantage" in cat or "selection" in cat:
        needs.update({"card_draw", "card_advantage"})
    if "targeted removal" in cat or "interaction" in cat or "answer" in cat:
        needs.update({"targeted_removal"})
    if "board wipe" in cat or "table-stabilizing" in cat:
        needs.update({"board_wipe", "targeted_removal"})
    if "protection" in cat:
        needs.update({"protection"})
    if "token" in cat:
        needs.update({"token_production"})
    if "combat" in cat or "evasion" in cat or "trample" in cat or "finisher" in cat:
        needs.update({"combat_support", "finisher_or_payoff", "token_production"})
    if "typal" in cat or "tribal" in cat or "dragon" in cat or "on-type" in cat:
        needs.update({"typal_or_theme_support", "creature", "finisher_or_payoff"})
    if "graveyard" in cat:
        needs.update({"graveyard_setup", "recursion"})
    if "recursion" in cat:
        needs.update({"recursion"})
    if "spell" in cat or "instant" in cat or "sorcery" in cat:
        needs.update({"spell_payoff", "instant", "sorcery", "card_draw"})
    if "mutate" in cat:
        needs.update({"creature", "protection"})
    if "sacrifice" in cat or "death" in cat:
        needs.update({"sacrifice_synergy", "token_production", "recursion"})
    if "counter" in cat:
        needs.update({"counter_synergy", "combat_support"})
    return needs


def _strategy_bonus_roles(primary: str, secondary: str) -> set[str]:
    joined = f"{primary} {secondary}".lower()
    roles: set[str] = set()
    if any(token in joined for token in ["token", "go-wide", "go-tall"]):
        roles.update({"token_production", "combat_support", "finisher_or_payoff", "protection"})
    if "combat" in joined or "voltron" in joined or "stompy" in joined:
        roles.update({"combat_support", "finisher_or_payoff", "protection"})
    if "landfall" in joined or "lands" in joined:
        roles.update({"ramp", "land", "mana_source", "token_production"})
    if "typal" in joined or "tribal" in joined or "dragon" in joined:
        roles.update({"typal_or_theme_support", "creature", "finisher_or_payoff"})
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


def _candidate_reason(matched_needs: list[str], roles: list[str], strategy_bonus: bool) -> str:
    if matched_needs:
        base = f"Matches collection role need(s): {', '.join(matched_needs[:4])}."
    else:
        base = "Does not directly match a current replacement category, but has generally relevant deck-building utility."
    if strategy_bonus:
        base += " Also overlaps with the current primary/secondary strategy shape."
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
    )


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
    category_hits: Counter[str] = Counter()

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
        score = 0
        for category, needed_roles in category_needs.items():
            overlap = role_set & needed_roles
            if overlap:
                matched_categories.append(category)
                category_hits[category] += 1
                score += 3 if len(overlap) >= 2 else 2

        strategy_overlap = bool(role_set & strategy_roles)
        if strategy_overlap:
            score += 1

        # General utility cards can be possible/shakeup candidates but should not
        # be called upgrades unless they match a real need.
        if "targeted_removal" in role_set or "card_draw" in role_set or "ramp" in role_set or "protection" in role_set:
            score += 1

        reason = _candidate_reason(matched_categories, roles, strategy_overlap)
        source_files = _source_files_for_card(collection_summary, card_name)

        if matched_categories and score >= 5 and not companion_warnings:
            candidate = _make_candidate(card_name, quantity, "Strong", "Owned card matches current deck needs", matched_categories, roles, reason, card, source_files)
            strong.append((score, candidate))
        elif matched_categories and score >= 3:
            candidate = _make_candidate(card_name, quantity, "Possible", "Owned card may fit current deck needs", matched_categories, roles, reason, card, source_files, companion_warnings)
            possible.append((score, candidate))
        else:
            # Shakeup cards are intentionally not called upgrades.
            if score >= 2 or mode == "shakeup":
                candidate = _make_candidate(card_name, quantity, "Shakeup only", "Best available / experiment, not a confirmed upgrade", matched_categories, roles, reason, card, source_files, companion_warnings)
                shakeup.append((score, candidate))

    strong.sort(key=lambda item: (-item[0], item[1].card_name.lower()))
    possible.sort(key=lambda item: (-item[0], item[1].card_name.lower()))
    shakeup.sort(key=lambda item: (-item[0], item[1].card_name.lower()))

    summary.strong_candidates = [candidate for _, candidate in strong[:12]]
    summary.possible_candidates = [candidate for _, candidate in possible[:16]]
    summary.shakeup_candidates = [candidate for _, candidate in shakeup[:12]]
    summary.rejected_candidates = rejected[:40]
    summary.no_strong_fit_categories = [category for category in priority_categories if category_hits[category] == 0]

    if summary.strong_candidates:
        summary.notes.append("Strong owned candidates were found for at least one current deck need.")
    else:
        summary.notes.append("No strong owned candidates found. The current collection may not contain cards that clearly improve this deck under the detected strategy, selected philosophy, color identity, companion restrictions, and replacement needs.")
        if mode == "only":
            summary.notes.append("Collection-only mode is active, so the report should not pretend outside cards are available from this collection.")
        elif mode == "prefer":
            summary.notes.append("Collection-preferred mode can still use outside-card suggestions later if the user wants upgrades beyond this collection.")
    if summary.shakeup_candidates:
        summary.notes.append("Shakeup candidates are not guaranteed upgrades; they are the best available experiments from the selected collection pool.")

    return summary
