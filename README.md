# The Dragon’s Touch

**The Dragon’s Touch** is a local Python-based Magic: The Gathering Commander deck helper.

It analyzes Commander decklists, generates deck reports, and creates guided review prompts that help a player refine, cut down, build up, or complete a Commander deck while keeping the pilot’s intent at the center of the process.

The tool is designed to support deck building, not replace player judgment. It aims to get a deck to a strong playable “70% solution,” while final tuning, pet-card decisions, local-meta calls, and playstyle choices remain with the player.

---

## Current Development Status

Current working version:

```text
v0.6.2.6 — Worksheet Guardrail Hotfix
```

Current major focus:

```text
v0.6 — User-Guided Review Prompt
```

The v0.6 goal is:

```text
Ask → collect user answers → summarize user intent → review/build based on that intent.
```

The tool should not jump straight from a raw deck report into final recommendations. It first gathers what the player actually wants the deck to do.

---

## What The Dragon’s Touch Does

The Dragon’s Touch can:

1. Read local Commander decklist `.txt` files.
2. Look up cards using a local Scryfall card database.
3. Identify commander color identity.
4. Check basic Commander legality concerns.
5. Identify overfilled, legal, underfilled, or card-pool-style decks.
6. Analyze likely deck strategy and synergy packages.
7. Generate a user-facing deck report.
8. Generate a guided review prompt for another AI chat.
9. Support cut-down reviews for overfilled or legal decks.
10. Support build-up reviews for incomplete decks.
11. Support build-from-scratch prompts for commander-only concepts.
12. Support optional collection/card-pool replacement candidates.
13. Generate debug/stress-test files for development and quality checks.

---

## Project Philosophy

The Dragon’s Touch is a **human-in-the-loop deck-building assistant**.

It is not meant to be an end-all-be-all deck optimizer.

It should:

1. Help the pilot understand what the deck is trying to do.
2. Identify cards that support the plan.
3. Identify cards that may be off-plan, redundant, replaceable, or worth reviewing.
4. Help incomplete decks move toward a legal 100-card Commander list.
5. Respect pet cards, protected cards, and emotional/theme choices.
6. Respect table intent and power expectations.
7. Avoid treating Game Changers or bracket pressure as automatic cuts.
8. Avoid treating the AI’s first guess as more important than the user’s stated plan.

Final decisions always belong to the player.

---

## Important Current Limits

The Dragon’s Touch currently does **not**:

1. Detect confirmed infinite combos from a combo database.
2. Use the Commander Spellbook API.
3. Import decklists directly from Archidekt, Moxfield, or MTGGoldfish.
4. Enforce Commander bracket rules.
5. Automatically cut Game Changers.
6. Guarantee perfect pricing or budget accuracy.
7. Guarantee a fully optimized final 100-card list.
8. Replace human deck-building judgment.

Combo-related questions in the generated prompt are currently **preference questions only**. The tool should not claim that it has confirmed infinite combos unless a future combo module is added.

---

## Required Files and Folders

A typical project folder should look like this:

```text
MTG Deck Helper/
├─ deck_helper.py
├─ data/
│  └─ scryfall_cards.json
├─ decklists/
│  └─ example_deck.txt
├─ rules/
│  ├─ card_attribute_rules.md
│  ├─ strategy_archetype_rules.md
│  ├─ cut_replacement_rules.md
│  └─ bracket_rules.md
├─ collections/
│  ├─ collection.txt
│  └─ card_pool.txt
└─ outputs/
```

Some folders may be created automatically when the script runs.

---

## Local Scryfall Card Database

The file:

```text
data/scryfall_cards.json
```

is the tool’s **local Scryfall card database**.

It is used as the offline card reference source for:

1. Card names.
2. Oracle text.
3. Type lines.
4. Color identity.
5. Mana value.
6. Commander legality data.
7. Card faces.
8. Basic land and duplicate-copy exceptions.
9. Role and strategy tag inference.

If this file is missing or outdated, card recognition and analysis quality may be worse.

---

## Decklist Input Format

The tool expects local `.txt` decklist files.

Common supported formats include:

```text
Commander
1 Miirym, Sentinel Wyrm

Deck
1 Sol Ring
1 Arcane Signet
1 Command Tower
```

Simple line formats are also supported:

```text
1 Sol Ring
1x Arcane Signet
Sol Ring
```

The script attempts to recognize sections such as:

```text
Commander
Deck
Creatures
Artifacts
Enchantments
Instants
Sorceries
Planeswalkers
Lands
```

It also tries to ignore non-mainboard/reference sections such as:

```text
Maybeboard
Sideboard
Tokens
Generated Tokens
Cuts
Considering
```

---

## Output Modes

When the script runs, it can create different output sets.

### 1. Normal User Mode

Best for ordinary deck review.

Typical files:

```text
DeckName_deck_report.txt
DeckName_user_guided_review_prompt.txt
```

or for build-up mode:

```text
DeckName_deck_report.txt
DeckName_build_up_review_prompt.txt
```

Use this mode when you want clean files to upload or paste into another AI chat.

### 2. Debug / Stress-Test Mode

Best for testing the script.

Typical files:

```text
01_DeckName_legality_report.txt
02_DeckName_strategy_report.txt
03_DeckName_bracket_report.txt
04_DeckName_cut_pressure_report.txt
05_DeckName_replacement_prompt.txt
06_DeckName_diagnostics.txt
DeckName_full_debug_report.txt
```

Use this mode when checking for overflagging, underflagging, strategy overfires, cut/protect conflicts, import problems, noisy tags, incorrect commander support, replacement issues, or batch QA problems.

### 3. Both Mode

Creates both normal user files and debug files.

Use this during development or broad testing.

---

## Review Direction

The tool asks whether the deck is being built up or cut down.

### Build Up / Complete to 100

Use this when the deck is under 100 cards, you only have commanders, you have a partial shell, you have an inspiration pool, or you want help adding cards.

Build-up modes include:

```text
1. Build from Scratch — commander only; Alpha feature
2. Point me in the right direction — 30+ cards needed
3. Help me get there — 11 to 30 cards needed
4. Finalize — 10 or fewer cards needed
```

Build from Scratch is currently an **Alpha feature** and still requires careful human review.

### Cut Down / Tune

Use this when the deck is over 100 cards, already legal but needs tuning, is a large card pool to trim, or needs cut/replacement/strategy review.

Cut depth modes include:

```text
1. Light
2. Normal
3. Strict
4. Brutal / Deep Review
5. Rebuild
6. Custom
```

---

## Cut Depth Modes

### Light

Only obvious problems: illegal cards, severe off-plan cards, very low-fit cards, and minimal optimization pressure.

### Normal

Practical tuning: reasonable cut candidates, synergy protection, and conservative default behavior.

### Strict

More serious optimization: more willing to pressure redundancy and low-impact cards while still protecting core engine cards.

### Brutal / Deep Review

Best for large pools or heavily overfilled decks. It gives a wider possible cut list and focuses on reaching a functional 100-card shell while still explaining replaceability.

### Rebuild

Treats the list as a rough pool and rebuilds toward the stated plan. It should not pretend the list is a finished deck.

---

## Prompt Interaction Modes

The Dragon’s Touch supports two prompt styles.

### 1. Interactive AI Chat

This is the recommended mode.

The reviewing AI asks one section at a time:

```text
Section 1 questions
→ user answers
→ AI summarizes Section 1
→ Section 2 questions
→ user answers
→ AI summarizes Section 2
→ continue
→ User Intent Summary
→ final review
```

This produces better results because the AI does not have to process every answer at once.

### 2. One-Shot Worksheet

This is an accessibility mode for free or limited-message AI use.

The reviewing AI asks all questions at once as a worksheet. The user can copy the worksheet, fill it out, and paste all answers back in one message.

Worksheet mode is useful for free AI tools with message limits, fewer back-and-forth messages, offline answering, or using another AI system such as Gemini, Claude, or a free ChatGPT session.

Worksheet mode is currently more experimental than interactive mode. It includes extra guardrails for color identity, banned cards, duplicate nonbasic cards, cards already in the deck, budget, casual table intent, required addition count, and final deck size validation.

---

## User-Guided Review Sections

The cut-down prompt uses these sections:

```text
Section 1 — Main Review Goal
Section 2 — Deck Plan
Section 3 — Commander Role
Section 4 — Protected / Pet / Build-Around Intent
Section 5 — Power / Bracket / Table Intent
Section 6 — Cut Philosophy
Section 7 — Replacement Philosophy and Output Questions
```

The build-up prompt uses sections focused on build-up context, commander plan/deck identity, power/table intent, card pool/budget/restrictions, and desired build output.

---

## User Intent Summary

Before final review, the reviewing AI must produce a User Intent Summary.

For cut-down reviews, the summary should include:

```text
Review Goal:
Deck Plan:
Commander Role:
Primary Strategy:
Secondary Strategy:
Theme / Package Intent:
Cut Depth:
Deck Size Status:
Power / Table Intent:
Replacement Preference:
Collection / Card Pool Restriction:
Cards Refused for Cuts:
Pet Cards / Protected Cards:
Cards to Build Around:
Cards User Is Uncertain About:
Cards Specifically Requested for Review:
Requested Output Style:
Assumptions / Unknowns:
```

For build-up reviews, the summary should include:

```text
Build-Up Mode:
Current Deck Status:
Cards Needed to Reach 100:
Commander Plan:
Primary Strategy:
Secondary Strategy:
Theme / Package Intent:
Power / Table Intent:
Card Pool Source:
Budget / Availability Limits:
Color / Theme Restrictions:
Protected / Must-Keep Cards:
Cards to Build Around:
Desired Addition Style:
Requested Output Style:
Assumptions / Unknowns:
```

The final review should follow this summary.

---

## Deck Size Behavior

### Over 100 Cards

```text
required_cuts = max(0, deck_card_count - 100)
```

Required cuts are mandatory and should be separated from optional optimization cuts.

### Exactly 100 Cards

No required cuts. Optional optimization cuts are allowed only if requested or useful.

### Under 100 Cards

No cut pressure unless rebuilding. The review should focus on additions, role gaps, shell completion, and construction needs.

### Large Card Pool / Inspiration Pool

The list should be treated as a trimming/building exercise, not a finished legal deck.

---

## Build-Up Addition Count

Build-up mode uses the deck size from the report as the source of truth.

Do not assume every build-from-scratch deck needs 98 additions.

Examples:

```text
Single commander only:
Current deck size: 1
Required additions: 99

Partner/background pair:
Current deck size: 2
Required additions: 98

Partial shell:
Current deck size: 67
Required additions: 33
```

The final addition list should contain exactly the number of cards needed to reach 100.

---

## Commander Color Identity Safety

Exact card suggestions must be legal within the commander’s color identity.

The reviewing AI should not recommend a card outside the commander’s color identity, even if that card supports the theme.

If a theme card is off-color, it should be identified as off-color and not included as a recommendation.

---

## Duplicate Recommendation Safety

The tool and generated prompts should avoid recommending cards already in the deck unless:

1. The card is a basic land.
2. The card has an explicit legal duplicate-copy exception.
3. The user specifically asks about adding more legal copies.

The reviewing AI should also avoid duplicate nonbasic recommendations in Commander.

---

## Banned Card Safety

The reviewing AI should not recommend banned Commander cards.

If a card would be strong but is banned, it should not be included in the recommended list.

---

## Bracket / Game Changer Policy

In v0.6, bracket and Game Changer information is context only.

The tool should not enforce brackets, treat Game Changers as automatic cuts, treat bracket pressure as a legality failure, or let power-level notes override user intent unless the user explicitly wants to tune up or tune down.

Bracket pressure may be used as a pregame conversation note.

---

## Interaction / Removal Policy

Interaction is important Commander infrastructure.

The tool should not over-cut targeted removal, board wipes, counterspells, protection, or stack interaction.

Removal and interaction should only be cut when clearly overrepresented, off-plan, inefficient for the deck’s needs, or when the user explicitly asks for fewer interaction pieces.

---

## Timing-Sensitive Synergy

The tool should be careful with temporary buffs.

Some commanders check power, toughness, counters, or other stats at end step. Temporary boosts that last “until end of turn” may still matter because the commander’s end-step trigger happens before the turn fully ends.

---

## Collection / Card Pool Support

The tool currently has early support for local collection/card-pool files.

Possible files:

```text
collections/collection.txt
collections/card_pool.txt
collections/collection.csv
collections/card_pool.csv
collection.txt
card_pool.txt
```

Environment variables:

```text
MTG_COLLECTION_FILE
MTG_CARD_POOL_FILE
```

Supported simple formats:

```text
1 Sol Ring
1x Sol Ring
Sol Ring
1,Sol Ring
Sol Ring,1
```

Current collection support can generate replacement or completion candidates from available cards.

The next planned development focus is stronger **collection-only / card-pool-only** behavior.

---

## Planned Next Version

Recommended next version:

```text
v0.6.3 — Collection-Only / Card-Pool-Only Support
```

Goal: allow the user to restrict additions and replacements to only the provided card pool.

Important distinction:

```text
Collection preferred = use collection first, then outside cards if needed.
Collection only = never recommend cards outside the provided pool.
```

Expected behavior:

1. Do not suggest cards outside the provided collection/card pool.
2. If no collection is loaded, ask the user to provide one.
3. If the pool cannot fill a role, say so.
4. Suggest missing categories instead of naming outside-pool cards.
5. Still obey color identity, legality, singleton rules, and duplicate protection.

Suggested report section:

```text
Collection-Only Build Feasibility
```

Possible contents:

```text
Collection file loaded: yes/no
Cards available in pool:
Legal color-identity candidates:
Role gaps the pool can fill:
Role gaps the pool cannot fill:
Warning if the pool is too small:
```

---

## Environment Variables

The script supports several environment variables for easier testing and batch runs.

Examples:

```text
MTG_DECK_FILE
MTG_OUTPUT_MODE
MTG_REVIEW_DIRECTION
MTG_BUILD_UP_MODE
MTG_CUT_DEPTH_MODE
MTG_OPTIONAL_CUT_TARGET
MTG_PROMPT_INTERACTION_MODE
MTG_COLLECTION_FILE
MTG_CARD_POOL_FILE
MTG_INTENDED_BRACKET
```

Common values:

```text
MTG_OUTPUT_MODE=normal
MTG_OUTPUT_MODE=debug
MTG_OUTPUT_MODE=both

MTG_REVIEW_DIRECTION=build_up
MTG_REVIEW_DIRECTION=cut_down

MTG_PROMPT_INTERACTION_MODE=interactive
MTG_PROMPT_INTERACTION_MODE=worksheet
```

---

## Running the Script

From the project folder, run:

```bash
python deck_helper.py
```

The script will ask you to select one or more Commander decklist files.

If multiple files are selected, it runs in batch mode.

---

## Recommended Workflow

### For normal deck review

1. Run `deck_helper.py`.
2. Choose Normal User Mode.
3. Choose Cut Down or Build Up.
4. Choose Interactive AI Chat mode.
5. Upload the generated deck report and prompt into an AI chat.
6. Answer the guided questions.
7. Review the User Intent Summary.
8. Get the final review/build plan.
9. Make final decisions yourself.

### For stress testing

1. Run `deck_helper.py`.
2. Choose Debug / Stress-Test Mode or Both Mode.
3. Review the debug files.
4. Look for repeated issues across decks.
5. Use findings to improve rules, prompts, and scoring.

### For free/limited-message AI use

1. Run `deck_helper.py`.
2. Choose Worksheet mode.
3. Upload/paste the deck report into the AI.
4. Fill out the worksheet.
5. Paste all answers back at once.
6. Check the final validation carefully.

Worksheet mode should be treated as experimental and requires closer human review.

---

## Known Development Priorities

Upcoming priorities include:

1. Collection-only / card-pool-only support.
2. Desktop App UI.
3. Better importer/failure handling.
4. Better broad testing support.
5. Future bracket and Game Changer tuning.
6. Possible future combo awareness through a separate data/API module.
7. Possible future Archidekt/Moxfield/MTGGoldfish importers.
8. Report polish.

---

## Naming Note

This project was previously referred to as:

```text
Deck Helper
MTG Commander Deck Helper
```

The planned project name is:

```text
The Dragon’s Touch
```

The internal script may still use names like `deck_helper.py` during development, but user-facing documentation can refer to the tool as **The Dragon’s Touch**.

---

## Disclaimer

The Dragon’s Touch is an unofficial fan-made deck-building support tool for Magic: The Gathering Commander.

It is not affiliated with, endorsed by, sponsored by, or approved by Wizards of the Coast, Scryfall, EDHREC, Commander Spellbook, Archidekt, Moxfield, MTGGoldfish, or any other Magic-related service.

Magic: The Gathering and related card names are property of Wizards of the Coast.

The tool is intended for personal deck-building support and educational use.

---

## Stability Recommendation

Current recommendation:

```text
Use v0.6.2.6 for continued testing.
Treat interactive prompt mode as stable.
Treat worksheet prompt mode as experimental but improved.
Begin v0.6.3 cleanup work for collection-only/card-pool-only support.
```
