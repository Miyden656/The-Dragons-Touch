# The Dragon's Touch — v0.6.6 Philosophy Bias Lock

## Lock status

v0.6.6 is the stable philosophy-bias checkpoint for The Dragon's Touch.

This milestone adds philosophy-aware review behavior without turning philosophy into a rules engine. The selected philosophy lens may shape explanation, optional cut pressure, protected/watch-card language, and replacement-candidate presentation. It must not override the deck's actual rules, legality, strategy detection, collection boundaries, or the pilot's stated intent.

## Locked behavior

### Philosophy guide framing

Reports include the selected lens, guide, primary question, lens summary, how to use the lens, Protect / Question / Prefer guidance, and boundaries.

Named guides are mentor frames only. They should not become heavy roleplay or speak in first person as if they are separate people.

### Optional cut bias

Philosophy may apply a light optional-cut nudge when a card clearly matches protect-biased or review-biased evidence for the selected lens.

It can:

- lower optional cut pressure for cards that clearly support the selected philosophy;
- raise optional review pressure for cards that clearly conflict with the selected philosophy;
- explain why a card should be kept, watched, or reviewed.

It cannot:

- override required cuts;
- override legality;
- force a card to be cut;
- ignore pilot-protected cards;
- replace strategy detection.

### Protected / watch-card language

Protected and watch-card entries should include:

- Protected Label
- Initial flag
- Philosophy adjustment
- Final verdict
- Why this matters
- Review instruction

The goal is to explain how the pilot should evaluate the card, not merely say that it is protected.

### Replacement-candidate bias

Philosophy may lightly influence owned-card candidate presentation or ordering when collection matching is active.

It can:

- note why an owned card fits the selected lens;
- nudge presentation/order among already valid candidates;
- provide visibility counters and examples in debug.

It cannot:

- force a weak card into Strong;
- bypass quality gates;
- bypass color identity;
- bypass companion filters;
- bypass collection-only mode;
- present a card as an automatic swap.

If no owned card is a real fit, the report should say so instead of forcing a bad recommendation.

## Lens-specific locked rules

### Balanced / Unknown

Balanced / Unknown is the neutral/default lens.

It should stay mostly conservative. It should not protect or challenge large portions of the deck just because they are normal infrastructure or primary-plan cards. Normal deck logic should handle those.

Balanced / Unknown may visibly nudge only clear cases such as:

- clear off-plan cards;
- explicit user-intent conflicts;
- declared user constraints.

Expected QA behavior: low adjustment ratio unless the deck is extremely polarized.

### Pet Card

Pet Card should protect explicitly declared pet cards, cards the pilot refuses to cut, or cards with clear personal-value evidence.

If no pet card is declared, Pet Card should not randomly apply cut protection.

### Commander Exploiter

Commander Exploiter should protect cards that directly interact with the commander's rules text, trigger structure, or commander-specific payoff plan.

It should not protect generic support unless the card has real commander-specific evidence.

### Engine Builder

Engine Builder should protect real engine pieces, connectors, enablers, payoffs, sacrifice outlets, recursion, and resource converters.

It should not treat every synergy-looking card as protected unless it actually connects the engine.

### Power-Level Calibrator

Power-Level Calibrator should evaluate table fit, bracket pressure, and power mismatch.

It should not assume stronger is always better.

### Competitive Closer

Competitive Closer should focus on whether the deck turns resources into a win.

It should protect real finishers and challenge value engines that do not help close the game when evidence exists.

### Big Moment / Big Creature

These lenses may protect cards that enable, protect, find, or amplify the deck's intended payoff moment.

They should still challenge unsupported haymakers and expensive cards that do not actually advance the payoff.

## Companion lock rule

Unsupported companion restrictions should be reported as manual-review required, not as automated violations.

Correct wording pattern:

- Companion legality result: Manual review required — automated restriction check is incomplete for this companion
- Companion legality violations found by automation: 0
- Manual companion reviews required: 1

## QA expectations before moving beyond v0.6.6

A healthy v0.6.6 run should show:

- readable philosophy guide section;
- visible bias counters in debug;
- conservative Balanced / Unknown behavior;
- Pet Card stays quiet without declared pet-card evidence;
- companion manual-review wording is clear;
- replacement-bias counters remain visible when collection matching is active;
- collection-only mode does not force bad recommendations;
- required legality boundaries remain protected.

## Locked milestone verdict

v0.6.6 is ready to serve as the stable philosophy-bias checkpoint if local smoke tests confirm the expected diagnostics.
