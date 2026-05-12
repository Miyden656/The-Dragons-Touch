"""Run Analysis page builder for The Dragon's Touch v0.7 alpha hardening.

This module intentionally builds only the Run Analysis page layout and local
widget wiring. The active MainWindow remains the workflow owner for guarded
confirmation, QProcess execution, CLI bridge state, report detection, and
Report Viewer handoff.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

try:
    from ui.constants import APP_VERSION, RUN_DETAIL_OPTIONS
    from ui.widgets import add_shadow, TexturedPanel, ForgeOrb, ReportCard
except ImportError:  # Allows direct local execution from inside the ui/ folder.
    from constants import APP_VERSION, RUN_DETAIL_OPTIONS
    from widgets import add_shadow, TexturedPanel, ForgeOrb, ReportCard


def build_run_analysis_page(window):
    """Build the Run Analysis page while keeping guarded-run behavior on MainWindow."""
    page, layout = window.page_container(
        "Run Analysis",
        f"Run main.py only after guarded confirmation. {APP_VERSION} shows diagnostics here; generated reports are read in Report Viewer."
    )
    body = QWidget(); body_layout = QHBoxLayout(body); body_layout.setContentsMargins(0, 0, 0, 0); body_layout.setSpacing(14)

    left = TexturedPanel(window.theme, kind="iron", glow=True); add_shadow(left, blur=28, y=8)
    l_layout = QVBoxLayout(left); l_layout.setContentsMargins(24, 24, 24, 24); l_layout.setSpacing(16)
    run_btn = QPushButton("🔥 Prepare Backend Run Preview")
    run_btn.setObjectName("primaryButton")
    run_btn.setMinimumHeight(64)
    run_btn.clicked.connect(window.run_placeholder_message)
    l_layout.addWidget(run_btn)
    guarded_btn = QPushButton("🛡 Guarded Execution Preview")
    guarded_btn.setMinimumHeight(48)
    guarded_btn.clicked.connect(window.guarded_execution_placeholder_message)
    l_layout.addWidget(guarded_btn)
    run_guarded_btn = QPushButton("Run main.py with Guarded Confirmation")
    run_guarded_btn.setObjectName("primaryButton")
    run_guarded_btn.setMinimumHeight(52)
    run_guarded_btn.clicked.connect(window.start_guarded_backend_run)
    window.guarded_run_button = run_guarded_btn
    window.guarded_run_buttons.append(run_guarded_btn)
    l_layout.addWidget(run_guarded_btn)

    readiness = ReportCard("Backend Readiness Checklist", window.theme, badges=[("No engine call", "manual")])
    readiness_box = window.readonly_text_box(window.run_readiness_text(), min_height=110, max_height=155)
    readiness_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    readiness.body.addWidget(readiness_box)
    l_layout.addWidget(readiness, stretch=0)

    bridge_status = ReportCard("Bridge Status", window.theme, badges=[("main.py guarded", "manual"), ("User-confirmed only", "protected")])
    bridge_status_box = window.readonly_text_box(
        "Active backend entrypoint: main.py\n"
        "Legacy name note: deck_helper.py was the older reference.\n"
        "Current alpha path: guarded QProcess run with explicit confirmation. No shell=True, no direct external API calls.\n"
        "Combo Tracker: optional future Commander Spellbook workflow, not part of normal deck review.",
        min_height=105,
        max_height=150
    )
    bridge_status_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    bridge_status.body.addWidget(bridge_status_box)
    l_layout.addWidget(bridge_status, stretch=0)

    orb_panel = TexturedPanel(window.theme, kind="iron_2", glow=True, corners=False)
    orb_layout = QVBoxLayout(orb_panel); orb_layout.setContentsMargins(12, 12, 12, 12)
    orb = ForgeOrb(window.theme)
    orb.setMinimumSize(190, 190)
    orb.setMaximumHeight(230)
    orb_layout.addWidget(orb, stretch=1)
    status = QLabel("Run the forge here. The latest successful manuscript loads from Report Viewer after output detection.")
    status.setObjectName("helperText"); status.setAlignment(Qt.AlignCenter); status.setWordWrap(True)
    orb_layout.addWidget(status)
    l_layout.addWidget(orb_panel, stretch=1)

    right = TexturedPanel(window.theme, kind="iron", glow=False); add_shadow(right, blur=28, y=8)
    r_layout = QVBoxLayout(right); r_layout.setContentsMargins(24, 24, 24, 24); r_layout.setSpacing(14)
    title = QLabel("Current Run Summary"); title.setObjectName("sectionTitle"); r_layout.addWidget(title)
    preview = QPlainTextEdit(); preview.setReadOnly(True); preview.setPlainText(window.run_config_preview_text()); preview.setMinimumHeight(130); preview.setMaximumHeight(180); preview.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded); preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    preview.setObjectName("runConfigPreview")
    window.run_config_preview_box = preview
    r_layout.addWidget(preview, stretch=0)

    selector_title = QLabel("Run Analysis Detail View"); selector_title.setObjectName("sectionTitle"); r_layout.addWidget(selector_title)
    selector_row = QHBoxLayout(); selector_row.setSpacing(10)
    selector_hint = QLabel("Detail section")
    selector_hint.setObjectName("helperText")
    selector_row.addWidget(selector_hint)
    detail_stack = QStackedWidget()
    detail_stack.setMinimumHeight(360)
    detail_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    detail_selector = QComboBox()
    detail_selector.setObjectName("detailSelectorCombo")
    detail_selector.addItems(RUN_DETAIL_OPTIONS)
    detail_selector.setMinimumWidth(260)
    detail_selector.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    window.configure_combo_popup(detail_selector)
    detail_selector.currentIndexChanged.connect(detail_stack.setCurrentIndex)
    selector_row.addWidget(detail_selector, stretch=1)
    selector_note = window.default_note("Guarded-run diagnostics stay here; generated report reading and file controls live in Report Viewer.")
    selector_row.addWidget(selector_note)
    r_layout.addLayout(selector_row)

    mapping_card = ReportCard("Backend Runtime Config Contract Preview", window.theme, badges=[("UI-only", "manual"), ("No engine call", "protected")])
    mapping_box = QPlainTextEdit()
    mapping_box.setReadOnly(True)
    mapping_box.setPlainText(window.backend_runtime_config_mapping_text())
    mapping_box.setMinimumHeight(260)
    mapping_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    mapping_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    mapping_box.setObjectName("runtimeMappingPreview")
    window.runtime_mapping_preview_box = mapping_box
    mapping_card.body.addWidget(mapping_box)
    detail_stack.addWidget(mapping_card)

    bridge_card = ReportCard("Safe Backend Bridge Preview", window.theme, badges=[("CLI bridge", "manual"), ("Guarded only", "protected")])
    bridge_box = QPlainTextEdit()
    bridge_box.setReadOnly(True)
    bridge_box.setPlainText(window.backend_bridge_preview_text())
    bridge_box.setMinimumHeight(260)
    bridge_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    bridge_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    bridge_box.setObjectName("backendBridgePreview")
    window.backend_bridge_preview_box = bridge_box
    bridge_card.body.addWidget(bridge_box)
    detail_stack.addWidget(bridge_card)

    combo_card = ReportCard("Optional Combo Tracker", window.theme, badges=[("Commander Spellbook later", "manual"), ("Opt-in", "protected")])
    combo_box = QPlainTextEdit()
    combo_box.setReadOnly(True)
    combo_box.setPlainText(window.combo_tracker_preview_text())
    combo_box.setMinimumHeight(250)
    combo_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    combo_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    combo_box.setObjectName("comboTrackerPreview")
    window.combo_tracker_preview_box = combo_box
    combo_card.body.addWidget(combo_box)
    combo_btn = QPushButton("Check Combos Later — Disabled Placeholder")
    combo_btn.setEnabled(False)
    combo_card.body.addWidget(combo_btn)
    combo_card.body.addWidget(window.default_note("Future behavior: only ping Commander Spellbook after explicit user click, and only when the decklist has changed since the last combo check."))
    detail_stack.addWidget(combo_card)

    guarded_card = ReportCard("Guarded Execution Bridge", window.theme, badges=[("Preview only", "manual"), ("subprocess disabled", "protected")])
    guarded_box = QPlainTextEdit()
    guarded_box.setReadOnly(True)
    guarded_box.setPlainText(window.guarded_execution_preview_text())
    guarded_box.setMinimumHeight(260)
    guarded_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    guarded_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    guarded_box.setObjectName("guardedExecutionPreview")
    window.guarded_execution_preview_box = guarded_box
    guarded_card.body.addWidget(guarded_box)
    guarded_preview_btn = QPushButton("Validate Guarded Run Preview — No Execution")
    guarded_preview_btn.clicked.connect(window.guarded_execution_placeholder_message)
    guarded_card.body.addWidget(guarded_preview_btn)
    guarded_run_btn = QPushButton("Run main.py with Guarded Confirmation")
    guarded_run_btn.setObjectName("primaryButton")
    guarded_run_btn.clicked.connect(window.start_guarded_backend_run)
    guarded_card.body.addWidget(guarded_run_btn)
    window.guarded_run_button = guarded_run_btn
    window.guarded_run_buttons.append(guarded_run_btn)
    guarded_card.body.addWidget(window.default_note("Run requires explicit confirmation. It uses QProcess, captures stdout/stderr, and does not call Commander Spellbook/API."))
    detail_stack.addWidget(guarded_card)

    result_card = ReportCard("Guarded Run Output / Result", window.theme, badges=[("Captured", "manual"), ("Review after run", "protected")])
    result_box = QPlainTextEdit()
    result_box.setReadOnly(True)
    result_box.setPlainText(window.guarded_run_result_text())
    result_box.setMinimumHeight(260)
    result_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    result_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    result_box.setObjectName("guardedRunResultPreview")
    window.guarded_run_result_box = result_box
    result_card.body.addWidget(result_box)
    result_card.body.addWidget(window.default_note("This output is captured from the guarded py main.py process. Report file paths are detected from stdout after successful runs."))
    detail_stack.addWidget(result_card)

    report_output_card = ReportCard("Report Output Detection", window.theme, badges=[("Path detection", "manual"), ("No parsing yet", "protected")])
    report_output_box = QPlainTextEdit()
    report_output_box.setReadOnly(True)
    report_output_box.setPlainText(window.report_output_summary_text())
    report_output_box.setMinimumHeight(220)
    report_output_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    report_output_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    report_output_box.setObjectName("reportOutputPreview")
    window.report_output_preview_box = report_output_box
    report_output_card.body.addWidget(report_output_box)
    open_row = QHBoxLayout()
    open_output_btn = QPushButton("Open Output Folder")
    open_output_btn.clicked.connect(window.open_last_output_folder)
    open_normal_btn = QPushButton("Open Normal Report Folder")
    open_normal_btn.clicked.connect(window.open_last_normal_report_folder)
    open_debug_btn = QPushButton("Open Debug Report Folder")
    open_debug_btn.clicked.connect(window.open_last_debug_report_folder)
    window.open_output_folder_button = open_output_btn
    window.open_normal_report_folder_button = open_normal_btn
    window.open_debug_report_folder_button = open_debug_btn
    window.refresh_report_output_buttons()
    open_row.addWidget(open_output_btn)
    open_row.addWidget(open_normal_btn)
    open_row.addWidget(open_debug_btn)
    report_output_card.body.addLayout(open_row)
    report_output_card.body.addWidget(window.default_note("Folder buttons use detected paths from the backend Files written block. Report contents are not parsed in this patch."))
    detail_stack.addWidget(report_output_card)

    boundary_card = ReportCard("Safety Boundary and Future Stages", window.theme, badges=[("v0.6.7.9.21", "manual")])
    stage_text = (
        "Future Backend Bridge Stages\n"
        "1. Runtime config contract is visible and refreshes live.\n"
        "2. Safe backend bridge preview is visible and refreshes live.\n"
        "3. Optional Combo Tracker placeholder is visible but API calls are disabled.\n"
        "4. Backend command execution is still disabled.\n"
        "5. A later guarded execution patch must preserve explicit user approval, error capture, and CLI source-of-truth boundaries.\n"
        "6. Report generation is still handled only by the locked CLI backend.\n\n"
        f"{window.backend_runtime_config_boundary_text()}"
    )
    boundary_box = window.readonly_text_box(stage_text, min_height=260, max_height=520)
    boundary_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    boundary_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    boundary_card.body.addWidget(boundary_box)
    detail_stack.addWidget(boundary_card)

    detail_stack.setCurrentIndex(0)
    r_layout.addWidget(detail_stack, stretch=1)

    body_layout.addWidget(left, stretch=1); body_layout.addWidget(right, stretch=2)
    run_scroll = QScrollArea()
    run_scroll.setWidgetResizable(True)
    run_scroll.setWidget(body)
    layout.addWidget(run_scroll, stretch=1)
    return page

