"""Review Setup page builder for The Dragon's Touch v0.7 alpha hardening.

This module intentionally builds only the Review Setup page layout and signal
wiring. The active MainWindow remains the workflow owner for staged state,
Run Analysis refreshes, backend handoff, and CLI/main.py execution.
"""

from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
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
        COMBO_AWARENESS_OPTIONS,
        COLLECTION_MODE_OPTIONS,
        COLLECTION_MODE_OPTIONS,
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
        COMBO_AWARENESS_OPTIONS,
    )
    from widgets import add_shadow, TexturedPanel, ReportCard



def _compact_row(window, label_text, widget, note_text=""):
    row = QWidget()
    row_layout = QHBoxLayout(row)
    row_layout.setContentsMargins(0, 0, 0, 0)
    row_layout.setSpacing(12)

    label = QLabel(label_text)
    label.setObjectName("helperText")
    label.setFixedWidth(120)
    label.setWordWrap(True)

    row_layout.addWidget(label)
    row_layout.addWidget(widget, stretch=1)

    if note_text:
        note = QLabel(note_text)
        note.setObjectName("defaultNote")
        note.setWordWrap(True)
        note.setMinimumWidth(140)
        row_layout.addWidget(note, stretch=1)

    return row


def _make_combo(window, options, current):
    combo = QComboBox()
    combo.addItems(options)
    combo.setCurrentText(current)
    window.configure_combo_popup(combo)
    combo.setMinimumHeight(30)
    return combo


def build_review_setup_page(window):
    """Build compact current-run Review Setup controls.

    v0.10.5.4-dev:
    - Compact current-run settings layout.

    v0.10.5.4.1-dev:
    - Readability and combo Yes/No hotfix.

    v0.10.5.4.2-dev:
    - Dashboard-fit layout.

    v0.10.6.1-dev:
    - Combo awareness is always included and no longer a user toggle.
    - Settings owns app-wide defaults.
    - Review Setup owns current-run choices.
    - Collection Mode now lives here.
    """
    page, layout = window.page_container(
        "Review Setup",
        f"Stage current-run choices for one deck review. {APP_VERSION} keeps app-wide defaults in Settings and run choices here."
    )

    scroll, content = window.scroll_content()
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    grid_panel = TexturedPanel(window.theme, kind="iron", glow=False)
    add_shadow(grid_panel, blur=24, y=8)
    grid = QGridLayout(grid_panel)
    grid.setContentsMargins(14, 14, 14, 14)
    grid.setSpacing(10)
    grid.setColumnStretch(0, 1)
    grid.setColumnStretch(1, 1)

    # ------------------------------------------------------------------
    # Review basics.
    # ------------------------------------------------------------------
    basics_card = ReportCard("Review Basics", window.theme, badges=[("Current run", "primary")])

    output_combo = _make_combo(window, OUTPUT_MODE_OPTIONS, window.state.output_mode)
    direction_combo = _make_combo(window, REVIEW_DIRECTION_OPTIONS, window.state.review_direction)
    cut_combo = _make_combo(window, REVIEW_INTENSITY_OPTIONS, window.state.cut_depth)
    build_up_combo = _make_combo(window, BUILD_UP_MODE_OPTIONS, window.state.build_up_mode)
    prompt_combo = _make_combo(window, PROMPT_MODE_OPTIONS, window.state.prompt_mode)

    basics_card.body.addWidget(_compact_row(window, "Output mode", output_combo, "Normal, debug, or both report paths."))
    basics_card.body.addWidget(_compact_row(window, "Review direction", direction_combo, "Cut down, build up, or auto batch."))
    basics_card.body.addWidget(_compact_row(window, "Review intensity", cut_combo, "How hard the review should press on cuts."))
    basics_card.body.addWidget(_compact_row(window, "Build-up mode", build_up_combo, "Used when the deck needs cards added."))
    basics_card.body.addWidget(_compact_row(window, "Prompt mode", prompt_combo, "Interactive AI chat or one-shot worksheet."))

    intensity_meaning_label = window.default_note(window.review_intensity_meaning())
    basics_card.body.addWidget(intensity_meaning_label)

    # ------------------------------------------------------------------
    # Table, collection, and combo boundaries.
    # ------------------------------------------------------------------
    boundaries_card = ReportCard("Table / Collection Boundaries", window.theme, badges=[("Current run", "primary")])

    intended_bracket_combo = _make_combo(window, INTENDED_BRACKET_OPTIONS, window.state.intended_bracket)
    budget_input = QLineEdit(window.state.budget_note)
    budget_input.setMinimumHeight(30)

    collection_mode_combo = _make_combo(window, COLLECTION_MODE_OPTIONS, window.state.collection_mode)
    # Combo awareness is always on; the engine reads this. The user-facing
    # "Combo analysis: Always included" row was removed (tester: redundant — the
    # user just receives the benefit, no need to be told it's always on).
    window.state.combo_awareness_mode = "Always included"

    boundaries_card.body.addWidget(_compact_row(window, "Intended bracket", intended_bracket_combo, "Used as table-fit guidance, not legality."))
    boundaries_card.body.addWidget(_compact_row(window, "Budget note", budget_input, "Optional note such as $25/card."))
    boundaries_card.body.addWidget(_compact_row(window, "Collection mode", collection_mode_combo, "Current-run replacement source behavior."))
    boundaries_card.body.addWidget(window.default_note(
        "Collection Source default lives in Settings. Collection Mode lives here because it changes the current review run."
    ))

    # ------------------------------------------------------------------
    # Summary.
    # ------------------------------------------------------------------
    summary = ReportCard("Run Settings Summary", window.theme)
    summary_label = window.make_text(window.review_settings_summary_text(), paper=True)
    summary_label.setMinimumHeight(205)
    summary_label.setStyleSheet("""
        QPlainTextEdit {
            color: #1f1208;
            background-color: rgba(246, 226, 170, 235);
            border: 1px solid rgba(126, 75, 26, 130);
            border-radius: 10px;
            padding: 10px;
            font-size: 12px;
        }
    """)
    summary.body.addWidget(summary_label)
    summary.body.addWidget(window.default_note("Auto-staged: changes update this summary immediately. No Apply button required."))

    # The "Safety Boundary" card was removed per tester feedback (no longer
    # needed for shipping). The no-auto-edit guarantee still holds and is noted
    # at the actual run step (guarded confirmation).

    # Run Settings Summary is Developer-Mode only (tester: redundant with the
    # button confirmations). User Mode = just Review Basics + Boundaries, compact.
    grid.addWidget(basics_card, 0, 0)
    if window.is_dev_mode():
        grid.addWidget(summary, 0, 1)
        grid.addWidget(boundaries_card, 1, 0, 1, 2)
    else:
        grid.addWidget(boundaries_card, 0, 1)

    def auto_stage_review():
        window.stage_review_settings(
            output_combo,
            direction_combo,
            cut_combo,
            build_up_combo,
            prompt_combo,
            budget_input,
            intended_bracket_combo,
            None,
            collection_mode_combo,
            summary_label,
            intensity_meaning_label,
        )

    output_combo.currentTextChanged.connect(lambda _text: auto_stage_review())
    direction_combo.currentTextChanged.connect(lambda _text: auto_stage_review())
    cut_combo.currentTextChanged.connect(lambda _text: auto_stage_review())
    build_up_combo.currentTextChanged.connect(lambda _text: auto_stage_review())
    prompt_combo.currentTextChanged.connect(lambda _text: auto_stage_review())
    budget_input.textChanged.connect(lambda _text: auto_stage_review())
    intended_bracket_combo.currentTextChanged.connect(lambda _text: auto_stage_review())
    collection_mode_combo.currentTextChanged.connect(lambda _text: auto_stage_review())

    content.addWidget(grid_panel)
    content.addStretch(1)
    layout.addWidget(scroll, stretch=1)
    return page
