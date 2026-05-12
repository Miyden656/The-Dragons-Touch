"""Collection Source page builder for The Dragon's Touch v0.7 alpha hardening.

This module intentionally builds only the Collection Source page layout and local
signal wiring. The active MainWindow remains the workflow owner for staged
state, collection chooser behavior, Run Analysis refreshes, backend handoff, and
CLI/main.py execution.
"""

from PySide6.QtWidgets import QComboBox, QGridLayout, QLabel, QPushButton, QVBoxLayout

try:
    from ui.constants import APP_VERSION, COLLECTION_MODE_OPTIONS, COLLECTION_SOURCE_OPTIONS
    from ui.widgets import add_shadow, TexturedPanel, ReportCard
except ImportError:  # Allows direct local execution from inside the ui/ folder.
    from constants import APP_VERSION, COLLECTION_MODE_OPTIONS, COLLECTION_SOURCE_OPTIONS
    from widgets import add_shadow, TexturedPanel, ReportCard


def build_collection_source_page(window):
    """Build the Collection Source page while keeping staged-state behavior on MainWindow."""
    page, layout = window.page_container(
        "Collection Source",
        f"Stage how collection data should guide the review. {APP_VERSION} keeps collection choices honest: they guide suggestions but do not force weak or illegal swaps."
    )
    scroll, content = window.scroll_content()
    body = TexturedPanel(window.theme, kind="iron", glow=False)
    add_shadow(body, blur=24, y=8)
    b_layout = QGridLayout(body)
    b_layout.setContentsMargins(22, 22, 22, 22)
    b_layout.setSpacing(16)
    b_layout.setColumnStretch(0, 1)
    b_layout.setColumnStretch(1, 1)

    mode_card = ReportCard("Collection Mode", window.theme, badges=[("Staged UI", "primary")])
    mode_card.setMinimumHeight(230)
    mode_card.body.addWidget(window.make_text(
        "Choose how owned cards should affect future recommendations once backend hooks are connected.",
        paper=True
    ))
    mode_combo = QComboBox()
    window.collection_mode_combo = mode_combo
    mode_combo.addItems(COLLECTION_MODE_OPTIONS)
    mode_combo.setCurrentText(window.state.collection_mode)
    window.configure_combo_popup(mode_combo)
    mode_combo.currentTextChanged.connect(lambda text: window.stage_collection_mode(text))
    mode_card.body.addWidget(mode_combo)
    mode_card.body.addWidget(window.default_note("Default: No collection"))
    mode_card.body.addWidget(window.make_text(
        "Collection-only still stays honest: if no owned card is a real fit, the report should say so instead of forcing a weak recommendation.",
        paper=True
    ))

    source_card = ReportCard("Collection Source", window.theme, badges=[("Local files", "normal")])
    source_card.setMinimumHeight(230)
    source_combo = QComboBox()
    window.collection_source_combo = source_combo
    source_combo.addItems(COLLECTION_SOURCE_OPTIONS)
    source_combo.setCurrentText(window.state.collection_source_mode)
    window.configure_combo_popup(source_combo)
    source_combo.currentTextChanged.connect(lambda text: window.stage_collection_source_mode(text))
    source_card.body.addWidget(source_combo)
    source_card.body.addWidget(window.default_note("Default: Entire collection folder"))
    source_card.body.addWidget(window.make_text(
        "Only the relevant chooser is shown for the selected source mode.",
        paper=True
    ))
    folder_btn = QPushButton("Choose Collection Folder")
    window.collection_folder_button = folder_btn
    folder_btn.clicked.connect(window.choose_collection_folder)
    files_btn = QPushButton("Select Collection Files")
    window.collection_files_button = files_btn
    files_btn.clicked.connect(window.choose_collection_files)
    folder_btn.setVisible(window.state.collection_source_mode == "Entire collection folder")
    files_btn.setVisible(window.state.collection_source_mode == "Select collection files")
    source_card.body.addWidget(folder_btn)
    source_card.body.addWidget(files_btn)

    summary_card = TexturedPanel(window.theme, kind="iron_2", glow=True)
    summary_card.setMinimumHeight(245)
    s_layout = QVBoxLayout(summary_card)
    s_layout.setContentsMargins(18, 16, 18, 16)
    s_layout.setSpacing(10)
    s_title = QLabel("Collection Settings Summary")
    s_title.setObjectName("sectionTitle")
    s_layout.addWidget(s_title)
    collection_summary_box = window.readonly_text_box(window.collection_settings_summary_text(), min_height=120, max_height=155)
    window.collection_preview_boxes.append(collection_summary_box)
    s_layout.addWidget(collection_summary_box)
    s_layout.addWidget(window.default_note("Auto-staged: collection choices update immediately. No Apply button required."))

    honesty_card = ReportCard("Collection Honesty Boundary", window.theme, badges=[("v0.6.6.6 locked", "protected")])
    honesty_card.setMinimumHeight(245)
    honesty_card.body.addWidget(window.make_text(
        "Owned cards remain candidates, not automatic swaps. Future backend integration should preserve the locked behavior: collection-first, collection-only, and shakeup modes cannot override strategy fit, legality, color identity, companion restrictions, or quality gates.",
        paper=True
    ))

    b_layout.addWidget(mode_card, 0, 0)
    b_layout.addWidget(source_card, 0, 1)
    b_layout.addWidget(honesty_card, 1, 0)
    b_layout.addWidget(summary_card, 1, 1)
    content.addWidget(body)
    content.addStretch(1)
    layout.addWidget(scroll, stretch=1)
    return page
