# PATCH NOTES — v0.7.21

## Patch

v0.7.21 — Alpha Launcher / Scryfall Setup Repair

## Type

Launcher/documentation repair.

## Reason

The cleaned alpha tester ZIP removed `Launch_The_Dragons_Touch.py`, but `Launch_The_Dragons_Touch.pyw` still imported it. Because `.pyw` launches without a console, the failure appeared as if nothing happened.

The user also needed a way for alpha testers to recreate Scryfall data without opening Visual Studio Code.

## Changes

- Replaced `Launch_The_Dragons_Touch.pyw` with a self-contained launcher.
- Added `Download_Scryfall_Data.pyw` as a no-console Scryfall data setup helper.
- Updated `README_START_HERE.txt`.
- Updated `README.md`.
- Added `docs/alpha_launcher_scryfall_setup_v0.7.21.md`.

## Not Changed

- No changes to `main.py`.
- No changes to UI behavior.
- No changes to backend analysis.
- No changes to guarded confirmation.
- No changes to output folders or reports.
- No Commander Spellbook/API work.
- No Batch/Aggregate work.
- No Replacement Candidate Engine work.

## Test Checklist

- `Launch_The_Dragons_Touch.pyw` opens the app from the clean tester ZIP.
- The app opens without requiring `Launch_The_Dragons_Touch.py`.
- The app does not require Visual Studio Code.
- `Download_Scryfall_Data.pyw` appears in the root folder.
- `Download_Scryfall_Data.pyw` can recreate `data/scryfall_cards.json`.
- Guarded run behavior remains unchanged.
