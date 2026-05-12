# PATCH NOTES — v0.7.20

## Patch Name

v0.7.20 — Alpha Tester Readiness Lock Candidate

## Patch Type

Documentation / checkpoint only.

## Purpose

Create a clean alpha readiness checkpoint after the v0.7 modularization, launcher cleanup, clean setup documentation, packaging readiness audit, and user-facing polish passes.

This patch prepares the project for a limited handoff to 1–2 trusted alpha testers without changing runtime behavior.

## Files Added

```text
docs/v0.7.20_alpha_tester_readiness_lock_candidate.md
docs/alpha_tester_handoff_checklist_v0.7.md
PATCH_NOTES_v0.7.20.md
```

## Runtime Code Changes

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

## Active Alpha Launch Path

```text
Launch_The_Dragons_Touch.pyw
```

## Deferred Scope

- Commander Spellbook/API integration.
- Real Batch / Aggregate workflow.
- Replacement Candidate Engine.
- Deep markdown rendering.
- Packaged executable.
- Installer.
- Desktop shortcut support.
- Automatic deck edits.
- Silent backend execution.

## Test Checklist

### File Check

- Pass/Fail: `docs/v0.7.20_alpha_tester_readiness_lock_candidate.md` exists.
- Pass/Fail: `docs/alpha_tester_handoff_checklist_v0.7.md` exists.
- Pass/Fail: `PATCH_NOTES_v0.7.20.md` exists.

### Content Check

- Pass/Fail: Lock candidate doc preserves the guarded `main.py` workflow boundary.
- Pass/Fail: Lock candidate doc says `.pyw` is the supported alpha launch path.
- Pass/Fail: Lock candidate doc says desktop shortcut support is deferred.
- Pass/Fail: Lock candidate doc includes Scryfall JSON/downloader guidance.
- Pass/Fail: Handoff checklist includes launch, navigation, full workflow, and boundary checks.
- Pass/Fail: Handoff checklist is suitable for 1–2 trusted testers.

### Optional Smoke Test

- Pass/Fail: `Launch_The_Dragons_Touch.pyw` opens the app.
- Pass/Fail: Deck Selection opens.
- Pass/Fail: Run Analysis opens.
- Pass/Fail: Report Viewer opens.

## Expected Status After Passing

```text
v0.7.20 — Alpha Tester Readiness Lock Candidate
Status: Passed
Decision: Safe to create a clean alpha tester handoff ZIP for 1–2 trusted testers.
```
