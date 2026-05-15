# v0.8.7.2.1-dev — Local Combo Index Builder with Data Path Cleanup Summary

## Scope Guard

- No API calls were made.
- No app integration was performed.
- `main.py` was not changed.
- UI and report generation were not changed.
- This only builds a compact local combo index from `data/combo.json`.

## Source Data

- Source version: 5.4.7
- Source timestamp: 2026-05-14T11:23:10.884507+00:00
- Source variants: 88,116

## Index Output

- Index path: `data\commander_spellbook\combo_index.json`
- Indexed variants: 86,728
- Skipped non-OK status: 0
- Skipped non-Commander-legal: 1,388
- Skipped spoiler-tagged: 0
- Skipped missing card names: 0
- Spoiler-tagged indexed and marked: 297
- mustBeCommander indexed and marked: 909
- Combos with template requirements indexed and marked: 3,286

## Top Bracket Tags in Index

- E: 75,507
- R: 5,829
- S: 2,845
- P: 2,089
- C: 244
- O: 214

## Combo Size Distribution in Index

- 1 cards: 7
- 2 cards: 4,453
- 3 cards: 40,501
- 4 cards: 35,604
- 5 cards: 6,126
- 6 cards: 25
- 7 cards: 6
- 8 cards: 1
- 9 cards: 4
- 10 cards: 1

## Top Produced Results in Index

- Infinite ETB: 55,542
- Infinite LTB: 48,266
- Infinite death triggers: 39,387
- Infinite sacrifice triggers: 37,633
- Infinite storm count: 18,657
- Infinite colored mana: 10,840
- Infinite creature tokens: 9,343
- Infinite +1/+1 counters on a creature: 8,616
- Infinite draw triggers: 8,586
- Infinite colorless mana: 8,097
- Infinite lifegain triggers: 7,964
- Infinite landfall triggers: 7,040
- Infinite card draw: 6,584
- Infinite damage: 6,208
- Infinite lifegain: 6,204
- Infinite magecraft triggers: 6,168
- Lock: 5,783
- Near-infinite ETB: 5,158
- Infinite untap of creatures you control: 4,750
- Infinite mana creatures you control can produce: 4,744

## Future Use

This index is meant for later v0.8 combo awareness work:

1. Detect infinite combos already present in a deck.
2. Detect one-card-away potential infinite combos.
3. Hide spoiler-tagged combos by default at match/report time.
4. Respect commander color identity and must-be-commander rules at match time.
5. Cross-check missing one-card combo pieces against collection files later.
