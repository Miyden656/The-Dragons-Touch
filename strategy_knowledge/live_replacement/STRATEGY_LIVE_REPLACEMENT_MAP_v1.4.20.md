# v1.4.20 — Strategy Knowledge Live Replacement Audit / Main Pipeline Map

## Purpose

Map exactly where Strategy Knowledge must replace the old live Build From Collection system.

This patch intentionally does not change runtime behavior. It exists to prevent another preview-only patch from being mistaken for the final replacement.

## Current State

- **v1_4_19_passed**: True
- **main_py_has_strategy_knowledge_live_bridge**: False
- **main_py_imports_full_draft_preview**: False
- **selected_executor_still_uses_old_e_model**: True
- **selected_executor_still_claims_no_deck_generation**: True
- **full_100_output_still_scaffold**: True
- **full_100_writer_writes_artifacts**: True
- **strategy_knowledge_report_surfaces_exist**: True
- **report_viewer_full_draft_lane_exists**: True

## Boundaries Still To Cross

### main.py

- Current status: unchanged; normal analysis entrypoint does not route to Strategy Knowledge live deck construction
- Next patch: v1.4.21 — Strategy Knowledge Main Pipeline Opt-In Live Bridge
- Required change: Add an explicit, guarded runtime route that can call Strategy Knowledge build outputs without breaking normal deck review.
- Target files:
  - `main.py`

### final_deck_export

- Current status: disabled; v1.4.19 only writes preview artifacts
- Next patch: v1.4.25 — Final Deck Export Integration
- Required change: Create final deck export artifacts only after final inclusion and land write gates are satisfied.
- Target files:
  - `build_from_collection/output_selected_report_executor.py`
  - `build_from_collection/full_100_card_draft_report_writer.py`
  - `reports/full_100_card_draft_preview.py`

### final_inclusion_lock

- Current status: disabled; exact cards are candidates only and full draft is preview-only
- Next patch: v1.4.22 — Final Inclusion Lock Integration
- Required change: Promote review-only candidates into explicitly locked inclusions with clear source, role, and protection/cut rationale.
- Target files:
  - `reports/exact_card_candidate_preview.py`
  - `reports/full_100_card_draft_preview.py`
  - `build_from_collection/full_100_card_draft_output.py`

### finished_mana_base_generation

- Current status: disabled; mana base exists only as planning guidance
- Next patch: v1.4.23 — Finished Mana Base Generation Integration
- Required change: Convert mana planning bands into a finished land package while preserving basic-land availability and collection-first nonbasic rules.
- Target files:
  - `reports/mana_base_planning.py`
  - `reports/land_insertion_preview.py`
  - `build_from_collection/full_100_card_draft_output.py`

### land_deck_write

- Current status: disabled; v1.4.18 previews slots but does not write lands into a deck
- Next patch: v1.4.24 — Land Deck-Write Integration
- Required change: Write land choices into the draft payload only after finished mana-base generation is available.
- Target files:
  - `reports/land_insertion_preview.py`
  - `reports/full_100_card_draft_preview.py`
  - `build_from_collection/full_100_card_draft_report_writer.py`

## Old System Targets To Replace

- `build_from_collection/strategy_selection.py` — Old commander text heuristic strategy inference / override preview. Replacement: Strategy Knowledge recognition and Strategy Brain runtime selector should become the default source, while user override remains.
- `build_from_collection/strategy_role_mapping.py` — Old strategy-to-role bucket mapping. Replacement: Strategy Knowledge role profiles and role-count target bands should become the live source.
- `build_from_collection/owned_role_classification.py` — Old preview-only owned card role classifier. Replacement: Strategy Knowledge exact-card candidates, cut/protect/replacement signals, and role-count bands should drive live classification.
- `build_from_collection/full_100_card_draft_output.py` — Old full 100-card draft scaffold/model with no true generation. Replacement: Strategy Knowledge full draft payload should become the source for real draft output.
- `build_from_collection/output_selected_report_executor.py` — Current B-E report route executor; E still routes to old full draft model/writer. Replacement: Depth E should route to Strategy Knowledge live full draft construction once final inclusion and land write gates pass.

## Replacement Sequence

- v1.4.21 — Strategy Knowledge Main Pipeline Opt-In Live Bridge
- v1.4.22 — Final Inclusion Lock Integration
- v1.4.23 — Finished Mana Base Generation Integration
- v1.4.24 — Land Deck-Write Integration
- v1.4.25 — Final Deck Export Integration
- v1.4.26 — Old Strategy System Deprecation / Fallback Cleanup
- v1.4.27 — Full Regression / v1.4 Lock Candidate

## Readiness

- Safe to replace blindly: False
- Ready for v1.4.21: True
- Reason: The current project has separate preview artifacts and old live Build From Collection scaffold paths. main.py and depth E output routing must be bridged deliberately.

## Boundary

- No runtime behavior changed.
- No `main.py` behavior changed.
- No final deck export changed.
- No final inclusion lock changed.
- No finished mana-base generation changed.
- No land deck-write changed.
