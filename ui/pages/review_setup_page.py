"""Review Setup page builder for The Dragon's Touch v0.7 alpha hardening.

This module intentionally builds only the Review Setup page layout and signal
wiring. The active MainWindow remains the workflow owner for staged state,
Run Analysis refreshes, backend handoff, and CLI/main.py execution.
"""

from PySide6.QtCore import QSignalBlocker
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

try:
    from ui.constants import (
        APP_VERSION,
        OUTPUT_MODE_OPTIONS,
        REVIEW_DIRECTION_OPTIONS,
        REVIEW_INTENSITY_OPTIONS,
        BUILD_UP_MODE_OPTIONS,
        PROMPT_MODE_OPTIONS,
        INTENDED_BRACKET_OPTIONS,
    )
    from ui.widgets import add_shadow, TexturedPanel, ReportCard
except ImportError:  # Allows direct local execution from inside the ui/ folder.
    from constants import (
        APP_VERSION,
        OUTPUT_MODE_OPTIONS,
        REVIEW_DIRECTION_OPTIONS,
        REVIEW_INTENSITY_OPTIONS,
        BUILD_UP_MODE_OPTIONS,
        PROMPT_MODE_OPTIONS,
        INTENDED_BRACKET_OPTIONS,
    )
    from widgets import add_shadow, TexturedPanel, ReportCard


def build_review_setup_page(window):
    """Build the Review Setup page while keeping staged-state behavior on MainWindow."""
    page, layout = window.page_container(
        "Review Setup",
        f"Stage the same review choices the CLI already supports. {APP_VERSION} auto-stages choices as you change them and hands them to main.py through the guarded CLI bridge."
    )
    scroll, content = window.scroll_content()
    grid_panel = TexturedPanel(window.theme, kind="iron", glow=False); add_shadow(grid_panel, blur=24, y=8)
    grid = QGridLayout(grid_panel); grid.setContentsMargins(22, 22, 22, 22); grid.setSpacing(16)
    grid.setColumnStretch(0, 1)
    grid.setColumnStretch(1, 1)

    output_card = ReportCard("Output Mode", window.theme)
    output_combo = QComboBox(); output_combo.addItems(OUTPUT_MODE_OPTIONS); output_combo.setCurrentText(window.state.output_mode); window.configure_combo_popup(output_combo)
    output_card.body.addWidget(output_combo); output_card.body.addWidget(window.default_note("Default: Both")); grid.addWidget(output_card, 0, 0)

    direction_card = ReportCard("Review Direction", window.theme)
    direction_combo = QComboBox(); direction_combo.addItems(REVIEW_DIRECTION_OPTIONS); direction_combo.setCurrentText(window.state.review_direction); window.configure_combo_popup(direction_combo)
    direction_card.body.addWidget(direction_combo)
    direction_card.body.addWidget(window.default_note("Default: Cut down. Auto batch is development-oriented and will move behind development mode later."))
    grid.addWidget(direction_card, 0, 1)

    cut_card = ReportCard("Review Intensity", window.theme)
    cut_combo = QComboBox(); cut_combo.addItems(REVIEW_INTENSITY_OPTIONS); cut_combo.setCurrentText(window.state.cut_depth); window.configure_combo_popup(cut_combo)
    cut_card.body.addWidget(cut_combo)
    intensity_meaning_label = window.make_text(window.review_intensity_meaning(), paper=True)
    cut_card.body.addWidget(intensity_meaning_label)
    cut_card.body.addWidget(window.default_note("Used when Review Direction is Cut down. Also used as an Auto batch default."))

    build_up_card = ReportCard("Build-Up Mode", window.theme)
    build_up_combo = QComboBox()
    build_up_combo.addItems(BUILD_UP_MODE_OPTIONS)
    build_up_combo.setCurrentText(window.state.build_up_mode)
    window.configure_combo_popup(build_up_combo)
    build_up_card.body.addWidget(build_up_combo)
    build_up_card.body.addWidget(window.default_note("Used when Review Direction is Build up. Auto batch may show both fields as global defaults."))

    direction_mode_stack = QStackedWidget()
    direction_mode_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    direction_mode_stack.addWidget(cut_card)
    direction_mode_stack.addWidget(build_up_card)
    auto_batch_panel = QWidget()
    auto_panel_layout = QVBoxLayout(auto_batch_panel)
    auto_panel_layout.setContentsMargins(0, 0, 0, 0)
    auto_panel_layout.setSpacing(12)
    # Clone-like dedicated cards keep the Auto batch view from moving the single-mode cards out of the stack.
    auto_cut_card = ReportCard("Review Intensity", window.theme)
    auto_cut_combo = QComboBox(); auto_cut_combo.addItems(REVIEW_INTENSITY_OPTIONS); auto_cut_combo.setCurrentText(window.state.cut_depth); window.configure_combo_popup(auto_cut_combo)
    auto_cut_card.body.addWidget(auto_cut_combo)
    auto_intensity_label = window.make_text(window.review_intensity_meaning(), paper=True)
    auto_cut_card.body.addWidget(auto_intensity_label)
    auto_cut_card.body.addWidget(window.default_note("Auto batch default for 100+ card / cut-down style reviews."))
    auto_build_card = ReportCard("Build-Up Mode", window.theme)
    auto_build_combo = QComboBox(); auto_build_combo.addItems(BUILD_UP_MODE_OPTIONS); auto_build_combo.setCurrentText(window.state.build_up_mode); window.configure_combo_popup(auto_build_combo)
    auto_build_card.body.addWidget(auto_build_combo)
    auto_build_card.body.addWidget(window.default_note("Auto batch default for under-100-card / build-up style reviews."))
    auto_panel_layout.addWidget(auto_cut_card)
    auto_panel_layout.addWidget(auto_build_card)
    auto_panel_layout.addWidget(window.default_note("Auto batch remains development-oriented and will move behind development mode later."))
    direction_mode_stack.addWidget(auto_batch_panel)
    grid.addWidget(direction_mode_stack, 1, 0)

    prompt_card = ReportCard("Prompt Mode", window.theme)
    prompt_combo = QComboBox(); prompt_combo.addItems(PROMPT_MODE_OPTIONS); prompt_combo.setCurrentText(window.state.prompt_mode); window.configure_combo_popup(prompt_combo)
    prompt_card.body.addWidget(prompt_combo); prompt_card.body.addWidget(window.default_note("Default: Interactive AI chat")); grid.addWidget(prompt_card, 1, 1)

    budget_card = ReportCard("Table / Budget Boundaries", window.theme)
    budget_input = QLineEdit(window.state.budget_note)
    intended_bracket_combo = QComboBox()
    intended_bracket_combo.addItems(INTENDED_BRACKET_OPTIONS)
    intended_bracket_combo.setCurrentText(window.state.intended_bracket)
    window.configure_combo_popup(intended_bracket_combo)
    budget_card.body.addWidget(QLabel("Budget Note"))
    budget_card.body.addWidget(budget_input)
    budget_card.body.addWidget(QLabel("Bracket Intended"))
    budget_card.body.addWidget(intended_bracket_combo)
    budget_card.body.addWidget(window.default_note("Collection mode and file selection live on the Collection Source page. Bracket and collection values are staged through dropdowns, not checkboxes."))
    grid.addWidget(budget_card, 2, 0)

    summary = TexturedPanel(window.theme, kind="iron_2", glow=True)
    s_layout = QVBoxLayout(summary); s_layout.setContentsMargins(18, 16, 18, 16)
    s_title = QLabel("Run Settings Summary"); s_title.setObjectName("sectionTitle"); s_layout.addWidget(s_title)
    summary_label = window.make_text(window.review_settings_summary_text())
    s_layout.addWidget(summary_label)
    auto_note = window.default_note("Auto-staged: changes update this summary immediately. No Apply button required.")
    s_layout.addWidget(auto_note)
    grid.addWidget(summary, 2, 1)

    def refresh_direction_specific_review_fields():
        direction = direction_combo.currentText()
        if direction == "Build up":
            direction_mode_stack.setCurrentIndex(1)
        elif direction == "Auto batch":
            direction_mode_stack.setCurrentIndex(2)
        else:
            direction_mode_stack.setCurrentIndex(0)

    def sync_auto_batch_mirrors():
        blocker_a = QSignalBlocker(auto_cut_combo)
        auto_cut_combo.setCurrentText(cut_combo.currentText())
        del blocker_a
        blocker_b = QSignalBlocker(auto_build_combo)
        auto_build_combo.setCurrentText(build_up_combo.currentText())
        del blocker_b
        auto_intensity_label.setText(window.review_intensity_meaning())

    def auto_stage_review():
        if direction_combo.currentText() == "Auto batch":
            # Keep the single-mode controls in sync with the Auto batch mirror controls.
            blocker_cut = QSignalBlocker(cut_combo)
            cut_combo.setCurrentText(auto_cut_combo.currentText())
            del blocker_cut
            blocker_build = QSignalBlocker(build_up_combo)
            build_up_combo.setCurrentText(auto_build_combo.currentText())
            del blocker_build
        window.stage_review_settings(output_combo, direction_combo, cut_combo, build_up_combo, prompt_combo, budget_input, intended_bracket_combo, summary_label, intensity_meaning_label)
        sync_auto_batch_mirrors()
        refresh_direction_specific_review_fields()

    refresh_direction_specific_review_fields()
    sync_auto_batch_mirrors()

    output_combo.currentTextChanged.connect(lambda _text: auto_stage_review())
    direction_combo.currentTextChanged.connect(lambda _text: auto_stage_review())
    cut_combo.currentTextChanged.connect(lambda _text: auto_stage_review())
    build_up_combo.currentTextChanged.connect(lambda _text: auto_stage_review())
    auto_cut_combo.currentTextChanged.connect(lambda _text: auto_stage_review())
    auto_build_combo.currentTextChanged.connect(lambda _text: auto_stage_review())
    prompt_combo.currentTextChanged.connect(lambda _text: auto_stage_review())
    budget_input.textChanged.connect(lambda _text: auto_stage_review())
    intended_bracket_combo.currentTextChanged.connect(lambda _text: auto_stage_review())

    note = TexturedPanel(window.theme, kind="iron_2", glow=False)
    n_layout = QVBoxLayout(note); n_layout.setContentsMargins(18, 14, 18, 14)
    n_title = QLabel("v0.6.7.9.12 Boundary"); n_title.setObjectName("sectionTitle"); n_layout.addWidget(n_title)
    n_layout.addWidget(window.make_text("These choices auto-stage inside the UI as soon as you change them. Table bracket and collection handoff checkboxes were removed; Bracket Intended and the Collection Source page now carry those staged values directly."))
    grid.addWidget(note, 3, 0, 1, 2)

    content.addWidget(grid_panel); content.addStretch(1); layout.addWidget(scroll, stretch=1); return page

