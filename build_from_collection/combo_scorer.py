"""Combo-aware scoring for Bin B deck builder (Item 5 v1.5.43).

Wires the existing combo_awareness package into the Full 100-Card Draft Builder
so the deck's scoring chain reflects the combos this commander + collection can
actually form. The scoring chain order is:

    base -> bracket -> commander-text (cap +6) -> philosophy-bias (cap +/- 8)
         -> combo-aware (cap +/- 6) [this module]

Two orientations:

- "leaning"  -> Combo Builder / Competitive Closer / Consistency Maximizer /
                 Efficiency Optimizer personas. Cards that appear in combos
                 reachable from the user's collection get a +score modifier.
                 Combos that are already one-card-away get an extra bonus.

- "averse"   -> Let Me Do My Thing / Big Moment / Theme-Vibe / Pet Card personas.
                 Cards in known combo lines get a -score modifier so the build
                 leans organic / durdle rather than infinite-combo finish.

- "neutral"  -> Everything else. Zero modifier (combo signal is ignored).

Boundaries:
- This is selection bias only. It does NOT change role tags, color identity, or
  bracket eligibility (the bracket filter still hard-excludes earlier in the chain).
- "Reachable" combos = combos whose color identity fits the commander AND have
  at least 2 cards already in the user's owned collection. A combo with only 1
  matching card is considered too speculative to score against.
- Combo detection is static against the COLLECTION, not iterative against the
  deck-in-progress. This is intentional: simpler, faster, and ~95% as accurate
  in practice.
- The combo index (data/commander_spellbook/combo_index.json) is large (~148 MB,
  ~88k combos) so it is cached at module level after the first load.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


# ---------------------------------------------------------------------------
# Persona -> orientation table
# ---------------------------------------------------------------------------
# Keys match the bare persona names emitted by
# build_from_collection.philosophy_bias.persona_name_from_selector_value
# (i.e. "Combo Builder", not "Combo Builder - Jasper / Jennifer").
PERSONA_ORIENTATION: dict[str, str] = {
    # Combo-leaning personas: actively want combo lines in the deck.
    "Combo Builder": "leaning",
    "Competitive Closer": "leaning",
    "Consistency Maximizer": "leaning",
    "Efficiency Optimizer": "leaning",

    # Combo-averse personas: prefer organic / durdle / synergy play.
    "Let Me Do My Thing": "averse",
    "Big Moment": "averse",
    "Theme / Vibe": "averse",
    "Pet Card": "averse",

    # Everything else is neutral and gets no combo modifier.
    # (Battlecruiser, Engine Builder, Big Creature / Stompy, Commander Exploiter,
    #  Weird Card Rescuer, Theme Mechanic Inventor, Self-Imposed Constraint Builder,
    #  Curve and Mana Discipline, Power-Level Calibrator, Interaction Controller.)
}


# ---------------------------------------------------------------------------
# Module-level lazy cache for the combo index
# ---------------------------------------------------------------------------
_combo_index_cache: dict[str, Any] | None = None
_combo_index_load_attempted: bool = False


def _default_combo_index_path() -> Path:
    """Where the combo index lives by default."""
    # build_from_collection/combo_scorer.py -> project root is parent.parent
    return Path(__file__).resolve().parent.parent / "data" / "commander_spellbook" / "combo_index.json"


def _load_combo_index_cached(index_path: Path | None = None) -> dict[str, Any] | None:
    """Load the combo index once per process. Returns None if unavailable."""
    global _combo_index_cache, _combo_index_load_attempted
    if _combo_index_cache is not None:
        return _combo_index_cache
    if _combo_index_load_attempted:
        return None
    _combo_index_load_attempted = True
    path = index_path or _default_combo_index_path()
    try:
        from combo_awareness.index_loader import load_combo_index
        _combo_index_cache = load_combo_index(path)
        return _combo_index_cache
    except Exception:
        return None


def _normalize(name: str) -> str:
    """Normalize a card name for matching against combo_index normalized_card_names."""
    try:
        from combo_awareness.normalization import normalize_card_name
        return normalize_card_name(name)
    except Exception:
        return " ".join(str(name).strip().casefold().split())


def _canonical_identity(identity: Any) -> set[str]:
    """Convert a combo identity field ('WUB' or list) to a set."""
    try:
        from combo_awareness.normalization import canonical_identity
        return canonical_identity(identity)
    except Exception:
        if identity is None:
            return set()
        if isinstance(identity, str):
            return {c for c in identity.upper() if c in "WUBRG"}
        result: set[str] = set()
        for item in identity:
            for c in str(item).upper():
                if c in "WUBRG":
                    result.add(c)
        return result


# ---------------------------------------------------------------------------
# Reachable combo discovery
# ---------------------------------------------------------------------------
@dataclass
class ReachableCombo:
    """One combo that fits this commander + has >=2 cards in the user's collection."""
    combo_id: str
    normalized_card_names: list[str]  # all combo pieces, normalized
    owned_normalized_names: set[str]  # subset already in collection
    missing_count: int  # how many pieces are NOT in the collection
    bracket_tag: str = ""
    description: str = ""

    @property
    def is_one_card_away(self) -> bool:
        return self.missing_count == 1

    @property
    def is_complete_in_collection(self) -> bool:
        return self.missing_count == 0


def relevant_combos_for_build(
    *,
    commander_identity: set[str] | None,
    owned_card_names: Iterable[str],
    max_results: int = 50,
    min_owned_pieces: int = 2,
    include_spoilers: bool = False,
    index_path: Path | None = None,
) -> list[ReachableCombo]:
    """Find combos reachable from this commander + collection.

    Returns up to max_results combos sorted by:
      1. owned-piece count desc (closer-to-complete combos first)
      2. total-card-count asc (smaller combos preferred when tied)
    """
    combo_index = _load_combo_index_cached(index_path)
    if not combo_index:
        return []
    combos = combo_index.get("combos") or []
    if not combos:
        return []

    owned_normalized = {_normalize(name) for name in owned_card_names if name}
    identity_set = set(commander_identity or set())

    reachable: list[ReachableCombo] = []
    for combo in combos:
        if combo.get("spoiler") and not include_spoilers:
            continue

        # Color-identity gate: combo identity must be subset of commander identity.
        combo_identity = _canonical_identity(combo.get("identity"))
        if combo_identity and identity_set:
            if not combo_identity.issubset(identity_set):
                continue
        elif combo_identity and not identity_set:
            # Colorless commander accepts only colorless combos.
            continue

        # Collect normalized combo card names.
        norm_names = combo.get("normalized_card_names") or []
        if not norm_names:
            # Fall back to deriving from card_names.
            card_names = combo.get("card_names") or []
            norm_names = [_normalize(n) for n in card_names if n]
        if not norm_names:
            continue

        owned_pieces = {n for n in norm_names if n in owned_normalized}
        if len(owned_pieces) < min_owned_pieces:
            continue

        reachable.append(ReachableCombo(
            combo_id=str(combo.get("id") or ""),
            normalized_card_names=list(norm_names),
            owned_normalized_names=owned_pieces,
            missing_count=len(norm_names) - len(owned_pieces),
            bracket_tag=str(combo.get("bracket_tag") or ""),
            description=str(combo.get("description") or ""),
        ))

    # Sort: most-owned first, then smallest combos first.
    reachable.sort(key=lambda c: (-len(c.owned_normalized_names), len(c.normalized_card_names)))
    return reachable[:max_results]


def build_combo_name_lookup(combos: list[ReachableCombo]) -> dict[str, list[ReachableCombo]]:
    """Build a normalized_card_name -> list[ReachableCombo] index for fast scoring."""
    lookup: dict[str, list[ReachableCombo]] = {}
    for combo in combos:
        for name in combo.normalized_card_names:
            lookup.setdefault(name, []).append(combo)
    return lookup


# ---------------------------------------------------------------------------
# Persona orientation
# ---------------------------------------------------------------------------
def combo_persona_orientation(sub_philosophy: str | None) -> str:
    """Return 'leaning' / 'averse' / 'neutral' for a sub-philosophy selector value."""
    if not sub_philosophy:
        return "neutral"
    try:
        from build_from_collection.philosophy_bias import persona_name_from_selector_value
        persona = persona_name_from_selector_value(sub_philosophy)
    except Exception:
        persona = ""
        text = str(sub_philosophy).strip()
        if " — " in text:
            persona = text.split(" — ", 1)[0].strip()
        elif " - " in text:
            persona = text.split(" - ", 1)[0].strip()
        else:
            persona = text
    return PERSONA_ORIENTATION.get(persona, "neutral")


# ---------------------------------------------------------------------------
# Per-card scoring
# ---------------------------------------------------------------------------
def combo_score_modifier(
    card_name: str,
    lookup: dict[str, list[ReachableCombo]],
    orientation: str,
) -> float:
    """Score delta this card should receive based on combo participation.

    Leaning:
      +1.5 per combo this card appears in
      +2.0 extra per one-card-away combo this card appears in
      +3.0 extra per complete-in-collection combo this card appears in
      capped at +6.0

    Averse:
      -1.5 per combo this card appears in
      -1.0 extra per one-card-away combo this card appears in
      capped at -6.0

    Neutral:
      0
    """
    if orientation == "neutral":
        return 0.0
    if not card_name or not lookup:
        return 0.0
    norm = _normalize(card_name)
    combos = lookup.get(norm) or []
    if not combos:
        return 0.0

    if orientation == "leaning":
        total = 0.0
        for combo in combos:
            total += 1.5
            if combo.is_one_card_away:
                total += 2.0
            elif combo.is_complete_in_collection:
                total += 3.0
        return min(total, 6.0)

    if orientation == "averse":
        total = 0.0
        for combo in combos:
            total -= 1.5
            if combo.is_one_card_away:
                total -= 1.0
        return max(total, -6.0)

    return 0.0


# ---------------------------------------------------------------------------
# Summary line for the report
# ---------------------------------------------------------------------------
def combo_awareness_summary(
    combos: list[ReachableCombo],
    orientation: str,
) -> str:
    """One-line note describing what the combo scorer detected and how it biased the build."""
    if orientation == "neutral":
        return ""
    if not combos:
        if orientation == "leaning":
            return (
                "Combo-aware scoring: no reachable combo lines were detected in your "
                "collection within this commander's color identity (combo scorer had no effect)."
            )
        return (
            "Combo-aware scoring: no reachable combo lines were detected (combo-averse "
            "bias had no effect)."
        )

    complete = sum(1 for c in combos if c.is_complete_in_collection)
    one_away = sum(1 for c in combos if c.is_one_card_away)
    total = len(combos)

    if orientation == "leaning":
        parts = [
            f"Combo-aware scoring (combo-leaning persona): {total} reachable combo line(s) detected"
        ]
        if complete:
            parts.append(f"{complete} already fully owned")
        if one_away:
            parts.append(f"{one_away} one card away")
        parts.append("combo pieces were preferred during picking.")
        return " — ".join(parts)

    # averse
    parts = [
        f"Combo-aware scoring (combo-averse persona): {total} known combo line(s) detected in collection"
    ]
    if complete or one_away:
        parts.append(f"({complete} complete, {one_away} one card away)")
    parts.append("combo pieces were de-prioritized during picking.")
    return " — ".join(parts)
