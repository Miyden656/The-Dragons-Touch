"""Report postprocessors for normal deck reports.

v1.5.21 extracts the final v0.9.5.5.2 report postprocess wrapper from
reports/report_builder.py. The goal is to remove the bottom-of-file
build_normal_report redefinition while preserving report text behavior.
"""

from __future__ import annotations
import re
from typing import Any
from reports.player_facing_status_cleanup import clean_player_facing_status_text
from reports.user_report_cleanup import clean_developer_noise_from_user_report
from reports.user_report_detail_suppression import clean_normal_report_user_details
from reports.user_report_candidate_combo_cleanup import clean_candidate_combo_user_wording
from reports.report_readability_cleanup import reframe_developer_report_framing


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


def _v095552_need_to_exact_preview_category(need_text: str) -> str:
    low = str(need_text or "").lower()
    if "toughness" in low or "defender" in low or "wall" in low:
        return "More toughness / defender support"
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
    return "Better role coverage"


def _v095552_examples_for_category(category: str) -> list[str]:
    exact = {
        "More toughness / defender support": ["High Alert", "Huatli, the Sun's Heart", "Doran, the Siege Tower", "Treefolk Umbra", "Tower Defense"],
        "More targeted interaction": ["Beast Within", "Generous Gift", "Swords to Plowshares", "Anguished Unmaking", "Assassin's Trophy"],
        "More board wipes": ["Austere Command", "Toxic Deluge", "Farewell", "Vanquish the Horde", "Expel the Interlopers"],
        "More protection": ["Heroic Intervention", "Teferi's Protection", "Flawless Maneuver", "Tamiyo's Safekeeping", "Swiftfoot Boots"],
        "More finishers": ["Craterhoof Behemoth", "Overwhelming Stampede", "Finale of Devastation", "Akroma's Will", "Triumph of the Hordes"],
        "More token support": ["Parallel Lives", "Anointed Procession", "Second Harvest", "Mondrak, Glory Dominus", "Adrix and Nev, Twincasters"],
        "More card draw / card advantage": ["Guardian Project", "Beast Whisperer", "Return of the Wildspeaker", "Rishkar's Expertise", "Esper Sentinel"],
        "More ramp / mana development": ["Arcane Signet", "Nature's Lore", "Three Visits", "Farseek", "Talisman cycle / Signet cycle"],
        "More recursion": ["Eternal Witness", "Regrowth", "Victimize", "Reanimate", "Sevinne's Reclamation"],
        "More confirmed Dragon support": ["Dragon Tempest", "Scourge of Valkas", "Lathliss, Dragon Queen", "Sarkhan's Triumph", "Crucible of Fire"],
    }
    return exact.get(category, ["Flexible removal", "Additional card draw", "Efficient ramp", "Protection for key engine pieces", "A cleaner finisher"])[:5]


def _v095552_card_status_and_tags(card: str) -> str:
    tags = "budget not checked; bracket not checked; table fit not checked"
    try:
        tags = "; ".join(_v0954_card_pressure_tags(card))
    except Exception:
        pass
    return f"color identity not verified) — {tags}"


def _v095552_extract_clean_needs(report_text: str) -> list[str]:
    needs: list[str] = []

    def add(item: str) -> None:
        item = str(item or "").strip()
        if not item:
            return
        low = item.lower()
        if low.startswith("note:"):
            return
        if "replacementneeddetail(" in low or "replacementneedsummary(" in low:
            return
        if "replacement categories are role needs" in low or "replacement need profile active" in low:
            return
        if "no urgent replacement category" in low:
            return
        if item not in needs:
            needs.append(item)

    start = report_text.find("## Replacement / Addition Needs")
    if start != -1:
        end = report_text.find("\n## ", start + 1)
        section = report_text[start:end if end != -1 else len(report_text)]
        for line in section.splitlines():
            if line.startswith("- "):
                add(line[2:])

    if not needs:
        for heading in ("### Strategy-Specific Need Summary", "### Role Gap Summary"):
            start = report_text.find(heading)
            if start == -1:
                continue
            next_h2 = report_text.find("\n## ", start + 1)
            next_h3 = report_text.find("\n### ", start + len(heading))
            candidates = [idx for idx in (next_h2, next_h3) if idx != -1]
            end = min(candidates) if candidates else len(report_text)
            section = report_text[start:end]
            for line in section.splitlines():
                if line.startswith("- "):
                    add(line[2:].split("(", 1)[0].strip())

    return needs[:10]


def _v095552_clean_fallback_trigger_lines(report_text: str) -> str:
    heading = "### Fallback Categories to Explore Later"
    start = report_text.find(heading)
    if start == -1:
        return report_text
    end = report_text.find("\n### Exact Full-Pool Candidate Preview", start)
    if end == -1:
        end = report_text.find("\n### Safety Boundaries", start)
    if end == -1:
        return report_text

    needs = _v095552_extract_clean_needs(report_text)
    if not needs:
        return report_text

    lines = [heading]
    seen: set[str] = set()
    for need in needs:
        category = _v095552_need_to_exact_preview_category(need)
        line = f"- {category} — triggered by: {need}"
        if line not in seen:
            seen.add(line)
            lines.append(line)

    return report_text[:start] + "\n".join(lines) + "\n" + report_text[end:]


def _v095552_exact_preview_categories(exact_block: str) -> list[str]:
    categories: list[str] = []
    for line in exact_block.splitlines():
        if line.startswith("#### "):
            cat = line[5:].strip()
            if cat and cat not in categories:
                categories.append(cat)
    return categories


def _v095552_add_need_aligned_addendum(report_text: str) -> str:
    if "### Exact Full-Pool Candidate Preview" not in report_text:
        return report_text
    if "### Need-Aligned Exact Preview Addendum" in report_text:
        return report_text

    needs = _v095552_extract_clean_needs(report_text)
    if not needs:
        return report_text

    exact_start = report_text.find("### Exact Full-Pool Candidate Preview")
    safety_start = report_text.find("### Exact Preview Safety Boundaries", exact_start)
    if safety_start == -1:
        return report_text

    exact_block = report_text[exact_start:safety_start]
    existing = set(_v095552_exact_preview_categories(exact_block))

    categories: list[str] = []
    for need in needs:
        cat = _v095552_need_to_exact_preview_category(need)
        if cat not in {"Better role coverage", "General role coverage only if the pilot wants outside-card options"}:
            if cat not in existing and cat not in categories:
                categories.append(cat)

    if not categories:
        return report_text

    addendum: list[str] = []
    addendum.append("### Need-Aligned Exact Preview Addendum")
    addendum.append("> v0.9.5.5.2 hotfix: These examples are mapped from the detected replacement needs so exact full-pool preview does not stay generic-only when the report has clearer role targets. They remain exploratory examples only.")
    addendum.append("")

    for category in categories[:4]:
        addendum.append(f"#### {category}")
        for card in _v095552_examples_for_category(category):
            addendum.append(f"- {card} ({_v095552_card_status_and_tags(card)}")
        addendum.append("")

    return report_text[:safety_start] + "\n".join(addendum) + "\n" + report_text[safety_start:]


def apply_normal_report_postprocessors(report_text: str) -> str:
    """Apply final normal-report postprocessors.

    This replaces the old report_builder.py bottom-of-file build_normal_report
    wrapper while preserving the same v0.9.5.5.2 final postprocess behavior.
    """

    report_text = _v095552_clean_fallback_trigger_lines(report_text)
    report_text = _v095552_add_need_aligned_addendum(report_text)
    report_text = clean_player_facing_status_text(report_text)
    report_text = clean_developer_noise_from_user_report(report_text)
    report_text = clean_normal_report_user_details(report_text)
    report_text = clean_candidate_combo_user_wording(report_text)
    report_text = reframe_developer_report_framing(report_text)
    return report_text

# v1.5.24 — Safe text-in/text-out postprocessor batch extracted from reports/report_builder.py

def _v0952_should_show_exact_preview(report_text: str) -> bool:
    start = report_text.find("## Full-Card-Pool Fallback Preview")
    if start == -1:
        return False
    end = report_text.find("\n## ", start + 1)
    section = report_text[start:end] if end != -1 else report_text[start:]
    return "Full-card-pool fallback preview active: Yes" in section

def _v09551_exact_preview_categories(exact_block: str) -> list[str]:
    categories: list[str] = []
    for line in exact_block.splitlines():
        if line.startswith("#### "):
            cat = line[5:].strip()
            if cat and cat not in categories:
                categories.append(cat)
    return categories
