# The Dragon's Touch — v1.6.0 Community Release

**The Dragon's Touch** is a free community Commander deck-building support tool for *Magic: The Gathering*.

It helps you turn a commander, a decklist, or a card collection into a smarter, more focused, more playable Commander deck — while keeping every final decision in your hands.

## Two ways to use it

**Deck review (paste/select a decklist):**
Point the app at an existing decklist. It generates a context-aware report explaining which cards are doing real work for your deck's plan, which are replaceable, which deserve protection from cuts, and what kinds of replacements would actually improve the deck. The report has rich per-card narrative — not just "this card is good / bad," but *"this card is useful interaction but doesn't advance your sacrifice or recursion engine — keep it if you need more answers, but it's not part of the deck's core plan."*

**Commander's Call (build from your collection):**
Point the app at your collection (plain-text card lists). It scans for legendary creatures you already own, lets you pick a commander, then generates a copy-paste 100-card decklist using your owned cards — biased by the strategy, persona, and bracket you choose. Each card in the output is annotated with the *why* (strategy fit, commander amplifier, combo piece, persona pick) so you can see at a glance what role it's playing.

The current beta is distributed as a **source-run ZIP**. It is not an installed app and not an EXE handoff.

---

## Current release

```text
Current version:    v1.6.0 (community release)
Stable base:        v1.5.0 (six-signal scoring chain locked)
Distribution:       Standalone EXE bundle + source-run ZIP
EXE launch:         Double-click TheDragonsTouch.exe
Source-run launch:  py desktop_ui_launcher.py
                    py ui\dragons_touch_pyside6_workstation.py (fallback)
```

The v1.6.0 community release is the first version distributed as a standalone EXE bundle for users who don't want to install Python. See [Distribution](#distribution--two-paths) below for both paths.

---

## What's new in v1.6

v1.6 is a stability + UX overhaul on top of the v1.5 scoring engine.

- **Closed the long-standing navigate-away-and-back bug.** Post-scan button clicks now fire on first try without requiring the workaround. Root cause was a stale shiboken widget reference in a refresh function silently aborting the scan handler — diagnosed via four rounds of targeted logging, fixed by the new `_safe_widget_call` helper applied codebase-wide.
- **70 → 1 popup removal.** Confirmation dialogs, success notifications, "no commander selected" nudges, and "X failed" error popups have all been replaced with inline status updates, disabled buttons + tooltips, or silent no-ops. The only remaining popup is the destructive "Reset Settings to Defaults" confirmation.
- **Per-card "why" annotations on the Full 100-Card Draft.** Each card in the generated decklist surfaces the scoring signals that earned it a slot — *Strategy fit*, *Commander amplifier*, *Combo piece*, *Persona pick* — so you can scan the deck and see at a glance what role each card is playing.
- **First-run polish.** A "Where to Next?" guidance card on Deck Selection explains the two main flows. The Archidekt export tip is now inline at the top of the Select File tab. When the scan fails because Scryfall data is missing or no collection is staged, the app auto-navigates to Settings with an explanatory status banner instead of a dead-end warning.
- **State preservation across page rebuilds.** Build Setup Panel selections (Primary/Secondary strategy, Philosophy/Sub-philosophy, Bracket, Collection toggle) now persist when you navigate away and back.
- **Standalone EXE build pipeline.** New `TheDragonsTouch.spec` + `build_exe.bat` produces a one-folder distributable. See [Distribution](#distribution--two-paths).
- **New stability test.** `tests/test_safe_widget_call.py` reproduces the navigate-away-and-back bug pattern against mocked stale widget stubs to prevent regression.

---

## What v1.5 shipped (still active in v1.6)

v1.5 added the **Commander's Call** deck-building suite (Bin B) and the fully wired six-signal scoring chain.

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
- **Full 100-Card Draft** generator with copy-paste decklist + role breakdown + per-card "why" annotations (strategy fit, commander amplifier, combo piece, persona pick)
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

## Collection files (for Commander's Call)

The Commander's Call flow reads your owned cards from plain-text files in `collection/`.

The expected format is **one card per line**, with optional quantity prefix. Anything Archidekt, Moxfield, Manabox, or your own spreadsheet exports as plain text usually works:

```text
1 Sol Ring
4 Llanowar Elves
Lightning Bolt
2x Counterspell
```

Multiple `.txt` files are supported — name them by storage location (e.g. `Cards in Avatar the last Airbender Box at desk.txt`). The report shows you which file each card came from, so you can find a physical card when building.

To point the app at your collection: **Settings → Collection Source → Choose Collection Folder**.

If you don't have your collection digitized yet, you can still use the deck-review flow (paste/select a decklist) without it.

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

## Feedback & bug reports

The best place to report a bug, request a feature, or share feedback is the project's [GitHub Issues](https://github.com/Miyden656/The-Dragons-Touch/issues) page.

When reporting a bug, what helps most:

- What you were trying to do (the goal, not just the click sequence)
- What you expected vs. what actually happened
- A screenshot if it's a UI issue
- The contents of any error message or traceback
- Which commander / decklist / collection you were working with (no need to share the full file — just the broad strokes)

For feature requests, framing it as *"I want to do X but the tool makes me do Y"* is more useful than a specific implementation request — it lets the design respond to the underlying need.

---

## Known limitations

This beta may still have:

- **Long waits during large data downloads/builds** — initial Scryfall + Combo data setup can take a few minutes
- **Long waits during 100-card draft generation** — 30–90 seconds depending on collection size; the button stays disabled until the draft is ready
- **Imperfect strategy detection on niche layers** — the 46 hand-curated strategy profiles cover the common cases; ~200 niche / fringe / emergent strategies still fall back to a generic tag set and may not get sharp Strategy-bucket selection
- **Imperfect cut recommendations** — the deck-review report's cut/protect/replace suggestions are a starting point, not a final authority. Pilot judgement remains the final word.
- **Rough wording in some report sections** — first-time deck-review reports may have phrasing leftovers worth polishing per release
- **Manual tester feedback collection** — no in-app feedback button yet; share bugs and suggestions however is easiest for you

---

## Distribution — two paths

### Path A: Source-run ZIP (current beta)
The beta has been distributed as a source-run ZIP: end users install Python + PySide6 themselves and double-click `Launch_The_Dragons_Touch.pyw`. This sidesteps Windows SmartScreen warnings entirely because there's no EXE to flag.

### Path B: Standalone EXE bundle (community release)
For a wider community release, a one-folder EXE bundle is the friendlier experience — users download a zip, extract it, and double-click `TheDragonsTouch.exe`. No Python install needed.

To build the EXE from source:
```powershell
py -3 -m pip install -r build-requirements.txt
build_exe.bat
```

The build script runs PyInstaller against `TheDragonsTouch.spec` and produces `dist\TheDragonsTouch\` — the distributable folder. Zip that folder to share.

### First-run note for end users of the EXE

Windows SmartScreen will display an "unknown publisher" warning the first time the EXE is launched. This is because the EXE is not yet code-signed — it's a normal warning for any unsigned community-distributed app.

To run the app:
1. Double-click `TheDragonsTouch.exe`
2. When Windows shows the blue SmartScreen warning, click **"More info"**
3. Then click **"Run anyway"**

This only happens on the very first launch.

The code-signing roadmap (SignPath Foundation for open-source projects is the planned free path) is documented in [LEGAL.md](LEGAL.md).

---

## Unofficial notice & attributions

The Dragon's Touch is a free, unofficial community tool. It is not affiliated with, endorsed, sponsored, or specifically approved by Wizards of the Coast LLC. The project uses Wizards' trademarks and intellectual property under the [Wizards Fan Content Policy](https://company.wizards.com/en/legal/fancontentpolicy).

**MAGIC: THE GATHERING**® is a trademark of Wizards of the Coast LLC. Card data is provided by [Scryfall](https://scryfall.com/). Combo data is based on the [Commander Spellbook](https://commanderspellbook.com/) community combo catalog. The desktop UI is built on PySide6 (Qt for Python, LGPL-3.0).

For the full trademark notices, third-party software credits, and project copyright details, see [LEGAL.md](LEGAL.md).
