"""Page builders for The Dragon's Touch PySide6 UI."""

from .collection_source_page import build_collection_source_page
from .deck_selection_page import build_deck_selection_page
from .future_workspace_page import build_batch_reports_page, build_settings_page
from .philosophy_lens_page import build_philosophy_lens_page
from .report_viewer_page import build_report_viewer_page
from .review_setup_page import build_review_setup_page
from .run_analysis_page import build_run_analysis_page

__all__ = [
    "build_batch_reports_page",
    "build_collection_source_page",
    "build_deck_selection_page",
    "build_philosophy_lens_page",
    "build_report_viewer_page",
    "build_review_setup_page",
    "build_run_analysis_page",
    "build_settings_page",
]
