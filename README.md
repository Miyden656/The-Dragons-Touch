# The Dragon's Touch — v1.5 Source-Run Beta

**The Dragon's Touch** is a free community Commander deck-building support tool for *Magic: The Gathering*.

The current beta path is a **source-run ZIP**. It is not an installed app, and it is not an EXE handoff.

The goal of the beta is to help Commander players review decks, identify cuts, see replacement needs, lean on local Combo Awareness, and produce AI handoff reports — while keeping final deck-building choices in the player's hands.

---

## Current beta status

```text
Current polish version: v1.5.0
Stable base:            v0.11 Stable — Source-Run Beta Handoff Lock
Package type:           Source-run ZIP
Primary launch:         py desktop_ui_launcher.py
Fallback launch:        py ui\dragons_touch_pyside6_workstation.py
```

The EXE/installer path remains paused. The protected beta handoff path is source-run.

---

## What's new in v1.5

v1.5 ships the **Commander's Call** deck-building suite (Bin B) and a fully wired six-signal scoring chain.

The Full 100-Card Draft Builder now respects six independent signals when picking cards for your deck:

```text
base score
  ↓ bracket filter           (hard exclude + soft modifier)
  ↓ commander-text amplifier (cap +6.0)
  ↓ philosophy / persona bias (cap ±8.0)
  ↓ combo-aware modifier      (cap ±6.0)
  ↓ role-tag classification   (51 EDH-staple overrides)
  ↓ strategy-profile match    (46 curated strategy tag sets)
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the deep walkthrough, [CHANGELOG.md](CHANGELOG.md) for version history.

Top-level v1.5 features:

- **Build Setup Panel** captures bracket, primary/secondary strategy, sub-philosophy persona, collection sources
- **Owned Cards by Role** loads your full collection, role-tags every card, groups into 11 buckets with source-file tracking
- **Rough Shell guidance** with 40+ role-tag entries
- **Full 100-Card Draft** generator with copy-paste decklist + role breakdown
- **Bracket-aware filtering** at build time (Bracket 1–5)
- **18 sub-philosophy personas** that drive meaningfully different decks from the same commander+collection
- **Combo Awareness** plugged into the picker — combo-leaning personas float combo pieces in, combo-averse personas push them out
- **249 strategy profile catalog** with 46 hand-curated strategy-defining tag sets so the Strategy bucket actually reflects the chosen strategy

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

No data downloads or index builds should happen automatically during normal deck analysis.

---

## Folder overview

```text
analysis\            Card-level analysis (role tagging, philosophy profiles, strategy scoring)
analysis_pipeline\   Deck-run orchestration (context, deck runner, batch runner, resources)
app_io\              Application IO helpers (paths, file handling)
build_from_collection\  Commander's Call deck-building (Bin B) — strategy filters, scorers, draft builder
collection\          User collection files (your owned-cards text files)
collection_services\ Collection loading + matching services
combo_awareness\     Combo Awareness — Spellbook index loader, matcher, reporting
commander_discovery\ Commander candidate discovery
cuts\                Cut-pressure analysis and replaceability scoring
data\                Runtime data (Scryfall cards, combo index, etc.)
Decklists\           Sample or user decklists
docs\                Developer + tester documentation, architecture notes, smoke checklists
examples\            Sample input files
legality\            Format legality + commander-detection helpers
Outputs\             Generated reports (timestamped per run)
parsing\             Decklist parser
philosophy\          Philosophy lens registry (Big Three personas + extensions)
replacements\        Replacement-candidate engine (collection-aware suggestions)
reports\             Report builders, sections, strategy-bridge modules
rules\               MTG rules text data
settings\            Runtime config + UI defaults
strategy_knowledge\  Strategy profile catalog + curated tag sets + 249-profile index
tools\               Setup, verifier, and helper tools
ui\                  PySide6 desktop UI (pages, services, theme)
```

---

## Required source-run tools

For this beta, the tools folder should include:

```text
tools\data_setup.py
tools\build_combo_index.py
tools\download_commander_spellbook_bulk_json.py
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
- imperfect strategy detection on niche/fringe layers (the 46 curated strategy profiles cover the common cases; ~200 niche/fringe/emergent strategies still fall back to a generic tag set)
- imperfect cut recommendations
- rough report wording
- limited error recovery
- manual tester feedback collection

---

## Distribution note

This beta is intentionally distributed as a source-run ZIP. Unsigned EXE builds can be blocked by Windows security features, so source-run avoids that for early beta testing.

---

## Unofficial notice

The Dragon's Touch is an unofficial community tool. It is not affiliated with Wizards of the Coast, Scryfall, Commander Spellbook, or any deck-hosting platform.
