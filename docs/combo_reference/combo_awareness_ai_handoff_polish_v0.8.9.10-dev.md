# v0.8.9.10-dev — Combo Awareness AI Handoff Polish + Final Report Viewer Regression

## Purpose

This patch polishes the v0.8.9.9.1-dev Combo Awareness AI handoff behavior and locks the intended final v0.8 direction:

- If Combo Awareness is disabled, the normal report and AI prompt stay clean.
- If report-section mode is selected, the normal deck report and user-guided prompt contain enough Combo Awareness context for AI handoff.
- Separate combo files remain optional support/dev artifacts.
- Full breakdown-only mode remains dev-facing and does not pollute normal report or prompt output.

## Stable v0.8 requirement confirmed

Opt-in Combo Awareness must be fully useful from the normal deck report / AI handoff prompt without requiring the user to provide separate combo documents.

## User-facing Report Viewer future note

Before beta/public v1.0, the Report Viewer should gain a more human-readable Simple View / Full Report View structure so normal players can understand the report without reading dense AI-oriented markdown.

## Files changed by script

- `main.py`
- `ui\constants.py`
- `combo_awareness\reporting.py`
- `combo_awareness\main_hook.py`

## Scope guard

- No API calls.
- No parser changes.
- No index-builder changes.
- No combo matcher logic changes.
- No automatic combo recommendations.
- Combo Awareness remains opt-in.
