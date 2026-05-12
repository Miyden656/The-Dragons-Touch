# The Dragon's Touch — Patch Notes

## v0.7.12 — Page Extraction: Collection Source

This patch extracts the Collection Source page layout into its own page module while preserving the existing staged-state and backend handoff behavior.

### Files changed

- `ui/dragons_touch_pyside6_workstation.py`
- `ui/pages/__init__.py`
- `ui/pages/collection_source_page.py`
- `docs/ui_refactor_map_v0.7.md`

### What changed

Created:

- `ui/pages/collection_source_page.py`

The active UI still has `MainWindow.page_collection_tools()`, but it now delegates to `build_collection_source_page(self)`.

### What stayed in MainWindow

MainWindow still owns:

- collection mode staging
- collection source mode staging
- folder chooser behavior
- selected collection files behavior
- collection summary refreshes
- context panel refreshes
- Run Analysis preview refreshes
- CLI/main.py guarded handoff

### What did not change

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

### Validation

Compile check passed for:

```bash
python -m py_compile ui/dragons_touch_pyside6_workstation.py ui/pages/collection_source_page.py ui/pages/__init__.py
```
