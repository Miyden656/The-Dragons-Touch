# Patch v0.6.8.4 — Stable v0.6 Regression Pass

Purpose: add the stable-v0.6 regression checkpoint and update version labels without changing feature behavior.

Updated files:
- main.py
- reports/prompt_builder.py
- ui/dragons_touch_pyside6_workstation.py

Included unchanged for safe full-file replacement:
- config.py
- reports/report_builder.py
- reports/debug_sections.py
- app_io/output_writer.py

Changes made:
- Updated backend version label to v0.6.8.4 — Stable v0.6 Regression Pass.
- Updated UI version/phase to v0.6.8.4 — Stable v0.6 Regression Pass.
- Added a Settings-page Stable v0.6 Regression Pass checklist.
- Preserved v0.6.8.3 user-facing boundary cleanup.
- Preserved v0.6.8.2.1 unique timestamped output folder routing.
- Preserved guarded main.py execution and CLI source-of-truth behavior.

No behavior changes:
- No legality logic changes.
- No strategy detection changes.
- No cut/replacement scoring changes.
- No collection matching changes.
- No Commander Spellbook/API integration.
- No Batch/Aggregate workflow.
- No deep markdown rendering.

Regression targets:
- Cut-down deck.
- Build-up deck.
- Duplicate legality deck.
- Companion deck if available.
- Partner commander deck if available.
- No collection mode.
- Collection only mode.
- Normal, Debug, and Both output modes.
- Report Viewer plain-text loading.
- Unique timestamped output folders.
- Commander Spellbook/API disabled boundary.
