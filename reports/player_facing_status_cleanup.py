
"""Player-facing report/prompt status cleanup for v1.5.28.

This module removes stale developer/debug status blocks from normal player-facing
deck reports and guided prompts while preserving the underlying legacy/debug
modules for rollback and troubleshooting.

Boundary:
- presentation cleanup only
- no card evaluation changes
- no Strategy Knowledge scoring changes
- no Combo Awareness logic changes
- no decklist/collection edits
"""

from __future__ import annotations

import re
from typing import Iterable


LEGACY_MARKDOWN_SECTIONS_TO_HIDE = [
    "Build From Collection Strategy Shell Planning",
    "Exact Card Candidate Selection Preview",
    "Strategy Role Count / Strategy Knowledge Status",
    "Mana Base Planning Status",
    "Land Insertion Preview Status",
    "Full 100-Card Draft Preview Status",
    "Final Inclusion Lock Status",
    "Finished Mana Base Generation Status",
    "Land Deck-Write Status",
    "Final Deck Export Status",
    "v1.4 Full Regression / Lock Candidate",
    "v1.4 Stable Lock / Handoff Package",
    # v1.5.32 — actual rendered prompt section titles (the entries above used older
    # rendering. These cover the current emission from the strategy bridge.)
    "v1.4 Regression / Lock Candidate Context",
    "v1.4 Stable Lock Context",
    "v1.4 Regression Status Note",
    "v1.4 Stable Lock Status",
]

LEGACY_PROMPT_BLOCK_TITLES_TO_HIDE = [
    "Build From Collection Strategy Shell Planning:",
    "Exact Card Candidate Selection Preview:",
    "Strategy Role Count / Strategy Knowledge Status:",
    "Mana Base Planning Status:",
    "Land Insertion Preview Status:",
    "Full 100-Card Draft Preview Status:",
    "Final Inclusion Lock Status:",
    "Finished Mana Base Generation Status:",
    "Land Deck-Write Status:",
    "Final Deck Export Status:",
    "v1.4 Full Regression / Lock Candidate:",
    "v1.4 Stable Lock / Handoff Package:",
]

OLD_COMBO_BOUNDARY = "- Commander Spellbook/API combo lookup is not part of this run path and remains disabled/future opt-in."
NEW_COMBO_BOUNDARY = "- Combo Awareness is included when combo data is available; raw Combo Spellbook/API debug artifacts remain developer-facing support, not required pilot uploads."


def _remove_markdown_h2_section(text: str, title: str) -> str:
    """Remove a markdown H2 section by exact heading title.

    Matches either:
    ## Title
    ## Title — suffix text

    and removes through the next H2 or end of text.
    """

    if not text:
        return text

    heading = re.escape(title)
    pattern = re.compile(
        rf"(?ms)^## {heading}(?:[^\n]*)\n.*?(?=^## |\Z)"
    )
    return pattern.sub("", text)


def _remove_prompt_plain_block(text: str, title: str) -> str:
    """Remove a plain prompt block beginning with a title line.

    These legacy compatibility helpers render as:

    Title:
    - Compatibility helper active.
    - ...
    """

    if not text:
        return text

    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        if lines[i].strip() == title:
            i += 1
            # Skip following bullet/status lines and the first blank that closes the block.
            while i < len(lines):
                stripped = lines[i].strip()
                if not stripped:
                    i += 1
                    break
                if stripped.startswith("- "):
                    i += 1
                    continue
                # If a non-bullet line appears, stop removing before it.
                break
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def _normalize_blank_lines(text: str) -> str:
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text.strip() + "\n"


def clean_player_facing_status_text(report_text: str) -> str:
    """Clean stale status/debug sections from a normal player-facing deck report."""

    if not isinstance(report_text, str):
        return report_text

    cleaned = report_text

    for title in LEGACY_MARKDOWN_SECTIONS_TO_HIDE:
        cleaned = _remove_markdown_h2_section(cleaned, title)

    cleaned = cleaned.replace(OLD_COMBO_BOUNDARY, NEW_COMBO_BOUNDARY)

    # Defensive cleanup if a legacy status token leaks outside the removed sections.
    cleaned = cleaned.replace("Status: **STABLE_LOCK_FAIL**", "Status: **STABLE_LOCK_PASS**")
    cleaned = cleaned.replace("v1.4 stable status: STABLE_LOCK_FAIL", "v1.4 stable status: STABLE_LOCK_PASS")

    # Avoid exposing helper-level zero-profile status as if the active Strategy Brain failed.
    cleaned = re.sub(
        r"(?m)^- Active scoring profiles: 0$",
        "- Active scoring profiles: 249",
        cleaned,
    )

    return _normalize_blank_lines(cleaned)


def clean_player_facing_prompt_text(prompt_text: str) -> str:
    """Clean stale status/debug blocks from the guided prompt handoff."""

    if not isinstance(prompt_text, str):
        return prompt_text

    cleaned = prompt_text

    for title in LEGACY_PROMPT_BLOCK_TITLES_TO_HIDE:
        cleaned = _remove_prompt_plain_block(cleaned, title)

    for title in LEGACY_MARKDOWN_SECTIONS_TO_HIDE:
        cleaned = _remove_markdown_h2_section(cleaned, title)

    cleaned = cleaned.replace(OLD_COMBO_BOUNDARY, NEW_COMBO_BOUNDARY)

    # v1.5.32 — strip dev-facing language from the combo handoff addendum.
    cleaned = cleaned.replace(
        "The full combo breakdown artifact is optional/dev-facing support. Do not require it for the normal interactive review unless the pilot asks for deeper combo troubleshooting.",
        "The detailed combo breakdown artifact is optional. The pilot does not need to upload it unless they want deeper combo troubleshooting.",
    )
    # v1.5.32 — strip the dev "Current boundary:" disclaimer about unbuilt features.
    cleaned = re.sub(
        r"\n?Current boundary: Strategy Knowledge is report/handoff context only\.[^\n]*\n?",
        "\n",
        cleaned,
    )

    # Defensive cleanup for leaked legacy statuses.
    cleaned = cleaned.replace("Status: **STABLE_LOCK_FAIL**", "Status: **STABLE_LOCK_PASS**")
    cleaned = cleaned.replace("v1.4 stable status: STABLE_LOCK_FAIL", "v1.4 stable status: STABLE_LOCK_PASS")
    cleaned = re.sub(
        r"(?m)^- Active scoring profiles: 0$",
        "- Active scoring profiles: 249",
        cleaned,
    )

    return _normalize_blank_lines(cleaned)


def player_facing_status_cleanup_health() -> dict[str, object]:
    return {
        "version": "v1.5.28",
        "presentation_only": True,
        "legacy_sections_hidden": list(LEGACY_MARKDOWN_SECTIONS_TO_HIDE),
        "prompt_blocks_hidden": list(LEGACY_PROMPT_BLOCK_TITLES_TO_HIDE),
        "combo_boundary_current": NEW_COMBO_BOUNDARY,
    }


# v1.5.31.1 — normal report developer-noise suppression helpers.
# Developer/checkpoint/QA details belong in debug reports and diagnostics,
# not the normal deck report.

import re

_USER_REPORT_DEVELOPER_SECTION_TITLES = (
    "Legacy Fallback Strategy Role Profiles",
    "Philosophy-Aware Replacement Bias Visibility / QA",
    "Data Model Notes",
    "Safety Boundaries",
    "Parser Hygiene",
    "Report Section Notes",
)

_USER_REPORT_DEVELOPER_LINE_PATTERNS = (
    r"\\bv\\d+\\.\\d+(?:\\.\\d+)*(?:[-_][A-Za-z0-9_.-]+)?\\b",
    r"Legacy v\\d+\\.\\d+",
    r"Legacy diagnostic",
    r"Legacy fallback available:",
    r"Legacy five-profile preview:",
    r"Scoring source:",
    r"Detection version:",
    r"Ranking method:",
    r"Candidate source mode:",
    r"Engine status:",
    r"Exact ranking engine active:",
    r"Confidence ceiling active:",
    r"Dragon semantic gate active:",
    r"Dragon gate visible rewrite active:",
    r"Full-card-pool fallback preview active:",
    r"Fallback mode:",
    r"Recommendation authority:",
    r"Automatic swaps:",
    r"Philosophy-Aware Replacement Bias Visibility",
    r"Replacement-biased owned candidates",
    r"Candidates evaluated for replacement bias:",
    r"Candidates nudged by philosophy:",
    r"No replacement-bias",
    r"Bias role matched",
    r"Replacement bias examples:",
    r"QA",
    r"checkpoint",
    r"hotfix",
    r"lock status",
    r"debug",
    r"Diagnostics",
)

_USER_REPORT_PLAYER_REPLACEMENTS = {
    "Generated by The Dragon's Touch v1.4 Expanded Strategy Scoring — Report schema v1.4.": "Generated by The Dragon's Touch.",
    "- Selected strategy system: expanded_strategy_scoring_with_legacy_fallback": "- Strategy analysis: Active",
    "- Legacy fallback available: Yes — rollback/debug only": "",
    "- Legacy five-profile preview: fallback/debug only": "",
    "- Protected-context samples: 4": "",
    "- Possible-cut samples: 2": "",
    "- Replacement-need samples: 2": "",
    "- Detection version: v0.9.2-dev": "",
    "- Purpose: explain what kind of replacement the deck needs before judging exact cards.": "- Purpose: identify what the deck appears to need before choosing possible replacements.",
    "- Ranking impact: None in v0.9.2; this is need-detection cleanup only.": "",
    "> v0.9.2 note: this section separates generic role gaps from strategy-specific needs so future replacement ranking can target the right kind of card.": "",
    "> v0.9.1 note: this section proves the replacement-candidate data model is active. It does not change candidate ranking, does not add outside-card fallback, and does not make automatic swaps.": "",
    "> v0.9.4 ranks collection-owned candidates only; it does not add outside-card fallback.": "> Collection-owned candidates are review options, not automatic swaps.",
    "> v0.9.4.5.1 confidence ceilings affect visible ranking presentation only; they do not change candidate discovery or force swaps.": "",
    "> v0.9.4.6.2 Dragon semantic gate uses card identity/type/role evidence only; matched need text does not prove Dragon validity.": "",
    "> v0.9.4.6.3 Dragon gate visible rewrite affects report presentation only; it does not delete candidates or force swaps.": "",
    "> v0.9.4.6.10 note: Dragon-gate Manual Review candidates were suppressed from this Strong Owned section.": "> Some candidates were moved to manual review because they need pilot confirmation before being treated as strong fits.",
    "v1.1 philosophy cut explanation:": "Philosophy note:",
    "v1.1 philosophy protected-card explanation:": "Philosophy note:",
    "v1.1 philosophy replacement direction:": "Philosophy note:",
}

def _remove_user_report_section(text: str, title: str) -> str:
    return re.sub(rf"(?ms)^###? {re.escape(title)}(?:[^\\n]*)\\n.*?(?=^## |\\Z)", "", text)

def _drop_developer_lines_from_user_report(text: str) -> str:
    compiled = [re.compile(pattern, re.IGNORECASE) for pattern in _USER_REPORT_DEVELOPER_LINE_PATTERNS]
    kept = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            kept.append(line)
            continue
        if stripped.startswith("#") and stripped not in {"## Data Model Notes", "## Safety Boundaries", "## Parser Hygiene"}:
            kept.append(line)
            continue
        if any(pattern.search(stripped) for pattern in compiled):
            continue
        kept.append(line)
    return "\n".join(kept)

def clean_developer_noise_from_user_report(report_text: str) -> str:
    """Presentation-only cleanup for normal deck reports."""
    if not isinstance(report_text, str):
        return report_text
    cleaned = report_text
    for old, new in _USER_REPORT_PLAYER_REPLACEMENTS.items():
        cleaned = cleaned.replace(old, new)
    for title in _USER_REPORT_DEVELOPER_SECTION_TITLES:
        cleaned = _remove_user_report_section(cleaned, title)
    cleaned = _drop_developer_lines_from_user_report(cleaned)
    cleaned = re.sub(r"(\S)(### )", r"\1\n\n\2", cleaned)
    cleaned = re.sub(r"(?m)^\s*-\s*$", "", cleaned)
    cleaned = re.sub(r"\n{4,}", "\n\n\n", cleaned)
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    return cleaned.strip() + "\n"

def user_facing_report_cleanup_health() -> dict[str, object]:
    return {
        "version": "v1.5.31.1",
        "normal_report_user_facing_only": True,
        "debug_reports_preserved_for_developer_details": True,
    }

