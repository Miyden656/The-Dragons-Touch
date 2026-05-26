"""Normal report user-facing detail suppression.

This module is presentation-only. It removes internal/developer-oriented detail
from the normal deck report while preserving user-facing findings and leaving
debug reports/diagnostics as the place for full machinery details.
"""

from __future__ import annotations

import re


SECTION_TITLES_TO_REMOVE = (
    "Annotated Decklist / Card Role Notes for AI Review",
    "Reference / Non-Mainboard / Ignored Cards",
)

SUBSECTION_TITLES_TO_REMOVE = (
    "Boundary",
    "Report Section Notes",
)

LINE_PREFIXES_TO_DROP = (
    "- Role tags:",
    "- Role note:",
    "- Plan-fit note:",
    "- Cut/review/protection status:",
    "- Source file(s):",
    "- Recommendation type:",
    "- Collection-first rank score:",
    "- Collection-first rank band:",
    "- Full-card-pool fallback active:",
    "- Candidate source mode:",
    "- Ranking method:",
    "- Engine status:",
    "- Exact ranking engine active:",
    "- Confidence ceiling active:",
    "- Dragon semantic gate active:",
    "- Dragon gate visible rewrite active:",
    "- Detected collection roles:",
    "- Philosophy replacement fit:",
    "- Support-only category overlap:",
)

INTERNAL_PHRASES_TO_DROP = (
    "candidate must render as",
    "Visible-field rewrite applied",
    "Dragon semantic gate requires manual review because Dragon-need text alone is not proof",
    "Dragon gate correction:",
    "Quality gate:",
    "semantic strong-fit gate",
    "Strong promotion gate is active",
    "Role mapping hardening is active",
    "Collection gaps are tracked role-by-role",
    "Full combo variant details remain available in the isolated combo awareness breakdown artifact",
    "This section intentionally hides Combo Finder parity",
    "Full-card-pool fallback stays dormant",
    "Collection-first candidates appear sufficient for this pass",
)

PLAYER_REPLACEMENTS = {
    "## Replacement Candidate Engine Preview": "## Owned Replacement Ideas",
    "### Current Candidate Snapshot": "### Owned Candidate Summary",
    "### Top Ranked Collection-First Candidates": "### Best Owned Cards to Review",
    "### Collection Pull Candidates": "### Collection-Based Review Candidates",
    "### Best Available Collection Shakeup Candidates": "### Experimental Owned Ideas",
    "### Collection Candidate Notes": "### How to Read These Candidates",
    "- Collection-owned candidates adapted:": "- Owned cards found for review:",
    "- Strong candidates adapted:": "- Strong owned fits:",
    "- Possible candidates adapted:": "- Possible owned fits:",
    "- Shakeup candidates adapted:": "- Experimental owned ideas:",
    "- Recommendation type: collection_owned_possible_review": "",
    "- Recommendation type: collection_owned_strong_review": "",
    "- Recommendation type: dragon_need_semantic_review": "",
    "- Confidence: Shakeup only": "- Confidence: Experimental",
    "- Fit type: Best available / experiment, not a confirmed upgrade": "- Fit type: Experimental idea, not a confirmed upgrade",
    "- Fit type: Owned card may fit current deck needs; pilot review recommended": "- Fit type: Possible owned fit; pilot review recommended",
    "- Source: collection": "",
    "- Owned status: owned": "",
    "Collection-first rank score": "Review score",
    "Collection-first rank band": "Review band",
    "Detected collection roles": "Why it may fit",
    "Quality gate": "Review caution",
    "Recommendation type": "Review type",
}


def _remove_h2_section(text: str, title: str) -> str:
    return re.sub(rf"(?ms)^## {re.escape(title)}(?:[^\n]*)\n.*?(?=^## |\Z)", "", text)


def _remove_subsection(text: str, title: str) -> str:
    # Remove H3 subsections until the next H2/H3. This avoids swallowing the
    # rest of a major section.
    return re.sub(rf"(?ms)^### {re.escape(title)}(?:[^\n]*)\n.*?(?=^## |^### |\Z)", "", text)


def _drop_internal_lines(text: str) -> str:
    kept: list[str] = []
    skip_indented_block = False

    for line in text.splitlines():
        stripped = line.strip()

        if not stripped:
            skip_indented_block = False
            kept.append(line)
            continue

        drop_line = False

        if stripped.startswith(LINE_PREFIXES_TO_DROP):
            drop_line = True
            # Many internal metadata bullets are followed by explanatory nested
            # bullets. Drop the nested block too.
            if stripped.startswith(("- Philosophy replacement fit:", "- Quality gate:")):
                skip_indented_block = True

        if skip_indented_block and (line.startswith("  - ") or line.startswith("    - ")):
            drop_line = True

        if any(phrase in stripped for phrase in INTERNAL_PHRASES_TO_DROP):
            drop_line = True

        if drop_line:
            continue

        skip_indented_block = False
        kept.append(line)

    return "\n".join(kept)


def _rewrite_candidate_summary(text: str) -> str:
    for old, new in PLAYER_REPLACEMENTS.items():
        text = text.replace(old, new)
    return text


def _clean_stranded_hashes_and_spacing(text: str) -> str:
    # Remove standalone "#", which appeared before some repeated candidate
    # headings after prior cleanup.
    text = re.sub(r"(?m)^#\s*$\n?", "", text)

    # Add spacing before glued headings.
    text = re.sub(r"(\S)(### )", r"\1\n\n\2", text)

    # Remove empty headings left behind by deleted sections or lines.
    text = re.sub(r"(?m)^###\s*$\n?", "", text)
    text = re.sub(r"(?m)^\s*-\s*$\n?", "", text)

    # Reduce excessive blank lines.
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text.strip() + "\n"


def clean_normal_report_user_details(report_text: str) -> str:
    """Suppress internal detail from a normal user-facing deck report."""

    if not isinstance(report_text, str):
        return report_text

    cleaned = report_text

    for title in SECTION_TITLES_TO_REMOVE:
        cleaned = _remove_h2_section(cleaned, title)

    for title in SUBSECTION_TITLES_TO_REMOVE:
        cleaned = _remove_subsection(cleaned, title)

    cleaned = _rewrite_candidate_summary(cleaned)
    cleaned = _drop_internal_lines(cleaned)
    cleaned = _clean_stranded_hashes_and_spacing(cleaned)

    return cleaned


def user_detail_suppression_health() -> dict[str, object]:
    return {
        "version": "v1.5.31.3",
        "normal_report_user_facing_only": True,
        "suppresses_annotated_role_dump": True,
        "debug_reports_preserve_detail": True,
    }
