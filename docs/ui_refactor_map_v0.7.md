# The Dragon's Touch v0.7 UI Refactor Map

## v0.7.8 update

Report Viewer page construction has been extracted from `ui/dragons_touch_pyside6_workstation.py` into:

`ui/pages/report_viewer_page.py`

The extracted module owns page layout only. MainWindow still owns the active Report Viewer methods and workflow state:

- report file list refresh
- report loading as plain text
- current report search/copy/open actions
- output folder/report folder open buttons
- report detection service wrappers

This keeps the first full-page extraction low risk while reducing the active one-script UI size.

## Still deferred

- Deck Selection page extraction
- Review Setup page extraction
- Philosophy Lens page extraction
- Collection Source page extraction
- Run Analysis page extraction
- `main_window.py` split
- deep markdown rendering
- Commander Spellbook/API integration
- Batch/Aggregate real workflow

## v0.7.9 update

Deck Selection page construction has been extracted from `ui/dragons_touch_pyside6_workstation.py` into:

`ui/pages/deck_selection_page.py`

The extracted module owns page layout only. MainWindow still owns the active Deck Selection behavior and staged-state mutations:

- deck file dialog selection
- deck preview reload
- lightweight deck preview parsing
- commander / partner / companion preview state
- selected deck handoff into staged state
- backend/main.py handoff through existing guarded workflow

This keeps the Deck Selection extraction conservative. The page can render from the separate builder, but the source-of-truth workflow and backend handoff remain unchanged.

## Next extraction candidates

- Review Setup page extraction
- Philosophy Lens page extraction
- Collection Source page extraction
- Run Analysis page extraction later, because it is highest risk
- `main_window.py` split only after page extraction is stable

## v0.7.10 update

Review Setup page construction has been extracted from `ui/dragons_touch_pyside6_workstation.py` into:

`ui/pages/review_setup_page.py`

The extracted module owns page layout and local widget signal wiring only. MainWindow still owns the active Review Setup behavior and staged-state mutations:

- Review Setup summary text generation
- review focus and intensity meaning helpers
- staged output mode, review direction, review intensity, build-up mode, prompt mode, budget note, and intended bracket values
- context panel refreshes
- Run Analysis preview refreshes
- guarded CLI/main.py handoff

This keeps Review Setup extraction conservative. Conditional Review Direction behavior remains wired through the same MainWindow staging method and still updates immediately without an Apply button.

## Remaining extraction candidates after v0.7.10

- Philosophy Lens page extraction
- Collection Source page extraction
- Run Analysis page extraction later, because it is highest risk
- Future/placeholder page extraction
- `main_window.py` split only after page extraction is stable

## v0.7.11 update

Philosophy Lens page construction has been extracted from `ui/dragons_touch_pyside6_workstation.py` into:

`ui/pages/philosophy_lens_page.py`

The extracted module owns page layout and local widget signal wiring only. MainWindow still owns the active Philosophy Lens behavior and staged-state mutations:

- top-level philosophy profile selection
- optional philosophy subtype staging
- guide presentation staging
- context panel refreshes
- Run Analysis preview refreshes
- guarded CLI/main.py handoff through the existing CLI bridge

This keeps Philosophy Lens extraction conservative. The philosophy lens remains framing guidance only and does not override legality, budget, collection mode, color identity, pilot intent, or deck evidence.

## Remaining extraction candidates after v0.7.11

- Collection Source page extraction
- Run Analysis page extraction later, because it is highest risk
- Future/placeholder page extraction
- `main_window.py` split only after page extraction is stable

---

## v0.7.12 Update — Collection Source Page Extraction

`page_collection_tools()` now delegates to `ui/pages/collection_source_page.py` through `build_collection_source_page(self)`.

Extraction boundary:
- Moved page layout construction and local widget signal wiring.
- Preserved collection staging, chooser behavior, state refreshes, CLI bridge handoff, and backend execution ownership in `MainWindow`.

Risk status:
- Medium-high, because Collection Source affects collection-mode/source staging and collection-only boundary behavior.
- Mitigation: behavior methods remain on `MainWindow`; only page construction moved.

Next planned extraction:
- `v0.7.13 — Page Extraction: Run Analysis`


## v0.7.13 Update — Run Analysis Page Extraction

Status: Run Analysis page layout extracted to `ui/pages/run_analysis_page.py`.

Scope:
- Moved `page_run_review()` layout construction into `build_run_analysis_page(window)`.
- Kept guarded confirmation, QProcess ownership, CLI bridge wrappers, backend runner service helpers, report detection, and state updates on `MainWindow`.
- Preserved the locked UI -> guarded confirmation -> subprocess/main.py -> CLI input bridge -> backend output folder -> report detection -> Report Viewer plain-text workflow.

Risk notes:
- This is the highest-risk page extraction because the page exposes guarded execution controls and report-output detection controls.
- The extraction intentionally keeps only page construction in the page module. Runtime behavior remains owned by the active MainWindow.

Next safe target:
- v0.7.14 — Future / Placeholder Pages Extraction, then main-window cleanup after that passes.

---

## v0.7.14 Update — Future / Placeholder Pages Extraction

Completed extraction:

- `page_batch_reports()` now delegates to `ui.pages.future_workspace_page.build_batch_reports_page(self)`.
- `page_settings()` now delegates to `ui.pages.future_workspace_page.build_settings_page(self)`.

Behavior ownership remains unchanged:

- Batch / Aggregate remains placeholder/future workspace only.
- Settings remains an informational/checkpoint page.
- Theme switching still calls the existing `MainWindow.set_theme()` behavior.
- No backend, batch workflow, Commander Spellbook/API, markdown rendering, or replacement engine behavior was introduced.

Current active page modules:

- `ui/pages/deck_selection_page.py`
- `ui/pages/review_setup_page.py`
- `ui/pages/philosophy_lens_page.py`
- `ui/pages/collection_source_page.py`
- `ui/pages/run_analysis_page.py`
- `ui/pages/report_viewer_page.py`
- `ui/pages/future_workspace_page.py`

Main UI now primarily owns shell/navigation, shared behavior methods, wrappers, process execution, report interaction behavior, and app startup.

---

## v0.7.15 Update — Main Window Cleanup / Alpha Hardening Pass

Completed cleanup after all page-layout extractions passed:

- Consolidated `run_analysis_page` and `report_viewer_page` imports into the top-level page import block instead of importing inside wrapper methods.
- Simplified `page_run_review()` and `page_report_viewer()` so they now only delegate to their extracted page builders.
- Removed unused imports that belonged to previously extracted widget/theme/page code.
- Removed duplicate Report Viewer attribute initialization.
- Corrected the v0.7 workflow boundary comment near the top of the active UI file.

Current page extraction status:

- Deck Selection layout extracted.
- Review Setup layout extracted.
- Philosophy Lens layout extracted.
- Collection Source layout extracted.
- Run Analysis layout extracted.
- Report Viewer layout extracted.
- Future / Placeholder pages extracted.

MainWindow still intentionally owns behavior that should not move yet without a separate behavior-focused patch:

- shell/navigation
- global refresh helpers
- staged-state mutation behavior
- guarded confirmation
- QProcess ownership
- CLI bridge wrapper calls
- report detection wrapper calls
- Report Viewer behavior
- file/folder opening behavior
- app startup

Next recommended milestone:

- Treat v0.7.15 as the first Alpha Hardening cleanup checkpoint.
- After v0.7.15 passes, consider a full regression test and then decide whether to lock a v0.7 modularization checkpoint or continue with deeper behavior/service extraction.


---

# v0.7.16 — Alpha Modularization Regression Pass / Checkpoint Summary

## Checkpoint Result

v0.7.16 is intended as a checkpoint and regression-confirmation step after the successful v0.7 modularization run through v0.7.15.

This checkpoint does not introduce new runtime behavior. It records the current modular structure, confirms the preserved workflow boundary, and defines the regression test checklist for deciding whether the v0.7 modularization track is stable enough to snapshot.

## Current Modularization Status

Completed and passing:

- v0.7.0 — Alpha Baseline / Version Transition
- v0.7.1 — UI Structure Audit / Refactor Map
- v0.7.2 — Constants and Version Labels Extraction
- v0.7.3 — Theme / QSS Extraction
- v0.7.4 — Shared Widgets Extraction
- v0.7.5 — Staged State Object Extraction
- v0.7.6 — Report Detection Service Extraction
- v0.7.7L.1 — Python Launcher Fallback
- v0.7.7L.3 — Launcher Scope Correction
- v0.7.7 — Backend Runner / CLI Bridge Service Extraction, passed after v0.7.7.3 hotfix
- v0.7.8 — Report Viewer Page Extraction
- v0.7.9 — Deck Selection Page Extraction
- v0.7.10 — Review Setup Page Extraction
- v0.7.11 — Philosophy Lens Page Extraction
- v0.7.12 — Collection Source Page Extraction
- v0.7.13 — Run Analysis Page Extraction
- v0.7.14 — Future / Placeholder Pages Extraction
- v0.7.15 — Main Window Cleanup / Alpha Hardening Pass

## Active Supported Alpha Launch Path

Supported v0.7 alpha launch path:

```text
Launch_The_Dragons_Touch.pyw
```

Desktop shortcut support is deferred because Windows Smart App Control blocked the shortcut path during testing. Do not instruct testers to disable Smart App Control. The long-term distribution path remains packaged app, signed release, and eventually installer support.

## Preserved Workflow Boundary

The locked workflow remains:

```text
UI staged state
-> guarded confirmation
-> subprocess/main.py
-> CLI input bridge
-> backend output folder
-> report detection
-> Report Viewer plain-text load
```

Do not bypass main.py. Do not silently execute backend commands. Do not create a second backend workflow. Do not turn the UI into the deck-analysis backend.

## Current UI Folder Target

Expected current structure:

```text
ui/
  __init__.py
  constants.py
  dragons_touch_pyside6_workstation.py
  dragons_touch_pyside6_workstation_legacy_v0.6.8.5.py

  pages/
    __init__.py
    collection_source_page.py
    deck_selection_page.py
    future_workspace_page.py
    philosophy_lens_page.py
    report_viewer_page.py
    review_setup_page.py
    run_analysis_page.py

  services/
    __init__.py
    backend_runner.py
    cli_bridge.py
    report_detector.py

  state/
    __init__.py
    staged_run_config.py

  styles/
    __init__.py
    theme.py

  widgets/
    __init__.py
    core.py
```

## Checkpoint Decision

If v0.7.16 regression testing passes, the recommended next action is to create a clean ZIP snapshot before additional v0.7 work.

Recommended status after pass:

```text
v0.7.16 — Alpha Modularization Regression Pass / Checkpoint Summary
Status: Passed
Decision: Safe to create clean modularization checkpoint ZIP.
```

## Work Not Included in This Checkpoint

v0.7.16 does not add:

- Commander Spellbook/API calls
- Batch/Aggregate real workflow
- Replacement Candidate Engine
- Deep markdown rendering
- Installer packaging
- Desktop shortcut support as a required alpha path
- Silent backend execution
- Any replacement for main.py
