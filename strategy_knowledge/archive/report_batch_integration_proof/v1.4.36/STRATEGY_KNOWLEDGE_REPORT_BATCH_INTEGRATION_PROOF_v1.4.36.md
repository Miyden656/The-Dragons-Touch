# Report / Batch Integration Proof — v1.4.36

## Result

- Report/batch integration proven: True
- Active scoring profiles: 249
- Legacy preview status: deprecated_fallback_only
- Sample deck count: 3
- main.py changed: False

## Batch Summary

- deck_count: 3
- all_decks_active_scoring_249: True
- all_decks_legacy_preview_fallback: True
- all_decks_have_top_matches: True
- all_direct_reports_have_249_language: True
- all_direct_prompts_have_249_language: True
- all_wrappers_available: False
- all_wrapper_reports_have_249_language: False
- all_wrapper_prompts_have_249_language: False
- bridge_writer_available: False
- all_bridge_payloads_active_249: False
- no_old_misleading_language: False

## Sample Deck Proofs

### Witherbloom Creature-Affinity X-Spells Smoke Test
- Commander: Witherbloom, the Balancer
- Active scoring profiles: 249
- Legacy preview status: deprecated_fallback_only
- Top matches: Spellslinger, Tokens, X-Spells / Big Spells, Go-Wide Combat, Aristocrats

### Miirym Dragon Copy Smoke Test
- Commander: Miirym, Sentinel Wyrm
- Active scoring profiles: 249
- Legacy preview status: deprecated_fallback_only
- Top matches: Dragon Typal, Saboteur / Combat Damage Triggers, Shared Combat Incentive, Forced Combat / Goad, Blink / Flicker

### Artifact Tokens Utility Smoke Test
- Commander: Toggo, Goblin Weaponsmith
- Active scoring profiles: 249
- Legacy preview status: deprecated_fallback_only
- Top matches: Tokens, Treasure, Equipment, Food, Food

## Gate Checks

- active_scoring_profiles_is_249: True
- legacy_preview_is_fallback_only: True
- top_matches_available_for_all_samples: True
- direct_report_sections_surface_249_language: True
- direct_prompt_blocks_surface_249_language: True
- wrapper_helpers_available: False
- wrapper_reports_surface_249_language: False
- wrapper_prompts_surface_249_language: False
- bridge_writer_available: False
- bridge_payloads_active_249: False
- old_misleading_five_profile_language_absent: False
- main_py_not_changed: True

## Boundary

- This patch proves report/helper/batch surfaces can call the 249-profile active scorer.
- It does not change `main.py`.
- It does not remove legacy fallback.

## Next Safe Step

v1.4.37 — Strategy Knowledge Scoring Regression / Old-vs-New Comparison
