# The Dragon's Touch v0.7.7L.3 — Launcher Scope Correction

## Purpose

Correct the v0.7 alpha access plan after Windows Smart App Control blocked the Desktop shortcut path.

## Result

The supported v0.7 alpha launch path is now only:

```text
Launch_The_Dragons_Touch.pyw
```

Desktop shortcut support is deferred until the later packaging/installer track.

## Why

- `.pyw` launcher passed and opened The Dragon's Touch without Visual Studio Code.
- `.bat` launcher was blocked by Smart App Control.
- Desktop shortcut path was also blocked by Smart App Control.
- A blocked shortcut makes the app look suspicious to testers.
- v0.7 should not ask testers to disable Windows security features.

## Files Changed

```text
README_START_HERE.txt
docs/alpha_access_launcher_v0.7.md
Create_Desktop_Shortcut.py
Create_Desktop_Shortcut.pyw
Create_Desktop_Shortcut.bat
Launch_The_Dragons_Touch.bat
PATCH_NOTES_v0.7.7L.3.md
```

## What Changed

- README now says `.pyw` is the supported v0.7 alpha launch path.
- Desktop shortcut support is clearly marked deferred.
- Shortcut helper files are experimental/developer-only.
- `Create_Desktop_Shortcut.py/.pyw` now shows a defer message instead of creating a shortcut.
- `.bat` files remain developer fallback only.

## What Did Not Change

This patch does not change:

- `main.py`
- UI behavior
- backend execution
- guarded confirmation
- CLI bridge behavior
- output folder behavior
- report detection
- Report Viewer
- Commander Spellbook/API
- Batch/Aggregate
- Replacement Candidate Engine

## Test Checklist

### Launcher

- Pass/Fail: `Launch_The_Dragons_Touch.pyw` opens the desktop UI.
- Pass/Fail: Launcher does not require Visual Studio Code.
- Pass/Fail: Launcher does not automatically run deck analysis.

### Shortcut Scope Correction

- Pass/Fail: `README_START_HERE.txt` says `.pyw` is the supported alpha launch path.
- Pass/Fail: `README_START_HERE.txt` says Desktop shortcut support is deferred.
- Pass/Fail: `Create_Desktop_Shortcut.pyw` does not create a shortcut and instead shows the deferred message.
- Pass/Fail: `.bat` files are labeled developer fallback only.

### Normal UI Workflow

- Pass/Fail: Deck Selection opens.
- Pass/Fail: Review Setup opens.
- Pass/Fail: Philosophy Lens opens.
- Pass/Fail: Collection Source opens.
- Pass/Fail: Run Analysis opens.
- Pass/Fail: Report Viewer opens.

### Backend Workflow Preservation

- Pass/Fail: Guarded confirmation still appears.
- Pass/Fail: Confirmed run still goes through `main.py`.
- Pass/Fail: Output folders are still generated normally.
- Pass/Fail: Report detection still works.
- Pass/Fail: Report Viewer still loads plain text.
