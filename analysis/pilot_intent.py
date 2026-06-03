"""Pilot intent — the user-declared inputs a decklist can't reveal.

Some guides' "need" lives in the pilot's head, not the 99 cards: which card is a
pet (never cut), what self-imposed rule the deck follows, which odd card is being
rescued, which two themes are being bridged, what overall vibe is intended. The UI
captures these via per-guide intake windows; this module is the single,
presentation-only home for them — it normalizes the inputs off the RuntimeConfig,
exposes the theme list for the dropdowns, and renders the intent for the deck
report and the AI guide.

Boundary: presentation/context only. It changes NO scoring, cut pressure, or the
capped philosophy bias. Pet/rescue cards being "protected" is surfaced as pilot
context; it never rewrites the engine's cut scoring.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def known_themes() -> list[str]:
    """Human-readable Commander themes for the Theme/Hybrid dropdowns.

    Sourced from the engine's archetype taxonomy so the UI dropdowns and the
    engine's own strategy detection stay in sync. Degrades to [] if unavailable.
    """
    try:
        from analysis.strategy_scoring import ARCHETYPE_DEFINITIONS
        return list(ARCHETYPE_DEFINITIONS.keys())
    except Exception:  # noqa: BLE001 - never let a taxonomy import break the UI
        return []


def _as_tuple(value: Any) -> tuple[str, ...]:
    """Coerce a string / list / comma-or-semicolon list into a clean tuple."""
    if value is None:
        return ()
    if isinstance(value, str):
        parts = [p.strip() for p in value.replace(";", ",").split(",")]
        return tuple(p for p in parts if p)
    try:
        return tuple(str(v).strip() for v in value if str(v).strip())
    except TypeError:
        text = str(value).strip()
        return (text,) if text else ()


def _as_text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


@dataclass(frozen=True)
class PilotIntent:
    """Normalized pilot-declared intent for one run."""

    pet_cards: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    rescue_cards: tuple[str, ...] = ()
    hybrid_themes: tuple[str, ...] = ()
    theme_intent: str = ""

    @property
    def is_empty(self) -> bool:
        return not (
            self.pet_cards or self.constraints or self.rescue_cards
            or self.hybrid_themes or self.theme_intent
        )

    @property
    def protected_cards(self) -> tuple[str, ...]:
        """Cards the pilot does not want cut = pet cards + rescue targets, deduped."""
        out: list[str] = []
        for card in (*self.pet_cards, *self.rescue_cards):
            if card and card not in out:
                out.append(card)
        return tuple(out)

    def to_ai_dict(self) -> dict:
        return {
            "pet_cards": list(self.pet_cards),
            "constraints": list(self.constraints),
            "rescue_cards": list(self.rescue_cards),
            "hybrid_themes": list(self.hybrid_themes),
            "theme_intent": self.theme_intent,
        }


def pilot_intent_from_runtime_config(runtime_config: Any) -> PilotIntent:
    """Build PilotIntent from a RuntimeConfig (or any object/dict with the fields)."""
    if runtime_config is None:
        return PilotIntent()

    def field(name: str) -> Any:
        if isinstance(runtime_config, dict):
            return runtime_config.get(name)
        return getattr(runtime_config, name, None)

    return PilotIntent(
        pet_cards=_as_tuple(field("pet_cards")),
        constraints=_as_tuple(field("declared_constraints")),
        rescue_cards=_as_tuple(field("rescue_cards")),
        hybrid_themes=_as_tuple(field("hybrid_themes")),
        theme_intent=_as_text(field("theme_intent")),
    )


def _entry_card_name(entry: Any) -> str:
    for attr_name in ("card_name", "name", "card"):
        value = getattr(entry, attr_name, None)
        if value:
            return str(value).strip()
    return ""


def apply_pilot_protection_to_cuts(possible_cuts: Any, protected_names: Any) -> Any:
    """Move pilot-protected cards out of the cut buckets into protected_from_cut.

    Presentation/intent-honoring only: it respects the pilot's explicit "never cut"
    declaration (pet + rescue cards). It does NOT change any cut/replaceability score
    — it only re-buckets already-scored entries so a protected card is shown as
    protected instead of as a cut candidate. Returns a new summary (never mutates the
    input); returns the input unchanged when there's nothing to move.
    """
    if possible_cuts is None:
        return possible_cuts
    wanted = {str(n).strip().lower() for n in (protected_names or ()) if str(n).strip()}
    if not wanted:
        return possible_cuts

    cut_buckets = (
        "required_cut_candidates", "optional_cut_candidates",
        "manual_review_candidates", "playtest_first_candidates",
    )
    new_buckets: dict[str, list] = {}
    moved: list = []
    for bucket in cut_buckets:
        keep, removed = [], []
        for entry in (getattr(possible_cuts, bucket, None) or []):
            (removed if _entry_card_name(entry).lower() in wanted else keep).append(entry)
        new_buckets[bucket] = keep
        moved.extend(removed)

    if not moved:
        return possible_cuts

    protected = list(getattr(possible_cuts, "protected_from_cut", None) or [])
    seen = {_entry_card_name(e).lower() for e in protected}
    for entry in moved:
        key = _entry_card_name(entry).lower()
        if key and key not in seen:
            protected.append(entry)
            seen.add(key)
    notes = list(getattr(possible_cuts, "notes", None) or [])
    moved_names = sorted({_entry_card_name(e) for e in moved if _entry_card_name(e)})
    if moved_names:
        notes.append(
            "Pilot-protected (never cut): " + ", ".join(moved_names)
            + " — moved out of cut candidates by pilot request."
        )

    import dataclasses
    try:
        return dataclasses.replace(
            possible_cuts, protected_from_cut=protected, notes=notes, **new_buckets
        )
    except Exception:  # noqa: BLE001 - last-resort in-place fallback
        for bucket, value in new_buckets.items():
            setattr(possible_cuts, bucket, value)
        setattr(possible_cuts, "protected_from_cut", protected)
        setattr(possible_cuts, "notes", notes)
        return possible_cuts


def render_pilot_intent_report_block(intent: PilotIntent) -> str:
    """Render the Pilot Intent section for the deck report. Returns '' when empty."""
    if intent is None or intent.is_empty:
        return ""
    lines = [
        "## Pilot Intent",
        "",
        "> What you told the guide before this review — these shape the "
        "recommendations below.",
    ]
    if intent.pet_cards:
        lines.append(f"- Protected pet cards (never cut): {', '.join(intent.pet_cards)}")
    if intent.rescue_cards:
        lines.append(
            "- Rescue target(s) — the deck is being built to support: "
            + ", ".join(intent.rescue_cards)
        )
    for constraint in intent.constraints:
        lines.append(f"- Self-imposed constraint: {constraint}")
    if intent.hybrid_themes:
        lines.append(f"- Hybrid themes to bridge: {' + '.join(intent.hybrid_themes)}")
    if intent.theme_intent:
        lines.append(f"- Theme / vibe goal: {intent.theme_intent}")
    return "\n".join(lines)
