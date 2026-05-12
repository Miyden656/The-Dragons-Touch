# The Dragon's Touch — Patch Notes

## v0.7.15 — Main Window Cleanup / Alpha Hardening Pass

Purpose:
Clean the active PySide6 UI file after successful page-layout extraction through v0.7.14.

This is a cleanup/hardening patch, not a feature patch.

## Changed

- Consolidated Run Analysis and Report Viewer page-builder imports into the top-level page import block.
- Simplified `page_run_review()` and `page_report_viewer()` so they delegate directly to extracted page modules.
- Removed unused imports left behind after moving theme/widgets/page layout code out of the active UI file.
- Removed duplicate Report Viewer attribute initialization.
- Corrected the v0.7 workflow boundary comment near the top of the UI file.
- Updated `docs/ui_refactor_map_v0.7.md` with the v0.7.15 cleanup checkpoint.

## Preserved

- `main.py` remains the backend source of truth.
- Guarded confirmation remains required.
- UI does not silently run backend analysis.
- CLI bridge behavior remains unchanged.
- Output folder behavior remains unchanged.
- Report detection behavior remains unchanged.
- Report Viewer remains plain text.
- Commander Spellbook/API remains disabled.
- Batch / Aggregate remains placeholder/future.
- Replacement Candidate Engine is not introduced.

## Validation

Syntax validation target:

```bash
python -m py_compile ui/dragons_touch_pyside6_workstation.py ui/pages/*.py
```

Expected result: pass.

## Test Focus

Because this patch cleans imports and wrappers, test:

- App launch
- All page navigation
- Run Analysis page load
- Report Viewer page load
- Guarded run confirmation
- Report detection
- Report Viewer plain-text loading
