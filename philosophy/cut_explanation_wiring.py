"""Philosophy-aware cut explanation wiring helpers for The Dragon's Touch.

Version: v1.1.12

This module is the first controlled behavior-adjacent wiring layer for
philosophy-aware cut explanations.

Important boundary:
- This module does not choose cut candidates.
- This module does not score cards.
- This module does not change cut rankings.
- This module does not remove or add cards.
- This module does not modify existing reports by itself.
- This module only adds philosophy-aware explanatory text to cut data that
  already exists.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional

from .cut_language import (
    format_cut_pressure_note_from_runtime_config,
    get_cut_pressure_language_from_runtime_config,
)
from .runtime_config_mapping import context_from_runtime_config


DEFAULT_CARD_NAME_KEYS = (
    "card_name",
    "name",
    "card",
    "cut",
    "candidate",
)

DEFAULT_REASON_KEYS = (
    "reason",
    "cut_reason",
    "explanation",
    "notes",
    "why",
)

DEFAULT_CONFIDENCE_KEYS = (
    "confidence",
    "cut_confidence",
)

DEFAULT_TYPE_KEYS = (
    "cut_type",
    "type",
    "category",
)


@dataclass(frozen=True)
class PhilosophyCutExplanation:
    """Structured philosophy-aware cut explanation for an existing cut candidate."""

    card_name: Optional[str]
    selected_lens: str
    parent_philosophy: str
    guide_role: Optional[str]
    language_type: str
    philosophy_note: str
    original_reason: Optional[str] = None
    confidence: Optional[str] = None
    cut_type: Optional[str] = None

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
            "cut_type": self.cut_type,
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


def infer_cut_language_type(candidate: Optional[Mapping[str, Any]] = None) -> str:
    """Infer a cut-language type from an existing candidate record.

    This does not change confidence or scoring. It only chooses which phrasing
    bucket to use for the explanation.
    """
    if not candidate:
        return "standard"

    confidence = str(_first_present(candidate, DEFAULT_CONFIDENCE_KEYS) or "").strip().lower()
    cut_type = str(_first_present(candidate, DEFAULT_TYPE_KEYS) or "").strip().lower()

    if "manual" in confidence or "manual" in cut_type or "review" in cut_type:
        return "manual_review"

    if "low" in confidence:
        return "low_confidence"

    if "protected" in cut_type or "conflict" in cut_type:
        return "protected_conflict"

    if "high" in confidence or "strong" in confidence:
        return "strong"

    return "standard"


def build_philosophy_cut_explanation(
    candidate: Optional[Mapping[str, Any]],
    runtime_config: Optional[Mapping[str, Any]] = None,
    *,
    language_type: Optional[str] = None,
    include_original_reason: bool = True,
) -> PhilosophyCutExplanation:
    """Build a philosophy-aware explanation for one existing cut candidate."""
    candidate = candidate or {}
    context = context_from_runtime_config(runtime_config)

    card_name = _clean_optional(_first_present(candidate, DEFAULT_CARD_NAME_KEYS))
    original_reason = _clean_optional(_first_present(candidate, DEFAULT_REASON_KEYS))
    confidence = _clean_optional(_first_present(candidate, DEFAULT_CONFIDENCE_KEYS))
    cut_type = _clean_optional(_first_present(candidate, DEFAULT_TYPE_KEYS))

    selected_language_type = language_type or infer_cut_language_type(candidate)
    reason = original_reason if include_original_reason else None

    philosophy_note = format_cut_pressure_note_from_runtime_config(
        runtime_config,
        card_name,
        reason=reason,
        language_type=selected_language_type,
    )

    return PhilosophyCutExplanation(
        card_name=card_name,
        selected_lens=context.profile.selected_lens,
        parent_philosophy=context.profile.parent_philosophy,
        guide_role=context.persona_context.get("guide_role"),
        language_type=selected_language_type,
        philosophy_note=philosophy_note,
        original_reason=original_reason,
        confidence=confidence,
        cut_type=cut_type,
    )


def attach_philosophy_cut_explanation(
    candidate: Mapping[str, Any],
    runtime_config: Optional[Mapping[str, Any]] = None,
    *,
    output_key: str = "philosophy_cut_explanation",
    note_key: str = "philosophy_cut_note",
    language_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Return a copy of a cut candidate with philosophy explanation fields added.

    The original candidate is not mutated.
    """
    result = dict(candidate)
    explanation = build_philosophy_cut_explanation(
        candidate,
        runtime_config,
        language_type=language_type,
    )
    result[output_key] = explanation.to_dict()
    result[note_key] = explanation.philosophy_note
    return result


def attach_philosophy_cut_explanations(
    candidates: Iterable[Mapping[str, Any]],
    runtime_config: Optional[Mapping[str, Any]] = None,
    *,
    output_key: str = "philosophy_cut_explanation",
    note_key: str = "philosophy_cut_note",
    language_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return copies of existing cut candidates with philosophy explanations added."""
    return [
        attach_philosophy_cut_explanation(
            candidate,
            runtime_config,
            output_key=output_key,
            note_key=note_key,
            language_type=language_type,
        )
        for candidate in candidates
    ]


def build_cut_explanation_preview(
    runtime_config: Optional[Mapping[str, Any]] = None,
    *,
    sample_card_name: str = "Sample Card",
) -> Dict[str, Any]:
    """Return a small preview payload for diagnostics or future UI previews."""
    sample_candidate = {
        "card_name": sample_card_name,
        "reason": "This is sample text only. No actual cut decision was made.",
        "confidence": "Medium",
        "cut_type": "Preview",
    }
    explanation = build_philosophy_cut_explanation(sample_candidate, runtime_config)
    return {
        "status": cut_explanation_wiring_status(),
        "sample_candidate": sample_candidate,
        "sample_explanation": explanation.to_dict(),
        "sample_note": explanation.philosophy_note,
    }


def cut_explanation_wiring_status() -> Dict[str, Any]:
    """Return a status object for smoke tests and diagnostics."""
    return {
        "version": "v1.1.12",
        "feature": "Philosophy-Aware Cut Explanation Wiring",
        "integration_status": "explanation_helper_only",
        "runtime_behavior_changed": False,
        "chooses_cut_candidates": False,
        "changes_cut_scoring": False,
        "changes_cut_ranking": False,
        "adds_or_removes_cards": False,
        "writes_report_files": False,
    }
