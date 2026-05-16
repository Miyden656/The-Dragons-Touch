"""Philosophy Lens page builder for The Dragon's Touch v0.7 alpha hardening.

This module intentionally builds only the Philosophy Lens page layout and local
signal wiring. The active MainWindow remains the workflow owner for staged
state, Run Analysis refreshes, backend handoff, and CLI/main.py execution.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

try:
    from ui.constants import GUIDE_PRESENTATION_OPTIONS, PHILOSOPHY_SUBTYPE_OPTIONS
    from ui.widgets import add_shadow, TexturedPanel, ReportCard
except ImportError:  # Allows direct local execution from inside the ui/ folder.
    from constants import GUIDE_PRESENTATION_OPTIONS, PHILOSOPHY_SUBTYPE_OPTIONS
    from widgets import add_shadow, TexturedPanel, ReportCard


def build_philosophy_lens_page(window):
    """Build the Philosophy Lens page while keeping behavior on MainWindow."""
    page, layout = window.page_container(
        "Philosophy Lens",
        "Choose the review lens and guide voice. This shapes explanations and priorities without overriding legality, budget, collection mode, color identity, pilot intent, or deck evidence."
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

    guide_card = ReportCard("Guide Presentation", window.theme, badges=[("CLI bridge", "manual")])
    guide_card.setMinimumHeight(150)
    guide_card.body.addWidget(window.make_text(
        "Choose how the philosophy guide should be presented. This belongs with the Philosophy Lens, not cut/build mechanics.",
        paper=True
    ))
    guide_combo = QComboBox()
    guide_combo.setMinimumHeight(44)
    guide_combo.addItems(GUIDE_PRESENTATION_OPTIONS)
    guide_combo.setCurrentText(window.state.guide_presentation)
    window.configure_combo_popup(guide_combo)
    guide_combo.currentTextChanged.connect(window.stage_guide_presentation)
    guide_card.body.addWidget(guide_combo)
    guide_card.body.addWidget(window.default_note(
        "Philosophy Lens is optional playstyle guidance. It shapes tone and priorities, but legality, strategy, bracket, budget, and explicit user intent still come first."
    )
    # "Default: Either / random. Used after the top-level philosophy lens in the guarded CLI bridge."))
    body_layout.addWidget(guide_card)

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

    body_layout.addStretch(1)
    layout.addWidget(body, stretch=1)
    return page
