"""Philosophy-aware protected-card explanation wiring helpers for The Dragon's Touch.

Version: v1.1.13

This module attaches philosophy-aware explanation text to protected-card data
that already exists.

Important boundary:
- This module does not decide which cards are protected.
- This module does not score cards.
- This module does not change cut logic.
- This module does not change protected-card detection.
- This module does not add or remove cards.
- This module does not modify existing reports by itself.
- This module only adds philosophy-aware explanatory text to protected-card
  records that already exist.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional

from .protected_language import format_protected_card_note_from_runtime_config
from .runtime_config_mapping import context_from_runtime_config


DEFAULT_CARD_NAME_KEYS = (
    "card_name",
    "name",
    "card",
    "protected_card",
    "candidate",
)

DEFAULT_REASON_KEYS = (
    "reason",
    "protection_reason",
    "protected_reason",
    "explanation",
    "notes",
    "why",
)

DEFAULT_PROTECTION_TYPE_KEYS = (
    "protection_type",
    "protected_type",
    "type",
    "category",
    "role",
)

DEFAULT_CONFIDENCE_KEYS = (
    "confidence",
    "protection_confidence",
)


@dataclass(frozen=True)
class PhilosophyProtectedExplanation:
    """Structured philosophy-aware explanation for an existing protected-card record."""

    card_name: Optional[str]
    selected_lens: str
    parent_philosophy: str
    guide_role: Optional[str]
    language_type: str
    philosophy_note: str
    original_reason: Optional[str] = None
    confidence: Optional[str] = None
    protection_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Optional[str]]:
        return {
            "card_name": self.card_name,
            "selected_lens": self.selected_lens,
            "parent_philosophy": self.parent_philosophy,
            "guide_role": self.guide_role,
            "language_type": self.language_type,
            "philosophy_note": self.philosophy_note,
            "original_reason": self.original_reason,
            "confidence": self.confidence,
            "protection_type": self.protection_type,
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


def infer_protected_language_type(record: Optional[Mapping[str, Any]] = None) -> str:
    """Infer protected-language type from an existing protected-card record.

    This does not decide whether the card should be protected. It only chooses
    which explanation phrasing bucket to use.
    """
    if not record:
        return "standard"

    protection_type = str(_first_present(record, DEFAULT_PROTECTION_TYPE_KEYS) or "").strip().lower()
    confidence = str(_first_present(record, DEFAULT_CONFIDENCE_KEYS) or "").strip().lower()

    if "manual" in protection_type or "review" in protection_type:
        return "manual_review"

    if "low power" in protection_type or "high synergy" in protection_type or "synergy" in protection_type:
        return "low_power_high_synergy"

    if "user" in protection_type or "intent" in protection_type or "pet" in protection_type or "declared" in protection_type:
        return "user_intent"

    if "support" in protection_type or "enabler" in protection_type or "infrastructure" in protection_type:
        return "support"

    if "core" in protection_type or "key" in protection_type or "essential" in protection_type or "critical" in confidence:
        return "core"

    return "standard"


def build_philosophy_protected_explanation(
    record: Optional[Mapping[str, Any]],
    runtime_config: Optional[Mapping[str, Any]] = None,
    *,
    language_type: Optional[str] = None,
    include_original_reason: bool = True,
) -> PhilosophyProtectedExplanation:
    """Build a philosophy-aware explanation for one existing protected-card record."""
    record = record or {}
    context = context_from_runtime_config(runtime_config)

    card_name = _clean_optional(_first_present(record, DEFAULT_CARD_NAME_KEYS))
    original_reason = _clean_optional(_first_present(record, DEFAULT_REASON_KEYS))
    confidence = _clean_optional(_first_present(record, DEFAULT_CONFIDENCE_KEYS))
    protection_type = _clean_optional(_first_present(record, DEFAULT_PROTECTION_TYPE_KEYS))

    selected_language_type = language_type or infer_protected_language_type(record)
    reason = original_reason if include_original_reason else None

    philosophy_note = format_protected_card_note_from_runtime_config(
        runtime_config,
        card_name,
        reason=reason,
        language_type=selected_language_type,
    )

    return PhilosophyProtectedExplanation(
        card_name=card_name,
        selected_lens=context.profile.selected_lens,
        parent_philosophy=context.profile.parent_philosophy,
        guide_role=context.persona_context.get("guide_role"),
        language_type=selected_language_type,
        philosophy_note=philosophy_note,
        original_reason=original_reason,
        confidence=confidence,
        protection_type=protection_type,
    )


def attach_philosophy_protected_explanation(
    record: Mapping[str, Any],
    runtime_config: Optional[Mapping[str, Any]] = None,
    *,
    output_key: str = "philosophy_protected_explanation",
    note_key: str = "philosophy_protected_note",
    language_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Return a copy of a protected-card record with philosophy explanation fields.

    The original record is not mutated.
    """
    result = dict(record)
    explanation = build_philosophy_protected_explanation(
        record,
        runtime_config,
        language_type=language_type,
    )
    result[output_key] = explanation.to_dict()
    result[note_key] = explanation.philosophy_note
    return result


def attach_philosophy_protected_explanations(
    records: Iterable[Mapping[str, Any]],
    runtime_config: Optional[Mapping[str, Any]] = None,
    *,
    output_key: str = "philosophy_protected_explanation",
    note_key: str = "philosophy_protected_note",
    language_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return copies of existing protected-card records with philosophy explanations."""
    return [
        attach_philosophy_protected_explanation(
            record,
            runtime_config,
            output_key=output_key,
            note_key=note_key,
            language_type=language_type,
        )
        for record in records
    ]


def build_protected_explanation_preview(
    runtime_config: Optional[Mapping[str, Any]] = None,
    *,
    sample_card_name: str = "Sample Protected Card",
) -> Dict[str, Any]:
    """Return a small preview payload for diagnostics or future UI previews."""
    sample_record = {
        "card_name": sample_card_name,
        "reason": "This is sample text only. No actual protection decision was made.",
        "confidence": "Medium",
        "protection_type": "Preview",
    }
    explanation = build_philosophy_protected_explanation(sample_record, runtime_config)
    return {
        "status": protected_explanation_wiring_status(),
        "sample_record": sample_record,
        "sample_explanation": explanation.to_dict(),
        "sample_note": explanation.philosophy_note,
    }


def protected_explanation_wiring_status() -> Dict[str, Any]:
    """Return a status object for smoke tests and diagnostics."""
    return {
        "version": "v1.1.13",
        "feature": "Philosophy-Aware Protected Card Explanation Wiring",
        "integration_status": "explanation_helper_only",
        "runtime_behavior_changed": False,
        "decides_protected_cards": False,
        "changes_protected_detection": False,
        "changes_cut_logic": False,
        "changes_cut_scoring": False,
        "adds_or_removes_cards": False,
        "writes_report_files": False,
    }
