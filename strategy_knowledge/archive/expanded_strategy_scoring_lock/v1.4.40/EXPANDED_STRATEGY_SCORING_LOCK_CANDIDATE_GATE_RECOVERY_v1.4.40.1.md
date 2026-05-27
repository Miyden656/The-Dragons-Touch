# Expanded Strategy Scoring Lock Candidate — v1.4.40.1 Gate Recovery

## Result

- Lock candidate status: LOCK_CANDIDATE_PASS
- Ready for stable lock: True
- Expanded strategy scoring locked: True
- Indexed profiles: 249
- Active scoring profiles: 249
- Legacy preview profile count: 5
- Legacy preview status: deprecated_fallback_only
- Report/batch integration proven: True
- Scoring regression new matches: 47
- Report generator integration active: True
- Batch output polished: True
- main.py changed: False

## Advisory Tool Summary

- tools_checked: 6
- tools_exited_cleanly: 3
- tools_with_nonzero_exit: ['tools/prove_strategy_knowledge_report_batch_integration.py', 'tools/integrate_active_scoring_into_report_generator.py', 'tools/polish_batch_output_strategy_status.py']
- all_lock_tools_exited_cleanly_advisory: False
- policy: advisory_only_in_v1.4.40.1; lock status is based on artifact and functional gates

## Functional Gate Checks

- live_index_exists: True
- indexed_profile_count_is_249: True
- unique_strategy_id_count_is_249: True
- active_scoring_artifact_exists: True
- active_scoring_profiles_is_249: True
- active_scoring_legacy_preview_is_fallback_only: True
- direct_scoring_profiles_is_249: True
- direct_scoring_top_matches_available: True
- report_batch_proof_exists: True
- report_batch_proof_passed: True
- report_batch_proof_active_249: True
- scoring_regression_exists: True
- scoring_regression_performed: True
- scoring_regression_found_new_matches: True
- report_generator_integration_exists: True
- report_generator_integration_active_249: True
- report_generator_integration_smoke_surfaces_249: True
- batch_output_polish_exists: True
- batch_output_polish_active_249: True
- batch_output_polish_player_status_249: True
- batch_output_polish_batch_status_249: True
- strategy_sections_has_v1_4_39_helper: True
- strategy_sections_lacks_raw_old_five_profile_line: True
- strategy_live_bridge_has_v1_4_39_helper: True
- main_py_exists: True
- main_py_compiles: True
- main_py_not_changed_by_lock_candidate: True
- legacy_fallback_preserved: True

## Stable Lock Meaning

- 249 Strategy Knowledge profiles are live and indexed.
- The active scorer uses 249 profiles.
- The legacy five-profile preview is fallback only.
- Report/helper/batch surfaces can call the 249-profile scorer.
- Player-facing and batch status language now emphasizes active 249-profile scoring.
- `main.py` remains unchanged by this lock candidate.

## Next Safe Step

v1.4.41 — v1.4 Expanded Strategy Scoring Stable Lock / Handoff Package
