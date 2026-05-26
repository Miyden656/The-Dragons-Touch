# Strategy Knowledge Active Scoring Expansion — v1.4.35

## Result

- Active scoring profiles: 249
- Scoring source: `strategy_knowledge/index/strategy_profile_index.latest.json`
- Legacy preview profile count: 5
- Legacy preview status: deprecated_fallback_only
- Active scoring wiring performed: True
- main.py changed: False

## Top Matches

1. **Aristocrats** (`aristocrats`) — score 93.152
   - Hits: aristocrats, artifacts, combat, combo, counters, graveyard, lifegain, recursion, sacrifice, tokens
2. **Voltron** (`voltron`) — score 88.671
   - Hits: artifacts, combat, combo, counters, graveyard, lifegain, recursion, sacrifice, tokens, voltron
3. **Spellslinger** (`spellslinger`) — score 88.372
   - Hits: artifacts, combat, combo, counters, graveyard, lifegain, recursion, sacrifice, spellslinger, tokens
4. **Tokens** (`tokens`) — score 84.797
   - Hits: artifacts, combat, combo, counters, graveyard, lifegain, recursion, sacrifice, tokens
5. **Control** (`control`) — score 74.254
   - Hits: artifacts, combat, combo, control, counters, graveyard, lifegain, recursion, sacrifice, tokens
6. **Enchantress** (`enchantress`) — score 72.825
   - Hits: artifacts, combat, combo, counters, enchantress, graveyard, lifegain, recursion, sacrifice, tokens
7. **Lifegain** (`lifegain`) — score 70.787
   - Hits: artifacts, combat, combo, counters, graveyard, lifegain, recursion, sacrifice, tokens
8. **Landfall / Lands Matter** (`landfall_lands_matter`) — score 69.258
   - Hits: artifacts, combat, combo, counters, graveyard, landfall, lifegain, recursion, sacrifice, tokens
9. **Combo** (`combo`) — score 69.214
   - Hits: artifacts, combat, combo, counters, graveyard, lifegain, recursion, sacrifice, tokens
10. **Mill** (`mill_05_1_niche_theme_rules`) — score 66.429
   - Hits: artifacts, combat, combo, counters, graveyard, lifegain, mill, recursion, sacrifice, tokens
11. **Mill** (`mill_02_mechanical_themes_micro_archetypes`) — score 66.397
   - Hits: artifacts, combat, combo, counters, graveyard, lifegain, mill, recursion, sacrifice, tokens
12. **Food** (`food_05_1_niche_theme_rules`) — score 66.397
   - Hits: artifacts, combat, combo, counters, food, graveyard, lifegain, recursion, sacrifice, tokens
13. **Food** (`food_02_mechanical_themes_micro_archetypes`) — score 66.364
   - Hits: artifacts, combat, combo, counters, food, graveyard, lifegain, recursion, sacrifice, tokens
14. **Vehicles** (`vehicles_05_1_niche_theme_rules`) — score 64.794
   - Hits: artifacts, combat, combo, counters, graveyard, lifegain, recursion, sacrifice, tokens, vehicles
15. **Vehicles** (`vehicles_02_mechanical_themes_micro_archetypes`) — score 64.762
   - Hits: artifacts, combat, combo, counters, graveyard, lifegain, recursion, sacrifice, tokens, vehicles

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
