"""Per-guide pilot-intent intake dialogs.

Self-contained PySide6 dialogs for the five guides whose need is user-intent-gated
(Pet Card / Self-Imposed Constraint / Weird Card Rescuer / Theme Mechanic Inventor /
Theme-Vibe). Each captures the missing input and returns it as a dict ready to merge
onto AppState; from there backend_runner.environment_values -> config.get_runtime_config
carries it into the report + the AI guide (no further wiring needed).

Integration (one call):
    from ui.dialogs.persona_intake_dialogs import persona_needs_intake, open_persona_intake
    if persona_needs_intake(selected_persona_key):
        result = open_persona_intake(selected_persona_key, parent=self,
                                     deck_cards=current_deck_card_names, current=app_state)
        if result:                      # None == user cancelled
            for k, v in result.items():
                setattr(app_state, k, v)

Kept dependency-light and theme-agnostic; pass an optional Qt stylesheet via
`stylesheet=` if you want it to match the app theme.
"""

from __future__ import annotations

from typing import Iterable

from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton, QVBoxLayout,
    QAbstractItemView,
)

from analysis.pilot_intent import known_themes

# persona key -> which intake this guide needs
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
    """Resolve a persona key from either a key (e.g. 'pet_card') or a UI subtype
    LABEL (e.g. 'Milo / Mia — Pet Card'). Robust to em-dash vs hyphen. Returns '' if
    the value isn't one of the five intake personas."""
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


class _BaseIntakeDialog(QDialog):
    def __init__(self, title: str, blurb: str, parent=None, stylesheet: str = ""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(440)
        if stylesheet:
            self.setStyleSheet(stylesheet)
        self._root = QVBoxLayout(self)
        heading = QLabel(blurb)
        heading.setWordWrap(True)
        self._root.addWidget(heading)

    def _add_buttons(self) -> None:
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self._root.addWidget(buttons)


class _CardPickerDialog(_BaseIntakeDialog):
    """Multi-select from the decklist + free-text add (used by Pet Card and Rescue)."""

    def __init__(self, title, blurb, deck_cards=(), current=(), parent=None, stylesheet=""):
        super().__init__(title, blurb, parent, stylesheet)
        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        chosen = {str(c).strip() for c in (current or [])}
        names: list[str] = []
        for name in deck_cards or []:
            name = str(name).strip()
            if name and name not in names:
                names.append(name)
        # include any current pick not in the deck (e.g. a card being added)
        for name in chosen:
            if name and name not in names:
                names.append(name)
        for name in names:
            item = QListWidgetItem(name)
            self._list.addItem(item)
            if name in chosen:
                item.setSelected(True)
        self._root.addWidget(self._list)

        add_row = QHBoxLayout()
        self._add_field = QLineEdit()
        self._add_field.setPlaceholderText("Add a card not listed above…")
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_typed)
        self._add_field.returnPressed.connect(self._add_typed)
        add_row.addWidget(self._add_field)
        add_row.addWidget(add_btn)
        self._root.addLayout(add_row)
        self._add_buttons()

    def _add_typed(self) -> None:
        name = self._add_field.text().strip()
        if not name:
            return
        for i in range(self._list.count()):
            if self._list.item(i).text() == name:
                self._list.item(i).setSelected(True)
                self._add_field.clear()
                return
        item = QListWidgetItem(name)
        self._list.addItem(item)
        item.setSelected(True)
        self._add_field.clear()

    def selected_cards(self) -> list[str]:
        return [i.text() for i in self._list.selectedItems()]


def _editable_combo(options: Iterable[str], current: str = "") -> QComboBox:
    """A dropdown that also accepts free text (dropdown + type-your-own in one)."""
    combo = QComboBox()
    combo.setEditable(True)
    combo.addItem("")
    for opt in options:
        combo.addItem(str(opt))
    if current:
        combo.setCurrentText(str(current))
    return combo


class _ConstraintDialog(_BaseIntakeDialog):
    def __init__(self, current="", parent=None, stylesheet=""):
        super().__init__(
            "Self-Imposed Constraint",
            "What's the rule for this deck? (e.g. budget ≤ $5/card, no green creatures, "
            "only cards from sets I opened)",
            parent, stylesheet,
        )
        self._text = QPlainTextEdit()
        self._text.setPlainText(str(current or ""))
        self._root.addWidget(self._text)
        self._add_buttons()

    def constraint_text(self) -> str:
        return self._text.toPlainText().strip()


class _HybridThemeDialog(_BaseIntakeDialog):
    def __init__(self, current=(), parent=None, stylesheet=""):
        super().__init__(
            "Theme Mechanic Inventor",
            "Which two ideas are you blending? Pick from the list or type your own.",
            parent, stylesheet,
        )
        cur = list(current or [])
        themes = known_themes()
        self._a = _editable_combo(themes, cur[0] if len(cur) > 0 else "")
        self._b = _editable_combo(themes, cur[1] if len(cur) > 1 else "")
        self._root.addWidget(QLabel("Theme A"))
        self._root.addWidget(self._a)
        self._root.addWidget(QLabel("Theme B"))
        self._root.addWidget(self._b)
        self._add_buttons()

    def themes(self) -> list[str]:
        return [t for t in (self._a.currentText().strip(), self._b.currentText().strip()) if t]


class _ThemeVibeDialog(_BaseIntakeDialog):
    def __init__(self, current="", parent=None, stylesheet=""):
        super().__init__(
            "Theme / Vibe",
            "What theme or vibe are you shooting for? Pick from the list or type your own "
            "(e.g. spooky graveyard, pirates, big dumb dragons).",
            parent, stylesheet,
        )
        self._combo = _editable_combo(known_themes(), str(current or ""))
        self._root.addWidget(self._combo)
        self._add_buttons()

    def vibe(self) -> str:
        return self._combo.currentText().strip()


def open_persona_intake(persona_key, parent=None, deck_cards=(), current=None, stylesheet=""):
    """Open the intake dialog for a persona; return a dict of AppState fields to set,
    or None if the guide needs no intake or the user cancelled. `current` may be the
    AppState (or any object/dict) to prefill from."""
    kind = PERSONA_INTAKE.get(str(persona_key or "").strip())
    if not kind:
        return None

    def cur(name, default):
        if current is None:
            return default
        if isinstance(current, dict):
            return current.get(name, default)
        return getattr(current, name, default)

    if kind == "pet_cards":
        dlg = _CardPickerDialog("Pet Cards", "Which cards will you never cut?",
                                deck_cards, cur("pet_cards", []), parent, stylesheet)
        return {"pet_cards": dlg.selected_cards()} if dlg.exec() == QDialog.DialogCode.Accepted else None
    if kind == "rescue_cards":
        dlg = _CardPickerDialog("Weird Card Rescuer", "Which card(s) are you trying to make work?",
                                deck_cards, cur("rescue_cards", []), parent, stylesheet)
        return {"rescue_cards": dlg.selected_cards()} if dlg.exec() == QDialog.DialogCode.Accepted else None
    if kind == "constraint":
        dlg = _ConstraintDialog(cur("declared_constraints", ""), parent, stylesheet)
        return {"declared_constraints": dlg.constraint_text()} if dlg.exec() == QDialog.DialogCode.Accepted else None
    if kind == "hybrid_themes":
        dlg = _HybridThemeDialog(cur("hybrid_themes", []), parent, stylesheet)
        return {"hybrid_themes": dlg.themes()} if dlg.exec() == QDialog.DialogCode.Accepted else None
    if kind == "theme_vibe":
        dlg = _ThemeVibeDialog(cur("theme_intent", ""), parent, stylesheet)
        return {"theme_intent": dlg.vibe()} if dlg.exec() == QDialog.DialogCode.Accepted else None
    return None
