# PATCH NOTES — v0.7.18 Alpha Tester Packaging Readiness Audit

## Patch Type

Documentation / readiness audit only.

## Purpose

Record the packaging-readiness concerns before any executable or installer work begins.

This patch exists to keep the project from jumping too early into PyInstaller, installer creation, shortcut creation, or signed release work before the v0.7 modular alpha flow is fully stable.

## Files Added

```text
docs/packaging_readiness_audit_v0.7.md
PATCH_NOTES_v0.7.18.md
```

## Runtime Code Changed

None.

## Runtime Behavior Changed

None.

## Preserved Workflow

```text
UI staged state
-> guarded confirmation
-> subprocess/main.py
-> CLI input bridge
-> backend output folder
-> report detection
-> Report Viewer plain-text load
```

## Key Decisions Recorded

- `Launch_The_Dragons_Touch.pyw` remains the supported v0.7 alpha launch path.
- `.bat` launchers remain developer fallback only.
- Desktop shortcut support remains deferred.
- Packaging is not being performed in v0.7.18.
- Future packaging must preserve guarded `main.py` execution.
- Future packaging must handle local data, outputs, deck files, collection files, and report detection.
- `data/scryfall_cards.json` may be omitted from clean ZIPs if `download_scryfall_data.py` is included in the project root.

## Scope Not Included

- No PyInstaller work.
- No installer work.
- No signing work.
- No desktop shortcut work.
- No backend refactor.
- No UI behavior changes.
- No Commander Spellbook/API integration.
- No Batch/Aggregate real workflow.
- No Replacement Candidate Engine.
- No deep markdown renderer.

## Test Checklist

### File Check

- Pass/Fail: `docs/packaging_readiness_audit_v0.7.md` exists.
- Pass/Fail: `PATCH_NOTES_v0.7.18.md` exists.

### Content Check

- Pass/Fail: Audit states `.pyw` is the supported alpha launch path.
- Pass/Fail: Audit states desktop shortcut support is deferred.
- Pass/Fail: Audit states `.bat` launchers are developer fallback only.
- Pass/Fail: Audit preserves the guarded `main.py` workflow boundary.
- Pass/Fail: Audit includes Scryfall JSON/download script guidance.
- Pass/Fail: Audit includes packaging risk checklist.

### Smoke Test

Because this is documentation-only, runtime smoke testing is optional but recommended:

- Pass/Fail: `Launch_The_Dragons_Touch.pyw` opens the app.
- Pass/Fail: Deck Selection opens.
- Pass/Fail: Run Analysis opens.
- Pass/Fail: Report Viewer opens.

## Recommended Next Step

Stop for the night with the clean v0.7.18 packaging-readiness checkpoint.

Next session, choose one:

```text
v0.7.19 — Small UI User-Facing Polish Pass
```

or

```text
v0.7.19 — Alpha Tester QA Checklist / Feedback Form Prep
```
