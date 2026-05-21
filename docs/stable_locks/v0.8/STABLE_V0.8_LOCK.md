# v0.8.10-dev — Stable v0.8 Lock

## Stable v0.8 Status

The Dragon's Touch v0.8 is locked as a stable local alpha milestone.

This lock means:

- The desktop UI can run a normal Commander deck review through the guarded `main.py` backend path.
- User-Facing Mode is the default interface mode.
- Dev-Facing Mode remains available for active development and deeper diagnostics.
- Run Analysis hands off to Report Viewer after successful runs.
- Combo Awareness remains optional and local-only.
- Opt-in Combo Awareness report-section modes embed concise combo context into the normal deck report and AI handoff prompt.
- Users do not need to provide separate combo documents to the AI interactive prompt when report-section Combo Awareness is selected.
- Full breakdown files remain optional/dev-facing support artifacts.
- No Commander Spellbook/API calls are part of the normal run path.
- Large local combo data and generated combo indexes are protected from Git tracking by `.gitignore`.

## Confirmed v0.8 Capabilities

### Core Review Flow

- Deck Selection works.
- Review Setup works.
- Philosophy Lens guidance works as framing only.
- Collection Source is optional and does not block normal reviews.
- Run Analysis works through the guarded backend path.
- Report Viewer opens after successful runs.

### User / Dev Mode Boundary

- User-Facing Mode is the default.
- User-Facing Mode hides Advanced Run Details.
- Dev-Facing Mode exposes advanced run details and breakdown reports.
- Dev-Facing Mode is labeled as developer/testing-only and should be hidden, gated, or protected before beta/public/v1.0.

### Combo Awareness

- Disabled mode writes no combo artifacts and does not affect the normal report or prompt.
- Report Section only mode writes `normal/combo_awareness_report_section.md`, appends Combo Awareness to the normal deck report, and appends the Combo Awareness AI Handoff Addendum to the user-guided prompt.
- Full Debug Breakdown only mode writes `debug/combo_awareness_breakdown.md` and does not affect the normal report or prompt.
- Both mode writes both artifacts and updates the normal report/prompt.
- Report-section modes include relevant potential combo counts.
- Report-section modes include collection-completable potential combo counts or a collection-not-loaded note.
- Combo findings are informational by default, not automatic recommendations.

## Stable v0.8 Boundaries

Stable v0.8 does not include:

- Live Commander Spellbook/API calls.
- Real batch processing.
- Full replacement candidate engine.
- Deep human-readable report rendering.
- Public/beta-grade Dev-Facing Mode protection.
- Automatic combo recommendations.
- Persistent user settings beyond current app behavior.

## Post-Lock Alpha Handoff Work

After this lock, the next work should happen in a post-lock alpha packaging lane.

Recommended next milestone:

`v0.8.10.1-alpha — Alpha ZIP Handoff Cleanup and Smoke Test`

Primary post-lock alpha goals:

1. Copy the locked project into a clean alpha handoff folder.
2. Remove failed patch scripts and old dev clutter.
3. Confirm required runtime data is included in the ZIP even if it is gitignored.
4. Confirm testers do not need to download combo or Scryfall data manually.
5. Confirm the app launches from a fresh extracted folder.
6. Confirm Run Analysis works from the fresh extracted folder.
7. Confirm Combo Awareness works locally from the fresh extracted folder.
8. Create the alpha ZIP.
9. Extract the ZIP somewhere clean and smoke test it before sending.

## Release Packaging Warning

GitHub rules and alpha ZIP rules are different:

- GitHub should not track huge generated combo data/index files.
- The alpha ZIP may need to include generated combo index files if Combo Awareness should work out of the box for testers.

Do not assume that `.gitignore` means a file should be absent from the tester ZIP.
