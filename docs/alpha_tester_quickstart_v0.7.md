# The Dragon's Touch v0.7 Alpha Tester Quickstart

## Supported Launch Path

Open the project folder and double-click:

```text
Launch_The_Dragons_Touch.pyw
```

Do not use the `.bat` files unless troubleshooting with the developer.

Desktop shortcut support is deferred for v0.7 alpha because Smart App Control blocked that path during testing.

## First Test Run

1. Launch `Launch_The_Dragons_Touch.pyw`.
2. Open Deck Selection.
3. Choose a Commander deck `.txt` file.
4. Confirm the deck preview loads.
5. Open Review Setup and choose the review direction/options.
6. Open Philosophy Lens and choose the desired lens/presentation style.
7. Open Collection Source and choose the collection mode/source.
8. Open Run Analysis.
9. Review the current run summary.
10. Click Run main.py with Guarded Confirmation.
11. Confirm the guarded run only if the settings look correct.
12. Open Report Viewer and load the generated report.

## What Should Happen

The UI should stage choices, ask for guarded confirmation, run `main.py`, detect the generated output folder, and load the report as plain text.

## What Should Not Happen

The app should not:

- run backend analysis automatically on launch
- bypass guarded confirmation
- edit deck files automatically
- call Commander Spellbook/API
- run Batch / Aggregate workflow
- use deep markdown rendering
- create a second backend workflow

## If Scryfall Data Is Missing

Run this from the project root:

```text
python download_scryfall_data.py
```

This recreates:

```text
data/scryfall_cards.json
```

Internet access is required for that download.
