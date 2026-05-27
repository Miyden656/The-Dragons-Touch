# Architecture — The Dragon's Touch v1.5

This document is the developer-facing walkthrough of how The Dragon's Touch is wired. For the end-user-facing overview, see [`README.md`](../README.md).

---

## Top-level layout

```text
main.py                       Thin CLI/orchestration entrypoint
desktop_ui_launcher.py        Desktop UI launcher (recommended path)
config.py                     Runtime configuration

analysis/                     Card-level analysis primitives
  role_tags.py                  Pattern-based role tag inference
  role_tag_overrides.py         Curated EDH-staple overrides (~51 cards)
  deck_building_philosophies.py Philosophy persona definitions
  strategy_scoring.py           Legacy archetype definitions (22 macros)

analysis_pipeline/            Deck-run orchestration
build_from_collection/        Commander's Call deck builder (Bin B)
combo_awareness/              Spellbook combo index loader + matcher
commander_discovery/          Commander candidate discovery
cuts/                         Cut-pressure + replaceability scoring
philosophy/                   Philosophy lens registry
replacements/                 Replacement-candidate engine
reports/                      Report writers + sections + strategy_bridge

strategy_knowledge/           Strategy profile catalog
  strategy_selector_catalog.py    Lookup chain: curated → index → legacy
  strategy_role_tag_profiles.py   46 curated strategy-defining tag sets
  adapter_boundary.py             Package boundary contract
  index/                          249-profile index (built from layers/)
  layers/                         Source markdown for each strategy
  (other subdirs)                 v1.4.x phase artifacts (slated for archive/)

ui/                           PySide6 desktop UI
  dragons_touch_pyside6_workstation.py  Main window
  pages/                       Page widgets (commander discovery, report viewer, settings, etc.)
  services/                    UI services (backend boundary, CLI bridge)
```

---

## The six-signal scoring chain

The Full 100-Card Draft Builder (in `build_from_collection/full_100_card_draft_builder.py`) scores each candidate card with six independent signals applied in order. Each one has a defined cap so no single signal can overwhelm the others.

```text
1. Base score (strategy overlap + tag count + curve bias)
2. Bracket filter
     - Hard exclude (bracket-disallowed cards never enter the pool)
     - Soft modifier (preference shift within allowed cards)
3. Commander-text amplifier
     - Cards whose role tags match the commander's "amplifier set"
       (derived from oracle text) get +1.5 per matching tag, capped at +6.0
4. Philosophy / persona bias
     - 18 personas (Engine Builder, Battlecruiser, Combo Builder, etc.)
     - Each maps to a {tag: modifier} profile, capped at ±8.0
5. Combo-aware modifier
     - "Leaning" personas (Combo Builder, Competitive Closer, etc.):
         +1.5 per combo this card appears in
         +2.0 extra per one-card-away combo
         +3.0 extra per already-complete combo
         capped at +6.0
     - "Averse" personas (Let Me Do My Thing, Big Moment, etc.):
         -1.5 per combo this card appears in
         -1.0 extra per one-card-away combo
         capped at -6.0
     - Neutral personas: no modifier
6. Strategy-profile tag overlap
     - +3.0 per overlap with the chosen Primary+Secondary strategy tags
     - The strategy_role_tag_profiles module ships 46 curated sets
     - Non-curated strategies have utility-bucket tags
       (ramp/protection/card_draw/removal/recursion/board_wipe)
       stripped from the placeholder so they don't starve utility buckets
```

After scoring, cards are routed into role buckets:

```text
_classify_role_bucket(card_tags, strategy_tags):
    if strategy_tags overlap with card_tags  → Strategy bucket
    elif any utility tag (ramp/draw/removal/protection) → that utility bucket
    else                                                 → Flex bucket
```

This routing means strategies that legitimately ARE their utility (Ramp/Big Mana, Control, Pillowfort) keep utility tags in their strategy_tags — for everything else those tags are explicitly trimmed so utility buckets fill correctly.

---

## Key data files

```text
data/scryfall_cards.json              ~37k Magic cards (Scryfall bulk)
data/commander_spellbook/
  combo_index.json                    ~88k combos (Commander Spellbook)
strategy_knowledge/index/
  strategy_profile_index.latest.json  249 strategy profiles
strategy_knowledge/layers/            249 source .md files for each profile
```

The combo index is large (~148 MB) and lazy-loaded with module-level caching in `build_from_collection/combo_scorer.py`. First build call after process launch pays ~0.9s; subsequent calls are ~60ms.

---

## How to extend

### Add a new sub-philosophy persona

1. Edit `build_from_collection/philosophy_bias.py`
2. Add an entry to `PERSONA_BIAS` mapping tag → modifier
3. Add the persona's display name to `build_from_collection/philosophy_bracket_preferences.py:SUB_PHILOSOPHY_OPTIONS`
4. Optionally add the bare persona name to `build_from_collection/combo_scorer.py:PERSONA_ORIENTATION` if it should be combo-leaning or combo-averse

### Add a new curated strategy profile

1. Edit `strategy_knowledge/strategy_role_tag_profiles.py`
2. Add an entry to `_MACRO`, `_MECHANICAL`, `_TYPAL`, or `_STRATEGIC` (or create a new category dict and include in `STRATEGY_ROLE_TAG_PROFILES`)
3. Pick 5–15 strategy-DEFINING tags from `analysis/role_tags.py`'s `ROLE_TAG_DISPLAY_ORDER` vocabulary
4. Avoid utility-bucket tags (ramp/card_draw/protection/removal/recursion/board_wipe) UNLESS the strategy IS that utility

### Add a card-name role-tag override

1. Edit `analysis/role_tag_overrides.py`
2. Add an entry to `ROLE_TAG_OVERRIDES` keyed by the lowercased card name
3. Use `add` to add tags, `remove` to strip incorrectly-pattern-matched tags
4. The override applies AFTER `infer_card_role_tags`, so it can correct false positives

### Add a new scoring signal

1. Create a new module under `build_from_collection/` following the pattern of `bracket_filter.py`, `commander_text_scorer.py`, `philosophy_bias.py`, or `combo_scorer.py`
2. Export a `score_modifier(...)` function and (optionally) a `summary(...)` for the report notes
3. Add a defensive try-import block to `build_from_collection/full_100_card_draft_builder.py` near the other scorer imports
4. Insert the per-card modifier call inside the pool-building loop, after the existing modifiers
5. Choose a cap that doesn't dominate the existing chain (current caps: bracket modifier ~±2, commander-text +6, philosophy ±8, combo ±6)

---

## Strategy selector lookup chain

When the user picks a strategy in the Build Setup Panel, the deck builder calls `strategy_knowledge.strategy_selector_catalog.role_tags_for_display_name(name)`. The lookup order is:

```text
1. strategy_role_tag_profiles.role_tags_for_strategy(bare_name)
     ~46 curated strategies → sharp 5-15 tag set
     This is the recommended path; covers all 9 Macro + top 20 Mechanical
     + 9 Typal + 8 Strategic strategies

2. The 249-profile index (strategy_profile_index.latest.json)
     If the placeholder fingerprint is detected (the same generic 17-tag list
     for every profile), utility-conflicting tags are stripped before return
     so non-curated strategies don't starve utility buckets

3. Legacy ARCHETYPE_DEFINITIONS (analysis/strategy_scoring.py)
     22 macro archetypes via anchors/payoffs/enablers
```

Strategies outside the curated 46 still work — they just contribute the placeholder's thematic tags (combo, combat, sacrifice, tokens, tribal, etc.) without the utility tags that would conflict with the utility buckets.

---

## What happens during a Full 100-Card Draft

1. **Pool construction** (`full_100_card_draft_builder.py:build_full_100_card_draft`)
   - Filter owned cards by commander color identity
   - Apply bracket hard-exclude
   - Tag each card via `analysis.role_tags.infer_card_role_tags` + `analysis.role_tag_overrides`
   - Score each card through the six-signal chain
   - Pre-compute reachable combos (if persona is non-neutral) for the combo scorer
2. **Bucket classification** — each card gets routed via `_classify_role_bucket`
3. **Pass 1: target fills** — for each bucket (Commander, Lands, Ramp, Card Draw, Removal, Protection, Strategy), greedily take the top-scored cards up to that bucket's target
4. **Pass 2: Flex** — pour remaining cards into Flex up to its target
5. **Pass 3: 100-card guarantee** — if total < 100, expand Flex with leftover pool
6. **Land base** — take owned nonbasic lands up to 17, fill remainder with basics distributed across identity colors
7. **Padding safety net** — if collection is genuinely too thin, pad with extra basics so output always hits 100 cards
8. **Report** — render markdown with copy-paste decklist, role breakdown, summary, and notes (one note per active signal explaining what it did)

---

## Refactor and cleanup guardrails

- **No facade files / no `_impl.py` wrappers.** If a file needs splitting, split by real responsibility and update all call sites — do not leave a backwards-compat facade.
- **Strategy Knowledge baseline is load-bearing.** `strategy_knowledge/index/strategy_profile_index.latest.json` and the `layers/` source files are the foundation. Don't delete without confirmed runtime tracing.
- **The 18 strategy_bridge scripts still referenced by `reports/strategy_knowledge_sections.py` and `ui/pages/report_viewer_page.py`** are alive in the import graph but may only execute behind dev-mode-only feature flags. Confirm runtime behavior before pruning.
- **UI changes need visual smoke.** The PySide6 UI can't be driven from agent sessions — always hand off to the user with explicit "what to click through" steps.
