# The Dragon’s Touch — v1.4 Stable Handoff Prompt

You are helping continue development of The Dragon’s Touch, a local Python-based Magic: The Gathering Commander deck review and deck-building assistant.

## Current Stable Version

v1.4 — Strategy Deep Dive / Strategy Knowledge Live Replacement

Status: STABLE_LOCK_PASS

## What v1.4 Locked

- Strategy Knowledge Base schema and verifier foundation.
- Strategy Knowledge loader/runtime preview and default-candidate path.
- Strategy scoring, role buckets, cut/protect/replacement integration.
- Report Viewer and AI handoff integration.
- Build From Collection strategy shell planning.
- exact-card candidate preview, role-count generation, mana-base planning, land insertion preview.
- full 100-card draft preview.
- opt-in live bridge through `TDT_STRATEGY_KNOWLEDGE_LIVE_BRIDGE`.
- final inclusion lock artifacts.
- finished mana-base artifacts.
- land deck-write artifacts.
- final deck export artifacts.
- old strategy system deprecation/fallback policy.
- v1.4 full regression lock-candidate validation.

## Safety Boundary

- Old strategy files were not deleted.
- Legacy fallback was not disabled.
- Rollback remains available.
- The old strategy system is deprecated fallback only.
- Save a clean v1.4 stable backup before starting new development.

## Patch Workflow Reminder

- Use small versioned patches.
- Include `tools/apply_vX.X.X_name.py`.
- Include `tools/verify_vX.X.X_name.py`.
- Include `docs/patch_history/README_PATCH_vX.X.X_name.txt`.
- Archive one-time patch tools under `Old Do Not Use/One-time patch tools/<parent version>/`.
- Subpatches archive under their parent version folder.
