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
