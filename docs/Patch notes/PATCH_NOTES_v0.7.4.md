# Patch Notes — v0.7.4 Shared Widgets Extraction

## Purpose

Continue the v0.7 Alpha Hardening modularization track by moving reusable visual widgets out of the one-script UI without changing runtime behavior.

## Files changed / added

```text
ui/dragons_touch_pyside6_workstation.py
ui/widgets/__init__.py
ui/widgets/core.py
docs/ui_refactor_map_v0.7.md
PATCH_NOTES_v0.7.4.md
```

## Extracted into `ui/widgets/core.py`

- `add_shadow`
- `TexturedPanel`
- `ForgeOrb`
- `SidebarButton`
- `Badge`
- `ReportCard`
- `SmallStat`
- `PillButton`

## Behavior boundaries

This patch does not change:

- `main.py`
- backend execution
- guarded confirmation
- CLI input bridge behavior
- output folder behavior
- report detection
- Report Viewer plain-text loading
- Commander Spellbook/API status
- Batch/Aggregate status
- Replacement Candidate Engine status

## Validation

Passed:

```bash
python -m py_compile ui/dragons_touch_pyside6_workstation.py ui/constants.py ui/styles/theme.py ui/widgets/core.py ui/widgets/__init__.py main.py config.py
```

## Next recommended patch

`v0.7.5 — Staged State Object Extraction`

This should move `AppState` into `ui/state/staged_run_config.py` while preserving all current defaults and staged values.
