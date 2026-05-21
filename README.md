# The Dragon's Touch — v0.12.1 Source-Run Beta

**The Dragon's Touch** is a free community Commander deck-building support tool for Magic: The Gathering.

The current protected beta path is a **source-run ZIP**. It is not an installed app, and it is not an EXE handoff.

The goal of this beta is to help Commander players review decks, understand strategy, identify possible cuts, see replacement needs, use local Combo Awareness, and prepare useful AI handoff reports while keeping final deck-building choices in the player's hands.

---

## Current beta status

```text
Current polish version: v0.12.1
Stable base: v0.11 Stable — Source-Run Beta Handoff Lock
Package type: Source-run ZIP
Primary launch command: py desktop_ui_launcher.py
Fallback launch command: py ui\dragons_touch_pyside6_workstation.py
```

The EXE/installer path is paused. The protected beta handoff path is source-run.

---

## Core features currently being tested

The Dragon's Touch currently supports:

- Commander decklist loading
- strategy and synergy review
- cut pressure and possible cut guidance
- replacement category guidance
- collection-aware review support
- local data setup through Settings
- Scryfall card data setup
- Commander Spellbook combo data setup
- normal combo index building
- Run Analysis readiness guidance
- report generation
- AI handoff prompt generation
- Report Viewer output review

---

## Quick start

For the shortest tester instructions, open:

```text
README_START_HERE.txt
```

Basic commands:

```powershell
py -m pip install -r requirements.txt
py desktop_ui_launcher.py
```

Fallback launch:

```powershell
py ui\dragons_touch_pyside6_workstation.py
```

---

## First-time data setup

Inside the app:

```text
Settings → Data Setup
```

Run these in order:

```text
1. Download / Update Scryfall
2. Download / Update Combo Data
3. Build Combo Index
```

These actions prepare local runtime data for deck analysis and Combo Awareness.

No data downloads or index builds should happen automatically during normal deck analysis.

---

## Source-run smoke testing

Use this checklist when testing a clean extracted beta folder:

```text
docs\source_run_beta_smoke_test_checklist_v0.12.0.md
```

The checklist verifies:

- clean folder extraction
- dependency install
- app launch
- fallback launch
- Settings → Data Setup
- Scryfall setup
- Combo data setup
- Combo Index build
- Deck Selection
- Review Setup
- Run Analysis
- Outputs folder creation
- report detection
- Report Viewer
- Combo Awareness result check
- useful failure capture notes

---

## Folder overview

```text
ui\                  Desktop UI
combo_awareness\     Combo Awareness support
analysis\            deck analysis support
app_io\              app IO support
cuts\                cut review support
data\                runtime data folder
Decklists\           sample or user decklists
collection\          collection files
Outputs\             generated reports
tools\               setup, verifier, and helper tools
docs\                tester docs and smoke-test checklists
```

---

## Required source-run tools

For this beta, the tools folder should include:

```text
tools\data_setup.py
tools\build_combo_index.py
tools\download_commander_spellbook_bulk_json.py
```

v0.12 polish patches may also add tester/support tools such as:

```text
tools\verify_v0.12.0_source_run_smoke_test_checklist.py
tools\verify_v0.12.1_readme_quickstart_polish.py
```

---

## Beta tester feedback

Useful feedback includes:

- Did the app launch?
- Could you reach Settings → Data Setup?
- Did data setup work?
- Could you load a decklist?
- Did Run Analysis complete?
- Did Report Viewer open the report?
- Was the report understandable?
- Were cut suggestions useful?
- Were any cards clearly misunderstood?
- Did any error appear?
- What deck did you test?
- Did Combo Awareness appear to work as expected?

Screenshots and copied error text are very helpful.

---

## Known limitations

This beta may still have:

- rough UI layout issues
- long waits during large data downloads/builds
- imperfect strategy detection
- imperfect cut recommendations
- rough report wording
- limited error recovery
- manual tester feedback collection

---

## Distribution note

This beta is intentionally distributed as a source-run ZIP.

Unsigned EXE builds can be blocked by Windows security features. To avoid that issue for early beta testing, use the source-run commands above.

---

## Unofficial notice

The Dragon's Touch is an unofficial community tool. It is not affiliated with Wizards of the Coast, Scryfall, Commander Spellbook, or any deck-hosting platform.
