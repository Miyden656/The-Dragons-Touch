# Patch Notes — v0.7.6 Report Detection Service Extraction

## Purpose

Continue the v0.7 Alpha Hardening modularization track by moving report-output detection helper logic out of the main PySide6 UI script and into a dedicated service module.

This is a behavior-preservation refactor. It does not change report generation, output folder naming, guarded execution, or plain-text report loading.

## Files changed / added

- `ui/dragons_touch_pyside6_workstation.py`
- `ui/services/__init__.py`
- `ui/services/report_detector.py`
- `docs/ui_refactor_map_v0.7.md`
- `PATCH_NOTES_v0.7.6.md`

## What moved

Created `ui/services/report_detector.py` and moved/extracted pure report-detection helpers into it:

- backend printed path resolution
- expected normal/debug category detection from Output Mode
- path folder/category checks
- detected output folder inference
- Files written stdout block parsing
- backend unique-output no-op status handling
- report detection result construction
- detected folder openability check

## What stayed in the main UI

The main UI still owns:

- state updates
- buttons
- Report Viewer widgets
- opening folders/files through Qt
- guarded execution UI
- plain-text report loading controls

The main UI now calls the service module rather than owning all report detection helper logic directly.

## Safety boundary

This patch does not:

- edit `main.py`
- run the backend differently
- change `subprocess`/`QProcess` behavior
- bypass guarded confirmation
- move generated report files
- change output folder behavior
- parse report markdown deeply
- introduce Commander Spellbook/API calls
- introduce Batch/Aggregate workflow
- introduce Replacement Candidate Engine behavior

Locked workflow preserved:

```text
UI staged state
-> guarded confirmation
-> subprocess/main.py
-> CLI input bridge
-> backend output folder
-> report detection
-> Report Viewer plain-text load
```

## Validation run

```bash
python -m py_compile ui/dragons_touch_pyside6_workstation.py ui/services/report_detector.py ui/services/__init__.py ui/constants.py ui/styles/theme.py ui/widgets/core.py ui/state/staged_run_config.py main.py config.py
```

Additional synthetic service smoke test passed for a stdout `Files written:` block containing one normal and one debug report path.
