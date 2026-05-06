# Philosophy Layer Integration Notes

This file explains how to wire the philosophy/persona layer into the current **MTG Deck Helper v0.6.2 CLEANUP** layout.

The active cleanup layout uses top-level packages:

```txt
analysis/
app_io/
cuts/
data/
legality/
parsing/
replacements/
reports/
rules/
main.py
config.py
```

There is also a nested `deck_helper/` package in the zip, but the active `main.py` says the cleanup rebuild should use the **top-level packages only**. These notes target the top-level structure.

---

# Files Added

Add these files:

```txt
rules/deck_building_philosophy_rules.md
rules/philosophy_persona_rules.md
analysis/deck_building_philosophies.py
PHILOSOPHY_LAYER_INTEGRATION_NOTES.md
```

## Why `analysis/deck_building_philosophies.py`?

The current active code imports top-level packages like:

```python
from analysis.strategy_scoring import build_strategy_summary
from cuts.cut_pressure import build_cut_pressure_summary
from reports.report_builder import write_normal_report
```

So the philosophy helper should live in:

```txt
analysis/deck_building_philosophies.py
```

and be imported as:

```python
from analysis.deck_building_philosophies import ...
```

Do not place the active module in `src/` unless you later restructure the project around a `src` package.

---

# Design Rule

Strategy detection remains primary.

```txt
Strategy = what the deck is trying to do.
Philosophy = how the pilot wants that strategy judged and guided.
Persona = the user-facing mentor voice for that philosophy.
```

Philosophy/persona must not override:
- legality
- color identity
- deck size rules
- required cuts
- strategy detection
- user intent
- budget
- combo tolerance
- bracket/table goals
- declared constraints

---

# Minimal Integration: No Prompt Changes Yet

For the first test, do the smallest safe integration:

1. Add the four files.
2. Add philosophy context to `main.py`.
3. Render the Philosophy Guide section in `reports/report_builder.py`.
4. Optionally add the philosophy add-on to `reports/prompt_builder.py`.

This gets visible output without changing cut scores yet.

---

# Step 1 — Add Import To `main.py`

In top-level `main.py`, add:

```python
from analysis.deck_building_philosophies import build_philosophy_context
```

near the other `analysis.*` imports.

---

# Step 2 — Add Philosophy Context In `build_analysis_context`

In top-level `main.py`, inside `build_analysis_context`, after `collection_candidates = build_collection_candidate_summary()`, add:

```python
philosophy_context = build_philosophy_context(
    key=None,
    guide_preference="either",
)
```

Then add it to the returned context dictionary:

```python
"philosophy_context": philosophy_context,
```

This first pass defaults every run to:

```txt
Balanced / Unknown
Guide: Rowan
```

That is the safest MVP because it will not change cut behavior.

---

# Step 3 — Render Philosophy Guide In `reports/report_builder.py`

In top-level `reports/report_builder.py`, add this import:

```python
from analysis.deck_building_philosophies import render_philosophy_guide_section
```

Then in `build_normal_report`, after the `Run Settings` section is built and before `Deck / Command Zone`, add:

```python
philosophy_context = context.get("philosophy_context")
if philosophy_context:
    lines.append("")
    lines.append(render_philosophy_guide_section(philosophy_context).rstrip())
```

Suggested placement:

```python
    if runtime_config.review_direction == "build_up":
        lines.append(f"- Build-up mode: {runtime_config.build_up_config.get('label', 'Not applicable')}")
    else:
        lines.append(f"- Cut depth mode: {runtime_config.cut_depth_config.get('mode', 'normal')}")
        lines.append(f"- Optional cut target: {runtime_config.cut_depth_config.get('optional_cut_target', 5)}")

    philosophy_context = context.get("philosophy_context")
    if philosophy_context:
        lines.append("")
        lines.append(render_philosophy_guide_section(philosophy_context).rstrip())

    lines += _section("Deck / Command Zone")
```

Expected report output:

```md
## Philosophy Guide

**Selected Lens:** Balanced / Unknown
**Guide:** Rowan
**Guide Role:** The Trail Guide
**Primary Question:** What path does this deck naturally want to follow?

Use a balanced exploratory lens and avoid subtype-specific protection unless the user chooses a philosophy.
```

---

# Step 4 — Optional Prompt Builder Integration

In top-level `reports/prompt_builder.py`, add:

```python
from analysis.deck_building_philosophies import render_philosophy_prompt_questions
```

Then in `build_user_guided_prompt`, after the current `intro` rules and before the worksheet/interactive sections, add:

```python
philosophy_context = context.get("philosophy_context")
if philosophy_context:
    intro.extend(["", render_philosophy_prompt_questions(philosophy_context)])
```

This adds a philosophy add-on to the generated user-guided prompt without replacing the old seven-section workflow.

---

# Environment Variable Selection: Optional Next Step

After the MVP works, allow philosophy selection through environment variables.

In top-level `main.py`, import `os` if not already imported.

Then replace the MVP context call:

```python
philosophy_context = build_philosophy_context(
    key=None,
    guide_preference="either",
)
```

with:

```python
philosophy_context = build_philosophy_context(
    key=os.environ.get("MTG_PHILOSOPHY", "balanced_unknown"),
    guide_preference=os.environ.get("MTG_GUIDE_PREFERENCE", "either"),
)
```

Then you can test from terminal:

```bash
MTG_PHILOSOPHY=big_moment MTG_GUIDE_PREFERENCE=masculine python main.py
```

Windows PowerShell:

```powershell
$env:MTG_PHILOSOPHY="big_moment"
$env:MTG_GUIDE_PREFERENCE="masculine"
python main.py
```

Useful keys:

```txt
balanced_unknown
timmy_tammy
johnny_jenny
spike
big_moment
big_creature_stompy
theme_vibe
pet_card
let_me_do_my_thing
battlecruiser
engine_builder
commander_exploiter
weird_card_rescuer
theme_mechanic_inventor
constraint_builder
combo_builder
consistency_maximizer
efficiency_optimizer
curve_mana_discipline
competitive_closer
power_level_calibrator
interaction_controller
```

Number aliases also work for subtypes:

```txt
1 = big_moment
12 = combo_builder
18 = interaction_controller
```

Guide preference values:

```txt
masculine
feminine
either
random
none
```

---

# Cut Logic Integration: Later Phase

Do not change scoring first.

First use philosophy context as labels/report guidance only.

Later, in `cuts/cut_pressure.py`, `cuts/replaceability.py`, or `cuts/possible_cut_review.py`, use:

```python
from analysis.deck_building_philosophies import get_cut_modifier_hints
```

Then:

```python
cut_hints = get_cut_modifier_hints(philosophy_context["key"])
```

MVP behavior should add labels before numeric changes:

```python
card_eval["philosophy_protection_reasons"] = []
card_eval["philosophy_review_reasons"] = []
```

Only after the labels look correct should scoring change.

Suggested light scoring pattern later:

```python
if card_eval["philosophy_protection_reasons"]:
    cut_score -= 1

if card_eval["philosophy_review_reasons"]:
    cut_score += 1
```

Special cases later:

## Pet Card

```python
if philosophy_key == "pet_card" and card.name in declared_pet_cards:
    card_eval["protected_from_cut"] = True
    card_eval["protection_label"] = "Protected pet card"
```

## Combo Builder

```python
if philosophy_key == "combo_builder" and card.name in known_combo_pieces:
    cut_score -= 2
    card_eval["protection_label"] = "Protected combo role-player"
```

## Efficiency Optimizer

```python
if philosophy_key == "efficiency_optimizer" and card_eval["high_replaceability"]:
    cut_score += 2
```

## Power-Level Calibrator

```python
if philosophy_key == "power_level_calibrator" and card_eval["power_mismatch"]:
    cut_score += 2
```

---

# Replacement Logic Integration: Later Phase

In `cuts/replacement_categories.py`, use:

```python
from analysis.deck_building_philosophies import get_replacement_bias
```

Then pass the selected key later once `replacement_categories.py` accepts context:

```python
replacement_bias = get_replacement_bias(philosophy_context["key"])
```

Use it to append notes or reorder replacement categories.

Examples:

```txt
Big Moment:
- better ramp
- payoff support
- protection
- copy or doubling effects

Engine Builder:
- engine redundancy
- repeatable effects
- bridge cards
- protection/recursion

Interaction Controller:
- flexible removal
- efficient protection
- strategy-supporting interaction
```

Do not let replacement bias recommend cards that violate:
- color identity
- budget
- combo tolerance
- deck strategy
- table expectations

---

# Batch Mode Behavior

Batch auto should default to:

```txt
Balanced / Unknown
Guide: Rowan
```

unless a global philosophy is provided.

If using environment variables, batch mode can use:

```bash
MTG_PHILOSOPHY=power_level_calibrator MTG_GUIDE_PREFERENCE=either python main.py
```

Rules:
- no philosophy input = Balanced / Unknown
- do not apply subtype-specific protection
- may report possible philosophy lean
- apply global philosophy only if explicitly provided

---

# Suggested Testing Checklist

## Test 1 — Default

Run:

```bash
python main.py
```

Expected:
- Report includes Philosophy Guide
- Selected Lens: Balanced / Unknown
- Guide: Rowan

## Test 2 — Big Moment

Run:

```bash
MTG_PHILOSOPHY=big_moment MTG_GUIDE_PREFERENCE=masculine python main.py
```

Expected:
- Selected Lens: Big Moment
- Guide: Michael
- Parent Philosophy: Timmy / Tammy

## Test 3 — Combo Builder

Run:

```bash
MTG_PHILOSOPHY=combo_builder MTG_GUIDE_PREFERENCE=feminine python main.py
```

Expected:
- Selected Lens: Combo Builder
- Guide: Jennifer
- Parent Philosophy: Johnny / Jenny

## Test 4 — No Persona Name

Run:

```bash
MTG_PHILOSOPHY=interaction_controller MTG_GUIDE_PREFERENCE=none python main.py
```

Expected:
- Selected Lens: Interaction Controller
- Guide: No named guide selected
- Parent Philosophy: Spike

## Test 5 — Module Smoke Test

From project root:

```bash
python -m analysis.deck_building_philosophies
```

Expected:
- A rendered Philosophy Guide section for Big Moment / Michael

---

# Final File Structure

Recommended active structure after adding these files:

```txt
MTG Deck Helper v0.6.2 CLEANUP/
├─ main.py
├─ config.py
├─ analysis/
│  ├─ __init__.py
│  ├─ bracket_analysis.py
│  ├─ deck_building_philosophies.py
│  ├─ plan_fit.py
│  ├─ role_tag_cleanup.py
│  ├─ role_tags.py
│  ├─ strategy_gates.py
│  └─ strategy_scoring.py
├─ cuts/
│  ├─ cut_pressure.py
│  ├─ possible_cut_review.py
│  ├─ protected_cards.py
│  ├─ replaceability.py
│  └─ replacement_categories.py
├─ reports/
│  ├─ debug_sections.py
│  ├─ prompt_builder.py
│  └─ report_builder.py
├─ rules/
│  ├─ bracket_rules.md
│  ├─ card_attribute_rules.md
│  ├─ cut_replacement_rules.md
│  ├─ deck_building_philosophy_rules.md
│  ├─ philosophy_persona_rules.md
│  ├─ section_1_macro_archetypes_commander.md
│  ├─ section_2_mechanical_themes_micro_archetypes.md
│  ├─ section_3_strategic_board_politics.md
│  ├─ section_4_typal_tribal_themes_rules.md
│  ├─ section_5_1_niche_theme_rules.md
│  ├─ section_5_2_fringe_theme_rules.md
│  ├─ section_5_3_emergent_theme_rules.md
│  └─ strategy_archetype_rules.md
└─ PHILOSOPHY_LAYER_INTEGRATION_NOTES.md
```
