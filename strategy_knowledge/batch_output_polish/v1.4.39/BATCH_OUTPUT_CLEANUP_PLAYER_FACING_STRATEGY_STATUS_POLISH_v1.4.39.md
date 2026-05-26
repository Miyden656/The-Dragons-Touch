# Batch Output Cleanup / Player-Facing Strategy Status Polish — v1.4.39

## Result

- Player-facing strategy status polished: True
- Batch output cleanup guidance installed: True
- Active scoring profiles: 249
- Legacy preview profile count: 5
- Legacy preview status: deprecated_fallback_only
- Scoring source: `strategy_knowledge/index/strategy_profile_index.latest.json`
- Top matches available: True
- main.py changed: False

## Source Patch

- Candidate files inspected: 6
- Patched files: 0


## Player-Facing Status Block

## Strategy Knowledge Status

- Strategy Knowledge: Active
- Active scoring profiles: 249
- Scoring source: `strategy_knowledge/index/strategy_profile_index.latest.json`
- Use: strategy recognition, cut/protect/replacement guidance, and AI handoff context.
- Legacy five-profile preview: fallback only

### Top Strategy Matches
- **Spellslinger** (`spellslinger`), score 67.832 — hits: artifacts, combat, lifegain, recursion, sacrifice
- **Tokens** (`tokens`), score 64.079 — hits: artifacts, combat, lifegain, recursion, sacrifice
- **Equipment** (`equipment`), score 57.388 — hits: artifacts, combat, equipment, lifegain, recursion
- **Lifegain** (`lifegain`), score 53.877 — hits: artifacts, combat, lifegain, recursion, sacrifice
- **Landfall / Lands Matter** (`landfall_lands_matter`), score 48.577 — hits: artifacts, combat, landfall, lifegain, recursion

## Batch Global Status Block

## Batch Strategy Knowledge Status

- Strategy Knowledge: Active
- Active scoring profiles: 249
- Scoring source: `strategy_knowledge/index/strategy_profile_index.latest.json`
- Legacy five-profile preview: fallback only
- Batch behavior: show this global status once, then show deck-specific top strategy matches per deck.

## Gate Checks

- active_scoring_profiles_is_249: True
- legacy_preview_profile_count_is_5: True
- legacy_preview_is_fallback_only: True
- top_matches_available: True
- player_status_surfaces_249: True
- player_status_marks_legacy_fallback: True
- batch_status_surfaces_249: True
- batch_status_marks_legacy_fallback: True
- sanitizer_removes_old_five_profile_line: False
- sanitizer_relabels_loaded_role_profiles: False
- strategy_sections_helpers_present: True
- strategy_live_bridge_helper_present: True
- main_py_not_changed: True

## Boundary

- This patch polishes player-facing/batch strategy status language.
- It keeps debug/fallback details available without presenting the five-profile preview as the active library.
- It does not change `main.py`.

## Next Safe Step
