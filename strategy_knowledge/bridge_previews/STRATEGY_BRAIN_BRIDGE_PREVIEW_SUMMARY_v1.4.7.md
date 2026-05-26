# Strategy Brain Bridge / Opt-In Preview v1.4.7

## Status

Bridge mode: `opt_in_preview_only`
Bridge enabled for preview: `True`
Default strategy system: `legacy_current_strategy_system`
Opt-in strategy system: `strategy_knowledge_preview`

## Runtime Boundary

- Runtime default changed: false
- Active runtime replacement: false
- Legacy fallback required: true
- Strategy scoring changed: false
- Deck generation enabled: false
- Exact card selection enabled: false
- Final deck inclusion enabled: false
- Mana-base generation enabled: false

## Preview Strategies

### Aristocrats (`aristocrats`)

Layer: `02_mechanical_themes`
Primary role buckets: `strategy_enablers, strategy_payoffs, recursion, finishers_win_conditions`
Basic land policy: `assume_available`
Nonbasic land policy: `collection_first_unless_upgrades_allowed`

### Landfall / Lands Matter (`landfall_lands_matter`)

Layer: `02_mechanical_themes`
Primary role buckets: `ramp_mana_development, strategy_enablers, strategy_payoffs, mana_base_support`
Basic land policy: `assume_available`
Nonbasic land policy: `collection_first_unless_upgrades_allowed`

### Spellslinger (`spellslinger`)

Layer: `02_mechanical_themes`
Primary role buckets: `strategy_enablers, strategy_payoffs, card_draw_card_advantage, finishers_win_conditions`
Basic land policy: `assume_available`
Nonbasic land policy: `collection_first_unless_upgrades_allowed`

### Tokens (`tokens`)

Layer: `02_mechanical_themes`
Primary role buckets: `strategy_enablers, strategy_payoffs, finishers_win_conditions, card_draw_card_advantage`
Basic land policy: `assume_available`
Nonbasic land policy: `collection_first_unless_upgrades_allowed`

### Voltron (`voltron`)

Layer: `02_mechanical_themes`
Primary role buckets: `protection, strategy_enablers, strategy_payoffs, finishers_win_conditions`
Basic land policy: `assume_available`
Nonbasic land policy: `collection_first_unless_upgrades_allowed`

## Replacement Gate

Replacement allowed: false

Next safe step: v1.4.8 — Strategy Brain Default Candidate