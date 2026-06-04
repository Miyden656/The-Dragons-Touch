"""Deck Coach Workbench — Phase 4 UI page.

A readable, persona-voiced view of the engine's own reasoning: why each card is a
cut candidate, what's protected, where to build up — narrated through the chosen
lens as an OPINION you can disagree with. Plus a steering wheel: pick cards to
keep / cut / add and re-run the coach view with those picks honored.

This page only RENDERS the headless ai/coach data layer (build_coach_view /
CoachPicks). It changes no scoring and runs the AI prompt pipeline not at all —
the coach view is deterministic narration of engine output, so there is no Ollama
call here and nothing to spend. The heavy work (Scryfall load + analysis) runs on
a background thread using the same QThread+moveToThread pattern as the Commander
Guide panel, so the UI never freezes.

build_deck_coach_page() is bulletproof: any construction error returns a small
label instead of breaking the workstation stack.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

try:
    from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot
    from PySide6.QtWidgets import (
        QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget,
    )
    from ui.widgets import ReportCard
    from ui.pages.commander_ai_panel import (
        PERSONA_DISPLAY, _guide_preference, _philosophy_key,
    )
except ImportError:  # running from inside ui/
    from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot
    from PySide6.QtWidgets import (
        QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget,
    )
    from widgets import ReportCard
    from pages.commander_ai_panel import (
        PERSONA_DISPLAY, _guide_preference, _philosophy_key,
    )


_PERSONA_BY_DISPLAY = {disp: key for disp, key in PERSONA_DISPLAY}
_NO_DECK = "No deck file selected"

# (display label, direction token)
_DIRECTION_DISPLAY = [
    ("Cut down (trim toward 100)", "cut_down"),
    ("Build up (add toward 100)", "build_up"),
]
_DIRECTION_BY_DISPLAY = {disp: tok for disp, tok in _DIRECTION_DISPLAY}


# --- background work ------------------------------------------------------

@dataclass
class _CoachResult:
    ok: bool
    text: str = ""
    guide_name: str = ""
    commander: str = ""
    persona_key: str = ""
    direction: str = "cut_down"
    error: str = ""
    view: object = None  # the CoachView, kept for instant direction re-framing


@dataclass
class _Picks:
    keep: list = field(default_factory=list)
    cut: list = field(default_factory=list)
    add: list = field(default_factory=list)
    note: str = ""

    def is_empty(self) -> bool:
        return not (self.keep or self.cut or self.add or self.note.strip())


def _split_csv(text: str) -> list:
    return [part.strip() for part in (text or "").split(",") if part.strip()]


def _build_coach(window, persona_key: str, direction: str, picks: _Picks) -> _CoachResult:
    """Full pipeline (worker thread): analysis -> coach view. No Ollama, no cost."""
    import main
    from config import RuntimeConfig
    from parsing.deck_parser import parse_deck_file

    from ai.coach.coach_view import build_coach_view
    from ai.coach.coach_picks import CoachPicks, picks_to_runtime_overlay

    deck_path = getattr(window.state, "selected_deck_path", "") or ""
    if not deck_path or deck_path == _NO_DECK:
        return _CoachResult(ok=False, error="Select a deck first (Deck Selection), then build the coach view.")
    if not Path(deck_path).exists():
        return _CoachResult(ok=False, error=f"Deck file not found: {deck_path}")

    lookup = getattr(window, "_commander_ai_scryfall_lookup", None)
    if not lookup:
        _cards, lookup, err = main.load_scryfall_or_none()
        if err or not lookup:
            return _CoachResult(ok=False, error="Card data isn't loaded. Use Settings -> Data Setup to download Scryfall data.")
        window._commander_ai_scryfall_lookup = lookup

    parsed = parse_deck_file(Path(deck_path), scryfall_lookup=lookup)

    # The user's picks steer the REFINED run via the existing intent channels:
    # keeps become pilot-protected, cut/add ride along as declared intent. Engine
    # truth + legality still win (picks steer, never override).
    coach_picks = CoachPicks(keep=picks.keep, cut=picks.cut, add=picks.add, note=picks.note)
    overlay = picks_to_runtime_overlay(coach_picks)

    resolved_persona = persona_key or _philosophy_key(window)
    presentation = _guide_preference(window)
    coach_presentation = "no_named_guide" if presentation == "none" else presentation

    runtime = RuntimeConfig(
        output_mode="normal", review_direction=direction, build_up_config={},
        cut_depth_config={}, prompt_interaction_mode="guided",
        philosophy_key=resolved_persona,
        guide_preference=presentation,
        intended_bracket=getattr(window.state, "bracket", "") or "Bracket 3",
        collection_mode="none",
        pet_cards=overlay.get("protected_cards", []),
        declared_constraints=overlay.get("declared_constraints", []),
    )
    analysis = main.build_analysis_context(parsed, runtime, lookup, None)

    view = build_coach_view(
        analysis,
        philosophy_key=resolved_persona,
        guide_presentation=coach_presentation,
        direction=direction,
    )
    return _CoachResult(
        ok=True,
        text=view.to_text(),
        guide_name=view.persona.get("guide_name", ""),
        commander=view.deck_plan.get("commander", ""),
        persona_key=view.persona.get("key", resolved_persona),
        direction=view.direction,
        view=view,
    )


class _CoachWorker(QObject):
    finished = Signal(object)  # _CoachResult
    failed = Signal(str)

    def __init__(self, window, persona_key, direction, picks):
        super().__init__()
        self._window = window
        self._persona_key = persona_key
        self._direction = direction
        self._picks = picks

    def run(self):
        try:
            self.finished.emit(_build_coach(self._window, self._persona_key, self._direction, self._picks))
        except Exception as exc:  # noqa: BLE001 - surfaced to the page, never crashes the app.
            self.failed.emit(str(exc))


class _CoachBridge(QObject):
    def __init__(self, output, status, buttons, export_button, store):
        super().__init__()
        self.output = output
        self.status = status
        self.buttons = list(buttons)
        self.export_button = export_button
        self.store = store

    def _reenable(self):
        for b in self.buttons:
            if b is not None:
                b.setEnabled(True)
        self.store["running"] = False

    @Slot(object)
    def on_finished(self, result):
        self._reenable()
        if result.ok:
            self.output.setPlainText(result.text)
            self.store["last_result"] = result
            self.export_button.setEnabled(True)
            who = result.guide_name or "the guide"
            self.status.setText(f"Coach view ready — {who}'s take on {result.commander or 'your deck'}.")
        else:
            self.output.setPlainText(result.error or "No coach view.")
            self.status.setText("Could not build the coach view — see the message above.")

    @Slot(str)
    def on_failed(self, message):
        self._reenable()
        self.output.setPlainText(f"Something went wrong: {message}")
        self.status.setText("Error.")

    @Slot()
    def release_refs(self):
        # Clear the thread/worker/bridge refs only after the thread has finished, so
        # the QThread is never garbage-collected while still running (that crashes Qt).
        self.store["_thread"] = None
        self.store["_worker"] = None
        self.store["_bridge"] = None


def _run_build(window, persona_combo, direction_combo, picks_inputs, output, status, buttons, export_button, store):
    # Re-entrancy guard: if a build is already in flight, ignore the click. Without
    # this, a second click would overwrite the live thread refs and Qt would crash
    # ("QThread: Destroyed while thread is still running").
    if store.get("running"):
        return
    persona = _PERSONA_BY_DISPLAY.get(persona_combo.currentText(), "") if persona_combo is not None else ""
    direction = _DIRECTION_BY_DISPLAY.get(direction_combo.currentText(), "cut_down")
    picks = _Picks(
        keep=_split_csv(picks_inputs["keep"].text()),
        cut=_split_csv(picks_inputs["cut"].text()),
        add=_split_csv(picks_inputs["add"].text()),
        note=picks_inputs["note"].text().strip(),
    )

    store["running"] = True
    for b in buttons:
        if b is not None:
            b.setEnabled(False)
    export_button.setEnabled(False)
    steer = "" if picks.is_empty() else "  (steering with your picks)"
    output.setPlainText(f"Building the coach view...{steer}  (the first build loads card data and can take a few seconds)")
    status.setText("Reading your deck through the chosen lens...")

    thread = QThread()
    worker = _CoachWorker(window, persona, direction, picks)
    bridge = _CoachBridge(output, status, buttons, export_button, store)
    worker.moveToThread(thread)

    worker.finished.connect(bridge.on_finished)
    worker.failed.connect(bridge.on_failed)
    worker.finished.connect(thread.quit)
    worker.failed.connect(thread.quit)
    thread.started.connect(worker.run)
    thread.finished.connect(worker.deleteLater)
    thread.finished.connect(bridge.release_refs)
    thread.finished.connect(thread.deleteLater)

    # Hold the live objects on the (stable) store dict so they survive until the
    # thread finishes; release_refs clears them only after thread.finished.
    store["_thread"] = thread
    store["_worker"] = worker
    store["_bridge"] = bridge
    thread.start()


def _on_direction_changed(direction_combo, output, status, store):
    """Direction is a free re-frame: the cut/keep/add data is direction-independent,
    so flip the framing instantly from the stored view without rebuilding."""
    result = store.get("last_result")
    if not result or getattr(result, "view", None) is None:
        return  # nothing built yet; the next Build click will use the chosen direction
    direction = _DIRECTION_BY_DISPLAY.get(direction_combo.currentText(), "cut_down")
    try:
        reframed = result.view.reframed(direction)
        output.setPlainText(reframed.to_text())
        result.view = reframed
        result.text = reframed.to_text()
        result.direction = direction
        status.setText(f"Flipped to {'build-up' if direction == 'build_up' else 'cut-down'} view.")
    except Exception:  # noqa: BLE001
        pass


def _export(window, result, status):
    if result is None:
        status.setText("Build the coach view first, then export.")
        return
    try:
        out_dir = Path(getattr(window.state, "report_output_folder", "Outputs") or "Outputs")
        out_dir.mkdir(parents=True, exist_ok=True)
        safe_cmd = "".join(c for c in (result.commander or "deck") if c.isalnum() or c in " _-").strip().replace(" ", "_")
        name = f"{safe_cmd}_coach_{result.persona_key}_{result.direction}.md"
        path = out_dir / name
        path.write_text(result.text, encoding="utf-8")
        status.setText(f"Exported the coach view -> {path}")
    except Exception as exc:  # noqa: BLE001
        status.setText(f"Could not export: {exc}")


# --- page construction ----------------------------------------------------

def build_deck_coach_page(window) -> QWidget:
    """The Deck Coach Workbench page. Bulletproof: returns a fallback label on any
    construction error so the workstation stack never breaks."""
    try:
        return _build_page(window)
    except Exception as exc:  # noqa: BLE001
        label = QLabel(f"Deck Coach Workbench unavailable: {exc}")
        label.setWordWrap(True)
        return label


def _build_page(window) -> QWidget:
    card = ReportCard("Deck Coach Workbench", window.theme, badges=[("Coach", "primary"), ("Beta", "manual")])
    card.body.addWidget(window.default_note(
        "A readable, persona-voiced take on your deck — why each card is a cut candidate, what's "
        "protected, and where to build up — narrated through your chosen lens as an OPINION you can "
        "disagree with. Pick a deck in Deck Selection first, then Build the coach view. Runs entirely "
        "on your machine; nothing here calls the AI model or spends anything."
    ))

    store: dict = {}

    # Shows which deck the coach view will read. Refreshed on navigation by the
    # workstation's go_to hook (refresh_deck_coach_page) since this page is built
    # once at startup, before any deck is selected.
    deck_label = QLabel(_deck_label_text(window))
    deck_label.setObjectName("helperText")
    deck_label.setWordWrap(True)
    card.body.addWidget(deck_label)
    window._deck_coach_deck_label = deck_label

    # --- controls: persona + direction + build ---
    controls = QHBoxLayout()
    controls.setSpacing(10)

    persona_label = QLabel("Lens")
    persona_label.setObjectName("helperText")
    persona_combo = QComboBox()
    for disp, _key in PERSONA_DISPLAY:
        persona_combo.addItem(disp)
    persona_combo.setMinimumWidth(220)
    persona_combo.setToolTip("The deck-building philosophy whose voice + priorities frame the coach view. Defaults to your selected philosophy.")
    if hasattr(window, "configure_combo_popup"):
        window.configure_combo_popup(persona_combo)
    _preselect_persona(window, persona_combo)
    controls.addWidget(persona_label)
    controls.addWidget(persona_combo)

    direction_label = QLabel("Direction")
    direction_label.setObjectName("helperText")
    direction_combo = QComboBox()
    for disp, _tok in _DIRECTION_DISPLAY:
        direction_combo.addItem(disp)
    direction_combo.setMinimumWidth(200)
    direction_combo.setToolTip("Cut-down leads with what to trim; build-up leads with what to add. Flipping is instant once a view is built.")
    if hasattr(window, "configure_combo_popup"):
        window.configure_combo_popup(direction_combo)
    controls.addWidget(direction_label)
    controls.addWidget(direction_combo)

    build_button = QPushButton("Build coach view")
    build_button.setObjectName("primaryButton")
    build_button.setMinimumHeight(38)
    controls.addWidget(build_button)
    controls.addStretch(1)
    card.body.addLayout(controls)

    # --- output ---
    output = window.readonly_text_box("Your deck coach view will appear here. Pick a deck, then Build coach view.", min_height=320, max_height=760)
    card.body.addWidget(output)

    # --- steering wheel: keep / cut / add picks ---
    card.body.addWidget(window.default_note(
        "Steer it: name cards (comma-separated) to keep, cut, or add, then Re-run. Keeps become "
        "protected; cut/add ride along as your stated intent. The engine's truth and legality still win."
    ))
    picks_inputs = {}
    for key, label_text, placeholder in (
        ("keep", "Keep", "cards you want protected, e.g. Nature's Rhythm, Craterhoof Behemoth"),
        ("cut", "Cut", "cards you plan to cut"),
        ("add", "Add", "cards you're considering adding"),
        ("note", "Note", "a steering note, e.g. lean harder into tokens"),
    ):
        row = QHBoxLayout()
        row.setSpacing(8)
        lbl = QLabel(label_text)
        lbl.setObjectName("helperText")
        lbl.setMinimumWidth(48)
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setMinimumHeight(30)
        row.addWidget(lbl)
        row.addWidget(edit, 1)
        card.body.addLayout(row)
        picks_inputs[key] = edit

    # --- actions: re-run with picks + export ---
    button_row = QHBoxLayout()
    button_row.setSpacing(8)
    rerun_button = QPushButton("Re-run with my picks")
    rerun_button.setObjectName("primaryButton")
    rerun_button.setMinimumHeight(36)
    export_button = QPushButton("Export coach view")
    export_button.setObjectName("utilityButton")
    export_button.setMinimumHeight(36)
    export_button.setEnabled(False)
    export_button.setToolTip("Save the current coach view as a readable .md file in your output folder.")
    button_row.addWidget(rerun_button)
    button_row.addWidget(export_button)
    button_row.addStretch(1)
    card.body.addLayout(button_row)

    status = QLabel("")
    status.setObjectName("mutedText")
    status.setWordWrap(True)
    card.body.addWidget(status)

    # --- wiring ---
    def _build():
        _run_build(window, persona_combo, direction_combo, picks_inputs, output, status,
                   [build_button, rerun_button], export_button, store)

    build_button.clicked.connect(_build)
    rerun_button.clicked.connect(_build)
    direction_combo.currentTextChanged.connect(
        lambda _t: _on_direction_changed(direction_combo, output, status, store)
    )
    export_button.clicked.connect(lambda: _export(window, store.get("last_result"), status))

    return card


def _preselect_persona(window, persona_combo) -> None:
    """Default the lens dropdown to the app's staged philosophy if it's a real key."""
    try:
        staged = _philosophy_key(window)
        for i, (_disp, key) in enumerate(PERSONA_DISPLAY):
            if key == staged:
                persona_combo.setCurrentIndex(i)
                return
    except Exception:  # noqa: BLE001
        pass


def _deck_label_text(window) -> str:
    """One-line 'which deck' label for the page header."""
    path = str(getattr(getattr(window, "state", None), "selected_deck_path", "") or "")
    if not path or path == _NO_DECK:
        return "No deck selected yet — pick one in Deck Selection, then click Build coach view."
    return f"Coaching the deck: {Path(path).name}"


def refresh_deck_coach_deck_label(window) -> None:
    """Update the page's deck label to the currently selected deck. Called by the
    workstation's go_to hook each time the Deck Coach page is shown (the page is
    built once at startup, so the label would otherwise be stale). Never raises."""
    try:
        label = getattr(window, "_deck_coach_deck_label", None)
        if label is not None:
            label.setText(_deck_label_text(window))
    except Exception:  # noqa: BLE001
        pass
