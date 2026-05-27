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
    "Strategy Knowledge Integration",
)

SUBSECTION_TITLES_TO_REMOVE = (
    "Strategy Brain Status",
    "Strategy-Aware Guidance Rules",
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
    # v1.5.32 — internal pipeline state under "Why to consider it" sub-bullets
    "  - Protected Label:",
    "  - Initial flag:",
    "  - Philosophy adjustment:",
    "- Protected Label:",
    "- Initial flag:",
    "- Philosophy adjustment:",
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
    # v1.5.32 — strip dev-roadmap line from User-Facing Boundaries section
    "deep markdown rendering and structured report parsing are deferred",
    # v1.5.32 — strip "raw Combo Spellbook/API debug artifacts" disclaimer (dev-facing)
    "raw Combo Spellbook/API debug artifacts remain developer-facing support",
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
    # v1.5.32 — friendlier section and intro wording
    "## User-Facing Boundaries": "## How to Read This Review",
    "player-facing handoff packet": "review summary",
    "AI handoff packet": "review summary",
    "complete AI handoff packet": "complete review summary",
}


TAG_TO_WORDS = {
    # Card roles / categories
    "artifact": "artifact synergy",
    "card_advantage": "card advantage",
    "card_draw": "card draw",
    "card_selection": "card selection",
    "combat_support": "combat support",
    "combat_synergy": "combat synergy",
    "copy_clone_value": "copy/clone value",
    "copy_token_payoff": "copy-token payoff",
    "counter_synergy": "counter synergy",
    "creature": "creature-based plan",
    "creature_type_present": "matches commander creature type",
    "dragon_card": "Dragon card",
    "dragon_typal": "Dragon typal piece",
    "dragon_typal_support": "Dragon typal support",
    "enchantment": "enchantment synergy",
    "evasion_support": "evasion support",
    "finisher_or_payoff": "finisher/payoff",
    "graveyard_setup": "graveyard setup",
    "land": "land",
    "lands_matter": "lands-matter piece",
    "mana_rock": "mana rock",
    "mana_source": "mana source",
    "narrow_typal_requirement": "needs typal context",
    "protection": "protection",
    "ramp": "ramp",
    "sacrifice_synergy": "sacrifice synergy",
    "sorcery": "sorcery role",
    "spell_payoff": "spell payoff",
    "synergy_piece": "synergy piece",
    "targeted_removal": "targeted removal",
    "team_wide_combat_support": "team-wide combat support",
    "token_maker": "token maker",
    "token_production": "token production",
    "treasure_synergy": "Treasure synergy",
    "typal_density_piece": "typal density piece",
    "typal_or_theme_support": "typal/theme support",
    # Engine/payoff role-bias tags (used in philosophy adjustments and replacement-bias fit)
    "big_moment_enabler": "big-moment enabler",
    "commander_payoff_amplifier": "commander payoff amplifier",
    "connector_card": "connector",
    "connector_piece": "connector",
    "enabler": "enabler",
    "enabler_density": "enabler",
    "engine_piece": "engine piece",
    "engine_redundancy": "engine redundancy",
    "payoff_bridge": "payoff bridge",
    "payoff_support": "payoff support",
    "weak_alone_strong_in_context": "context-dependent piece",
}


def _remove_section(text: str, title: str) -> str:
    escaped = re.escape(title)
    text = re.sub(rf"(?ms)^## {escaped}(?:[^\n]*)\n.*?(?=^## |\Z)", "", text)
    text = re.sub(rf"(?ms)^### {escaped}(?:[^\n]*)\n.*?(?=^## |^### |\Z)", "", text)
    return text


def _remove_subsection(text: str, title: str) -> str:
    """Remove an H3 subsection without consuming the next H2 above it."""
    escaped = re.escape(title)
    return re.sub(rf"(?ms)^### {escaped}(?:[^\n]*)\n.*?(?=^## |^### |\Z)", "", text)


def _strip_windows_paths(text: str) -> str:
    # Shorten backtick-wrapped absolute paths to just the filename. The surrounding
    # line label (e.g. "- Deck file:", "found in:") already carries the meaning, so
    # we do NOT re-add a "deck file:" / "collection file:" prefix here — that caused
    # the earlier "- Deck file: `deck file: X.txt`" double-prefix bug.
    text = re.sub(r"`[A-Za-z]:[\\/][^`\n]+[\\/]([^`\\/\n]+)`", r"`\1`", text)
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
    # Keep combo findings; strip duplicate deck-identifier lines that the report header already covers.
    text = re.sub(r"(?m)^Deck checked: .*$\n?", "", text)
    # Strip any remaining bracket-tag annotations that originated from cached/older runs.
    text = re.sub(r"\s*_\(Bracket tag:[^)]*\)_", "", text)
    text = re.sub(r"\s*_\(Bracket tags seen:[^)]*\)_", "", text)
    return text


_REPLACEABILITY_LINE = re.compile(r"^(\s*-\s*)Replaceability score:\s*(-?\d+)\s*$")


def _replaceability_bucket(score: int) -> str:
    if score >= 6:
        return "Easy to replace"
    if score >= 3:
        return "Replaceable"
    if score >= 0:
        return "Could swap with care"
    if score >= -5:
        return "Hard to replace"
    return "Protected — hard to replace"


def _translate_replaceability_lines(text: str) -> str:
    """Turn 'Replaceability score: N' into a plain-English bucket label."""
    lines: list[str] = []
    for line in text.splitlines():
        match = _REPLACEABILITY_LINE.match(line)
        if match:
            indent = match.group(1)
            score = int(match.group(2))
            lines.append(f"{indent}Cut difficulty: {_replaceability_bucket(score)}")
        else:
            lines.append(line)
    return "\n".join(lines)


_ROLE_SNAPSHOT_HEADER = re.compile(r"^##\s+Role Snapshot\s*$", re.MULTILINE)
_ROLE_SNAPSHOT_LINE = re.compile(r"^(\s*-\s*)([a-z][a-z0-9_]*?)(:\s*\d+\s*)$")


def _translate_role_snapshot(text: str) -> str:
    """Inside the Role Snapshot section, translate underscore tag names to readable labels."""
    header_match = _ROLE_SNAPSHOT_HEADER.search(text)
    if not header_match:
        return text
    start = header_match.end()
    end_match = re.search(r"^##\s+", text[start:], re.MULTILINE)
    end = start + end_match.start() if end_match else len(text)
    section = text[start:end]
    new_lines: list[str] = []
    for line in section.splitlines():
        match = _ROLE_SNAPSHOT_LINE.match(line)
        if match:
            indent, tag, tail = match.groups()
            readable = TAG_TO_WORDS.get(tag, tag.replace("_", " "))
            new_lines.append(f"{indent}{readable}{tail}")
        else:
            new_lines.append(line)
    return text[:start] + "\n".join(new_lines) + text[end:]


_PLAN_FIT_VIA = re.compile(r"(Supports primary strategy via:\s*)([a-z0-9_,\s]+?)(\s*$|\s*\n)", re.MULTILINE)


def _translate_plan_fit_lines(text: str) -> str:
    """Translate the comma list in 'Supports primary strategy via: tag, tag' lines."""
    def repl(match: re.Match) -> str:
        prefix, tag_list, tail = match.group(1), match.group(2), match.group(3)
        tags = [t.strip() for t in tag_list.split(",") if t.strip()]
        readable = [TAG_TO_WORDS.get(t, t.replace("_", " ")) for t in tags]
        return f"{prefix}{', '.join(readable)}{tail}"
    return _PLAN_FIT_VIA.sub(repl, text)


_SCORE_PAREN = re.compile(r"\s*\((commander_defined_emergent|mechanical_micro_archetype|typal_strategy_shape|niche_theme),\s*score\s*-?\d+\)")
_EVIDENCE_HIT_PHRASES = re.compile(
    r";?\s*\d+\s+(anchor/support|payoff|enabler)\s+role\s+hits\b"
)
_EVIDENCE_LEADING_SEMI = re.compile(r"(Primary evidence:\s*);\s*", re.IGNORECASE)


def _strip_internal_scoring_text(text: str) -> str:
    """Strip raw taxonomy parentheticals and role-hit counter phrases from user-facing strings."""
    text = _SCORE_PAREN.sub("", text)
    text = _EVIDENCE_HIT_PHRASES.sub("", text)
    # Strip a "specific strategy label avoids generic Typal Strategy" trailing dev note.
    text = re.sub(r";?\s*specific strategy label avoids generic Typal Strategy", "", text)
    text = re.sub(r";?\s*commander support:\s*\w+", "", text)
    text = _EVIDENCE_LEADING_SEMI.sub(r"\1", text)
    # Collapse any double semicolons left behind.
    text = re.sub(r";\s*;\s*", "; ", text)
    # Drop the entire "Primary evidence:" bullet if nothing meaningful remains after the colon.
    text = re.sub(r"(?m)^\s*-\s*Primary evidence:\s*[;\s.]*$\n?", "", text)
    return text


_INLINE_METADATA_TRUNCATE = re.compile(
    r"(?P<keep>.+?)(?P<meta>[;.]?\s*(?:Protected Label:|Initial flag:|Philosophy adjustment:).*)$"
)


def _strip_inline_pipeline_metadata(text: str) -> str:
    """For lines that contain inline 'Protected Label:' / 'Initial flag:' / 'Philosophy adjustment:'
    trailing metadata after a user-friendly sentence, drop everything from the first metadata marker
    to end of line.

    This handles the 'Philosophy note: **Card:** friendly text. Protected Label: X; Initial flag: Y; ...'
    pattern where the dev metadata is glued onto the friendly sentence rather than a separate bullet.
    """
    kept: list[str] = []
    for line in text.splitlines():
        match = _INLINE_METADATA_TRUNCATE.search(line)
        if not match:
            kept.append(line)
            continue
        keep_portion = match.group("keep")
        # Require some actual word content in the keep portion — not just bullet markers / whitespace.
        if not re.search(r"\w", keep_portion):
            # No user content before the metadata. Drop the whole line.
            continue
        trimmed = keep_portion.rstrip().rstrip(";").rstrip()
        if not trimmed.endswith("."):
            trimmed += "."
        kept.append(trimmed)
    return "\n".join(kept)


def _clean_spacing(text: str) -> str:
    text = re.sub(r"(?m)^#\s*$\n?", "", text)
    # Ensure a blank line before H2 and H3 headers (some sections get glued together
    # after section removal).
    text = re.sub(r"(\S)\n(## )", r"\1\n\n\2", text)
    text = re.sub(r"(\S)(### )", r"\1\n\n\2", text)
    text = re.sub(r"(?m)^###\s*$\n?", "", text)
    text = re.sub(r"(?m)^\s*-\s*$\n?", "", text)
    # Drop any stub bullet that became just "  -." or "- ." after metadata strip.
    text = re.sub(r"(?m)^\s*-\s*\.\s*$\n?", "", text)
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

    for title in SUBSECTION_TITLES_TO_REMOVE:
        cleaned = _remove_subsection(cleaned, title)

    cleaned = _strip_internal_scoring_text(cleaned)
    # Drop standalone "- Protected Label:" / "- Initial flag:" / "- Philosophy adjustment:" bullets
    # BEFORE the inline-metadata-strip so they're fully removed rather than reduced to "-." stubs.
    cleaned = _drop_or_rewrite_lines(cleaned)
    cleaned = _strip_inline_pipeline_metadata(cleaned)
    cleaned = _translate_role_snapshot(cleaned)
    cleaned = _translate_plan_fit_lines(cleaned)
    cleaned = _translate_replaceability_lines(cleaned)
    cleaned = _strip_windows_paths(cleaned)
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
