# PATCH NOTES — v0.7.19

## Patch

v0.7.19 — Small UI User-Facing Polish Pass

## Type

Low-risk UI wording / alpha-tester clarity patch.

## Changed

- Updated visible app version to `v0.7.19`.
- Updated phase label to `Modular Alpha / User-Facing Polish`.
- Clarified header/footer/sidebar wording for alpha testers.
- Replaced outdated `mock data` and disconnected-backend wording with current guarded workflow wording.
- Clarified Review Setup settings as guidance only, not automatic deck edits.
- Clarified Philosophy Lens boundaries.
- Clarified Collection Source honesty boundaries.
- Clarified Run Analysis as active guarded `main.py` execution, not silent execution.
- Clarified Report Viewer as plain-text viewing only.
- Marked Batch / Aggregate as `Future / Not Active Yet`.
- Updated Settings/checkpoint labels toward v0.7 modular alpha wording.
- Added `docs/ui_user_facing_polish_v0.7.19.md`.

## Not changed

- `main.py`
- backend logic
- guarded confirmation behavior
- CLI bridge mapping
- output folder behavior
- report detection behavior
- Report Viewer plain-text behavior
- Commander Spellbook/API status
- Batch/Aggregate real workflow
- Replacement Candidate Engine
- deep markdown rendering

## Preserved workflow

UI staged state -> guarded confirmation -> subprocess/main.py -> CLI input bridge -> backend output folder -> report detection -> Report Viewer plain-text load
