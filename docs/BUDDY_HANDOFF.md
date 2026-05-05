# Buddy Handoff — MTG Deck Helper v0.6.2 Cleanup

## Project purpose

This tool helps the user review and build Magic: The Gathering Commander decks.

The current cleanup goal is to refactor the stable single-file script into modules so future work is easier.

## Stable reference

The stable backup is:

```text
deck_helper_v0.6.2.6.py
```

Do not edit that file directly.

## Cleanup branch/package

The modular checkpoint is:

```text
./
```

Entry point:

```bash
python main.py
```

## Current architecture

```text
./
├─ main.py                         # orchestration only
├─ config.py                       # runtime config and constants
├─ io/                             # file picker, batch runner, output writing
├─ data/                           # Scryfall/card helper layer
├─ parsing/                        # decklist parser and section rules
├─ legality/                       # command zone and Commander legality
├─ analysis/                       # role tags, strategy, bracket, plan-fit
├─ cuts/                           # cut pressure and replaceability
├─ replacements/                   # collection/deck-completion boundaries
└─ reports/                        # reports, prompts, debug output
```

## What not to do during cleanup

Do not add:

- Commander Spellbook API integration
- Infinite combo detection
- Desktop UI
- New bracket system
- New report sections
- New scoring philosophy

Those come later.

## Best way to help

1. Run compile and smoke tests.
2. Run the stable monolith and modular version on the same deck.
3. Compare the broad behavior, not exact wording first.
4. Identify functions that are still too large or in the wrong module.
5. Avoid changing logic unless a bug blocks parity.

## High-risk areas

These are the areas most likely to need careful review:

- `analysis/role_tags.py`
- `analysis/strategy_scoring.py`
- `analysis/strategy_gates.py`
- `cuts/replaceability.py`
- `reports/prompt_builder.py`
- collection/card-pool candidate parity

## Current known limitation

The modular version is runnable, but it still needs parity testing against the monolith before it replaces the stable script.
