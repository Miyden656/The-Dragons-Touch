"""Settings page for The Dragon's Touch.

v0.10.5.1-dev:
Settings controls app-wide defaults.
Review Setup controls the current run.

v0.10.5.7-dev:
Guide Presentation is confirmed as an app-wide Settings control, not a Philosophy Lens control.
"""

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

    from ui.constants import (
        INTERFACE_MODE_OPTIONS,
        GUIDE_PRESENTATION_OPTIONS,
        APP_COLLECTION_SOURCE_DEFAULT_OPTIONS,
        UI_DENSITY_OPTIONS,
    )
    from ui.styles.theme import ADVENTURERS_MAP, DRAGON_FORGE
    from ui.widgets import add_shadow, ReportCard, TexturedPanel
except ImportError:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

    from constants import (
        INTERFACE_MODE_OPTIONS,
        GUIDE_PRESENTATION_OPTIONS,
        APP_COLLECTION_SOURCE_DEFAULT_OPTIONS,
        UI_DENSITY_OPTIONS,
    )
    from styles.theme import ADVENTURERS_MAP, DRAGON_FORGE
    from widgets import add_shadow, ReportCard, TexturedPanel


def _row(label_text, widget, note_text=None):
    row = QHBoxLayout()
    label = QLabel(label_text)
    label.setObjectName("helperText")
    label.setMinimumWidth(185)
    row.addWidget(label)
    row.addWidget(widget, stretch=1)
    return row


def _combo(window, values, current):
    combo = QComboBox()
    combo.addItems(values)
    combo.setCurrentText(current if current in values else values[0])
    combo.setMinimumWidth(260)
    window.configure_combo_popup(combo)
    return combo


def build_settings_page(window):
    page, layout = window.page_container(
        "Settings",
        "App-wide preferences for The Dragon's Touch. Settings persist across restarts; Review Setup remains for the current run."
    )

    scroll, content = window.scroll_content()
    body = TexturedPanel(window.theme, kind="iron", glow=False)
    add_shadow(body, blur=24, y=8)

    b_layout = QVBoxLayout(body)
    b_layout.setContentsMargins(22, 22, 22, 22)
    b_layout.setSpacing(16)

    # Developer mode banner.
    if window.is_dev_mode():
        dev_banner = TexturedPanel(window.theme, kind="iron_2", glow=True)
        banner_layout = QHBoxLayout(dev_banner)
        banner_layout.setContentsMargins(16, 12, 16, 12)
        banner = QLabel("Developer Mode Enabled")
        banner.setObjectName("sectionTitle")
        detail = QLabel("Development, diagnostics, raw reports, and testing controls may be visible.")
        detail.setObjectName("defaultNote")
        detail.setWordWrap(True)
        banner_layout.addWidget(banner)
        banner_layout.addWidget(detail, stretch=1)
        b_layout.addWidget(dev_banner)

    # Interface Mode.
    interface_card = ReportCard("Interface Mode", window.theme, badges=[("Persistent", "primary")])
    interface_combo = _combo(window, INTERFACE_MODE_OPTIONS, window.interface_mode_display_text())
    window.interface_mode_combo = interface_combo
    interface_combo.currentTextChanged.connect(window.stage_interface_mode)
    interface_card.body.addLayout(_row("Mode", interface_combo))
    interface_card.body.addWidget(window.default_note(
        "User Mode is the clean default for normal deck reviews. Developer Mode is enabled here only and exposes testing/diagnostic tools."
    ))
    if window.is_dev_mode():
        interface_card.body.addWidget(window.default_note("Developer Mode Enabled. Remember to switch back to User Mode before handing the app to a normal tester."))
    b_layout.addWidget(interface_card)

    # Appearance.
    appearance_card = ReportCard("Appearance", window.theme, badges=[("Visual", "primary")])
    theme_row = QHBoxLayout()
    dark = QPushButton("Dragon Forge")
    dark.setObjectName("primaryButton" if window.theme()["name"] == "Dragon Forge" else "utilityButton")
    dark.clicked.connect(lambda: window.set_theme(DRAGON_FORGE))
    light = QPushButton("Adventurer's Map")
    light.setObjectName("primaryButton" if window.theme()["name"] == "Adventurer's Map" else "utilityButton")
    light.clicked.connect(lambda: window.set_theme(ADVENTURERS_MAP))
    window.settings_theme_buttons = [(dark, "Dragon Forge"), (light, "Adventurer's Map")]
    theme_row.addWidget(dark)
    theme_row.addWidget(light)
    theme_row.addStretch(1)
    appearance_card.body.addLayout(theme_row)

    density_combo = _combo(window, UI_DENSITY_OPTIONS, getattr(window.state, "ui_density", "Normal"))
    density_combo.currentTextChanged.connect(window.stage_ui_density)
    appearance_card.body.addLayout(_row("UI density", density_combo))
    appearance_card.body.addWidget(window.default_note("Density is persisted now. Layout-specific density tuning will expand in later cleanup passes."))
    b_layout.addWidget(appearance_card)

    # Guide Presentation.
    guide_card = ReportCard("Guide Presentation", window.theme, badges=[("Persistent", "primary")])
    guide_combo = _combo(window, GUIDE_PRESENTATION_OPTIONS, window.state.guide_presentation)
    guide_combo.currentTextChanged.connect(window.stage_guide_presentation)
    guide_card.body.addLayout(_row("Guide style", guide_combo))
    guide_card.body.addWidget(window.default_note(
        "This controls the gendered or neutral guide voice used for Timmy/Tammy, Johnny/Jenny, and Spike-style guidance. It is independent from Philosophy Lens, so No Philosophy still keeps the selected guide presentation."
    ))
    b_layout.addWidget(guide_card)

    # Collection Defaults.
    collection_card = ReportCard("Collection Defaults", window.theme, badges=[("App default", "manual")])
    collection_default = window.collection_source_default_display_text()
    collection_combo = _combo(window, APP_COLLECTION_SOURCE_DEFAULT_OPTIONS, collection_default)
    collection_combo.currentTextChanged.connect(window.stage_collection_source_default)
    collection_card.body.addLayout(_row("Default source", collection_combo))

    folder_row = QHBoxLayout()
    folder_label = QLabel("Local path")
    folder_label.setObjectName("helperText")
    folder_label.setMinimumWidth(185)
    folder_value = QLabel(window.state.collection_folder or "collection")
    folder_value.setObjectName("defaultNote")
    folder_value.setWordWrap(True)
    window.settings_collection_folder_label = folder_value
    choose_folder = QPushButton("Choose Collection Folder")
    choose_folder.setObjectName("utilityButton")
    choose_folder.clicked.connect(window.choose_collection_folder)
    choose_files = QPushButton("Choose Collection Files")
    choose_files.setObjectName("utilityButton")
    choose_files.clicked.connect(window.choose_collection_files)
    folder_row.addWidget(folder_label)
    folder_row.addWidget(folder_value, stretch=1)
    folder_row.addWidget(choose_folder)
    folder_row.addWidget(choose_files)
    collection_card.body.addLayout(folder_row)
    collection_card.body.addWidget(window.default_note(
        "Collection source is an app-wide default. Collection Mode will move to Review Setup because it is a current-run choice."
    ))
    b_layout.addWidget(collection_card)

    # Report Folder.
    report_card = ReportCard("Report Folder", window.theme, badges=[("Persistent", "primary")])
    report_row = QHBoxLayout()
    report_label = QLabel("Output folder")
    report_label.setObjectName("helperText")
    report_label.setMinimumWidth(185)
    report_value = QLabel(getattr(window.state, "report_output_folder", "Outputs") or "Outputs")
    report_value.setObjectName("defaultNote")
    report_value.setWordWrap(True)
    window.settings_report_folder_label = report_value
    choose_report = QPushButton("Choose Report Folder")
    choose_report.setObjectName("utilityButton")
    choose_report.clicked.connect(window.choose_report_output_folder)
    report_row.addWidget(report_label)
    report_row.addWidget(report_value, stretch=1)
    report_row.addWidget(choose_report)
    report_card.body.addLayout(report_row)
    report_card.body.addWidget(window.default_note(
        "User Mode Report Viewer will use this folder as the default place to find the latest user-facing handoff."
    ))
    b_layout.addWidget(report_card)

    # Developer settings status.
    dev_card = ReportCard("Developer Settings", window.theme, badges=[("Settings only", "manual")])
    dev_card.body.addWidget(window.make_text(
        "Developer Mode is intentionally controlled from Settings only. No quick switch should be added elsewhere.\n\n"
        f"Current mode: {window.interface_mode_display_text()}\n"
        f"Developer Report Viewer last view: {getattr(window.state, 'developer_report_viewer_last_view', 'User View')}\n"
        f"Settings file: {window.user_settings_path_text()}",
        paper=True,
    ))
    reset_btn = QPushButton("Reset Settings to Defaults")
    reset_btn.setObjectName("utilityButton")
    reset_btn.clicked.connect(window.reset_user_settings_to_defaults)
    dev_card.body.addWidget(reset_btn)
    b_layout.addWidget(dev_card)

    b_layout.addStretch(1)
    content.layout().addWidget(body)
    layout.addWidget(scroll, stretch=1)
    return page
