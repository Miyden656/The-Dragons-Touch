# v0.8.10.1-alpha — Alpha ZIP Contents Checklist

Use this before compressing the tester ZIP.

## Required launch/runtime files

- [ ] `main.py`
- [ ] `ui/`
- [ ] `combo_awareness/`
- [ ] Active backend helper modules used by `main.py`
- [ ] UI assets/helper dragon art, if stored separately
- [ ] Example `Decklists/`

## Local data for pickup-and-go testing

- [ ] Active Scryfall card data file is present.
- [ ] `data/commander_spellbook/combo_index.json` is present if Combo Awareness should work without setup.
- [ ] `data/commander_spellbook/combo_index_parity.json` is present if Dev-Facing breakdown/parity checks should work.
- [ ] `collection/` is present if testers should test collection-first behavior.

## Exclude from tester ZIP unless intentionally needed

- [ ] Old failed patch scripts.
- [ ] Old Do not use folders unless deliberately archived outside the release ZIP.
- [ ] Prior output folders.
- [ ] Personal/private collection files if they should not be shared.
- [ ] Large raw `data/combo.json` unless testers need to rebuild indexes.

## Smoke-test after extracting ZIP

- [ ] Extract to a fresh folder with a simple path.
- [ ] Launch the app from the extracted folder.
- [ ] Run one Combo Awareness Disabled review.
- [ ] Run one Combo Awareness Report Section review.
- [ ] Confirm Report Viewer opens.
- [ ] Confirm report-section Combo Awareness appears in deck report and prompt.
- [ ] Confirm no API calls.
