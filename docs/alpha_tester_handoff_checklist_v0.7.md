# The Dragon's Touch — Alpha Tester Handoff Checklist v0.7

Use this checklist before handing the current Modular Alpha build to a trusted tester.

## 1. Clean Folder Check

- Pass/Fail: Project folder is named clearly, such as `The Dragon's Touch (Modular Alpha)`.
- Pass/Fail: `Launch_The_Dragons_Touch.pyw` exists in the project root.
- Pass/Fail: `README_START_HERE.txt` exists in the project root.
- Pass/Fail: `download_scryfall_data.py` exists in the project root.
- Pass/Fail: `main.py` exists in the project root.
- Pass/Fail: `config.py` exists in the project root.
- Pass/Fail: `ui/` exists.
- Pass/Fail: `docs/` exists.
- Pass/Fail: Old patch ZIP files are not included in the handoff folder.
- Pass/Fail: `__pycache__/` folders are removed.
- Pass/Fail: `.pyc` files are removed.

## 2. Scryfall Data Check

- Pass/Fail: If this is a lean ZIP, `data/scryfall_cards.json` is omitted.
- Pass/Fail: If `data/scryfall_cards.json` is omitted, `download_scryfall_data.py` is included.
- Pass/Fail: README explains how to run `python download_scryfall_data.py`.
- Pass/Fail: Tester understands internet access is required to regenerate Scryfall data.

## 3. Launch Check

- Pass/Fail: Double-clicking `Launch_The_Dragons_Touch.pyw` opens the app.
- Pass/Fail: App opens without Visual Studio Code.
- Pass/Fail: App opens without import errors.
- Pass/Fail: App header shows current v0.7 Modular Alpha wording.
- Pass/Fail: `.bat` launchers are not presented as the primary path.
- Pass/Fail: Desktop shortcut support is not presented as an active requirement.

## 4. Navigation Check

- Pass/Fail: Deck Selection opens.
- Pass/Fail: Review Setup opens.
- Pass/Fail: Philosophy Lens opens.
- Pass/Fail: Collection Source opens.
- Pass/Fail: Run Analysis opens.
- Pass/Fail: Report Viewer opens.
- Pass/Fail: Batch / Aggregate opens only as future/placeholder.
- Pass/Fail: Settings opens.

## 5. Single-Deck Workflow Check

- Pass/Fail: Tester can select one Commander deck file.
- Pass/Fail: Deck preview loads.
- Pass/Fail: Commander preview appears.
- Pass/Fail: Review Setup choices stage correctly.
- Pass/Fail: Philosophy Lens choices stage correctly.
- Pass/Fail: Collection Source choices stage correctly.
- Pass/Fail: Run Analysis summary reflects staged choices.
- Pass/Fail: Guarded confirmation appears before backend execution.
- Pass/Fail: Cancel prevents backend execution.
- Pass/Fail: Confirmed run goes through `main.py`.
- Pass/Fail: Output folder is created.
- Pass/Fail: Report detection works.
- Pass/Fail: Report Viewer loads the generated report as plain text.

## 6. Boundary Check

- Pass/Fail: UI says guidance does not automatically edit the deck.
- Pass/Fail: UI says `main.py` runs only after guarded confirmation.
- Pass/Fail: Philosophy Lens does not imply it overrides legality, budget, collection mode, color identity, pilot intent, or deck evidence.
- Pass/Fail: Collection Source does not imply outside cards are available in collection-only mode.
- Pass/Fail: Commander Spellbook/API remains disabled/future.
- Pass/Fail: Batch / Aggregate remains future/placeholder.
- Pass/Fail: Replacement Candidate Engine is not introduced.
- Pass/Fail: Report Viewer remains plain-text loading.

## 7. Tester Feedback Questions

Ask the tester:

1. Could you open the app without help?
2. Did the README explain the launch process clearly?
3. Did you understand the order of pages?
4. Did the Run Analysis guarded confirmation make sense?
5. Did the report load where you expected it to?
6. Did any page feel like it was promising a feature that was not actually active?
7. What wording confused you?
8. What was the first thing you tried that did not work?
9. Would you feel comfortable running a second deck without help?
10. What would make the app feel more trustworthy?

## 8. Handoff Decision

If the checklist passes, record:

```text
v0.7.20 Alpha Tester Readiness Lock Candidate: Passed
Ready for 1–2 trusted alpha testers.
```

If any item fails, record the exact failure and keep the tester group limited until the issue is fixed.
