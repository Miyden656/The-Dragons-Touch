# Strategy Role Bucket Mapping Integration v1.4.11

## Status

Mapping mode: `strategy_role_bucket_mapping_integration_preview`
Strategy profiles: `5`
Sample mappings: `6`
Sample mapping warnings: `0`

## Gate Checks

- runtime_contract_selected_strategy_knowledge: `True`
- scoring_preview_passed: `True`
- loader_preview_available: `True`
- all_strategy_profiles_role_mapping_ready: `True`

## Strategy Profiles

### Aristocrats (`aristocrats`)

Primary role buckets: `strategy_enablers, strategy_payoffs, recursion, finishers_win_conditions`
Secondary role buckets: `card_draw_card_advantage, targeted_removal, protection`
Strategy-specific roles: `free_sacrifice_outlets, repeatable_sacrifice_outlets, death_trigger_payoffs, token_fodder, creature_recursion, drain_finishers`

### Landfall / Lands Matter (`landfall_lands_matter`)

Primary role buckets: `ramp_mana_development, strategy_enablers, strategy_payoffs, mana_base_support`
Secondary role buckets: `card_draw_card_advantage, recursion, finishers_win_conditions`
Strategy-specific roles: `extra_land_drops, landfall_payoffs, land_recursion, fetch_lands_and_land_tutors, land_token_payoffs, big_mana_finishers`

### Spellslinger (`spellslinger`)

Primary role buckets: `strategy_enablers, strategy_payoffs, card_draw_card_advantage, finishers_win_conditions`
Secondary role buckets: `targeted_removal, protection, ramp_mana_development`
Strategy-specific roles: `cheap_cantrips, spell_payoffs, cost_reducers, copy_effects, graveyard_spell_recursion, spell_based_finishers`

### Tokens (`tokens`)

Primary role buckets: `strategy_enablers, strategy_payoffs, finishers_win_conditions, card_draw_card_advantage`
Secondary role buckets: `ramp_mana_development, protection, targeted_removal`
Strategy-specific roles: `repeatable_token_makers, burst_token_makers, anthem_payoffs, token_draw_payoffs, token_finishers, fodder_converters`

### Voltron (`voltron`)

Primary role buckets: `protection, strategy_enablers, strategy_payoffs, finishers_win_conditions`
Secondary role buckets: `ramp_mana_development, card_draw_card_advantage, targeted_removal`
Strategy-specific roles: `evasion_granting_cards, protection_spells, equipment_or_aura_payoffs, commander_damage_scalers, combat_card_draw, recovery_after_removal`

## Runtime Boundary

- Strategy role mapping enabled: true
- Live role-count generation changed: false
- Owned-card role classification runtime changed: false
- Deck generation enabled: false
- Exact-card selection enabled: false
- Final deck inclusion enabled: false
- main.py changed: false
- Report Viewer changed: false

## Next Safe Step

v1.4.12 — Strategy Cut / Protect / Replacement Integration