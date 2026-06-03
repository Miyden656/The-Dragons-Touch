"""Deck Selection page builder for The Dragon's Touch v0.7 alpha hardening.

    # Alpha onboarding note: Archidekt export tip: export or copy your decklist as plain text, save it as a .txt file in Decklists, then select it here.

This module intentionally builds only the Deck Selection page layout. It does
not own deck parsing, file dialogs, staged state mutation, backend handoff, or
backend validation. The active MainWindow remains the workflow owner and passes
itself into this builder so existing Deck Selection methods/signals remain
stable during page extraction.
"""

from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot
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

from deck_import import SUPPORTED_SOURCES, detect_source, import_from_url


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


# ---------------------------------------------------------------------------
# Import Link tab — URL → normalized decklist → existing paste pipeline.
# ---------------------------------------------------------------------------


class _DeckImportWorker(QObject):
    """Background-thread worker that runs deck_import.import_from_url."""

    finished = Signal(object)   # emits DeckImportResult
    failed = Signal(str)

    def __init__(self, url, *, timeout=None):
        super().__init__()
        self._url = url
        self._timeout = timeout

    def run(self):
        try:
            result = import_from_url(self._url, timeout=self._timeout)
            self.finished.emit(result)
        except Exception as exc:  # importer should never raise, but never crash the UI either
            self.failed.emit(str(exc))


class _DeckImportBridge(QObject):
    """Receive worker signals on the UI thread + restore widgets."""

    def __init__(self, window, *, import_btn, status_label, preview_box,
                 use_btn, save_btn, clear_btn, original_btn_text):
        super().__init__()
        self.window = window
        self.import_btn = import_btn
        self.status_label = status_label
        self.preview_box = preview_box
        self.use_btn = use_btn
        self.save_btn = save_btn
        self.clear_btn = clear_btn
        self.original_btn_text = original_btn_text

    def _restore_import_button(self):
        if self.import_btn is not None:
            self.import_btn.setEnabled(True)
            self.import_btn.setText(self.original_btn_text)

    @Slot(object)
    def on_finished(self, result):
        self._restore_import_button()
        if result is None:
            self.status_label.setText("Import failed: no result returned.")
            return

        if not getattr(result, "ok", False):
            error_kind = getattr(result, "error_kind", "") or "error"
            self.status_label.setText(f"Import failed ({error_kind}): {result.message}")
            self.preview_box.setPlainText("")
            self.window._imported_deck_result = None
            self.use_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
            self.clear_btn.setEnabled(True)
            return

        # Success — stash the result on the window so the action buttons can use it.
        self.window._imported_deck_result = result

        commander = result.commander or "(not detected)"
        cards_total = result.card_count()
        summary = (
            f"Imported from {result.source}: \"{result.deck_name}\"  "
            f"Commander: {commander}  Cards: {cards_total}"
        )
        self.status_label.setText(summary)
        self.preview_box.setPlainText(result.decklist_text)
        self.use_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)

    @Slot(str)
    def on_failed(self, message):
        self._restore_import_button()
        self.status_label.setText(f"Import error: {message}")

    @Slot()
    def release_refs(self):
        if self.import_btn is not None:
            self.import_btn._deck_import_thread = None
            self.import_btn._deck_import_worker = None
            self.import_btn._deck_import_bridge = None


def _on_import_url_changed(window, url_input, hint_label):
    text = (url_input.text() or "").strip()
    if not text:
        hint_label.setText(f"Supported: {', '.join(SUPPORTED_SOURCES).title()}")
        return
    adapter = detect_source(text)
    if adapter is None:
        hint_label.setText(
            f"Site not recognized. Supported: {', '.join(SUPPORTED_SOURCES).title()}."
        )
    else:
        hint_label.setText(f"Detected: {adapter.NAME.title()}")


def _start_import(window, url_input, import_btn, status_label, preview_box,
                  use_btn, save_btn, clear_btn):
    url = (url_input.text() or "").strip()
    if not url:
        status_label.setText("Paste a deck URL above first.")
        return

    # Reset prior result + clear preview.
    window._imported_deck_result = None
    use_btn.setEnabled(False)
    save_btn.setEnabled(False)
    preview_box.setPlainText("")

    original_text = import_btn.text()
    import_btn.setEnabled(False)
    import_btn.setText("Importing...")
    status_label.setText(f"Fetching {url} ...")

    thread = QThread()
    worker = _DeckImportWorker(url, timeout=20)
    bridge = _DeckImportBridge(
        window,
        import_btn=import_btn,
        status_label=status_label,
        preview_box=preview_box,
        use_btn=use_btn,
        save_btn=save_btn,
        clear_btn=clear_btn,
        original_btn_text=original_text,
    )
    worker.moveToThread(thread)

    worker.finished.connect(bridge.on_finished)
    worker.failed.connect(bridge.on_failed)
    worker.finished.connect(thread.quit)
    worker.failed.connect(thread.quit)
    thread.started.connect(worker.run)
    thread.finished.connect(worker.deleteLater)
    thread.finished.connect(bridge.release_refs)
    thread.finished.connect(thread.deleteLater)

    # Keep refs alive until the worker thread fully finishes.
    import_btn._deck_import_thread = thread
    import_btn._deck_import_worker = worker
    import_btn._deck_import_bridge = bridge
    thread.start()


def _use_imported_for_run(window):
    result = getattr(window, "_imported_deck_result", None)
    if result is None or not getattr(result, "ok", False):
        window.state.status = "Import a deck URL first."
        window.refresh_context_panel_values()
        return
    path_text = window.create_temp_pasted_decklist(result.decklist_text)
    window.load_deck_file_preview(path_text)
    window.state.status = (
        f"Imported {result.source} deck staged for this run: {result.deck_name}"
    )
    window.refresh_context_panel_values()


def _save_imported_to_folder(window):
    result = getattr(window, "_imported_deck_result", None)
    if result is None or not getattr(result, "ok", False):
        window.state.status = "Import a deck URL first."
        window.refresh_context_panel_values()
        return

    default_name = result.deck_name or f"{result.source} deck"
    name, ok = QInputDialog.getText(
        window,
        "Save Imported Decklist",
        "Deck name:",
        text=default_name,
    )
    if not ok:
        return

    path_text = window.save_pasted_decklist_to_deck_folder(result.decklist_text, name)
    if not path_text:
        return

    window.load_deck_file_preview(path_text)
    window.state.status = f"Saved imported decklist: {Path(path_text).name}"
    window.refresh_context_panel_values()


def _clear_imported(window, url_input, status_label, preview_box, use_btn, save_btn, clear_btn):
    window._imported_deck_result = None
    url_input.clear()
    preview_box.setPlainText("")
    status_label.setText(f"Paste a deck URL above. Supported: {', '.join(SUPPORTED_SOURCES).title()}.")
    use_btn.setEnabled(False)
    save_btn.setEnabled(False)
    clear_btn.setEnabled(False)


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
    # Import Link tab — fetch a deck from Moxfield / Archidekt / MTGGoldfish.
    # ------------------------------------------------------------------
    link_tab = QWidget()
    link_layout = QVBoxLayout(link_tab)
    link_layout.setContentsMargins(14, 14, 14, 14)
    link_layout.setSpacing(12)

    link_card = ReportCard("Import Link", window.theme, badges=[("New", "primary")])
    link_card.body.addWidget(window.default_note(
        "Paste a deck URL from Moxfield, Archidekt, or MTGGoldfish. The deck is fetched "
        "in the background and normalized into the same plain-text format the Paste tab uses, "
        "so the rest of the Dragon's Touch workflow works exactly the same."
    ))
    link_card.body.addWidget(window.make_text(
        "Examples:\n"
        "  https://www.moxfield.com/decks/<id>\n"
        "  https://archidekt.com/decks/<id>/<slug>\n"
        "  https://www.mtggoldfish.com/deck/<id>\n\n"
        "Only public decks can be imported. Private decks return a friendly error.",
        paper=True,
    ))

    link_input = QLineEdit()
    link_input.setPlaceholderText("https://www.moxfield.com/decks/...")
    link_card.body.addWidget(link_input)

    detected_hint = QLabel(f"Supported: {', '.join(SUPPORTED_SOURCES).title()}")
    detected_hint.setObjectName("helperText")
    detected_hint.setWordWrap(True)
    link_card.body.addWidget(detected_hint)
    link_input.textChanged.connect(
        lambda _t, w=window, ui=link_input, hl=detected_hint: _on_import_url_changed(w, ui, hl)
    )

    import_btn = QPushButton("Import Deck")
    import_btn.setObjectName("primaryButton")
    link_card.body.addWidget(import_btn)

    link_status = QLabel(f"Paste a deck URL above. Supported: {', '.join(SUPPORTED_SOURCES).title()}.")
    link_status.setObjectName("defaultNote")
    link_status.setWordWrap(True)
    link_card.body.addWidget(link_status)

    link_preview = QPlainTextEdit()
    link_preview.setReadOnly(True)
    link_preview.setObjectName("reportFilePreview")
    link_preview.setMinimumHeight(220)
    link_preview.setPlaceholderText("The imported decklist will appear here.")
    link_card.body.addWidget(link_preview)

    link_actions = QHBoxLayout()
    use_imported_btn = QPushButton("Use for This Run")
    use_imported_btn.setObjectName("utilityButton")
    use_imported_btn.setEnabled(False)

    save_imported_btn = QPushButton("Save to Decklist Folder")
    save_imported_btn.setObjectName("primaryButton")
    save_imported_btn.setEnabled(False)

    clear_imported_btn = QPushButton("Clear")
    clear_imported_btn.setObjectName("utilityButton")
    clear_imported_btn.setEnabled(False)

    link_actions.addWidget(use_imported_btn)
    link_actions.addWidget(save_imported_btn)
    link_actions.addWidget(clear_imported_btn)
    link_actions.addStretch(1)
    link_card.body.addLayout(link_actions)

    link_card.body.addWidget(window.default_note(
        "Use for This Run stages the deck without saving. Save to Decklist Folder writes it "
        "into your Decklist Folder with the next available number (existing files are never overwritten)."
    ))

    # Initialize the per-window stash so action buttons can find the last result.
    if not hasattr(window, "_imported_deck_result"):
        window._imported_deck_result = None

    import_btn.clicked.connect(
        lambda checked=False: _start_import(
            window, link_input, import_btn, link_status, link_preview,
            use_imported_btn, save_imported_btn, clear_imported_btn,
        )
    )
    use_imported_btn.clicked.connect(lambda checked=False: _use_imported_for_run(window))
    save_imported_btn.clicked.connect(lambda checked=False: _save_imported_to_folder(window))
    clear_imported_btn.clicked.connect(
        lambda checked=False: _clear_imported(
            window, link_input, link_status, link_preview,
            use_imported_btn, save_imported_btn, clear_imported_btn,
        )
    )

    link_layout.addWidget(link_card)
    link_layout.addStretch(1)
    tabs.addTab(link_tab, "Import Link")

    shell_layout.addWidget(tabs)

    # The "Where to Next?" first-run guidance was removed from this page to
    # reduce scrolling (tester feedback). The same guidance already lives in
    # README.md under "Two ways to use it", "Quick start", and
    # "First-time data setup".

    content.layout().addWidget(shell)
    layout.addWidget(scroll, stretch=1)

    # Lightweight refresh hook so load_deck_file_preview can update just the
    # preview + status instead of rebuilding the whole shell (tester: deck-file
    # selection felt slow — the cause was a full rebuild_shell on every load).
    window.refresh_deck_selection_preview = lambda: _update_deck_selection_preview(window)

    _update_deck_selection_preview(window)
    return page
