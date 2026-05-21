# The Dragon's Touch v0.10 Stable Lock

## Stable lock status

v0.10.8-dev is the v0.10 stable lock package.

This release locks the v0.10 development line after the Interface Mode architecture cleanup and the combo always-on regression chain.

## Major locked work

### Interface Mode Architecture Cleanup

- Brand-new users default to User Mode.
- Developer Mode is explicit and Settings-controlled.
- Developer Mode has a visible indicator.
- User Mode / Developer Mode visibility is separated across the app.
- Collection Source page is removed from active navigation.
- Batch Tools page is removed from active navigation.
- Settings now owns app-wide defaults.
- Review Setup owns current-run choices.
- Guide Presentation lives in Settings.
- Collection Source defaults live in Settings.
- Collection Mode lives in Review Setup.
- Deck Selection supports Select File, Paste Decklist, and Import Link placeholder.
- Current Deck Context remains preserved.
- Run Analysis has a cleaner User Mode and fuller Developer Mode.
- Report Viewer has User Mode AI Handoff and Developer Mode report diagnostics.

### Combo Analysis Always-On

- Combo analysis is no longer optional.
- Combo Analysis is always included when combo data is available.
- Backend combo awareness remains always enabled.
- Backend and CLI request both combo artifacts.
- Review Setup no longer exposes Combo Awareness as a Yes/No toggle.
- Report Viewer keeps the Combos section.
- Generated reports no longer call Combo Awareness optional.
- Missing-card combo optimization remains opt-in.

## v0.10 stable lock verifier

Run:

```powershell
py tools\verify_v0.10.8_v0.10_stable_lock.py
```

Expected final line:

```text
PASS — v0.10.8 v0.10 stable lock verification is clean.
```

## Recommended real-run check

Run one normal deck review, then run:

```powershell
Select-String -Path "Outputs\**\**\*_deck_report.md" -Pattern "combo analysis is always part of The Dragon's Touch","optional section was added" -SimpleMatch
```

Expected for new reports:

- The new always-included wording appears.
- The old optional wording does not appear.

## What v0.10.8 does not change

- No new recommendation logic.
- No new cut logic.
- No new replacement ranking logic.
- No new collection parsing logic.
- No new combo matching logic.
- No new external API behavior.
- No automatic swap behavior.
- No live price checking.
