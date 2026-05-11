# Patch v0.6.8.5 — Stable v0.6 Lock

## Purpose

Formally lock stable v0.6 after the v0.6.8.4 regression pass succeeded.

## Changes

- Updated backend version label to `v0.6.8.5 — Stable v0.6 Lock`.
- Updated UI version/phase to `v0.6.8.5 — Stable v0.6 Lock`.
- Added a Settings-page Stable v0.6 Lock note.
- Preserved the v0.6.8.4 regression checklist as a completed checkpoint.
- Preserved v0.6.8.3 user-facing boundary cleanup.
- Preserved v0.6.8.2.1 unique timestamped output-folder routing.
- Preserved guarded `main.py` execution and CLI/main.py source-of-truth behavior.

## Locked stable v0.6 behavior

- Single-deck desktop UI foundation is locked.
- Guarded main.py execution is locked.
- Backend unique timestamped output folders are locked.
- Deck filename distinction in output folders is locked.
- Report detection and plain-text Report Viewer loading are locked.
- Prompt/report wording polish is locked.
- User-facing boundaries are locked.
- Duplicate legality first-pass wording is locked.
- Commander Spellbook/API calls remain disabled and future opt-in only.
- Batch / Aggregate remains placeholder/future workspace.

## No behavior changes

This patch does not change legality logic, strategy detection, cut scoring, replacement scoring, collection matching, output routing, Commander Spellbook/API behavior, Batch/Aggregate behavior, or markdown rendering.

## Next roadmap step

`v0.7 — Desktop UI Alpha Foundation / Alpha Hardening`

v0.7 builds on the locked v0.6 foundation. It is not a rebuild from scratch.
