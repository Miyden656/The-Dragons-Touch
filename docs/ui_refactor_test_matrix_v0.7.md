# The Dragon's Touch v0.7 UI Refactor Test Matrix

## Purpose
This test matrix protects the locked v0.6.8.5 workflow while the one-script UI is split into modules during v0.7 Alpha Hardening.

Locked workflow:
`UI staged state -> guarded confirmation -> subprocess/main.py -> CLI input bridge -> backend output folder -> report detection -> Report Viewer plain-text load`

---

# Always-Run Smoke Test After Every v0.7 Refactor Patch

## App Launch / Version
- Pass/Fail: App launches from the same command as before.
- Pass/Fail: UI still identifies itself as v0.7.x Alpha Foundation / Alpha Hardening.
- Pass/Fail: No import errors occur.
- Pass/Fail: No startup crash occurs.

## Navigation
- Pass/Fail: Deck Selection opens.
- Pass/Fail: Review Setup opens.
- Pass/Fail: Philosophy Lens opens.
- Pass/Fail: Collection Source opens.
- Pass/Fail: Run Analysis opens.
- Pass/Fail: Report Viewer opens.
- Pass/Fail: Future/placeholder pages remain visibly future/placeholder.

## State Preservation
- Pass/Fail: Selected deck remains staged after navigating away.
- Pass/Fail: Review Setup choices remain staged after navigating away.
- Pass/Fail: Philosophy choices remain staged after navigating away.
- Pass/Fail: Collection choices remain staged after navigating away.
- Pass/Fail: Run Analysis reads the latest staged values.

## Guarded Run Boundary
- Pass/Fail: Run button does not silently execute backend.
- Pass/Fail: Guarded confirmation appears.
- Pass/Fail: Cancel prevents execution.
- Pass/Fail: Confirm executes through `main.py`.
- Pass/Fail: No second backend workflow appears.

## Output / Report
- Pass/Fail: Output folder is created after confirmed run.
- Pass/Fail: Output folder includes commander name.
- Pass/Fail: Output folder includes source deck filename distinction.
- Pass/Fail: Output folder includes timestamp.
- Pass/Fail: `normal/` folder exists.
- Pass/Fail: `debug/` folder exists.
- Pass/Fail: Report detection finds the latest run.
- Pass/Fail: Report Viewer loads report as plain text.

---

# Patch-Specific Test Focus

## v0.7.2 — Constants and Version Labels Extraction
- Pass/Fail: App launches.
- Pass/Fail: Version label still displays correctly.
- Pass/Fail: Backend stable lock wording still displays correctly.
- Pass/Fail: Dropdown options still populate correctly.
- Pass/Fail: Future feature labels still display correctly.
- Pass/Fail: No behavior changes are observed.

## v0.7.3 — Theme / QSS Extraction
- Pass/Fail: App launches.
- Pass/Fail: Dragon Forge theme still displays correctly.
- Pass/Fail: Adventurer's Map theme still displays correctly.
- Pass/Fail: Theme toggle works.
- Pass/Fail: Combo popup styling still works.
- Pass/Fail: Text remains readable.
- Pass/Fail: No flat/generic visual regression appears.

## v0.7.4 — Shared Widget Extraction
- Pass/Fail: Textured panels still render.
- Pass/Fail: Sidebar buttons still render.
- Pass/Fail: Badges still render.
- Pass/Fail: Report cards still render.
- Pass/Fail: Stat cards still render.
- Pass/Fail: Button click behavior remains intact.

## v0.7.5 — Staged State Object Extraction
- Pass/Fail: Selected deck persists across navigation.
- Pass/Fail: Review Setup staging persists.
- Pass/Fail: Philosophy staging persists.
- Pass/Fail: Collection staging persists.
- Pass/Fail: Run Analysis summary reads current state.
- Pass/Fail: CLI bridge preview reads current state.
- Pass/Fail: No stale/default values overwrite user selections.

## v0.7.6 — Report Detection Service Extraction
- Pass/Fail: Latest output folder is detected.
- Pass/Fail: Normal report folder is detected.
- Pass/Fail: Debug report folder is detected.
- Pass/Fail: Missing report state is handled gracefully.
- Pass/Fail: Repeated same-deck runs create separate folders.
- Pass/Fail: Report Viewer does not load an older report after a new run.

## v0.7.7 — Backend Runner / CLI Bridge Extraction
- Pass/Fail: Guarded confirmation still appears.
- Pass/Fail: Cancel prevents backend execution.
- Pass/Fail: Confirm runs `main.py`.
- Pass/Fail: CLI input order matches previous behavior.
- Pass/Fail: Interactive mode still asks one section at a time.
- Pass/Fail: One-shot worksheet mode remains available.
- Pass/Fail: Intended Bracket reaches prompt/report.
- Pass/Fail: Budget Note reaches prompt/report.
- Pass/Fail: Collection Mode/Source reaches prompt/report.

## v0.7.8 — Report Viewer Page Extraction
- Pass/Fail: Report Viewer opens.
- Pass/Fail: File list refreshes.
- Pass/Fail: Plain-text report loads.
- Pass/Fail: Search works.
- Pass/Fail: Copy works.
- Pass/Fail: Refresh works.
- Pass/Fail: Open current report works.
- Pass/Fail: Open current report folder works.
- Pass/Fail: Open output folder works.
- Pass/Fail: No deep markdown renderer is introduced.

## v0.7.9 — Deck Selection Page Extraction
- Pass/Fail: Deck file picker opens.
- Pass/Fail: Deck path displays.
- Pass/Fail: Deck preview loads.
- Pass/Fail: Commander displays.
- Pass/Fail: Partner commander preview still works if applicable.
- Pass/Fail: Companion/reference companion preview still works if applicable.
- Pass/Fail: Deck size/count displays.
- Pass/Fail: Selected deck reaches Run Analysis.

## v0.7.10 — Review Setup / Philosophy / Collection Page Extraction
- Pass/Fail: Review Setup controls update summary immediately.
- Pass/Fail: Cut-down shows Review Intensity.
- Pass/Fail: Build-up shows Build-Up Mode.
- Pass/Fail: No Apply Settings workflow returns.
- Pass/Fail: Philosophy Lens staging works.
- Pass/Fail: Guide Presentation staging works.
- Pass/Fail: Collection Mode staging works.
- Pass/Fail: Collection Source folder/file picking works.
- Pass/Fail: All staged values reach Run Analysis.

## v0.7.11 — Run Analysis Page Extraction
- Pass/Fail: Run Analysis page opens.
- Pass/Fail: Readiness summary displays selected deck.
- Pass/Fail: Readiness summary displays Review Setup choices.
- Pass/Fail: Readiness summary displays Philosophy choices.
- Pass/Fail: Readiness summary displays Collection choices.
- Pass/Fail: Guarded confirmation appears.
- Pass/Fail: Confirm runs `main.py`.
- Pass/Fail: Report detection runs after process completion.
- Pass/Fail: Report Viewer can load generated output.

## v0.7 Launcher Track
- Pass/Fail: Launcher opens UI only.
- Pass/Fail: Launcher does not require Visual Studio Code.
- Pass/Fail: Launcher does not silently run deck analysis.
- Pass/Fail: Launcher uses correct working directory.
- Pass/Fail: Desktop shortcut opens UI.
- Pass/Fail: README_START_HERE explains setup clearly.

---

# Scope Guard Checks

## Future Feature Boundaries
- Pass/Fail: Commander Spellbook/API remains disabled.
- Pass/Fail: Batch/Aggregate remains placeholder unless entering v0.7.x.
- Pass/Fail: Replacement Candidate Engine is not introduced.
- Pass/Fail: No automatic deck edits are introduced.
- Pass/Fail: No silent backend run path exists.
- Pass/Fail: No second backend workflow exists.
