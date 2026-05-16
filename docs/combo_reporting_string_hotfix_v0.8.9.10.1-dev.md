# v0.8.9.10.1-dev — Combo Awareness Reporting String Hotfix

## Purpose

This hotfix repairs the failed v0.8.9.10-dev polish patch where a report-section note was inserted as an unterminated Python string literal in `combo_awareness/reporting.py`.

## Files changed by script

- `combo_awareness\reporting.py`
- `main.py`
- `combo_awareness\main_hook.py`
- `combo_awareness\reporting.py`
- `ui\constants.py`

## Scope guard

- No API calls.
- No combo matcher logic changes.
- No parser changes.
- No index-builder changes.
- Combo Awareness remains opt-in.
