"""
The Dragon's Touch - PySide6 Desktop UI Alpha Foundation
Version: v0.7.0 — Desktop UI Alpha Foundation

Standalone local desktop UI foundation for a fantasy-themed Commander deck-building
and deck-review app.

This version focuses on:
- preserving the Dragon Forge / parchment manuscript visual direction
- formalizing the mockup into the first official desktop UI foundation
- preserving the locked v0.6.8.5 stable workflow while entering v0.7 alpha hardening
- using the guarded CLI bridge as the safe backend handoff
- loading generated reports as plain text while preserving CLI/main.py as the source of truth

Current scope:
- UI shell and navigation are active
- deck file selection and preview are active
- review settings and collection source staging are active
- Run Analysis can launch the guarded CLI bridge after explicit confirmation
- report outputs are written into unique timestamped folders by the backend
- generated reports can be detected, opened, and read in the Report Viewer as plain text
- Commander Spellbook/API calls remain disabled until a future opt-in phase
- command-line backend remains the stable source of truth

Run:
    pip install PySide6
    python dragons_touch_pyside6_workstation.py
"""

import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QSignalBlocker, QProcess, QProcessEnvironment, QUrl
from PySide6.QtGui import QFont, QDesktopServices, QTextCursor
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QComboBox, QFileDialog, QFrame,
    QHBoxLayout, QLabel, QListView, QMainWindow, QMessageBox,
    QPlainTextEdit, QPushButton, QScrollArea, QSizePolicy,
    QStackedWidget, QVBoxLayout, QWidget
)

try:
    from ui.constants import (
        APP_VERSION, APP_PHASE, BACKEND_STATUS, LOCKED_BACKEND_VERSION,
        OUTPUT_MODE_OPTIONS, REVIEW_DIRECTION_OPTIONS, REVIEW_INTENSITY_OPTIONS, BUILD_UP_MODE_OPTIONS,
        PROMPT_MODE_OPTIONS, INTENDED_BRACKET_OPTIONS, GUIDE_PRESENTATION_OPTIONS,
        PHILOSOPHY_SUBTYPE_OPTIONS, RUN_DETAIL_OPTIONS, COLLECTION_MODE_OPTIONS, COLLECTION_SOURCE_OPTIONS, COMBO_AWARENESS_OPTIONS,
        DEFAULT_SELECTED_PHILOSOPHY, DEFAULT_PHILOSOPHY_SUBTYPE, DEFAULT_GUIDE_PRESENTATION,
        DEFAULT_OUTPUT_MODE, DEFAULT_REVIEW_DIRECTION, DEFAULT_REVIEW_INTENSITY, DEFAULT_BUILD_UP_MODE,
        DEFAULT_PROMPT_MODE, DEFAULT_INTENDED_BRACKET, DEFAULT_COLLECTION_MODE, DEFAULT_COLLECTION_SOURCE_MODE, DEFAULT_COMBO_AWARENESS_MODE,
    )
    from ui.styles.theme import DRAGON_FORGE, ADVENTURERS_MAP, build_main_qss
    from ui.widgets import (
        add_shadow, TexturedPanel, ForgeOrb, SidebarButton, Badge, ReportCard, SmallStat, PillButton
    )
    from ui.state import AppState
    from ui.services import report_detector, cli_bridge, backend_runner
    from ui.pages.deck_selection_page import build_deck_selection_page
    from ui.pages.review_setup_page import build_review_setup_page
    from ui.pages.philosophy_lens_page import build_philosophy_lens_page
    from ui.pages.collection_source_page import build_collection_source_page
    from ui.pages.run_analysis_page import build_run_analysis_page
    from ui.pages.report_viewer_page import build_report_viewer_page
    from ui.pages.future_workspace_page import build_batch_reports_page, build_settings_page
except ImportError:  # Allows direct execution from inside the ui/ folder during local testing.
    from constants import (
        APP_VERSION, APP_PHASE, BACKEND_STATUS, LOCKED_BACKEND_VERSION,
        OUTPUT_MODE_OPTIONS, REVIEW_DIRECTION_OPTIONS, REVIEW_INTENSITY_OPTIONS, BUILD_UP_MODE_OPTIONS,
        PROMPT_MODE_OPTIONS, INTENDED_BRACKET_OPTIONS, GUIDE_PRESENTATION_OPTIONS,
        PHILOSOPHY_SUBTYPE_OPTIONS, RUN_DETAIL_OPTIONS, COLLECTION_MODE_OPTIONS, COLLECTION_SOURCE_OPTIONS, COMBO_AWARENESS_OPTIONS,
        DEFAULT_SELECTED_PHILOSOPHY, DEFAULT_PHILOSOPHY_SUBTYPE, DEFAULT_GUIDE_PRESENTATION,
        DEFAULT_OUTPUT_MODE, DEFAULT_REVIEW_DIRECTION, DEFAULT_REVIEW_INTENSITY, DEFAULT_BUILD_UP_MODE,
        DEFAULT_PROMPT_MODE, DEFAULT_INTENDED_BRACKET, DEFAULT_COLLECTION_MODE, DEFAULT_COLLECTION_SOURCE_MODE, DEFAULT_COMBO_AWARENESS_MODE,
    )
    from styles.theme import DRAGON_FORGE, ADVENTURERS_MAP, build_main_qss
    from widgets import (
        add_shadow, TexturedPanel, ForgeOrb, SidebarButton, Badge, ReportCard, SmallStat, PillButton
    )
    from state import AppState
    from services import report_detector, cli_bridge, backend_runner
    from pages.deck_selection_page import build_deck_selection_page
    from pages.review_setup_page import build_review_setup_page
    from pages.philosophy_lens_page import build_philosophy_lens_page
    from pages.collection_source_page import build_collection_source_page
    from pages.run_analysis_page import build_run_analysis_page
    from pages.report_viewer_page import build_report_viewer_page
    from pages.future_workspace_page import build_batch_reports_page, build_settings_page

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
# - v0.6.7.9.20 changes text boxes and dropdowns to the parchment/plain-text visual style while keeping scrollability.
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
# v0.6.7.12 checkpoint: desktop UI foundation is locked; future work should build on this guarded bridge rather than replacing it.
# v0.7.0 alpha hardening boundary: preserve UI staged state -> guarded confirmation -> subprocess/main.py -> CLI input bridge -> backend output folder -> report detection -> plain-text Report Viewer.
# Do not bypass main.py, silently execute backend commands, or create a second backend workflow.



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
        self.report_viewer_current_file_label = None
        self.report_viewer_copy_button = None
        self.report_viewer_refresh_file_button = None
        self.report_viewer_open_current_folder_button = None
        self.report_viewer_search_input = None
        self.report_viewer_wrap_button = None
        self.open_output_folder_button = None
        self.open_normal_report_folder_button = None
        self.open_debug_report_folder_button = None
        self.guarded_run_button = None
        self.guarded_run_buttons = []
        self.run_analysis_content_stack = None
        self.run_analysis_running_status_label = None
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
        self.report_viewer_current_file_label = None
        self.report_viewer_copy_button = None
        self.report_viewer_refresh_file_button = None
        self.report_viewer_open_current_folder_button = None
        self.open_output_folder_button = None
        self.open_normal_report_folder_button = None
        self.open_debug_report_folder_button = None
        self.guarded_run_button = None
        self.guarded_run_buttons = []
        self.run_analysis_content_stack = None
        self.run_analysis_running_status_label = None
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
        left = QLabel(f"The Dragon's Touch {APP_VERSION}  •  PySide6 Desktop UI Alpha Foundation  •  {BACKEND_STATUS}")
        left.setObjectName("footerText")
        right = QLabel("Single-deck alpha workflow. Guarded runs only. No automatic deck edits.")
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
            ("📚  Batch Tools", self.BATCH_REPORTS), ("⚒  Settings", self.SETTINGS),
        ]
        group = QButtonGroup(self)
        group.setExclusive(True)
        for text, index in nav_items:
            btn = SidebarButton(text, index)
            if index == self.COLLECTION:
                btn.setToolTip("Optional: choose collection folder/files for collection-aware reviews.")
            elif index == self.PHILOSOPHY:
                btn.setToolTip("Optional playstyle guidance; does not override legality or strategy.")
            elif index == self.SETTINGS:
                btn.setToolTip("App preferences and future utilities; not required for a normal run.")
            elif index == self.BATCH_REPORTS:
                btn.setToolTip("Future multi-deck tools; not active for normal single-deck reviews.")
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
        notes = QLabel("• Single-deck alpha review only\n• Use guarded confirmation before analysis\n• Report Viewer loads plain text\n• Future features stay labeled and disabled; Batch Tools are future / not active yet")
        notes.setObjectName("mutedText"); notes.setWordWrap(True); layout.addWidget(notes)
        layout.addStretch(1)
        mascot = TexturedPanel(self.theme, kind="iron_2", glow=True, corners=False)
        mascot_layout = QVBoxLayout(mascot); mascot_layout.setContentsMargins(12, 12, 12, 12)
        dragon = QLabel("☕🐲"); dragon.setObjectName("contextMascot"); dragon.setAlignment(Qt.AlignCenter)
        text = QLabel("Ready to guide a deck through the locked v0.6.8.5 workflow while v0.7 hardens alpha usability."); text.setObjectName("mutedText"); text.setWordWrap(True); text.setAlignment(Qt.AlignCenter)
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
        return build_main_qss(t)

    def go_to(self, index):
        self.stack.setCurrentIndex(index)
        for btn in self.nav_buttons:
            btn.setChecked(btn.index == index)
        if index == self.RUN_ANALYSIS:
            self.refresh_run_analysis_previews()
        if index == self.REPORT:
            self.refresh_report_viewer_file_list()

    def is_guarded_run_active(self):
        """Return True only while a guarded backend process is actively running."""
        return bool(self.state.guarded_run_in_progress and self.backend_process is not None)

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
        if getattr(self, "run_analysis_content_stack", None) is not None:
            self.run_analysis_content_stack.setCurrentIndex(1 if self.is_guarded_run_active() else 0)
        if getattr(self, "run_analysis_running_status_label", None) is not None:
            self.run_analysis_running_status_label.setText(
                "The helper dragon is working through the guarded backend. Report Viewer will open when the run completes successfully."
                if self.is_guarded_run_active()
                else "The forge is ready. The helper-dragon loading view only appears during an active guarded run."
            )
        guarded_buttons = list(getattr(self, "guarded_run_buttons", []))
        if self.guarded_run_button is not None and self.guarded_run_button not in guarded_buttons:
            guarded_buttons.append(self.guarded_run_button)
        for button in guarded_buttons:
            button.setEnabled(not self.is_guarded_run_active())
            button.setText("Running Analysis..." if self.is_guarded_run_active() else "Run Analysis")

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
            f"This control is a future/placeholder utility in {APP_VERSION}. The active alpha workflow is Deck Selection -> Review Setup -> Philosophy Lens -> optional Collection Source -> Run Analysis -> Report Viewer. Settings and Batch Tools are not required for normal single-deck reviews."
        )

    def backend_hook_message(self, hook_name):
        QMessageBox.information(
            self,
            "Backend Hook Placeholder",
            f"{hook_name} is reserved for a later deliberate patch. The active alpha workflow still uses guarded main.py execution and the locked {LOCKED_BACKEND_VERSION} backend boundary."
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
        return build_deck_selection_page(self)

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
            f"Combo awareness: {self.state.combo_awareness_mode}\n"
            f"Collection mode: {self.state.collection_mode}\n"
            f"Collection source: {self.state.collection_source_mode}\n"
            "Backend config mapping: staged by guarded bridge when run is confirmed"
        )

    def stage_review_settings(self, output_combo, direction_combo, cut_combo, build_up_combo, prompt_combo, budget_input, intended_bracket_combo, combo_awareness_combo=None, summary_label=None, intensity_meaning_label=None):
        """Auto-stage Review Setup choices without requiring an Apply button or popup."""
        self.state.output_mode = output_combo.currentText()
        self.state.review_direction = direction_combo.currentText()
        self.state.cut_depth = cut_combo.currentText()
        self.state.build_up_mode = build_up_combo.currentText()
        self.state.prompt_mode = prompt_combo.currentText()
        self.state.budget_note = budget_input.text().strip() or "No budget note provided"
        self.state.intended_bracket = intended_bracket_combo.currentText()
        if combo_awareness_combo is not None:
            self.state.combo_awareness_mode = combo_awareness_combo.currentText()
        self.state.bracket = self.state.intended_bracket if self.state.intended_bracket != "Not sure yet" else "Not estimated"
        self.state.status = "Review settings auto-staged"
        if summary_label is not None:
            summary_label.setText(self.review_settings_summary_text())
        if intensity_meaning_label is not None:
            intensity_meaning_label.setText(self.review_intensity_meaning())
        self.refresh_context_panel_values()
        self.refresh_run_analysis_previews()

    def page_analysis_setup(self):
        return build_review_setup_page(self)

    def page_philosophy(self):
        return build_philosophy_lens_page(self)

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
            f"- Combo awareness: {self.state.combo_awareness_mode}\n"
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
            f"- combo_awareness_mode -> {self.state.combo_awareness_mode}\n"
            "- combo_awareness_default -> Disabled; user opt-in required\n"
            "- combo_awareness_backend_behavior -> separate artifact only; no normal report injection\n"
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
            f"- combo_awareness_mode -> {self.state.combo_awareness_mode}\n"
            f"- collection_source_detail -> {source_detail}\n\n"
            "Bridge Safety Gates For A Later Patch\n"
            "- require visible command preview before execution -> True\n"
            "- require explicit user action before execution -> True\n"
            "- require backend path/entrypoint validation -> True\n"
            "- require output folder handling plan -> True\n"
            "- require error capture and user-readable failure message -> True\n"
            "- guarded_execution_bridge_preview_ready -> True\n"
            f"- combo_awareness_mode -> {self.state.combo_awareness_mode}\n"
            "- combo_awareness_optional -> True\n"
            "- ready_for_actual_qprocess_execution -> guarded confirmation required"
        )

    def backend_entrypoint_path(self):
        """Resolve the currently previewed backend entrypoint relative to the working directory."""
        return backend_runner.backend_entrypoint_path(self.state)

    def guarded_command_preview(self):
        """Build the visible command preview for the guarded bridge. This matches the manual backend command."""
        return backend_runner.guarded_command_preview(self.state)

    def guarded_command_parts(self):
        """Return the actual guarded command as a list. Never use shell=True."""
        return backend_runner.guarded_command_parts(self.state)


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
            "- This is the actual guarded execution path.\n"
            "- main.py can run only after explicit user confirmation.\n"
            "- The UI uses QProcess with a command list and never uses shell=True.\n"
            "- The UI must keep CLI/main.py as the source of truth and must not invent a second backend workflow.\n"
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
            "- companion_legality_source -> backend validation only; UI preview does not enforce companion restrictions\n"
            f"- collection_folder_or_file_path_answered -> {self.collection_source_detail_answered()}\n"
            f"- active_collection_source_detail -> {self.collection_source_detail_preview_text()}\n"
            f"- specific_philosophy_subtype_answered -> {self.should_send_philosophy_subtype_input()}\n"
            f"- last_cli_input_sent -> {self.state.cli_input_bridge_last_sent}\n"
            "- stdin_closed_after_known_answers -> True\n"
            "- unknown_future_prompts_answered -> False\n\n"
            "Execution Readiness Checklist\n"
            f"- deck_file_selected_for_ui_context -> {deck_ready}\n"
            f"- selected_deck_handoff_env -> {self.state.selected_deck_path if deck_ready else 'not set; run blocked until a deck is selected'}\n"
            f"- combo_awareness_mode -> {self.state.combo_awareness_mode}\n"
            f"- combo_awareness_env_enabled -> {backend_runner.combo_awareness_enabled(self.state)}\n"
            f"- combo_awareness_env_artifact -> {backend_runner.combo_awareness_artifact_value(self.state)}\n"
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
            "- output_folder_opening -> active after report detection succeeds\n\n"
            "Current Patch Safety Boundary\n"
            "- subprocess.run -> disabled; QProcess is used for guarded execution\n"
            "- main.py execution -> confirmation-gated\n"
            "- backend analysis -> only through CLI/main.py after confirmation\n"
            "- Commander Spellbook/API calls -> disabled\n"
            "- ready_for_actual_execution -> guarded only, not automatic\n"
        )

    def cli_output_mode_input_value(self):
        """Map the UI Output Mode to the first known main.py CLI prompt."""
        return cli_bridge.output_mode_input_value(self.state)

    def cli_review_direction_input_value(self):
        """Map the UI Review Direction to the second known main.py CLI prompt."""
        return cli_bridge.review_direction_input_value(self.state)

    def cli_build_up_mode_input_value(self):
        """Map the durable UI Build-Up Mode field to the build-up mode CLI prompt."""
        return cli_bridge.build_up_mode_input_value(self.state)

    def cli_review_intensity_input_value(self):
        """Map Review Intensity to the cut-down / strictness CLI prompt."""
        return cli_bridge.review_intensity_input_value(self.state)

    def cli_prompt_mode_input_value(self):
        """Map the UI Prompt Mode to the prompt interaction CLI prompt."""
        return cli_bridge.prompt_mode_input_value(self.state)

    def should_send_prompt_mode_input(self):
        """Send prompt mode after the known mode-specific prompt for build-up, cut-down, or auto-batch."""
        return cli_bridge.should_send_prompt_mode_input(self.state)

    def cli_philosophy_lens_input_value(self):
        """Map the UI Philosophy Lens to the CLI philosophy prompt."""
        return cli_bridge.philosophy_lens_input_value(self.state)

    def cli_philosophy_subtype_input_value(self):
        """Best-effort mapping for Specific philosophy subtype prompt using the planned subtype order."""
        return cli_bridge.philosophy_subtype_input_value(self.state)

    def should_send_philosophy_subtype_input(self):
        """Only send subtype when user chose an explicit subtype."""
        return cli_bridge.should_send_philosophy_subtype_input(self.state)

    def should_send_philosophy_lens_input(self):
        """Send philosophy after prompt mode for all bridged directions."""
        return cli_bridge.should_send_philosophy_lens_input(self.state)

    def cli_guide_presentation_input_value(self):
        """Map the UI Guide Presentation field to the CLI guide presentation prompt."""
        return cli_bridge.guide_presentation_input_value(self.state)

    def should_send_guide_presentation_input(self):
        """Only send guide presentation after the known top-level philosophy lens prompt is bridged."""
        return cli_bridge.should_send_guide_presentation_input(self.state)

    def cli_collection_mode_input_value(self):
        """Map the existing Collection Source page mode to the CLI collection mode prompt."""
        return cli_bridge.collection_mode_input_value(self.state)

    def should_send_collection_mode_input(self):
        """Only send collection mode after guide presentation is safely bridged in the known Build-up path."""
        return cli_bridge.should_send_collection_mode_input(self.state)

    def cli_collection_source_input_value(self):
        """Map the existing Collection Source page source mode to the CLI collection source prompt."""
        return cli_bridge.collection_source_input_value(self.state)

    def should_send_collection_source_input(self):
        """Only send collection source after collection mode is bridged and collection is enabled."""
        return cli_bridge.should_send_collection_source_input(self.state)

    def collection_source_detail_answered(self):
        """Return whether the active collection source detail is sufficiently staged for the guarded bridge preview."""
        return cli_bridge.collection_source_detail_answered(self.state)

    def collection_source_detail_preview_text(self):
        """Describe the active collection source detail without mixing stale folder/file state."""
        return cli_bridge.collection_source_detail_preview_text(self.state)

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
        return cli_bridge.cli_input_bridge_preview_text(self.state)


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
        return report_detector.resolve_backend_output_path(raw_path, self.state.backend_working_directory)

    def expected_report_category_notes(self):
        """Describe which report categories are expected based on the staged Output Mode."""
        return report_detector.expected_report_categories(self.state.output_mode)

    def path_contains_folder(self, path_text, folder_name):
        return report_detector.path_contains_folder(path_text, folder_name)

    def derive_output_folder_from_detected_files(self, detected_files):
        """Infer the deck output root from detected backend files without reading report contents."""
        return report_detector.derive_output_folder_from_detected_files(detected_files)

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
        detected, status = report_detector.normalize_detected_output_files(detected_files)
        self.state.last_backend_unique_output_status = status
        return detected

    def extract_files_written_paths(self, stdout_text):
        """Return backend file paths printed under the Files written block. Does not read files."""
        return report_detector.extract_files_written_paths(stdout_text, self.state.backend_working_directory)

    def detect_report_outputs_from_stdout(self, stdout_text):
        """Parse report paths from stdout and harden status messaging across output modes."""
        self.clear_detected_report_outputs()
        result = report_detector.detect_report_outputs(
            stdout_text,
            self.state.output_mode,
            self.state.backend_working_directory,
        )
        self.state.last_output_files = result.output_files
        self.state.last_normal_report_files = result.normal_report_files
        self.state.last_debug_report_files = result.debug_report_files
        self.state.last_output_folder = result.output_folder
        self.state.last_normal_report_folder = result.normal_report_folder
        self.state.last_debug_report_folder = result.debug_report_folder
        self.state.last_original_output_folder = result.original_output_folder
        self.state.last_backend_unique_output_status = result.backend_unique_output_status
        self.state.last_report_detection_status = result.status
        self.state.last_report_detection_mode = result.mode
        self.state.last_report_detection_warning = result.warning

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
            "Breakdown reports\n"
            f"{debug_preview}\n\n"
            "Boundary\n"
            "- The backend writes directly into a unique deck-file-distinguished timestamped output folder.\n"
            "- The UI detects file paths from stdout and opens generated folders/files without moving report contents.\n"
            "- Folder buttons are enabled only when a detected local folder exists.\n"
            "- The Report Viewer loads markdown/text as plain text only; deep parsing is intentionally deferred.\n"
            "- Backend report generation remains CLI/main.py source of truth.\n"
        )

    def folder_path_is_openable(self, folder_path):
        return report_detector.folder_path_is_openable(folder_path)

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
        self.open_folder_path(self.state.last_debug_report_folder, "Breakdown Report Folder")

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
            "- Combo awareness is optional, local-only, and writes separate artifacts when enabled.\n"
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
            f"Combo awareness mode:\n{self.state.combo_awareness_mode}\n\n"
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
            "- Combo awareness is passed by environment variable only when explicitly enabled in Review Setup.\n"
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
        self.state.last_guarded_run_status = "Running analysis through guarded main.py..."
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
        for env_key, env_value in backend_runner.environment_values(self.state).items():
            process_env.insert(env_key, env_value)
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
        payload = cli_bridge.build_cli_input_payload(self.state)
        self.backend_process.write(payload.input_text.encode("utf-8"))
        self.backend_process.closeWriteChannel()
        self.guarded_cli_input_sent = True
        self.state.cli_input_bridge_last_sent = payload.sent_summary
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
        if exit_code == 0:
            self.go_to(self.REPORT)
        else:
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
        return backend_runner.trim_process_output(text, limit=limit)

    def combo_tracker_preview_text(self):
        """Preview the optional local Commander Spellbook combo-awareness handoff. No API calls."""
        deck_path = self.state.selected_deck_path if self.state.selected_deck_path != "No deck file selected" else "None"
        deck_loaded = deck_path != "None"
        deck_signature_preview = "No deck file loaded"
        if deck_loaded:
            deck_signature_preview = f"{Path(deck_path).name} | size_preview={self.state.deck_size} | commander={self.state.commander}"

        artifact_note = backend_runner.combo_awareness_artifact_value(self.state)
        enabled = backend_runner.combo_awareness_enabled(self.state)
        return (
            "Optional Combo Awareness Preview\n"
            "- Current integration target -> local Commander Spellbook combo index\n"
            "- External API calls -> disabled\n"
            "- User opt-in required -> True\n"
            "- Default behavior -> Disabled\n"
            "- Normal report injection -> disabled\n"
            "- Generated output -> separate combo-awareness artifact(s) only\n\n"
            "Current UI Selection\n"
            f"- combo_awareness_mode -> {self.state.combo_awareness_mode}\n"
            f"- enabled_for_next_guarded_run -> {enabled}\n"
            f"- backend_artifact_mode -> {artifact_note}\n\n"
            "When Enabled\n"
            "- report_section -> writes normal/combo_awareness_report_section.md\n"
            "- breakdown -> writes debug/combo_awareness_breakdown.md\n"
            "- both -> writes both separate artifacts\n"
            "- missing combo cards remain findings, not automatic recommendations\n\n"
            "Current Deck Change Preview\n"
            f"- deck_loaded -> {deck_loaded}\n"
            f"- deck_signature_preview -> {deck_signature_preview}\n"
            "- local_combo_index_expected -> data/commander_spellbook/combo_index.json\n"
            "- raw_combo_json_expected -> data/combo.json\n"
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
        return build_run_analysis_page(self)

    def update_progress_mock(self):
        if not self.progress_bars or self.stack.currentIndex() != self.RUN_REVIEW: return
        self.progress_tick += 1
        for i, bar in enumerate(self.progress_bars): bar.setValue(min(100, (self.progress_tick * (i + 2) + i * 17) % 120))

    def report_file_role_rank(self, path_text):
        """Sort reports into the order a user is most likely to read them."""
        lower = Path(path_text).name.lower()
        ordered_markers = [
            ("_deck_report", 10),
            ("_user_guided_prompt", 20),
            ("combo_awareness_report_section", 30),
            ("_legality_debug", 110),
            ("_strategy_debug", 120),
            ("_bracket_debug", 130),
            ("_cut_pressure_debug", 140),
            ("_replacement_prompt_debug", 150),
            ("_diagnostics_debug", 160),
            ("_full_debug_report", 190),
            ("combo_awareness_breakdown", 200),
            ("combo_awareness_error", 210),
        ]
        for marker, rank in ordered_markers:
            if marker in lower:
                return rank
        return 999

    def detected_report_file_entries(self):
        """Return detected report files as display entries without parsing report sections."""
        entries = []
        for path_text in sorted(self.state.last_normal_report_files, key=self.report_file_role_rank):
            entries.append(("Normal", path_text))
        for path_text in sorted(self.state.last_debug_report_files, key=self.report_file_role_rank):
            entries.append(("Debug", path_text))
        # Include any detected report files that did not classify cleanly.
        known = {str(Path(path)) for _category, path in entries}
        other_paths = []
        for path_text in self.state.last_output_files:
            normalized = str(Path(path_text))
            if normalized not in known:
                other_paths.append(path_text)
        for path_text in sorted(other_paths, key=lambda p: Path(p).name.lower()):
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
            role = "Full Breakdown"
        elif "_legality_debug" in lower:
            role = "Legality"
        elif "_strategy_debug" in lower:
            role = "Strategy"
        elif "_bracket_debug" in lower:
            role = "Bracket"
        elif "_cut_pressure_debug" in lower:
            role = "Cut Pressure"
        elif "_replacement_prompt_debug" in lower:
            role = "Replacement"
        elif "_diagnostics_debug" in lower:
            role = "Diagnostics"
        elif "combo_awareness_report_section" in lower:
            role = "Combo Awareness Section"
        elif "combo_awareness_breakdown" in lower:
            role = "Combo Awareness Breakdown"
        elif "combo_awareness_error" in lower:
            role = "Combo Awareness Error"
        else:
            # Fallback keeps the label readable without forcing horizontal scrolling.
            stem = Path(path_text).stem
            role = stem[-34:] if len(stem) > 34 else stem
        return role if category in {"Normal", "Debug"} else f"{category}: {role}"

    def report_group_entries(self):
        """Group detected files for the Report Viewer navigation."""
        grouped = {"Normal Reports": [], "Breakdown Reports": [], "Other Files": []}
        for category, path_text in self.detected_report_file_entries():
            if category == "Normal":
                grouped["Normal Reports"].append((category, path_text))
            elif category == "Debug":
                grouped["Breakdown Reports"].append((category, path_text))
            else:
                grouped["Other Files"].append((category, path_text))
        return grouped

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
            self.apply_report_viewer_readability_settings()
        self.refresh_report_viewer_current_file_controls()

    def apply_report_viewer_readability_settings(self):
        """Apply report-reader wrapping. Font sizing is deferred to Settings later."""
        if self.report_viewer_text_box is None:
            return
        font = QFont("Segoe UI", self.state.report_viewer_font_size)
        self.report_viewer_text_box.setFont(font)
        self.report_viewer_text_box.setLineWrapMode(
            QPlainTextEdit.WidgetWidth if self.state.report_viewer_word_wrap else QPlainTextEdit.NoWrap
        )
        if self.report_viewer_wrap_button is not None:
            self.report_viewer_wrap_button.setText("Wrap: On" if self.state.report_viewer_word_wrap else "Wrap: Off")

    def toggle_report_viewer_word_wrap(self):
        self.state.report_viewer_word_wrap = not self.state.report_viewer_word_wrap
        self.apply_report_viewer_readability_settings()

    def jump_report_viewer_top(self):
        if self.report_viewer_text_box is not None:
            self.report_viewer_text_box.moveCursor(QTextCursor.Start)
            self.report_viewer_text_box.ensureCursorVisible()

    def jump_report_viewer_bottom(self):
        if self.report_viewer_text_box is not None:
            self.report_viewer_text_box.moveCursor(QTextCursor.End)
            self.report_viewer_text_box.ensureCursorVisible()

    def find_in_current_report(self):
        if self.report_viewer_text_box is None:
            return
        query = self.report_viewer_search_input.text().strip() if self.report_viewer_search_input is not None else ""
        self.state.report_viewer_search_text = query
        if not query:
            QMessageBox.information(self, "Search Report", "Enter text to search inside the currently loaded report.")
            return
        found = self.report_viewer_text_box.find(query)
        if not found:
            self.report_viewer_text_box.moveCursor(QTextCursor.Start)
            found = self.report_viewer_text_box.find(query)
        if not found:
            QMessageBox.information(self, "Search Report", f"No match found for: {query}")

    def latest_successful_run_checkpoint_text(self):
        success = str(self.state.last_guarded_run_return_code) == "0"
        folder_ready = self.folder_path_is_openable(self.state.last_output_folder)
        folder_name = Path(self.state.last_output_folder).name if folder_ready else "No successful output folder detected yet"
        if success and folder_ready:
            return f"Latest successful run: Yes — {folder_name}"
        if success:
            return "Latest successful run: Yes — report folder not detected"
        return "Latest successful run: Not yet detected in this UI session"

    def report_viewer_status_text(self):
        entries = self.detected_report_file_entries()
        current = Path(self.state.report_viewer_current_file)
        output_folder = Path(self.state.last_output_folder)
        current_name = current.name if current.is_file() or self.state.report_viewer_current_file != "No report file selected" else "No report selected"
        output_name = output_folder.name if self.state.last_output_folder not in {"No output folder detected yet", "Not detected"} else "No output folder detected"
        normal_count = len(self.state.last_normal_report_files)
        debug_count = len(self.state.last_debug_report_files)
        return (
            f"Status: {self.state.report_viewer_current_status}\n"
            f"Loaded file: {current_name}\n"
            f"Detected files: {len(entries)} total | Normal: {normal_count} | Breakdown: {debug_count}\n"
            f"{self.latest_successful_run_checkpoint_text()}\n"
            f"Latest run folder: {output_name}\n"
            "Boundary: plain text preview only; structured navigation and markdown rendering come later."
        )

    def report_viewer_current_file_label_text(self):
        path = Path(self.state.report_viewer_current_file)
        if path.is_file():
            return f"Current file: {path.name}"
        return "Current file: No report selected"

    def refresh_report_viewer_current_file_controls(self):
        """Refresh Report Viewer status/control widgets without rebuilding the page."""
        path = Path(self.state.report_viewer_current_file)
        file_ready = path.is_file()
        if self.report_viewer_status_label is not None:
            self.report_viewer_status_label.setPlainText(self.report_viewer_status_text())
            self.report_viewer_status_label.setToolTip(
                f"Current file: {self.state.report_viewer_current_file}\nOutput folder: {self.state.last_output_folder}"
            )
        if self.report_viewer_current_file_label is not None:
            self.report_viewer_current_file_label.setText(self.report_viewer_current_file_label_text())
            self.report_viewer_current_file_label.setToolTip(str(path) if file_ready else "No report selected")
        if self.open_current_report_file_button is not None:
            self.open_current_report_file_button.setEnabled(file_ready)
        if self.report_viewer_open_current_folder_button is not None:
            self.report_viewer_open_current_folder_button.setEnabled(file_ready and path.parent.exists())
        if self.report_viewer_refresh_file_button is not None:
            self.report_viewer_refresh_file_button.setEnabled(file_ready)
        if self.report_viewer_copy_button is not None:
            self.report_viewer_copy_button.setEnabled(bool(self.state.report_viewer_current_text.strip()))

    def refresh_report_viewer_file_list(self):
        """Populate Report Viewer with grouped files detected from the latest guarded run."""
        if self.report_viewer_file_buttons_layout is None:
            return
        self.clear_layout_widgets(self.report_viewer_file_buttons_layout)
        entries = self.detected_report_file_entries()
        if not entries:
            empty = QLabel("No generated report files detected yet. Run Analysis first.")
            empty.setObjectName("mutedText")
            empty.setWordWrap(True)
            self.report_viewer_file_buttons_layout.addWidget(empty)
        else:
            groups = self.report_group_entries()
            for group_name in ("Normal Reports", "Breakdown Reports", "Other Files"):
                group_entries = groups.get(group_name, [])
                if not group_entries:
                    continue
                header = QLabel(group_name.upper())
                header.setObjectName("smallCaps")
                self.report_viewer_file_buttons_layout.addWidget(header)
                for category, path_text in group_entries:
                    btn = QPushButton(self.report_file_button_label(category, path_text))
                    btn.setObjectName("utilityButton")
                    btn.setMinimumHeight(38)
                    btn.setToolTip(f"{Path(path_text).name}\n{path_text}")
                    btn.clicked.connect(lambda checked=False, p=path_text: self.load_report_file_into_viewer(p))
                    self.report_viewer_file_buttons_layout.addWidget(btn)
                self.report_viewer_file_buttons_layout.addSpacing(8)
        self.report_viewer_file_buttons_layout.addStretch(1)
        if self.report_viewer_text_box is not None:
            # Auto-load the deck report first when possible, then user prompt, then debug files.
            current = Path(self.state.report_viewer_current_file)
            if entries and (self.state.report_viewer_current_file == "No report file selected" or not current.exists()):
                preferred = sorted(entries, key=lambda item: self.report_file_role_rank(item[1]))[0]
                self.load_report_file_into_viewer(preferred[1])
            else:
                self.report_viewer_text_box.setPlainText(self.state.report_viewer_current_text)
                self.apply_report_viewer_readability_settings()
        self.refresh_report_viewer_current_file_controls()

    def reload_latest_reports_into_viewer(self):
        self.refresh_report_viewer_file_list()
        QMessageBox.information(
            self,
            "Report Viewer Reloaded",
            "Detected report files from the latest guarded run have been refreshed. Report contents are still shown as plain text only."
        )

    def refresh_current_report_file(self):
        path = Path(self.state.report_viewer_current_file)
        if not path.exists() or not path.is_file():
            QMessageBox.information(self, "No Report File Selected", "No loaded report file is available to refresh yet.")
            return
        self.load_report_file_into_viewer(str(path))
        QMessageBox.information(self, "Report File Refreshed", f"Reloaded {path.name} from disk.")

    def copy_current_report_text(self):
        text = self.state.report_viewer_current_text or ""
        if not text.strip():
            QMessageBox.information(self, "No Report Text", "No loaded report text is available to copy yet.")
            return
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Report Text Copied", "The currently loaded report text has been copied to the clipboard.")

    def open_current_report_file(self):
        path = Path(self.state.report_viewer_current_file)
        if not path.exists() or not path.is_file():
            QMessageBox.information(self, "No Report File Selected", "No loaded report file is available to open yet.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def open_current_report_folder(self):
        path = Path(self.state.report_viewer_current_file)
        if not path.exists() or not path.is_file():
            QMessageBox.information(self, "No Report File Selected", "No loaded report file is available yet.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.parent)))

    def page_report_viewer(self):
        return build_report_viewer_page(self)

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
        return build_collection_source_page(self)

    def page_batch_reports(self):
        return build_batch_reports_page(self)

    def page_settings(self):
        return build_settings_page(self)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("The Dragon's Touch")
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
