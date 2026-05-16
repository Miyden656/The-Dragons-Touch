"""
The Dragon's Touch - PySide6 Textured Desktop UI Prototype

Standalone local desktop UI mockup for a fantasy-themed Commander deck-building
and deck-review app.

This version focuses on:
- dark forge workspace outside
- parchment strategy manuscript inside
- practical deck-analysis workflow structure
- left navigation, main workspace, right context panel
- rich fantasy texture direction without requiring image assets

This is a non-functional UI prototype only:
- No real deck-building logic
- No API calls
- No card database
- No real file import/export
- Placeholder data only

Run:
    pip install PySide6
    python dragons_touch_pyside6_workstation.py
"""

import sys
import math
from dataclasses import dataclass

from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QFont, QLinearGradient, QRadialGradient
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QComboBox, QFrame, QGraphicsDropShadowEffect,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPlainTextEdit, QProgressBar, QPushButton, QScrollArea, QSlider,
    QStackedWidget, QVBoxLayout, QWidget
)


DRAGON_FORGE = {
    "name": "Dragon Forge", "mode": "dark", "bg": "#0b0908", "outer": "#100d0b",
    "sidebar": "#15100d", "sidebar_2": "#201712", "iron": "#1d1814", "iron_2": "#2a211a",
    "stone": "#252321", "leather": "#2b1d14", "bronze": "#6f4425",
    "parchment": "#ead7a9", "parchment_2": "#f4e4bd", "parchment_3": "#d6bd82",
    "paper_text": "#3a2818", "text": "#f4e8d4", "muted": "#bca892", "muted_2": "#8d7b68",
    "accent": "#e86a24", "accent_2": "#d9a441", "accent_3": "#ff9b4a",
    "danger": "#b64031", "success": "#7fc95d", "warning": "#f0c35a",
    "border": "#74401f", "border_soft": "#46301f", "input": "#120f0c", "input_border": "#6a4326",
}

ADVENTURERS_MAP = {
    "name": "Adventurer's Map", "mode": "light", "bg": "#cdb789", "outer": "#dcc79a",
    "sidebar": "#6b4d2c", "sidebar_2": "#7d5c34", "iron": "#ead8ab", "iron_2": "#dcc28e",
    "stone": "#c6aa73", "leather": "#8a6031", "bronze": "#9e702b",
    "parchment": "#f3e4bd", "parchment_2": "#fff2cc", "parchment_3": "#d9bd7e",
    "paper_text": "#3a2818", "text": "#3a2818", "muted": "#6d5a43", "muted_2": "#8b7558",
    "accent": "#3e6b3a", "accent_2": "#b88a2e", "accent_3": "#79551b",
    "danger": "#a54832", "success": "#3e7b3c", "warning": "#98691d",
    "border": "#8a6838", "border_soft": "#b5975f", "input": "#fff8e3", "input_border": "#a98445",
}


@dataclass
class AppState:
    theme: dict
    selected_philosophy: str = "Balanced / Mentor Guided"
    deck_name: str = "Verdant Awakening"
    commander: str = "Liora, Verdant Sage"
    deck_size: int = 100
    bracket: str = "Bracket 3"
    warnings: int = 2
    status: str = "Ready for mock review"


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
        l = QLabel(label)
        l.setObjectName("statLabel")
        v = QLabel(value)
        v.setObjectName("statValue")
        layout.addWidget(l)
        layout.addWidget(v)


class PillButton(QPushButton):
    def __init__(self, text, checked=False, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("pillButton")


class MainWindow(QMainWindow):
    DECK_INPUT, ANALYSIS_SETUP, PHILOSOPHY, RUN_REVIEW, REPORT, COLLECTION, COMBO, SETTINGS = range(8)

    def __init__(self):
        super().__init__()
        self.state = AppState(theme=DRAGON_FORGE)
        self.nav_buttons = []
        self.progress_bars = []
        self.progress_tick = 0
        self.setWindowTitle("The Dragon's Touch")
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
        self.go_to(self.DECK_INPUT)
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
        self.go_to(page_index if page_index is not None else self.DECK_INPUT)

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
        tagline = QLabel("Forge Insight. Refine Power. Play Your Legend.")
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
        left = QLabel("Local Desktop UI Prototype  •  PySide6  •  No backend connected")
        left.setObjectName("footerText")
        right = QLabel("Fantasy frame, practical content.")
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
            ("🃏  Deck Input", self.DECK_INPUT), ("⚙  Analysis Setup", self.ANALYSIS_SETUP),
            ("🧠  Philosophy Profile", self.PHILOSOPHY), ("🔥  Run Review", self.RUN_REVIEW),
            ("📜  Report Viewer", self.REPORT), ("🗃  Collection Tools", self.COLLECTION),
            ("♾  Combo Finder", self.COMBO), ("⚒  Settings", self.SETTINGS),
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
        for label in ["Save Mock Session", "Copy Report", "Export Placeholder"]:
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
        for label, value in [
            ("Deck", self.state.deck_name), ("Commander", self.state.commander), ("Deck Size", f"{self.state.deck_size} cards"),
            ("Bracket Estimate", self.state.bracket), ("Warnings", f"{self.state.warnings} to review"), ("Status", self.state.status),
        ]:
            layout.addWidget(SmallStat(label, value, self.theme))
        line = QFrame(); line.setObjectName("goldDivider"); line.setFixedHeight(1); layout.addWidget(line)
        notes_title = QLabel("QUICK NOTES"); notes_title.setObjectName("smallCaps"); layout.addWidget(notes_title)
        notes = QLabel("• Mock data only\n• Report viewer is the design priority\n• Backend will connect later\n• Responsible API behavior planned")
        notes.setObjectName("mutedText"); notes.setWordWrap(True); layout.addWidget(notes)
        layout.addStretch(1)
        mascot = TexturedPanel(self.theme, kind="iron_2", glow=True, corners=False)
        mascot_layout = QVBoxLayout(mascot); mascot_layout.setContentsMargins(12, 12, 12, 12)
        dragon = QLabel("☕🐲"); dragon.setObjectName("contextMascot"); dragon.setAlignment(Qt.AlignCenter)
        text = QLabel("Ready to examine the deck placed upon the forge-table."); text.setObjectName("mutedText"); text.setWordWrap(True); text.setAlignment(Qt.AlignCenter)
        mascot_layout.addWidget(dragon); mascot_layout.addWidget(text); layout.addWidget(mascot)
        return panel

    def build_pages(self):
        self.stack.addWidget(self.page_deck_input())
        self.stack.addWidget(self.page_analysis_setup())
        self.stack.addWidget(self.page_philosophy())
        self.stack.addWidget(self.page_run_review())
        self.stack.addWidget(self.page_report_viewer())
        self.stack.addWidget(self.page_collection_tools())
        self.stack.addWidget(self.page_combo_finder())
        self.stack.addWidget(self.page_settings())

    def apply_theme(self):
        self.root.setStyleSheet(self.qss(self.theme()))

    def toggle_theme(self):
        self.state.theme = ADVENTURERS_MAP if self.theme()["name"] == "Dragon Forge" else DRAGON_FORGE
        self.rebuild_shell()

    def set_theme(self, theme):
        self.state.theme = theme
        self.rebuild_shell(self.SETTINGS)

    def qss(self, t):
        return f'''
        QWidget {{ color: {t["text"]}; font-family: "Segoe UI", "Arial", sans-serif; font-size: 14px; background: transparent; }}
        QMainWindow {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {t["bg"]}, stop:0.55 {t["outer"]}, stop:1 {t["leather"]}); }}
        QLabel#dragonMark {{ font-size: 42px; }} QLabel#appTitle {{ font-family: Georgia, serif; font-size: 34px; font-weight: 800; letter-spacing: 2px; color: {t["text"]}; }}
        QLabel#tagline {{ font-family: Georgia, serif; font-size: 14px; font-style: italic; color: {t["accent_2"]}; }}
        QLabel#pageTitle {{ font-family: Georgia, serif; font-size: 30px; font-weight: 800; color: {t["accent_2"]}; }}
        QLabel#sectionTitle {{ font-family: Georgia, serif; font-size: 19px; font-weight: 800; color: {t["accent_2"]}; }}
        QLabel#smallCaps {{ font-family: Georgia, serif; color: {t["accent_2"]}; font-size: 12px; font-weight: 800; letter-spacing: 1.2px; }}
        QLabel#mutedText, QLabel#helperText {{ color: {t["muted"]}; line-height: 1.4; }} QLabel#footerText {{ color: {t["muted_2"]}; font-size: 12px; }}
        QLabel#mascotHeader {{ font-size: 32px; }} QLabel#sidebarMascot {{ font-size: 36px; }} QLabel#contextMascot {{ font-size: 42px; }}
        QLabel#statLabel {{ color: {t["muted"]}; font-size: 11px; font-weight: 700; }} QLabel#statValue {{ color: {t["text"]}; font-size: 14px; font-weight: 700; }}
        QLabel#reportTitle {{ color: {t["paper_text"]}; font-family: Georgia, serif; font-size: 22px; font-weight: 900; }} QLabel#reportBody {{ color: {t["paper_text"]}; font-size: 14px; line-height: 1.5; }}
        QLabel#warningText {{ color: {t["warning"]}; font-weight: 700; }}
        QPushButton {{ border-radius: 12px; border: 1px solid {t["border"]}; padding: 10px 14px; color: {t["text"]}; font-weight: 700; background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {t["iron_2"]}, stop:1 {t["leather"]}); }}
        QPushButton:hover {{ border: 1px solid {t["accent_2"]}; background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {t["bronze"]}, stop:1 {t["iron_2"]}); }}
        QPushButton:pressed {{ background: {t["accent"]}; color: {t["bg"]}; }} QPushButton#primaryButton {{ color: {t["bg"]}; border: 1px solid {t["accent_2"]}; background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {t["accent"]}, stop:1 {t["accent_2"]}); font-weight: 900; }}
        QPushButton#utilityButton {{ padding: 8px 12px; font-size: 13px; }} QPushButton#sidebarButton {{ text-align: left; border-radius: 13px; padding: 12px 13px; color: {t["muted"]}; background: transparent; border: 1px solid transparent; }}
        QPushButton#sidebarButton:hover {{ color: {t["text"]}; background: {t["sidebar_2"]}; border: 1px solid {t["border_soft"]}; }} QPushButton#sidebarButton:checked {{ color: {t["bg"]}; background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {t["accent"]}, stop:1 {t["accent_2"]}); border: 1px solid {t["accent_2"]}; font-weight: 900; }}
        QPushButton#pillButton {{ border-radius: 15px; padding: 7px 12px; color: {t["muted"]}; background: {t["iron_2"]}; border: 1px solid {t["border_soft"]}; }} QPushButton#pillButton:checked {{ color: {t["bg"]}; background: {t["accent"]}; border: 1px solid {t["accent_2"]}; }}
        QLineEdit, QPlainTextEdit, QComboBox {{ color: {t["text"]}; background: {t["input"]}; border: 1px solid {t["input_border"]}; border-radius: 12px; padding: 10px; selection-background-color: {t["accent"]}; selection-color: {t["bg"]}; }}
        QComboBox::drop-down {{ border: none; width: 28px; }} QCheckBox {{ spacing: 8px; color: {t["text"]}; }} QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 5px; border: 1px solid {t["border"]}; background: {t["input"]}; }} QCheckBox::indicator:checked {{ background: {t["accent"]}; border: 1px solid {t["accent_2"]}; }}
        QProgressBar {{ border: 1px solid {t["border"]}; border-radius: 8px; background: {t["input"]}; height: 15px; text-align: center; color: {t["text"]}; font-size: 10px; }} QProgressBar::chunk {{ border-radius: 7px; background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {t["accent"]}, stop:1 {t["accent_2"]}); }}
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

    def placeholder_message(self):
        QMessageBox.information(self, "Prototype Placeholder", "This control is part of the UI mockup only. It is not connected yet.")

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

    def page_deck_input(self):
        page, layout = self.page_container("Deck Input", "Place the deck on the forge-table: commander, decklist, import options, and validation status.")
        body = TexturedPanel(self.theme, kind="iron", glow=False); add_shadow(body, blur=26, y=8)
        body_layout = QHBoxLayout(body); body_layout.setContentsMargins(22, 22, 22, 22); body_layout.setSpacing(16)
        left = TexturedPanel(self.theme, parchment=True)
        left_layout = QVBoxLayout(left); left_layout.setContentsMargins(20, 18, 20, 18); left_layout.setSpacing(12)
        title = QLabel("Commander & Decklist"); title.setObjectName("reportTitle"); left_layout.addWidget(title)
        deck_name = QLineEdit(self.state.deck_name); commander = QLineEdit(self.state.commander)
        decklist = QPlainTextEdit(); decklist.setPlainText("1 Sol Ring\n1 Arcane Signet\n1 Cultivate\n1 Kodama's Reach\n1 Beast Within\n1 Eternal Witness\n1 Avenger of Zendikar\n1 Craterhoof Behemoth\n... placeholder decklist ..."); decklist.setMinimumHeight(390)
        for label, widget in [("Deck Name", deck_name), ("Commander Name", commander), ("Decklist", decklist)]:
            left_layout.addWidget(QLabel(label)); left_layout.addWidget(widget, stretch=1 if widget is decklist else 0)
        button_row = QHBoxLayout()
        for label in ["Import Deck", "Load From File", "Paste From Clipboard"]:
            b = QPushButton(label); b.clicked.connect(self.placeholder_message); button_row.addWidget(b)
        left_layout.addLayout(button_row)
        right = QVBoxLayout(); right.setSpacing(14)
        status = TexturedPanel(self.theme, kind="iron_2", glow=True); status_layout = QVBoxLayout(status); status_layout.setContentsMargins(18, 16, 18, 16)
        cap = QLabel("VALIDATION STATUS"); cap.setObjectName("smallCaps"); status_layout.addWidget(cap)
        status_layout.addWidget(self.make_text("Deck size: 100 cards\nCommander detected: Yes\nColor identity: Placeholder\nLegality: Not checked"))
        p = QProgressBar(); p.setValue(74); status_layout.addWidget(p)
        quick = ReportCard("Forge Note", self.theme); quick.body.addWidget(self.make_text("The final version will parse this list, validate card names, check commander legality, and prepare the analysis request. For now, this is a visual shell.", paper=True))
        right.addWidget(status); right.addWidget(quick); right.addStretch(1)
        body_layout.addWidget(left, stretch=2); body_layout.addLayout(right, stretch=1)
        layout.addWidget(body, stretch=1); return page

    def page_analysis_setup(self):
        page, layout = self.page_container("Analysis Setup", "Set the boundaries: bracket, budget, collection preference, combo tolerance, and cut strictness.")
        scroll, content = self.scroll_content()
        grid_panel = TexturedPanel(self.theme, kind="iron", glow=False); add_shadow(grid_panel, blur=24, y=8)
        grid = QGridLayout(grid_panel); grid.setContentsMargins(22, 22, 22, 22); grid.setSpacing(16)
        settings = [("Bracket Target", ["Bracket 1", "Bracket 2", "Bracket 3", "Bracket 4", "High Power"], "Bracket 3"), ("Combo Tolerance", ["None", "Low", "Medium", "High", "Infinite Welcome"], "Medium"), ("Cut Strictness", ["Gentle", "Normal", "Strict", "Very Strict"], "Normal"), ("Report Detail Level", ["Short", "Normal", "Detailed", "Exhaustive"], "Detailed")]
        for i, (label, opts, selected) in enumerate(settings):
            card = ReportCard(label, self.theme); combo = QComboBox(); combo.addItems(opts); combo.setCurrentText(selected); card.body.addWidget(combo); grid.addWidget(card, i // 2, i % 2)
        budget_card = ReportCard("Budget Setting", self.theme); budget_card.body.addWidget(QLineEdit("$200 total / $25 per card")); budget_card.body.addWidget(QCheckBox("Collection-only recommendations")); budget_card.body.addWidget(QCheckBox("Allow owned cards even if over budget")); grid.addWidget(budget_card, 2, 0)
        summary = TexturedPanel(self.theme, kind="iron_2", glow=True); s_layout = QVBoxLayout(summary); s_layout.setContentsMargins(18, 16, 18, 16); s_title = QLabel("Run Settings Summary"); s_title.setObjectName("sectionTitle"); s_layout.addWidget(s_title); s_layout.addWidget(self.make_text("Target: Bracket 3\nBudget: $200 total\nCombo tolerance: Medium\nCut strictness: Normal\nCollection mode: Optional")); grid.addWidget(summary, 2, 1)
        content.addWidget(grid_panel); content.addStretch(1); layout.addWidget(scroll, stretch=1); return page

    def page_philosophy(self):
        page, layout = self.page_container("Philosophy Profile", "Shape guidance and tone without changing card legality. This affects how the tool explains tradeoffs.")
        body = TexturedPanel(self.theme, kind="iron", glow=False); add_shadow(body, blur=24, y=8); body_layout = QVBoxLayout(body); body_layout.setContentsMargins(22, 22, 22, 22); body_layout.setSpacing(16)
        cards = QHBoxLayout(); cards.setSpacing(16)
        philosophies = [("Timmy / Tammy", "Big moments, splashy plays, memorable stories.", "🐲", "Big Creature • Theme • Battlecruiser"), ("Johnny / Jenny", "Engines, clever interactions, weird card rescues.", "🛠", "Engine Builder • Combo • Constraint"), ("Spike", "Consistency, efficiency, discipline, clean closing power.", "⚔", "Optimizer • Calibrator • Controller")]
        for name, desc, icon, tags in philosophies:
            card = ReportCard(name, self.theme, badges=[(tags, "normal")]); portrait = QLabel(icon); portrait.setAlignment(Qt.AlignCenter); portrait.setStyleSheet("font-size: 48px; color: #3a2818;"); card.body.addWidget(portrait); card.body.addWidget(self.make_text(desc, paper=True)); btn = QPushButton("Select Profile"); btn.clicked.connect(lambda checked=False, n=name: self.select_philosophy(n)); card.body.addWidget(btn); cards.addWidget(card)
        body_layout.addLayout(cards)
        prefs = TexturedPanel(self.theme, kind="iron_2", glow=True); p_layout = QVBoxLayout(prefs); p_layout.setContentsMargins(18, 16, 18, 16); title = QLabel("Preference Sliders"); title.setObjectName("sectionTitle"); p_layout.addWidget(title)
        for label, value in [("Protect theme / vibe", 75), ("Prioritize consistency", 55), ("Allow strange synergy pieces", 68), ("Push power level", 45)]:
            row = QHBoxLayout(); row.addWidget(QLabel(label)); slider = QSlider(Qt.Horizontal); slider.setValue(value); row.addWidget(slider); p_layout.addLayout(row)
        note = QLabel("This shapes guidance, explanations, and cut/replacement bias. It does not determine card legality."); note.setObjectName("warningText"); p_layout.addWidget(note); body_layout.addWidget(prefs)
        layout.addWidget(body, stretch=1); return page

    def select_philosophy(self, name):
        self.state.selected_philosophy = name; self.state.status = f"{name} profile selected"; self.rebuild_shell(self.PHILOSOPHY)

    def page_run_review(self):
        page, layout = self.page_container("Run Review", "Start the mock Dragon’s Touch review and watch the analysis stages light up across the forge.")
        body = QWidget(); body_layout = QHBoxLayout(body); body_layout.setContentsMargins(0, 0, 0, 0); body_layout.setSpacing(14)
        left = TexturedPanel(self.theme, kind="iron", glow=True); add_shadow(left, blur=28, y=8); l_layout = QVBoxLayout(left); l_layout.setContentsMargins(24, 24, 24, 24); l_layout.setSpacing(16)
        run_btn = QPushButton("🔥 Run Dragon’s Touch Review"); run_btn.setObjectName("primaryButton"); run_btn.setMinimumHeight(64); run_btn.clicked.connect(self.placeholder_message); l_layout.addWidget(run_btn); l_layout.addWidget(ForgeOrb(self.theme), stretch=1)
        status = QLabel("Mock review status: ready to forge. No backend connected yet."); status.setObjectName("helperText"); status.setAlignment(Qt.AlignCenter); status.setWordWrap(True); l_layout.addWidget(status)
        right = TexturedPanel(self.theme, kind="iron", glow=False); add_shadow(right, blur=28, y=8); r_layout = QVBoxLayout(right); r_layout.setContentsMargins(24, 24, 24, 24); r_layout.setSpacing(14)
        title = QLabel("Analysis Stages"); title.setObjectName("sectionTitle"); r_layout.addWidget(title); self.progress_bars = []
        stages = ["Deck validation", "Commander strategy read", "Archetype detection", "Synergy review", "Cut pressure review", "Replacement category review", "Philosophy adjustment", "Final report generation"]
        for i, stage in enumerate(stages):
            row = QHBoxLayout(); label = QLabel(stage); label.setMinimumWidth(230); bar = QProgressBar(); bar.setRange(0, 100); bar.setValue(max(0, 100 - i * 13)); self.progress_bars.append(bar); row.addWidget(label); row.addWidget(bar, stretch=1); r_layout.addLayout(row)
        narration = ReportCard("Guide Commentary", self.theme); narration.body.addWidget(self.make_text("“I am checking what your deck is trying to become, then sorting cards by role, synergy, pressure, and purpose.”", paper=True)); r_layout.addWidget(narration)
        body_layout.addWidget(left, stretch=1); body_layout.addWidget(right, stretch=2); layout.addWidget(body, stretch=1); return page

    def update_progress_mock(self):
        if not self.progress_bars or self.stack.currentIndex() != self.RUN_REVIEW: return
        self.progress_tick += 1
        for i, bar in enumerate(self.progress_bars): bar.setValue(min(100, (self.progress_tick * (i + 2) + i * 17) % 120))

    def page_report_viewer(self):
        page, layout = self.page_container("Report Viewer", "The strategy manuscript: parchment report cards inside a dark forge workspace.")
        body = QWidget(); body_layout = QHBoxLayout(body); body_layout.setContentsMargins(0, 0, 0, 0); body_layout.setSpacing(14)
        report_nav = TexturedPanel(self.theme, kind="iron", glow=False); report_nav.setFixedWidth(240); add_shadow(report_nav, blur=22, y=7); rn_layout = QVBoxLayout(report_nav); rn_layout.setContentsMargins(16, 16, 16, 16); rn_layout.setSpacing(8); cap = QLabel("REPORT SECTIONS"); cap.setObjectName("smallCaps"); rn_layout.addWidget(cap)
        for section in ["Strategy Read", "Commander Support", "Core Synergy", "Possible Cuts", "Protected Cards", "Replacements", "Philosophy", "Final Notes"]: rn_layout.addWidget(SidebarButton(section, -1))
        rn_layout.addStretch(1); export = QPushButton("Export"); export.setObjectName("primaryButton"); export.clicked.connect(self.placeholder_message); rn_layout.addWidget(export); rn_layout.addWidget(QPushButton("Save")); rn_layout.addWidget(QPushButton("Copy"))
        scroll = QScrollArea(); scroll.setWidgetResizable(True); manuscript = TexturedPanel(self.theme, parchment=True, glow=True); add_shadow(manuscript, blur=30, y=8); m_layout = QVBoxLayout(manuscript); m_layout.setContentsMargins(26, 24, 26, 24); m_layout.setSpacing(16)
        heading = QLabel("The Dragon’s Touch Strategy Manuscript"); heading.setObjectName("reportTitle"); m_layout.addWidget(heading)
        intro = QLabel("Prepared for Verdant Awakening. This placeholder report demonstrates the intended long-form reading experience. Each section is presented as a readable parchment card, not text over a busy background."); intro.setObjectName("reportBody"); intro.setWordWrap(True); m_layout.addWidget(intro)
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

    def page_collection_tools(self):
        page, layout = self.page_container("Collection Tools", "Mock collection workspace for owned cards, missing cards, and replacement suggestions.")
        body = TexturedPanel(self.theme, kind="iron", glow=False); add_shadow(body, blur=24, y=8); b_layout = QGridLayout(body); b_layout.setContentsMargins(22, 22, 22, 22); b_layout.setSpacing(16)
        import_card = ReportCard("Collection Import", self.theme, badges=[("Placeholder", "manual")]); import_card.body.addWidget(self.make_text("Import collection files, select source, and summarize owned inventory.", paper=True)); import_card.body.addWidget(QPushButton("Import Collection")); source = QComboBox(); source.addItems(["Manual CSV", "Local export file", "Card scanner export placeholder", "Future integration"]); import_card.body.addWidget(source)
        summary = ReportCard("Card Count Summary", self.theme, badges=[("Mock Data", "normal")]); summary.body.addWidget(self.make_text("Owned cards: 8,462\nUnique cards: 3,118\nCommander staples: 341\nPotential upgrades: 22", paper=True))
        missing = ReportCard("Missing Cards", self.theme, badges=[("Manual Review", "manual")]); missing.body.addWidget(self.make_text("• Heroic Intervention\n• Finale of Devastation\n• Tireless Provisioner\n• Beast Whisperer", paper=True))
        owned = ReportCard("Owned Replacement Suggestions", self.theme, badges=[("Collection", "primary")]); owned.body.addWidget(self.make_text("Suggest replacements from owned inventory before recommending purchases.", paper=True))
        b_layout.addWidget(import_card, 0, 0); b_layout.addWidget(summary, 0, 1); b_layout.addWidget(missing, 1, 0); b_layout.addWidget(owned, 1, 1); layout.addWidget(body, stretch=1); return page

    def page_combo_finder(self):
        page, layout = self.page_container("Combo Finder", "Commander Spellbook integration placeholder with responsible lookup behavior.")
        body = TexturedPanel(self.theme, kind="iron", glow=False); add_shadow(body, blur=24, y=8); b_layout = QVBoxLayout(body); b_layout.setContentsMargins(22, 22, 22, 22); b_layout.setSpacing(16)
        top = QHBoxLayout()
        for label, value in [("Total Combos Found", "12"), ("Fully In Deck", "3"), ("Missing One Card", "5"), ("Manual Review", "4")]: top.addWidget(SmallStat(label, value, self.theme))
        b_layout.addLayout(top); combo_panel = ReportCard("Combo Steps Preview", self.theme, badges=[("Placeholder", "manual")]); combo_panel.body.addWidget(self.make_text("Combo: Example Engine Loop\n1. Resolve engine card.\n2. Create recurring resource.\n3. Convert resource into cards or mana.\n4. Repeat until win condition is available.", paper=True)); b_layout.addWidget(combo_panel)
        warning = TexturedPanel(self.theme, kind="iron_2", glow=True); w_layout = QVBoxLayout(warning); w_layout.setContentsMargins(18, 16, 18, 16); w_title = QLabel("Responsible Lookup Behavior"); w_title.setObjectName("sectionTitle"); w_layout.addWidget(w_title); w_layout.addWidget(self.make_text("Future Commander Spellbook access should use documented endpoints, caching, delays, and respectful request behavior. The desktop app should avoid spamming APIs or scraping pages.")); b_layout.addWidget(warning); b_layout.addStretch(1); layout.addWidget(body, stretch=1); return page

    def page_settings(self):
        page, layout = self.page_container("Settings", "Theme options, report detail, save location, export format, and app version placeholders.")
        body = TexturedPanel(self.theme, kind="iron", glow=False); add_shadow(body, blur=24, y=8); b_layout = QVBoxLayout(body); b_layout.setContentsMargins(22, 22, 22, 22); b_layout.setSpacing(16)
        theme_card = ReportCard("Theme Options", self.theme, badges=[("Current", "primary")]); row = QHBoxLayout(); dark = QPushButton("Dragon Forge"); dark.setObjectName("primaryButton" if self.theme()["name"] == "Dragon Forge" else "utilityButton"); dark.clicked.connect(lambda: self.set_theme(DRAGON_FORGE)); light = QPushButton("Adventurer's Map"); light.setObjectName("primaryButton" if self.theme()["name"] == "Adventurer's Map" else "utilityButton"); light.clicked.connect(lambda: self.set_theme(ADVENTURERS_MAP)); row.addWidget(dark); row.addWidget(light); row.addStretch(1); theme_card.body.addLayout(row); theme_card.body.addWidget(self.make_text("Color scheme remains close to the original Dragon Forge and Adventurer’s Map direction.", paper=True)); b_layout.addWidget(theme_card)
        prefs = ReportCard("Prototype Preferences", self.theme); pref_grid = QGridLayout(); pref_grid.addWidget(QLabel("Report Detail Level"), 0, 0); detail = QComboBox(); detail.addItems(["Short", "Normal", "Detailed", "Exhaustive"]); detail.setCurrentText("Detailed"); pref_grid.addWidget(detail, 0, 1); pref_grid.addWidget(QLabel("Export Format"), 1, 0); export = QComboBox(); export.addItems(["Markdown", "Text", "HTML later", "PDF later"]); pref_grid.addWidget(export, 1, 1); pref_grid.addWidget(QLabel("Save Folder"), 2, 0); pref_grid.addWidget(QLineEdit("C:/Users/Bruce/Documents/DragonsTouchReports"), 2, 1); prefs.body.addLayout(pref_grid); b_layout.addWidget(prefs)
        version = ReportCard("App Version", self.theme); version.body.addWidget(self.make_text("The Dragon’s Touch PySide6 Workstation Mockup\nVersion: UI Prototype v0.2\nBackend: Not connected\nPurpose: Visual structure and usability testing", paper=True)); b_layout.addWidget(version); b_layout.addStretch(1); layout.addWidget(body, stretch=1); return page


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("The Dragon's Touch")
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
