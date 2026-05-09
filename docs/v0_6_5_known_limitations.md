# The Dragon’s Touch v0.6.5 — Known Limitations

## Current milestone

v0.6.5 is the Philosophy-Aware Report Guidance checkpoint.

The philosophy layer is intentionally guidance-only at this stage.

It can affect:

- Report language.
- Guided prompt language.
- Persona / guide framing.
- Protection language.
- Review framing.
- How another AI interprets the deck during the guided review.

It does not yet affect:

- Cut scores.
- Replacement scores.
- Collection candidate scores.
- Strategy detection.
- Legality.
- Deck-size handling.
- Required cuts.
- Auto-batch routing.

## Philosophy limitations

The selected philosophy lens appears in the report and prompt, but the backend does not yet automatically lower or raise cut pressure based on that philosophy.

Examples:

- A Commander Exploiter deck may still flag a commander-specific card as off-plan if the script does not yet understand that commander’s unique interaction.
- A Theme / Vibe deck may still flag flavorful cards if their mechanical tags do not match the detected strategy.
- A Combo Builder or Engine Builder lens may explain why engine cards matter, but it does not yet fully protect those pieces through scoring.

This is expected in v0.6.5. Scoring changes are planned for v0.6.6.

## Strategy detection limitations

The strategy read is a strong starting point, not final truth.

The pilot may need to correct:

- Primary strategy.
- Secondary strategy.
- Win condition.
- Protected packages.
- Theme or vibe goals.
- Bracket/table intent.

The guided prompt is designed to let the pilot override the script when needed.

## Collection limitations

Collection Pull is active, but collection candidates are review candidates, not automatic upgrades.

Known limitations:

- Strong Owned Candidates may still require pilot judgment.
- Possible Owned Candidates should not be treated as upgrades without review.
- Shakeup Candidates are experiments only.
- Collection gaps should be stated clearly instead of forcing weak recommendations.
- The system may not yet know every nuanced reason a card is a good or bad fit for a specific commander.

## Replacement limitations

v0.6.5 can suggest replacement categories and use collection candidates, but the exact one-for-one replacement engine is not final.

The tool should avoid saying “cut X for Y” unless the deck report, pilot answers, and card roles make the swap clearly justified.

Full replacement intelligence is planned for later versions.

## Commander-specific limitations

The system may not fully understand every commander’s unique text yet.

Examples from testing:

- Vadrik, Astral Archmage cares deeply about power-scaling, generic cost reduction, X-spells, and buyback spells.
- Some of those cards may look weak or off-plan to generic heuristics until the pilot explains the plan.

v0.6.6 should begin addressing this by making philosophy and pilot intent influence cut/replacement bias.

## Prompt handoff limitations

The generated user-guided prompt works best when used with a capable AI that follows instructions carefully.

The prompt expects the reviewing AI to:

- Ask for the deck report first.
- Ask one section at a time.
- Accept numbered answers.
- Ask only for missing items when answers are partial.
- Summarize the pilot’s answers.
- Wait for final confirmation before recommendations.

Some AI tools may still format text differently or skip steps.

## Debug/report limitations

Debug reports are intentionally verbose. They are for testing and analysis, not normal user reading.

Normal deck reports are the primary human-facing output.

Batch aggregate reports are convenience copies. The per-deck output folders remain the source outputs.

## Not public-release ready yet

v0.6.5 is suitable for a very small trusted preview, not broad public release.

Before public release, the project still needs:

- More QA across different commanders and strategies.
- More collection-pull testing.
- Philosophy-aware cut/replacement bias.
- Better exact replacement logic.
- Clear setup instructions.
- Cleaner documentation.
- More safeguards around expectations and limitations.

