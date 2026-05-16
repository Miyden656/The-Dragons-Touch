# v0.8.9.8-dev — Dev-Facing Protection Boundary Notes

## Purpose

This patch adds a visible boundary around Dev-Facing Mode while keeping it accessible for active development.

## User-Facing Mode

- Remains the default.
- Keeps normal/player-facing workflows clean.
- Keeps Advanced Run Details hidden.
- Keeps Report Viewer focused on normal reports.

## Dev-Facing Mode

- Remains available for active development and trusted alpha testing.
- Shows advanced run details, runtime/bridge diagnostics, breakdown reports, and combo debugging artifacts.
- Is clearly labeled as developer/testing-only.

## Future protection requirement

Before beta, public preview, or v1.0, Dev-Facing Mode should be hidden, gated, or otherwise protected so normal users cannot accidentally open developer-only diagnostics.

## Scope Guard

- No backend changes.
- No main.py changes.
- No combo matcher changes.
- No parser changes.
- No index-builder changes.
- No API calls.
- No automatic Combo Awareness enabling.
- No combo recommendations.
