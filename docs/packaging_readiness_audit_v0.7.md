# The Dragon's Touch — v0.7.18 Alpha Tester Packaging Readiness Audit

## Purpose

This audit records what must be true before The Dragon's Touch moves from a Python-launched alpha build toward packaged executable and installer testing.

This is not a packaging patch.

v0.7.18 does not build an `.exe`, does not create an installer, does not change the UI runtime, and does not alter backend execution. It exists to protect the current stable modular alpha build by documenting the packaging risks, dependencies, path assumptions, and future test gates before any packaging work begins.

## Current Supported Alpha Launch Path

Supported v0.7 alpha launch path:

```text
Launch_The_Dragons_Touch.pyw
```

The `.pyw` launcher is the current user-facing alpha path because it successfully opens the desktop UI without Visual Studio Code.

The `.bat` launchers remain developer fallback only.

Desktop shortcut support is deferred because Smart App Control blocked the batch/shortcut path during testing.

## Packaging End Goal

Long-term user-facing goal:

```text
Installer
-> Start Menu shortcut
-> Desktop shortcut
-> The Dragon's Touch opens like a normal app
-> user selects deck/settings
-> guarded Run Analysis
-> main.py backend runs
-> Report Viewer loads generated report
```

The installer/signing path belongs to a later packaging/release track, not the current v0.7 modularization checkpoint.

## Preserved Workflow Boundary

Packaging must preserve the locked workflow:

```text
UI staged state
-> guarded confirmation
-> subprocess/main.py
-> CLI input bridge
-> backend output folder
-> report detection
-> Report Viewer plain-text load
```

Packaging must not create a second backend workflow.

Packaging must not bypass `main.py`.

Packaging must not silently execute backend commands.

Packaging must not remove guarded run confirmation.

## Current Project Shape Relevant to Packaging

Expected important root-level files:

```text
main.py
config.py
Launch_The_Dragons_Touch.pyw
Launch_The_Dragons_Touch.py
README_START_HERE.txt
README.md
download_scryfall_data.py
```

Expected important folders:

```text
ui/
docs/
rules/
analysis/
app_io/
cuts/
data/
deck_helper/
io/
legality/
parsing/
replacements/
reports/
tools/
```

Expected modular UI structure:

```text
ui/
  constants.py
  dragons_touch_pyside6_workstation.py
  dragons_touch_pyside6_workstation_legacy_v0.6.8.5.py

  pages/
    collection_source_page.py
    deck_selection_page.py
    future_workspace_page.py
    philosophy_lens_page.py
    report_viewer_page.py
    review_setup_page.py
    run_analysis_page.py

  services/
    backend_runner.py
    cli_bridge.py
    report_detector.py

  state/
    staged_run_config.py

  styles/
    theme.py

  widgets/
    core.py
```

## Scryfall Data Packaging Decision

The clean alpha ZIP may omit:

```text
data/scryfall_cards.json
```

because it is very large.

The clean build should keep:

```text
download_scryfall_data.py
```

in the project root so the local card database can be regenerated with:

```bash
python download_scryfall_data.py
```

Packaging readiness requirement:

- The app must handle a missing `data/scryfall_cards.json` gracefully, or the README must clearly instruct the user to regenerate it before running analysis.
- A future packaged build should decide whether to ship with no card JSON, a compressed card database, or a first-run downloader.

## Known Packaging Risks

### 1. Path handling

The current app relies on local project folders and relative paths. Packaging may change where files appear at runtime.

Packaging tests must verify:

- `main.py` can still be found.
- `ui/` modules can still be imported.
- `rules/` files can still be found.
- `data/` files can still be found or regenerated.
- `Outputs/` can still be created.
- Report detection can still find generated folders.

### 2. Subprocess execution

The UI currently launches `main.py` through guarded execution. Packaging must preserve this behavior.

Packaging tests must verify:

- The packaged UI can still run the backend through the intended path.
- The app does not accidentally run backend analysis at startup.
- The guarded confirmation still appears.
- stdout/stderr capture still works.
- report detection after backend completion still works.

### 3. PySide6 packaging

PySide6 apps often require hidden imports, Qt plugins, or careful asset inclusion.

Packaging tests must verify:

- The window opens.
- Themes/QSS load.
- Dropdowns render correctly.
- File/folder dialogs work.
- Text areas and buttons behave normally.
- No missing Qt platform plugin errors appear.

### 4. Local file access

The app is built around local deck files, local collection files, and local output folders.

Packaging tests must verify:

- Deck file picker works.
- Collection folder/file picker works.
- Outputs folder can be created beside the app or in an intentional user-writable location.
- Report Viewer can open generated reports.
- Folder-opening buttons work.

### 5. Security/reputation warnings

Unsigned scripts, shortcuts, and executables may trigger Windows Smart App Control or SmartScreen warnings.

Current decision:

- Do not tell users to disable Smart App Control.
- Do not rely on `.bat` launchers as the user-facing path.
- Do not rely on desktop shortcut support until a proper packaged/signed installer path is pursued.

Future release direction:

- Packaged executable test first.
- Installer candidate later.
- Signed release path when public distribution is realistic.

## Packaging Readiness Checklist

### Pre-Packaging Source Check

- Pass/Fail: Clean project launches with `Launch_The_Dragons_Touch.pyw`.
- Pass/Fail: Clean project does not require Visual Studio Code.
- Pass/Fail: `main.py` remains backend source of truth.
- Pass/Fail: `download_scryfall_data.py` exists in the project root.
- Pass/Fail: The app can run after `data/scryfall_cards.json` is regenerated.
- Pass/Fail: No `__pycache__/` folders are required.
- Pass/Fail: No `.pyc` files are required.
- Pass/Fail: No `.git/` folder is required for runtime.

### Packaging Spike Candidate Checklist

- Pass/Fail: Packaged app opens without Python command line.
- Pass/Fail: Packaged app opens without Visual Studio Code.
- Pass/Fail: Deck Selection page works.
- Pass/Fail: Review Setup page works.
- Pass/Fail: Philosophy Lens page works.
- Pass/Fail: Collection Source page works.
- Pass/Fail: Run Analysis page works.
- Pass/Fail: Report Viewer page works.
- Pass/Fail: Batch / Aggregate remains placeholder/future.
- Pass/Fail: Settings page works.

### Packaged Backend Workflow Checklist

- Pass/Fail: Run Analysis still shows guarded confirmation.
- Pass/Fail: Cancel prevents backend execution.
- Pass/Fail: Confirmed run still goes through `main.py` or the intentionally packaged equivalent of `main.py`.
- Pass/Fail: Backend stdout is captured.
- Pass/Fail: Backend stderr is captured if present.
- Pass/Fail: Output folder is created.
- Pass/Fail: Output folder includes commander name.
- Pass/Fail: Output folder includes source deck filename distinction.
- Pass/Fail: Output folder includes timestamp.
- Pass/Fail: Repeated runs create separate folders.
- Pass/Fail: Report detection works.
- Pass/Fail: Report Viewer loads generated report as plain text.

### Installer Candidate Checklist

- Pass/Fail: Installer creates an application folder.
- Pass/Fail: Installer creates Start Menu shortcut.
- Pass/Fail: Installer creates Desktop shortcut only if Smart App Control/SmartScreen behavior is acceptable.
- Pass/Fail: Installed app opens normally.
- Pass/Fail: Installed app can create outputs in a user-writable location.
- Pass/Fail: Installed app can access selected deck and collection files.
- Pass/Fail: Installed app can regenerate or locate Scryfall card data.
- Pass/Fail: Installed app can be uninstalled cleanly if uninstall support is included.

## Deferred Packaging Decisions

The following decisions are intentionally deferred:

- PyInstaller vs another packaging tool.
- One-file executable vs one-folder executable.
- Whether to bundle `data/scryfall_cards.json`.
- Whether to store outputs beside the app or in a user data folder.
- Whether to publish through GitHub Releases, Microsoft Store/MSIX, MSI, or another installer route.
- Whether/when to code-sign release artifacts.
- Whether/when to restore desktop shortcut support.

## Recommended Future Packaging Order

```text
v0.7 — Alpha Access
Supported path: Launch_The_Dragons_Touch.pyw
Goal: trusted testers can open the app without VS Code.

v0.8/v0.9 — Packaging Spike
Goal: prove a packaged executable can preserve the current guarded workflow.

v0.9/v1.0 — Installer Candidate
Goal: installer creates normal app access and stable paths.

v1.0+ — Signed Public Release Path
Goal: improve user trust and reduce platform warnings for public distribution.
```

## v0.7.18 Decision

v0.7.18 does not package the app.

v0.7.18 records that packaging should wait until the modular alpha workflow remains stable and the project is ready for a dedicated packaging spike.

Current safe launch path remains:

```text
Launch_The_Dragons_Touch.pyw
```
