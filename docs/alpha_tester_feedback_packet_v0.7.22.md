# The Dragon's Touch v0.7.22 — Alpha Tester Feedback Packet

## Purpose

This alpha test is not just checking whether the app opens. It is checking whether a trusted tester can complete the full Dragon's Touch workflow from a clean handoff ZIP through an AI-assisted review without needing the developer to explain each step.

The tester should follow the checklist exactly and report what happened.

## Current Alpha Scope

Active in this alpha:

- Single-deck Commander review
- PySide6 desktop UI
- Clean `.pyw` app launcher
- Scryfall data download helper
- Deck file selection
- Review Setup staging
- Philosophy Lens staging
- Collection Source staging
- Guarded `main.py` backend execution
- Timestamped output folder generation
- Report detection
- Plain-text Report Viewer
- AI follow-up review using the generated report

Not active yet:

- Commander Spellbook / API combo lookup
- Real Batch / Aggregate workflow
- Replacement Candidate Engine
- Deep markdown rendering
- Packaged installer
- Desktop shortcut support
- Automatic deck editing

## Tester Setup Instructions

1. Extract the alpha candidate ZIP into a fresh folder.
2. Open the extracted folder.
3. Read `README_START_HERE.txt`.
4. Double-click `Download_Scryfall_Data.pyw`.
5. Confirm that `data/scryfall_cards.json` is created.
6. Double-click `Launch_The_Dragons_Touch.pyw`.
7. Confirm that The Dragon's Touch desktop UI opens.

If the app does not open, record what happened and stop.

## App Smoke Test Checklist

### Launch

- Pass/Fail: The ZIP extracts without errors.
- Pass/Fail: `Download_Scryfall_Data.pyw` runs without Visual Studio Code.
- Pass/Fail: `data/scryfall_cards.json` is created.
- Pass/Fail: `Launch_The_Dragons_Touch.pyw` opens the app.
- Pass/Fail: Visual Studio Code is not required to launch the app.

### Navigation

- Pass/Fail: Deck Selection opens.
- Pass/Fail: Review Setup opens.
- Pass/Fail: Philosophy Lens opens.
- Pass/Fail: Collection Source opens.
- Pass/Fail: Run Analysis opens.
- Pass/Fail: Report Viewer opens.
- Pass/Fail: Batch / Aggregate opens as a future placeholder.
- Pass/Fail: Settings opens.

### Deck Selection

- Pass/Fail: Choose a Commander deck file.
- Pass/Fail: Deck preview loads.
- Pass/Fail: Commander preview appears.
- Pass/Fail: Deck count appears.
- Pass/Fail: Partner or companion preview appears if applicable.

### Review Setup

- Pass/Fail: Output Mode can be changed.
- Pass/Fail: Review Direction can be changed.
- Pass/Fail: Review Intensity / Build-Up Mode displays correctly based on direction.
- Pass/Fail: Prompt Mode can be changed.
- Pass/Fail: Intended Bracket can be changed.
- Pass/Fail: Budget Note can be entered.
- Pass/Fail: Run Settings Summary updates immediately.

### Philosophy Lens

- Pass/Fail: A philosophy lens can be selected.
- Pass/Fail: A subtype/persona can be selected if desired.
- Pass/Fail: Guide Presentation can be changed.
- Pass/Fail: The page clearly says philosophy does not override legality, budget, color identity, collection mode, pilot intent, or deck evidence.

### Collection Source

- Pass/Fail: No Collection can be selected.
- Pass/Fail: Prefer Collection First can be selected.
- Pass/Fail: Collection Only can be selected.
- Pass/Fail: Collection Source mode can be selected.
- Pass/Fail: Folder/file picker appears when appropriate.
- Pass/Fail: Collection summary updates immediately.

### Run Analysis

- Pass/Fail: Run Analysis shows staged settings.
- Pass/Fail: Bridge Preview displays the selected/staged choices.
- Pass/Fail: Guarded Execution Preview appears.
- Pass/Fail: Clicking Run shows guarded confirmation.
- Pass/Fail: Cancel prevents backend execution.
- Pass/Fail: Confirm runs `main.py`.
- Pass/Fail: The app does not silently run the backend.

### Output and Report Viewer

- Pass/Fail: Output folder is created after a confirmed run.
- Pass/Fail: Output folder includes commander name.
- Pass/Fail: Output folder includes source deck filename distinction.
- Pass/Fail: Output folder includes timestamp.
- Pass/Fail: Normal/debug folders are created.
- Pass/Fail: Report detection finds the generated report.
- Pass/Fail: Report Viewer loads the report as plain text.
- Pass/Fail: Search/copy/refresh/open-folder controls work.

## Required First Test: Use One Included Sample Deck

Start with one of the included sample decklists in the `Decklists/` folder.

These are known test cases. They help confirm that the app can complete the basic workflow before testing unusual or personal files.

Included sample deck purposes:

1. **Miirym Duplicate Legality Test**
   - Tests duplicate legality reporting.
   - Includes two copies of `Life Finds a Way`.

2. **Phelia Bracket 2 Test**
   - Tests lower-power / bracket-sensitive review.

3. **Voja Build-Up Test**
   - Tests an incomplete deck that needs three more cards to become legal.

4. **Inga & Esika Companion Test**
   - Tests companion or restriction handling.

5. **Toggo / Keskit Partner Test**
   - Tests partner commander handling and landfall/artifact/sacrifice package recognition.

After testing one sample deck, please test one of your own Commander decks if you are willing.

## AI Follow-Up Review Requirement

After generating a Dragon's Touch report, the tester must also run the report through an AI follow-up review.

This is part of the alpha test.

The goal is to confirm that the report is not only generated, but also useful as an input for a guided deck-review conversation.

### AI Follow-Up Steps

1. Open the generated Dragon's Touch report.
2. Copy or upload the report into ChatGPT.
3. Start a new chat titled:

   `Alpha Tester Attempt — [Commander Name]`

4. Use this opening prompt:

```text
I am alpha testing The Dragon's Touch, a local Magic: The Gathering Commander deck-review tool.

I have completed the clean ZIP extract, Scryfall data setup, desktop UI launch, deck selection, guarded Run Analysis, output folder generation, report detection, and Report Viewer smoke test.

Now I want to run the generated Dragon's Touch report through an AI-assisted review.

Please do the following:
1. Confirm receipt of the report.
2. Summarize what the report appears to say.
3. Identify the commander, deck status, required cuts, primary strategy, secondary strategy, and any major cut/review candidates.
4. Begin a guided review one section at a time.
5. Ask for my pilot intent and correct the Dragon's Touch strategy read if needed.
6. Treat legal decks as optional tuning unless the report identifies legality issues.
7. Do not present recommendations as automatic deck edits.
8. Preserve budget, collection mode, table power, color identity, and pilot intent boundaries.
```

5. Answer the AI's guided questions.
6. Confirm whether the AI-assisted review was useful.
7. Save or copy the final review summary.

### AI Follow-Up Checklist

- Pass/Fail: AI confirmed receipt of the report.
- Pass/Fail: AI correctly identified the commander.
- Pass/Fail: AI correctly identified whether the deck was legal.
- Pass/Fail: AI correctly identified whether cuts were required or optional.
- Pass/Fail: AI summarized the Dragon's Touch strategy read.
- Pass/Fail: AI asked for pilot intent.
- Pass/Fail: AI allowed the pilot to correct the strategy read.
- Pass/Fail: AI preserved budget / collection / table-power boundaries.
- Pass/Fail: AI did not treat suggestions as automatic deck edits.
- Pass/Fail: AI produced useful final playtest notes or recommendations.

## Feedback Questions for Tester

Please answer these after completing the app test and AI follow-up review.

1. Could you launch the app without help?
2. Was the Scryfall data setup clear?
3. Did any security warning appear?
4. Was it clear which file to double-click?
5. Was the page navigation understandable?
6. Did the app explain what each setup page was for?
7. Did Run Analysis make it clear that `main.py` would run only after confirmation?
8. Did the generated report appear where expected?
9. Did Report Viewer make it easy to open and copy the report?
10. Did the AI follow-up review make the Dragon's Touch output more useful?
11. What confused you?
12. What felt polished?
13. What felt unfinished?
14. Would you be able to test another deck without additional instructions?
15. What is the single biggest improvement needed before a wider alpha?

## What to Send Back to the Developer

Send back:

- The commander/deck tested
- Whether the ZIP extracted correctly
- Whether Scryfall data downloaded correctly
- Whether the app launched correctly
- Whether the full smoke test passed
- The generated Dragon's Touch report
- The AI follow-up review result
- Any screenshots of errors
- Any confusing steps
- The answers to the feedback questions above

## Pass Standard

This alpha attempt passes if:

- The tester can extract the ZIP.
- The tester can download Scryfall data.
- The tester can launch the app without Visual Studio Code.
- The tester can run one guarded deck review.
- The tester can open the generated report.
- The tester can use that report in an AI follow-up review.
- The tester can provide clear feedback without needing the developer to explain each step live.

## Optional Stress Tests

After the basic smoke test passes, please try to break the system in useful ways.

Useful stress tests:

- Add your own Commander decklist to the `Decklists/` folder.
- Try a `.txt` export from a deckbuilding site other than Archidekt.
- Try a copied/pasted decklist saved as a `.txt` file.
- Try your own collection file.
- Try a partner commander deck.
- Try a companion deck.
- Try an incomplete deck.
- Try a deck with a known illegal duplicate.
- Try a deck with unusual formatting.

If something fails, please report:

- what file you tested,
- where the file came from,
- what steps you followed,
- what you expected to happen,
- what actually happened,
- and include screenshots if possible.
