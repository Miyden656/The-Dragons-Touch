# Parity Test Plan

The goal of parity testing is not to force identical wording. The goal is to confirm that the modular cleanup preserves the important behavior of the stable monolith.

## Use these deck categories

Test at least one deck from each category if available:

1. Normal legal 100-card deck
2. Underfilled build-up deck
3. Overfilled cut-down deck
4. Partner commander deck
5. Deck with companion
6. Deck with custom sections / maybeboard / tokens
7. Typal deck
8. Commander-defined strategy deck
9. Collection/card-pool replacement test
10. Batch run with multiple deck files

## Compare these fields

For each deck, compare the stable monolith output and modular output on:

```text
Deck size
Commander name(s)
Command-zone rule
Color identity
Companion note
Unknown card count
Legality warnings
Primary strategy
Secondary strategy
Core synergy packages
Bracket pressure notes
Required cuts
Optional cuts
Protected cards
Replacement category needs
Build-up/addition-first behavior
Prompt mode: interactive vs worksheet
Output mode: normal/debug/both
```

## Acceptable differences during cleanup

These are acceptable before final polish:

- Slightly different wording
- Different ordering of non-critical bullet points
- Shorter debug output
- More conservative strategy confidence
- Fewer exact replacement suggestions, if collection parity has not been finalized

## Not acceptable

These should block replacing the monolith:

- Fails to run
- Fails to load `data/scryfall_cards.json`
- Cannot parse common decklists
- Miscounts deck size
- Loses commander detection
- Treats token/helper cards as mainboard cards
- Produces required cuts for underfilled decks
- Ignores over-100 required cuts
- Recommends off-color cards
- Ignores user-protected cards
- Stops producing the user-guided prompt
