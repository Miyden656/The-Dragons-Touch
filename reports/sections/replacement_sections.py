from __future__ import annotations
from replacements.replacement_candidates import ensure_replacement_candidate_summary_from_context
from reports.report_postprocessors import apply_normal_report_postprocessors, _v0952_should_show_exact_preview, _v09551_exact_preview_categories  # v1.5.24 safe postprocessor batch
"""Normal report builder for the modular cleanup version.

Patch Batch 5.1 goal:
- Preserve the normal report as a complete AI handoff packet.
- Include the full decklist.
- Include annotated card-role notes for every main-deck card so another AI can
  reason about cuts, protection, and replacements without losing context.
"""


from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from app_io.output_writer import get_unique_output_path, write_text_file
from reports.strategy_knowledge_sections import build_strategy_knowledge_report_section  # v1.4.13 Strategy Knowledge report handoff
from analysis.deck_building_philosophies import render_philosophy_guide_section as _legacy_render_philosophy_guide_section  # fallback only after v1.1.18
from philosophy.report_section import format_philosophy_guide_section_from_runtime_config  # v1.1.18 live report guide section
# v1.1.22.3 manual-context review clarity: off-plan/manual review examples are context flags, not automatic cuts.
# v1.1.19.1 EXPLANATION WORDING CLEANUP / REPLACEMENT DE-DUP
# - Protected infrastructure entries now use infrastructure-safe wording instead
#   of commander-trigger/copy wording.
# - Replacement-direction explanations remain in Replacement Need Profile and
#   are no longer duplicated in the short Replacement / Addition Needs summary.

from philosophy.cut_explanation_wiring import build_philosophy_cut_explanation  # v1.1.19 live cut explanation wording
from philosophy.protected_explanation_wiring import build_philosophy_protected_explanation  # v1.1.19 live protected explanation wording
from philosophy.replacement_explanation_wiring import build_philosophy_replacement_explanation  # v1.1.19 live replacement-direction wording
from legality.companion_rules import (
    OFFICIAL_COMPANION_CARD_NAMES as COMPANION_CARD_NAMES,
    companion_is_banned_as_companion,
    get_companion_banned_note,
    get_companion_intake_lines,
    get_companion_replacement_filter_note,
    get_companion_restriction_summary,
)


# Companion card names are imported from legality.companion_rules.

def _v1119_replacement_record_from_need_detail(detail: Any) -> dict[str, Any]:
    """Convert an existing replacement need detail into a safe explanation record."""
    evidence = list(getattr(detail, "deck_evidence", []) or [])
    reason_parts = []
    reason = getattr(detail, "reason", "")
    if reason:
        reason_parts.append(str(reason))
    caution = getattr(detail, "caution", "")
    if caution:
        reason_parts.append(str(caution))
    if evidence:
        reason_parts.append("; ".join(str(item) for item in evidence[:3]))
    return {
        "role": getattr(detail, "category", None),
        "reason": "; ".join(part for part in reason_parts if part),
        "priority": getattr(detail, "priority", None),
        "replacement_category": getattr(detail, "category", None),
        "need": getattr(detail, "category", None),
        "type": getattr(detail, "need_type", None),
    }

def _v1119_build_replacement_note(detail_or_category: Any, context: dict[str, Any] | None) -> str:
    """Return v1.1 philosophy-aware replacement-direction text for an existing need."""
    runtime_config = _v1119_runtime_config_for_explanations(context)
    if isinstance(detail_or_category, str):
        record = {"role": detail_or_category, "reason": "Existing replacement need from the current report."}
    else:
        record = _v1119_replacement_record_from_need_detail(detail_or_category)
    try:
        explanation = build_philosophy_replacement_explanation(record, runtime_config)
        return str(getattr(explanation, "philosophy_note", "") or "").strip()
    except Exception:
        return ""

def _replacement_confidence_ceiling_is_active(summary: object) -> bool:
    """Return True when any v0.9.4.x confidence ceiling signal is present."""
    if bool(getattr(summary, 'ranking_confidence_ceiling_active', False)):
        return True

    version = str(getattr(summary, 'ranking_confidence_ceiling_version', '') or '').lower()
    if 'v0.9.4.5' in version or 'confidence' in version:
        return True

    notes = ' '.join(str(item) for item in (getattr(summary, 'notes', []) or [])).lower()
    if 'confidence ceiling' in notes or 'confidence ceilings' in notes:
        return True

    boundaries = ' '.join(str(item) for item in (getattr(summary, 'safety_boundaries', []) or [])).lower()
    if 'confidence ceiling' in boundaries or 'confidence ceilings' in boundaries:
        return True

    for candidate in list(getattr(summary, 'candidates', []) or []):
        if getattr(candidate, 'collection_first_confidence_ceiling', None) is not None:
            return True
        if getattr(candidate, 'collection_first_raw_rank_score', None) is not None:
            return True

    return False

def _replacement_dragon_semantic_gate_is_active(summary: object) -> bool:
    if bool(getattr(summary, "dragon_semantic_gate_active", False)):
        return True
    version = str(getattr(summary, "dragon_semantic_gate_version", "") or "").lower()
    if "v0.9.4.6" in version or "dragon semantic gate" in version:
        return True
    notes = " ".join(str(item) for item in (getattr(summary, "notes", []) or [])).lower()
    if "dragon semantic gate active" in notes:
        return True
    boundaries = " ".join(str(item) for item in (getattr(summary, "safety_boundaries", []) or [])).lower()
    if "dragon semantic gate" in boundaries:
        return True
    for candidate in list(getattr(summary, "candidates", []) or []):
        if getattr(candidate, "dragon_semantic_gate_adjusted", False):
            return True
    return False

def _candidate_dragon_gate_visible_adjusted(candidate: object) -> bool:
    if bool(getattr(candidate, 'dragon_gate_visible_rewrite_active', False)):
        return True
    if bool(getattr(candidate, 'dragon_semantic_gate_adjusted', False)):
        return True
    rec_type = str(getattr(candidate, 'recommendation_type', '') or '').lower()
    careful = str(getattr(candidate, 'why_to_be_careful', '') or '').lower()
    return rec_type == 'dragon_need_semantic_review' or 'visible-field rewrite applied' in careful or 'dragon semantic gate' in careful

def _display_candidate_confidence(candidate: object) -> str:
    if _candidate_dragon_gate_visible_adjusted(candidate):
        return 'Manual Review'
    return str(getattr(candidate, 'confidence', 'Review') or 'Review')

def _display_candidate_recommendation_type(candidate: object) -> str:
    if _candidate_dragon_gate_visible_adjusted(candidate):
        return 'dragon_need_semantic_review'
    return str(getattr(candidate, 'recommendation_type', 'review') or 'review')

def _display_candidate_rank_score(candidate: object) -> int:
    score = int(getattr(candidate, 'collection_first_rank_score', 0) or 0)
    if _candidate_dragon_gate_visible_adjusted(candidate):
        return min(score, 49)
    return score

def _display_candidate_rank_band(candidate: object) -> str:
    if _candidate_dragon_gate_visible_adjusted(candidate):
        return 'Dragon Gate Manual Review'
    return str(getattr(candidate, 'collection_first_rank_band', 'Unranked') or 'Unranked')

def _dragon_gate_visible_rewrite_is_active(summary: object) -> bool:
    if bool(getattr(summary, 'dragon_gate_visible_rewrite_active', False)):
        return True
    notes = ' '.join(str(item) for item in (getattr(summary, 'notes', []) or [])).lower()
    if 'dragon gate visible rewrite active' in notes:
        return True
    for candidate in list(getattr(summary, 'candidates', []) or []):
        if _candidate_dragon_gate_visible_adjusted(candidate):
            return True
    return False

def _dragon_gate_manual_review_candidates(summary: object) -> list[object]:
    return [
        candidate for candidate in list(getattr(summary, 'candidates', []) or [])
        if _candidate_dragon_gate_visible_adjusted(candidate)
    ]

def _v094610_collect_dragon_gate_manual_names(report_text: str) -> set[str]:
    names: set[str] = set()

    top_start = report_text.find("### Top Ranked Collection-First Candidates")
    top_end = report_text.find("### Safety Boundaries", top_start) if top_start != -1 else -1
    top_section = report_text[top_start:top_end] if top_start != -1 and top_end != -1 else ""

    for block in top_section.split("\n#### "):
        if "Dragon Gate Manual Review" not in block:
            continue
        block_lines = block.splitlines()
        if not block_lines:
            continue
        first_line = block_lines[0].strip().lstrip("#").strip()
        if first_line and not first_line.startswith("Top Ranked"):
            names.add(first_line)

    manual_start = report_text.find("### Dragon Gate Manual Review Candidates")
    manual_end = report_text.find("### Possible Owned Candidates", manual_start) if manual_start != -1 else -1
    if manual_end == -1 and manual_start != -1:
        manual_end = report_text.find("### Collection Gaps", manual_start)
    manual_section = report_text[manual_start:manual_end] if manual_start != -1 and manual_end != -1 else (report_text[manual_start:] if manual_start != -1 else "")

    for block in manual_section.split("\n### "):
        block_lines = block.splitlines()
        if not block_lines:
            continue
        first_line = block_lines[0].strip().lstrip("#").strip()
        if not first_line:
            continue
        if first_line.startswith("Dragon Gate Manual Review"):
            continue
        if first_line.startswith(">"):
            continue
        if len(first_line) <= 80:
            names.add(first_line)

    return names

def _v095_full_pool_category_for_need(need: str) -> str:
    low = need.lower()
    if "ramp" in low or "mana" in low:
        return "More ramp / mana development"
    if "draw" in low or "card advantage" in low or "refill" in low:
        return "More card draw / card advantage"
    if "removal" in low or "interaction" in low:
        return "More targeted interaction"
    if "wipe" in low or "board clear" in low:
        return "More board wipes"
    if "protection" in low or "protect" in low:
        return "More protection"
    if "dragon" in low:
        return "More confirmed Dragon support"
    if "combo" in low:
        return "Combo support only if user opts in"
    if "token" in low:
        return "More token support"
    if "recursion" in low or "graveyard" in low:
        return "More recursion"
    if "finisher" in low or "win" in low:
        return "More finishers"
    return "Better role coverage"

def _v095_build_full_pool_preview_lines(context: dict) -> list[str]:
    summary = (
        context.get("replacement_candidates")
        or context.get("replacement_candidate_summary")
        or context.get("replacement_summary")
        or context.get("replacement_candidate_engine")
    )

    lines: list[str] = []
    lines.append("## Full-Card-Pool Fallback Preview")
    lines.append("")
    lines.append("> v0.9.5 preview: This section is informational only. It does not override collection-first recommendations and does not create automatic swaps.")
    lines.append("> Use this when the owned-card pool is thin, overly gated, or missing a clear role. Owned cards remain preferred when they are real fits.")
    lines.append("")

    if not summary:
        lines.append("- Full-card-pool fallback active: Preview unavailable — replacement candidate summary was not found.")
        lines.append("- Safety boundary: No outside-card recommendations were generated.")
        lines.append("")
        return lines

    collection_weak = _v095_collection_first_pool_is_weak(summary)
    lines.append(f"- Full-card-pool fallback preview active: {'Yes' if collection_weak else 'No'}")
    lines.append("- Fallback mode: preview only")
    lines.append("- Recommendation authority: collection-first remains primary")
    lines.append("- Automatic swaps: No")
    lines.append("")

    if not collection_weak:
        lines.append("Collection-first candidates appear sufficient for this pass, so full-card-pool fallback stays dormant.")
        lines.append("")
        return lines

    needs = _v095_get_replacement_needs_from_context(context)
    if not needs:
        lines.append("No replacement needs were available to map into fallback categories.")
        lines.append("")
        return lines

    lines.append("### Fallback Categories to Explore Later")
    for need in needs:
        category = _v095_full_pool_category_for_need(need)
        lines.append(f"- {category} — triggered by: {need}")

    lines.append("")
    lines.append("### Safety Boundaries")
    lines.append("- These are replacement categories, not exact card recommendations.")
    lines.append("- Full-card-pool card names should be added in a later patch only after role matching and safety gates are stable.")
    lines.append("- Combo-related outside-card suggestions remain informational unless combo optimization is explicitly enabled.")
    lines.append("")

    return lines

def _v0951_clean_need_text(value: object) -> list[str]:
    cleaned: list[str] = []

    def add(text: object) -> None:
        item = str(text or "").strip()
        if not item:
            return
        if item.startswith("ReplacementNeedSummary("):
            return
        if item.startswith("[") and "ReplacementNeedSummary(" in item:
            return
        if item not in cleaned:
            cleaned.append(item)

    if value is None:
        return cleaned

    # Dataclass/object style ReplacementNeedSummary support.
    for attr in ("priority_categories", "notes", "role_gap_summary", "strategy_need_summary", "need_details"):
        if hasattr(value, attr):
            attr_value = getattr(value, attr, None)
            if isinstance(attr_value, dict):
                for k, v in attr_value.items():
                    add(k)
                    if isinstance(v, (list, tuple, set)):
                        for item in v:
                            add(item)
                    else:
                        add(v)
            elif isinstance(attr_value, (list, tuple, set)):
                for item in attr_value:
                    add(item)
            else:
                add(attr_value)

    if cleaned:
        return cleaned

    if isinstance(value, dict):
        for key in ("priority_categories", "notes", "role_gap_summary", "strategy_need_summary", "need_details"):
            attr_value = value.get(key)
            if isinstance(attr_value, (list, tuple, set)):
                for item in attr_value:
                    add(item)
            elif attr_value:
                add(attr_value)
        return cleaned

    if isinstance(value, (list, tuple, set)):
        for item in value:
            for sub in _v0951_clean_need_text(item):
                add(sub)
        return cleaned

    add(value)
    return cleaned

def _v0951_full_pool_category_for_need(need: str) -> str:
    low = need.lower()
    if "no urgent" in low or "no active replacement" in low:
        return "General role coverage only if the pilot wants outside-card options"
    if "ramp" in low or "mana" in low:
        return "More ramp / mana development"
    if "draw" in low or "card advantage" in low or "refill" in low:
        return "More card draw / card advantage"
    if "removal" in low or "interaction" in low:
        return "More targeted interaction"
    if "wipe" in low or "board clear" in low:
        return "More board wipes"
    if "protection" in low or "protect" in low:
        return "More protection"
    if "dragon" in low:
        return "More confirmed Dragon support"
    if "combo" in low:
        return "Combo support only if user opts in"
    if "token" in low:
        return "More token support"
    if "recursion" in low or "graveyard" in low:
        return "More recursion"
    if "finisher" in low or "win" in low:
        return "More finishers"
    if "role" in low or "coverage" in low:
        return "Better role coverage"
    return "Better role coverage"

def _v0952_exact_preview_pool() -> dict[str, list[str]]:
    # Conservative, role-based examples only. These are not automatic swaps.
    return {
        "More ramp / mana development": [
            "Arcane Signet",
            "Nature's Lore",
            "Three Visits",
            "Farseek",
            "Talisman cycle / Signet cycle",
        ],
        "More card draw / card advantage": [
            "Guardian Project",
            "Beast Whisperer",
            "Return of the Wildspeaker",
            "Rishkar's Expertise",
            "Esper Sentinel",
        ],
        "More targeted interaction": [
            "Beast Within",
            "Generous Gift",
            "Swords to Plowshares",
            "Chaos Warp",
            "Assassin's Trophy",
        ],
        "More board wipes": [
            "Blasphemous Act",
            "Farewell",
            "Austere Command",
            "Toxic Deluge",
            "Cyclonic Rift",
        ],
        "More protection": [
            "Heroic Intervention",
            "Teferi's Protection",
            "Flawless Maneuver",
            "Tamiyo's Safekeeping",
            "Swiftfoot Boots",
        ],
        "More confirmed Dragon support": [
            "Dragon Tempest",
            "Scourge of Valkas",
            "Lathliss, Dragon Queen",
            "Sarkhan's Triumph",
            "Crucible of Fire",
        ],
        "More token support": [
            "Parallel Lives",
            "Anointed Procession",
            "Second Harvest",
            "Adrix and Nev, Twincasters",
            "Mondrak, Glory Dominus",
        ],
        "More recursion": [
            "Eternal Witness",
            "Regrowth",
            "Victimize",
            "Reanimate",
            "Sevinne's Reclamation",
        ],
        "More finishers": [
            "Craterhoof Behemoth",
            "Overwhelming Stampede",
            "Finale of Devastation",
            "Torment of Hailfire",
            "Triumph of the Hordes",
        ],
        "Better role coverage": [
            "Flexible removal",
            "Additional card draw",
            "Efficient ramp",
            "Protection for key engine pieces",
            "A cleaner finisher",
        ],
        "General role coverage only if the pilot wants outside-card options": [
            "Flexible removal",
            "Additional card draw",
            "Efficient ramp",
            "Protection for key engine pieces",
            "A cleaner finisher",
        ],
        "Combo support only if user opts in": [
            "No exact combo card examples shown unless combo optimization is explicitly enabled",
        ],
    }

def _v0952_candidate_examples_for_category(category: str) -> list[str]:
    pool = _v0952_exact_preview_pool()
    if category in pool:
        return pool[category]
    low = category.lower()
    if "dragon" in low:
        return pool["More confirmed Dragon support"]
    if "ramp" in low or "mana" in low:
        return pool["More ramp / mana development"]
    if "draw" in low or "advantage" in low:
        return pool["More card draw / card advantage"]
    if "interaction" in low or "removal" in low:
        return pool["More targeted interaction"]
    if "protection" in low:
        return pool["More protection"]
    if "token" in low:
        return pool["More token support"]
    if "recursion" in low or "graveyard" in low:
        return pool["More recursion"]
    if "finisher" in low or "win" in low:
        return pool["More finishers"]
    return pool["Better role coverage"]

def _v0952_insert_exact_full_pool_preview(report_text: str) -> str:
    if "### Exact Full-Pool Candidate Preview" in report_text:
        return report_text
    if not _v0952_should_show_exact_preview(report_text):
        return report_text

    start = report_text.find("## Full-Card-Pool Fallback Preview")
    end = report_text.find("\n## ", start + 1)
    if start == -1:
        return report_text
    section_end = end if end != -1 else len(report_text)
    section = report_text[start:section_end]

    category_lines = []
    in_categories = False
    for line in section.splitlines():
        if line.strip() == "### Fallback Categories to Explore Later":
            in_categories = True
            continue
        if in_categories and line.startswith("### "):
            break
        if in_categories and line.startswith("- "):
            category = line[2:].split(" — triggered by:", 1)[0].strip()
            if category and category not in category_lines:
                category_lines.append(category)

    if not category_lines:
        category_lines = ["Better role coverage"]

    preview_lines: list[str] = []
    preview_lines.append("### Exact Full-Pool Candidate Preview")
    preview_lines.append("> v0.9.5.2 preview: These are outside-card examples by role, not owned-card claims, not upgrade guarantees, and not automatic swaps.")
    preview_lines.append("> Check color identity, budget, bracket, collection availability, and pilot intent before treating any card as a real recommendation.")
    preview_lines.append("")

    for category in category_lines[:6]:
        preview_lines.append(f"#### {category}")
        for card in _v0952_candidate_examples_for_category(category)[:5]:
            preview_lines.append(f"- {card}")
        preview_lines.append("")

    preview_lines.append("### Exact Preview Safety Boundaries")
    preview_lines.append("- These card names are examples for exploration, not finalized replacement recommendations.")
    preview_lines.append("- Collection-first remains primary when owned cards are real fits.")
    preview_lines.append("- Automatic swaps: No.")
    preview_lines.append("- Combo-card examples stay suppressed unless combo optimization is explicitly enabled.")
    preview_lines.append("")

    insert_text = "\n".join(preview_lines)
    # Insert before Safety Boundaries inside the fallback preview when possible.
    safety = section.find("### Safety Boundaries")
    if safety != -1:
        new_section = section[:safety] + insert_text + "\n" + section[safety:]
    else:
        new_section = section.rstrip() + "\n\n" + insert_text

    return report_text[:start] + new_section + report_text[section_end:]

def _v0953_card_color_identity_map() -> dict[str, set[str]]:
    # Conservative examples used by v0.9.5.2 exact preview.
    # Empty set means colorless or effectively color-identity flexible for the preview.
    return {
        "Arcane Signet": set(),
        "Nature's Lore": {"G"},
        "Three Visits": {"G"},
        "Farseek": {"G"},
        "Talisman cycle / Signet cycle": set(),

        "Guardian Project": {"G"},
        "Beast Whisperer": {"G"},
        "Return of the Wildspeaker": {"G"},
        "Rishkar's Expertise": {"G"},
        "Esper Sentinel": {"W"},

        "Beast Within": {"G"},
        "Generous Gift": {"W"},
        "Swords to Plowshares": {"W"},
        "Chaos Warp": {"R"},
        "Assassin's Trophy": {"B", "G"},

        "Blasphemous Act": {"R"},
        "Farewell": {"W"},
        "Austere Command": {"W"},
        "Toxic Deluge": {"B"},
        "Cyclonic Rift": {"U"},

        "Heroic Intervention": {"G"},
        "Teferi's Protection": {"W"},
        "Flawless Maneuver": {"W"},
        "Tamiyo's Safekeeping": {"G"},
        "Swiftfoot Boots": set(),

        "Dragon Tempest": {"R"},
        "Scourge of Valkas": {"R"},
        "Lathliss, Dragon Queen": {"R"},
        "Sarkhan's Triumph": {"R"},
        "Crucible of Fire": {"R"},

        "Parallel Lives": {"G"},
        "Anointed Procession": {"W"},
        "Second Harvest": {"G"},
        "Adrix and Nev, Twincasters": {"G", "U"},
        "Mondrak, Glory Dominus": {"W"},

        "Eternal Witness": {"G"},
        "Regrowth": {"G"},
        "Victimize": {"B"},
        "Reanimate": {"B"},
        "Sevinne's Reclamation": {"W"},

        "Craterhoof Behemoth": {"G"},
        "Overwhelming Stampede": {"G"},
        "Finale of Devastation": {"G"},
        "Torment of Hailfire": {"B"},
        "Triumph of the Hordes": {"G"},

        "Flexible removal": set(),
        "Additional card draw": set(),
        "Efficient ramp": set(),
        "Protection for key engine pieces": set(),
        "A cleaner finisher": set(),
        "No exact combo card examples shown unless combo optimization is explicitly enabled": set(),
    }

def _v0953_extract_commander_color_identity(report_text: str) -> set[str] | None:
    for line in report_text.splitlines():
        if line.startswith("- Commander color identity:"):
            raw = line.split(":", 1)[1].strip()
            if not raw or raw.lower() in {"none", "colorless", "c"}:
                return set()
            parts = [part.strip().upper() for part in raw.replace("/", " ").replace(",", " ").split()]
            colors = {part for part in parts if part in {"W", "U", "B", "R", "G"}}
            return colors
    return None

def _v0953_card_is_color_legal(card_name: str, commander_identity: set[str] | None) -> tuple[bool, str]:
    if commander_identity is None:
        return True, "color identity not verified"
    card_map = _v0953_card_color_identity_map()
    card_identity = card_map.get(card_name)
    if card_identity is None:
        return True, "color identity not verified"
    if card_identity.issubset(commander_identity):
        return True, "color identity verified"
    return False, "filtered by commander color identity"

def _v0953_rebuild_exact_preview_with_color_guard(report_text: str) -> str:
    start = report_text.find("### Exact Full-Pool Candidate Preview")
    if start == -1:
        return report_text

    section_end_marker = "### Exact Preview Safety Boundaries"
    safety_start = report_text.find(section_end_marker, start)
    if safety_start == -1:
        return report_text

    end = report_text.find("\n## ", start)
    if end == -1:
        end = len(report_text)

    exact_body = report_text[start:safety_start]
    safety_and_after = report_text[safety_start:end]

    commander_identity = _v0953_extract_commander_color_identity(report_text)
    commander_label = "not verified" if commander_identity is None else ("/".join(sorted(commander_identity)) if commander_identity else "Colorless")

    lines: list[str] = []
    lines.append("### Exact Full-Pool Candidate Preview")
    lines.append("> v0.9.5.3 preview: These are outside-card examples by role, not owned-card claims, not upgrade guarantees, and not automatic swaps.")
    lines.append("> Color identity is filtered when the commander's color identity is available from the report.")
    lines.append(f"> Commander color identity check: {commander_label}.")
    lines.append("")

    current_category = None
    categories: list[tuple[str, list[str]]] = []
    for line in exact_body.splitlines():
        if line.startswith("#### "):
            current_category = line[5:].strip()
            categories.append((current_category, []))
            continue
        if line.startswith("- ") and current_category and categories:
            card = line[2:].strip()
            # Skip safety/boundary list lines accidentally captured.
            if card and not card.lower().startswith(("these card names", "collection-first", "automatic swaps", "combo-card")):
                categories[-1][1].append(card)

    filtered_any = False
    unverified_any = False

    for category, cards in categories:
        legal_cards: list[tuple[str, str]] = []
        for card in cards:
            ok, status = _v0953_card_is_color_legal(card, commander_identity)
            if not ok:
                filtered_any = True
                continue
            if status == "color identity not verified":
                unverified_any = True
            legal_cards.append((card, status))

        if not legal_cards:
            lines.append(f"#### {category}")
            lines.append("- No exact examples shown after color-identity filtering.")
            lines.append("")
            continue

        lines.append(f"#### {category}")
        for card, status in legal_cards[:5]:
            lines.append(f"- {card} ({status})")
        lines.append("")

    # Rebuild safety section with explicit v0.9.5.3 guard text.
    safety_lines = []
    safety_lines.append("### Exact Preview Safety Boundaries")
    safety_lines.append("- These card names are examples for exploration, not finalized replacement recommendations.")
    safety_lines.append("- Collection-first remains primary when owned cards are real fits.")
    safety_lines.append("- Automatic swaps: No.")
    safety_lines.append("- Exact preview cards are not claimed as owned or collection-sourced.")
    safety_lines.append("- Color identity filtering is applied when the report exposes commander color identity.")
    if filtered_any:
        safety_lines.append("- Some exact examples were filtered out by commander color identity.")
    if unverified_any:
        safety_lines.append("- Some exact examples are marked color identity not verified and require pilot/manual review.")
    safety_lines.append("- Combo-card examples stay suppressed unless combo optimization is explicitly enabled.")
    safety_lines.append("")

    new_section = "\n".join(lines + safety_lines)
    return report_text[:start] + new_section + report_text[end:]

def _v0954_card_pressure_tags(card_name: str) -> list[str]:
    tags: list[str] = []

    high_budget = {
        "Three Visits",
        "Esper Sentinel",
        "Cyclonic Rift",
        "Teferi's Protection",
        "Flawless Maneuver",
        "Parallel Lives",
        "Anointed Procession",
        "Mondrak, Glory Dominus",
        "Craterhoof Behemoth",
        "Finale of Devastation",
        "Reanimate",
        "Toxic Deluge",
        "Assassin's Trophy",
        "Heroic Intervention",
    }

    bracket_pressure = {
        "Cyclonic Rift",
        "Teferi's Protection",
        "Esper Sentinel",
        "Toxic Deluge",
        "Reanimate",
        "Finale of Devastation",
        "Craterhoof Behemoth",
        "Torment of Hailfire",
        "Triumph of the Hordes",
        "Flawless Maneuver",
    }

    salt_or_table_fit = {
        "Cyclonic Rift",
        "Triumph of the Hordes",
        "Torment of Hailfire",
        "Craterhoof Behemoth",
        "Toxic Deluge",
        "Reanimate",
        "Teferi's Protection",
    }

    if card_name in high_budget:
        tags.append("budget not checked / may be expensive")
    else:
        tags.append("budget not checked")

    if card_name in bracket_pressure:
        tags.append("bracket pressure review")
    else:
        tags.append("bracket not checked")

    if card_name in salt_or_table_fit:
        tags.append("confirm table fit")
    else:
        tags.append("table fit not checked")

    return tags

def _v0954_add_budget_bracket_labels_to_exact_preview(report_text: str) -> str:
    start = report_text.find("### Exact Full-Pool Candidate Preview")
    if start == -1:
        return report_text

    section_end_marker = "### Exact Preview Safety Boundaries"
    safety_start = report_text.find(section_end_marker, start)
    if safety_start == -1:
        return report_text

    exact_body = report_text[start:safety_start]
    safety_end = report_text.find("\n## ", safety_start)
    if safety_end == -1:
        safety_end = len(report_text)

    lines: list[str] = []
    for line in exact_body.splitlines():
        if line.startswith("- ") and "(" in line and ")" in line:
            card_name = line[2:].split("(", 1)[0].strip()
            if card_name and not card_name.lower().startswith(("these card names", "collection-first", "automatic swaps", "combo-card")):
                if "budget not checked" not in line and "bracket" not in line and "table fit" not in line and "confirm table fit" not in line:
                    tags = "; ".join(_v0954_card_pressure_tags(card_name))
                    line = line.rstrip() + f" — {tags}"
        lines.append(line)

    rebuilt_exact_body = "\n".join(lines)

    safety_block = report_text[safety_start:safety_end]
    additions = []
    if "Budget status: not checked" not in safety_block:
        additions.append("- Budget status: not checked for exact full-pool examples.")
    if "Bracket/table-fit status: review required" not in safety_block:
        additions.append("- Bracket/table-fit status: review required before recommending exact examples.")
    if "Price data source: none" not in safety_block:
        additions.append("- Price data source: none in this patch.")
    if "Power-level guarantee: none" not in safety_block:
        additions.append("- Power-level guarantee: none; these remain exploratory examples.")

    if additions:
        safety_lines = safety_block.splitlines()
        insert_at = len(safety_lines)
        for i, existing in enumerate(safety_lines):
            if existing.strip() == "":
                insert_at = i
                break
        safety_lines = safety_lines[:insert_at] + additions + safety_lines[insert_at:]
        safety_block = "\n".join(safety_lines)

    return report_text[:start] + rebuilt_exact_body + safety_block + report_text[safety_end:]

def _v0955_need_to_exact_preview_category(need_text: str) -> str:
    low = str(need_text or "").lower()

    if "table-stabilizing" in low or "interaction" in low or "removal" in low:
        return "More targeted interaction"
    if "board wipe" in low or "wipe" in low or "clear" in low:
        return "More board wipes"
    if "board protection" in low or "protection" in low or "protect" in low:
        return "More protection"
    if "evasion" in low or "trample" in low:
        return "More finishers"
    if "combat finisher" in low or "combat payoff" in low or "finisher" in low:
        return "More finishers"
    if "token" in low or "go-wide" in low:
        return "More token support"
    if "draw" in low or "card advantage" in low or "refill" in low:
        return "More card draw / card advantage"
    if "ramp" in low or "mana" in low or "land" in low:
        return "More ramp / mana development"
    if "recursion" in low or "graveyard" in low:
        return "More recursion"
    if "dragon" in low:
        return "More confirmed Dragon support"
    if "combo" in low:
        return "Combo support only if user opts in"
    if "no urgent" in low or "general" in low or "broad" in low or "role coverage" in low:
        return "General role coverage only if the pilot wants outside-card options"
    return "Better role coverage"

def _v0955_extract_report_need_lines(report_text: str) -> list[str]:
    needs: list[str] = []

    # Prefer explicit Replacement / Addition Needs section.
    start = report_text.find("## Replacement / Addition Needs")
    if start != -1:
        end = report_text.find("\n## ", start + 1)
        section = report_text[start:end if end != -1 else len(report_text)]
        for line in section.splitlines():
            if not line.startswith("- "):
                continue
            item = line[2:].strip()
            if not item or item.lower().startswith("note:"):
                continue
            if item not in needs:
                needs.append(item)

    # Fallback to Replacement Need Profile role/strategy summaries.
    if not needs:
        for heading in ("### Role Gap Summary", "### Strategy-Specific Need Summary"):
            start = report_text.find(heading)
            if start == -1:
                continue
            end = report_text.find("\n### ", start + 1)
            if end == -1:
                end = report_text.find("\n## ", start + 1)
            section = report_text[start:end if end != -1 else len(report_text)]
            for line in section.splitlines():
                if line.startswith("- "):
                    item = line[2:].split("(", 1)[0].strip()
                    if item and item not in needs:
                        needs.append(item)

    return needs[:10]

def _v0955_existing_exact_categories(report_text: str) -> set[str]:
    categories: set[str] = set()
    start = report_text.find("### Exact Full-Pool Candidate Preview")
    if start == -1:
        return categories
    end = report_text.find("### Exact Preview Safety Boundaries", start)
    section = report_text[start:end if end != -1 else len(report_text)]
    for line in section.splitlines():
        if line.startswith("#### "):
            categories.add(line[5:].strip())
    return categories

def _v0955_build_category_block(category: str) -> list[str]:
    lines: list[str] = []
    lines.append(f"#### {category}")
    examples = []
    if "_v0952_candidate_examples_for_category" in globals():
        try:
            examples = list(_v0952_candidate_examples_for_category(category) or [])
        except Exception:
            examples = []
    if not examples:
        examples = ["Flexible removal", "Additional card draw", "Efficient ramp", "Protection for key engine pieces", "A cleaner finisher"]

    for card in examples[:5]:
        status = "color identity not verified"
        if "_v0953_card_is_color_legal" in globals():
            # Cannot reliably pass commander identity here without re-parsing full text inside this helper.
            # v0.9.5.3 rebuild will run before/inside the final chain; v0.9.5.5 adds role alignment first then reuses v0.9.5.4 labels later.
            status = "color identity not verified"
        tags = ""
        if "_v0954_card_pressure_tags" in globals():
            try:
                tags = "; ".join(_v0954_card_pressure_tags(card))
            except Exception:
                tags = "budget not checked; bracket not checked; table fit not checked"
        else:
            tags = "budget not checked; bracket not checked; table fit not checked"
        lines.append(f"- {card} ({status}) — {tags}")
    lines.append("")
    return lines

def _v0955_improve_exact_preview_role_alignment(report_text: str) -> str:
    start = report_text.find("### Exact Full-Pool Candidate Preview")
    if start == -1:
        return report_text

    safety_start = report_text.find("### Exact Preview Safety Boundaries", start)
    if safety_start == -1:
        return report_text

    existing_categories = _v0955_existing_exact_categories(report_text)
    need_lines = _v0955_extract_report_need_lines(report_text)
    mapped_categories: list[str] = []

    for need in need_lines:
        category = _v0955_need_to_exact_preview_category(need)
        if category not in mapped_categories:
            mapped_categories.append(category)

    # If the report only had vague/general exact categories but actual needs exist,
    # insert up to three more specific need-aligned categories before safety boundaries.
    specific_categories = [
        c for c in mapped_categories
        if c not in {
            "Better role coverage",
            "General role coverage only if the pilot wants outside-card options",
        }
    ]

    categories_to_add = [c for c in specific_categories if c not in existing_categories][:3]
    if not categories_to_add:
        return report_text

    insertion: list[str] = []
    insertion.append("### Need-Aligned Exact Preview Addendum")
    insertion.append("> v0.9.5.5 cleanup: These examples are mapped from detected replacement needs so the exact preview is less generic. They remain exploratory examples only.")
    insertion.append("")

    for category in categories_to_add:
        insertion.extend(_v0955_build_category_block(category))

    insertion_text = "\n".join(insertion)
    return report_text[:safety_start] + insertion_text + "\n" + report_text[safety_start:]

def _v09551_need_to_exact_preview_category(need_text: str) -> str:
    low = str(need_text or "").lower()

    if "table-stabilizing" in low or "interaction" in low or "removal" in low:
        return "More targeted interaction"
    if "board wipe" in low or "wipe" in low or "clear" in low:
        return "More board wipes"
    if "board protection" in low:
        return "More protection"
    if "protection" in low or "protect" in low:
        return "More protection"
    if "evasion" in low or "trample" in low:
        return "More finishers"
    if "combat finisher" in low or "combat payoff" in low or "finisher" in low:
        return "More finishers"
    if "token" in low or "go-wide" in low:
        return "More token support"
    if "draw" in low or "card advantage" in low or "refill" in low:
        return "More card draw / card advantage"
    if "ramp" in low or "mana" in low or "land" in low:
        return "More ramp / mana development"
    if "recursion" in low or "graveyard" in low:
        return "More recursion"
    if "dragon" in low:
        return "More confirmed Dragon support"
    if "combo" in low:
        return "Combo support only if user opts in"
    if "no urgent" in low or "general" in low or "broad" in low or "role coverage" in low:
        return "General role coverage only if the pilot wants outside-card options"
    return "Better role coverage"

def _v09551_extract_replacement_addition_needs(report_text: str) -> list[str]:
    needs: list[str] = []

    start = report_text.find("## Replacement / Addition Needs")
    if start != -1:
        end = report_text.find("\n## ", start + 1)
        section = report_text[start:end if end != -1 else len(report_text)]
        for line in section.splitlines():
            if not line.startswith("- "):
                continue
            item = line[2:].strip()
            if not item:
                continue
            if item.lower().startswith("note:"):
                continue
            if "no urgent replacement category" in item.lower():
                continue
            if item not in needs:
                needs.append(item)

    if not needs:
        for heading in ("### Role Gap Summary", "### Strategy-Specific Need Summary"):
            start = report_text.find(heading)
            if start == -1:
                continue
            next_h2 = report_text.find("\n## ", start + 1)
            next_h3 = report_text.find("\n### ", start + len(heading))
            candidates = [idx for idx in (next_h2, next_h3) if idx != -1]
            end = min(candidates) if candidates else len(report_text)
            section = report_text[start:end]
            for line in section.splitlines():
                if not line.startswith("- "):
                    continue
                item = line[2:].split("(", 1)[0].strip()
                if item and item not in needs:
                    needs.append(item)

    return needs[:10]

def _v09551_make_card_line(card: str) -> str:
    status = "color identity not verified"
    tags = "budget not checked; bracket not checked; table fit not checked"
    if "_v0954_card_pressure_tags" in globals():
        try:
            tags = "; ".join(_v0954_card_pressure_tags(card))
        except Exception:
            pass
    return f"- {card} ({status}) — {tags}"

def _v09551_examples_for_category(category: str) -> list[str]:
    if "_v0952_candidate_examples_for_category" in globals():
        try:
            examples = list(_v0952_candidate_examples_for_category(category) or [])
            if examples:
                return examples[:5]
        except Exception:
            pass
    fallback = {
        "More targeted interaction": ["Beast Within", "Generous Gift", "Swords to Plowshares", "Chaos Warp", "Assassin's Trophy"],
        "More board wipes": ["Blasphemous Act", "Farewell", "Austere Command", "Toxic Deluge", "Cyclonic Rift"],
        "More protection": ["Heroic Intervention", "Teferi's Protection", "Flawless Maneuver", "Tamiyo's Safekeeping", "Swiftfoot Boots"],
        "More finishers": ["Craterhoof Behemoth", "Overwhelming Stampede", "Finale of Devastation", "Torment of Hailfire", "Triumph of the Hordes"],
        "More token support": ["Parallel Lives", "Anointed Procession", "Second Harvest", "Adrix and Nev, Twincasters", "Mondrak, Glory Dominus"],
        "More card draw / card advantage": ["Guardian Project", "Beast Whisperer", "Return of the Wildspeaker", "Rishkar's Expertise", "Esper Sentinel"],
        "More ramp / mana development": ["Arcane Signet", "Nature's Lore", "Three Visits", "Farseek", "Talisman cycle / Signet cycle"],
        "More recursion": ["Eternal Witness", "Regrowth", "Victimize", "Reanimate", "Sevinne's Reclamation"],
        "More confirmed Dragon support": ["Dragon Tempest", "Scourge of Valkas", "Lathliss, Dragon Queen", "Sarkhan's Triumph", "Crucible of Fire"],
    }
    return fallback.get(category, ["Flexible removal", "Additional card draw", "Efficient ramp", "Protection for key engine pieces", "A cleaner finisher"])[:5]

def _v09551_force_need_aligned_addendum_after_exact_preview(report_text: str) -> str:
    if "### Exact Full-Pool Candidate Preview" not in report_text:
        return report_text
    if "### Need-Aligned Exact Preview Addendum" in report_text:
        return report_text

    needs = _v09551_extract_replacement_addition_needs(report_text)
    if not needs:
        return report_text

    categories: list[str] = []
    for need in needs:
        cat = _v09551_need_to_exact_preview_category(need)
        if cat not in categories and cat not in {
            "Better role coverage",
            "General role coverage only if the pilot wants outside-card options",
        }:
            categories.append(cat)

    if not categories:
        return report_text

    exact_start = report_text.find("### Exact Full-Pool Candidate Preview")
    safety_start = report_text.find("### Exact Preview Safety Boundaries", exact_start)
    if safety_start == -1:
        return report_text

    exact_block = report_text[exact_start:safety_start]
    existing_categories = set(_v09551_exact_preview_categories(exact_block))
    categories_to_add = [cat for cat in categories if cat not in existing_categories][:4]
    if not categories_to_add:
        return report_text

    addendum: list[str] = []
    addendum.append("### Need-Aligned Exact Preview Addendum")
    addendum.append("> v0.9.5.5.1 hotfix: These examples are mapped directly from detected replacement needs so the exact preview is not stuck on generic role coverage. They remain exploratory examples only.")
    addendum.append("")

    for category in categories_to_add:
        addendum.append(f"#### {category}")
        for card in _v09551_examples_for_category(category):
            addendum.append(_v09551_make_card_line(card))
        addendum.append("")

    addendum_text = "\n".join(addendum)
    return report_text[:safety_start] + addendum_text + "\n" + report_text[safety_start:]
