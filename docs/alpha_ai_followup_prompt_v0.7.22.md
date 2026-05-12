# The Dragon's Touch v0.7.22 — Alpha AI Follow-Up Prompt

Use this after the alpha tester has generated a Dragon's Touch deck report.

## Chat Title

`Alpha Tester Attempt — [Commander Name]`

## Prompt

```text
I am alpha testing The Dragon's Touch, a local Magic: The Gathering Commander deck-review tool.

I have completed the clean ZIP extract, Scryfall data setup, desktop UI launch, deck selection, guarded Run Analysis, output folder generation, report detection, and Report Viewer smoke test.

Before beginning the AI follow-up review, ask the tester whether the report came from:

1. one of the included sample decklists,
2. their own decklist,
3. a decklist exported from Archidekt,
4. a decklist exported from another deckbuilding site,
5. or an unusual/custom text file.

If the report came from a sample deck, ask which sample was used.

If the report came from the tester's own deck, ask what the deck is supposed to do and whether the Dragon's Touch strategy read matches the tester's intent.

Now I want to run the generated Dragon's Touch report through an AI-assisted review.

Please do the following:
1. Confirm receipt of the report.
2. Summarize what the report appears to say.
3. Identify the commander, deck status, required cuts, primary strategy, secondary strategy, and any major cut/review candidates.
4. Begin a guided review one section at a time.
5. Ask for my pilot intent and correct the Dragon's Touch strategy read if needed.
6. Treat legal decks as optional tuning unless the report identifies legality issues.
7. Do not present recommendations as automatic deck edits.
8. Preserve budget, collection mode, table power, color identity, and pilot intent boundaries.
```

## Tester Instructions

1. Upload or paste the Dragon's Touch report.
2. Answer the AI's questions one section at a time.
3. Correct the AI if the deck's real plan is different from the Dragon's Touch strategy read.
4. Save the final AI-assisted review.
5. Send the final review and feedback notes back to the developer.
