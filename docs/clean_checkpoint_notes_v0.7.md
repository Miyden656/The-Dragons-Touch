# v0.7 Clean Checkpoint Notes

## Clean Checkpoint Decision

The v0.7 Modular Alpha clean ZIP may omit the large Scryfall cache file:

```text
data/scryfall_cards.json
```

That file can be regenerated with:

```text
python download_scryfall_data.py
```

The downloader must remain in the project root.

## Lean ZIP

Use for GitHub/share/checkpoint upload:

- Exclude `data/scryfall_cards.json`.
- Include `download_scryfall_data.py`.
- Exclude `__pycache__/` and `*.pyc`.
- Exclude `.git/` from share/checkpoint ZIPs.
- Exclude old patch ZIPs and old generated output runs.

## Offline Personal Backup ZIP

Use for private backup only:

- Include `data/scryfall_cards.json`.
- Larger file size.
- Can run card lookup without redownloading Scryfall data.

## Supported Launch Path

The supported v0.7 alpha launch path is:

```text
Launch_The_Dragons_Touch.pyw
```

Desktop shortcut support is deferred until a packaging/installer track.
