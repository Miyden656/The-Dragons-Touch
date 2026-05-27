# Strategy Knowledge Scoring Regression / Old-vs-New Comparison — v1.4.37

## Result

- Regression performed: True
- Active scoring profiles: 249
- Legacy preview profile count: 5
- Legacy preview status: deprecated_fallback_only
- main.py changed: False

## Old vs New Definitions

- Old scoring: legacy five-profile preview set: Aristocrats, Landfall, Spellslinger, Tokens, Voltron
- New scoring: 249-profile Strategy Knowledge index active scoring

## Aggregate

- sample_deck_count: 5
- all_decks_active_scoring_249: True
- all_decks_legacy_preview_fallback_only: True
- all_decks_have_new_matches_not_possible_in_legacy: True
- all_decks_have_top_matches: True
- total_new_matches_not_possible_in_legacy_top_12: 47

## Deck Comparisons

### Witherbloom Creature-Affinity X-Spells Smoke Test
- Commander: Witherbloom, the Balancer
- New finds more than legacy: True
- Legacy-visible matches:
  - Spellslinger (`spellslinger`), score 65.443
  - Tokens (`tokens`), score 63.116
  - Aristocrats (`aristocrats`), score 35.234
  - Voltron (`voltron`), score 30.675
  - Landfall / Lands Matter (`landfall_lands_matter`), score 30.3
- New 249-profile top matches:
  - Spellslinger (`spellslinger`), score 65.443
  - Tokens (`tokens`), score 63.116
  - X-Spells / Big Spells (`x_spells_big_spells`), score 36.288
  - Go-Wide Combat (`go_wide_combat`), score 35.752
  - Aristocrats (`aristocrats`), score 35.234
  - Token Combat / Go-Wide-Go-Tall Hybrid (`token_combat_go_wide_go_tall_hybrid`), score 33.51
  - Samurai / Monk / Mouse / Otter Typal-Spellslinger or Combat Hybrids (`samurai_monk_mouse_otter_typal_spellslinger_or_combat_hybrids`), score 32.079
  - Blood Tokens / Madness / Discard Value (`blood_tokens_madness_discard_value`), score 32.013
- First match impossible in old preview: X-Spells / Big Spells (`x_spells_big_spells`)

### Miirym Dragon Copy Smoke Test
- Commander: Miirym, Sentinel Wyrm
- New finds more than legacy: True
- Legacy-visible matches:
  - Spellslinger (`spellslinger`), score 26.75
  - Tokens (`tokens`), score 25.054
  - Landfall / Lands Matter (`landfall_lands_matter`), score 25.01
  - Voltron (`voltron`), score 24.924
  - Aristocrats (`aristocrats`), score 23.167
- New 249-profile top matches:
  - Dragon Typal (`dragon_typal`), score 50.018
  - Saboteur / Combat Damage Triggers (`saboteur_combat_damage_triggers`), score 34.35
  - Blink / Flicker (`blink_flicker`), score 34.264
  - Shared Combat Incentive (`shared_combat_incentive`), score 33.921
  - Forced Combat / Goad (`forced_combat_goad`), score 33.904
  - Warrior Typal (`warrior_typal`), score 33.854
  - Extra Combat (`extra_combat`), score 33.854
  - Go-Tall Combat (`go_tall_combat`), score 33.821
- First match impossible in old preview: Dragon Typal (`dragon_typal`)

### Toggo Artifact Tokens / Landfall Smoke Test
- Commander: Toggo, Goblin Weaponsmith
- New finds more than legacy: True
- Legacy-visible matches:
  - Tokens (`tokens`), score 52.034
  - Landfall / Lands Matter (`landfall_lands_matter`), score 34.629
  - Aristocrats (`aristocrats`), score 31.855
  - Voltron (`voltron`), score 31.634
  - Spellslinger (`spellslinger`), score 24.84
- New 249-profile top matches:
  - Tokens (`tokens`), score 52.034
  - Treasure (`treasure`), score 49.92
  - Equipment (`equipment`), score 45.203
  - Food (`food_05_1_niche_theme_rules`), score 43.61
  - Food (`food_02_mechanical_themes_micro_archetypes`), score 43.589
  - Landfall / Lands Matter (`landfall_lands_matter`), score 34.629
  - Artifact/Treasure Combo-Value (`artifact_treasure_combo_value`), score 32.327
  - Aristocrats (`aristocrats`), score 31.855
- First match impossible in old preview: Treasure (`treasure`)

### Life Gain Drain Smoke Test
- Commander: Generic Orzhov Lifegain Commander
- New finds more than legacy: True
- Legacy-visible matches:
  - Aristocrats (`aristocrats`), score 54.54
  - Tokens (`tokens`), score 22.163
  - Landfall / Lands Matter (`landfall_lands_matter`), score 22.124
  - Spellslinger (`spellslinger`), score 21.974
  - Voltron (`voltron`), score 21.569
- New 249-profile top matches:
  - Aristocrats (`aristocrats`), score 54.54
  - Lifegain (`lifegain`), score 41.686
  - Life Total Exchange (`life_total_exchange`), score 29.144
  - Life Total Politics (`life_total_politics`), score 27.569
  - Commander-Defined Single-Card Archetypes (`commander_defined_single_card_archetypes`), score 24.298
  - Commander Tax Advantage (`commander_tax_advantage`), score 24.259
  - Free Interaction / Protection Package (`free_interaction_protection_package`), score 24.158
  - Blood Tokens / Madness / Discard Value (`blood_tokens_madness_discard_value`), score 24.109
- First match impossible in old preview: Lifegain (`lifegain`)

### Vehicle Artifact Combat Smoke Test
- Commander: Generic Jeskai Vehicle Commander
- New finds more than legacy: True
- Legacy-visible matches:
  - Voltron (`voltron`), score 27.8
  - Aristocrats (`aristocrats`), score 23.65
  - Tokens (`tokens`), score 23.608
  - Landfall / Lands Matter (`landfall_lands_matter`), score 23.567
  - Spellslinger (`spellslinger`), score 23.407
- New 249-profile top matches:
  - Equipment (`equipment`), score 44.81
  - Vehicles (`vehicles_05_1_niche_theme_rules`), score 38.091
  - Vehicles (`vehicles_02_mechanical_themes_micro_archetypes`), score 38.072
  - Voltron (`voltron`), score 27.8
  - Aristocrats (`aristocrats`), score 23.65
  - Tokens (`tokens`), score 23.608
  - Landfall / Lands Matter (`landfall_lands_matter`), score 23.567
  - Spellslinger (`spellslinger`), score 23.407
- First match impossible in old preview: Equipment (`equipment`)

## Gate Checks

- regression_performed: True
- active_scoring_profiles_is_249_for_all_samples: True
- legacy_preview_is_fallback_only_for_all_samples: True
- new_scoring_finds_matches_not_possible_in_legacy_for_all_samples: True
- top_matches_available_for_all_samples: True
- total_new_matches_not_possible_in_legacy_positive: True
- main_py_not_changed: True

## Boundary

- This patch proves the expanded scorer finds matches outside the old five-profile preview set.
- It does not change `main.py`.
- It does not remove fallback.

## Next Safe Step

v1.4.38 — v1.4 Expanded Strategy Scoring Lock Candidate
