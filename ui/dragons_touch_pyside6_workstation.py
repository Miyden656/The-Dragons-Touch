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
import re

from PySide6.QtCore import Qt, QTimer, QSignalBlocker, QProcess, QProcessEnvironment, QUrl
from PySide6.QtGui import QFont, QDesktopServices, QTextCursor
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QFrame,
    QHBoxLayout, QLabel, QListView, QMainWindow, QMenu, QMessageBox,
    QPlainTextEdit, QPushButton, QScrollArea, QSizePolicy,
    QStackedWidget, QVBoxLayout, QWidget
)

try:
    from ui.constants import (
        APP_VERSION, APP_PHASE, BACKEND_STATUS, LOCKED_BACKEND_VERSION,
        OUTPUT_MODE_OPTIONS, REVIEW_DIRECTION_OPTIONS, REVIEW_INTENSITY_OPTIONS, BUILD_UP_MODE_OPTIONS,
        PROMPT_MODE_OPTIONS, INTENDED_BRACKET_OPTIONS, GUIDE_PRESENTATION_OPTIONS,
        PHILOSOPHY_SUBTYPE_OPTIONS, RUN_DETAIL_OPTIONS, COLLECTION_MODE_OPTIONS, COLLECTION_SOURCE_OPTIONS, COMBO_AWARENESS_OPTIONS, INTERFACE_MODE_OPTIONS, DEFAULT_INTERFACE_MODE,
        DEFAULT_SELECTED_PHILOSOPHY, DEFAULT_PHILOSOPHY_SUBTYPE, DEFAULT_GUIDE_PRESENTATION,
        DEFAULT_OUTPUT_MODE, DEFAULT_REVIEW_DIRECTION, DEFAULT_REVIEW_INTENSITY, DEFAULT_BUILD_UP_MODE,
        DEFAULT_PROMPT_MODE, DEFAULT_INTENDED_BRACKET, DEFAULT_COLLECTION_MODE, DEFAULT_COLLECTION_SOURCE_MODE, DEFAULT_COMBO_AWARENESS_MODE,
        USER_MODE_RUN_ANALYSIS_NOTE, DEV_MODE_RUN_ANALYSIS_NOTE, USER_MODE_REPORT_VIEWER_NOTE, DEV_MODE_REPORT_VIEWER_NOTE,
    )
    from ui.styles.theme import DRAGON_FORGE, ADVENTURERS_MAP, build_main_qss
    from ui.widgets import (
        add_shadow, TexturedPanel, ForgeOrb, Badge, ReportCard, SmallStat, PillButton
    )
    from ui.state import AppState
    from ui.services import report_detector, cli_bridge, backend_runner, user_settings
    from ui.pages.deck_selection_page import build_deck_selection_page
    from ui.pages.review_setup_page import build_review_setup_page
    from ui.pages.philosophy_lens_page import build_philosophy_lens_page
    from ui.pages.commander_discovery_page import build_commander_discovery_page
    from ui.pages.collection_source_page import build_collection_source_page
    from ui.pages.run_analysis_page import build_run_analysis_page
    from ui.pages.report_viewer_page import build_report_viewer_page
    from ui.pages.future_workspace_page import build_batch_reports_page
    from ui.pages.settings_page import build_settings_content
    from ui.pages.commander_ai_panel import build_commander_ai_panel
    from ui.pages.training_review_page import build_training_review_page
    from ui.pages.deck_coach_page import build_deck_coach_page, refresh_deck_coach_deck_label
except ImportError:  # Allows direct execution from inside the ui/ folder during local testing.
    from constants import (
        APP_VERSION, APP_PHASE, BACKEND_STATUS, LOCKED_BACKEND_VERSION,
        OUTPUT_MODE_OPTIONS, REVIEW_DIRECTION_OPTIONS, REVIEW_INTENSITY_OPTIONS, BUILD_UP_MODE_OPTIONS,
        PROMPT_MODE_OPTIONS, INTENDED_BRACKET_OPTIONS, GUIDE_PRESENTATION_OPTIONS,
        PHILOSOPHY_SUBTYPE_OPTIONS, RUN_DETAIL_OPTIONS, COLLECTION_MODE_OPTIONS, COLLECTION_SOURCE_OPTIONS, COMBO_AWARENESS_OPTIONS, INTERFACE_MODE_OPTIONS, DEFAULT_INTERFACE_MODE,
        DEFAULT_SELECTED_PHILOSOPHY, DEFAULT_PHILOSOPHY_SUBTYPE, DEFAULT_GUIDE_PRESENTATION,
        DEFAULT_OUTPUT_MODE, DEFAULT_REVIEW_DIRECTION, DEFAULT_REVIEW_INTENSITY, DEFAULT_BUILD_UP_MODE,
        DEFAULT_PROMPT_MODE, DEFAULT_INTENDED_BRACKET, DEFAULT_COLLECTION_MODE, DEFAULT_COLLECTION_SOURCE_MODE, DEFAULT_COMBO_AWARENESS_MODE,
        USER_MODE_RUN_ANALYSIS_NOTE, DEV_MODE_RUN_ANALYSIS_NOTE, USER_MODE_REPORT_VIEWER_NOTE, DEV_MODE_REPORT_VIEWER_NOTE,
    )
    from styles.theme import DRAGON_FORGE, ADVENTURERS_MAP, build_main_qss
    from widgets import (
        add_shadow, TexturedPanel, ForgeOrb, Badge, ReportCard, SmallStat, PillButton
    )
    from state import AppState
    from services import report_detector, cli_bridge, backend_runner, user_settings
    from pages.deck_selection_page import build_deck_selection_page
    from pages.review_setup_page import build_review_setup_page
    from pages.philosophy_lens_page import build_philosophy_lens_page
    from pages.commander_discovery_page import build_commander_discovery_page
    from pages.collection_source_page import build_collection_source_page
    from pages.run_analysis_page import build_run_analysis_page
    from pages.report_viewer_page import build_report_viewer_page
    from pages.future_workspace_page import build_batch_reports_page
    from pages.settings_page import build_settings_content
    from pages.commander_ai_panel import build_commander_ai_panel
    from pages.training_review_page import build_training_review_page
    from pages.deck_coach_page import build_deck_coach_page, refresh_deck_coach_deck_label


try:
    USER_MODE_RUN_ANALYSIS_NOTE
except NameError:
    USER_MODE_RUN_ANALYSIS_NOTE = "User-Facing Mode keeps Run Analysis focused on the normal player workflow."
    DEV_MODE_RUN_ANALYSIS_NOTE = "Dev-Facing Mode exposes advanced diagnostics for testing."
    USER_MODE_REPORT_VIEWER_NOTE = "User-Facing Mode prioritizes normal reports."
    DEV_MODE_REPORT_VIEWER_NOTE = "Dev-Facing Mode shows normal reports plus breakdown/debug artifacts."

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
# v0.10.4.3.1-dev launcher crash hotfix: refresh_report_viewer_file_list now uses clear_layout_widgets, not missing clear_layout.
# v0.6.7.12 checkpoint: desktop UI foundation is locked; future work should build on this guarded bridge rather than replacing it.
# v0.7.0 alpha hardening boundary: preserve UI staged state -> guarded confirmation -> subprocess/main.py -> CLI input bridge -> backend output folder -> report detection -> plain-text Report Viewer.
# Do not bypass main.py, silently execute backend commands, or create a second backend workflow.



class MainWindow(QMainWindow):
    # COMMANDER_GUIDE removed: the local AI guide is now hosted as a slide-in
    # drawer / embedded panel on Report Viewer + Commander's Call (no standalone page).
    # SETTINGS removed as a stack page — it is now a slide-over overlay drawer
    # (open_settings_drawer) so closing returns to the exact prior page.
    DECK_SELECTION, REVIEW_SETUP, PHILOSOPHY, RUN_ANALYSIS, REPORT, COMMANDER_DISCOVERY, COLLECTION, BATCH_REPORTS, TRAINING_REVIEW, DECK_COACH = range(10)

    # v0.6.7.1 shell aliases kept for low-risk page wiring during the first UI patch.
    DECK_INPUT = DECK_SELECTION
    ANALYSIS_SETUP = REVIEW_SETUP
    RUN_REVIEW = RUN_ANALYSIS
    COMBO = BATCH_REPORTS

    def __init__(self):
        super().__init__()
        self.state = AppState(theme=DRAGON_FORGE)
        self.app_settings = user_settings.load_app_settings()
        user_settings.apply_settings_to_state(self.state, self.app_settings, DRAGON_FORGE, ADVENTURERS_MAP)
        self.nav_buttons = []
        # Header navigation (replaces the old Forge sidebar). The "+" New menu and
        # cog Settings button live in build_header; the stepper strip and per-page
        # Continue/Back footers thread the linear workflow now that the sidebar is gone.
        self.new_menu_button = None
        self.new_menu = None
        self.dev_mode_badge = None
        self.settings_nav_button = None
        self.stepper_panel = None
        self.stepper_labels = {}
        # Overlay drawers (free children of root; lazily populated).
        self.ai_drawer = None
        self._ai_drawer_body = None
        self._ai_drawer_panel = None
        self.settings_drawer = None
        self._settings_drawer_body = None
        self._settings_drawer_content = None
        # Gated "Continue to Report Viewer" button on the Run Analysis footer.
        self.run_to_report_btn = None
        # Which entry the user started from ("analysis" = paste/select a decklist,
        # "commander" = The Commander's Call). Drives Back targets and "Start New".
        self.entry_mode = "analysis"
        self.progress_bars = []
        self.progress_tick = 0
        self.context_value_labels = {}
        self.context_run_settings_label = None
        self.warnings_detail_label = None
        self.view_warnings_button = None
        self.run_user_summary_label = None
        self.theme_button = None
        self.settings_theme_buttons = []
        self.interface_mode_combo = None
        self.settings_collection_folder_label = None
        self.settings_report_folder_label = None
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
        self.run_readiness_box = None
        self.run_latest_output_card = None
        self.run_analysis_mode_note_label = None
        self.run_analysis_summary_mode_note_label = None
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
        self.report_viewer_open_detected_file = None
        self.report_viewer_show_user_prompt = None
        self.report_viewer_show_deck_report = None
        self.report_viewer_show_user_section = None
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
        # Tightened to reclaim the vertical space the stepper + flow footer now
        # consume, so page bodies scroll less and feel less cramped.
        self.root_layout.setContentsMargins(16, 12, 16, 12)
        self.root_layout.setSpacing(10)
        self.stack = QStackedWidget()
        self.build_shell()
        self.apply_theme()
        self.go_to(self.DECK_SELECTION)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress_mock)
        self.timer.start(600)

    def theme(self):
        return self.state.theme

    def interface_mode_display_text(self):
        return user_settings.normalize_interface_mode(getattr(self.state, "interface_mode", "User Mode"))

    def is_dev_facing_mode(self):
        return self.interface_mode_display_text() == "Developer Mode"

    def is_user_facing_mode(self):
        return not self.is_dev_facing_mode()

    def interface_mode_run_analysis_note(self):
        return DEV_MODE_RUN_ANALYSIS_NOTE if self.is_dev_facing_mode() else USER_MODE_RUN_ANALYSIS_NOTE

    def interface_mode_report_viewer_note(self):
        return DEV_MODE_REPORT_VIEWER_NOTE if self.is_dev_facing_mode() else USER_MODE_REPORT_VIEWER_NOTE

    def is_dev_mode(self):
        """Return True when the UI is in development/testing visibility mode."""
        return self.is_dev_facing_mode()

    def persist_user_settings(self):
        """Persist app-wide settings only. Review Setup remains current-run state."""
        self.app_settings["interface_mode"] = self.interface_mode_display_text()
        self.app_settings["guide_presentation"] = user_settings.normalize_guide_presentation(self.state.guide_presentation)
        self.app_settings["collection_source_default"] = self.collection_source_default_display_text()
        self.app_settings["collection_source_path"] = self.state.collection_folder
        self.app_settings["collection_source_files"] = list(self.state.selected_collection_files)
        self.app_settings["report_output_folder"] = getattr(self.state, "report_output_folder", "Outputs")
        self.app_settings["theme"] = self.theme()["name"]
        self.app_settings["ui_density"] = getattr(self.state, "ui_density", "Normal")
        self.app_settings["developer_report_viewer_last_view"] = getattr(self.state, "developer_report_viewer_last_view", "User View")
        user_settings.save_app_settings(self.app_settings)

    def user_settings_path_text(self):
        return str(user_settings.settings_path())

    def collection_source_default_display_text(self):
        if getattr(self.state, "collection_source_mode", "Entire collection folder") == "Select collection files":
            return "Specific local collection files"
        return user_settings.normalize_collection_source_default(self.app_settings.get("collection_source_default", "Local collection folder"))

    # v0.10.5.1.1 flash hotfix: mode changes persist immediately but do not rebuild
    # the active Settings page during the combo-box change event.
    def stage_interface_mode(self, mode):
        """Stage and persist the User / Developer UI mode without changing backend behavior."""
        normalized = user_settings.normalize_interface_mode(mode)
        self.state.interface_mode = normalized
        self.state.status = f"Interface mode staged: {normalized}"
        self.persist_user_settings()
        if getattr(self, "interface_mode_combo", None) is not None and self.interface_mode_combo.currentText() != normalized:
            blocker = QSignalBlocker(self.interface_mode_combo)
            self.interface_mode_combo.setCurrentText(normalized)
            del blocker
        if getattr(self, "run_advanced_details_toggle", None) is not None:
            self.run_advanced_details_toggle.setChecked(self.is_dev_mode())
        # Live-toggle the header "Developer Mode Enabled" badge.
        if getattr(self, "dev_mode_badge", None) is not None:
            self.dev_mode_badge.setVisible(self.is_dev_mode())
        self.refresh_context_panel_values()
        self.refresh_run_analysis_previews()
        self.refresh_report_viewer_mode_controls()
        self.refresh_report_viewer_file_list()
        # Show/hide the dev-only Training Review entry live on mode change
        # (no full page rebuild needed — just toggle the header menu action).
        act = getattr(self, "_training_review_menu_action", None)
        if act is not None:
            act.setVisible(self.is_dev_mode())
            sep = getattr(self, "_training_review_separator", None)
            if sep is not None:
                sep.setVisible(self.is_dev_mode())
            if not self.is_dev_mode() and self.stack.currentIndex() == self.TRAINING_REVIEW:
                self.go_to(self.DECK_SELECTION)  # don't strand the user on a now-hidden page
        # Settings drawer content bakes its dev/user gates at build time, so a mode
        # change after it was first opened would leave stale dev content showing.
        # Drop the cached content so it rebuilds with the new mode (reopen if visible).
        if getattr(self, "_settings_drawer_content", None) is not None:
            was_visible = self.settings_drawer is not None and self.settings_drawer.isVisible()
            self._settings_drawer_content.setParent(None)
            self._settings_drawer_content.deleteLater()
            self._settings_drawer_content = None
            if was_visible:
                self.open_settings_drawer()
        # v0.10.5.1.1: Do not rebuild the current page during combo-box mode changes.
        # Rebuilding while the Settings combo popup is closing creates a visible flash.
        # The new mode is persisted immediately; page-specific visibility will update
        # when the user navigates or reopens the page.

    def stage_ui_density(self, value):
        self.state.ui_density = user_settings.normalize_ui_density(value)
        self.state.status = f"UI density saved: {self.state.ui_density}"
        self.persist_user_settings()
        self.refresh_context_panel_values()

    def stage_collection_source_default(self, value):
        normalized = user_settings.normalize_collection_source_default(value)
        self.app_settings["collection_source_default"] = normalized
        if normalized == "Specific local collection files":
            self.state.collection_source_mode = "Select collection files"
        elif normalized == "Local collection folder":
            self.state.collection_source_mode = "Entire collection folder"
        self.state.status = f"Collection source default saved: {normalized}"
        self.persist_user_settings()
        self.refresh_collection_page_widgets()
        self.refresh_context_panel_values()

    def choose_report_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose Report / Output Folder", getattr(self.state, "report_output_folder", "Outputs") or "")
        if not folder:
            return
        self.state.report_output_folder = folder
        self.state.status = "Report folder saved"
        self.persist_user_settings()
        if getattr(self, "settings_report_folder_label", None) is not None:
            self.settings_report_folder_label.setText(folder)
        self.refresh_context_panel_values()
        self.refresh_report_viewer_file_list()

    def reset_user_settings_to_defaults(self):
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Reset app-wide settings to defaults? This will not edit decks or reports.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self.app_settings = user_settings.reset_app_settings()
        user_settings.apply_settings_to_state(self.state, self.app_settings, DRAGON_FORGE, ADVENTURERS_MAP)
        self.state.status = "Settings reset to defaults"
        # Rebuild the shell to apply defaults, then re-open the Settings drawer so
        # the user stays in Settings (it's an overlay now, not a stack page).
        self.rebuild_shell()
        self.open_settings_drawer()

    def interface_mode_summary_text(self):
        """Small user-readable summary of current interface mode behavior."""
        if self.is_dev_mode():
            return (
                "Interface mode: Developer Mode\n"
                "- Developer Mode Enabled.\n"
                "- Advanced run details default open.\n"
                "- Breakdown/debug report files remain visible in Report Viewer.\n"
                "- Runtime contract, bridge preview, diagnostics, and combo breakdown visibility are preserved for QA.\n"
                "- Backend behavior, combo awareness, and report writing are unchanged."
            )
        return (
            "Interface mode: User Mode\n"
            "- Clean single-deck workflow is the default.\n"
            "- Advanced run details default closed.\n"
            "- Developer-only report files and diagnostics are hidden.\n"
            "- Backend behavior, combo awareness, and report writing are unchanged."
        )

    def build_shell(self):
        self.build_header()
        # Slim step indicator replaces the old sidebar's sense of "where am I".
        self.root_layout.addWidget(self.build_stepper())
        app_body = QWidget()
        body_layout = QHBoxLayout(app_body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(12)
        self.build_pages()
        body_layout.addWidget(self.stack, stretch=1)
        body_layout.addWidget(self.build_context_panel())
        self.root_layout.addWidget(app_body, stretch=1)
        self.build_footer()
        # Overlay drawers float over the body (free children of root, not in a
        # layout), hidden until summoned. Closing them returns to the same page.
        self.build_ai_drawer()
        self.build_settings_drawer()

    def rebuild_shell(self, page_index=None):
        page_index = self.stack.currentIndex() if page_index is None and self.stack else page_index
        while self.root_layout.count():
            item = self.root_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        # The overlay drawers are free children of self.root (not in root_layout),
        # so the teardown loop above does not catch them — delete explicitly.
        for _attr in ("ai_drawer", "settings_drawer"):
            _d = getattr(self, _attr, None)
            if _d is not None:
                _d.setParent(None)
                _d.deleteLater()
        self.ai_drawer = None
        self._ai_drawer_body = None
        self._ai_drawer_panel = None
        self.settings_drawer = None
        self._settings_drawer_body = None
        self._settings_drawer_content = None
        self.nav_buttons = []
        # Header nav + stepper handles are recreated by build_shell below; clear
        # them so a teardown never leaves references to deleted widgets.
        self.new_menu_button = None
        self.new_menu = None
        self.dev_mode_badge = None
        self.settings_nav_button = None
        self.stepper_panel = None
        self.stepper_labels = {}
        self.run_to_report_btn = None
        self.progress_bars = []
        self.settings_theme_buttons = []
        self.interface_mode_combo = None
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
        # Always create the dev badge; toggle visibility live on mode change so it
        # never lingers as "Developer Mode Enabled" after switching to User Mode.
        dev_badge = QLabel("Developer Mode Enabled")
        dev_badge.setObjectName("warningText")
        dev_badge.setVisible(self.is_dev_mode())
        self.dev_mode_badge = dev_badge
        layout.addWidget(dev_badge)
        # "+" New — opens a small themed menu to start a flow. Replaces the old
        # Forge sidebar's Deck Selection / Commander's Call entry points.
        new_btn = QPushButton("＋  New")
        new_btn.setObjectName("utilityButton")
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.setToolTip("Start a new deck review or Commander's Call")
        menu = QMenu(new_btn)
        act_analysis = menu.addAction("🃏  Analysis (deck review)")
        act_analysis.triggered.connect(lambda checked=False: self.start_new_flow("analysis"))
        act_call = menu.addAction("📣  The Commander's Call")
        act_call.triggered.connect(lambda checked=False: self.start_new_flow("commander"))
        # Jump back to the current report from anywhere (enabled once a report
        # exists), so leaving the flow no longer forces a re-run.
        menu.addSeparator()
        act_view_report = menu.addAction("📜  View current report")
        act_view_report.triggered.connect(lambda checked=False: self.go_to(self.REPORT))
        self._view_report_menu_action = act_view_report
        # Deck Coach Workbench — a readable, persona-voiced view of the engine's
        # reasoning + a card-picking steering wheel. Real user feature (both modes).
        act_coach = menu.addAction("🧭  Deck Coach Workbench")
        act_coach.triggered.connect(lambda checked=False: self.go_to(self.DECK_COACH))
        self._deck_coach_menu_action = act_coach
        # Dev-only Training Review (re-homes the old sidebar entry). The action
        # always exists so Settings' interface-mode toggle can show/hide it live.
        self._training_review_separator = menu.addSeparator()
        act_training = menu.addAction("🛠  Training Review (dev)")
        act_training.triggered.connect(lambda checked=False: self.go_to(self.TRAINING_REVIEW))
        self._training_review_menu_action = act_training
        act_training.setVisible(self.is_dev_mode())
        self._training_review_separator.setVisible(self.is_dev_mode())
        # The menu is a top-level popup and does NOT inherit self.root's stylesheet,
        # so re-theme it every time it opens (mirrors configure_combo_popup). Also
        # refresh the "View current report" enabled state on open.
        def _on_menu_show():
            menu.setStyleSheet(self.menu_qss())
            act_view_report.setEnabled(self.report_is_available())
        menu.aboutToShow.connect(_on_menu_show)
        new_btn.setMenu(menu)
        self.new_menu_button = new_btn
        self.new_menu = menu
        layout.addWidget(new_btn)
        theme_btn = QPushButton(f"Theme: {self.theme()['name']}")
        self.theme_button = theme_btn
        theme_btn.setObjectName("utilityButton")
        theme_btn.clicked.connect(self.toggle_theme)
        layout.addWidget(theme_btn)
        # Cog — Settings. Consolidated into the header per tester feedback.
        settings_btn = QPushButton("⚙")
        settings_btn.setObjectName("utilityButton")
        settings_btn.setCursor(Qt.PointingHandCursor)
        settings_btn.setToolTip("Settings")
        settings_btn.clicked.connect(lambda checked=False: self.toggle_settings_drawer())
        self.settings_nav_button = settings_btn
        layout.addWidget(settings_btn)
        mascot = QLabel("☕🐲")
        mascot.setObjectName("mascotHeader")
        layout.addWidget(mascot)
        self.root_layout.addWidget(header)

    def menu_qss(self):
        """Themed stylesheet for header QMenu popups.

        A QMenu opens as its own top-level window, so it does not inherit the
        stylesheet applied to self.root. Build one from the active palette using
        the same combo-popup color keys the combo dropdowns use, so the menu
        matches in both Dragon Forge and Adventurer's Map.
        """
        t = self.theme()
        bg = t.get("combo_popup_bg", t["iron_2"])
        text = t.get("combo_popup_text", t.get("input_text", t["text"]))
        border = t.get("combo_popup_border", t["border"])
        item_bg = t.get("combo_popup_item_bg", bg)
        sel_bg = t.get("combo_popup_selected_bg", t["accent"])
        sel_text = t.get("combo_popup_selected_text", t.get("button_pressed_text", t["bg"]))
        sep = t.get("accent_2", border)
        return f'''
        QMenu {{ background-color: {bg}; color: {text}; border: 1px solid {border}; padding: 4px; }}
        QMenu::item {{ background-color: {item_bg}; color: {text}; padding: 7px 18px; min-height: 24px; border-radius: 6px; }}
        QMenu::item:selected {{ background-color: {sel_bg}; color: {sel_text}; }}
        QMenu::separator {{ height: 1px; background: {sep}; margin: 4px 8px; }}
        '''

    def start_new_flow(self, mode):
        """Begin a workflow from the header "+" menu.

        mode == "analysis"  -> land on Deck Selection (paste/select a decklist).
        mode == "commander" -> land on The Commander's Call.
        The chosen mode drives Back targets and the Report Viewer "Start New" button.
        """
        self.entry_mode = "commander" if mode == "commander" else "analysis"
        # New flow: re-gate the Continue-to-Report button so the prior run's
        # report no longer counts as "available" until this flow runs.
        self.state.last_report_detection_mode = "not_attempted"
        self.go_to(self.COMMANDER_DISCOVERY if self.entry_mode == "commander" else self.DECK_SELECTION)

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

    # Ordered linear workflow. The old Forge sidebar exposed these as buttons;
    # now the header "+" menu enters the flow and per-page Continue/Back footers
    # plus this stepper move between them. Order is unchanged from the sidebar.
    def build_stepper(self):
        """Slim step indicator above the workflow content.

        Replaces the removed sidebar's sense of "where am I". Hidden on
        non-flow pages (Settings, Commander's Call entry, Commander Guide,
        Training Review) by refresh_stepper.
        """
        panel = TexturedPanel(self.theme, kind="iron", glow=False, corners=True)
        row = QHBoxLayout(panel)
        row.setContentsMargins(18, 6, 18, 6)
        row.setSpacing(6)
        self.stepper_labels = {}
        self._stepper_seps = []
        steps = [
            (self.DECK_SELECTION, "Deck"),
            (self.REVIEW_SETUP, "Review Setup"),
            (self.PHILOSOPHY, "Philosophy"),
            (self.RUN_ANALYSIS, "Run Analysis"),
            (self.REPORT, "Report"),
        ]
        row.addStretch(1)
        for i, (index, label) in enumerate(steps):
            # Clickable flat step (tester: reach any step — esp. Report — directly).
            btn = QPushButton(label)
            btn.setObjectName("stepperStep")
            btn.setFlat(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, idx=index: self._stepper_go(idx))
            self.stepper_labels[index] = btn
            row.addWidget(btn)
            if i < len(steps) - 1:
                sep = QLabel("›")
                sep.setObjectName("stepperSep")
                self._stepper_seps.append(sep)
                row.addWidget(sep)
        row.addStretch(1)
        self.stepper_panel = panel
        return panel

    def _stepper_go(self, index):
        """Navigate from a clicked stepper step (Report gated on a report existing)."""
        if index == self.REPORT and not self.report_is_available():
            return
        if index == self.DECK_SELECTION and self.entry_mode == "commander":
            self.go_to(self.COMMANDER_DISCOVERY)
            return
        self.go_to(index)

    def stepper_flow_pages(self):
        return (self.DECK_SELECTION, self.REVIEW_SETUP, self.PHILOSOPHY, self.RUN_ANALYSIS, self.REPORT)

    def refresh_stepper(self, index):
        """Show the stepper on flow pages only and highlight the current step."""
        if self.stepper_panel is None:
            return
        show = index in self.stepper_flow_pages()
        self.stepper_panel.setVisible(show)
        if not show:
            return
        t = self.theme()
        active_color = t.get("accent_2", t["accent"])
        muted_color = t.get("muted", t["text"])
        # The first step is the deck OR the commander, depending on how the
        # user entered the flow.
        first = self.stepper_labels.get(self.DECK_SELECTION)
        if first is not None:
            first.setText("Commander" if self.entry_mode == "commander" else "Deck")
        disabled_color = t.get("muted_2", muted_color)
        for idx, lbl in self.stepper_labels.items():
            is_active = (idx == index)
            # The Report step is only reachable once a report exists.
            reachable = (idx != self.REPORT) or self.report_is_available()
            lbl.setEnabled(reachable)
            lbl.setCursor(Qt.PointingHandCursor if reachable else Qt.ArrowCursor)
            weight = "900" if is_active else "700"
            color = active_color if is_active else (muted_color if reachable else disabled_color)
            lbl.setStyleSheet(
                "QPushButton { background: transparent; border: none; text-align: center; "
                f"color: {color}; font-size: 12px; font-weight: {weight}; letter-spacing: 0.5px; padding: 4px 6px; }}"
                f"QPushButton:hover {{ color: {active_color}; }}"
            )
        for sep in getattr(self, "_stepper_seps", []):
            sep.setStyleSheet(f"color: {muted_color}; font-size: 12px;")

    # ---- Commander AI guide hosting (slide-in drawer / embedded panel) -----
    # The local Ollama guide no longer has its own page. It is hosted as a
    # slide-in drawer (default) or an embedded collapsible panel on Report
    # Viewer + Commander's Call. The user picks which in Settings.

    def commander_ai_display_mode(self):
        return user_settings.normalize_commander_ai_display_mode(
            self.app_settings.get("commander_ai_display_mode")
        )

    def _make_overlay_drawer(self, title, on_close):
        """Build a hidden right-side overlay drawer (free child of root).

        Shared by the Commander AI guide and the Settings slide-over so both
        behave identically: open over the current page, close returns you to
        the exact page you were on. Returns (drawer, body_layout).
        """
        drawer = TexturedPanel(self.theme, kind="outer", glow=True, corners=True)
        drawer.setParent(self.root)
        add_shadow(drawer, blur=34, y=0)
        v = QVBoxLayout(drawer)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(10)
        header = QHBoxLayout()
        ttl = QLabel(title)
        ttl.setObjectName("sectionTitle")
        close_btn = QPushButton("✕  Close")
        close_btn.setObjectName("utilityButton")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(on_close)
        header.addWidget(ttl, stretch=1)
        header.addWidget(close_btn)
        v.addLayout(header)
        body = QVBoxLayout()
        v.addLayout(body, stretch=1)
        drawer.hide()
        return drawer, body

    def _position_drawer(self, drawer, frac, min_w, max_w):
        if drawer is None:
            return
        w = self.root.width()
        h = self.root.height()
        dw = min(max_w, max(min_w, int(w * frac)))
        drawer.setGeometry(w - dw, 0, dw, h)

    # --- Commander AI drawer ---
    def build_ai_drawer(self):
        drawer, body = self._make_overlay_drawer("Ask the Commander Guide", self.close_ai_drawer)
        self.ai_drawer = drawer
        self._ai_drawer_body = body
        self._ai_drawer_panel = None
        return drawer

    def _position_ai_drawer(self):
        # ~1/3 of the window, clamped 360–460px (tester: old drawer too big).
        self._position_drawer(getattr(self, "ai_drawer", None), 0.33, 360, 460)

    def open_ai_drawer(self):
        if getattr(self, "ai_drawer", None) is None:
            return
        if self._ai_drawer_panel is None:
            self._ai_drawer_panel = build_commander_ai_panel(self, compact=True)
            self._ai_drawer_body.addWidget(self._ai_drawer_panel, stretch=1)
        self._position_ai_drawer()
        self.ai_drawer.show()
        self.ai_drawer.raise_()

    def close_ai_drawer(self):
        if getattr(self, "ai_drawer", None) is not None:
            self.ai_drawer.hide()

    def toggle_ai_drawer(self):
        if getattr(self, "ai_drawer", None) is None:
            return
        self.close_ai_drawer() if self.ai_drawer.isVisible() else self.open_ai_drawer()

    # --- Settings drawer (slide-over; replaces the old Settings stack page) ---
    def build_settings_drawer(self):
        drawer, body = self._make_overlay_drawer("Settings", self.close_settings_drawer)
        self.settings_drawer = drawer
        self._settings_drawer_body = body
        self._settings_drawer_content = None
        return drawer

    def _position_settings_drawer(self):
        # Settings is dense — wider than the AI drawer (~half, clamped 480–760px).
        self._position_drawer(getattr(self, "settings_drawer", None), 0.5, 480, 760)

    def open_settings_drawer(self):
        if getattr(self, "settings_drawer", None) is None:
            return
        if self._settings_drawer_content is None:
            self._settings_drawer_content = build_settings_content(self)
            self._settings_drawer_body.addWidget(self._settings_drawer_content, stretch=1)
        self.close_ai_drawer()  # never stack the two overlays
        self._position_settings_drawer()
        self.settings_drawer.show()
        self.settings_drawer.raise_()

    def close_settings_drawer(self):
        if getattr(self, "settings_drawer", None) is not None:
            self.settings_drawer.hide()

    def toggle_settings_drawer(self):
        if getattr(self, "settings_drawer", None) is None:
            return
        self.close_settings_drawer() if self.settings_drawer.isVisible() else self.open_settings_drawer()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if getattr(self, "ai_drawer", None) is not None and self.ai_drawer.isVisible():
            self._position_ai_drawer()
        if getattr(self, "settings_drawer", None) is not None and self.settings_drawer.isVisible():
            self._position_settings_drawer()

    def add_commander_ai_trigger(self, layout, context_label=""):
        """Add an 'Ask the Commander Guide' control to a host page layout.

        Behavior follows the Settings preference, read at click time:
        - Slide-in panel: opens the shared drawer over the page.
        - Embedded panel: toggles an inline collapsible panel hosted right here.
        Returns the trigger button.
        """
        row = QHBoxLayout()
        btn = QPushButton("🐉  Ask the Commander Guide")
        btn.setObjectName("utilityButton")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setToolTip(
            "Ask the optional local AI guide about your deck. "
            "Enable it in Settings → Local Commander AI."
        )
        row.addWidget(btn)
        row.addStretch(1)
        layout.addLayout(row)

        # Embedded host: a scroll area so the panel is never cramped/clipped
        # (tester: embedded panel "so small I can't see anything", couldn't scroll).
        container = QScrollArea()
        container.setWidgetResizable(True)
        container.setFrameShape(QFrame.NoFrame)
        container.setMinimumHeight(420)
        container.setMinimumWidth(520)  # keep the persona/mode dropdowns from compressing
        container.setVisible(False)
        layout.addWidget(container)
        holder = {"panel": None}

        def _on_click():
            if self.commander_ai_display_mode() == "Embedded panel":
                # Clean transition: make sure the slide-in drawer isn't left open
                # from a previous mode (tester: toggle "didn't change back").
                self.close_ai_drawer()
                if holder["panel"] is None:
                    holder["panel"] = build_commander_ai_panel(self, compact=True)
                    container.setWidget(holder["panel"])
                container.setVisible(not container.isVisible())
            else:
                # Slide-in mode: keep any inline panel collapsed, use the drawer.
                container.setVisible(False)
                self.toggle_ai_drawer()

        btn.clicked.connect(lambda checked=False: _on_click())
        return btn

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
        # Clickable warnings detail (tester: wanted to see what the warnings are).
        view_warnings_btn = QPushButton("View warnings")
        view_warnings_btn.setObjectName("utilityButton")
        view_warnings_btn.setCursor(Qt.PointingHandCursor)
        view_warnings_btn.clicked.connect(self.toggle_warnings_detail)
        self.view_warnings_button = view_warnings_btn
        layout.addWidget(view_warnings_btn)
        warn_detail = QLabel(""); warn_detail.setObjectName("mutedText"); warn_detail.setWordWrap(True); warn_detail.setVisible(False)
        self.warnings_detail_label = warn_detail
        layout.addWidget(warn_detail)
        line = QFrame(); line.setObjectName("goldDivider"); line.setFixedHeight(1); layout.addWidget(line)
        # Run Setting Summary folded into the deck context (replaces the obsolete
        # "Quick Notes" block per tester feedback).
        run_title = QLabel("RUN SETTINGS"); run_title.setObjectName("sidebarSectionTitle"); layout.addWidget(run_title)
        run_summary = QLabel(self.context_run_settings_text())
        run_summary.setObjectName("mutedText"); run_summary.setWordWrap(True)
        self.context_run_settings_label = run_summary
        layout.addWidget(run_summary)
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
        self.stack.addWidget(self.page_commander_discovery())
        self.stack.addWidget(self.page_collection_tools())
        self.stack.addWidget(self.page_batch_reports())
        # Settings is no longer a stack page — it's the slide-over drawer.
        self.stack.addWidget(self.page_training_review())   # index 8 = TRAINING_REVIEW (dev-only nav; page always in stack so indices stay stable)
        self.stack.addWidget(self.page_deck_coach())        # index 9 = DECK_COACH (visible in both modes)

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
        self.persist_user_settings()
        self.refresh_theme_in_place()

    def set_theme(self, theme):
        self.state.theme = theme
        self.persist_user_settings()
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
        # Stepper labels use inline (theme-derived) colors, so re-tint them on toggle.
        if self.stack is not None:
            self.refresh_stepper(self.stack.currentIndex())
        self.refresh_context_panel_values()
        self.root.update()

    def qss(self, t):
        return build_main_qss(t)

    def refresh_commander_discovery_page(self):
        """Rebuild The Commander's Call page so User/Developer Mode visibility is current.

        v1.2.8.5:
        Commander Discovery has separate User Mode and Developer Mode layouts.
        The page is built once during shell startup, so mode changes from Settings
        need a safe page refresh before showing The Commander's Call again.
        """
        if not getattr(self, "stack", None):
            return
        if self.stack.count() <= self.COMMANDER_DISCOVERY:
            return
        old_page = self.stack.widget(self.COMMANDER_DISCOVERY)
        new_page = self.page_commander_discovery()
        self.stack.removeWidget(old_page)
        old_page.deleteLater()
        self.stack.insertWidget(self.COMMANDER_DISCOVERY, new_page)

    def go_to(self, index):
        # v0.10.5.2 removed-page navigation guard:
        # Collection Source and Batch Tools are no longer visible navigation pages.
        if index == self.COLLECTION:
            # Collection Source lives in the Settings drawer now; open it and
            # keep the user on their current page underneath.
            self.state.status = "Collection Source moved to Settings / Review Setup"
            self.open_settings_drawer()
            return
        elif index == self.BATCH_REPORTS:
            self.state.status = "Batch Tools removed from UI navigation"
            index = self.REPORT

        if index == self.COMMANDER_DISCOVERY:
            self.refresh_commander_discovery_page()

        self.stack.setCurrentIndex(index)
        for btn in self.nav_buttons:
            btn.setChecked(btn.index == index)
        self.refresh_stepper(index)
        if index == self.RUN_ANALYSIS:
            self.refresh_run_analysis_previews()
            # Re-evaluate the gated Continue-to-Report button on every visit.
            if getattr(self, "run_to_report_btn", None) is not None:
                self.run_to_report_btn.setEnabled(self.report_is_available())
        if index == self.REPORT:
            self.refresh_report_viewer_mode_controls()
            self.refresh_report_viewer_file_list()
        if index == self.DECK_COACH:
            refresh_deck_coach_deck_label(self)

    def is_guarded_run_active(self):
        """Return True only while a guarded backend process is actively running."""
        return bool(self.state.guarded_run_in_progress and self.backend_process is not None)


    def refresh_run_analysis_mode_controls(self):
        """Refresh Run Analysis User Mode / Developer Mode visibility.

        v0.10.5.5:
        User Mode shows only the player-facing run controls, current run summary,
        and Ready to Run checklist. Developer Mode reveals captured output and
        diagnostic detail panels. This does not rebuild the page and does not
        affect the Running Analysis animation.
        """
        is_dev = self.is_dev_mode()

        if getattr(self, "run_latest_output_card", None) is not None:
            self.run_latest_output_card.setVisible(is_dev)

        # Dev-only Run Analysis clutter (tester feedback): User Mode shows only
        # the Run button + guarded confirmation note. These panels remain in
        # Developer Mode for diagnostics.
        for attr in (
            "run_readiness_card", "run_summary_card",
            "run_data_readiness_card", "run_data_warning_card",
        ):
            card = getattr(self, attr, None)
            if card is not None:
                card.setVisible(is_dev)

        if getattr(self, "run_advanced_details_toggle", None) is not None:
            self.run_advanced_details_toggle.setVisible(is_dev)
            if is_dev:
                self.run_advanced_details_toggle.setChecked(True)
                self.run_advanced_details_toggle.setText("Hide Advanced Run Details")
            else:
                self.run_advanced_details_toggle.setChecked(False)
                self.run_advanced_details_toggle.setText("Show Advanced Run Details")

        if getattr(self, "run_advanced_details_container", None) is not None:
            self.run_advanced_details_container.setVisible(is_dev)

        if getattr(self, "run_analysis_mode_note_label", None) is not None:
            self.run_analysis_mode_note_label.setText(
                self.interface_mode_run_analysis_note()
                + " Combo analysis is always included when combo data is available."
            )

        if getattr(self, "run_analysis_summary_mode_note_label", None) is not None:
            self.run_analysis_summary_mode_note_label.setText(self.interface_mode_summary_text())

    def refresh_run_analysis_previews(self):
        """Refresh Run Analysis preview text from current staged UI state without rebuilding pages."""
        self.refresh_run_analysis_mode_controls()
        if getattr(self, "run_user_summary_label", None) is not None:
            self.run_user_summary_label.setText(self.run_compact_summary_text())
        if getattr(self, "run_readiness_box", None) is not None:
            self.run_readiness_box.setPlainText(self.run_readiness_text())
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
        if getattr(self, "context_run_settings_label", None) is not None:
            self.context_run_settings_label.setText(self.context_run_settings_text())
        warn_label = getattr(self, "warnings_detail_label", None)
        if warn_label is not None and warn_label.isVisible():
            warn_label.setText(self.warnings_detail_text())

    def warnings_detail_text(self):
        details = getattr(self.state, "warning_details", []) or []
        if not details:
            return "No warnings for the current deck preview."
        return "\n".join(f"• {d}" for d in details)

    def toggle_warnings_detail(self):
        """Show/hide the warning details under the context panel."""
        label = getattr(self, "warnings_detail_label", None)
        button = getattr(self, "view_warnings_button", None)
        if label is None:
            return
        now_visible = not label.isVisible()
        label.setText(self.warnings_detail_text())
        label.setVisible(now_visible)
        if button is not None:
            button.setText("Hide warnings" if now_visible else "View warnings")

    def run_compact_summary_text(self):
        """Short 'what will run' summary for the Run Analysis page (User Mode)."""
        s = self.state
        return (
            f"Deck: {s.deck_name}\n"
            f"Commander: {s.commander}\n"
            f"Lens: {s.selected_philosophy} · Intended bracket: {s.intended_bracket}"
        )

    def context_run_settings_text(self):
        """Compact run-setting summary folded into the deck context panel."""
        s = self.state
        return (
            f"Lens: {s.selected_philosophy}\n"
            f"Subtype: {s.philosophy_subtype}\n"
            f"Intended bracket: {s.intended_bracket}\n"
            f"Review: {s.review_direction} · {s.cut_depth}\n"
            f"Output: {s.output_mode}"
        )

    def rebuild_then_message(self, page_index, title, message):
        """Rebuild the shell, then post `title: message` to state.status.

        Category B (popup removal): the deferred QMessageBox.information was
        the previous feedback path. Now we just update the status panel so
        the feedback is inline.
        """
        self.rebuild_shell(page_index)
        try:
            self.state.status = f"{title}: {message}" if message else title
            self.refresh_context_panel_values()
        except Exception:
            pass

    def placeholder_message(self):
        # Category E (popup removal): silent no-op. Active alpha workflow is
        # Deck Selection → Review Setup → Philosophy Lens → Run Analysis → Report Viewer.
        # Placeholder Quick Actions are hidden in user mode; this is defensive.
        pass

    def backend_hook_message(self, hook_name):
        # Category E (popup removal): silent no-op. Reserved hook stub.
        pass

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

    # ---- Linear-workflow in-page navigation -------------------------------
    # The old Forge sidebar was the only way to move between flow pages. With it
    # gone, each flow page gets a pinned Continue/Back footer. Targets are keyed
    # by page-index constant (not "next index") so the stack order never changes.

    def flow_back_target(self, index):
        """Return the page a Back button should go to, or None for no Back."""
        if index == self.REVIEW_SETUP:
            # Review Setup is the join point: in Commander's Call mode Back returns
            # to the discovery page; otherwise to Deck Selection.
            return self.COMMANDER_DISCOVERY if self.entry_mode == "commander" else self.DECK_SELECTION
        if index == self.PHILOSOPHY:
            return self.REVIEW_SETUP
        if index == self.RUN_ANALYSIS:
            return self.PHILOSOPHY
        if index == self.REPORT:
            return self.RUN_ANALYSIS
        return None

    def flow_continue_target(self, index):
        """Return (target_index, label) for a Continue button, or None."""
        if index == self.DECK_SELECTION:
            return (self.REVIEW_SETUP, "Continue to Review Setup  →")
        if index == self.COMMANDER_DISCOVERY:
            return (self.REVIEW_SETUP, "Continue to Review Setup  →")
        if index == self.REVIEW_SETUP:
            return (self.PHILOSOPHY, "Continue to Philosophy Lens  →")
        if index == self.PHILOSOPHY:
            # Tester: this should RUN the analysis directly (handled specially in
            # build_flow_footer), not just navigate. Label reflects that.
            return (self.RUN_ANALYSIS, "Run Analysis  →")
        if index == self.RUN_ANALYSIS:
            # Forward to the report. The button is gated (disabled until a run
            # has produced a report) in build_flow_footer / refresh, so Report
            # stays unreachable before the first run but is freely revisitable
            # afterward — both tester wishes honored.
            return (self.REPORT, "Continue to Report Viewer  →")
        return None

    def report_is_available(self):
        """True once a guarded run has attempted report detection."""
        return getattr(self.state, "last_report_detection_mode", "not_attempted") != "not_attempted"

    def _run_from_philosophy(self):
        """Philosophy's primary button: go to Run Analysis (for the animation),
        then start the guarded backend run in the same gesture (tester request)."""
        self.go_to(self.RUN_ANALYSIS)
        if hasattr(self, "start_guarded_backend_run"):
            self.start_guarded_backend_run()

    def build_flow_footer(self, index):
        """Pinned Back / Continue bar for a linear-workflow page."""
        bar = TexturedPanel(self.theme, kind="iron", glow=False, corners=True)
        row = QHBoxLayout(bar)
        row.setContentsMargins(18, 9, 18, 9)
        row.setSpacing(12)

        if self.flow_back_target(index) is not None:
            back_btn = QPushButton("←  Back")
            back_btn.setObjectName("utilityButton")
            back_btn.setCursor(Qt.PointingHandCursor)
            # Recompute the target on click so it honors the current entry mode.
            back_btn.clicked.connect(lambda checked=False, i=index: self.go_to(self.flow_back_target(i)))
            row.addWidget(back_btn)

        row.addStretch(1)

        if index == self.REPORT:
            # End of the flow: offer a clean restart into the same entry mode.
            restart_btn = QPushButton("✦  Start New")
            restart_btn.setObjectName("primaryButton")
            restart_btn.setMinimumHeight(40)
            restart_btn.setCursor(Qt.PointingHandCursor)
            restart_btn.clicked.connect(lambda checked=False: self.start_new_flow(self.entry_mode))
            row.addWidget(restart_btn)
            return bar

        cont = self.flow_continue_target(index)
        if cont is not None:
            cont_index, cont_label = cont
            cont_btn = QPushButton(cont_label)
            cont_btn.setObjectName("primaryButton")
            cont_btn.setMinimumHeight(40)
            cont_btn.setCursor(Qt.PointingHandCursor)
            if index == self.PHILOSOPHY:
                # Run the analysis straight from Philosophy (tester): jump to the
                # Run Analysis page for the animation, then start the guarded run.
                cont_btn.clicked.connect(lambda checked=False: self._run_from_philosophy())
            else:
                cont_btn.clicked.connect(lambda checked=False, i=cont_index: self.go_to(i))
            if index == self.RUN_ANALYSIS:
                # Gated: only usable once a report exists. Keep a handle so go_to
                # can refresh the enabled state (footers are built once at init).
                self.run_to_report_btn = cont_btn
                cont_btn.setEnabled(self.report_is_available())
                cont_btn.setToolTip(
                    "Available after you run an analysis and a report is generated."
                )
            row.addWidget(cont_btn)
        return bar

    def wrap_flow_page(self, page, index):
        """Wrap a flow page with its pinned Continue/Back footer.

        The wrapper keeps the page's stack index unchanged; only the visible
        widget tree gains a footer below the (possibly scrolling) page body.
        """
        wrapper = QWidget()
        v = QVBoxLayout(wrapper)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(8)
        v.addWidget(page, stretch=1)
        v.addWidget(self.build_flow_footer(index))
        return wrapper

    def page_deck_input(self):
        return self.wrap_flow_page(build_deck_selection_page(self), self.DECK_SELECTION)

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


    def sanitize_deck_file_name(self, name):
        """Return a filesystem-safe deck name for pasted decklist saves."""
        cleaned = re.sub(r'[<>:"/\\|?*]+', " ", str(name or "").strip())
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
        return cleaned or "Pasted Deck"

    def next_decklist_number(self, folder):
        """Return the next main integer prefix for saved pasted decklists."""
        path = Path(folder or "Decklists")
        path.mkdir(parents=True, exist_ok=True)
        highest = 0

        for file_path in path.iterdir():
            if not file_path.is_file():
                continue
            match = re.match(r"^\s*(\d+)(?:[.\s-]|$)", file_path.name)
            if not match:
                continue
            try:
                highest = max(highest, int(match.group(1)))
            except ValueError:
                continue

        return highest + 1

    def save_pasted_decklist_to_deck_folder(self, deck_text, deck_name):
        """Save a pasted decklist into the Decklist Folder using next-number naming."""
        text = str(deck_text or "").strip()
        if not text:
            # Category C (popup removal): paste box is empty; status text surfaces this.
            self.state.status = "Paste a decklist into the Paste tab before saving."
            self.refresh_context_panel_values()
            return ""

        safe_name = self.sanitize_deck_file_name(deck_name)
        raw_folder = getattr(self.state, "deck_folder", "") or ""
        folder = Path(raw_folder) if raw_folder else Path("Decklists")
        # Never save into the temp staging folder, even if state.deck_folder was
        # transiently pointed there by a "Use for This Run" preview. The real
        # Decklists folder is the canonical save target.
        if folder.name == "_temp_pasted_decklists" or "_temp_pasted_decklists" in folder.parts:
            folder = Path(self.default_deck_folder() or "Decklists")
            self.state.deck_folder = str(folder)
        folder.mkdir(parents=True, exist_ok=True)

        number = self.next_decklist_number(folder)
        candidate = folder / f"{number}. {safe_name}.txt"

        # Never overwrite. If something unusual exists, add a suffix.
        suffix = 2
        while candidate.exists():
            candidate = folder / f"{number}. {safe_name} ({suffix}).txt"
            suffix += 1

        candidate.write_text(text + "\n", encoding="utf-8")
        return str(candidate)

    def create_temp_pasted_decklist(self, deck_text):
        """Create a temporary run-only pasted decklist file under Outputs/_temp_pasted_decklists."""
        text = str(deck_text or "").strip()
        temp_root = Path(getattr(self.state, "report_output_folder", "Outputs") or "Outputs") / "_temp_pasted_decklists"
        temp_root.mkdir(parents=True, exist_ok=True)
        path = temp_root / "current_pasted_decklist.txt"
        path.write_text(text + "\n", encoding="utf-8")
        return str(path)

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
            # Category C (popup removal): refresh button should be disabled when no deck selected.
            self.state.status = "Select a deck file on the Deck Selection page first."
            self.refresh_context_panel_values()
            return
        self.load_deck_file_preview(self.state.selected_deck_path)

    def load_deck_file_preview(self, path):
        try:
            text = Path(path).read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            try:
                text = Path(path).read_text(encoding="cp1252")
            except Exception as exc:
                # Category D (popup removal): surface in status + stderr.
                import sys as _err_sys
                print(f"Deck Preview Failed: could not read {path}: {exc}", file=_err_sys.stderr)
                self.state.status = f"Deck preview failed — could not read {Path(path).name}"
                self.refresh_context_panel_values()
                return
        except Exception as exc:
            import sys as _err_sys
            print(f"Deck Preview Failed: could not read {path}: {exc}", file=_err_sys.stderr)
            self.state.status = f"Deck preview failed — could not read {Path(path).name}"
            self.refresh_context_panel_values()
            return

        summary = self.summarize_deck_preview(text, Path(path).stem)
        self.state.selected_deck_path = path
        # Only update the persistent decklist folder if this is a real saved
        # deck. The temp staging folder must not become the user's decklist
        # folder (it would poison both "Choose Folder" and future Save targets).
        loaded_parent = Path(path).parent
        if loaded_parent.name != "_temp_pasted_decklists" and "_temp_pasted_decklists" not in loaded_parent.parts:
            self.state.deck_folder = str(loaded_parent)
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
        self.state.warning_details = summary.get("warning_details", [])
        self.state.status = "Deck preview loaded"
        self.state.deck_preview_note = summary["note"]
        # Targeted refresh instead of a full rebuild_shell (tester: deck load felt
        # slow). Update the deck preview + context panel + run summary in place;
        # other pages refresh when navigated to. Fall back to a rebuild only if the
        # lightweight hook isn't available.
        hook = getattr(self, "refresh_deck_selection_preview", None)
        if hook is not None:
            hook()
            self.refresh_context_panel_values()
            self.refresh_run_analysis_previews()
        else:
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
        warning_details = []
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
            warning_details.append("No counted main-deck card lines were detected by the lightweight preview.")
        if total_count and total_count != 100:
            warning_details.append(f"Card total is {total_count}, not 100 (Commander decks are 100 cards including the commander).")
        if not commander_detected:
            warning_details.append("No commander was detected. Add a 'Commander:' section, or the backend will need to infer it.")
        warnings = len(warning_details)

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
            "warning_details": warning_details,
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
            f"Combo analysis: {self.state.combo_awareness_mode}\n"
            f"Collection mode: {self.state.collection_mode}\n"
            f"Collection source: {self.state.collection_source_mode}\n"
            "Backend config mapping: staged by guarded bridge when run is confirmed"
        )

    # v0.10.6.1 combo awareness always-on: Review Setup no longer controls combo enablement.
    def stage_review_settings(self, output_combo, direction_combo, cut_combo, build_up_combo, prompt_combo, budget_input, intended_bracket_combo, combo_awareness_combo=None, collection_mode_combo=None, summary_label=None, intensity_meaning_label=None):
        """Auto-stage Review Setup choices without requiring an Apply button or popup."""
        self.state.output_mode = output_combo.currentText()
        self.state.review_direction = direction_combo.currentText()
        self.state.cut_depth = cut_combo.currentText()
        self.state.build_up_mode = build_up_combo.currentText()
        self.state.prompt_mode = prompt_combo.currentText()
        self.state.budget_note = budget_input.text().strip() or "No budget note provided"
        self.state.intended_bracket = intended_bracket_combo.currentText()
        self.state.combo_awareness_mode = "Always included"
        if collection_mode_combo is not None:
            self.state.collection_mode = collection_mode_combo.currentText()
            self.state.use_collection_settings = self.state.collection_mode not in {"No collection", "Full card pool only", "No replacement suggestions"}
            if self.state.use_collection_settings:
                self.state.collection_source_note = "Collection mode staged from Review Setup. Source default remains managed in Settings."
            else:
                self.state.collection_source_note = "Collection not used for this staged run."
        self.state.bracket = self.state.intended_bracket if self.state.intended_bracket != "Not sure yet" else "Not estimated"
        self.state.status = "Review settings auto-staged"
        if summary_label is not None:
            summary_label.setText(self.review_settings_summary_text())
        if intensity_meaning_label is not None:
            intensity_meaning_label.setText(self.review_intensity_meaning())
        self.refresh_context_panel_values()
        self.refresh_run_analysis_previews()

    def page_analysis_setup(self):
        return self.wrap_flow_page(build_review_setup_page(self), self.REVIEW_SETUP)

    def page_philosophy(self):
        return self.wrap_flow_page(build_philosophy_lens_page(self), self.PHILOSOPHY)

    def page_commander_discovery(self):
        return self.wrap_flow_page(build_commander_discovery_page(self), self.COMMANDER_DISCOVERY)

    def stage_guide_presentation(self, text):
        """Save guide presentation as an app-wide setting."""
        self.state.guide_presentation = user_settings.normalize_guide_presentation(text)
        self.state.status = "Guide presentation saved"
        self.persist_user_settings()
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
            f"- Combo analysis: {self.state.combo_awareness_mode}\n"
            f"- Interface mode: {self.state.interface_mode}\n"
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
            f"- interface_mode -> {self.state.interface_mode}\n"
            "- combo_awareness_default -> Disabled; user opt-in required\n"
            "- combo_awareness_backend_behavior -> opt-in report section can append to normal report; breakdown remains dev-facing\n"
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
            if self.state.collection_mode not in {"No collection", "Full card pool only", "No replacement suggestions"}:
                self.state.collection_source_note = "Entire collection folder staged for guarded run. Selected file payload will not be sent."
        elif self.state.collection_source_mode == "Select collection files":
            self.state.collection_txt_file_count = len(self.state.selected_collection_files)
            if self.state.collection_mode not in {"No collection", "Full card pool only", "No replacement suggestions"}:
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
            # Category C (popup removal): button disabled when folder not detected.
            self.state.status = f"No {label.lower()} detected yet — run Analysis first."
            self.refresh_context_panel_values()
            return
        path = Path(path_text)
        if not path.exists() or not path.is_dir():
            # Category D (popup removal): surface in status + stderr.
            import sys as _err_sys
            print(f"{label} Missing: detected {label.lower()} not found at {path}", file=_err_sys.stderr)
            self.state.status = f"{label} missing — {path}"
            self.refresh_context_panel_values()
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
        # Category E (popup removal): silent no-op. Dev-mode preview button explained itself
        # in a modal — for community release the button it's wired to is hidden in user mode
        # (see run_analysis_page.py).
        pass

    def start_guarded_backend_run(self):
        """Run py main.py only after explicit confirmation, using QProcess and captured output."""
        if self.state.guarded_run_in_progress:
            # Category C (popup removal): the run-in-progress visible state on the Run Analysis page is the signal.
            self.state.last_guarded_run_status = "main.py is already running. Wait for it to finish before starting another guarded run."
            self.refresh_run_analysis_previews()
            return

        entrypoint_path = self.backend_entrypoint_path()
        if self.state.selected_deck_path == "No deck file selected":
            # Category D (popup removal): error already surfaced via last_guarded_run_status + refresh below.
            self.state.last_guarded_run_status = (
                "Guarded run blocked: choose a deck on Deck Selection page first. "
                "The guarded bridge hands that selected deck to main.py using MTG_DECK_FILE."
            )
            self.refresh_run_analysis_previews()
            return

        self.normalize_collection_source_for_guarded_run()
        if self.state.collection_mode not in {"No collection", "Full card pool only", "No replacement suggestions"} and not self.collection_source_detail_answered():
            # Category D (popup removal): error already in last_guarded_run_status.
            self.state.last_guarded_run_status = (
                "Guarded run blocked: collection mode is enabled but no collection source is staged. "
                "Choose a collection folder or select collection files first."
            )
            self.refresh_collection_page_widgets()
            self.refresh_run_analysis_previews()
            return

        if not entrypoint_path.exists():
            # Category D (popup removal): error → status + stderr.
            import sys as _err_sys
            print(f"main.py Not Found at {entrypoint_path}", file=_err_sys.stderr)
            self.state.last_guarded_run_status = (
                f"Guarded run blocked: backend entrypoint not found at {entrypoint_path}. "
                "Confirm the UI was launched from the project root."
            )
            self.refresh_run_analysis_previews()
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
        # Category A (popup removal 2026-05-29): user clicked Run, just run.
        # The status text + visible progress on the Run Analysis page is the
        # feedback. The pre-run details message above is preserved as the
        # status text so the user can still see what's about to happen.
        self.state.last_guarded_run_status = "Starting guarded run: " + message
        self.refresh_run_analysis_previews()

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
        # Category D (popup removal): failure path — status already updated above,
        # Run Analysis page refresh shows the failure inline.

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
        # Category D (popup removal): error in last_guarded_run_status, visible on Run Analysis page.

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
            "Combo analysis Preview\n"
            "- Current integration target -> local Commander Spellbook combo index\n"
            "- External API calls -> disabled\n"
            "- User opt-in required -> True\n"
            "- Default behavior -> Disabled\n"
            "- Normal report insertion -> enabled only for opted-in report-section modes\n"
            "- Generated output -> concise normal report section when selected; breakdown artifact when selected\n\n"
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
        collection_disabled = self.state.collection_mode in {"No collection", "Full card pool only", "No replacement suggestions"}
        collection_ready = collection_disabled or self.state.collection_source_note != "Collection source not staged yet."
        review_ready = True
        philosophy_ready = True

        return (
            f"{'✅' if deck_ready else '❌'} Deck selected: {'Yes' if deck_ready else 'No'}\n"
            f"{'✅' if commander_ready else '❌'} Commander detected: {'Yes' if commander_ready else 'No'}\n"
            f"{'✅' if review_ready else '❌'} Review settings staged: Yes\n"
            f"{'✅' if collection_ready else '❌'} Collection ready or optional: {'Yes' if collection_ready else 'No'}\n"
            f"{'✅' if philosophy_ready else '❌'} Philosophy lens available: Yes\n"
            "⚠️ Backend execution still requires guarded confirmation"
        )

    def run_placeholder_message(self):
        # Category E (popup removal): silent no-op. Dev-mode preview hook.
        pass

    def page_run_review(self):
        return self.wrap_flow_page(build_run_analysis_page(self), self.RUN_ANALYSIS)

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
                if self.is_dev_mode():
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
            # Category C (popup removal): empty query is a no-op; user just sees nothing happen.
            return
        found = self.report_viewer_text_box.find(query)
        if not found:
            self.report_viewer_text_box.moveCursor(QTextCursor.Start)
            found = self.report_viewer_text_box.find(query)
        if not found:
            # Category C (popup removal): use the search input's tooltip to surface "no match".
            try:
                if self.report_viewer_search_input is not None:
                    self.report_viewer_search_input.setToolTip(f"No match found for: {query}")
            except Exception:
                pass

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
            f"Interface mode: {self.state.interface_mode}\n"
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

    def report_viewer_file_button_clicked(self, path_text):
        """Handle Report Viewer detected-file buttons in either User View or Dev View."""
        handler = getattr(self, "report_viewer_open_detected_file", None)
        if callable(handler):
            handler(path_text)
        else:
            self.load_report_file_into_viewer(path_text)


    def refresh_report_viewer_mode_controls(self):
        """Refresh Report Viewer User/Dev visibility from the current Interface Mode.

        v0.10.5.3.3:
        Report Viewer pages are built once with both lanes available. This method
        keeps User Mode clean while allowing Developer Mode to reveal Dev View
        without rebuilding the active Settings page and causing the flash popup.
        """
        is_dev = self.is_dev_mode()

        if getattr(self, "report_viewer_nav_panel", None) is not None:
            self.report_viewer_nav_panel.setVisible(is_dev)

        if getattr(self, "report_viewer_dev_view_button", None) is not None:
            self.report_viewer_dev_view_button.setVisible(is_dev)

        if getattr(self, "report_viewer_mode_intro_label", None) is not None:
            self.report_viewer_mode_intro_label.setText(
                "User View is for AI handoff and readable guidance. Raw report tools are available in Dev View."
                if is_dev
                else "User View is for AI handoff and readable guidance."
            )

        if not is_dev and getattr(self, "report_viewer_mode_stack", None) is not None:
            self.report_viewer_mode_stack.setCurrentIndex(0)
            if getattr(self, "report_viewer_user_view_button", None) is not None:
                self.report_viewer_user_view_button.setObjectName("primaryButton")
                self.report_viewer_user_view_button.style().unpolish(self.report_viewer_user_view_button)
                self.report_viewer_user_view_button.style().polish(self.report_viewer_user_view_button)
            if getattr(self, "report_viewer_dev_view_button", None) is not None:
                self.report_viewer_dev_view_button.setObjectName("utilityButton")
                self.report_viewer_dev_view_button.style().unpolish(self.report_viewer_dev_view_button)
                self.report_viewer_dev_view_button.style().polish(self.report_viewer_dev_view_button)

    def refresh_report_viewer_file_list(self):
        if self.is_user_facing_mode():
            layout = getattr(self, "report_viewer_file_buttons_layout", None)
            if layout is not None:
                self.clear_layout_widgets(layout)
            return

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
                    btn.clicked.connect(lambda checked=False, p=path_text: self.report_viewer_file_button_clicked(p))
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
        # Category B (popup removal): the file list visibly refreshes — that's the feedback.
        self.refresh_report_viewer_file_list()

    def refresh_current_report_file(self):
        path = Path(self.state.report_viewer_current_file)
        if not path.exists() or not path.is_file():
            # Category C (popup removal): button should be disabled when no report file (see refresh_report_viewer_current_file_controls).
            return
        # Category B (popup removal): the report content visibly updates — that's the feedback.
        self.load_report_file_into_viewer(str(path))

    def copy_current_report_text(self):
        text = self.state.report_viewer_current_text or ""
        if not text.strip():
            # Category C (popup removal): copy button should be disabled when no text.
            return
        # Category B (popup removal): clipboard works silently like every other app.
        QApplication.clipboard().setText(text)

    def open_current_report_file(self):
        path = Path(self.state.report_viewer_current_file)
        if not path.exists() or not path.is_file():
            # Category C (popup removal): button should be disabled when no report file.
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def open_current_report_folder(self):
        path = Path(self.state.report_viewer_current_file)
        if not path.exists() or not path.is_file():
            # Category C (popup removal): button should be disabled when no report file.
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.parent)))

    def page_report_viewer(self):
        return self.wrap_flow_page(build_report_viewer_page(self), self.REPORT)

    def page_training_review(self):
        return build_training_review_page(self)

    def page_deck_coach(self):
        return build_deck_coach_page(self)

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
        self.state.use_collection_settings = mode not in {"No collection", "Full card pool only", "No replacement suggestions"}
        if mode in {"No collection", "Full card pool only", "No replacement suggestions"}:
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
        self.state.use_collection_settings = self.state.collection_mode not in {"No collection", "Full card pool only", "No replacement suggestions"}
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
        self.state.use_collection_settings = self.state.collection_mode not in {"No collection", "Full card pool only", "No replacement suggestions"}
        self.state.status = "Collection folder auto-staged"
        self.persist_user_settings()
        if getattr(self, "settings_collection_folder_label", None) is not None:
            self.settings_collection_folder_label.setText(folder)
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
        self.state.use_collection_settings = self.state.collection_mode not in {"No collection", "Full card pool only", "No replacement suggestions"}
        self.state.status = "Collection files auto-staged"
        self.persist_user_settings()
        if getattr(self, "settings_collection_folder_label", None) is not None:
            self.settings_collection_folder_label.setText(f"{len(files)} selected file(s)")
        self.refresh_collection_page_widgets()

    def stage_collection_settings(self, summary_label=None):
        """Auto-stage collection settings without requiring an Apply button or popup."""
        self.state.use_collection_settings = self.state.collection_mode not in {"No collection", "Full card pool only", "No replacement suggestions"}
        if self.state.collection_mode in {"No collection", "Full card pool only", "No replacement suggestions"}:
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


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("The Dragon's Touch")
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
