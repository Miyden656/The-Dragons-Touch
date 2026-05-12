# The Dragon's Touch — Patch Notes

## v0.7.7.1 — Guarded Execution Preview Hotfix

### Purpose
Fix a startup regression introduced in v0.7.7 where the Run Analysis page still calls `guarded_execution_preview_text()` during page construction, but that method was accidentally omitted while extracting backend-runner / CLI-bridge helper logic.

### Fix
Restored `MainWindow.guarded_execution_preview_text()` in `ui/dragons_touch_pyside6_workstation.py`.

### What changed
- Re-added the missing guarded execution preview text method.
- Left the v0.7.7 backend-runner / CLI-bridge service extraction intact.

### What did not change
- No backend behavior changed.
- `main.py` remains the backend source of truth.
- Guarded confirmation remains required.
- No silent backend execution was introduced.
- Output folder behavior was not changed.
- Report detection was not changed.
- Report Viewer plain-text loading was not changed.
- Commander Spellbook/API remains disabled.
- Batch/Aggregate remains placeholder/future.
- Replacement Candidate Engine was not introduced.

### Validation
Compiled successfully with:

```bash
python -m py_compile ui/dragons_touch_pyside6_workstation.py ui/services/backend_runner.py ui/services/cli_bridge.py
```
