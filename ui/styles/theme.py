"""Theme palettes and QSS builders for The Dragon's Touch PySide6 UI.

This module is part of the v0.7 alpha-hardening modularization track.
It contains visual styling data and stylesheet builders only; it must not
run backend analysis, call main.py, or alter staged UI state.
"""

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
    "combo_popup_bg": "#f4e4bd", "combo_popup_text": "#3a2818",
    "combo_popup_border": "#b08b4d", "combo_popup_item_bg": "#f4e4bd",
    "combo_popup_selected_bg": "#d9a441", "combo_popup_selected_text": "#3a2818",
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



def build_main_qss(t):
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
    input_paper_bg = t.get("parchment_2", t["input"])
    input_paper_bg_2 = t.get("parchment", input_paper_bg)
    input_paper_border = t.get("parchment_3", t["input_border"])
    input_paper_text = t.get("paper_text", input_text)
    input_paper_selection = t.get("accent_2", t["accent"])
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
    QLineEdit, QPlainTextEdit, QComboBox {{ color: {input_paper_text}; background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {input_paper_bg_2}, stop:1 {input_paper_bg}); border: 1px solid {input_paper_border}; border-radius: 12px; padding: 10px; selection-background-color: {input_paper_selection}; selection-color: {input_paper_text}; combobox-popup: 0; }}
    QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{ border: 1px solid {t["accent_2"]}; }}
    QPlainTextEdit QScrollBar:vertical {{ background: transparent; width: 10px; border-radius: 5px; }}
    QPlainTextEdit QScrollBar::handle:vertical {{ background: {t["border"]}; border-radius: 5px; min-height: 24px; }}
    QPlainTextEdit QScrollBar::handle:vertical:hover {{ background: {t["accent"]}; }}
    QPlainTextEdit#reportStatusPreview {{ color: {t["paper_text"]}; background: transparent; border: 0px; border-radius: 0px; padding: 4px; selection-background-color: {t["accent_2"]}; selection-color: {t["paper_text"]}; }}
    QPlainTextEdit#reportStatusPreview QScrollBar:vertical {{ background: transparent; width: 10px; border-radius: 5px; }}
    QPlainTextEdit#reportStatusPreview QScrollBar::handle:vertical {{ background: {t["border_soft"]}; border-radius: 5px; min-height: 24px; }}
    QComboBox::drop-down {{ border: none; width: 28px; }}
    QComboBox::down-arrow {{ color: {input_paper_text}; }}
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

