"""Replacement candidate data model and collection-first ranking for The Dragon's Touch.

v0.9.4.1-dev hotfix goal:
- Ensure the v0.9 replacement-candidate preview/data-model layer actually consumes
  the already-working Collection Pull Candidates.
- Keep collection-first ranking active without adding full-card-pool fallback.
- Preserve review-candidate language and no automatic swaps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

def _why_to_be_careful(candidate: Any) -> str:
    warnings = _as_list(getattr(candidate, "warnings", None))
    if warnings:
        return str(warnings[0])
    confidence = str(getattr(candidate, "confidence", "Review"))
    if confidence.lower().startswith("strong"):
        return "Still not an automatic swap; confirm it improves the pilot's stated plan first."
    if confidence.lower().startswith("possible"):
        return "Pilot review required before treating this as an upgrade."
    if "shakeup" in confidence.lower():
        return "Experiment only; do not frame as a confirmed upgrade."
    return "Review candidate only; final deckbuilding choice remains with the pilot."

def _v0943_textual_caution_penalty(candidate: ReplacementCandidate) -> int:
    warnings = " | ".join(str(item).lower() for item in (getattr(candidate, "warnings", []) or []))
    careful = str(getattr(candidate, "why_to_be_careful", "") or "").lower()
    text = warnings + " | " + careful

    penalty = 0
    if "strict category gate" in text:
        penalty += 8
    if "broad role overlap" in text:
        penalty += 8
    if "support-only" in text or "support only" in text:
        penalty += 6
    if "self-protection" in text or "generic protection" in text:
        penalty += 5
    if "narrow typal" in text:
        penalty += 4
    if "experiment only" in text:
        penalty += 6

    return penalty
