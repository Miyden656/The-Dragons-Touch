# Changelog

All notable changes are tracked here, reconstructed from git commit history. Dates are approximate (commit dates).

---

## v1.5.0 — 2026-05-27 — Bin B Items 5-6 + cleanup pass

Highlights:

- **Item 5 — Combo-aware scoring**: New `build_from_collection/combo_scorer.py` plugs the existing Commander Spellbook combo index (~88k combos) into the deck builder. Persona orientation (`leaning` / `averse` / `neutral`) drives per-card modifiers capped at ±6.0. Combo Builder personas now visibly pull storm enablers and combo pieces in; Let Me Do My Thing personas push them out.
- **Item 6 Phase A — Role-tag fixes**: Narrowed false-positive board_wipe patterns in `analysis/role_tags.py`. Added `shroud` + `totem armor` to protection keywords. New `analysis/role_tag_overrides.py` — 51 hand-curated EDH staples with tag adds/removes (Demonic Consultation no longer false board_wipe; Phyrexian Altar, Sensei's Top, LED, Underworld Breach correctly tagged as combo pieces).
- **Item 6 Phase B — Strategy profile differentiation**: Discovered all 249 strategy profiles in the index had identical generic 17-tag `role_tags` (placeholder data). New `strategy_knowledge/strategy_role_tag_profiles.py` ships 46 hand-curated strategy-defining tag sets covering all 9 Macro + 20 Mechanical + 9 Typal + 8 Strategic. Wired into `role_tags_for_display_name` with consult-overrides-first pattern. Placeholder fingerprint detection strips utility-bucket-conflicting tags from non-curated strategies. Result: same commander/collection now produces visibly different decks per strategy choice; all utility buckets fill to target.
- **Cleanup**: Deleted `Refracting on markdown/` (19 stale source duplicates from rolled-back refactor), 6 confirmed-dead `reports/strategy_bridge/*.py` scripts, 2 `.before_v1.4.40.7.2.py` backup files, `strategy_knowledge/strategy_quality_audit.json` (3.6 MB), 4 stale root README .txt packaging artifacts, empty `Old Do Not Use/` folder. Net: ~5 MB freed, no runtime impact.
- **Documentation**: New `docs/ARCHITECTURE.md`, this `CHANGELOG.md`, updated root `README.md`, `VERSION` file pinned.

---

## v1.4.x — Strategy Knowledge expansion

Multi-version arc that built the 249-profile strategy index and the supporting pipeline. Phase artifacts (one JSON + one MD per phase) for each v1.4.10–v1.4.41 step are preserved under `strategy_knowledge/` subdirectories pending archive reorganization.

Selected milestones from commit history:

- v1.4.10 — Scoring previews
- v1.4.11 — Role mapping
- v1.4.12 — Cut-protect-replacement contract
- v1.4.13 — Report viewer handoff preview
- v1.4.14 — Shell planning
- v1.4.15 — Exact card candidates
- v1.4.16 — Role count plan
- v1.4.17 — Mana base planning
- v1.4.18 — Land insertion preview
- v1.4.19 — Full 100-card draft preview
- v1.4.20 — Live replacement map
- v1.4.21 — Live bridge preview
- v1.4.22 — Final inclusion lock
- v1.4.23 — Finished mana base
- v1.4.24 — Land deck write
- v1.4.25 — Final deck export
- v1.4.26 — Old strategy system deprecation
- v1.4.30 — Import staging
- v1.4.40 — Diagnostics package
- v1.4.41 — Expanded strategy scoring stable lock

---

## v0.12.x — Beta tester documentation polish — 2026-05 (pre-merge)

- v0.12.0 — Source-run beta smoke test checklist locked
- v0.12.1 — README quickstart polish locked
- v0.12.2 — First-run troubleshooting section patched

---

## v0.11 Stable — Source-Run Beta Handoff Lock — 2026-04

Locked the source-run beta path. EXE/installer path paused due to Windows security concerns with unsigned binaries.

---

## v0.10 Stable Release — 2026-03

Stable release lock.

---

## v0.9 — 2026-02

Replacement candidate engine foundation locked.

---

## v0.8.5 to v0.8.10.1-alpha — 2026-01

- Combo Awareness early implementation
- UI cleanup
- Alpha Handoff polish

---

## v0.7 Modular Alpha — 2025-12

- Modular alpha checkpoint through v0.7.22
- Alpha Tester Feedback Packet
- Repo structure cleanup for v0.7 alpha handoff

---

## v0.6.x — 2025-11

- v0.6 stable lock through v0.6.7.7.2
- UI foundation, staging, runtime preview, bridge preview
- Run Analysis cleanup
- Desktop UI Foundation lock

---

## Earlier history

Pre-v0.6 history is preserved in commit log. Reach for `git log --oneline` for the full picture.
