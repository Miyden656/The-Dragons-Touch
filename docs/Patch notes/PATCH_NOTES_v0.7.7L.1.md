# Patch Notes — v0.7.7L.1 Python Launcher / Shortcut Fallback

## Purpose

Correct the launcher/access path after Windows Smart App Control blocked the `.bat` launcher on test.

The `.bat` launcher should no longer be the recommended alpha-user path. Use the Python launchers instead.

## Files Added / Updated

```text
Launch_The_Dragons_Touch.py
Launch_The_Dragons_Touch.pyw
README_START_HERE.txt
docs/alpha_access_launcher_v0.7.md
PATCH_NOTES_v0.7.7L.1.md
```

## Recommended Launch Path

```text
Primary:  Launch_The_Dragons_Touch.pyw
Fallback: Launch_The_Dragons_Touch.py
```

The `.bat` launcher may remain in the project as a developer fallback, but it is not the recommended alpha-user launch path because Windows Smart App Control may block it.

## Behavior

The Python launcher opens the PySide6 desktop UI:

```text
ui/dragons_touch_pyside6_workstation.py
```

It does not automatically run deck analysis.

The normal locked workflow remains:

```text
UI staged state
-> guarded confirmation
-> subprocess/main.py
-> CLI input bridge
-> backend output folder
-> report detection
-> Report Viewer plain-text load
```

## What This Patch Does Not Change

- No changes to main.py.
- No changes to backend execution.
- No changes to guarded run behavior.
- No changes to CLI bridge behavior.
- No changes to output folder behavior.
- No changes to report detection.
- No changes to Report Viewer.
- No Commander Spellbook/API integration.
- No Batch/Aggregate real workflow.
- No Replacement Candidate Engine.
- No executable packaging yet.
- No installer yet.

## Test Checklist

### Python Launcher

- Pass/Fail: `Launch_The_Dragons_Touch.pyw` exists in the project root.
- Pass/Fail: Double-clicking `Launch_The_Dragons_Touch.pyw` opens the desktop UI.
- Pass/Fail: If `.pyw` does not open, double-clicking `Launch_The_Dragons_Touch.py` opens the desktop UI.
- Pass/Fail: Launching with `python Launch_The_Dragons_Touch.py` opens the desktop UI.
- Pass/Fail: Launcher does not require Visual Studio Code.
- Pass/Fail: Launcher does not automatically run deck analysis.
- Pass/Fail: Launcher starts from the project root correctly.
- Pass/Fail: Launcher shows a useful error if PySide6 is missing.

### Normal UI Workflow

- Pass/Fail: Deck Selection opens.
- Pass/Fail: Review Setup opens.
- Pass/Fail: Philosophy Lens opens.
- Pass/Fail: Collection Source opens.
- Pass/Fail: Run Analysis opens.
- Pass/Fail: Report Viewer opens.

### Backend Workflow Preservation

- Pass/Fail: UI still stages choices before run.
- Pass/Fail: Guarded confirmation still appears.
- Pass/Fail: Cancel prevents execution.
- Pass/Fail: Confirmed run still goes through main.py.
- Pass/Fail: Output folders are still generated normally.
- Pass/Fail: Report detection still works.
- Pass/Fail: Report Viewer still loads plain text.

### Smart App Control Handling

- Pass/Fail: README no longer presents `.bat` as the primary alpha-user launch path.
- Pass/Fail: README says not to disable Smart App Control just to run the alpha launcher.
- Pass/Fail: Long-term plan still points toward packaged/signed installer path later.
