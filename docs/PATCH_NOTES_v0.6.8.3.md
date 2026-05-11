# Patch v0.6.8.3 — Final User-Facing Boundary Cleanup

Purpose:
- Clarify final player-facing boundaries before the stable v0.6 lock.
- Preserve v0.6.8.2.1 unique timestamped output-folder routing.
- Preserve v0.6.8.2 prompt/report wording polish.

Changed files:
- main.py
- reports/prompt_builder.py
- reports/report_builder.py
- ui/dragons_touch_pyside6_workstation.py

Changes made:
- Updated backend version label to v0.6.8.3.
- Updated UI version/phase to v0.6.8.3 — Final User-Facing Boundary Cleanup.
- Added a normal-report User-Facing Boundaries section.
- Clarified that reports are guidance, not automatic deck edits.
- Clarified required cuts vs optional optimization candidates.
- Clarified that legality issues outrank ordinary cut candidates.
- Clarified collection-mode boundaries.
- Clarified that philosophy/persona language does not override legality, pilot intent, budget, collection mode, color identity, or deck evidence.
- Clarified Commander Spellbook/API remains disabled and future opt-in only.
- Clarified Report Viewer remains plain-text loading, not deep markdown parsing.
- Added Duplicate Legality First-Pass Fixes before Required Cut / Legality Review Candidates.
- Duplicate-copy fixes now appear before ordinary required cut candidates when illegal duplicates exist.
- Did not change legality logic, cut scoring, replacement scoring, strategy detection, collection matching, or output routing.

Expected duplicate behavior:
- If a deck has an illegal duplicate such as Life Finds a Way x2 and also has required cuts, the report surfaces the extra duplicate copy as a first-pass legality/deck-size fix before listing ordinary required cut candidates.

Regression boundaries:
- Commander Spellbook/API calls remain disabled.
- Report Viewer remains plain text only.
- Batch / Aggregate remains placeholder/future workspace.
- CLI/main.py remains source of truth.
