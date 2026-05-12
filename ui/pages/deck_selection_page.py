"""Deck Selection page builder for The Dragon's Touch v0.7 alpha hardening.

This module intentionally builds only the Deck Selection page layout. It does
not own deck parsing, file dialogs, staged state mutation, backend handoff, or
backend validation. The active MainWindow remains the workflow owner and passes
itself into this builder so existing Deck Selection methods/signals remain
stable during page extraction.
"""

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

try:
    from ui.constants import APP_VERSION
    from ui.widgets import add_shadow, TexturedPanel, ReportCard
except ImportError:  # Allows direct local execution from inside the ui/ folder.
    from constants import APP_VERSION
    from widgets import add_shadow, TexturedPanel, ReportCard


def build_deck_selection_page(window):
    """Build the Deck Selection page while keeping behavior on MainWindow."""
    page, layout = window.page_container(
        "Deck Selection",
        f"Choose a local deck file and preview it safely. {APP_VERSION} uses this staged deck for guarded CLI runs while the backend remains the source of truth."
    )
    body = TexturedPanel(window.theme, kind="iron", glow=False)
    add_shadow(body, blur=26, y=8)
    body_layout = QHBoxLayout(body)
    body_layout.setContentsMargins(22, 22, 22, 22)
    body_layout.setSpacing(16)

    left = TexturedPanel(window.theme, parchment=True)
    left_layout = QVBoxLayout(left)
    left_layout.setContentsMargins(20, 18, 20, 18)
    left_layout.setSpacing(12)
    title = QLabel("Deck File & Commander Preview")
    title.setObjectName("reportTitle")
    left_layout.addWidget(title)

    file_path = QLineEdit(window.state.selected_deck_path)
    file_path.setReadOnly(True)
    deck_name = QLineEdit(window.state.deck_name)
    deck_name.setReadOnly(True)
    commander = QLineEdit(window.state.commander)
    commander.setReadOnly(True)
    decklist = QPlainTextEdit()
    decklist.setPlainText(window.state.deck_preview_text)
    # Keep the preview scrollable but deliberately short enough that the
    # action-button row always lives below it instead of visually sitting on top.
    # The backend parser remains the source of truth later; this is only a UI preview.
    decklist.setMinimumHeight(175)
    decklist.setMaximumHeight(195)
    decklist.setFixedHeight(185)
    decklist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    decklist.setReadOnly(True)

    for label, widget in [
        ("Selected Deck File", file_path),
        ("Deck Name", deck_name),
        ("Commander Name", commander),
        ("Decklist Preview", decklist),
    ]:
        left_layout.addWidget(QLabel(label))
        left_layout.addWidget(widget, stretch=0)

    # Keep the preview box from consuming the button row area at normal window sizes.
    # The preview remains scrollable, but the action buttons always get their own
    # separate row with a visible parchment gap above it.
    left_layout.addSpacing(18)
    button_row = QHBoxLayout()
    button_row.setContentsMargins(0, 8, 0, 0)
    button_row.setSpacing(12)
    choose_btn = QPushButton("Choose Deck File")
    choose_btn.clicked.connect(window.choose_deck_file)
    preview_btn = QPushButton("Reload Preview")
    preview_btn.clicked.connect(window.reload_selected_deck_preview)
    paste_btn = QPushButton("Paste Decklist Later")
    paste_btn.clicked.connect(lambda: window.backend_hook_message("Paste/import decklist"))
    for button in [choose_btn, preview_btn, paste_btn]:
        button.setMinimumHeight(44)
        button_row.addWidget(button)
    left_layout.addLayout(button_row, stretch=0)
    left_layout.addStretch(1)

    right = QVBoxLayout()
    right.setSpacing(14)
    status = TexturedPanel(window.theme, kind="iron_2", glow=True)
    status_layout = QVBoxLayout(status)
    status_layout.setContentsMargins(18, 16, 18, 16)
    cap = QLabel("FILE PREVIEW STATUS")
    cap.setObjectName("smallCaps")
    status_layout.addWidget(cap)
    status_layout.addWidget(window.make_text(window.deck_preview_status_text()))
    progress = QProgressBar()
    progress.setValue(100 if window.state.selected_deck_path != "No deck file selected" else 0)
    status_layout.addWidget(progress)
    quick = ReportCard("Forge Note", window.theme)
    quick.body.addWidget(window.make_text(
        f"{APP_VERSION} keeps real local deck-file selection, preserves preview spacing, and stages the selected file for guarded CLI handoff. Backend validation, legality, collection loading, and report generation remain owned by main.py.",
        paper=True
    ))
    right.addWidget(status)
    right.addWidget(quick)
    right.addStretch(1)
    body_layout.addWidget(left, stretch=2)
    body_layout.addLayout(right, stretch=1)
    layout.addWidget(body, stretch=1)
    return page
