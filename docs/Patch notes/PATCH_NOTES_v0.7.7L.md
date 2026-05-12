# Patch Notes — v0.7.7L Local Launcher / Alpha Access

## Purpose

Make The Dragon's Touch easier to launch for alpha testing without requiring Visual Studio Code.

## Files Added

```text
Launch_The_Dragons_Touch.bat
Create_Desktop_Shortcut.bat
README_START_HERE.txt
docs/alpha_access_launcher_v0.7.md
```

## Behavior

The launcher opens the PySide6 desktop UI:

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

### Launcher

- Pass/Fail: `Launch_The_Dragons_Touch.bat` exists in the project root.
- Pass/Fail: Double-clicking launcher opens the desktop UI.
- Pass/Fail: Launcher does not require Visual Studio Code.
- Pass/Fail: Launcher does not automatically run deck analysis.
- Pass/Fail: Launcher starts from the project root correctly.
- Pass/Fail: Launcher shows a useful error if Python is missing.
- Pass/Fail: Launcher shows a useful error if PySide6 is missing.

### Desktop Shortcut

- Pass/Fail: `Create_Desktop_Shortcut.bat` exists in the project root.
- Pass/Fail: Running it creates a desktop shortcut.
- Pass/Fail: Desktop shortcut opens the UI.
- Pass/Fail: Shortcut uses the correct working directory.
- Pass/Fail: Shortcut does not silently execute backend analysis.

### Workflow Preservation

- Pass/Fail: UI still stages choices before run.
- Pass/Fail: Guarded confirmation still appears.
- Pass/Fail: Confirmed run still goes through main.py.
- Pass/Fail: Output folders are still generated normally.
- Pass/Fail: Report detection still works.
- Pass/Fail: Report Viewer still loads plain text.
