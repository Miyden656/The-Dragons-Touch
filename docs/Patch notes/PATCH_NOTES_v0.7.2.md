# The Dragon's Touch — Patch Notes v0.7.2

## Patch Name
v0.7.2 — Constants and Version Labels Extraction

## Purpose
Start the first safe code-movement step of the v0.7 UI modularization track by moving stable UI labels, dropdown option lists, and default staged values out of the one-script PySide6 UI file.

## Files Changed
- `ui/dragons_touch_pyside6_workstation.py`
- `ui/constants.py`

## What Changed
- Added `ui/constants.py` as the first low-risk extracted UI module.
- Moved app/version labels into constants:
  - `APP_VERSION`
  - `APP_PHASE`
  - `BACKEND_STATUS`
  - `LOCKED_BACKEND_VERSION`
- Moved dropdown option lists into constants:
  - output mode
  - review direction
  - review intensity
  - build-up mode
  - prompt mode
  - intended bracket
  - guide presentation
  - philosophy subtype/persona
  - Run Analysis detail selector
  - collection mode
  - collection source
- Moved matching default staged values into constants.
- Updated `AppState` defaults to use the new constants.
- Updated affected `QComboBox.addItems(...)` calls to use the new option constants.
- Added a flexible import fallback so the UI can still be launched either from the project root or directly from inside the `ui/` folder during local testing.

## What Did Not Change
- No backend behavior changed.
- `main.py` remains the backend source of truth.
- Guarded run confirmation remains required.
- No silent backend execution was added.
- CLI bridge behavior was not changed.
- Output folder behavior was not changed.
- Report detection was not changed.
- Report Viewer remains plain-text loading.
- Commander Spellbook/API remains disabled.
- Batch/Aggregate remains future/placeholder.
- Replacement Candidate Engine was not introduced.

## Validation Performed
Passed:

```bash
python -m py_compile ui/dragons_touch_pyside6_workstation.py ui/constants.py main.py config.py
```

## Recommended Test
Run the focused v0.7.2 constants extraction checklist before moving to v0.7.3 Theme / QSS Extraction.
