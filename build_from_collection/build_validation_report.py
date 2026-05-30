"""Build-validation report block (v1.6.1 Phase 7).

WHY THIS FILE EXISTS
--------------------
Phases 1-6 added a lot of diagnostic counters to the deck build result
(legality exclusions, color-identity exclusions, bracket filter,
creature-band ceiling, scryfall-unmatched, banned commander flag, etc.).
The existing markdown renderer had a single "Legality & Collection
Diagnostics" block but it was an unorganized list of lines and didn't
produce the explicit verdict statements the user asked for in the
original brief:

  - "This deck is legal."
  - "This deck is legal but structurally weak."
  - "This deck is collection-limited."
  - "This deck violates Commander rules."
  - "This deck includes banned cards and should fail validation."

This module is the canonical builder of the **Build Validation** report
block. It takes a `Full100CardDraftResult` and produces:

  1. A primary structural verdict (one of the strings above).
  2. A bracket-expectations sub-status.
  3. A collection-readiness sub-status (collection-limited details).
  4. The full diagnostics breakdown the user can scan at a glance.

The report writer calls `build_validation_report_lines(result)` and
splices the returned lines into the markdown report. Behavior is pure-
function and dependency-free aside from the result type.

PUBLIC API
----------
- VERDICT_LEGAL / VERDICT_LEGAL_BUT_WEAK / VERDICT_COLLECTION_LIMITED /
  VERDICT_ILLEGAL / VERDICT_CUSTOM_MODE        — verdict identifiers
- compute_build_verdict(result) -> str         — picks the verdict
- compute_bracket_expectations_status(result)  -> str
- compute_collection_readiness_status(result)  -> str
- build_validation_report_lines(result)        -> list[str]
- build_validation_top_line(result)            -> str  (one-line summary)
"""
from __future__ import annotations

from typing import Any


VERDICT_LEGAL = "legal"
VERDICT_LEGAL_BUT_WEAK = "legal_but_structurally_weak"
VERDICT_COLLECTION_LIMITED = "collection_limited"
VERDICT_ILLEGAL = "illegal"
VERDICT_CUSTOM_MODE = "custom_mode_banned_cards_allowed"


_VERDICT_HEADLINE_TEXT: dict[str, str] = {
    VERDICT_LEGAL: "This deck is legal in Commander.",
    VERDICT_LEGAL_BUT_WEAK: (
        "This deck is legal but structurally weak — one or more role buckets "
        "did not fill to their target."
    ),
    VERDICT_COLLECTION_LIMITED: (
        "This deck is collection-limited — the build hit its target through "
        "basic-land padding or by relaxing the creature ceiling because the "
        "collection was thin on noncreature support."
    ),
    VERDICT_ILLEGAL: (
        "This deck violates Commander rules — the commander is banned in "
        "Commander, or the deck includes banned cards. Do not bring this "
        "deck to a normal Commander table."
    ),
    VERDICT_CUSTOM_MODE: (
        "CUSTOM MODE — banned-card filtering was explicitly disabled. The "
        "deck does not meet normal Commander legality. Rule Zero / playgroup "
        "approval required before play."
    ),
}


_VERDICT_BADGE: dict[str, str] = {
    VERDICT_LEGAL: "✓ LEGAL",
    VERDICT_LEGAL_BUT_WEAK: "⚠ LEGAL (structurally weak)",
    VERDICT_COLLECTION_LIMITED: "⚠ LEGAL (collection-limited)",
    VERDICT_ILLEGAL: "❌ ILLEGAL",
    VERDICT_CUSTOM_MODE: "❌ CUSTOM MODE",
}


def _has_missing_slots(result: Any) -> bool:
    """True if any role bucket ended up below its target."""
    missing = getattr(result, "missing_slots", None) or {}
    return any(int(v or 0) > 0 for v in missing.values())


def _collection_limited(result: Any) -> bool:
    """True if the build relied on collection-limited fallbacks.

    Specifically: the safety-net pass added creatures past the creature
    ceiling (because the collection was thin on noncreature support), OR the
    creature count is below the band floor (collection thin on creatures).
    Basic-land padding alone does NOT count — that's normal for any deck
    whose nonbasic lands are limited.
    """
    if int(getattr(result, "creatures_added_past_ceiling", 0) or 0) > 0:
        return True
    floor = int(getattr(result, "creature_band_floor", 0) or 0)
    count = int(getattr(result, "creature_count", 0) or 0)
    # Floor of 0 = no band classified (legacy result); skip the check.
    if floor > 0 and count > 0 and count < floor:
        return True
    return False


def _banned_cards_present(result: Any) -> bool:
    """True if banned cards landed in the final deck (only possible in custom mode)."""
    if not bool(getattr(result, "allow_banned_cards", False)):
        return False
    # In custom mode the gate doesn't exclude banned cards. If there WERE
    # banned cards in the collection that fit color identity, they likely
    # entered the deck. We can't know for sure without re-scanning the
    # final entries against Scryfall here, but the conservative read is:
    # if allow_banned_cards was on, we assume the deck might contain them.
    return True


def compute_build_verdict(result: Any) -> str:
    """Pick the primary structural verdict from a Full100CardDraftResult.

    Order of precedence (most severe first):
      ILLEGAL (banned commander)
      CUSTOM_MODE (allow_banned_cards was on)
      LEGAL_BUT_WEAK (any role bucket below target)
      COLLECTION_LIMITED (creature ceiling relaxed or below floor)
      LEGAL (clean)
    """
    if bool(getattr(result, "commander_is_banned", False)) and not bool(
        getattr(result, "allow_banned_cards", False)
    ):
        return VERDICT_ILLEGAL
    if bool(getattr(result, "allow_banned_cards", False)):
        # Custom mode is its own verdict regardless of whether the commander
        # itself is banned — the user opted in, and the deck does not meet
        # normal Commander legality either way.
        return VERDICT_CUSTOM_MODE
    if int(getattr(result, "total_cards", 0) or 0) != 100:
        # Deck size wrong is a separate kind of illegal — shouldn't happen
        # in practice because the builder pads to 100, but we should catch
        # it if it does.
        return VERDICT_ILLEGAL
    if _has_missing_slots(result):
        return VERDICT_LEGAL_BUT_WEAK
    if _collection_limited(result):
        return VERDICT_COLLECTION_LIMITED
    return VERDICT_LEGAL


def compute_bracket_expectations_status(result: Any) -> str:
    """Plain-language note about bracket expectations.

    Phase 5's bracket filter has hard exclusions, so bracket-pressure cards
    that fail the filter never enter the pool. This status simply explains
    that to the user: "the filter ran and N cards were excluded." If no
    bracket was selected, says so.
    """
    bracket_excluded = int(getattr(result, "bracket_excluded_count", 0) or 0)
    if bracket_excluded > 0:
        return (
            f"Bracket filter ran: {bracket_excluded} card(s) from your collection "
            f"were excluded for bracket-pressure reasons. Surviving picks fit the "
            f"chosen bracket's profile."
        )
    return (
        "Bracket filter ran but no cards were excluded for bracket-pressure "
        "reasons — either no bracket was selected, or none of your collection's "
        "cards tripped the filter."
    )


def compute_collection_readiness_status(result: Any) -> list[str]:
    """Plain-language explanations of any collection-limited fallbacks.

    Returns multiple lines because there can be multiple reasons (creature
    ceiling relaxed, missing-slot roles, scryfall-unmatched, etc.). Empty
    list means the collection had no shortfalls.
    """
    lines: list[str] = []

    relaxed = int(getattr(result, "creatures_added_past_ceiling", 0) or 0)
    if relaxed > 0:
        ceiling = int(getattr(result, "creature_band_ceiling", 0) or 0)
        lines.append(
            f"Creature ceiling ({ceiling}) was relaxed: {relaxed} additional "
            f"creature(s) were taken to reach 100 cards because the collection "
            f"was thin on noncreature support for this strategy."
        )

    floor = int(getattr(result, "creature_band_floor", 0) or 0)
    count = int(getattr(result, "creature_count", 0) or 0)
    if floor > 0 and count > 0 and count < floor:
        lines.append(
            f"Creature floor ({floor}) was not met: only {count} creature(s) in "
            f"the deck. The collection may be thin on creatures for this "
            f"strategy, or the noncreature score dominated selection."
        )

    missing = getattr(result, "missing_slots", None) or {}
    short_buckets = [(b, int(v or 0)) for b, v in missing.items() if int(v or 0) > 0]
    for bucket, short in short_buckets:
        lines.append(
            f"Role bucket '{bucket}' short by {short} — collection thin on "
            f"cards that satisfy this role for the chosen strategy + bracket."
        )

    unmatched = int(getattr(result, "scryfall_unmatched_count", 0) or 0)
    if unmatched > 0:
        lines.append(
            f"{unmatched} card(s) from your collection couldn't be matched to "
            f"the local Scryfall database and were skipped. Check the card "
            f"names in your collection files."
        )

    return lines


def build_validation_top_line(result: Any) -> str:
    """One-line headline summary (badge + verdict) for the top of the block."""
    verdict = compute_build_verdict(result)
    badge = _VERDICT_BADGE.get(verdict, "?")
    headline = _VERDICT_HEADLINE_TEXT.get(verdict, "Unknown verdict.")
    return f"{badge} — {headline}"


def build_validation_report_lines(result: Any) -> list[str]:
    """Build the full Build Validation markdown section as a list of lines.

    Section layout:
        ## Build Validation
        - Top-line verdict badge + sentence
        - Legality verdict (per-component: commander, banned-card filter, deck-size)
        - Role breakdown vs target (✓ / ⚠ per bucket)
        - Creature density vs band
        - Collection readiness (only if there are issues)
        - Bracket expectations status
        - Counter totals (collection size, exclusions per gate)
    """
    verdict = compute_build_verdict(result)
    lines: list[str] = []
    lines.append("## Build Validation")
    lines.append("")
    lines.append(f"**{build_validation_top_line(result)}**")
    lines.append("")

    # ---- Legality block ------------------------------------------------
    lines.append("### Legality")
    lines.append("")
    if bool(getattr(result, "commander_is_banned", False)):
        if bool(getattr(result, "allow_banned_cards", False)):
            lines.append(
                "- Commander: ❌ BANNED in Commander, allowed by custom-mode flag"
            )
        else:
            lines.append("- Commander: ❌ BANNED in Commander (pick a different commander)")
    else:
        lines.append("- Commander: ✓ Legal as a commander")

    banned_excluded = int(getattr(result, "legality_banned_excluded_count", 0) or 0)
    not_legal_excluded = int(getattr(result, "legality_not_legal_excluded_count", 0) or 0)
    if bool(getattr(result, "allow_banned_cards", False)):
        lines.append("- Banned-card filter: ❌ DISABLED (custom mode)")
        if banned_excluded > 0 or _banned_cards_present(result):
            lines.append(
                "  - Banned cards may appear in the final deck — see deck list "
                "for review."
            )
    else:
        if banned_excluded == 0:
            lines.append(
                "- Banned-card filter: ✓ Active; no Commander-banned cards in collection"
            )
        else:
            lines.append(
                f"- Banned-card filter: ✓ Active; {banned_excluded} "
                f"Commander-banned card(s) excluded from build"
            )

    if not_legal_excluded > 0:
        lines.append(
            f"- Not-legal-in-format filter: ✓ {not_legal_excluded} non-Commander "
            f"card(s) (conspiracies, un-cards, etc.) excluded"
        )

    total = int(getattr(result, "total_cards", 0) or 0)
    if total == 100:
        lines.append(f"- Deck size: ✓ 100 cards")
    else:
        lines.append(f"- Deck size: ❌ {total} cards (expected 100)")

    color_excluded = int(getattr(result, "color_identity_excluded_count", 0) or 0)
    if color_excluded > 0:
        lines.append(
            f"- Color identity: ✓ {color_excluded} off-identity card(s) excluded"
        )
    else:
        lines.append("- Color identity: ✓ all picks within commander's identity")
    lines.append("")

    # ---- Role breakdown -----------------------------------------------
    role_counts = getattr(result, "role_counts", None) or {}
    if role_counts:
        # Lazy import to avoid touching the builder's module-level constants.
        try:
            from build_from_collection.full_100_card_draft_builder import (
                TARGET_COUNTS,
                ROLE_BUCKET_ORDER,
            )
        except Exception:
            TARGET_COUNTS = {}
            ROLE_BUCKET_ORDER = tuple(role_counts.keys())
        lines.append("### Role breakdown vs target")
        lines.append("")
        for bucket in ROLE_BUCKET_ORDER:
            actual = int(role_counts.get(bucket, 0) or 0)
            target = int(TARGET_COUNTS.get(bucket, 0) or 0)
            if target == 0:
                # Bucket that doesn't have a numeric target (e.g., Commander).
                lines.append(f"- {bucket}: {actual}")
                continue
            mark = "✓" if actual >= target else f"⚠ short by {target - actual}"
            lines.append(f"- {bucket}: {actual} / {target} {mark}")
        lines.append("")

    # ---- Creature density vs band -------------------------------------
    band_category = str(getattr(result, "creature_band_category", "") or "")
    if band_category:
        floor = int(getattr(result, "creature_band_floor", 0) or 0)
        target = int(getattr(result, "creature_band_target", 0) or 0)
        ceiling = int(getattr(result, "creature_band_ceiling", 0) or 0)
        count = int(getattr(result, "creature_count", 0) or 0)
        noncreature = int(getattr(result, "noncreature_nonland_count", 0) or 0)

        lines.append("### Creature density vs band")
        lines.append("")
        lines.append(
            f"- Band: **{band_category}** — floor {floor}, target {target}, ceiling {ceiling}"
        )
        if count < floor:
            status = f"⚠ below floor ({count} < {floor})"
        elif count > ceiling:
            status = f"⚠ above ceiling ({count} > {ceiling})"
        else:
            status = f"✓ within band ({count} between {floor} and {ceiling})"
        lines.append(f"- Final creature count: {count} ({status})")
        lines.append(f"- Final noncreature-nonland count: {noncreature}")

        skipped = int(getattr(result, "creatures_skipped_for_ceiling", 0) or 0)
        relaxed = int(getattr(result, "creatures_added_past_ceiling", 0) or 0)
        if skipped > 0:
            lines.append(
                f"- Creatures skipped to enforce ceiling: {skipped}"
            )
        if relaxed > 0:
            lines.append(
                f"- Creatures added past ceiling (safety-net fill): {relaxed}"
            )
        lines.append("")

    # ---- Collection readiness -----------------------------------------
    readiness = compute_collection_readiness_status(result)
    if readiness:
        lines.append("### Collection readiness")
        lines.append("")
        for line in readiness:
            lines.append(f"- {line}")
        lines.append("")

    # ---- Bracket expectations -----------------------------------------
    lines.append("### Bracket expectations")
    lines.append("")
    lines.append(f"- {compute_bracket_expectations_status(result)}")
    lines.append("")

    # ---- Counter totals -----------------------------------------------
    lines.append("### Diagnostic counts")
    lines.append("")
    lines.append(
        f"- Collection cards analyzed: {int(getattr(result, 'collection_cards_analyzed', 0) or 0)}"
    )
    lines.append(
        f"- Scryfall-unmatched skipped: {int(getattr(result, 'scryfall_unmatched_count', 0) or 0)}"
    )
    lines.append(
        f"- Excluded for color identity: {color_excluded}"
    )
    lines.append(
        f"- Excluded for Commander legality (banned): {banned_excluded}"
    )
    lines.append(
        f"- Excluded for Commander legality (not legal): {not_legal_excluded}"
    )
    restricted_excluded = int(getattr(result, "legality_restricted_excluded_count", 0) or 0)
    if restricted_excluded > 0:
        lines.append(f"- Excluded as restricted: {restricted_excluded}")
    lines.append(
        f"- Excluded by bracket filter: {int(getattr(result, 'bracket_excluded_count', 0) or 0)}"
    )
    lines.append("")
    return lines
