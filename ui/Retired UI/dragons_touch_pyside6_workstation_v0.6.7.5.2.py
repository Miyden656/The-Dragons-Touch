"""
The Dragon's Touch - PySide6 Desktop UI Foundation
Version: v0.6.7.5.2 — Auto-Staged Settings and Philosophy Layout Cleanup

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
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QFont, QLinearGradient, QRadialGradient
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QComboBox, QFileDialog, QFrame, QGraphicsDropShadowEffect,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListView, QMainWindow, QMessageBox,
    QPlainTextEdit, QProgressBar, QPushButton, QScrollArea, QSlider, QSizePolicy,
    QStackedWidget, QVBoxLayout, QWidget
)


APP_VERSION = "v0.6.7.5.2"
APP_PHASE = "Auto-Staged Settings and Philosophy Layout Cleanup"
BACKEND_STATUS = "Backend not connected — CLI remains stable source of truth"
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
# - v0.6.7.6 should be the first safe backend-call bridge, if the config preview checks out.
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
    "panel_text": "#24180E", "heading_text": "#7A4F1E", "section_heading_text": "#24180E", "smallcaps_text": "#8A4F13",
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
    output_mode: str = "Both"
    review_direction: str = "Cut down"
    cut_depth: str = "Normal"
    prompt_mode: str = "Interactive AI chat"
    budget_note: str = "Optional budget note, e.g. $25/card"
    respect_table_bracket: bool = False
    use_collection_settings: bool = False
    collection_mode: str = "No collection"
    collection_source_mode: str = "Entire collection folder"
    collection_folder: str = "collection"
    selected_collection_files: list[str] = field(default_factory=list)
    collection_txt_file_count: int = 0
    collection_source_note: str = "Collection source not staged yet."


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
        title.setObjectName("smallCaps")
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
        quick = QLabel("QUICK ACTIONS"); quick.setObjectName("smallCaps"); layout.addWidget(quick)
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
        title = QLabel("CURRENT DECK CONTEXT"); title.setObjectName("smallCaps"); layout.addWidget(title)
        self.context_value_labels = {}
        for label, value in [
            ("Deck", self.state.deck_name), ("Commander", self.state.commander), ("Deck Size", f"{self.state.deck_size} cards"),
            ("Bracket Estimate", self.state.bracket), ("Warnings", f"{self.state.warnings} to review"), ("Status", self.state.status),
        ]:
            stat = SmallStat(label, value, self.theme)
            self.context_value_labels[label] = stat.value_label
            layout.addWidget(stat)
        line = QFrame(); line.setObjectName("goldDivider"); line.setFixedHeight(1); layout.addWidget(line)
        notes_title = QLabel("QUICK NOTES"); notes_title.setObjectName("smallCaps"); layout.addWidget(notes_title)
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
        self.rebuild_shell()

    def set_theme(self, theme):
        self.state.theme = theme
        self.rebuild_shell(self.SETTINGS)

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
        QLabel#mutedText, QLabel#helperText {{ color: {t["muted"]}; line-height: 1.4; }} QLabel#footerText {{ color: {t["muted_2"]}; font-size: 12px; }}
        QLabel#mascotHeader {{ font-size: 32px; }} QLabel#sidebarMascot {{ font-size: 36px; }} QLabel#contextMascot {{ font-size: 42px; }}
        QLabel#statLabel {{ color: {t["muted"]}; font-size: 11px; font-weight: 700; }} QLabel#statValue {{ color: {t["text"]}; font-size: 14px; font-weight: 700; }}
        QLabel#reportTitle {{ color: {t["paper_text"]}; font-family: Georgia, serif; font-size: 22px; font-weight: 900; }} QLabel#reportBody {{ color: {t["paper_text"]}; font-size: 14px; line-height: 1.5; }}
        QLabel#warningText {{ color: {t["warning"]}; font-weight: 700; }}
        QLabel#defaultNote {{ color: {default_note_text}; font-size: 12px; font-weight: 700; padding-left: 2px; }}
        QPushButton {{ border-radius: 12px; border: 1px solid {t["border"]}; padding: 10px 14px; color: {button_text}; font-weight: 800; background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {t["iron_2"]}, stop:1 {t["bronze"]}); }}
        QPushButton:hover {{ color: {sidebar_hover_text}; border: 1px solid {t["accent_2"]}; background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {t["bronze"]}, stop:1 {t["iron_2"]}); }}
        QPushButton:pressed {{ background: {primary_start}; color: {button_pressed_text}; }} QPushButton#primaryButton {{ color: {sidebar_checked_text}; border: 1px solid {t["accent_2"]}; background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {primary_start}, stop:1 {primary_end}); font-weight: 900; }}
        QPushButton#utilityButton {{ padding: 8px 12px; font-size: 13px; color: {button_text}; }} QPushButton#sidebarButton {{ text-align: left; border-radius: 13px; padding: 12px 13px; color: {sidebar_text}; background: transparent; border: 1px solid transparent; font-weight: 800; }}
        QPushButton#sidebarButton:hover {{ color: {sidebar_hover_text}; background: {t["sidebar_2"]}; border: 1px solid {t["accent_2"]}; }} QPushButton#sidebarButton:checked {{ color: {sidebar_checked_text}; background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {sidebar_checked_start}, stop:1 {sidebar_checked_end}); border: 1px solid {t["accent_2"]}; font-weight: 900; }}
        QPushButton#pillButton {{ border-radius: 15px; padding: 7px 12px; color: {sidebar_muted}; background: {t["iron_2"]}; border: 1px solid {t["border_soft"]}; }} QPushButton#pillButton:checked {{ color: {sidebar_checked_text}; background: {sidebar_checked_start}; border: 1px solid {t["accent_2"]}; }}
        QLineEdit, QPlainTextEdit, QComboBox {{ color: {input_text}; background: {t["input"]}; border: 1px solid {t["input_border"]}; border-radius: 12px; padding: 10px; selection-background-color: {t["accent"]}; selection-color: {button_pressed_text}; combobox-popup: 0; }}
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
        self.state.warnings = summary["warnings"]
        self.state.status = "Deck preview loaded"
        self.state.deck_preview_note = summary["note"]
        self.rebuild_shell(self.DECK_SELECTION)

    def summarize_deck_preview(self, text, fallback_name):
        """Lightweight UI preview only. The locked backend remains the source of truth."""
        section = "main"
        commander = "No commander detected"
        commander_detected = False
        main_count = 0
        warnings = 0
        ignored_sections = {"sideboard", "maybeboard", "tokens", "token", "attractions", "stickers", "reference", "references"}
        commander_sections = {"commander", "commanders", "command zone", "command-zone"}

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
            if section_key in commander_sections and not commander_detected:
                commander = name
                commander_detected = True
                continue
            if section_key in ignored_sections:
                continue
            main_count += qty

        if not commander_detected:
            # Fallback: many simple deck exports put the commander as the first card or include it in the filename.
            for raw in text.splitlines():
                qty, name = self.parse_deck_line(raw.strip())
                if name:
                    commander = "No commander detected"
                    break

        if main_count == 0:
            warnings += 1
        if main_count and main_count != 100:
            warnings += 1
        if not commander_detected:
            warnings += 1

        if main_count == 100 and commander_detected:
            note = "Preview loaded. Deck appears to have 100 counted main-deck cards and a commander section. Backend validation still required."
        elif main_count == 0:
            note = "Preview loaded, but no counted card lines were detected by the lightweight UI preview. Backend parser may still handle this format later."
        else:
            note = "Preview loaded. Count and commander detection are lightweight UI estimates only; backend validation still required."

        return {
            "deck_name": fallback_name,
            "commander": commander,
            "commander_detected": commander_detected,
            "deck_size": main_count,
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
            f"Deck size estimate: {self.state.deck_size} card(s)\n"
            f"Commander section detected: {commander_status}\n"
            f"Backend validation: Not run\n"
            f"Note: {self.state.deck_preview_note}"
        )

    def review_settings_summary_text(self):
        collection_line = f"{self.state.collection_mode} / {self.state.collection_source_mode}" if self.state.use_collection_settings else "Collection setting not staged here"
        bracket_line = "Respect stated table bracket" if self.state.respect_table_bracket else "No table-bracket checkbox selected"
        return (
            f"Output mode: {self.state.output_mode}\n"
            f"Review direction: {self.state.review_direction}\n"
            f"Cut depth: {self.state.cut_depth}\n"
            f"Prompt mode: {self.state.prompt_mode}\n"
            f"Budget note: {self.state.budget_note}\n"
            f"Table boundary: {bracket_line}\n"
            f"Collection handoff: {collection_line}\n"
            "Backend config mapping: not connected yet"
        )

    def stage_review_settings(self, output_combo, direction_combo, cut_combo, prompt_combo, budget_input, bracket_check, collection_check, summary_label=None):
        """Auto-stage Review Setup choices without requiring an Apply button or popup."""
        self.state.output_mode = output_combo.currentText()
        self.state.review_direction = direction_combo.currentText()
        self.state.cut_depth = cut_combo.currentText()
        self.state.prompt_mode = prompt_combo.currentText()
        self.state.budget_note = budget_input.text().strip() or "No budget note provided"
        self.state.respect_table_bracket = bracket_check.isChecked()
        self.state.use_collection_settings = collection_check.isChecked()
        self.state.status = "Review settings auto-staged"
        if summary_label is not None:
            summary_label.setText(self.review_settings_summary_text())
        self.refresh_context_panel_values()

    def page_analysis_setup(self):
        page, layout = self.page_container(
            "Review Setup",
            f"Stage the same review choices the CLI already supports. {APP_VERSION} auto-stages choices as you change them; backend mapping still comes later."
        )
        scroll, content = self.scroll_content()
        grid_panel = TexturedPanel(self.theme, kind="iron", glow=False); add_shadow(grid_panel, blur=24, y=8)
        grid = QGridLayout(grid_panel); grid.setContentsMargins(22, 22, 22, 22); grid.setSpacing(16)

        output_card = ReportCard("Output Mode", self.theme)
        output_combo = QComboBox(); output_combo.addItems(["Normal User Mode", "Debug / Stress-Test Mode", "Both"]); output_combo.setCurrentText(self.state.output_mode); self.configure_combo_popup(output_combo)
        output_card.body.addWidget(output_combo); output_card.body.addWidget(self.default_note("Default: Both")); grid.addWidget(output_card, 0, 0)

        direction_card = ReportCard("Review Direction", self.theme)
        direction_combo = QComboBox(); direction_combo.addItems(["Build up", "Cut down", "Auto batch"]); direction_combo.setCurrentText(self.state.review_direction); self.configure_combo_popup(direction_combo)
        direction_card.body.addWidget(direction_combo); direction_card.body.addWidget(self.default_note("Default: Cut down")); grid.addWidget(direction_card, 0, 1)

        cut_card = ReportCard("Cut Depth", self.theme)
        cut_combo = QComboBox(); cut_combo.addItems(["Light", "Normal", "Strict", "Brutal / Deep Review", "Rebuild"]); cut_combo.setCurrentText(self.state.cut_depth); self.configure_combo_popup(cut_combo)
        cut_card.body.addWidget(cut_combo); cut_card.body.addWidget(self.default_note("Default: Normal")); grid.addWidget(cut_card, 1, 0)

        prompt_card = ReportCard("Prompt Mode", self.theme)
        prompt_combo = QComboBox(); prompt_combo.addItems(["Interactive AI chat", "One-shot worksheet"]); prompt_combo.setCurrentText(self.state.prompt_mode); self.configure_combo_popup(prompt_combo)
        prompt_card.body.addWidget(prompt_combo); prompt_card.body.addWidget(self.default_note("Default: Interactive AI chat")); grid.addWidget(prompt_card, 1, 1)

        budget_card = ReportCard("Table / Budget Boundaries", self.theme)
        budget_input = QLineEdit(self.state.budget_note)
        bracket_check = QCheckBox("Respect stated table bracket")
        bracket_check.setChecked(self.state.respect_table_bracket)
        collection_check = QCheckBox("Use Collection Source page settings when connected")
        collection_check.setChecked(self.state.use_collection_settings)
        budget_card.body.addWidget(budget_input)
        budget_card.body.addWidget(bracket_check)
        budget_card.body.addWidget(collection_check)
        budget_card.body.addWidget(self.default_note("Collection mode and file selection live on the Collection Source page."))
        grid.addWidget(budget_card, 2, 0)

        summary = TexturedPanel(self.theme, kind="iron_2", glow=True)
        s_layout = QVBoxLayout(summary); s_layout.setContentsMargins(18, 16, 18, 16)
        s_title = QLabel("Run Settings Summary"); s_title.setObjectName("sectionTitle"); s_layout.addWidget(s_title)
        summary_label = self.make_text(self.review_settings_summary_text())
        s_layout.addWidget(summary_label)
        auto_note = self.default_note("Auto-staged: changes update this summary immediately. No Apply button required.")
        s_layout.addWidget(auto_note)
        grid.addWidget(summary, 2, 1)

        def auto_stage_review():
            self.stage_review_settings(output_combo, direction_combo, cut_combo, prompt_combo, budget_input, bracket_check, collection_check, summary_label)

        output_combo.currentTextChanged.connect(lambda _text: auto_stage_review())
        direction_combo.currentTextChanged.connect(lambda _text: auto_stage_review())
        cut_combo.currentTextChanged.connect(lambda _text: auto_stage_review())
        prompt_combo.currentTextChanged.connect(lambda _text: auto_stage_review())
        budget_input.textChanged.connect(lambda _text: auto_stage_review())
        bracket_check.toggled.connect(lambda _checked: auto_stage_review())
        collection_check.toggled.connect(lambda _checked: auto_stage_review())

        note = TexturedPanel(self.theme, kind="iron_2", glow=False)
        n_layout = QVBoxLayout(note); n_layout.setContentsMargins(18, 14, 18, 14)
        n_title = QLabel("v0.6.7.5.2 Boundary"); n_title.setObjectName("sectionTitle"); n_layout.addWidget(n_title)
        n_layout.addWidget(self.make_text("These choices auto-stage inside the UI as soon as you change them. They are not yet handed to the locked backend. Collection mode belongs on the Collection Source page; backend runtime-config mapping comes later."))
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
            subtype = self.default_note(tags)
            card.body.addWidget(subtype)
            portrait = QLabel(icon)
            portrait.setAlignment(Qt.AlignCenter)
            portrait.setStyleSheet("font-size: 48px; color: #3a2818;")
            card.body.addWidget(portrait)
            card.body.addWidget(self.make_text(desc, paper=True))
            btn = QPushButton("Select Profile")
            btn.clicked.connect(lambda checked=False, n=name: self.select_philosophy(n))
            card.body.addWidget(btn)
            cards.addWidget(card)
        body_layout.addLayout(cards)

        prefs = TexturedPanel(self.theme, kind="iron_2", glow=True)
        p_layout = QVBoxLayout(prefs)
        p_layout.setContentsMargins(18, 16, 18, 16)
        title = QLabel("Preference Sliders")
        title.setObjectName("sectionTitle")
        p_layout.addWidget(title)
        for label, value in [("Protect theme / vibe", 75), ("Prioritize consistency", 55), ("Allow strange synergy pieces", 68), ("Push power level", 45)]:
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            slider = QSlider(Qt.Horizontal)
            slider.setValue(value)
            row.addWidget(slider)
            p_layout.addLayout(row)
        note = QLabel("This shapes guidance, explanations, and cut/replacement bias. It does not determine card legality.")
        note.setObjectName("warningText")
        p_layout.addWidget(note)
        body_layout.addWidget(prefs)
        layout.addWidget(body, stretch=1)
        return page

    def select_philosophy(self, name):
        self.state.selected_philosophy = name
        self.state.status = f"{name} profile selected"
        self.refresh_context_panel_values()

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
            f"- Preview count estimate: {self.state.deck_size} main-deck/card lines\n"
            f"- Commander detected separately: {'Yes' if self.state.commander_detected else 'No'}\n\n"
            "Review setup\n"
            f"- Output mode: {self.state.output_mode}\n"
            f"- Review direction: {self.state.review_direction}\n"
            f"- Cut depth: {self.state.cut_depth}\n"
            f"- Prompt mode: {self.state.prompt_mode}\n"
            f"- Budget note: {self.state.budget_note}\n"
            f"- Table boundary: {'Respect stated table bracket' if self.state.respect_table_bracket else 'No table-bracket checkbox selected'}\n"
            f"- Collection handoff: {'Use Collection Source page settings' if self.state.use_collection_settings else 'Collection handoff not selected on Review Setup'}\n\n"
            "Philosophy lens\n"
            f"- Selected lens: {self.state.selected_philosophy}\n\n"
            "Collection source\n"
            f"- Collection mode: {self.state.collection_mode}\n"
            f"- Collection source: {self.state.collection_source_mode}\n"
            f"- Collection folder: {self.state.collection_folder}\n"
            f"- {collection_file_note}\n"
            f"- Collection source note: {self.state.collection_source_note}\n\n"
            "Backend mapping\n"
            "- Backend execution: not connected in UI yet\n"
            "- Locked backend source of truth: v0.6.6.6 CLI workflow\n"
            "- v0.6.7.5.2 purpose: confirm staged information and clean up refresh/popup timing before a future backend bridge"
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
            "⚠ Backend execution: intentionally not connected yet"
        )

    def run_placeholder_message(self):
        QMessageBox.information(
            self,
            "Run Analysis Backend Hook Prepared",
            f"{APP_VERSION} has gathered the staged UI choices into a backend configuration preview. It still does not call the locked {LOCKED_BACKEND_VERSION} analysis engine. Review the Run Configuration Preview before the future backend bridge patch."
        )

    def page_run_review(self):
        page, layout = self.page_container(
            "Run Analysis",
            f"Review the staged run configuration before future backend execution. {APP_VERSION} prepares the hook, but still does not call the analysis engine."
        )
        body = QWidget(); body_layout = QHBoxLayout(body); body_layout.setContentsMargins(0, 0, 0, 0); body_layout.setSpacing(14)

        left = TexturedPanel(self.theme, kind="iron", glow=True); add_shadow(left, blur=28, y=8)
        l_layout = QVBoxLayout(left); l_layout.setContentsMargins(24, 24, 24, 24); l_layout.setSpacing(16)
        run_btn = QPushButton("🔥 Prepare Backend Run Preview")
        run_btn.setObjectName("primaryButton")
        run_btn.setMinimumHeight(64)
        run_btn.clicked.connect(self.run_placeholder_message)
        l_layout.addWidget(run_btn)

        readiness = ReportCard("Backend Readiness Checklist", self.theme, badges=[("No engine call", "manual")])
        readiness.body.addWidget(self.make_text(self.run_readiness_text(), paper=True))
        l_layout.addWidget(readiness)

        orb_panel = TexturedPanel(self.theme, kind="iron_2", glow=True, corners=False)
        orb_layout = QVBoxLayout(orb_panel); orb_layout.setContentsMargins(12, 12, 12, 12)
        orb_layout.addWidget(ForgeOrb(self.theme), stretch=1)
        status = QLabel("The forge is staged, not fired. This page now gathers deck, review, philosophy, and collection choices for inspection before a future backend bridge.")
        status.setObjectName("helperText"); status.setAlignment(Qt.AlignCenter); status.setWordWrap(True)
        orb_layout.addWidget(status)
        l_layout.addWidget(orb_panel, stretch=1)

        right = TexturedPanel(self.theme, kind="iron", glow=False); add_shadow(right, blur=28, y=8)
        r_layout = QVBoxLayout(right); r_layout.setContentsMargins(24, 24, 24, 24); r_layout.setSpacing(14)
        title = QLabel("Run Configuration Preview"); title.setObjectName("sectionTitle"); r_layout.addWidget(title)
        preview = QPlainTextEdit(); preview.setReadOnly(True); preview.setPlainText(self.run_config_preview_text()); preview.setMinimumHeight(330)
        preview.setObjectName("runConfigPreview")
        r_layout.addWidget(preview, stretch=1)

        stages_card = ReportCard("Future Backend Mapping Stages", self.theme, badges=[("v0.6.7.5.2", "manual")])
        stage_text = (
            "1. Deck path and preview state are staged.\n"
            "2. Review Setup choices are staged.\n"
            "3. Philosophy Lens choice is staged.\n"
            "4. Collection Source choices are staged.\n"
            "5. Backend runtime-config mapping is still reserved for a later patch.\n"
            "6. Report generation is still handled only by the locked CLI backend."
        )
        stages_card.body.addWidget(self.make_text(stage_text, paper=True))
        r_layout.addWidget(stages_card)

        boundary = TexturedPanel(self.theme, kind="iron_2", glow=False)
        b_layout = QVBoxLayout(boundary); b_layout.setContentsMargins(18, 14, 18, 14)
        b_title = QLabel("v0.6.7.5.2 Boundary"); b_title.setObjectName("sectionTitle"); b_layout.addWidget(b_title)
        b_layout.addWidget(self.make_text("This patch keeps the backend hook preview in one place while Review Setup and Collection Source choices auto-stage immediately. It does not run analysis, load Scryfall, validate legality, load a collection, or write reports."))
        r_layout.addWidget(boundary)

        body_layout.addWidget(left, stretch=1); body_layout.addWidget(right, stretch=2); layout.addWidget(body, stretch=1); return page

    def update_progress_mock(self):
        if not self.progress_bars or self.stack.currentIndex() != self.RUN_REVIEW: return
        self.progress_tick += 1
        for i, bar in enumerate(self.progress_bars): bar.setValue(min(100, (self.progress_tick * (i + 2) + i * 17) % 120))

    def page_report_viewer(self):
        page, layout = self.page_container("Report Viewer", "The strategy manuscript: parchment report cards inside a dark forge workspace.")
        body = QWidget(); body_layout = QHBoxLayout(body); body_layout.setContentsMargins(0, 0, 0, 0); body_layout.setSpacing(14)
        report_nav = TexturedPanel(self.theme, kind="iron", glow=False); report_nav.setFixedWidth(240); add_shadow(report_nav, blur=22, y=7); rn_layout = QVBoxLayout(report_nav); rn_layout.setContentsMargins(16, 16, 16, 16); rn_layout.setSpacing(8); cap = QLabel("REPORT SECTIONS"); cap.setObjectName("smallCaps"); rn_layout.addWidget(cap)
        for section in ["Deck Report", "Debug Report", "Aggregate Deck Reports", "Strategy Read", "Cut Pressure", "Protected Cards", "Collection Candidates", "Philosophy", "Final Notes"]: rn_layout.addWidget(SidebarButton(section, -1))
        rn_layout.addStretch(1); export = QPushButton("Export"); export.setObjectName("primaryButton"); export.clicked.connect(self.placeholder_message); rn_layout.addWidget(export); rn_layout.addWidget(QPushButton("Save")); rn_layout.addWidget(QPushButton("Copy"))
        scroll = QScrollArea(); scroll.setWidgetResizable(True); manuscript = TexturedPanel(self.theme, parchment=True, glow=True); add_shadow(manuscript, blur=30, y=8); m_layout = QVBoxLayout(manuscript); m_layout.setContentsMargins(26, 24, 26, 24); m_layout.setSpacing(16)
        heading = QLabel("The Dragon’s Touch Strategy Manuscript"); heading.setObjectName("reportTitle"); m_layout.addWidget(heading)
        intro = QLabel(f"Prepared for future Dragon’s Touch reports. {APP_VERSION} demonstrates the intended long-form reading experience. Later patches will load normal reports, debug reports, and aggregate reports from the output folder."); intro.setObjectName("reportBody"); intro.setWordWrap(True); m_layout.addWidget(intro)
        reports = [("Strategy Read", [("Primary Plan", "primary"), ("Medium Confidence", "medium")], "This deck appears to be a commander-centered value deck with a ramp-forward shell. The primary plan is to turn early mana development into overwhelming board presence."), ("Commander Support Level", [("High Synergy", "high")], "The commander is supported by several cards that either accelerate the plan, convert resources into cards, or amplify the deck’s strongest turns."), ("Core Synergy Packages", [("Secondary Package", "normal")], "Ramp, token production, recursion, and payoff creatures appear to form the core package. Future analysis will separate true strategy support from incidental overlap."), ("Possible Cut Review", [("Manual Review", "manual"), ("Medium Confidence", "medium")], "These are not automatic cuts. They are candidates worth reviewing based on curve, redundancy, role pressure, and whether they support the primary plan."), ("Protected From Cut", [("Protected", "protected"), ("High Synergy", "high")], "Cards that look weak in isolation may be protected if they enable the deck’s actual engine, support the commander, or preserve the player’s intended experience."), ("Replacement Categories", [("Primary Plan", "primary")], "Prioritize more commander synergy, stronger draw engines, lower-curve ramp, and replacements that keep the deck’s main identity intact."), ("Philosophy Adjustment", [("Manual Review", "manual")], "The chosen player profile shapes tone and recommendation pressure. It does not override legality, deck identity, or explicit user constraints."), ("Final Notes", [("Protected", "protected")], "A strong Dragon’s Touch report should help the player understand the deck they wanted to build, not simply force the deck toward generic optimization.")]
        for title, badges, text in reports:
            card = ReportCard(title, self.theme, badges=badges); card.body.addWidget(self.make_text(text, paper=True));
            if title == "Possible Cut Review":
                mini = QHBoxLayout()
                for name in ["Card A", "Card B", "Card C", "Card D"]:
                    thumb = QLabel(name); thumb.setAlignment(Qt.AlignCenter); thumb.setFixedSize(86, 112); thumb.setStyleSheet(f"background: {self.theme()['parchment_3']}; border: 1px solid #8d6a32; border-radius: 10px; color: {self.theme()['paper_text']}; font-weight: 800;"); mini.addWidget(thumb)
                mini.addStretch(1); card.body.addLayout(mini)
            m_layout.addWidget(card)
        scroll.setWidget(manuscript); body_layout.addWidget(report_nav); body_layout.addWidget(scroll, stretch=1); layout.addWidget(body, stretch=1); return page

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

    def stage_collection_mode(self, mode):
        self.state.collection_mode = mode
        self.state.use_collection_settings = mode != "No collection"
        if mode == "No collection":
            self.state.collection_source_note = "Collection disabled for this staged run."
            self.state.status = "Collection disabled"
        else:
            self.state.collection_source_note = "Collection mode staged in UI. Choose or confirm a collection source before backend mapping."
            self.state.status = "Collection mode staged"
        self.rebuild_shell(self.COLLECTION)

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
        self.rebuild_shell(self.COLLECTION)

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
        self.rebuild_shell(self.COLLECTION)

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
        self.rebuild_shell(self.COLLECTION)

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
        self.refresh_context_panel_values()

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
        folder_btn.clicked.connect(self.choose_collection_folder)
        files_btn = QPushButton("Select Collection Files")
        files_btn.clicked.connect(self.choose_collection_files)
        folder_btn.setVisible(self.state.collection_source_mode == "Entire collection folder")
        files_btn.setVisible(self.state.collection_source_mode == "Select collection files")
        source_card.body.addWidget(folder_btn)
        source_card.body.addWidget(files_btn)

        current_source = ReportCard("Current Source Preview", self.theme, badges=[("Preview", "manual")])
        current_source.setMinimumHeight(245)
        current_source.body.addWidget(self.readonly_text_box(self.collection_settings_summary_text(), min_height=132, max_height=170))

        summary_card = TexturedPanel(self.theme, kind="iron_2", glow=True)
        summary_card.setMinimumHeight(245)
        s_layout = QVBoxLayout(summary_card)
        s_layout.setContentsMargins(18, 16, 18, 16)
        s_layout.setSpacing(10)
        s_title = QLabel("Collection Settings Summary")
        s_title.setObjectName("sectionTitle")
        s_layout.addWidget(s_title)
        s_layout.addWidget(self.readonly_text_box(self.collection_settings_summary_text(), min_height=120, max_height=155))
        s_layout.addWidget(self.default_note("Auto-staged: collection choices update immediately. No Apply button required."))

        honesty_card = ReportCard("Collection Honesty Boundary", self.theme, badges=[("v0.6.6.6 locked", "protected")])
        honesty_card.body.addWidget(self.make_text(
            "Owned cards remain candidates, not automatic swaps. Future backend integration should preserve the locked behavior: collection-first, collection-only, and shakeup modes cannot override strategy fit, legality, color identity, companion restrictions, or quality gates.",
            paper=True
        ))

        b_layout.addWidget(mode_card, 0, 0)
        b_layout.addWidget(source_card, 0, 1)
        b_layout.addWidget(current_source, 1, 0)
        b_layout.addWidget(summary_card, 1, 1)
        b_layout.addWidget(honesty_card, 2, 0, 1, 2)
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
        theme_card = ReportCard("Theme Options", self.theme, badges=[("Current", "primary")]); row = QHBoxLayout(); dark = QPushButton("Dragon Forge"); dark.setObjectName("primaryButton" if self.theme()["name"] == "Dragon Forge" else "utilityButton"); dark.clicked.connect(lambda: self.set_theme(DRAGON_FORGE)); light = QPushButton("Adventurer's Map"); light.setObjectName("primaryButton" if self.theme()["name"] == "Adventurer's Map" else "utilityButton"); light.clicked.connect(lambda: self.set_theme(ADVENTURERS_MAP)); row.addWidget(dark); row.addWidget(light); row.addStretch(1); theme_card.body.addLayout(row); theme_card.body.addWidget(self.make_text("Dragon Forge remains ember-forge dark. Adventurer’s Map now uses the Cartographer Palette: parchment, dark ink, antique brass, and deep map blue.", paper=True)); b_layout.addWidget(theme_card)
        prefs = ReportCard("UI Preferences", self.theme); pref_grid = QGridLayout(); pref_grid.addWidget(QLabel("Report Detail Level"), 0, 0); detail = QComboBox(); detail.addItems(["Short", "Normal", "Detailed", "Exhaustive"]); detail.setCurrentText("Detailed"); self.configure_combo_popup(detail); pref_grid.addWidget(detail, 0, 1); pref_grid.addWidget(QLabel("Export Format"), 1, 0); export = QComboBox(); export.addItems(["Markdown", "Text", "HTML later", "PDF later"]); self.configure_combo_popup(export); pref_grid.addWidget(export, 1, 1); pref_grid.addWidget(QLabel("Save Folder"), 2, 0); pref_grid.addWidget(QLineEdit("Outputs/"), 2, 1); prefs.body.addLayout(pref_grid); b_layout.addWidget(prefs)
        version = ReportCard("App Version", self.theme); version.body.addWidget(self.make_text(f"The Dragon’s Touch PySide6 Workstation\nVersion: {APP_VERSION}\nPhase: {APP_PHASE}\nLocked backend: {LOCKED_BACKEND_VERSION}\nBackend: Not connected in UI yet\nPurpose: local deck preview, review settings, collection-source staging, and Run Analysis backend-hook preparation while keeping backend execution disconnected", paper=True)); b_layout.addWidget(version); b_layout.addStretch(1); layout.addWidget(body, stretch=1); return page


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("The Dragon's Touch")
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
