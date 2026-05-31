"""Dev-mode "Training Review" page — generate + curate training candidates.

Two cards, both maintainer-only (dev mode):

  1. Generate — point at a folder of decklists, pick a persona and how many decks,
     and produce candidates with the local model on a background thread (the UI
     stays responsive). New candidates append to the corpus; the review card
     reloads automatically when it finishes. This lets a collaborator who cloned
     the repo build candidates from THEIR OWN decks entirely in the UI.
  2. Review — one unapproved candidate at a time: Keep / Reject / Skip, then Save.

Saves to Outputs/commander_ai_training_data.jsonl (a .bak is written first).
All corpus + generation logic lives in ai/training/* (pure + tested); this file
is only the screen. build_training_review_page() is bulletproof — any
construction error returns a small label instead of breaking the app.
"""

from __future__ import annotations

from pathlib import Path

try:
    from PySide6.QtCore import QObject, QThread, Signal, Slot
    from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget
    from ui.widgets import ReportCard
    from ui.pages.commander_ai_panel import PERSONA_DISPLAY
except ImportError:  # running from inside ui/
    from PySide6.QtCore import QObject, QThread, Signal, Slot
    from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget
    from widgets import ReportCard
    from pages.commander_ai_panel import PERSONA_DISPLAY

_PERSONA_BY_DISPLAY = {disp: key for disp, key in PERSONA_DISPLAY}
_DECK_COUNT_CHOICES = ["3", "5", "10", "25", "50", "All"]


def _load():
    """Load the corpus + indices of unapproved candidates. Never raises."""
    from ai.training.corpus import default_corpus_path, load_corpus

    path = default_corpus_path()
    loaded = load_corpus(path)
    review = [i for i, r in enumerate(loaded.records)
              if isinstance(r, dict) and r.get("approved") is not True]
    return path, loaded, review


# --- background generation ------------------------------------------------

class _GenWorker(QObject):
    finished = Signal(int)      # total kept
    failed = Signal(str)
    progress = Signal(str)

    def __init__(self, window, deck_dir, persona, limit):
        super().__init__()
        self._window = window
        self._deck_dir = deck_dir
        self._persona = persona
        self._limit = limit

    def run(self):
        try:
            import main
            from ai.commander_ai_config import from_settings
            from ai.commander_ai_service import CommanderAIService
            from ai.training.corpus import default_corpus_path
            from ai.training.generate import DEFAULT_PROMPT_PLAN, append_candidates, generate_for_deck

            lookup = getattr(self._window, "_commander_ai_scryfall_lookup", None)
            if not lookup:
                _cards, lookup, err = main.load_scryfall_or_none()
                if err or not lookup:
                    self.failed.emit("Card data isn't loaded (Settings -> Data Setup).")
                    return
                self._window._commander_ai_scryfall_lookup = lookup

            config = from_settings(self._window.app_settings)
            service = CommanderAIService(config, scryfall_lookup=lookup)
            avail = service.is_available()
            if not avail.ok:
                self.failed.emit(f"Local model not reachable: {avail.message}")
                return

            decks = sorted(Path(self._deck_dir).glob("*.txt"))
            if self._limit > 0:
                decks = decks[: self._limit]
            if not decks:
                self.failed.emit(f"No .txt decklists found in {self._deck_dir}")
                return

            out_path = default_corpus_path()
            total = 0
            for i, deck in enumerate(decks, start=1):
                try:
                    kept, stats = generate_for_deck(
                        deck, service=service, scryfall_lookup=lookup,
                        persona=self._persona, prompt_plan=DEFAULT_PROMPT_PLAN,
                    )
                except Exception as exc:  # noqa: BLE001 - one bad deck can't abort the batch
                    self.progress.emit(f"[{i}/{len(decks)}] {deck.name} — error: {exc}")
                    continue
                if kept:
                    append_candidates(out_path, kept)
                total += stats["kept"]
                self.progress.emit(f"[{i}/{len(decks)}] {deck.name} — kept {stats['kept']}, "
                                   f"dropped {stats['dropped']}  (total {total})")
            self.finished.emit(total)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"Generation failed: {exc}")


class _GenBridge(QObject):
    def __init__(self, status, button, on_done):
        super().__init__()
        self.status = status
        self.button = button
        self.on_done = on_done

    @Slot(str)
    def on_progress(self, msg):
        self.status.setText(msg)

    @Slot(int)
    def on_finished(self, total):
        self.button.setEnabled(True)
        self.status.setText(f"Done — {total} new candidate(s) added. Review them below.")
        try:
            self.on_done()
        except Exception:  # noqa: BLE001
            pass

    @Slot(str)
    def on_failed(self, message):
        self.button.setEnabled(True)
        self.status.setText(message)

    @Slot()
    def release(self):
        if self.button is not None:
            self.button._gen_thread = None
            self.button._gen_worker = None
            self.button._gen_bridge = None


# --- page -----------------------------------------------------------------

def build_training_review_page(window) -> QWidget:
    page, layout = window.page_container(
        "Training Review (Dev)",
        "Generate AI training candidates from your decklists and curate them into "
        "approved training data. Maintainer tool — hidden from normal users. "
        "Saves to the corpus file the CLI also uses (a .bak backup is written first).",
    )
    scroll, content = window.scroll_content()
    try:
        content.addWidget(_build_panel(window))
    except Exception as exc:  # noqa: BLE001 - the page must always render.
        label = QLabel(f"Training Review unavailable: {exc}")
        label.setWordWrap(True)
        content.addWidget(label)
    content.addStretch(1)
    layout.addWidget(scroll, stretch=1)
    return page


def _build_panel(window) -> QWidget:
    container = QWidget()
    from PySide6.QtWidgets import QVBoxLayout
    box = QVBoxLayout(container)
    box.setContentsMargins(0, 0, 0, 0)
    box.setSpacing(14)

    review_card, reload_fn = _build_review_card(window)
    box.addWidget(_build_generate_card(window, reload_fn))
    box.addWidget(review_card)
    return container


def _build_generate_card(window, on_done) -> QWidget:
    card = ReportCard("Generate candidates", window.theme, badges=[("Dev", "manual"), ("Local AI", "primary")])
    card.body.addWidget(window.default_note(
        "Generate candidates from a folder of .txt decklists using the local model. "
        "Pick a persona and how many decks. Runs in the background; new candidates "
        "appear in Review below when it finishes. Put your own decks in the folder to "
        "train on them."
    ))

    row = QHBoxLayout()
    row.setSpacing(10)

    folder_label = QLabel("Decks folder"); folder_label.setObjectName("helperText")
    folder_edit = QLineEdit("Decklists"); folder_edit.setMinimumWidth(160)
    row.addWidget(folder_label); row.addWidget(folder_edit)

    persona_label = QLabel("Persona"); persona_label.setObjectName("helperText")
    persona_combo = QComboBox()
    for disp, _key in PERSONA_DISPLAY:
        persona_combo.addItem(disp)
    persona_combo.setMinimumWidth(200)
    if hasattr(window, "configure_combo_popup"):
        window.configure_combo_popup(persona_combo)
    row.addWidget(persona_label); row.addWidget(persona_combo)

    count_label = QLabel("Decks"); count_label.setObjectName("helperText")
    count_combo = QComboBox()
    count_combo.addItems(_DECK_COUNT_CHOICES)
    if hasattr(window, "configure_combo_popup"):
        window.configure_combo_popup(count_combo)
    row.addWidget(count_label); row.addWidget(count_combo)
    row.addStretch(1)
    card.body.addLayout(row)

    gen_btn = QPushButton("Generate candidates")
    gen_btn.setObjectName("primaryButton")
    gen_btn.setMinimumHeight(38)
    card.body.addWidget(gen_btn)

    status = QLabel("")
    status.setObjectName("mutedText")
    status.setWordWrap(True)
    card.body.addWidget(status)

    def _start():
        persona = _PERSONA_BY_DISPLAY.get(persona_combo.currentText(), "balanced_unknown")
        choice = count_combo.currentText()
        limit = 0 if choice == "All" else int(choice)
        deck_dir = folder_edit.text().strip() or "Decklists"
        if not Path(deck_dir).exists():
            status.setText(f"Folder not found: {deck_dir}")
            return
        gen_btn.setEnabled(False)
        status.setText("Starting... (the first deck loads card data and can take a few seconds)")

        thread = QThread()
        worker = _GenWorker(window, deck_dir, persona, limit)
        bridge = _GenBridge(status, gen_btn, on_done)
        worker.moveToThread(thread)
        worker.progress.connect(bridge.on_progress)
        worker.finished.connect(bridge.on_finished)
        worker.failed.connect(bridge.on_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.started.connect(worker.run)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(bridge.release)
        thread.finished.connect(thread.deleteLater)
        gen_btn._gen_thread = thread
        gen_btn._gen_worker = worker
        gen_btn._gen_bridge = bridge
        thread.start()

    gen_btn.clicked.connect(_start)
    return card


def _build_review_card(window):
    """Returns (card_widget, reload_callable)."""
    card = ReportCard("Review candidates", window.theme, badges=[("Dev", "manual"), ("Curation", "primary")])
    card.body.addWidget(window.default_note(
        "Review unapproved candidates one at a time. Keep = mark approved (goes into training). "
        "Reject = remove from the corpus. Skip = leave for later. Save writes your decisions "
        "(a .bak backup is made first). Reload picks up newly generated candidates."
    ))

    path, loaded, review = _load()
    store = {"path": path, "loaded": loaded, "review": review, "pos": 0, "decisions": {}}

    counter = QLabel(""); counter.setObjectName("helperText"); card.body.addWidget(counter)
    meta = QLabel(""); meta.setObjectName("mutedText"); meta.setWordWrap(True); card.body.addWidget(meta)
    question = QLabel(""); question.setObjectName("sectionTitle"); question.setWordWrap(True); card.body.addWidget(question)
    answer = window.readonly_text_box("The candidate answer will appear here.", min_height=240, max_height=520)
    card.body.addWidget(answer)
    status = QLabel(""); status.setObjectName("mutedText"); status.setWordWrap(True)

    def _cur_idx():
        rv, pos = store["review"], store["pos"]
        return rv[pos] if 0 <= pos < len(rv) else -1

    def _render():
        rv = store["review"]
        if not rv:
            counter.setText("No candidates to review.")
            meta.setText("Generate some above, then they'll appear here.")
            question.setText(""); answer.setPlainText("Nothing to review right now.")
            return
        store["pos"] = max(0, min(store["pos"], len(rv) - 1))
        rec = store["loaded"].records[_cur_idx()]
        kept = sum(1 for v in store["decisions"].values() if v == "keep")
        rejected = sum(1 for v in store["decisions"].values() if v == "reject")
        counter.setText(f"Candidate {store['pos'] + 1} of {len(rv)}   (decided: {kept} keep, {rejected} reject)")
        meta.setText(f"Commander: {rec.get('commander', '?')}    Mode: {rec.get('mode', '?')}    "
                     f"Persona: {rec.get('persona', '?')}    Source: {rec.get('source', 'panel')}    "
                     f"Decision: {store['decisions'].get(_cur_idx(), '(none)')}")
        question.setText("Q:  " + str(rec.get("question", "")))
        answer.setPlainText(str(rec.get("answer", "")))

    def _decide(action):
        if not store["review"]:
            return
        store["decisions"][_cur_idx()] = action
        store["pos"] = min(store["pos"] + 1, len(store["review"]) - 1)
        _render()

    def _nav(delta):
        store["pos"] += delta
        _render()

    def _reload():
        p, loaded2, rv2 = _load()
        store.update({"path": p, "loaded": loaded2, "review": rv2, "pos": 0, "decisions": {}})
        _render()

    def _save():
        from ai.training.corpus import apply_review_decisions, write_corpus
        if not store["decisions"]:
            status.setText("No decisions yet — Keep or Reject some candidates first.")
            return
        try:
            records = store["loaded"].records
            backup = store["path"].with_suffix(store["path"].suffix + ".bak")
            write_corpus(backup, records)
            updated, summary = apply_review_decisions(records, store["decisions"])
            write_corpus(store["path"], updated)
            status.setText(f"Saved: kept {summary['kept']}, rejected {summary['rejected']}. "
                           f"Backup: {backup.name}.")
            _reload()
        except Exception as exc:  # noqa: BLE001
            status.setText(f"Could not save: {exc}")

    nav_row = QHBoxLayout(); nav_row.setSpacing(8)
    prev_btn = QPushButton("← Prev"); prev_btn.setObjectName("utilityButton"); prev_btn.clicked.connect(lambda: _nav(-1))
    next_btn = QPushButton("Next →"); next_btn.setObjectName("utilityButton"); next_btn.clicked.connect(lambda: _nav(1))
    nav_row.addWidget(prev_btn); nav_row.addWidget(next_btn); nav_row.addStretch(1)
    card.body.addLayout(nav_row)

    decide_row = QHBoxLayout(); decide_row.setSpacing(8)
    keep_btn = QPushButton("✓ Keep"); keep_btn.setObjectName("primaryButton"); keep_btn.setMinimumHeight(38); keep_btn.clicked.connect(lambda: _decide("keep"))
    reject_btn = QPushButton("✗ Reject"); reject_btn.setObjectName("utilityButton"); reject_btn.setMinimumHeight(38); reject_btn.clicked.connect(lambda: _decide("reject"))
    skip_btn = QPushButton("Skip"); skip_btn.setObjectName("utilityButton"); skip_btn.setMinimumHeight(38); skip_btn.clicked.connect(lambda: _nav(1))
    decide_row.addWidget(keep_btn); decide_row.addWidget(reject_btn); decide_row.addWidget(skip_btn); decide_row.addStretch(1)
    card.body.addLayout(decide_row)

    action_row = QHBoxLayout(); action_row.setSpacing(8)
    save_btn = QPushButton("Save decisions"); save_btn.setObjectName("primaryButton"); save_btn.setMinimumHeight(38); save_btn.clicked.connect(_save)
    reload_btn = QPushButton("Reload"); reload_btn.setObjectName("utilityButton"); reload_btn.setMinimumHeight(38); reload_btn.clicked.connect(_reload)
    action_row.addWidget(save_btn); action_row.addWidget(reload_btn); action_row.addStretch(1)
    card.body.addLayout(action_row)

    card.body.addWidget(status)
    _render()
    return card, _reload
