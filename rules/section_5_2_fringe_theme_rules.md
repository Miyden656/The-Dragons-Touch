# Section 5.2: Fringe Theme Rules
Version: v0.5.6-ready
Purpose: Help the MTG Commander Deck Helper identify buildable but fragile, low-support, meta-dependent, Rule Zero-sensitive, or user-intent-dependent themes.

A fringe theme is playable, but the deck helper should usually treat it as:
- Manual review
- Intentional user theme
- Minor package
- Meta-dependent package
- Rule Zero / legality-sensitive package
- Flavor-first package

A fringe theme should rarely become a primary strategy unless the user explicitly declared the theme or the commander and decklist provide overwhelming support.

Most important rule:

```text
A fringe card is not automatically a cut.
But a fringe card without user intent, payoff support, commander support, or table context should be reviewed before it is protected.
```

---

# 5.2.1 Core Fringe Theme Philosophy

Fringe themes differ from niche themes.

A niche theme is narrow but recognized and supported enough to function as a normal intentional Commander theme.

A fringe theme is buildable but usually has one or more problems:

- Low card density
- Weak payoff density
- Heavy reliance on one commander
- Rule Zero or legality complications
- Meta dependence
- High table-salt risk
- Inconsistent execution
- More flavor than function
- A mechanic that was never deeply supported
- A theme that works only if the user intentionally wants it
- A package that needs specific pieces together
- A theme that creates self-synergy conflicts

The helper should not treat fringe as bad.

The helper should treat fringe as requiring more caution.

Correct framing:

```text
This looks like a fringe package rather than a core plan. I would not automatically cut it if this is intentional, but it needs manual review because the deck does not currently show enough support to make it reliable.
```

---

# 5.2.2 Fringe Theme Output Fields

For each detected fringe theme, record:

```yaml
fringe_theme:
  name:
  role: primary | secondary | minor_package | support_package | manual_review | intentional_user_theme
  confidence: low | medium | high
  user_declared_theme: true | false
  commander_support: none | light | moderate | strong
  theme_count:
  payoff_count:
  enabler_count:
  package_dependency:
  missing_package_piece:
  legality_sensitive: true | false
  rule_zero_required: true | false
  outside_game_component: true | false
  social_contract_pressure: none | low | medium | high
  meta_dependency: none | low | medium | high
  self_synergy_conflict: true | false
  flavor_first_likelihood: none | low | medium | high
  protected_if_intentional:
  higher_cut_pressure_cards:
  replacement_constraints:
  report_notes:
```

---

# 5.2.3 Default Fringe Classification

Most fringe themes should default to manual review unless user intent is clear.

```python
def fringe_theme_review_status(theme_detected, user_declared_theme):
    if not theme_detected:
        return "not_present"
    if user_declared_theme:
        return "intentional_theme_review"
    return "manual_review_minor_package"
```

The helper should not automatically promote a fringe theme to primary from detected cards alone.

---

# 5.2.4 Fringe Primary Gate

Fringe themes need stronger proof than normal niche themes.

```python
def can_be_primary_fringe_theme(
    theme_count,
    payoff_count,
    commander_support,
    user_declared_theme
):
    return (
        user_declared_theme
        and commander_support
        and theme_count >= 5
        and payoff_count >= 2
    ) or (
        user_declared_theme
        and theme_count >= 8
        and payoff_count >= 2
    )
```

If this gate fails, classify as:
- Manual review
- Intentional user theme review
- Minor package
- Meta-dependent package
- Rule Zero package
- Flavor-first package

---

# 5.2.5 Fringe Secondary / Minor Package Gate

Use this for fringe themes that appear meaningfully but should not define the deck.

```python
def can_be_secondary_fringe_package(
    theme_count,
    payoff_count,
    commander_support,
    user_declared_theme
):
    return (
        user_declared_theme
        and theme_count >= 3
        and payoff_count >= 1
    ) or (
        commander_support
        and theme_count >= 4
        and payoff_count >= 1
    )
```

If this gate fails, mark as:
- Isolated fringe card
- Manual review
- Possible cut if optimization is the goal

---

# 5.2.6 User Intent Priority Rule

Fringe themes are highly user-intent dependent.

If the user explicitly says the deck is built around a fringe theme, the helper should:
- Preserve the theme during cut review.
- Avoid over-optimizing it away.
- Recommend improvements within the theme first.
- Separate “power optimization” from “theme preservation.”
- Ask for bracket/power intent only if needed and not already known.

If user intent is unknown, the helper should:
- Flag the theme for manual review.
- Avoid calling cards bad.
- Avoid aggressively protecting them.
- Avoid aggressively cutting them.
- Explain what support the package would need.

---

# 5.2.7 Rule Zero / Legality-Sensitive Gate

Some fringe themes require legality or table-permission review.

Use for:
- Attractions
- Stickers
- Contraptions
- Silver-border cards
- Acorn cards
- Outside-game components
- Nonstandard legality themes
- Rule Zero commanders/cards

```python
def requires_rule_zero_or_legality_review(tags):
    return bool(tags & {
        "acorn_card",
        "silver_border",
        "contraptions",
        "rule_zero_only",
        "outside_game_component",
        "nonstandard_legality",
        "attractions",
        "stickers",
        "sticker_sheet",
        "attraction_deck"
    })
```

Report behavior:

```markdown
This package may require Rule Zero or legality review. Do not assume these cards are legal or accepted at every Commander table.
```

Cut logic:
- Do not cut if the user’s table allows it and theme is intentional.
- Increase cut pressure if legality/table permission is unknown and the user wants normal Commander legality.
- Always separate legality concern from power concern.

---

# 5.2.8 Social Contract Pressure Gate

Some fringe themes are legal but socially sensitive.

Use for:
- Mass Land Denial
- Nonbasic Land Hate
- Hard Locks
- Graveyard Locks
- Artifact Locks
- ETB Locks
- Repeated Extra Turns
- Opponent Discard Locks
- Extreme Stax
- Grief Theft
- Salt-heavy strategies

```python
def has_social_contract_pressure(tags):
    return bool(tags & {
        "mass_land_denial",
        "extreme_stax",
        "hard_lock",
        "repeated_extra_turns",
        "opponent_discard_lock",
        "grief_theft",
        "nonbasic_land_hate",
        "graveyard_lock",
        "artifact_lock",
        "etb_lock"
    })
```

Report behavior:

```markdown
This package may create table-expectation pressure. It is not automatically wrong, but it should be discussed if the deck is intended for casual or lower-bracket pods.
```

---

# 5.2.9 Self-Synergy Conflict Check

Some fringe packages shut off the deck’s own plan.

Use this check:

```python
def has_self_synergy_conflict(tags):
    conflict_pairs = [
        ("graveyard_lock", "reanimator"),
        ("graveyard_lock", "flashback"),
        ("graveyard_lock", "escape"),
        ("graveyard_lock", "muldrotha_recursion"),
        ("artifact_lock", "artifact_ramp"),
        ("artifact_lock", "treasure_tokens"),
        ("artifact_lock", "clue_tokens"),
        ("artifact_lock", "food_tokens"),
        ("artifact_lock", "equipment"),
        ("etb_lock", "etb_value"),
        ("etb_lock", "blink"),
        ("torpor_orb_effect", "blink"),
        ("torpor_orb_effect", "etb_value"),
        ("rule_of_law", "storm"),
        ("rule_of_law", "spellslinger_chain"),
        ("colorless_restriction", "colored_pip_requirement"),
        ("nonbasic_land_hate", "nonbasic_heavy_mana_base")
    ]

    return any(a in tags and b in tags for a, b in conflict_pairs)
```

If conflict exists:
- Do not automatically cut.
- Flag as manual review.
- Explain both sides of the conflict.
- Ask whether the hate piece is meta tech or accidental only if the user has not already supplied intent.

---

# 5.2.10 Fringe Suppression Rules

## Suppress Fringe Theme to Manual Review If

Suppress fringe theme scoring if:
- Theme has fewer than 3 cards and no commander support.
- User did not declare the theme.
- Payoff count is zero.
- Package requires another card that is missing.
- The mechanic creates legality or table-permission issues.
- The package conflicts with the primary strategy.
- The card is meta-dependent but no meta was provided.
- The theme is flavor-first and optimization intent is unclear.

## Suppress Behind Major or Niche Theme

Many fringe themes are better understood as packages inside broader strategies.

Examples:
- Clash → Topdeck Matters package
- Renown → Counter/Combat package
- Bloodthirst → Chip Damage / Counter package
- Level Up → Mana Sink / Counter package
- Classes → Enchantment support
- Caves → Land-subtype package
- Locus → Big Mana land package
- Damage Reflection → Aikido package
- Fog Tribal → Pillowfort/Turbo-Fog package
- Case Enchantments → Enchantment package
- Rooms → Enchantment/Eerie package
- Meld → Specific package dependency
- Odd/Even MV → Companion/restriction package
- Color Hate → Meta-dependent hate package

---

# 5.2.11 Global Fringe Cut Rules

## Do Not Automatically Cut Fringe Cards When

Do not automatically cut fringe cards when:
- The user explicitly declared the theme.
- The commander clearly supports the theme.
- The card is one of the few available payoff pieces.
- The card is part of a required package, such as meld pairs or donate/bad-gift pairs.
- The deck is flavor-first.
- The card is meta tech for the user’s known playgroup.
- The card is legally unusual but the user’s table allows it.
- The theme is intentionally low-power or casual.
- The card preserves a deckbuilding restriction, such as companion or odd/even mana value.
- The card is necessary to make a narrow commander function.

## Apply Higher Cut Pressure When

Apply higher cut pressure when:
- The fringe card appears without payoff support.
- The card creates legality or Rule Zero issues the user did not ask for.
- The card conflicts with the deck’s own main plan.
- The theme is only represented by one or two isolated cards.
- The card is meta-dependent but the user gave no meta reason.
- The card creates table-salt pressure without helping the deck win.
- The card requires another specific card that is missing.
- The card is only funny once but weak repeatedly.
- The card makes replacements harder without sufficient payoff.
- The card consumes resources that the primary plan needs.

---

# 5.2.12 Global Fringe Replacement Logic

Replacement suggestions must respect user intent and restrictions.

```yaml
fringe_replacement_categories:
  general_fringe:
    - More theme enablers
    - More theme payoffs
    - More commander synergy
    - More consistency tools
    - More protection
    - More card draw
    - More reliable win conditions

  rule_zero_sensitive:
    - Commander-legal alternatives
    - Black-border alternatives
    - Non-acorn alternatives
    - Table-friendly alternatives
    - Theme-preserving replacements

  social_contract_pressure:
    - Lower-salt alternatives
    - Less oppressive interaction
    - More win conditions
    - More parity-breaking support
    - Pregame discussion note

  meta_dependent_hate:
    - More flexible interaction
    - More broadly useful removal
    - More card draw
    - More role-flexible hate pieces
    - Sideboard-like review note

  self_synergy_conflict:
    - Asymmetrical alternatives
    - Less self-punishing versions
    - Replacement that preserves primary plan
    - More parity-breaking support

  package_dependency:
    - Missing package half
    - More tutors
    - More redundancy
    - More recursion
    - More protection

  flavor_first:
    - More flavorful support
    - More mechanically useful in-theme cards
    - More gentle upgrades
    - Avoid over-optimization
```

---

# 5.2.13 Attractions

## Definition

Attraction decks open Attractions from a separate Attraction deck and visit them for repeatable value.

## Detection Signals

Increase Attraction score for:
- Attraction cards
- Attraction deck requirement
- Visit Attractions effects
- Ticket/Attraction support
- Artifact/enchantment support if relevant
- Commander supports Attractions
- Outside-game component

## Primary Gate

```python
def can_be_primary_attractions(
    attraction_card_count,
    attraction_payoff_count,
    commander_support,
    user_declared_theme
):
    return (
        user_declared_theme
        and commander_support
        and attraction_card_count >= 5
        and attraction_payoff_count >= 2
    )
```

## Special Review

Always check:
- Legality
- Acorn status
- Commander table permission
- Attraction deck availability
- Outside-game component

## Cut Logic

Protect:
- Attraction cards if user declared theme and table allows them
- Visit Attractions enablers
- Attraction payoffs
- Artifact/enchantment overlap if relevant

Review:
- Attraction cards if user wants normal Commander legality
- Acorn or silver-border cards
- Outside-game components in unknown pods
- Attraction cards without enough visit support

## Replacement Categories

- Commander-legal alternatives
- Non-acorn alternatives
- More Attraction enablers if allowed
- More artifact/enchantment support
- More reliable win conditions

## Report Behavior

Include:
- “Requires legality/table-permission review”
- “Outside-game component required”
- “Do not assume all Attraction cards are legal”
- “Protect only if user declared theme or Rule Zero allowed”

---

# 5.2.14 Stickers

## Definition

Sticker decks use sticker sheets to modify cards with name, ability, power/toughness, or art stickers.

## Detection Signals

Increase Sticker score for:
- Sticker cards
- Ticket counters
- Sticker sheets
- Name modification
- Ability stickers
- Power/toughness stickers
- Commander supports stickers

## Primary Gate

```python
def can_be_primary_stickers(
    sticker_card_count,
    sticker_payoff_count,
    commander_support,
    user_declared_theme
):
    return (
        user_declared_theme
        and commander_support
        and sticker_card_count >= 5
        and sticker_payoff_count >= 2
    )
```

## Special Review

Always flag:
- Rule Zero review
- Legality sensitivity
- Sticker sheet requirement
- Physical component requirement
- Table comfort

## Cut Logic

Protect:
- Sticker cards only if theme declared and table allows them
- Ticket generation
- Sticker payoff cards

Review:
- Sticker cards in normal Commander legality review
- Sticker cards without ticket generation/payoff
- Cards that only function with external components

## Replacement Categories

- Commander-legal alternatives
- Non-sticker alternatives
- More ticket generation if allowed
- More theme-preserving replacements
- More reliable payoff

## Report Behavior

Include:
- “Stickers are not normal counters, Auras, or Equipment”
- “Requires physical sticker components”
- “Legality/table-permission review required”

---

# 5.2.15 Contraptions

## Definition

Contraption decks assemble Contraptions from a separate Contraption deck and use sprockets for recurring effects.

## Detection Signals

Increase Contraption score for:
- Contraption cards
- Assemble Contraption text
- Sprocket references
- Silver-border/Un-set cards
- Outside-game component
- Commander supports Contraptions

## Primary Gate

```python
def can_be_primary_contraptions(
    contraption_card_count,
    commander_support,
    user_declared_theme
):
    return (
        user_declared_theme
        and commander_support
        and contraption_card_count >= 5
    )
```

## Special Review

Contraptions should normally be:
- Rule Zero only
- Outside-game component
- Manual review
- Not normal Commander-legal unless table explicitly allows

## Cut Logic

Protect:
- Contraption cards only if user declared theme and table allows them

Review:
- All Contraption cards under normal legality
- Silver-border cards
- Unsupported assemble effects

## Replacement Categories

- Rule Zero alternatives
- Artifact theme alternatives
- Commander-legal artifact engines
- Flavor-preserving replacements

## Report Behavior

Include:
- “Rule Zero only unless table explicitly allows”
- “Outside-game component required”
- “Do not evaluate as normal artifact deck without user intent”

---

# 5.2.16 Splice / Arcane

## Definition

Arcane decks use spells with the Arcane subtype and Splice onto Arcane to reuse spell text.

## Detection Signals

Increase Splice/Arcane score for:
- Arcane spell count
- Splice cards
- Spirit/Arcane support
- Spell copy
- Spell recursion
- Commander rewards spells
- Repeatable Arcane engines

## Primary Gate

```python
def can_be_primary_splice_arcane(
    arcane_count,
    splice_count,
    payoff_count,
    commander_support,
    user_declared_theme
):
    return (
        user_declared_theme
        and arcane_count >= 8
        and splice_count >= 3
        and payoff_count >= 2
    ) or (
        commander_support
        and arcane_count >= 10
        and splice_count >= 4
        and payoff_count >= 2
    )
```

## Cut Logic

Protect:
- Arcane density cards
- Splice cards
- Spell recursion
- Spirit/Arcane bridge cards
- Spell-copy support

Review:
- Splice cards with too few Arcane spells
- Arcane spells that are weak without payoff
- Spirit cards that do not support Arcane or commander
- Generic spellslinger cards if they dilute Arcane density

## Replacement Categories

- More Arcane density
- More splice payoff
- More spell recursion
- More spell copy
- More card draw
- More Spirit/Arcane bridge cards

## Report Behavior

Include:
- “Manual review unless user declared theme”
- “Arcane density”
- “Splice count”
- “Whether this is better understood as spellslinger support”

---

# 5.2.17 Clash

## Definition

Clash reveals the top card of clashing players’ libraries, compares mana values, and rewards the winner.

## Detection Signals

Increase Clash score for:
- Clash cards
- Topdeck manipulation
- High-MV reveal support
- Randomness engine
- Topdeck-damage overlap
- Commander rewards topdeck

## Primary Gate

```python
def can_be_primary_clash(
    clash_count,
    topdeck_manipulation_count,
    payoff_count,
    user_declared_theme
):
    return (
        user_declared_theme
        and clash_count >= 5
        and topdeck_manipulation_count >= 5
        and payoff_count >= 1
    )
```

## Suppression Rule

Usually classify as:
- Topdeck Matters package
- Randomness package
- Manual review

Not primary Clash unless user declared it.

## Cut Logic

Protect:
- Clash cards only if intentional
- Topdeck manipulation
- High-MV reveal support

Review:
- Clash cards without topdeck manipulation
- Low-impact clash cards
- Randomness cards with no payoff
- High-MV cards if no reveal payoff exists

## Replacement Categories

- More topdeck manipulation
- More topdeck payoff
- More reliable value cards
- More card draw
- More theme-preserving upgrades

## Report Behavior

Include:
- “Usually topdeck package, not primary”
- “Clash support count”
- “High-variance warning”

---

# 5.2.18 Fateseal / Opponent Topdeck Control

## Definition

Fateseal and opponent-topdeck-control manipulate what opponents draw and may combine with mill, theft, Lantern-style control, or denial.

## Detection Signals

Increase score for:
- Fateseal
- Opponent topdeck manipulation
- Lantern control effects
- Draw denial
- Mill support
- Exile/topdeck theft
- Control locks

## Primary Gate

```python
def can_be_primary_fateseal(
    opponent_topdeck_control_count,
    payoff_count,
    user_declared_theme
):
    return (
        user_declared_theme
        and opponent_topdeck_control_count >= 6
        and payoff_count >= 2
    )
```

## Suppression Rule

Usually classify as:
- Control package
- Lantern-style package
- Mill/theft support
- Manual review

## Cut Logic

Protect:
- Opponent topdeck control only if intentional
- Mill/theft payoffs
- Lock support if table accepts it

Review:
- Fateseal effects with no lock/payoff
- Slow denial pieces
- Salt-heavy cards with no finisher
- Cards that create frustrating play without advancing win

## Replacement Categories

- More control finishers
- More mill payoff
- More theft payoff
- More card draw
- Less oppressive alternatives

## Report Behavior

Include:
- “Frustration/salt risk”
- “Usually control package”
- “Does the deck actually win after controlling draws?”

---

# 5.2.19 Adamant

## Definition

Adamant rewards spending at least three mana of one color to cast a spell.

## Detection Signals

Increase Adamant score for:
- Adamant cards
- Mono-color mana base
- Heavy-color pip requirements
- Devotion support
- Color-heavy payoff
- Commander rewards mono-color or devotion

## Primary Gate

```python
def can_be_primary_adamant(
    adamant_count,
    payoff_count,
    user_declared_theme
):
    return (
        user_declared_theme
        and adamant_count >= 6
        and payoff_count >= 2
    )
```

## Suppression Rule

Usually classify as:
- Mono-color support
- Devotion-adjacent
- Minor package

## Cut Logic

Protect:
- Adamant cards if mono-color or heavy-color deck supports them
- Devotion overlap
- Color-heavy mana support

Review:
- Adamant cards in multicolor decks with weak color consistency
- Adamant cards with low payoff
- Cards that do not support primary plan beyond Adamant

## Replacement Categories

- More mono-color payoff
- More devotion support
- Better color consistency
- More broadly useful cards
- More commander synergy

## Report Behavior

Include:
- “Adamant is usually support, not primary”
- “Can the mana base reliably enable Adamant?”
- “Devotion overlap”

---

# 5.2.20 Renown

## Definition

Renown gives a creature +1/+1 counters after it deals combat damage to a player for the first time.

## Detection Signals

Increase Renown score for:
- Renown cards
- Evasion
- Combat damage triggers
- Counter support
- Modified support
- Proliferate
- Commander rewards counters/combat damage

## Primary Gate

```python
def can_be_primary_renown(
    renown_count,
    evasion_count,
    counter_payoff_count,
    user_declared_theme
):
    return (
        user_declared_theme
        and renown_count >= 6
        and evasion_count >= 5
        and counter_payoff_count >= 2
    )
```

## Suppression Rule

Usually classify as:
- Counter support
- Combat damage package
- Modified support
- Manual review

## Cut Logic

Protect:
- Renown cards only if theme declared or counter/combat plan supports them
- Evasion
- Counter payoffs

Review:
- Renown creatures without evasion
- Renown cards with no counter payoff
- One-shot growth effects in slow Commander pods
- Combat cards that do not scale

## Replacement Categories

- More evasion
- More counter payoff
- More combat damage payoff
- More protection
- More efficient creatures

## Report Behavior

Include:
- “Renown is slow and one-shot”
- “Evasion needed”
- “Usually counter/combat support”

---

# 5.2.21 Bloodthirst

## Definition

Bloodthirst creatures enter with +1/+1 counters if an opponent was dealt damage that turn.

## Detection Signals

Increase Bloodthirst score for:
- Bloodthirst cards
- Chip damage enablers
- Pingers
- Opponent life-loss triggers
- Counter payoff
- Aggressive sequencing
- Commander rewards life loss or counters

## Primary Gate

```python
def can_be_primary_bloodthirst(
    bloodthirst_count,
    chip_damage_enabler_count,
    counter_payoff_count,
    user_declared_theme
):
    return (
        user_declared_theme
        and bloodthirst_count >= 6
        and chip_damage_enabler_count >= 5
        and counter_payoff_count >= 2
    )
```

## Suppression Rule

Usually classify as:
- Chip damage support
- Counter package
- Combat package
- Minor package

## Cut Logic

Protect:
- Bloodthirst cards if theme declared
- Repeatable chip damage enablers
- Counter payoffs

Review:
- Bloodthirst creatures without damage enablers
- Counter cards without payoff
- Aggressive cards that do not scale in multiplayer
- Cards that require awkward sequencing

## Replacement Categories

- More chip damage enablers
- More counter payoff
- More aggressive pressure
- More card draw
- More protection

## Report Behavior

Include:
- “Bloodthirst needs reliable precombat damage”
- “Usually support package, not primary”
- “Counter overlap”

---

# 5.2.22 Hellbent

## Definition

Hellbent rewards having no cards in hand.

## Detection Signals

Increase Hellbent score for:
- Hellbent cards
- Low hand size rewards
- Discard outlets
- Madness support
- Graveyard compensation
- Commander-based card advantage
- Topdeck/exile-cast engines
- Fast hand-emptying curve

## Primary Gate

```python
def can_be_primary_hellbent(
    hellbent_count,
    hand_emptying_count,
    compensation_engine_count,
    commander_support,
    user_declared_theme
):
    return (
        user_declared_theme
        and hellbent_count >= 5
        and hand_emptying_count >= 5
        and compensation_engine_count >= 3
    ) or (
        commander_support
        and hellbent_count >= 5
        and compensation_engine_count >= 3
    )
```

## Special Rule

Do not automatically recommend more hand-filling draw if the deck intentionally wants low hand size.

Instead evaluate:
- Graveyard recursion
- Commander draw
- Exile-cast value
- Madness
- Topdeck engines

## Cut Logic

Protect:
- Hellbent payoff
- Discard outlets
- Graveyard compensation
- Commander-based advantage
- Low-curve hand-emptying cards

Review:
- Hellbent cards with no compensation engine
- Draw-heavy cards that conflict with Hellbent if theme intentional
- Discard outlets with no payoff
- Cards that leave deck empty-handed with no recovery

## Replacement Categories

- More graveyard compensation
- More madness/discard payoff
- More exile-cast value
- More low-cost spells
- More commander synergy
- More protection

## Report Behavior

Include:
- “Low hand size appears intentional or accidental?”
- “Compensation engine count”
- “Do not blindly add draw if Hellbent is intentional”

---

# 5.2.23 Level Up

## Definition

Level Up creatures gain level counters through mana investment and eventually unlock stronger abilities.

## Detection Signals

Increase Level Up score for:
- Level Up creatures
- Level counter support
- Counter manipulation
- Proliferate
- Training Grounds-style cost reduction
- Mana sink support
- Commander rewards counters

## Primary Gate

```python
def can_be_primary_level_up(
    level_up_count,
    counter_support_count,
    mana_sink_support_count,
    user_declared_theme
):
    return (
        user_declared_theme
        and level_up_count >= 6
        and (counter_support_count + mana_sink_support_count) >= 4
    )
```

## Suppression Rule

Usually classify as:
- Mana sink package
- Counter package
- Slow value package

## Cut Logic

Protect:
- Level Up creatures if theme intentional
- Counter manipulation
- Proliferate
- Cost reduction
- Mana sink support

Review:
- Slow Level Up creatures without support
- Mana sinks in mana-poor decks
- Counter support with too few level counters
- Level Up cards that do not impact board soon enough

## Replacement Categories

- More counter manipulation
- More cost reduction
- More ramp
- More proliferate
- More protection
- More efficient mana sinks

## Report Behavior

Include:
- “Level Up is mana-intensive”
- “Counter manipulation support”
- “Usually not primary unless user-declared”

---

# 5.2.24 Classes as Primary Theme

## Definition

Class enchantments level up over time and provide staged effects. They usually support enchantment decks rather than define a primary archetype.

## Detection Signals

Increase Class score for:
- Class enchantments
- Enchantress support
- Mana sink support
- Level-up enchantment payoffs
- Staged value
- Commander rewards enchantments

## Primary Gate

```python
def can_be_primary_classes(
    class_count,
    enchantment_payoff_count,
    user_declared_theme
):
    return (
        user_declared_theme
        and class_count >= 7
        and enchantment_payoff_count >= 3
    )
```

## Suppression Rule

Usually classify as:
- Enchantment support
- Enchantress package
- Mana sink package
- Staged value package

## Cut Logic

Protect:
- Classes if user declared Class theme
- Strong enchantment support
- Mana sink support
- Class cards that support primary strategy

Review:
- Classes that do not support the deck’s plan
- Too many mana-hungry Classes
- Enchantment payoffs with low enchantment density
- Class theme without user intent

## Replacement Categories

- More enchantment payoff
- More mana sinks
- More card draw
- More theme-relevant Classes
- More protection

## Report Behavior

Include:
- “Class tribal is fringe”
- “Usually enchantment support”
- “Mana investment concern”

---

# 5.2.25 Caves

## Definition

Cave decks use Cave lands and cards that reward Caves entering or being controlled.

## Detection Signals

Increase Cave score for:
- Cave land count
- Cave payoff
- Land recursion
- Land tutors
- Descend support
- Landfall support
- Commander supports Caves or land value

## Primary Gate

```python
def can_be_primary_caves(
    cave_count,
    cave_payoff_count,
    land_support_count,
    commander_support,
    user_declared_theme
):
    return (
        user_declared_theme
        and cave_count >= 8
        and cave_payoff_count >= 2
    ) or (
        commander_support
        and cave_count >= 8
        and cave_payoff_count >= 2
        and land_support_count >= 2
    )
```

## Suppression Rule

Usually classify as:
- Land-subtype package
- Descend/lands support
- Manual review

## Cut Logic

Protect:
- Caves if user declared theme
- Cave payoffs
- Land tutors/recursion
- Descend support if linked

Review:
- Caves with no payoff
- Cave payoffs with low Cave count
- Tapped lands that weaken mana without payoff
- Landfall/descend cards if support is low

## Replacement Categories

- More Caves
- More Cave payoff
- More land tutors
- More land recursion
- Better fixing that preserves Cave density
- More broadly useful lands if unsupported

## Report Behavior

Include:
- “Cave count”
- “Usually land-subtype package”
- “Do not make primary without strong support”

---

# 5.2.26 Locus

## Definition

Locus decks use Locus lands to generate large amounts of mana, relying heavily on tutors, copying, and recursion.

## Detection Signals

Increase Locus score for:
- Locus lands
- Land tutors
- Land copying
- Land recursion
- Big mana payoffs
- Mana sinks
- Commander supports lands/big mana

## Primary Gate

```python
def can_be_primary_locus(
    locus_count,
    land_tutor_or_copy_count,
    big_mana_payoff_count,
    user_declared_theme
):
    return (
        user_declared_theme
        and locus_count >= 2
        and land_tutor_or_copy_count >= 4
        and big_mana_payoff_count >= 3
    )
```

## Suppression Rule

Usually classify as:
- Land package
- Big mana package
- Utility land package

## Cut Logic

Protect:
- Locus lands
- Land tutors
- Land copy effects
- Land recursion
- Big mana payoffs

Review:
- Locus package with no tutors/copy effects
- Big mana payoffs without mana production
- Utility lands that hurt color consistency
- Locus cards if not user-declared and unsupported

## Replacement Categories

- More land tutors
- More land copy
- More land recursion
- More mana sinks
- More big mana payoff
- More color fixing

## Report Behavior

Include:
- “Locus is a package, not usually primary”
- “Land tutor/copy dependency”
- “Big mana payoff count”

---

# 5.2.27 Color Hate

## Definition

Color Hate decks use protection, removal, or lockout effects targeting specific colors.

## Detection Signals

Increase Color Hate score for:
- Protection from color
- Color-specific removal
- Color-specific damage prevention
- Color lockout effects
- Sword-style color protection
- Meta call cards

## Primary Gate

```python
def can_be_primary_color_hate(
    color_hate_count,
    payoff_count,
    user_declared_theme,
    known_meta_reason
):
    return (
        user_declared_theme
        and known_meta_reason
        and color_hate_count >= 6
        and payoff_count >= 2
    )
```

## Classification Rule

Usually classify as:
- Meta-dependent manual review
- Sideboard-like card
- Protection package
- Voltron support if Equipment-based

## Cut Logic

Protect:
- Color hate if known meta reason exists
- Protection pieces in Voltron if broadly useful
- Color-specific cards that are also strong removal

Review:
- Color hate with no known meta
- Narrow color-specific cards
- Hate that does nothing against many pods
- Cards that create negative experience without improving win rate

## Replacement Categories

- More flexible removal
- Broader protection
- More universally useful interaction
- More meta-appropriate hate
- More card draw

## Report Behavior

Include:
- “Meta-dependent”
- “Sideboard-like card”
- “Should not be default core unless playgroup supports it”

---

# 5.2.28 Life Total Exchange

## Definition

Life Total Exchange decks manipulate life totals directly, often paying life aggressively and then exchanging or reversing life totals.

## Detection Signals

Increase score for:
- Life total exchange
- Life payment
- Self-damage
- Lifedrain payoff
- Aetherflux-style payoff
- Commander supports life manipulation
- Life gain/loss control

## Primary Gate

```python
def can_be_primary_life_exchange(
    life_exchange_count,
    life_payment_count,
    payoff_count,
    commander_support,
    user_declared_theme
):
    return (
        user_declared_theme
        and life_exchange_count >= 2
        and life_payment_count >= 4
        and payoff_count >= 2
    ) or (
        commander_support
        and life_exchange_count >= 2
        and payoff_count >= 3
    )
```

## Cut Logic

Protect:
- Life exchange cards
- Life payment enablers if exchange/payoff exists
- Lifedrain payoffs
- Life recovery
- Protection from dying before exchange

Review:
- Self-damage without exchange/payoff
- Life exchange cards with no setup
- Lifegain/lifepay cards that conflict
- High-risk cards in aggressive metas

## Replacement Categories

- More life exchange payoff
- More life payment enablers
- More lifedrain
- More protection
- More life recovery
- More tutors

## Report Behavior

Include:
- “Life payment is enabler only if exchange/payoff exists”
- “High-risk sequencing”
- “Protection needed before reversal”

---

# 5.2.29 Damage Reflection / Stuffy Doll Effects

## Definition

Damage Reflection decks redirect, reflect, or convert damage dealt to creatures or the pilot into damage against opponents.

## Detection Signals

Increase Damage Reflection score for:
- Damage reflection
- Stuffy Doll effects
- Brash Taunter effects
- Self-damage enablers
- Indestructible creatures
- Damage-based wipes
- Damage doublers
- Aikido package

## Primary Gate

```python
def can_be_primary_damage_reflection(
    reflection_count,
    self_damage_enabler_count,
    payoff_count,
    user_declared_theme
):
    return (
        user_declared_theme
        and reflection_count >= 4
        and self_damage_enabler_count >= 3
        and payoff_count >= 2
    )
```

## Cut Logic

Protect:
- Reflection pieces
- Indestructible bodies
- Self-damage enablers
- Damage doublers
- Damage-based board wipes that combo with reflectors

Review:
- Reflection pieces with no damage enablers
- Self-damage without safe reflectors
- Reactive cards if opponents can ignore them
- Expensive pieces that do nothing alone

## Replacement Categories

- More reflection pieces
- More self-damage enablers
- More indestructible bodies
- More damage doublers
- More tutors
- More protection

## Report Behavior

Include:
- “Requires pieces together”
- “Can the deck force damage through?”
- “What happens if opponents ignore reflectors?”

---

# 5.2.30 Fog Tribal

## Definition

Fog Tribal decks run many combat damage prevention effects and win through alternate win conditions, planeswalkers, mill, pillowfort, or inevitability.

## Detection Signals

Increase Fog Tribal score for:
- Fog effects
- Combat damage prevention
- Fog recursion
- Pillowfort support
- Planeswalkers
- Alternate win conditions
- Mill/control finish
- Commander supports fogs

## Primary Gate

```python
def can_be_primary_fog_tribal(
    fog_count,
    inevitability_count,
    commander_support,
    user_declared_theme
):
    return (
        user_declared_theme
        and fog_count >= 8
        and inevitability_count >= 2
    ) or (
        commander_support
        and fog_count >= 6
        and inevitability_count >= 2
    )
```

## Cut Logic

Protect:
- Fogs if inevitability exists
- Fog recursion
- Pillowfort
- Alternate win conditions
- Planeswalkers/mill finishers

Review:
- Fogs with no win condition
- Excess fogs in noncombat metas
- Combat prevention that does not stop combo
- Defensive cards that stall without closing

## Replacement Categories

- More inevitability
- More alternate win support
- More planeswalker/control payoff
- More card draw
- More noncombat interaction

## Report Behavior

Include:
- “Fog prevents losing but does not win”
- “Inevitability check”
- “Noncombat weakness”
- “Stall risk”

---

# 5.2.31 Extra Upkeeps

## Definition

Extra-upkeep decks create or exploit additional upkeep steps to multiply upkeep triggers.

## Detection Signals

Increase Extra Upkeep score for:
- Extra upkeep effects
- Upkeep triggers
- Court support
- Curse upkeep triggers
- Suspend/time counter support
- Commander creates extra upkeep
- Trigger doubling/copying

## Primary Gate

```python
def can_be_primary_extra_upkeeps(
    extra_upkeep_count,
    meaningful_upkeep_trigger_count,
    payoff_count,
    commander_support,
    user_declared_theme
):
    return (
        user_declared_theme
        and extra_upkeep_count >= 3
        and meaningful_upkeep_trigger_count >= 6
        and payoff_count >= 2
    ) or (
        commander_support
        and extra_upkeep_count >= 2
        and meaningful_upkeep_trigger_count >= 6
    )
```

## Cut Logic

Protect:
- Extra upkeep enablers
- Strong upkeep triggers
- Courts/Curses if upkeep matters
- Time-counter support if linked
- Trigger payoff

Review:
- Extra upkeep effects with too few upkeep triggers
- Upkeep triggers that are too low impact
- Cards that only delay without payoff
- Packages that do nothing until multiple pieces assemble

## Replacement Categories

- More upkeep triggers
- More extra upkeep effects
- More protection
- More card draw
- More finishers
- More trigger payoff

## Report Behavior

Include:
- “Extra upkeeps are empty without upkeep triggers”
- “Meaningful upkeep trigger count”
- “Package dependency”

---

# 5.2.32 End the Turn

## Definition

End-the-turn decks use effects that immediately end the turn, exiling the stack and skipping to cleanup. They often abuse delayed sacrifice/exile triggers.

## Detection Signals

Increase End the Turn score for:
- End the turn effects
- Delayed trigger abuse
- Temporary permanents
- “At the beginning of the next end step” clauses
- “Exile/sacrifice it at end step” clauses
- Obeka synergy
- Sundial-style effects

## Primary Gate

```python
def can_be_primary_end_the_turn(
    end_the_turn_count,
    delayed_trigger_abuse_count,
    commander_support,
    user_declared_theme
):
    return (
        user_declared_theme
        and end_the_turn_count >= 3
        and delayed_trigger_abuse_count >= 5
    ) or (
        commander_support
        and end_the_turn_count >= 2
        and delayed_trigger_abuse_count >= 5
    )
```

## Cut Logic

Protect:
- End-the-turn effects
- Temporary permanent generators
- Delayed-trigger abuse cards
- Obeka/Sundial synergy pieces
- Tutors/protection for the engine

Review:
- End-the-turn cards with no delayed triggers to abuse
- Temporary permanents with no way to keep them
- Narrow interaction that does not support primary plan
- Rules-complex cards if unsupported

## Replacement Categories

- More delayed-trigger payoffs
- More end-the-turn redundancy
- More tutors
- More protection
- More card draw
- More temporary permanent generators

## Report Behavior

Include:
- “Look for delayed sacrifice/exile clauses”
- “Rules complexity”
- “End-the-turn card is narrow without abuse targets”

---

# 5.2.33 Turn / Phase Manipulation

## Definition

Turn/phase manipulation decks skip, add, or rearrange steps and phases.

## Detection Signals

Increase score for:
- Skip step effects
- Extra phase effects
- Extra main phases
- Combat step manipulation
- Phase-ending effects
- Time counter support
- Commander supports turn structure manipulation

## Primary Gate

```python
def can_be_primary_phase_manipulation(
    phase_manipulation_count,
    payoff_count,
    commander_support,
    user_declared_theme
):
    return (
        user_declared_theme
        and phase_manipulation_count >= 4
        and payoff_count >= 2
    ) or (
        commander_support
        and phase_manipulation_count >= 4
        and payoff_count >= 2
    )
```

## Cut Logic

Protect:
- Phase manipulation if commander/theme supports it
- Payoffs that exploit skipped/added phases
- Time-counter support if linked
- Rules-critical combo pieces

Review:
- Phase manipulation with no payoff
- Rules-complex cards with low impact
- Cards that skip your own important resources
- Packages that require too many pieces

## Replacement Categories

- More payoff density
- More tutors
- More card draw
- More protection
- More simpler alternatives if optimization desired

## Report Behavior

Include:
- “Manual review and rules complexity”
- “Does the deck exploit the phase change?”
- “Commander dependency”

---

# 5.2.34 Vanilla Matters

## Definition

Vanilla Matters decks reward creatures with no rules text.

## Detection Signals

Increase Vanilla Matters score for:
- Creatures with no rules text
- Vanilla payoff
- Ruxa/Jasmine-style support
- Muraganda-style payoff
- Token production with no abilities
- Overrun/mass pump

## Primary Gate

```python
def can_be_primary_vanilla_matters(
    vanilla_creature_count,
    vanilla_payoff_count,
    commander_support,
    user_declared_theme
):
    return (
        user_declared_theme
        and vanilla_creature_count >= 14
        and vanilla_payoff_count >= 2
    ) or (
        commander_support
        and vanilla_creature_count >= 12
        and vanilla_payoff_count >= 2
    )
```

## Special Rule

Do not recommend “strictly better” creatures with abilities if that breaks the theme.

## Cut Logic

Protect:
- No-rules-text creatures
- Vanilla payoff
- Mass pump
- Commander support
- Theme-preserving density pieces

Review:
- Creatures with abilities if no-ability density matters
- Vanilla creatures if no payoff/commander support
- Generic upgrades that break theme
- Weak cards if user wants power over theme

## Replacement Categories

- More no-ability creatures
- More vanilla payoff
- More mass pump
- More protection
- More card draw
- Theme-preserving upgrades

## Report Behavior

Include:
- “Intentional rejection of normal card quality”
- “Do not over-optimize away theme”
- “No-ability density”

---

# 5.2.35 No-Abilities Matters

## Definition

No-Abilities Matters decks use creatures with no abilities or remove abilities from creatures to enable payoffs.

## Detection Signals

Increase score for:
- No-ability creatures
- Ability-removal effects
- No-ability payoff
- Commander rewards no abilities
- Mass pump
- Combat support

## Primary Gate

```python
def can_be_primary_no_abilities(
    no_ability_count,
    payoff_count,
    commander_support,
    user_declared_theme
):
    return (
        user_declared_theme
        and no_ability_count >= 14
        and payoff_count >= 2
    ) or (
        commander_support
        and no_ability_count >= 12
        and payoff_count >= 2
    )
```

## Cut Logic

Protect:
- No-ability creatures
- Ability-removal support if intentional
- No-ability payoff
- Mass pump

Review:
- Ability creatures that break synergy
- No-ability cards without payoff
- Ability-removal cards if no payoff
- Generic creature upgrades that undermine plan

## Replacement Categories

- More no-ability creatures
- More no-ability payoff
- More mass pump
- More protection
- More theme-safe card draw

## Report Behavior

Include:
- “Only recognize as intentional with commander/payoff support”
- “Theme protection warning”
- “Generic upgrades may be wrong”

---

# 5.2.36 Donate Bad Gifts

## Definition

Donate decks give opponents harmful permanents, liabilities, or creatures with drawbacks.

## Detection Signals

Increase Donate/Bad Gifts score for:
- Donate effects
- Bad gifts
- Harmful permanents
- Gift payoff
- Forced attack donated creatures
- Zedruu/Blim/Jon Irenicus support
- Political control

## Primary Gate

```python
def can_be_primary_donate_bad_gifts(
    donate_count,
    bad_gift_count,
    payoff_count,
    commander_support,
    user_declared_theme
):
    return (
        user_declared_theme
        and donate_count >= 4
        and bad_gift_count >= 5
        and payoff_count >= 2
    ) or (
        commander_support
        and donate_count >= 3
        and bad_gift_count >= 5
        and payoff_count >= 2
    )
```

## Package Dependency Rule

Bad gifts need donate effects.
Donate effects need worthwhile gifts.

If one half is missing, increase cut pressure or replacement urgency.

## Cut Logic

Protect:
- Bad gifts if donate outlets exist
- Donate effects if bad gifts exist
- Gift payoff
- Pillowfort/protection
- Political support

Review:
- Bad gifts with no donate effects
- Donate effects with no gifts
- Cards that hurt the pilot more than opponents
- Cute gifts that do not advance win

## Replacement Categories

- More donate effects
- More bad gifts
- More gift payoff
- More protection
- More pillowfort
- More win conditions

## Report Behavior

Include:
- “Do not evaluate bad gifts in isolation”
- “Package dependency”
- “Is this funny, functional, or both?”

---

# 5.2.37 Curse Pillowfort

## Definition

Curse Pillowfort decks enchant opponents with Curses while making the pilot difficult to attack.

## Detection Signals

Increase score for:
- Curses
- Curse recursion
- Pillowfort
- Political enchantments
- Attack incentives
- Curse payoff
- Commander supports Curses/enchantments

## Primary Gate

```python
def can_be_primary_curse_pillowfort(
    curse_count,
    pillowfort_count,
    payoff_or_recursion_count,
    commander_support,
    user_declared_theme
):
    return (
        user_declared_theme
        and curse_count >= 6
        and pillowfort_count >= 3
        and payoff_or_recursion_count >= 2
    ) or (
        commander_support
        and curse_count >= 6
        and payoff_or_recursion_count >= 2
    )
```

## Cut Logic

Protect:
- Curses if payoff/recursion exists
- Curse recursion
- Pillowfort pieces
- Political attack incentives
- Enchantment support

Review:
- Curses with no payoff
- Curses that only annoy one player
- Pillowfort with no win condition
- Enchantment cards that do not support curse plan

## Replacement Categories

- More curse payoff
- More curse recursion
- More pillowfort
- More enchantment support
- More finishers
- More protection

## Report Behavior

Include:
- “Curse pressure can create grudges”
- “Does the deck spread pressure or bully one player?”
- “Pillowfort plus inevitability check”

---

# 5.2.38 Battle Tribal

## Definition

Battle Tribal decks run many Battles and try to flip them for value.

## Detection Signals

Increase Battle Tribal score for:
- Battle count
- Battle payoff
- Battle flip enablers
- Combat-to-battle access
- Direct damage to Battles
- Proliferate/counter manipulation if relevant
- Commander supports Battles

## Primary Gate

```python
def can_be_primary_battle_tribal(
    battle_count,
    battle_flip_enabler_count,
    battle_payoff_count,
    commander_support,
    user_declared_theme
):
    return (
        user_declared_theme
        and battle_count >= 8
        and battle_flip_enabler_count >= 5
        and battle_payoff_count >= 2
    ) or (
        commander_support
        and battle_count >= 8
        and battle_flip_enabler_count >= 5
        and battle_payoff_count >= 2
    )
```

## Cut Logic

Protect:
- Battles if flip support exists
- Battle flip enablers
- Direct damage/evasive attackers
- Battle payoff

Review:
- Battles that cannot realistically flip
- High Battle count without enablers
- Battle payoffs with too few Battles
- Low-impact Battles

## Replacement Categories

- More flip enablers
- More evasive attackers
- More direct damage
- More Battle payoff
- More removal
- More card draw

## Report Behavior

Include:
- “Can the deck flip Battles?”
- “Battle count vs flip enabler count”
- “High cut pressure if Battles stay unflipped”

---

# 5.2.39 Case Enchantments

## Definition

Cases are enchantments that unlock rewards after a condition is solved.

## Detection Signals

Increase Case score for:
- Case enchantments
- Case solving support
- Conditional payoff
- Enchantress support
- Commander supports enchantments
- Deck naturally satisfies Case conditions

## Primary Gate

```python
def can_be_primary_cases(
    case_count,
    solvable_case_count,
    enchantment_payoff_count,
    user_declared_theme
):
    return (
        user_declared_theme
        and case_count >= 6
        and solvable_case_count >= 5
        and enchantment_payoff_count >= 2
    )
```

## Case Solvability Rule

For each Case, evaluate:
- Is the solve condition realistic?
- Does the deck naturally do this?
- Does the reward matter?
- How quickly can it solve?

## Cut Logic

Protect:
- Cases the deck can reliably solve
- Enchantress support
- Cards that enable multiple Case conditions

Review:
- Unsolvable Cases
- Cases with weak rewards
- Case theme without enough enchantment payoff
- Cards that only exist to solve one weak Case

## Replacement Categories

- More solvable Cases
- More Case enablers
- More enchantress payoff
- More card draw
- More interaction
- More reliable enchantments

## Report Behavior

Include:
- “Can the deck solve each Case?”
- “Unsolvable Cases are high cut pressure”
- “Usually enchantment package, not primary”

---

# 5.2.40 Rooms as Primary Theme

## Definition

Rooms are split enchantments unlocked in stages. Room-heavy decks use them as modal enchantment value pieces.

## Detection Signals

Increase Room score for:
- Room count
- Room unlock support
- Enchantment support
- Eerie support
- Recursion
- Blink/flicker if relevant
- Commander supports Rooms or enchantments

## Primary Gate

```python
def can_be_primary_rooms(
    room_count,
    room_specific_payoff_count,
    enchantment_payoff_count,
    user_declared_theme
):
    return (
        user_declared_theme
        and room_count >= 8
        and (room_specific_payoff_count + enchantment_payoff_count) >= 3
    )
```

## Suppression Rule

Usually classify as:
- Enchantment package
- Eerie support
- Long-game value package
- Manual review

## Cut Logic

Protect:
- Rooms if enchantment/eerie support exists
- Room-specific payoffs
- Enchantment recursion
- Unlock support

Review:
- Rooms with no enchantment payoff
- Too many mana-hungry Rooms
- Room theme without user intent
- Unlock costs that slow deck too much

## Replacement Categories

- More enchantment payoff
- More eerie support
- More room synergy
- More card draw
- More interaction
- More efficient enchantments

## Report Behavior

Include:
- “Rooms are usually enchantment/eerie package”
- “Unlock mana investment”
- “Do not infer primary without user intent”

---

# 5.2.41 Companion-Influenced Builds

## Definition

Some Commander decks use companions or voluntarily follow companion-like restrictions.

## Detection Signals

Increase Companion score for:
- Companion present
- Companion restriction compliance
- Odd/even mana value restriction
- Card type restriction
- Creature size restriction
- Commander/deck built around restriction
- Replacement constraints

## Primary Gate

```python
def can_be_primary_companion_influenced(
    companion_present,
    restriction_compliance,
    payoff_count,
    user_declared_theme
):
    return (
        companion_present
        and restriction_compliance
        and (payoff_count >= 1 or user_declared_theme)
    )
```

## Replacement Constraint Rule

Never recommend replacements that break the companion restriction if the user is using the companion.

## Cut Logic

Protect:
- Cards required for restriction compliance
- Companion payoff cards
- Odd/even MV support if relevant
- Cards that maintain deck construction rule

Review:
- Cards that violate companion restriction
- Payoffs that are not worth severe restriction
- Replacement suggestions that break restriction
- Cards included only because they comply but do little

## Replacement Categories

- Restriction-compliant upgrades
- More payoff for restriction
- More consistency tools
- More card draw
- More removal within restriction
- More win conditions within restriction

## Report Behavior

Include:
- “Companion restriction detected”
- “Replacement suggestions must preserve restriction”
- “Cards that break restriction”
- “Is restriction payoff worth it?”

---

# 5.2.42 Meld Packages

## Definition

Meld decks assemble specific card pairs that combine into a larger permanent.

## Detection Signals

Increase Meld score for:
- Meld cards
- Both halves present
- Tutors for meld pieces
- Recursion
- Protection
- Commander is a meld half or supports pair
- Specific pair dependency

## Primary Gate

```python
def can_be_primary_meld(
    meld_pair_complete,
    tutor_or_recursion_count,
    payoff_count,
    user_declared_theme
):
    return (
        user_declared_theme
        and meld_pair_complete
        and tutor_or_recursion_count >= 2
        and payoff_count >= 1
    )
```

## Package Dependency Rule

Evaluate meld pairs together.

Do not judge each half in isolation without checking:
- Is the other half present?
- Can the deck tutor or recur both?
- Is the melded permanent worth the package?

## Cut Logic

Protect:
- Meld halves if pair is complete and intentional
- Tutors
- Recursion
- Protection for meld pieces

Review:
- Single meld half with no partner
- Meld package with no tutor/recursion
- Weak individual halves if meld is unreliable
- Meld cards that do not support primary plan

## Replacement Categories

- Missing meld half
- More tutors
- More recursion
- More protection
- More reliable payoff
- Theme-preserving alternatives

## Report Behavior

Include:
- “Review meld pieces together”
- “Missing half warning”
- “Package reliability”
- “Do not evaluate each half alone”

---

# 5.2.43 Odd / Even Mana Value Restrictions

## Definition

These decks care about whether cards have odd or even mana values, often due to companions or commanders.

## Detection Signals

Increase Odd/Even score for:
- Odd mana value restriction
- Even mana value restriction
- Companion constraint
- Mana value payoff
- Topdeck manipulation
- Commander rewards odd/even MV
- Replacement constraint

## Primary Gate

```python
def can_be_primary_odd_even_mv(
    restriction_density,
    payoff_count,
    commander_support,
    user_declared_theme
):
    return (
        (user_declared_theme or commander_support)
        and restriction_density >= 0.85
        and payoff_count >= 2
    )
```

## Replacement Constraint Rule

Never recommend replacements that break the chosen parity restriction.

## Cut Logic

Protect:
- Restriction-compliant role players
- Odd/even payoffs
- Topdeck manipulation if relevant
- Cards that maintain companion compliance

Review:
- Cards that violate chosen restriction
- Payoffs with too few compliant cards
- Strictly better cards that break restriction
- Weak cards included only for parity if no payoff

## Replacement Categories

- Odd/even-compliant upgrades
- More payoff for restriction
- More topdeck manipulation
- More card draw
- More removal within restriction
- More win conditions within restriction

## Report Behavior

Include:
- “Odd/even restriction detected”
- “Replacement suggestions must preserve restriction”
- “Restriction compliance rate”
- “Cards that violate restriction”

---

# 5.2.44 Rule Zero / Silver-Border / Acorn Themes

## Definition

These decks use cards or mechanics not normally legal in sanctioned Commander or require explicit table consent.

## Detection Signals

Increase Rule Zero score for:
- Rule Zero cards
- Silver-border cards
- Acorn cards
- Un-set commanders
- Nonstandard legality
- Mini-game mechanics
- Outside-game components
- User declared Rule Zero intent

## Primary Gate

```python
def can_be_primary_rule_zero(
    rule_zero_card_count,
    user_declared_theme
):
    return (
        user_declared_theme
        and rule_zero_card_count >= 1
    )
```

## Special Rule

Always flag for:
- Table permission
- Legality review
- Rule Zero discussion
- Casual-intent preservation

## Cut Logic

Protect:
- Rule Zero cards only if user/table allows them and theme is intentional
- Flavor/theme staples

Review:
- All nonstandard cards if user wants normal Commander legality
- Cards that require physical components
- Cards that create confusing table states
- Cards that do not support declared theme

## Replacement Categories

- Commander-legal alternatives
- Non-acorn alternatives
- Black-border alternatives
- Theme-preserving legal replacements
- More table-friendly cards

## Report Behavior

Include:
- “Rule Zero required”
- “Do not assume legality”
- “Ask/confirm table permission if not known”
- “Optimization may not be the goal”

---

# 5.2.45 Mass Land Denial

## Definition

Mass Land Denial decks destroy, bounce, tax, or shut down lands, then try to break parity.

## Detection Signals

Increase Mass Land Denial score for:
- Mass land destruction
- Land bounce
- Land tax/lock
- Mana denial
- Parity breakers
- Mana rocks/dorks
- Planeswalkers
- Indestructible lands
- Land recursion
- Commander supports land denial

## Primary Gate

```python
def can_be_primary_mass_land_denial(
    mass_land_denial_count,
    parity_breaker_count,
    win_condition_count,
    user_declared_theme
):
    return (
        user_declared_theme
        and mass_land_denial_count >= 3
        and parity_breaker_count >= 3
        and win_condition_count >= 2
    )
```

## Social Contract Rule

Always flag separately from normal removal.

This is a table-expectation issue, not just a power issue.

## Cut Logic

Protect:
- Mass land denial only if user declared strategy or bracket supports it
- Parity breakers
- Win conditions under denial
- Mana sources that survive denial

Review:
- MLD with no parity breaker
- MLD with no win condition
- Repeated land denial in casual/lower bracket
- Land denial that hurts pilot equally

## Replacement Categories

- Lower-salt interaction
- More parity breakers
- More win conditions
- More mana rocks/dorks
- More table-appropriate removal
- More pregame discussion note

## Report Behavior

Include:
- “Social contract pressure”
- “Does the deck break parity?”
- “Can the deck close after land denial?”
- “Not the same as normal removal”

---

# 5.2.46 Nonbasic Land Hate

## Definition

Nonbasic Land Hate punishes greedy mana bases through damage, land-type conversion, nonbasic shutdown, or land destruction.

## Detection Signals

Increase score for:
- Nonbasic land punishment
- Nonbasic shutdown
- Land-type conversion
- Mana base punisher
- Stax pressure
- Meta call cards
- Commander supports mana denial

## Primary Gate

```python
def can_be_primary_nonbasic_land_hate(
    nonbasic_hate_count,
    pressure_count,
    known_meta_reason,
    user_declared_theme
):
    return (
        user_declared_theme
        and known_meta_reason
        and nonbasic_hate_count >= 4
        and pressure_count >= 2
    )
```

## Classification Rule

Usually classify as:
- Meta-dependent hate package
- Bracket-pressure package
- Manual review

## Cut Logic

Protect:
- Nonbasic hate if meta is multicolor/nonbasic-heavy
- Pressure cards that capitalize on mana denial
- Hate that does not hurt pilot much

Review:
- Nonbasic hate with no known meta
- Hate that hurts pilot’s own mana base
- Cards dead against basic-heavy pods
- Salt-heavy hate in casual pods

## Replacement Categories

- More flexible interaction
- Less oppressive alternatives
- More pressure
- Better mana base compatibility
- More broadly useful hate

## Report Behavior

Include:
- “Meta-dependent”
- “May be oppressive or dead depending on pod”
- “Check pilot’s own nonbasic dependency”

---

# 5.2.47 Graveyard Lock

## Definition

Graveyard Lock decks use repeatable or static graveyard denial to shut down graveyard strategies.

## Detection Signals

Increase Graveyard Lock score for:
- Static graveyard hate
- Repeatable graveyard exile
- Replacement effects that exile graveyards
- Opponent graveyard denial
- Exile payoff
- Commander unaffected by graveyard lock
- Control finishers

## Primary Gate

```python
def can_be_primary_graveyard_lock(
    graveyard_lock_count,
    payoff_count,
    known_meta_reason,
    user_declared_theme
):
    return (
        user_declared_theme
        and known_meta_reason
        and graveyard_lock_count >= 4
        and payoff_count >= 2
    )
```

## Self-Conflict Check

Flag conflict if deck also uses:
- Reanimator
- Flashback
- Escape
- Delve
- Muldrotha-style recursion
- Graveyard Matters
- Self-mill

## Cut Logic

Protect:
- Graveyard lock if meta supports it
- Exile payoffs
- Lock pieces that do not hurt pilot
- Control finishers

Review:
- Graveyard lock conflicting with own recursion
- Graveyard hate with no meta reason
- Redundant lock pieces
- Hate that does not help win

## Replacement Categories

- More asymmetrical graveyard hate
- More flexible graveyard interaction
- More win conditions
- More card draw
- Less self-punishing alternatives

## Report Behavior

Include:
- “Meta-dependent”
- “Self-synergy conflict check”
- “Does lock hurt your own deck?”
- “How deck wins through the lock”

---

# 5.2.48 Artifact Lock / Null Rod Effects

## Definition

Artifact Lock decks shut down artifact activated abilities or heavily punish artifact-based mana and value engines.

## Detection Signals

Increase Artifact Lock score for:
- Null Rod effects
- Stony Silence effects
- Artifact hate
- Mana rock shutdown
- Artifact activated ability denial
- Commander/deck unaffected by artifacts
- Creature-based ramp

## Primary Gate

```python
def can_be_primary_artifact_lock(
    artifact_lock_count,
    pressure_count,
    known_meta_reason,
    user_declared_theme
):
    return (
        user_declared_theme
        and known_meta_reason
        and artifact_lock_count >= 3
        and pressure_count >= 2
    )
```

## Self-Conflict Check

Flag conflict if deck relies on:
- Artifact ramp
- Treasures
- Clues
- Food
- Blood
- Equipment
- Artifact combo
- Vehicles

## Cut Logic

Protect:
- Artifact locks if deck breaks parity and meta supports it
- Creature ramp
- Pressure pieces
- Nonartifact value engines

Review:
- Artifact locks that shut off own mana rocks/tokens
- Artifact hate with no meta reason
- Redundant lock pieces
- Locks without pressure

## Replacement Categories

- More asymmetrical artifact hate
- More creature/land ramp
- More pressure
- More flexible removal
- Less self-punishing alternatives

## Report Behavior

Include:
- “Self-synergy conflict check”
- “Does this shut off your own artifacts?”
- “Meta-dependent artifact hate”

---

# 5.2.49 ETB Lock / Torpor Orb Effects

## Definition

ETB Lock decks shut off enters-the-battlefield abilities while using strategies that do not rely on ETBs themselves.

## Detection Signals

Increase ETB Lock score for:
- Torpor Orb effects
- ETB denial
- Hushbringer-style effects
- Hatebear control
- Planeswalker/non-ETB win conditions
- Commander/deck breaks parity

## Primary Gate

```python
def can_be_primary_etb_lock(
    etb_lock_count,
    pressure_or_payoff_count,
    known_meta_reason,
    user_declared_theme
):
    return (
        user_declared_theme
        and known_meta_reason
        and etb_lock_count >= 3
        and pressure_or_payoff_count >= 2
    )
```

## Self-Conflict Check

Flag conflict if deck also uses:
- ETB value
- Blink
- Panharmonicon effects
- Creature tutors for ETB bodies
- Reanimation of ETB creatures

## Cut Logic

Protect:
- ETB lock if meta supports and deck breaks parity
- Hatebear pressure
- Non-ETB win conditions
- Planeswalkers or static-value engines

Review:
- ETB lock with high own ETB count
- ETB lock with no meta reason
- Lock pieces with no pressure
- Cards that conflict with commander

## Replacement Categories

- More asymmetrical ETB hate
- More pressure
- More non-ETB win conditions
- More flexible interaction
- Less self-punishing alternatives

## Report Behavior

Include:
- “Self-synergy conflict check”
- “Does this shut off your own ETBs?”
- “Bracket/social pressure note”

---

# 5.2.50 Tutor Hate

## Definition

Tutor Hate prevents, punishes, or steals library searches.

## Detection Signals

Increase Tutor Hate score for:
- Search hate
- Tutor punishment
- Library search restriction
- Opposition Agent-style effects
- Aven Mindcensor-style effects
- Fetchland punishment
- Hatebear package

## Primary Gate

```python
def can_be_primary_tutor_hate(
    tutor_hate_count,
    pressure_count,
    known_meta_reason,
    user_declared_theme
):
    return (
        user_declared_theme
        and known_meta_reason
        and tutor_hate_count >= 4
        and pressure_count >= 2
    )
```

## Classification Rule

Usually classify as:
- Meta-dependent hate package
- Hatebear support
- Manual review

## Cut Logic

Protect:
- Tutor hate if meta has tutors/fetches/combo
- Hatebears that pressure
- Search hate that does not harm pilot

Review:
- Tutor hate with no known meta reason
- Search hate that hurts pilot’s land tutors/fetches
- Hate pieces with no pressure
- Cards that are dead in low-tutor pods

## Replacement Categories

- More flexible interaction
- More broadly useful hate
- More pressure
- More card draw
- Less meta-dependent removal

## Report Behavior

Include:
- “Meta-dependent”
- “Strong in tutor-heavy pods, weak in tutor-light pods”
- “Check own tutor/fetch reliance”

---

# 5.2.51 Colorless Restriction / Wastes Matters

## Definition

Colorless restriction decks intentionally use colorless cards or care about Wastes/basic colorless land structure.

## Detection Signals

Increase score for:
- Colorless identity
- Wastes count
- Colorless source needs
- Eldrazi support
- Artifact engines
- Utility lands
- Colorless-only restrictions
- Commander is colorless

## Primary Gate

```python
def can_be_primary_colorless_restriction(
    commander_is_colorless,
    colorless_card_ratio,
    colorless_source_count
):
    return (
        commander_is_colorless
        and colorless_card_ratio >= 0.90
        and colorless_source_count >= 25
    )
```

## Replacement Constraint Rule

Do not judge colorless decks by normal color-pie role expectations.

Do not recommend colored replacements for colorless commanders.

## Cut Logic

Protect:
- Colorless ramp
- Wastes if needed
- Utility lands
- Colorless interaction
- Artifact card draw
- Eldrazi support

Review:
- Cards with colored pips
- Lands that do not produce needed colorless
- Colorless cards that are low impact and not role-filling
- Overly slow haymakers without ramp

## Replacement Categories

- More colorless ramp
- More Wastes/colorless sources
- More artifact draw
- More utility lands
- More Eldrazi/colorless payoff
- More colorless interaction

## Report Behavior

Include:
- “Colorless replacement constraint”
- “Do not compare to colored staples”
- “Colorless source count”
- “Wastes/utility land balance”

---

# 5.2.52 Theme / Flavor-First Decks

## Definition

Flavor-first decks prioritize story, art, set, character, plane, tribe, or personal theme over raw optimization.

## Detection Signals

Increase Flavor-First likelihood for:
- Many cards from one set/plane/IP
- Character/story cohesion
- Art/theme cohesion
- User declares flavor/theme
- Mechanically weak but flavor-matching cards
- Commander chosen for concept over optimization

## Primary Gate

```python
def can_be_primary_flavor_first(
    user_declared_theme,
    flavor_cohesion_count
):
    return (
        user_declared_theme
        and flavor_cohesion_count >= 5
    )
```

## User Intent Rule

Do not cut flavor staples aggressively unless the user asks for power tuning.

Ask or infer whether the user wants:
- Optimization
- Flavor preservation
- A balance between both

## Cut Logic

Protect:
- Flavor staples
- Story/theme-defining cards
- Cards user specifically wants
- Mechanically weak but theme-important cards

Review:
- Only if user wants optimization
- Cards that weaken play experience too much
- Cards that do not support flavor or function
- Cards that conflict with desired bracket

## Replacement Categories

- More flavorful support
- More mechanically useful in-theme cards
- Gentle upgrades
- Flavor-preserving alternatives
- Power upgrades only if requested

## Report Behavior

Include:
- “Optimization may not be the main goal”
- “Do not over-optimize away theme”
- “Separate flavor cuts from power cuts”
- “Ask/track user intent if unclear”

---

# 5.2.53 Fringe Theme Scoring Model

Use additive scoring, then apply gates, suppression, and manual review defaults.

```yaml
score_inputs:
  user_declared_theme:
    points: 6

  commander_strongly_supports_theme:
    points: 5

  commander_lightly_supports_theme:
    points: 2

  theme_card:
    points: 1

  payoff:
    points: 2

  required_package_half_present:
    points: 2

  both_package_halves_present:
    points: 4

  meta_reason_known:
    points: 3

  legality_confirmed_or_rule_zero_allowed:
    points: 3

  flavor_intent_declared:
    points: 4

  parity_breaker_present:
    points: 3

  replacement_constraint_present:
    points: 2
```

Risk penalties:

```yaml
risk_penalties:
  no_user_intent:
    points: -3

  no_payoff:
    points: -4

  missing_package_half:
    points: -5

  legality_unknown:
    points: -4

  rule_zero_required_unknown:
    points: -5

  social_contract_pressure_without_win_path:
    points: -4

  meta_dependent_no_meta_reason:
    points: -3

  self_synergy_conflict:
    points: -5

  only_funny_once:
    points: -2

  no_clear_win_condition:
    points: -5

  high_complexity_low_payoff:
    points: -3
```

Confidence bands:

```yaml
confidence:
  high:
    - user declared theme
    - commander support moderate or strong
    - package has enough density
    - payoff exists
    - legality/table status known if relevant
    - no major self-conflict

  medium:
    - commander support exists
    - theme count is moderate
    - payoff exists
    - user intent unclear
    - should be manual review

  low:
    - isolated cards
    - no commander support
    - no payoff
    - legality uncertain
    - meta reason unknown
    - self-synergy conflict present
```

---

# 5.2.54 Fringe Report Behavior

When fringe themes appear, include a dedicated report section:

```markdown
## Fringe / Manual Review Theme

Detected fringe theme:
Status:
User intent known:
Commander support:
Theme density:
Payoff support:
Package dependency:
Missing pieces:
Legality or Rule Zero concerns:
Social contract pressure:
Meta dependency:
Self-synergy conflicts:
Cards that are protected if intentional:
Cards with higher cut pressure:
Replacement constraints:
Recommended review question:
```

The report should answer:

1. Is this theme user-declared or inferred?
2. Is it supported enough to function?
3. Does it require Rule Zero, legality review, or outside-game components?
4. Is it meta-dependent?
5. Does it create social contract pressure?
6. Does it conflict with the deck’s own plan?
7. Is it a package that needs missing pieces?
8. Are replacements constrained by companion, colorless, odd/even, flavor, legality, or theme?
9. Should it be protected, cut, or manually reviewed?
10. What would make the theme more reliable?

---

# 5.2.55 Fringe Warning Messages

Use warnings when appropriate.

## Manual Review Default Warning

```markdown
Warning: This appears to be a fringe package. I would treat it as manual review unless the user intentionally wants this theme.
```

## User Intent Warning

```markdown
Warning: This theme may be intentional, but user intent is not clear. Avoid cutting or protecting these cards too aggressively until the desired balance of flavor, power, and theme is known.
```

## Rule Zero Warning

```markdown
Warning: This package may require Rule Zero or legality review before normal Commander play.
```

## Social Contract Warning

```markdown
Warning: This package may create table-expectation or salt pressure. It is not automatically wrong, but it should be discussed for casual pods.
```

## Meta Dependency Warning

```markdown
Warning: This package is highly meta-dependent. It may be strong in the right pod and weak or dead in the wrong one.
```

## Self-Synergy Conflict Warning

```markdown
Warning: This package may conflict with the deck’s own plan. Review whether the deck breaks parity or accidentally shuts itself off.
```

## Package Missing Piece Warning

```markdown
Warning: This package appears incomplete. One half of the required synergy is missing or underrepresented.
```

## Flavor-First Warning

```markdown
Note: This may be a flavor-first inclusion. Do not remove it purely for efficiency unless the user wants power optimization.
```

---

# 5.2.56 Final Section 5.2 Summary Rule

Fringe analysis should not ask only:

```text
Is this theme strong?
```

It should ask:

```text
Is this theme intentional, supported, legal/table-appropriate, and compatible with the deck’s actual plan?
```

A fringe card should be protected from cuts when it:
- Supports a user-declared theme
- Is one of the few available payoff pieces
- Completes a required package
- Preserves a deckbuilding restriction
- Supports a flavor-first build
- Is known meta tech
- Is legal/table-approved in the user’s pod
- Lets the deck break parity on a socially sensitive effect

A fringe card should be reviewed as a possible cut when it:
- Has no payoff support
- Requires a missing partner card
- Creates legality or Rule Zero issues
- Conflicts with the deck’s own plan
- Is only useful in a specific meta with no evidence that meta exists
- Creates salt pressure without helping the deck win
- Is funny once but weak repeatedly
- Makes replacement logic harder without enough payoff

Most important language rule:

```text
This is not automatically bad, but it is not safe to assume it belongs unless the deck or user intent supports it.
```
