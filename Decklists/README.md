# Your decklists go here

Drop plain-text Commander decklist files into this folder. The Deck Selection
page reads `.txt` files from here for the deck-review flow.

## Expected format

**One card per line**, optional quantity prefix. Standard Archidekt /
Moxfield / Manabox plain-text exports work directly:

```
1 Atraxa, Praetors' Voice
1 Sol Ring
1 Arcane Signet
1 Command Tower
...
```

Both `1 Card Name`, `1x Card Name`, and just `Card Name` formats are
accepted. Quantities default to 1 when not specified.

## How to get a plain-text decklist from Archidekt

1. Open your deck on Archidekt
2. Click the three-dot menu → **Export**
3. Choose **Plain Text**
4. Either copy the text and paste it into the Paste tab in the app,
   OR save the file here in `Decklists/` and use Select File tab

## What's NOT in this folder

`.txt` files inside `Decklists/` are **gitignored** — your real decklists
are local to your machine and never get committed to the project repo.
This README is here to explain the format; everything else you add here
stays private.
