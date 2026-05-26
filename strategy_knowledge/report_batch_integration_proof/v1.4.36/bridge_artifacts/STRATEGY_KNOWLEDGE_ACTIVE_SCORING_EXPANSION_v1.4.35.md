# Strategy Knowledge Active Scoring Expansion — v1.4.35

## Result

- Active scoring profiles: 249
- Scoring source: `strategy_knowledge/index/strategy_profile_index.latest.json`
- Legacy preview profile count: 5
- Legacy preview status: deprecated_fallback_only
- Active scoring wiring performed: True
- main.py changed: False

## Top Matches

1. **Tokens** (`tokens`) — score 47.216
   - Hits: artifacts, sacrifice, tokens
2. **Treasure** (`treasure`) — score 45.203
   - Hits: artifacts, sacrifice, tokens, treasure
3. **Equipment** (`equipment`) — score 42.059
   - Hits: artifacts, equipment, sacrifice, tokens
4. **Food** (`food_05_1_niche_theme_rules`) — score 38.895
   - Hits: artifacts, food, sacrifice, tokens
5. **Food** (`food_02_mechanical_themes_micro_archetypes`) — score 38.876
   - Hits: artifacts, food, sacrifice, tokens
6. **Landfall / Lands Matter** (`landfall_lands_matter`) — score 31.743
   - Hits: artifacts, landfall, sacrifice, tokens
7. **Voltron** (`voltron`) — score 29.238
   - Hits: artifacts, equipment, sacrifice, tokens
8. **Artifact/Treasure Combo-Value** (`artifact_treasure_combo_value`) — score 27.596
   - Hits: artifacts, sacrifice, tokens, treasure
9. **Aristocrats** (`aristocrats`) — score 27.511
   - Hits: artifacts, sacrifice, tokens
10. **Commander-Created Landfall** (`commander_created_landfall`) — score 27.469
   - Hits: artifacts, landfall, sacrifice, tokens
11. **Treasure Tutor Chains** (`treasure_tutor_chains`) — score 25.219
   - Hits: artifacts, sacrifice, tokens, treasure
12. **Utility Lands Matter** (`utility_lands_matter`) — score 24.06
   - Hits: artifacts, sacrifice, tokens
13. **Blood Tokens / Madness / Discard Value** (`blood_tokens_madness_discard_value`) — score 23.714
   - Hits: artifacts, sacrifice, tokens
14. **Spellslinger** (`spellslinger`) — score 22.929
   - Hits: artifacts, sacrifice, tokens
15. **Clues / Investigate** (`clues_investigate_05_1_niche_theme_rules`) — score 22.46
   - Hits: artifacts, sacrifice, tokens

## Gate Checks

- index_available: True
- index_profile_count_is_249: True
- active_scoring_profiles_is_249: True
- legacy_preview_is_fallback_only: True
- top_matches_available: True
- main_py_not_changed: True

## Boundary

- This patch makes the 249-profile Strategy Knowledge index the active scoring source.
- The old five-profile preview set is retained as fallback only.
- This patch does not change `main.py`.

## Next Safe Step

v1.4.36 — Report / Batch Integration Proof
