# Strategy Knowledge — v1.5 Layout

This folder owns the strategy profile catalog that drives Build Setup Panel choices, the deck builder's Strategy bucket selection, and report strategy sections.

## Active runtime (the load-bearing core)

```text
strategy_selector_catalog.py    Lookup chain for strategy display name -> role_tags
strategy_role_tag_profiles.py   46 hand-curated strategy-defining tag sets (v1.5)
adapter_boundary.py             Package boundary contract
__init__.py                     Package init
index/
  strategy_profile_index.latest.json   The 249-profile index built from layers/
layers/
  *.md (249 files)              Source markdown for each strategy profile
import_staging/
  *.md (250 files)              Staged copies; preserved for index rebuilds
import_sources/                 Original ingest source
```

`role_tags_for_display_name` (in `strategy_selector_catalog.py`) is the entry point. It tries:

1. Curated profiles in `strategy_role_tag_profiles.py` (sharp 5-15 tag sets for ~46 strategies)
2. The 249-profile index (placeholder utility tags filtered out)
3. Legacy `analysis/strategy_scoring.py:ARCHETYPE_DEFINITIONS` (22 macro archetypes)

## archive/

Contains 22 v1.4.x phase-output subdirectories that were checkpoints during the multi-version Strategy Knowledge buildout. They have **zero Python references anywhere in the codebase** as confirmed by audit:

```text
archive/active_scoring/                     archive/loader_previews/
archive/batch_output_polish/                archive/loaders/
archive/bridge_previews/                    archive/promotion_plan/
archive/default_candidate/                  archive/regression/
archive/expanded_strategy_scoring_lock/     archive/report_batch_integration_proof/
archive/import_batches/                     archive/report_generator_integration/
archive/import_plans/                       archive/scoring_regression/
archive/inventory_audit/                    archive/shadow_compare/
archive/legacy_mapping/                     archive/stable_lock/
archive/live_profile_status/                archive/tags/
archive/live_promotion/                     archive/templates/
```

These are kept for historical traceability. Safe to delete entirely if disk space becomes a concern.

## Still-referenced legacy subdirectories (not yet archived)

The following 18 subdirectories are referenced by string-path lookups in `reports/strategy_bridge/strategy_v1_4_regression_lock_candidate.py` and similar audit scripts. **They cannot be moved to archive/ without also updating those scripts' string paths.**

```text
card_candidates/        finished_mana_base/   live_replacement/    role_counts/
cut_protect_replacement/ full_draft_preview/  mana_base/           role_mapping/
deprecation/            land_deck_write/      report_viewer_handoff/  runtime/
final_deck_export/      land_insertion/       scoring_previews/    shell_planning/
final_inclusion_lock/   live_bridge/
```

The 18 calling scripts in `reports/strategy_bridge/` are themselves alive in the import graph but feed dev-mode-only Build From Collection preview cards. A future runtime trace pass can confirm they're inert in user mode, at which point both the scripts and these subdirectories can be archived together.

## Quality notes (historical, retained from v1.4.0 schema lock)

Every runtime-ready strategy file in `layers/` is at least 40 KB and includes the canonical markdown sections.

Layer IDs:

```text
01_macro_archetypes
02_mechanical_themes
03_strategic_board_politics
04_typal_tribal_themes
05_1_niche_theme_rules
05_2_fringe_theme_rules
05_3_emergent_theme_rules
```

Basic land policy (preserved from v1.3): all strategy files assume `basic_land_policy: "assume_available"`.

Nonbasic land policy: `collection_first_unless_upgrades_allowed`.

## How to add a curated strategy profile

See [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md#how-to-extend) for the full extension recipe. Short version: edit `strategy_role_tag_profiles.py`, add a key under the appropriate category dict (`_MACRO`, `_MECHANICAL`, `_TYPAL`, `_STRATEGIC`), pick 5-15 strategy-DEFINING tags from `analysis/role_tags.py`'s vocabulary, and avoid generic utility tags (ramp/card_draw/protection/removal/recursion/board_wipe) unless the strategy IS that utility.
