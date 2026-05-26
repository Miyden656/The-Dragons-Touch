
COLLECTION_SOURCE_PREFERENCE_UI_OPTIONS = [
    "Owned cards only, except assumed basic lands",
    "Prefer owned cards, show missing categories",
    "Prefer owned cards, suggest exact outside-collection upgrades",
]
# v1.3.16 marker: Collection Source Preference UI is selection-only; no deck generation.

PHILOSOPHY_MAIN_UI_OPTIONS = ["No Philosophy / Adventurer Guide", "Timmy/Tammy", "Johnny/Jenny", "Spike", "Hybrid / Mixed"]
PHILOSOPHY_SUB_UI_OPTIONS = ["No Persona / Not Sure Yet", "Big Moment — Michael / Michelle", "Engine Builder — Brad / Bria", "Commander Exploiter — Kyle / Katie", "Combo Builder — Jasper / Jennifer", "Consistency Maximizer — Avery", "Interaction Controller — Riley"]
BRACKET_PREFERENCE_UI_OPTIONS = ["Not Sure Yet", "Bracket 1 — Low Power / Precon-Friendly", "Bracket 2 — Casual Upgraded", "Bracket 3 — Strong Casual", "Bracket 4 — High Power", "Bracket 5 — cEDH / Competitive"]
# v1.3.15 marker: Philosophy + Bracket Build Preference UI is selection-only; no deck generation.
"""Commander Discovery page builder for The Dragon's Touch v1.2.8.4.

This page is the visible UI home for The Commander's Call. v1.2.8.4 keeps the
v1.2.6 guarded scan/report path, v1.2.7 result selector, and v1.2.8 live filters
while separating User Mode layout from Developer Mode diagnostics. User Mode
uses a simple scan-then-ready flow; Developer Mode keeps implementation boundaries visible.
"""

from pathlib import Path
import random

# v1.3.1 marker: Selected Commander Build-Start UI Preview is display-only.
# v1.3.10 marker: Shell Skeleton UI Preview is display-only.
# v1.3.11 marker: Build From Collection Setup Summary Preview is display-only.
# v1.3.13 marker: Build Depth Selection UI is selection-only; no deck generation.
# v1.3.14 marker: Strategy Selection / Override Preview UI is selection-only; no deck generation.

try:
    from PySide6.QtCore import Qt, QUrl
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QVBoxLayout,
    )

    from ui.widgets import add_shadow, ReportCard, SmallStat, TexturedPanel
except ImportError:  # Allows direct execution from inside the ui/ folder during local testing.
    from PySide6.QtCore import Qt, QUrl
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QVBoxLayout,
    )

    from widgets import add_shadow, ReportCard, SmallStat, TexturedPanel


WUBRG_COLOR_WORDS = {
    "W": "White",
    "U": "Blue",
    "B": "Black",
    "R": "Red",
    "G": "Green",
    "C": "Colorless",
}

COLOR_IDENTITY_FILTER_OPTIONS = [
    "Any color identity",
    "Colorless — C",
    "Mono-White — W",
    "Mono-Blue — U",
    "Mono-Black — B",
    "Mono-Red — R",
    "Mono-Green — G",
    "Azorius — WU",
    "Dimir — UB",
    "Rakdos — BR",
    "Gruul — RG",
    "Selesnya — WG",
    "Orzhov — WB",
    "Izzet — UR",
    "Golgari — BG",
    "Boros — WR",
    "Simic — UG",
    "Esper — WUB",
    "Grixis — UBR",
    "Jund — BRG",
    "Naya — WRG",
    "Bant — WUG",
    "Abzan — WBG",
    "Jeskai — WUR",
    "Sultai — UBG",
    "Mardu — WBR",
    "Temur — URG",
    "Yore-Tiller — WUBR — Missing Green",
    "Glint-Eye — UBRG — Missing White",
    "Dune-Brood — WBRG — Missing Blue",
    "Ink-Treader — WURG — Missing Black",
    "Witch-Maw — WUBG — Missing Red",
    "Five-color — WUBRG",
]

FOUR_COLOR_IDENTITY_NAMES = {
    "WUBR": ("Yore-Tiller", "Missing Green"),
    "UBRG": ("Glint-Eye", "Missing White"),
    "WBRG": ("Dune-Brood", "Missing Blue"),
    "WURG": ("Ink-Treader", "Missing Black"),
    "WUBG": ("Witch-Maw", "Missing Red"),
}

CANDIDATE_TYPE_FILTER_OPTIONS = [
    "All possible commanders",
    "Regular legendary creatures",
    "Special command-zone exceptions",
]

CANDIDATE_TYPE_ALIASES = {
    "All possible commanders": "All possible commanders",
    "MVP eligible + manual review": "All possible commanders",
    "Regular legendary creatures": "Regular legendary creatures",
    "Clearly legal commanders": "Regular legendary creatures",
    "MVP Legendary Creature only": "Regular legendary creatures",
    "Special command-zone exceptions": "Special command-zone exceptions",
    "Special-rule commanders": "Special command-zone exceptions",
    "Manual-review only": "Special command-zone exceptions",
}

STRATEGY_SELECTION_UI_OPTIONS = [
    "Use inferred strategy",
    "Aristocrats",
    "Tokens",
    "Lifegain",
    "Voltron",
    "Spellslinger",
    "Graveyard Recursion",
    "Reanimator",
    "Go-Wide Combat",
    "+1/+1 Counters",
    "Artifacts",
    "Enchantress",
    "Landfall",
    "Sacrifice",
    "Blink / Flicker",
    "Ramp Into Big Threats",
    "Control",
    "Combo-Adjacent Value",
    "Tribal / Typal",
    "Custom / Not Sure Yet",
]


def _is_developer_mode(window):
    """Return True only when the desktop shell is explicitly in Developer Mode.

    v1.2.8.5 makes the Commander's Call mode check conservative. The page should
    not assume Developer Mode from stale helper state; it should read the current
    interface mode value and only show developer-only controls when that value is
    exactly Developer Mode.
    """
    mode = ""

    display_text = getattr(window, "interface_mode_display_text", None)
    if callable(display_text):
        try:
            mode = str(display_text())
        except Exception:
            mode = ""

    if not mode:
        state = getattr(window, "state", None)
        mode = str(getattr(state, "interface_mode", "") or "")

    if not mode:
        app_settings = getattr(window, "app_settings", {}) or {}
        mode = str(app_settings.get("interface_mode", "") or "")

    normalized = mode.strip().lower().replace("_", " ").replace("-", " ")
    return normalized in {"developer mode", "dev mode", "dev facing mode", "developer facing mode"}



def _clean_identity_selection_text(selected_identity):
    return str(selected_identity or "").split(" — ", 1)[0]


def _wubrg_key_from_selection(selected_identity):
    text = str(selected_identity or "")
    if " — " not in text:
        return ""
    parts = [part.strip() for part in text.split(" — ")]
    if len(parts) >= 2:
        key = parts[1].replace(" ", "").upper()
        if all(ch in "WUBRGC" for ch in key):
            return "" if key == "C" else key
    return ""


def _format_color_identity_for_user(candidate):
    key = str(candidate.get("color_identity_key") or "").upper()
    color_count = int(candidate.get("color_count") or len(key))
    if not key and color_count == 0:
        return "Colorless — C"
    color_words = " + ".join(WUBRG_COLOR_WORDS.get(symbol, symbol) for symbol in key)
    if key in FOUR_COLOR_IDENTITY_NAMES:
        name, missing = FOUR_COLOR_IDENTITY_NAMES[key]
        return f"{name} — {key} — {color_words} ({missing})"
    if key == "WUBRG":
        return f"Five-color — WUBRG — {color_words}"
    group = candidate.get("color_identity_group") or candidate.get("color_identity_text") or "Unknown"
    if key:
        return f"{group} — {key} — {color_words}"
    return str(group)


def _developer_note(window, text):
    return window.default_note(text) if _is_developer_mode(window) else None


def _collection_source_summary(window):
    """Return a short, UI-safe collection source summary without loading files."""
    mode = getattr(window.state, "collection_source_mode", "Entire collection folder")
    folder = getattr(window.state, "collection_folder", "") or "Not selected"
    files = getattr(window.state, "selected_collection_files", []) or []
    if mode == "Select collection files":
        return f"Specific files selected: {len(files)}"
    return f"Collection folder: {folder}"


def _disabled_combo(items, current_index=0):
    """Build a disabled combo box for the selector/filter preview."""
    combo = QComboBox()
    combo.addItems(items)
    combo.setCurrentIndex(current_index)
    combo.setEnabled(False)
    return combo


def _disabled_line_edit(text):
    """Build a disabled line edit for the selector/filter preview."""
    field = QLineEdit()
    field.setText(text)
    field.setEnabled(False)
    return field


def _disabled_checkbox(label, checked=False):
    """Build a disabled checkbox for the selector/filter preview."""
    box = QCheckBox(label)
    box.setChecked(checked)
    box.setEnabled(False)
    return box


def _add_filter_row(grid, row, label_text, widget):
    """Add one labeled filter row to the Commander Discovery preview grid."""
    label = QLabel(label_text)
    label.setObjectName("mutedLabel")
    grid.addWidget(label, row, 0)
    grid.addWidget(widget, row, 1)


def _last_report_path(window):
    path_text = getattr(window, "commander_discovery_last_report_path", "") or ""
    return Path(path_text) if path_text else None


def _refresh_commander_discovery_buttons(window):
    path = _last_report_path(window)
    has_report = bool(path and path.exists())
    open_report_button = getattr(window, "commander_discovery_open_report_button", None)
    if open_report_button is not None:
        # User Mode should not kick the user out of the UI to open raw markdown.
        # Developer Mode keeps the raw report tool for QA and validation.
        open_report_button.setVisible(_is_developer_mode(window))
        open_report_button.setEnabled(has_report and _is_developer_mode(window))
    _refresh_random_commander_button(window)


def _set_commander_discovery_status(window, text):
    if getattr(window, "commander_discovery_status_box", None) is not None:
        window.commander_discovery_status_box.setPlainText(text)


def _empty_candidate_detail_text():
    return (
        "No Commander Discovery results loaded yet.\n"
        "- Run Scan Collection and Write Report first.\n"
        "- Discovered commanders will populate the selector above.\n"
        "- Selecting a commander here does not build a deck shell yet."
    )


def _candidate_detail_text(candidate):
    if not candidate:
        return _empty_candidate_detail_text()
    source_files = candidate.get("source_files") or []
    manual_notes = candidate.get("manual_review_notes") or []
    lines = [
        f"Selected Commander Candidate: {candidate.get('card_name', 'Unknown')}",
        f"- Color identity: {_format_color_identity_for_user(candidate)}",
        f"- Mana value: {candidate.get('mana_value_text') or candidate.get('mana_value') or 'Unknown'}",
        f"- Owned quantity: {candidate.get('owned_quantity', 0)}",
        f"- Eligibility status: {candidate.get('status_text') or candidate.get('eligibility_status') or 'Unknown'}",
        f"- Eligibility rule: {candidate.get('eligibility_rule') or 'Unknown'}",
        f"- Type line: {candidate.get('type_line') or 'Unknown'}",
    ]
    if candidate.get("commander_eligibility_reason"):
        lines.append(f"- Reason: {candidate.get('commander_eligibility_reason')}")
    if candidate.get("special_commander_rule"):
        lines.append(f"- Special rule note: {candidate.get('special_commander_rule')}")
    if manual_notes:
        lines.append("- Manual-review notes:")
        for note in manual_notes[:6]:
            lines.append(f"  - {note}")
    if source_files:
        lines.append("- Source files:")
        for source in source_files[:6]:
            lines.append(f"  - {source}")
        if len(source_files) > 6:
            lines.append(f"  - ...and {len(source_files) - 6} more source file(s)")
    if candidate.get("oracle_text_preview"):
        lines.append("")
        lines.append("Oracle text preview:")
        lines.append(str(candidate.get("oracle_text_preview")))
    lines.append("")
    lines.append("v1.2.8.4 boundary: selection and filtering are informational only and do not build a deck shell yet.")
    return "\n".join(lines)



def _current_selected_commander_candidate(window):
    # Return the currently selected commander candidate summary, if any.
    candidate = getattr(window, "commander_discovery_selected_candidate_summary", None)
    if candidate:
        return candidate
    candidates = getattr(window, "commander_discovery_candidate_summaries", []) or []
    combo = getattr(window, "commander_discovery_candidate_combo", None)
    index = combo.currentIndex() if combo is not None else -1
    if 0 <= index < len(candidates):
        return candidates[index]
    return None


def _empty_build_start_preview_text():
    return (
        "No commander selected for Build From Collection yet.\n"
        "- Run Commander Discovery if needed.\n"
        "- Select a commander candidate from the result list.\n"
        "- Click Start Build From This Commander to preview the v1.3 handoff.\n\n"
        "v1.3.1 boundary: this preview does not generate a deck, create a 100-card shell, "
        "write build files, or change normal deck review behavior."
    )


def _format_build_start_handoff_preview(handoff):
    # Render a user-readable selected-commander handoff preview.
    data = handoff.to_dict()
    scope = data.get("scope", {}) or {}
    strategy = data.get("strategy", {}) or {}
    philosophy = data.get("philosophy", {}) or {}
    discovery = data.get("discovery", {}) or {}
    bracket = data.get("bracket", {}) or {}
    lines = [
        "Build From Collection handoff preview created.",
        "",
        f"Selected commander: {data.get('commander_name', 'Unknown')}",
        f"- Color identity: {data.get('color_identity_text') or data.get('color_identity_key') or 'Colorless'}",
        f"- Color group: {data.get('color_identity_group') or 'Unknown'}",
        f"- Color count: {data.get('color_count', 0)}",
        f"- Owned quantity: {data.get('owned_quantity', 0)}",
        f"- Type line: {data.get('type_line') or 'Unknown'}",
        f"- Eligibility status: {data.get('eligibility_status') or 'Unknown'}",
        f"- Eligibility rule: {data.get('eligibility_rule') or 'Unknown'}",
        "",
        "Future build context placeholders:",
        f"- Primary strategy: {strategy.get('primary_strategy') or 'Not selected yet'}",
        f"- Secondary strategy: {strategy.get('secondary_strategy') or 'Not selected yet'}",
        f"- Main philosophy: {philosophy.get('main_philosophy') or 'Not selected yet'}",
        f"- Sub-philosophy/persona: {philosophy.get('sub_philosophy') or philosophy.get('persona') or 'Not selected yet'}",
        f"- Discovery mode: {discovery.get('discovery_mode') or 'Not selected yet'}",
        f"- Bracket preference: {bracket.get('intended_bracket') or 'Not selected yet'}",
        "",
        "v1.3 boundary checks:",
        f"- Scope: {scope.get('scope_name', 'Commander Selection Handoff / Build Scope Baseline')}",
        f"- Full deck generation allowed now: {scope.get('full_deck_generation_allowed', False)}",
        f"- 100-card shell allowed now: {scope.get('one_hundred_card_shell_allowed', False)}",
        f"- Normal deck review changes allowed now: {scope.get('normal_deck_review_changes_allowed', False)}",
        "",
        "Next later step: collect build preferences before any shell planning.",
    ]
    return "\n".join(lines)


def _empty_build_setup_panel_preview_text():
    return (
        "Build Setup Panel Preview is waiting for a selected commander.\n"
        "- Select a commander from the result list.\n"
        "- Click Preview Build Setup to view the display-only setup payload.\n"
        "- Basic lands are assumed available later: Plains, Island, Swamp, Mountain, Forest, and Wastes.\n\n"
        "v1.3.3 boundary: this panel does not generate a deck, create a 100-card shell, add lands, create role buckets, or change normal deck review behavior."
    )


def _format_build_setup_panel_preview(preview):
    data = preview.to_dict()
    commander = data.get("selected_commander", {}) or {}
    preferences = data.get("build_preferences", {}) or {}
    basic_policy = data.get("basic_land_policy", {}) or {}
    basic_lands = basic_policy.get("assumed_available_basic_lands", []) or []
    lines = [
        "Build Setup Panel Preview created.",
        "",
        f"Selected commander: {commander.get('commander_name') or commander.get('card_name') or 'Not selected yet'}",
        f"- Color identity: {commander.get('color_identity_text') or commander.get('color_identity_key') or 'Not selected yet'}",
        f"- Owned quantity: {commander.get('owned_quantity', 'Not selected yet')}",
        "",
        "Build preference placeholders:",
        f"- Primary strategy: {preferences.get('primary_strategy') or 'Not selected yet'}",
        f"- Secondary strategy: {preferences.get('secondary_strategy') or 'Not selected yet'}",
        f"- Main philosophy: {preferences.get('main_philosophy') or 'Not selected yet'}",
        f"- Sub-philosophy/persona: {preferences.get('sub_philosophy') or preferences.get('persona') or 'Not selected yet'}",
        f"- Discovery mode: {preferences.get('discovery_mode') or 'Not selected yet'}",
        f"- Bracket preference: {preferences.get('bracket_preference') or 'Not selected yet'}",
        f"- Collection-first preference: {preferences.get('collection_first_preference') or 'Use owned cards as the starting point.'}",
        f"- Replacement source preference: {preferences.get('replacement_source_preference') or 'Prefer my collection first.'}",
        "",
        "Basic Land Access Assumption:",
        f"- Assumed available basics: {', '.join(basic_lands) if basic_lands else 'Plains, Island, Swamp, Mountain, Forest, Wastes'}",
        "- Nonbasic lands remain collection-first.",
        "- This preview does not add lands or generate a mana base.",
        "",
        "Deferred behavior:",
    ]
    for item in data.get("deferred_behavior", []):
        lines.append(f"- {item}")
    return "\n".join(lines)


def _empty_commander_preference_handoff_preview_text():
    return (
        "Commander + Preference Handoff Preview is waiting for a selected commander.\n"
        "- Select a commander from the result list.\n"
        "- Click Preview Commander + Preferences to combine selected commander, build preferences, and basic-land policy.\n"
        "- This is setup context only.\n\n"
        "v1.3.4 boundary: this preview does not generate a deck, create a 100-card shell, create role buckets, add lands, score cards, or change normal deck review behavior."
    )


def _format_commander_preference_handoff_preview(preview):
    data = preview.to_dict()
    commander = data.get("selected_commander", {}) or {}
    preferences = data.get("build_preferences", {}) or {}
    basic_policy = data.get("basic_land_policy", {}) or {}
    basic_lands = basic_policy.get("assumed_available_basic_lands", []) or []
    lines = [
        "Commander + Preference Handoff Preview created.", "", "Selected commander:",
        f"- Name: {commander.get('commander_name') or commander.get('card_name') or 'Unknown'}",
        f"- Color identity: {commander.get('color_identity_text') or commander.get('color_identity_key') or 'Colorless'}",
        f"- Candidate type / eligibility: {commander.get('eligibility_status') or commander.get('candidate_type') or 'Unknown'}",
        f"- Source: {commander.get('source') or commander.get('collection_source') or commander.get('source_file') or 'Selected from Commander Discovery results'}",
        "", "Build preferences travelling with this commander:",
        f"- Primary strategy: {preferences.get('primary_strategy') or 'Not selected yet'}",
        f"- Secondary strategy: {preferences.get('secondary_strategy') or 'Not selected yet'}",
        f"- Main philosophy: {preferences.get('main_philosophy') or 'Not selected yet'}",
        f"- Sub-philosophy/persona: {preferences.get('sub_philosophy') or preferences.get('persona') or 'Not selected yet'}",
        f"- Discovery mode: {preferences.get('discovery_mode') or 'Not selected yet'}",
        f"- Bracket preference: {preferences.get('bracket_preference') or 'Not selected yet'}",
        f"- Collection-first preference: {preferences.get('collection_first_preference') or 'Use owned cards as the starting point.'}",
        f"- Replacement source preference: {preferences.get('replacement_source_preference') or 'Prefer my collection first.'}",
        "", "Basic Land Access Assumption:",
        f"- Assumed available basics: {', '.join(basic_lands) if basic_lands else 'Plains, Island, Swamp, Mountain, Forest, Wastes'}",
        "- Nonbasic lands remain collection-first.",
        "- This preview does not add lands or generate a mana base.",
        "", "Deferred behavior:",
    ]
    for item in data.get("deferred_behavior", []):
        lines.append(f"- {item}")
    return "\n".join(lines)




def _empty_build_depth_selection_preview_text():
    return (
        "Build Depth Selection is waiting for a commander and user choice.\n"
        "Choose how far Commander’s Call should take the selected commander build process:\n"
        "- B — Build-Start Summary\n"
        "- C — Owned Cards By Role\n"
        "- D — Rough Shell\n"
        "- E — Full 100-Card Draft\n\n"
        "v1.3.13 boundary: selecting a build depth does not execute deck generation, exact card selection, role-count targets, mana-base generation, land insertion, shell generation, or normal deck review changes."
    )


def _format_build_depth_selection_model_preview(model):
    data = model.to_dict()
    selected_label = data.get("selected_depth_user_choice_label") or data.get("selected_depth_label") or "B — Build-Start Summary"
    lines = [
        "Build Depth Selection recorded.",
        "This is user-selected setup context only; it does not execute the build yet.",
        "",
        f"Selected depth: {selected_label}",
        "",
        "Available build depths:",
    ]
    for option in data.get("available_depths", []):
        lines.append(f"- {option.get('user_choice_label')}: {option.get('description')}")
    lines.extend([
        "",
        "Execution boundaries for this patch:",
        f"- Exact card selection now: {data.get('exact_card_selection_now', False)}",
        f"- Role-count targets now: {data.get('role_count_target_generated_now', False)}",
        f"- Mana base generated now: {data.get('mana_base_generated_now', False)}",
        f"- Lands inserted now: {data.get('land_inserted_now', False)}",
        f"- Shell generated now: {data.get('shell_generated_now', False)}",
        f"- Deck generated now: {data.get('deck_generated_now', False)}",
        "",
        data.get("basic_land_policy", "Basic lands are assumed available."),
        data.get("nonbasic_land_policy", "Nonbasic lands remain collection-first unless outside-collection upgrades are allowed by the user."),
    ])
    return "\n".join(lines)


def _select_commander_build_depth(window, depth_key):
    try:
        from build_from_collection.build_depth import create_build_depth_selection_model

        model = create_build_depth_selection_model(depth_key)
        data = model.to_dict()
        window.commander_discovery_selected_build_depth_key = data.get("selected_depth_key", depth_key)
        window.commander_discovery_build_depth_selection_preview = data
        preview_text = _format_build_depth_selection_model_preview(model)
    except Exception as exc:
        window.commander_discovery_selected_build_depth_key = "build_start_summary"
        window.commander_discovery_build_depth_selection_preview = {}
        preview_text = (
            "Build Depth Selection UI failed before completion.\n"
            f"- Error detail: {exc}\n\n"
            "No deck was generated, no lands were added, no cards were selected, no role counts were created, and no normal deck review behavior was changed."
        )
        QMessageBox.warning(window, "Build Depth Selection Failed", str(exc))

    box = getattr(window, "commander_discovery_build_depth_selection_preview_box", None)
    if box is not None:
        box.setPlainText(preview_text)
    _refresh_build_start_preview_controls(window)



def _empty_strategy_selection_override_preview_text():
    return (
        "Strategy Selection / Override Preview is waiting for a selected commander.\n"
        "- Select a commander from the result list.\n"
        "- Choose primary and secondary strategy, or leave them on Use inferred strategy.\n"
        "- Click Preview Strategy Selection to carry strategy setup into Build From Collection.\n\n"
        "v1.3.14 boundary: this preview does not select exact cards, create role-count targets, generate a mana base, insert lands, generate a shell, generate a deck, or change normal deck review behavior."
    )


def _format_strategy_selection_override_preview(preview):
    data = preview.to_dict()
    mapping = data.get("strategy_mapping_preview", {}) or {}
    primary_mapping = mapping.get("primary_strategy", {}) or {}
    secondary_mapping = mapping.get("secondary_strategy", {}) or {}
    lines = [
        "Strategy Selection / Override Preview created.",
        "This is strategy setup context only; it does not build the deck.",
        "",
        "Inferred strategy suggestions:",
    ]
    inferred = data.get("inferred_strategy_labels", []) or []
    if inferred:
        for label in inferred:
            lines.append(f"- {label}")
    else:
        lines.append("- None")
    lines.extend([
        "",
        "Selected strategy:",
        f"- Primary strategy: {data.get('primary_strategy') or 'Not selected yet'} ({data.get('primary_strategy_source') or 'unknown'})",
        f"- Secondary strategy: {data.get('secondary_strategy') or 'Not selected yet'} ({data.get('secondary_strategy_source') or 'unknown'})",
        f"- User override allowed: {data.get('user_override_allowed', True)}",
        "",
        "Role emphasis preview:",
        f"- Primary emphasis: {', '.join(primary_mapping.get('emphasized_role_buckets', []) or []) or 'Not selected yet'}",
        f"- Secondary emphasis: {', '.join(secondary_mapping.get('emphasized_role_buckets', []) or []) or 'Not selected yet'}",
        "",
        "Boundary checks:",
        f"- Exact card selection: {data.get('exact_card_selection', False)}",
        f"- Role-count target generated: {data.get('role_count_target_generated', False)}",
        f"- Mana base generated: {data.get('mana_base_generated', False)}",
        f"- Lands inserted: {data.get('land_inserted', False)}",
        f"- Shell generated: {data.get('shell_generated', False)}",
        f"- Deck generated: {data.get('deck_generated', False)}",
        "",
        "Deferred behavior:",
    ])
    for item in data.get("deferred_behavior", []):
        lines.append(f"- {item}")
    return "\n".join(lines)


def _strategy_combo_value(window, attr):
    combo = getattr(window, attr, None)
    if combo is None:
        return "Use inferred strategy"
    return combo.currentText() if hasattr(combo, "currentText") else "Use inferred strategy"


def _preview_strategy_selection_override(window):
    candidate = _current_selected_commander_candidate(window)
    if not candidate:
        QMessageBox.information(
            window,
            "No Commander Selected",
            "Select a commander candidate first. v1.3.14 only previews strategy selection after a commander is selected.",
        )
        _refresh_build_start_preview_controls(window)
        return
    try:
        from build_from_collection.strategy_selection import create_strategy_selection_override_preview

        primary_choice = _strategy_combo_value(window, "commander_discovery_primary_strategy_combo")
        secondary_choice = _strategy_combo_value(window, "commander_discovery_secondary_strategy_combo")
        preview = create_strategy_selection_override_preview(
            selected_commander=candidate,
            primary_strategy=primary_choice,
            secondary_strategy=secondary_choice,
            user_override_allowed=True,
        )
        data = preview.to_dict()
        window.commander_discovery_strategy_selection_override_preview = data
        window.commander_discovery_selected_primary_strategy = data.get("primary_strategy", "")
        window.commander_discovery_selected_secondary_strategy = data.get("secondary_strategy", "")
        preview_text = _format_strategy_selection_override_preview(preview)
    except Exception as exc:
        window.commander_discovery_strategy_selection_override_preview = {}
        window.commander_discovery_selected_primary_strategy = ""
        window.commander_discovery_selected_secondary_strategy = ""
        preview_text = (
            "Strategy Selection / Override Preview failed before completion.\n"
            f"- Error detail: {exc}\n\n"
            "No deck was generated, no lands were added, no cards were selected, no role counts were created, and no normal deck review behavior was changed."
        )
        QMessageBox.warning(window, "Strategy Selection Preview Failed", str(exc))

    box = getattr(window, "commander_discovery_strategy_selection_override_preview_box", None)
    if box is not None:
        box.setPlainText(preview_text)
    _refresh_build_start_preview_controls(window)




def _empty_collection_source_preference_preview_text():
    return (
        "Collection Source Preference is waiting for user input.\n"
        "Choose how Commander’s Call should treat owned cards and outside-collection upgrades.\n\n"
        "Options:\n"
        "- Owned cards only, except assumed basic lands\n"
        "- Prefer owned cards, show missing categories\n"
        "- Prefer owned cards, suggest exact outside-collection upgrades\n\n"
        "v1.3.16 boundary: this preview does not select exact cards, create role-count targets, generate a mana base, insert lands, generate a shell, generate a deck, or change normal deck review behavior."
    )


def _format_collection_source_preference_preview(preview):
    data = preview.to_dict()
    allowed = "Yes" if data.get("outside_collection_upgrades_allowed") else "No"
    return "\n".join([
        "Collection Source Preference Preview created.",
        "This is collection-behavior setup context only; it does not build the deck.",
        "",
        f"Collection behavior: {data.get('collection_source_label') or 'Not selected yet'}",
        f"Outside-collection upgrades allowed: {allowed}",
        "Basic lands are assumed available.",
        "Nonbasic lands remain collection-first unless outside-collection upgrades are allowed by the user.",
        "",
        "No exact card selection.",
        "No role-count target generation.",
        "No mana-base generation.",
        "No land insertion.",
        "No shell generation.",
        "No deck generation.",
    ])


def _preview_collection_source_preference(window):
    try:
        from build_from_collection.collection_source_preferences import create_collection_source_preference_preview
        preference = _combo_text(
            window,
            "commander_discovery_collection_source_preference_combo",
            "Prefer owned cards, suggest exact outside-collection upgrades",
        )
        preview = create_collection_source_preference_preview(preference)
        data = preview.to_dict()
        window.commander_discovery_collection_source_preference_preview = data
        window.commander_discovery_selected_collection_source_preference = data.get("collection_source_label", "")
        window.commander_discovery_outside_collection_upgrades_allowed = bool(data.get("outside_collection_upgrades_allowed"))
        preview_text = _format_collection_source_preference_preview(preview)
    except Exception as exc:
        window.commander_discovery_collection_source_preference_preview = {}
        window.commander_discovery_selected_collection_source_preference = ""
        window.commander_discovery_outside_collection_upgrades_allowed = False
        preview_text = f"Collection Source Preference Preview failed before completion.\n- Error detail: {exc}\n\nNo deck generation."
        QMessageBox.warning(window, "Collection Source Preference Preview Failed", str(exc))
    box = getattr(window, "commander_discovery_collection_source_preference_preview_box", None)
    if box is not None:
        box.setPlainText(preview_text)
    _refresh_build_start_preview_controls(window)


def _empty_build_start_summary_output_text():
    return (
        "Build-Start Summary Output is waiting for a selected commander.\n"
        "- Select a commander from the result list.\n"
        "- Choose build depth, strategy, philosophy, bracket, and collection source preferences if desired.\n"
        "- Click Write Build-Start Summary Output to create the human-readable report and AI handoff prompt.\n\n"
        "v1.3.19.2 boundary: this output writes depth-B summary files only. It does not select exact cards, "
        "create role-count targets, generate a mana base, insert lands, generate a shell, generate a deck, "
        "or change normal deck review behavior."
    )

def _format_build_start_summary_write_result(result, output):
    data = result.to_dict() if hasattr(result, "to_dict") else {}
    output_data = output.to_dict() if hasattr(output, "to_dict") else {}
    return "\n".join([
        "Build-Start Summary Output written.",
        "This is the first usable depth-B Build From Collection output.",
        "",
        f"Commander: {output_data.get('selected_commander_name') or 'Unknown'}",
        f"Selected build depth: {output_data.get('output_depth_label') or 'Build-Start Summary'}",
        f"Primary strategy: {output_data.get('primary_strategy') or 'Not selected yet'}",
        f"Secondary strategy: {output_data.get('secondary_strategy') or 'Not selected yet'}",
        f"Main philosophy: {output_data.get('main_philosophy') or 'Not selected yet'}",
        f"Sub-philosophy / persona: {output_data.get('sub_philosophy') or 'Not selected yet'}",
        f"Bracket preference: {output_data.get('bracket_preference') or 'Not selected yet'}",
        f"Collection source preference: {output_data.get('collection_source_preference') or 'Not selected yet'}",
        "",
        "Files written:",
        f"- Human-readable report: {data.get('human_report_path')}",
        f"- AI handoff prompt: {data.get('ai_handoff_prompt_path')}",
        f"- Manifest: {data.get('manifest_path')}",
        "",
        "Land policy:",
        f"- {output_data.get('basic_land_policy') or 'Basic lands are assumed available.'}",
        f"- {output_data.get('nonbasic_land_policy') or 'Nonbasic lands remain collection-first.'}",
        "",
        "Boundary checks:",
        "- No exact card selection.",
        "- No role-count target generation.",
        "- No mana-base generation.",
        "- No land insertion.",
        "- No shell generation.",
        "- No deck generation.",
    ])

def _preview_write_build_start_summary_output(window):
    candidate = _current_selected_commander_candidate(window)
    if not candidate:
        QMessageBox.information(
            window,
            "No Commander Selected",
            "Select a commander candidate first. v1.3.19.2 only writes the build-start summary after a commander is selected.",
        )
        _refresh_build_start_preview_controls(window)
        return
    try:
        from build_from_collection.build_start_summary import create_build_start_summary_output
        from build_from_collection.build_start_report_writer import write_build_start_summary_output

        build_depth_key = getattr(window, "commander_discovery_selected_build_depth_key", "B") or "B"
        output = create_build_start_summary_output(
            selected_commander=candidate,
            build_depth_selection=getattr(window, "commander_discovery_build_depth_selection_preview", {}),
            strategy_selection_preview=getattr(window, "commander_discovery_strategy_selection_override_preview", {}),
            philosophy_bracket_preview=getattr(window, "commander_discovery_philosophy_bracket_preference_preview", {}),
            collection_source_preview=getattr(window, "commander_discovery_collection_source_preference_preview", {}),
            build_depth_key=build_depth_key,
            primary_strategy=getattr(window, "commander_discovery_selected_primary_strategy", ""),
            secondary_strategy=getattr(window, "commander_discovery_selected_secondary_strategy", ""),
            main_philosophy=getattr(window, "commander_discovery_selected_main_philosophy", ""),
            sub_philosophy=getattr(window, "commander_discovery_selected_sub_philosophy", ""),
            bracket_preference=getattr(window, "commander_discovery_selected_bracket_preference", ""),
            collection_source_preference=getattr(window, "commander_discovery_selected_collection_source_preference", ""),
            outside_collection_upgrades_allowed=getattr(window, "commander_discovery_outside_collection_upgrades_allowed", False),
        )
        output_root = getattr(getattr(window, "state", None), "report_output_folder", "Outputs") or "Outputs"
        result = write_build_start_summary_output(output, output_root=output_root)
        window.commander_discovery_build_start_summary_output = output.to_dict()
        window.commander_discovery_build_start_summary_write_result = result.to_dict()
        preview_text = _format_build_start_summary_write_result(result, output)
    except Exception as exc:
        window.commander_discovery_build_start_summary_output = {}
        window.commander_discovery_build_start_summary_write_result = {}
        preview_text = (
            "Build-Start Summary Output failed before completion.\n"
            f"- Error detail: {exc}\n\n"
            "No deck was generated, no lands were inserted, no exact cards were selected, and no normal deck review behavior was changed."
        )
        QMessageBox.warning(window, "Build-Start Summary Output Failed", str(exc))

    box = getattr(window, "commander_discovery_build_start_summary_output_box", None)
    if box is not None:
        box.setPlainText(preview_text)
    _refresh_build_start_preview_controls(window)


# BEGIN v1.3.21 Owned Cards By Role UI / Report Write Hook helpers
def _empty_owned_cards_by_role_output_text():
    return (
        "Owned Cards By Role Output is waiting for a selected commander.\n"
        "- Select a commander from the result list.\n"
        "- Click Write Owned Cards By Role Output to create the human-readable report and AI handoff prompt.\n\n"
        "v1.3.21 boundary: this output writes possible owned-card role fits only. It does not generate a deck."
    )

def _format_owned_cards_by_role_write_result(result, output):
    data = result.to_dict() if hasattr(result, "to_dict") else {}
    output_data = output.to_dict() if hasattr(output, "to_dict") else {}
    grouped = output_data.get("grouped_by_role", {}) or {}
    grouped_count = sum(len(cards) for cards in grouped.values()) if isinstance(grouped, dict) else 0
    return "\n".join([
        "Owned Cards By Role Output written.",
        "This is depth-C Build From Collection output: possible owned-card role fits only.",
        "",
        f"Commander: {output_data.get('selected_commander') or 'Unknown'}",
        f"Possible role-fit entries: {grouped_count}",
        "",
        "Files written:",
        f"- Human-readable report: {data.get('human_report_path')}",
        f"- AI handoff prompt: {data.get('ai_handoff_prompt_path')}",
        f"- Manifest: {data.get('manifest_path')}",
        "",
        "No exact card selection.",
        "No final deck inclusion decisions.",
        "No deck generation.",
    ])

def _sample_owned_cards_by_role_candidates(window):
    return [
        {"name": "Sol Ring", "owned_quantity": 1, "oracle_text": "Add two colorless mana.", "type_line": "Artifact"},
        {"name": "Arcane Signet", "owned_quantity": 1, "oracle_text": "Add one mana of any color in your commander's color identity.", "type_line": "Artifact"},
        {"name": "Command Tower", "owned_quantity": 1, "oracle_text": "Add one mana of any color in your commander's color identity.", "type_line": "Land"},
    ]

def _preview_write_owned_cards_by_role_output(window):
    candidate = _current_selected_commander_candidate(window)
    if not candidate:
        QMessageBox.information(window, "No Commander Selected", "Select a commander candidate first.")
        _refresh_build_start_preview_controls(window)
        return
    try:
        from build_from_collection.owned_cards_by_role_output import create_owned_cards_by_role_output
        from build_from_collection.owned_cards_by_role_report_writer import write_owned_cards_by_role_output
        commander_name = candidate.get("commander_name") if isinstance(candidate, dict) else getattr(candidate, "commander_name", None)
        if not commander_name:
            commander_name = candidate.get("card_name", "Selected commander") if isinstance(candidate, dict) else getattr(candidate, "card_name", "Selected commander")
        output = create_owned_cards_by_role_output(
            owned_cards=_sample_owned_cards_by_role_candidates(window),
            selected_commander=commander_name,
            primary_strategy=getattr(window, "commander_discovery_selected_primary_strategy", "") or "Not selected yet",
            secondary_strategy=getattr(window, "commander_discovery_selected_secondary_strategy", "") or "Not selected yet",
        )
        output_root = getattr(getattr(window, "state", None), "report_output_folder", "Outputs") or "Outputs"
        result = write_owned_cards_by_role_output(output, output_root=output_root)
        window.commander_discovery_owned_cards_by_role_output = output.to_dict()
        window.commander_discovery_owned_cards_by_role_write_result = result.to_dict()
        preview_text = _format_owned_cards_by_role_write_result(result, output)
    except Exception as exc:
        window.commander_discovery_owned_cards_by_role_output = {}
        window.commander_discovery_owned_cards_by_role_write_result = {}
        preview_text = f"Owned Cards By Role Output failed before completion.\n- Error detail: {exc}\n\nNo deck generation."
        QMessageBox.warning(window, "Owned Cards By Role Output Failed", str(exc))
    box = getattr(window, "commander_discovery_owned_cards_by_role_output_box", None)
    if box is not None:
        box.setPlainText(preview_text)
    _refresh_build_start_preview_controls(window)
# END v1.3.21 Owned Cards By Role UI / Report Write Hook helpers

def _format_build_from_collection_setup_summary_preview(preview):
    data = preview.to_dict()
    commander = data.get("selected_commander", {}) or {}
    if hasattr(commander, "to_dict"):
        commander = commander.to_dict()
    if not isinstance(commander, dict):
        commander = {}
    prefs = data.get("build_preferences", {}) or {}
    build_depth = data.get("build_depth_selection", {}) or {}
    strategy_selection = data.get("strategy_selection_preview", {}) or {}
    role_plan = data.get("role_bucket_plan", {}) or {}
    shell = data.get("shell_skeleton_preview", {}) or {}
    candidate_pool = data.get("candidate_pool_shape", {}) or {}
    owned_roles = data.get("owned_role_classification_preview", {}) or {}
    basic_policy = data.get("basic_land_policy", {}) or {}
    basics = basic_policy.get("assumed_available_basic_lands", []) or []
    nonbasic_policy = data.get("nonbasic_land_policy") or "Nonbasic lands remain collection-first."

    role_bucket_count = len(role_plan.get("role_buckets", []) or role_plan.get("buckets", []) or [])
    shell_sections = shell.get("sections", []) or []
    candidate_entries = candidate_pool.get("entries", []) or []
    classifications = owned_roles.get("classifications", []) or []

    lines = [
        "Build From Collection Setup Summary Preview created.",
        "This combines setup context only. It does not build the deck.",
        "",
        "Selected commander:",
        f"- Name: {commander.get('commander_name') or commander.get('card_name') or 'Unknown'}",
        f"- Color identity: {commander.get('color_identity_text') or commander.get('color_identity_key') or 'Not selected yet'}",
        f"- Owned quantity: {commander.get('owned_quantity', 'Not selected yet')}",
        "",
        "Build preferences:",
        f"- Primary strategy: {prefs.get('primary_strategy') or 'Not selected yet'}",
        f"- Secondary strategy: {prefs.get('secondary_strategy') or 'Not selected yet'}",
        f"- Main philosophy: {prefs.get('main_philosophy') or 'Not selected yet'}",
        f"- Sub-philosophy / persona: {prefs.get('sub_philosophy') or 'Not selected yet'}",
        f"- Discovery mode: {prefs.get('discovery_mode') or 'Not selected yet'}",
        f"- Bracket preference: {prefs.get('bracket_preference') or 'Not selected yet'}",
        f"- Collection-first preference: {prefs.get('collection_first_preference') or 'Collection first'}",
        f"- Selected build depth: {build_depth.get('selected_depth_user_choice_label') or build_depth.get('selected_depth_label') or 'B — Build-Start Summary'}",
        "",
        "Strategy selection:",
        f"- Inferred suggestions: {', '.join(strategy_selection.get('inferred_strategy_labels', [])) if strategy_selection.get('inferred_strategy_labels') else 'None'}",
        f"- Selected primary strategy: {strategy_selection.get('primary_strategy') or prefs.get('primary_strategy') or 'Not selected yet'}",
        f"- Selected secondary strategy: {strategy_selection.get('secondary_strategy') or prefs.get('secondary_strategy') or 'Not selected yet'}",
        "- Strategy can be inferred or user-overridden.",
        "",
        "Setup context included:",
        f"- Role bucket plan: {role_bucket_count or 'baseline'} planning buckets",
        f"- Candidate pool shape: {len(candidate_entries)} entries carried for future use",
        f"- Owned-card role classification preview: {len(classifications)} preview classifications",
        f"- Shell skeleton: {len(shell_sections)} preview sections",
        "",
        "Land policy:",
        f"- Basic lands assumed available: {', '.join(basics) if basics else 'Plains, Island, Swamp, Mountain, Forest, Wastes'}",
        f"- {nonbasic_policy}",
        "",
        "Boundary checks:",
        f"- Exact card selection: {data.get('exact_card_selection', False)}",
        f"- Role-count target generated: {data.get('role_count_target_generated', False)}",
        f"- Mana base generated: {data.get('mana_base_generated', False)}",
        f"- Lands inserted: {data.get('land_inserted', False)}",
        f"- Shell completed: {data.get('shell_completed', False)}",
        f"- Deck generated: {data.get('deck_generated', False)}",
        "",
        "Deferred behavior:",
    ]
    for item in data.get("deferred_behavior", []):
        lines.append(f"- {item}")
    return "\n".join(lines)

def _empty_commander_shell_skeleton_preview_text():
    return (
        "Commander Shell Skeleton Preview is waiting for a selected commander.\n"
        "- Select a commander from the result list.\n"
        "- Click Preview Shell Skeleton to view the future shell outline.\n"
        "- Basic lands are assumed available.\n"
        "- Nonbasic lands remain collection-first.\n\n"
        "v1.3.10 boundary: this preview does not select exact cards, create role-count targets, generate a mana base, insert lands, complete a shell, generate a deck, or change normal deck review behavior."
    )


def _format_commander_shell_skeleton_preview(preview):
    data = preview.to_dict()
    commander = data.get("selected_commander", {}) or {}
    if hasattr(commander, "to_dict"):
        commander = commander.to_dict()
    if not isinstance(commander, dict):
        commander = {}
    sections = data.get("sections", []) or []
    basic_policy = data.get("basic_land_policy", {}) or {}
    basic_lands = basic_policy.get("assumed_available_basic_lands", []) or []
    nonbasic_policy = data.get("nonbasic_land_policy") or "Nonbasic lands remain collection-first."

    lines = [
        "Commander Shell Skeleton Preview created.",
        "",
        "Selected commander:",
        f"- Name: {commander.get('commander_name') or commander.get('card_name') or 'Unknown'}",
        f"- Color identity: {commander.get('color_identity_text') or commander.get('color_identity_key') or 'Not selected yet'}",
        f"- Owned quantity: {commander.get('owned_quantity', 'Not selected yet')}",
        "",
        "Strategy context:",
        f"- Primary strategy: {data.get('primary_strategy') or 'Not selected yet'}",
        f"- Secondary strategy: {data.get('secondary_strategy') or 'Not selected yet'}",
        "",
        "Shell skeleton sections, preview only:",
    ]
    for section in sections:
        section_name = section.get("section_name", "Unnamed Section")
        purpose = section.get("purpose", "Preview-only future shell section.")
        lines.append(f"- {section_name}: {purpose}")
    lines.extend([
        "",
        "Land policy:",
        f"- Basic lands assumed available: {', '.join(basic_lands) if basic_lands else 'Plains, Island, Swamp, Mountain, Forest, Wastes'}",
        f"- {nonbasic_policy}",
        "- This preview does not generate a mana base or insert lands.",
        "",
        "Boundary checks:",
        f"- Exact card selection: {data.get('exact_card_selection', False)}",
        f"- Role-count target generated: {data.get('role_count_target_generated', False)}",
        f"- Mana base generated: {data.get('mana_base_generated', False)}",
        f"- Lands inserted: {data.get('land_inserted', False)}",
        f"- Deck generated: {data.get('deck_generated', False)}",
        f"- Shell completed: {data.get('shell_completed', False)}",
        "",
        "Deferred behavior:",
    ])
    for item in data.get("deferred_behavior", []):
        lines.append(f"- {item}")
    return "\n".join(lines)

def _preview_build_setup_panel(window):
    candidate = _current_selected_commander_candidate(window)
    if not candidate:
        QMessageBox.information(
            window,
            "No Commander Selected",
            "Select a commander candidate first. v1.3.3 only previews build setup after a commander is selected.",
        )
        _refresh_build_start_preview_controls(window)
        return

    try:
        from build_from_collection.build_setup import build_setup_panel_preview

        preview = build_setup_panel_preview(candidate)
        window.commander_discovery_build_setup_panel_preview = preview.to_dict()
        preview_text = _format_build_setup_panel_preview(preview)
    except Exception as exc:  # Defensive UI boundary.
        window.commander_discovery_build_setup_panel_preview = {}
        preview_text = (
            "Build Setup Panel Preview failed before completion.\n"
            f"- Error detail: {exc}\n\n"
            "No deck was generated, no lands were added, and no normal deck review behavior was changed."
        )
        QMessageBox.warning(window, "Build Setup Preview Failed", str(exc))

    box = getattr(window, "commander_discovery_build_setup_panel_preview_box", None)
    if box is not None:
        box.setPlainText(preview_text)
    _refresh_build_start_preview_controls(window)

def _preview_commander_preference_handoff(window):
    candidate = _current_selected_commander_candidate(window)
    if not candidate:
        QMessageBox.information(window, "No Commander Selected", "Select a commander candidate first. v1.3.4 only previews commander + preference handoff context after a commander is selected.")
        _refresh_build_start_preview_controls(window)
        return
    try:
        from build_from_collection.commander_preference_preview import create_commander_preference_handoff_preview
        preview = create_commander_preference_handoff_preview(candidate)
        window.commander_discovery_commander_preference_handoff_preview = preview.to_dict()
        preview_text = _format_commander_preference_handoff_preview(preview)
    except Exception as exc:
        window.commander_discovery_commander_preference_handoff_preview = {}
        preview_text = "Commander + Preference Handoff Preview failed before completion.\n- Error detail: " + str(exc) + "\n\nNo deck was generated, no lands were added, no cards were scored, and no normal deck review behavior was changed."
        QMessageBox.warning(window, "Commander + Preference Preview Failed", str(exc))
    box = getattr(window, "commander_discovery_commander_preference_handoff_preview_box", None)
    if box is not None:
        box.setPlainText(preview_text)
    _refresh_build_start_preview_controls(window)



def _preview_build_from_collection_setup_summary(window):
    candidate = _current_selected_commander_candidate(window)
    if not candidate:
        QMessageBox.information(
            window,
            "No Commander Selected",
            "Select a commander candidate first. v1.3.11 only summarizes setup context after a commander is selected.",
        )
        _refresh_build_start_preview_controls(window)
        return

    try:
        from build_from_collection.setup_summary import create_build_from_collection_setup_summary_preview

        build_depth_key = getattr(window, "commander_discovery_selected_build_depth_key", "B")
        primary_strategy = getattr(window, "commander_discovery_selected_primary_strategy", "")
        secondary_strategy = getattr(window, "commander_discovery_selected_secondary_strategy", "")
        preview = create_build_from_collection_setup_summary_preview(
            candidate,
            primary_strategy=primary_strategy,
            secondary_strategy=secondary_strategy,
            main_philosophy=getattr(window, "commander_discovery_selected_main_philosophy", ""),
            sub_philosophy=getattr(window, "commander_discovery_selected_sub_philosophy", ""),
            bracket_preference=getattr(window, "commander_discovery_selected_bracket_preference", ""),
            collection_source_preference=getattr(window, "commander_discovery_selected_collection_source_preference", ""),
            build_depth_key=build_depth_key,
        )
        window.commander_discovery_setup_summary_preview = preview.to_dict()
        preview_text = _format_build_from_collection_setup_summary_preview(preview)
    except Exception as exc:
        window.commander_discovery_setup_summary_preview = {}
        preview_text = (
            "Build From Collection Setup Summary Preview failed before completion.\n"
            f"- Error detail: {exc}\n\n"
            "No deck was generated, no lands were added, no cards were selected, no role counts were created, and no normal deck review behavior was changed."
        )
        QMessageBox.warning(window, "Setup Summary Preview Failed", str(exc))

    box = getattr(window, "commander_discovery_setup_summary_preview_box", None)
    if box is not None:
        box.setPlainText(preview_text)
    _refresh_build_start_preview_controls(window)

def _preview_commander_shell_skeleton(window):
    candidate = _current_selected_commander_candidate(window)
    if not candidate:
        QMessageBox.information(
            window,
            "No Commander Selected",
            "Select a commander candidate first. v1.3.10 only previews the shell skeleton after a commander is selected.",
        )
        _refresh_build_start_preview_controls(window)
        return

    try:
        from build_from_collection.shell_skeleton import create_commander_shell_skeleton_preview

        preview = create_commander_shell_skeleton_preview(candidate)
        window.commander_discovery_shell_skeleton_preview = preview.to_dict()
        preview_text = _format_commander_shell_skeleton_preview(preview)
    except Exception as exc:
        window.commander_discovery_shell_skeleton_preview = {}
        preview_text = (
            "Commander Shell Skeleton Preview failed before completion.\n"
            f"- Error detail: {exc}\n\n"
            "No deck was generated, no lands were added, no cards were selected, no role counts were created, and no normal deck review behavior was changed."
        )
        QMessageBox.warning(window, "Shell Skeleton Preview Failed", str(exc))

    box = getattr(window, "commander_discovery_shell_skeleton_preview_box", None)
    if box is not None:
        box.setPlainText(preview_text)
    _refresh_build_start_preview_controls(window)

def _refresh_build_start_preview_controls(window):
    # Enable build-from-collection preview buttons only when a candidate is selected.
    candidate = _current_selected_commander_candidate(window)
    button = getattr(window, "commander_discovery_start_build_preview_button", None)
    if button is not None:
        button.setEnabled(bool(candidate))
    setup_button = getattr(window, "commander_discovery_build_setup_panel_preview_button", None)
    if setup_button is not None:
        setup_button.setEnabled(bool(candidate))
    commander_preference_button = getattr(window, "commander_discovery_commander_preference_handoff_preview_button", None)
    if commander_preference_button is not None:
        commander_preference_button.setEnabled(bool(candidate))
    shell_skeleton_button = getattr(window, "commander_discovery_shell_skeleton_preview_button", None)
    if shell_skeleton_button is not None:
        shell_skeleton_button.setEnabled(bool(candidate))
    setup_summary_button = getattr(window, "commander_discovery_setup_summary_preview_button", None)
    if setup_summary_button is not None:
        setup_summary_button.setEnabled(bool(candidate))
    build_depth_buttons = getattr(window, "commander_discovery_build_depth_selection_buttons", []) or []
    for build_depth_button in build_depth_buttons:
        build_depth_button.setEnabled(bool(candidate))
    strategy_button = getattr(window, "commander_discovery_strategy_selection_override_preview_button", None)
    if strategy_button is not None:
        strategy_button.setEnabled(bool(candidate))
    strategy_combos = [
        getattr(window, "commander_discovery_primary_strategy_combo", None),
        getattr(window, "commander_discovery_secondary_strategy_combo", None),
    ]
    for strategy_combo in strategy_combos:
        if strategy_combo is not None:
            strategy_combo.setEnabled(bool(candidate))


    build_start_summary_button = getattr(window, "commander_discovery_build_start_summary_output_button", None)
    if build_start_summary_button is not None:
        build_start_summary_button.setEnabled(bool(candidate))
    rough_shell_output_button = getattr(window, "commander_discovery_rough_shell_output_button", None)
    if rough_shell_output_button is not None:
        rough_shell_output_button.setEnabled(bool(candidate))
    owned_cards_by_role_button = getattr(window, "commander_discovery_owned_cards_by_role_output_button", None)
    if owned_cards_by_role_button is not None:
        owned_cards_by_role_button.setEnabled(bool(candidate))

def _preview_build_from_selected_commander(window):
    # Create a display-only v1.3 handoff preview from the selected commander.
    candidate = _current_selected_commander_candidate(window)
    if not candidate:
        QMessageBox.information(
            window,
            "No Commander Selected",
            "Select a commander candidate first. v1.3.1 only previews the build-start handoff after a commander is selected.",
        )
        _refresh_build_start_preview_controls(window)
        return

    try:
        from build_from_collection.models import build_commander_selection_handoff

        handoff = build_commander_selection_handoff(candidate)
        window.commander_discovery_build_start_handoff_preview = handoff.to_dict()
        preview_text = _format_build_start_handoff_preview(handoff)
    except Exception as exc:  # Defensive UI boundary.
        window.commander_discovery_build_start_handoff_preview = {}
        preview_text = (
            "Build From Collection handoff preview failed before completion.\n"
            f"- Error detail: {exc}\n\n"
            "No deck was generated and no normal deck review behavior was changed."
        )
        QMessageBox.warning(window, "Build-Start Preview Failed", str(exc))

    box = getattr(window, "commander_discovery_build_start_preview_box", None)
    if box is not None:
        box.setPlainText(preview_text)
    _refresh_build_start_preview_controls(window)

def _selected_commander_candidate_changed(window, index):
    """Refresh selected-candidate detail text when the result selector changes."""
    candidates = getattr(window, "commander_discovery_candidate_summaries", []) or []
    candidate = candidates[index] if 0 <= index < len(candidates) else None
    window.commander_discovery_selected_candidate = candidate.get("card_name", "") if candidate else ""
    window.commander_discovery_selected_candidate_summary = candidate
    if getattr(window, "commander_discovery_candidate_detail_box", None) is not None:
        window.commander_discovery_candidate_detail_box.setPlainText(_candidate_detail_text(candidate))
    _refresh_build_start_preview_controls(window)


def _candidate_filter_value(window, attr, default=""):
    widget = getattr(window, attr, None)
    if widget is None:
        return default
    if hasattr(widget, "currentText"):
        return widget.currentText()
    if hasattr(widget, "text"):
        return widget.text()
    return default


def _candidate_matches_identity_filter(candidate, selected_identity):
    """Return True if a candidate matches the selected WUBRG/color identity filter."""
    if not selected_identity or selected_identity == "Any color identity":
        return True
    clean_name = _clean_identity_selection_text(selected_identity)
    selected_key = _wubrg_key_from_selection(selected_identity)
    key = str(candidate.get("color_identity_key") or "").upper()
    group = str(candidate.get("color_identity_group") or "")
    color_count = int(candidate.get("color_count") or 0)
    identity_map = {
        "Colorless": {"key": "", "group": "Colorless"},
        "Mono-White": {"key": "W", "group": "Mono-White"},
        "Mono-Blue": {"key": "U", "group": "Mono-Blue"},
        "Mono-Black": {"key": "B", "group": "Mono-Black"},
        "Mono-Red": {"key": "R", "group": "Mono-Red"},
        "Mono-Green": {"key": "G", "group": "Mono-Green"},
        "Azorius": {"key": "WU", "group": "Azorius"},
        "Dimir": {"key": "UB", "group": "Dimir"},
        "Rakdos": {"key": "BR", "group": "Rakdos"},
        "Gruul": {"key": "RG", "group": "Gruul"},
        "Selesnya": {"key": "WG", "group": "Selesnya"},
        "Orzhov": {"key": "WB", "group": "Orzhov"},
        "Izzet": {"key": "UR", "group": "Izzet"},
        "Golgari": {"key": "BG", "group": "Golgari"},
        "Boros": {"key": "WR", "group": "Boros"},
        "Simic": {"key": "UG", "group": "Simic"},
        "Esper": {"key": "WUB", "group": "Esper"},
        "Grixis": {"key": "UBR", "group": "Grixis"},
        "Jund": {"key": "BRG", "group": "Jund"},
        "Naya": {"key": "WRG", "group": "Naya"},
        "Bant": {"key": "WUG", "group": "Bant"},
        "Abzan": {"key": "WBG", "group": "Abzan"},
        "Jeskai": {"key": "WUR", "group": "Jeskai"},
        "Sultai": {"key": "UBG", "group": "Sultai"},
        "Mardu": {"key": "WBR", "group": "Mardu"},
        "Temur": {"key": "URG", "group": "Temur"},
        "Yore-Tiller": {"key": "WUBR", "group": "Yore-Tiller"},
        "Glint-Eye": {"key": "UBRG", "group": "Glint-Eye"},
        "Dune-Brood": {"key": "WBRG", "group": "Dune-Brood"},
        "Ink-Treader": {"key": "WURG", "group": "Ink-Treader"},
        "Witch-Maw": {"key": "WUBG", "group": "Witch-Maw"},
        "Five-color": {"key": "WUBRG", "group": "Five-color"},
    }
    if clean_name == "Four-color":
        return color_count == 4
    if selected_key:
        return key == selected_key
    expected = identity_map.get(clean_name)
    if not expected:
        return True
    return key == expected["key"] or group == expected["group"]


def _candidate_matches_group_filter(candidate, selected_group):
    """Return True if a candidate matches the selected broad color-count group."""
    if not selected_group or selected_group == "Any group":
        return True
    color_count = int(candidate.get("color_count") or 0)
    if selected_group == "Colorless":
        return color_count == 0
    if selected_group == "Mono-color":
        return color_count == 1
    if selected_group == "Two-color":
        return color_count == 2
    if selected_group == "Three-color":
        return color_count == 3
    if selected_group == "Four-color":
        return color_count == 4
    if selected_group == "Five-color":
        return color_count == 5
    return True


def _candidate_matches_owned_filter(candidate, selected_owned):
    if not selected_owned or selected_owned == "Any owned quantity":
        return True
    owned = int(candidate.get("owned_quantity") or 0)
    thresholds = {"At least 1": 1, "At least 2": 2, "At least 3": 3, "At least 4": 4}
    return owned >= thresholds.get(selected_owned, 0)


def _candidate_matches_type_filter(candidate, selected_type):
    selected_type = CANDIDATE_TYPE_ALIASES.get(selected_type or "All possible commanders", selected_type or "All possible commanders")
    if selected_type == "All possible commanders":
        return True
    if selected_type == "Regular legendary creatures":
        return bool(candidate.get("is_mvp_eligible"))
    if selected_type == "Special command-zone exceptions":
        return not bool(candidate.get("is_mvp_eligible"))
    return True


def _candidate_matches_text_filter(candidate, search_text):
    text = str(search_text or "").strip().lower()
    if not text:
        return True
    haystack_parts = [
        candidate.get("card_name", ""),
        candidate.get("display_label", ""),
        candidate.get("type_line", ""),
        candidate.get("oracle_text_preview", ""),
        candidate.get("color_identity_group", ""),
        candidate.get("color_identity_text", ""),
        candidate.get("commander_eligibility_reason", ""),
        candidate.get("special_commander_rule", ""),
        " ".join(candidate.get("manual_review_notes") or []),
        " ".join(candidate.get("source_files") or []),
    ]
    return text in " ".join(str(part).lower() for part in haystack_parts)


def _candidate_matches_live_filters(window, candidate):
    """Apply the v1.2.8 live UI filter surface to one candidate summary."""
    return (
        _candidate_matches_identity_filter(candidate, _candidate_filter_value(window, "commander_discovery_color_identity_filter", "Any color identity"))
        and _candidate_matches_group_filter(candidate, _candidate_filter_value(window, "commander_discovery_color_group_filter", "Any group"))
        and _candidate_matches_owned_filter(candidate, _candidate_filter_value(window, "commander_discovery_owned_quantity_filter", "Any owned quantity"))
        and _candidate_matches_type_filter(candidate, _candidate_filter_value(window, "commander_discovery_candidate_type_filter", "All possible commanders"))
        and _candidate_matches_text_filter(candidate, _candidate_filter_value(window, "commander_discovery_search_filter", ""))
    )


def _load_filtered_candidates_into_selector(window, candidates):
    """Load already-filtered candidate summaries into the selector widget."""
    window.commander_discovery_candidate_summaries = list(candidates or [])
    combo = getattr(window, "commander_discovery_candidate_combo", None)
    if combo is None:
        return
    combo.blockSignals(True)
    combo.clear()
    if window.commander_discovery_candidate_summaries:
        combo.addItems([candidate.get("display_label", candidate.get("card_name", "Unknown")) for candidate in window.commander_discovery_candidate_summaries])
        combo.setCurrentIndex(0)
        combo.setEnabled(True)
    else:
        all_candidates = getattr(window, "commander_discovery_all_candidate_summaries", []) or []
        combo.addItem("No commander candidates match current filters" if all_candidates else "No commander candidates found")
        combo.setCurrentIndex(0)
        combo.setEnabled(False)
    combo.blockSignals(False)
    _selected_commander_candidate_changed(window, 0 if window.commander_discovery_candidate_summaries else -1)
    _refresh_random_commander_button(window)


def _update_filter_status(window, before_count, after_count):
    status = getattr(window, "commander_discovery_filter_status_label", None)
    if status is not None:
        status.setText(f"Showing {after_count} of {before_count} possible commander(s) after filters.")


def _apply_commander_discovery_filters(window):
    """Recompute the live result list without rerunning the Commander Discovery scanner."""
    all_candidates = list(getattr(window, "commander_discovery_all_candidate_summaries", []) or [])
    filtered = [candidate for candidate in all_candidates if _candidate_matches_live_filters(window, candidate)]
    _load_filtered_candidates_into_selector(window, filtered)
    _update_filter_status(window, len(all_candidates), len(filtered))


def _populate_commander_discovery_selector(window, result):
    """Populate the live Commander Result List after a scan, then apply active filters."""
    candidates = list(getattr(result, "candidate_summaries", []) or [])
    window.commander_discovery_all_candidate_summaries = candidates
    _apply_commander_discovery_filters(window)

def _run_guarded_commander_discovery_scan(window):
    """Run the first guarded Commander Discovery UI scan path."""
    reply = QMessageBox.question(
        window,
        "Run Commander Discovery Scan",
        "Scan the staged local collection files for commander candidates and write a Commander Discovery report?\n\n"
        "This will not run normal deck review, modify your deck, generate a 100-card shell, or make network/API calls.",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No,
    )
    if reply != QMessageBox.Yes:
        return

    _set_commander_discovery_status(window, "Commander Discovery scan is running...\n- Loading local Scryfall data\n- Loading staged local collection source\n- Finding commander candidates\n- Writing markdown report\n- Preparing Commander Result List")
    if getattr(window, "commander_discovery_scan_button", None) is not None:
        window.commander_discovery_scan_button.setEnabled(False)

    try:
        from commander_discovery.ui_scan_path import run_guarded_commander_discovery_scan

        result = run_guarded_commander_discovery_scan(window.state)
    except Exception as exc:  # Defensive UI boundary.
        result = None
        _set_commander_discovery_status(window, f"Commander Discovery scan failed before completion.\n- Error detail: {exc}")
        QMessageBox.warning(window, "Commander Discovery Scan Failed", str(exc))
    finally:
        if getattr(window, "commander_discovery_scan_button", None) is not None:
            window.commander_discovery_scan_button.setEnabled(True)

    if result is None:
        _refresh_commander_discovery_buttons(window)
        return

    _set_commander_discovery_status(window, result.to_status_text())
    if result.success:
        window.commander_discovery_last_report_path = result.report_path
        window.commander_discovery_last_scan_result = result
        window.state.status = "Commander Discovery report written"
        if getattr(window, "commander_discovery_scan_card", None) is not None:
            window.commander_discovery_scan_card.setVisible(False)
        if getattr(window, "commander_discovery_ready_card", None) is not None:
            window.commander_discovery_ready_card.setVisible(True)
        _populate_commander_discovery_selector(window, result)
        QMessageBox.information(
            window,
            "Commander Discovery Scan Complete",
            f"Commander candidates found: {result.commander_candidate_count}\nReport written:\n{result.report_path}",
        )
    else:
        _populate_commander_discovery_selector(window, result)
        QMessageBox.warning(window, "Commander Discovery Scan Did Not Complete", result.message or "The scan did not complete.")
    _refresh_commander_discovery_buttons(window)
    if hasattr(window, "refresh_context_panel_values"):
        window.refresh_context_panel_values()


def _refresh_random_commander_button(window):
    """Enable I Want You! only after Commander Discovery has candidates to choose from."""
    button = getattr(window, "commander_discovery_random_button", None)
    if button is None:
        return
    candidates = getattr(window, "commander_discovery_candidate_summaries", []) or []
    all_candidates = getattr(window, "commander_discovery_all_candidate_summaries", []) or []
    button.setEnabled(bool(candidates or all_candidates))


def _set_candidate_type_filter(window, label):
    """Set the user-facing commander type filter from a result-list button."""
    combo = getattr(window, "commander_discovery_candidate_type_filter", None)
    if combo is None:
        return
    target = CANDIDATE_TYPE_ALIASES.get(label, label)
    for index in range(combo.count()):
        if CANDIDATE_TYPE_ALIASES.get(combo.itemText(index), combo.itemText(index)) == target:
            combo.setCurrentIndex(index)
            return


def _choose_random_commander_candidate(window):
    """I Want You! randomly selects one visible commander candidate after a scan."""
    candidates = getattr(window, "commander_discovery_candidate_summaries", []) or []
    if not candidates:
        candidates = getattr(window, "commander_discovery_all_candidate_summaries", []) or []
    combo = getattr(window, "commander_discovery_candidate_combo", None)
    if not candidates or combo is None:
        QMessageBox.information(
            window,
            "No Commander Candidates Yet",
            "Run Commander Discovery first. After commanders are found, I Want You! can randomly choose one from the visible list.",
        )
        return
    chosen = random.randrange(len(candidates))
    # If the random source fell back to all candidates, reload the selector first so the index is valid.
    if candidates is not getattr(window, "commander_discovery_candidate_summaries", []):
        _load_filtered_candidates_into_selector(window, candidates)
    combo.setCurrentIndex(chosen)
    candidate = candidates[chosen]
    QMessageBox.information(
        window,
        "I Want You!",
        f"Commander selected: {candidate.get('card_name', 'Unknown')}\n\nThis only selects a commander. Deck-shell building begins later in v1.3.",
    )


def _open_latest_commander_discovery_report(window):
    path = _last_report_path(window)
    if not path or not path.exists():
        QMessageBox.information(window, "No Commander Discovery Report", "No Commander Discovery report has been written in this UI session yet.")
        _refresh_commander_discovery_buttons(window)
        return
    QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))


# BEGIN v1.3.23 Rough Shell UI / Report Write Hook helpers
def _empty_rough_shell_output_text():
    return (
        "Rough Shell Output is waiting for a selected commander.\n"
        "- Select a commander from the result list.\n"
        "- Click Write Rough Shell Output to create the human-readable rough-shell report and AI handoff prompt.\n\n"
        "v1.3.23 boundary: this output writes a rough-shell report only. It does not complete a shell or generate a deck."
    )


def _format_rough_shell_write_result(result, model, commander_name):
    data = result.to_dict() if hasattr(result, "to_dict") else {}
    model_data = model.to_dict() if hasattr(model, "to_dict") else {}
    section_count = len(model_data.get("sections", []) or [])
    return "\n".join([
        "Rough Shell Output written.",
        "This is depth-D Build From Collection output: rough shell report only.",
        "It is not a completed shell and not a final decklist.",
        "",
        f"Commander: {commander_name or 'Unknown'}",
        f"Build depth: {model_data.get('build_depth_label') or model_data.get('depth_label') or 'D - Rough Shell'}",
        f"Rough shell sections: {section_count}",
        "",
        "Files written:",
        f"- Human-readable report: {data.get('human_report_path')}",
        f"- AI handoff prompt: {data.get('ai_handoff_prompt_path')}",
        f"- Manifest: {data.get('manifest_path')}",
        "",
        "No exact card selection.",
        "No final deck inclusion decisions.",
        "No completed shell generation.",
        "No deck generation.",
    ])


def _preview_write_rough_shell_output(window):
    candidate = _current_selected_commander_candidate(window)
    if not candidate:
        QMessageBox.information(window, "No Commander Selected", "Select a commander candidate first.")
        _refresh_build_start_preview_controls(window)
        return
    try:
        from build_from_collection.rough_shell_output import create_rough_shell_output_model
        from build_from_collection.rough_shell_report_writer import write_rough_shell_output
        if isinstance(candidate, dict):
            commander_name = candidate.get("commander_name") or candidate.get("card_name") or "Selected commander"
        else:
            commander_name = getattr(candidate, "commander_name", None) or getattr(candidate, "card_name", "Selected commander")
        model = create_rough_shell_output_model()
        output_root = getattr(getattr(window, "state", None), "report_output_folder", "Outputs") or "Outputs"
        result = write_rough_shell_output(model, selected_commander=commander_name, output_root=output_root)
        window.commander_discovery_rough_shell_output = model.to_dict()
        window.commander_discovery_rough_shell_write_result = result.to_dict()
        preview_text = _format_rough_shell_write_result(result, model, commander_name)
    except Exception as exc:
        window.commander_discovery_rough_shell_output = {}
        window.commander_discovery_rough_shell_write_result = {}
        preview_text = f"Rough Shell Output failed before completion.\n- Error detail: {exc}\n\nNo deck generation."
        QMessageBox.warning(window, "Rough Shell Output Failed", str(exc))
    box = getattr(window, "commander_discovery_rough_shell_output_box", None)
    if box is not None:
        box.setPlainText(preview_text)
    _refresh_build_start_preview_controls(window)
# END v1.3.23 Rough Shell UI / Report Write Hook helpers

# BEGIN v1.3.25 Full 100-Card Draft UI / Report Write Hook helpers
def _empty_full_100_card_draft_output_text():
    return (
        "Full 100-Card Draft Output is waiting for a selected commander.\n"
        "- Select a commander from the result list.\n"
        "- Click Write Full 100-Card Draft Output to create the depth-E model report and AI handoff prompt.\n\n"
        "v1.3.25 boundary: this output writes a full-draft model/report only. It does not generate a 100-card deck."
    )


def _format_full_100_card_draft_write_result(result, model, commander_name):
    data = result.to_dict() if hasattr(result, "to_dict") else {}
    model_data = model.to_dict() if hasattr(model, "to_dict") else {}
    section_count = len(model_data.get("sections", []) or [])
    return "\n".join([
        "Full 100-Card Draft Output written.",
        f"Selected commander: {commander_name}",
        "Build depth: E - Full 100-Card Draft",
        f"Future output sections: {section_count}",
        "",
        "Files written:",
        f"- Human-readable report: {data.get('human_report_path')}",
        f"- AI handoff prompt: {data.get('ai_handoff_prompt_path')}",
        f"- Manifest: {data.get('manifest_path')}",
        "",
        "No exact card selection.",
        "No final deck inclusion decisions.",
        "No mana-base generation.",
        "No full 100-card draft generation.",
        "No deck generation.",
    ])


def _preview_write_full_100_card_draft_output(window):
    candidate = _current_selected_commander_candidate(window)
    if not candidate:
        QMessageBox.information(window, "No Commander Selected", "Select a commander candidate first.")
        _refresh_build_start_preview_controls(window)
        return
    try:
        from build_from_collection.full_100_card_draft_output import create_full_100_card_draft_output_model
        from build_from_collection.full_100_card_draft_report_writer import write_full_100_card_draft_output
        if isinstance(candidate, dict):
            commander_name = candidate.get("commander_name") or candidate.get("card_name") or "Selected commander"
        else:
            commander_name = getattr(candidate, "commander_name", None) or getattr(candidate, "card_name", "Selected commander")
        model = create_full_100_card_draft_output_model(selected_commander=commander_name)
        output_root = getattr(getattr(window, "state", None), "report_output_folder", "Outputs") or "Outputs"
        result = write_full_100_card_draft_output(model, selected_commander=commander_name, output_root=output_root)
        window.commander_discovery_full_100_card_draft_output = model.to_dict()
        window.commander_discovery_full_100_card_draft_write_result = result.to_dict()
        preview_text = _format_full_100_card_draft_write_result(result, model, commander_name)
    except Exception as exc:
        window.commander_discovery_full_100_card_draft_output = {}
        window.commander_discovery_full_100_card_draft_write_result = {}
        preview_text = f"Full 100-Card Draft Output failed before completion.\n- Error detail: {exc}\n\nNo deck generation."
        QMessageBox.warning(window, "Full 100-Card Draft Output Failed", str(exc))
    box = getattr(window, "commander_discovery_full_100_card_draft_output_box", None)
    if box is not None:
        box.setPlainText(preview_text)
    _refresh_build_start_preview_controls(window)
# END v1.3.25 Full 100-Card Draft UI / Report Write Hook helpers

def build_commander_discovery_page(window):
    """Build The Commander's Call page as an isolated UI scan/report surface."""
    page, layout = window.page_container(
        "The Commander's Call",
        "Find commanders you already own, then choose one to build around later."
    )

    scroll, content = window.scroll_content()
    body = TexturedPanel(window.theme, kind="iron", glow=False)
    add_shadow(body, blur=24, y=8)
    b_layout = QVBoxLayout(body)
    b_layout.setContentsMargins(22, 22, 22, 22)
    b_layout.setSpacing(16)

    if _is_developer_mode(window):
        top = QHBoxLayout()
        for label, value in [
            ("Feature", "Commander Discovery"),
            ("Current Scope", "Find commanders"),
            ("Color IDs", "WUBRG/C"),
            ("Deck Builder", "v1.3 later"),
        ]:
            top.addWidget(SmallStat(label, value, window.theme))
        b_layout.addLayout(top)

    run_card = ReportCard("Scan Your Collection for Commanders", window.theme, badges=[("Local scan", "primary"), ("Writes report", "manual")])
    window.commander_discovery_scan_card = run_card
    run_card.body.addWidget(window.make_text(
        "Start here. Scan your local collection to find possible commanders you own. Once a scan succeeds, this section collapses so you can focus on browsing results.",
        paper=True,
    ))
    window.commander_discovery_status_box = window.readonly_text_box(
        "No Commander Discovery scan has been run in this UI session yet.\n"
        "- Stage a collection folder or selected collection files first.\n"
        "- Click Scan Collection and Write Report when ready.\n"
        "- The generated report can be opened directly from this page.\n"
        "- Discovered commanders will populate the selector below.",
        min_height=150,
        max_height=230,
    )
    window.commander_discovery_status_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    run_card.body.addWidget(window.commander_discovery_status_box)

    scan_action_row = QHBoxLayout()
    window.commander_discovery_scan_button = QPushButton("Scan Collection and Write Report")
    window.commander_discovery_scan_button.setObjectName("primaryButton")
    window.commander_discovery_scan_button.clicked.connect(lambda checked=False: _run_guarded_commander_discovery_scan(window))
    scan_action_row.addWidget(window.commander_discovery_scan_button)
    run_card.body.addLayout(scan_action_row)
    if _is_developer_mode(window):
        run_card.body.addWidget(window.default_note(
            "Developer guardrail: this button only runs Commander Discovery. It does not run deck review, cut logic, replacement logic, combo matching, or build-from-collection automation."
        ))
    if _last_report_path(window) and _last_report_path(window).exists():
        run_card.setVisible(False)
    b_layout.addWidget(run_card)

    ready_card = ReportCard("Ready for the Call?", window.theme, badges=[("Scan complete", "protected"), ("Random selector", "primary")])
    window.commander_discovery_ready_card = ready_card
    ready_row = QHBoxLayout()
    ready_row.addWidget(window.make_text(
        "Your commander scan is complete. Browse the results below, or let The Commander's Call randomly choose from the visible commander list.",
        paper=True,
    ), stretch=1)
    window.commander_discovery_random_button = QPushButton("I Want You!")
    window.commander_discovery_random_button.setObjectName("primaryButton")
    window.commander_discovery_random_button.setEnabled(False)
    window.commander_discovery_random_button.clicked.connect(lambda checked=False: _choose_random_commander_candidate(window))
    ready_row.addWidget(window.commander_discovery_random_button)
    ready_report_button = QPushButton("Open Report")
    ready_report_button.setObjectName("utilityButton")
    ready_report_button.setToolTip("Developer Mode only: open the raw Commander Discovery markdown report outside the UI.")
    ready_report_button.clicked.connect(lambda checked=False: _open_latest_commander_discovery_report(window))
    # Share the same report-button state target so the normal refresh helper controls it.
    # v1.2.8.4: hidden in User Mode because raw file opening feels like dev tooling.
    window.commander_discovery_open_report_button = ready_report_button
    ready_report_button.setVisible(_is_developer_mode(window))
    ready_row.addWidget(ready_report_button)
    ready_card.body.addLayout(ready_row)
    if _is_developer_mode(window):
        ready_card.body.addWidget(window.default_note(
            "Developer boundary: Ready for the Call replaces the scan card after success. I Want You! only chooses from the local result list; it does not build a deck, rerun the scanner, or modify a deck."
        ))
    ready_card.setVisible(bool(_last_report_path(window) and _last_report_path(window).exists()))
    b_layout.addWidget(ready_card)

    filter_surface = ReportCard("Browse and Filter Commanders", window.theme, badges=[("Live narrowing", "primary"), ("No rescan", "protected")])
    filter_surface.body.addWidget(window.make_text(
        "Narrow the commanders found in your collection by color identity, color count, name, owned quantity, or commander type.",
        paper=True,
    ))

    filter_grid = QGridLayout()
    filter_grid.setHorizontalSpacing(14)
    filter_grid.setVerticalSpacing(10)

    window.commander_discovery_color_identity_filter = QComboBox()
    window.commander_discovery_color_identity_filter.addItems(COLOR_IDENTITY_FILTER_OPTIONS)
    window.commander_discovery_color_identity_filter.currentIndexChanged.connect(lambda index: _apply_commander_discovery_filters(window))

    window.commander_discovery_color_group_filter = QComboBox()
    window.commander_discovery_color_group_filter.addItems(["Any group", "Colorless", "Mono-color", "Two-color", "Three-color", "Four-color", "Five-color"])
    window.commander_discovery_color_group_filter.currentIndexChanged.connect(lambda index: _apply_commander_discovery_filters(window))

    window.commander_discovery_search_filter = QLineEdit()
    window.commander_discovery_search_filter.setPlaceholderText("Name, type line, oracle text, source file, or rule note")
    window.commander_discovery_search_filter.textChanged.connect(lambda text: _apply_commander_discovery_filters(window))

    window.commander_discovery_owned_quantity_filter = QComboBox()
    window.commander_discovery_owned_quantity_filter.addItems(["Any owned quantity", "At least 1", "At least 2", "At least 3", "At least 4"])
    window.commander_discovery_owned_quantity_filter.currentIndexChanged.connect(lambda index: _apply_commander_discovery_filters(window))

    window.commander_discovery_candidate_type_filter = QComboBox()
    window.commander_discovery_candidate_type_filter.addItems(CANDIDATE_TYPE_FILTER_OPTIONS)
    window.commander_discovery_candidate_type_filter.currentIndexChanged.connect(lambda index: _apply_commander_discovery_filters(window))

    _add_filter_row(filter_grid, 0, "Color identity (WUBRG/C)", window.commander_discovery_color_identity_filter)
    _add_filter_row(filter_grid, 1, "Color group", window.commander_discovery_color_group_filter)
    _add_filter_row(filter_grid, 2, "Search text", window.commander_discovery_search_filter)
    _add_filter_row(filter_grid, 3, "Owned quantity", window.commander_discovery_owned_quantity_filter)
    _add_filter_row(filter_grid, 4, "Commander type", window.commander_discovery_candidate_type_filter)
    filter_surface.body.addLayout(filter_grid)

    window.commander_discovery_filter_status_label = QLabel("Showing 0 of 0 possible commander(s) after filters.")
    window.commander_discovery_filter_status_label.setObjectName("mutedLabel")
    filter_surface.body.addWidget(window.commander_discovery_filter_status_label)

    filter_surface.body.addWidget(window.default_note(
        "Color key: W=White, U=Blue, B=Black, R=Red, G=Green, C=Colorless. Four-color names show which color is missing."
    ))
    if _is_developer_mode(window):
        filter_surface.body.addWidget(window.default_note(
            "Developer boundary: these controls narrow the local result list already returned by the guarded scan. They do not rerun Scryfall loading, rewrite the report, call main.py, or build a deck shell."
        ))
    b_layout.addWidget(filter_surface)

    selector = ReportCard("Commander Result List", window.theme, badges=[("Live after scan", "primary"), ("Selection safe", "protected")])
    selector.body.addWidget(window.make_text(
        "After a successful scan, commanders you own appear here. Use the quick buttons to view regular legendary creatures, special command-zone exceptions, or all possible commanders.",
        paper=True,
    ))

    type_button_row = QHBoxLayout()
    for label in ["All possible commanders", "Regular legendary creatures", "Special command-zone exceptions"]:
        button = QPushButton(label)
        button.setObjectName("utilityButton")
        button.clicked.connect(lambda checked=False, selected=label: _set_candidate_type_filter(window, selected))
        type_button_row.addWidget(button)
    selector.body.addLayout(type_button_row)

    window.commander_discovery_all_candidate_summaries = []
    window.commander_discovery_candidate_summaries = []
    window.commander_discovery_selected_candidate = ""
    window.commander_discovery_selected_candidate_summary = None
    window.commander_discovery_build_start_handoff_preview = {}
    window.commander_discovery_build_setup_panel_preview = {}
    window.commander_discovery_commander_preference_handoff_preview = {}
    window.commander_discovery_candidate_combo = QComboBox()
    window.commander_discovery_candidate_combo.addItem("Run a Commander Discovery scan to populate candidates")
    window.commander_discovery_candidate_combo.setEnabled(False)
    window.commander_discovery_candidate_combo.currentIndexChanged.connect(lambda index: _selected_commander_candidate_changed(window, index))
    selector.body.addWidget(window.commander_discovery_candidate_combo)

    window.commander_discovery_candidate_detail_box = window.readonly_text_box(
        _empty_candidate_detail_text(),
        min_height=220,
        max_height=330,
    )
    window.commander_discovery_candidate_detail_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    selector.body.addWidget(window.commander_discovery_candidate_detail_box)
    if _is_developer_mode(window):
        selector.body.addWidget(window.default_note(
            "Developer boundary: choosing a commander here is only a local UI selection preview. It does not launch deck construction, does not modify a deck, and does not write a build-around prompt yet."
        ))
    b_layout.addWidget(selector)


    build_start = ReportCard("Build From Collection Preview", window.theme, badges=[("v1.3.1", "primary"), ("No deck generation", "protected")])
    build_start.body.addWidget(window.make_text(
        "Use the selected commander as the starting point for future Build From Collection setup. This preview confirms the handoff data only; it does not create a deck shell.",
        paper=True,
    ))
    build_action_row = QHBoxLayout()
    window.commander_discovery_start_build_preview_button = QPushButton("Start Build From This Commander")
    window.commander_discovery_start_build_preview_button.setObjectName("primaryButton")
    window.commander_discovery_start_build_preview_button.setEnabled(False)
    window.commander_discovery_start_build_preview_button.clicked.connect(lambda checked=False: _preview_build_from_selected_commander(window))
    build_action_row.addWidget(window.commander_discovery_start_build_preview_button)
    build_start.body.addLayout(build_action_row)
    window.commander_discovery_build_start_preview_box = window.readonly_text_box(
        _empty_build_start_preview_text(),
        min_height=210,
        max_height=300,
    )
    window.commander_discovery_build_start_preview_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    build_start.body.addWidget(window.commander_discovery_build_start_preview_box)
    if _is_developer_mode(window):
        build_start.body.addWidget(window.default_note(
            "Developer boundary: v1.3.1 uses build_commander_selection_handoff() only for a display preview. It does not write a build file, generate cards, alter scoring, or call main.py."
        ))
    b_layout.addWidget(build_start)

    build_setup = ReportCard("Build Setup Panel Preview", window.theme, badges=[("v1.3.3", "primary"), ("Basic lands assumed", "protected"), ("No deck generation", "protected")])
    build_setup.body.addWidget(window.make_text(
        "Preview the future Build From Collection setup context before shell planning. Basic lands are assumed available later, while nonbasic lands remain collection-first.",
        paper=True,
    ))
    setup_action_row = QHBoxLayout()
    window.commander_discovery_build_setup_panel_preview_button = QPushButton("Preview Build Setup")
    window.commander_discovery_build_setup_panel_preview_button.setObjectName("utilityButton")
    window.commander_discovery_build_setup_panel_preview_button.setEnabled(False)
    window.commander_discovery_build_setup_panel_preview_button.clicked.connect(lambda checked=False: _preview_build_setup_panel(window))
    setup_action_row.addWidget(window.commander_discovery_build_setup_panel_preview_button)
    build_setup.body.addLayout(setup_action_row)
    window.commander_discovery_build_setup_panel_preview_box = window.readonly_text_box(
        _empty_build_setup_panel_preview_text(),
        min_height=240,
        max_height=340,
    )
    window.commander_discovery_build_setup_panel_preview_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    build_setup.body.addWidget(window.commander_discovery_build_setup_panel_preview_box)
    if _is_developer_mode(window):
        build_setup.body.addWidget(window.default_note(
            "Developer boundary: v1.3.3 previews build preferences plus the Basic Land Access Assumption only. It does not generate a mana base, add lands, write a decklist, alter scoring, or call main.py."
        ))
    b_layout.addWidget(build_setup)

    commander_preference = ReportCard("Commander + Preference Handoff Preview", window.theme, badges=[("v1.3.4", "primary"), ("Setup context only", "protected"), ("No deck generation", "protected")])
    commander_preference.body.addWidget(window.make_text("Combine the selected commander, build preference placeholders, and Basic Land Access Assumption into one setup-context preview before role-bucket planning.", paper=True))
    commander_preference_action_row = QHBoxLayout()
    window.commander_discovery_commander_preference_handoff_preview_button = QPushButton("Preview Commander + Preferences")
    window.commander_discovery_commander_preference_handoff_preview_button.setObjectName("utilityButton")
    window.commander_discovery_commander_preference_handoff_preview_button.setEnabled(False)
    window.commander_discovery_commander_preference_handoff_preview_button.clicked.connect(lambda checked=False: _preview_commander_preference_handoff(window))
    commander_preference_action_row.addWidget(window.commander_discovery_commander_preference_handoff_preview_button)
    commander_preference.body.addLayout(commander_preference_action_row)
    window.commander_discovery_commander_preference_handoff_preview_box = window.readonly_text_box(_empty_commander_preference_handoff_preview_text(), min_height=270, max_height=390)
    window.commander_discovery_commander_preference_handoff_preview_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    commander_preference.body.addWidget(window.commander_discovery_commander_preference_handoff_preview_box)
    if _is_developer_mode(window):
        commander_preference.body.addWidget(window.default_note("Developer boundary: v1.3.4 combines commander selection, build preferences, and the Basic Land Access Assumption only. It does not generate role buckets, build a mana base, add lands, score cards, alter cuts/replacements, or call main.py."))
    b_layout.addWidget(commander_preference)


    build_start_summary_output = ReportCard("Build-Start Summary Output", window.theme, badges=[("v1.3.19", "primary"), ("Depth B", "protected"), ("No deck generation", "protected")])
    build_start_summary_output.body.addWidget(window.make_text("Write the selected commander’s depth-B Build From Collection summary as a human-readable report and AI handoff prompt. This writes output files only; it does not select cards or generate a deck.", paper=True))
    build_start_summary_action_row = QHBoxLayout()
    window.commander_discovery_build_start_summary_output_button = QPushButton("Write Build-Start Summary Output")
    window.commander_discovery_build_start_summary_output_button.setObjectName("primaryButton")
    window.commander_discovery_build_start_summary_output_button.setEnabled(False)
    window.commander_discovery_build_start_summary_output_button.clicked.connect(lambda checked=False: _preview_write_build_start_summary_output(window))
    build_start_summary_action_row.addWidget(window.commander_discovery_build_start_summary_output_button)
    build_start_summary_output.body.addLayout(build_start_summary_action_row)
    window.commander_discovery_build_start_summary_output_box = window.readonly_text_box(_empty_build_start_summary_output_text(), min_height=320, max_height=520)
    window.commander_discovery_build_start_summary_output_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    build_start_summary_output.body.addWidget(window.commander_discovery_build_start_summary_output_box)
    if _is_developer_mode(window):
        build_start_summary_output.body.addWidget(window.default_note("Developer boundary: v1.3.19 writes the depth-B build-start report and AI handoff prompt only. No exact card selection, role counts, mana base, shell, or deck generation."))
    b_layout.addWidget(build_start_summary_output)

    rough_shell_output = ReportCard("Rough Shell Output", window.theme, badges=[("v1.3.23", "primary"), ("Depth D", "protected"), ("No deck generation", "protected")])
    rough_shell_output.body.addWidget(window.make_text("Write the selected commander's depth-D Rough Shell output as a human-readable report and AI handoff prompt. This writes a rough-shell report only; it does not complete a shell or generate a deck.", paper=True))
    rough_shell_action_row = QHBoxLayout()
    window.commander_discovery_rough_shell_output_button = QPushButton("Write Rough Shell Output")
    window.commander_discovery_rough_shell_output_button.setObjectName("primaryButton")
    window.commander_discovery_rough_shell_output_button.setEnabled(False)
    window.commander_discovery_rough_shell_output_button.clicked.connect(lambda checked=False: _preview_write_rough_shell_output(window))
    rough_shell_action_row.addWidget(window.commander_discovery_rough_shell_output_button)
    rough_shell_output.body.addLayout(rough_shell_action_row)
    window.commander_discovery_rough_shell_output_box = window.readonly_text_box(_empty_rough_shell_output_text(), min_height=320, max_height=520)
    window.commander_discovery_rough_shell_output_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    rough_shell_output.body.addWidget(window.commander_discovery_rough_shell_output_box)
    if _is_developer_mode(window):
        rough_shell_output.body.addWidget(window.default_note("Developer boundary: v1.3.23 writes the depth-D rough-shell report and AI handoff prompt only. No exact card selection, role counts, mana base, completed shell, shell generation, or deck generation."))
    b_layout.addWidget(rough_shell_output)

    full_100_card_draft_output = ReportCard("Full 100-Card Draft Output", window.theme, badges=[("v1.3.25", "primary"), ("Depth E", "protected"), ("No deck generation", "protected")])
    full_100_card_draft_output.body.addWidget(window.make_text("Write the selected commander's depth-E Full 100-Card Draft model output as a human-readable report and AI handoff prompt. This writes a future full-draft model only; it does not generate a 100-card deck.", paper=True))
    full_100_card_draft_action_row = QHBoxLayout()
    window.commander_discovery_full_100_card_draft_output_button = QPushButton("Write Full 100-Card Draft Output")
    window.commander_discovery_full_100_card_draft_output_button.setObjectName("primaryButton")
    window.commander_discovery_full_100_card_draft_output_button.setEnabled(False)
    window.commander_discovery_full_100_card_draft_output_button.clicked.connect(lambda checked=False: _preview_write_full_100_card_draft_output(window))
    full_100_card_draft_action_row.addWidget(window.commander_discovery_full_100_card_draft_output_button)
    full_100_card_draft_output.body.addLayout(full_100_card_draft_action_row)
    window.commander_discovery_full_100_card_draft_output_box = window.readonly_text_box(_empty_full_100_card_draft_output_text(), min_height=320, max_height=520)
    window.commander_discovery_full_100_card_draft_output_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    full_100_card_draft_output.body.addWidget(window.commander_discovery_full_100_card_draft_output_box)
    if _is_developer_mode(window):
        full_100_card_draft_output.body.addWidget(window.default_note("Developer boundary: v1.3.25 writes the depth-E full-draft model report and AI handoff prompt only. No exact card selection, role counts, mana base, full 100-card draft generation, or deck generation."))
    b_layout.addWidget(full_100_card_draft_output)




    owned_cards_by_role_output = ReportCard("Owned Cards By Role Output", window.theme, badges=[("v1.3.21", "primary"), ("Depth C", "protected"), ("No deck generation", "protected")])
    owned_cards_by_role_output.body.addWidget(window.make_text("Write the selected commander's depth-C Owned Cards By Role output as a human-readable report and AI handoff prompt. This writes possible owned-card role fits only; it does not make final deck inclusion decisions or generate a deck.", paper=True))
    owned_cards_by_role_action_row = QHBoxLayout()
    window.commander_discovery_owned_cards_by_role_output_button = QPushButton("Write Owned Cards By Role Output")
    window.commander_discovery_owned_cards_by_role_output_button.setObjectName("primaryButton")
    window.commander_discovery_owned_cards_by_role_output_button.setEnabled(False)
    window.commander_discovery_owned_cards_by_role_output_button.clicked.connect(lambda checked=False: _preview_write_owned_cards_by_role_output(window))
    owned_cards_by_role_action_row.addWidget(window.commander_discovery_owned_cards_by_role_output_button)
    owned_cards_by_role_output.body.addLayout(owned_cards_by_role_action_row)
    window.commander_discovery_owned_cards_by_role_output_box = window.readonly_text_box(_empty_owned_cards_by_role_output_text(), min_height=320, max_height=520)
    window.commander_discovery_owned_cards_by_role_output_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    owned_cards_by_role_output.body.addWidget(window.commander_discovery_owned_cards_by_role_output_box)
    b_layout.addWidget(owned_cards_by_role_output)

    if _is_developer_mode(window):
        rules = ReportCard("What Counts as a Commander?", window.theme, badges=[("Locked simple rule", "primary")])
        rules.body.addWidget(window.make_text(
            "The Commander’s Call looks for commanders you own. Clearly legal commanders are legendary creatures. Special-rule commanders are kept in a separate review bucket so they are not missed.",
            paper=True,
        ))
        rules_box = window.readonly_text_box(
            "MVP eligible now\n"
            "- type_line contains \"Legendary Creature\"\n\n"
            "Manual-review / deferred rule families\n"
            "- Planeswalkers that say they can be your commander\n"
            "- Partner / partner with and partner variants\n"
            "- Choose a Background / Background\n"
            "- Friends forever\n"
            "- Doctor’s companion\n"
            "- Other special command-zone exceptions\n\n"
            "Boundary\n"
            "- Discover candidates first\n"
            "- Select one commander later\n"
            "- Build from collection later",
            min_height=185,
            max_height=255,
        )
        rules_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        rules.body.addWidget(rules_box)
        b_layout.addWidget(rules)

        status = ReportCard("Commander Discovery Status", window.theme, badges=[("Developer Mode", "manual"), ("v1.2.8.4", "primary")])
        status.body.addWidget(window.make_text(
            "Developer status view for the isolated Commander Discovery path, collection source preview, and current v1.2 boundaries.",
            paper=True,
        ))
        status_box = window.readonly_text_box(
            "Current collection source preview\n"
            f"- Source mode: {getattr(window.state, 'collection_source_mode', 'Entire collection folder')}\n"
            f"- {_collection_source_summary(window)}\n"
            f"- Report output folder: {getattr(window.state, 'report_output_folder', 'Outputs') or 'Outputs'}\n\n"
            "Developer boundaries\n"
            "- Local collection data already selected in the app\n"
            "- Local Scryfall metadata already available to the project\n"
            "- No account login\n"
            "- No remote API call from this page\n"
            "- Does not call main.py\n"
            "- Does not build a 100-card commander deck shell",
            min_height=165,
            max_height=235,
        )
        status_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        status.body.addWidget(status_box)
        b_layout.addWidget(status)

        workflow = ReportCard("Coming Next", window.theme, badges=[("v1.3 later", "manual"), ("No deck shell yet", "protected")])
        workflow.body.addWidget(window.make_text(
            "The next major Commander’s Call step is v1.3: use the selected commander, your collection, strategy choices, philosophy, and bracket preference to start a deck shell.",
            paper=True,
        ))
        workflow.body.addWidget(window.default_note(
            "Still deferred: automatic 100-card shells, full build-from-collection logic, random deck generation, Archidekt import, and account login."
        ))
        b_layout.addWidget(workflow)

    _refresh_commander_discovery_buttons(window)
    _refresh_build_start_preview_controls(window)
    content.addWidget(body)
    content.addStretch(1)
    layout.addWidget(scroll, stretch=1)
    return page


# v1.3.27 marker: Build From Collection Output Selector UI is selector-only; no deck generation.
def _empty_build_from_collection_output_selector_text():
    return (
        "Build From Collection Output Selector is waiting for a build depth selection.\n"
        "Choose build depth B, C, D, or E, then preview which output family Commander’s Call will route to.\n\n"
        "Boundary: this selector does not execute writers, select exact cards, generate role counts, generate a mana base, insert lands, generate a shell, generate a 100-card draft, or generate a deck."
    )


def _format_build_from_collection_output_selector_preview(preview):
    data = preview.to_dict()
    yes_no = lambda value: "Yes" if value else "No"
    return "\n".join([
        "Build From Collection Output Selector UI Preview",
        "",
        f"Selected depth: {data.get('selected_depth_key', 'B')}",
        f"Output route: {data.get('output_label', 'B - Build-Start Summary')}",
        f"Output family: {data.get('output_family', 'build_start_summary')}",
        "",
        str(data.get("description", "Selector route preview.")),
        "",
        "Boundary checks:",
        f"- Selector UI only: {yes_no(data.get('selector_ui_only', True))}",
        f"- Executes writer now: {yes_no(data.get('executes_writer', False))}",
        f"- Selects exact cards: {yes_no(data.get('selects_exact_cards', False))}",
        f"- Generates role counts: {yes_no(data.get('generates_role_count_targets', False))}",
        f"- Generates mana base: {yes_no(data.get('generates_mana_base', False))}",
        f"- Inserts lands: {yes_no(data.get('inserts_lands', False))}",
        f"- Generates shell: {yes_no(data.get('generates_shell', False))}",
        f"- Generates full 100-card draft: {yes_no(data.get('generates_100_card_draft', False))}",
        f"- Generates deck: {yes_no(data.get('generates_deck', False))}",
    ])


def _preview_build_from_collection_output_selector(window):
    try:
        from build_from_collection.output_selector_ui import create_build_from_collection_output_selector_ui_preview

        depth_key = getattr(window, "commander_discovery_selected_build_depth_key", "B") or "B"
        preview = create_build_from_collection_output_selector_ui_preview(depth_key)
        window.commander_discovery_output_selector_ui_preview = preview.to_dict()
        preview_text = _format_build_from_collection_output_selector_preview(preview)
    except Exception as exc:
        window.commander_discovery_output_selector_ui_preview = {}
        preview_text = (
            "Build From Collection Output Selector failed before completion.\n"
            f"- Error detail: {exc}\n\n"
            "No writer was executed, no exact cards were selected, no role counts were created, no mana base was generated, no lands were inserted, no shell was generated, no 100-card draft was generated, and no deck was generated."
        )
        QMessageBox.warning(window, "Output Selector Preview Failed", str(exc))

    box = getattr(window, "commander_discovery_output_selector_preview_box", None)
    if box is not None:
        box.setPlainText(preview_text)
    return preview_text


# v1.2.8.4 UI markers: User Mode hides raw report opener, Developer Mode shows raw report opener, Ready for the Call replaces scan after successful report, User Mode clean, Developer Mode guardrails, WUBRG color identity nomenclature, four-color identity names, All possible commanders, Clearly legal commanders, Special-rule commanders.
# v1.3.1 UI markers: Build From Collection Preview, Start Build From This Commander, commander_discovery_build_start_handoff_preview, display-only handoff preview, No deck generation.

# v1.2.8.4 mode-separation markers: User Mode hides Open Report; Developer Mode shows Open Report; uses is_dev_mode/is_dev_facing_mode/interface_mode_display_text; What Counts as a Commander? is Developer Mode only.

# v1.3.3 UI markers: Build Setup Panel Preview, Preview Build Setup, Basic Land Access Assumption, commander_discovery_build_setup_panel_preview, No deck generation.
# v1.3.4 UI markers: Commander + Preference Handoff Preview, Preview Commander + Preferences, commander_discovery_commander_preference_handoff_preview, selected commander, build preferences, Basic Land Access Assumption, No deck generation.

# v1.3.10 UI markers: Commander Shell Skeleton Preview, Preview Shell Skeleton, commander_discovery_shell_skeleton_preview, create_commander_shell_skeleton_preview, Basic lands are assumed available, Nonbasic lands remain collection-first, No deck generation.

# v1.3.11 UI markers: Build From Collection Setup Summary Preview, Preview Setup Summary, commander_discovery_setup_summary_preview, create_build_from_collection_setup_summary_preview, Basic lands are assumed available, Nonbasic lands remain collection-first, No deck generation.

# v1.3.13 UI markers: Build Depth Selection, B — Build-Start Summary, C — Owned Cards By Role, D — Rough Shell, E — Full 100-Card Draft, commander_discovery_selected_build_depth_key, commander_discovery_build_depth_selection_preview, selected build depth, No deck generation.

# v1.3.14 UI markers: Strategy Selection / Override Preview, Preview Strategy Selection, commander_discovery_strategy_selection_override_preview, commander_discovery_primary_strategy_combo, commander_discovery_secondary_strategy_combo, inferred strategy suggestions, user strategy override, selected strategy carried into setup summary, No deck generation.

# v1.3.15 UI markers: Philosophy + Bracket Build Preference, Preview Philosophy + Bracket, commander_discovery_philosophy_bracket_preference_preview, commander_discovery_main_philosophy_combo, commander_discovery_sub_philosophy_combo, commander_discovery_bracket_preference_combo, philosophy selection carried into setup summary, bracket preference carried into setup summary, No deck generation.

# v1.3.16 UI markers: Collection Source Preference, Preview Collection Source Preference, commander_discovery_collection_source_preference_combo, commander_discovery_collection_source_preference_preview, outside-collection upgrades are user-controlled, No deck generation.

# v1.3.16.2 marker: repaired Collection Source Preference UI syntax; Collection Source Preference; Preview Collection Source Preference; No deck generation.

# v1.3.19 UI markers: Build-Start Summary Output, Write Build-Start Summary Output, commander_discovery_build_start_summary_output, commander_discovery_build_start_summary_write_result, human-readable report, AI handoff prompt, No deck generation.
# v1.3.21 UI markers: Owned Cards By Role Output, Write Owned Cards By Role Output, commander_discovery_owned_cards_by_role_output, commander_discovery_owned_cards_by_role_write_result, possible role fits, AI handoff prompt, No deck generation.

# v1.3.27.1 marker: Preview Selected Output Route
BUILD_FROM_COLLECTION_OUTPUT_SELECTOR_UI_MARKER_v1_3_27_1 = 'Preview Selected Output Route'

# v1.3.29 Build From Collection Output Execution UI Hook
COMMANDER_DISCOVERY_OUTPUT_EXECUTION_GUARD_STATUS_LABEL = "Output Execution Guard Status"
COMMANDER_DISCOVERY_PREVIEW_OUTPUT_EXECUTION_GUARD_LABEL = "Preview Output Execution Guard"
COMMANDER_DISCOVERY_OUTPUT_EXECUTION_GUARD_BOUNDARY = "No writer execution. No deck generation."

def _v1_3_29_output_execution_ui_hook_marker() -> str:
    return "Output Execution Guard Status - Preview Output Execution Guard - No writer execution - No deck generation"


# v1.3.30 Build From Collection Output Execute Selected Report Button UI hook markers
# Execute Selected Report Output
# _execute_selected_build_from_collection_report_output
# commander_discovery_execute_selected_report_output_result
# Guarded report output only - No deck generation
# v1.3.31 Build From Collection Execute Selected Report UI Polish markers
# Execute Selected Report Output
# Selected Report Output Status
# Explicit confirmation required
# Writes report artifacts only
# No writer execution
# No deck generation


def _v1_3_31_execute_selected_report_ui_polish_markers() -> tuple[str, ...]:
    """Display-only markers for v1.3.31 selected report execution UI polish."""
    return (
        "Execute Selected Report Output",
        "Selected Report Output Status",
        "Explicit confirmation required",
        "Writes report artifacts only",
        "No writer execution",
        "No deck generation",
    )
