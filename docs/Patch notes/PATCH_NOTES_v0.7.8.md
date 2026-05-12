# v0.7.8 — Page Extraction: Report Viewer First

## Purpose
Move the Report Viewer page builder out of the main PySide6 UI file while preserving existing Report Viewer behavior.

## Files changed
- `ui/dragons_touch_pyside6_workstation.py`
- `ui/pages/__init__.py`
- `ui/pages/report_viewer_page.py`

## What changed
- Added `ui/pages/report_viewer_page.py`.
- Moved the Report Viewer page-construction code into `build_report_viewer_page(window)`.
- Left MainWindow-owned report loading, report detection, search, copy, open-file, open-folder, and refresh methods in place.
- Kept `MainWindow.page_report_viewer()` as a compatibility wrapper.

## What did not change
- No backend behavior changed.
- No `main.py` behavior changed.
- No guarded execution behavior changed.
- No CLI bridge behavior changed.
- No output folder behavior changed.
- No report detection behavior changed.
- No Report Viewer plain-text behavior changed.
- No deep markdown rendering was introduced.

## Scope guard
The Report Viewer page module is visual/page construction only. It does not create a second backend workflow and does not run analysis.
