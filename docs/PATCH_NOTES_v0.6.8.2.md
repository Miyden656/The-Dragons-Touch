# Patch v0.6.8.2 — Final Report Wording Cleanup + Prompt Carry-Forward Cleanup

## Purpose
Polish generated prompt/report wording while preserving v0.6.7 locked UI behavior and v0.6.8.1.1 prompt formatting improvements.

## Changed Files
- `main.py`
- `config.py`
- `reports/prompt_builder.py`
- `reports/report_builder.py`
- `ui/dragons_touch_pyside6_workstation.py`

## Prompt Carry-Forward Cleanup
- Removed the repeated Section 1 review-outcome confirmation question.
- Renumbered Section 1 for cut-down and build-up flows.
- Cut-down Section 1 now asks the pilot to confirm/correct the staged Review Intensity.
- Build-up Section 1 now asks the pilot to confirm/correct the staged Build-Up Mode.
- Restored Section 5 Game Changer / fast mana / tutor / free interaction question to clean numbered choices:
  - `1 = Yes.`
  - `2 = No.`
  - `3 = Some / case-by-case.`
  - `4 = Explain.`
- Preserved indented answer-choice formatting.
- Preserved interactive one-section-at-a-time behavior.
- Preserved one-shot worksheet behavior.

## Report Wording Cleanup
- Added clearer wording that required cuts are legality/deck-size pressure, not generic optimization.
- Renamed `Required Cut Candidates` to `Required Cut / Legality Review Candidates`.
- Renamed `Optional Optimization Cut Candidates` to `Optional Optimization Review Candidates`.
- Added language clarifying optional cuts are not mandatory.
- Added duplicate legality note so illegal duplicates are reviewed before treating non-duplicate candidates as mandatory.
- Added intended bracket and budget note to Run Settings when present in runtime config.
- Reduced internal/refactor wording in the normal report opening note.
- Replaced “bad recommendation” wording with “weak or off-plan recommendation.”

## UI Update
- Updated UI version to `v0.6.8.2`.
- Updated UI phase to `Final Report Wording Cleanup + Prompt Carry-Forward Cleanup`.
- Preserved the v0.6.7 locked desktop UI foundation behavior.
- Added guarded-run environment handoff for:
  - `MTG_BUDGET_NOTE`
  - `MTG_INTENDED_BRACKET`

## Not Changed
- No legality logic changes.
- No strategy scoring changes.
- No cut scoring changes.
- No replacement scoring changes.
- No collection matching changes.
- No output folder routing changes.
- No Batch / Aggregate real workflow.
- No Commander Spellbook/API integration.
- No deep markdown rendering.
