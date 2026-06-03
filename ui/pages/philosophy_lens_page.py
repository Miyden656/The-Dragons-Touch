"""Philosophy Lens page builder for The Dragon's Touch v0.7 alpha hardening.

v0.10.5.7-dev:
- App-wide guide style selection now lives in Settings only.
- Philosophy Lens remains focused on deckbuilding philosophy/persona direction.

This module intentionally builds only the Philosophy Lens page layout and local
signal wiring. The active MainWindow remains the workflow owner for staged
state, Run Analysis refreshes, backend handoff, and CLI/main.py execution.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

try:
    from ui.constants import PHILOSOPHY_SUBTYPE_OPTIONS, PHILOSOPHY_LENS_HELP_TEXT
    from ui.widgets import add_shadow, TexturedPanel, ReportCard
except ImportError:  # Allows direct local execution from inside the ui/ folder.
    from constants import PHILOSOPHY_SUBTYPE_OPTIONS, PHILOSOPHY_LENS_HELP_TEXT
    from widgets import add_shadow, TexturedPanel, ReportCard


def _clear_layout(layout):
    """Remove and delete every widget currently in a layout."""
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()


def build_philosophy_lens_page(window):
    """Build the Philosophy Lens page while keeping behavior on MainWindow."""
    page, layout = window.page_container(
        "Philosophy Lens",
        "Optional playstyle guidance for tone and priorities. It does not override legality, budget, collection mode, color identity, pilot intent, or deck evidence."
    )
    body = TexturedPanel(window.theme, kind="iron", glow=False)
    add_shadow(body, blur=24, y=8)
    body_layout = QVBoxLayout(body)
    body_layout.setContentsMargins(22, 22, 22, 22)
    body_layout.setSpacing(16)

    cards = QHBoxLayout()
    cards.setSpacing(16)
    philosophies = [
        ("Timmy / Tammy", "Big moments, splashy plays, memorable stories.", "🐲", "Big Creature • Theme • Battlecruiser"),
        ("Johnny / Jenny", "Engines, clever interactions, weird card rescues.", "🛠", "Engine Builder • Combo • Constraint"),
        ("Spike", "Consistency, efficiency, discipline, clean closing power.", "⚔", "Optimizer • Calibrator • Controller"),
    ]
    for name, desc, icon, tags in philosophies:
        card = ReportCard(name, window.theme)
        card.setMinimumWidth(250)
        card.setMinimumHeight(235)
        subtype = QLabel(tags)
        subtype.setWordWrap(True)
        subtype.setObjectName("philosophySubtype")
        card.body.addWidget(subtype)
        portrait = QLabel(icon)
        portrait.setAlignment(Qt.AlignCenter)
        portrait.setStyleSheet("font-size: 48px; color: #3a2818;")
        card.body.addWidget(portrait)
        card.body.addWidget(window.make_text(desc, paper=True))
        btn = QPushButton("Select Profile")
        btn.setMinimumHeight(38)
        btn.clicked.connect(lambda checked=False, n=name: window.select_philosophy(n))
        card.body.addWidget(btn)
        cards.addWidget(card)
    body_layout.addLayout(cards)

    subtype_card = ReportCard("Specific Philosophy Subtype", window.theme, badges=[("optional bridge", "manual")])
    subtype_card.setMinimumHeight(150)
    subtype_card.body.addWidget(window.make_text(
        "Optional. Use this only when you want the backend's Specific philosophy subtype route instead of the top-level profile route.",
        paper=True
    ))
    subtype_combo = QComboBox()
    subtype_combo.setMinimumHeight(44)
    subtype_combo.addItems(PHILOSOPHY_SUBTYPE_OPTIONS)
    subtype_combo.setCurrentText(window.state.philosophy_subtype)
    window.configure_combo_popup(subtype_combo)
    subtype_combo.currentTextChanged.connect(window.stage_philosophy_subtype)
    subtype_card.body.addWidget(subtype_combo)
    subtype_card.body.addWidget(window.default_note("Default: None / top-level only. Subtype bridge is optional and only used when this dropdown is changed."))
    body_layout.addWidget(subtype_card)

    # Inline pilot-intent intake: for the five guides whose need is user-declared
    # (Pet Card / Constraint / Weird Card Rescuer / Theme Mechanic Inventor /
    # Theme-Vibe), render the intake panel right here under the subtype dropdown.
    # The page is already scrollable (page_container wraps it in a QScrollArea), so
    # the panel can be as tall as it needs to be. Panels write to the staged AppState
    # live; the dropdown swap is connected AFTER staging so the subtype is current.
    intake_holder = QWidget()
    intake_layout = QVBoxLayout(intake_holder)
    intake_layout.setContentsMargins(0, 0, 0, 0)
    intake_layout.setSpacing(12)
    body_layout.addWidget(intake_holder)

    def _refresh_intake(label):
        _clear_layout(intake_layout)
        try:
            from ui.dialogs.persona_intake_panels import build_intake_panel
            panel = build_intake_panel(window, label)
        except Exception:
            panel = None
        if panel is not None:
            intake_layout.addWidget(panel)

    subtype_combo.currentTextChanged.connect(_refresh_intake)
    _refresh_intake(window.state.philosophy_subtype)  # show the panel for the current pick

    # The page itself has no scroll (page_container/wrap_flow_page don't add one), so
    # a tall intake panel would compress and overlap the philosophy cards. Wrap the
    # body in a scroll area so the whole page scrolls instead. No addStretch here —
    # the content must take its natural height for the scrollbar to engage.
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setWidget(body)
    layout.addWidget(scroll, stretch=1)
    return page
