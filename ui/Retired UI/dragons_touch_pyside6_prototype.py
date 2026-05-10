"""
Dragon's Touch - PySide6 UI Prototype
Standalone desktop UI mockup for a fantasy-themed Commander deck-building and deck-review app.

This is a non-functional UI prototype only:
- No real deck-building logic
- No API calls
- No database
- No card search
- No file import/export implementation
- Placeholder data only

Run:
    pip install PySide6
    python dragons_touch_pyside6_prototype.py
"""

import sys
import math
from dataclasses import dataclass

from PySide6.QtCore import Qt, QTimer, QSize, QRectF, QPointF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QLinearGradient, QRadialGradient, QFont
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QComboBox, QFrame, QGraphicsDropShadowEffect,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPlainTextEdit, QProgressBar, QPushButton, QScrollArea, QSizePolicy,
    QStackedWidget, QVBoxLayout, QWidget
)

DRAGON_FORGE = {
    "name": "Dragon Forge", "mode": "dark", "bg": "#0c0b0a", "bg_2": "#15120f",
    "surface": "#1d1713", "surface_2": "#2a211a", "surface_3": "#35271d",
    "card": "#211812", "card_hover": "#352319", "inset": "#100d0b",
    "text": "#f4e8d4", "muted": "#bda995", "muted_2": "#8f7b6a",
    "accent": "#e86a24", "accent_2": "#d9a441", "accent_3": "#ff9b4a",
    "danger": "#b64031", "success": "#7fc95d", "warning": "#f0c35a",
    "border": "#74401f", "border_soft": "#47301f", "input": "#120f0c", "input_border": "#6a4326",
    "persona_sage": "#66b86d", "persona_warlord": "#e1563f", "persona_artisan": "#3d83d6",
}

ADVENTURERS_MAP = {
    "name": "Adventurer's Map", "mode": "light", "bg": "#d3bd8e", "bg_2": "#e4d2a9",
    "surface": "#f2e3bd", "surface_2": "#e6cf9b", "surface_3": "#d3b67b",
    "card": "#f7ebca", "card_hover": "#efe0b6", "inset": "#fff7df",
    "text": "#3a2818", "muted": "#6d5a43", "muted_2": "#8b7558",
    "accent": "#3e6b3a", "accent_2": "#b88a2e", "accent_3": "#7f5b1e",
    "danger": "#a54832", "success": "#3e7b3c", "warning": "#98691d",
    "border": "#8a6838", "border_soft": "#ba9b63", "input": "#fff8e3", "input_border": "#a98445",
    "persona_sage": "#477a42", "persona_warlord": "#b94b35", "persona_artisan": "#3c678f",
}

@dataclass
class AppState:
    theme: dict
    selected_persona: str = "The Sage"
    current_mode: str = "Home"
    deck_name: str = "Verdant Awakening"
    commanders: str = "Liora, Verdant Sage"
    progress_step: int = 1


def add_shadow(widget, blur=28, x=0, y=8, color=QColor(0, 0, 0, 120)):
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(x, y)
    effect.setColor(color)
    widget.setGraphicsEffect(effect)


class TexturedFrame(QFrame):
    """Rounded fantasy panel with gradients, mottled texture, corner accents, and optional glow."""
    def __init__(self, theme_getter, variant="surface", glow=False, parchment=False, parent=None):
        super().__init__(parent)
        self.theme_getter = theme_getter
        self.variant = variant
        self.glow = glow
        self.parchment = parchment
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumHeight(36)

    def paintEvent(self, event):
        theme = self.theme_getter()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = 18
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        base = QColor(theme.get(self.variant, theme["surface"]))
        alt = QColor(theme["surface_2"])
        if self.parchment:
            base = QColor(theme["card"])
            alt = QColor(theme["surface"])
        grad.setColorAt(0.0, base.lighter(114 if theme["mode"] == "light" else 120))
        grad.setColorAt(0.48, base)
        grad.setColorAt(1.0, alt.darker(104 if theme["mode"] == "light" else 135))
        painter.fillPath(path, grad)

        radial = QRadialGradient(rect.center(), max(rect.width(), rect.height()) * 0.72)
        accent = QColor(theme["accent"])
        accent.setAlpha(42 if self.glow else 13)
        radial.setColorAt(0.0, accent)
        radial.setColorAt(0.82, QColor(0, 0, 0, 0))
        painter.fillPath(path, radial)

        painter.setClipPath(path)
        dot_color = QColor(96, 63, 25, 24) if (self.parchment or theme["mode"] == "light") else QColor(255, 188, 101, 14)
        painter.setPen(Qt.NoPen)
        painter.setBrush(dot_color)
        w, h = max(1, self.width()), max(1, self.height())
        for i in range(110):
            x = (i * 47 + 19) % w
            y = (i * 83 + 31) % h
            r = 1.25 if (x + y + i) % 5 == 0 else 0.75
            painter.drawEllipse(QPointF(x, y), r, r)
        painter.setClipping(False)

        if self.glow:
            painter.setPen(QPen(QColor(theme["accent"]), 3))
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), radius, radius)
        painter.setPen(QPen(QColor(theme["border"]), 1))
        painter.drawRoundedRect(rect, radius, radius)

        corner = QColor(theme["accent_2"])
        corner.setAlpha(175)
        painter.setPen(QPen(corner, 1.4))
        s, inset = 18, 9
        painter.drawLine(QPointF(inset, inset+s), QPointF(inset, inset)); painter.drawLine(QPointF(inset, inset), QPointF(inset+s, inset))
        painter.drawLine(QPointF(rect.width()-inset-s, inset), QPointF(rect.width()-inset, inset)); painter.drawLine(QPointF(rect.width()-inset, inset), QPointF(rect.width()-inset, inset+s))
        painter.drawLine(QPointF(inset, rect.height()-inset-s), QPointF(inset, rect.height()-inset)); painter.drawLine(QPointF(inset, rect.height()-inset), QPointF(inset+s, rect.height()-inset))
        painter.drawLine(QPointF(rect.width()-inset-s, rect.height()-inset), QPointF(rect.width()-inset, rect.height()-inset)); painter.drawLine(QPointF(rect.width()-inset, rect.height()-inset-s), QPointF(rect.width()-inset, rect.height()-inset))
        super().paintEvent(event)


class MascotWidget(TexturedFrame):
    def __init__(self, theme_getter, compact=False, parent=None):
        super().__init__(theme_getter, variant="surface_2", glow=True, parent=parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)
        icon = QLabel("☕🐲")
        icon.setObjectName("mascotIcon")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedWidth(56 if compact else 76)
        layout.addWidget(icon)
        if not compact:
            text = QLabel("Your deck.\nYour legend.\nGuided by dragons.")
            text.setObjectName("mascotText")
            text.setWordWrap(True)
            layout.addWidget(text)


class ForgeVisual(QWidget):
    def __init__(self, theme_getter, parent=None):
        super().__init__(parent)
        self.theme_getter = theme_getter
        self.angle = 0
        self.pulse = 0
        self.setMinimumSize(340, 340)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(45)

    def tick(self):
        self.angle = (self.angle + 3) % 360
        self.pulse = (self.pulse + 1) % 120
        self.update()

    def paintEvent(self, event):
        theme = self.theme_getter()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(14, 14, -14, -14)
        center = rect.center()
        radius = min(rect.width(), rect.height()) / 2
        radial = QRadialGradient(center, radius)
        glow = QColor(theme["accent"]); glow.setAlpha(105)
        radial.setColorAt(0.0, glow); radial.setColorAt(0.45, QColor(theme["surface_2"])); radial.setColorAt(1.0, QColor(theme["bg"]))
        painter.fillRect(self.rect(), radial)
        pulse_scale = 1 + 0.06 * math.sin(self.pulse / 120 * math.tau)
        for i, alpha in enumerate([180, 95, 55]):
            c = QColor(theme["accent_2"]); c.setAlpha(alpha)
            painter.setPen(QPen(c, 2 if i == 0 else 1))
            r = radius * (0.43 + i * 0.16) * pulse_scale
            painter.drawEllipse(center, r, r)
        painter.save(); painter.translate(center); painter.rotate(self.angle)
        for i in range(10):
            painter.save(); painter.rotate(i * 36); painter.translate(0, -radius * 0.68); painter.rotate(-self.angle - i * 36)
            card_rect = QRectF(-18, -25, 36, 50); path = QPainterPath(); path.addRoundedRect(card_rect, 5, 5)
            painter.fillPath(path, QColor(theme["card"])); painter.setPen(QPen(QColor(theme["accent"]), 1.2)); painter.drawPath(path)
            painter.setPen(QPen(QColor(theme["accent_2"]), 1)); painter.drawLine(QPointF(-10, -10), QPointF(10, -10)); painter.drawLine(QPointF(-10, 2), QPointF(10, 2))
            painter.restore()
        painter.restore()
        central = QRectF(center.x()-55, center.y()-76, 110, 152); path = QPainterPath(); path.addRoundedRect(central, 12, 12)
        painter.fillPath(path, QColor(theme["card"])); painter.setPen(QPen(QColor(theme["accent_2"]), 2)); painter.drawPath(path)
        painter.setPen(QColor(theme["accent_2"])); painter.setFont(QFont("Georgia", 34)); painter.drawText(central, Qt.AlignCenter, "🐉")
        painter.setPen(QColor(theme["text"])); painter.setFont(QFont("Georgia", 11, QFont.Bold)); painter.drawText(QRectF(0, rect.bottom()-42, self.width(), 28), Qt.AlignCenter, "Forging insight into legend...")


class DashboardTile(QPushButton):
    def __init__(self, icon, title, subtitle, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(184)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setObjectName("dashboardTile")
        self.setText(f"{icon}\n\n{title}\n{subtitle}")

class PillButton(QPushButton):
    def __init__(self, text, checked=False, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True); self.setChecked(checked); self.setCursor(Qt.PointingHandCursor); self.setObjectName("pillButton")

class NavButton(QPushButton):
    def __init__(self, text, page_index=None, parent=None):
        super().__init__(text, parent)
        self.page_index = page_index
        self.setCursor(Qt.PointingHandCursor); self.setObjectName("navButton"); self.setCheckable(True)

class SectionPanel(TexturedFrame):
    def __init__(self, title, theme_getter, parchment=False, parent=None):
        super().__init__(theme_getter, variant="card", glow=False, parchment=parchment, parent=parent)
        layout = QVBoxLayout(self); layout.setContentsMargins(18, 18, 18, 18); layout.setSpacing(12)
        title_label = QLabel(title); title_label.setObjectName("sectionTitle"); layout.addWidget(title_label)
        self.body = QVBoxLayout(); self.body.setSpacing(10); layout.addLayout(self.body)

class PersonaCard(TexturedFrame):
    def __init__(self, persona, theme_getter, select_callback, selected=False, parent=None):
        super().__init__(theme_getter, variant="card", glow=selected, parent=parent)
        self.persona = persona; self.select_callback = select_callback
        self.setCursor(Qt.PointingHandCursor); self.setMinimumHeight(350)
        layout = QVBoxLayout(self); layout.setContentsMargins(20, 20, 20, 20); layout.setSpacing(10)
        portrait = QLabel(persona["icon"]); portrait.setAlignment(Qt.AlignCenter); portrait.setObjectName("personaPortrait"); portrait.setStyleSheet(f"color: {persona['accent']};"); layout.addWidget(portrait)
        name = QLabel(persona["name"]); name.setAlignment(Qt.AlignCenter); name.setObjectName("personaName"); layout.addWidget(name)
        tags = QLabel(persona["tags"]); tags.setAlignment(Qt.AlignCenter); tags.setWordWrap(True); tags.setObjectName("personaTags"); tags.setStyleSheet(f"color: {persona['accent']};"); layout.addWidget(tags)
        desc = QLabel(persona["desc"]); desc.setAlignment(Qt.AlignCenter); desc.setWordWrap(True); desc.setObjectName("personaDesc"); layout.addWidget(desc, stretch=1)
        chip_row = QHBoxLayout(); chip_row.setSpacing(6)
        for chip in persona["chips"]:
            lbl = QLabel(chip); lbl.setAlignment(Qt.AlignCenter); lbl.setObjectName("traitChip"); chip_row.addWidget(lbl)
        layout.addLayout(chip_row)
        btn = QPushButton("Selected" if selected else "Select Guide"); btn.setObjectName("primaryButton" if selected else "secondaryButton"); btn.clicked.connect(lambda: self.select_callback(persona["name"])); layout.addWidget(btn)
    def mousePressEvent(self, event):
        self.select_callback(self.persona["name"])
        super().mousePressEvent(event)


class MainWindow(QMainWindow):
    HOME, WORKFLOW, PERSONA, PROCESSING, REPORT, SETTINGS = range(6)

    def __init__(self):
        super().__init__()
        self.state = AppState(theme=DRAGON_FORGE)
        self.nav_buttons = []
        self.processing_bars = []
        self.setWindowTitle("Dragon's Touch")
        self.resize(1440, 920); self.setMinimumSize(1120, 760)
        self.root = QWidget(); self.setCentralWidget(self.root)
        self.main_layout = QVBoxLayout(self.root); self.main_layout.setContentsMargins(18, 16, 18, 14); self.main_layout.setSpacing(12)
        self.header = None; self.stack = QStackedWidget(); self.footer = None
        self.build_header(); self.main_layout.addWidget(self.stack, stretch=1); self.build_footer(); self.build_pages(); self.apply_theme(); self.go_to(self.HOME)
        self.processing_timer = QTimer(self); self.processing_timer.timeout.connect(self.update_processing_animation); self.processing_timer.start(500)

    def theme(self): return self.state.theme

    def apply_theme(self): self.root.setStyleSheet(self.generate_qss(self.theme()))

    def generate_qss(self, t):
        return f"""
        QWidget {{ background: transparent; color: {t['text']}; font-family: 'Segoe UI', Arial, sans-serif; font-size: 14px; }}
        QMainWindow {{ background: {t['bg']}; }}
        QLabel#appTitle {{ font-family: Georgia, 'Times New Roman', serif; font-size: 42px; font-weight: 700; letter-spacing: 2px; color: {t['text']}; }}
        QLabel#tagline {{ font-family: Georgia, 'Times New Roman', serif; font-style: italic; font-size: 15px; color: {t['accent_2']}; }}
        QLabel#pageTitle {{ font-family: Georgia, 'Times New Roman', serif; font-size: 28px; font-weight: 700; color: {t['accent_2']}; }}
        QLabel#pageSubtitle, QLabel#helperText {{ color: {t['muted']}; font-size: 14px; }}
        QLabel#sectionTitle {{ font-family: Georgia, 'Times New Roman', serif; font-size: 18px; font-weight: 700; color: {t['accent_2']}; }}
        QLabel#smallCaps {{ font-family: Georgia, 'Times New Roman', serif; color: {t['accent_2']}; font-size: 12px; font-weight: 700; letter-spacing: 1px; }}
        QLabel#mascotIcon {{ font-size: 34px; }} QLabel#mascotText {{ font-family: Georgia, 'Times New Roman', serif; color: {t['text']}; font-size: 13px; font-style: italic; }}
        QPushButton {{ border: 1px solid {t['border']}; border-radius: 12px; padding: 10px 15px; background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 {t['surface_3']}, stop:1 {t['surface_2']}); color: {t['text']}; font-weight: 600; }}
        QPushButton:hover {{ border: 1px solid {t['accent_2']}; background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 {t['card_hover']}, stop:1 {t['surface_3']}); }}
        QPushButton:pressed {{ background: {t['accent']}; color: {t['bg']}; }}
        QPushButton#primaryButton {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {t['accent']}, stop:1 {t['accent_2']}); color: {t['bg']}; border: 1px solid {t['accent_2']}; font-weight: 800; }}
        QPushButton#secondaryButton {{ background: {t['surface_2']}; color: {t['text']}; }}
        QPushButton#navButton {{ text-align: left; padding: 11px 13px; border-radius: 10px; background: transparent; border: 1px solid transparent; color: {t['muted']}; }}
        QPushButton#navButton:hover {{ color: {t['text']}; background: {t['surface_2']}; border: 1px solid {t['border_soft']}; }}
        QPushButton#navButton:checked {{ color: {t['bg']}; background: {t['accent_2']}; border: 1px solid {t['accent_2']}; font-weight: 800; }}
        QPushButton#dashboardTile {{ text-align: center; font-family: Georgia, 'Times New Roman', serif; font-size: 15px; font-weight: 700; border-radius: 18px; border: 1px solid {t['border']}; padding: 18px; color: {t['text']}; background: qradialgradient(cx:0.5,cy:0.2,radius:0.95, stop:0 {t['card_hover']}, stop:0.45 {t['card']}, stop:1 {t['inset']}); }}
        QPushButton#dashboardTile:hover {{ border: 2px solid {t['accent']}; background: qradialgradient(cx:0.5,cy:0.2,radius:0.95, stop:0 {t['surface_3']}, stop:0.45 {t['card_hover']}, stop:1 {t['card']}); }}
        QPushButton#pillButton {{ border-radius: 14px; padding: 7px 12px; background: {t['surface_2']}; color: {t['muted']}; border: 1px solid {t['border_soft']}; font-weight: 600; }}
        QPushButton#pillButton:checked {{ background: {t['accent']}; color: {t['bg']}; border: 1px solid {t['accent_2']}; }}
        QLineEdit, QPlainTextEdit, QComboBox {{ background: {t['input']}; color: {t['text']}; border: 1px solid {t['input_border']}; border-radius: 10px; padding: 10px; selection-background-color: {t['accent']}; selection-color: {t['bg']}; }}
        QComboBox::drop-down {{ border: none; width: 30px; }}
        QCheckBox {{ color: {t['text']}; spacing: 9px; }}
        QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 5px; border: 1px solid {t['border']}; background: {t['input']}; }}
        QCheckBox::indicator:checked {{ background: {t['accent']}; border: 1px solid {t['accent_2']}; }}
        QProgressBar {{ border: 1px solid {t['border']}; border-radius: 8px; background: {t['inset']}; height: 14px; text-align: center; color: {t['text']}; font-size: 10px; }}
        QProgressBar::chunk {{ border-radius: 7px; background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {t['accent']}, stop:1 {t['accent_2']}); }}
        QScrollArea {{ border: none; background: transparent; }}
        QScrollBar:vertical {{ background: {t['surface']}; width: 12px; margin: 0; border-radius: 6px; }}
        QScrollBar::handle:vertical {{ background: {t['border']}; border-radius: 6px; min-height: 28px; }} QScrollBar::handle:vertical:hover {{ background: {t['accent']}; }}
        QLabel#personaPortrait {{ font-size: 56px; }} QLabel#personaName {{ font-family: Georgia, 'Times New Roman', serif; font-size: 23px; font-weight: 700; color: {t['text']}; }}
        QLabel#personaTags {{ font-family: Georgia, 'Times New Roman', serif; font-size: 13px; font-style: italic; }} QLabel#personaDesc {{ color: {t['muted']}; font-size: 14px; }}
        QLabel#traitChip {{ border: 1px solid {t['border_soft']}; border-radius: 10px; padding: 5px 8px; background: {t['surface_2']}; color: {t['text']}; font-size: 11px; font-weight: 700; }}
        QLabel#warningText {{ color: {t['warning']}; font-size: 13px; }} QLabel#successText {{ color: {t['success']}; }} QLabel#dangerText {{ color: {t['danger']}; }}
        QFrame#line {{ background: {t['border']}; max-height: 1px; }}
        """

    def refresh_all_pages(self):
        current = self.stack.currentIndex()
        self.main_layout.removeWidget(self.header); self.header.deleteLater(); self.build_header(); self.main_layout.insertWidget(0, self.header)
        self.main_layout.removeWidget(self.footer); self.footer.deleteLater(); self.build_footer(); self.main_layout.addWidget(self.footer)
        while self.stack.count():
            widget = self.stack.widget(0); self.stack.removeWidget(widget); widget.deleteLater()
        self.build_pages(); self.apply_theme(); self.go_to(current)

    def build_header(self):
        self.header = TexturedFrame(self.theme, variant="bg_2", glow=True); add_shadow(self.header, blur=25, y=8)
        layout = QHBoxLayout(self.header); layout.setContentsMargins(22, 16, 22, 16); layout.setSpacing(18)
        dragon_mark = QLabel("🐉"); dragon_mark.setStyleSheet("font-size: 42px;"); layout.addWidget(dragon_mark)
        title_box = QVBoxLayout(); title = QLabel("DRAGON'S TOUCH"); title.setObjectName("appTitle"); tagline = QLabel("Forge Insight. Refine Power. Play Your Legend."); tagline.setObjectName("tagline")
        title_box.addWidget(title); title_box.addWidget(tagline); layout.addLayout(title_box, stretch=1)
        labels = [("Home", self.HOME), ("Workflow", self.WORKFLOW), ("Personas", self.PERSONA), ("Processing", self.PROCESSING), ("Report", self.REPORT), ("Settings", self.SETTINGS)]
        self.nav_buttons = []; group = QButtonGroup(self); group.setExclusive(True)
        for label, idx in labels:
            btn = NavButton(label, idx); btn.clicked.connect(lambda checked=False, page=idx: self.go_to(page)); self.nav_buttons.append(btn); group.addButton(btn); layout.addWidget(btn)
        theme_btn = QPushButton(f"Theme: {self.theme()['name']}"); theme_btn.setObjectName("secondaryButton"); theme_btn.clicked.connect(self.toggle_theme); layout.addWidget(theme_btn)
        layout.addWidget(MascotWidget(self.theme, compact=True))

    def build_footer(self):
        self.footer = TexturedFrame(self.theme, variant="bg_2")
        layout = QHBoxLayout(self.footer); layout.setContentsMargins(16, 8, 16, 8)
        left = QLabel("Single Desktop Experience  •  Built for Focus  •  Python + PySide6 Prototype"); left.setObjectName("helperText"); layout.addWidget(left, stretch=1)
        right = QLabel("Concept UI Design  •  Non-functional Mockup  •  Subject to Change"); right.setObjectName("helperText"); layout.addWidget(right)

    def toggle_theme(self):
        self.state.theme = ADVENTURERS_MAP if self.theme()["name"] == "Dragon Forge" else DRAGON_FORGE
        self.refresh_all_pages()

    def go_to(self, index):
        self.stack.setCurrentIndex(index)
        for btn in self.nav_buttons: btn.setChecked(btn.page_index == index)

    def build_pages(self):
        for page in [self.home_page(), self.workflow_page(), self.persona_page(), self.processing_page(), self.report_page(), self.settings_page()]:
            self.stack.addWidget(page)

    def page_shell(self, title, subtitle, heavy=False):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(0,0,0,0); layout.setSpacing(12)
        hero = TexturedFrame(self.theme, variant="surface", glow=heavy); add_shadow(hero, blur=20, y=6)
        hero_layout = QHBoxLayout(hero); hero_layout.setContentsMargins(22, 18, 22, 18); hero_layout.setSpacing(16)
        text_box = QVBoxLayout(); title_lbl = QLabel(title); title_lbl.setObjectName("pageTitle"); subtitle_lbl = QLabel(subtitle); subtitle_lbl.setObjectName("pageSubtitle"); subtitle_lbl.setWordWrap(True)
        text_box.addWidget(title_lbl); text_box.addWidget(subtitle_lbl); hero_layout.addLayout(text_box, stretch=1); hero_layout.addWidget(MascotWidget(self.theme))
        layout.addWidget(hero); return page, layout

    def make_line(self):
        line = QFrame(); line.setObjectName("line"); line.setFrameShape(QFrame.HLine); return line

    def home_page(self):
        page, layout = self.page_shell("Home Dashboard", "Choose how Dragon’s Touch will help forge, review, or refine your next Commander-style deck.", heavy=True)
        body = TexturedFrame(self.theme, variant="surface", glow=True); add_shadow(body, blur=30, y=10)
        body_layout = QVBoxLayout(body); body_layout.setContentsMargins(26,24,26,24); body_layout.setSpacing(18)
        top = QHBoxLayout(); intro = QLabel("The forge is warm. The map is open. What legend are we building today?"); intro.setObjectName("helperText"); top.addWidget(intro, stretch=1)
        personas = QPushButton("Personas"); personas.setObjectName("primaryButton"); personas.clicked.connect(lambda: self.go_to(self.PERSONA)); top.addWidget(personas); body_layout.addLayout(top); body_layout.addWidget(self.make_line())
        grid = QGridLayout(); grid.setSpacing(18)
        tiles = [("⚒", "Build Up", "Create and refine your deck.", self.WORKFLOW), ("🔍", "Deck Review / Clean Up", "Analyze and improve your deck.", self.WORKFLOW), ("📥", "Import Deck", "Bring in a list from file or source.", self.WORKFLOW), ("📖", "Saved Decks / History", "Open past decks and progress.", self.SETTINGS), ("🧭", "Combo Finder", "Discover powerful interactions.", self.PROCESSING), ("🃏", "Card Suggestions", "Find cards that fit your plan.", self.REPORT), ("📝", "Worksheet / Guided Questions", "Answer prompts to sharpen focus.", self.WORKFLOW), ("⚙", "Settings", "Customize theme and preferences.", self.SETTINGS)]
        for i, (icon, title, subtitle, page_idx) in enumerate(tiles):
            tile = DashboardTile(icon, title, subtitle); tile.clicked.connect(lambda checked=False, idx=page_idx: self.go_to(idx)); grid.addWidget(tile, i//4, i%4)
        for col in range(4): grid.setColumnStretch(col, 1)
        for row in range(2): grid.setRowStretch(row, 1)
        body_layout.addLayout(grid, stretch=1)
        quote = QLabel("Forge better decks. Become legend."); quote.setAlignment(Qt.AlignCenter); quote.setObjectName("tagline"); body_layout.addWidget(quote)
        layout.addWidget(body, stretch=1); return page

    def workflow_sidebar(self):
        sidebar = TexturedFrame(self.theme, variant="surface_2"); sidebar.setFixedWidth(290); add_shadow(sidebar, blur=20, y=6)
        layout = QVBoxLayout(sidebar); layout.setContentsMargins(18,18,18,18); layout.setSpacing(12)
        def cap(text): label = QLabel(text); label.setObjectName("smallCaps"); return label
        layout.addWidget(cap("CURRENT MODE")); layout.addWidget(QLabel("Deck Review / Build Up")); layout.addWidget(cap("DECK")); layout.addWidget(QLabel(f"<b>{self.state.deck_name}</b>")); c = QLabel(self.state.commanders); c.setObjectName("helperText"); c.setWordWrap(True); layout.addWidget(c)
        layout.addWidget(cap("WORKFLOW STEPS"))
        for i, step in enumerate(["Deck Identity", "Strategy & Game Plan", "Key Cards & Synergies", "Strengths & Weaknesses", "Meta & Playgroup", "Review & Confirm"], 1):
            lbl = QLabel(("➤ " if i == 1 else "○ ") + step); lbl.setStyleSheet(f"color: {self.theme()['accent_2'] if i == 1 else self.theme()['muted']};"); layout.addWidget(lbl)
        layout.addWidget(cap("SELECTED PERSONA")); layout.addWidget(QLabel(f"☕🐲  {self.state.selected_persona}")); change = QPushButton("Change Persona"); change.clicked.connect(lambda: self.go_to(self.PERSONA)); layout.addWidget(change)
        layout.addWidget(cap("DECK STATUS")); status = QLabel("Saved progress: Demo only\nWarnings: 2 placeholder issues"); status.setObjectName("helperText"); status.setWordWrap(True); layout.addWidget(status)
        layout.addStretch(1); layout.addWidget(QPushButton("Import")); layout.addWidget(QPushButton("Export")); report_btn = QPushButton("Forge Report"); report_btn.setObjectName("primaryButton"); report_btn.clicked.connect(lambda: self.go_to(self.PROCESSING)); layout.addWidget(report_btn); return sidebar

    def workflow_page(self):
        page, layout = self.page_shell("Workflow / Guided Worksheet", "Structured input, mentor-style guidance, and a restrained workspace for serious deck tuning.")
        body = QWidget(); body_layout = QHBoxLayout(body); body_layout.setContentsMargins(0,0,0,0); body_layout.setSpacing(14); body_layout.addWidget(self.workflow_sidebar())
        workspace = TexturedFrame(self.theme, variant="surface", parchment=(self.theme()["mode"] == "light")); add_shadow(workspace, blur=24, y=8)
        work = QVBoxLayout(workspace); work.setContentsMargins(24,22,24,22); work.setSpacing(16)
        step = QLabel("Step 1 of 6  •  Deck Identity"); step.setObjectName("sectionTitle"); work.addWidget(step)
        helper = QLabel("Let’s begin by understanding the heart of your deck. Answer a few questions so your chosen guide can protect the cards that matter."); helper.setObjectName("helperText"); helper.setWordWrap(True); work.addWidget(helper)
        identity = SectionPanel("Core Identity", self.theme, parchment=(self.theme()["mode"] == "light")); form = QGridLayout(); form.setHorizontalSpacing(16); form.setVerticalSpacing(12)
        widgets = [(QLabel("Deck Name"), QLineEdit(self.state.deck_name)), (QLabel("Commander / Commanders"), QLineEdit(self.state.commanders))]
        form.addWidget(widgets[0][0],0,0); form.addWidget(widgets[0][1],1,0); form.addWidget(widgets[1][0],0,1); form.addWidget(widgets[1][1],1,1)
        form.addWidget(QLabel("Primary goal or win condition"),2,0,1,2); goal = QPlainTextEdit(); goal.setPlainText("Overwhelm opponents with synergistic threats, value engines, and a clear finishing plan."); goal.setMinimumHeight(94); form.addWidget(goal,3,0,1,2)
        meta = QComboBox(); meta.addItems(["Casual / Friendly", "Upgraded Casual", "High Power", "Bracket 3", "Bracket 4"]); budget = QLineEdit("$200")
        form.addWidget(QLabel("Playgroup / Meta"),4,0); form.addWidget(QLabel("Budget Target"),4,1); form.addWidget(meta,5,0); form.addWidget(budget,5,1); identity.body.addLayout(form); work.addWidget(identity)
        tags = SectionPanel("Strategy Tags", self.theme); pill_row = QHBoxLayout();
        for name, checked in [("Aggro",False),("Midrange",True),("Control",False),("Combo",False),("Ramp",True),("Tokens",True),("Aristocrats",False),("Other",False)]: pill_row.addWidget(PillButton(name, checked))
        pill_row.addStretch(1); tags.body.addLayout(pill_row); work.addWidget(tags)
        mentor = TexturedFrame(self.theme, variant="surface_2", glow=True); mentor_l = QHBoxLayout(mentor); mentor_l.setContentsMargins(16,14,16,14); mentor_l.addWidget(QLabel("☕🐲")); txt = QLabel(f"<b>{self.state.selected_persona} says:</b> The clearer your goal, the better I can read the deck’s true shape. Fast entry is welcome, but context makes the final report smarter."); txt.setObjectName("helperText"); txt.setWordWrap(True); mentor_l.addWidget(txt, stretch=1); work.addWidget(mentor)
        checks = QHBoxLayout();
        for text in ["Protect pet cards", "Allow combo review", "Prefer synergy over raw power"]: checks.addWidget(QCheckBox(text))
        checks.addStretch(1); work.addLayout(checks); warning = QLabel("⚠ Skipping guided context may reduce report quality."); warning.setObjectName("warningText"); work.addWidget(warning)
        buttons = QHBoxLayout(); buttons.addWidget(QPushButton("Back")); buttons.addWidget(QPushButton("Save Progress")); buttons.addStretch(1); adv = QPushButton("Skip to Advanced Edit"); adv.clicked.connect(lambda: QMessageBox.warning(self, "Advanced Edit", "Skipping guided context may reduce report quality.")); buttons.addWidget(adv); nxt = QPushButton("Next"); nxt.setObjectName("primaryButton"); buttons.addWidget(nxt); work.addLayout(buttons)
        body_layout.addWidget(workspace, stretch=1); layout.addWidget(body, stretch=1); return page

    def persona_page(self):
        page, layout = self.page_shell("Persona Selection", "Choose the guide who will help analyze, narrate, and present the deck report.", heavy=True)
        body = TexturedFrame(self.theme, variant="surface", glow=True); add_shadow(body, blur=28, y=9); body_l = QVBoxLayout(body); body_l.setContentsMargins(26,24,26,24); body_l.setSpacing(18)
        phil = QHBoxLayout(); phil.addWidget(QLabel("Core Philosophies")); phil.addStretch(1)
        for name in ["Timmy / Tammy", "Johnny / Jenny", "Spike", "Adventurer"]: phil.addWidget(PillButton(name, checked=(name=="Adventurer")))
        body_l.addLayout(phil); body_l.addWidget(self.make_line()); cards = QHBoxLayout(); cards.setSpacing(18)
        personas = [
            {"name":"The Sage","icon":"🧙","tags":"Balance • Wisdom • Growth","desc":"Sees the whole picture. Guides with patience, deep understanding, and careful explanation.","chips":["Balanced","Educational","Methodical"],"accent":self.theme()["persona_sage"]},
            {"name":"The Warlord","icon":"🐲","tags":"Power • Aggression • Domination","desc":"Seeks victory through strength, speed, pressure, and decisive action.","chips":["Aggressive","Competitive","Results-Driven"],"accent":self.theme()["persona_warlord"]},
            {"name":"The Artisan","icon":"🛠","tags":"Creativity • Synergy • Ingenuity","desc":"Finds beauty in synergy. Loves clever interactions, strange engines, and unique builds.","chips":["Creative","Synergistic","Innovative"],"accent":self.theme()["persona_artisan"]},]
        for p in personas: cards.addWidget(PersonaCard(p, self.theme, self.select_persona, selected=(p["name"]==self.state.selected_persona)))
        body_l.addLayout(cards, stretch=1); footer = QHBoxLayout(); footer.addWidget(QLabel(f"Selected guide: <b>{self.state.selected_persona}</b>")); footer.addStretch(1); cont = QPushButton("Continue to Workflow"); cont.setObjectName("primaryButton"); cont.clicked.connect(lambda: self.go_to(self.WORKFLOW)); footer.addWidget(cont); body_l.addLayout(footer); layout.addWidget(body, stretch=1); return page

    def select_persona(self, name): self.state.selected_persona = name; self.refresh_all_pages(); self.go_to(self.PERSONA)

    def processing_page(self):
        page, layout = self.page_shell("Thinking / Processing", "The selected persona talks through the review while Dragon’s Touch forges the report.", heavy=True)
        body = QWidget(); body_l = QHBoxLayout(body); body_l.setContentsMargins(0,0,0,0); body_l.setSpacing(14)
        left = TexturedFrame(self.theme, variant="surface"); left.setFixedWidth(330); add_shadow(left, blur=22, y=8); l = QVBoxLayout(left); l.setContentsMargins(20,20,20,20); l.setSpacing(12)
        l.addWidget(QLabel(f"<b>{self.state.selected_persona} Speaks</b>")); narr = QLabel("“I am finding the root of your deck’s growing shape. Let me examine the branches, the leaves, and the soil beneath.”"); narr.setWordWrap(True); narr.setObjectName("helperText"); l.addWidget(narr); l.addWidget(self.make_line())
        for item, done in [("Understanding deck identity",True),("Mapping key themes & mechanics",True),("Analyzing card relationships",True),("Evaluating mana base",True),("Scanning for synergy depth",False),("Checking for weaknesses",False),("Comparing to playgroup meta",False),("Forging final report",False)]:
            lbl = QLabel(("✓ " if done else "◦ ")+item); lbl.setStyleSheet(f"color: {self.theme()['success'] if done else self.theme()['muted']};"); l.addWidget(lbl)
        l.addStretch(1); l.addWidget(QLabel("Elapsed Time: 00:01:48\nEst. Remaining: 00:01:12"))
        center = TexturedFrame(self.theme, variant="bg_2", glow=True); add_shadow(center, blur=30, y=10); c_l = QVBoxLayout(center); c_l.setContentsMargins(18,18,18,18); title = QLabel("Forging Your Deck Report"); title.setObjectName("sectionTitle"); title.setAlignment(Qt.AlignCenter); c_l.addWidget(title); c_l.addWidget(ForgeVisual(self.theme), stretch=1)
        right = TexturedFrame(self.theme, variant="surface"); right.setFixedWidth(340); add_shadow(right, blur=22, y=8); r = QVBoxLayout(right); r.setContentsMargins(20,20,20,20); r.setSpacing(12); r.addWidget(QLabel("<b>Analysis Status</b>")); self.processing_bars=[]
        for label, value in [("Deck Identity",100),("Themes & Strategy",100),("Card Synergy",86),("Mana & Curve",72),("Strengths",44),("Weaknesses",22),("Meta Analysis",18),("Report Assembly",8)]:
            r.addWidget(QLabel(label)); bar=QProgressBar(); bar.setRange(0,100); bar.setValue(value); bar.setFormat("%p%"); self.processing_bars.append(bar); r.addWidget(bar)
        r.addStretch(1); r.addWidget(MascotWidget(self.theme)); report_btn=QPushButton("View Demo Report"); report_btn.setObjectName("primaryButton"); report_btn.clicked.connect(lambda: self.go_to(self.REPORT)); r.addWidget(report_btn)
        body_l.addWidget(left); body_l.addWidget(center, stretch=1); body_l.addWidget(right); layout.addWidget(body, stretch=1); return page

    def update_processing_animation(self):
        if self.stack.currentIndex() != self.PROCESSING or not self.processing_bars: return
        for i, bar in enumerate(self.processing_bars):
            if bar.value() < 100 and i >= 4: bar.setValue(min(100, bar.value() + (1 if i < 6 else 2)))

    def report_page(self):
        page, layout = self.page_shell("Final Report / Results", "A persona-presented fantasy tome with structured, readable deck analysis sections.", heavy=True)
        body = QWidget(); body_l = QHBoxLayout(body); body_l.setContentsMargins(0,0,0,0); body_l.setSpacing(14)
        nav = TexturedFrame(self.theme, variant="surface_2"); nav.setFixedWidth(280); add_shadow(nav, blur=22, y=8); n = QVBoxLayout(nav); n.setContentsMargins(18,18,18,18); n.setSpacing(10); n.addWidget(QLabel("<b>Report Overview</b>"))
        for item in ["Deck Identity / Strategy", "Synergy Overview", "Strengths", "Possible Issues", "Suggested Cuts", "Recommendations", "Next Steps"]: n.addWidget(NavButton(item))
        n.addStretch(1); exp = QPushButton("Export Report"); exp.setObjectName("primaryButton"); exp.clicked.connect(lambda: QMessageBox.information(self, "Prototype", "Export is a placeholder.")); n.addWidget(exp); n.addWidget(QPushButton("Save")); n.addWidget(QPushButton("Copy"))
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll_body = TexturedFrame(self.theme, variant="card", glow=True, parchment=True); add_shadow(scroll_body, blur=28, y=8); rep = QVBoxLayout(scroll_body); rep.setContentsMargins(28,26,28,26); rep.setSpacing(18)
        presented = QLabel(f"Presented by {self.state.selected_persona}"); presented.setObjectName("sectionTitle"); rep.addWidget(presented); intro = QLabel("This is a placeholder report showing how Dragon’s Touch could present a polished, readable deck review. Future versions will connect this panel to the real deck helper output."); intro.setWordWrap(True); intro.setObjectName("helperText"); rep.addWidget(intro)
        sections = [("Deck Identity / Strategy", "This deck appears to be a focused synergy deck with a clear commander-centered plan. The final tool will distinguish primary strategy, secondary strategy, support packages, and off-plan cards."), ("Synergy Overview", "Strong synergy between token generation, value engines, and board development. Several cards are likely to be weak in isolation but strong in context."), ("Strengths", "✓ Clear identity\n✓ Strong commander support\n✓ Multiple overlapping engines\n✓ Room for meaningful upgrades"), ("Possible Issues", "⚠ Some cards may be generically strong but off-plan.\n⚠ Mana curve may need review.\n⚠ Interaction count may need playgroup-specific tuning."), ("Suggested Cuts or Improvements", "• Review replaceable off-theme cards.\n• Protect pet cards and strategy-critical low-power cards.\n• Add upgrades that strengthen the primary engine."), ("Recommendations / Next Steps", "1. Confirm desired power level.\n2. Review protected cards.\n3. Compare possible cuts to replacement categories.\n4. Run combo review only if desired.")]
        for title, text in sections:
            panel = SectionPanel(title, self.theme, parchment=True); body_text = QLabel(text); body_text.setWordWrap(True); body_text.setObjectName("helperText"); panel.body.addWidget(body_text)
            if title == "Synergy Overview":
                thumbs = QHBoxLayout()
                for i in range(5):
                    thumb = QLabel(f"Card\n{i+1}"); thumb.setAlignment(Qt.AlignCenter); thumb.setFixedSize(82,112); thumb.setStyleSheet(f"background: {self.theme()['surface_2']}; border: 1px solid {self.theme()['border']}; border-radius: 10px;"); thumbs.addWidget(thumb)
                thumbs.addStretch(1); panel.body.addLayout(thumbs)
            rep.addWidget(panel)
        note = QLabel("☕🐲 Report forged. Wisdom served warm."); note.setAlignment(Qt.AlignRight); note.setObjectName("tagline"); rep.addWidget(note); scroll.setWidget(scroll_body)
        body_l.addWidget(nav); body_l.addWidget(scroll, stretch=1); layout.addWidget(body, stretch=1); return page

    def settings_page(self):
        page, layout = self.page_shell("Settings / Theme Preview", "Preview theme direction and prototype preferences. Real settings persistence is not connected yet.")
        body = TexturedFrame(self.theme, variant="surface"); add_shadow(body, blur=24, y=8); b = QVBoxLayout(body); b.setContentsMargins(26,24,26,24); b.setSpacing(18)
        theme_panel = SectionPanel("Theme Selection", self.theme); row = QHBoxLayout(); dark = QPushButton("Dragon Forge / Dark Mode"); dark.setObjectName("primaryButton" if self.theme()["name"]=="Dragon Forge" else "secondaryButton"); dark.clicked.connect(lambda: self.set_theme(DRAGON_FORGE)); light = QPushButton("Adventurer's Map / Light Mode"); light.setObjectName("primaryButton" if self.theme()["name"]=="Adventurer's Map" else "secondaryButton"); light.clicked.connect(lambda: self.set_theme(ADVENTURERS_MAP)); row.addWidget(dark); row.addWidget(light); row.addStretch(1); theme_panel.body.addLayout(row)
        desc = QLabel("Dragon Forge emphasizes dark iron, ember glow, and command-center focus. Adventurer’s Map emphasizes parchment, forest green, old gold, and cozy readability."); desc.setWordWrap(True); desc.setObjectName("helperText"); theme_panel.body.addWidget(desc); b.addWidget(theme_panel)
        preview = SectionPanel("Component Preview", self.theme, parchment=(self.theme()["mode"]=="light")); pr = QHBoxLayout(); pr.addWidget(QPushButton("Secondary Button")); primary=QPushButton("Primary Action"); primary.setObjectName("primaryButton"); pr.addWidget(primary); pr.addWidget(PillButton("Selected Pill", True)); pr.addWidget(PillButton("Option Pill")); pr.addStretch(1); preview.body.addLayout(pr); inrow = QHBoxLayout(); sample=QLineEdit("Sample input field"); combo=QComboBox(); combo.addItems(["Casual / Friendly", "Upgraded Casual", "High Power"]); inrow.addWidget(sample); inrow.addWidget(combo); preview.body.addLayout(inrow); b.addWidget(preview)
        about = SectionPanel("Prototype Scope", self.theme); txt = QLabel("This prototype is a styled navigation shell only. It intentionally avoids real card data, APIs, database access, deck import logic, and report generation. The goal is to test visual direction, screen layout, navigation, and theme feel."); txt.setObjectName("helperText"); txt.setWordWrap(True); about.body.addWidget(txt); b.addWidget(about); b.addStretch(1); layout.addWidget(body, stretch=1); return page

    def set_theme(self, theme): self.state.theme = theme; self.refresh_all_pages(); self.go_to(self.SETTINGS)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Dragon's Touch")
    app.setOrganizationName("Dragon's Touch Prototype")
    app.setStyle("Fusion")
    window = MainWindow(); window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
