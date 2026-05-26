# Strategy Knowledge Main Pipeline Opt-In Live Bridge

Strategy Knowledge is now connected to the main pipeline when the opt-in environment variable is enabled.

## Opt-In

- Environment variable: `TDT_STRATEGY_KNOWLEDGE_LIVE_BRIDGE`
- Enabled for this run: `False`

## Deck Context

- Commander: Unknown
- Deck card count: None
- Legacy strategy label: Unknown

## Live Bridge Status

- Live bridge mode: `opt_in_report_artifact_bridge`
- Legacy pipeline still available: `True`
- Active runtime replacement: `False`

## Boundary

- This bridge is opt-in only.
- This writes Strategy Knowledge bridge artifacts from the main pipeline.
- This does not export a final deck.
- This does not lock final inclusions.
- This does not generate a finished mana base.
- This does not write lands into a deck.

## Next Step
