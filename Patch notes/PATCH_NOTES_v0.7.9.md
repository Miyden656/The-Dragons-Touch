# The Dragon's Touch — Patch Notes

## v0.7.9 — Page Extraction: Deck Selection

This patch extracts the Deck Selection page layout builder from the active one-script PySide6 UI into a page module.

### Files changed

- `ui/dragons_touch_pyside6_workstation.py`
- `ui/pages/deck_selection_page.py`
- `docs/ui_refactor_map_v0.7.md`
- `PATCH_NOTES_v0.7.9.md`

### Files added

- `ui/pages/deck_selection_page.py`

### What changed

- `MainWindow.page_deck_input()` now delegates to `build_deck_selection_page(self)`.
- The Deck Selection page layout now lives in `ui/pages/deck_selection_page.py`.

### What stayed in MainWindow

MainWindow still owns the behavior:

- deck file picker
- preview reload
- deck-file reading
- lightweight preview parsing
- commander/companion preview state updates
- selected deck staged-state handoff
- rebuild behavior after preview load

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

Syntax validation passed for:

```bash
python -m py_compile ui/dragons_touch_pyside6_workstation.py ui/pages/deck_selection_page.py ui/pages/report_viewer_page.py ui/pages/__init__.py
```

### Testing emphasis

Because Deck Selection feeds staged state and backend handoff, test file selection, preview reload, commander/companion preview, Run Analysis selected-deck summary, and a guarded run after applying this patch.
