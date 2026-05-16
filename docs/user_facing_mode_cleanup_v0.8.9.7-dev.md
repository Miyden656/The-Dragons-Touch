# v0.8.9.7-dev — User-Facing Mode Cleanup + User/Dev Regression Notes

## Purpose

This patch folds the User/Dev mode checkpoint into a real UI cleanup pass.

## Scope

- User-Facing Mode remains the default.
- User-Facing Mode keeps Run Analysis focused on the normal player workflow.
- Dev-Facing Mode keeps advanced diagnostics, runtime previews, bridge details, and breakdown reports available for active development.
- Report Viewer keeps normal reports prominent in User-Facing Mode.
- Breakdown/debug report visibility remains Dev-Facing Mode behavior.
- Combo Awareness remains opt-in.
- No API calls are introduced.

## Regression notes

Expected pass behavior:

- App launches.
- UI version shows `v0.8.9.7-dev`.
- Settings still shows Interface Mode.
- User-Facing Mode is the default.
- User-Facing Mode does not expose Advanced Run Details on Run Analysis.
- Dev-Facing Mode exposes Advanced Run Details.
- User-Facing Mode keeps Report Viewer focused on normal/player-facing reports.
- Dev-Facing Mode shows Breakdown Reports.
- Run Analysis still works.
- Successful runs still open Report Viewer.
- Combo Awareness disabled/report-section/both modes still work.
- No API calls.

## Future protection note

Dev-Facing Mode remains visible for active development in v0.8.9.7-dev. Before beta/public release, Dev-Facing Mode should be protected, hidden, or intentionally unlocked by a developer-only setting.
