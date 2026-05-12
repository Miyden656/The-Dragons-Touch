# v0.7.14 — Future / Placeholder Pages Extraction

## Purpose
Extract the remaining lower-risk placeholder/settings page layouts out of the main PySide6 UI script while preserving the locked v0.7 alpha workflow.

## Files changed
- `ui/dragons_touch_pyside6_workstation.py`
- `ui/pages/__init__.py`
- `ui/pages/future_workspace_page.py`
- `docs/ui_refactor_map_v0.7.md`

## What changed
- Added `ui/pages/future_workspace_page.py`.
- Moved the Batch / Aggregate placeholder page layout into `build_batch_reports_page(host)`.
- Moved the Settings/checkpoint page layout into `build_settings_page(host)`.
- Updated `page_batch_reports()` and `page_settings()` in the main UI to delegate to the new page builders.
- Updated `ui/pages/__init__.py` to expose the new page builders.

## What did not change
- No backend behavior changed.
- No `main.py` behavior changed.
- No guarded execution behavior changed.
- No CLI bridge behavior changed.
- No output folder behavior changed.
- No report detection behavior changed.
- No Report Viewer behavior changed.
- No Commander Spellbook/API behavior was added.
- No Batch / Aggregate real workflow was added.
- No Replacement Candidate Engine behavior was added.

## Safety boundary
This extraction only moves page layout code. Batch / Aggregate remains a placeholder/future workspace, and Settings remains an informational/checkpoint page.

The locked workflow remains:

`UI staged state -> guarded confirmation -> subprocess/main.py -> CLI input bridge -> backend output folder -> report detection -> Report Viewer plain-text load`

## Validation
Passed:

```bash
python -m py_compile ui/dragons_touch_pyside6_workstation.py ui/pages/future_workspace_page.py ui/pages/__init__.py
```
