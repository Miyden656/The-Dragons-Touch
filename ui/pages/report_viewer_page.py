"""Report Viewer page builder for The Dragon's Touch v0.7 alpha hardening.

This module intentionally builds only the Report Viewer page. It does not own
backend execution, report generation, or report detection policy. The active
MainWindow remains the workflow owner and passes itself into this builder so the
existing report viewer methods/signals remain stable during the first full-page
extraction.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

try:
    from ui.constants import APP_VERSION
    from ui.widgets import add_shadow, TexturedPanel, ReportCard
except ImportError:  # Allows direct local execution from inside the ui/ folder.
    from constants import APP_VERSION
    from widgets import add_shadow, TexturedPanel, ReportCard


def build_report_viewer_page(window):
    page, layout = window.page_container(
        "Report Viewer",
        f"Read latest guarded-run reports from backend-created output folders. {APP_VERSION} keeps plain-text report viewing and final user-facing boundaries explicit."
    )
    body = QWidget()
    body_layout = QHBoxLayout(body)
    body_layout.setContentsMargins(0, 0, 0, 0)
    body_layout.setSpacing(14)

    report_nav = TexturedPanel(window.theme, kind="iron", glow=False)
    report_nav.setFixedWidth(330)
    add_shadow(report_nav, blur=22, y=7)
    rn_layout = QVBoxLayout(report_nav)
    rn_layout.setContentsMargins(16, 16, 16, 16)
    rn_layout.setSpacing(10)
    cap = QLabel("DETECTED REPORT FILES")
    cap.setObjectName("smallCaps")
    rn_layout.addWidget(cap)
    file_scroll = QScrollArea()
    file_scroll.setWidgetResizable(True)
    file_inner = QWidget()
    window.report_viewer_file_buttons_layout = QVBoxLayout(file_inner)
    window.report_viewer_file_buttons_layout.setContentsMargins(0, 0, 6, 0)
    window.report_viewer_file_buttons_layout.setSpacing(8)
    file_scroll.setWidget(file_inner)
    rn_layout.addWidget(file_scroll, stretch=1)

    reload_btn = QPushButton("Reload Latest Reports")
    reload_btn.clicked.connect(window.reload_latest_reports_into_viewer)
    window.report_viewer_reload_button = reload_btn
    rn_layout.addWidget(reload_btn)

    open_folder_btn = QPushButton("Open Output Folder")
    open_folder_btn.clicked.connect(window.open_last_output_folder)
    rn_layout.addWidget(open_folder_btn)

    viewer_panel = TexturedPanel(window.theme, kind="iron", glow=True)
    add_shadow(viewer_panel, blur=26, y=8)
    viewer_layout = QVBoxLayout(viewer_panel)
    viewer_layout.setContentsMargins(22, 22, 22, 22)
    viewer_layout.setSpacing(18)

    report_text_card = ReportCard("Report File Preview", window.theme, badges=[("Plain text", "manual"), ("Grouped files", "protected")])
    report_text_card.setMinimumHeight(430)
    report_text_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    current_file_label = QLabel(window.report_viewer_current_file_label_text())
    current_file_label.setObjectName("defaultNote")
    current_file_label.setWordWrap(True)
    current_file_label.setToolTip(window.state.report_viewer_current_file)
    window.report_viewer_current_file_label = current_file_label
    report_text_card.body.addWidget(current_file_label)

    reader_tools = QHBoxLayout()
    reader_tools.setSpacing(8)
    search_input = QLineEdit(window.state.report_viewer_search_text)
    search_input.setPlaceholderText("Search current report")
    window.report_viewer_search_input = search_input
    search_btn = QPushButton("Find")
    search_btn.clicked.connect(window.find_in_current_report)
    search_input.returnPressed.connect(window.find_in_current_report)
    top_btn = QPushButton("Top")
    top_btn.clicked.connect(window.jump_report_viewer_top)
    bottom_btn = QPushButton("Bottom")
    bottom_btn.clicked.connect(window.jump_report_viewer_bottom)
    wrap_btn = QPushButton("Wrap: On" if window.state.report_viewer_word_wrap else "Wrap: Off")
    wrap_btn.clicked.connect(window.toggle_report_viewer_word_wrap)
    window.report_viewer_wrap_button = wrap_btn
    reader_tools.addWidget(search_input, stretch=2)
    reader_tools.addWidget(search_btn)
    reader_tools.addWidget(top_btn)
    reader_tools.addWidget(bottom_btn)
    reader_tools.addWidget(wrap_btn)
    report_text_card.body.addLayout(reader_tools)

    text_box = QPlainTextEdit()
    text_box.setReadOnly(True)
    text_box.setPlainText(window.state.report_viewer_current_text)
    text_box.setMinimumHeight(300)
    text_box.setMaximumHeight(16777215)
    text_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    text_box.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    text_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    text_box.setObjectName("reportFilePreview")
    window.report_viewer_text_box = text_box
    window.apply_report_viewer_readability_settings()
    report_text_card.body.addWidget(text_box, stretch=1)
    viewer_layout.addWidget(report_text_card, stretch=4)

    status_card = ReportCard("Loaded Report Status", window.theme, badges=[("No deep parsing", "protected")])
    status_card.setMinimumHeight(210)
    status_card.setMaximumHeight(285)
    status_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    status_label = QPlainTextEdit()
    status_label.setReadOnly(True)
    status_label.setPlainText(window.report_viewer_status_text())
    status_label.setObjectName("reportStatusPreview")
    status_label.setMinimumHeight(84)
    status_label.setMaximumHeight(125)
    status_label.setFrameShape(QFrame.NoFrame)
    status_label.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    status_label.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    status_label.setToolTip(
        f"Current file: {window.state.report_viewer_current_file}\nOutput folder: {window.state.last_output_folder}"
    )
    window.report_viewer_status_label = status_label
    status_card.body.addWidget(status_label)
    action_row = QHBoxLayout()
    action_row.setContentsMargins(0, 8, 0, 0)
    refresh_btn = QPushButton("Refresh Current File")
    refresh_btn.clicked.connect(window.refresh_current_report_file)
    window.report_viewer_refresh_file_button = refresh_btn
    copy_btn = QPushButton("Copy Report Text")
    copy_btn.clicked.connect(window.copy_current_report_text)
    window.report_viewer_copy_button = copy_btn
    open_folder_current_btn = QPushButton("Open Current Folder")
    open_folder_current_btn.clicked.connect(window.open_current_report_folder)
    window.report_viewer_open_current_folder_button = open_folder_current_btn
    open_file_btn = QPushButton("Open Current Report File")
    open_file_btn.clicked.connect(window.open_current_report_file)
    window.open_current_report_file_button = open_file_btn
    action_row.addWidget(refresh_btn)
    action_row.addWidget(copy_btn)
    action_row.addStretch(1)
    action_row.addWidget(open_folder_current_btn)
    action_row.addWidget(open_file_btn)
    status_card.body.addLayout(action_row)
    viewer_layout.addWidget(status_card, stretch=0)

    body_layout.addWidget(report_nav, stretch=0)
    body_layout.addWidget(viewer_panel, stretch=1)
    layout.addWidget(body, stretch=1)
    window.refresh_report_viewer_file_list()
    return page
