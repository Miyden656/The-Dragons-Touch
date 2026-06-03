"""Inline pilot-intent intake panels for the Philosophy Lens page.

The five intent-gated guides (Pet Card / Self-Imposed Constraint / Weird Card
Rescuer / Theme Mechanic Inventor / Theme-Vibe) render their intake INLINE beneath
the Specific Philosophy Subtype dropdown (not as modal dialogs). Each panel writes
its value onto the staged AppState live as the user edits; from there
backend_runner.environment_values -> config.get_runtime_config carries it into the
report + the AI guide (already wired).

build_intake_panel(window, persona_or_label) returns a QWidget to drop into the page
(or None for guides that need no intake). The Philosophy Lens page swaps the active
panel when the subtype dropdown changes.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QLabel, QListWidget, QListWidgetItem,
    QPlainTextEdit, QVBoxLayout, QWidget,
)

from analysis.pilot_intent import known_themes

try:
    from ui.widgets import ReportCard
except ImportError:  # direct execution from inside ui/
    from widgets import ReportCard  # type: ignore

# persona key -> intake kind
PERSONA_INTAKE = {
    "pet_card": "pet_cards",
    "constraint_builder": "constraint",
    "weird_card_rescuer": "rescue_cards",
    "theme_mechanic_inventor": "hybrid_themes",
    "theme_vibe": "theme_vibe",
}


def persona_needs_intake(persona_key: str) -> bool:
    return str(persona_key or "").strip() in PERSONA_INTAKE


def resolve_persona_key(value: str) -> str:
    """Resolve a persona key from a key ('pet_card') or a UI subtype LABEL
    ('Milo / Mia — Pet Card'). Em-dash/hyphen tolerant; '' if not an intake guide."""
    v = str(value or "").strip()
    if v in PERSONA_INTAKE:
        return v
    low = v.lower()
    if "pet card" in low:
        return "pet_card"
    if "constraint" in low:
        return "constraint_builder"
    if "weird card" in low:
        return "weird_card_rescuer"
    if "theme mechanic" in low:
        return "theme_mechanic_inventor"
    if "theme / vibe" in low or "theme/vibe" in low or "theme vibe" in low:
        return "theme_vibe"
    return ""


_SECTION_HEADERS = {
    "main", "mainboard", "deck", "sideboard", "maybeboard", "tokens", "token",
    "attractions", "stickers", "reference", "references",
}


def deck_card_names_from_window(window) -> list[str]:
    """Parse the card names from the currently-loaded deck preview, reusing the
    workstation's own line parser. Returns [] when no deck is loaded."""
    state = getattr(window, "state", None)
    text = getattr(state, "deck_preview_text", "") or ""
    parse = getattr(window, "parse_deck_line", None)
    names: list[str] = []
    seen: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", "//")):
            continue
        cleaned = line.rstrip(":").strip()
        # skip section header lines (no digits, few words) the same way the preview does
        if not any(ch.isdigit() for ch in cleaned) and len(cleaned.split()) <= 5:
            continue
        if parse is not None:
            _, name = parse(line)
        else:
            parts = line.lstrip("-•*").strip().split(maxsplit=1)
            name = parts[1].strip() if len(parts) == 2 and parts[0].isdigit() else ""
        if name and name not in seen:
            seen.add(name)
            names.append(name)
    return names


def _state(window):
    return getattr(window, "state", None)


def _text_widget(window, text: str) -> QWidget:
    """A wrapped, paper-style label matching the page; falls back to a plain label."""
    make = getattr(window, "make_text", None)
    if callable(make):
        try:
            return make(text, paper=True)
        except Exception:
            pass
    label = QLabel(text)
    label.setWordWrap(True)
    return label


def _card(window, title: str):
    card = ReportCard(title, getattr(window, "theme", None))
    return card


def _editable_combo(options, current: str = "") -> QComboBox:
    combo = QComboBox()
    combo.setEditable(True)
    combo.setMinimumHeight(40)
    combo.addItem("")
    for opt in options:
        combo.addItem(str(opt))
    if current:
        combo.setCurrentText(str(current))
    return combo


def _card_picker_panel(window, field: str, title: str, blurb: str) -> QWidget:
    card = _card(window, title)
    card.body.addWidget(_text_widget(window, blurb))
    state = _state(window)
    current = list(getattr(state, field, None) or [])

    names = deck_card_names_from_window(window)
    if not names:
        card.body.addWidget(_text_widget(
            window,
            "No deck is loaded yet — choose a deck on the Deck Selection page, then "
            "reopen this guide to pick cards.",
        ))

    listw = QListWidget()
    listw.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
    listw.setMinimumHeight(260)
    ordered = list(names)
    for name in current:
        if name not in ordered:
            ordered.append(name)  # keep an earlier pick even if not in the current deck
    for name in ordered:
        item = QListWidgetItem(name)
        listw.addItem(item)
        if name in current:
            item.setSelected(True)
    card.body.addWidget(listw)

    count = QLabel()
    card.body.addWidget(count)

    def _sync() -> None:
        chosen = [i.text() for i in listw.selectedItems()]
        if state is not None:
            setattr(state, field, chosen)
        count.setText(f"Selected: {len(chosen)}" if chosen else "Select one or more cards.")

    listw.itemSelectionChanged.connect(_sync)
    _sync()
    return card


def _constraint_panel(window) -> QWidget:
    card = _card(window, "Self-Imposed Constraint")
    card.body.addWidget(_text_widget(
        window,
        "What's the rule for this deck? e.g. budget ≤ $5/card, no green creatures, "
        "only cards from sets I opened.",
    ))
    state = _state(window)
    box = QPlainTextEdit()
    box.setMinimumHeight(120)
    box.setPlainText(str(getattr(state, "declared_constraints", "") or ""))

    def _sync() -> None:
        if state is not None:
            setattr(state, "declared_constraints", box.toPlainText().strip())

    box.textChanged.connect(_sync)
    card.body.addWidget(box)
    return card


def _hybrid_panel(window) -> QWidget:
    card = _card(window, "Theme Mechanic Inventor")
    card.body.addWidget(_text_widget(
        window, "Which two ideas are you blending? Pick from the list or type your own."))
    state = _state(window)
    cur = list(getattr(state, "hybrid_themes", None) or [])
    themes = known_themes()
    combo_a = _editable_combo(themes, cur[0] if len(cur) > 0 else "")
    combo_b = _editable_combo(themes, cur[1] if len(cur) > 1 else "")

    def _sync() -> None:
        if state is not None:
            chosen = [t for t in (combo_a.currentText().strip(), combo_b.currentText().strip()) if t]
            setattr(state, "hybrid_themes", chosen)

    combo_a.currentTextChanged.connect(lambda _=None: _sync())
    combo_b.currentTextChanged.connect(lambda _=None: _sync())
    card.body.addWidget(_text_widget(window, "Theme A"))
    card.body.addWidget(combo_a)
    card.body.addWidget(_text_widget(window, "Theme B"))
    card.body.addWidget(combo_b)
    return card


def _vibe_panel(window) -> QWidget:
    card = _card(window, "Theme / Vibe")
    card.body.addWidget(_text_widget(
        window,
        "What theme or vibe are you shooting for? Pick from the list or type your own "
        "(e.g. spooky graveyard, pirates, big dumb dragons).",
    ))
    state = _state(window)
    combo = _editable_combo(known_themes(), str(getattr(state, "theme_intent", "") or ""))

    def _sync() -> None:
        if state is not None:
            setattr(state, "theme_intent", combo.currentText().strip())

    combo.currentTextChanged.connect(lambda _=None: _sync())
    card.body.addWidget(combo)
    return card


def build_intake_panel(window, persona_or_label) -> QWidget | None:
    """Return the inline intake panel for the selected guide, or None if it needs none."""
    key = resolve_persona_key(persona_or_label)
    if key == "pet_card":
        return _card_picker_panel(window, "pet_cards", "Pet Cards — never cut these",
                                  "Pick every card you will never let the deck cut.")
    if key == "weird_card_rescuer":
        return _card_picker_panel(window, "rescue_cards", "Weird Card Rescuer",
                                  "Pick the card(s) you're trying to make work — the deck "
                                  "will be reviewed around supporting them.")
    if key == "constraint_builder":
        return _constraint_panel(window)
    if key == "theme_mechanic_inventor":
        return _hybrid_panel(window)
    if key == "theme_vibe":
        return _vibe_panel(window)
    return None
