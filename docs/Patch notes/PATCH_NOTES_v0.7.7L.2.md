# Patch Notes — v0.7.7L.2 Launcher Cleanup / Shortcut Retarget

## Purpose

Clean up the alpha launcher path after v0.7.7L.1 testing confirmed that `Launch_The_Dragons_Touch.pyw` opens the desktop UI without Visual Studio Code.

The `.bat` launcher is no longer the recommended alpha path because Windows Smart App Control blocked it during testing.

## Files Added / Updated

```text
Launch_The_Dragons_Touch.py
Launch_The_Dragons_Touch.pyw
Create_Desktop_Shortcut.py
Create_Desktop_Shortcut.pyw
Launch_The_Dragons_Touch.bat
Create_Desktop_Shortcut.bat
README_START_HERE.txt
docs/alpha_access_launcher_v0.7.md
PATCH_NOTES_v0.7.7L.2.md
```

## Recommended Launch Path

```text
Primary: Launch_The_Dragons_Touch.pyw
```

The `.py` launcher is still present for command-line/manual fallback, but on development machines it may open in Visual Studio Code due to Windows file association.

## Shortcut Behavior

The preferred shortcut helper is now:

```text
Create_Desktop_Shortcut.pyw
```

It creates a Desktop shortcut pointing to:

```text
Launch_The_Dragons_Touch.pyw
```

It does not point to the `.bat` launcher.

## Batch Files

The `.bat` files remain in the project only as developer fallback wrappers:

```text
Launch_The_Dragons_Touch.bat
Create_Desktop_Shortcut.bat
```

They now clearly state that they are developer fallback files and forward toward the Python launcher/shortcut helper.

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

- Pass/Fail: `Launch_The_Dragons_Touch.pyw` exists in the project root.
- Pass/Fail: Double-clicking `Launch_The_Dragons_Touch.pyw` opens the desktop UI.
- Pass/Fail: Launcher does not require Visual Studio Code.
- Pass/Fail: Launcher does not automatically run deck analysis.
- Pass/Fail: Launcher starts from the project root correctly.

### Shortcut Helper

- Pass/Fail: `Create_Desktop_Shortcut.pyw` exists in the project root.
- Pass/Fail: Double-clicking `Create_Desktop_Shortcut.pyw` creates a Desktop shortcut.
- Pass/Fail: Desktop shortcut points to `Launch_The_Dragons_Touch.pyw`.
- Pass/Fail: Desktop shortcut opens the UI.
- Pass/Fail: Desktop shortcut does not silently run backend analysis.

### Batch Fallback Files

- Pass/Fail: `Launch_The_Dragons_Touch.bat` clearly says it is developer fallback only.
- Pass/Fail: `Create_Desktop_Shortcut.bat` clearly says it is developer fallback only.
- Pass/Fail: README no longer presents `.bat` as the recommended alpha path.

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
- Pass/Fail: Confirmed run still goes through `main.py`.
- Pass/Fail: Output folders are still generated normally.
- Pass/Fail: Report detection still works.
- Pass/Fail: Report Viewer still loads plain text.
