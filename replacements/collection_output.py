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
    quality_gate: str = ""
    swap_guidance: list[str] = field(default_factory=list)
    strong_fit_needs: list[str] = field(default_factory=list)
    philosophy_bias_matches: list[str] = field(default_factory=list)
    philosophy_bias_note: str = ""
    philosophy_bias_explanation: str = ""
    philosophy_replacement_nudge: int = 0

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
    category_strong_fit_counts: list[tuple[str, int]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    quality_gate_notes: list[str] = field(default_factory=list)
    strong_candidates_considered: int = 0
    strong_candidates_accepted: int = 0
    downgraded_to_possible: int = 0
    downgraded_to_shakeup: int = 0
    downgrade_reason_counts: list[tuple[str, int]] = field(default_factory=list)
    replacement_bias_active: bool = False
    replacement_bias_lens: str = "Balanced / Unknown"
    replacement_bias_roles_checked: list[str] = field(default_factory=list)
    replacement_bias_adjusted_cards: int = 0
    replacement_bias_strong_adjusted_cards: int = 0
    replacement_bias_possible_adjusted_cards: int = 0
    replacement_bias_shakeup_adjusted_cards: int = 0
    replacement_bias_candidates_evaluated: int = 0
    replacement_bias_candidates_nudged: int = 0
    replacement_bias_candidates_not_nudged: int = 0
    replacement_bias_candidates_no_match: int = 0
    replacement_bias_candidates_no_deck_evidence: int = 0
    replacement_bias_examples: list[str] = field(default_factory=list)
    replacement_bias_no_match_examples: list[str] = field(default_factory=list)
    replacement_bias_no_evidence_examples: list[str] = field(default_factory=list)

    @property
    def candidates(self) -> list[str]:
        """Backward-compatible string list used by older report code."""
        return [candidate.card_name for candidate in self.strong_candidates]

@dataclass(frozen=True)
class CategoryNeed:
    direct: frozenset[str]
    support: frozenset[str] = frozenset()
    label: str = ""

def _swap_guidance_for_candidate(matched_categories: list[str], role_set: set[str], confidence: str) -> list[str]:
    guidance: list[str] = []
    if not matched_categories:
        return ["No direct swap role identified; treat as a shakeup/playtest idea."]
    for category in matched_categories[:4]:
        cat = category.lower()
        if "token" in cat:
            guidance.append("Review against low-impact token makers or cards meant to create board presence.")
        elif "combat" in cat or "finisher" in cat or "evasion" in cat or "trample" in cat:
            guidance.append("Review against replaceable combat payoffs, standalone beaters, or evasion slots.")
        elif "protection" in cat:
            guidance.append("Review against protection slots, but prefer board/commander protection over self-protection.")
        elif "interaction" in cat or "removal" in cat or "table-stabilizing" in cat:
            guidance.append("Review against flexible interaction slots, not core engine pieces.")
        elif "ramp" in cat or "mana" in cat:
            guidance.append("Review against slower ramp/fixing slots only if curve and role balance support it.")
        elif "draw" in cat or "card advantage" in cat:
            guidance.append("Review against lower-impact card-advantage slots.")
    if confidence.lower().startswith("strong"):
        guidance.append("Do not treat as an automatic swap; confirm it improves the deck's stated plan first.")
    else:
        guidance.append("Pilot review required before treating this as an upgrade.")
    # De-duplicate while preserving order.
    return list(dict.fromkeys(guidance))[:4]

def _source_files_for_card(collection_summary: Any, card_name: str) -> list[str]:
    sources = getattr(collection_summary, "card_sources", {}) or {}
    return list(sources.get(card_name, []) or sources.get(_card_name_key(card_name), []) or [])

def _candidate_reason(matched_needs: list[str], roles: list[str], strategy_bonus: bool, quality_gate: str) -> str:
    if matched_needs:
        base = f"Matches owned-card role need(s): {', '.join(matched_needs[:4])}."
    else:
        base = "Does not directly satisfy a current replacement category."
    if strategy_bonus:
        base += " Has some overlap with the current primary/secondary strategy shape."
    if quality_gate:
        base += f" Quality gate: {quality_gate}."
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
    quality_gate: str = "",
    swap_guidance: list[str] | None = None,
    strong_fit_needs: list[str] | None = None,
    philosophy_bias_matches: list[str] | None = None,
    philosophy_bias_note: str = "",
    philosophy_bias_explanation: str = "",
    philosophy_replacement_nudge: int = 0,
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
        quality_gate=quality_gate,
        swap_guidance=swap_guidance or [],
        strong_fit_needs=strong_fit_needs or [],
        philosophy_bias_matches=philosophy_bias_matches or [],
        philosophy_bias_note=philosophy_bias_note,
        philosophy_bias_explanation=philosophy_bias_explanation,
        philosophy_replacement_nudge=philosophy_replacement_nudge,
    )
