# The Dragon's Touch

The Dragon's Touch is a local Python-based Magic: The Gathering Commander deck-building and deck-review tool.

It analyzes Commander decklists, generates deck reports, and creates guided review prompts that help a player refine, cut down, build up, or complete a Commander deck while keeping the pilot's intent at the center of the process.

The tool is designed to support deck building, not replace player judgment. It aims to get a deck to a strong playable "70% solution," while final tuning, pet-card decisions, local-meta calls, and playstyle choices remain with the player.

---

## Current Development Status

Current checkpoint:

```text
v0.7.21 — Alpha Tester README / Clean Setup Polish
```

Current build identity:

```text
The Dragon's Touch (Modular Alpha)
```

Stable base preserved:

```text
v0.6.8.5 — Stable v0.6 Lock
```

The v0.7 track is focused on Desktop UI Alpha Foundation / Alpha Hardening. It modularized the existing PySide6 desktop UI and preserved the stable backend workflow.

---

## Supported Alpha Launch Path

Use:

```text
Launch_The_Dragons_Touch.pyw
```

You do not need Visual Studio Code to open the app.

The `.bat` launchers are developer fallback only. Desktop shortcut support is deferred because Windows Smart App Control blocked shortcut/batch paths during testing.

Do not disable Smart App Control just to run this tool.

---

## Preserved Workflow Boundary

The UI does not replace the backend. The current workflow remains:

```text
UI staged state
-> guarded confirmation
-> subprocess/main.py
-> CLI input bridge
-> backend output folder
-> report detection
-> Report Viewer plain-text load
```

Do not bypass `main.py`. Do not silently execute backend commands. Do not create a second backend workflow.

---

## Quick Start

1. Open the project folder.
2. Double-click `Launch_The_Dragons_Touch.pyw`.
3. Select a Commander deck file.
4. Set Review Setup.
5. Set Philosophy Lens.
6. Set Collection Source.
7. Open Run Analysis.
8. Run `main.py` with guarded confirmation.
9. Open the generated report in Report Viewer.

---

## Local Scryfall Card Database

The large local Scryfall cache file is:

```text
data/scryfall_cards.json
```

Clean ZIPs may omit this file because it is very large.

If it is missing, recreate it from the project root:

```text
python download_scryfall_data.py
```

This requires an internet connection and recreates:

```text
data/scryfall_cards.json
```

Keep `download_scryfall_data.py` in the root project folder.

---

## What The Dragon's Touch Currently Does

The current alpha checkpoint supports:

1. Local single-deck Commander review.
2. Deck file selection and lightweight preview.
3. Review Setup staging.
4. Philosophy Lens staging.
5. Collection Source staging.
6. Guarded backend execution through `main.py`.
7. CLI input bridge handoff.
8. Unique timestamped output folders.
9. Report detection.
10. Plain-text Report Viewer loading.
11. User-facing boundaries for guidance versus automatic edits.
12. Duplicate legality first-pass reporting.

---

## Current Limits / Deferred Scope

The Dragon's Touch currently does not include:

1. Commander Spellbook/API integration.
2. Real Batch / Aggregate workflow.
3. Replacement Candidate Engine.
4. Deep markdown report rendering.
5. Installer or packaged executable.
6. Supported desktop shortcut creation.
7. Automatic deck edits.
8. Confirmed infinite-combo detection from an external database.

Batch / Aggregate and Commander Spellbook areas remain future/placeholder workspaces.

---

## Current UI Module Structure

The v0.7 modularization track split the desktop UI into these main areas:

```text
ui/
  constants.py
  dragons_touch_pyside6_workstation.py
  dragons_touch_pyside6_workstation_legacy_v0.6.8.5.py

  pages/
    collection_source_page.py
    deck_selection_page.py
    future_workspace_page.py
    philosophy_lens_page.py
    report_viewer_page.py
    review_setup_page.py
    run_analysis_page.py

  services/
    backend_runner.py
    cli_bridge.py
    report_detector.py

  state/
    staged_run_config.py

  styles/
    theme.py

  widgets/
    core.py
```

The active launch UI remains:

```text
ui/dragons_touch_pyside6_workstation.py
```

The v0.6.8.5 legacy UI copy remains available as a reference/fallback file.

---

## Clean ZIP Guidance

For a clean checkpoint/share ZIP, remove:

```text
__pycache__/
*.pyc
old patch ZIPs
old generated output runs
.git/ for share/checkpoint ZIPs
```

For a lean ZIP, omit:

```text
data/scryfall_cards.json
```

For a fully offline personal backup, keep:

```text
data/scryfall_cards.json
```

---

## Project Philosophy

The Dragon's Touch is a human-in-the-loop deck-building assistant.

It should:

1. Help the pilot understand what the deck is trying to do.
2. Identify cards that support the plan.
3. Identify cards that may be off-plan, redundant, replaceable, or worth reviewing.
4. Help incomplete decks move toward a legal 100-card Commander list.
5. Respect pet cards, protected cards, and emotional/theme choices.
6. Respect table intent and power expectations.
7. Avoid treating bracket pressure as automatic cuts.
8. Avoid treating the AI's first guess as more important than the user's stated plan.

Final decisions always belong to the player.


## v0.7.21 Launcher / Scryfall Setup Note

Alpha testers do not need Visual Studio Code. Visual Studio Code is only a development editor.

Supported launch path:

```text
Launch_The_Dragons_Touch.pyw
```

If the clean ZIP does not include `data/scryfall_cards.json`, recreate it by double-clicking:

```text
Download_Scryfall_Data.pyw
```

Command-line fallback:

```text
python download_scryfall_data.py
```

The `.pyw` launcher is self-contained as of v0.7.21 and should not require `Launch_The_Dragons_Touch.py` to be present in the tester ZIP.
