# The Dragon's Touch — Patch Notes

## v0.7.3 — Theme / QSS Extraction

### Purpose
Continue the v0.7 alpha-hardening modularization track by separating the main visual theme data and app-wide QSS builder from the one-script PySide6 UI file.

This is a maintainability refactor only. It should not change runtime behavior, backend behavior, report generation, output folder naming, or the guarded UI-to-main.py workflow.

### Files Changed / Added

- `ui/dragons_touch_pyside6_workstation.py`
- `ui/styles/__init__.py`
- `ui/styles/theme.py`
- `docs/ui_refactor_map_v0.7.md`

### What Changed

- Moved `DRAGON_FORGE` and `ADVENTURERS_MAP` theme dictionaries into `ui/styles/theme.py`.
- Moved the large app-wide QSS stylesheet builder into `ui/styles/theme.py` as `build_main_qss(t)`.
- Updated the main UI script to import `DRAGON_FORGE`, `ADVENTURERS_MAP`, and `build_main_qss`.
- Kept a small `qss(self, t)` wrapper in the main window so existing theme application code remains stable.

### What Did Not Change

- No changes to `main.py`.
- No changes to backend execution.
- No changes to guarded confirmation.
- No changes to CLI input bridge behavior.
- No changes to output folder behavior.
- No changes to report detection behavior.
- No changes to Report Viewer plain-text loading.
- No Commander Spellbook/API integration added.
- No Batch/Aggregate workflow added.
- No Replacement Candidate Engine behavior added.

### Validation

Passed:

```bash
python -m py_compile ui/dragons_touch_pyside6_workstation.py ui/constants.py ui/styles/theme.py main.py config.py
```

### Test Focus

The main thing to test is visual parity:

- App launches.
- Dragon Forge theme still looks correct.
- Adventurer's Map theme still looks correct.
- Theme toggle still works.
- Dropdown popup styling still works.
- Run Analysis and Report Viewer still behave normally.
