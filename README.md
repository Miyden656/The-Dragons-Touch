# The Dragon's Touch

The Dragon's Touch is a local Python-based Magic: The Gathering Commander deck-building and deck-review tool.

It analyzes Commander decklists, generates deck reports, and creates guided review prompts that help a player refine, cut down, build up, or complete a Commander deck while keeping the pilot's intent at the center of the process.

The tool is designed to support deck building, not replace player judgment. It aims to get a deck to a strong playable "70% solution," while final tuning, pet-card decisions, local-meta calls, and playstyle choices remain with the player.

---

## Current Development Status

Current checkpoint:

```text
v0.7.22 — Alpha Tester Feedback Packet
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

Current v0.7.22 status:

1. Modular UI foundation is passing.
2. Clean alpha ZIP extraction has passed.
3. Scryfall data recreation has passed.
4. `.pyw` launcher has passed without Visual Studio Code.
5. Single-deck smoke test has passed.
6. First ChatGPT alpha user review flow has passed.
7. Alpha tester feedback packet and AI follow-up prompt have been added.

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

## Scryfall Data Setup

The clean ZIP may omit the large local Scryfall cache file:

```text
data/scryfall_cards.json
```

If it is missing, recreate it by double-clicking:

```text
Download_Scryfall_Data.pyw
```

Command-line fallback:

```text
python download_scryfall_data.py
```

This requires an internet connection and recreates:

```text
data/scryfall_cards.json
```

Keep these files in the project root:

```text
download_scryfall_data.py
Download_Scryfall_Data.pyw
```

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
2. If `data/scryfall_cards.json` is missing, double-click `Download_Scryfall_Data.pyw`.
3. Double-click `Launch_The_Dragons_Touch.pyw`.
4. Select one Commander deck file.
5. Set Review Setup.
6. Set Philosophy Lens.
7. Set Collection Source.
8. Open Run Analysis.
9. Run `main.py` with guarded confirmation.
10. Open the generated report in Report Viewer.
11. Copy or save the generated report.
12. Run the generated report through AI follow-up review using:

```text
docs/alpha_ai_followup_prompt_v0.7.22.md
```

13. Send feedback using:

```text
docs/alpha_tester_feedback_packet_v0.7.22.md
```

## Sample Decklists and Alpha Test Decks

The alpha handoff package includes a small set of sample decklists in the `Decklists/` folder. These are included as known test cases, not as the only decks that can be reviewed.

Current sample deck purposes:

1. **Miirym Duplicate Legality Test**
   - Tests illegal duplicate reporting.
   - Includes two copies of `Life Finds a Way`.
   - Useful for confirming duplicate legality fixes appear before ordinary cut candidates.

2. **Phelia Bracket 2 Test**
   - Tests lower-power and bracket-sensitive review behavior.
   - Useful for checking whether the report respects a more casual intended table.

3. **Voja Build-Up Test**
   - Tests an incomplete deck that needs three more cards to become legal.
   - Useful for checking build-up / incomplete deck handling.

4. **Inga & Esika Companion Test**
   - Tests companion or companion-style restriction handling.
   - Useful for checking whether companion context survives preview, setup, and report generation.

5. **Toggo / Keskit Partner Test**
   - Tests partner commander handling.
   - Useful for checking landfall, artifact, token, and sacrifice package recognition.

Alpha testers should start with one included sample deck to confirm the workflow works. After that, testers are encouraged to add and test one of their own Commander decks.

## Adding Your Own Decklists

To test your own deck:

1. Export or copy your Commander decklist as plain text.
2. Save it as a `.txt` file.
3. Put the file in the `Decklists/` folder.
4. Launch The Dragon's Touch.
5. Select that deck from the Deck Selection page.

The included samples were created from Archidekt text exports, either by copying/pasting the exported text into a `.txt` file or downloading/exporting the deck as a `.txt` file.

Testers are welcome to try `.txt` decklist exports from other deckbuilding sites as well. This is useful alpha feedback.

If a decklist from another site does not load correctly, please report:

- the deckbuilding site used,
- whether the file was copied/pasted or downloaded,
- the file format if known,
- what The Dragon's Touch displayed,
- and any error messages or screenshots.

## Collection Files

The collection files included in this alpha package are based on my personal collection data.

Testers do not have to use them.

If testers want to test their own collection data, they may add their own collection files and select them from the Collection Source page.

Useful collection feedback includes:

- whether the collection file loads,
- whether the selected collection source is reflected in Run Analysis,
- whether collection-only behavior is understandable,
- whether collection-preferred behavior is understandable,
- and whether the final report appears to respect the selected collection mode.

## Alpha Testing Goal

The goal of this alpha is not only to confirm that the app works under perfect conditions. The goal is also to find confusing steps, bad assumptions, unsupported decklist formats, unclear report language, broken handoffs, and rough edges.

Trying to break the system is useful.

Please test:

- one included sample deck,
- one personal Commander deck if possible,
- one exported decklist from another deckbuilding site if possible,
- collection mode behavior if you have collection data,
- partner commanders,
- companion decks,
- incomplete decks,
- illegal duplicates,
- and any workflow that feels natural to you as a Commander player.

If something breaks, please send the decklist file if you are comfortable sharing it, screenshots of the issue, and a short explanation of what you expected to happen.

---

## Required Alpha Tester Workflow

Alpha testing should follow a complete dictated checklist. Testers should not have to guess what to do.

Required path:

```text
Extract ZIP
-> Download Scryfall data if needed
-> Launch app with Launch_The_Dragons_Touch.pyw
-> Select deck
-> Stage Review Setup
-> Stage Philosophy Lens
-> Stage Collection Source
-> Run Analysis with guarded confirmation
-> Confirm output folder/report detection
-> Open report in Report Viewer
-> Run generated report through AI follow-up review
-> Send feedback, generated report, AI review result, and any screenshots/errors
```

Use:

```text
docs/alpha_tester_feedback_packet_v0.7.22.md
```

for the full checklist.

---

## AI Follow-Up Review Requirement

The current alpha workflow includes an AI follow-up step after the app generates a report.

This helps test whether Dragon's Touch reports are clear enough to support an actual deck-review conversation.

Use:

```text
docs/alpha_ai_followup_prompt_v0.7.22.md
```

The AI follow-up should:

1. Confirm receipt of the generated report.
2. Summarize what the report says.
3. Identify commander, deck status, required cuts, strategy read, and review candidates.
4. Ask for pilot intent one section at a time.
5. Correct the strategy read if the pilot says the deck is trying to do something else.
6. Treat all recommendations as guidance, not automatic deck edits.
7. Respect legality, budget, collection mode, color identity, table power, and pilot intent.

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
13. AI-assisted report follow-up review.

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

Do not include tester-confusing developer fallback files unless intentionally making a developer backup:

```text
Launch_The_Dragons_Touch.bat
Launch_The_Dragons_Touch.py
Create_Desktop_Shortcut.bat
Create_Desktop_Shortcut.py
Create_Desktop_Shortcut.pyw
```

---

## What Alpha Testers Should Send Back

Alpha testers should send:

1. Whether the ZIP extracted cleanly.
2. Whether Scryfall data downloaded successfully.
3. Whether `Launch_The_Dragons_Touch.pyw` opened the app.
4. Whether a deck review completed.
5. Whether the report appeared in Report Viewer.
6. The generated report file.
7. The AI follow-up review result.
8. Any screenshots of errors.
9. Any confusing steps or unclear wording.
10. Any feature requests or quality concerns.

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
