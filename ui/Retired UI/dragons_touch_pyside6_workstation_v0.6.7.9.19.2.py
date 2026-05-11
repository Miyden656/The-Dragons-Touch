"""
The Dragon's Touch - PySide6 Desktop UI Foundation
Version: v0.6.7.9.18 — Backend Unique Run Output Folder Handoff Fix with Deck Filename Distinction

Standalone local desktop UI foundation for a fantasy-themed Commander deck-building
and deck-review app.

This version focuses on:
- preserving the Dragon Forge / parchment manuscript visual direction
- formalizing the mockup into the first official desktop UI foundation
- aligning pages with the locked v0.6.6.6 workflow
- keeping the backend safely disconnected until later v0.6.7 patches
- adding clear backend-hook placeholders for future integration

Current scope:
- UI shell and navigation are active
- deck file selection and preview are active
- review settings and collection source staging are active
- Run Analysis shows a staged backend configuration preview
- no analysis engine is called yet
- no card database is loaded yet
- no real report files are opened yet
- command-line backend remains the stable source of truth

Run:
    pip install PySide6
    python dragons_touch_pyside6_workstation.py
"""

import sys
import math
import shutil
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QRectF, QPointF, QSignalBlocker, QProcess, QProcessEnvironment, QUrl
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QFont, QLinearGradient, QRadialGradient, QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QComboBox, QFileDialog, QFrame, QGraphicsDropShadowEffect,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListView, QMainWindow, QMessageBox,
    QPlainTextEdit, QProgressBar, QPushButton, QScrollArea, QSlider, QSizePolicy,
    QStackedWidget, QVBoxLayout, QWidget
)


APP_VERSION = "v0.6.7.9.19.2"
APP_PHASE = "Report Viewer Parchment Status Layout Hotfix"
BACKEND_STATUS = "Guarded backend bridge available — review setup cleanup and commander pair preview fixed"
LOCKED_BACKEND_VERSION = "v0.6.6.6"

# Future backend integration notes:
# - v0.6.7.2 adds real deck-file selection and local preview.
# - v0.6.7.3 adds a real UI review-settings form and stages values for later backend config mapping.
# - v0.6.7.3.3 cleans up Adventurer’s Map dropdown popup frames while preserving review setup behavior.
# - v0.6.7.4 adds real UI collection-mode and collection-source staging.
# - v0.6.7.4.1 cleans up collection-source control visibility, immediate preview updates, and card layout.
# - v0.6.7.5 prepares the Run Analysis page by showing the staged backend configuration preview.
# - v0.6.7.5.2 cleans up staged refresh timing so summaries update before confirmation popups.
# - v0.6.7.5.2 auto-stages Review Setup and Collection Source choices and cleans up Philosophy Lens cards.
# - v0.6.7.5.3 removes shell rebuilds from collection auto-staging and theme switching to prevent transient flash popups.
# - v0.6.7.5.4.1 applies visible UI cleanup for Review Intensity, collection summary layout, sidebar heading readability, and philosophy subtype readability.
# - v0.6.7.5.5 adds an intended bracket selector to Review Setup and staged run previews while keeping backend execution disconnected.
# - v0.6.7.6 adds a backend runtime config mapping preview without calling the backend.
# - v0.6.7.6.1 refreshes Run Analysis preview boxes when staged UI values change and lightly cleans up layout spacing.
# - v0.6.7.6.2 polishes the runtime config mapping into a clearer future backend handoff contract.
# - v0.6.7.7 adds a first safe backend bridge preview without executing main.py or any backend command.
# - v0.6.7.7.1 updates the backend entrypoint preview to main.py, cleans up Run Analysis layout, and adds an optional Commander Spellbook combo tracker placeholder.
# - v0.6.7.7.2 fixes Run Analysis scrollbox/detail-panel sizing and prevents dense text clipping.
# - v0.6.7.8 adds the first guarded execution bridge preview with entrypoint validation, command preview, and error/output capture planning while keeping actual subprocess execution disabled.
# - v0.6.7.9.18 loads detected generated report files into the Report Viewer as plain text without deep parsing.
# - v0.6.7.8.1 replaces the Run Analysis detail button row with a compact dropdown selector.
# - v0.6.7.9 adds the first actual guarded QProcess run path for py main.py with explicit confirmation, output capture, and safe failure handling.
# - v0.6.7.9.10 hands the selected Deck Selection file to main.py through MTG_DECK_FILE and cleans Philosophy Lens layout/readability.
# - v0.6.7.9.11 normalizes collection folder/file readiness so Entire collection folder and Select collection files are treated correctly.
# - v0.6.7.9.1 adds the first controlled stdin bridge for the known output-mode prompt only.
# - v0.6.7.9.2 adds the second controlled stdin bridge for the known review-direction prompt only.
# - v0.6.7.9.3 adds a durable Build-Up Mode UI field and bridges the build-up prompt when Review Direction is Build up.
# - v0.6.7.9.4 adds the Prompt Mode bridge for the known Build-up flow and makes Review Setup direction-aware.
# - v0.6.7.9.6 adds Philosophy Lens CLI bridging and cleans up Review Setup conditional card layout.
# - v0.6.7.9.6 adds a durable Guide Presentation UI field and bridges the guide presentation CLI prompt.
# - v0.6.7.9.7 bridges the Collection Mode CLI prompt using the existing Collection Source page setting.
# - v0.6.7.9.13 adds companion-section preview detection and handoff status without validating companion legality.
# Keep this file standalone until backend execution patches are intentionally made.

DRAGON_FORGE = {
    "name": "Dragon Forge", "mode": "dark", "bg": "#0b0908", "outer": "#100d0b",
    "sidebar": "#15100d", "sidebar_2": "#201712", "iron": "#1d1814", "iron_2": "#2a211a",
    "stone": "#252321", "leather": "#2b1d14", "bronze": "#6f4425",
    "parchment": "#ead7a9", "parchment_2": "#f4e4bd", "parchment_3": "#d6bd82",
    "paper_text": "#3a2818", "text": "#f4e8d4", "muted": "#bca892", "muted_2": "#8d7b68",
    "accent": "#e86a24", "accent_2": "#d9a441", "accent_3": "#ff9b4a",
    "danger": "#b64031", "success": "#7fc95d", "warning": "#f0c35a",
    "border": "#74401f", "border_soft": "#46301f", "input": "#120f0c", "input_border": "#6a4326",
    "panel_text": "#f4e8d4", "heading_text": "#d9a441", "section_heading_text": "#d9a441", "smallcaps_text": "#d9a441",
    "sidebar_text": "#f4e8d4", "sidebar_muted": "#bca892", "sidebar_hover_text": "#fff2d6",
    "sidebar_checked_text": "#100d0b", "sidebar_checked_start": "#e86a24", "sidebar_checked_end": "#d9a441",
    "button_text": "#f4e8d4", "button_pressed_text": "#0b0908",
    "primary_button_start": "#e86a24", "primary_button_end": "#d9a441",
    "input_text": "#f4e8d4", "progress_text": "#f4e8d4",
    "progress_track": "#120f0c", "progress_chunk_start": "#e86a24", "progress_chunk_end": "#d9a441",
    "combo_popup_bg": "#201712", "combo_popup_text": "#f4e8d4",
    "combo_popup_border": "#d9a441", "combo_popup_item_bg": "#201712",
    "combo_popup_selected_bg": "#e86a24", "combo_popup_selected_text": "#0b0908",
    "default_note_text": "#d9a441",
}

ADVENTURERS_MAP = {
    "name": "Adventurer's Map", "mode": "light", "bg": "#cdb789", "outer": "#dcc79a",
    "sidebar": "#8B6338", "sidebar_2": "#D6BD82", "iron": "#EAD8AB", "iron_2": "#DCC28E",
    "stone": "#C6AA73", "leather": "#7A4F2A", "bronze": "#B8872E",
    "parchment": "#F3E4BD", "parchment_2": "#FFF4D2", "parchment_3": "#D8BD7A",
    "paper_text": "#24180E", "text": "#24180E", "muted": "#5A3A1F", "muted_2": "#6F5738",
    "accent": "#2F5D73", "accent_2": "#B8872E", "accent_3": "#6F9FB0",
    "danger": "#8E2F24", "success": "#4F6F3A", "warning": "#8A4F13",
    "border": "#7A551F", "border_soft": "#A98445", "input": "#FFF8E6", "input_border": "#9B7434",
    "panel_text": "#24180E", "heading_text": "#7A4F1E", "section_heading_text": "#24180E", "smallcaps_text": "#24180E",
    "sidebar_text": "#24180E", "sidebar_muted": "#3A2818", "sidebar_hover_text": "#24180E",
    "sidebar_checked_text": "#FFF8E6", "sidebar_checked_start": "#2F5D73", "sidebar_checked_end": "#1F3E4D",
    "button_text": "#24180E", "button_pressed_text": "#FFF8E6",
    "primary_button_start": "#2F5D73", "primary_button_end": "#1F3E4D",
    "input_text": "#24180E", "progress_text": "#24180E",
    "progress_track": "#FFF8E6", "progress_chunk_start": "#2F5D73", "progress_chunk_end": "#B8872E",
    "combo_popup_bg": "#FFF8E6", "combo_popup_text": "#24180E",
    "combo_popup_border": "#7A551F", "combo_popup_item_bg": "#FFF8E6",
    "combo_popup_selected_bg": "#2F5D73", "combo_popup_selected_text": "#FFF8E6",
    "default_note_text": "#5A3A1F",
}


@dataclass
class AppState:
    theme: dict
    selected_philosophy: str = "Balanced / Unknown"
    philosophy_subtype: str = "None / top-level only"
    guide_presentation: str = "Either / random"
    deck_name: str = "No deck selected"
    commander: str = "No commander detected"
    deck_size: int = 0
    bracket: str = "Not estimated"
    warnings: int = 0
    status: str = "Auto-staged settings ready"
    selected_deck_path: str = "No deck file selected"
    deck_preview_text: str = "Choose a deck file to preview it here. The backend is still disconnected; this page only loads and summarizes the local file."
    deck_preview_note: str = "No deck file loaded yet."
    commander_detected: bool = False
    main_deck_count: int = 0
    commander_count: int = 0
    companion_name: str = "No companion detected"
    companion_detected: bool = False
    companion_count: int = 0
    output_mode: str = "Both"
    review_direction: str = "Cut down"
    cut_depth: str = "Normal"
    build_up_mode: str = "Finalize — 10 or fewer cards needed"
    prompt_mode: str = "Interactive AI chat"
    budget_note: str = "Optional budget note, e.g. $25/card"
    intended_bracket: str = "Not sure yet"
    respect_table_bracket: bool = False
    use_collection_settings: bool = False
    collection_mode: str = "No collection"
    collection_source_mode: str = "Entire collection folder"
    collection_folder: str = "collection"
    selected_collection_files: list[str] = field(default_factory=list)
    collection_txt_file_count: int = 0
    collection_source_note: str = "Collection source not staged yet."
    backend_entrypoint: str = "main.py"
    backend_working_directory: str = field(default_factory=lambda: str(Path.cwd()))
    guarded_run_in_progress: bool = False
    last_guarded_run_started_at: str = "Never"
    last_guarded_run_finished_at: str = "Never"
    last_guarded_run_status: str = "No guarded run attempted yet."
    last_guarded_run_return_code: str = "N/A"
    last_guarded_run_stdout: str = "No stdout captured yet."
    last_guarded_run_stderr: str = "No stderr captured yet."
    cli_input_bridge_enabled: bool = True
    cli_input_bridge_scope: str = "Full known CLI bridge: output mode, review direction, build-up/cut-down/auto-batch defaults, prompt mode, philosophy lens/subtype, guide presentation, collection mode, collection source, and conservative collection file-path handoff when selected files are staged"
    cli_input_bridge_last_sent: str = "No CLI input sent yet."
    last_output_files: list[str] = field(default_factory=list)
    last_normal_report_files: list[str] = field(default_factory=list)
    last_debug_report_files: list[str] = field(default_factory=list)
    last_output_folder: str = "Not detected"
    last_normal_report_folder: str = "Not detected"
    last_debug_report_folder: str = "Not detected"
    last_original_output_folder: str = "Not detected"
    last_backend_unique_output_status: str = "No backend unique output detection attempted yet."
    last_report_detection_status: str = "No guarded run report output detected yet."
    last_report_detection_mode: str = "not_attempted"
    last_report_detection_warning: str = "No report detection warning."
    report_viewer_current_file: str = "No report file selected"
    report_viewer_current_status: str = "No generated report loaded into the viewer yet."
    report_viewer_current_text: str = "Run the backend with guarded confirmation, then open Report Viewer to load detected report files here."


def add_shadow(widget, blur=30, x=0, y=10, color=None):
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(x, y)
    effect.setColor(color or QColor(0, 0, 0, 135))
    widget.setGraphicsEffect(effect)


class TexturedPanel(QFrame):
    """Painted panel using gradients, mottled texture dots, inset lines, glow, and corner accents."""

    def __init__(self, theme_getter, kind="iron", glow=False, parchment=False, corners=True, parent=None):
        super().__init__(parent)
        self.theme_getter = theme_getter
        self.kind = kind
        self.glow = glow
        self.parchment = parchment
        self.corners = corners
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName("texturedPanel")
        self.setProperty("parchmentPanel", "true" if parchment else "false")

    def paintEvent(self, event):
        t = self.theme_getter()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.6, 0.6, -0.6, -0.6)
        radius = 18
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        if self.parchment:
            base, alt, edge = QColor(t["parchment"]), QColor(t["parchment_2"]), QColor(t["parchment_3"])
        else:
            base, alt, edge = QColor(t.get(self.kind, t["iron"])), QColor(t["iron_2"]), QColor(t["border"])

        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        if self.parchment:
            grad.setColorAt(0.0, alt)
            grad.setColorAt(0.48, base)
            grad.setColorAt(1.0, edge)
        else:
            grad.setColorAt(0.0, alt.lighter(112 if t["mode"] == "dark" else 104))
            grad.setColorAt(0.42, base)
            grad.setColorAt(1.0, base.darker(128 if t["mode"] == "dark" else 106))
        painter.fillPath(path, grad)

        radial = QRadialGradient(rect.center(), max(rect.width(), rect.height()) * 0.76)
        glow_color = QColor(t["accent"] if not self.parchment else t["accent_2"])
        glow_color.setAlpha(58 if self.glow else 20)
        radial.setColorAt(0.0, glow_color)
        radial.setColorAt(0.72, QColor(0, 0, 0, 0))
        painter.fillPath(path, radial)

        painter.setClipPath(path)
        painter.setPen(Qt.NoPen)
        dot = QColor(95, 55, 23, 30) if self.parchment else QColor(255, 160, 74, 13)
        painter.setBrush(dot)
        w, h = max(1, self.width()), max(1, self.height())
        for i in range(135):
            x = (i * 37 + 23) % w
            y = (i * 71 + 41) % h
            if (x + y + i) % 4 == 0:
                painter.drawEllipse(QPointF(x, y), 1.0, 1.0)
            elif (x * 3 + y + i) % 11 == 0:
                painter.drawEllipse(QPointF(x, y), 1.7, 0.9)
        painter.setClipping(False)

        painter.setPen(QPen(QColor(t["border_soft"] if not self.parchment else "#b08b4d"), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect.adjusted(5, 5, -5, -5), radius - 5, radius - 5)

        if self.glow:
            painter.setPen(QPen(QColor(t["accent"]), 2.4))
            painter.drawRoundedRect(rect.adjusted(1.5, 1.5, -1.5, -1.5), radius, radius)

        painter.setPen(QPen(QColor(t["border"] if not self.parchment else "#8d6a32"), 1.2))
        painter.drawRoundedRect(rect, radius, radius)

        if self.corners:
            corner = QColor(t["accent_2"])
            corner.setAlpha(180)
            painter.setPen(QPen(corner, 1.5))
            inset, size = 10, 18
            painter.drawLine(QPointF(inset, inset + size), QPointF(inset, inset))
            painter.drawLine(QPointF(inset, inset), QPointF(inset + size, inset))
            painter.drawLine(QPointF(rect.width() - inset - size, inset), QPointF(rect.width() - inset, inset))
            painter.drawLine(QPointF(rect.width() - inset, inset), QPointF(rect.width() - inset, inset + size))
            painter.drawLine(QPointF(inset, rect.height() - inset - size), QPointF(inset, rect.height() - inset))
            painter.drawLine(QPointF(inset, rect.height() - inset), QPointF(inset + size, rect.height() - inset))
            painter.drawLine(QPointF(rect.width() - inset - size, rect.height() - inset), QPointF(rect.width() - inset, rect.height() - inset))
            painter.drawLine(QPointF(rect.width() - inset, rect.height() - inset - size), QPointF(rect.width() - inset, rect.height() - inset))

        super().paintEvent(event)


class ForgeOrb(QWidget):
    """Small animated forge/arcane symbol for the Run Review page."""

    def __init__(self, theme_getter, parent=None):
        super().__init__(parent)
        self.theme_getter = theme_getter
        self.angle = 0
        self.pulse = 0
        self.setMinimumSize(260, 260)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(45)

    def tick(self):
        self.angle = (self.angle + 4) % 360
        self.pulse = (self.pulse + 1) % 120
        self.update()

    def paintEvent(self, event):
        t = self.theme_getter()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(10, 10, -10, -10)
        center = rect.center()
        radius = min(rect.width(), rect.height()) / 2
        radial = QRadialGradient(center, radius)
        c = QColor(t["accent"])
        c.setAlpha(120)
        radial.setColorAt(0.0, c)
        radial.setColorAt(0.52, QColor(t["iron_2"]))
        radial.setColorAt(1.0, QColor(t["outer"]))
        painter.fillRect(self.rect(), radial)
        pulse = 1.0 + 0.06 * math.sin(self.pulse / 120 * math.tau)
        for r_mult, alpha in [(0.36, 210), (0.55, 130), (0.74, 75)]:
            pen_color = QColor(t["accent_2"])
            pen_color.setAlpha(alpha)
            painter.setPen(QPen(pen_color, 2))
            r = radius * r_mult * pulse
            painter.drawEllipse(center, r, r)
        painter.save()
        painter.translate(center)
        painter.rotate(self.angle)
        painter.setPen(QPen(QColor(t["accent"]), 2))
        for _ in range(8):
            painter.rotate(45)
            painter.drawLine(QPointF(0, -radius * 0.22), QPointF(0, -radius * 0.72))
        painter.restore()
        painter.setPen(QColor(t["accent_2"]))
        painter.setFont(QFont("Georgia", 42, QFont.Bold))
        painter.drawText(rect, Qt.AlignCenter, "🐉")


class SidebarButton(QPushButton):
    def __init__(self, text, index, parent=None):
        super().__init__(text, parent)
        self.index = index
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("sidebarButton")


class Badge(QLabel):
    def __init__(self, text, kind="normal", parent=None):
        super().__init__(text, parent)
        self.setObjectName(f"badge_{kind}")
        self.setAlignment(Qt.AlignCenter)


class ReportCard(TexturedPanel):
    def __init__(self, title, theme_getter, badges=None, parent=None):
        super().__init__(theme_getter, parchment=True, glow=False, corners=True, parent=parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)
        top = QHBoxLayout()
        title_lbl = QLabel(title)
        title_lbl.setObjectName("reportTitle")
        top.addWidget(title_lbl)
        top.addStretch(1)
        for b_text, b_kind in badges or []:
            top.addWidget(Badge(b_text, b_kind))
        layout.addLayout(top)
        line = QFrame()
        line.setObjectName("goldDivider")
        line.setFixedHeight(1)
        layout.addWidget(line)
        self.body = QVBoxLayout()
        self.body.setSpacing(8)
        layout.addLayout(self.body)


class SmallStat(TexturedPanel):
    def __init__(self, label, value, theme_getter, parent=None):
        super().__init__(theme_getter, kind="iron_2", glow=False, corners=False, parent=parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)
        self.label_label = QLabel(label)
        self.label_label.setObjectName("statLabel")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("statValue")
        layout.addWidget(self.label_label)
        layout.addWidget(self.value_label)


class PillButton(QPushButton):
    def __init__(self, text, checked=False, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("pillButton")


class MainWindow(QMainWindow):
    DECK_SELECTION, REVIEW_SETUP, PHILOSOPHY, RUN_ANALYSIS, REPORT, COLLECTION, BATCH_REPORTS, SETTINGS = range(8)

    # v0.6.7.1 shell aliases kept for low-risk page wiring during the first UI patch.
    DECK_INPUT = DECK_SELECTION
    ANALYSIS_SETUP = REVIEW_SETUP
    RUN_REVIEW = RUN_ANALYSIS
    COMBO = BATCH_REPORTS

    def __init__(self):
        super().__init__()
        self.state = AppState(theme=DRAGON_FORGE)
        self.nav_buttons = []
        self.progress_bars = []
        self.progress_tick = 0
        self.context_value_labels = {}
        self.theme_button = None
        self.settings_theme_buttons = []
        self.collection_mode_combo = None
        self.collection_source_combo = None
        self.collection_folder_button = None
        self.collection_files_button = None
        self.collection_preview_boxes = []
        self.run_config_preview_box = None
        self.runtime_mapping_preview_box = None
        self.backend_bridge_preview_box = None
        self.combo_tracker_preview_box = None
        self.guarded_execution_preview_box = None
        self.guarded_run_result_box = None
        self.report_output_preview_box = None
        self.report_viewer_file_buttons_layout = None
        self.report_viewer_text_box = None
        self.report_viewer_status_label = None
        self.open_current_report_file_button = None
        self.report_viewer_reload_button = None
        self.open_output_folder_button = None
        self.open_normal_report_folder_button = None
        self.open_debug_report_folder_button = None
        self.guarded_run_button = None
        self.guarded_run_buttons = []
        self.backend_process = None
        self.backend_process_stdout = ""
        self.backend_process_stderr = ""
        self.backend_process_timed_out = False
        self.guarded_cli_input_sent = False
        self.setWindowTitle(f"The Dragon's Touch — {APP_VERSION}")
        self.resize(1500, 930)
        self.setMinimumSize(1180, 760)
        self.root = QWidget()
        self.setCentralWidget(self.root)
        self.root_layout = QVBoxLayout(self.root)
        self.root_layout.setContentsMargins(16, 14, 16, 14)
        self.root_layout.setSpacing(12)
        self.stack = QStackedWidget()
        self.build_shell()
        self.apply_theme()
        self.go_to(self.DECK_SELECTION)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress_mock)
        self.timer.start(600)

    def theme(self):
        return self.state.theme

    def build_shell(self):
        self.build_header()
        app_body = QWidget()
        body_layout = QHBoxLayout(app_body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(12)
        body_layout.addWidget(self.build_sidebar())
        self.build_pages()
        body_layout.addWidget(self.stack, stretch=1)
        body_layout.addWidget(self.build_context_panel())
        self.root_layout.addWidget(app_body, stretch=1)
        self.build_footer()

    def rebuild_shell(self, page_index=None):
        page_index = self.stack.currentIndex() if page_index is None and self.stack else page_index
        while self.root_layout.count():
            item = self.root_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.nav_buttons = []
        self.progress_bars = []
        self.settings_theme_buttons = []
        self.collection_mode_combo = None
        self.collection_source_combo = None
        self.collection_folder_button = None
        self.collection_files_button = None
        self.collection_preview_boxes = []
        self.run_config_preview_box = None
        self.runtime_mapping_preview_box = None
        self.backend_bridge_preview_box = None
        self.combo_tracker_preview_box = None
        self.guarded_execution_preview_box = None
        self.guarded_run_result_box = None
        self.report_output_preview_box = None
        self.report_viewer_file_buttons_layout = None
        self.report_viewer_text_box = None
        self.report_viewer_status_label = None
        self.open_current_report_file_button = None
        self.report_viewer_reload_button = None
        self.open_output_folder_button = None
        self.open_normal_report_folder_button = None
        self.open_debug_report_folder_button = None
        self.guarded_run_button = None
        self.guarded_run_buttons = []
        self.backend_process = None
        self.backend_process_stdout = ""
        self.backend_process_stderr = ""
        self.backend_process_timed_out = False
        self.guarded_cli_input_sent = False
        self.stack = QStackedWidget()
        self.build_shell()
        self.apply_theme()
        self.go_to(page_index if page_index is not None else self.DECK_SELECTION)

    def build_header(self):
        header = TexturedPanel(self.theme, kind="outer", glow=True, corners=True)
        add_shadow(header, blur=32, y=8)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(22, 14, 22, 14)
        layout.setSpacing(18)
        mark = QLabel("🐉")
        mark.setObjectName("dragonMark")
        layout.addWidget(mark)
        title_box = QVBoxLayout()
        title = QLabel("THE DRAGON'S TOUCH")
        title.setObjectName("appTitle")
        tagline = QLabel(f"{APP_VERSION} — {APP_PHASE} • Locked backend: {LOCKED_BACKEND_VERSION}")
        tagline.setObjectName("tagline")
        title_box.addWidget(title)
        title_box.addWidget(tagline)
        layout.addLayout(title_box, stretch=1)
        theme_btn = QPushButton(f"Theme: {self.theme()['name']}")
        self.theme_button = theme_btn
        theme_btn.setObjectName("utilityButton")
        theme_btn.clicked.connect(self.toggle_theme)
        layout.addWidget(theme_btn)
        mascot = QLabel("☕🐲")
        mascot.setObjectName("mascotHeader")
        layout.addWidget(mascot)
        self.root_layout.addWidget(header)

    def build_footer(self):
        footer = TexturedPanel(self.theme, kind="outer", glow=False, corners=False)
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(14, 8, 14, 8)
        left = QLabel(f"The Dragon's Touch {APP_VERSION}  •  PySide6 Desktop UI Foundation  •  {BACKEND_STATUS}")
        left.setObjectName("footerText")
        right = QLabel("Fantasy frame, practical workflow. Analysis backend hooks come later.")
        right.setObjectName("footerText")
        layout.addWidget(left)
        layout.addStretch(1)
        layout.addWidget(right)
        self.root_layout.addWidget(footer)

    def build_sidebar(self):
        sidebar = TexturedPanel(self.theme, kind="sidebar", glow=False, corners=True)
        sidebar.setFixedWidth(270)
        add_shadow(sidebar, blur=25, y=8)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 18, 16, 18)
        layout.setSpacing(9)
        title = QLabel("FORGE NAVIGATION")
        title.setObjectName("sidebarSectionTitle")
        layout.addWidget(title)
        nav_items = [
            ("🃏  Deck Selection", self.DECK_SELECTION), ("⚙  Review Setup", self.REVIEW_SETUP),
            ("🧠  Philosophy Lens", self.PHILOSOPHY), ("🗃  Collection Source", self.COLLECTION),
            ("🔥  Run Analysis", self.RUN_ANALYSIS), ("📜  Report Viewer", self.REPORT),
            ("📚  Batch / Aggregate", self.BATCH_REPORTS), ("⚒  Settings", self.SETTINGS),
        ]
        group = QButtonGroup(self)
        group.setExclusive(True)
        for text, index in nav_items:
            btn = SidebarButton(text, index)
            btn.clicked.connect(lambda checked=False, idx=index: self.go_to(idx))
            group.addButton(btn)
            self.nav_buttons.append(btn)
            layout.addWidget(btn)
        layout.addSpacing(10)
        line = QFrame(); line.setObjectName("goldDivider"); line.setFixedHeight(1); layout.addWidget(line)
        quick = QLabel("QUICK ACTIONS"); quick.setObjectName("sidebarSectionTitle"); layout.addWidget(quick)
        for label in ["Save UI Session Placeholder", "Open Output Folder Later", "Export Placeholder"]:
            b = QPushButton(label); b.setObjectName("utilityButton"); b.clicked.connect(self.placeholder_message); layout.addWidget(b)
        layout.addStretch(1)
        dragon_note = TexturedPanel(self.theme, kind="iron_2", glow=True, corners=False)
        note_layout = QVBoxLayout(dragon_note); note_layout.setContentsMargins(12, 10, 12, 10)
        icon = QLabel("☕🐲"); icon.setObjectName("sidebarMascot"); icon.setAlignment(Qt.AlignCenter)
        txt = QLabel("The helper dragon watches the forge."); txt.setObjectName("mutedText"); txt.setWordWrap(True); txt.setAlignment(Qt.AlignCenter)
        note_layout.addWidget(icon); note_layout.addWidget(txt); layout.addWidget(dragon_note)
        return sidebar

    def build_context_panel(self):
        panel = TexturedPanel(self.theme, kind="iron", glow=False, corners=True)
        panel.setFixedWidth(310)
        add_shadow(panel, blur=25, y=8)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        title = QLabel("CURRENT DECK CONTEXT"); title.setObjectName("sidebarSectionTitle"); layout.addWidget(title)
        self.context_value_labels = {}
        for label, value in [
            ("Deck", self.state.deck_name), ("Commander", self.state.commander), ("Deck Size", f"{self.state.deck_size} cards"),
            ("Bracket Estimate", self.state.bracket), ("Warnings", f"{self.state.warnings} to review"), ("Status", self.state.status),
        ]:
            stat = SmallStat(label, value, self.theme)
            self.context_value_labels[label] = stat.value_label
            layout.addWidget(stat)
        line = QFrame(); line.setObjectName("goldDivider"); line.setFixedHeight(1); layout.addWidget(line)
        notes_title = QLabel("QUICK NOTES"); notes_title.setObjectName("sidebarSectionTitle"); layout.addWidget(notes_title)
        notes = QLabel("• Mock data only\n• Report viewer is the design priority\n• Backend will connect later\n• Responsible API behavior planned")
        notes.setObjectName("mutedText"); notes.setWordWrap(True); layout.addWidget(notes)
        layout.addStretch(1)
        mascot = TexturedPanel(self.theme, kind="iron_2", glow=True, corners=False)
        mascot_layout = QVBoxLayout(mascot); mascot_layout.setContentsMargins(12, 12, 12, 12)
        dragon = QLabel("☕🐲"); dragon.setObjectName("contextMascot"); dragon.setAlignment(Qt.AlignCenter)
        text = QLabel("Ready to guide a deck through the locked v0.6.6 workflow once backend hooks are connected."); text.setObjectName("mutedText"); text.setWordWrap(True); text.setAlignment(Qt.AlignCenter)
        mascot_layout.addWidget(dragon); mascot_layout.addWidget(text); layout.addWidget(mascot)
        return panel

    def build_pages(self):
        self.stack.addWidget(self.page_deck_input())
        self.stack.addWidget(self.page_analysis_setup())
        self.stack.addWidget(self.page_philosophy())
        self.stack.addWidget(self.page_run_review())
        self.stack.addWidget(self.page_report_viewer())
        self.stack.addWidget(self.page_collection_tools())
        self.stack.addWidget(self.page_batch_reports())
        self.stack.addWidget(self.page_settings())

    def apply_theme(self):
        self.root.setStyleSheet(self.qss(self.theme()))

    def configure_combo_popup(self, combo):
        """Give combo popups a fully themed QListView so light-mode menus avoid native dark frame bands."""
        t = self.theme()
        input_text = t.get("input_text", t["text"])
        button_pressed_text = t.get("button_pressed_text", t["bg"])
        combo_popup_bg = t.get("combo_popup_bg", t["iron_2"])
        combo_popup_text = t.get("combo_popup_text", input_text)
        combo_popup_border = t.get("combo_popup_border", t["border"])
        combo_popup_item_bg = t.get("combo_popup_item_bg", combo_popup_bg)
        combo_popup_selected_bg = t.get("combo_popup_selected_bg", t["accent"])
        combo_popup_selected_text = t.get("combo_popup_selected_text", button_pressed_text)

        view = QListView(combo)
        view.setObjectName("comboPopupView")
        view.setFrameShape(QFrame.NoFrame)
        view.setLineWidth(0)
        view.setUniformItemSizes(True)
        view.setSpacing(0)
        view.setAutoFillBackground(True)
        view.viewport().setAutoFillBackground(True)
        popup_style = f"""
            QListView#comboPopupView {{
                color: {combo_popup_text};
                background-color: {combo_popup_bg};
                border: 1px solid {combo_popup_border};
                outline: 0;
                padding: 0px;
                margin: 0px;
                selection-background-color: {combo_popup_selected_bg};
                selection-color: {combo_popup_selected_text};
            }}
            QListView#comboPopupView::item {{
                min-height: 28px;
                padding: 6px 10px;
                color: {combo_popup_text};
                background-color: {combo_popup_item_bg};
                border: 0px;
            }}
            QListView#comboPopupView::item:selected,
            QListView#comboPopupView::item:hover {{
                color: {combo_popup_selected_text};
                background-color: {combo_popup_selected_bg};
            }}
        """
        view.setStyleSheet(popup_style)
        view.viewport().setStyleSheet(f"background-color: {combo_popup_bg}; border: 0px; margin: 0px; padding: 0px;")
        combo.setView(view)
        combo.setMaxVisibleItems(10)

    def toggle_theme(self):
        self.state.theme = ADVENTURERS_MAP if self.theme()["name"] == "Dragon Forge" else DRAGON_FORGE
        self.refresh_theme_in_place()

    def set_theme(self, theme):
        self.state.theme = theme
        self.refresh_theme_in_place()

    def refresh_theme_in_place(self):
        """Apply theme changes without rebuilding the shell, preventing transient popup flashes."""
        self.apply_theme()
        if self.theme_button is not None:
            self.theme_button.setText(f"Theme: {self.theme()['name']}")
        for button, theme_name in self.settings_theme_buttons:
            button.setObjectName("primaryButton" if self.theme()["name"] == theme_name else "utilityButton")
            button.style().unpolish(button)
            button.style().polish(button)
        for combo in self.findChildren(QComboBox):
            self.configure_combo_popup(combo)
        self.refresh_context_panel_values()
        self.root.update()

    def qss(self, t):
        panel_text = t.get("panel_text", t["text"])
        heading_text = t.get("heading_text", t["accent_2"])
        section_heading_text = t.get("section_heading_text", t["accent_2"])
        smallcaps_text = t.get("smallcaps_text", t["accent_2"])
        sidebar_text = t.get("sidebar_text", t["text"])
        sidebar_muted = t.get("sidebar_muted", t["muted"])
        sidebar_hover_text = t.get("sidebar_hover_text", t["text"])
        sidebar_checked_text = t.get("sidebar_checked_text", t["bg"])
        sidebar_checked_start = t.get("sidebar_checked_start", t["accent"])
        sidebar_checked_end = t.get("sidebar_checked_end", t["accent_2"])
        button_text = t.get("button_text", t["text"])
        button_pressed_text = t.get("button_pressed_text", t["bg"])
        primary_start = t.get("primary_button_start", t["accent"])
        primary_end = t.get("primary_button_end", t["accent_2"])
        input_text = t.get("input_text", t["text"])
        progress_text = t.get("progress_text", t["text"])
        progress_track = t.get("progress_track", t["input"])
        progress_start = t.get("progress_chunk_start", t["accent"])
        progress_end = t.get("progress_chunk_end", t["accent_2"])
        combo_popup_bg = t.get("combo_popup_bg", t["iron_2"])
        combo_popup_text = t.get("combo_popup_text", input_text)
        combo_popup_border = t.get("combo_popup_border", t["border"])
        combo_popup_item_bg = t.get("combo_popup_item_bg", combo_popup_bg)
        combo_popup_selected_bg = t.get("combo_popup_selected_bg", t["accent"])
        combo_popup_selected_text = t.get("combo_popup_selected_text", button_pressed_text)
        default_note_text = t.get("default_note_text", t["muted"])
        return f'''
        QWidget {{ color: {panel_text}; font-family: "Segoe UI", "Arial", sans-serif; font-size: 14px; background: transparent; }}
        QMainWindow {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {t["bg"]}, stop:0.55 {t["outer"]}, stop:1 {t["leather"]}); }}
        QFrame[parchmentPanel="true"] QLabel {{ color: {t["paper_text"]}; }}
        QFrame[parchmentPanel="true"] QCheckBox {{ color: {t["paper_text"]}; }}
        QLabel#dragonMark {{ font-size: 42px; }} QLabel#appTitle {{ font-family: Georgia, serif; font-size: 34px; font-weight: 800; letter-spacing: 2px; color: {t["text"]}; }}
        QLabel#tagline {{ font-family: Georgia, serif; font-size: 14px; font-style: italic; color: {t["accent_2"]}; }}
        QLabel#pageTitle {{ font-family: Georgia, serif; font-size: 30px; font-weight: 800; color: {heading_text}; }}
        QLabel#sectionTitle {{ font-family: Georgia, serif; font-size: 19px; font-weight: 800; color: {section_heading_text}; }}
        QLabel#smallCaps {{ font-family: Georgia, serif; color: {smallcaps_text}; font-size: 12px; font-weight: 800; letter-spacing: 1.2px; }}
        QLabel#sidebarSectionTitle {{ font-family: Georgia, serif; color: {smallcaps_text}; font-size: 12px; font-weight: 900; letter-spacing: 1.2px; }}
        QLabel#mutedText, QLabel#helperText {{ color: {t["muted"]}; line-height: 1.4; }} QLabel#footerText {{ color: {t["muted_2"]}; font-size: 12px; }}
        QLabel#mascotHeader {{ font-size: 32px; }} QLabel#sidebarMascot {{ font-size: 36px; }} QLabel#contextMascot {{ font-size: 42px; }}
        QLabel#statLabel {{ color: {t["muted"]}; font-size: 11px; font-weight: 700; }} QLabel#statValue {{ color: {t["text"]}; font-size: 14px; font-weight: 700; }}
        QLabel#reportTitle {{ color: {t["paper_text"]}; font-family: Georgia, serif; font-size: 22px; font-weight: 900; }} QLabel#reportBody {{ color: {t["paper_text"]}; font-size: 14px; line-height: 1.5; }}
        QLabel#warningText {{ color: {t["warning"]}; font-weight: 700; }}
        QLabel#defaultNote {{ color: {default_note_text}; font-size: 12px; font-weight: 700; padding-left: 2px; }}
        QLabel#philosophySubtype {{ color: {t["paper_text"]}; font-size: 13px; font-weight: 900; padding-left: 2px; }}
        QPushButton {{ border-radius: 12px; border: 1px solid {t["border"]}; padding: 10px 14px; color: {button_text}; font-weight: 800; background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {t["iron_2"]}, stop:1 {t["bronze"]}); }}
        QPushButton:hover {{ color: {sidebar_hover_text}; border: 1px solid {t["accent_2"]}; background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {t["bronze"]}, stop:1 {t["iron_2"]}); }}
        QPushButton:pressed {{ background: {primary_start}; color: {button_pressed_text}; }} QPushButton#primaryButton {{ color: {sidebar_checked_text}; border: 1px solid {t["accent_2"]}; background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {primary_start}, stop:1 {primary_end}); font-weight: 900; }}
        QPushButton#utilityButton {{ padding: 8px 12px; font-size: 13px; color: {button_text}; }} QPushButton#sidebarButton {{ text-align: left; border-radius: 13px; padding: 12px 13px; color: {sidebar_text}; background: transparent; border: 1px solid transparent; font-weight: 800; }}
        QPushButton#sidebarButton:hover {{ color: {sidebar_hover_text}; background: {t["sidebar_2"]}; border: 1px solid {t["accent_2"]}; }} QPushButton#sidebarButton:checked {{ color: {sidebar_checked_text}; background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {sidebar_checked_start}, stop:1 {sidebar_checked_end}); border: 1px solid {t["accent_2"]}; font-weight: 900; }}
        QPushButton#pillButton {{ border-radius: 15px; padding: 7px 12px; color: {sidebar_muted}; background: {t["iron_2"]}; border: 1px solid {t["border_soft"]}; }} QPushButton#pillButton:checked {{ color: {sidebar_checked_text}; background: {sidebar_checked_start}; border: 1px solid {t["accent_2"]}; }}
        QLineEdit, QPlainTextEdit, QComboBox {{ color: {input_text}; background: {t["input"]}; border: 1px solid {t["input_border"]}; border-radius: 12px; padding: 10px; selection-background-color: {t["accent"]}; selection-color: {button_pressed_text}; combobox-popup: 0; }}
        QPlainTextEdit#reportStatusPreview {{ color: {t["paper_text"]}; background: transparent; border: 0px; border-radius: 0px; padding: 4px; selection-background-color: {t["accent_2"]}; selection-color: {t["paper_text"]}; }}
        QPlainTextEdit#reportStatusPreview QScrollBar:vertical {{ background: transparent; width: 10px; border-radius: 5px; }}
        QPlainTextEdit#reportStatusPreview QScrollBar::handle:vertical {{ background: {t["border_soft"]}; border-radius: 5px; min-height: 24px; }}
        QComboBox::drop-down {{ border: none; width: 28px; }}
        QComboBox QAbstractItemView {{ color: {combo_popup_text}; background-color: {combo_popup_bg}; border: 1px solid {combo_popup_border}; selection-background-color: {combo_popup_selected_bg}; selection-color: {combo_popup_selected_text}; outline: 0; padding: 0px; margin: 0px; }}
        QComboBox QAbstractItemView::item {{ min-height: 28px; padding: 6px 10px; color: {combo_popup_text}; background-color: {combo_popup_item_bg}; }}
        QComboBox QAbstractItemView::item:selected {{ color: {combo_popup_selected_text}; background-color: {combo_popup_selected_bg}; }}
        QComboBox QAbstractItemView::item:hover {{ color: {combo_popup_selected_text}; background-color: {combo_popup_selected_bg}; }}
        QCheckBox {{ spacing: 8px; color: {panel_text}; }} QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 5px; border: 1px solid {t["border"]}; background: {t["input"]}; }} QCheckBox::indicator:checked {{ background: {t["accent"]}; border: 1px solid {t["accent_2"]}; }}
        QProgressBar {{ border: 1px solid {t["border"]}; border-radius: 8px; background: {progress_track}; height: 15px; text-align: center; color: {progress_text}; font-weight: 800; font-size: 10px; }} QProgressBar::chunk {{ border-radius: 7px; background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {progress_start}, stop:1 {progress_end}); }}
        QSlider::groove:horizontal {{ height: 8px; border-radius: 4px; background: {t["input"]}; border: 1px solid {t["border"]}; }} QSlider::handle:horizontal {{ width: 18px; margin: -6px 0; border-radius: 9px; background: {t["accent_2"]}; border: 1px solid {t["accent"]}; }}
        QScrollArea {{ border: none; background: transparent; }} QScrollBar:vertical {{ background: {t["iron"]}; width: 12px; border-radius: 6px; }} QScrollBar::handle:vertical {{ background: {t["border"]}; border-radius: 6px; min-height: 30px; }} QScrollBar::handle:vertical:hover {{ background: {t["accent"]}; }}
        QFrame#goldDivider {{ background: {t["accent_2"]}; max-height: 1px; }}
        QLabel#badge_normal, QLabel#badge_primary, QLabel#badge_protected, QLabel#badge_manual, QLabel#badge_medium, QLabel#badge_high {{ color: {t["paper_text"]}; border-radius: 10px; padding: 4px 8px; font-size: 11px; font-weight: 800; border: 1px solid #8a6838; }}
        QLabel#badge_normal {{ background: #ead196; }} QLabel#badge_primary {{ background: #d8a642; }} QLabel#badge_protected {{ background: #92b36e; }} QLabel#badge_manual {{ background: #c8a25b; }} QLabel#badge_medium {{ background: #e3ba63; }} QLabel#badge_high {{ background: #a7c47a; }}
        '''

    def go_to(self, index):
        self.stack.setCurrentIndex(index)
        for btn in self.nav_buttons:
            btn.setChecked(btn.index == index)
        if index == self.RUN_ANALYSIS:
            self.refresh_run_analysis_previews()
        if index == self.REPORT:
            self.refresh_report_viewer_file_list()

    def refresh_run_analysis_previews(self):
        """Refresh Run Analysis preview text from current staged UI state without rebuilding pages."""
        if self.run_config_preview_box is not None:
            self.run_config_preview_box.setPlainText(self.run_config_preview_text())
        if self.runtime_mapping_preview_box is not None:
            self.runtime_mapping_preview_box.setPlainText(self.backend_runtime_config_mapping_text())
        if self.backend_bridge_preview_box is not None:
            self.backend_bridge_preview_box.setPlainText(self.backend_bridge_preview_text())
        if self.combo_tracker_preview_box is not None:
            self.combo_tracker_preview_box.setPlainText(self.combo_tracker_preview_text())
        if self.guarded_execution_preview_box is not None:
            self.guarded_execution_preview_box.setPlainText(self.guarded_execution_preview_text())
        if self.guarded_run_result_box is not None:
            self.guarded_run_result_box.setPlainText(self.guarded_run_result_text())
        if self.report_output_preview_box is not None:
            self.report_output_preview_box.setPlainText(self.report_output_summary_text())
        self.refresh_report_output_buttons()
        self.refresh_report_viewer_file_list()
        guarded_buttons = list(getattr(self, "guarded_run_buttons", []))
        if self.guarded_run_button is not None and self.guarded_run_button not in guarded_buttons:
            guarded_buttons.append(self.guarded_run_button)
        for button in guarded_buttons:
            button.setEnabled(not self.state.guarded_run_in_progress)
            button.setText("Running main.py..." if self.state.guarded_run_in_progress else "Run main.py with Guarded Confirmation")

    def refresh_context_panel_values(self):
        """Refresh right-side context values without rebuilding the whole shell."""
        values = {
            "Deck": self.state.deck_name,
            "Commander": self.state.commander,
            "Deck Size": f"{self.state.deck_size} cards",
            "Bracket Estimate": self.state.bracket,
            "Warnings": f"{self.state.warnings} to review",
            "Status": self.state.status,
        }
        for key, value in values.items():
            label = self.context_value_labels.get(key)
            if label is not None:
                label.setText(value)

    def rebuild_then_message(self, page_index, title, message):
        """Update the visible UI first, then show the confirmation popup after the redraw begins."""
        self.rebuild_shell(page_index)
        QTimer.singleShot(90, lambda: QMessageBox.information(self, title, message))

    def placeholder_message(self):
        QMessageBox.information(
            self,
            "UI Foundation Placeholder",
            f"This control is part of {APP_VERSION}. The desktop shell is active, but backend integration is intentionally reserved for later v0.6.7 patches."
        )

    def backend_hook_message(self, hook_name):
        QMessageBox.information(
            self,
            "Backend Hook Placeholder",
            f"{hook_name} is reserved for a later v0.6.7 backend integration patch. The locked {LOCKED_BACKEND_VERSION} command-line backend remains unchanged."
        )

    def page_header(self, title, subtitle):
        panel = TexturedPanel(self.theme, kind="iron", glow=True, corners=True)
        add_shadow(panel, blur=24, y=8)
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(22, 18, 22, 18)
        text_box = QVBoxLayout()
        ttl = QLabel(title); ttl.setObjectName("pageTitle")
        sub = QLabel(subtitle); sub.setObjectName("helperText"); sub.setWordWrap(True)
        text_box.addWidget(ttl); text_box.addWidget(sub)
        layout.addLayout(text_box, stretch=1)
        mascot = QLabel("☕🐲"); mascot.setObjectName("mascotHeader"); layout.addWidget(mascot)
        return panel

    def page_container(self, title, subtitle):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(self.page_header(title, subtitle))
        return page, layout

    def scroll_content(self):
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        inner = QWidget(); layout = QVBoxLayout(inner); layout.setContentsMargins(4, 4, 12, 4); layout.setSpacing(14)
        scroll.setWidget(inner)
        return scroll, layout

    def make_text(self, text, paper=False):
        lbl = QLabel(text); lbl.setWordWrap(True); lbl.setObjectName("reportBody" if paper else "helperText"); return lbl

    def default_note(self, text):
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setObjectName("defaultNote")
        return lbl

    def readonly_text_box(self, text, min_height=118, max_height=170):
        """Scrollable read-only text block for dense preview/summary text inside cards."""
        box = QPlainTextEdit()
        box.setPlainText(text)
        box.setReadOnly(True)
        box.setMinimumHeight(min_height)
        box.setMaximumHeight(max_height)
        box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        box.setFrameShape(QFrame.NoFrame)
        return box

    def page_deck_input(self):
        page, layout = self.page_container(
            "Deck Selection",
            f"Choose a local deck file and preview it safely. {APP_VERSION} does not run analysis yet; backend hooks come later."
        )
        body = TexturedPanel(self.theme, kind="iron", glow=False); add_shadow(body, blur=26, y=8)
        body_layout = QHBoxLayout(body); body_layout.setContentsMargins(22, 22, 22, 22); body_layout.setSpacing(16)

        left = TexturedPanel(self.theme, parchment=True)
        left_layout = QVBoxLayout(left); left_layout.setContentsMargins(20, 18, 20, 18); left_layout.setSpacing(12)
        title = QLabel("Deck File & Commander Preview"); title.setObjectName("reportTitle"); left_layout.addWidget(title)

        file_path = QLineEdit(self.state.selected_deck_path)
        file_path.setReadOnly(True)
        deck_name = QLineEdit(self.state.deck_name)
        deck_name.setReadOnly(True)
        commander = QLineEdit(self.state.commander)
        commander.setReadOnly(True)
        decklist = QPlainTextEdit()
        decklist.setPlainText(self.state.deck_preview_text)
        # Keep the preview scrollable but deliberately short enough that the
        # action-button row always lives below it instead of visually sitting on top.
        # The backend parser remains the source of truth later; this is only a UI preview.
        decklist.setMinimumHeight(175)
        decklist.setMaximumHeight(195)
        decklist.setFixedHeight(185)
        decklist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        decklist.setReadOnly(True)

        for label, widget in [
            ("Selected Deck File", file_path),
            ("Deck Name", deck_name),
            ("Commander Name", commander),
            ("Decklist Preview", decklist),
        ]:
            left_layout.addWidget(QLabel(label))
            left_layout.addWidget(widget, stretch=0)

        # Keep the preview box from consuming the button row area at normal window sizes.
        # The preview remains scrollable, but the action buttons always get their own
        # separate row with a visible parchment gap above it.
        left_layout.addSpacing(18)
        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 8, 0, 0)
        button_row.setSpacing(12)
        choose_btn = QPushButton("Choose Deck File")
        choose_btn.clicked.connect(self.choose_deck_file)
        preview_btn = QPushButton("Reload Preview")
        preview_btn.clicked.connect(self.reload_selected_deck_preview)
        paste_btn = QPushButton("Paste Decklist Later")
        paste_btn.clicked.connect(lambda: self.backend_hook_message("Paste/import decklist"))
        for b in [choose_btn, preview_btn, paste_btn]:
            b.setMinimumHeight(44)
            button_row.addWidget(b)
        left_layout.addLayout(button_row, stretch=0)
        left_layout.addStretch(1)

        right = QVBoxLayout(); right.setSpacing(14)
        status = TexturedPanel(self.theme, kind="iron_2", glow=True); status_layout = QVBoxLayout(status); status_layout.setContentsMargins(18, 16, 18, 16)
        cap = QLabel("FILE PREVIEW STATUS"); cap.setObjectName("smallCaps"); status_layout.addWidget(cap)
        status_layout.addWidget(self.make_text(self.deck_preview_status_text()))
        p = QProgressBar(); p.setValue(100 if self.state.selected_deck_path != "No deck file selected" else 0); status_layout.addWidget(p)
        quick = ReportCard("Forge Note", self.theme)
        quick.body.addWidget(self.make_text(
            f"{APP_VERSION} keeps real local deck-file selection, keeps a clear gap between the deck preview and action buttons, and stages Review Setup choices for later backend mapping. It does not call the analysis engine, Scryfall lookup, legality system, collection loader, or report generator yet.",
            paper=True
        ))
        right.addWidget(status); right.addWidget(quick); right.addStretch(1)
        body_layout.addWidget(left, stretch=2); body_layout.addLayout(right, stretch=1)
        layout.addWidget(body, stretch=1); return page

    def default_deck_folder(self):
        """Return a sensible starting folder for deck-file selection without requiring project config."""
        candidates = [
            Path.cwd() / "Decklists",
            Path.cwd() / "decklists",
            Path.cwd(),
            Path.home() / "Desktop",
            Path.home(),
        ]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        return str(Path.home())

    def choose_deck_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Dragon's Touch Deck File",
            self.default_deck_folder(),
            "Deck files (*.txt *.deck *.dec *.csv);;Text files (*.txt);;CSV files (*.csv);;All files (*)"
        )
        if path:
            self.load_deck_file_preview(path)

    def reload_selected_deck_preview(self):
        if self.state.selected_deck_path == "No deck file selected":
            self.placeholder_message()
            return
        self.load_deck_file_preview(self.state.selected_deck_path)

    def load_deck_file_preview(self, path):
        try:
            text = Path(path).read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            try:
                text = Path(path).read_text(encoding="cp1252")
            except Exception as exc:
                QMessageBox.warning(self, "Deck Preview Failed", f"Could not read deck file:\n{path}\n\n{exc}")
                return
        except Exception as exc:
            QMessageBox.warning(self, "Deck Preview Failed", f"Could not read deck file:\n{path}\n\n{exc}")
            return

        summary = self.summarize_deck_preview(text, Path(path).stem)
        self.state.selected_deck_path = path
        self.state.deck_preview_text = text[:12000] + ("\n\n... preview truncated for UI responsiveness ..." if len(text) > 12000 else "")
        self.state.deck_name = summary["deck_name"]
        self.state.commander = summary["commander"]
        self.state.commander_detected = summary["commander_detected"]
        self.state.deck_size = summary["deck_size"]
        self.state.main_deck_count = summary.get("main_deck_count", summary["deck_size"])
        self.state.commander_count = summary.get("commander_count", 1 if summary["commander_detected"] else 0)
        self.state.companion_name = summary.get("companion_name", "No companion detected")
        self.state.companion_detected = summary.get("companion_detected", False)
        self.state.companion_count = summary.get("companion_count", 0)
        self.state.warnings = summary["warnings"]
        self.state.status = "Deck preview loaded"
        self.state.deck_preview_note = summary["note"]
        self.rebuild_shell(self.DECK_SELECTION)

    def summarize_deck_preview(self, text, fallback_name):
        """Lightweight UI preview only. The locked backend remains the source of truth.

        v0.6.7.9.13 keeps the commander-counting preview and also detects
        Companion sections as a separate auxiliary zone. This is not legality
        validation; companion restrictions remain a backend concern.
        """
        section = "main"
        commander_names = []
        companion_names = []
        main_count = 0
        warnings = 0
        ignored_sections = {"sideboard", "maybeboard", "tokens", "token", "attractions", "stickers", "reference", "references"}
        commander_sections = {"commander", "commanders", "command zone", "command-zone"}
        companion_sections = {"companion", "companions"}

        for raw in text.splitlines():
            line = raw.strip()
            if not line or line.startswith(("#", "//")):
                continue
            cleaned = line.rstrip(":").strip()
            lower = cleaned.lower()
            if not any(ch.isdigit() for ch in cleaned) and len(cleaned.split()) <= 5:
                section = lower
                continue

            qty, name = self.parse_deck_line(line)
            if not name:
                continue
            section_key = section.lower()
            if section_key in commander_sections:
                for _ in range(max(1, qty)):
                    commander_names.append(name)
                continue
            if section_key in companion_sections:
                for _ in range(max(1, qty)):
                    companion_names.append(name)
                continue
            if section_key in ignored_sections:
                continue
            main_count += qty

        commander_count = len(commander_names)
        commander_detected = commander_count > 0
        if commander_detected:
            deduped_commanders = []
            for name in commander_names:
                if name not in deduped_commanders:
                    deduped_commanders.append(name)
            commander = " / ".join(deduped_commanders)
        else:
            commander = "No commander detected"

        companion_count = len(companion_names)
        companion_detected = companion_count > 0
        if companion_detected:
            deduped_companions = []
            for name in companion_names:
                if name not in deduped_companions:
                    deduped_companions.append(name)
            companion_name = " / ".join(deduped_companions)
        else:
            companion_name = "No companion detected"

        # Companion cards are previewed as an auxiliary/sideboard-style zone and
        # are not included in the 100-card Commander deck estimate.
        total_count = main_count + commander_count

        if main_count == 0:
            warnings += 1
        if total_count and total_count != 100:
            warnings += 1
        if not commander_detected:
            warnings += 1

        companion_note = f" Companion detected separately: {companion_name}. Backend validates companion restriction." if companion_detected else ""
        if total_count == 100 and commander_detected:
            note = f"Preview loaded. Estimate: {main_count} main-deck card(s) + {commander_count} commander card(s) = 100 total.{companion_note} Backend validation still required."
        elif main_count == 0:
            note = "Preview loaded, but no counted card lines were detected by the lightweight UI preview. Backend parser may still handle this format later."
        else:
            note = f"Preview loaded. Estimate: {main_count} main-deck card(s) + {commander_count} commander card(s) = {total_count} total.{companion_note} Backend validation still required."

        return {
            "deck_name": fallback_name,
            "commander": commander,
            "commander_detected": commander_detected,
            "deck_size": total_count,
            "main_deck_count": main_count,
            "commander_count": commander_count,
            "companion_name": companion_name,
            "companion_detected": companion_detected,
            "companion_count": companion_count,
            "warnings": warnings,
            "note": note,
        }

    def parse_deck_line(self, line):
        if not line:
            return 0, ""
        line = line.strip().lstrip("-•*").strip()
        parts = line.split(maxsplit=1)
        if len(parts) >= 2 and parts[0].isdigit():
            qty = int(parts[0])
            name = parts[1].split("//", 1)[0].strip() if parts[1].startswith("//") else parts[1].strip()
            # Keep double-faced card names intact; only remove common export set/collector suffixes.
            for marker in [" [", " (", "\t"]:
                if marker in name:
                    name = name.split(marker, 1)[0].strip()
            return max(0, qty), name
        return 0, ""

    def deck_preview_status_text(self):
        commander_status = "Yes" if self.state.commander_detected else "No"
        return (
            f"Selected file: {Path(self.state.selected_deck_path).name if self.state.selected_deck_path != 'No deck file selected' else 'None'}\n"
            f"Main-deck estimate: {self.state.main_deck_count} card(s)\n"
            f"Commander card estimate: {self.state.commander_count} card(s)\n"
            f"Total Commander deck estimate: {self.state.deck_size} card(s)\n"
            f"Commander section detected: {commander_status}\n"
            f"Companion detected: {'Yes' if self.state.companion_detected else 'No'}\n"
            f"Companion preview: {self.state.companion_name} ({self.state.companion_count} card(s))\n"
            f"Companion legality: Backend validation required\n"
            f"Backend validation: Not run\n"
            f"Note: {self.state.deck_preview_note}"
        )

    def review_focus_text(self):
        if self.state.review_direction == "Build up":
            return "Additions, role gaps, and upgrade paths"
        if self.state.review_direction == "Auto batch":
            return "Batch-safe review using staged defaults"
        return "Cuts, replaceability, and optimization pressure"

    def review_intensity_meaning(self):
        meanings_cut = {
            "Light": "Light pass: safest review, flags only obvious concerns.",
            "Normal": "Normal pass: balanced review of synergy, curve, role balance, and likely cuts.",
            "Strict": "Strict pass: higher cut pressure and closer scrutiny of low-impact or redundant cards.",
            "Brutal / Deep Review": "Deep review: aggressive scrutiny for major refinement, still protecting core/pet constraints.",
            "Rebuild": "Rebuild lens: assumes major restructuring may be needed while preserving stated deck identity.",
        }
        meanings_build = {
            "Light": "Light build-up: suggest only obvious support additions and missing essentials.",
            "Normal": "Normal build-up: identify role gaps, synergy upgrades, and practical additions.",
            "Strict": "Strict build-up: prioritize stronger additions and clearer role upgrades over loose maybes.",
            "Brutal / Deep Review": "Deep build-up: map larger upgrade packages and structural improvements.",
            "Rebuild": "Rebuild lens: propose a broader reconstruction path around the stated commander plan.",
        }
        if self.state.review_direction == "Build up":
            return meanings_build.get(self.state.cut_depth, meanings_build["Normal"])
        return meanings_cut.get(self.state.cut_depth, meanings_cut["Normal"])

    def review_settings_summary_text(self):
        return (
            f"Output mode: {self.state.output_mode}\n"
            f"Review direction: {self.state.review_direction}\n"
            f"Review focus: {self.review_focus_text()}\n"
            f"Review intensity: {self.state.cut_depth}\n"
            f"Intensity meaning: {self.review_intensity_meaning()}\n"
            f"Build-up mode: {self.state.build_up_mode}\n"
            f"Prompt mode: {self.state.prompt_mode}\n"
            f"Budget note: {self.state.budget_note}\n"
            f"Intended bracket: {self.state.intended_bracket}\n"
            f"Collection mode: {self.state.collection_mode}\n"
            f"Collection source: {self.state.collection_source_mode}\n"
            "Backend config mapping: staged by guarded bridge when run is confirmed"
        )

    def stage_review_settings(self, output_combo, direction_combo, cut_combo, build_up_combo, prompt_combo, budget_input, intended_bracket_combo, summary_label=None, intensity_meaning_label=None):
        """Auto-stage Review Setup choices without requiring an Apply button or popup."""
        self.state.output_mode = output_combo.currentText()
        self.state.review_direction = direction_combo.currentText()
        self.state.cut_depth = cut_combo.currentText()
        self.state.build_up_mode = build_up_combo.currentText()
        self.state.prompt_mode = prompt_combo.currentText()
        self.state.budget_note = budget_input.text().strip() or "No budget note provided"
        self.state.intended_bracket = intended_bracket_combo.currentText()
        self.state.bracket = self.state.intended_bracket if self.state.intended_bracket != "Not sure yet" else "Not estimated"
        self.state.status = "Review settings auto-staged"
        if summary_label is not None:
            summary_label.setText(self.review_settings_summary_text())
        if intensity_meaning_label is not None:
            intensity_meaning_label.setText(self.review_intensity_meaning())
        self.refresh_context_panel_values()
        self.refresh_run_analysis_previews()

    def page_analysis_setup(self):
        page, layout = self.page_container(
            "Review Setup",
            f"Stage the same review choices the CLI already supports. {APP_VERSION} auto-stages choices as you change them; backend mapping still comes later."
        )
        scroll, content = self.scroll_content()
        grid_panel = TexturedPanel(self.theme, kind="iron", glow=False); add_shadow(grid_panel, blur=24, y=8)
        grid = QGridLayout(grid_panel); grid.setContentsMargins(22, 22, 22, 22); grid.setSpacing(16)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        output_card = ReportCard("Output Mode", self.theme)
        output_combo = QComboBox(); output_combo.addItems(["Normal User Mode", "Debug / Stress-Test Mode", "Both"]); output_combo.setCurrentText(self.state.output_mode); self.configure_combo_popup(output_combo)
        output_card.body.addWidget(output_combo); output_card.body.addWidget(self.default_note("Default: Both")); grid.addWidget(output_card, 0, 0)

        direction_card = ReportCard("Review Direction", self.theme)
        direction_combo = QComboBox(); direction_combo.addItems(["Build up", "Cut down", "Auto batch"]); direction_combo.setCurrentText(self.state.review_direction); self.configure_combo_popup(direction_combo)
        direction_card.body.addWidget(direction_combo)
        direction_card.body.addWidget(self.default_note("Default: Cut down. Auto batch is development-oriented and will move behind development mode later."))
        grid.addWidget(direction_card, 0, 1)

        cut_card = ReportCard("Review Intensity", self.theme)
        cut_combo = QComboBox(); cut_combo.addItems(["Light", "Normal", "Strict", "Brutal / Deep Review", "Rebuild"]); cut_combo.setCurrentText(self.state.cut_depth); self.configure_combo_popup(cut_combo)
        cut_card.body.addWidget(cut_combo)
        intensity_meaning_label = self.make_text(self.review_intensity_meaning(), paper=True)
        cut_card.body.addWidget(intensity_meaning_label)
        cut_card.body.addWidget(self.default_note("Used when Review Direction is Cut down. Also used as an Auto batch default."))

        build_up_card = ReportCard("Build-Up Mode", self.theme)
        build_up_combo = QComboBox()
        build_up_combo.addItems([
            "Build from Scratch — Commander(s) only",
            "Point me in the right direction — 30+ cards needed",
            "Help me get there — 11 to 30 cards needed",
            "Finalize — 10 or fewer cards needed",
        ])
        build_up_combo.setCurrentText(self.state.build_up_mode)
        self.configure_combo_popup(build_up_combo)
        build_up_card.body.addWidget(build_up_combo)
        build_up_card.body.addWidget(self.default_note("Used when Review Direction is Build up. Auto batch may show both fields as global defaults."))

        direction_mode_stack = QStackedWidget()
        direction_mode_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        direction_mode_stack.addWidget(cut_card)
        direction_mode_stack.addWidget(build_up_card)
        auto_batch_panel = QWidget()
        auto_panel_layout = QVBoxLayout(auto_batch_panel)
        auto_panel_layout.setContentsMargins(0, 0, 0, 0)
        auto_panel_layout.setSpacing(12)
        # Clone-like dedicated cards keep the Auto batch view from moving the single-mode cards out of the stack.
        auto_cut_card = ReportCard("Review Intensity", self.theme)
        auto_cut_combo = QComboBox(); auto_cut_combo.addItems(["Light", "Normal", "Strict", "Brutal / Deep Review", "Rebuild"]); auto_cut_combo.setCurrentText(self.state.cut_depth); self.configure_combo_popup(auto_cut_combo)
        auto_cut_card.body.addWidget(auto_cut_combo)
        auto_intensity_label = self.make_text(self.review_intensity_meaning(), paper=True)
        auto_cut_card.body.addWidget(auto_intensity_label)
        auto_cut_card.body.addWidget(self.default_note("Auto batch default for 100+ card / cut-down style reviews."))
        auto_build_card = ReportCard("Build-Up Mode", self.theme)
        auto_build_combo = QComboBox(); auto_build_combo.addItems([
            "Build from Scratch — Commander(s) only",
            "Point me in the right direction — 30+ cards needed",
            "Help me get there — 11 to 30 cards needed",
            "Finalize — 10 or fewer cards needed",
        ]); auto_build_combo.setCurrentText(self.state.build_up_mode); self.configure_combo_popup(auto_build_combo)
        auto_build_card.body.addWidget(auto_build_combo)
        auto_build_card.body.addWidget(self.default_note("Auto batch default for under-100-card / build-up style reviews."))
        auto_panel_layout.addWidget(auto_cut_card)
        auto_panel_layout.addWidget(auto_build_card)
        auto_panel_layout.addWidget(self.default_note("Auto batch remains development-oriented and will move behind development mode later."))
        direction_mode_stack.addWidget(auto_batch_panel)
        grid.addWidget(direction_mode_stack, 1, 0)

        prompt_card = ReportCard("Prompt Mode", self.theme)
        prompt_combo = QComboBox(); prompt_combo.addItems(["Interactive AI chat", "One-shot worksheet"]); prompt_combo.setCurrentText(self.state.prompt_mode); self.configure_combo_popup(prompt_combo)
        prompt_card.body.addWidget(prompt_combo); prompt_card.body.addWidget(self.default_note("Default: Interactive AI chat")); grid.addWidget(prompt_card, 1, 1)

        budget_card = ReportCard("Table / Budget Boundaries", self.theme)
        budget_input = QLineEdit(self.state.budget_note)
        intended_bracket_combo = QComboBox()
        intended_bracket_combo.addItems(["Not sure yet", "Bracket 1", "Bracket 2", "Bracket 3", "Bracket 4", "Bracket 5"])
        intended_bracket_combo.setCurrentText(self.state.intended_bracket)
        self.configure_combo_popup(intended_bracket_combo)
        budget_card.body.addWidget(QLabel("Budget Note"))
        budget_card.body.addWidget(budget_input)
        budget_card.body.addWidget(QLabel("Bracket Intended"))
        budget_card.body.addWidget(intended_bracket_combo)
        budget_card.body.addWidget(self.default_note("Collection mode and file selection live on the Collection Source page. Bracket and collection values are staged through dropdowns, not checkboxes."))
        grid.addWidget(budget_card, 2, 0)

        summary = TexturedPanel(self.theme, kind="iron_2", glow=True)
        s_layout = QVBoxLayout(summary); s_layout.setContentsMargins(18, 16, 18, 16)
        s_title = QLabel("Run Settings Summary"); s_title.setObjectName("sectionTitle"); s_layout.addWidget(s_title)
        summary_label = self.make_text(self.review_settings_summary_text())
        s_layout.addWidget(summary_label)
        auto_note = self.default_note("Auto-staged: changes update this summary immediately. No Apply button required.")
        s_layout.addWidget(auto_note)
        grid.addWidget(summary, 2, 1)

        def refresh_direction_specific_review_fields():
            direction = direction_combo.currentText()
            if direction == "Build up":
                direction_mode_stack.setCurrentIndex(1)
            elif direction == "Auto batch":
                direction_mode_stack.setCurrentIndex(2)
            else:
                direction_mode_stack.setCurrentIndex(0)

        def sync_auto_batch_mirrors():
            blocker_a = QSignalBlocker(auto_cut_combo)
            auto_cut_combo.setCurrentText(cut_combo.currentText())
            del blocker_a
            blocker_b = QSignalBlocker(auto_build_combo)
            auto_build_combo.setCurrentText(build_up_combo.currentText())
            del blocker_b
            auto_intensity_label.setText(self.review_intensity_meaning())

        def auto_stage_review():
            if direction_combo.currentText() == "Auto batch":
                # Keep the single-mode controls in sync with the Auto batch mirror controls.
                blocker_cut = QSignalBlocker(cut_combo)
                cut_combo.setCurrentText(auto_cut_combo.currentText())
                del blocker_cut
                blocker_build = QSignalBlocker(build_up_combo)
                build_up_combo.setCurrentText(auto_build_combo.currentText())
                del blocker_build
            self.stage_review_settings(output_combo, direction_combo, cut_combo, build_up_combo, prompt_combo, budget_input, intended_bracket_combo, summary_label, intensity_meaning_label)
            sync_auto_batch_mirrors()
            refresh_direction_specific_review_fields()

        refresh_direction_specific_review_fields()
        sync_auto_batch_mirrors()

        output_combo.currentTextChanged.connect(lambda _text: auto_stage_review())
        direction_combo.currentTextChanged.connect(lambda _text: auto_stage_review())
        cut_combo.currentTextChanged.connect(lambda _text: auto_stage_review())
        build_up_combo.currentTextChanged.connect(lambda _text: auto_stage_review())
        auto_cut_combo.currentTextChanged.connect(lambda _text: auto_stage_review())
        auto_build_combo.currentTextChanged.connect(lambda _text: auto_stage_review())
        prompt_combo.currentTextChanged.connect(lambda _text: auto_stage_review())
        budget_input.textChanged.connect(lambda _text: auto_stage_review())
        intended_bracket_combo.currentTextChanged.connect(lambda _text: auto_stage_review())

        note = TexturedPanel(self.theme, kind="iron_2", glow=False)
        n_layout = QVBoxLayout(note); n_layout.setContentsMargins(18, 14, 18, 14)
        n_title = QLabel("v0.6.7.9.12 Boundary"); n_title.setObjectName("sectionTitle"); n_layout.addWidget(n_title)
        n_layout.addWidget(self.make_text("These choices auto-stage inside the UI as soon as you change them. Table bracket and collection handoff checkboxes were removed; Bracket Intended and the Collection Source page now carry those staged values directly."))
        grid.addWidget(note, 3, 0, 1, 2)

        content.addWidget(grid_panel); content.addStretch(1); layout.addWidget(scroll, stretch=1); return page

    def page_philosophy(self):
        page, layout = self.page_container(
            "Philosophy Lens",
            "Choose the review lens and guide voice. This shapes explanations without overriding legality, strategy, or collection honesty."
        )
        body = TexturedPanel(self.theme, kind="iron", glow=False)
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
            card = ReportCard(name, self.theme)
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
            card.body.addWidget(self.make_text(desc, paper=True))
            btn = QPushButton("Select Profile")
            btn.setMinimumHeight(38)
            btn.clicked.connect(lambda checked=False, n=name: self.select_philosophy(n))
            card.body.addWidget(btn)
            cards.addWidget(card)
        body_layout.addLayout(cards)

        guide_card = ReportCard("Guide Presentation", self.theme, badges=[("CLI bridge", "manual")])
        guide_card.setMinimumHeight(150)
        guide_card.body.addWidget(self.make_text(
            "Choose how the philosophy guide should be presented. This belongs with the Philosophy Lens, not cut/build mechanics.",
            paper=True
        ))
        guide_combo = QComboBox()
        guide_combo.setMinimumHeight(44)
        guide_combo.addItems(["Masculine guide", "Feminine guide", "Either / random", "No named guide, just philosophy labels"])
        guide_combo.setCurrentText(self.state.guide_presentation)
        self.configure_combo_popup(guide_combo)
        guide_combo.currentTextChanged.connect(self.stage_guide_presentation)
        guide_card.body.addWidget(guide_combo)
        guide_card.body.addWidget(self.default_note("Default: Either / random. Used after the top-level philosophy lens in the guarded CLI bridge."))
        body_layout.addWidget(guide_card)

        subtype_card = ReportCard("Specific Philosophy Subtype", self.theme, badges=[("optional bridge", "manual")])
        subtype_card.setMinimumHeight(150)
        subtype_card.body.addWidget(self.make_text(
            "Optional. Use this only when you want the backend's Specific philosophy subtype route instead of the top-level profile route.",
            paper=True
        ))
        subtype_combo = QComboBox()
        subtype_combo.setMinimumHeight(44)
        subtype_combo.addItems([
            "None / top-level only",
            "Michael / Michelle — Big Moment",
            "Alexander / Alexandria — Big Creature / Stompy",
            "Benjamin / Bethany — Theme / Vibe",
            "Milo / Mia — Pet Card",
            "William / Willow — Let Me Do My Thing",
            "Aaron / Ariana — Battlecruiser",
            "Brad / Bria — Engine Builder",
            "Kyle / Katie — Commander Exploiter",
            "Elund / Emily — Weird Card Rescuer",
            "Brandon / Brenda — Theme Mechanic Inventor",
            "Clark / Clarissa — Self-Imposed Constraint Builder",
            "Jasper / Jennifer — Combo Builder",
            "Avery — Consistency Maximizer",
            "Jordan — Efficiency Optimizer",
            "River — Curve and Mana Discipline",
            "Charlie — Competitive Closer",
            "Kai — Power-Level Calibrator",
            "Riley — Interaction Controller",
        ])
        subtype_combo.setCurrentText(self.state.philosophy_subtype)
        self.configure_combo_popup(subtype_combo)
        subtype_combo.currentTextChanged.connect(self.stage_philosophy_subtype)
        subtype_card.body.addWidget(subtype_combo)
        subtype_card.body.addWidget(self.default_note("Default: None / top-level only. Subtype bridge is optional and only used when this dropdown is changed."))
        body_layout.addWidget(subtype_card)

        body_layout.addStretch(1)
        layout.addWidget(body, stretch=1)
        return page

    def stage_guide_presentation(self, text):
        """Auto-stage guide presentation from Philosophy Lens without requiring Apply."""
        self.state.guide_presentation = text
        self.state.status = "Guide presentation auto-staged"
        self.refresh_context_panel_values()
        self.refresh_run_analysis_previews()

    def stage_philosophy_subtype(self, text):
        """Auto-stage optional philosophy subtype from Philosophy Lens without requiring Apply."""
        self.state.philosophy_subtype = text
        if text != "None / top-level only":
            self.state.selected_philosophy = "Specific philosophy subtype"
        self.state.status = "Philosophy subtype auto-staged"
        self.refresh_context_panel_values()
        self.refresh_run_analysis_previews()

    def select_philosophy(self, name):
        self.state.selected_philosophy = name
        self.state.philosophy_subtype = "None / top-level only"
        self.state.status = f"{name} profile selected"
        self.refresh_context_panel_values()
        self.refresh_run_analysis_previews()

    def run_config_preview_text(self):
        selected_files = len(self.state.selected_collection_files)
        collection_file_note = (
            f"Selected collection files: {selected_files}"
            if self.state.collection_source_mode == "Select collection files"
            else f"Detected .txt files in folder: {self.state.collection_txt_file_count}"
        )
        return (
            "Deck input\n"
            f"- Deck file: {self.state.selected_deck_path}\n"
            f"- Deck name: {self.state.deck_name}\n"
            f"- Commander: {self.state.commander}\n"
            f"- Main-deck estimate: {self.state.main_deck_count} card lines\n"
            f"- Commander card estimate: {self.state.commander_count} card(s)\n"
            f"- Total Commander deck estimate: {self.state.deck_size} card(s)\n"
            f"- Commander detected separately: {'Yes' if self.state.commander_detected else 'No'}\n"
            f"- Companion detected separately: {'Yes' if self.state.companion_detected else 'No'}\n"
            f"- Companion preview: {self.state.companion_name} ({self.state.companion_count} card(s))\n"
            f"- Companion legality: backend validated later, not UI-validated\n\n"
            "Review setup\n"
            f"- Output mode: {self.state.output_mode}\n"
            f"- Review direction: {self.state.review_direction}\n"
            f"- Review intensity: {self.state.cut_depth}\n"
            f"- Intensity meaning: {self.review_intensity_meaning()}\n"
            f"- Build-up mode: {self.state.build_up_mode}\n"
            f"- Prompt mode: {self.state.prompt_mode}\n"
            f"- Budget note: {self.state.budget_note}\n"
            f"- Intended bracket: {self.state.intended_bracket}\n"
            f"- Collection mode: {self.state.collection_mode}\n"
            f"- Collection source: {self.state.collection_source_mode}\n\n"
            "Philosophy lens\n"
            f"- Selected lens: {self.state.selected_philosophy}\n"
            f"- Specific subtype: {self.state.philosophy_subtype}\n"
            f"- Guide presentation: {self.state.guide_presentation}\n\n"
            "Collection source\n"
            f"- Collection mode: {self.state.collection_mode}\n"
            f"- Collection source: {self.state.collection_source_mode}\n"
            f"- Collection folder: {self.state.collection_folder}\n"
            f"- {collection_file_note}\n"
            f"- Collection source note: {self.state.collection_source_note}\n\n"
            "Backend mapping\n"
            "- Backend execution: not connected in UI yet\n"
            "- Locked backend source of truth: v0.6.6.6 CLI workflow\n"
            "- v0.6.7.9.9 purpose: attempt the selected deck handoff across build-up, cut-down, auto-batch defaults, philosophy subtype, guide presentation, collection mode, and collection source"
        )

    def backend_runtime_config_mapping_text(self):
        """Contract-style preview of the future backend runtime config. UI-only; no backend calls."""
        collection_files = [str(Path(path)) for path in self.state.selected_collection_files]
        collection_files_preview = "None selected"
        if collection_files:
            collection_files_preview = "\n".join(f"    - {path}" for path in collection_files[:6])
            if len(collection_files) > 6:
                collection_files_preview += f"\n    - ...and {len(collection_files) - 6} more"

        deck_path = self.state.selected_deck_path if self.state.selected_deck_path != "No deck file selected" else "None"
        collection_folder = self.state.collection_folder if self.state.collection_source_mode == "Entire collection folder" else "Not used for selected-file mode"
        selected_collection_files = len(self.state.selected_collection_files)
        deck_handoff_ready = deck_path != "None"
        collection_source_ready = self.state.collection_mode == "No collection" or self.state.collection_source_note != "Collection source not staged yet."

        return (
            "Runtime Config Contract Preview\n"
            "- UI-only contract preview. No backend command is executed.\n"
            "- This is the proposed handoff shape for the future backend bridge.\n"
            "- The future bridge should consume this staged UI contract instead of inventing a separate workflow.\n"
            "- Disconnected systems: Scryfall lookup, legality validation, collection loading, strategy detection, cuts, replacements, and report generation.\n\n"
            "Execution Boundary\n"
            "- execution_enabled -> False\n"
            "- backend_status -> Not connected\n"
            f"- locked_backend_version -> {LOCKED_BACKEND_VERSION}\n"
            "- report_generation -> CLI-only for now\n\n"
            "Deck Input Contract\n"
            f"- deck_path -> {deck_path}\n"
            f"- deck_handoff_ready -> {deck_handoff_ready}\n"
            f"- deck_name_preview -> {self.state.deck_name}\n"
            f"- commander_preview -> {self.state.commander}\n"
            f"- commander_detected_preview -> {self.state.commander_detected}\n"
            f"- main_deck_count_preview -> {self.state.main_deck_count}\n"
            f"- commander_count_preview -> {self.state.commander_count}\n"
            f"- companion_detected_preview -> {self.state.companion_detected}\n"
            f"- companion_name_preview -> {self.state.companion_name}\n"
            f"- companion_count_preview -> {self.state.companion_count}\n"
            f"- deck_size_preview -> {self.state.deck_size}\n"
            "- companion_legality_source -> backend validation later; UI preview does not enforce companion restrictions\n"
            "- source_of_truth -> backend parser later; UI preview is an estimate\n\n"
            "Review Setup Contract\n"
            f"- output_mode -> {self.state.output_mode}\n"
            f"- review_direction -> {self.state.review_direction}\n"
            f"- review_focus -> {self.review_focus_text()}\n"
            f"- review_intensity -> {self.state.cut_depth}\n"
            f"- review_intensity_meaning -> {self.review_intensity_meaning()}\n"
            f"- build_up_mode -> {self.state.build_up_mode}\n"
            f"- prompt_mode -> {self.state.prompt_mode}\n"
            f"- budget_note -> {self.state.budget_note}\n"
            f"- intended_bracket -> {self.state.intended_bracket}\n"
            "- table_boundary_checkbox -> removed in v0.6.7.9.12; intended bracket is the staged value\n"
            "- collection_handoff_checkbox -> removed in v0.6.7.9.12; Collection Source page is the staged value\n\n"
            "Philosophy Contract\n"
            f"- selected_philosophy -> {self.state.selected_philosophy}\n"
            f"- philosophy_subtype -> {self.state.philosophy_subtype}\n"
            f"- guide_presentation -> {self.state.guide_presentation}\n"
            "- backend_effect -> guidance bias only; does not override legality, strategy, or explicit user constraints\n\n"
            "Collection Contract\n"
            f"- collection_mode -> {self.state.collection_mode}\n"
            f"- collection_source_mode -> {self.state.collection_source_mode}\n"
            f"- collection_source_ready -> {collection_source_ready}\n"
            f"- collection_folder -> {collection_folder}\n"
            f"- selected_collection_file_count -> {selected_collection_files}\n"
            f"- collection_txt_file_count_preview -> {self.state.collection_txt_file_count}\n"
            f"- collection_source_note -> {self.state.collection_source_note}\n"
            f"- selected_collection_files_preview ->\n{collection_files_preview}\n\n"
            "Contract Status\n"
            "- ready_for_preview_review -> True\n"
            "- ready_for_backend_execution -> False\n"
            "- next_patch_candidate -> v0.6.7.8 first guarded execution bridge only after preview approval\n"
        )

    def backend_bridge_preview_text(self):
        """Preview the safest possible future backend bridge handoff. No subprocess calls."""
        deck_path = self.state.selected_deck_path if self.state.selected_deck_path != "No deck file selected" else "None"
        deck_ready = deck_path != "None"
        collection_ready = self.state.collection_mode == "No collection" or self.state.collection_source_note != "Collection source not staged yet."
        selected_files = len(self.state.selected_collection_files)
        source_detail = (
            f"collection_files_count={selected_files}"
            if self.state.collection_source_mode == "Select collection files"
            else f"collection_folder={self.state.collection_folder}; txt_count_preview={self.state.collection_txt_file_count}"
        )
        manual_command_preview = "python main.py"
        if deck_ready:
            manual_command_preview += f"  # future handoff deck_path={deck_path}"
        else:
            manual_command_preview += "  # deck path required before execution"

        return (
            "Safe Backend Bridge Preview\n"
            "- This is a bridge preview only. It does not execute anything.\n"
            "- subprocess.run -> disabled\n"
            "- main.py execution -> disabled\n"
            "- legacy_entrypoint_name -> deck_helper.py / older documentation reference\n"
            "- Scryfall / legality / collection loader / strategy engine / report writer -> disconnected\n"
            "- The CLI backend remains the source of truth until a later guarded execution patch.\n\n"
            "Bridge Readiness\n"
            f"- deck_ready_for_handoff -> {deck_ready}\n"
            f"- collection_source_ready_or_optional -> {collection_ready}\n"
            "- runtime_contract_visible -> True\n"
            "- runtime_contract_refreshes_live -> True\n"
            "- execution_allowed_in_this_patch -> False\n\n"
            "Future Backend Entry Candidate\n"
            "- entrypoint_candidate -> main.py\n"
            "- legacy_entrypoint_name -> deck_helper.py\n"
            "- launch_method_candidate -> external subprocess later, not enabled now\n"
            "- config_source_candidate -> staged UI runtime config contract\n"
            "- report_output_candidate -> existing CLI output workflow, not opened here yet\n\n"
            "Manual Command Preview Only\n"
            f"- command_preview -> {manual_command_preview}\n"
            f"- review_direction -> {self.state.review_direction}\n"
            f"- review_intensity -> {self.state.cut_depth}\n"
            f"- intended_bracket -> {self.state.intended_bracket}\n"
            f"- collection_mode -> {self.state.collection_mode}\n"
            f"- collection_source_detail -> {source_detail}\n\n"
            "Bridge Safety Gates For A Later Patch\n"
            "- require visible command preview before execution -> True\n"
            "- require explicit user action before execution -> True\n"
            "- require backend path/entrypoint validation -> True\n"
            "- require output folder handling plan -> True\n"
            "- require error capture and user-readable failure message -> True\n"
            "- guarded_execution_bridge_preview_ready -> True\n"
            "- ready_for_actual_qprocess_execution -> guarded confirmation required"
        )

    def backend_entrypoint_path(self):
        """Resolve the currently previewed backend entrypoint relative to the working directory."""
        return Path(self.state.backend_working_directory) / self.state.backend_entrypoint

    def guarded_command_preview(self):
        """Build the visible command preview for the guarded bridge. This matches the manual backend command."""
        deck_path = self.state.selected_deck_path if self.state.selected_deck_path != "No deck file selected" else "No UI deck selected; main.py may prompt interactively"
        return f'py {self.state.backend_entrypoint}  # guarded run; MTG_DECK_FILE="{deck_path}"'

    def guarded_command_parts(self):
        """Return the actual guarded command as a list. Never use shell=True."""
        return ["py", self.state.backend_entrypoint]

    def cli_output_mode_input_value(self):
        """Map the UI Output Mode to the first known main.py CLI prompt."""
        mapping = {
            "Normal User Mode": "1",
            "Debug / Stress-Test Mode": "2",
            "Both": "3",
        }
        return mapping.get(self.state.output_mode, "1")

    def cli_review_direction_input_value(self):
        """Map the UI Review Direction to the second known main.py CLI prompt."""
        mapping = {
            "Build up": "1",
            "Cut down": "2",
            "Auto batch": "3",
        }
        return mapping.get(self.state.review_direction, "2")

    def cli_build_up_mode_input_value(self):
        """Map the durable UI Build-Up Mode field to the build-up mode CLI prompt."""
        mapping = {
            "Build from Scratch — Commander(s) only": "1",
            "Point me in the right direction — 30+ cards needed": "2",
            "Help me get there — 11 to 30 cards needed": "3",
            "Finalize — 10 or fewer cards needed": "4",
        }
        if self.state.build_up_mode in mapping:
            return mapping[self.state.build_up_mode]
        intensity_fallback = {
            "Light": "4",
            "Normal": "3",
            "Strict": "2",
            "Brutal / Deep Review": "2",
            "Rebuild": "1",
        }
        return intensity_fallback.get(self.state.cut_depth, "4")

    def cli_review_intensity_input_value(self):
        """Map Review Intensity to the cut-down / strictness CLI prompt."""
        mapping = {
            "Light": "1",
            "Normal": "2",
            "Strict": "3",
            "Brutal / Deep Review": "4",
            "Rebuild": "5",
        }
        return mapping.get(self.state.cut_depth, "2")

    def cli_prompt_mode_input_value(self):
        """Map the UI Prompt Mode to the prompt interaction CLI prompt."""
        mapping = {
            "Interactive AI chat": "1",
            "One-shot worksheet": "2",
        }
        return mapping.get(self.state.prompt_mode, "1")

    def should_send_prompt_mode_input(self):
        """Send prompt mode after the known mode-specific prompt for build-up, cut-down, or auto-batch."""
        return self.state.review_direction in {"Build up", "Cut down", "Auto batch"}

    def cli_philosophy_lens_input_value(self):
        """Map the UI Philosophy Lens to the CLI philosophy prompt."""
        if self.state.philosophy_subtype != "None / top-level only":
            return "5"
        mapping = {
            "Balanced / Unknown": "1",
            "Timmy / Tammy": "2",
            "Johnny / Jenny": "3",
            "Spike": "4",
        }
        return mapping.get(self.state.selected_philosophy, "1")

    def cli_philosophy_subtype_input_value(self):
        """Best-effort mapping for Specific philosophy subtype prompt using the planned subtype order."""
        mapping = {
            "Michael / Michelle — Big Moment": "1",
            "Alexander / Alexandria — Big Creature / Stompy": "2",
            "Benjamin / Bethany — Theme / Vibe": "3",
            "Milo / Mia — Pet Card": "4",
            "William / Willow — Let Me Do My Thing": "5",
            "Aaron / Ariana — Battlecruiser": "6",
            "Brad / Bria — Engine Builder": "7",
            "Kyle / Katie — Commander Exploiter": "8",
            "Elund / Emily — Weird Card Rescuer": "9",
            "Brandon / Brenda — Theme Mechanic Inventor": "10",
            "Clark / Clarissa — Self-Imposed Constraint Builder": "11",
            "Jasper / Jennifer — Combo Builder": "12",
            "Avery — Consistency Maximizer": "13",
            "Jordan — Efficiency Optimizer": "14",
            "River — Curve and Mana Discipline": "15",
            "Charlie — Competitive Closer": "16",
            "Kai — Power-Level Calibrator": "17",
            "Riley — Interaction Controller": "18",
        }
        return mapping.get(self.state.philosophy_subtype, "")

    def should_send_philosophy_subtype_input(self):
        """Only send subtype when user chose an explicit subtype."""
        return self.state.philosophy_subtype != "None / top-level only"

    def should_send_philosophy_lens_input(self):
        """Send philosophy after prompt mode for all bridged directions."""
        return self.should_send_prompt_mode_input()

    def cli_guide_presentation_input_value(self):
        """Map the UI Guide Presentation field to the CLI guide presentation prompt."""
        mapping = {
            "Masculine guide": "1",
            "Feminine guide": "2",
            "Either / random": "3",
            "No named guide, just philosophy labels": "4",
        }
        return mapping.get(self.state.guide_presentation, "3")

    def should_send_guide_presentation_input(self):
        """Only send guide presentation after the known top-level philosophy lens prompt is bridged."""
        return self.should_send_philosophy_lens_input()

    def cli_collection_mode_input_value(self):
        """Map the existing Collection Source page mode to the CLI collection mode prompt."""
        mapping = {
            "No collection": "1",
            "Prefer collection first": "2",
            "Collection only": "3",
            "Collection shakeup": "4",
        }
        return mapping.get(self.state.collection_mode, "1")

    def should_send_collection_mode_input(self):
        """Only send collection mode after guide presentation is safely bridged in the known Build-up path."""
        return self.should_send_guide_presentation_input()

    def cli_collection_source_input_value(self):
        """Map the existing Collection Source page source mode to the CLI collection source prompt."""
        mapping = {
            "Entire collection folder": "1",
            "Select collection files": "2",
        }
        return mapping.get(self.state.collection_source_mode, "1")

    def should_send_collection_source_input(self):
        """Only send collection source after collection mode is bridged and collection is enabled."""
        return self.should_send_collection_mode_input() and self.state.collection_mode != "No collection"

    def collection_source_detail_answered(self):
        """Return whether the active collection source detail is sufficiently staged for the guarded bridge preview."""
        if self.state.collection_mode == "No collection":
            return True
        if self.state.collection_source_mode == "Entire collection folder":
            return bool(str(self.state.collection_folder).strip())
        if self.state.collection_source_mode == "Select collection files":
            return bool(self.state.selected_collection_files)
        return False

    def collection_source_detail_preview_text(self):
        """Describe the active collection source detail without mixing stale folder/file state."""
        if self.state.collection_mode == "No collection":
            return "not required because Collection Mode is No collection"
        if self.state.collection_source_mode == "Entire collection folder":
            folder = str(self.state.collection_folder).strip() or "not staged"
            return f"folder={folder}; txt_count_preview={self.state.collection_txt_file_count}"
        if self.state.collection_source_mode == "Select collection files":
            if not self.state.selected_collection_files:
                return "selected_files=0; no file payload staged"
            examples = "; ".join(Path(path).name for path in self.state.selected_collection_files[:3])
            if len(self.state.selected_collection_files) > 3:
                examples += f"; ...and {len(self.state.selected_collection_files) - 3} more"
            return f"selected_files={len(self.state.selected_collection_files)}; examples={examples}"
        return "unknown collection source mode"

    def normalize_collection_source_for_guarded_run(self):
        """Normalize active source mode before a guarded run without mutating unrelated saved selections."""
        if self.state.collection_source_mode == "Entire collection folder":
            try:
                self.state.collection_txt_file_count = len(list(Path(self.state.collection_folder).glob("*.txt")))
            except Exception:
                self.state.collection_txt_file_count = 0
            if self.state.collection_mode != "No collection":
                self.state.collection_source_note = "Entire collection folder staged for guarded run. Selected file payload will not be sent."
        elif self.state.collection_source_mode == "Select collection files":
            self.state.collection_txt_file_count = len(self.state.selected_collection_files)
            if self.state.collection_mode != "No collection":
                self.state.collection_source_note = "Selected collection files staged for guarded run. Folder payload will not be sent."

    def cli_input_bridge_preview_text(self):
        """Preview the full known stdin bridge used in this patch."""
        build_up_answer = self.cli_build_up_mode_input_value() if self.state.review_direction == "Build up" else "not sent unless Review Direction is Build up"
        cut_depth_answer = self.cli_review_intensity_input_value() if self.state.review_direction in {"Cut down", "Auto batch"} else "not sent unless Review Direction is Cut down or Auto batch"
        prompt_mode_answer = self.cli_prompt_mode_input_value() if self.should_send_prompt_mode_input() else "not sent until prior prompts are mapped for this review direction"
        philosophy_answer = self.cli_philosophy_lens_input_value() if self.should_send_philosophy_lens_input() else "not sent until prompt mode is safely bridged"
        subtype_answer = self.cli_philosophy_subtype_input_value() if self.should_send_philosophy_subtype_input() else "not sent unless Specific philosophy subtype is selected"
        guide_answer = self.cli_guide_presentation_input_value() if self.should_send_guide_presentation_input() else "not sent until philosophy lens is safely bridged"
        collection_answer = self.cli_collection_mode_input_value() if self.should_send_collection_mode_input() else "not sent until guide presentation is safely bridged"
        collection_source_answer = self.cli_collection_source_input_value() if self.should_send_collection_source_input() else "not sent unless collection mode is enabled and safely bridged"
        selected_file_preview = "None selected"
        if self.state.selected_collection_files:
            selected_file_preview = "; ".join(str(Path(path)) for path in self.state.selected_collection_files[:3])
            if len(self.state.selected_collection_files) > 3:
                selected_file_preview += f"; ...and {len(self.state.selected_collection_files) - 3} more"
        return (
            "Full CLI Bridge Gap Pass\n"
            "- bridge_scope -> Build-up, Cut-down, Auto-batch defaults, top-level/subtype philosophy, guide presentation, collection mode, and collection source\n"
            "- strategy -> send staged UI answers in the same order main.py asks for them, then capture any unexpected prompt/error\n"
            f"- selected_deck_handoff -> MTG_DECK_FILE={self.state.selected_deck_path if self.state.selected_deck_path != 'No deck file selected' else 'not staged'}\n"
            "- known_prompt_1 -> Output mode [1=Normal]:\n"
            f"- ui_output_mode -> {self.state.output_mode}\n"
            f"- output_mode_stdin_value_to_send -> {self.cli_output_mode_input_value()}\n"
            "- known_prompt_2 -> Review direction [2=Cut down]:\n"
            f"- ui_review_direction -> {self.state.review_direction}\n"
            f"- review_direction_stdin_value_to_send -> {self.cli_review_direction_input_value()}\n"
            "- mode_specific_prompt_when_build_up -> Build-up mode [4=Finalize]:\n"
            f"- ui_build_up_mode -> {self.state.build_up_mode}\n"
            f"- build_up_mode_stdin_value_to_send -> {build_up_answer}\n"
            "- mode_specific_prompt_when_cut_down_or_auto_batch -> Review Intensity / Cut Strictness:\n"
            f"- ui_review_intensity -> {self.state.cut_depth}\n"
            f"- review_intensity_stdin_value_to_send -> {cut_depth_answer}\n"
            "- known_prompt_prompt_mode -> Prompt interaction mode [1=Interactive]:\n"
            f"- ui_prompt_mode -> {self.state.prompt_mode}\n"
            f"- prompt_mode_stdin_value_to_send -> {prompt_mode_answer}\n"
            f"- prompt_mode_bridge_active_for_this_direction -> {self.should_send_prompt_mode_input()}\n"
            "- known_prompt_philosophy -> Philosophy lens [1=Balanced / Unknown]:\n"
            f"- ui_philosophy_lens -> {self.state.selected_philosophy}\n"
            f"- ui_philosophy_subtype -> {self.state.philosophy_subtype}\n"
            f"- philosophy_lens_stdin_value_to_send -> {philosophy_answer}\n"
            f"- philosophy_subtype_stdin_value_to_send -> {subtype_answer}\n"
            f"- philosophy_subtype_bridge_active -> {self.should_send_philosophy_subtype_input()}\n"
            "- known_prompt_guide -> Guide presentation [3=Either/random]:\n"
            f"- ui_guide_presentation -> {self.state.guide_presentation}\n"
            f"- guide_presentation_stdin_value_to_send -> {guide_answer}\n"
            "- known_prompt_collection_mode -> Collection mode [1=No]:\n"
            f"- ui_collection_mode -> {self.state.collection_mode}\n"
            f"- collection_mode_stdin_value_to_send -> {collection_answer}\n"
            "- known_prompt_collection_source -> Collection source [1=Entire collection folder]:\n"
            f"- ui_collection_source_mode -> {self.state.collection_source_mode}\n"
            f"- collection_source_stdin_value_to_send -> {collection_source_answer}\n"
            f"- collection_source_bridge_active_for_this_run -> {self.should_send_collection_source_input()}\n"
            f"- collection_folder_or_file_path_answered -> {self.collection_source_detail_answered()}\n"
            f"- active_collection_source_detail -> {self.collection_source_detail_preview_text()}\n"
            f"- collection_folder_preview -> {self.state.collection_folder}\n"
            f"- selected_collection_files_preview -> {selected_file_preview}\n"
            "- active_source_payload_rule -> Entire folder uses folder/default backend behavior; selected files sends file payload only when files are staged\n"
            "- selected_file_path_handoff -> best-effort only if backend asks for typed paths; unexpected prompts are captured safely\n"
            "- stdin_closed_after_known_answers -> True\n"
            "- unknown_future_prompts_answered -> False\n"
            "- safety_note -> this patch attempts all known gaps, but still captures surprises instead of hiding them\n"
        )

    def guarded_execution_preview_text(self):
        """Preview the guarded execution bridge and current readiness."""
        entrypoint_path = self.backend_entrypoint_path()
        entrypoint_exists = entrypoint_path.exists()
        deck_ready = self.state.selected_deck_path != "No deck file selected"
        runtime_contract_ready = self.runtime_mapping_preview_box is not None or self.stack.currentIndex() == self.RUN_ANALYSIS
        collection_ready = self.state.collection_mode == "No collection" or self.state.collection_source_note != "Collection source not staged yet."
        command_preview = self.guarded_command_preview()
        can_attempt = entrypoint_exists and not self.state.guarded_run_in_progress

        return (
            "Guarded Execution Bridge Preview\n"
            "- This is the first actual guarded execution path.\n"
            "- main.py can run only after explicit user confirmation.\n"
            "- The UI uses QProcess with a command list and never uses shell=True.\n"
            "- The UI must keep CLI/main.py as the source of truth and must not invent a second backend workflow.\n"
            "- v0.6.7.9.14 keeps the Deck Selection handoff, companion preview status, and adds guarded-run report path detection without parsing report contents.\n"
            "- If a backend prompt does not match the expected order, stdout/stderr capture will reveal it without freezing the UI.\n"
            "- After sending known answers, stdin is closed so unexpected later prompts are captured safely instead of guessed.\n\n"
            "Entrypoint Validation\n"
            f"- entrypoint_name -> {self.state.backend_entrypoint}\n"
            f"- working_directory -> {self.state.backend_working_directory}\n"
            f"- entrypoint_path -> {entrypoint_path}\n"
            f"- entrypoint_exists_preview -> {entrypoint_exists}\n"
            "- validation_source -> local filesystem preview only\n\n"
            "Visible Command Preview\n"
            f"- command_preview -> {command_preview}\n"
            f"- command_parts -> {self.guarded_command_parts()}\n"
            "- command_visible_before_execution -> True\n"
            "- user_confirmation_required -> True\n"
            "- silent_execution_allowed -> False\n"
            "- shell_true_allowed -> False\n\n"
            "CLI Input Bridge\n"
            f"- cli_input_bridge_enabled -> {self.state.cli_input_bridge_enabled}\n"
            f"- cli_input_bridge_scope -> {self.state.cli_input_bridge_scope}\n"
            f"- output_mode_prompt_answer -> {self.cli_output_mode_input_value()}\n"
            f"- review_direction_prompt_answer -> {self.cli_review_direction_input_value()}\n"
            f"- build_up_mode_prompt_answer -> {self.cli_build_up_mode_input_value() if self.state.review_direction == 'Build up' else 'not sent unless Build up'}\n"
            f"- review_intensity_prompt_answer -> {self.cli_review_intensity_input_value() if self.state.review_direction in {'Cut down', 'Auto batch'} else 'not sent unless Cut down or Auto batch'}\n"
            f"- prompt_mode_prompt_answer -> {self.cli_prompt_mode_input_value() if self.should_send_prompt_mode_input() else 'not sent until safe for this review direction'}\n"
            f"- philosophy_lens_prompt_answer -> {self.cli_philosophy_lens_input_value() if self.should_send_philosophy_lens_input() else 'not sent until safe for this review direction'}\n"
            f"- philosophy_subtype_prompt_answer -> {self.cli_philosophy_subtype_input_value() if self.should_send_philosophy_subtype_input() else 'not sent unless specific subtype is selected'}\n"
            f"- guide_presentation_prompt_answer -> {self.cli_guide_presentation_input_value() if self.should_send_guide_presentation_input() else 'not sent until safe for this review direction'}\n"
            f"- collection_mode_prompt_answer -> {self.cli_collection_mode_input_value() if self.should_send_collection_mode_input() else 'not sent until safe for this review direction'}\n"
            f"- collection_source_prompt_answer -> {self.cli_collection_source_input_value() if self.should_send_collection_source_input() else 'not sent unless collection mode is enabled'}\n"
            f"- companion_detected_preview -> {self.state.companion_detected}\n"
            f"- companion_name_preview -> {self.state.companion_name}\n"
            f"- companion_count_preview -> {self.state.companion_count}\n"
            f"- companion_legality_source -> backend validation only; UI preview does not enforce companion restrictions\n"
            f"- collection_folder_or_file_path_answered -> {self.collection_source_detail_answered()}\n"
            f"- active_collection_source_detail -> {self.collection_source_detail_preview_text()}\n"
            f"- specific_philosophy_subtype_answered -> {self.should_send_philosophy_subtype_input()}\n"
            f"- last_cli_input_sent -> {self.state.cli_input_bridge_last_sent}\n"
            "- stdin_closed_after_known_answers -> True\n"
            "- unknown_future_prompts_answered -> False\n\n"
            "Execution Readiness Checklist\n"
            f"- deck_file_selected_for_ui_context -> {deck_ready}\n"
            f"- selected_deck_handoff_env -> {self.state.selected_deck_path if deck_ready else 'not set; run blocked until a deck is selected'}\n"
            f"- companion_preview_handoff_status -> {'detected for backend validation' if self.state.companion_detected else 'no companion detected in UI preview'}\n"
            "- deck_file_required_by_guarded_run -> True for UI handoff; main.py receives MTG_DECK_FILE\n"
            f"- runtime_contract_visible -> {runtime_contract_ready}\n"
            f"- collection_source_ready_or_optional -> {collection_ready}\n"
            f"- main_py_found_preview -> {entrypoint_exists}\n"
            "- output_capture_plan_visible -> True\n"
            "- error_capture_plan_visible -> True\n"
            f"- guarded_run_in_progress -> {self.state.guarded_run_in_progress}\n"
            f"- actual_execution_available_after_confirmation -> {can_attempt}\n\n"
            "Output / Error Capture Plan\n"
            "- stdout_capture -> active\n"
            "- stderr_capture -> active\n"
            "- return_code_handling -> active\n"
            "- timeout_handling -> active; process will be killed if it exceeds the timeout\n"
            "- cli_input_bridge -> active for output mode, review direction, build-up/cut-down/auto-batch defaults, prompt mode, top-level/subtype philosophy, guide presentation, collection mode, collection source, and conservative selected-file path payloads\n"
            "- user_readable_failure_message -> active\n"
            "- output_folder_opening -> planned after successful run, not active yet\n\n"
            "Current Patch Safety Boundary\n"
            "- subprocess.run -> disabled; QProcess is used for guarded execution\n"
            "- main.py execution -> confirmation-gated\n"
            "- backend analysis -> only through CLI/main.py after confirmation\n"
            "- Commander Spellbook/API calls -> disabled\n"
            "- ready_for_actual_execution -> guarded only, not automatic\n"
        )

    def clear_detected_report_outputs(self):
        """Reset report-output detection state before a guarded run."""
        self.state.last_output_files = []
        self.state.last_normal_report_files = []
        self.state.last_debug_report_files = []
        self.state.last_output_folder = "Not detected"
        self.state.last_normal_report_folder = "Not detected"
        self.state.last_debug_report_folder = "Not detected"
        self.state.last_original_output_folder = "Not detected"
        self.state.last_backend_unique_output_status = "No backend unique output detection attempted yet."
        self.state.last_report_detection_status = "No guarded run report output detected yet."
        self.state.last_report_detection_mode = "not_attempted"
        self.state.last_report_detection_warning = "No report detection warning."

    def resolve_backend_output_path(self, raw_path):
        """Resolve a backend printed path relative to the guarded run working directory."""
        cleaned = (raw_path or "").strip().strip('"').strip("'")
        if not cleaned:
            return None
        normalized = cleaned.replace("\\", "/")
        path = Path(normalized)
        if not path.is_absolute():
            path = Path(self.state.backend_working_directory) / path
        return path

    def expected_report_category_notes(self):
        """Describe which report categories are expected based on the staged Output Mode."""
        mode = (self.state.output_mode or "").lower()
        expect_normal = "normal" in mode or "both" in mode
        expect_debug = "debug" in mode or "stress" in mode or "both" in mode
        if not expect_normal and not expect_debug:
            # Be conservative for any future custom wording.
            expect_normal = True
        return expect_normal, expect_debug

    def path_contains_folder(self, path_text, folder_name):
        try:
            return folder_name.lower() in [part.lower() for part in Path(path_text).parts]
        except Exception:
            return False

    def derive_output_folder_from_detected_files(self, detected_files):
        """Infer the deck output root from detected backend files without reading report contents."""
        for path_text in detected_files:
            path = Path(path_text)
            parts_lower = [part.lower() for part in path.parts]
            if "outputs" in parts_lower:
                idx = parts_lower.index("outputs")
                if len(path.parts) > idx + 1:
                    return str(Path(*path.parts[:idx + 2]))
            parent = path.parent
            if parent.name.lower() in {"normal", "debug"}:
                return str(parent.parent)
        return "Not detected"

    def make_unique_guarded_run_output_folder(self, original_output_folder):
        """Create a sibling output folder for this guarded run so repeated deck runs do not pile into one folder."""
        original = Path(original_output_folder)
        parent = original.parent
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{original.name}_run_{stamp}"
        candidate = parent / base_name
        suffix = 2
        while candidate.exists():
            candidate = parent / f"{base_name}_{suffix}"
            suffix += 1
        candidate.mkdir(parents=True, exist_ok=False)
        return candidate

    def relocate_detected_output_files_to_unique_run_folder(self, detected_files):
        """Compatibility no-op after v0.6.7.9.17 backend output fix.

        The backend now writes directly into one unique, deck-file-distinguished
        run folder. Keep this method name so the existing report-detection flow
        remains stable, but do not move files or leave empty commander-shell
        folders behind.
        """
        detected_files = list(detected_files or [])
        if not detected_files:
            self.state.last_backend_unique_output_status = "No files detected; backend unique output status was not evaluated."
            return []
        self.state.last_backend_unique_output_status = (
            "Skipped: backend now writes directly to a unique deck-file-distinguished run folder; "
            "UI relocation is no longer needed."
        )
        return [str(Path(path)) for path in detected_files]

    def extract_files_written_paths(self, stdout_text):
        """Return backend file paths printed under the Files written block. Does not read files."""
        lines = (stdout_text or "").splitlines()
        in_files_block = False
        detected = []
        for line in lines:
            stripped = line.strip()
            lower = stripped.lower().rstrip(":")
            if lower == "files written" or lower.endswith("files written") or stripped.lower().startswith("files written"):
                in_files_block = True
                continue
            if not in_files_block:
                continue
            if not stripped:
                continue
            bullet = None
            for prefix in ("- ", "• ", "* "):
                if stripped.startswith(prefix):
                    bullet = stripped[len(prefix):].strip()
                    break
            if bullet is None:
                if detected:
                    break
                continue
            resolved = self.resolve_backend_output_path(bullet)
            if resolved is not None:
                suffix = resolved.suffix.lower()
                if suffix in {".md", ".txt", ".markdown", ".log"}:
                    resolved_text = str(resolved)
                    if resolved_text not in detected:
                        detected.append(resolved_text)
        return detected

    def detect_report_outputs_from_stdout(self, stdout_text):
        """Parse report paths from stdout and harden status messaging across output modes."""
        self.clear_detected_report_outputs()
        detected = self.extract_files_written_paths(stdout_text)
        detected = self.relocate_detected_output_files_to_unique_run_folder(detected)
        self.state.last_output_files = detected
        self.state.last_normal_report_files = [p for p in detected if self.path_contains_folder(p, "normal")]
        self.state.last_debug_report_files = [p for p in detected if self.path_contains_folder(p, "debug")]
        if detected:
            self.state.last_output_folder = self.derive_output_folder_from_detected_files(detected)
        if self.state.last_normal_report_files:
            self.state.last_normal_report_folder = str(Path(self.state.last_normal_report_files[0]).parent)
        if self.state.last_debug_report_files:
            self.state.last_debug_report_folder = str(Path(self.state.last_debug_report_files[0]).parent)

        expect_normal, expect_debug = self.expected_report_category_notes()
        warnings = []
        if expect_normal and not self.state.last_normal_report_files:
            warnings.append("expected normal report output for current Output Mode, but none was detected")
        if expect_debug and not self.state.last_debug_report_files:
            warnings.append("expected debug report output for current Output Mode, but none was detected")
        if detected and self.state.last_output_folder == "Not detected":
            warnings.append("files were detected, but output folder root could not be inferred")

        if detected:
            self.state.last_report_detection_mode = "stdout_files_written_block"
            self.state.last_report_detection_status = (
                f"Detected {len(detected)} output file(s): "
                f"{len(self.state.last_normal_report_files)} normal, "
                f"{len(self.state.last_debug_report_files)} debug."
            )
        else:
            self.state.last_report_detection_mode = "no_files_written_block_detected"
            self.state.last_report_detection_status = (
                "No report paths detected from guarded-run stdout. "
                "If the backend completed successfully, check the CLI output folder manually."
            )
            warnings.append("no Files written block or report path bullets were detected")

        self.state.last_report_detection_warning = "; ".join(warnings) if warnings else "No report detection warnings."

    def report_output_summary_text(self):
        normal_preview = "None detected"
        if self.state.last_normal_report_files:
            normal_preview = "\n".join(f"  - {Path(p).name}" for p in self.state.last_normal_report_files[:8])
            if len(self.state.last_normal_report_files) > 8:
                normal_preview += f"\n  - ...and {len(self.state.last_normal_report_files) - 8} more"
        debug_preview = "None detected"
        if self.state.last_debug_report_files:
            debug_preview = "\n".join(f"  - {Path(p).name}" for p in self.state.last_debug_report_files[:10])
            if len(self.state.last_debug_report_files) > 10:
                debug_preview += f"\n  - ...and {len(self.state.last_debug_report_files) - 10} more"
        expect_normal, expect_debug = self.expected_report_category_notes()
        return (
            "Report Output Detection\n"
            f"- detection_status -> {self.state.last_report_detection_status}\n"
            f"- detection_mode -> {self.state.last_report_detection_mode}\n"
            f"- detection_warning -> {self.state.last_report_detection_warning}\n"
            f"- output_mode_at_detection -> {self.state.output_mode}\n"
            f"- expected_normal_reports -> {expect_normal}\n"
            f"- expected_debug_reports -> {expect_debug}\n"
            f"- output_folder -> {self.state.last_output_folder}\n"
            f"- original_backend_output_folder -> {self.state.last_original_output_folder}\n"
            f"- backend_unique_output_status -> {self.state.last_backend_unique_output_status}\n"
            f"- normal_report_folder -> {self.state.last_normal_report_folder}\n"
            f"- debug_report_folder -> {self.state.last_debug_report_folder}\n"
            f"- output_folder_button_enabled -> {self.folder_path_is_openable(self.state.last_output_folder)}\n"
            f"- normal_folder_button_enabled -> {self.folder_path_is_openable(self.state.last_normal_report_folder)}\n"
            f"- debug_folder_button_enabled -> {self.folder_path_is_openable(self.state.last_debug_report_folder)}\n"
            f"- total_output_files_detected -> {len(self.state.last_output_files)}\n"
            f"- normal_report_files_detected -> {len(self.state.last_normal_report_files)}\n"
            f"- debug_report_files_detected -> {len(self.state.last_debug_report_files)}\n\n"
            "Normal reports\n"
            f"{normal_preview}\n\n"
            "Debug reports\n"
            f"{debug_preview}\n\n"
            "Boundary\n"
            "- The UI detects file paths from stdout, then moves this run’s detected files into one unique guarded-run output folder.\n"
            "- The backend still writes first; the UI isolates the detected files after a successful guarded run.\n"
            "- Folder buttons are enabled only when a detected local folder exists.\n"
            "- The UI does not parse report contents yet.\n"
            "- Backend report generation remains CLI/main.py source of truth.\n"
        )

    def folder_path_is_openable(self, folder_path):
        path_text = folder_path or "Not detected"
        if path_text == "Not detected":
            return False
        path = Path(path_text)
        return path.exists() and path.is_dir()

    def refresh_report_output_buttons(self):
        button_pairs = [
            (getattr(self, "open_output_folder_button", None), self.state.last_output_folder),
            (getattr(self, "open_normal_report_folder_button", None), self.state.last_normal_report_folder),
            (getattr(self, "open_debug_report_folder_button", None), self.state.last_debug_report_folder),
        ]
        for button, folder in button_pairs:
            if button is not None:
                button.setEnabled(self.folder_path_is_openable(folder))

    def open_folder_path(self, folder_path, label):
        path_text = folder_path or "Not detected"
        if path_text == "Not detected":
            QMessageBox.information(self, f"{label} Not Detected", f"No {label.lower()} has been detected from a successful guarded run yet.")
            return
        path = Path(path_text)
        if not path.exists() or not path.is_dir():
            QMessageBox.warning(self, f"{label} Missing", f"The detected {label.lower()} does not exist or is not a folder:\n\n{path}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def open_last_output_folder(self):
        self.open_folder_path(self.state.last_output_folder, "Output Folder")

    def open_last_normal_report_folder(self):
        self.open_folder_path(self.state.last_normal_report_folder, "Normal Report Folder")

    def open_last_debug_report_folder(self):
        self.open_folder_path(self.state.last_debug_report_folder, "Debug Report Folder")

    def guarded_run_result_text(self):
        return (
            "Guarded Run Output / Result\n"
            f"- run_in_progress -> {self.state.guarded_run_in_progress}\n"
            f"- last_run_started_at -> {self.state.last_guarded_run_started_at}\n"
            f"- last_run_finished_at -> {self.state.last_guarded_run_finished_at}\n"
            f"- last_run_status -> {self.state.last_guarded_run_status}\n"
            f"- last_run_return_code -> {self.state.last_guarded_run_return_code}\n"
            f"- cli_input_bridge_last_sent -> {self.state.cli_input_bridge_last_sent}\n"
            f"- report_detection_status -> {self.state.last_report_detection_status}\n"
            f"- report_detection_warning -> {self.state.last_report_detection_warning}\n"
            f"- backend_unique_output_status -> {self.state.last_backend_unique_output_status}\n\n"
            "Captured stdout preview\n"
            f"{self.state.last_guarded_run_stdout}\n\n"
            "Captured stderr preview\n"
            f"{self.state.last_guarded_run_stderr}\n\n"
            f"{self.report_output_summary_text()}\n"
            "Boundary\n"
            "- Commander Spellbook/API calls are not part of this run path.\n"
            "- The UI detects report file paths and folders but does not parse report contents yet.\n"
            "- CLI/main.py remains the source of truth.\n"
        )

    def guarded_execution_placeholder_message(self):
        QMessageBox.information(
            self,
            "Guarded Execution Bridge",
            "v0.6.7.9.9 can attempt a guarded QProcess run of py main.py only after explicit confirmation.\n\n"
            "This patch attempts the selected deck handoff across Build-up, Cut-down, Auto-batch defaults, Philosophy Lens/subtype, Guide Presentation, Collection Mode, and Collection Source, then safely captures any unexpected prompt/error for review."
        )

    def start_guarded_backend_run(self):
        """Run py main.py only after explicit confirmation, using QProcess and captured output."""
        if self.state.guarded_run_in_progress:
            QMessageBox.information(self, "Guarded Run Already Active", "main.py is already running. Wait for it to finish before starting another guarded run.")
            return

        entrypoint_path = self.backend_entrypoint_path()
        if self.state.selected_deck_path == "No deck file selected":
            QMessageBox.warning(
                self,
                "Deck File Required",
                "Choose a deck on the Deck Selection page before running main.py from the UI.\n\nThe guarded bridge now hands that selected deck to main.py using MTG_DECK_FILE so the backend processes the same deck shown in Current Deck Context."
            )
            self.state.last_guarded_run_status = "Guarded run blocked: no Deck Selection file staged for MTG_DECK_FILE handoff."
            self.refresh_run_analysis_previews()
            return

        self.normalize_collection_source_for_guarded_run()
        if self.state.collection_mode != "No collection" and not self.collection_source_detail_answered():
            QMessageBox.warning(
                self,
                "Collection Source Detail Required",
                "Collection mode is enabled, but the active collection source detail is not staged. Choose a collection folder or select collection files before running main.py."
            )
            self.state.last_guarded_run_status = "Guarded run blocked: active collection source detail was not staged."
            self.refresh_collection_page_widgets()
            self.refresh_run_analysis_previews()
            return

        if not entrypoint_path.exists():
            QMessageBox.warning(
                self,
                "main.py Not Found",
                f"The guarded bridge could not find the backend entrypoint:\n\n{entrypoint_path}\n\nConfirm you launched the UI from the project root or update the working directory in a later settings patch."
            )
            return

        deck_note = self.state.selected_deck_path
        message = (
            "This will start the existing backend entrypoint using the same manual command you use outside the UI.\n\n"
            f"Working directory:\n{self.state.backend_working_directory}\n\n"
            f"Entrypoint:\n{entrypoint_path}\n\n"
            f"Command preview:\n{self.guarded_command_preview()}\n\n"
            f"Selected deck handoff (MTG_DECK_FILE):\n{deck_note}\n\n"
            "Safety boundary:\n"
            "- CLI/main.py remains the source of truth.\n"
            "- The UI does not call Commander Spellbook or any external API here.\n"
            "- The UI captures stdout, stderr, and return code.\n"
            "- shell=True is not used.\n"
            f"- The UI will send output mode {self.cli_output_mode_input_value()} for {self.state.output_mode}, then review direction {self.cli_review_direction_input_value()} for {self.state.review_direction}.\n"
            f"- If Review Direction is Build up, the UI will also send build-up mode {self.cli_build_up_mode_input_value()} for {self.state.build_up_mode}.\n"
            f"- If the known CLI path reaches Prompt Mode, the UI will send prompt mode {self.cli_prompt_mode_input_value()} for {self.state.prompt_mode}.\n"
            f"- If the known CLI path reaches Philosophy Lens, the UI will send philosophy lens {self.cli_philosophy_lens_input_value()} for {self.state.selected_philosophy}.\n"
            f"- If Specific philosophy subtype is selected, the UI will send subtype answer {self.cli_philosophy_subtype_input_value()} for {self.state.philosophy_subtype}.\n"
            f"- If the known CLI path reaches Guide Presentation, the UI will send guide presentation {self.cli_guide_presentation_input_value()} for {self.state.guide_presentation}.\n"
            f"- If the known CLI path reaches Collection Mode, the UI will send collection mode {self.cli_collection_mode_input_value()} for {self.state.collection_mode}.\n"
            f"- If collection is enabled and the known CLI path reaches Collection Source, the UI will send collection source {self.cli_collection_source_input_value()} for {self.state.collection_source_mode}.\n"
            "- Specific philosophy subtypes are answered only when the optional subtype dropdown is set away from None / top-level only.\n"
            "- The selected Deck Selection file is handed to main.py through MTG_DECK_FILE.\n"
            "- Collection folder/file readiness is normalized before the run: Entire collection folder uses the staged folder/default backend path, while Select collection files sends only explicit selected file payloads.\n"
            "- stdin is closed after the known answers, so the next unknown interactive prompt may produce EOF and be captured safely.\n\n"
            "Run py main.py now?"
        )
        answer = QMessageBox.question(self, "Confirm Guarded Backend Run", message, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            self.state.last_guarded_run_status = "Guarded run cancelled by user before execution."
            self.refresh_run_analysis_previews()
            return

        self.state.guarded_run_in_progress = True
        self.state.last_guarded_run_started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.state.last_guarded_run_finished_at = "Running"
        self.state.last_guarded_run_status = "Running py main.py with guarded confirmation..."
        self.state.last_guarded_run_return_code = "Running"
        self.state.last_guarded_run_stdout = "Waiting for stdout..."
        self.state.last_guarded_run_stderr = "Waiting for stderr..."
        self.clear_detected_report_outputs()
        self.backend_process_stdout = ""
        self.backend_process_stderr = ""
        self.backend_process_timed_out = False
        self.guarded_cli_input_sent = False
        self.state.cli_input_bridge_last_sent = "Pending full known CLI bridge inputs..."
        self.refresh_run_analysis_previews()

        process = QProcess(self)
        self.backend_process = process
        process.setWorkingDirectory(self.state.backend_working_directory)
        process_env = QProcessEnvironment.systemEnvironment()
        process_env.insert("MTG_DECK_FILE", self.state.selected_deck_path)
        process.setProcessEnvironment(process_env)
        process.setProgram("py")
        process.setArguments([self.state.backend_entrypoint])
        process.setProcessChannelMode(QProcess.SeparateChannels)
        process.readyReadStandardOutput.connect(self.capture_guarded_stdout)
        process.readyReadStandardError.connect(self.capture_guarded_stderr)
        process.finished.connect(self.finish_guarded_backend_run)
        process.errorOccurred.connect(self.handle_guarded_process_error)
        process.start()
        QTimer.singleShot(75, self.send_known_cli_inputs_to_guarded_process)
        QTimer.singleShot(300000, self.timeout_guarded_backend_run)

    def send_known_cli_inputs_to_guarded_process(self):
        """Send known CLI answers, then close stdin to avoid hanging on unknown prompts."""
        if self.backend_process is None or not self.state.guarded_run_in_progress or self.guarded_cli_input_sent:
            return
        self.normalize_collection_source_for_guarded_run()
        input_lines = []
        sent_parts = []

        if self.state.selected_deck_path != "No deck file selected":
            sent_parts.append(f"handed selected deck to main.py via MTG_DECK_FILE: {self.state.selected_deck_path}")

        output_value = self.cli_output_mode_input_value()
        input_lines.append(output_value)
        sent_parts.append(f"sent output-mode answer {output_value} for UI Output Mode: {self.state.output_mode}")

        direction_value = self.cli_review_direction_input_value()
        input_lines.append(direction_value)
        sent_parts.append(f"sent review-direction answer {direction_value} for UI Review Direction: {self.state.review_direction}")

        if self.state.review_direction == "Build up":
            build_up_value = self.cli_build_up_mode_input_value()
            input_lines.append(build_up_value)
            sent_parts.append(f"sent build-up-mode answer {build_up_value} for UI Build-Up Mode: {self.state.build_up_mode}")
        elif self.state.review_direction in {"Cut down", "Auto batch"}:
            intensity_value = self.cli_review_intensity_input_value()
            input_lines.append(intensity_value)
            sent_parts.append(f"sent review-intensity/cut-strictness answer {intensity_value} for UI Review Intensity: {self.state.cut_depth}")
        else:
            sent_parts.append("no mode-specific answer sent because Review Direction was not recognized")

        if self.should_send_prompt_mode_input():
            prompt_value = self.cli_prompt_mode_input_value()
            input_lines.append(prompt_value)
            sent_parts.append(f"sent prompt-mode answer {prompt_value} for UI Prompt Mode: {self.state.prompt_mode}")
        else:
            sent_parts.append("prompt-mode answer not sent until prior prompts are mapped for this review direction")

        if self.should_send_philosophy_lens_input():
            philosophy_value = self.cli_philosophy_lens_input_value()
            input_lines.append(philosophy_value)
            sent_parts.append(f"sent philosophy-lens answer {philosophy_value} for UI Philosophy Lens: {self.state.selected_philosophy}")
            if self.should_send_philosophy_subtype_input():
                subtype_value = self.cli_philosophy_subtype_input_value()
                if subtype_value:
                    input_lines.append(subtype_value)
                    sent_parts.append(f"sent philosophy-subtype answer {subtype_value} for UI Philosophy Subtype: {self.state.philosophy_subtype}")
                else:
                    sent_parts.append(f"philosophy-subtype answer not sent because subtype mapping was unavailable for: {self.state.philosophy_subtype}")
        else:
            sent_parts.append("philosophy-lens answer not sent until prompt mode is safely bridged for this direction")

        if self.should_send_guide_presentation_input():
            guide_value = self.cli_guide_presentation_input_value()
            input_lines.append(guide_value)
            sent_parts.append(f"sent guide-presentation answer {guide_value} for UI Guide Presentation: {self.state.guide_presentation}")
        else:
            sent_parts.append("guide-presentation answer not sent until philosophy lens is safely bridged")

        if self.should_send_collection_mode_input():
            collection_value = self.cli_collection_mode_input_value()
            input_lines.append(collection_value)
            sent_parts.append(f"sent collection-mode answer {collection_value} for UI Collection Mode: {self.state.collection_mode}")
        else:
            sent_parts.append("collection-mode answer not sent until guide presentation is safely bridged")

        if self.should_send_collection_source_input():
            collection_source_value = self.cli_collection_source_input_value()
            input_lines.append(collection_source_value)
            sent_parts.append(f"sent collection-source answer {collection_source_value} for UI Collection Source: {self.state.collection_source_mode}")
            # Normalize active source behavior: entire-folder mode does not send stale selected files,
            # while selected-file mode sends only the files explicitly staged in the UI.
            if self.state.collection_source_mode == "Entire collection folder":
                sent_parts.append(f"using entire collection folder detail: {self.state.collection_folder}; selected-file payload not sent")
            elif self.state.collection_source_mode == "Select collection files" and self.state.selected_collection_files:
                file_payload = ";".join(str(Path(path)) for path in self.state.selected_collection_files)
                input_lines.append(file_payload)
                sent_parts.append(f"sent selected-collection-file path payload for {len(self.state.selected_collection_files)} file(s)")
            elif self.state.collection_source_mode == "Select collection files":
                sent_parts.append("selected collection files source was active but no files were staged; no file payload sent")
        else:
            sent_parts.append("collection-source answer not sent because collection mode is No collection or not safely bridged yet")

        self.backend_process.write(("\n".join(input_lines) + "\n").encode("utf-8"))
        self.backend_process.closeWriteChannel()
        self.guarded_cli_input_sent = True
        self.state.cli_input_bridge_last_sent = "; ".join(sent_parts)
        self.refresh_run_analysis_previews()

    def capture_guarded_stdout(self):
        if self.backend_process is None:
            return
        data = bytes(self.backend_process.readAllStandardOutput()).decode(errors="replace")
        self.backend_process_stdout += data
        self.state.last_guarded_run_stdout = self.trim_process_output(self.backend_process_stdout)
        self.refresh_run_analysis_previews()

    def capture_guarded_stderr(self):
        if self.backend_process is None:
            return
        data = bytes(self.backend_process.readAllStandardError()).decode(errors="replace")
        self.backend_process_stderr += data
        self.state.last_guarded_run_stderr = self.trim_process_output(self.backend_process_stderr)
        self.refresh_run_analysis_previews()

    def timeout_guarded_backend_run(self):
        if self.backend_process is not None and self.state.guarded_run_in_progress:
            self.backend_process_timed_out = True
            self.backend_process.kill()

    def finish_guarded_backend_run(self, exit_code, exit_status):
        self.state.guarded_run_in_progress = False
        self.state.last_guarded_run_finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.state.last_guarded_run_return_code = str(exit_code)
        self.state.last_guarded_run_stdout = self.trim_process_output(self.backend_process_stdout or "No stdout captured.")
        self.state.last_guarded_run_stderr = self.trim_process_output(self.backend_process_stderr or "No stderr captured.")
        self.detect_report_outputs_from_stdout(self.backend_process_stdout or "")
        if self.backend_process_timed_out:
            self.state.last_guarded_run_status = "Timed out. The guarded bridge killed the process after the timeout window."
        elif exit_code == 0:
            self.state.last_guarded_run_status = "Completed successfully. Report output detection completed; review stdout or open detected folders below."
        else:
            self.state.last_guarded_run_status = "Completed with an error or non-zero return code. Review stderr/stdout below."
        self.backend_process = None
        self.refresh_run_analysis_previews()
        QMessageBox.information(self, "Guarded Run Finished", self.state.last_guarded_run_status)

    def handle_guarded_process_error(self, error):
        self.state.guarded_run_in_progress = False
        self.state.last_guarded_run_finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.state.last_guarded_run_status = f"Process failed to start or crashed: {error}"
        self.state.last_guarded_run_return_code = "Process error"
        self.state.last_guarded_run_stdout = self.trim_process_output(self.backend_process_stdout or "No stdout captured.")
        self.state.last_guarded_run_stderr = self.trim_process_output(self.backend_process_stderr or "No stderr captured.")
        self.detect_report_outputs_from_stdout(self.backend_process_stdout or "")
        self.backend_process = None
        self.refresh_run_analysis_previews()
        QMessageBox.warning(self, "Guarded Run Failed", self.state.last_guarded_run_status)

    def trim_process_output(self, text, limit=6000):
        text = text or ""
        if len(text) <= limit:
            return text
        return text[-limit:] + "\n\n... output truncated to the most recent captured text ..."

    def combo_tracker_preview_text(self):
        """Preview the future optional Commander Spellbook combo tracker. No API calls."""
        deck_path = self.state.selected_deck_path if self.state.selected_deck_path != "No deck file selected" else "None"
        deck_loaded = deck_path != "None"
        deck_signature_preview = "No deck file loaded"
        if deck_loaded:
            deck_signature_preview = f"{Path(deck_path).name} | size_preview={self.state.deck_size} | commander={self.state.commander}"

        return (
            "Optional Combo Tracker Preview\n"
            "- Future integration target -> Commander Spellbook API\n"
            "- Current patch behavior -> placeholder only\n"
            "- External API calls -> disabled\n"
            "- Automatic combo lookup during normal deck review -> disabled\n"
            "- User opt-in required -> True\n\n"
            "Intended Future Behavior\n"
            "- Combo lookup should run only when the user clicks a dedicated button.\n"
            "- If the decklist has not changed since the last combo check, the button should be disabled or report deck unchanged.\n"
            "- Local state should track the last checked decklist signature/hash.\n"
            "- The UI should avoid repeated API pings for the same unchanged decklist.\n"
            "- Normal deck analysis should remain separate from combo lookup.\n\n"
            "Future Result Targets\n"
            "- total_combos_found\n"
            "- combo names\n"
            "- combo pieces\n"
            "- combo steps, if returned by the API\n"
            "- whether each combo is fully contained within the current deck\n"
            "- optional notes for partial/missing pieces later\n\n"
            "Current Deck Change Preview\n"
            f"- deck_loaded -> {deck_loaded}\n"
            f"- deck_signature_preview -> {deck_signature_preview}\n"
            "- last_combo_check_signature -> Not stored in this patch\n"
            "- combo_check_button_state -> Disabled / placeholder in this patch\n"
            "- commander_spellbook_request_allowed -> False"
        )

    def backend_runtime_config_boundary_text(self):
        return (
            "v0.6.7.9.14 boundary\n"
            "- This page now includes a guarded execution bridge with controlled stdin inputs across the selected deck handoff.\n"
            "- The future backend entrypoint preview now points to main.py.\n"
            "- deck_helper.py is retained only as a legacy/older-name reference in the bridge preview.\n"
            "- The runtime-config handoff contract, safe backend bridge preview, and combo tracker remain preview/disabled. Guarded execution can run main.py only after confirmation.\n"
            "- The Combo Tracker is an optional future Commander Spellbook workflow and does not call any API here.\n"
            "- Backend execution is guarded and confirmation-gated through CLI/main.py only; Commander Spellbook API calls, direct UI Scryfall lookup, direct UI legality validation, direct UI collection loading, direct UI strategy detection, direct UI cuts/replacements, and direct UI report writing remain disconnected.\n"
            "- This patch detects report file paths from the backend Files written stdout block. The backend now writes directly into unique deck-file-distinguished run folders, so the UI no longer relocates report files."
        )

    def run_readiness_text(self):
        deck_ready = self.state.selected_deck_path != "No deck file selected"
        commander_ready = self.state.commander_detected
        collection_ready = self.state.collection_source_note != "Collection source not staged yet." or self.state.collection_mode == "No collection"
        return (
            f"{'✓' if deck_ready else '⚠'} Deck file selected: {'Yes' if deck_ready else 'No'}\n"
            f"{'✓' if commander_ready else '⚠'} Commander detected in preview: {'Yes' if commander_ready else 'No'}\n"
            "✓ Review settings staged: UI defaults or applied values are available\n"
            f"{'✓' if collection_ready else '⚠'} Collection source staged or optional: {'Yes' if collection_ready else 'No'}\n"
            "✓ Philosophy lens available: Yes\n"
            "⚠ Backend execution: guarded confirmation required"
        )

    def run_placeholder_message(self):
        QMessageBox.information(
            self,
            "Run Analysis Backend Hook Prepared",
            f"{APP_VERSION} has gathered staged UI choices and can run py main.py only through the guarded confirmation button. This preview button does not run the backend. Use Guarded Execution to review the command and the full known CLI input bridge before starting a confirmed run."
        )

    def page_run_review(self):
        page, layout = self.page_container(
            "Run Analysis",
            f"Run py main.py only through a guarded confirmation path. {APP_VERSION} captures stdout/stderr and keeps Commander Spellbook/API calls disabled."
        )
        body = QWidget(); body_layout = QHBoxLayout(body); body_layout.setContentsMargins(0, 0, 0, 0); body_layout.setSpacing(14)

        left = TexturedPanel(self.theme, kind="iron", glow=True); add_shadow(left, blur=28, y=8)
        l_layout = QVBoxLayout(left); l_layout.setContentsMargins(24, 24, 24, 24); l_layout.setSpacing(16)
        run_btn = QPushButton("🔥 Prepare Backend Run Preview")
        run_btn.setObjectName("primaryButton")
        run_btn.setMinimumHeight(64)
        run_btn.clicked.connect(self.run_placeholder_message)
        l_layout.addWidget(run_btn)
        guarded_btn = QPushButton("🛡 Guarded Execution Preview")
        guarded_btn.setMinimumHeight(48)
        guarded_btn.clicked.connect(self.guarded_execution_placeholder_message)
        l_layout.addWidget(guarded_btn)
        run_guarded_btn = QPushButton("Run main.py with Guarded Confirmation")
        run_guarded_btn.setObjectName("primaryButton")
        run_guarded_btn.setMinimumHeight(52)
        run_guarded_btn.clicked.connect(self.start_guarded_backend_run)
        self.guarded_run_button = run_guarded_btn
        self.guarded_run_buttons.append(run_guarded_btn)
        l_layout.addWidget(run_guarded_btn)

        readiness = ReportCard("Backend Readiness Checklist", self.theme, badges=[("No engine call", "manual")])
        readiness_box = self.readonly_text_box(self.run_readiness_text(), min_height=110, max_height=155)
        readiness_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        readiness.body.addWidget(readiness_box)
        l_layout.addWidget(readiness, stretch=0)

        bridge_status = ReportCard("Bridge Status", self.theme, badges=[("main.py preview", "manual"), ("Execution disabled", "protected")])
        bridge_status_box = self.readonly_text_box(
            "Future backend entrypoint preview: main.py\n"
            "Legacy name note: deck_helper.py was the older reference.\n"
            "Current patch: confirmed QProcess run path is available. No shell=True, no direct external API calls.\n"
            "Combo Tracker: optional future Commander Spellbook workflow, not part of normal deck review.",
            min_height=105,
            max_height=150
        )
        bridge_status_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        bridge_status.body.addWidget(bridge_status_box)
        l_layout.addWidget(bridge_status, stretch=0)

        orb_panel = TexturedPanel(self.theme, kind="iron_2", glow=True, corners=False)
        orb_layout = QVBoxLayout(orb_panel); orb_layout.setContentsMargins(12, 12, 12, 12)
        orb = ForgeOrb(self.theme)
        orb.setMinimumSize(190, 190)
        orb.setMaximumHeight(230)
        orb_layout.addWidget(orb, stretch=1)
        status = QLabel("The forge is staged, not fired. Dense preview details now live behind the detail selector on the right.")
        status.setObjectName("helperText"); status.setAlignment(Qt.AlignCenter); status.setWordWrap(True)
        orb_layout.addWidget(status)
        l_layout.addWidget(orb_panel, stretch=1)

        right = TexturedPanel(self.theme, kind="iron", glow=False); add_shadow(right, blur=28, y=8)
        r_layout = QVBoxLayout(right); r_layout.setContentsMargins(24, 24, 24, 24); r_layout.setSpacing(14)
        title = QLabel("Current Run Summary"); title.setObjectName("sectionTitle"); r_layout.addWidget(title)
        preview = QPlainTextEdit(); preview.setReadOnly(True); preview.setPlainText(self.run_config_preview_text()); preview.setMinimumHeight(180); preview.setMaximumHeight(240); preview.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded); preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        preview.setObjectName("runConfigPreview")
        self.run_config_preview_box = preview
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
        detail_selector.addItems([
            "Runtime Contract",
            "Bridge Preview",
            "Combo Tracker",
            "Guarded Execution",
            "Run Output / Result",
            "Report Output",
            "Safety Boundary",
        ])
        detail_selector.setMinimumWidth(260)
        detail_selector.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.configure_combo_popup(detail_selector)
        detail_selector.currentIndexChanged.connect(detail_stack.setCurrentIndex)
        selector_row.addWidget(detail_selector, stretch=1)
        selector_note = self.default_note("Use this selector instead of horizontal tabs so the detail view stays usable at narrower widths.")
        selector_row.addWidget(selector_note)
        r_layout.addLayout(selector_row)

        mapping_card = ReportCard("Backend Runtime Config Contract Preview", self.theme, badges=[("UI-only", "manual"), ("No engine call", "protected")])
        mapping_box = QPlainTextEdit()
        mapping_box.setReadOnly(True)
        mapping_box.setPlainText(self.backend_runtime_config_mapping_text())
        mapping_box.setMinimumHeight(260)
        mapping_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        mapping_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        mapping_box.setObjectName("runtimeMappingPreview")
        self.runtime_mapping_preview_box = mapping_box
        mapping_card.body.addWidget(mapping_box)
        detail_stack.addWidget(mapping_card)

        bridge_card = ReportCard("Safe Backend Bridge Preview", self.theme, badges=[("Preview only", "manual"), ("Execution disabled", "protected")])
        bridge_box = QPlainTextEdit()
        bridge_box.setReadOnly(True)
        bridge_box.setPlainText(self.backend_bridge_preview_text())
        bridge_box.setMinimumHeight(260)
        bridge_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        bridge_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        bridge_box.setObjectName("backendBridgePreview")
        self.backend_bridge_preview_box = bridge_box
        bridge_card.body.addWidget(bridge_box)
        detail_stack.addWidget(bridge_card)

        combo_card = ReportCard("Optional Combo Tracker", self.theme, badges=[("Commander Spellbook later", "manual"), ("Opt-in", "protected")])
        combo_box = QPlainTextEdit()
        combo_box.setReadOnly(True)
        combo_box.setPlainText(self.combo_tracker_preview_text())
        combo_box.setMinimumHeight(250)
        combo_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        combo_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        combo_box.setObjectName("comboTrackerPreview")
        self.combo_tracker_preview_box = combo_box
        combo_card.body.addWidget(combo_box)
        combo_btn = QPushButton("Check Combos Later — Disabled Placeholder")
        combo_btn.setEnabled(False)
        combo_card.body.addWidget(combo_btn)
        combo_card.body.addWidget(self.default_note("Future behavior: only ping Commander Spellbook after explicit user click, and only when the decklist has changed since the last combo check."))
        detail_stack.addWidget(combo_card)

        guarded_card = ReportCard("Guarded Execution Bridge", self.theme, badges=[("Preview only", "manual"), ("subprocess disabled", "protected")])
        guarded_box = QPlainTextEdit()
        guarded_box.setReadOnly(True)
        guarded_box.setPlainText(self.guarded_execution_preview_text())
        guarded_box.setMinimumHeight(260)
        guarded_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        guarded_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        guarded_box.setObjectName("guardedExecutionPreview")
        self.guarded_execution_preview_box = guarded_box
        guarded_card.body.addWidget(guarded_box)
        guarded_preview_btn = QPushButton("Validate Guarded Run Preview — No Execution")
        guarded_preview_btn.clicked.connect(self.guarded_execution_placeholder_message)
        guarded_card.body.addWidget(guarded_preview_btn)
        guarded_run_btn = QPushButton("Run main.py with Guarded Confirmation")
        guarded_run_btn.setObjectName("primaryButton")
        guarded_run_btn.clicked.connect(self.start_guarded_backend_run)
        guarded_card.body.addWidget(guarded_run_btn)
        self.guarded_run_button = guarded_run_btn
        self.guarded_run_buttons.append(guarded_run_btn)
        guarded_card.body.addWidget(self.default_note("Run requires explicit confirmation. It uses QProcess, captures stdout/stderr, and does not call Commander Spellbook/API."))
        detail_stack.addWidget(guarded_card)

        result_card = ReportCard("Guarded Run Output / Result", self.theme, badges=[("Captured", "manual"), ("Review after run", "protected")])
        result_box = QPlainTextEdit()
        result_box.setReadOnly(True)
        result_box.setPlainText(self.guarded_run_result_text())
        result_box.setMinimumHeight(260)
        result_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        result_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        result_box.setObjectName("guardedRunResultPreview")
        self.guarded_run_result_box = result_box
        result_card.body.addWidget(result_box)
        result_card.body.addWidget(self.default_note("This output is captured from the guarded py main.py process. Report file paths are detected from stdout after successful runs."))
        detail_stack.addWidget(result_card)

        report_output_card = ReportCard("Report Output Detection", self.theme, badges=[("Path detection", "manual"), ("No parsing yet", "protected")])
        report_output_box = QPlainTextEdit()
        report_output_box.setReadOnly(True)
        report_output_box.setPlainText(self.report_output_summary_text())
        report_output_box.setMinimumHeight(220)
        report_output_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        report_output_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        report_output_box.setObjectName("reportOutputPreview")
        self.report_output_preview_box = report_output_box
        report_output_card.body.addWidget(report_output_box)
        open_row = QHBoxLayout()
        open_output_btn = QPushButton("Open Output Folder")
        open_output_btn.clicked.connect(self.open_last_output_folder)
        open_normal_btn = QPushButton("Open Normal Report Folder")
        open_normal_btn.clicked.connect(self.open_last_normal_report_folder)
        open_debug_btn = QPushButton("Open Debug Report Folder")
        open_debug_btn.clicked.connect(self.open_last_debug_report_folder)
        self.open_output_folder_button = open_output_btn
        self.open_normal_report_folder_button = open_normal_btn
        self.open_debug_report_folder_button = open_debug_btn
        self.refresh_report_output_buttons()
        open_row.addWidget(open_output_btn)
        open_row.addWidget(open_normal_btn)
        open_row.addWidget(open_debug_btn)
        report_output_card.body.addLayout(open_row)
        report_output_card.body.addWidget(self.default_note("Folder buttons use detected paths from the backend Files written block. Report contents are not parsed in this patch."))
        detail_stack.addWidget(report_output_card)

        boundary_card = ReportCard("Safety Boundary and Future Stages", self.theme, badges=[("v0.6.7.9.18", "manual")])
        stage_text = (
            "Future Backend Bridge Stages\n"
            "1. Runtime config contract is visible and refreshes live.\n"
            "2. Safe backend bridge preview is visible and refreshes live.\n"
            "3. Optional Combo Tracker placeholder is visible but API calls are disabled.\n"
            "4. Backend command execution is still disabled.\n"
            "5. A later guarded execution patch must preserve explicit user approval, error capture, and CLI source-of-truth boundaries.\n"
            "6. Report generation is still handled only by the locked CLI backend.\n\n"
            f"{self.backend_runtime_config_boundary_text()}"
        )
        boundary_box = self.readonly_text_box(stage_text, min_height=260, max_height=520)
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

    def update_progress_mock(self):
        if not self.progress_bars or self.stack.currentIndex() != self.RUN_REVIEW: return
        self.progress_tick += 1
        for i, bar in enumerate(self.progress_bars): bar.setValue(min(100, (self.progress_tick * (i + 2) + i * 17) % 120))

    def detected_report_file_entries(self):
        """Return detected report files as display entries without parsing report sections."""
        entries = []
        for path_text in self.state.last_normal_report_files:
            entries.append(("Normal", path_text))
        for path_text in self.state.last_debug_report_files:
            entries.append(("Debug", path_text))
        # Include any detected report files that did not classify cleanly.
        known = {str(Path(path)) for _category, path in entries}
        for path_text in self.state.last_output_files:
            normalized = str(Path(path_text))
            if normalized not in known:
                entries.append(("Other", path_text))
        return entries

    def report_file_button_label(self, category, path_text):
        """Return a compact, readable file-list label while keeping the full path in the tooltip."""
        name = Path(path_text).name
        lower = name.lower()
        if "_deck_report" in lower:
            role = "Deck Report"
        elif "_user_guided_prompt" in lower:
            role = "User Prompt"
        elif "_full_debug_report" in lower:
            role = "Full Debug"
        elif "_legality_debug" in lower:
            role = "Legality Debug"
        elif "_strategy_debug" in lower:
            role = "Strategy Debug"
        elif "_bracket_debug" in lower:
            role = "Bracket Debug"
        elif "_cut_pressure_debug" in lower:
            role = "Cut Pressure Debug"
        elif "_replacement_prompt_debug" in lower:
            role = "Replacement Debug"
        elif "_diagnostics_debug" in lower:
            role = "Diagnostics Debug"
        else:
            # Fallback keeps the label readable without forcing horizontal scrolling.
            stem = Path(path_text).stem
            role = stem[-34:] if len(stem) > 34 else stem
        return f"{category}: {role}"

    def clear_layout_widgets(self, layout):
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                self.clear_layout_widgets(child_layout)

    def read_report_file_text(self, path_text):
        path = Path(path_text)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Report file does not exist: {path}")
        for encoding in ("utf-8-sig", "utf-8", "cp1252"):
            try:
                return path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
        return path.read_text(errors="replace")

    def load_report_file_into_viewer(self, path_text):
        path = Path(path_text)
        try:
            text = self.read_report_file_text(path_text)
            self.state.report_viewer_current_file = str(path)
            self.state.report_viewer_current_text = text
            self.state.report_viewer_current_status = f"Loaded report file: {path.name}"
        except Exception as exc:
            self.state.report_viewer_current_file = str(path)
            self.state.report_viewer_current_text = f"Could not load report file:\n{path}\n\n{exc}"
            self.state.report_viewer_current_status = "Report file load failed."
        if self.report_viewer_text_box is not None:
            self.report_viewer_text_box.setPlainText(self.state.report_viewer_current_text)
        if self.report_viewer_status_label is not None:
            self.report_viewer_status_label.setPlainText(self.report_viewer_status_text())
            self.report_viewer_status_label.setToolTip(
                f"Current file: {self.state.report_viewer_current_file}\nOutput folder: {self.state.last_output_folder}"
            )
        if self.open_current_report_file_button is not None:
            self.open_current_report_file_button.setEnabled(Path(self.state.report_viewer_current_file).is_file())

    def report_viewer_status_text(self):
        entries = self.detected_report_file_entries()
        current = Path(self.state.report_viewer_current_file)
        output_folder = Path(self.state.last_output_folder)
        current_name = current.name if current.is_file() or self.state.report_viewer_current_file != "No report file selected" else "No report selected"
        output_name = output_folder.name if self.state.last_output_folder != "No output folder detected yet" else "No output folder detected"
        return (
            f"Status: {self.state.report_viewer_current_status}\n"
            f"Loaded file: {current_name}\n"
            f"Detected files: {len(entries)}   Output folder: {output_name}\n"
            "Boundary: plain text preview only; structured navigation and markdown rendering come later."
        )

    def refresh_report_viewer_file_list(self):
        """Populate Report Viewer with files detected from the latest guarded run."""
        if self.report_viewer_file_buttons_layout is None:
            return
        self.clear_layout_widgets(self.report_viewer_file_buttons_layout)
        entries = self.detected_report_file_entries()
        if not entries:
            empty = QLabel("No generated report files detected yet. Run main.py with guarded confirmation first.")
            empty.setObjectName("mutedText")
            empty.setWordWrap(True)
            self.report_viewer_file_buttons_layout.addWidget(empty)
        else:
            for category, path_text in entries:
                btn = QPushButton(self.report_file_button_label(category, path_text))
                btn.setObjectName("utilityButton")
                btn.setMinimumHeight(40)
                btn.setToolTip(f"{Path(path_text).name}\n{path_text}")
                btn.clicked.connect(lambda checked=False, p=path_text: self.load_report_file_into_viewer(p))
                self.report_viewer_file_buttons_layout.addWidget(btn)
        self.report_viewer_file_buttons_layout.addStretch(1)
        if self.report_viewer_status_label is not None:
            self.report_viewer_status_label.setPlainText(self.report_viewer_status_text())
            self.report_viewer_status_label.setToolTip(
                f"Current file: {self.state.report_viewer_current_file}\nOutput folder: {self.state.last_output_folder}"
            )
        if self.report_viewer_text_box is not None:
            # Auto-load the first available report when no report has been selected yet.
            current = Path(self.state.report_viewer_current_file)
            if entries and (self.state.report_viewer_current_file == "No report file selected" or not current.exists()):
                self.load_report_file_into_viewer(entries[0][1])
            else:
                self.report_viewer_text_box.setPlainText(self.state.report_viewer_current_text)
        if self.open_current_report_file_button is not None:
            self.open_current_report_file_button.setEnabled(Path(self.state.report_viewer_current_file).is_file())

    def reload_latest_reports_into_viewer(self):
        self.refresh_report_viewer_file_list()
        QMessageBox.information(
            self,
            "Report Viewer Reloaded",
            "Detected report files from the latest guarded run have been refreshed. Report contents are still shown as plain text only."
        )

    def open_current_report_file(self):
        path = Path(self.state.report_viewer_current_file)
        if not path.exists() or not path.is_file():
            QMessageBox.information(self, "No Report File Selected", "No loaded report file is available to open yet.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def page_report_viewer(self):
        page, layout = self.page_container(
            "Report Viewer",
            f"Load generated Dragon's Touch report files as plain readable text. {APP_VERSION} does not deeply parse report sections yet."
        )
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(14)

        report_nav = TexturedPanel(self.theme, kind="iron", glow=False)
        report_nav.setFixedWidth(330)
        add_shadow(report_nav, blur=22, y=7)
        rn_layout = QVBoxLayout(report_nav)
        rn_layout.setContentsMargins(16, 16, 16, 16)
        rn_layout.setSpacing(10)
        cap = QLabel("DETECTED REPORT FILES")
        cap.setObjectName("smallCaps")
        rn_layout.addWidget(cap)
        hint = QLabel("Files come from the latest successful guarded run. Click a file to load it as plain text.")
        hint.setObjectName("mutedText")
        hint.setWordWrap(True)
        rn_layout.addWidget(hint)

        file_scroll = QScrollArea()
        file_scroll.setWidgetResizable(True)
        file_inner = QWidget()
        self.report_viewer_file_buttons_layout = QVBoxLayout(file_inner)
        self.report_viewer_file_buttons_layout.setContentsMargins(0, 0, 6, 0)
        self.report_viewer_file_buttons_layout.setSpacing(8)
        file_scroll.setWidget(file_inner)
        rn_layout.addWidget(file_scroll, stretch=1)

        reload_btn = QPushButton("Reload Latest Reports")
        reload_btn.clicked.connect(self.reload_latest_reports_into_viewer)
        self.report_viewer_reload_button = reload_btn
        rn_layout.addWidget(reload_btn)

        open_folder_btn = QPushButton("Open Output Folder")
        open_folder_btn.clicked.connect(self.open_last_output_folder)
        rn_layout.addWidget(open_folder_btn)

        viewer_panel = TexturedPanel(self.theme, kind="iron", glow=True)
        add_shadow(viewer_panel, blur=26, y=8)
        viewer_layout = QVBoxLayout(viewer_panel)
        viewer_layout.setContentsMargins(22, 22, 22, 22)
        viewer_layout.setSpacing(18)

        report_text_card = ReportCard("Report File Preview", self.theme, badges=[("Markdown/text", "normal")])
        report_text_card.setMinimumHeight(430)
        report_text_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        text_box = QPlainTextEdit()
        text_box.setReadOnly(True)
        text_box.setPlainText(self.state.report_viewer_current_text)
        text_box.setMinimumHeight(300)
        text_box.setMaximumHeight(16777215)
        text_box.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        text_box.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        text_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        text_box.setObjectName("reportFilePreview")
        self.report_viewer_text_box = text_box
        report_text_card.body.addWidget(text_box, stretch=1)
        viewer_layout.addWidget(report_text_card, stretch=4)

        status_card = ReportCard("Loaded Report Status", self.theme, badges=[("Plain text", "manual"), ("No deep parsing", "protected")])
        status_card.setMinimumHeight(190)
        status_card.setMaximumHeight(255)
        status_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        status_label = QPlainTextEdit()
        status_label.setReadOnly(True)
        status_label.setPlainText(self.report_viewer_status_text())
        status_label.setObjectName("reportStatusPreview")
        status_label.setMinimumHeight(86)
        status_label.setMaximumHeight(125)
        status_label.setFrameShape(QFrame.NoFrame)
        status_label.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        status_label.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        status_label.setToolTip(
            f"Current file: {self.state.report_viewer_current_file}\nOutput folder: {self.state.last_output_folder}"
        )
        self.report_viewer_status_label = status_label
        status_card.body.addWidget(status_label)
        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 6, 0, 0)
        action_row.addStretch(1)
        open_file_btn = QPushButton("Open Current Report File")
        open_file_btn.clicked.connect(self.open_current_report_file)
        self.open_current_report_file_button = open_file_btn
        open_file_btn.setEnabled(Path(self.state.report_viewer_current_file).is_file())
        action_row.addWidget(open_file_btn, stretch=0, alignment=Qt.AlignRight)
        status_card.body.addLayout(action_row)
        viewer_layout.addWidget(status_card, stretch=0)

        body_layout.addWidget(report_nav, stretch=0)
        body_layout.addWidget(viewer_panel, stretch=1)
        layout.addWidget(body, stretch=1)
        self.refresh_report_viewer_file_list()
        return page

    def collection_settings_summary_text(self):
        if self.state.collection_source_mode == "Select collection files":
            source_detail = f"Selected files: {len(self.state.selected_collection_files)}"
            if self.state.selected_collection_files:
                examples = "\n".join(f"  - {Path(path).name}" for path in self.state.selected_collection_files[:8])
                if len(self.state.selected_collection_files) > 8:
                    examples += f"\n  - ...and {len(self.state.selected_collection_files) - 8} more"
                source_detail += f"\n{examples}"
        else:
            source_detail = f"Folder: {self.state.collection_folder}\nDetected .txt files: {self.state.collection_txt_file_count}"
        return (
            f"Collection mode: {self.state.collection_mode}\n"
            f"Collection source: {self.state.collection_source_mode}\n"
            f"{source_detail}\n"
            f"Backend collection loader: not connected yet\n"
            f"Note: {self.state.collection_source_note}"
        )

    def refresh_collection_page_widgets(self):
        """Refresh visible collection controls quietly without rebuilding the whole shell."""
        if self.collection_mode_combo is not None and self.collection_mode_combo.currentText() != self.state.collection_mode:
            blocker = QSignalBlocker(self.collection_mode_combo)
            self.collection_mode_combo.setCurrentText(self.state.collection_mode)
            del blocker
        if self.collection_source_combo is not None and self.collection_source_combo.currentText() != self.state.collection_source_mode:
            blocker = QSignalBlocker(self.collection_source_combo)
            self.collection_source_combo.setCurrentText(self.state.collection_source_mode)
            del blocker
        if self.collection_folder_button is not None:
            self.collection_folder_button.setVisible(self.state.collection_source_mode == "Entire collection folder")
        if self.collection_files_button is not None:
            self.collection_files_button.setVisible(self.state.collection_source_mode == "Select collection files")
        summary_text = self.collection_settings_summary_text()
        for box in self.collection_preview_boxes:
            if box is not None:
                box.setPlainText(summary_text)
        self.refresh_context_panel_values()
        self.refresh_run_analysis_previews()

    def stage_collection_mode(self, mode):
        self.state.collection_mode = mode
        self.state.use_collection_settings = mode != "No collection"
        if mode == "No collection":
            self.state.collection_source_note = "Collection disabled for this staged run."
            self.state.status = "Collection disabled"
        else:
            self.state.collection_source_note = "Collection mode staged in UI. Choose or confirm a collection source before backend mapping."
            self.state.status = "Collection mode staged"
        self.refresh_collection_page_widgets()

    def stage_collection_source_mode(self, source_mode):
        self.state.collection_source_mode = source_mode
        if source_mode == "Entire collection folder":
            try:
                self.state.collection_txt_file_count = len(list(Path(self.state.collection_folder).glob("*.txt")))
            except Exception:
                self.state.collection_txt_file_count = 0
            self.state.collection_source_note = "Entire collection folder selected in UI. Choose a folder if this path is not correct."
        else:
            self.state.collection_txt_file_count = len(self.state.selected_collection_files)
            self.state.collection_source_note = "Specific collection files selected in UI. Use Select Collection Files to choose one or more .txt files."
        self.state.use_collection_settings = self.state.collection_mode != "No collection"
        self.state.status = "Collection settings auto-staged"
        self.refresh_collection_page_widgets()

    def choose_collection_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose Collection Folder", self.state.collection_folder or "")
        if not folder:
            return
        self.state.collection_folder = folder
        try:
            self.state.collection_txt_file_count = len(list(Path(folder).glob("*.txt")))
        except Exception:
            self.state.collection_txt_file_count = 0
        self.state.collection_source_mode = "Entire collection folder"
        self.state.collection_source_note = "Collection folder staged in UI. Backend loader is not connected yet."
        self.state.use_collection_settings = self.state.collection_mode != "No collection"
        self.state.status = "Collection folder auto-staged"
        self.refresh_collection_page_widgets()

    def choose_collection_files(self):
        start_dir = self.state.collection_folder if self.state.collection_folder else ""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Collection Text Files",
            start_dir,
            "Collection text files (*.txt);;All files (*)"
        )
        if not files:
            return
        self.state.selected_collection_files = files
        self.state.collection_source_mode = "Select collection files"
        self.state.collection_txt_file_count = len(files)
        self.state.collection_source_note = "Specific collection files staged in UI. Backend loader is not connected yet."
        self.state.use_collection_settings = self.state.collection_mode != "No collection"
        self.state.status = "Collection files auto-staged"
        self.refresh_collection_page_widgets()

    def stage_collection_settings(self, summary_label=None):
        """Auto-stage collection settings without requiring an Apply button or popup."""
        self.state.use_collection_settings = self.state.collection_mode != "No collection"
        if self.state.collection_mode == "No collection":
            self.state.collection_source_note = "Collection disabled for this staged run."
        elif self.state.collection_source_mode == "Entire collection folder":
            try:
                self.state.collection_txt_file_count = len(list(Path(self.state.collection_folder).glob("*.txt")))
            except Exception:
                self.state.collection_txt_file_count = 0
            self.state.collection_source_note = "Entire collection folder staged. Backend collection loader is not connected yet."
        else:
            self.state.collection_txt_file_count = len(self.state.selected_collection_files)
            self.state.collection_source_note = "Selected collection files staged. Backend collection loader is not connected yet."
        self.state.status = "Collection settings auto-staged"
        if summary_label is not None:
            summary_label.setPlainText(self.collection_settings_summary_text())
        self.refresh_collection_page_widgets()

    def page_collection_tools(self):
        page, layout = self.page_container(
            "Collection Source",
            f"Stage collection behavior for future recommendations. {APP_VERSION} auto-stages collection choices immediately but does not load owned cards yet."
        )
        scroll, content = self.scroll_content()
        body = TexturedPanel(self.theme, kind="iron", glow=False)
        add_shadow(body, blur=24, y=8)
        b_layout = QGridLayout(body)
        b_layout.setContentsMargins(22, 22, 22, 22)
        b_layout.setSpacing(16)
        b_layout.setColumnStretch(0, 1)
        b_layout.setColumnStretch(1, 1)

        mode_card = ReportCard("Collection Mode", self.theme, badges=[("Staged UI", "primary")])
        mode_card.setMinimumHeight(230)
        mode_card.body.addWidget(self.make_text(
            "Choose how owned cards should affect future recommendations once backend hooks are connected.",
            paper=True
        ))
        mode_combo = QComboBox()
        self.collection_mode_combo = mode_combo
        mode_combo.addItems(["No collection", "Prefer collection first", "Collection only", "Collection shakeup"])
        mode_combo.setCurrentText(self.state.collection_mode)
        self.configure_combo_popup(mode_combo)
        mode_combo.currentTextChanged.connect(lambda text: self.stage_collection_mode(text))
        mode_card.body.addWidget(mode_combo)
        mode_card.body.addWidget(self.default_note("Default: No collection"))
        mode_card.body.addWidget(self.make_text(
            "Collection-only still stays honest: if no owned card is a real fit, the report should say so instead of forcing a weak recommendation.",
            paper=True
        ))

        source_card = ReportCard("Collection Source", self.theme, badges=[("Local files", "normal")])
        source_card.setMinimumHeight(230)
        source_combo = QComboBox()
        self.collection_source_combo = source_combo
        source_combo.addItems(["Entire collection folder", "Select collection files"])
        source_combo.setCurrentText(self.state.collection_source_mode)
        self.configure_combo_popup(source_combo)
        source_combo.currentTextChanged.connect(lambda text: self.stage_collection_source_mode(text))
        source_card.body.addWidget(source_combo)
        source_card.body.addWidget(self.default_note("Default: Entire collection folder"))
        source_card.body.addWidget(self.make_text(
            "Only the relevant chooser is shown for the selected source mode.",
            paper=True
        ))
        folder_btn = QPushButton("Choose Collection Folder")
        self.collection_folder_button = folder_btn
        folder_btn.clicked.connect(self.choose_collection_folder)
        files_btn = QPushButton("Select Collection Files")
        self.collection_files_button = files_btn
        files_btn.clicked.connect(self.choose_collection_files)
        folder_btn.setVisible(self.state.collection_source_mode == "Entire collection folder")
        files_btn.setVisible(self.state.collection_source_mode == "Select collection files")
        source_card.body.addWidget(folder_btn)
        source_card.body.addWidget(files_btn)

        summary_card = TexturedPanel(self.theme, kind="iron_2", glow=True)
        summary_card.setMinimumHeight(245)
        s_layout = QVBoxLayout(summary_card)
        s_layout.setContentsMargins(18, 16, 18, 16)
        s_layout.setSpacing(10)
        s_title = QLabel("Collection Settings Summary")
        s_title.setObjectName("sectionTitle")
        s_layout.addWidget(s_title)
        collection_summary_box = self.readonly_text_box(self.collection_settings_summary_text(), min_height=120, max_height=155)
        self.collection_preview_boxes.append(collection_summary_box)
        s_layout.addWidget(collection_summary_box)
        s_layout.addWidget(self.default_note("Auto-staged: collection choices update immediately. No Apply button required."))

        honesty_card = ReportCard("Collection Honesty Boundary", self.theme, badges=[("v0.6.6.6 locked", "protected")])
        honesty_card.setMinimumHeight(245)
        honesty_card.body.addWidget(self.make_text(
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

    def page_batch_reports(self):
        page, layout = self.page_container("Batch / Aggregate Reports", "Future workspace for batch runs, combined deck reports, combined debug reports, and output review.")
        body = TexturedPanel(self.theme, kind="iron", glow=False); add_shadow(body, blur=24, y=8)
        b_layout = QVBoxLayout(body); b_layout.setContentsMargins(22, 22, 22, 22); b_layout.setSpacing(16)
        top = QHBoxLayout()
        for label, value in [("Batch Files", "Not selected"), ("Deck Reports", "Aggregate later"), ("Debug Reports", "Aggregate later"), ("Prompt Reports", "Not required")]:
            top.addWidget(SmallStat(label, value, self.theme))
        b_layout.addLayout(top)
        aggregate_panel = ReportCard("Aggregate Output Plan", self.theme, badges=[("v0.6.7 later", "manual")])
        aggregate_panel.body.addWidget(self.make_text(
            "The locked backend already supports useful report outputs. This page will eventually open the combined deck-report and debug-report files so you do not have to enter each deck output folder manually.",
            paper=True
        ))
        b_layout.addWidget(aggregate_panel)
        workflow = TexturedPanel(self.theme, kind="iron_2", glow=True)
        w_layout = QVBoxLayout(workflow); w_layout.setContentsMargins(18, 16, 18, 16)
        w_title = QLabel("v0.6.7 Batch UI Boundary"); w_title.setObjectName("sectionTitle"); w_layout.addWidget(w_title)
        w_layout.addWidget(self.make_text("This page is a visual foundation only. The future backend hook should call the existing batch workflow and then surface aggregate markdown/text outputs here."))
        b_layout.addWidget(workflow); b_layout.addStretch(1); layout.addWidget(body, stretch=1); return page

    def page_settings(self):
        page, layout = self.page_container("Settings", "Theme options, report detail, save location, export format, readability, and app version placeholders.")
        body = TexturedPanel(self.theme, kind="iron", glow=False); add_shadow(body, blur=24, y=8); b_layout = QVBoxLayout(body); b_layout.setContentsMargins(22, 22, 22, 22); b_layout.setSpacing(16)
        theme_card = ReportCard("Theme Options", self.theme, badges=[("Current", "primary")]); row = QHBoxLayout(); dark = QPushButton("Dragon Forge"); dark.setObjectName("primaryButton" if self.theme()["name"] == "Dragon Forge" else "utilityButton"); dark.clicked.connect(lambda: self.set_theme(DRAGON_FORGE)); light = QPushButton("Adventurer's Map"); light.setObjectName("primaryButton" if self.theme()["name"] == "Adventurer's Map" else "utilityButton"); light.clicked.connect(lambda: self.set_theme(ADVENTURERS_MAP)); self.settings_theme_buttons = [(dark, "Dragon Forge"), (light, "Adventurer's Map")]; row.addWidget(dark); row.addWidget(light); row.addStretch(1); theme_card.body.addLayout(row); theme_card.body.addWidget(self.make_text("Dragon Forge remains ember-forge dark. Adventurer’s Map now uses the Cartographer Palette: parchment, dark ink, antique brass, and deep map blue.", paper=True)); b_layout.addWidget(theme_card)
        prefs = ReportCard("UI Preferences", self.theme); pref_grid = QGridLayout(); pref_grid.addWidget(QLabel("Report Detail Level"), 0, 0); detail = QComboBox(); detail.addItems(["Short", "Normal", "Detailed", "Exhaustive"]); detail.setCurrentText("Detailed"); self.configure_combo_popup(detail); pref_grid.addWidget(detail, 0, 1); pref_grid.addWidget(QLabel("Export Format"), 1, 0); export = QComboBox(); export.addItems(["Markdown", "Text", "HTML later", "PDF later"]); self.configure_combo_popup(export); pref_grid.addWidget(export, 1, 1); pref_grid.addWidget(QLabel("Save Folder"), 2, 0); pref_grid.addWidget(QLineEdit("Outputs/"), 2, 1); prefs.body.addLayout(pref_grid); b_layout.addWidget(prefs)
        version = ReportCard("App Version", self.theme); version.body.addWidget(self.make_text(f"The Dragon’s Touch PySide6 Workstation\nVersion: {APP_VERSION}\nPhase: {APP_PHASE}\nLocked backend: {LOCKED_BACKEND_VERSION}\nBackend: guarded bridge available through explicit confirmation\nPurpose: local deck preview, selected deck handoff through MTG_DECK_FILE, review settings, normalized collection folder/file handoff, cleaned Review Setup boundaries, commander-pair preview counting, companion preview detection/handoff status, guarded-run report output detection for backend-created unique deck-file-distinguished run folders, Report Viewer plain-text file loading, runtime-config contract preview, safe backend bridge preview, guarded execution bridge, conditional Review Setup fields, CLI input bridge through Build-up, Cut-down, Auto-batch defaults, top-level/subtype Philosophy Lens, Guide Presentation, Collection Mode, and Collection Source, and optional combo-tracker placeholder while keeping external API calls disabled", paper=True)); b_layout.addWidget(version); b_layout.addStretch(1); layout.addWidget(body, stretch=1); return page


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("The Dragon's Touch")
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
