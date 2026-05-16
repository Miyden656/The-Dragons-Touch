# v0.8.10.1-alpha — Alpha ZIP Handoff Cleanup and Smoke Test

## Purpose

This checkpoint prepares the post-lock Stable v0.8 build for alpha handoff packaging.

Stable v0.8 is already locked. This alpha pass is not feature work. Its goal is to make sure a tester can unzip the folder, launch the desktop app, run a deck review, and test optional Combo Awareness without needing to understand the development workflow.

## Alpha Handoff Rule

The GitHub repository and the alpha ZIP have different rules:

- The GitHub repository should not track huge local/generated combo data.
- The alpha ZIP may need to include generated local combo indexes so Combo Awareness works out of the box.

## Include in tester ZIP when possible

- Application source files.
- UI package and assets.
- `main.py` backend entry point.
- Decklists examples.
- Local collection folder if testers should test collection-aware behavior.
- Local Scryfall data required by the current backend.
- `data/commander_spellbook/combo_index.json` if testers should use Combo Awareness without building indexes.
- `data/commander_spellbook/combo_index_parity.json` if testers should use Dev-Facing parity/breakdown validation.

## Do not require alpha testers to do unless explicitly documented

- Download Scryfall data.
- Download Commander Spellbook data.
- Build combo indexes.
- Run audit scripts.
- Understand Dev-Facing Mode.
- Provide separate Combo Awareness files during AI handoff.

## Stable v0.8 lock remains intact

- Combo Awareness remains opt-in.
- No API calls are part of the normal run path.
- Report-section Combo Awareness embeds concise combo context in the normal deck report and AI handoff prompt.
- Breakdown files remain optional/dev-facing.
- User-Facing Mode remains default.
