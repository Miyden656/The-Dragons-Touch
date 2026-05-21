# v0.8.7.2.1-dev — Local Combo Index Builder with Data Path Cleanup Summary

## Scope Guard

- No API calls were made.
- No app integration was performed.
- `main.py` was not changed.
- UI and report generation were not changed.
- This only builds a compact local combo index from `data/combo.json`.

## Source Data

- Source version: 5.4.10
- Source timestamp: 2026-05-20T09:35:41.433297+00:00
- Source variants: 88,554

## Index Output

- Index path: `C:\Users\Bruce\Desktop\The Dragon's Touch (Modular Alpha)\data\commander_spellbook\combo_index.json`
- Indexed variants: 87,164
- Skipped non-OK status: 0
- Skipped non-Commander-legal: 1,390
- Skipped spoiler-tagged: 0
- Skipped missing card names: 0
- Spoiler-tagged indexed and marked: 364
- mustBeCommander indexed and marked: 912
- Combos with template requirements indexed and marked: 3,307

## Top Bracket Tags in Index

- E: 75,860
- R: 5,876
- S: 2,878
- P: 2,091
- C: 245
- O: 214

## Combo Size Distribution in Index

- 1 cards: 7
- 2 cards: 4,481
- 3 cards: 40,715
- 4 cards: 35,775
- 5 cards: 6,149
- 6 cards: 25
- 7 cards: 6
- 8 cards: 1
- 9 cards: 4
- 10 cards: 1

## Top Produced Results in Index

- Infinite ETB: 55,858
- Infinite LTB: 48,555
- Infinite death triggers: 39,642
- Infinite sacrifice triggers: 37,884
- Infinite storm count: 18,753
- Infinite colored mana: 10,857
- Infinite creature tokens: 9,385
- Infinite +1/+1 counters on a creature: 8,666
- Infinite draw triggers: 8,609
- Infinite colorless mana: 8,114
- Infinite lifegain triggers: 7,969
- Infinite landfall triggers: 7,049
- Infinite card draw: 6,608
- Infinite damage: 6,226
- Infinite lifegain: 6,207
- Infinite magecraft triggers: 6,186
- Lock: 5,849
- Near-infinite ETB: 5,179
- Infinite untap of creatures you control: 4,766
- Infinite mana creatures you control can produce: 4,760

## Future Use

This index is meant for later v0.8 combo awareness work:

1. Detect infinite combos already present in a deck.
2. Detect one-card-away potential infinite combos.
3. Hide spoiler-tagged combos by default at match/report time.
4. Respect commander color identity and must-be-commander rules at match time.
5. Cross-check missing one-card combo pieces against collection files later.
