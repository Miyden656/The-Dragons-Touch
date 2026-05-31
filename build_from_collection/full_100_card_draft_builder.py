"""Full 100-Card Draft Builder (Bin B Phase 4 v1.5.37).

Given a selected commander + the user's owned collection + a BuildPreferenceDataShape,
generate a complete 100-card decklist that:
- Has exactly 1 commander (the selected one)
- Has cards strictly within the commander's color identity
- Has a reasonable land base (~37 lands)
- Is heavy on cards relevant to the chosen primary/secondary strategy
- Pulls every nonland card from the user's owned collection
- Is copy-pasteable into Archidekt / Moxfield / etc.

Boundaries:
- This DOES generate an actual decklist (unlike Owned Cards by Role / Rough Shell
  which were guidance-only).
- It does NOT validate combo legality, bracket compliance, or playgroup fit.
- It does NOT do deep card synergy reasoning — heuristic role bucketing only.
- Pilot judgement is still the final authority; treat the output as a draft.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


# Target distribution for a 100-card Commander deck (commander + 99 others).
# These are approximate role targets; the generator falls back to flex slots
# when a role can't be filled from the available pool.
TARGET_COUNTS: dict[str, int] = {
    "Commander": 1,
    "Lands": 37,
    "Ramp": 10,
    "Card Draw": 10,
    "Removal": 7,
    "Protection": 3,
    "Strategy": 25,
    "Flex": 7,
}


# Role-bucket display order in the output report.
ROLE_BUCKET_ORDER: tuple[str, ...] = (
    "Commander",
    "Lands",
    "Ramp",
    "Card Draw",
    "Removal",
    "Protection",
    "Strategy",
    "Flex",
)


# Map each role bucket to the role tags from analysis/role_tags.py that fill it.
ROLE_BUCKET_TAGS: dict[str, set[str]] = {
    "Ramp": {"ramp", "mana_rock", "mana_dork", "extra_land_play", "mana_doubler", "mana_source"},
    "Card Draw": {"card_draw", "card_advantage", "card_selection"},
    "Removal": {"targeted_removal", "board_wipe", "counterspell"},
    "Protection": {"protection"},
}


# Mana-symbol basic land mapping.
COLOR_TO_BASIC_LAND: dict[str, str] = {
    "W": "Plains",
    "U": "Island",
    "B": "Swamp",
    "R": "Mountain",
    "G": "Forest",
    "C": "Wastes",
}


@dataclass
class DraftedCardEntry:
    """One card chosen for the generated 100-card deck."""

    card_name: str
    quantity: int = 1
    role_bucket: str = "Flex"
    source_files: list[str] = field(default_factory=list)
    is_basic_land: bool = False
    is_commander: bool = False
    mana_value: float = 0.0
    type_line: str = ""
    # Short reason tags describing WHY this card was picked. Drawn from the
    # six-signal scoring chain: strategy fit (card tags overlap chosen
    # strategy's tag set), commander amplifier (card tags overlap the
    # commander's derived amplifier tags), combo piece (card name appears in
    # a combo this commander+collection can reach), persona pick (philosophy
    # bias score modifier was meaningfully positive). Empty for basic lands
    # and the commander itself.
    why_tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "card_name": self.card_name,
            "quantity": self.quantity,
            "role_bucket": self.role_bucket,
            "source_files": list(self.source_files),
            "is_basic_land": self.is_basic_land,
            "is_commander": self.is_commander,
            "mana_value": self.mana_value,
            "type_line": self.type_line,
            "why_tags": list(self.why_tags),
        }


@dataclass
class Full100CardDraftResult:
    """Output of the deck builder."""

    commander_name: str
    color_identity: list[str]
    primary_strategy: str
    secondary_strategy: str
    entries: list[DraftedCardEntry] = field(default_factory=list)
    role_counts: dict[str, int] = field(default_factory=dict)
    missing_slots: dict[str, int] = field(default_factory=dict)
    total_cards: int = 0
    notes: list[str] = field(default_factory=list)
    # v1.6.1 Phase 1: legality / matching diagnostics surfaced in the report
    # so the user can see exactly what the pre-build gates filtered out.
    # These are owned-collection card counts, not unique-name counts.
    collection_cards_analyzed: int = 0
    scryfall_unmatched_count: int = 0
    color_identity_excluded_count: int = 0
    legality_banned_excluded_count: int = 0
    legality_not_legal_excluded_count: int = 0
    legality_restricted_excluded_count: int = 0
    bracket_excluded_count: int = 0
    allow_banned_cards: bool = False
    commander_is_banned: bool = False
    # v1.6.1 Phase 3: creature-density diagnostics so the user can see at a
    # glance whether the deck is creature-heavy / -light / balanced for the
    # chosen strategy. Defaults are wide so legacy callers see "no signal".
    creature_count: int = 0
    noncreature_nonland_count: int = 0
    creature_band_category: str = ""
    creature_band_floor: int = 0
    creature_band_target: int = 0
    creature_band_ceiling: int = 0
    creatures_skipped_for_ceiling: int = 0
    creatures_added_past_ceiling: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "commander_name": self.commander_name,
            "color_identity": list(self.color_identity),
            "primary_strategy": self.primary_strategy,
            "secondary_strategy": self.secondary_strategy,
            "entries": [e.to_dict() for e in self.entries],
            "role_counts": dict(self.role_counts),
            "missing_slots": dict(self.missing_slots),
            "total_cards": self.total_cards,
            "notes": list(self.notes),
            "collection_cards_analyzed": self.collection_cards_analyzed,
            "scryfall_unmatched_count": self.scryfall_unmatched_count,
            "color_identity_excluded_count": self.color_identity_excluded_count,
            "legality_banned_excluded_count": self.legality_banned_excluded_count,
            "legality_not_legal_excluded_count": self.legality_not_legal_excluded_count,
            "legality_restricted_excluded_count": self.legality_restricted_excluded_count,
            "bracket_excluded_count": self.bracket_excluded_count,
            "allow_banned_cards": self.allow_banned_cards,
            "commander_is_banned": self.commander_is_banned,
            "creature_count": self.creature_count,
            "noncreature_nonland_count": self.noncreature_nonland_count,
            "creature_band_category": self.creature_band_category,
            "creature_band_floor": self.creature_band_floor,
            "creature_band_target": self.creature_band_target,
            "creature_band_ceiling": self.creature_band_ceiling,
            "creatures_skipped_for_ceiling": self.creatures_skipped_for_ceiling,
            "creatures_added_past_ceiling": self.creatures_added_past_ceiling,
        }


def _card_color_identity(card: dict[str, Any]) -> set[str]:
    raw = card.get("color_identity") or []
    return {str(c).upper() for c in raw if c}


def _card_is_land(card: dict[str, Any]) -> bool:
    type_line = str(card.get("type_line") or "").lower()
    return "land" in type_line


def _strategy_role_tags(strategy_name: str) -> set[str]:
    """Pull role tags for the named strategy.

    v1.5.38 (Task #39): tries the Strategy Knowledge 249-profile catalog first
    (which uses 'role_tags'), then falls back to the legacy ARCHETYPE_DEFINITIONS
    (which uses anchors / payoffs / enablers). Selector values may come in with
    a "[Layer] " prefix from the Build Setup Panel — the catalog strips it.
    """
    if not strategy_name or strategy_name in ("Not selected yet", "None", ""):
        return set()
    # Try the 249-profile catalog first.
    try:
        from strategy_knowledge.strategy_selector_catalog import role_tags_for_display_name
        tags = role_tags_for_display_name(strategy_name)
        if tags:
            return tags
    except Exception:
        pass
    # Fallback path: ARCHETYPE_DEFINITIONS (22 macro archetypes).
    try:
        from analysis.strategy_scoring import ARCHETYPE_DEFINITIONS
    except Exception:
        return set()
    # Strip any "[Layer] " prefix the user picked from the new selector.
    bare = strategy_name
    if bare.startswith("[") and "]" in bare:
        bare = bare.split("]", 1)[1].strip()
    arch = ARCHETYPE_DEFINITIONS.get(bare, {}) or {}
    tags = set()
    for key in ("anchors", "payoffs", "enablers"):
        for tag in (arch.get(key) or set()):
            tags.add(str(tag))
    return tags


def _classify_role_bucket(card_tags: set[str], strategy_tags: set[str]) -> str:
    """Return the highest-priority role bucket this card fills."""
    if strategy_tags and (card_tags & strategy_tags):
        return "Strategy"
    for bucket in ("Ramp", "Card Draw", "Removal", "Protection"):
        if card_tags & ROLE_BUCKET_TAGS[bucket]:
            return bucket
    return "Flex"


def _score_card(card_tags: set[str], strategy_tags: set[str], mana_value: float) -> float:
    """Heuristic score for picking within a role bucket."""
    score = 0.0
    score += 3.0 * len(card_tags & strategy_tags)
    score += 0.5 * len(card_tags)
    # Slight curve bias: prefer cards <= 5 CMC (not too top-heavy).
    if mana_value and mana_value <= 5:
        score += 0.5
    if mana_value and mana_value >= 7:
        score -= 0.5
    return score


def build_full_100_card_draft(
    *,
    commander_candidate: dict[str, Any],
    owned_cards: list[dict[str, Any]],
    scryfall_lookup: dict[str, dict[str, Any]],
    primary_strategy: str = "",
    secondary_strategy: str = "",
    bracket_preference: str = "",
    sub_philosophy: str = "",
    allow_banned_cards: bool = False,
) -> Full100CardDraftResult:
    """Generate a 100-card Commander decklist from the user's owned collection.

    owned_cards is a list of dicts with at minimum: name, owned_quantity, oracle_text,
    type_line, source_files. (Same shape produced by the Owned Cards by Role loader.)

    allow_banned_cards (v1.6.1) is the explicit, off-by-default escape hatch for
    Rule Zero / house-rules tables. When False (the default), any card Scryfall
    marks as banned in Commander is dropped before bracket filtering. When True,
    banned cards are allowed through and the report says CUSTOM MODE. Cards
    marked `not_legal` in Commander (un-cards / conspiracies / etc.) are ALWAYS
    dropped, even in custom mode.
    """
    commander_name = (
        commander_candidate.get("commander_name")
        or commander_candidate.get("card_name")
        or "Selected commander"
    )
    # v1.6.1 Phase 4: build a name-resolution index ONCE per build call so
    # we can resolve the commander and per-owned-card names through the same
    # smart resolver the collection loader uses (exact → normalized → face /
    # printed / flavor alt). Falls back to the raw lookup if the module
    # isn't importable.
    try:
        from data.card_resolution import (
            build_card_resolution_indexes,
            resolve_card_simple,
        )
        _resolution_indexes = build_card_resolution_indexes(scryfall_lookup)
        _resolve = lambda nm: resolve_card_simple(nm, scryfall_lookup, _resolution_indexes)
    except Exception:
        _resolution_indexes = None
        _resolve = lambda nm: scryfall_lookup.get((nm or "").lower())

    commander_scry = _resolve(commander_name) or {}
    # v1.6.1 Phase 1: detect a banned commander up front. Phase 2 will block
    # banned commanders at the discovery layer; for now we flag the build so
    # the report can shout about it instead of silently producing an illegal
    # deck.
    try:
        from legality.build_legality_gate import is_card_banned_in_commander as _is_banned_cmdr
        commander_is_banned = bool(commander_scry) and _is_banned_cmdr(commander_scry)
    except Exception:
        commander_is_banned = False
    commander_identity = _card_color_identity(commander_scry)
    # Fall back to the candidate's stored identity_key (string like "URG") if Scryfall lookup empty.
    if not commander_identity:
        key = str(commander_candidate.get("color_identity_key") or "").upper()
        commander_identity = {c for c in key if c in "WUBRG"}

    # Identity used for lane filtering — colorless commanders ({}) accept colorless cards.
    identity_set = commander_identity if commander_identity else set()

    strategy_tags = _strategy_role_tags(primary_strategy)
    secondary_tags = _strategy_role_tags(secondary_strategy)
    combined_strategy_tags = strategy_tags | secondary_tags

    # v1.5.41 Item 3: Commander-text scoring. Read the commander's oracle text
    # and derive amplifier role tags — card categories that multiply this
    # commander's specific ability. Cards with those tags get an extra score
    # boost during pool building so the picked deck feels commander-specific.
    try:
        from build_from_collection.commander_text_scorer import commander_amplifier_tags
        commander_amp_tags = commander_amplifier_tags(commander_scry)
    except Exception:
        commander_amp_tags = set()

    # v1.5.42 Item 4: Philosophy / persona bias. Different sub-philosophies
    # (Battlecruiser vs Engine Builder vs Efficiency Optimizer etc.) get
    # different tag-score modifiers so the same commander+collection produces
    # meaningfully different decks per persona choice.
    try:
        from build_from_collection.philosophy_bias import philosophy_score_modifier
    except Exception:
        philosophy_score_modifier = None  # type: ignore[assignment]

    # v1.5.43 Item 5: Combo-aware scoring. Detect combos this commander +
    # collection can reach and bias scoring toward (or away from) cards in
    # those combo lines based on the user's chosen persona.
    try:
        from build_from_collection.combo_scorer import (
            relevant_combos_for_build,
            build_combo_name_lookup,
            combo_persona_orientation,
            combo_score_modifier,
            combo_awareness_summary,
        )
    except Exception:
        relevant_combos_for_build = None  # type: ignore[assignment]
        build_combo_name_lookup = None  # type: ignore[assignment]
        combo_persona_orientation = None  # type: ignore[assignment]
        combo_score_modifier = None  # type: ignore[assignment]
        combo_awareness_summary = None  # type: ignore[assignment]

    try:
        from analysis.role_tags import infer_card_role_tags
    except Exception:
        infer_card_role_tags = None  # type: ignore[assignment]

    # v1.6.2 Phase C: Tribal fidelity boost. When the commander is a typal
    # legendary creature (Dragon, Dinosaur, Rabbit, etc.), on-tribe creatures
    # in the collection get an explicit score boost so the Strategy bucket
    # doesn't fill with random off-tribe creatures whose scores happen to be
    # high (the Ghalta 2-dinosaur-of-29 problem).
    try:
        from build_from_collection.tribal_fidelity import (
            extract_commander_tribes,
            extract_card_tribes,
            tribal_fidelity_boost,
            describe_tribal_match,
        )
        commander_tribes = extract_commander_tribes(commander_scry)
    except Exception:
        extract_commander_tribes = None  # type: ignore[assignment]
        extract_card_tribes = None  # type: ignore[assignment]
        tribal_fidelity_boost = None  # type: ignore[assignment]
        describe_tribal_match = None  # type: ignore[assignment]
        commander_tribes = set()

    # v1.6.1 Phase 3: Strategy-aware creature density band. Caps the deck's
    # total creature count at fill-time so even a creature-heavy collection
    # doesn't over-tilt the build. Falls back to a wide default band when the
    # module is unavailable so the builder still works.
    try:
        from build_from_collection.creature_skeleton import (
            classify_creature_band,
            is_creature_type_line,
            creature_band_status_label,
            BAND_DEFAULT,
        )
        creature_band = classify_creature_band(
            strategy_tags=combined_strategy_tags,
            primary_strategy_label=primary_strategy,
            secondary_strategy_label=secondary_strategy,
        )
    except Exception:
        classify_creature_band = None  # type: ignore[assignment]
        is_creature_type_line = lambda tl: "Creature" in (tl or "")  # type: ignore[assignment]
        creature_band_status_label = None  # type: ignore[assignment]
        BAND_DEFAULT = None  # type: ignore[assignment]
        creature_band = None

    # v1.5.40: Bracket-aware filtering. Cards that fail the bracket filter
    # never enter the pool (hard exclude); cards that pass get a soft score
    # modifier so high-bracket preferences are reflected in selection order.
    try:
        from build_from_collection.bracket_filter import (
            is_card_allowed_in_bracket,
            score_modifier_for_bracket,
            bracket_to_int,
        )
    except Exception:
        is_card_allowed_in_bracket = None  # type: ignore[assignment]
        score_modifier_for_bracket = None  # type: ignore[assignment]
        bracket_to_int = None  # type: ignore[assignment]

    # v1.6.1 Phase 1: Commander legality gate. Excludes cards Scryfall marks
    # as banned or not_legal in Commander BEFORE the bracket filter sees them.
    # This is the single source of truth for "is this card playable in 99".
    # Without this gate, a banned card in the user's collection would land in
    # the deck whenever color identity allowed it.
    try:
        from legality.build_legality_gate import (
            should_exclude_from_commander_build,
            commander_legality_gate_summary,
            EXCLUDE_REASON_BANNED,
            EXCLUDE_REASON_NOT_LEGAL,
            EXCLUDE_REASON_RESTRICTED,
        )
    except Exception:
        should_exclude_from_commander_build = None  # type: ignore[assignment]
        commander_legality_gate_summary = None  # type: ignore[assignment]
        EXCLUDE_REASON_BANNED = "banned"
        EXCLUDE_REASON_NOT_LEGAL = "not_legal"
        EXCLUDE_REASON_RESTRICTED = "restricted"

    # v1.5.43 Item 5: Pre-compute combos reachable from this commander +
    # collection. Done ONCE before the pool loop so each card's lookup is O(1).
    # "Reachable" = combo identity fits commander AND >=2 pieces are in the
    # owned collection. Neutral personas skip this work entirely.
    combo_orientation = "neutral"
    combo_name_lookup: dict[str, list[Any]] = {}
    reachable_combos: list[Any] = []
    if (
        relevant_combos_for_build is not None
        and combo_persona_orientation is not None
        and build_combo_name_lookup is not None
    ):
        combo_orientation = combo_persona_orientation(sub_philosophy)
        if combo_orientation != "neutral":
            try:
                owned_names_for_combo = [
                    str(c.get("name") or "") for c in owned_cards if c.get("name")
                ]
                # The commander itself is guaranteed in the deck — treat it as owned
                # so commander-anchored combo lines (e.g., must_be_commander) score.
                owned_names_for_combo.append(commander_name)
                reachable_combos = relevant_combos_for_build(
                    commander_identity=identity_set,
                    owned_card_names=owned_names_for_combo,
                )
                combo_name_lookup = build_combo_name_lookup(reachable_combos)
            except Exception:
                reachable_combos = []
                combo_name_lookup = {}

    # Build scored pool of nonland legal cards plus a separate land pool.
    nonland_pool: list[tuple[float, dict[str, Any], set[str], str]] = []
    nonbasic_land_pool: list[tuple[float, dict[str, Any]]] = []
    bracket_excluded_count = 0
    # v1.6.1 Phase 1: counters surfaced in the report so the user can see
    # exactly what the legality + color-identity gates filtered out.
    color_identity_excluded_count = 0
    legality_banned_excluded_count = 0
    legality_not_legal_excluded_count = 0
    legality_restricted_excluded_count = 0
    scryfall_unmatched_count = 0

    for card_entry in owned_cards:
        name = card_entry.get("name") or ""
        if not name or name == commander_name:
            continue
        # v1.6.1 Phase 4: smart resolver (exact → normalized → face /
        # printed / flavor alt) instead of raw .lower() lookup. Handles
        # MDFC face names, split-card sides, accented variants, and the
        # printed/flavor-name reprints (Universes Within, etc.) cleanly.
        scry = _resolve(name) or {}
        if not scry:
            # Card name didn't resolve in Scryfall (printed-name MDFC, typo,
            # name drift). Counted so the report can flag it for the user.
            scryfall_unmatched_count += 1
            continue
        # v1.6.1 Phase 4: rewrite the working name to the canonical Scryfall
        # name. If the user typed "Fire" we want the decklist line to say
        # "Fire // Ice" so it pastes into Archidekt / Moxfield correctly and
        # so duplicate detection across alt spellings works.
        canonical_name = str(scry.get("name") or name)
        if canonical_name and canonical_name != name:
            name = canonical_name
        # v1.6.1 Phase 1: Commander legality gate. Run BEFORE the bracket
        # filter so a banned card is rejected at any bracket, with or without
        # bracket-pressure tags. The allow_banned_cards flag is the explicit
        # off-by-default Rule Zero / custom-mode escape hatch.
        if should_exclude_from_commander_build is not None:
            excluded, reason = should_exclude_from_commander_build(
                scry, allow_banned_cards=allow_banned_cards,
            )
            if excluded:
                if reason == EXCLUDE_REASON_BANNED:
                    legality_banned_excluded_count += 1
                elif reason == EXCLUDE_REASON_NOT_LEGAL:
                    legality_not_legal_excluded_count += 1
                elif reason == EXCLUDE_REASON_RESTRICTED:
                    legality_restricted_excluded_count += 1
                continue
        card_identity = _card_color_identity(scry)
        # Color identity rule: card's identity must be a subset of commander's.
        if card_identity and not card_identity.issubset(identity_set):
            color_identity_excluded_count += 1
            continue
        type_line = str(scry.get("type_line") or "")
        mana_value = float(scry.get("cmc") or 0)

        if _card_is_land(scry):
            # Skip basic lands here (we'll add basics ourselves).
            if "Basic" in type_line:
                continue
            nonbasic_land_pool.append((mana_value, {
                "name": name,
                "owned_quantity": int(card_entry.get("owned_quantity") or 1),
                "source_files": list(card_entry.get("source_files") or []),
                "type_line": type_line,
                "mana_value": mana_value,
            }))
            continue

        # Role-tag the card.
        if infer_card_role_tags is not None:
            try:
                card_tags = set(infer_card_role_tags(scry))
            except Exception:
                card_tags = set()
        else:
            card_tags = set()

        # v1.5.40: Bracket hard filter — drop cards excluded by the chosen bracket.
        if is_card_allowed_in_bracket is not None and bracket_preference:
            if not is_card_allowed_in_bracket(card_tags, name, bracket_preference):
                bracket_excluded_count += 1
                continue

        bucket = _classify_role_bucket(card_tags, combined_strategy_tags)
        score = _score_card(card_tags, combined_strategy_tags, mana_value)
        # Track which signals contributed to this card's score — used to render
        # short per-card "why" tags in the markdown output so the user can see
        # at a glance why a particular card was included.
        why_tags: list[str] = []
        strategy_match_count = len(card_tags & combined_strategy_tags) if combined_strategy_tags else 0
        if strategy_match_count > 0:
            why_tags.append("Strategy fit")
        # v1.5.40: Apply the bracket score modifier (soft preference shift).
        if score_modifier_for_bracket is not None and bracket_preference:
            score += score_modifier_for_bracket(card_tags, bracket_preference)
        # v1.5.41 Item 3: Commander-text amplifier boost. Cards that amplify the
        # commander's specific ability (token doublers for token commanders,
        # ETB doublers for blink commanders, etc.) get a meaningful score bump
        # so the deck feels built around this commander.
        if commander_amp_tags:
            overlap = card_tags & commander_amp_tags
            if overlap:
                # 1.5 per matching amplifier tag, capped so a 5-tag overlap
                # doesn't completely dominate the pool ranking.
                score += min(len(overlap) * 1.5, 6.0)
                why_tags.append("Commander amplifier")
        # v1.5.42 Item 4: Philosophy / persona bias. Add the persona's
        # tag-score modifiers on top of the existing scoring chain.
        if philosophy_score_modifier is not None and sub_philosophy:
            philosophy_amount = philosophy_score_modifier(card_tags, sub_philosophy)
            score += philosophy_amount
            if philosophy_amount >= 1.0:
                why_tags.append("Persona pick")
        # v1.5.43 Item 5: Combo-aware scoring. Bias toward (or away from) cards
        # in combos this commander + collection can actually reach. Capped
        # internally at +/- 6.0 so it nudges without overwhelming earlier signals.
        if combo_score_modifier is not None and combo_orientation != "neutral" and combo_name_lookup:
            score += combo_score_modifier(name, combo_name_lookup, combo_orientation)
            # Flag combo pieces regardless of orientation — the user wants to
            # know which cards form a reachable combo line in their deck.
            if combo_name_lookup.get(name.lower()):
                why_tags.append("Combo piece")
        # v1.6.2 Phase C: Tribal fidelity boost. On-tribe creatures get an
        # explicit score nudge so the Strategy bucket prefers (e.g.) Dinosaurs
        # for Ghalta over generic green creatures with high tag counts.
        if (
            commander_tribes
            and tribal_fidelity_boost is not None
            and extract_card_tribes is not None
        ):
            card_tribes_set = extract_card_tribes(scry)
            if card_tribes_set:
                boost = tribal_fidelity_boost(commander_tribes, card_tribes_set)
                if boost > 0:
                    score += boost
                    if describe_tribal_match is not None:
                        match_label = describe_tribal_match(
                            commander_tribes, card_tribes_set,
                        )
                        if match_label:
                            why_tags.append(match_label)
        nonland_pool.append((score, {
            "name": name,
            "owned_quantity": int(card_entry.get("owned_quantity") or 1),
            "source_files": list(card_entry.get("source_files") or []),
            "type_line": type_line,
            "mana_value": mana_value,
            "why_tags": why_tags,
            # v1.6.1 Phase 3: type-aware fill needs to know creature-ness per
            # card so the creature ceiling can be enforced at pick time.
            "is_creature": is_creature_type_line(type_line),
        }, card_tags, bucket))

    # Sort nonland pool by score descending.
    nonland_pool.sort(key=lambda x: (-x[0], x[1]["name"]))

    # Assign cards to buckets up to target counts.
    picked_names: set[str] = set()
    picks_by_bucket: dict[str, list[DraftedCardEntry]] = {b: [] for b in ROLE_BUCKET_ORDER}

    # v1.6.1 Phase 3: creature-ceiling enforcement state.
    # Commander is usually a creature; pre-count it. Planeswalker / background /
    # special-rule commanders may not be — check the type line.
    commander_is_creature = is_creature_type_line(
        str(commander_scry.get("type_line") or "")
    )
    creature_count = 1 if commander_is_creature else 0
    creature_ceiling = creature_band.ceiling if creature_band is not None else 99
    creatures_skipped_for_ceiling = 0  # diagnostic
    creatures_added_past_ceiling = 0  # safety-net pass relaxes ceiling

    def _try_add_to_bucket(
        bucket: str,
        card: dict,
        *,
        enforce_creature_ceiling: bool,
    ) -> bool:
        """Add card to picks_by_bucket[bucket] if it fits the bucket + creature ceiling.

        Returns True if added, False if skipped. Updates creature_count and
        the skipped/over-ceiling diagnostic counters.
        """
        nonlocal creature_count, creatures_skipped_for_ceiling, creatures_added_past_ceiling
        is_creature = bool(card.get("is_creature"))
        if enforce_creature_ceiling and is_creature and creature_count >= creature_ceiling:
            creatures_skipped_for_ceiling += 1
            return False
        picks_by_bucket[bucket].append(DraftedCardEntry(
            card_name=card["name"],
            quantity=1,
            role_bucket=bucket,
            source_files=card["source_files"],
            mana_value=card["mana_value"],
            type_line=card["type_line"],
            why_tags=list(card.get("why_tags") or []),
        ))
        picked_names.add(card["name"])
        if is_creature:
            creature_count += 1
            if not enforce_creature_ceiling and creature_count > creature_ceiling:
                creatures_added_past_ceiling += 1
        return True

    # Pass 1: try to fill each role bucket from cards whose best bucket matches.
    # Creature ceiling enforced for Strategy + Flex (Utility buckets rarely
    # contain creatures, but the same enforcement applies uniformly).
    for score, card, tags, bucket in nonland_pool:
        if card["name"] in picked_names:
            continue
        target = TARGET_COUNTS.get(bucket, 0)
        if target == 0:
            continue
        if len(picks_by_bucket[bucket]) >= target:
            continue
        _try_add_to_bucket(bucket, card, enforce_creature_ceiling=True)

    # Pass 2: pour leftover top-scored cards into Flex until target. Creature
    # ceiling enforced — this is where the bias toward creatures matters most
    # because the scoring formula rewards tag-heavy cards (creatures usually win).
    flex_target = TARGET_COUNTS["Flex"]
    for score, card, tags, bucket in nonland_pool:
        if len(picks_by_bucket["Flex"]) >= flex_target:
            break
        if card["name"] in picked_names:
            continue
        _try_add_to_bucket("Flex", card, enforce_creature_ceiling=True)

    # v1.5.39: After the standard passes, compute the deck-size shortfall and
    # ALWAYS try to hit 100 cards. If non-flex role buckets came up short
    # (e.g., your collection is thin on Protection), expand Flex by that
    # shortfall and pull additional cards from the unused pool.
    def _current_nonland_total() -> int:
        total = 1  # commander
        for b in ("Ramp", "Card Draw", "Removal", "Protection", "Strategy", "Flex"):
            total += len(picks_by_bucket[b])
        return total

    # Target non-land total = 100 - target lands (37) = 63
    target_nonland_total = 100 - TARGET_COUNTS["Lands"]

    # v1.6.1 Phase 3: Two-stage safety-net fill. First try to hit 100 with the
    # ceiling enforced (prefers noncreatures). If still short, relax the
    # ceiling so the deck reaches 100 (better an extra creature than a 95-card
    # deck). The relax-pass increments creatures_added_past_ceiling so the
    # report can explain the bulge.
    for enforce_ceiling in (True, False):
        while _current_nonland_total() < target_nonland_total:
            added_in_pass = False
            for score, card, tags, bucket in nonland_pool:
                if _current_nonland_total() >= target_nonland_total:
                    break
                if card["name"] in picked_names:
                    continue
                if _try_add_to_bucket("Flex", card, enforce_creature_ceiling=enforce_ceiling):
                    added_in_pass = True
            if not added_in_pass:
                break

    # Lands: take up to ~17 owned nonbasics, fill rest with basics.
    # v1.6.2 Phase D: when the commander has 2+ colors, prefer premium fixing
    # lands (Command Tower, triomes, shocks, fetches) ahead of alphabetical
    # so the mana base is functional in multi-color decks. Mono-color decks
    # still get alphabetical order — they don't need color fixing.
    try:
        from rules.multi_color_lands import (
            fixer_priority,
            prefers_premium_fixers,
        )
        _color_count = len([c for c in identity_set if c in "WUBRG"])
        if prefers_premium_fixers(_color_count):
            nonbasic_land_pool.sort(
                key=lambda x: (fixer_priority(x[1]["name"]), x[1]["name"])
            )
        else:
            nonbasic_land_pool.sort(key=lambda x: x[1]["name"])
    except Exception:
        nonbasic_land_pool.sort(key=lambda x: x[1]["name"])
    land_target = TARGET_COUNTS["Lands"]
    land_entries: list[DraftedCardEntry] = []
    nonbasic_take = min(len(nonbasic_land_pool), land_target - 10)  # leave at least 10 slots for basics
    for _, land in nonbasic_land_pool[:nonbasic_take]:
        if land["name"] in picked_names:
            continue
        land_entries.append(DraftedCardEntry(
            card_name=land["name"],
            quantity=1,
            role_bucket="Lands",
            source_files=land["source_files"],
            mana_value=0.0,
            type_line=land["type_line"],
        ))
        picked_names.add(land["name"])

    # Fill remainder with basics distributed across identity colors.
    remaining_lands = land_target - len(land_entries)
    if remaining_lands > 0:
        colors_for_basics = sorted([c for c in identity_set if c in "WUBRG"])
        if not colors_for_basics:
            # Colorless commander: use Wastes.
            land_entries.append(DraftedCardEntry(
                card_name="Wastes",
                quantity=remaining_lands,
                role_bucket="Lands",
                is_basic_land=True,
                type_line="Basic Land — Wastes",
            ))
        else:
            per_color = remaining_lands // len(colors_for_basics)
            leftover = remaining_lands - (per_color * len(colors_for_basics))
            for color in colors_for_basics:
                count = per_color + (1 if leftover > 0 else 0)
                if leftover > 0:
                    leftover -= 1
                if count <= 0:
                    continue
                land_entries.append(DraftedCardEntry(
                    card_name=COLOR_TO_BASIC_LAND[color],
                    quantity=count,
                    role_bucket="Lands",
                    is_basic_land=True,
                    type_line=f"Basic Land — {COLOR_TO_BASIC_LAND[color]}",
                ))

    picks_by_bucket["Lands"] = land_entries

    # Commander entry.
    picks_by_bucket["Commander"] = [DraftedCardEntry(
        card_name=commander_name,
        quantity=1,
        role_bucket="Commander",
        is_commander=True,
        type_line=str(commander_scry.get("type_line") or ""),
        mana_value=float(commander_scry.get("cmc") or 0),
    )]

    # v1.5.39: If the deck is STILL under 100 (collection genuinely too thin in
    # color identity for the role targets), pad to 100 with extra basic lands
    # distributed across identity colors. The user explicitly wants the output
    # to always reach 100 cards — better to have an extra basic than a 95-card
    # deck that won't even be legal when copy-pasted into Archidekt.
    current_total = 1  # commander
    for b in ("Lands", "Ramp", "Card Draw", "Removal", "Protection", "Strategy", "Flex"):
        current_total += sum(e.quantity for e in picks_by_bucket[b])
    shortfall = 100 - current_total
    if shortfall > 0:
        # Add extra basics to the Lands bucket.
        colors_for_basics = sorted([c for c in identity_set if c in "WUBRG"])
        if not colors_for_basics:
            # Colorless: add Wastes.
            picks_by_bucket["Lands"].append(DraftedCardEntry(
                card_name="Wastes",
                quantity=shortfall,
                role_bucket="Lands",
                is_basic_land=True,
                type_line="Basic Land — Wastes",
            ))
        else:
            # Find existing basic-land entries we can bump up first.
            existing_basics: dict[str, DraftedCardEntry] = {
                e.card_name: e for e in picks_by_bucket["Lands"] if e.is_basic_land
            }
            per_color = shortfall // len(colors_for_basics)
            leftover = shortfall - (per_color * len(colors_for_basics))
            for color in colors_for_basics:
                add = per_color + (1 if leftover > 0 else 0)
                if leftover > 0:
                    leftover -= 1
                if add <= 0:
                    continue
                basic_name = COLOR_TO_BASIC_LAND[color]
                if basic_name in existing_basics:
                    existing_basics[basic_name].quantity += add
                else:
                    picks_by_bucket["Lands"].append(DraftedCardEntry(
                        card_name=basic_name,
                        quantity=add,
                        role_bucket="Lands",
                        is_basic_land=True,
                        type_line=f"Basic Land — {basic_name}",
                    ))

    # Assemble final entries in display order.
    entries: list[DraftedCardEntry] = []
    role_counts: dict[str, int] = {}
    missing_slots: dict[str, int] = {}
    for bucket in ROLE_BUCKET_ORDER:
        bucket_entries = picks_by_bucket.get(bucket, []) or []
        entries.extend(bucket_entries)
        total_in_bucket = sum(e.quantity for e in bucket_entries)
        role_counts[bucket] = total_in_bucket
        target = TARGET_COUNTS.get(bucket, 0)
        if total_in_bucket < target:
            missing_slots[bucket] = target - total_in_bucket

    total_cards = sum(e.quantity for e in entries)

    # v1.6.1 Phase 3: compute final creature / noncreature counts from the
    # assembled deck. creature_count was tracked during the fill passes for
    # ceiling enforcement; recompute here to match what actually landed in
    # the final entries list (e.g., the commander + all drafted creatures).
    final_creature_count = 0
    final_noncreature_nonland_count = 0
    for entry in entries:
        if entry.is_basic_land or entry.role_bucket == "Lands":
            continue
        if is_creature_type_line(entry.type_line):
            final_creature_count += entry.quantity
        else:
            final_noncreature_nonland_count += entry.quantity

    notes: list[str] = []
    # v1.6.1 Phase 1: legality gate summary FIRST so users see this before
    # bracket / persona / combo notes. Banned-commander flag is loudest.
    if commander_is_banned:
        if allow_banned_cards:
            notes.append(
                f"CUSTOM MODE: selected commander '{commander_name}' is BANNED "
                "in Commander but allow_banned_cards=True. This deck is illegal "
                "at any normal Commander table — Rule Zero / playgroup approval "
                "required before play."
            )
        else:
            notes.append(
                f"WARNING: selected commander '{commander_name}' is BANNED in "
                "Commander. The deck builder will still produce a list, but "
                "the deck is not legal. Pick a different commander."
            )
    if commander_legality_gate_summary is not None:
        notes.append(commander_legality_gate_summary(
            banned_excluded=legality_banned_excluded_count,
            not_legal_excluded=legality_not_legal_excluded_count,
            restricted_excluded=legality_restricted_excluded_count,
            allow_banned_cards=allow_banned_cards,
        ))
    if color_identity_excluded_count > 0:
        notes.append(
            f"{color_identity_excluded_count} card(s) from your collection were "
            f"excluded for color identity (outside the commander's color identity)."
        )
    if scryfall_unmatched_count > 0:
        notes.append(
            f"{scryfall_unmatched_count} card(s) from your collection could not be "
            f"resolved against the local Scryfall database and were skipped."
        )
    # v1.6.1 Phase 3: creature-density note. Surfaces the band, the actual
    # count, and whether the ceiling was relaxed during the safety-net fill
    # pass so the user can read the structural shape at a glance.
    if creature_band is not None and creature_band_status_label is not None:
        label = creature_band_status_label(creature_band, final_creature_count)
        notes.append(f"Creature skeleton ({creature_band.category}): {label}")
        if creatures_added_past_ceiling > 0:
            notes.append(
                f"{creatures_added_past_ceiling} creature(s) were added past the "
                f"creature ceiling ({creature_band.ceiling}) during the safety-net "
                f"fill — your collection was thin on noncreature support for this "
                f"strategy, so the deck pushed past the band to reach 100 cards."
            )
        elif creatures_skipped_for_ceiling > 0:
            notes.append(
                f"{creatures_skipped_for_ceiling} creature pick(s) were skipped "
                f"because the creature ceiling ({creature_band.ceiling}) was "
                f"already reached. Their slot went to noncreature support instead."
            )
    if total_cards < 100:
        notes.append(
            f"Deck is {total_cards} cards — short by {100 - total_cards}. "
            "Likely cause: collection thin in one or more roles. See Missing slots below."
        )
    elif total_cards > 100:
        notes.append(f"Deck is {total_cards} cards — over by {total_cards - 100}.")
    if shortfall > 0:
        notes.append(
            f"{shortfall} extra basic land(s) were added to reach 100 cards because "
            "the collection was thin in one or more role buckets. See Missing slots."
        )
    if not strategy_tags:
        notes.append(
            "No Primary strategy was selected in the Build Setup Panel, "
            "so cards were placed in role buckets based on utility roles only "
            "(ramp / draw / removal / protection / flex)."
        )
    # v1.5.40: surface what bracket filtering did so the user understands why
    # certain cards may have been skipped (or boosted).
    if bracket_preference:
        try:
            from build_from_collection.bracket_filter import bracket_filter_summary
            notes.append(f"Bracket filter: {bracket_filter_summary(bracket_preference)}")
        except Exception:
            pass
        if bracket_excluded_count > 0:
            notes.append(
                f"{bracket_excluded_count} card(s) from your collection were excluded "
                f"by the bracket filter for {bracket_preference}."
            )
    # v1.5.41 Item 3: surface what the commander-text scorer detected so the
    # user understands why certain card categories were preferred.
    if commander_amp_tags:
        try:
            from build_from_collection.commander_text_scorer import commander_amplifier_summary
            notes.append(commander_amplifier_summary(commander_scry))
        except Exception:
            pass
    # v1.5.42 Item 4: explain the philosophy / persona bias applied.
    if sub_philosophy:
        try:
            from build_from_collection.philosophy_bias import philosophy_bias_summary
            summary = philosophy_bias_summary(sub_philosophy)
            if summary:
                notes.append(summary)
        except Exception:
            pass
    # v1.5.43 Item 5: explain combo-aware scoring detection + bias direction.
    if combo_awareness_summary is not None and combo_orientation != "neutral":
        try:
            combo_summary = combo_awareness_summary(reachable_combos, combo_orientation)
            if combo_summary:
                notes.append(combo_summary)
        except Exception:
            pass

    return Full100CardDraftResult(
        commander_name=commander_name,
        color_identity=sorted(identity_set),
        primary_strategy=primary_strategy or "Not selected yet",
        secondary_strategy=secondary_strategy or "None",
        entries=entries,
        role_counts=role_counts,
        missing_slots=missing_slots,
        total_cards=total_cards,
        notes=notes,
        collection_cards_analyzed=len(owned_cards),
        scryfall_unmatched_count=scryfall_unmatched_count,
        color_identity_excluded_count=color_identity_excluded_count,
        legality_banned_excluded_count=legality_banned_excluded_count,
        legality_not_legal_excluded_count=legality_not_legal_excluded_count,
        legality_restricted_excluded_count=legality_restricted_excluded_count,
        bracket_excluded_count=bracket_excluded_count,
        allow_banned_cards=allow_banned_cards,
        commander_is_banned=commander_is_banned,
        creature_count=final_creature_count,
        noncreature_nonland_count=final_noncreature_nonland_count,
        creature_band_category=creature_band.category if creature_band else "",
        creature_band_floor=creature_band.floor if creature_band else 0,
        creature_band_target=creature_band.target if creature_band else 0,
        creature_band_ceiling=creature_band.ceiling if creature_band else 0,
        creatures_skipped_for_ceiling=creatures_skipped_for_ceiling,
        creatures_added_past_ceiling=creatures_added_past_ceiling,
    )


def render_full_100_card_draft_markdown(result: Full100CardDraftResult) -> str:
    """Produce a markdown report containing a copy-paste decklist + role breakdown."""
    identity_text = "/".join(result.color_identity) if result.color_identity else "Colorless"
    lines: list[str] = [
        f"# Full 100-Card Draft — {result.commander_name}",
        "",
        f"- Color identity: {identity_text}",
        f"- Primary strategy: {result.primary_strategy}",
        f"- Secondary strategy: {result.secondary_strategy}",
        f"- Total cards: {result.total_cards}",
        "",
        "## Copy-Paste Decklist",
        "",
        "Paste this section into Archidekt, Moxfield, or any deckbuilding site.",
        "",
        "```",
    ]
    # Standard MTG list format: "<qty> <Card Name>" per line, commander first.
    for entry in result.entries:
        lines.append(f"{entry.quantity} {entry.card_name}")
    lines.append("```")
    lines.append("")

    # Role-bucket breakdown for human reading.
    lines.append("## Breakdown By Role")
    lines.append("")
    for bucket in ROLE_BUCKET_ORDER:
        bucket_entries = [e for e in result.entries if e.role_bucket == bucket]
        if not bucket_entries:
            continue
        target = TARGET_COUNTS.get(bucket, 0)
        actual = sum(e.quantity for e in bucket_entries)
        target_text = f" (target {target})" if target else ""
        lines.append(f"### {bucket}: {actual}{target_text}")
        lines.append("")
        for entry in bucket_entries:
            line = f"- **{entry.card_name}** ×{entry.quantity}"
            # Per-card "why" annotation — short reason tags from the scoring chain.
            # Shows the user at a glance why a particular card was included
            # (strategy fit, commander amplifier, combo piece, persona pick).
            if entry.why_tags:
                line += f" — _why: {', '.join(entry.why_tags)}_"
            if entry.source_files:
                seen: list[str] = []
                for src in entry.source_files:
                    if src and src not in seen:
                        seen.append(src)
                line += f" — owned from: `{'; '.join(seen)}`"
            elif entry.is_basic_land:
                line += " — basic land (assumed available)"
            lines.append(line)
        lines.append("")

    # Curve + missing slots summary.
    lines.append("## Summary")
    lines.append("")
    for bucket in ROLE_BUCKET_ORDER:
        count = result.role_counts.get(bucket, 0)
        target = TARGET_COUNTS.get(bucket, 0)
        status = "✓" if count >= target else f"⚠ short by {target - count}"
        lines.append(f"- {bucket}: {count}/{target} {status}")
    lines.append("")

    # v1.6.1 Phase 7: the structured Build Validation report block replaces
    # the legacy "Legality & Collection Diagnostics" wall of lines. The new
    # block has a top-line verdict (LEGAL / LEGAL but weak / collection-
    # limited / ILLEGAL / CUSTOM MODE) followed by per-component sub-sections.
    try:
        from build_from_collection.build_validation_report import (
            build_validation_report_lines,
        )
        lines.extend(build_validation_report_lines(result))
    except Exception:
        # Defensive fallback so the report still renders if the validation
        # module fails to import — only happens during partial installs.
        lines.append("## Build Validation")
        lines.append("")
        lines.append("- (Build validation module unavailable in this build.)")
        lines.append("")
    if result.missing_slots:
        lines.append("**Missing slots:**")
        for bucket, missing in result.missing_slots.items():
            lines.append(f"- {bucket}: short by {missing}")
        lines.append("")
    if result.notes:
        lines.append("**Notes:**")
        for note in result.notes:
            lines.append(f"- {note}")
        lines.append("")

    lines.append("## Boundaries")
    lines.append("")
    lines.append("- Generated from heuristic role bucketing on your owned cards.")
    lines.append("- Color-identity-correct against the selected commander.")
    lines.append("- Does NOT validate bracket, playgroup fit, or combo legality.")
    lines.append("- Treat as a starting draft — pilot judgement decides final inclusions.")
    return "\n".join(lines)


def render_full_100_card_draft_plain_decklist(result: Full100CardDraftResult) -> str:
    """Bare 'qty name' format with no headings — for direct paste into deckbuilding sites."""
    return "\n".join(f"{e.quantity} {e.card_name}" for e in result.entries)
