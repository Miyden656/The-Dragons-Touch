# Strategy Knowledge 249-File Inventory / Import Readiness Audit — v1.4.29

## Result

- Runtime behavior changed: False
- Import performed: False
- Source ZIP exists: True
- External importable strategy profile files: 249
- External unique strategy slugs: 244
- Duplicate source strategy slugs: 5
- Current live strategy profiles: 5
- Already live from source: 5
- Missing unique source slugs from live: 239

## Gate Checks

- source_zip_exists: True
- source_zip_has_249_importable_strategy_profiles: True
- source_zip_folder_counts_match_expected: True
- current_live_profile_count_detected: True
- current_live_profile_count_is_5_sample_profiles: True
- gap_detected_between_source_and_live: True
- no_runtime_behavior_changed: True

## Source Folder Counts

- 01_macro_archetypes_commander: 9 / 9
- 02_mechanical_themes_micro_archetypes: 37 / 37
- 03_strategic_board_politics: 42 / 42
- 04_typal_tribal_themes: 44 / 44
- 05_1_niche_theme_rules: 40 / 40
- 05_2_fringe_theme_rules: 40 / 40
- 05_3_emergent_theme_rules: 37 / 37

## Current Live Profiles

- Aristocrats (`aristocrats`) — `strategy_knowledge/layers/02_mechanical_themes/aristocrats.md`
- Landfall / Lands Matter (`landfall_lands_matter`) — `strategy_knowledge/layers/02_mechanical_themes/landfall_lands_matter.md`
- Spellslinger (`spellslinger`) — `strategy_knowledge/layers/02_mechanical_themes/spellslinger.md`
- Tokens (`tokens`) — `strategy_knowledge/layers/02_mechanical_themes/tokens.md`
- Voltron (`voltron`) — `strategy_knowledge/layers/02_mechanical_themes/voltron.md`

## Interpretation

The v1.4 Strategy Knowledge pipeline is stable, but the full 249-file strategy library is not yet imported into the live `strategy_knowledge/layers/` profile set.

The correct report wording right now is:

> Strategy Knowledge is active with 5 live strategy profiles. The 249-file expanded strategy library is available as an import source but has not yet been imported into live layers.

## Recommended Next Step

v1.4.30 — Strategy Knowledge 249-File Import / Staging

## Duplicate Source Strategy Slugs

These are duplicate import slugs in the 249-file source library. They explain why raw source file count and unique import slug count can differ.

- clues_investigate: 2 files
  - `strategy_deep_dive_knowledge_base/02_mechanical_themes_micro_archetypes/clues_investigate.md`
  - `strategy_deep_dive_knowledge_base/05_1_niche_theme_rules/clues_investigate.md`
- exile_matters_cast_from_exile: 2 files
  - `strategy_deep_dive_knowledge_base/02_mechanical_themes_micro_archetypes/exile_matters_cast_from_exile.md`
  - `strategy_deep_dive_knowledge_base/05_1_niche_theme_rules/exile_matters_cast_from_exile.md`
- food: 2 files
  - `strategy_deep_dive_knowledge_base/02_mechanical_themes_micro_archetypes/food.md`
  - `strategy_deep_dive_knowledge_base/05_1_niche_theme_rules/food.md`
- mill: 2 files
  - `strategy_deep_dive_knowledge_base/02_mechanical_themes_micro_archetypes/mill.md`
  - `strategy_deep_dive_knowledge_base/05_1_niche_theme_rules/mill.md`
- vehicles: 2 files
  - `strategy_deep_dive_knowledge_base/02_mechanical_themes_micro_archetypes/vehicles.md`
  - `strategy_deep_dive_knowledge_base/05_1_niche_theme_rules/vehicles.md`

## Missing From Live — First 40

- adamant
- adventures
- aggro
- aikido_judo
- ally_typal
- alternate_win_conditions
- angel_typal
- anti_combo_social_police
- archenemy_villain_deck
- artifact_lock_null_rod_effects
- artifact_synergy
- artifact_treasure_combo_value
- assassin_typal
- attack_elsewhere_incentive
- attractions
- auras
- bat_rabbit_bloomburrow_style_small_typal
- battle_tribal
- battles_sieges
- blink_flicker
- blood
- blood_tokens_madness_discard_value
- bloodthirst
- bounty_incentivized_combat
- bracket_aware_stax_hatebear_packages
- bracket_pressure_high_power_value
- bribery_gift_based_politics
- cascade
- case_enchantments
- cat_dog_typal
- caves
- chaos
- clash
- classes_as_primary_theme
- cleric_typal
- clues_investigate
- coin_flipping
- collection_aware_replacement_planning
- color_hate
- colorless_restriction_wastes_matters
- ...and 199 more
