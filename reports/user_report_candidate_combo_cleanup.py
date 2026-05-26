"""Normal report candidate/combo wording cleanup.

Presentation-only layer for the user-facing deck report. This suppresses
remaining engine/scoring/source-path wording after the broader user detail
suppression step. Debug reports and diagnostics retain full machinery detail.
"""

from __future__ import annotations

import re


SECTION_TITLES_TO_REMOVE = (
    "Report Section Notes",
    "Full-Card-Pool Fallback Preview",
)

LINE_PREFIXES_TO_DROP = (
    "- Review score:",
    "- Review band:",
    "- Recommendation type:",
    "- Detected collection roles:",
    "- Philosophy replacement fit:",
    "- Support-only category overlap:",
    "- Source file(s):",
    "- Source:",
    "- Owned status:",
    "- Collection mode:",
    "- Collection loaded:",
    "- Selected collection files:",
    "- Philosophy-aware replacement bias active:",
    "- Replacement bias lens:",
    "- Full-card-pool fallback active:",
)

PHRASES_TO_DROP_LINE = (
    "This is a nudge only; normal collection fit, strategy fit, legality, and pilot intent still decide.",
    "philosophy replacement-bias nudge applied",
    "still subject to normal quality gates",
    "passes strong promotion gate",
    "Support-only category overlap:",
    "Full combo variant details remain available in the isolated combo awareness breakdown artifact",
    "This section intentionally hides Combo Finder parity",
    "Collection-completable potential combos are grouped by missing card for readability.",
)

USER_REPLACEMENTS = {
    "## Collection Pull Candidates": "## Collection-Based Review Candidates",
    "### Top Ranked Collection-First Candidates": "### Best Owned Cards to Review",
    "### Current Candidate Snapshot": "### Owned Candidate Summary",
    "### Best Available Collection Shakeup Candidates": "### Experimental Owned Ideas",
    "### Collection Candidate Notes": "### How to Read These Candidates",
    "Collection-owned candidates adapted": "Owned cards found for review",
    "Strong candidates adapted": "Strong owned fits",
    "Possible candidates adapted": "Possible owned fits",
    "Shakeup candidates adapted": "Experimental owned ideas",
    "Dragon Gate Manual Review": "Manual Review",
    "collection_owned_possible_review": "Possible owned fit",
    "collection_owned_strong_review": "Strong owned fit",
    "dragon_need_semantic_review": "Manual review",
    "Review caution:": "Careful because:",
    "Reason:": "Why to consider it:",
    "Why it may fit:": "Useful role notes:",
}


TAG_TO_WORDS = {
    "artifact": "artifact synergy",
    "card_advantage": "card advantage",
    "card_draw": "card draw",
    "card_selection": "card selection",
    "combat_support": "combat support",
    "copy_token_payoff": "copy-token payoff",
    "counter_synergy": "counter synergy",
    "creature": "creature-based plan",
    "dragon_card": "Dragon card",
    "dragon_typal_support": "Dragon typal support",
    "enchantment": "enchantment synergy",
    "evasion_support": "evasion support",
    "finisher_or_payoff": "finisher/payoff role",
    "graveyard_setup": "graveyard setup",
    "land": "land slot",
    "mana_source": "mana source",
    "narrow_typal_requirement": "typal support requirement",
    "protection": "protection",
    "ramp": "ramp",
    "sacrifice_synergy": "sacrifice synergy",
    "sorcery": "sorcery role",
    "spell_payoff": "spell payoff",
    "targeted_removal": "targeted removal",
    "team_wide_combat_support": "team-wide combat support",
    "token_production": "token production",
    "treasure_synergy": "Treasure synergy",
    "typal_or_theme_support": "typal/theme support",
}


def _remove_section(text: str, title: str) -> str:
    escaped = re.escape(title)
    text = re.sub(rf"(?ms)^## {escaped}(?:[^\n]*)\n.*?(?=^## |\Z)", "", text)
    text = re.sub(rf"(?ms)^### {escaped}(?:[^\n]*)\n.*?(?=^## |^### |\Z)", "", text)
    return text


def _strip_windows_paths(text: str) -> str:
    # Replace collection/deck absolute paths with player-facing source labels.
    text = re.sub(r"`[A-Za-z]:\\[^`\n]+\\collection\\([^`\\\n]+)`", r"`collection file: \1`", text)
    text = re.sub(r"`[A-Za-z]:\\[^`\n]+\\Decklists\\([^`\\\n]+)`", r"`deck file: \1`", text)
    text = re.sub(r"`[A-Za-z]:\\[^`\n]+`", "`local file`", text)
    return text


def _plain_role_notes(tag_text: str) -> str:
    tags = [piece.strip().strip(".") for piece in tag_text.split(",") if piece.strip()]
    readable: list[str] = []
    for tag in tags:
        readable.append(TAG_TO_WORDS.get(tag, tag.replace("_", " ")))
    # Keep this short in the normal report.
    unique = []
    for item in readable:
        if item not in unique:
            unique.append(item)
    return ", ".join(unique[:6])


def _rewrite_tag_line(line: str) -> str:
    stripped = line.strip()
    if stripped.startswith("- Useful role notes:"):
        _, _, rest = line.partition(":")
        plain = _plain_role_notes(rest)
        if plain:
            return "- Useful role notes: " + plain
    if stripped.startswith("- Why it may fit:"):
        _, _, rest = line.partition(":")
        plain = _plain_role_notes(rest)
        if plain:
            return "- Useful role notes: " + plain
    return line


def _drop_or_rewrite_lines(text: str) -> str:
    kept: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            kept.append(line)
            continue

        if stripped.startswith(LINE_PREFIXES_TO_DROP):
            continue

        if any(phrase in stripped for phrase in PHRASES_TO_DROP_LINE):
            # Preserve the useful half of a "Why to consider it" sentence when possible.
            if stripped.startswith("- Why to consider it:"):
                shortened = stripped
                for phrase in PHRASES_TO_DROP_LINE:
                    shortened = shortened.replace(phrase, "")
                shortened = re.sub(r"\s*;\s*;\s*", "; ", shortened)
                shortened = re.sub(r"\s+\.\s*$", ".", shortened)
                if len(shortened) > len("- Why to consider it: ") + 10:
                    kept.append(shortened)
            continue

        rewritten = _rewrite_tag_line(line)
        kept.append(rewritten)

    return "\n".join(kept)


def _clean_combo_section(text: str) -> str:
    # Keep combo findings, but strip local collection file paths and report-formatting notes.
    text = text.replace("Deck checked: `local file`", "")
    text = re.sub(r"(?m)^Deck checked: .*$\n?", "", text)
    text = text.replace("found in: `collection file: ", "owned source: `")
    return text


def _clean_spacing(text: str) -> str:
    text = re.sub(r"(?m)^#\s*$\n?", "", text)
    text = re.sub(r"(\S)(### )", r"\1\n\n\2", text)
    text = re.sub(r"(?m)^###\s*$\n?", "", text)
    text = re.sub(r"(?m)^\s*-\s*$\n?", "", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text.strip() + "\n"


def clean_candidate_combo_user_wording(report_text: str) -> str:
    """Clean remaining candidate/combo machinery from the normal report."""

    if not isinstance(report_text, str):
        return report_text

    cleaned = report_text

    for old, new in USER_REPLACEMENTS.items():
        cleaned = cleaned.replace(old, new)

    for title in SECTION_TITLES_TO_REMOVE:
        cleaned = _remove_section(cleaned, title)

    cleaned = _strip_windows_paths(cleaned)
    cleaned = _drop_or_rewrite_lines(cleaned)
    cleaned = _clean_combo_section(cleaned)
    cleaned = _clean_spacing(cleaned)

    return cleaned


def candidate_combo_cleanup_health() -> dict[str, object]:
    return {
        "version": "v1.5.31.4",
        "normal_report_user_facing_only": True,
        "suppresses_candidate_engine_metadata": True,
        "suppresses_combo_report_notes": True,
        "debug_reports_preserve_detail": True,
    }
