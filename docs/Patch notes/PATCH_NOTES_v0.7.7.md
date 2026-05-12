# The Dragon's Touch — Patch Notes

## v0.7.7 — Backend Runner / CLI Bridge Service Extraction

Purpose:
Continue the v0.7 Alpha Hardening modularization track by moving backend-runner helper logic and CLI-bridge answer mapping out of the main PySide6 UI script while preserving the locked guarded workflow.

Files included in this patch:

- `ui/dragons_touch_pyside6_workstation.py`
- `ui/services/backend_runner.py`
- `ui/services/cli_bridge.py`
- `docs/ui_refactor_map_v0.7.md`
- `PATCH_NOTES_v0.7.7.md`

What changed:

- Added `ui/services/backend_runner.py` for non-visual guarded-run helper functions:
  - backend entrypoint path resolution
  - guarded command preview
  - guarded command parts
  - backend process environment values
  - process-output trimming
- Added `ui/services/cli_bridge.py` for non-visual CLI bridge helpers:
  - UI option to CLI answer mappings
  - conditional bridge checks
  - collection-source detail preview helpers
  - full stdin payload generation
  - CLI bridge preview text
- Updated `ui/dragons_touch_pyside6_workstation.py` so existing `MainWindow` methods delegate to the new service modules.

What did not change:

- `main.py` remains backend source of truth.
- The UI still owns guarded confirmation.
- The UI still owns QProcess creation and process lifetime.
- The UI still uses `py main.py` through QProcess.
- The UI still avoids `shell=True`.
- The UI still closes stdin after known answers.
- Report detection still runs after guarded backend completion.
- Report Viewer remains plain-text loading.
- Commander Spellbook/API remains disabled.
- Batch/Aggregate remains placeholder/future.
- Replacement Candidate Engine is not introduced.

Validation performed:

```bash
python -m py_compile ui/dragons_touch_pyside6_workstation.py ui/services/backend_runner.py ui/services/cli_bridge.py ui/services/report_detector.py ui/services/__init__.py ui/constants.py ui/styles/theme.py ui/widgets/core.py ui/state/staged_run_config.py main.py config.py
```

Additional smoke validation:

- Created an `AppState` object.
- Generated a CLI input payload through `ui.services.cli_bridge`.
- Confirmed output mode/review direction/review intensity/prompt/philosophy/guide/collection answers are generated in the expected order.
- Confirmed backend command/environment helper output.

Scope guard:
This is not a backend rewrite. This is not a new execution path. It is a service extraction that preserves the existing guarded UI-to-main.py workflow.
