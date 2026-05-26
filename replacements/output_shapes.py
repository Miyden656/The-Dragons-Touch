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

@dataclass(slots=True)
class ReplacementCandidate:
    """Structured v0.9 replacement candidate."""

    card_name: str
    source: str = "unknown"
    owned_status: str = "unknown"
    source_file: str = ""
    replacement_role: str = ""
    replacement_category: str = ""

    supports_primary_strategy: bool = False
    supports_secondary_strategy: bool = False

    commander_synergy_score: int = 0
    role_fit_score: int = 0
    collection_first_rank_score: int = 0
    collection_first_rank_band: str = "Unranked"
    collection_first_rank_reason: str = ""

    budget_status: str = "not_checked"
    estimated_price_if_available: str = ""

    bracket_pressure_flag: bool = False
    combo_risk_flag: bool = False

    collection_match_reason: str = ""
    why_it_fits: str = ""
    why_to_be_careful: str = ""

    confidence: str = "Review"
    recommendation_type: str = "review_candidate"

    matched_needs: list[str] = field(default_factory=list)
    strong_fit_needs: list[str] = field(default_factory=list)
    role_tags: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    swap_guidance: list[str] = field(default_factory=list)

    collection_rank_score: int = 0
    collection_rank_band: str = "Unranked"
    ranking_notes: list[str] = field(default_factory=list)

@dataclass(slots=True)
class ReplacementCandidateSummary:
    """v0.9 replacement-candidate summary."""

    active: bool = True
    engine_version: str = "v0.9.4-dev"
    engine_status: str = "collection_first_ranking_active"
    candidate_source_mode: str = "collection_first_adapter"
    ranking_method: str = "collection_first_deck_fit_v0.9.4"
    exact_ranking_active: bool = True
    full_card_pool_fallback_active: bool = False

    collection_owned_candidates_adapted: int = 0
    strong_candidates_adapted: int = 0
    possible_candidates_adapted: int = 0
    shakeup_candidates_adapted: int = 0

    top_ranked_candidates: list[ReplacementCandidate] = field(default_factory=list)
    candidates: list[ReplacementCandidate] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    safety_boundaries: list[str] = field(default_factory=list)
