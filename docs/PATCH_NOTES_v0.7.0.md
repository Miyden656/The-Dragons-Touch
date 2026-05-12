# Patch v0.7.0 — Desktop UI Alpha Foundation Baseline

## Purpose
Begin v0.7 Alpha Hardening without changing runtime behavior.

## What changed
- Updated the active PySide6 UI version label from `v0.6.8.5` to `v0.7.0`.
- Updated the UI phase label to `Desktop UI Alpha Foundation / Alpha Hardening`.
- Preserved the stable backend workflow language: guarded UI bridge uses CLI/main.py as source of truth.
- Updated locked backend/status wording to reference the stable v0.6.8.5 workflow.
- Created a legacy copy of the prior one-script UI:
  - `ui/dragons_touch_pyside6_workstation_legacy_v0.6.8.5.py`
- Added a refactor planning document:
  - `docs/ui_refactor_map_v0.7.md`

## What did not change
- No backend behavior changed.
- No output folder behavior changed.
- No report generation behavior changed.
- No Commander Spellbook/API behavior was added.
- No Batch/Aggregate real workflow was added.
- No deep markdown rendering was added.
- Guarded run behavior remains the intended workflow.
- main.py remains the backend source of truth.

## Validation performed
- `python -m py_compile ui/dragons_touch_pyside6_workstation.py main.py config.py` passed.

## Next recommended patch
v0.7.1 — UI Structure Audit / Refactor Map Refinement

Recommended next step: use the refactor map to confirm section boundaries before extracting constants/theme/widgets.
