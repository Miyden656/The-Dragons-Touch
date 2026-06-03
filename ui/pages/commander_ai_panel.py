"""Phase 5b: the in-app "Ask the Commander Guide" panel for the Report Viewer.

Self-contained on purpose: report_viewer_page.py only adds this one widget, so the
big page file barely changes. All the heavy work (loading Scryfall, building the
analysis context, calling the model, safety-checking) runs on a BACKGROUND THREAD
using the same QThread+moveToThread pattern the Settings page already uses, so the
UI never freezes — the first ask loads the 539 MB card data (cached afterward),
which would otherwise lock the window for seconds.

build_commander_ai_panel() is bulletproof: if anything fails to construct, it
returns a small label instead of breaking the Report Viewer page.

The "Save as training example" button appends approved (question, answer, grounded
context) records to Outputs/commander_ai_training_data.jsonl — the seed corpus for
the eventual custom fine-tuned Commander model.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

try:
    from PySide6.QtCore import QObject, QThread, Signal, Slot
    from PySide6.QtWidgets import (
        QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget,
    )
    from ui.widgets import ReportCard
except ImportError:  # running from inside ui/
    from PySide6.QtCore import QObject, QThread, Signal, Slot
    from PySide6.QtWidgets import (
        QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget,
    )
    from widgets import ReportCard


# (display label, mode token) — order shown in the dropdown.
MODE_DISPLAY = [
    ("Commander Review", "commander_review"),
    ("Cut Review", "cut_review"),
    ("Replacement Ideas", "replacement"),
    ("Strategy Tutor", "strategy_tutor"),
    ("Build From Collection", "build_from_collection"),
    ("Persona Coaching", "persona_coaching"),
]
_MODE_BY_DISPLAY = {disp: tok for disp, tok in MODE_DISPLAY}

_NO_DECK = "No deck file selected"


def _persona_display() -> list[tuple[str, str]]:
    """(display label, philosophy key) for the persona dropdown, built from the
    engine's real 18+ profiles so the panel and engine never drift. Ordered:
    Balanced first, then each archetype followed by its sub-personas (indented).
    Falls back to just Balanced if the engine module can't be imported."""
    try:
        from analysis.deck_building_philosophies import PHILOSOPHY_PROFILES
    except Exception:  # noqa: BLE001
        return [("Balanced / Unknown", "balanced_unknown")]

    profs = PHILOSOPHY_PROFILES
    out: list[tuple[str, str]] = []
    if "balanced_unknown" in profs:
        out.append(("Balanced / Unknown", "balanced_unknown"))
    archetypes = [
        k for k, v in profs.items()
        if getattr(v, "parent", None) is None and k != "balanced_unknown"
    ]
    for arch in archetypes:
        out.append((str(getattr(profs[arch], "label", arch)), arch))
        for k, v in profs.items():
            if getattr(v, "parent", None) == arch:
                out.append(("   " + str(getattr(v, "label", k)), k))
    return out


PERSONA_DISPLAY = _persona_display()
_PERSONA_BY_DISPLAY = {disp: key for disp, key in PERSONA_DISPLAY}


# --- background work ------------------------------------------------------

@dataclass
class _AskResult:
    ok: bool
    answer_text: str = ""       # safety-annotated text to display
    raw_answer: str = ""        # model's original text (for training capture)
    ctx_json: str = ""
    commander: str = ""
    persona: str = ""
    guide_style: str = ""
    mode: str = ""
    question: str = ""
    flag_count: int = 0
    error: str = ""


def _philosophy_key(window) -> str:
    """Best-effort: use the staged philosophy if it looks like a key; else balanced."""
    state = getattr(window, "state", None)
    for attr in ("philosophy_key", "philosophy_subtype", "selected_philosophy"):
        val = getattr(state, attr, None)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return "balanced_unknown"


def _select_default_persona(window, persona_combo) -> None:
    """Preselect the dropdown to the app's staged philosophy if it's a real key,
    else leave it on the first entry (Balanced). Never raises."""
    try:
        staged = _philosophy_key(window)
        for i, (_disp, key) in enumerate(PERSONA_DISPLAY):
            if key == staged:
                persona_combo.setCurrentIndex(i)
                return
    except Exception:  # noqa: BLE001
        pass


def _do_ask(window, question: str, mode: str, persona: str = "") -> _AskResult:
    """Full pipeline (runs on the worker thread): context -> service -> response."""
    from ai.commander_ai_config import from_settings
    from ai.commander_ai_service import CommanderAIService
    from ai.schemas.ai_context import CommanderAIRequest
    import main
    from config import RuntimeConfig
    from parsing.deck_parser import parse_deck_file

    config = from_settings(window.app_settings)
    if not config.enabled:
        return _AskResult(ok=False, error="Local Commander AI is off. Turn it on in Settings -> Local Commander AI.")

    deck_path = getattr(window.state, "selected_deck_path", "") or ""
    if not deck_path or deck_path == _NO_DECK:
        return _AskResult(ok=False, error="Select a deck first (Deck Selection), then ask the Guide.")
    if not Path(deck_path).exists():
        return _AskResult(ok=False, error=f"Deck file not found: {deck_path}")

    # Cache the (large) Scryfall lookup on the window after the first load.
    lookup = getattr(window, "_commander_ai_scryfall_lookup", None)
    if not lookup:
        _cards, lookup, err = main.load_scryfall_or_none()
        if err or not lookup:
            return _AskResult(ok=False, error="Card data isn't loaded. Use Settings -> Data Setup to download Scryfall data.")
        window._commander_ai_scryfall_lookup = lookup

    parsed = parse_deck_file(Path(deck_path), scryfall_lookup=lookup)
    runtime = RuntimeConfig(
        output_mode="normal", review_direction="both", build_up_config={},
        cut_depth_config={}, prompt_interaction_mode="guided",
        philosophy_key=(persona.strip() or _philosophy_key(window)), guide_preference="either",
        intended_bracket=getattr(window.state, "bracket", "") or "Bracket 3",
        collection_mode="none",
    )
    analysis = main.build_analysis_context(parsed, runtime, lookup, None)

    service = CommanderAIService(config, scryfall_lookup=lookup)
    request = CommanderAIRequest(user_text=question, mode=mode)
    ctx, _messages = service.build(request, analysis)  # for the grounded training record
    response = service.answer(request, analysis)

    if not response.ok:
        return _AskResult(ok=False, error=response.error or "The local model did not return an answer.",
                          commander=ctx.commander.get("commander", ""), mode=mode, question=question)
    return _AskResult(
        ok=True,
        answer_text=response.text,
        raw_answer=response.raw_text,
        ctx_json=ctx.to_json(),
        commander=ctx.commander.get("commander", ""),
        persona=ctx.persona.get("key", ""),
        guide_style=ctx.guide_style,
        mode=mode,
        question=question,
        flag_count=len(response.safety_flags),
    )


class _AskWorker(QObject):
    finished = Signal(object)  # _AskResult
    failed = Signal(str)

    def __init__(self, window, question, mode, persona=""):
        super().__init__()
        self._window = window
        self._question = question
        self._mode = mode
        self._persona = persona

    def run(self):
        try:
            self.finished.emit(_do_ask(self._window, self._question, self._mode, self._persona))
        except Exception as exc:  # noqa: BLE001 - surfaced to the panel, never crashes the app.
            self.failed.emit(str(exc))


class _AskBridge(QObject):
    """Handles worker completion on the UI thread."""

    def __init__(self, output, status, ask_button, save_button, store):
        super().__init__()
        self.output = output
        self.status = status
        self.ask_button = ask_button
        self.save_button = save_button
        self.store = store

    @Slot(object)
    def on_finished(self, result):
        self.ask_button.setEnabled(True)
        if result.ok:
            self.output.setPlainText(result.answer_text)
            self.store["last_result"] = result
            self.save_button.setEnabled(True)
            note = f"  •  {result.flag_count} fact-check note(s)" if result.flag_count else ""
            self.status.setText(f"Answered.{note}")
        else:
            self.output.setPlainText(result.error or "No answer.")
            self.status.setText("Could not answer — see the message above.")

    @Slot(str)
    def on_failed(self, message):
        self.ask_button.setEnabled(True)
        self.output.setPlainText(f"Something went wrong: {message}")
        self.status.setText("Error.")

    @Slot()
    def release_refs(self):
        if self.ask_button is not None:
            self.ask_button._ai_ask_thread = None
            self.ask_button._ai_ask_worker = None
            self.ask_button._ai_ask_bridge = None


def _run_ask(window, question_edit, mode_combo, persona_combo, output, status, ask_button, save_button, store):
    question = question_edit.text().strip()
    if not question:
        status.setText("Type a question first.")
        return
    mode = _MODE_BY_DISPLAY.get(mode_combo.currentText(), "commander_review")
    persona = _PERSONA_BY_DISPLAY.get(persona_combo.currentText(), "") if persona_combo is not None else ""

    ask_button.setEnabled(False)
    save_button.setEnabled(False)
    output.setPlainText("Thinking...  (the first question loads card data and can take a few seconds)")
    status.setText("Contacting the local model...")

    thread = QThread()
    worker = _AskWorker(window, question, mode, persona)
    bridge = _AskBridge(output, status, ask_button, save_button, store)
    worker.moveToThread(thread)

    worker.finished.connect(bridge.on_finished)
    worker.failed.connect(bridge.on_failed)
    worker.finished.connect(thread.quit)
    worker.failed.connect(thread.quit)
    thread.started.connect(worker.run)
    thread.finished.connect(worker.deleteLater)
    thread.finished.connect(bridge.release_refs)
    thread.finished.connect(thread.deleteLater)

    ask_button._ai_ask_thread = thread
    ask_button._ai_ask_worker = worker
    ask_button._ai_ask_bridge = bridge
    thread.start()


def _save_training_example(window, result, status):
    if result is None:
        status.setText("Ask something first, then save the answer.")
        return
    try:
        out_dir = Path(getattr(window.state, "report_output_folder", "Outputs") or "Outputs")
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "commander_ai_training_data.jsonl"
        record = {
            "commander": result.commander,
            "mode": result.mode,
            "persona": result.persona,
            "guide_style": result.guide_style,
            "question": result.question,
            "answer": result.raw_answer,
            "context": result.ctx_json,
            "approved": True,
        }
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        status.setText(f"Saved as a training example -> {path}")
    except Exception as exc:  # noqa: BLE001
        status.setText(f"Could not save training example: {exc}")


# --- panel construction ---------------------------------------------------

def build_commander_ai_panel(window, compact: bool = False) -> QWidget:
    """Reusable "Ask the Commander Guide" widget.

    Hosted in a slide-in drawer (default) or an embedded collapsible section on
    the Report Viewer and Commander's Call pages — the user picks which in
    Settings. Self-contained and async; never raises (returns a fallback label
    on construction error) so a host page can drop it in safely.

    compact=True drops the long descriptive note so the panel fits a narrow
    drawer / small embedded area without wasting vertical space.
    """
    try:
        return _build_panel(window, compact=compact)
    except Exception as exc:  # noqa: BLE001 - hosts must always render.
        label = QLabel(f"Commander AI panel unavailable: {exc}")
        label.setWordWrap(True)
        return label


def _build_panel(window, compact: bool = False) -> QWidget:
    # Compact (embedded/drawer) hosting drops the "Local AI"/"Beta" badges —
    # tester found them noisy/cut-off. Full-page hosting could keep them, but
    # there's no full-page host anymore.
    badges = [] if compact else [("Local AI", "primary"), ("Beta", "manual")]
    card = ReportCard("Ask the Commander Guide", window.theme, badges=badges)
    if not compact:
        card.body.addWidget(window.default_note(
            "Ask the local AI about the selected deck. It uses The Dragon's Touch analysis as the "
            "source of truth and runs entirely on your machine. Enable it in Settings -> Local "
            "Commander AI, then pick a deck in Deck Selection."
        ))

    store: dict = {}  # holds the last successful _AskResult for the Save button

    controls = QHBoxLayout()
    controls.setSpacing(10)
    mode_label = QLabel("Mode")
    mode_label.setObjectName("helperText")
    mode_combo = QComboBox()
    for disp, _tok in MODE_DISPLAY:
        mode_combo.addItem(disp)
    mode_combo.setMinimumWidth(200)
    if hasattr(window, "configure_combo_popup"):
        window.configure_combo_popup(mode_combo)
    controls.addWidget(mode_label)
    controls.addWidget(mode_combo)

    persona_label = QLabel("Persona")
    persona_label.setObjectName("helperText")
    persona_combo = QComboBox()
    for disp, _key in PERSONA_DISPLAY:
        persona_combo.addItem(disp)
    persona_combo.setMinimumWidth(220)
    persona_combo.setToolTip(
        "The deck-building philosophy the Guide coaches from (protect/cut/replace priorities). "
        "Defaults to your selected philosophy, or Balanced."
    )
    if hasattr(window, "configure_combo_popup"):
        window.configure_combo_popup(persona_combo)
    _select_default_persona(window, persona_combo)
    controls.addWidget(persona_label)
    controls.addWidget(persona_combo)
    controls.addStretch(1)
    card.body.addLayout(controls)

    question_edit = QLineEdit()
    question_edit.setPlaceholderText("e.g. What is this deck trying to do? — or — What should I cut, and why?")
    question_edit.setMinimumHeight(34)
    card.body.addWidget(question_edit)

    button_row = QHBoxLayout()
    button_row.setSpacing(8)
    ask_button = QPushButton("Ask the Guide")
    ask_button.setObjectName("primaryButton")
    ask_button.setMinimumHeight(38)
    save_button = QPushButton("Save as training example")
    save_button.setObjectName("utilityButton")
    save_button.setMinimumHeight(38)
    save_button.setEnabled(False)
    save_button.setToolTip("Save this answer to your local training-data file for the future custom model.")
    button_row.addWidget(ask_button)
    button_row.addWidget(save_button)
    button_row.addStretch(1)
    card.body.addLayout(button_row)

    # Use the app's themed read-only text box so the answer is readable in BOTH
    # themes (a raw QTextEdit rendered white-on-cream and was unreadable).
    output = window.readonly_text_box("The Guide's answer will appear here.", min_height=240, max_height=640)
    card.body.addWidget(output)

    status = QLabel("")
    status.setObjectName("mutedText")
    status.setWordWrap(True)
    card.body.addWidget(status)

    def _ask():
        _run_ask(window, question_edit, mode_combo, persona_combo, output, status, ask_button, save_button, store)

    ask_button.clicked.connect(_ask)
    question_edit.returnPressed.connect(_ask)
    save_button.clicked.connect(lambda: _save_training_example(window, store.get("last_result"), status))

    return card
