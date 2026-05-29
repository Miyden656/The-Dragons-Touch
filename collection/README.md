# Your card collection goes here

Drop plain-text card list files into this folder. The Commander's Call flow
scans every `.txt` file in here to figure out what commanders you own and
which cards you have available for deck-building.

## Expected format

**One card per line**, optional quantity prefix. Anything that Archidekt,
Moxfield, Manabox, or your own spreadsheet exports as plain text usually
works:

```
1 Sol Ring
4 Llanowar Elves
Lightning Bolt
2x Counterspell
Aang, at the Crossroads
```

Both `1 Card Name`, `1x Card Name`, and just `Card Name` formats are
accepted. Quantities default to 1 when not specified.

## Multiple files are encouraged

The tool tracks **which file each card came from**, so you can name files
by storage location to help find physical cards later:

- `Cards in Avatar the last Airbender Box at desk.txt`
- `Cards in Phyrexian Bundle Box at Desk.txt`
- `Proxies at Desk.txt`
- `Cards in trade binder.txt`

The "Owned Cards by Role" report shows the source file next to each card,
so when the app suggests *"Lightning Greaves — owned from: Cards in Brown
box with sparks at Desk.txt"*, you know where to physically grab it.

## What's NOT in this folder

`.txt` files inside `collection/` are **gitignored** — your real card data
is local to your machine and never gets committed to the project repo.
This README is here to explain the format; everything else you add here
stays private.

## If you don't have a digital collection yet

The deck-review flow (paste a decklist, run analysis, open report) does
**not** need a collection. You can use The Dragon's Touch without ever
filling this folder. The Commander's Call flow is the one that uses it.
