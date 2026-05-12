# The Dragon's Touch — Patch Notes

## v0.7.5 — Staged State Object Extraction

This patch continues the v0.7 Alpha Hardening modularization track.

## Files changed / added

```text
ui/dragons_touch_pyside6_workstation.py
ui/state/__init__.py
ui/state/staged_run_config.py
docs/ui_refactor_map_v0.7.md
PATCH_NOTES_v0.7.5.md
```

## What changed

Created:

```text
ui/state/
  __init__.py
  staged_run_config.py
```

Moved `AppState` out of the main one-script UI and into `ui/state/staged_run_config.py`.

The main UI now imports `AppState` from `ui.state`.

## What did not change

This patch does not change:

- `main.py`
- backend execution
- guarded confirmation
- CLI input bridge behavior
- output folder behavior
- report detection behavior
- Report Viewer plain-text loading
- Commander Spellbook/API status
- Batch/Aggregate status
- Replacement Candidate Engine status
- page layout ownership
- active workflow behavior

## Important boundary

`AppState` remains a passive staged-state dataclass. It must not become a service object, backend runner, report detector, or workflow controller.

Locked workflow remains:

```text
UI staged state
-> guarded confirmation
-> subprocess/main.py
-> CLI input bridge
-> backend output folder
-> report detection
-> Report Viewer plain-text load
```

## Validation

Passed:

```bash
python -m py_compile ui/dragons_touch_pyside6_workstation.py ui/constants.py ui/styles/theme.py ui/widgets/core.py ui/state/staged_run_config.py ui/state/__init__.py main.py config.py
```

## Next recommended patch

`v0.7.6 — Report Detection Service Extraction`

Only start v0.7.6 after v0.7.5 passes the staged-state workflow checks.
