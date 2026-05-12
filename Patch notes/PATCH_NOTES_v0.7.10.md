# The Dragon's Touch — Patch Notes

## v0.7.10 — Page Extraction: Review Setup

This patch extracts the Review Setup page layout from the active PySide6 UI script into a dedicated page module.

## Files changed

- `ui/dragons_touch_pyside6_workstation.py`
- `ui/pages/review_setup_page.py`
- `docs/ui_refactor_map_v0.7.md`

## What changed

Created:

- `ui/pages/review_setup_page.py`

The active `MainWindow.page_analysis_setup()` method now delegates to:

- `build_review_setup_page(self)`

## What stayed on MainWindow

MainWindow still owns the active Review Setup behavior:

- `review_focus_text()`
- `review_intensity_meaning()`
- `review_settings_summary_text()`
- `stage_review_settings()`
- context panel refresh
- Run Analysis preview refresh
- staged-state mutation
- guarded backend handoff

## What did not change

This patch does not change:

- `main.py`
- backend execution
- guarded confirmation
- CLI bridge behavior
- output folder behavior
- report detection
- Report Viewer plain-text loading
- Commander Spellbook/API status
- Batch/Aggregate status
- Replacement Candidate Engine status

## Test focus

Pay special attention to:

- Review Direction conditional fields
- Review Intensity / Build-Up Mode stack switching
- Auto batch mirror controls
- immediate Run Settings Summary updates
- Budget Note staging
- Intended Bracket staging
- Run Analysis preview refreshes
