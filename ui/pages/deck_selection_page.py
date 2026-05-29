"""Deck Selection page builder for The Dragon's Touch v0.7 alpha hardening.

    # Alpha onboarding note: Archidekt export tip: export or copy your decklist as plain text, save it as a .txt file in Decklists, then select it here.

This module intentionally builds only the Deck Selection page layout. It does
not own deck parsing, file dialogs, staged state mutation, backend handoff, or
backend validation. The active MainWindow remains the workflow owner and passes
itself into this builder so existing Deck Selection methods/signals remain
stable during page extraction.
"""

from pathlib import Path

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QTabWidget,
    QTextEdit,
    QInputDialog,
    QMessageBox,
    QFileDialog,
)

try:
    from ui.constants import APP_VERSION, ARCHIDEKT_EXPORT_HELP_TEXT
    from ui.widgets import add_shadow, TexturedPanel, ReportCard
except ImportError:  # Allows direct local execution from inside the ui/ folder.
    from constants import APP_VERSION, ARCHIDEKT_EXPORT_HELP_TEXT
    from widgets import add_shadow, TexturedPanel, ReportCard


def _deck_selection_intro_text():
    return (
        "Choose how to provide the deck for this run. "
        "Select an existing file, paste a decklist, or use the future import-link placeholder."
    )


def _current_selected_deck_path(window):
    path_text = getattr(window.state, "selected_deck_path", "") or ""
    if not path_text or path_text == "No deck file selected":
        path_text = getattr(window.state, "deck_file", "") or ""
    return path_text


def _deck_file_preview_text(window):
    path_text = _current_selected_deck_path(window)
    if not path_text:
        return "No deck file selected yet."

    try:
        path = Path(path_text)
        if not path.exists():
            return f"Selected deck file no longer exists:\n{path_text}"
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        preview = "\n".join(lines[:28])
        if len(lines) > 28:
            preview += f"\n...\n({len(lines) - 28} more line(s) in deck file)"
        return preview or "Selected deck file is empty."
    except Exception as exc:
        return f"Could not preview selected deck file:\n{path_text}\n\n{exc}"


def _update_deck_selection_preview(window):
    preview = getattr(window, "deck_selection_preview_box", None)
    if preview is not None:
        preview.setPlainText(_deck_file_preview_text(window))

    status = getattr(window, "deck_selection_status_label", None)
    if status is not None:
        deck_file = _current_selected_deck_path(window)
        status.setText(deck_file if deck_file else "No deck selected yet.")


def _paste_deck_text(window):
    box = getattr(window, "paste_decklist_text_box", None)
    return box.toPlainText().strip() if box is not None else ""


def _clear_pasted_decklist(window):
    box = getattr(window, "paste_decklist_text_box", None)
    if box is not None:
        box.clear()
    window.state.status = "Pasted decklist cleared"
    window.refresh_context_panel_values()


def _use_pasted_decklist_without_saving(window):
    text = _paste_deck_text(window)
    if not text:
        # Category C (popup removal): paste box is the source of truth — user sees it's empty.
        window.state.status = "Paste a decklist into the Paste tab before using it for this run."
        if hasattr(window, "refresh_context_panel_values"):
            window.refresh_context_panel_values()
        return

    path_text = window.create_temp_pasted_decklist(text)
    window.load_deck_file_preview(path_text)
    window.state.status = "Pasted decklist staged for this run without saving to Decklist Folder"
    window.refresh_context_panel_values()


def _save_pasted_decklist(window):
    text = _paste_deck_text(window)
    if not text:
        # Category C (popup removal): paste box is the source of truth.
        window.state.status = "Paste a decklist into the Paste tab before saving."
        if hasattr(window, "refresh_context_panel_values"):
            window.refresh_context_panel_values()
        return

    name, ok = QInputDialog.getText(window, "Save Pasted Decklist", "Deck name:")
    if not ok:
        return

    path_text = window.save_pasted_decklist_to_deck_folder(text, name)
    if not path_text:
        return

    window.load_deck_file_preview(path_text)
    # Category B (popup removal): the status update + visible preview is the
    # feedback. The right-side context panel shows "Saved pasted decklist: X"
    # via window.state.status; the deck preview box on this page now shows
    # the file content. No modal needed.
    window.state.status = f"Saved pasted decklist: {Path(path_text).name}"
    window.refresh_context_panel_values()


def _select_deck_file(window):
    start = getattr(window.state, "deck_folder", "Decklists") or "Decklists"
    file_path, _ = QFileDialog.getOpenFileName(
        window,
        "Select Commander Decklist",
        start,
        "Decklists (*.txt *.dek *.csv);;Text files (*.txt);;All files (*.*)",
    )
    if not file_path:
        return
    window.state.deck_folder = str(Path(file_path).parent)
    window.load_deck_file_preview(file_path)
    window.refresh_context_panel_values()


def _choose_deck_folder(window):
    start = getattr(window.state, "deck_folder", "Decklists") or "Decklists"
    folder = QFileDialog.getExistingDirectory(window, "Choose Decklist Folder", start)
    if not folder:
        return
    window.state.deck_folder = folder
    window.state.status = "Decklist folder selected"
    if getattr(window, "deck_folder_label", None) is not None:
        window.deck_folder_label.setText(folder)
    window.refresh_context_panel_values()
    _update_deck_selection_preview(window)

def build_deck_selection_page(window):
    page, layout = window.page_container(
        "Deck Selection",
        "Choose a Commander decklist by selecting a file, pasting a decklist, or preparing for future link import."
    )

    scroll, content = window.scroll_content()

    shell = TexturedPanel(window.theme, kind="iron", glow=False)
    add_shadow(shell, blur=24, y=8)
    shell_layout = QVBoxLayout(shell)
    shell_layout.setContentsMargins(22, 22, 22, 22)
    shell_layout.setSpacing(16)

    intro = QLabel(_deck_selection_intro_text())
    intro.setObjectName("defaultNote")
    intro.setWordWrap(True)
    shell_layout.addWidget(intro)

    tabs = QTabWidget()
    tabs.setObjectName("deckSelectionTabs")
    tabs.setDocumentMode(True)

    # ------------------------------------------------------------------
    # Select File tab.
    # ------------------------------------------------------------------
    select_tab = QWidget()
    select_layout = QVBoxLayout(select_tab)
    select_layout.setContentsMargins(14, 14, 14, 14)
    select_layout.setSpacing(12)

    select_card = ReportCard("Select File", window.theme, badges=[("Current", "primary")])
    select_card.body.addWidget(window.default_note(
        "Select an existing decklist file. This preserves the current file-selection workflow."
    ))
    # First-run polish: surface the Archidekt export path inline so new users
    # know where to get a compatible plain-text decklist from.
    select_card.body.addWidget(window.make_text(
        "New here? From Archidekt, open your deck → Export / Download → save the plain-text decklist, "
        "then use Choose Folder + Select Deck File below to pick it. Commander sections, maybeboard, tokens, "
        "and companion sections are previewed conservatively before the backend validation run.",
        paper=True,
    ))

    deck_folder_row = QHBoxLayout()
    deck_folder_label = QLabel("Decklist Folder")
    deck_folder_label.setObjectName("helperText")
    deck_folder_label.setMinimumWidth(150)
    current_folder = QLabel(getattr(window.state, "deck_folder", "Decklists") or "Decklists")
    current_folder.setObjectName("defaultNote")
    current_folder.setWordWrap(True)
    window.deck_folder_label = current_folder

    choose_folder_btn = QPushButton("Choose Folder")
    choose_folder_btn.setObjectName("utilityButton")
    choose_folder_btn.clicked.connect(lambda checked=False: _choose_deck_folder(window))

    select_file_btn = QPushButton("Select Deck File")
    select_file_btn.setObjectName("primaryButton")
    select_file_btn.clicked.connect(lambda checked=False: _select_deck_file(window))

    deck_folder_row.addWidget(deck_folder_label)
    deck_folder_row.addWidget(current_folder, stretch=1)
    deck_folder_row.addWidget(choose_folder_btn)
    deck_folder_row.addWidget(select_file_btn)
    select_card.body.addLayout(deck_folder_row)

    selected_status = QLabel(_current_selected_deck_path(window) or "No deck selected yet.")
    selected_status.setObjectName("defaultNote")
    selected_status.setWordWrap(True)
    window.deck_selection_status_label = selected_status
    select_card.body.addWidget(selected_status)

    preview = QPlainTextEdit()
    preview.setReadOnly(True)
    preview.setObjectName("reportFilePreview")
    preview.setMinimumHeight(220)
    preview.setPlainText(_deck_file_preview_text(window))
    window.deck_selection_preview_box = preview
    select_card.body.addWidget(preview)

    select_layout.addWidget(select_card)
    select_layout.addStretch(1)
    tabs.addTab(select_tab, "Select File")

    # ------------------------------------------------------------------
    # Paste Decklist tab.
    # ------------------------------------------------------------------
    paste_tab = QWidget()
    paste_layout = QVBoxLayout(paste_tab)
    paste_layout.setContentsMargins(14, 14, 14, 14)
    paste_layout.setSpacing(12)

    paste_card = ReportCard("Paste Decklist", window.theme, badges=[("New", "primary")])
    paste_card.body.addWidget(window.default_note(
        "Paste a Commander decklist here. You can use it for the current run only, or save it into the Decklist Folder with the next available number."
    ))

    paste_box = QTextEdit()
    paste_box.setObjectName("deckPasteBox")
    paste_box.setPlaceholderText("Paste decklist here...\n\nExample:\n1 Sol Ring\n1 Arcane Signet\n1 Command Tower")
    paste_box.setStyleSheet("""
        QTextEdit#deckPasteBox {
            color: #1f1208;
            background-color: rgba(245, 225, 170, 230);
            selection-color: #fff8e8;
            selection-background-color: #7a3f18;
            border: 1px solid rgba(126, 75, 26, 150);
            border-radius: 10px;
            padding: 10px;
        }
        QTextEdit#deckPasteBox QScrollBar:vertical {
            background: rgba(70, 34, 16, 60);
            width: 12px;
        }
    """)
    paste_box.setMinimumHeight(280)
    window.paste_decklist_text_box = paste_box
    paste_card.body.addWidget(paste_box)

    paste_actions = QHBoxLayout()
    use_without_save_btn = QPushButton("Use for This Run")
    use_without_save_btn.setObjectName("utilityButton")
    use_without_save_btn.clicked.connect(lambda checked=False: _use_pasted_decklist_without_saving(window))

    save_paste_btn = QPushButton("Save to Decklist Folder")
    save_paste_btn.setObjectName("primaryButton")
    save_paste_btn.clicked.connect(lambda checked=False: _save_pasted_decklist(window))

    clear_paste_btn = QPushButton("Clear")
    clear_paste_btn.setObjectName("utilityButton")
    clear_paste_btn.clicked.connect(lambda checked=False: _clear_pasted_decklist(window))

    paste_actions.addWidget(use_without_save_btn)
    paste_actions.addWidget(save_paste_btn)
    paste_actions.addWidget(clear_paste_btn)
    paste_actions.addStretch(1)
    paste_card.body.addLayout(paste_actions)

    paste_card.body.addWidget(window.default_note(
        "Saved pasted decklists use the next available number, such as 29. My Deck Name.txt. Existing decklists are never overwritten."
    ))

    paste_layout.addWidget(paste_card)
    paste_layout.addStretch(1)
    tabs.addTab(paste_tab, "Paste Decklist")

    # ------------------------------------------------------------------
    # Import Link tab.
    # ------------------------------------------------------------------
    link_tab = QWidget()
    link_layout = QVBoxLayout(link_tab)
    link_layout.setContentsMargins(14, 14, 14, 14)
    link_layout.setSpacing(12)

    link_card = ReportCard("Import Link", window.theme, badges=[("Coming soon", "manual")])
    link_card.body.addWidget(window.make_text(
        "Import Link is a placeholder for a future release.\n\n"
        "Planned future use:\n"
        "- Paste a decklist URL\n"
        "- Detect supported source\n"
        "- Import into Decklist Folder\n\n"
        "For v0.10.5-dev, use Select File or Paste Decklist.",
        paper=True,
    ))

    link_input = QLineEdit()
    link_input.setPlaceholderText("Future placeholder — link import is not active yet")
    link_input.setEnabled(False)
    link_card.body.addWidget(link_input)

    coming_soon = QPushButton("Import Link Coming Soon")
    coming_soon.setEnabled(False)
    link_card.body.addWidget(coming_soon)

    link_layout.addWidget(link_card)
    link_layout.addStretch(1)
    tabs.addTab(link_tab, "Import Link")

    shell_layout.addWidget(tabs)

    # First-run polish: clear "where to next" guidance for the two main flows.
    next_steps_card = ReportCard("Where to Next?", window.theme, badges=[("Quick Start", "primary")])
    next_steps_card.body.addWidget(window.make_text(
        "Two ways to use The Dragon's Touch:\n\n"
        "• Deck review — pick or paste a decklist above, then go to Run Analysis to generate a "
        "cut/protect/replacement report. Open it from Report Viewer.\n\n"
        "• Commander's Call — build a deck FROM your card collection. Open Settings → Collection Source "
        "first to point at your collection folder, then go to The Commander's Call to scan for possible commanders.\n\n"
        "Both flows need Scryfall data. If you haven't downloaded it yet, Settings has a one-click Data Setup button.",
        paper=True,
    ))
    shell_layout.addWidget(next_steps_card)

    content.layout().addWidget(shell)
    layout.addWidget(scroll, stretch=1)

    _update_deck_selection_preview(window)
    return page
