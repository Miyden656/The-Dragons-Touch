"""Staged run state for The Dragon's Touch desktop UI.

This module stores UI-staged values only. It must not run the backend,
call main.py, detect reports, or perform filesystem side effects beyond
default path text values.

Locked workflow boundary:
UI staged state -> guarded confirmation -> subprocess/main.py -> CLI input bridge
-> backend output folder -> report detection -> plain-text Report Viewer.
"""

from dataclasses import dataclass, field
from pathlib import Path

try:
    from ui.constants import (
        DEFAULT_SELECTED_PHILOSOPHY, DEFAULT_PHILOSOPHY_SUBTYPE, DEFAULT_GUIDE_PRESENTATION,
        DEFAULT_OUTPUT_MODE, DEFAULT_REVIEW_DIRECTION, DEFAULT_REVIEW_INTENSITY, DEFAULT_BUILD_UP_MODE,
        DEFAULT_PROMPT_MODE, DEFAULT_INTENDED_BRACKET, DEFAULT_COLLECTION_MODE, DEFAULT_COLLECTION_SOURCE_MODE, DEFAULT_COMBO_AWARENESS_MODE, DEFAULT_INTERFACE_MODE,
    )
except ImportError:  # Allows direct execution from inside the ui/ folder during local testing.
    from constants import (
        DEFAULT_SELECTED_PHILOSOPHY, DEFAULT_PHILOSOPHY_SUBTYPE, DEFAULT_GUIDE_PRESENTATION,
        DEFAULT_OUTPUT_MODE, DEFAULT_REVIEW_DIRECTION, DEFAULT_REVIEW_INTENSITY, DEFAULT_BUILD_UP_MODE,
        DEFAULT_PROMPT_MODE, DEFAULT_INTENDED_BRACKET, DEFAULT_COLLECTION_MODE, DEFAULT_COLLECTION_SOURCE_MODE, DEFAULT_COMBO_AWARENESS_MODE, DEFAULT_INTERFACE_MODE,
    )


@dataclass
class AppState:
    theme: dict
    selected_philosophy: str = DEFAULT_SELECTED_PHILOSOPHY
    philosophy_subtype: str = DEFAULT_PHILOSOPHY_SUBTYPE
    guide_presentation: str = DEFAULT_GUIDE_PRESENTATION
    deck_name: str = "No deck selected"
    commander: str = "No commander detected"
    deck_size: int = 0
    bracket: str = "Not estimated"
    warnings: int = 0
    status: str = "Ready — select a deck or start with Commander's Call"
    selected_deck_path: str = "No deck file selected"
    deck_preview_text: str = "Choose a deck file to preview it here. The backend is still disconnected; this page only loads and summarizes the local file."
    deck_preview_note: str = "No deck file loaded yet."
    commander_detected: bool = False
    main_deck_count: int = 0
    commander_count: int = 0
    companion_name: str = "No companion detected"
    companion_detected: bool = False
    companion_count: int = 0
    output_mode: str = DEFAULT_OUTPUT_MODE
    review_direction: str = DEFAULT_REVIEW_DIRECTION
    cut_depth: str = DEFAULT_REVIEW_INTENSITY
    build_up_mode: str = DEFAULT_BUILD_UP_MODE
    prompt_mode: str = DEFAULT_PROMPT_MODE
    budget_note: str = "Optional budget note, e.g. $25/card"
    intended_bracket: str = DEFAULT_INTENDED_BRACKET
    respect_table_bracket: bool = False
    use_collection_settings: bool = False
    collection_mode: str = DEFAULT_COLLECTION_MODE
    collection_source_mode: str = DEFAULT_COLLECTION_SOURCE_MODE
    combo_awareness_mode: str = "Always included"
    interface_mode: str = DEFAULT_INTERFACE_MODE
    report_output_folder: str = "Outputs"
    ui_density: str = "Normal"
    developer_report_viewer_last_view: str = "User View"
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
    report_viewer_font_size: int = 14
    report_viewer_word_wrap: bool = True
    report_viewer_search_text: str = ""
