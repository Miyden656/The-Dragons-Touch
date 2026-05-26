# Active Scoring Report Generator Integration — v1.4.38

- Recovery version: v1.4.38.2
- Report generator integration performed: True
- Active scoring profiles: 249
- Legacy preview profile count: 5
- Legacy preview status: deprecated_fallback_only
- Scoring source: `strategy_knowledge/index/strategy_profile_index.latest.json`
- Top matches available: True
- main.py changed: False

## Source Checks

### `reports/strategy_knowledge_sections.py`
- exists: True
- changed: False
- changes: ['replace:Legacy Fallback Strategy Role Profiles', 'replace:Strategy Knowledge Integration']
- has_marker: True
- has_active_scoring_call: True
- raw_old_five_profile_line_present: False

### `reports/strategy_live_bridge.py`
- exists: True
- changed: False
- changes: []
- has_helper: True
- has_active_scoring_profiles_key: True

## Gate Checks

- active_scoring_profiles_is_249: True
- legacy_preview_profile_count_is_5: True
- legacy_preview_is_fallback_only: True
- top_matches_available: True
- strategy_sections_has_active_scoring_surface: True
- live_bridge_has_active_scoring_surface: True
- generated_report_smoke_surfaces_249: True
- generated_report_smoke_marks_legacy_fallback: True
- generated_report_smoke_omits_old_misleading_language: False
- main_py_not_changed: True

## Next Safe Step

v1.4.39 — Batch Output Cleanup / Player-Facing Strategy Status Polish
