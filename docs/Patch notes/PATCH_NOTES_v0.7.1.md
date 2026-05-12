# Patch Notes — v0.7.1

## Patch Name
v0.7.1 — UI Structure Audit / Refactor Map Refinement

## Purpose
This is a no-runtime-behavior-change planning patch. It refines the v0.7 UI modularization plan after the v0.7.0 baseline passed user testing.

## Files Added/Updated
- `docs/ui_refactor_map_v0.7.md`
- `docs/ui_refactor_test_matrix_v0.7.md`

## What Changed
- Expanded the UI refactor map with line-level section inventory.
- Documented MainWindow method clusters and extraction risks.
- Added a patch-by-patch test matrix for v0.7 modularization.
- Preserved the launcher/access track as part of v0.7 Alpha Hardening.

## Runtime Behavior
No runtime behavior should change.

## Backend Behavior
No backend behavior changed.

## Guardrails Preserved
- Do not bypass `main.py`.
- Do not silently execute backend commands.
- Do not create a second backend workflow.
- Do not remove guarded confirmation.
- Do not introduce Commander Spellbook/API calls.
- Do not introduce Replacement Candidate Engine behavior.
- Do not introduce Batch/Aggregate real workflow yet.
- Do not introduce deep markdown rendering.

## Next Recommended Patch
v0.7.2 — Constants and Version Labels Extraction

This should create `ui/constants.py` and move low-risk labels/options/constants out of the main one-script UI while preserving identical behavior.
