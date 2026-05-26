"""Philosophy-aware replacement-direction explanation wiring helpers.

Version: v1.1.14

v1.1.22.1 REPLACEMENT DIRECTION ROLE MAPPING POLISH:
- Treat evasion/trample replacement needs as combat-conversion needs before ramp/mana detection.
- Prevent "More evasion/trample" from using ramp/fixing replacement language.

This module attaches philosophy-aware replacement-direction explanation text to
replacement-need/category data that already exists.

Important boundary:
- This module does not recommend exact cards.
- This module does not select replacement candidates.
- This module does not score replacement candidates.
- This module does not change replacement rankings.
- This module does not add or remove cards.
- This module does not modify existing reports by itself.
- This module only adds philosophy-aware explanatory text to replacement records
  that already exist.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional

from .replacement_language import format_replacement_direction_note_from_runtime_config
from .runtime_config_mapping import context_from_runtime_config


DEFAULT_ROLE_KEYS = (
    "role",
    "replacement_role",
    "replacement_category",
    "category",
    "need",
    "type",
)

DEFAULT_REASON_KEYS = (
    "reason",
    "replacement_reason",
    "explanation",
    "notes",
    "why",
)

DEFAULT_CONFIDENCE_KEYS = (
    "confidence",
    "replacement_confidence",
)

DEFAULT_PRIORITY_KEYS = (
    "priority",
    "replacement_priority",
)

DEFAULT_CARD_NAME_KEYS = (
    "card_name",
    "name",
    "card",
    "cut_card",
    "replace_card",
)


@dataclass(frozen=True)
class PhilosophyReplacementExplanation:
    """Structured philosophy-aware explanation for an existing replacement need."""

    role: Optional[str]
    selected_lens: str
    parent_philosophy: str
    guide_role: Optional[str]
    language_type: str
    philosophy_note: str
    original_reason: Optional[str] = None
    confidence: Optional[str] = None
    priority: Optional[str] = None
    card_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Optional[str]]:
        return {
            "role": self.role,
            "selected_lens": self.selected_lens,
            "parent_philosophy": self.parent_philosophy,
            "guide_role": self.guide_role,
            "language_type": self.language_type,
            "philosophy_note": self.philosophy_note,
            "original_reason": self.original_reason,
            "confidence": self.confidence,
            "priority": self.priority,
            "card_name": self.card_name,
        }


def _first_present(mapping: Mapping[str, Any], keys: Iterable[str]) -> Optional[Any]:
    for key in keys:
        if key in mapping and mapping[key] not in (None, ""):
            return mapping[key]
    return None


def _clean_optional(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _v11221_is_combat_evasion_replacement_role(role: Optional[str]) -> bool:
    """Return True for combat-conversion replacement needs.

    This must run before generic ramp/mana checks because "trample" contains
    the letters "ramp" and can otherwise be misclassified as ramp/fixing.
    """
    text = str(role or "").strip().lower()
    if not text:
        return False
    return any(
        token in text
        for token in (
            "evasion",
            "trample",
            "menace",
            "flying",
            "unblockable",
            "combat evasion",
            "combat conversion",
            "connect in combat",
        )
    )


def _v11221_format_combat_evasion_replacement_note(
    runtime_config: Optional[Mapping[str, Any]],
    role: Optional[str],
    reason: Optional[str] = None,
) -> str:
    """Format safe replacement-direction wording for evasion/trample needs."""
    role_label = str(role or "More evasion/trample").strip()
    note = (
        f"Replacement Direction — {role_label}: Prefer evasion, trample, menace, flying, "
        "unblockable pressure, haste, or team-wide combat support that helps the deck "
        "convert its board into damage. This is a combat-conversion need, not a ramp "
        "or mana-fixing need."
    )
    if reason:
        note += f" {reason}"
    return note


def infer_replacement_language_type(record: Optional[Mapping[str, Any]] = None) -> str:
    """Infer replacement-language type from an existing replacement record.

    This does not choose or score replacement cards. It only chooses which
    explanation phrasing bucket to use.
    """
    if not record:
        return "standard"

    role = str(_first_present(record, DEFAULT_ROLE_KEYS) or "").strip().lower()

    # v1.1.22.1: combat evasion/trample needs must be classified before ramp.
    # Without this guard, "trample" can be caught by broad "ramp" substring logic.
    if _v11221_is_combat_evasion_replacement_role(role):
        return "combat_evasion"

    if any(token in role for token in ("ramp", "mana", "fixing")):
        return "ramp"

    if any(token in role for token in ("draw", "card advantage", "selection")):
        return "draw"

    if any(token in role for token in ("interaction", "removal", "answer", "wipe", "hate")):
        return "interaction"

    if any(token in role for token in ("protection", "protect", "resilience", "recursion")):
        return "protection"

    if any(token in role for token in ("finisher", "closer", "wincon", "win condition", "payoff")):
        return "finisher"

    if any(token in role for token in ("synergy", "engine", "commander", "theme")):
        return "synergy"

    if any(token in role for token in ("curve", "efficiency", "lower", "mana value")):
        return "curve"

    return "standard"


def build_philosophy_replacement_explanation(
    record: Optional[Mapping[str, Any]],
    runtime_config: Optional[Mapping[str, Any]] = None,
    *,
    language_type: Optional[str] = None,
    include_original_reason: bool = True,
) -> PhilosophyReplacementExplanation:
    """Build a philosophy-aware explanation for one existing replacement record."""
    record = record or {}
    context = context_from_runtime_config(runtime_config)

    role = _clean_optional(_first_present(record, DEFAULT_ROLE_KEYS))
    original_reason = _clean_optional(_first_present(record, DEFAULT_REASON_KEYS))
    confidence = _clean_optional(_first_present(record, DEFAULT_CONFIDENCE_KEYS))
    priority = _clean_optional(_first_present(record, DEFAULT_PRIORITY_KEYS))
    card_name = _clean_optional(_first_present(record, DEFAULT_CARD_NAME_KEYS))

    selected_language_type = language_type or infer_replacement_language_type(record)
    reason = original_reason if include_original_reason else None

    if selected_language_type == "combat_evasion":
        philosophy_note = _v11221_format_combat_evasion_replacement_note(
            runtime_config,
            role,
            reason=reason,
        )
    else:
        philosophy_note = format_replacement_direction_note_from_runtime_config(
            runtime_config,
            role,
            reason=reason,
            language_type=selected_language_type,
        )

    return PhilosophyReplacementExplanation(
        role=role,
        selected_lens=context.profile.selected_lens,
        parent_philosophy=context.profile.parent_philosophy,
        guide_role=context.persona_context.get("guide_role"),
        language_type=selected_language_type,
        philosophy_note=philosophy_note,
        original_reason=original_reason,
        confidence=confidence,
        priority=priority,
        card_name=card_name,
    )


def attach_philosophy_replacement_explanation(
    record: Mapping[str, Any],
    runtime_config: Optional[Mapping[str, Any]] = None,
    *,
    output_key: str = "philosophy_replacement_explanation",
    note_key: str = "philosophy_replacement_note",
    language_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Return a copy of a replacement record with philosophy explanation fields.

    The original record is not mutated.
    """
    result = dict(record)
    explanation = build_philosophy_replacement_explanation(
        record,
        runtime_config,
        language_type=language_type,
    )
    result[output_key] = explanation.to_dict()
    result[note_key] = explanation.philosophy_note
    return result


def attach_philosophy_replacement_explanations(
    records: Iterable[Mapping[str, Any]],
    runtime_config: Optional[Mapping[str, Any]] = None,
    *,
    output_key: str = "philosophy_replacement_explanation",
    note_key: str = "philosophy_replacement_note",
    language_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return copies of existing replacement records with philosophy explanations."""
    return [
        attach_philosophy_replacement_explanation(
            record,
            runtime_config,
            output_key=output_key,
            note_key=note_key,
            language_type=language_type,
        )
        for record in records
    ]


def build_replacement_explanation_preview(
    runtime_config: Optional[Mapping[str, Any]] = None,
    *,
    sample_role: str = "More card draw",
) -> Dict[str, Any]:
    """Return a small preview payload for diagnostics or future UI previews."""
    sample_record = {
        "role": sample_role,
        "reason": "This is sample text only. No exact replacement card was recommended.",
        "confidence": "Medium",
        "priority": "Preview",
    }
    explanation = build_philosophy_replacement_explanation(sample_record, runtime_config)
    return {
        "status": replacement_explanation_wiring_status(),
        "sample_record": sample_record,
        "sample_explanation": explanation.to_dict(),
        "sample_note": explanation.philosophy_note,
    }


def replacement_explanation_wiring_status() -> Dict[str, Any]:
    """Return a status object for smoke tests and diagnostics."""
    return {
        "version": "v1.1.14",
        "feature": "Philosophy-Aware Replacement Direction Wiring",
        "integration_status": "explanation_helper_only",
        "runtime_behavior_changed": False,
        "recommends_exact_cards": False,
        "selects_replacement_candidates": False,
        "scores_replacement_candidates": False,
        "changes_replacement_ranking": False,
        "adds_or_removes_cards": False,
        "writes_report_files": False,
    }
