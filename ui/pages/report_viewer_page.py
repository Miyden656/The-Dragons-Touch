"""
v1.1.22.3-dev clarifies the AI Handoff Review lane as Manual Context Review so context-dependent/protected cards do not look like simple off-plan mistakes.
Report Viewer page builder for The Dragon's Touch.

v0.10.5.3.3 Report Viewer Developer Mode Visibility Hotfix:
- Report nav visibility is controlled by Interface Mode.

v0.10.5.6-dev — Report Viewer User Mode Final Polish:
- User Mode / Developer Mode final polish.

v0.10.6.1-dev:
- Combo findings are always part of the deck report when combo data is available.

v0.10.6.2-dev:
- Combo findings are always part of the deck report when combo data is available.
- User Mode remains AI Handoff only; Developer Mode exposes raw report tools.
- Report nav is always in layout but hidden in User Mode.
- Dev View button is refreshed dynamically from Interface Mode.

v0.10.4.4-dev restores the clean Report Viewer mode split after the Simple View regression.
User-Facing Mode shows only AI Handoff; Dev-Facing Mode restores Detected Reports plus raw Report Preview/Status tools.
User View keeps AI handoff controls, then fills Summary / Owned / Examples /
Review / Safety with lightweight snippets from the generated deck report.

v0.10.1.10 Direct File Layout Replacement keeps the AI handoff lane intact,
while moving Dev View status/actions into a separate right-side column so
Report File Preview and Loaded Report Status no longer visually collide.

v0.10.1.7-dev keeps the v0.10.1.6 User View / Dev View split, then makes
User View immediately useful as an AI handoff lane:

- Copy User Prompt
- Copy Deck Report
- Open User Prompt
- Open Deck Report

Simple View remains a preview-only section until v0.10.2 report extraction.
This module still does not own backend execution, report generation, recommendation
logic, report parsing, candidate ranking, or automatic swaps.
"""

from pathlib import Path
import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

try:
    from ui.constants import APP_VERSION
    from ui.widgets import add_shadow, TexturedPanel, ReportCard
except ImportError:  # Allows direct local execution from inside the ui/ folder.
    from constants import APP_VERSION
    from widgets import add_shadow, TexturedPanel, ReportCard


def _make_simple_view_detail_box():
    box = QPlainTextEdit()
    box.setReadOnly(True)
    box.setObjectName("simpleViewUserDetail")
    box.setMinimumHeight(240)
    box.setMaximumHeight(420)
    box.setFrameShape(QFrame.NoFrame)
    box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    box.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    box.setLineWrapMode(QPlainTextEdit.WidgetWidth)
    box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    return box


def _make_report_view_mode_button(label, tooltip):
    button = QPushButton(label)
    button.setObjectName("utilityButton")
    button.setMinimumHeight(38)
    button.setToolTip(tooltip)
    return button


def _report_role_match(path_text, role):
    lower = Path(path_text).name.lower()
    if role == "user_prompt":
        return "_user_guided_prompt" in lower or "user_prompt" in lower or "guided_prompt" in lower
    if role == "deck_report":
        return "_deck_report" in lower or lower.endswith("deck_report.md")
    return False


def _find_report_role_path(window, role):
    candidates = []
    candidates.extend(getattr(window.state, "last_normal_report_files", []) or [])
    candidates.extend(getattr(window.state, "last_output_files", []) or [])
    for path_text in candidates:
        if _report_role_match(path_text, role):
            path = Path(path_text)
            if path.exists() and path.is_file():
                return str(path)
    return ""


def _role_display_name(role):
    if role == "user_prompt":
        return "User Prompt"
    if role == "deck_report":
        return "Deck Report"
    return "Report"



def _normalize_heading_text(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def _read_text_file_safely(path_text):
    if not path_text:
        return ""
    try:
        return Path(path_text).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _is_markdown_heading(line):
    stripped = line.strip()
    return stripped.startswith("#") and stripped.lstrip("#").strip()


def _heading_level(line):
    stripped = line.lstrip()
    return len(stripped) - len(stripped.lstrip("#"))


def _extract_markdown_section(text, heading_terms, max_lines=22):
    """Return a compact markdown section snippet by matching heading text.

    This is intentionally lightweight. It does not change report generation or
    recommendation logic; it only extracts already-generated report text for the
    User View presentation layer.
    """
    if not text:
        return ""

    terms = [_normalize_heading_text(term) for term in heading_terms]
    lines = text.splitlines()

    for idx, line in enumerate(lines):
        if not _is_markdown_heading(line):
            continue
        normalized = _normalize_heading_text(line.lstrip("#").strip())
        if not any(term and term in normalized for term in terms):
            continue

        level = _heading_level(line)
        collected = [line.strip()]
        for next_line in lines[idx + 1:]:
            if _is_markdown_heading(next_line) and _heading_level(next_line) <= level:
                break
            collected.append(next_line.rstrip())
            if len(collected) >= max_lines:
                collected.append("...")
                break
        return "\n".join(collected).strip()

    return ""


def _extract_first_matching_block(text, marker_terms, max_lines=18):
    if not text:
        return ""

    terms = [_normalize_heading_text(term) for term in marker_terms]
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        normalized = _normalize_heading_text(line)
        if not any(term and term in normalized for term in terms):
            continue

        collected = [line.strip()]
        for next_line in lines[idx + 1:]:
            if _is_markdown_heading(next_line) and len(collected) > 1:
                break
            collected.append(next_line.rstrip())
            if len(collected) >= max_lines:
                collected.append("...")
                break
        return "\n".join(collected).strip()

    return ""




def _strip_markdown_heading(line):
    stripped = line.strip()
    if stripped.startswith("#"):
        return stripped.lstrip("#").strip()
    return stripped


def _clean_report_display_line(line):
    """Convert generated markdown-ish report lines into friendlier plain text."""
    raw = line.rstrip()
    stripped = raw.strip()

    if not stripped:
        return ""

    if stripped.startswith("```"):
        return ""

    # Remove markdown heading marks but keep the heading text.
    if stripped.startswith("#"):
        return _strip_markdown_heading(stripped)

    # Report generator often uses quote blocks for notes. Make them readable.
    if stripped.startswith(">"):
        cleaned = stripped.lstrip(">").strip()
        if not cleaned:
            return ""
        return f"Note: {cleaned}"

    # Normalize common markdown bullets.
    if stripped.startswith("- "):
        return f"• {stripped[2:].strip()}"

    if stripped.startswith("* "):
        return f"• {stripped[2:].strip()}"

    # Remove accidental inline heading glue from extracted sections.
    stripped = stripped.replace("### ", "")
    stripped = stripped.replace("## ", "")
    stripped = stripped.replace("# ", "")

    return stripped


def _polish_report_snippet(snippet, max_lines=18):
    """Polish extracted report text for User View.

    This intentionally stays plain text because the current panel is a
    QPlainTextEdit. It is presentation-only and does not alter report data,
    recommendation logic, ranking, or candidate generation.
    """
    if not snippet:
        return ""

    cleaned_lines = []
    previous_blank = False

    for raw_line in snippet.splitlines():
        line = _clean_report_display_line(raw_line)

        if not line:
            if cleaned_lines and not previous_blank:
                cleaned_lines.append("")
                previous_blank = True
            continue

        cleaned_lines.append(line)
        previous_blank = False

    # Remove leading/trailing blank lines.
    while cleaned_lines and not cleaned_lines[0].strip():
        cleaned_lines.pop(0)
    while cleaned_lines and not cleaned_lines[-1].strip():
        cleaned_lines.pop()

    if len(cleaned_lines) > max_lines:
        cleaned_lines = cleaned_lines[:max_lines] + ["...", "Additional details are available in the full generated report."]

    return "\n".join(cleaned_lines).strip()


def _section_header(title, file_name, summary_line):
    return (
        f"{title}\n"
        f"{'=' * min(len(title), 42)}\n\n"
        f"Source: {file_name}\n\n"
        f"{summary_line}\n"
    )


def _compact_snippet(title, file_name, snippet, fallback, summary_line="Extracted from the generated deck report."):
    if snippet:
        polished = _polish_report_snippet(snippet)
        return f"{_section_header(title, file_name, summary_line)}\n{polished}"
    return f"{title}\n{'=' * min(len(title), 42)}\n\n{fallback}"


def _load_deck_report_text(window):
    report_path = _find_report_role_path(window, "deck_report")
    if not report_path:
        return "", ""
    return report_path, _read_text_file_safely(report_path)


def _build_summary_section(window):
    report_path, report_text = _load_deck_report_text(window)
    file_name = Path(report_path).name if report_path else "No deck report detected"

    candidates = [
        _extract_markdown_section(report_text, ["Strategy Read", "Strategy", "Deck Plan"], max_lines=18),
        _extract_markdown_section(report_text, ["Replacement / Addition Needs", "Replacement Candidate Engine Preview"], max_lines=20),
        _extract_markdown_section(report_text, ["Cut Pressure Review", "Possible Cut Review"], max_lines=18),
    ]
    snippet = next((item for item in candidates if item), "")

    return _compact_snippet(
        "Deck Need Summary",
        file_name,
        snippet,
        "Run Analysis first, then return here. This will show a compact strategy/needs summary from the generated deck report.",
        "Quick read of the deck's plan, needs, or tuning pressure.",
    )



def _build_strategy_brain_section(window):
    """Show the deck's detected strategy — primary, secondary, confidence, synergy packages."""
    report_path, report_text = _load_deck_report_text(window)
    file_name = Path(report_path).name if report_path else "No deck report detected"

    snippet = _extract_markdown_section(report_text, ["Strategy Read"], max_lines=40)

    return _compact_snippet(
        "Strategy Detection",
        file_name,
        snippet,
        "Run Analysis first, then return here. Strategy detection appears once the deck report is generated.",
        "What The Dragon's Touch thinks this deck is trying to do. Use this as context; pilot intent still decides.",
    )


def _build_strategy_shell_section(window):
    report_path, report_text = _load_deck_report_text(window)
    file_name = Path(report_path).name if report_path else "No deck report detected"

    snippet = _extract_markdown_section(report_text, ["Build From Collection Strategy Shell Planning", "Strategy Shell Planning"], max_lines=42)

    if snippet:
        return _compact_snippet(
            "Strategy Shell",
            file_name,
            snippet,
            "",
            "Strategy Knowledge rough shell-planning context surfaced from the generated deck report.",
        )

    try:
        from reports.strategy_bridge.strategy_shell_planning import build_strategy_shell_viewer_summary
        fallback = build_strategy_shell_viewer_summary()
    except Exception:
        fallback = (
            "Strategy Shell Planning\n"
            "=======================\n\n"
            "Run Analysis first, then return here. Strategy shell planning appears when the generated report includes the v1.4.14 shell section."
        )

    return fallback


def _build_exact_card_candidates_section(window):
    report_path, report_text = _load_deck_report_text(window)
    file_name = Path(report_path).name if report_path else "No deck report detected"

    snippet = _extract_markdown_section(report_text, ["Exact Card Candidate Selection Preview", "Exact Card Candidate Preview"], max_lines=42)

    if snippet:
        return _compact_snippet(
            "Exact Card Candidates",
            file_name,
            snippet,
            "",
            "Strategy Knowledge exact-card candidates surfaced from the generated deck report.",
        )

    try:
        from reports.strategy_bridge.exact_card_candidate_preview import build_exact_card_candidate_viewer_summary
        fallback = build_exact_card_candidate_viewer_summary()
    except Exception:
        fallback = (
            "Exact Card Candidate Preview\n"
            "============================\n\n"
            "Run Analysis first, then return here. Candidate preview appears when the generated report includes the v1.4.15 candidate section."
        )

    return fallback


def _build_strategy_role_counts_section(window):
    report_path, report_text = _load_deck_report_text(window)
    file_name = Path(report_path).name if report_path else "No deck report detected"

    snippet = _extract_markdown_section(report_text, ["Strategy-Based Role Count Generation", "Strategy Role Count Generation"], max_lines=42)

    if snippet:
        return _compact_snippet(
            "Role Counts",
            file_name,
            snippet,
            "",
            "Strategy Knowledge target role-count bands surfaced from the generated deck report.",
        )

    try:
        from reports.strategy_bridge.strategy_role_count_generation import build_strategy_role_count_viewer_summary
        fallback = build_strategy_role_count_viewer_summary()
    except Exception:
        fallback = (
            "Strategy Role Count Generation\n"
            "==============================\n\n"
            "Run Analysis first, then return here. Role count target bands appear when the generated report includes the v1.4.16 role-count section."
        )

    return fallback


def _build_mana_base_planning_section(window):
    report_path, report_text = _load_deck_report_text(window)
    file_name = Path(report_path).name if report_path else "No deck report detected"

    snippet = _extract_markdown_section(report_text, ["Mana Base Planning"], max_lines=42)

    if snippet:
        return _compact_snippet(
            "Mana Base",
            file_name,
            snippet,
            "",
            "Strategy Knowledge mana-base planning surfaced from the generated deck report.",
        )

    try:
        from reports.strategy_bridge.mana_base_planning import build_mana_base_viewer_summary
        fallback = build_mana_base_viewer_summary()
    except Exception:
        fallback = (
            "Mana Base Planning\n"
            "==================\n\n"
            "Run Analysis first, then return here. Mana-base planning appears when the generated report includes the v1.4.17 mana section."
        )

    return fallback


def _build_land_insertion_preview_section(window):
    report_path, report_text = _load_deck_report_text(window)
    file_name = Path(report_path).name if report_path else "No deck report detected"

    snippet = _extract_markdown_section(report_text, ["Land Insertion Preview"], max_lines=42)

    if snippet:
        return _compact_snippet(
            "Land Insertion",
            file_name,
            snippet,
            "",
            "Strategy Knowledge land insertion preview surfaced from the generated deck report.",
        )

    try:
        from reports.strategy_bridge.land_insertion_preview import build_land_insertion_viewer_summary
        fallback = build_land_insertion_viewer_summary()
    except Exception:
        fallback = (
            "Land Insertion Preview\n"
            "======================\n\n"
            "Run Analysis first, then return here. Land insertion preview appears when the generated report includes the v1.4.18 land insertion section."
        )

    return fallback


def _build_full_100_card_draft_preview_section(window):
    report_path, report_text = _load_deck_report_text(window)
    file_name = Path(report_path).name if report_path else "No deck report detected"

    snippet = _extract_markdown_section(report_text, ["Full 100-Card Draft Preview"], max_lines=42)

    if snippet:
        return _compact_snippet(
            "Full Draft Preview",
            file_name,
            snippet,
            "",
            "Strategy Knowledge full draft preview surfaced from the generated deck report.",
        )

    try:
        from reports.strategy_bridge.full_100_card_draft_preview import build_full_100_card_draft_viewer_summary
        fallback = build_full_100_card_draft_viewer_summary()
    except Exception:
        fallback = (
            "Full 100-Card Draft Preview\n"
            "===========================\n\n"
            "Run Analysis first, then return here. Full draft preview appears when the generated report includes the v1.4.19 full draft section."
        )

    return fallback


def _build_final_inclusion_lock_section(window):
    report_path, report_text = _load_deck_report_text(window)
    file_name = Path(report_path).name if report_path else "No deck report detected"

    snippet = _extract_markdown_section(report_text, ["Final Inclusion Lock Integration", "Final Inclusion Lock"], max_lines=42)

    if snippet:
        return _compact_snippet(
            "Final Inclusion Lock",
            file_name,
            snippet,
            "",
            "Strategy Knowledge final inclusion lock surfaced from the generated deck report.",
        )

    try:
        from reports.strategy_bridge.final_inclusion_lock import build_final_inclusion_lock_viewer_summary
        fallback = build_final_inclusion_lock_viewer_summary()
    except Exception:
        fallback = (
            "Final Inclusion Lock\n"
            "====================\n\n"
            "Run Analysis first, then return here. Final inclusion lock appears when the generated report includes the v1.4.22 lock section."
        )

    return fallback


def _build_finished_mana_base_section(window):
    report_path, report_text = _load_deck_report_text(window)
    file_name = Path(report_path).name if report_path else "No deck report detected"

    snippet = _extract_markdown_section(report_text, ["Finished Mana Base Generation Integration", "Finished Mana Base"], max_lines=42)

    if snippet:
        return _compact_snippet(
            "Finished Mana Base",
            file_name,
            snippet,
            "",
            "Strategy Knowledge finished mana-base artifact surfaced from the generated deck report.",
        )

    try:
        from reports.strategy_bridge.finished_mana_base_generation import build_finished_mana_base_viewer_summary
        fallback = build_finished_mana_base_viewer_summary()
    except Exception:
        fallback = (
            "Finished Mana Base\n"
            "==================\n\n"
            "Run Analysis first, then return here. Finished mana-base artifacts appear when the generated report includes the v1.4.23 mana-base section."
        )

    return fallback


def _build_land_deck_write_section(window):
    report_path, report_text = _load_deck_report_text(window)
    file_name = Path(report_path).name if report_path else "No deck report detected"

    snippet = _extract_markdown_section(report_text, ["Land Deck-Write Integration", "Land Deck-Write"], max_lines=42)

    if snippet:
        return _compact_snippet(
            "Land Deck-Write",
            file_name,
            snippet,
            "",
            "Strategy Knowledge land deck-write artifact surfaced from the generated deck report.",
        )

    try:
        from reports.strategy_bridge.land_deck_write_integration import build_land_deck_write_viewer_summary
        fallback = build_land_deck_write_viewer_summary()
    except Exception:
        fallback = (
            "Land Deck-Write\n"
            "===============\n\n"
            "Run Analysis first, then return here. Land deck-write artifacts appear when the generated report includes the v1.4.24 land-write section."
        )

    return fallback


def _build_final_deck_export_section(window):
    report_path, report_text = _load_deck_report_text(window)
    file_name = Path(report_path).name if report_path else "No deck report detected"

    snippet = _extract_markdown_section(report_text, ["Final Deck Export Integration", "Final Deck Export"], max_lines=42)

    if snippet:
        return _compact_snippet(
            "Final Deck Export",
            file_name,
            snippet,
            "",
            "Strategy Knowledge final deck export artifact surfaced from the generated deck report.",
        )

    try:
        from reports.strategy_bridge.final_deck_export_integration import build_final_deck_export_viewer_summary
        fallback = build_final_deck_export_viewer_summary()
    except Exception:
        fallback = (
            "Final Deck Export\n"
            "=================\n\n"
            "Run Analysis first, then return here. Final deck export artifacts appear when the generated report includes the v1.4.25 export section."
        )

    return fallback


def _build_old_strategy_deprecation_section(window):
    report_path, report_text = _load_deck_report_text(window)
    file_name = Path(report_path).name if report_path else "No deck report detected"

    snippet = _extract_markdown_section(report_text, ["Old Strategy System Deprecation / Fallback Cleanup", "Old Strategy System Deprecation"], max_lines=42)

    if snippet:
        return _compact_snippet(
            "Old Strategy Deprecation",
            file_name,
            snippet,
            "",
            "Strategy Knowledge old-system deprecation status surfaced from the generated deck report.",
        )

    try:
        from reports.strategy_bridge.old_strategy_deprecation import build_old_strategy_deprecation_viewer_summary
        fallback = build_old_strategy_deprecation_viewer_summary()
    except Exception:
        fallback = (
            "Old Strategy System Deprecation\n"
            "===============================\n\n"
            "Run Analysis first, then return here. Deprecation status appears when the generated report includes the v1.4.26 deprecation section."
        )

    return fallback


def _build_v1_4_regression_section(window):
    report_path, report_text = _load_deck_report_text(window)
    file_name = Path(report_path).name if report_path else "No deck report detected"

    snippet = _extract_markdown_section(report_text, ["v1.4 Full Regression / Lock Candidate"], max_lines=42)

    if snippet:
        return _compact_snippet(
            "v1.4 Regression",
            file_name,
            snippet,
            "",
            "Strategy Knowledge v1.4 regression status surfaced from the generated deck report.",
        )

    try:
        from reports.strategy_bridge.strategy_v1_4_regression_lock_candidate import build_v1_4_regression_viewer_summary
        fallback = build_v1_4_regression_viewer_summary()
    except Exception:
        fallback = (
            "v1.4 Full Regression / Lock Candidate\n"
            "=====================================\n\n"
            "Run Analysis first, then return here. v1.4 regression status appears when the generated report includes the v1.4.27 regression section."
        )

    return fallback


def _build_v1_4_stable_lock_section(window):
    report_path, report_text = _load_deck_report_text(window)
    file_name = Path(report_path).name if report_path else "No deck report detected"

    snippet = _extract_markdown_section(report_text, ["v1.4 Stable Lock / Handoff Package"], max_lines=42)

    if snippet:
        return _compact_snippet(
            "v1.4 Stable Lock",
            file_name,
            snippet,
            "",
            "Strategy Knowledge v1.4 stable lock status surfaced from the generated deck report.",
        )

    try:
        from reports.strategy_bridge.strategy_v1_4_stable_lock_handoff import build_v1_4_stable_lock_viewer_summary
        fallback = build_v1_4_stable_lock_viewer_summary()
    except Exception:
        fallback = (
            "v1.4 Stable Lock / Handoff Package\n"
            "===================================\n\n"
            "Run the v1.4.28 stable lock tool first, then return here."
        )

    return fallback


def _looks_like_candidate_line(line):
    """Best-effort display filter for card/candidate lines in User View.

    This is intentionally presentation-only. It does not rank, recommend,
    validate legality, or modify candidate generation.
    """
    stripped = line.strip()
    if not stripped:
        return False

    lowered = stripped.lower()
    skip_markers = [
        "note:",
        "these are owned cards",
        "use them as",
        "automatic swaps",
        "collection-first remains primary",
        "not confirmed owned",
        "this section",
        "preview:",
        "recommendation authority",
        "fallback mode",
        "full-card-pool",
        "dragon gate manual review",
        "they are kept",
        "they are still review",
    ]
    if any(marker in lowered for marker in skip_markers):
        return False

    if stripped.startswith("#") or stripped.startswith(">"):
        return False

    if stripped.startswith(("- ", "* ", "• ")):
        return True

    if re.match(r"^\d+[\).\s-]+", stripped):
        return True

    if ":" in stripped and len(stripped.split(":", 1)[0].strip()) <= 60:
        return True

    if " — " in stripped or " - " in stripped:
        return True

    return False


def _candidate_display_lines_from_section(snippet, max_lines=14):
    if not snippet:
        return ""

    lines = []
    for raw in snippet.splitlines():
        cleaned = _clean_report_display_line(raw)
        if not cleaned:
            continue
        if _looks_like_candidate_line(cleaned):
            lines.append(cleaned)
        if len(lines) >= max_lines:
            lines.append("...")
            lines.append("Additional owned-candidate details are available in the full generated report.")
            break

    return "\n".join(lines).strip()


def _owned_candidate_snippet_from_report(report_text):
    # Headings updated for v1.5.32: the post-processor renames "Collection Pull Candidates"
    # to "Collection-Based Review Candidates" and "Top Ranked Collection-First Candidates"
    # to "Best Owned Cards to Review", so look up the renamed headings too.
    sections = [
        _extract_markdown_section(report_text, ["Best Owned Cards to Review"], max_lines=60),
        _extract_markdown_section(report_text, ["Possible Owned Candidates"], max_lines=60),
        _extract_markdown_section(report_text, ["Collection-Based Review Candidates"], max_lines=60),
        _extract_markdown_section(report_text, ["Strong Owned Candidates"], max_lines=42),
        _extract_markdown_section(report_text, ["Top Ranked Collection-First Candidates"], max_lines=42),
        _extract_markdown_section(report_text, ["Collection Pull Candidates"], max_lines=42),
        _extract_markdown_section(report_text, ["Collection Candidates"], max_lines=42),
    ]

    for section in sections:
        candidate_lines = _candidate_display_lines_from_section(section)
        if candidate_lines:
            return candidate_lines

    return next((section for section in sections if section), "")

def _build_owned_section(window):
    report_path, report_text = _load_deck_report_text(window)
    file_name = Path(report_path).name if report_path else "No deck report detected"

    snippet = _owned_candidate_snippet_from_report(report_text)

    return _compact_snippet(
        "Collection Candidates",
        file_name,
        snippet,
        "Owned-card suggestions will appear here when the deck report includes collection-first candidate sections. Collection-first remains primary.",
        "Owned or collection-first candidates worth reviewing. These are not automatic swaps.",
    )

def _build_examples_section(window):
    report_path, report_text = _load_deck_report_text(window)
    file_name = Path(report_path).name if report_path else "No deck report detected"

    candidates = [
        _extract_markdown_section(report_text, ["Exact Full-Pool Candidate Preview"], max_lines=24),
        _extract_markdown_section(report_text, ["Full-Card-Pool Fallback Preview"], max_lines=24),
        _extract_markdown_section(report_text, ["Full Pool", "Full-Pool Examples"], max_lines=20),
    ]
    snippet = next((item for item in candidates if item), "")

    return _compact_snippet(
        "Full-Pool Examples",
        file_name,
        snippet,
        "Full-pool examples will appear here when present. These are example-only and not confirmed owned.",
        "Example-only outside-card ideas. These are not confirmed owned.",
    )


def _build_review_section(window):
    report_path, report_text = _load_deck_report_text(window)
    file_name = Path(report_path).name if report_path else "No deck report detected"

    candidates = [
        _extract_markdown_section(report_text, ["Possible Off-Plan / Manual Context Review Examples"], max_lines=24),
        _extract_markdown_section(report_text, ["Manual Context Review"], max_lines=24),
        _extract_markdown_section(report_text, ["Manual Review"], max_lines=24),
        _extract_markdown_section(report_text, ["Context-Dependent Cards to Review Manually"], max_lines=24),
        _extract_markdown_section(report_text, ["Cards to Review Manually"], max_lines=24),
        _extract_first_matching_block(report_text, ["manual context review", "manual review", "low confidence", "caution-heavy"], max_lines=18),
    ]
    snippet = next((item for item in candidates if item), "")

    return _compact_snippet(
        "Manual Context Review",
        file_name,
        snippet,
        "Low-confidence, filtered, caution-heavy, or context-dependent cards will appear here when the deck report identifies them.",
        "These are pilot/context review flags, not automatic cuts. Some may be protected elsewhere by v1.1 philosophy, commander, synergy, or role-context logic.",
    )


def _build_safety_section(window):
    report_path, report_text = _load_deck_report_text(window)
    file_name = Path(report_path).name if report_path else "No deck report detected"

    candidates = [
        _extract_markdown_section(report_text, ["How to Read This Review"], max_lines=20),
        _extract_markdown_section(report_text, ["User-Facing Boundaries"], max_lines=20),
        _extract_markdown_section(report_text, ["Safety", "Safety Notes"], max_lines=20),
        _extract_first_matching_block(report_text, ["Automatic swaps", "collection-first", "not confirmed owned"], max_lines=20),
    ]
    snippet = next((item for item in candidates if item), "")

    fallback = (
        "No automatic swaps.\n"
        "Collection-first remains primary.\n"
        "Full-pool examples are not confirmed owned.\n"
        "Budget is not checked unless the report says otherwise.\n"
        "Bracket/table-fit caution may apply.\n"
        "Combo findings are shown when combo data exists in the loaded report."
    )

    return _compact_snippet(
        "Safety Notes",
        file_name,
        snippet,
        fallback,
        "Boundaries and cautions for using this report safely.",
    )



def _extract_markdown_section_by_exact_heading(text, heading_terms, max_lines=220):
    """Extract a section by heading match, allowing deeper combo sections to stay intact."""
    if not text:
        return ""

    terms = [_normalize_heading_text(term) for term in heading_terms]
    lines = text.splitlines()

    for idx, line in enumerate(lines):
        if not _is_markdown_heading(line):
            continue
        normalized = _normalize_heading_text(line.lstrip("#").strip())
        if not any(term and term in normalized for term in terms):
            continue

        level = _heading_level(line)
        collected = [line.strip()]
        for next_line in lines[idx + 1:]:
            if _is_markdown_heading(next_line) and _heading_level(next_line) <= level:
                break
            collected.append(next_line.rstrip())
            if len(collected) >= max_lines:
                collected.append("...")
                collected.append("Additional combo details are available in the full generated report.")
                break
        return "\n".join(collected).strip()

    return ""


def _extract_combo_awareness_text(report_text):
    candidates = [
        _extract_markdown_section_by_exact_heading(report_text, ["Combo analysis"], max_lines=360),
        _extract_markdown_section_by_exact_heading(report_text, ["Combo analysis Section"], max_lines=360),
        _extract_markdown_section_by_exact_heading(report_text, ["Commander Spellbook"], max_lines=360),
        _extract_markdown_section_by_exact_heading(report_text, ["Combo Tracker"], max_lines=360),
    ]
    return next((item for item in candidates if item), "")


def _extract_combo_summary_lines(combo_text):
    wanted = [
        "Infinite combos found in deck",
        "Relevant potential combos found",
        "Dragon's Touch Potential Combos",
        "Collection-completable potential combos",
        "Collection completion check",
    ]
    lines = []
    for raw in combo_text.splitlines():
        cleaned = _clean_report_display_line(raw)
        lowered = cleaned.lower()
        if any(item.lower() in lowered for item in wanted):
            lines.append(cleaned)
    return "\n".join(lines).strip()


def _extract_combo_subsection(combo_text, heading_terms, max_lines=180):
    return _extract_markdown_section_by_exact_heading(combo_text, heading_terms, max_lines=max_lines)


def _split_combo_blocks(section_text):
    """Best-effort block splitter for combo listings in generated markdown."""
    if not section_text:
        return []

    blocks = []
    current = []
    for raw in section_text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()

        is_combo_start = False
        if _is_markdown_heading(stripped) and _heading_level(stripped) >= 3:
            normalized = _normalize_heading_text(stripped)
            is_combo_start = bool(normalized and "combo" not in normalized and len(normalized) <= 90)
        if stripped.startswith(("- ", "* ", "• ")) and (":" in stripped or " + " in stripped or " — " in stripped):
            # Treat dense bullet lines as possible standalone combo entries.
            if current and len(current) > 1:
                blocks.append("\n".join(current).strip())
                current = []
            is_combo_start = True

        if is_combo_start and current:
            blocks.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)

    if current:
        blocks.append("\n".join(current).strip())

    return [block for block in blocks if block.strip()]


def _extract_combo_name_from_block(block):
    for raw in block.splitlines():
        cleaned = _clean_report_display_line(raw).strip("• ").strip()
        if not cleaned:
            continue
        lowered = cleaned.lower()
        if lowered.startswith(("note:", "source:", "missing", "needs", "owned", "collection")):
            continue
        if cleaned.lower() in {"combo awareness", "combo summary"}:
            continue
        # Keep the first meaningful line as the combo label.
        return cleaned[:140]
    return "Unnamed combo"


def _extract_missing_cards_from_block(block):
    """Return best-effort missing/needed card list from a combo block."""
    patterns = [
        r"missing cards?\s*[:\-]\s*(.+)",
        r"missing from deck\s*[:\-]\s*(.+)",
        r"cards? needed\s*[:\-]\s*(.+)",
        r"needed cards?\s*[:\-]\s*(.+)",
        r"needs?\s*[:\-]\s*(.+)",
        r"add\s*[:\-]\s*(.+)",
        r"owned missing cards?\s*[:\-]\s*(.+)",
        r"collection card(?:s)? needed\s*[:\-]\s*(.+)",
    ]

    for raw in block.splitlines():
        cleaned = _clean_report_display_line(raw)
        for pattern in patterns:
            match = re.search(pattern, cleaned, flags=re.IGNORECASE)
            if not match:
                continue
            value = match.group(1)
            value = re.split(r"\s+\|\s+|;|\.\s", value, maxsplit=1)[0]
            value = value.replace(" and ", ", ")
            parts = [part.strip(" .`*_") for part in re.split(r",|\+|/| & ", value) if part.strip(" .`*_")]
            # Avoid treating explanatory text as card names.
            parts = [part for part in parts if len(part) <= 80 and not part.lower().startswith(("none", "no ", "n/a"))]
            return parts

    return []


def _single_card_completion_alerts(collection_section):
    """Find owned one-card additions that appear to complete multiple combos."""
    if not collection_section:
        return ""

    blocks = _split_combo_blocks(collection_section)
    grouped = {}

    for block in blocks:
        missing_cards = _extract_missing_cards_from_block(block)
        if len(missing_cards) != 1:
            continue
        card = missing_cards[0]
        combo_name = _extract_combo_name_from_block(block)
        grouped.setdefault(card, []).append(combo_name)

    multi = {card: combos for card, combos in grouped.items() if len(combos) >= 2}
    if not multi:
        return ""

    lines = ["Single-card completion alerts", ""]
    lines.append("These collection-completable findings appear to share one missing card:")
    lines.append("")
    for card, combos in sorted(multi.items(), key=lambda item: (-len(item[1]), item[0].lower())):
        lines.append(f"• {card}: appears to complete {len(combos)} combo lines.")
        for combo in combos[:5]:
            lines.append(f"  - {combo}")
        if len(combos) > 5:
            lines.append(f"  - ...and {len(combos) - 5} more.")
    lines.append("")
    lines.append("Review before adding. This is informational and does not create automatic swaps.")
    return "\n".join(lines).strip()


def _format_combo_section(title, section_text, max_lines=160):
    if not section_text:
        return ""

    polished = _polish_report_snippet(section_text, max_lines=max_lines)
    if not polished:
        return ""

    return f"{title}\n{'-' * min(len(title), 42)}\n\n{polished}"



def _looks_like_combo_artifact_name(path_text):
    name = Path(path_text).name.lower()
    if not name.endswith((".md", ".txt")):
        return False
    combo_terms = ["combo", "combos", "spellbook", "breakdown", "isolated"]
    report_terms = ["debug", "report", "artifact", "analysis"]
    return any(term in name for term in combo_terms) and any(term in name for term in report_terms)


def _find_combo_artifact_path(window):
    """Find a full combo/breakdown artifact when the concise deck report omits details."""
    candidates = []
    candidates.extend(getattr(window.state, "last_normal_report_files", []) or [])
    candidates.extend(getattr(window.state, "last_output_files", []) or [])

    # Include nearby files in the most recent output folder, if available.
    roots = []
    current_file = getattr(window.state, "report_viewer_current_file", "") or ""
    last_output_folder = getattr(window.state, "last_output_folder", "") or ""
    if current_file:
        roots.append(Path(current_file).parent)
    if last_output_folder:
        roots.append(Path(last_output_folder))

    for root in roots:
        try:
            if root.exists() and root.is_dir():
                for path in root.rglob("*"):
                    if path.is_file() and _looks_like_combo_artifact_name(str(path)):
                        candidates.append(str(path))
        except Exception:
            continue

    seen = set()
    for path_text in candidates:
        if not path_text or path_text in seen:
            continue
        seen.add(path_text)
        path = Path(path_text)
        if path.exists() and path.is_file() and _looks_like_combo_artifact_name(path_text):
            return str(path)

    return ""


def _load_combo_artifact_text(window):
    path_text = _find_combo_artifact_path(window)
    if not path_text:
        return "", ""
    return path_text, _read_text_file_safely(path_text)


def _grouped_completion_alerts_from_section(collection_section):
    """Detect grouped lines like 'Doubling Season — Completes 3 potential combo variants.'"""
    if not collection_section:
        return ""

    lines = collection_section.splitlines()
    alerts = []
    idx = 0

    while idx < len(lines):
        line = _clean_report_display_line(lines[idx])
        # Example expected after markdown cleanup:
        # 1. **Doubling Season** — found in: ...
        # or 1. Doubling Season — found in: ...
        match = re.match(r"^\s*(?:\d+[\).\s-]+)?(?:\*\*)?(.+?)(?:\*\*)?\s+—\s+found in:", line)
        if not match:
            idx += 1
            continue

        card_name = match.group(1).strip(" `*_")
        lookahead = "\n".join(_clean_report_display_line(item) for item in lines[idx:idx + 8])
        count_match = re.search(r"Completes\s+(\d+)\s+potential combo variant", lookahead, flags=re.IGNORECASE)
        if not count_match:
            idx += 1
            continue

        count = int(count_match.group(1))
        examples = []
        example_match = re.search(r"Example variant\(s\):\s*(.+)", lookahead, flags=re.IGNORECASE)
        if example_match:
            raw_examples = example_match.group(1)
            examples = [part.strip(" .`*_") for part in raw_examples.split(";") if part.strip(" .`*_")]

        if count >= 2:
            alerts.append((card_name, count, examples))

        idx += 1

    if not alerts:
        return ""

    output = ["Single-card completion alerts", ""]
    output.append("These collection cards appear to complete multiple potential combo variants:")
    output.append("")

    for card_name, count, examples in sorted(alerts, key=lambda item: (-item[1], item[0].lower())):
        output.append(f"• {card_name}: appears to complete {count} potential combo variants.")
        for example in examples[:5]:
            output.append(f"  - {example}")
        if len(examples) > 5:
            output.append(f"  - ...and {len(examples) - 5} more examples.")
    output.append("")
    output.append("Review before adding. This is informational and does not create automatic swaps.")
    return "\n".join(output).strip()


def _expanded_single_card_completion_alerts(collection_section):
    grouped = _grouped_completion_alerts_from_section(collection_section)
    if grouped:
        return grouped
    return _single_card_completion_alerts(collection_section)


def _extract_in_deck_combo_fallback(combo_text, artifact_text):
    """Use artifact text when the concise report summary says combos exist but no list is present."""
    candidates = [
        _extract_combo_subsection(combo_text, ["Current Infinite Combos Found"], max_lines=260),
        _extract_combo_subsection(combo_text, ["Infinite Combos Found in Deck"], max_lines=260),
        _extract_combo_subsection(combo_text, ["Combos Found in Deck"], max_lines=260),
        _extract_combo_subsection(combo_text, ["Combos In Deck"], max_lines=260),
        _extract_combo_subsection(combo_text, ["Deck Combos"], max_lines=260),
        _extract_combo_subsection(combo_text, ["In-Deck Combos"], max_lines=260),
    ]
    concise = next((section for section in candidates if section), "")
    if concise:
        return concise, "deck report"

    if artifact_text:
        artifact_candidates = [
            _extract_markdown_section_by_exact_heading(artifact_text, ["Current Infinite Combos Found"], max_lines=320),
            _extract_markdown_section_by_exact_heading(artifact_text, ["Infinite Combos Found in Deck"], max_lines=320),
            _extract_markdown_section_by_exact_heading(artifact_text, ["Combos Found in Deck"], max_lines=320),
            _extract_markdown_section_by_exact_heading(artifact_text, ["Combos In Deck"], max_lines=320),
            _extract_markdown_section_by_exact_heading(artifact_text, ["Deck Combos"], max_lines=320),
            _extract_markdown_section_by_exact_heading(artifact_text, ["In-Deck Combos"], max_lines=320),
            _extract_first_matching_block(artifact_text, ["current infinite combos found", "infinite combos found in deck", "combos found in deck", "in deck combo"], max_lines=260),
        ]
        artifact_section = next((section for section in artifact_candidates if section), "")
        if artifact_section:
            return artifact_section, "combo artifact"

    return "", ""


def _combo_count_from_summary(summary_text):
    match = re.search(r"Infinite combos found in deck:\s*(\d+)", summary_text, flags=re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 0
def _build_combos_section(window):
    report_path, report_text = _load_deck_report_text(window)
    file_name = Path(report_path).name if report_path else "No deck report detected"
    artifact_path, artifact_text = _load_combo_artifact_text(window)
    artifact_name = Path(artifact_path).name if artifact_path else ""

    combo_text = _extract_combo_awareness_text(report_text)

    if not combo_text and artifact_text:
        combo_text = _extract_combo_awareness_text(artifact_text) or artifact_text
        file_name = artifact_name or file_name

    if not combo_text:
        fallback = (
            "No combo section was detected in the current deck report.\n\n"
            "If Combo analysis data was unavailable for this run, rerun with combo data available, then return here.\n\n"
            "Reminder: combo examples should remain informational and should not create automatic swaps."
        )
        return _compact_snippet(
            "Combos",
            file_name,
            "",
            fallback,
            "Combo-aware findings from the generated report when combo data is available.",
        )

    summary = _extract_combo_summary_lines(combo_text)
    in_deck, in_deck_source = _extract_in_deck_combo_fallback(combo_text, artifact_text)

    collection_complete = next(
        (
            section for section in [
                _extract_combo_subsection(combo_text, ["Collection-Completable Potential Combos"], max_lines=260),
                _extract_combo_subsection(combo_text, ["Collection Completable Potential Combos"], max_lines=260),
                _extract_combo_subsection(combo_text, ["Collection Completion"], max_lines=260),
                _extract_combo_subsection(combo_text, ["Completable From Collection"], max_lines=260),
            ] if section
        ),
        "",
    )

    potential = next(
        (
            section for section in [
                _extract_combo_subsection(combo_text, ["Relevant Potential Combos"], max_lines=220),
                _extract_combo_subsection(combo_text, ["Potential Combos"], max_lines=220),
                _extract_combo_subsection(combo_text, ["Dragon's Touch Potential Combos"], max_lines=220),
            ] if section
        ),
        "",
    )

    alerts = _expanded_single_card_completion_alerts(collection_complete)
    in_deck_count = _combo_count_from_summary(summary)

    lines = [
        "Combos",
        "======",
        "",
        f"Source: {Path(report_path).name if report_path else file_name}",
    ]

    if artifact_name:
        lines.append(f"Combo artifact: {artifact_name}")

    lines.extend([
        "",
        "Combo-aware findings from the generated report.",
        "",
    ])

    if summary:
        lines.extend(["Combo Overview", "--------------", "", _polish_report_snippet(summary, max_lines=16), ""])

    if alerts:
        lines.extend([alerts, ""])

    if in_deck:
        heading = "Every combo already found in deck"
        if in_deck_source == "combo artifact":
            heading += " (from combo artifact)"
        lines.extend([_format_combo_section(heading, in_deck, max_lines=260), ""])
    else:
        lines.extend([
            "Every combo already found in deck",
            "---------------------------------",
            "",
            f"The combo summary says {in_deck_count} in-deck combo(s) exist, but no dedicated in-deck combo list was detected in the concise report.",
            "Check the full generated report for the full Combo analysis artifact/report, or confirm the isolated combo breakdown file is being generated in the output folder.",
            "",
        ])

    if collection_complete:
        lines.extend([_format_combo_section("Collection-completable potential combos", collection_complete, max_lines=220), ""])
    else:
        lines.extend([
            "Collection-completable potential combos",
            "---------------------------------------",
            "",
            "No dedicated collection-completable combo section was detected.",
            "",
        ])

    if potential and potential != collection_complete:
        lines.extend([_format_combo_section("Relevant potential combos", potential, max_lines=120), ""])

    lines.extend([
        "Boundary",
        "--------",
        "",
        "Combo findings are informational by default.",
        "Missing cards are not automatic add recommendations unless combo optimization is intentionally enabled later.",
    ])

    return "\n".join(part for part in lines if part is not None).strip()

def build_report_viewer_page(window):
    page, layout = window.page_container(
        "Report Viewer",
        f"Read generated reports from backend-created output folders. {APP_VERSION} keeps User-Facing Mode focused on normal reports and Dev-Facing Mode available for breakdown review."
    )
    body = QWidget()
    body_layout = QHBoxLayout(body)
    body_layout.setContentsMargins(0, 0, 0, 0)
    body_layout.setSpacing(14)

    # v0.10.4.4 mode split restore:
    # User-Facing Mode should show only the AI Handoff lane.
    # Dev-Facing Mode restores Detected Report Files and raw report tools.
    show_report_nav = window.is_dev_mode()

    report_nav = TexturedPanel(window.theme, kind="iron", glow=False)
    report_nav.setFixedWidth(330)
    window.report_viewer_nav_panel = report_nav
    add_shadow(report_nav, blur=22, y=7)
    rn_layout = QVBoxLayout(report_nav)
    rn_layout.setContentsMargins(16, 16, 16, 16)
    rn_layout.setSpacing(10)

    cap = QLabel("DETECTED REPORT FILES")
    cap.setObjectName("smallCaps")
    rn_layout.addWidget(cap)

    mode_note = QLabel(window.interface_mode_report_viewer_note())
    mode_note.setObjectName("mutedText")
    mode_note.setWordWrap(True)
    rn_layout.addWidget(mode_note)

    rn_layout.addWidget(window.default_note("User-Facing Mode shows normal reports by default. Dev-Facing Mode also shows breakdown/debug files."))

    file_scroll = QScrollArea()
    file_scroll.setWidgetResizable(True)
    file_inner = QWidget()
    window.report_viewer_file_buttons_layout = QVBoxLayout(file_inner)
    window.report_viewer_file_buttons_layout.setContentsMargins(0, 0, 6, 0)
    window.report_viewer_file_buttons_layout.setSpacing(8)
    file_scroll.setWidget(file_inner)
    rn_layout.addWidget(file_scroll, stretch=1)

    reload_btn = QPushButton("Reload Latest Reports")
    reload_btn.clicked.connect(window.reload_latest_reports_into_viewer)
    window.report_viewer_reload_button = reload_btn
    rn_layout.addWidget(reload_btn)

    open_folder_btn = QPushButton("Open Output Folder")
    open_folder_btn.clicked.connect(window.open_last_output_folder)
    rn_layout.addWidget(open_folder_btn)

    viewer_panel = TexturedPanel(window.theme, kind="iron", glow=True)
    add_shadow(viewer_panel, blur=26, y=8)
    viewer_layout = QVBoxLayout(viewer_panel)
    viewer_layout.setContentsMargins(22, 22, 22, 22)
    viewer_layout.setSpacing(14)

    # v0.10.1.7 User View AI Handoff Controls — mode selector remains, User View becomes useful.
    mode_row = QHBoxLayout()
    mode_row.setSpacing(10)

    mode_intro = QLabel(
        "User View is for AI handoff and readable guidance."
        if not window.is_dev_mode()
        else "User View is for AI handoff and readable guidance. Developer Mode exposes raw report tools."
    )
    mode_intro.setObjectName("defaultNote")
    mode_intro.setWordWrap(True)
    mode_row.addWidget(mode_intro, stretch=1)

    user_view_btn = _make_report_view_mode_button("User View", "Show the AI handoff and readable guidance lane.")
    dev_view_btn = _make_report_view_mode_button("Dev View", "Show raw report preview, search, and loaded report status.")
    # dev_view_btn's initial visibility is set after mode_row is added to its
    # parent layout (further down at viewer_layout.addLayout(mode_row)) — see
    # _set_dev_view_btn_initial_visibility() below. Calling setVisible(True)
    # on a parentless widget would briefly flash it as a top-level window.

    # v0.10.5.3.3: keep these controls addressable so Interface Mode can refresh
    # without rebuilding the Settings page or causing the mode-switch flash.
    window.report_viewer_user_view_button = user_view_btn
    window.report_viewer_dev_view_button = dev_view_btn
    window.report_viewer_mode_intro_label = mode_intro

    mode_row.addWidget(user_view_btn)
    mode_row.addWidget(dev_view_btn)
    viewer_layout.addLayout(mode_row)
    # Set dev_view_btn's initial visibility now that mode_row is parented.
    dev_view_btn.setVisible(window.is_dev_mode())

    report_mode_stack = QStackedWidget()
    report_mode_stack.setObjectName("reportViewerModeStack")
    report_mode_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    window.report_viewer_mode_stack = report_mode_stack

    # User View — AI handoff lane.
    user_view = QWidget()
    user_layout = QVBoxLayout(user_view)
    user_layout.setContentsMargins(0, 0, 0, 0)
    user_layout.setSpacing(12)

    handoff_card = ReportCard("User View — AI Handoff", window.theme, badges=[("User-facing", "protected"), ("Copy-ready", "manual")])
    handoff_card.setMinimumHeight(0)
    handoff_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    handoff_intro = QLabel(
        "Copy the User Prompt first, then copy the Deck Report when the prompt asks for it. Use the section buttons below for readable snippets."
    )
    handoff_intro.setObjectName("defaultNote")
    handoff_intro.setWordWrap(True)
    handoff_card.body.addWidget(handoff_intro)

    handoff_action_row = QHBoxLayout()
    handoff_action_row.setSpacing(8)

    copy_prompt_btn = QPushButton("Copy User Prompt")
    copy_prompt_btn.setObjectName("primaryButton")
    copy_prompt_btn.setMinimumHeight(40)
    copy_prompt_btn.setToolTip("Copy the generated user-guided prompt to the clipboard.")

    copy_report_btn = QPushButton("Copy Deck Report")
    copy_report_btn.setObjectName("primaryButton")
    copy_report_btn.setMinimumHeight(40)
    copy_report_btn.setToolTip("Copy the generated deck report to the clipboard.")

    load_prompt_btn = QPushButton("Open User Prompt")
    load_prompt_btn.setObjectName("utilityButton")
    load_prompt_btn.setMinimumHeight(40)

    load_report_btn = QPushButton("Open Deck Report")
    load_report_btn.setObjectName("utilityButton")
    load_report_btn.setMinimumHeight(40)

    handoff_action_row.addWidget(copy_prompt_btn)
    handoff_action_row.addWidget(copy_report_btn)
    handoff_action_row.addWidget(load_prompt_btn)
    handoff_action_row.addWidget(load_report_btn)
    handoff_card.body.addLayout(handoff_action_row)

    export_action_row = QHBoxLayout()
    export_action_row.setSpacing(8)

    copy_current_section_btn = QPushButton("Copy Current Section")
    copy_current_section_btn.setObjectName("utilityButton")
    copy_current_section_btn.setMinimumHeight(38)
    copy_current_section_btn.setToolTip("Copy the currently selected User View section.")

    copy_all_summary_btn = QPushButton("Copy All User View Summary")
    copy_all_summary_btn.setObjectName("utilityButton")
    copy_all_summary_btn.setMinimumHeight(38)
    copy_all_summary_btn.setToolTip("Copy the readable User View summary sections.")

    copy_ai_package_btn = QPushButton("Copy AI Handoff Package")
    copy_ai_package_btn.setObjectName("primaryButton")
    copy_ai_package_btn.setMinimumHeight(38)
    copy_ai_package_btn.setToolTip("Copy a complete handoff package for AI chat or notes.")

    copy_current_section_btn.clicked.connect(lambda checked=False: _copy_current_simple_view_section())
    copy_all_summary_btn.clicked.connect(lambda checked=False: _copy_all_user_view_summary())
    copy_ai_package_btn.clicked.connect(lambda checked=False: _copy_ai_handoff_package())

    export_action_row.addWidget(copy_current_section_btn)
    export_action_row.addWidget(copy_all_summary_btn)
    export_action_row.addWidget(copy_ai_package_btn)
    handoff_card.body.addLayout(export_action_row)


    simple_view_button_grid = QGridLayout()
    simple_view_button_grid.setSpacing(8)
    simple_view_button_grid.setContentsMargins(0, 2, 0, 2)

    simple_view_detail_box = _make_simple_view_detail_box()

    def _handoff_status_text():
        prompt_path = _find_report_role_path(window, "user_prompt")
        report_path = _find_report_role_path(window, "deck_report")
        prompt_name = Path(prompt_path).name if prompt_path else "Not detected"
        report_name = Path(report_path).name if report_path else "Not detected"
        return (
            "AI Handoff\n\n"
            "Recommended flow:\n"
            "1. Click Copy User Prompt and paste it into the AI chat.\n"
            "2. When the prompt asks for the deck report, click Copy Deck Report and paste it into the same chat.\n\n"
            f"User Prompt file: {prompt_name}\n"
            f"Deck Report file: {report_name}\n\n"
            "Boundary:\n"
            "- No automatic swaps.\n"
            "- Collection-first remains primary.\n"
            "- Full-pool examples are not confirmed owned.\n"
            "- Budget is not checked.\n"
            "- Combo findings are shown when combo data exists in the loaded report."
        )

    # v0.10.2.1 User View Report Section Extraction MVP.
    # Each section reads lightweight snippets from the generated deck report.
    # This is presentation-only; it does not change report generation or ranking.
    current_simple_view_section = {"name": "Handoff"}

    simple_view_details = {
        "Handoff": _handoff_status_text,
        "Summary": lambda: _build_summary_section(window),
        "Strategy Brain": lambda: _build_strategy_brain_section(window),
        "Strategy Shell": lambda: _build_strategy_shell_section(window),
        "Exact Candidates": lambda: _build_exact_card_candidates_section(window),
        "Role Counts": lambda: _build_strategy_role_counts_section(window),
        "Mana Base": lambda: _build_mana_base_planning_section(window),
        "Land Insertion": lambda: _build_land_insertion_preview_section(window),
        "Full Draft": lambda: _build_full_100_card_draft_preview_section(window),
        "Final Lock": lambda: _build_final_inclusion_lock_section(window),
        "Finished Mana": lambda: _build_finished_mana_base_section(window),
        "Land Write": lambda: _build_land_deck_write_section(window),
        "Final Export": lambda: _build_final_deck_export_section(window),
        "Old System": lambda: _build_old_strategy_deprecation_section(window),
        "v1.4 Regression": lambda: _build_v1_4_regression_section(window),
        "v1.4 Stable": lambda: _build_v1_4_stable_lock_section(window),
        "Owned": lambda: _build_owned_section(window),
        "Examples": lambda: _build_examples_section(window),
        "Review": lambda: _build_review_section(window),
        "Combos": lambda: _build_combos_section(window),
        "Safety": lambda: _build_safety_section(window),
    }

    def _show_simple_view_section(section_name):
        current_simple_view_section["name"] = section_name
        value = simple_view_details.get(section_name)
        simple_view_detail_box.setPlainText(value() if callable(value) else str(value or ""))

    def _simple_view_section_text(section_name):
        value = simple_view_details.get(section_name)
        return value() if callable(value) else str(value or "")

    def _copy_text_to_clipboard(title, text_value):
        # Category B (popup removal): clipboard works silently like every
        # other desktop app. User verifies by pasting. The "There is no
        # text to copy yet" nudge stays as a status update on the status
        # label (handled by category C in a later pass).
        if not text_value or not str(text_value).strip():
            return
        QApplication.clipboard().setText(str(text_value).strip())

    def _copy_current_simple_view_section():
        section_name = current_simple_view_section.get("name", "Handoff")
        _copy_text_to_clipboard(
            f"Copied {section_name}",
            _simple_view_section_text(section_name),
        )

    def _build_all_user_view_summary_text():
        ordered_sections = ["Handoff", "Summary", "Strategy Brain", "Owned", "Examples", "Review", "Combos", "Safety"]
        chunks = []
        seen = set()

        for section_name in ordered_sections:
            if section_name in seen:
                continue
            seen.add(section_name)
            section_text = _simple_view_section_text(section_name).strip()
            if not section_text:
                continue
            chunks.append(section_text)

        if not chunks:
            return ""

        return ("\n\n" + ("-" * 72) + "\n\n").join(chunks)

    def _build_ai_handoff_package_text():
        prompt_path = _find_report_role_path(window, "user_prompt")
        report_path = _find_report_role_path(window, "deck_report")
        prompt_name = Path(prompt_path).name if prompt_path else "Not detected"
        report_name = Path(report_path).name if report_path else "Not detected"

        package_intro = (
            "The Dragon's Touch — AI Handoff Package\n"
            "========================================\n\n"
            "Use this package to start or continue an AI-assisted Commander deck review.\n\n"
            f"User Prompt file: {prompt_name}\n"
            f"Deck Report file: {report_name}\n\n"
            "Workflow:\n"
            "1. Paste the User Prompt into the AI chat first.\n"
            "2. When the prompt asks for the deck report, paste the Deck Report.\n"
            "3. Use the summary sections below as a quick player-facing reference.\n\n"
            "Boundaries:\n"
            "- No automatic swaps.\n"
            "- Collection-first remains primary.\n"
            "- Full-pool examples are not confirmed owned.\n"
            "- Budget is not checked unless the report says otherwise.\n"
            "- Combo findings are informational unless combo optimization is explicitly enabled.\n"
        )

        summary = _build_all_user_view_summary_text().strip()
        if summary:
            return package_intro + "\n\n" + ("=" * 72) + "\n\n" + summary
        return package_intro

    def _copy_all_user_view_summary():
        _copy_text_to_clipboard("Copied User View Summary", _build_all_user_view_summary_text())

    def _copy_ai_handoff_package():
        _copy_text_to_clipboard("Copied AI Handoff Package", _build_ai_handoff_package_text())


    def _copy_report_role(role):
        path_text = _find_report_role_path(window, role)
        label = _role_display_name(role)
        if not path_text:
            # Category C (popup removal): surface the "run analysis first" hint inline in the detail box.
            try:
                simple_view_detail_box.setPlainText(
                    f"No generated {label.lower()} file was detected yet. "
                    "Run Analysis first, then return to Report Viewer."
                )
            except Exception:
                pass
            _show_simple_view_section("Handoff")
            return
        try:
            text = window.read_report_file_text(path_text)
        except Exception as exc:
            # Category D (popup removal): log to stderr for diagnostics, show
            # error inline in the detail box where the user is looking.
            import sys as _err_sys
            print(f"{label} Copy Failed: could not read {path_text}: {exc}", file=_err_sys.stderr)
            try:
                simple_view_detail_box.setPlainText(
                    f"Could not read {label.lower()}:\n\n{path_text}\n\nError: {exc}"
                )
            except Exception:
                pass
            return
        QApplication.clipboard().setText(text)
        _show_simple_view_section("Handoff")
        # Category B (popup removal): clipboard is silent. User can paste to verify.

    def _show_report_role_in_user_view(role):
        path_text = _find_report_role_path(window, role)
        label = _role_display_name(role)
        if not path_text:
            # Category C (popup removal): inline hint in detail box.
            try:
                simple_view_detail_box.setPlainText(
                    f"No generated {label.lower()} file was detected yet. "
                    "Run Analysis first, then return to Report Viewer."
                )
            except Exception:
                pass
            _show_simple_view_section("Handoff")
            return

        try:
            text_value = window.read_report_file_text(path_text)
        except Exception as exc:
            # Category D (popup removal): log to stderr, surface in detail box.
            import sys as _err_sys
            print(f"{label} Open Failed: could not read {path_text}: {exc}", file=_err_sys.stderr)
            try:
                simple_view_detail_box.setPlainText(
                    f"Could not read {label.lower()}:\n\n{path_text}\n\nError: {exc}"
                )
            except Exception:
                pass
            return

        window.load_report_file_into_viewer(path_text)

        current_simple_view_section["name"] = label
        simple_view_detail_box.setPlainText(
            f"{label}\n"
            f"{'=' * min(len(label), 42)}\n\n"
            f"Source: {Path(path_text).name}\n\n"
            f"{text_value}"
        )
        report_mode_stack.setCurrentIndex(0)

    def _open_detected_report_in_current_mode(path_text):
        window.load_report_file_into_viewer(path_text)

        if report_mode_stack.currentIndex() != 0:
            return

        lower_name = Path(path_text).name.lower()

        if _report_role_match(path_text, "user_prompt"):
            _show_report_role_in_user_view("user_prompt")
            return

        if _report_role_match(path_text, "deck_report"):
            _show_simple_view_section("Summary")
            return

        if "combo" in lower_name or "spellbook" in lower_name:
            _show_simple_view_section("Combos")
            return

        if "cut" in lower_name or "review" in lower_name:
            _show_simple_view_section("Review")
            return

        _show_simple_view_section("Handoff")

    def _load_report_role_in_raw_view(role):
        path_text = _find_report_role_path(window, role)
        label = _role_display_name(role)
        if not path_text:
            # Category C (popup removal): inline hint in detail box.
            try:
                simple_view_detail_box.setPlainText(
                    f"No generated {label.lower()} file was detected yet. "
                    "Run Analysis first, then return to Report Viewer."
                )
            except Exception:
                pass
            _show_simple_view_section("Handoff")
            return
        window.load_report_file_into_viewer(path_text)
        _show_dev_view()

    # Expose a page-local handler so the left detected-report buttons remain useful
    # while the mode stack is on User View.
    window.report_viewer_open_detected_file = _open_detected_report_in_current_mode
    window.report_viewer_show_user_prompt = lambda: _show_report_role_in_user_view("user_prompt")
    window.report_viewer_show_deck_report = lambda: _show_report_role_in_user_view("deck_report")
    window.report_viewer_show_user_section = _show_simple_view_section

    copy_prompt_btn.clicked.connect(lambda checked=False: _copy_report_role("user_prompt"))
    copy_report_btn.clicked.connect(lambda checked=False: _copy_report_role("deck_report"))
    load_prompt_btn.clicked.connect(lambda checked=False: _show_report_role_in_user_view("user_prompt"))
    load_report_btn.clicked.connect(lambda checked=False: _show_report_role_in_user_view("deck_report"))

    visible_user_view_sections = ("Handoff", "Summary", "Strategy Brain", "Owned", "Examples", "Review", "Combos", "Safety")
    # v1.5.32: Buttons that only matter when their section has real content for the
    # current report. We probe content after the row is built and hide buttons whose
    # section is empty / shows only the "no content" fallback.
    _hideable_when_empty = {"Examples", "Review"}
    simple_view_buttons: dict[str, QPushButton] = {}
    for index, simple_view_name in enumerate(visible_user_view_sections):
        simple_view_button = QPushButton(simple_view_name)
        simple_view_button.setObjectName("smallActionButton")
        simple_view_button.setMinimumHeight(38)
        simple_view_button.setMinimumWidth(132)
        simple_view_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        simple_view_button.setToolTip(f"Show User View section: {simple_view_name}")
        simple_view_button.clicked.connect(lambda checked=False, name=simple_view_name: _show_simple_view_section(name))
        simple_view_button_grid.addWidget(simple_view_button, index // 4, index % 4)
        simple_view_buttons[simple_view_name] = simple_view_button

    for column_index in range(4):
        simple_view_button_grid.setColumnStretch(column_index, 1)

    def _refresh_user_view_button_visibility():
        """Hide buttons whose section has no real content for the loaded report."""
        for name, button in simple_view_buttons.items():
            if name not in _hideable_when_empty:
                button.setVisible(True)
                continue
            try:
                content = _simple_view_section_text(name) or ""
            except Exception:
                content = ""
            stripped = content.strip()
            # The compact-snippet builder always includes the title + source line plus
            # the fallback message. We treat the section as "empty" if it contains the
            # fallback message AND no other substantive content beyond the header.
            is_empty = (
                not stripped
                or "will appear here when present" in stripped
                or "will appear here when the deck report identifies" in stripped
            )
            button.setVisible(not is_empty)

    handoff_card.body.addLayout(simple_view_button_grid)
    _show_simple_view_section("Handoff")
    _refresh_user_view_button_visibility()
    window.refresh_user_view_button_visibility = _refresh_user_view_button_visibility
    window.simple_view_user_detail_box = simple_view_detail_box
    handoff_card.body.addWidget(simple_view_detail_box, stretch=1)
    user_layout.addWidget(handoff_card, stretch=1)

    report_mode_stack.addWidget(user_view)

    # Dev View — full report lane.
    dev_view = QWidget()
    dev_layout = QVBoxLayout(dev_view)
    dev_layout.setContentsMargins(0, 0, 0, 0)
    dev_layout.setSpacing(14)

    report_text_card = ReportCard("Report File Preview", window.theme, badges=[("Plain text", "manual"), ("Grouped files", "protected")])
    report_text_card.setMinimumHeight(480)
    report_text_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    current_file_label = QLabel(window.report_viewer_current_file_label_text())
    current_file_label.setObjectName("defaultNote")
    current_file_label.setWordWrap(True)
    current_file_label.setToolTip(window.state.report_viewer_current_file)
    window.report_viewer_current_file_label = current_file_label
    report_text_card.body.addWidget(current_file_label)

    reader_tools = QHBoxLayout()
    reader_tools.setSpacing(8)

    search_input = QLineEdit(window.state.report_viewer_search_text)
    search_input.setPlaceholderText("Search current report")
    window.report_viewer_search_input = search_input

    search_btn = QPushButton("Find")
    search_btn.clicked.connect(window.find_in_current_report)
    search_input.returnPressed.connect(window.find_in_current_report)

    top_btn = QPushButton("Top")
    top_btn.clicked.connect(window.jump_report_viewer_top)

    bottom_btn = QPushButton("Bottom")
    bottom_btn.clicked.connect(window.jump_report_viewer_bottom)

    wrap_btn = QPushButton("Wrap: On" if window.state.report_viewer_word_wrap else "Wrap: Off")
    wrap_btn.clicked.connect(window.toggle_report_viewer_word_wrap)
    window.report_viewer_wrap_button = wrap_btn

    reader_tools.addWidget(search_input, stretch=2)
    reader_tools.addWidget(search_btn)
    reader_tools.addWidget(top_btn)
    reader_tools.addWidget(bottom_btn)
    reader_tools.addWidget(wrap_btn)
    report_text_card.body.addLayout(reader_tools)

    text_box = QPlainTextEdit()
    text_box.setReadOnly(True)
    text_box.setPlainText(window.state.report_viewer_current_text)
    text_box.setMinimumHeight(300)
    text_box.setMaximumHeight(16777215)
    text_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    text_box.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    text_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    text_box.setObjectName("reportFilePreview")
    window.report_viewer_text_box = text_box
    window.apply_report_viewer_readability_settings()
    report_text_card.body.addWidget(text_box, stretch=1)
    # v0.10.1.10 Direct File Layout Replacement — split Dev View into preview and status columns.
    dev_content = QWidget()
    dev_content.setObjectName("devViewReportAndStatusSplit")
    dev_content_layout = QHBoxLayout(dev_content)
    dev_content_layout.setContentsMargins(0, 0, 0, 0)
    dev_content_layout.setSpacing(28)

    report_text_card.setMinimumHeight(620)
    report_text_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    dev_content_layout.addWidget(report_text_card, stretch=5)

    status_column = QWidget()
    status_column.setObjectName("devViewStatusColumn")
    status_column.setMinimumWidth(330)
    status_column.setMaximumWidth(380)
    status_column.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

    status_column_layout = QVBoxLayout(status_column)
    status_column_layout.setContentsMargins(0, 0, 0, 0)
    status_column_layout.setSpacing(14)

    status_section_label = QLabel("REPORT STATUS / ACTIONS")
    status_section_label.setObjectName("smallCaps")
    status_section_label.setWordWrap(True)
    status_column_layout.addWidget(status_section_label)

    status_card = ReportCard("Loaded Report Status", window.theme, badges=[("No deep parsing", "protected")])
    status_card.setMinimumHeight(315)
    status_card.setMaximumHeight(16777215)
    status_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    status_label = QPlainTextEdit()
    status_label.setReadOnly(True)
    status_label.setPlainText(window.report_viewer_status_text())
    status_label.setObjectName("reportStatusPreview")
    status_label.setMinimumHeight(150)
    status_label.setMaximumHeight(210)
    status_label.setFrameShape(QFrame.NoFrame)
    status_label.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    status_label.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    status_label.setToolTip(
        f"Current file: {window.state.report_viewer_current_file}\nOutput folder: {window.state.last_output_folder}"
    )
    window.report_viewer_status_label = status_label
    status_card.body.addWidget(status_label)

    action_grid = QVBoxLayout()
    action_grid.setContentsMargins(0, 8, 0, 0)
    action_grid.setSpacing(8)

    refresh_btn = QPushButton("Refresh Current File")
    refresh_btn.clicked.connect(window.refresh_current_report_file)
    window.report_viewer_refresh_file_button = refresh_btn

    copy_btn = QPushButton("Copy Report Text")
    copy_btn.clicked.connect(window.copy_current_report_text)
    window.report_viewer_copy_button = copy_btn

    open_folder_current_btn = QPushButton("Open Current Folder")
    open_folder_current_btn.clicked.connect(window.open_current_report_folder)
    window.report_viewer_open_current_folder_button = open_folder_current_btn

    open_file_btn = QPushButton("Open Current Report File")
    open_file_btn.clicked.connect(window.open_current_report_file)
    window.open_current_report_file_button = open_file_btn

    for action_button in (refresh_btn, copy_btn, open_folder_current_btn, open_file_btn):
        action_button.setMinimumHeight(38)
        action_grid.addWidget(action_button)

    status_card.body.addLayout(action_grid)
    status_column_layout.addWidget(status_card)
    status_column_layout.addStretch(1)

    status_help = QLabel(
        "Raw report tools stay separate from the user-facing AI handoff controls."
    )
    status_help.setObjectName("mutedText")
    status_help.setWordWrap(True)
    status_column_layout.addWidget(status_help)

    dev_content_layout.addWidget(status_column, stretch=0)
    dev_layout.addWidget(dev_content, stretch=1)

    report_mode_stack.addWidget(dev_view)

    def _show_user_view():
        report_mode_stack.setCurrentIndex(0)
        user_view_btn.setObjectName("primaryButton")
        dev_view_btn.setObjectName("utilityButton")
        user_view_btn.style().unpolish(user_view_btn)
        user_view_btn.style().polish(user_view_btn)
        dev_view_btn.style().unpolish(dev_view_btn)
        dev_view_btn.style().polish(dev_view_btn)
        _show_simple_view_section("Handoff")

    def _show_dev_view():
        if not window.is_dev_mode():
            _show_user_view()
            return
        report_mode_stack.setCurrentIndex(1)
        user_view_btn.setObjectName("utilityButton")
        dev_view_btn.setObjectName("primaryButton")
        user_view_btn.style().unpolish(user_view_btn)
        user_view_btn.style().polish(user_view_btn)
        dev_view_btn.style().unpolish(dev_view_btn)
        dev_view_btn.style().polish(dev_view_btn)

    user_view_btn.clicked.connect(_show_user_view)
    dev_view_btn.clicked.connect(_show_dev_view)

    viewer_layout.addWidget(report_mode_stack, stretch=1)

    # Always land on User View first. Dev-Facing Mode exposes Dev View as an optional raw/QA lane.
    _show_user_view()

    # v0.10.5.3.3: always keep the report navigation panel in the layout so
    # Developer Mode can reveal it later without a full page rebuild. User Mode
    # still hides it.
    body_layout.addWidget(report_nav, stretch=0)
    report_nav.setVisible(show_report_nav)

    body_layout.addWidget(viewer_panel, stretch=1)
    layout.addWidget(body, stretch=1)

    window.refresh_report_viewer_file_list()
    return page
# v1.4.13.1 marker: Strategy Knowledge context informs review language; it does not generate decks by itself.
# v1.4.14 marker: Strategy shell planning gives rough role guidance; it does not select exact cards or generate full decks.
# v1.4.15 marker: Exact card candidates are review-only; they are not final deck inclusions.
# v1.4.16 marker: Role count targets are planning bands; they are not final locked deck counts.
# v1.4.17 marker: Mana base planning is guidance only; it does not insert lands or generate a finished mana base.
# v1.4.18 marker: Land insertion preview is not a deck write and does not create a final land list.
# v1.4.19 marker: Full draft preview is not a final deck export and does not lock final inclusions.
# v1.4.22 marker: Final inclusion lock is an artifact layer; it does not export the final deck.
# v1.4.23 marker: Finished mana base is an artifact layer; it does not write lands into the deck.
# v1.4.24 marker: Land deck-write is an artifact layer; it does not export the final deck.
# v1.4.25 marker: Final deck export is an artifact layer; it does not remove the old strategy system.
# v1.4.26 marker: Old strategy system is deprecated fallback; rollback remains available.
# v1.4.27 marker: v1.4 regression preserves fallback and rollback.
# v1.4.28 marker: v1.4 stable lock preserves fallback and rollback.
# v1.5.29 marker: Report Viewer User View buttons are grid-based and limited to player-facing sections.
