# v0.8.9.11-dev — Stable v0.8 Candidate Cleanup

## Purpose

This patch is a cleanup/stabilization checkpoint before the stable v0.8 candidate regression pass.

## Stable v0.8 Candidate Definition

Stable v0.8 should confirm that The Dragon's Touch can run a clean local Commander deck review through the desktop UI, optionally include local Combo Awareness in the normal deck report and AI handoff prompt, keep deeper breakdowns available for development/testing, and present a cleaner User-Facing Mode by default without making API calls or bypassing `main.py`.

## Locked Behaviors From Recent Passes

- User-Facing Mode remains the default interface mode.
- Dev-Facing Mode remains available for active development/testing.
- Dev-Facing Mode is labeled as developer/testing-only and should be hidden, gated, or protected before beta/public/v1.0.
- Run Analysis still executes through the guarded `main.py` path.
- Report Viewer opens after successful runs.
- Combo Awareness remains opt-in.
- Disabled Combo Awareness writes no combo artifacts and does not alter normal report/prompt output.
- Report-section Combo Awareness embeds concise Combo Awareness in the normal deck report and AI handoff prompt.
- Full Debug Breakdown only remains dev-facing and does not alter normal report/prompt output.
- Both mode writes both artifacts and embeds the concise Combo Awareness section in normal handoff output.
- No API calls are part of the current run path.

## Large File / Git Hygiene

The following generated or oversized local combo files should stay ignored and should not be committed:

```text
data/combo.json
data/Combo.json
data/commander_spellbook/combo_index.json
data/commander_spellbook/combo_index_parity.json
```

## What This Patch Does

- Updates known version labels from v0.8.9.10.1-dev / v0.8.9.10-dev to v0.8.9.11-dev where present.
- Adds missing `.gitignore` protections for local combo data, generated indexes, output folders, and local-only working docs.
- Writes this cleanup note into `docs/`.
- Runs compile checks against key backend/UI/combo-awareness files that exist in the local tree.
- Prints cleanup candidates for manual review without moving or deleting active files.

## What This Patch Does Not Do

- No feature changes.
- No backend behavior changes.
- No combo matcher logic changes.
- No parser changes.
- No index-builder changes.
- No API calls.
- No automatic combo recommendations.
- No deletion or movement of files.
