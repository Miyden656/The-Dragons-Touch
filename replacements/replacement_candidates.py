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


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _candidate_source_file(candidate: Any) -> str:
    sources = _as_list(getattr(candidate, "source_files", None))
    if not sources:
        return ""
    return str(sources[0])


def _candidate_replacement_role(candidate: Any) -> str:
    strong_fit_needs = _as_list(getattr(candidate, "strong_fit_needs", None))
    matched_needs = _as_list(getattr(candidate, "matched_needs", None))
    if strong_fit_needs:
        return str(strong_fit_needs[0])
    if matched_needs:
        return str(matched_needs[0])
    return "manual_review"


def _role_fit_score_from_confidence(confidence: str) -> int:
    text = str(confidence or "").lower()
    if text.startswith("strong"):
        return 80
    if text.startswith("possible"):
        return 50
    if "shakeup" in text:
        return 25
    return 10


def _recommendation_type_from_confidence(confidence: str) -> str:
    text = str(confidence or "").lower()
    if text.startswith("strong"):
        return "collection_owned_strong_review"
    if text.startswith("possible"):
        return "collection_owned_possible_review"
    if "shakeup" in text:
        return "collection_owned_shakeup_experiment"
    return "review_candidate"


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


def _rank_band(score: int) -> str:
    if score >= 95:
        return "Top owned fit"
    if score >= 80:
        return "Strong owned fit"
    if score >= 60:
        return "Possible owned fit"
    if score >= 35:
        return "Shakeup / manual review"
    return "Low-confidence review"


def _score_collection_candidate(candidate: ReplacementCandidate) -> tuple[int, list[str]]:
    score = 0
    notes: list[str] = []

    confidence = candidate.confidence.lower()
    if confidence.startswith("strong"):
        score += 55
        notes.append("Strong collection bucket")
    elif confidence.startswith("possible"):
        score += 35
        notes.append("Possible collection bucket")
    elif "shakeup" in confidence:
        score += 15
        notes.append("Shakeup-only collection bucket")
    else:
        score += 5
        notes.append("Review bucket")

    strong_needs = set(candidate.strong_fit_needs)
    matched_needs = set(candidate.matched_needs)
    if strong_needs:
        bonus = min(25, 10 + 5 * len(strong_needs))
        score += bonus
        notes.append(f"Strong-fit need coverage: {len(strong_needs)}")
    elif matched_needs:
        bonus = min(18, 6 + 3 * len(matched_needs))
        score += bonus
        notes.append(f"Matched need coverage: {len(matched_needs)}")

    role_tags = set(candidate.role_tags)
    high_value_tags = {
        "dragon_card",
        "dragon_typal_support",
        "dragon_copy_value",
        "copy_token_payoff",
        "commander_protection",
        "board_protection_specific",
        "finisher_or_payoff",
        "typal_or_theme_support",
    }
    tag_hits = sorted(role_tags & high_value_tags)
    if tag_hits:
        score += min(18, 4 * len(tag_hits))
        notes.append("Deck-fit role tags: " + ", ".join(tag_hits[:5]))

    if "combo_piece_possible" in role_tags or candidate.combo_risk_flag:
        score -= 6
        candidate.combo_risk_flag = True
        notes.append("Combo-risk/manual-review flag")

    warning_text = " ".join(str(w).lower() for w in candidate.warnings)
    if "strict category gate" in warning_text:
        score -= 10
        notes.append("v0.9.3 strict gate caution")
    if "generic" in warning_text or "support-only" in warning_text:
        score -= 6
        notes.append("Generic/support-only caution")
    if "narrow" in warning_text:
        score -= 4
        notes.append("Narrow-context caution")

    score = max(0, min(100, score))
    return score, notes


def adapt_collection_candidate(candidate: Any) -> ReplacementCandidate:
    """Convert an existing CollectionCandidate-like object into v0.9 shape."""

    confidence = str(getattr(candidate, "confidence", "Review"))
    matched_needs = [str(x) for x in _as_list(getattr(candidate, "matched_needs", None))]
    strong_fit_needs = [str(x) for x in _as_list(getattr(candidate, "strong_fit_needs", None))]
    role_tags = [str(x) for x in _as_list(getattr(candidate, "role_tags", None))]
    warnings = [str(x) for x in _as_list(getattr(candidate, "warnings", None))]

    adapted = ReplacementCandidate(
        card_name=str(getattr(candidate, "card_name", "Unknown card")),
        source="collection",
        owned_status="owned",
        source_file=_candidate_source_file(candidate),
        replacement_role=_candidate_replacement_role(candidate),
        replacement_category=_candidate_replacement_role(candidate),
        supports_primary_strategy=False,
        supports_secondary_strategy=False,
        commander_synergy_score=int(getattr(candidate, "philosophy_replacement_nudge", 0) or 0),
        role_fit_score=_role_fit_score_from_confidence(confidence),
        budget_status="not_checked",
        estimated_price_if_available="",
        bracket_pressure_flag=False,
        combo_risk_flag="combo_piece_possible" in set(role_tags),
        collection_match_reason=str(getattr(candidate, "reason", "")),
        why_it_fits=str(getattr(candidate, "reason", "")),
        why_to_be_careful=_why_to_be_careful(candidate),
        confidence=confidence,
        recommendation_type=_recommendation_type_from_confidence(confidence),
        matched_needs=matched_needs,
        strong_fit_needs=strong_fit_needs,
        role_tags=role_tags,
        warnings=warnings,
        swap_guidance=[str(x) for x in _as_list(getattr(candidate, "swap_guidance", None))],
    )
    score, notes = _score_collection_candidate(adapted)
    adapted.collection_rank_score = score
    adapted.collection_rank_band = _rank_band(score)
    adapted.ranking_notes = notes
    return adapted


def _extract_candidate_buckets(collection_candidates: Any | None) -> tuple[list[Any], list[Any], list[Any]]:
    """Read candidate buckets from the existing collection candidate summary.

    This intentionally supports multiple likely attribute names because prior alpha/dev
    checkpoints used slightly different field names in reports and diagnostics.
    """
    if collection_candidates is None:
        return [], [], []

    strong = _as_list(getattr(collection_candidates, "strong_candidates", None))
    possible = _as_list(getattr(collection_candidates, "possible_candidates", None))
    shakeup = _as_list(getattr(collection_candidates, "shakeup_candidates", None))

    if not strong:
        strong = _as_list(getattr(collection_candidates, "strong_owned_candidates", None))
    if not possible:
        possible = _as_list(getattr(collection_candidates, "possible_owned_candidates", None))
    if not shakeup:
        shakeup = _as_list(getattr(collection_candidates, "shakeup_owned_candidates", None))

    # Last-resort support if the summary stores everything in a generic list.
    if not (strong or possible or shakeup):
        all_candidates = _as_list(getattr(collection_candidates, "candidates", None))
        for item in all_candidates:
            confidence = str(getattr(item, "confidence", "")).lower()
            if confidence.startswith("strong"):
                strong.append(item)
            elif confidence.startswith("possible"):
                possible.append(item)
            elif "shakeup" in confidence:
                shakeup.append(item)

    return strong, possible, shakeup


def build_replacement_candidate_summary(
    collection_candidates: Any | None = None,
    replacement_needs: Any | None = None,
    strategy_summary: Any | None = None,
    runtime_config: Any | None = None,
    philosophy_context: dict[str, Any] | None = None,
) -> ReplacementCandidateSummary:
    """Build the v0.9 candidate summary from existing collection candidates."""

    summary = ReplacementCandidateSummary()
    summary.safety_boundaries.extend([
        "v0.9.4 ranks collection-owned candidates only; it does not add outside-card fallback.",
        "Existing collection candidates remain review candidates, not automatic swaps.",
        "Full-card-pool fallback is not active in v0.9.4.",
        "Budget and price checks are not active unless a later data source supports them.",
        "Combo-risk flags are informational only and do not create combo recommendations.",
    ])

    if replacement_needs is not None:
        priority_categories = [str(x) for x in _as_list(getattr(replacement_needs, "priority_categories", None))]
        if priority_categories:
            summary.notes.append("Replacement needs available: " + ", ".join(priority_categories[:8]))

        need_profile = getattr(replacement_needs, "need_profile", None)
        if need_profile is not None:
            high_priority = [str(x) for x in _as_list(getattr(need_profile, "high_priority_need_names", None))]
            if high_priority:
                summary.notes.append("High-priority need targets available: " + ", ".join(high_priority[:8]))
            summary.notes.append(
                "v0.9.2 need profile available for future ranking: role gaps and strategy-specific needs include evidence/caution metadata."
            )

    if strategy_summary is not None:
        primary = str(getattr(strategy_summary, "primary_strategy", "") or "")
        secondary = str(getattr(strategy_summary, "secondary_strategy", "") or "")
        if primary:
            summary.notes.append(f"Primary strategy context available: {primary}")
        if secondary:
            summary.notes.append(f"Secondary strategy context available: {secondary}")

    strong, possible, shakeup = _extract_candidate_buckets(collection_candidates)

    adapted: list[ReplacementCandidate] = []
    adapted.extend(adapt_collection_candidate(candidate) for candidate in strong)
    adapted.extend(adapt_collection_candidate(candidate) for candidate in possible)
    adapted.extend(adapt_collection_candidate(candidate) for candidate in shakeup)

    adapted.sort(key=lambda c: (c.collection_rank_score, c.role_fit_score, c.card_name.lower()), reverse=True)

    summary.candidates = adapted
    summary.top_ranked_candidates = adapted[:10]
    summary.strong_candidates_adapted = len(strong)
    summary.possible_candidates_adapted = len(possible)
    summary.shakeup_candidates_adapted = len(shakeup)
    summary.collection_owned_candidates_adapted = len(adapted)

    if adapted:
        summary.notes.append(
            f"Adapted and ranked {len(adapted)} collection-owned review candidate(s) into the v0.9.4 replacement candidate model."
        )
    else:
        summary.notes.append(
            "No collection-owned candidates were available to adapt. If Collection Pull Candidates are visible, run v0.9.4.1 wiring hotfix diagnostics."
        )
    return _v0944_apply_confidence_ceilings(summary)


def ensure_replacement_candidate_summary_from_context(context: dict[str, Any]) -> ReplacementCandidateSummary | None:
    """Ensure report rendering has a live v0.9.4 summary.

    Some dev builds created the replacement summary before the collection summary was
    fully available or stored it under the old v0.9.1 state. This function rebuilds
    the summary at report time when it is missing, stale, or empty while collection
    candidates are present.
    """
    existing = context.get("replacement_candidates")
    collection_candidates = context.get("collection_candidates")

    existing_count = int(getattr(existing, "collection_owned_candidates_adapted", 0) or 0) if existing else 0
    existing_version = str(getattr(existing, "engine_version", "") or "") if existing else ""

    if existing and existing_count > 0 and existing_version.startswith("v0.9.4"):
        return existing

    rebuilt = build_replacement_candidate_summary(
        collection_candidates=collection_candidates,
        replacement_needs=context.get("replacement_needs"),
        strategy_summary=context.get("strategy_summary"),
        runtime_config=context.get("runtime_config") or context.get("resolved_config"),
        philosophy_context=context.get("philosophy_context"),
    )
    context["replacement_candidates"] = rebuilt
    return rebuilt

# --- v0.9.4.3 collection-first score population hotfix start ---

def _v0943_confidence_base_score(confidence: str) -> int:
    text = str(confidence or "").lower()
    if text.startswith("strong"):
        return 70
    if text.startswith("possible"):
        return 45
    if "shakeup" in text:
        return 20
    return 10


def _v0943_need_score(candidate: ReplacementCandidate) -> int:
    matched = [str(item).lower() for item in (getattr(candidate, "matched_needs", []) or [])]
    role = str(getattr(candidate, "replacement_role", "") or "").lower()
    category = str(getattr(candidate, "replacement_category", "") or "").lower()
    text_blob = " | ".join(matched + [role, category])

    score = 0

    direct_need_terms = [
        "dragon density",
        "dragon payoff",
        "copy-token payoff",
        "copy token payoff",
        "commander protection",
    ]
    for term in direct_need_terms:
        if term in text_blob:
            score += 8

    if role and role != "manual_review":
        score += 8

    unique_needs = len(set(matched))
    if unique_needs >= 3:
        score += 4
    elif unique_needs == 2:
        score += 3
    elif unique_needs == 1:
        score += 2

    return score


def _v0943_role_tag_score(candidate: ReplacementCandidate) -> int:
    tags = {str(item).lower() for item in (getattr(candidate, "role_tags", []) or [])}
    score = 0

    if "dragon_card" in tags:
        score += 12
    if "dragon_typal_support" in tags:
        score += 10
    if "copy_token_payoff" in tags:
        score += 10
    if "board_protection_specific" in tags:
        score += 10
    if "commander_protection" in tags:
        score += 10
    if "typal_or_theme_support" in tags:
        score += 5
    if "finisher_or_payoff" in tags:
        score += 5
    if "token_production" in tags:
        score += 4
    if "card_advantage" in tags or "card_draw" in tags:
        score += 3
    if "combat_support" in tags:
        score += 2

    if "generic_utility_only" in tags:
        score -= 10
    if "generic_colorless_artifact" in tags:
        score -= 10
    if "support_only" in tags:
        score -= 8
    if "artifact_context_dependent" in tags:
        score -= 6
    if "narrow_typal_requirement" in tags:
        score -= 4

    return score


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


def _v0943_philosophy_score(candidate: ReplacementCandidate) -> int:
    score = int(getattr(candidate, "commander_synergy_score", 0) or 0)
    if score > 8:
        return 8
    if score < -8:
        return -8
    return score


def _v0943_rank_band(score: int, confidence: str) -> str:
    text = str(confidence or "").lower()

    if "shakeup" in text:
        if score >= 40:
            return "Playable Shakeup"
        return "Shakeup / Experiment"

    if score >= 90:
        return "Top Collection Fit"
    if score >= 75:
        return "Strong Collection Fit"
    if score >= 60:
        return "Good Collection Fit"
    if score >= 40:
        return "Possible Collection Fit"
    return "Low Confidence Review"


def _v0943_populate_collection_first_score(candidate: ReplacementCandidate) -> ReplacementCandidate:
    base = _v0943_confidence_base_score(getattr(candidate, "confidence", ""))
    need = _v0943_need_score(candidate)
    role_tags = _v0943_role_tag_score(candidate)
    philosophy = _v0943_philosophy_score(candidate)
    caution = _v0943_textual_caution_penalty(candidate)

    score = max(1, min(100, base + need + role_tags + philosophy - caution))
    band = _v0943_rank_band(score, getattr(candidate, "confidence", ""))

    object.__setattr__(candidate, "collection_first_rank_score", score)
    object.__setattr__(candidate, "collection_first_rank_band", band)
    object.__setattr__(
        candidate,
        "collection_first_rank_reason",
        (
            f"Score {score}: confidence base {base}, need fit +{need}, "
            f"role tags +{role_tags}, philosophy nudge {philosophy:+}, caution -{caution}."
        ),
    )
    return candidate


def _v0943_candidate_sort_key(candidate: ReplacementCandidate) -> tuple[int, int, str]:
    confidence = str(getattr(candidate, "confidence", "") or "").lower()
    if confidence.startswith("strong"):
        bucket = 3
    elif confidence.startswith("possible"):
        bucket = 2
    elif "shakeup" in confidence:
        bucket = 1
    else:
        bucket = 0

    score = int(getattr(candidate, "collection_first_rank_score", 0) or 0)
    name = str(getattr(candidate, "card_name", "") or "")
    return (bucket, score, name)


def build_replacement_candidate_summary(
    collection_candidates: Any | None = None,
    replacement_needs: Any | None = None,
    strategy_summary: Any | None = None,
    runtime_config: Any | None = None,
    philosophy_context: dict[str, Any] | None = None,
) -> ReplacementCandidateSummary:
    summary = ReplacementCandidateSummary()
    summary.engine_version = "v0.9.4-dev"
    summary.engine_status = "collection_first_ranking_active"
    summary.candidate_source_mode = "collection_first_adapter"
    summary.exact_ranking_active = True
    summary.full_card_pool_fallback_active = False

    try:
        object.__setattr__(summary, "ranking_method", "collection_first_deck_fit_v0.9.4")
    except Exception:
        pass

    summary.safety_boundaries.extend([
        "v0.9.4 ranks collection-owned candidates only; it does not add outside-card fallback.",
        "Existing collection candidates remain review candidates, not automatic swaps.",
        "Full-card-pool fallback is not active in v0.9.4.",
        "Budget and price checks are not active unless a later data source supports them.",
        "Combo-risk flags are informational only and do not create combo recommendations.",
    ])

    if replacement_needs is not None:
        priority_categories = list(getattr(replacement_needs, "priority_categories", []) or [])
        if priority_categories:
            summary.notes.append("Replacement needs available: " + ", ".join(priority_categories[:8]))

    if strategy_summary is not None:
        primary = str(getattr(strategy_summary, "primary_strategy", "") or "")
        secondary = str(getattr(strategy_summary, "secondary_strategy", "") or "")
        if primary:
            summary.notes.append(f"Primary strategy context available: {primary}")
        if secondary:
            summary.notes.append(f"Secondary strategy context available: {secondary}")

    if not collection_candidates:
        summary.notes.append("No collection candidate summary was available to adapt.")
        return summary

    strong = list(getattr(collection_candidates, "strong_candidates", []) or [])
    possible = list(getattr(collection_candidates, "possible_candidates", []) or [])
    shakeup = list(getattr(collection_candidates, "shakeup_candidates", []) or [])

    adapted: list[ReplacementCandidate] = []
    adapted.extend(_v0943_populate_collection_first_score(adapt_collection_candidate(candidate)) for candidate in strong)
    adapted.extend(_v0943_populate_collection_first_score(adapt_collection_candidate(candidate)) for candidate in possible)
    adapted.extend(_v0943_populate_collection_first_score(adapt_collection_candidate(candidate)) for candidate in shakeup)

    adapted.sort(key=_v0943_candidate_sort_key, reverse=True)

    summary.candidates = adapted
    summary.strong_candidates_adapted = len(strong)
    summary.possible_candidates_adapted = len(possible)
    summary.shakeup_candidates_adapted = len(shakeup)
    summary.collection_owned_candidates_adapted = len(adapted)

    if adapted:
        summary.notes.append(
            f"Adapted and ranked {len(adapted)} collection-owned review candidate(s) into the v0.9.4.3 replacement candidate model."
        )
    else:
        summary.notes.append("Collection candidate summary existed, but no visible candidates were available to adapt.")

    return summary

# --- v0.9.4.3 collection-first score population hotfix end ---

# v0.9.4.4-dev — Ranking Confidence Ceiling Cleanup
#
# This layer keeps collection-first ranking readable by preventing lower-confidence
# candidates from visually outranking stronger quality-gated candidates.
#
# It does not change candidate discovery, legality, collection loading,
# Combo Awareness, full-card-pool fallback, or automatic swap behavior.

def _v0944_confidence_ceiling(candidate: object) -> int:
    confidence = str(getattr(candidate, "confidence", "") or "").lower()
    recommendation_type = str(getattr(candidate, "recommendation_type", "") or "").lower()

    if confidence.startswith("strong") or "strong" in recommendation_type:
        return 100
    if confidence.startswith("possible") or "possible" in recommendation_type:
        return 79
    if "shakeup" in confidence or "shakeup" in recommendation_type:
        return 49
    return 59


def _v0944_band_for_score_and_confidence(score: int, candidate: object) -> str:
    confidence = str(getattr(candidate, "confidence", "") or "").lower()
    recommendation_type = str(getattr(candidate, "recommendation_type", "") or "").lower()

    is_strong = confidence.startswith("strong") or "strong" in recommendation_type
    is_possible = confidence.startswith("possible") or "possible" in recommendation_type
    is_shakeup = "shakeup" in confidence or "shakeup" in recommendation_type

    if is_strong:
        if score >= 90:
            return "Top Collection Fit"
        if score >= 75:
            return "Strong Collection Fit"
        if score >= 60:
            return "Good Collection Fit"
        return "Review Candidate"

    if is_possible:
        if score >= 70:
            return "Good Possible Fit"
        if score >= 55:
            return "Possible Fit"
        return "Manual Review Fit"

    if is_shakeup:
        if score >= 40:
            return "Best Available Shakeup"
        return "Shakeup / Experiment"

    if score >= 70:
        return "Review Fit"
    if score >= 50:
        return "Manual Review Fit"
    return "Low Confidence Review"


def _v0944_apply_confidence_ceilings(summary: object) -> object:
    candidates = list(getattr(summary, "candidates", []) or [])

    adjusted = 0
    for candidate in candidates:
        current_score = int(getattr(candidate, "collection_first_rank_score", 0) or 0)
        ceiling = _v0944_confidence_ceiling(candidate)

        try:
            setattr(candidate, "collection_first_raw_rank_score", current_score)
        except Exception:
            pass

        capped_score = min(current_score, ceiling)
        if capped_score != current_score:
            adjusted += 1

        try:
            setattr(candidate, "collection_first_rank_score", capped_score)
        except Exception:
            pass

        try:
            setattr(candidate, "collection_first_rank_band", _v0944_band_for_score_and_confidence(capped_score, candidate))
        except Exception:
            pass

        try:
            setattr(candidate, "collection_first_confidence_ceiling", ceiling)
        except Exception:
            pass

    try:
        setattr(summary, "ranking_confidence_ceiling_active", True)
        setattr(summary, "ranking_confidence_ceiling_version", "v0.9.4.4-dev")
        setattr(summary, "ranking_confidence_ceiling_adjusted", adjusted)
    except Exception:
        pass

    notes = list(getattr(summary, "notes", []) or [])
    ceiling_note = (
        "v0.9.4.4 confidence ceiling active: Strong candidates can reach Top Collection Fit; "
        "Possible candidates are capped below Top Collection Fit; Shakeup candidates are capped as experiments."
    )
    if ceiling_note not in notes:
        notes.append(ceiling_note)
    try:
        setattr(summary, "notes", notes)
    except Exception:
        pass

    boundaries = list(getattr(summary, "safety_boundaries", []) or [])
    boundary = "v0.9.4.4 confidence ceilings affect visible ranking presentation only; they do not change candidate discovery or force swaps."
    if boundary not in boundaries:
        boundaries.append(boundary)
    try:
        setattr(summary, "safety_boundaries", boundaries)
    except Exception:
        pass

    def sort_key(candidate: object) -> tuple[int, int, str]:
        confidence = str(getattr(candidate, "confidence", "") or "").lower()
        recommendation_type = str(getattr(candidate, "recommendation_type", "") or "").lower()
        if confidence.startswith("strong") or "strong" in recommendation_type:
            bucket = 3
        elif confidence.startswith("possible") or "possible" in recommendation_type:
            bucket = 2
        elif "shakeup" in confidence or "shakeup" in recommendation_type:
            bucket = 1
        else:
            bucket = 0
        return (bucket, int(getattr(candidate, "collection_first_rank_score", 0) or 0), str(getattr(candidate, "card_name", "")))

    candidates.sort(key=sort_key, reverse=True)
    try:
        setattr(summary, "candidates", candidates)
    except Exception:
        pass

    return summary

# v0.9.4.5.1-dev — Confidence Ceiling Wiring Hotfix
def apply_collection_first_confidence_ceiling(summary: object) -> object:
    """Apply visible confidence ceilings to the active replacement candidate summary."""
    candidates = list(getattr(summary, 'candidates', []) or [])
    adjusted = 0

    def confidence_bucket(candidate: object) -> str:
        confidence = str(getattr(candidate, 'confidence', '') or '').lower()
        recommendation_type = str(getattr(candidate, 'recommendation_type', '') or '').lower()
        if confidence.startswith('strong') or 'strong' in recommendation_type:
            return 'strong'
        if confidence.startswith('possible') or 'possible' in recommendation_type:
            return 'possible'
        if 'shakeup' in confidence or 'shakeup' in recommendation_type:
            return 'shakeup'
        return 'review'

    def ceiling_for(candidate: object) -> int:
        bucket = confidence_bucket(candidate)
        if bucket == 'strong':
            return 100
        if bucket == 'possible':
            return 79
        if bucket == 'shakeup':
            return 49
        return 59

    def band_for(score: int, candidate: object) -> str:
        bucket = confidence_bucket(candidate)
        if bucket == 'strong':
            if score >= 90:
                return 'Top Collection Fit'
            if score >= 75:
                return 'Strong Collection Fit'
            if score >= 60:
                return 'Good Collection Fit'
            return 'Review Candidate'
        if bucket == 'possible':
            if score >= 70:
                return 'Good Possible Fit'
            if score >= 55:
                return 'Possible Fit'
            return 'Manual Review Fit'
        if bucket == 'shakeup':
            if score >= 40:
                return 'Best Available Shakeup'
            return 'Shakeup / Experiment'
        if score >= 70:
            return 'Review Fit'
        if score >= 50:
            return 'Manual Review Fit'
        return 'Low Confidence Review'

    for candidate in candidates:
        current_score = int(getattr(candidate, 'collection_first_rank_score', 0) or 0)
        ceiling = ceiling_for(candidate)
        capped_score = min(current_score, ceiling)
        if capped_score != current_score:
            adjusted += 1
        try:
            setattr(candidate, 'collection_first_raw_rank_score', current_score)
            setattr(candidate, 'collection_first_rank_score', capped_score)
            setattr(candidate, 'collection_first_rank_band', band_for(capped_score, candidate))
            setattr(candidate, 'collection_first_confidence_ceiling', ceiling)
        except Exception:
            pass

    def sort_key(candidate: object) -> tuple[int, int, str]:
        bucket = confidence_bucket(candidate)
        bucket_score = {'strong': 3, 'possible': 2, 'shakeup': 1, 'review': 0}.get(bucket, 0)
        score = int(getattr(candidate, 'collection_first_rank_score', 0) or 0)
        name = str(getattr(candidate, 'card_name', ''))
        return (bucket_score, score, name)

    candidates.sort(key=sort_key, reverse=True)
    try:
        setattr(summary, 'candidates', candidates)
        setattr(summary, 'ranking_confidence_ceiling_active', True)
        setattr(summary, 'ranking_confidence_ceiling_version', 'v0.9.4.5.1-dev')
        setattr(summary, 'ranking_confidence_ceiling_adjusted', adjusted)
    except Exception:
        pass

    notes = list(getattr(summary, 'notes', []) or [])
    note = 'v0.9.4.5.1 confidence ceiling wiring active: Possible candidates are capped below Top Collection Fit and Shakeup candidates remain experimental.'
    if note not in notes:
        notes.append(note)
    try:
        setattr(summary, 'notes', notes)
    except Exception:
        pass

    boundaries = list(getattr(summary, 'safety_boundaries', []) or [])
    boundary = 'v0.9.4.5.1 confidence ceilings affect visible ranking presentation only; they do not change candidate discovery or force swaps.'
    if boundary not in boundaries:
        boundaries.append(boundary)
    try:
        setattr(summary, 'safety_boundaries', boundaries)
    except Exception:
        pass

    return summary


# v0.9.4.6-dev — Dragon Need Semantic Gate Cleanup
#
# This layer prevents broad non-Dragon cards from visually satisfying Dragon-specific
# replacement needs such as More Dragon density and More Dragon payoff.
#
# It does not change collection loading, Combo Awareness, full-card-pool fallback,
# legality, cut logic, or automatic swap behavior.

# v0.9.4.6.2-dev — Dragon Semantic Gate Evidence-Source Hotfix
def _v09462_list_strings(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value]
    return [str(value)]

def _v09462_need_blob(candidate: object) -> str:
    parts: list[str] = []
    for attr in ('replacement_role', 'replacement_category', 'matched_need', 'matched_needs', 'need_name', 'need_category', 'why_it_fits', 'collection_match_reason', 'swap_guidance'):
        parts.extend(_v09462_list_strings(getattr(candidate, attr, None)))
    return ' '.join(parts).lower()

def _v09462_card_identity_blob(candidate: object) -> str:
    parts: list[str] = []
    for attr in ('card_name', 'name', 'type_line', 'oracle_text', 'card_type', 'card_types', 'subtypes', 'role_tags', 'card_role_tags', 'scryfall_type_line', 'scryfall_oracle_text'):
        parts.extend(_v09462_list_strings(getattr(candidate, attr, None)))
    return ' '.join(parts).lower()

def _v09462_has_dragon_need(candidate: object) -> bool:
    blob = _v09462_need_blob(candidate)
    return ('more dragon density' in blob or 'more dragon payoff' in blob or 'dragon density' in blob or 'dragon payoff' in blob or 'dragon typal' in blob or 'dragon_typal' in blob)

def _v09462_is_dragon_valid(candidate: object) -> bool:
    identity_blob = _v09462_card_identity_blob(candidate)
    card_name = str(getattr(candidate, 'card_name', '') or getattr(candidate, 'name', '') or '').lower() 
    if 'dragon_typal' in identity_blob:
        return True
    if 'creature —' in identity_blob and 'dragon' in identity_blob:
        return True
    if 'creature -' in identity_blob and 'dragon' in identity_blob:
        return True
    if '— dragon' in identity_blob or '- dragon' in identity_blob:
        return True
    for marker in ('changeling', 'all creature types', 'all creature type', 'every creature type', 'is every creature type'):
        if marker in identity_blob:
            return True
    for marker in ('dragon spell', 'dragon spells', 'dragon creature', 'dragon creatures', 'dragon you control', 'dragons you control', 'choose dragon', 'chosen type is dragon'):
        if marker in identity_blob:
            return True
    for marker in ('choose a creature type', 'chosen type', 'creatures of the chosen type', 'creature type you chose'):
        if marker in identity_blob:
            return True
    if 'dragon' in card_name or 'draco' in card_name:
        return True
    return False

def apply_dragon_need_semantic_gate(summary: object) -> object:
    candidates = list(getattr(summary, 'candidates', []) or [])
    adjusted = 0
    for candidate in candidates:
        if not _v09462_has_dragon_need(candidate):
            continue
        if _v09462_is_dragon_valid(candidate):
            continue
        adjusted += 1
        old_confidence = str(getattr(candidate, 'confidence', '') or '')
        old_type = str(getattr(candidate, 'recommendation_type', '') or '')
        old_score = int(getattr(candidate, 'collection_first_rank_score', 0) or 0)
        try:
            setattr(candidate, 'dragon_semantic_gate_adjusted', True)
            setattr(candidate, 'dragon_semantic_gate_version', 'v0.9.4.6.2-dev')
            setattr(candidate, 'dragon_semantic_gate_previous_confidence', old_confidence)
            setattr(candidate, 'dragon_semantic_gate_previous_recommendation_type', old_type)
            setattr(candidate, 'dragon_semantic_gate_previous_rank_score', old_score)
            setattr(candidate, 'confidence', 'Manual Review')
            setattr(candidate, 'recommendation_type', 'dragon_need_semantic_review')
            setattr(candidate, 'collection_first_rank_score', min(old_score, 49))
            setattr(candidate, 'collection_first_rank_band', 'Dragon Gate Manual Review')
            setattr(candidate, 'collection_first_confidence_ceiling', 49)
        except Exception:
            pass
        warnings = list(getattr(candidate, 'warnings', []) or [])
        warning = 'v0.9.4.6.2 Dragon semantic gate: card identity evidence does not prove this is an actual Dragon, changeling/all-creature-type card, or explicit Dragon-typal support.'
        if warning not in warnings:
            warnings.append(warning)
        try:
            setattr(candidate, 'warnings', warnings)
        except Exception:
            pass
        careful = str(getattr(candidate, 'why_to_be_careful', '') or '')
        gate_text = 'Dragon semantic gate requires manual review because Dragon-need text alone is not proof of Dragon support.'
        if gate_text not in careful:
            careful = (careful + ' ' + gate_text).strip()
        try:
            setattr(candidate, 'why_to_be_careful', careful)
        except Exception:
            pass
    def sort_key(candidate: object) -> tuple[int, int, str]:
        confidence = str(getattr(candidate, 'confidence', '') or '').lower()
        recommendation_type = str(getattr(candidate, 'recommendation_type', '') or '').lower()
        if bool(getattr(candidate, 'dragon_semantic_gate_adjusted', False)):
            bucket = 0
        elif confidence.startswith('strong') or 'strong' in recommendation_type:
            bucket = 4
        elif confidence.startswith('possible') or 'possible' in recommendation_type:
            bucket = 3
        elif 'shakeup' in confidence or 'shakeup' in recommendation_type:
            bucket = 2
        else:
            bucket = 1
        return (bucket, int(getattr(candidate, 'collection_first_rank_score', 0) or 0), str(getattr(candidate, 'card_name', '')))
    candidates.sort(key=sort_key, reverse=True)
    try:
        setattr(summary, 'candidates', candidates)
        setattr(summary, 'dragon_semantic_gate_active', True)
        setattr(summary, 'dragon_semantic_gate_version', 'v0.9.4.6.2-dev')
        setattr(summary, 'dragon_semantic_gate_adjusted', adjusted)
    except Exception:
        pass
    notes = list(getattr(summary, 'notes', []) or [])
    note = f'v0.9.4.6.2 Dragon semantic gate active: {adjusted} broad non-Dragon Dragon-need candidate(s) moved to manual review using card-identity evidence only.'
    if note not in notes:
        notes.append(note)
    try:
        setattr(summary, 'notes', notes)
    except Exception:
        pass
    boundaries = list(getattr(summary, 'safety_boundaries', []) or [])
    boundary = 'v0.9.4.6.2 Dragon semantic gate uses card identity/type/role evidence only; matched need text does not prove Dragon validity.'
    if boundary not in boundaries:
        boundaries.append(boundary)
    try:
        setattr(summary, 'safety_boundaries', boundaries)
    except Exception:
        pass
    return summary

# v0.9.4.6.3-dev — Dragon Gate Visible Candidate Field Rewrite Hotfix
def _v09463_list_strings(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value]
    return [str(value)]

def _v09463_dragon_gate_candidate_is_adjusted(candidate: object) -> bool:
    if bool(getattr(candidate, 'dragon_semantic_gate_adjusted', False)):
        return True
    if bool(getattr(candidate, 'dragon_gate_visible_rewrite_active', False)):
        return True
    warning_text = ' '.join(_v09463_list_strings(getattr(candidate, 'warnings', []))).lower()
    careful_text = str(getattr(candidate, 'why_to_be_careful', '') or '').lower()
    rec_type = str(getattr(candidate, 'recommendation_type', '') or '').lower()
    return ('dragon semantic gate' in warning_text or 'dragon semantic gate' in careful_text or rec_type == 'dragon_need_semantic_review')

def _v09463_clean_dragon_need_list(value: object) -> list[str]:
    cleaned: list[str] = []
    for item in _v09463_list_strings(value):
        low = item.lower()
        if 'dragon density' in low or 'dragon payoff' in low or low.strip() in {'more dragon density', 'more dragon payoff'}:
            continue
        cleaned.append(item)
    return cleaned

def apply_dragon_gate_visible_field_rewrite(summary: object) -> object:
    candidates = list(getattr(summary, 'candidates', []) or [])
    adjusted = 0
    for candidate in candidates:
        if not _v09463_dragon_gate_candidate_is_adjusted(candidate):
            continue
        adjusted += 1
        old_score = int(getattr(candidate, 'collection_first_rank_score', 0) or 0)
        try:
            setattr(candidate, 'dragon_gate_visible_rewrite_active', True)
            setattr(candidate, 'dragon_gate_visible_rewrite_version', 'v0.9.4.6.3-dev')
            setattr(candidate, 'confidence', 'Manual Review')
            setattr(candidate, 'recommendation_type', 'dragon_need_semantic_review')
            setattr(candidate, 'collection_first_rank_score', min(old_score, 49))
            setattr(candidate, 'collection_first_rank_band', 'Dragon Gate Manual Review')
            setattr(candidate, 'collection_first_confidence_ceiling', 49)
        except Exception:
            pass
        for attr in ('matched_needs', 'strong_fit_roles', 'matched_deck_needs', 'replacement_needs_matched'):
            if hasattr(candidate, attr):
                try:
                    setattr(candidate, attr, _v09463_clean_dragon_need_list(getattr(candidate, attr, [])))
                except Exception:
                    pass
        role = str(getattr(candidate, 'replacement_role', '') or '')
        if 'dragon density' in role.lower() or 'dragon payoff' in role.lower():
            try:
                setattr(candidate, 'replacement_role', 'Manual review — Dragon gate')
            except Exception:
                pass
        why = str(getattr(candidate, 'why_it_fits', '') or '')
        correction = 'Dragon gate correction: do not count this as confirmed Dragon density/payoff without Dragon identity evidence.'
        if ('More Dragon density' in why or 'More Dragon payoff' in why) and correction not in why:
            try:
                setattr(candidate, 'why_it_fits', why + ' ' + correction)
            except Exception:
                pass
        careful = str(getattr(candidate, 'why_to_be_careful', '') or '')
        visible_note = 'Visible-field rewrite applied: this candidate must render as Manual Review, not Strong/Top Collection Fit, for Dragon-specific needs.'
        if visible_note not in careful:
            careful = (careful + ' ' + visible_note).strip()
        try:
            setattr(candidate, 'why_to_be_careful', careful)
        except Exception:
            pass
    def sort_key(candidate: object) -> tuple[int, int, str]:
        if _v09463_dragon_gate_candidate_is_adjusted(candidate):
            bucket = 0
        else:
            confidence = str(getattr(candidate, 'confidence', '') or '').lower()
            recommendation_type = str(getattr(candidate, 'recommendation_type', '') or '').lower()
            if confidence.startswith('strong') or 'strong' in recommendation_type:
                bucket = 4
            elif confidence.startswith('possible') or 'possible' in recommendation_type:
                bucket = 3
            elif 'shakeup' in confidence or 'shakeup' in recommendation_type:
                bucket = 2
            else:
                bucket = 1
        return (bucket, int(getattr(candidate, 'collection_first_rank_score', 0) or 0), str(getattr(candidate, 'card_name', '') or ''))
    candidates.sort(key=sort_key, reverse=True)
    try:
        setattr(summary, 'candidates', candidates)
        setattr(summary, 'dragon_gate_visible_rewrite_active', True)
        setattr(summary, 'dragon_gate_visible_rewrite_version', 'v0.9.4.6.3-dev')
        setattr(summary, 'dragon_gate_visible_rewrite_adjusted', adjusted)
    except Exception:
        pass
    notes = list(getattr(summary, 'notes', []) or [])
    note = f'v0.9.4.6.3 Dragon gate visible rewrite active: {adjusted} candidate(s) forced to Manual Review display after Dragon semantic gate adjustment.'
    if note not in notes:
        notes.append(note)
    try:
        setattr(summary, 'notes', notes)
    except Exception:
        pass
    boundaries = list(getattr(summary, 'safety_boundaries', []) or [])
    boundary = 'v0.9.4.6.3 Dragon gate visible rewrite affects report presentation only; it does not delete candidates or force swaps.'
    if boundary not in boundaries:
        boundaries.append(boundary)
    try:
        setattr(summary, 'safety_boundaries', boundaries)
    except Exception:
        pass
    return summary

# v0.9.6.1-dev — Do-Not-Recommend Reason Field Standardization
def normalize_do_not_recommend_reason(reason=None, *, filtered_reason=None, skip_reason=None, manual_review_reason=None):
    """Return a single stable do-not-recommend reason string for v0.10 Simple View handoff."""
    for value in (reason, filtered_reason, skip_reason, manual_review_reason):
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def build_do_not_recommend_reason(*, color_identity=False, off_plan=False, not_owned=False, budget=False, bracket=False, user_preference=False, low_confidence=False, manual_review=False):
    """Build a conservative, user-safe reason for not recommending a candidate."""
    reasons = []
    if color_identity:
        reasons.append("Filtered because it may not fit the commander's color identity.")
    if off_plan:
        reasons.append("Filtered because it does not clearly support the deck's stated plan.")
    if not_owned:
        reasons.append("Filtered from collection-first recommendations because it was not confirmed as owned.")
    if budget:
        reasons.append("Held back because budget or price impact is not confirmed.")
    if bracket:
        reasons.append("Held back because it may create bracket or table-fit pressure.")
    if user_preference:
        reasons.append("Filtered because it may conflict with the user's stated preferences.")
    if low_confidence:
        reasons.append("Held for manual review because fit confidence is low.")
    if manual_review:
        reasons.append("Held for manual review.")
    return " ".join(reasons).strip()
