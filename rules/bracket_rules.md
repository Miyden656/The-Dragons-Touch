# MTG Deck Helper — Commander Bracket Rules

**File:** `rules/bracket_rules.md`  
**Version:** v0.5.6 hotfix  
**Last reviewed:** 2026-05-01  
**Primary purpose:** Evaluate Commander bracket/table-fit pressure while keeping bracket logic separate from strategy detection and cut logic.

---

## Purpose

This rule file governs Commander bracket awareness.

The deck helper must use this file when it is asked to:

- Estimate a deck's likely Commander bracket
- Check whether a deck fits an intended bracket
- Explain why a deck may be above or below its intended bracket
- Review bracket pressure caused by Game Changers, fast mana, tutors, free interaction, high-power value, compact combos, mass land denial, or table-sensitive play patterns
- Separate bracket pressure from archetype identity
- Separate bracket pressure from automatic cut recommendations
- Separate social/table-experience warnings from raw power level
- Identify Rule Zero or legality-sensitive cards/packages
- Ask the user what bracket they are aiming for
- Give a bracket recommendation when the user does not know their intended bracket

This file should work alongside, but not replace:

- `card_attribute_rules.md`
- `strategy_archetype_rules.md`
- `cut_replacement_rules.md`
- `section_1_macro_archetypes_commander.md`
- `section_2_mechanical_themes_micro_archetypes.md`
- `section_3_strategic_board_politics.md`
- `section_4_typal_tribal_themes_rules.md`
- `section_5_1_niche_theme_rules.md`
- `section_5_2_fringe_theme_rules.md`
- `section_5_3_emergent_theme_rules.md`
- Scryfall-backed legality/card validation
- Commander banned list validation
- Color identity validation

This file does **not** replace the Commander banned list.

A banned card is still illegal even if it would otherwise fit a bracket.

---

# Core Principle

## Bracket pressure is a power/table-fit modifier, not a strategy label and not an automatic cut

Bracket logic answers:

> What kind of table experience does this deck appear to create?

Strategy logic answers:

> What is this deck actually trying to do?

Cut logic answers:

> Which cards are most replaceable based on legality, deck size, commander synergy, role balance, intended bracket, and user goals?

These must remain separate.

The deck helper must not let bracket pressure become:

- The deck's primary strategy
- An archetype score bonus
- A synergy score bonus
- A recommended cut by itself
- A cEDH label by itself
- A Turbo Combo label by itself

Bracket pressure should be tracked as:

- `bracket_modifier`
- `power_signal`
- `pregame_discussion_point`
- `possible_cut_if_lowering_bracket`
- `conflict_manual_review` when the card is core but bracket-pushing

---

# Required User Question

## Ask for intended bracket during cut/replacement review

When running a cut review, replacement review, optimization review, bracket review, or deck improvement review, the deck helper must ask:

> "What bracket are you aiming for with this deck? Bracket 1 Exhibition, Bracket 2 Core, Bracket 3 Upgraded, Bracket 4 Optimized, or Bracket 5 cEDH?"

If the user does not know, the deck helper should say:

> "No problem. I will give the general recommendation based on the bracket rules, visible Game Changers, win speed, combo pressure, and overall deck intent."

If the user provides an intended bracket, evaluate the deck against that bracket.

If the user does not provide an intended bracket, continue anyway and provide a best-effort bracket estimate.

Do not stall the review because the bracket is unknown.

---

# Bracket Overview

## Bracket 1 — Exhibition

### Intent

Bracket 1 is for highly thematic, unusual, expressive, ultra-casual decks.

Winning is not the primary goal. The main goal is showing off a theme, joke, story, restriction, or unusual deck-building idea.

### Expected play experience

Players generally expect:

- Theme over power
- Unusual deck construction
- Rule Zero flexibility
- Highly thematic or intentionally substandard win conditions
- Long games
- Time for the deck to show what it is doing
- A low-pressure social experience

### Turn expectation

A Bracket 1 game should generally allow players to play at least **nine turns** before they win or lose.

### Deck helper interpretation

Treat a deck as possible Bracket 1 if:

- The deck is clearly theme-first
- The win conditions are slow, cute, flavorful, or intentionally inefficient
- The deck is not optimized for consistency
- The deck may use odd restrictions or unusual commanders
- The deck is built more for expression than performance

### Bracket 1 pressure flags

A deck should usually be moved out of Bracket 1 if it has:

- Multiple Game Changers without a clear Rule Zero/thematic reason
- Fast mana packages
- Efficient tutors for best cards
- Consistent combo lines
- Efficient extra-turn chaining
- Mass land denial
- A game plan that regularly threatens to win before turn nine
- High optimization despite claiming to be theme-first

### Game Changers

By default, Bracket 1 decks should exclude Game Changers.

Exception:

- If a Game Changer is included for a highly thematic reason, move it into **Rule Zero / Manual Review**, not automatic failure.

---

## Bracket 2 — Core

### Intent

Bracket 2 is for low-pressure, socially focused Commander decks that are functional but not heavily optimized.

### Expected play experience

Players generally expect:

- Unoptimized or lightly optimized decks
- Straightforward game plans
- Creative, flavorful, pet-card, or lower-efficiency choices
- Incremental and telegraphed win conditions
- Win conditions that can be seen coming and disrupted
- Low-pressure gameplay
- Considerate play patterns
- Decks that are trying to win, but not trying to win quickly

### Turn expectation

A Bracket 2 game should generally allow players to play at least **eight turns** before they win or lose.

### Deck helper interpretation

Treat a deck as possible Bracket 2 if:

- It has a coherent plan but is not tuned for speed or consistency
- It can win through board presence, combat, incremental value, slow engines, or visible setup
- Its strongest turns are splashy but not abrupt
- It has imperfect, flavorful, budget, pet, or lower-efficiency choices
- It avoids cards and packages that strongly signal higher-power play

### Bracket 2 pressure flags

Bracket 2 decks should generally avoid:

- Game Changers
- Intentional two-card infinite combos
- Mass land denial
- Efficient early combo lines
- Chained or looped extra turns
- Heavy fast mana
- Dense tutor packages designed to find the same best cards every game
- Win conditions that regularly happen before turn eight
- Highly optimized card quality across nearly every slot

### Game Changers

Bracket 2 decks should have **0 Game Changers**.

If a Bracket 2 deck contains one or more Game Changers:

- Flag the card(s)
- Explain why they create bracket pressure
- Usually recommend cutting the card or Rule Zero discussion if the user wants strict Bracket 2
- Do not automatically upgrade the whole deck to Bracket 3 if the Game Changer is not structurally supported
- Mark the card as bracket pressure first, not as an automatic cut

---

## Bracket 3 — Upgraded

### Intent

Bracket 3 is for tuned casual Commander decks that are stronger than Core decks but are still socially focused.

### Expected play experience

Players generally expect:

- Strong synergy
- Higher card quality
- More interaction
- More efficient engines
- Some Game Changers
- Big turns from accrued resources
- Proactive and reactive gameplay
- Stronger win conditions than Bracket 2
- A deck that has been intentionally upgraded

### Turn expectation

A Bracket 3 game should generally allow players to play at least **six turns** before they win or lose.

### Deck helper interpretation

Treat a deck as possible Bracket 3 if:

- The deck has a focused plan and a strong engine
- Most cards support the deck's main strategy
- The deck has enough interaction to disrupt opponents
- The deck can produce powerful turns
- The deck may contain up to three Game Changers
- The deck may win with a large, decisive turn after setup
- The deck is not primarily built for early combo kills

### Bracket 3 pressure flags

Bracket 3 decks should generally avoid:

- More than three Game Changers
- Intentional early-game two-card infinite combos
- Combo lines that regularly threaten wins before turn six
- Mass land denial
- Extra-turn chaining or loops
- Extremely dense fast mana
- cEDH-style compact win packages
- Tutor density that makes the deck play the same optimized line every game
- Bracket 4 speed or consistency

### Game Changers

Bracket 3 allows **up to three Game Changers**.

If the deck contains 1–3 Game Changers:

- List them
- Explain whether they support the deck's plan or are generic power
- Flag whether they are likely acceptable for Bracket 3

If the deck contains 4+ Game Changers:

- Flag bracket pressure
- Usually recommend Bracket 4 unless the user wants to cut down to three or fewer
- Do not call the deck cEDH from Game Changer count alone

---

## Bracket 4 — Optimized

### Intent

Bracket 4 is for high-powered Commander decks that are fast, lethal, consistent, and optimized, but not necessarily built around the cEDH tournament metagame.

### Expected play experience

Players generally expect:

- Fast, lethal, consistent decks
- Highly optimized card choices
- Strong tutors
- Efficient combos
- Explosive starts
- Powerful disruption
- Strong fast mana
- Many or unlimited Game Changers
- Efficient win conditions
- Decks that may end games quickly

### Turn expectation

A Bracket 4 game should generally allow players to play at least **four turns** before they win or lose.

### Deck helper interpretation

Treat a deck as possible Bracket 4 if:

- The deck is built for high-power play
- It can present wins or overwhelming advantage quickly
- It has many Game Changers
- It uses efficient tutors to assemble its best lines
- It uses compact combo lines
- It has fast mana or free interaction
- It has high card quality across most slots
- It does not appear to be tuned specifically for a cEDH metagame

### Game Changers

Bracket 4 allows unlimited Game Changers.

Still list Game Changers because they matter for pregame communication.

---

## Bracket 5 — cEDH

### Intent

Bracket 5 is for competitive Commander.

These decks are built to win as efficiently as possible within the Commander banned list and the known cEDH metagame.

### Expected play experience

Players generally expect:

- Metagame-aware deck construction
- Highly efficient win conditions
- Fast mana
- Dense interaction
- Free spells
- Efficient tutors
- Compact combo wins
- High consistency
- Tight sequencing
- Winning as the main priority
- Advanced gameplay with little margin for error

### Turn expectation

Bracket 5 games can end on any turn.

### Deck helper interpretation

Only call a deck Bracket 5 if:

- The deck is clearly attempting to be cEDH
- The card choices match known competitive patterns
- The deck is built around optimized win lines
- It has speed, interaction, mana, and consistency expected of cEDH
- It has compact win conditions backed by efficient mana, tutors, and protection
- The user states that the deck is intended for cEDH, or the list strongly indicates it

Do not call a deck cEDH simply because it has:

- Expensive cards
- Several Game Changers
- A combo
- Fast mana
- A high win rate in a casual pod
- A powerful commander
- A single high-power value card
- A slow alternate win condition
- A large mana-sink finisher

Many powerful decks are Bracket 4, not Bracket 5.

---

# Separation of Strategy, Bracket, Politics, Legality, and Cuts

## Bracket does not define archetype

A deck can be:

- Token Combat at Bracket 2
- Token Combat at Bracket 4
- Dragon Tutor Chain at Bracket 3
- Dragon Tutor Chain at Bracket 5
- Political Group Slug at Bracket 2
- Political Group Slug at Bracket 4
- Stax at Bracket 3 with table consent
- Stax at Bracket 4 with optimized lock pieces

The bracket modifies the table-fit assessment.

It does not define the archetype.

## Bracket pressure does not increase archetype synergy score

The following should **not** increase archetype synergy score by themselves:

- Fast mana
- Free interaction
- Efficient tutors
- Game Changers
- Mass land denial
- High-power value pieces
- Bracket-pressure cards
- Salt-risk cards
- Rule Zero cards
- Reputation-pressure cards

These are report modifiers unless they also pass a relevant strategy gate in the dedicated strategy files.

## Strategy labels require strategy gates

Do not make the primary strategy become any of the following from bracket pressure alone:

- Turbo Combo
- Ramp-Control
- Generic Control
- Artifact/Treasure Tutor Chain
- Generic Value
- Generic Goodstuff
- Stax
- Politics
- Villain Deck

Only assign those strategies if the deck passes the relevant strategy gate from the appropriate section rules.

## Examples

```text
Fast mana + token deck = higher-power Token Combat, not automatically Ramp-Control.
```

```text
Efficient tutor + Dragon deck = bracket pressure or Dragon Tutor Chain only if the Dragon tutor-chain gate passes.
```

```text
Pillowfort + slow win condition = table-fit/stall review, not automatically high-power Control.
```

```text
Group Hug + kingmaker risk = politics warning, not high bracket by itself.
```

```text
Acorn or outside-game component = Rule Zero review, not bracket level by itself.
```

---

# Classification Tags

The deck helper must use the following tags when evaluating bracket and table-fit pressure.

These tags are not mutually exclusive.

A card may have multiple tags.

---

## Power / bracket tags

### `game_changer`

Use for cards on the current Commander Game Changers list.

A Game Changer is not banned.

A Game Changer is a bracket marker.

Game Changers should be counted separately from general bracket pressure.

---

### `bracket_pressure`

Use for cards, packages, or play patterns that may push a deck above the user's intended bracket.

A bracket-pressure card may be:

- Powerful and correct for the deck
- Correct only at a higher bracket
- Wrong for the intended table
- Core but requiring pregame discussion
- A possible cut only if the user wants a lower bracket

Do not treat `bracket_pressure` as the same thing as `recommended_cut`.

---

### `high_bracket_pressure`

Use for cards or packages that strongly indicate Bracket 4 or Bracket 5 pressure.

Examples include:

- Multiple Game Changers beyond Bracket 3 limits
- Compact two-card combo packages with tutors and protection
- True fast mana plus efficient tutors plus early win lines
- Mass land denial in Bracket 1–3
- Extra-turn loops
- Dense free interaction supporting fast combo
- Highly consistent early deterministic wins

Use this tag carefully.

Do not apply it to a single expensive payoff, slow win condition, or powerful value card unless the surrounding deck infrastructure supports it.

---

### `bracket_pressure_possible`

Use when a card may create bracket pressure, but deck context is not enough to make a strong claim.

Useful for:

- High-power value pieces without fast lines
- Slow alternate win conditions
- Powerful but fair haymakers
- One-off efficient tutors
- One-off extra-turn cards without loops
- Cards that are scary by reputation but not supported by the deck's plan

Cards with `bracket_pressure_possible` should usually go to review flags, not recommended cuts.

---

### `high_power_value_piece`

Use for cards that generate major advantage but are not combo pieces by themselves.

Examples include:

- Explosive card advantage engines
- Repeatable treasure or mana engines
- One-card value engines that dominate long games
- High-efficiency protection/value cards
- Board resets that radically reshape the game
- Resource engines that are strong but do not directly assemble a deterministic win

Default tags:

```text
high_power_value_piece, high_power_value_not_turbo, bracket_pressure_possible
```

Do not tag a high-power value piece as `true_turbo_combo` unless it is paired with fast mana, efficient tutors, compact combo pieces, protection, and realistic early win pressure.

---

### `high_power_value_not_turbo`

Use when a card is strong enough to affect bracket estimate but is not a combo engine.

This tag prevents misclassification into Turbo Combo or cEDH.

---

## Combo-related tags

### `compact_combo_piece`

Use for a card that is part of a small deterministic combo, usually two or three cards.

This tag does not automatically mean the card is a cut.

Evaluate:

- Is the combo actually present?
- Is the combo intentional?
- Is the combo efficient?
- Is the combo commander-supported?
- Is the combo easy to find?
- Is the combo protected?
- Does the combo regularly win before the intended bracket's expected turn window?

A compact combo piece without tutors, protection, or fast mana may be manual review rather than high bracket pressure.

---

### `fast_combo_enabler`

Use for cards that accelerate, cheat, discount, untap, copy, or recur combo pieces in a way that creates realistic early win pressure.

Do not tag normal ramp or fair synergy as `fast_combo_enabler` unless it actually supports early combo pressure.

---

### `true_turbo_combo`

Use only when the deck passes the hard turbo gate.

Do not use this tag for:

- A single powerful card
- A single efficient tutor
- A single Game Changer
- A slow alternate win condition
- A high-power value piece
- A high-cost finisher
- A combo that exists but is slow, fragile, or unsupported
- A deck that merely has a possible combo line

---

### `combo_protection`

Use for cards that make combo wins difficult to stop.

Examples of function:

- Free counterspells
- Cheap protection spells
- Silence effects
- Hand attack used to clear the way
- Grand Abolisher-style effects
- Protection attached to commander text
- Recursion that easily recovers failed combo attempts

Do not call a deck turbo combo just because it has one protection spell.

---

### `efficient_tutor`

Use for low-cost, flexible, or highly reliable tutors.

Some efficient tutors are also Game Changers.

A tutor does not automatically make a deck high bracket.

Evaluate:

- What does it usually find?
- Does it repeatedly find the same best card?
- Does it assemble a compact combo?
- Does it find a slow value piece?
- Does it find interaction or utility?
- Is it one tutor or part of a tutor package?

---

### `tutor_chain`

Use when the deck has enough tutors, recursion, or search effects to reliably find the same win condition or line across games.

Do not use `tutor_chain` for a deck simply because it has one or two tutors.

A tutor chain usually requires:

- Multiple efficient tutors
- Repeated access to tutors
- Tutors that find tutors
- Commander-supported searching
- Redundant combo pieces
- A clear repeated destination card or line

A tutor chain with slow, fair, or utility targets may create bracket pressure but is not automatically true turbo combo.

---

## Slow alternate win tags

### `slow_alt_win_condition`

Use for cards that can win the game but usually require time, mana investment, visible setup, repeated activations, or a full turn cycle.

Examples include:

- Large mana-sink win conditions
- Slow enchantment win conditions
- High-cost value finishers
- Expensive alternate win conditions
- Telegraphed win conditions that opponents can interact with
- Win conditions that require repeated activations
- Win conditions that require surviving until a later upkeep or later combat

Default tags:

```text
slow_alt_win_condition, visible_win_condition, protected_setup_required, not_turbo_combo
```

Only upgrade pressure if the deck also has:

- Efficient tutors
- Fast mana
- Protection
- Shortcut combo pieces
- Commander support that makes the win immediate or fast

---

### `visible_win_condition`

Use when the win condition is visible, telegraphed, and interactable.

This tag reduces the chance of misclassifying the card as turbo combo.

---

### `protected_setup_required`

Use when the win condition needs protection, pillowfort, control, lifegain, counters, tokens, artifacts, lands, or other setup to survive long enough to win.

---

### `not_turbo_combo`

Use as an explicit suppression tag when a card is a win condition but does not meet true turbo combo requirements.

---

## Land denial / table pressure tags

### `mass_land_denial`

Use for cards and plans that regularly destroy, exile, bounce, lock, or disable many lands.

This includes:

- Mass land destruction
- Mass land bounce
- Nonbasic land punishment that strongly prevents normal play
- Land lock pieces
- Mana conversion effects that shut off many decks
- Recurring land denial engines

Mass land denial should not appear in Brackets 1–3 without explicit Rule Zero discussion.

If the intended bracket is 1–3, tag these cards as:

```text
mass_land_denial, high_bracket_pressure, salt_risk, pregame_discussion_piece
```

---

# Political and Salt-Risk Bracket Review

Political and salt-risk signals are social/table-experience warnings.

They are not automatically high bracket.

They are not automatically primary strategy.

They are not automatic cuts.

Use these tags when appropriate:

```yaml
political_bracket_review_tags:
  table_dependency:
  kingmaker_risk:
  salt_risk:
  stall_risk:
  reputation_pressure:
  archenemy_pressure:
  pregame_discussion_piece:
```

## `table_dependency`

Use when a card or package depends heavily on opponent behavior, table talk, creature-heavy pods, negotiation, or players making certain choices.

Examples:

- Forced combat
- Goad
- Group Hug
- Voting
- Bounty effects
- Political gifts
- Theft/clone politics

This is not automatically high bracket.

---

## `kingmaker_risk`

Use when the deck can accidentally help one opponent more than the pilot.

Examples:

- Group Hug may be low bracket but high kingmaker risk.
- Gift effects may help the current threat.
- Table-balancer cards may determine which opponent wins without advancing the pilot.

This is a table-experience warning, not a power-level label.

---

## `salt_risk`

Use for effects that may create table frustration.

Examples:

- Stax
- Mass land denial
- Repeated extra turns
- Hard locks
- Discard locks
- Theft-heavy packages
- Chaos that prevents progress
- Board resets without a closer

Salt risk may overlap with bracket pressure, but it is not the same thing.

---

## `stall_risk`

Use when a card or package slows the game without clearly advancing a win condition.

Examples:

- Pillowfort may stall games without being high power.
- Board resets may prolong games without ending them.
- Soft locks may delay but not close.

Stall risk should trigger pregame notes and win-condition review.

---

## `reputation_pressure`

Use when a commander, archetype, or card package draws early attention regardless of actual list power.

Examples:

- Villain commanders
- Famous combo commanders
- High-salt commanders
- Theft/discard/stax reputations
- Known oppressive archetypes

Reputation pressure may require resilience or pregame explanation.

It is not an archetype by itself.

---

## `archenemy_pressure`

Use when the deck is likely to become the table's main threat early.

This may happen because of:

- Commander reputation
- Visible oppressive pieces
- Large board presence
- Obvious combo threat
- High-salt effects
- Fast resource snowball

Do not equate archenemy pressure with cEDH.

---

## `pregame_discussion_piece`

Use when a card or package should be mentioned before the game.

Examples:

- Group Hug with kingmaker risk
- Stax with salt risk
- Villain deck reputation pressure
- Pillowfort with stall risk
- Forced combat in creature-light pods
- Rule Zero cards
- Outside-game components
- Bracket 2 Game Changers
- Fourth-plus Game Changers in Bracket 3

---

# Rule Zero and Legality-Sensitive Review

Rule Zero and legality-sensitive cards are not bracket levels by themselves.

A card can be normal-power but still require Rule Zero.

Use these tags:

```yaml
rule_zero_legality_tags:
  rule_zero_review:
  nonstandard_legality_review:
  outside_game_component:
  acorn_or_silver_border_review:
  attraction_or_sticker_component:
  table_permission_needed:
```

## `rule_zero_review`

Use when a card, commander, or package requires explicit table agreement or exists outside normal Commander assumptions.

This is a legality/table-permission issue, not a power-level issue.

---

## `nonstandard_legality_review`

Use when a card or component may not be legal in normal Commander.

This should trigger legal validation and a report note.

---

## `outside_game_component`

Use when a strategy requires objects outside the deck/game, such as separate decks or sheets.

Examples:

- Attraction deck
- Sticker sheet
- Contraption deck
- Other outside-game components

---

## `acorn_or_silver_border_review`

Use for acorn, silver-border, Un-set, or otherwise nonstandard cards.

Do not assume these are legal or accepted at every Commander table.

---

## `attraction_or_sticker_component`

Use for Attractions, Stickers, or related physical component mechanics.

These require special handling and should not be mistaken for normal artifact/enchantment/token support.

---

## `table_permission_needed`

Use when table acceptance is the central issue.

If the user says the table allows it, preserve the theme and evaluate it on its own terms.

If the user wants normal Commander legality, increase cut pressure on nonstandard cards.

---

# Bracket Pressure Is a Report Modifier

## Do not feed bracket pressure into strategy scoring

When strategy rules score archetypes, bracket-pressure tags should contribute **0 archetype points** unless the card also has a separate legitimate strategy role.

Suggested scoring behavior:

```yaml
strategy_score_interaction:
  bracket_pressure_card:
    strategy_points: 0
    note: Track separately from archetype score.

  game_changer:
    strategy_points: 0
    note: Track separately as Game Changer count and power signal.

  fast_mana:
    strategy_points: 0
    note: Track as bracket modifier unless it supports an actual strategy gate.

  free_interaction:
    strategy_points: 0
    note: Track as power signal and protection, not primary strategy.

  efficient_tutor:
    strategy_points: 0
    note: Track as consistency signal unless tutor-chain strategy gate passes.

  mass_land_denial:
    strategy_points: 0
    note: Track as table-fit and salt-risk pressure unless Mass Land Denial strategy gate passes.

  high_power_value_piece:
    strategy_points: 0
    note: Track as power signal unless it supports the real strategy.
```

## Strategy gate requirement

Do not assign the following labels unless their relevant gate passes:

```python
def bracket_pressure_cannot_define_strategy(
    bracket_pressure_tags,
    strategy_gate_passed
):
    if bracket_pressure_tags and not strategy_gate_passed:
        return "report_modifier_only"
    return "strategy_label_allowed"
```

This prevents:

- A Token deck with fast mana from becoming Ramp-Control
- A Dragon deck with tutors from becoming Tutor Chain unless the Dragon/Treasure Tutor Chain gate passes
- A political deck with salt risk from becoming high-power Control
- A high-power value deck from becoming Turbo Combo
- A Rule Zero package from becoming a bracket level

---

# True Turbo Combo Hard Gate

Use this hard gate before assigning `true_turbo_combo`.

```python
def can_be_true_turbo_combo(
    fast_mana_count,
    efficient_tutor_count,
    compact_combo_count,
    protection_count
):
    return (
        fast_mana_count >= 3
        and efficient_tutor_count >= 3
        and compact_combo_count >= 1
        and protection_count >= 2
    )
```

Do not use `true_turbo_combo` if this gate fails.

If the gate fails, use one of these instead:

- `possible_combo_piece_manual_review`
- `combo_adjacent_value`
- `backup_combo`
- `compact_combo_piece`
- `bracket_pressure_possible`
- `high_power_value_not_turbo`
- `slow_alt_win_condition`
- `not_turbo_combo`

## Turbo Combo suppression rule

Do not call a deck Turbo Combo / Fast Tutor Chain unless multiple of these exist:

- True fast mana
- Efficient tutors
- Compact combo pieces
- Combo protection
- Commander-supported fast win line
- Repeated ability to find the same win condition
- Realistic early win pressure

A single powerful card, slow alternate win condition, high-power value piece, expensive payoff, or theoretical combo is not enough.

---

# Combo Centrality Categories

Separate "has combo" from "is combo."

Use these categories:

```yaml
combo_centrality:
  no_combo_detected:
  possible_combo_piece_manual_review:
  combo_adjacent_value:
  backup_combo:
  combo_primary:
  true_turbo_combo:
```

## `no_combo_detected`

Use when no meaningful combo piece or combo line is visible.

---

## `possible_combo_piece_manual_review`

Use when the deck has one possible combo piece, one partial interaction, or one missing-piece combo signal.

The deck should not be called combo-primary just because it has one possible combo piece.

---

## `combo_adjacent_value`

Use when the deck contains synergy loops or value engines that can become overwhelming but are not primarily deterministic wins.

Examples:

- Sacrifice-recursion value loops
- Artifact token value loops
- Blink value loops
- Landfall/resource engines
- Treasure engines that generate advantage but not an immediate deterministic win

---

## `backup_combo`

Use when the deck has a real combo line, but the primary plan appears to be combat, value, control, typal, politics, or another strategy.

Backup combo may create bracket pressure, but it should not override primary strategy unless it is the main win plan.

---

## `combo_primary`

Use when combo is a major deck plan, but the deck does not meet the true turbo combo hard gate.

Usually requires:

- Multiple combo pieces
- Some redundancy
- Some tutor/card-selection support
- Commander support or clear payoff
- Combo plan more central than combat/value

---

## `true_turbo_combo`

Use only when the true turbo combo hard gate passes and the deck has realistic early win pressure.

---

# Slow Alternate Win Condition Handling

Slow alternate win condition is not true turbo combo.

Use:

```text
slow_alt_win_condition
visible_win_condition
protected_setup_required
not_turbo_combo
```

Examples of slow alternate win categories:

- Large mana-sink win conditions
- Slow enchantment win conditions
- High-cost value finishers
- Delayed alternate-win conditions
- Expensive one-card closers
- Win conditions that require surviving to a later turn
- Win conditions that require multiple visible steps

Only upgrade to combo/bracket pressure if the deck also has:

- Efficient tutors
- Fast mana
- Protection
- Shortcut combo pieces
- Commander support that makes the win immediate or fast

If these supports are absent, report the card as:

```text
slow_alt_win_condition, visible_win_condition, protected_setup_required, not_turbo_combo
```

---

# High-Power Value but Not Turbo Combo

High-power value can raise bracket estimate without making the deck cEDH or Turbo Combo.

Use:

```text
high_power_value_piece
high_power_value_not_turbo
bracket_pressure_possible
```

High-power value includes:

- Explosive draw engines
- Snowballing resource engines
- High-efficiency protection/value pieces
- Board resets with unusual table impact
- Strong mana/value engines
- Cards that dominate fair games but do not directly assemble deterministic wins

Do not call these Turbo Combo unless the true turbo combo hard gate passes.

---

# Game Changers

## Definition

Game Changers are cards that can dramatically warp Commander games.

They often do one or more of the following:

- Let a player run away with resources
- Create overwhelming card, mana, or board advantage
- Shift the game in ways many players dislike
- Stop players from playing normally
- Efficiently search for the strongest cards
- Create high-power expectations
- Signal a different kind of pregame conversation
- Make a deck less appropriate for lower brackets

Game Changers are not banned.

They are bracket markers.

---

## Game Changer Limits by Bracket

| Bracket | Game Changer expectation |
|---|---:|
| Bracket 1 — Exhibition | 0 by default; Rule Zero/manual review if strongly thematic |
| Bracket 2 — Core | 0 |
| Bracket 3 — Upgraded | Up to 3 |
| Bracket 4 — Optimized | Unlimited |
| Bracket 5 — cEDH | Unlimited |

---

## Game Changer rules

The deck helper must follow these rules:

- Game Changers in Bracket 1 are usually 0 unless Rule Zero/theme supports them.
- Game Changers in Bracket 2 should be 0.
- Game Changers in Bracket 2 should usually be cut or Rule Zero discussed if the user wants strict Bracket 2.
- Bracket 3 can include limited Game Changers, up to 3.
- Fourth-plus Game Changer usually creates Bracket 4 pressure.
- Bracket 4 allows unlimited Game Changers.
- Bracket 5 allows unlimited Game Changers but requires competitive intent, speed, consistency, compact combos, and cEDH construction.
- Game Changer count alone does not equal cEDH.
- A Game Changer that is core to the deck may belong in Conflict / Manual Review instead of Recommended Cuts.
- A Game Changer that is off-plan may be a stronger cut candidate if the intended bracket is lower.
- A Game Changer that is included as a pet card or thematic card may be Rule Zero / Manual Review instead of an automatic bracket upgrade.

---

# Current Game Changers List

The deck helper must treat the following cards as Game Changers.

## White

- Drannith Magistrate
- Enlightened Tutor
- Farewell
- Humility
- Serra's Sanctum
- Smothering Tithe
- Teferi's Protection

## Blue

- Consecrated Sphinx
- Cyclonic Rift
- Fierce Guardianship
- Force of Will
- Gifts Ungiven
- Intuition
- Mystical Tutor
- Narset, Parter of Veils
- Rhystic Study
- Thassa's Oracle

## Black

- Ad Nauseam
- Bolas's Citadel
- Braids, Cabal Minion
- Demonic Tutor
- Imperial Seal
- Necropotence
- Opposition Agent
- Orcish Bowmasters
- Tergrid, God of Fright
- Vampiric Tutor

## Red

- Gamble
- Jeska's Will
- Underworld Breach

## Green

- Biorhythm
- Crop Rotation
- Gaea's Cradle
- Natural Order
- Seedborn Muse
- Survival of the Fittest
- Worldly Tutor

## Multicolor

- Aura Shards
- Coalition Victory
- Grand Arbiter Augustin IV
- Notion Thief

## Colorless and Lands

- Ancient Tomb
- Chrome Mox
- Field of the Dead
- Glacial Chasm
- Grim Monolith
- Lion's Eye Diamond
- Mana Vault
- Mishra's Workshop
- Mox Diamond
- Panoptic Mirror
- The One Ring
- The Tabernacle at Pendrell Vale

---

# Bracket Pressure Evaluation

Evaluate bracket pressure using all of the following factors.

No single factor automatically determines bracket, except where bracket rules clearly set a limit, such as Game Changer count for Bracket 2 or Bracket 3.

Even then, the result should be:

- A bracket estimate
- A bracket-pressure explanation
- A possible adjustment path

not an automatic statement that the deck is illegal or bad.

## 1. Game Changer count

Count every Game Changer in:

- Main deck
- Commander slot
- Partner commander slots
- Background or companion-like deck-defining slots if applicable

Report:

- Total Game Changers
- Names of Game Changers
- Whether each one supports the commander plan or is generic power
- Whether the total exceeds the user's intended bracket
- Whether any Game Changer is core enough to require Conflict / Manual Review

## 2. Win speed

Estimate whether the deck can reasonably win or create a functionally winning state before:

- Turn 9 for Bracket 1
- Turn 8 for Bracket 2
- Turn 6 for Bracket 3
- Turn 4 for Bracket 4

Do not judge only by goldfish speed.

Consider:

- Commander dependency
- Setup required
- Mana requirements
- Tutor density
- Protection
- Interaction from opponents
- Whether the line is realistic or magical Christmasland
- Whether the win is compact and deterministic or slow and telegraphed

A slow alternate win condition that wins after setup is not the same as turbo combo.

## 3. Combo pressure

Flag combos by centrality and type.

For each combo, estimate:

- Speed
- Consistency
- Tutor support
- Protection
- Whether it is the primary plan
- Whether it fits the intended bracket
- Whether it is realistic or theoretical
- Whether the commander directly supports it
- Whether the deck can repeatedly find it

Do not overreact to accidental or low-consistency combos.

Do not call a deck turbo combo unless it passes the true turbo combo hard gate.

## 4. Tutor pressure

Tutor restrictions have been removed from the bracket system, but efficient tutors still matter because many are Game Changers and because tutor density affects consistency.

Do not say "too many tutors" as a hard bracket violation by itself.

Instead, say:

- "The tutor density increases consistency and may push this deck toward a higher bracket."
- "These tutors are mostly slow/narrow and do not strongly increase bracket pressure."
- "These efficient tutors are Game Changers and directly affect the bracket estimate."
- "The deck appears to use tutors to repeatedly find the same win condition."
- "The deck has tutors, but they mostly find fair value, ramp, lands, or utility rather than compact wins."

## 5. Fast mana pressure

Fast mana increases bracket pressure when it enables early explosive starts.

Flag:

- Mana-positive rocks
- Zero-mana mana artifacts
- Lands that produce more than one mana early
- Rituals that enable early wins
- Fast mana combined with commanders or payoff cards that snowball quickly

Fast mana is especially relevant for Bracket 4 and Bracket 5 classification.

Do not treat normal ramp, fair land ramp, or medium-speed mana rocks as true fast mana.

## 6. Mass land denial

Mass land denial should not appear in Brackets 1–3 without explicit Rule Zero discussion.

Mass land denial includes cards and plans that regularly:

- Destroy many lands
- Exile many lands
- Bounce many lands
- Keep many lands tapped
- Change what mana many lands can produce
- Prevent opponents from meaningfully using lands

If the deck has mass land denial and the intended bracket is 1–3:

- Flag it as bracket-incompatible
- Mark it as `mass_land_denial, high_bracket_pressure, salt_risk, pregame_discussion_piece`
- Recommend removal if the user wants to stay in that bracket
- Otherwise recommend Bracket 4+ or Rule Zero discussion

## 7. Extra-turn pressure

Extra-turn cards are bracket pressure when they are:

- Chained
- Looped
- Copied repeatedly
- Recurred repeatedly
- Used as a primary win plan
- Supported by tutors and recursion to happen consistently

Low-quantity, non-looping extra-turn cards may be acceptable in Bracket 2 or 3 if they are not the main plan and do not regularly create repetitive gameplay.

Do not overclassify a single expensive extra-turn spell as turbo combo unless it is part of a repeated-turn engine.

## 8. Stax / play prevention pressure

Stax and play-prevention cards increase bracket pressure when they:

- Stop opponents from casting spells
- Lock players out of resources
- Prevent normal game actions
- Create repeated non-games
- Combine with fast clocks or hard locks
- Are part of the deck's main plan

Do not automatically call all stax cards Bracket 4.

Evaluate severity, density, symmetry, commander support, parity breaking, win condition, salt risk, and how early the lock appears.

## 9. Resource snowball pressure

A card or package creates resource snowball pressure when it can pull a player far ahead quickly.

Flag:

- Explosive card draw
- Repeatable treasure generation
- Fast token-to-mana engines
- Free spell engines
- Untap engines
- Land engines that produce overwhelming mana
- Commander-supported repeatable value that is hard to disrupt

Resource snowball pressure matters most when combined with:

- Fast mana
- Efficient tutors
- Protection
- Compact finishers
- Low curve

Resource snowball pressure alone is usually `high_power_value_piece` or `bracket_pressure_possible`, not true turbo combo.

## 10. Political / salt / table-fit pressure

Review:

- Table dependency
- Kingmaker risk
- Salt risk
- Stall risk
- Reputation pressure
- Archenemy pressure
- Pregame discussion needs

These may affect table fit without changing bracket estimate.

## 11. Rule Zero / legality-sensitive pressure

Review:

- Rule Zero cards
- Nonstandard legality
- Outside-game components
- Acorn or silver-border cards
- Attractions or stickers
- Table permission needs

These are not bracket levels by themselves.

## 12. Intent and table experience

A deck's bracket is partly about intent.

Ask:

- Is this deck trying to win as quickly as possible?
- Is this deck trying to create fair, interactive games?
- Is this deck built to showcase a theme?
- Is this deck built to test the strongest possible version of an idea?
- Is this deck intended for cEDH?
- Would opponents reasonably want advance warning before playing against this deck?

If the user's intended bracket and the deck's visible construction disagree, say so clearly and respectfully.

---

# Bracket-Driven Cut Logic

Bracket pressure is not the same as a cut.

A bracket-pressure card may be:

- Powerful and correct for the deck
- Correct only at a higher bracket
- Wrong for the intended table
- Core but requiring pregame discussion
- A possible cut only if the user wants a lower bracket

## If intended bracket is known

Use this logic:

```text
If bracket pressure is above target and the card is off-plan:
    It may become a Possible Bracket Pressure Cut or Recommended Cut.

If bracket pressure is above target and the card is on-plan:
    Move it to Conflict / Manual Review.

If bracket pressure is above target and the card is core:
    Move it to Conflict / Manual Review.

If the card is powerful but bracket-compatible:
    Do not cut for bracket reasons.

If the user accepts a higher bracket:
    Bracket-pressure cards may be correct keeps.
```

## If intended bracket is unknown

Do not cut solely for bracket.

Flag for review and estimate likely bracket.

Required wording:

> "The intended bracket is unknown, so this is a review flag rather than an automatic cut."

## Core but bracket-pressure cards

A card can be both:

- Strategically correct for the deck
- Core to the deck's plan
- A source of bracket pressure

When this happens, do not put it in:

- Protected From Cut
- Recommended Cut

Instead, move it to:

## Conflict / Manual Review

Required language:

> "This card strongly supports the deck's plan, but it may push the deck above the intended bracket."

Use this structure:

```markdown
## Conflict / Manual Review

- Card Name — This card strongly supports the deck's plan, but it may push the deck above the intended bracket.
  - Pressure type: game_changer / high_power_value_piece / compact_combo_piece / efficient_tutor / mass_land_denial / salt_risk / rule_zero_review / etc.
  - Keep if: you are comfortable moving toward Bracket Y or having a Rule Zero discussion.
  - Cut if: you want to stay closer to Bracket X.
```

---

# Bracket / Power Read Report Requirements

When bracket rules are used, include a section titled:

## Bracket / Power Read

Use this structure:

```markdown
## Bracket / Power Read

**Intended bracket:** Bracket X / Unknown  
**Estimated bracket:** Bracket Y  
**Confidence:** Low / Medium / High  

### Game Changer Count
- Total Game Changers: X
- Game Changers found:
  - Card Name — reason it matters

### Bracket Pressure Cards
- Card Name — pressure type — explanation

### High-Power Value Pieces
- Card Name — high_power_value_piece, high_power_value_not_turbo, bracket_pressure_possible — explanation

### Slow Alternate Win Conditions
- Card Name — slow_alt_win_condition, visible_win_condition, protected_setup_required, not_turbo_combo — explanation

### Combo Centrality
- no_combo_detected / possible_combo_piece_manual_review / combo_adjacent_value / backup_combo / combo_primary / true_turbo_combo
- Explanation:

### True Turbo Combo Gate Result
- Fast mana count:
- Efficient tutor count:
- Compact combo count:
- Protection count:
- Gate passed: Yes / No
- Result:

### Political / Salt Risk
- table_dependency:
- kingmaker_risk:
- salt_risk:
- stall_risk:
- reputation_pressure:
- archenemy_pressure:
- pregame_discussion_piece:

### Rule Zero / Legality-Sensitive Notes
- rule_zero_review:
- nonstandard_legality_review:
- outside_game_component:
- acorn_or_silver_border_review:
- attraction_or_sticker_component:
- table_permission_needed:

### Cards That Are Core but Bracket-Pushing
- Card Name — This card strongly supports the deck's plan, but it may push the deck above the intended bracket.

### Cards That Are Off-Plan and Bracket-Pushing
- Card Name — possible bracket-pressure cut if user wants lower bracket

### Pregame Discussion Notes
- Note what the pilot should tell the table before the game.
```

---

# Replacement Guidance by Intended Bracket

## For Bracket 1

Prefer replacements that are:

- More thematic
- More flavorful
- Slower
- More expressive
- Less generically powerful
- Better at showing the deck's idea

Avoid replacements that:

- Increase speed
- Increase consistency too much
- Add efficient tutors
- Add fast mana
- Add compact combos

## For Bracket 2

Prefer replacements that are:

- Synergistic but fair
- Visible on board
- Disruptable
- Incremental
- Fun to play with and against
- Good at supporting the deck's main plan without spiking power too hard

Avoid replacements that:

- Add Game Changers
- Add early two-card combos
- Add mass land denial
- Add extra-turn loops
- Add high tutor density for the same best card
- Turn slow alternate win conditions into protected fast tutor lines

## For Bracket 3

Prefer replacements that are:

- Strongly synergistic
- Efficient but not cEDH-leaning
- Interactive
- Good at supporting the commander's plan
- Useful in multiple game states
- Capable of closing the game after setup

Avoid replacements that:

- Push Game Changers above three
- Add fast deterministic combo lines before turn six
- Add mass land denial
- Push the deck into Bracket 4 speed or consistency unless the user wants that
- Convert a value deck into a true turbo combo shell by accident

## For Bracket 4

Prefer replacements that are:

- Efficient
- Consistent
- High-impact
- Strongly aligned with the primary plan
- Able to support faster wins
- Able to protect the deck's key engine

Bracket 4 may use Game Changers freely.

Still avoid replacements that are off-plan or only generically powerful if they do not help the deck's actual strategy.

## For Bracket 5

Only suggest cEDH-level replacements when:

- The user explicitly wants cEDH
- The deck is already close to cEDH
- The replacement supports a known competitive strategy
- The replacement improves speed, consistency, resilience, or interaction

Do not casually recommend cEDH staples for lower-bracket decks.

Do not call a deck Bracket 5 unless it has competitive intent, speed, consistency, compact combos, protection, and cEDH-level construction.

---

# Handling Unknown Intended Bracket

If the user does not provide an intended bracket, the deck helper should:

1. Estimate the deck's likely bracket.
2. Explain the evidence.
3. Identify what bracket the deck would need to aim for if the user wants:
   - More casual/social play
   - Strong upgraded play
   - High-power optimized play
   - cEDH
4. Treat bracket pressure as review flags, not automatic cuts.
5. Avoid making cuts solely to lower the bracket unless the user says that is the goal.

Use:

```markdown
**Intended bracket:** Unknown  
**Estimated bracket:** Bracket X  
**General recommendation:** Based on the current list, I would tune this as a Bracket X deck unless you want to intentionally lower or raise the power level.

The intended bracket is unknown, so this is a review flag rather than an automatic cut.
```

---

# Do Not Misclassify These Situations

## A deck is not Bracket 5 just because it wins quickly in casual pods

A deck can dominate casual pods and still be Bracket 4 rather than cEDH.

Bracket 5 requires competitive intent, cEDH-level construction, speed, consistency, compact combos, protection, and metagame awareness.

## A deck is not Bracket 1 just because it is weak

Bracket 1 is theme-first Exhibition play, not simply "bad deck."

A weak pile with no theme is not automatically Bracket 1.

## A deck is not Bracket 2 just because it has no Game Changers

A deck with no Game Changers can still be Bracket 3 or 4 if it is fast, consistent, combo-heavy, or highly optimized.

## A deck is not automatically Bracket 3 because it has one Game Changer

One Game Changer creates bracket pressure, but the full deck context matters.

If the deck is otherwise casual and the card is not central, flag it as a bracket issue rather than reclassifying the whole deck with high confidence.

## A Game Changer is not automatically a cut in Bracket 3

Bracket 3 allows up to three Game Changers.

Evaluate whether the card supports the deck's plan or is just generic power.

## A fourth Game Changer does not automatically mean cEDH

Fourth-plus Game Changers usually create Bracket 4 pressure.

Bracket 5 requires competitive intent, speed, consistency, compact combos, protection, and cEDH-level construction.

## Expensive cards are not automatically high bracket

Price is not bracket.

Evaluate play pattern, speed, consistency, and table experience.

## High synergy is not the same as high power

A very synergistic deck can still be Bracket 2 if the cards are slow, visible, disruptable, and fair.

A low-synergy goodstuff deck can still create bracket pressure if it uses many Game Changers or fast high-power cards.

## A slow alternate win condition is not turbo combo

A slow alternate win condition may be powerful, table-sensitive, or bracket-pressure, but it should not be called turbo combo unless the deck can repeatedly find and protect it early and the true turbo combo gate passes.

## A high-power value card is not a combo by default

High-power value pieces can raise bracket pressure without being combo.

Treat them as value/bracket review unless the deck turns them into a fast deterministic win line.

## A single tutor does not create a tutor chain

A tutor chain requires repeated ability to find the same win condition or line.

A deck with one efficient tutor may create bracket pressure, especially in Bracket 2, but it is not automatically a fast tutor chain.

## Politics risk is not power level by itself

Group Hug may be low bracket but high kingmaker risk.

Pillowfort may stall games without being high power.

Forced combat may be table-dependent without being optimized.

Villain decks may have reputation pressure even if they are not powerful.

## Rule Zero review is not bracket level by itself

A card can require table permission while being normal-power or low-power.

Do not treat nonstandard legality as Bracket 4 or Bracket 5 by itself.

---

# Source Notes for Future Updates

The Commander Bracket system is still subject to updates.

When updating this file, verify:

- Current Commander banned list
- Current Game Changers list
- Current bracket descriptions
- Any changes to hybrid mana or color identity rules
- Any new bracket terminology
- Any newly added or removed Game Changers
- Any change to Lutri's banned-as-companion status
- Any change to how preconstructed decks are classified

Do not assume the Game Changers list is permanent.

---

# Final Instruction to the Agent

When bracket rules conflict with generic optimization, the user's intended play experience wins.

A perfect card for Bracket 4 may be the wrong recommendation for Bracket 2.

A card should not be cut simply because it is powerful; it should be reviewed because it changes the deck's bracket, play pattern, consistency, speed, or table expectations.

Always separate:

- "This card is bad"
- "This card is powerful but wrong for the intended bracket"
- "This card is powerful and correct if the user accepts a higher bracket"
- "This card is core to the deck but creates bracket pressure"
- "This card belongs in manual review"
- "This card is a Game Changer"
- "This card is bracket pressure"
- "This card is high-power value, not combo"
- "This card is a slow alternate win condition, not turbo combo"
- "This card is a political/table-experience warning"
- "This card requires Rule Zero or legality review"
- "This card is part of a true turbo combo shell"

The most important v0.5.6 hotfix correction is:

> Bracket pressure is a report modifier, not a strategy label and not an automatic cut.
