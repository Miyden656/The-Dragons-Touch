# Refactor Acceptance Checklist

Use this before calling the cleanup version stable.

## Terminal checks

- [ ] `python -m compileall -q .` passes.
- [ ] `python tools/smoke_test_round8.py` passes.
- [ ] `python main.py` opens the file picker or honors `MTG_DECK_FILE`.
- [ ] Output folder is created.
- [ ] Normal report is written in normal mode.
- [ ] Debug files are written in debug mode.
- [ ] Both normal and debug files are written in both mode.

## Parser checks

- [ ] Commander section is parsed.
- [ ] Deck/mainboard section is parsed.
- [ ] Token/helper sections are ignored.
- [ ] Maybeboard/sideboard/cut sections are ignored as non-mainboard.
- [ ] Unknown/unparsed lines are reported.

## Scryfall checks

- [ ] Local `data/scryfall_cards.json` loads.
- [ ] Face/card helper logic works for normal cards.
- [ ] Color identity is read correctly.
- [ ] Type line and Oracle text are available to role tagging.

## Legality checks

- [ ] Commander color identity is calculated.
- [ ] Off-color cards are flagged.
- [ ] Duplicate nonbasic cards are flagged.
- [ ] Basic lands are not flagged as duplicate violations.
- [ ] Deck size status is correct.

## Strategy checks

- [ ] Primary strategy is produced.
- [ ] Secondary strategy is produced when appropriate.
- [ ] Broad fallback labels do not override clear commander-defined strategy.
- [ ] Strategy confidence is not wildly inflated.

## Cut checks

- [ ] Underfilled decks are addition-first.
- [ ] Overfilled decks report required cuts.
- [ ] Legal decks can still produce optional review cuts.
- [ ] Protected cards are not recommended as confident cuts.

## Prompt/report checks

- [ ] User-guided prompt is written.
- [ ] Interactive and worksheet mode are both available.
- [ ] Prompt asks for user intent before final review.
- [ ] Debug sections are separated.

## Final decision

Only replace the monolith when the checklist passes on multiple real decks.
