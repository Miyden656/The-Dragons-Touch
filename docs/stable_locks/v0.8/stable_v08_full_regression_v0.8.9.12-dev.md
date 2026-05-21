# v0.8.9.12-dev — Stable v0.8 Full Regression Pass

## Purpose

This is the final broad regression pass before Stable v0.8 Lock.

No new features should be added in this patch unless a regression fails and requires a focused hotfix.

## Stable v0.8 Candidate Definition

Stable v0.8 means:

- The desktop UI can run a clean local Commander deck review.
- `main.py` remains the backend source of truth.
- User-Facing Mode is the default.
- Dev-Facing Mode remains available for active development/testing.
- Combo Awareness remains opt-in.
- Report-section Combo Awareness embeds enough summary context in the normal deck report and AI handoff prompt that users do not need separate combo files.
- Full breakdown artifacts remain optional/dev-facing support files.
- No Commander Spellbook/API calls are made.
- Large local combo data and generated indexes are protected by `.gitignore`.

## Full Regression Matrix

### 1. Launch / UI Shell

- PASS / FAIL — App launches.
- PASS / FAIL — UI/backend labels show v0.8.9.12-dev where applicable.
- PASS / FAIL — Navigation still loads all expected pages.
- PASS / FAIL — User-Facing Mode remains default.
- PASS / FAIL — Dev-Facing Mode is still accessible for active development/testing.

### 2. Deck Selection

- PASS / FAIL — Deck Selection loads.
- PASS / FAIL — Deck file can be selected.
- PASS / FAIL — Deck preview still displays useful deck information.
- PASS / FAIL — Archidekt/plain-text export guidance remains visible.
- PASS / FAIL — No helper-dragon loading visual appears on idle pages.

### 3. Review Setup

- PASS / FAIL — Output Mode selector works.
- PASS / FAIL — Review Direction selector works.
- PASS / FAIL — Review Intensity / Cut Depth selector works.
- PASS / FAIL — Prompt Mode selector works.
- PASS / FAIL — Intended Bracket selector works.
- PASS / FAIL — Budget field still updates run settings.
- PASS / FAIL — Combo Awareness selector remains opt-in.

### 4. Philosophy Lens

- PASS / FAIL — Philosophy Lens page loads.
- PASS / FAIL — Philosophy wording remains guidance-only.
- PASS / FAIL — Philosophy selection still maps into the run.

### 5. Collection Source

- PASS / FAIL — Collection Source page loads.
- PASS / FAIL — Collection Source wording makes collection optional.
- PASS / FAIL — Entire collection folder mode still works.
- PASS / FAIL — Selected-file mode still works if tested.
- PASS / FAIL — Collection-only/prefer-collection settings remain clear.

### 6. Run Analysis

- PASS / FAIL — Run Analysis page loads.
- PASS / FAIL — User-Facing Mode does not expose Advanced Run Details by default.
- PASS / FAIL — Dev-Facing Mode exposes Advanced Run Details.
- PASS / FAIL — Guarded confirmation still appears before backend execution.
- PASS / FAIL — Helper-dragon forge/loading canvas appears only during active run.
- PASS / FAIL — Successful run opens Report Viewer automatically.
- PASS / FAIL — Failed/non-zero run does not auto-open Report Viewer.
- PASS / FAIL — No API calls.

### 7. Report Viewer

- PASS / FAIL — Report Viewer opens after successful run.
- PASS / FAIL — User-Facing Mode focuses on normal/player-facing reports.
- PASS / FAIL — Dev-Facing Mode shows Breakdown Reports.
- PASS / FAIL — Normal deck report loads.
- PASS / FAIL — Debug/breakdown report loads in Dev-Facing Mode.
- PASS / FAIL — Report Viewer still treats markdown/text as plain readable text.

### 8. Combo Awareness Four-Mode Matrix

Test these modes with known decks:

#### Disabled

- PASS / FAIL — No combo artifacts write.
- PASS / FAIL — Normal deck report does not include Combo Awareness.
- PASS / FAIL — User-guided prompt does not include Combo Awareness AI Handoff Addendum.

#### Report Section only

- PASS / FAIL — `normal/combo_awareness_report_section.md` writes.
- PASS / FAIL — Normal deck report includes `## Combo Awareness`.
- PASS / FAIL — User-guided prompt includes `## Combo Awareness AI Handoff Addendum`.
- PASS / FAIL — Deck report includes relevant potential combo count.
- PASS / FAIL — Deck report includes collection-completable count or collection-not-loaded note.
- PASS / FAIL — User does not need separate combo files for AI interactive prompt.

#### Full Debug Breakdown only

- PASS / FAIL — `debug/combo_awareness_breakdown.md` writes.
- PASS / FAIL — Normal deck report does not include Combo Awareness.
- PASS / FAIL — User-guided prompt does not include Combo Awareness AI Handoff Addendum.
- PASS / FAIL — Breakdown wording no longer says app/main/normal report integration was not performed.

#### Both report section and breakdown

- PASS / FAIL — Both combo artifacts write.
- PASS / FAIL — Normal deck report includes `## Combo Awareness`.
- PASS / FAIL — User-guided prompt includes `## Combo Awareness AI Handoff Addendum`.
- PASS / FAIL — Deck report includes relevant potential combo count.
- PASS / FAIL — Deck report includes collection-completable count or collection-not-loaded note.
- PASS / FAIL — Breakdown remains optional/dev-facing.

### 9. Output / File Hygiene

- PASS / FAIL — Output folder is deck-distinguished and timestamped.
- PASS / FAIL — Report paths are detected from backend stdout.
- PASS / FAIL — `.gitignore` includes `data/combo.json`.
- PASS / FAIL — `.gitignore` includes `data/commander_spellbook/combo_index.json`.
- PASS / FAIL — `.gitignore` includes `data/commander_spellbook/combo_index_parity.json`.
- PASS / FAIL — Generated output folders are not staged for commit.
- PASS / FAIL — Large local combo files are not staged for commit.

## Suggested Minimum Test Decks

- Normal/no-combo or Combo Awareness Disabled deck.
- Report Section only deck with at least some potential combos.
- Full Debug Breakdown only deck with known combos.
- Both mode deck with known combos and collection-completable potential combos.
- One deck in User-Facing Mode.
- One deck in Dev-Facing Mode.

## Pass Criteria

Stable v0.8 can proceed to lock when:

- The app launches cleanly.
- Compile checks pass.
- Run Analysis and Report Viewer work.
- User-Facing/Dev-Facing split remains stable.
- Combo Awareness four-mode matrix passes.
- Normal report and user-guided prompt include Combo Awareness only when opted in via report-section modes.
- No API calls occur.
- Large combo data/index files remain ignored.

## If Anything Fails

Do not add new features.

Create a focused hotfix:

`v0.8.9.12.1-dev — <specific failed area> Hotfix`

Then rerun only the impacted regression area plus one end-to-end smoke test.
