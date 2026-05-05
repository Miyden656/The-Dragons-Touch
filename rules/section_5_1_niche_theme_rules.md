# Section 5.1: Niche Theme Rules
Version: v0.5.6-ready
Purpose: Help the MTG Commander Deck Helper identify narrow but legitimate Commander themes, evaluate whether they are primary/secondary/minor packages, and apply context-aware cut/replacement logic.

A niche theme is narrower than a major Commander archetype, but still legitimate enough that a deck can intentionally be built around it.

Niche does not mean bad.  
Unsupported means bad.

A niche theme should be recognized when the deck has enough:
- Theme density
- Payoff density
- Commander support
- Enabler/payoff balance
- Strategy fit
- Execution reliability
- Win condition relevance

Many niche cards look weak by generic standards but are correct when they provide density, enable a narrow mechanic, or bridge multiple supported themes.

---

# 5.1.1 Core Niche Theme Philosophy

A niche theme should be evaluated through this formula:

```text
niche_theme_strength = commander_support + enabler_density + payoff_density + execution_support + win_path
```

The helper should not ask only:

```text
Is this card generically powerful?
```

It should ask:

```text
Does this card enable a narrow theme that the deck is actually built to support?
```

Examples:
- A Gate is weak mana fixing in most decks, but core infrastructure in a Gates deck.
- A cheap non-Human body may look replaceable, but it is a mutate base in Mutate.
- A one-mana evasive Infect creature may look small, but poison changes combat math.
- Blood tokens are not just rummage; they can support Vampires, discard, Madness, Reanimator, artifacts, and sacrifice.
- Powerstones are not normal ramp; they only matter if the deck can spend the colorless mana effectively.
- A Battle is not automatically good value; the deck needs realistic ways to flip it.

---

# 5.1.2 Niche Theme Output Fields

For each detected niche theme, record:

```yaml
niche_theme:
  name:
  role: primary | secondary | minor_package | support_package | manual_review
  confidence: low | medium | high
  commander_support: none | light | moderate | strong
  theme_count:
  enabler_count:
  payoff_count:
  generator_count:
  execution_support_count:
  win_condition_present: true | false
  linked_themes:
  strategy_shape:
  parasitic_level: low | medium | high
  table_dependency: low | medium | high
  bracket_pressure: none | low | medium | high
  key_enablers:
  key_payoffs:
  protected_cards:
  possible_cut_candidates:
  replacement_categories:
  report_notes:
```

---

# 5.1.3 Niche Theme Role Definitions

## Primary Niche Theme

A niche theme may be primary if:
- The commander directly supports the theme, and density/payoffs are sufficient.
- Or the deck has high enough theme density and payoff count without commander support.
- The theme has a clear path to victory.
- The theme shapes cuts, replacements, and protected cards.

## Secondary Niche Package

A niche theme may be secondary if:
- It supports the primary plan.
- It has moderate density.
- It has at least one meaningful payoff.
- It helps the deck’s engine function.

## Minor Niche Package

A niche theme is minor if:
- It appears in a small cluster.
- It supports a larger archetype.
- It is not strong enough to define the deck.
- It may be context-dependent or playtest-first.

## Support Package

A niche theme is support if:
- It is mostly infrastructure.
- It enables another primary strategy.
- It does not itself provide the win condition.

## Manual Review

Use manual review if:
- The deck has only one or two theme cards.
- Payoff/enabler balance is unclear.
- The cards may be flavor inclusions.
- The cards are narrow and unsupported.
- The theme may conflict with the primary plan.

---

# 5.1.4 Global Niche Theme Primary Gate

A niche theme should not become primary from one or two cards.

Use this gate:

```python
def can_be_primary_niche_theme(theme_count, payoff_count, commander_support):
    return (
        commander_support and theme_count >= 6 and payoff_count >= 2
    ) or (
        theme_count >= 9 and payoff_count >= 3
    )
```

A theme that fails this gate may still be:
- Secondary package
- Minor package
- Support package
- Manual review

---

# 5.1.5 Global Niche Secondary Package Gate

Use this for lower-density but real packages:

```python
def can_be_secondary_niche_package(theme_count, payoff_count, commander_support):
    return (
        commander_support and theme_count >= 3 and payoff_count >= 1
    ) or (
        theme_count >= 5 and payoff_count >= 1
    )
```

If this gate fails, the theme should usually be marked:
- Incidental
- Manual review
- Possible off-plan package

---

# 5.1.6 Parasitic Mechanic Gate

Some niche mechanics are parasitic. They need both generators and payoffs.

Use for:
- Energy
- Food
- Blood
- Clues
- Dice rolling
- Coin flipping
- Mutate
- Venture
- Initiative
- Incubate
- Role tokens
- Powerstones
- Face-down mechanics
- Battles
- Sagas
- Ring temptation

```python
def parasitic_theme_supported(generator_count, payoff_count):
    return generator_count >= 5 and payoff_count >= 2
```

If payoff count is high but generator count is low:
- Increase cut pressure on payoffs.

If generator count is high but payoff count is low:
- Increase replacement priority for payoffs.

---

# 5.1.7 Land-Subtype Theme Gate

Use for:
- Gates
- Deserts
- Snow
- Utility Lands
- Land Animation
- Land subtype matters

```python
def land_subtype_theme_supported(
    relevant_land_count,
    payoff_count,
    tutor_or_recursion_count
):
    return (
        relevant_land_count >= 8
        and payoff_count >= 2
    ) or (
        relevant_land_count >= 6
        and payoff_count >= 1
        and tutor_or_recursion_count >= 2
    )
```

Important:
- Relevant lands should not be judged only as mana fixing.
- Tapped lands may be correct if the subtype is part of the engine.
- Replacing lands in these decks must preserve the relevant subtype or utility role when possible.

---

# 5.1.8 Cast-from-Exile Gate

Use for:
- Exile Matters
- Adventures
- Foretell
- Suspend
- Cascade
- Discover
- Plot
- Rebound
- Impulse draw
- Ring-related exile packages if relevant

```python
def cast_from_exile_supported(
    exile_cast_count,
    payoff_count,
    commander_support
):
    return (
        commander_support and exile_cast_count >= 4 and payoff_count >= 1
    ) or (
        exile_cast_count >= 7 and payoff_count >= 2
    )
```

Separate:
- Self-exile value
- Opponent-exile theft
- Delayed casting
- Free-spell chains
- Topdeck/free-cast setup

---

# 5.1.9 Niche Theme Suppression Rules

Niche themes are easy to over-detect.

## Suppress to Minor or Manual Review If

Suppress niche theme scoring if:
- The deck has one or two cards from the mechanic.
- The commander does not support the theme.
- There are no payoffs.
- There are payoffs but not enough enablers.
- The theme conflicts with the primary strategy.
- The theme is better explained as part of a major archetype.

## Suppress Behind Stronger Major Archetype

Examples:
- Foretell often belongs under Exile Matters, Spirits, or Control.
- Adventures may belong under Creature Value, Spellslinger, or Cast-from-Exile.
- Clues may belong under Artifact Tokens or Draw Matters.
- Food may belong under Lifegain, Artifacts, Sacrifice, or Halfling/Hobbit/Squirrel typal.
- Blood may belong under Vampire, Madness, Reanimator, Discard, or Artifact Sacrifice.
- Monarch and Goad may belong under Section 3 Political Strategies.
- Sagas may belong under Enchantress or Enchantment Value.
- Proliferate Poison may belong under Poison, Proliferate, or Control.

## Do Not Suppress If Commander Explicitly Supports Theme

If the commander directly names or repeatedly enables the niche mechanic, preserve the niche theme as at least a secondary package unless the deck clearly lacks support.

---

# 5.1.10 Global Niche Cut Rules

## Do Not Automatically Cut Niche Cards When

Do not automatically cut a niche card if:
- The commander explicitly supports the mechanic.
- The deck has enough enablers and payoffs.
- The card is one of the few available support pieces for a narrow mechanic.
- The card fixes a known weakness of the theme.
- The card contributes to multiple linked themes.
- The card looks weak generically but is a key density piece.
- The deck’s mana base, card type structure, or token economy depends on the theme.
- The card is narrow but necessary for execution.
- The card is a bridge between primary and secondary plans.

## Increase Cut Pressure When

Increase cut pressure if:
- The niche card appears without payoff support.
- The payoff exists but there are not enough enablers.
- The enablers exist but there are no meaningful payoffs.
- The theme conflicts with the primary plan.
- The card is only good when already ahead.
- The card is too narrow for the deck’s actual commander.
- The deck has one or two cards from the theme but no package.
- The mechanic consumes resources the deck needs for another plan.
- The card has high complexity or salt risk without meaningful payoff.
- The card is a low-impact one-shot effect in a theme that needs repeatability.

---

# 5.1.11 Global Niche Replacement Logic

Replacement suggestions should usually be category-based.

Common replacement categories:

```yaml
niche_replacement_categories:
  general:
    - More enablers
    - More payoffs
    - More commander synergy
    - More card draw
    - More protection
    - More interaction
    - More win conditions

  parasitic_mechanics:
    - More generators
    - More payoffs
    - More repeatable engines
    - More payoff redundancy
    - More protection

  land_subtype_themes:
    - More relevant lands
    - More land tutors
    - More land recursion
    - More landfall support
    - More payoff cards
    - Better fixing that preserves subtype density

  exile_cast_themes:
    - More cast-from-exile enablers
    - More exile payoffs
    - More card selection
    - More topdeck manipulation
    - More mana smoothing

  token_artifact_themes:
    - More token generators
    - More artifact payoff
    - More sacrifice outlets
    - More recursion
    - More card draw

  poison_themes:
    - More poison enablers
    - More proliferate
    - More evasion
    - More protection
    - More interaction

  random_mechanics:
    - More trigger density
    - More payoff density
    - More dice/coin modifiers
    - More reliable win conditions
    - More card draw
```

---

# 5.1.12 Mutate

## Definition

Mutate decks cast creatures for their mutate cost onto non-Human creatures, stacking abilities and repeatedly triggering mutate abilities.

## Detection Signals

Increase Mutate score for:
- Mutate creatures
- Mutate payoff cards
- Cheap non-Human bodies
- Hexproof/indestructible/protection
- Recursion
- Evasion
- Commander supports mutate
- Repeated mutate triggers
- Nethroi-style graveyard setup

## Primary Gate

```python
def can_be_primary_mutate(
    mutate_count,
    mutate_payoff_count,
    non_human_body_count,
    protection_count,
    commander_support
):
    return (
        commander_support
        and mutate_count >= 8
        and mutate_payoff_count >= 2
        and non_human_body_count >= 6
    ) or (
        mutate_count >= 12
        and mutate_payoff_count >= 3
        and non_human_body_count >= 8
        and protection_count >= 3
    )
```

## Cut Logic

Protect:
- Cheap non-Human bodies
- Mutate creatures
- Mutate payoff cards
- Protection
- Evasion
- Recursion
- Graveyard setup in Nethroi-style builds

Review:
- Humans that cannot be mutate bases unless they have another role
- Expensive mutate creatures without strong trigger
- Mutate cards with too few safe bodies
- Auras/Equipment if they do not protect the stack
- Noncreature cards that do not support protection, recursion, or draw

## Replacement Categories

- More cheap non-Human bodies
- More protection
- More mutate payoffs
- More recursion
- More evasion
- More card draw

## Report Behavior

Include:
- “Safe mutation base count”
- “Protection for mutate stack”
- “Mutate trigger density”
- “Whether the deck folds to single-target removal”

---

# 5.1.13 Dungeons / Venture

## Definition

Dungeon decks use venture into the dungeon to progress through dungeon rooms for incremental value.

## Detection Signals

Increase Venture score for:
- Venture triggers
- Repeatable venture
- Dungeon completion payoff
- Blink support
- Recursion
- ETB loops
- Death triggers that venture
- Commander supports dungeon completion

## Primary Gate

```python
def can_be_primary_venture(
    venture_count,
    repeatable_venture_count,
    dungeon_payoff_count,
    commander_support
):
    return (
        commander_support
        and venture_count >= 6
        and repeatable_venture_count >= 2
        and dungeon_payoff_count >= 2
    ) or (
        venture_count >= 9
        and repeatable_venture_count >= 3
        and dungeon_payoff_count >= 3
    )
```

## Cut Logic

Protect:
- Repeatable venture engines
- Blink support
- ETB creatures with venture
- Dungeon completion payoffs
- Recursion in Sefris-style decks

Review:
- One-shot venture cards with no repeatability
- Dungeon payoffs if completion is unlikely
- Blink cards with too few ETB venture targets
- Combat-only venture if deck cannot connect

## Replacement Categories

- More repeatable venture
- More blink
- More recursion
- More dungeon completion payoff
- More protection
- More card draw

## Report Behavior

Include:
- “Can the deck complete dungeons consistently?”
- “Repeatable venture count”
- “Best dungeon completion payoffs”
- “One-shot venture cards under review”

---

# 5.1.14 Initiative / Undercity

## Definition

Initiative decks take the initiative and progress through the Undercity. The initiative can be stolen through combat, so these decks need defense or ways to reclaim it.

## Detection Signals

Increase Initiative score for:
- Initiative cards
- Undercity payoff
- Evasive creatures
- Defensive blockers
- Pillowfort
- Goad
- Removal
- Commander supports initiative or dungeon value

## Primary Gate

```python
def can_be_primary_initiative(
    initiative_count,
    initiative_payoff_count,
    initiative_defense_count,
    commander_support
):
    return (
        commander_support
        and initiative_count >= 4
        and initiative_payoff_count >= 2
        and initiative_defense_count >= 3
    ) or (
        initiative_count >= 6
        and initiative_payoff_count >= 2
        and initiative_defense_count >= 4
    )
```

## Cut Logic

Protect:
- Initiative enablers
- Evasive initiative attackers
- Defensive deterrents
- Pillowfort
- Removal that helps keep initiative
- Dungeon completion support

Review:
- Initiative cards if deck cannot defend/reclaim it
- Expensive initiative creatures without protection
- Combat cards with no evasion
- Dungeon payoff cards with low dungeon progression

## Replacement Categories

- More evasive attackers
- More defense
- More pillowfort
- More removal
- More initiative payoffs
- More card draw

## Report Behavior

Include:
- “Can the deck keep or retake initiative?”
- “Initiative defense count”
- “Evasive attacker count”
- “Risk of giving opponents Undercity value”

---

# 5.1.15 Vehicles

## Definition

Vehicle decks use creatures to crew artifact Vehicles, often combining artifact synergy, pilot tokens, tap/untap effects, combat, and control.

## Detection Signals

Increase Vehicle score for:
- Vehicle count
- Crew enablers
- Pilot tokens
- Artifact support
- Tap/untap support
- Vehicle cost reduction
- Commander rewards Vehicles
- Creatures with high power for crew
- Token makers that crew efficiently

## Primary Gate

```python
def can_be_primary_vehicles(
    vehicle_count,
    crew_enabler_count,
    vehicle_payoff_count,
    commander_support
):
    return (
        commander_support
        and vehicle_count >= 7
        and crew_enabler_count >= 6
        and vehicle_payoff_count >= 2
    ) or (
        vehicle_count >= 10
        and crew_enabler_count >= 8
        and vehicle_payoff_count >= 3
    )
```

## Cut Logic

Protect:
- Cheap creatures that crew
- Pilot token makers
- Vehicle payoff cards
- Artifact support
- Tap/untap support
- Shorikai-style draw/discard engines

Review:
- Vehicles with high crew costs and low payoff
- Creatures that do not crew well or support artifact plan
- Artifact payoffs with too few artifacts
- Combat-only cards if Vehicle density is low

## Replacement Categories

- More crew enablers
- More efficient Vehicles
- More pilot tokens
- More artifact payoff
- More card draw
- More protection

## Report Behavior

Include:
- “Vehicle count”
- “Crew infrastructure”
- “Artifact support”
- “Cards that look low-impact but enable crew”

---

# 5.1.16 Gates

## Definition

Gate decks use lands with the Gate subtype and cards that reward Gate count.

## Detection Signals

Increase Gates score for:
- Gate land count
- Gate payoff
- Maze’s End
- Gate tutors
- Land recursion
- Landfall support
- Five-color fixing
- Commander supports Gates or land combat

## Primary Gate

```python
def can_be_primary_gates(
    gate_count,
    gate_payoff_count,
    gate_tutor_or_recursion_count,
    commander_support
):
    return (
        gate_count >= 8
        and gate_payoff_count >= 2
    ) or (
        commander_support
        and gate_count >= 6
        and gate_payoff_count >= 1
        and gate_tutor_or_recursion_count >= 2
    )
```

## Cut Logic

Protect:
- Gates
- Maze’s End
- Gate tutors
- Gate payoff cards
- Land recursion
- Landfall support if linked

Review:
- Non-Gate tapped lands
- Gate payoffs with too few Gates
- Color-fixing cards that reduce Gate density too much
- Landfall cards if land count/support is low

## Replacement Categories

- More Gates
- More Gate tutors
- More land recursion
- More payoff cards
- More landfall support
- Better fixing that preserves Gate count

## Report Behavior

Include:
- “Gate count”
- “Maze’s End viability”
- “Tapped land risk vs subtype importance”
- “Gate payoffs worth protecting”

---

# 5.1.17 Shrines

## Definition

Shrine decks use Shrine enchantments that scale with the number of Shrines controlled.

## Detection Signals

Increase Shrines score for:
- Shrine count
- Shrine payoff
- Enchantment support
- Shrine recursion
- Shrine tutors
- Five-color mana fixing
- Commander supports Shrines or enchantments

## Primary Gate

```python
def can_be_primary_shrines(
    shrine_count,
    shrine_payoff_count,
    enchantment_support_count,
    commander_support
):
    return (
        commander_support
        and shrine_count >= 8
        and shrine_payoff_count >= 2
    ) or (
        shrine_count >= 10
        and shrine_payoff_count >= 2
        and enchantment_support_count >= 4
    )
```

## Cut Logic

Protect:
- Shrines
- Shrine tutors
- Shrine recursion
- Enchantment support
- Five-color fixing
- Payoff enchantments

Review:
- Enchantment cards with no Shrine support if deck is Shrine-focused
- Shrines if count is too low to scale
- Five-color goodstuff that dilutes Shrine density
- Expensive support that does not protect or recur Shrines

## Replacement Categories

- More Shrines
- More enchantment support
- More Shrine recursion
- More tutors
- More five-color fixing
- More protection

## Report Behavior

Include:
- “Shrine count”
- “Scaling payoff quality”
- “Enchantment support”
- “Five-color mana stability”

---

# 5.1.18 Mill

## Definition

Mill decks put opponents’ libraries into their graveyards. In Commander, successful mill usually needs repeatable engines, burst mill, theft, graveyard exile, or combo.

## Detection Signals

Increase Mill score for:
- Opponent mill
- Repeatable mill engines
- Mill payoff
- Theft from milled cards
- Graveyard exile payoff
- Horror/Rogue mill support
- Infinite mill loops
- Commander mills or rewards mill

## Primary Gate

```python
def can_be_primary_mill(
    mill_count,
    repeatable_mill_count,
    mill_payoff_count,
    commander_support
):
    return (
        commander_support
        and mill_count >= 6
        and repeatable_mill_count >= 2
        and mill_payoff_count >= 2
    ) or (
        mill_count >= 9
        and repeatable_mill_count >= 3
        and mill_payoff_count >= 3
    )
```

## Cut Logic

Protect:
- Repeatable mill
- Mill payoff
- Graveyard theft
- Graveyard exile payoff
- Combo mill pieces

Review:
- Small one-shot mill cards
- Self-mill cards unless graveyard hybrid
- Mill without payoff or scale
- Theft payoffs with too little mill
- Cards that fuel opponents’ graveyard decks without benefit

## Replacement Categories

- More repeatable mill
- More mill payoff
- More graveyard theft
- More graveyard exile
- More control
- More protection

## Report Behavior

Include:
- “Does the deck scale to three 100-card libraries?”
- “Repeatable mill count”
- “Mill payoff count”
- “Risk of helping graveyard decks”

---

# 5.1.19 Infect

## Definition

Infect deals damage to players as poison counters and to creatures as -1/-1 counters. Infect changes combat math because players lose at 10 poison counters.

## Detection Signals

Increase Infect score for:
- Infect creatures
- Poison counter support
- Pump spells
- Evasion
- Protection
- Proliferate
- Commander supports poison
- Low-cost efficient infect threats

## Primary Gate

```python
def can_be_primary_infect(
    infect_count,
    pump_or_evasion_count,
    protection_count,
    poison_payoff_count,
    commander_support
):
    return (
        commander_support
        and infect_count >= 6
        and pump_or_evasion_count >= 5
        and protection_count >= 2
    ) or (
        infect_count >= 8
        and pump_or_evasion_count >= 6
        and poison_payoff_count >= 2
    )
```

## Cut Logic

Protect:
- Low-stat infect creatures
- Pump spells
- Evasion
- Protection
- Proliferate support
- Poison payoff cards

Review:
- Infect creatures without evasion/protection
- Pump spells with too few poison creatures
- Poison payoffs without poison enablers
- Slow value cards that do not help close

## Replacement Categories

- More poison enablers
- More evasion
- More protection
- More proliferate
- More pump
- More interaction

## Report Behavior

Include:
- “Poison threat density”
- “Protection/evasion count”
- “Table threat perception”
- “Whether the deck can finish after giving early poison”

---

# 5.1.20 Toxic / Corrupted

## Definition

Toxic gives fixed poison counters when combat damage is dealt. Corrupted rewards opponents having three or more poison counters.

## Detection Signals

Increase Toxic/Corrupted score for:
- Toxic creatures
- Mite tokens
- Corrupted payoff
- Proliferate
- Poison value cards
- Evasion
- Commander supports corrupted/poison
- Combat support

## Primary Gate

```python
def can_be_primary_toxic_corrupted(
    toxic_count,
    corrupted_payoff_count,
    proliferate_count,
    commander_support
):
    return (
        commander_support
        and toxic_count >= 6
        and corrupted_payoff_count >= 2
    ) or (
        toxic_count >= 8
        and corrupted_payoff_count >= 3
        and proliferate_count >= 2
    )
```

## Cut Logic

Protect:
- Toxic creatures
- Mite token makers
- Corrupted payoffs
- Proliferate
- Evasion
- Poison value pieces

Review:
- Corrupted payoffs with too few poison enablers
- Toxic creatures without evasion or board support
- Poison cards that do not support the value plan
- Slow cards that do not advance poison or corrupted

## Replacement Categories

- More toxic creatures
- More corrupted payoff
- More proliferate
- More evasive threats
- More protection
- More card draw

## Report Behavior

Include:
- “Is the deck trying to kill with poison or turn on corrupted?”
- “Poison enabler count”
- “Corrupted payoff count”
- “Proliferate support”

---

# 5.1.21 Energy

## Definition

Energy decks generate energy counters and spend them on creatures, artifacts, tokens, copying, damage, or activated abilities.

Energy is parasitic and needs generator/payoff balance.

## Detection Signals

Increase Energy score for:
- Energy generators
- Energy payoffs
- Energy sinks
- Artifact-energy support
- Token/copy energy support
- Commander generates or spends energy
- Repeated activated abilities using energy

## Primary Gate

```python
def can_be_primary_energy(
    energy_generator_count,
    energy_payoff_count,
    energy_sink_count,
    commander_support
):
    return (
        commander_support
        and energy_generator_count >= 5
        and (energy_payoff_count + energy_sink_count) >= 3
    ) or (
        energy_generator_count >= 8
        and (energy_payoff_count + energy_sink_count) >= 4
    )
```

## Cut Logic

Protect:
- Energy generators
- Energy sinks
- Energy payoff cards
- Artifact support in energy artifact shells
- Copy/token engines tied to energy

Review:
- Energy payoffs without energy production
- Energy generators with no meaningful sink
- Cards that require too much energy for low impact
- Off-theme artifact cards with no energy role

## Replacement Categories

- More energy generators
- More energy payoffs
- More energy sinks
- More artifact support
- More card draw
- More protection

## Report Behavior

Include:
- “Generator/payoff balance”
- “Energy sink quality”
- “Whether the commander solves energy production”
- “Cards with high cut pressure due to unsupported energy cost”

---

# 5.1.22 Coin Flipping

## Definition

Coin flip decks use random coin outcomes and cards that reward flipping, winning flips, or multiplying flips.

## Detection Signals

Increase Coin Flip score for:
- Coin flip cards
- Coin flip payoff
- Coin flip multipliers
- Randomness payoff
- Commander rewards flips
- Spell copy from flips
- Okaun/Zndrsplt-style combat or draw payoffs

## Primary Gate

```python
def can_be_primary_coin_flip(
    coin_flip_count,
    coin_flip_payoff_count,
    coin_flip_multiplier_count,
    commander_support
):
    return (
        commander_support
        and coin_flip_count >= 5
        and coin_flip_payoff_count >= 2
    ) or (
        coin_flip_count >= 8
        and coin_flip_payoff_count >= 3
    ) or (
        coin_flip_count >= 5
        and coin_flip_multiplier_count >= 2
        and coin_flip_payoff_count >= 2
    )
```

## Cut Logic

Protect:
- Coin flip payoffs
- Flip multipliers
- Cards that trigger repeatedly
- Okaun/Zndrsplt support
- Krark-style spell-copy infrastructure

Review:
- One-off random cards with no payoff
- Coin flip cards that do not advance win condition
- Chaos cards that only slow the game
- High-variance cards without payoff density

## Replacement Categories

- More coin flip triggers
- More coin flip payoff
- More multipliers
- More protection
- More reliable win conditions
- More card draw

## Report Behavior

Include:
- “Flip trigger density”
- “Payoff density”
- “Randomness value vs randomness noise”
- “How the deck wins despite variance”

---

# 5.1.23 Dice Rolling

## Definition

Dice decks roll dice for value and use cards that improve, copy, or reward rolls.

## Detection Signals

Increase Dice score for:
- Dice rolling effects
- Dice payoffs
- Dice modifiers
- Treasure from dice
- Token creation from dice
- Commander rewards dice
- Artifact-token payoffs if dice creates tokens

## Primary Gate

```python
def can_be_primary_dice(
    dice_roll_count,
    dice_payoff_count,
    dice_modifier_count,
    commander_support
):
    return (
        commander_support
        and dice_roll_count >= 5
        and dice_payoff_count >= 2
    ) or (
        dice_roll_count >= 8
        and dice_payoff_count >= 3
    ) or (
        dice_roll_count >= 5
        and dice_modifier_count >= 2
        and dice_payoff_count >= 2
    )
```

## Cut Logic

Protect:
- Repeatable dice roll cards
- Dice payoff cards
- Dice modifiers
- Treasure/token dice engines
- Mr. House-style artifact-token support

Review:
- Random roll cards without payoff
- Dice payoffs with too few roll triggers
- High-variance cards with low output
- Cards that do not support the actual dice reward type

## Replacement Categories

- More dice triggers
- More dice payoffs
- More dice modifiers
- More token/artifact payoff
- More card draw
- More finishers

## Report Behavior

Include:
- “Roll trigger density”
- “Payoff density”
- “Dice modifier count”
- “Whether random value converts into a win”

---

# 5.1.24 Adventures

## Definition

Adventure decks use creature cards with attached instant or sorcery Adventure halves. These cards can count across multiple roles.

## Detection Signals

Increase Adventure score for:
- Adventure cards
- Adventure payoff
- Creature/spell hybrid support
- Cast-from-exile triggers
- Spell copying
- Bounce/recast support
- Commander copies or rewards Adventures
- Creature ETB value

## Primary Gate

```python
def can_be_primary_adventures(
    adventure_count,
    adventure_payoff_count,
    cast_from_exile_payoff_count,
    commander_support
):
    return (
        commander_support
        and adventure_count >= 8
        and (adventure_payoff_count + cast_from_exile_payoff_count) >= 2
    ) or (
        adventure_count >= 12
        and (adventure_payoff_count + cast_from_exile_payoff_count) >= 3
    )
```

## Multi-Role Counting Rule

Adventure cards may count as:
- Creature density
- Spell density
- Cast-from-exile support
- Creature ETB support
- Bounce/recast support
- Spellslinger support

## Cut Logic

Protect:
- Adventure cards that serve multiple roles
- Adventure payoff
- Cast-from-exile payoff
- Bounce/recast engines
- Spell-copy support for Adventure halves

Review:
- Adventure cards where neither half supports the deck
- Payoffs with too few Adventure cards
- Generic creatures if spell plan is primary
- Spell support if Adventure density is too low

## Replacement Categories

- More Adventure cards
- More cast-from-exile payoff
- More bounce/recast support
- More card draw
- More protection
- More spell/creature hybrid payoffs

## Report Behavior

Include:
- “Adventure cards counted as both creature and spell support”
- “Cast-from-exile overlap”
- “Payoff density”
- “Cards that look odd but fill multiple roles”

---

# 5.1.25 Foretell

## Definition

Foretell exiles cards face down for later casting, usually at a reduced cost. It often supports cast-from-exile, Spirit tokens, and control.

## Detection Signals

Increase Foretell score for:
- Foretell cards
- Foretell payoff
- Cast-from-exile payoff
- Spirit token support
- Delayed casting
- Instant-speed flexibility
- Commander supports foretell or exile

## Primary Gate

```python
def can_be_primary_foretell(
    foretell_count,
    foretell_payoff_count,
    commander_support
):
    return (
        commander_support
        and foretell_count >= 6
        and foretell_payoff_count >= 2
    ) or (
        foretell_count >= 10
        and foretell_payoff_count >= 3
    )
```

## Suppression Rules

Foretell is usually a subtheme unless commander support is strong.

Suppress behind:
- Exile Matters
- Spirits
- Control
- Cast-from-exile value

## Cut Logic

Protect:
- Foretell payoff cards
- Cast-from-exile payoffs
- Spirit token engines
- Control cards that benefit from delayed casting

Review:
- Foretell cards with no payoff
- Foretell payoffs with too few foretell cards
- Slow delayed spells that do not support the control plan
- Cards that do not trigger commander/exile payoff

## Replacement Categories

- More foretell cards
- More cast-from-exile payoff
- More Spirit support
- More control tools
- More card draw

## Report Behavior

Include:
- “Foretell primary or subtheme?”
- “Cast-from-exile overlap”
- “Spirit/control support”
- “Delayed casting payoff density”

---

# 5.1.26 Suspend

## Definition

Suspend exiles spells with time counters and casts them later. Suspend decks use time-counter manipulation, cast-from-exile payoffs, and big delayed spells.

## Detection Signals

Increase Suspend score for:
- Suspend cards
- Time counter manipulation
- Cast-from-exile payoff
- Big delayed spells
- Commander supports suspend/time counters
- Extra turns or spell-copy payoff

## Primary Gate

```python
def can_be_primary_suspend(
    suspend_count,
    time_counter_support_count,
    payoff_count,
    commander_support
):
    return (
        commander_support
        and suspend_count >= 5
        and payoff_count >= 2
    ) or (
        suspend_count >= 8
        and payoff_count >= 2
        and time_counter_support_count >= 2
    )
```

## Cut Logic

Protect:
- Suspend spells
- Time-counter manipulation
- Cast-from-exile payoffs
- Big delayed spells if deck cheats timing
- Spell-copy payoff

Review:
- Suspend cards with no time support or payoff
- Big suspend spells that arrive too late
- Payoffs with too few suspend/exile casts
- Cards that conflict with curve or tempo

## Replacement Categories

- More suspend cards
- More time-counter manipulation
- More cast-from-exile payoff
- More protection
- More card draw
- More interaction

## Report Behavior

Include:
- “Suspend count”
- “Time-counter manipulation”
- “Whether suspend functions as cost-cheat”
- “Risk of delayed spells being too slow”

---

# 5.1.27 Cascade

## Definition

Cascade reveals cards until a cheaper nonland card is found and casts it for free. Cascade decks can be fair value or carefully built to control hits.

## Detection Signals

Increase Cascade score for:
- Cascade cards
- Free-spell payoff
- High-MV cascade enablers
- Low-MV hit quality
- Commander grants cascade
- Topdeck manipulation
- Mana value curve construction
- Sliver cascade support if relevant

## Primary Gate

```python
def can_be_primary_cascade(
    cascade_count,
    cascade_payoff_count,
    good_hit_count,
    commander_support
):
    return (
        commander_support
        and cascade_count >= 5
        and cascade_payoff_count >= 2
        and good_hit_count >= 8
    ) or (
        cascade_count >= 8
        and cascade_payoff_count >= 2
        and good_hit_count >= 10
    )
```

## Cascade Hit Quality Rule

Flag:
- `good_cascade_hit`
- `bad_cascade_hit`
- `curve_pollution`
- `intentional_no_low_mv_build`

A cascade deck should review cheap cards that are poor cascade hits.

## Cut Logic

Protect:
- Cascade enablers
- Strong cascade hits
- Topdeck manipulation
- Free-spell payoff
- Mana fixing/ramp for high-MV cascade spells

Review:
- Low-MV cards that are bad cascade hits
- Cascade cards with poor hit quality
- Cheap narrow interaction if it undermines cascade plan
- High-MV spells that do not justify cascade sequencing

## Replacement Categories

- Better cascade hits
- More cascade enablers
- More topdeck manipulation
- More ramp
- More free-spell payoff
- Better curve construction

## Report Behavior

Include:
- “Cascade hit quality”
- “Bad cascade hits”
- “Mana value curve concerns”
- “Whether deck is fair cascade or controlled cascade”

---

# 5.1.28 Discover

## Definition

Discover is similar to cascade but allows the revealed card to be cast or put into hand. Discover decks convert one spell or trigger into another.

## Detection Signals

Increase Discover score for:
- Discover cards
- Discover payoff
- Free-spell payoff
- Dinosaur discover support
- Graveyard/spell recursion if relevant
- Mana value curve construction
- Commander triggers discover

## Primary Gate

```python
def can_be_primary_discover(
    discover_count,
    discover_payoff_count,
    good_hit_count,
    commander_support
):
    return (
        commander_support
        and discover_count >= 5
        and discover_payoff_count >= 2
        and good_hit_count >= 8
    ) or (
        discover_count >= 8
        and discover_payoff_count >= 2
        and good_hit_count >= 10
    )
```

## Cut Logic

Protect:
- Discover enablers
- Strong discover hits
- Dinosaur discover support
- Free-spell payoffs
- Curve manipulation

Review:
- Low-impact discover hits
- Discover cards with poor hit quality
- Cards that disrupt intended mana value spread
- Discover payoff cards with too little discover

## Replacement Categories

- Better discover hits
- More discover enablers
- More free-spell payoff
- More topdeck manipulation
- Better curve construction
- More card draw

## Report Behavior

Include:
- “Discover hit quality”
- “Mana value spread”
- “Whether discover is primary or Dinosaur support”
- “Bad discover hits under review”

---

# 5.1.29 Cycling

## Definition

Cycling decks discard cards to draw cards, triggering cycling payoffs, discard payoffs, draw triggers, graveyard setup, or reanimation support.

## Detection Signals

Increase Cycling score for:
- Cycling cards
- Cycling payoff
- Discard payoff
- Draw triggers
- Graveyard setup
- Reanimation payoff
- Astral Slide-style blink
- Commander supports cycling

## Primary Gate

```python
def can_be_primary_cycling(
    cycling_count,
    cycling_payoff_count,
    discard_or_draw_payoff_count,
    commander_support
):
    return (
        commander_support
        and cycling_count >= 12
        and (cycling_payoff_count + discard_or_draw_payoff_count) >= 3
    ) or (
        cycling_count >= 16
        and (cycling_payoff_count + discard_or_draw_payoff_count) >= 4
    )
```

## Cut Logic

Protect:
- Low-cost cycling cards
- Cycling payoffs
- Draw/discard payoffs
- Reanimation setup cards
- Astral Slide-style blink pieces

Review:
- Cycling cards with high cycling costs and weak front sides
- Cycling payoffs with too few cycling cards
- Discard payoffs with too few discard outlets
- Cards that do not cycle or support payoff density

## Replacement Categories

- More cycling cards
- More cycling payoff
- More discard payoff
- More draw payoff
- More graveyard payoff
- More reanimation

## Report Behavior

Include:
- “Cycling count”
- “Average cycling cost if available”
- “Cycling payoff count”
- “Cards that are included for cycling mode, not front side”

---

# 5.1.30 Madness

## Definition

Madness lets cards be cast for an alternate cost when discarded. Madness decks need discard outlets, rummage, wheels, graveyard synergies, and discard payoffs.

## Detection Signals

Increase Madness score for:
- Madness cards
- Discard outlets
- Rummage
- Wheels
- Discard payoff
- Graveyard setup
- Reanimation
- Commander supports madness/discard

## Primary Gate

```python
def can_be_primary_madness(
    madness_count,
    discard_outlet_count,
    madness_payoff_count,
    commander_support
):
    return (
        commander_support
        and madness_count >= 8
        and discard_outlet_count >= 6
        and madness_payoff_count >= 2
    ) or (
        madness_count >= 12
        and discard_outlet_count >= 8
        and madness_payoff_count >= 3
    )
```

## Cut Logic

Protect:
- Discard outlets
- Madness cards
- Rummage/wheel effects
- Graveyard payoff
- Reanimation support

Review:
- Madness cards without discard outlets
- Discard outlets without payoffs
- Expensive madness cards with low impact
- Cards that discard at bad timing or high cost

## Replacement Categories

- More discard outlets
- More madness cards
- More discard payoff
- More reanimation
- More card draw
- More graveyard support

## Report Behavior

Include:
- “Discard outlet count”
- “Madness payoff count”
- “Discard is engine, not card disadvantage”
- “Unsupported madness cards under review”

---

# 5.1.31 Face-Down / Morph / Manifest / Disguise / Cloak

## Definition

Face-down decks play creatures face down, then turn them face up or use them as hidden value.

## Detection Signals

Increase Face-Down score for:
- Morph
- Manifest
- Disguise
- Cloak
- Face-up triggers
- Face-down cost reduction
- Commander supports face-down creatures
- Blink/bounce support
- Graveyard/manifest support
- Combat ambiguity

## Primary Gate

```python
def can_be_primary_face_down(
    face_down_count,
    face_up_payoff_count,
    face_down_support_count,
    commander_support
):
    return (
        commander_support
        and face_down_count >= 10
        and (face_up_payoff_count + face_down_support_count) >= 3
    ) or (
        face_down_count >= 14
        and (face_up_payoff_count + face_down_support_count) >= 4
    )
```

## Cut Logic

Protect:
- Face-down creatures
- Face-up trigger payoffs
- Cost reducers
- Manifest/cloak engines
- Hidden information payoff
- Protection for face-down board

Review:
- Face-down cards with weak face-up value
- Support cards with too few face-down creatures
- Combat tricks that do not scale
- Expensive morphs without payoff

## Replacement Categories

- More face-down creatures
- More face-up payoff
- More cost reduction
- More protection
- More card draw
- More finishers

## Report Behavior

Include:
- “Face-down density”
- “Face-up payoff count”
- “Hidden information value”
- “Cards that look inefficient but support face-down density”

---

# 5.1.32 Sagas

## Definition

Saga decks use enchantments with chapter abilities and often manipulate, recur, copy, blink, or proliferate lore counters.

## Detection Signals

Increase Saga score for:
- Saga count
- Lore counter manipulation
- Saga recursion
- Enchantment support
- Proliferate
- Blink/copy support
- Commander supports Sagas

## Primary Gate

```python
def can_be_primary_sagas(
    saga_count,
    saga_payoff_count,
    lore_counter_support_count,
    commander_support
):
    return (
        commander_support
        and saga_count >= 8
        and saga_payoff_count >= 2
    ) or (
        saga_count >= 10
        and saga_payoff_count >= 2
        and lore_counter_support_count >= 2
    )
```

## Cut Logic

Protect:
- Sagas
- Saga recursion
- Lore counter manipulation
- Enchantment support
- Proliferate if lore counters matter
- Tom Bombadil-style payoff pieces

Review:
- Sagas with low chapter impact
- Saga payoffs with too few Sagas
- Enchantment support that does not help Sagas
- Lore counter cards with too few Sagas

## Replacement Categories

- More Sagas
- More Saga recursion
- More enchantment support
- More lore counter manipulation
- More protection
- More card draw

## Report Behavior

Include:
- “Saga count”
- “Chapter manipulation”
- “Enchantment overlap”
- “Whether Saga is primary or enchantment support”

---

# 5.1.33 Battles / Sieges

## Definition

Battle decks play Battle cards and need to damage or attack them to transform them into stronger backside effects.

## Detection Signals

Increase Battle score for:
- Battle count
- Battle payoff
- Battle flip enablers
- Combat access
- Direct damage to Battles
- Proliferate/counter manipulation if relevant
- Evasive attackers
- Commander supports Battles

## Primary Gate

```python
def can_be_primary_battles(
    battle_count,
    battle_payoff_count,
    battle_flip_enabler_count,
    commander_support
):
    return (
        commander_support
        and battle_count >= 6
        and battle_payoff_count >= 2
        and battle_flip_enabler_count >= 4
    ) or (
        battle_count >= 9
        and battle_payoff_count >= 3
        and battle_flip_enabler_count >= 5
    )
```

## Cut Logic

Protect:
- Battles with strong back sides
- Battle flip enablers
- Evasive attackers
- Direct damage to Battles
- Proliferate/counter support if it helps flip Battles

Review:
- Battles that the deck cannot realistically flip
- Low-impact Battles
- Battle payoffs with too few Battles
- Combat support if deck cannot safely attack Battles

## Replacement Categories

- More Battle flip enablers
- More evasive attackers
- More direct damage
- More Battle payoff
- More removal
- More card draw

## Report Behavior

Include:
- “Battle count”
- “Can the deck flip its Battles?”
- “Attacker/damage access”
- “Battles with high cut pressure due to low flip reliability”

---

# 5.1.34 Clues / Investigate

## Definition

Investigate creates Clue artifact tokens that can be sacrificed to draw cards. Clues support artifacts, sacrifice, token count, second-draw, and draw triggers.

## Detection Signals

Increase Clue score for:
- Investigate
- Clue token generation
- Clue payoff
- Artifact token payoff
- Sacrifice payoff
- Second-draw payoff
- Commander supports Clues
- Token doubling

## Primary Gate

```python
def can_be_primary_clues(
    clue_generator_count,
    clue_payoff_count,
    artifact_token_payoff_count,
    commander_support
):
    return (
        commander_support
        and clue_generator_count >= 5
        and (clue_payoff_count + artifact_token_payoff_count) >= 2
    ) or (
        clue_generator_count >= 8
        and (clue_payoff_count + artifact_token_payoff_count) >= 3
    )
```

## Cut Logic

Protect:
- Repeatable investigate
- Clue payoff
- Artifact token payoff
- Sacrifice outlets
- Second-draw payoff
- Token doublers

Review:
- One-shot investigate with no payoff
- Artifact payoff with low artifact-token count
- Second-draw payoffs without enough draw triggers
- Clue cards that are too slow for the deck’s plan

## Replacement Categories

- More investigate
- More Clue payoff
- More artifact payoff
- More sacrifice outlets
- More second-draw payoff
- More token doubling

## Report Behavior

Include:
- “Clues as card draw, artifacts, tokens, and sacrifice fodder”
- “Generator/payoff balance”
- “Second-draw overlap”
- “Artifact-token support”

---

# 5.1.35 Food

## Definition

Food decks create Food artifact tokens and use them for lifegain, sacrifice, artifact count, forage, typal support, or value engines.

## Detection Signals

Increase Food score for:
- Food token generation
- Food payoff
- Lifegain payoff
- Artifact token payoff
- Sacrifice outlets
- Forage
- Typal support for Halflings/Hobbits/Squirrels
- Commander supports Food

## Primary Gate

```python
def can_be_primary_food(
    food_generator_count,
    food_payoff_count,
    linked_payoff_count,
    commander_support
):
    return (
        commander_support
        and food_generator_count >= 5
        and (food_payoff_count + linked_payoff_count) >= 2
    ) or (
        food_generator_count >= 8
        and (food_payoff_count + linked_payoff_count) >= 3
    )
```

## Linked Payoffs

Food may support:
- Lifegain
- Artifact sacrifice
- Tokens
- Forage
- Squirrels
- Halflings/Hobbits
- Aristocrats
- Ygra-style artifact/creature conversion

## Cut Logic

Protect:
- Food generators
- Food payoff
- Lifegain payoff if Food fuels it
- Artifact sacrifice payoff
- Typal support cards
- Token doublers

Review:
- Food cards with no payoff
- Lifegain-only cards without payoff
- Artifact payoff with low artifact-token density
- Food cards that are too slow for the primary plan

## Replacement Categories

- More Food generation
- More Food payoff
- More artifact sacrifice payoff
- More lifegain payoff
- More token support
- More card draw

## Report Behavior

Include:
- “Food is artifact, lifegain, sacrifice, and token support”
- “Generator/payoff balance”
- “Linked themes”
- “Cards that look like lifegain but are actually engine pieces”

---

# 5.1.36 Blood

## Definition

Blood tokens are artifacts that can be sacrificed to discard and draw. They connect Vampires, discard, Madness, Reanimator, artifacts, and sacrifice.

## Detection Signals

Increase Blood score for:
- Blood token generation
- Blood payoff
- Discard payoff
- Madness
- Reanimation setup
- Artifact sacrifice payoff
- Vampire support
- Commander rewards Blood

## Primary Gate

```python
def can_be_primary_blood(
    blood_generator_count,
    blood_payoff_count,
    linked_payoff_count,
    commander_support
):
    return (
        commander_support
        and blood_generator_count >= 5
        and (blood_payoff_count + linked_payoff_count) >= 2
    ) or (
        blood_generator_count >= 8
        and (blood_payoff_count + linked_payoff_count) >= 3
    )
```

## Linked Payoffs

Blood may support:
- Vampires
- Madness
- Reanimator
- Discard
- Artifact sacrifice
- Graveyard setup
- Lifedrain

## Cut Logic

Protect:
- Blood generators
- Blood payoff
- Vampire support in Strefan/Anje shells
- Madness/reanimation support
- Artifact sacrifice payoff
- Discard payoffs

Review:
- Blood cards with no payoff
- Madness cards without discard outlets
- Artifact payoffs with low Blood/artifact density
- Vampire cards that do not support Blood plan if Blood is primary

## Replacement Categories

- More Blood generation
- More Blood payoff
- More discard payoff
- More reanimation
- More artifact sacrifice payoff
- More Vampire support

## Report Behavior

Include:
- “Blood as discard, artifact, and graveyard glue”
- “Generator/payoff balance”
- “Vampire/Madness/Reanimator overlap”
- “Cards protected as glue pieces”

---

# 5.1.37 Powerstones

## Definition

Powerstones are artifact tokens that tap for colorless mana that cannot be spent to cast nonartifact spells.

## Detection Signals

Increase Powerstone score for:
- Powerstone token generation
- Artifact casting needs
- Activated ability support
- Colorless mana sinks
- Artifact payoff
- Big artifact threats
- Commander rewards artifacts or colorless mana

## Primary Gate

```python
def can_be_primary_powerstones(
    powerstone_generator_count,
    powerstone_payoff_count,
    spendable_colorless_sink_count,
    commander_support
):
    return (
        commander_support
        and powerstone_generator_count >= 5
        and (powerstone_payoff_count + spendable_colorless_sink_count) >= 3
    ) or (
        powerstone_generator_count >= 8
        and (powerstone_payoff_count + spendable_colorless_sink_count) >= 4
    )
```

## Spendability Rule

Powerstones should not be counted as normal ramp unless the deck can spend that mana on:
- Artifact spells
- Activated abilities
- Colorless spells
- Artifact token synergies
- Big artifact engines

## Cut Logic

Protect:
- Powerstone generators if spendability is high
- Artifact payoffs
- Activated ability sinks
- Colorless mana sinks
- Big artifact threats

Review:
- Powerstones if deck cannot spend colorless mana well
- Generic ramp that does not support artifact plan
- Artifact payoffs with low artifact count
- High-cost artifacts with low payoff

## Replacement Categories

- More artifact payoffs
- More activated ability sinks
- More artifact threats
- More card draw
- More colorless mana outlets
- Better ramp if Powerstones are unsupported

## Report Behavior

Include:
- “Powerstones are not normal ramp”
- “Spendability score”
- “Artifact/activated ability sink count”
- “Cards with cut pressure because Powerstone mana is unusable”

---

# 5.1.38 Incubate

## Definition

Incubate creates artifact tokens with +1/+1 counters that can transform into Phyrexian artifact creatures.

## Detection Signals

Increase Incubate score for:
- Incubate cards
- Incubator token payoff
- Artifact payoff
- +1/+1 counter support
- Proliferate
- Phyrexian support
- Sacrifice support
- Commander supports Incubate

## Primary Gate

```python
def can_be_primary_incubate(
    incubate_count,
    artifact_payoff_count,
    counter_or_phyrexian_payoff_count,
    commander_support
):
    return (
        commander_support
        and incubate_count >= 5
        and (artifact_payoff_count + counter_or_phyrexian_payoff_count) >= 2
    ) or (
        incubate_count >= 8
        and (artifact_payoff_count + counter_or_phyrexian_payoff_count) >= 3
    )
```

## Multi-Theme Rule

Incubate cards may count as:
- Artifact token support
- Counter support
- Phyrexian support
- Sacrifice fodder
- Token strategy
- Artifact creature typal

## Cut Logic

Protect:
- Incubate generators
- Artifact payoff
- Counter/proliferate support
- Phyrexian payoff
- Sacrifice outlets
- Token payoff

Review:
- Incubate cards with no artifact/counter payoff
- Payoffs with too few incubators
- Cards that require transforming tokens but do not support mana needs
- Off-plan Phyrexian cards if Incubate is primary

## Replacement Categories

- More Incubate
- More artifact payoff
- More counter/proliferate support
- More sacrifice outlets
- More Phyrexian payoff
- More card draw

## Report Behavior

Include:
- “Incubate supports artifacts, counters, tokens, and Phyrexians”
- “Transform cost considerations”
- “Payoff balance”
- “Protected multi-role cards”

---

# 5.1.39 Role Tokens

## Definition

Role tokens are Aura enchantment tokens that modify creatures and support enchantment, Aura, modified, constellation, and combat strategies.

## Detection Signals

Increase Role Token score for:
- Role token creation
- Aura payoff
- Enchantment payoff
- Constellation
- Modified creature payoff
- Eerie/enchantment ETB-style support
- Commander rewards Roles or enchanted creatures

## Primary Gate

```python
def can_be_primary_role_tokens(
    role_token_generator_count,
    aura_or_enchantment_payoff_count,
    modified_payoff_count,
    commander_support
):
    return (
        commander_support
        and role_token_generator_count >= 5
        and (aura_or_enchantment_payoff_count + modified_payoff_count) >= 2
    ) or (
        role_token_generator_count >= 8
        and (aura_or_enchantment_payoff_count + modified_payoff_count) >= 3
    )
```

## Multi-Role Rule

Role tokens count as:
- Auras
- Enchantments
- Enchantment tokens
- Modified support
- Constellation/enchantment ETB support
- Combat buffs

## Cut Logic

Protect:
- Role token makers
- Aura/enchantment payoff
- Constellation support
- Modified payoff
- Enchanted creature payoff
- Eriette/Ellivere-style engines

Review:
- Role cards without enchantment/Aura payoff
- Modified payoff with too few modified creatures
- Aura payoffs with low Aura/Role density
- Combat buffs if deck is not combat-oriented

## Replacement Categories

- More Role token makers
- More enchantment payoff
- More Aura payoff
- More modified payoff
- More protection
- More card draw

## Report Behavior

Include:
- “Role tokens count as Auras and enchantments”
- “Constellation/enchantment ETB overlap”
- “Modified support”
- “Cards protected because they create enchantment tokens”

---

# 5.1.40 Monarch

## Definition

Monarch creates a political card-advantage status that can be stolen through combat.

## Detection Signals

Increase Monarch score for:
- Monarch cards
- Monarch payoff
- Deathtouch blockers
- Pillowfort
- Rattlesnake defense
- Evasive creatures
- Goad
- Commander supports monarch or political combat

## Primary Gate

```python
def can_be_primary_monarch(
    monarch_count,
    monarch_payoff_count,
    crown_defense_count,
    commander_support
):
    return (
        commander_support
        and monarch_count >= 3
        and crown_defense_count >= 3
    ) or (
        monarch_count >= 5
        and monarch_payoff_count >= 2
        and crown_defense_count >= 4
    )
```

## Cut Logic

Protect:
- Monarch enablers
- Crown defense
- Deathtouch blockers
- Pillowfort
- Evasive creatures that reclaim monarch
- Political combat tools

Review:
- Monarch cards if deck cannot defend/reclaim crown
- Expensive monarch cards
- Defensive tools that do not help keep crown
- Monarch package if it helps opponents more

## Replacement Categories

- More crown defense
- More evasive creatures
- More pillowfort
- More deathtouch blockers
- More removal
- More card draw

## Report Behavior

Include:
- “Can the deck keep or reclaim monarch?”
- “Does monarch help opponents too much?”
- “Crown defense count”
- “Political combat implications”

---

# 5.1.41 Goad

## Definition

Goad forces creatures to attack and usually makes them attack someone other than the pilot.

## Detection Signals

Increase Goad score for:
- Goad cards
- Forced combat
- Attack elsewhere effects
- Opponent creature weaponization
- Combat politics
- Attack-trigger payoff
- Commander supports goad

## Primary Gate

```python
def can_be_primary_goad(
    goad_count,
    combat_payoff_count,
    defensive_support_count,
    commander_support
):
    return (
        commander_support
        and goad_count >= 4
        and (combat_payoff_count + defensive_support_count) >= 3
    ) or (
        goad_count >= 6
        and combat_payoff_count >= 3
    )
```

## Cut Logic

Protect:
- Repeatable goad
- Forced combat effects
- Attack elsewhere payoffs
- Defensive tools
- Combat payoff

Review:
- One-shot goad effects with no payoff
- Goad in creature-light metas
- Cards that cannot answer noncreature engines
- Combat-only cards without a way to close

## Replacement Categories

- More repeatable goad
- More defensive support
- More removal for noncreature threats
- More attack payoff
- More finishers
- More card draw

## Report Behavior

Include:
- “Creature-light pod weakness”
- “Does goad replace too much removal?”
- “How the deck closes after opponents fight”
- “Political combat support”

---

# 5.1.42 Ring Temptation

## Definition

Ring temptation decks repeatedly trigger “the Ring tempts you,” improving a Ring-bearer and supporting evasion, looting, legendary creatures, Wraiths/Nazgûl, sacrifice, and combat damage.

## Detection Signals

Increase Ring Temptation score for:
- Ring temptation triggers
- Ring-bearer payoff
- Legendary support
- Wraith/Nazgûl support
- Combat looting
- Evasive creatures
- Sacrifice/graveyard support from looting
- Commander rewards Ring temptation

## Primary Gate

```python
def can_be_primary_ring_temptation(
    ring_temptation_count,
    ring_payoff_count,
    commander_support
):
    return (
        commander_support
        and ring_temptation_count >= 5
        and ring_payoff_count >= 2
    ) or (
        ring_temptation_count >= 8
        and ring_payoff_count >= 3
    )
```

## Suppression Rules

Ring temptation is often a package, not a full archetype.

Suppress to secondary/minor if:
- Commander does not directly support it.
- Payoffs are low.
- It only appears incidentally on otherwise useful cards.

## Cut Logic

Protect:
- Repeated Ring temptation
- Ring-bearer payoff
- Wraith/Nazgûl support
- Looting/graveyard synergy
- Evasive Ring-bearers

Review:
- Ring temptation cards with no payoff
- Ring-bearer support without enough tempt triggers
- Legendary support with too few legends
- Combat cards that do not support Ring plan

## Replacement Categories

- More Ring temptation
- More Ring-bearer payoff
- More evasive creatures
- More legendary support
- More graveyard payoff
- More protection

## Report Behavior

Include:
- “Primary theme or package?”
- “Ring temptation count”
- “Ring-bearer payoff”
- “Linked Wraith/Nazgûl/legendary/graveyard themes”

---

# 5.1.43 Exile Matters / Cast from Exile

## Definition

These decks reward cards being exiled or cast from exile through impulse draw, Adventure, Foretell, Suspend, Plot, Cascade, Discover, Rebound, or commander exile effects.

## Detection Signals

Increase Exile Matters score for:
- Cast-from-exile effects
- Impulse draw
- Exile payoff
- Self-exile value
- Delayed casting
- Adventure/Foretell/Suspend
- Cascade/Discover
- Commander rewards exile casts

## Primary Gate

```python
def can_be_primary_exile_matters(
    exile_cast_count,
    exile_payoff_count,
    commander_support
):
    return (
        commander_support
        and exile_cast_count >= 4
        and exile_payoff_count >= 1
    ) or (
        exile_cast_count >= 7
        and exile_payoff_count >= 2
    )
```

## Subtype Separation

Separate:
- Self-exile value
- Opponent-exile theft
- Impulse draw
- Delayed casting
- Free-spell chains
- Topdeck exile/cast

## Cut Logic

Protect:
- Impulse draw
- Exile payoff
- Cast-from-exile triggers
- Treasure support in Prosper-style decks
- Token makers in Faldorn/Rocco-style decks

Review:
- Exile cards that cannot be cast reliably
- Payoffs with too few exile casts
- Generic draw if exile triggers matter more
- Exile theft cards if deck is self-exile value

## Replacement Categories

- More impulse draw
- More cast-from-exile payoff
- More mana smoothing
- More card selection
- More protection
- More theme-specific payoff

## Report Behavior

Include:
- “Self-exile or opponent-exile?”
- “Cast-from-exile count”
- “Exile payoff count”
- “Cards that trigger commander vs generic value”

---

# 5.1.44 Topdeck Matters

## Definition

Topdeck decks care about the top card of the library through casting from top, revealing for damage, manipulating the top card, or setting up cascade/discover/miracle.

## Detection Signals

Increase Topdeck score for:
- Topdeck manipulation
- Cast from top
- Reveal top for damage
- Library reveal payoff
- Miracle setup
- High-MV topdeck damage support
- Commander rewards topdeck
- Scry/surveil/fateseal style setup

## Primary Gate

```python
def can_be_primary_topdeck_matters(
    topdeck_payoff_count,
    topdeck_manipulation_count,
    commander_support
):
    return (
        commander_support
        and topdeck_payoff_count >= 2
        and topdeck_manipulation_count >= 5
    ) or (
        topdeck_payoff_count >= 3
        and topdeck_manipulation_count >= 8
    )
```

## Special Rule

High-MV cards may be intentional in:
- Yuriko
- Yennett
- Cascade setup
- Discover setup
- Miracle setup
- Topdeck damage shells

Do not automatically cut high-MV cards if topdeck payoff uses mana value.

## Cut Logic

Protect:
- Topdeck manipulation
- Cast-from-top enablers
- High-MV reveal payoff cards if relevant
- Miracle setup
- Scry/surveil support

Review:
- High-MV cards if topdeck payoff is absent
- Topdeck manipulation with no payoff
- Payoff cards with too little manipulation
- Cards that shuffle away stacked topdecks without benefit

## Replacement Categories

- More topdeck manipulation
- More topdeck payoff
- More card selection
- More shuffle control
- More protection
- More draw

## Report Behavior

Include:
- “Topdeck payoff type”
- “Manipulation count”
- “High-MV cards intentionally included?”
- “Bad topdeck cards under review”

---

# 5.1.45 Snow

## Definition

Snow decks use snow lands and snow permanents to enable special mana, removal, payoffs, untap engines, or snow creature combat.

## Detection Signals

Increase Snow score for:
- Snow land count
- Snow permanent count
- Snow payoff
- Snow mana requirements
- Snow untap effects
- Snow recursion
- Commander supports snow

## Primary Gate

```python
def can_be_primary_snow(
    snow_land_count,
    snow_payoff_count,
    snow_permanent_count,
    commander_support
):
    return (
        commander_support
        and snow_land_count >= 15
        and snow_payoff_count >= 2
    ) or (
        snow_land_count >= 20
        and snow_payoff_count >= 3
        and snow_permanent_count >= 5
    )
```

## Cut Logic

Protect:
- Snow lands
- Snow payoffs
- Snow mana support
- Snow untap engines
- Snow permanent density

Review:
- Non-snow basics if snow density matters
- Snow payoffs with too few snow sources
- Snow cards with no payoff
- Replacements that lower snow count too far

## Replacement Categories

- More snow lands
- More snow payoff
- More snow permanents
- More snow mana sinks
- More card draw
- More interaction

## Report Behavior

Include:
- “Snow land count”
- “Snow payoff count”
- “Replacement lands should preserve snow density”
- “Snow as mana-base theme”

---

# 5.1.46 Deserts

## Definition

Desert decks use Desert lands, land sacrifice, land recursion, token generation, and landfall-like triggers.

## Detection Signals

Increase Deserts score for:
- Desert land count
- Desert payoff
- Land recursion
- Land sacrifice
- Sand Warrior tokens
- Landfall
- Commander supports Deserts
- Graveyard land support

## Primary Gate

```python
def can_be_primary_deserts(
    desert_count,
    desert_payoff_count,
    land_recursion_count,
    commander_support
):
    return (
        commander_support
        and desert_count >= 8
        and desert_payoff_count >= 2
    ) or (
        desert_count >= 10
        and desert_payoff_count >= 2
        and land_recursion_count >= 2
    )
```

## Cut Logic

Protect:
- Deserts
- Desert payoff
- Land recursion
- Land sacrifice support
- Sand Warrior token makers
- Landfall support if linked

Review:
- Non-Desert tapped lands
- Desert payoffs with low Desert count
- Land-sacrifice cards without recursion
- Cards that reduce Desert density without improving mana/function

## Replacement Categories

- More Deserts
- More land recursion
- More Desert payoff
- More land tutors
- More token payoff
- Better fixing that preserves Desert density

## Report Behavior

Include:
- “Desert count”
- “Tapped land concern vs subtype value”
- “Land recursion”
- “Yuma/Hazezon-style payoff support”

---

# 5.1.47 Land Animation

## Definition

Land Animation decks turn lands into creatures temporarily or permanently and often combine landfall, counters, protection, and control.

## Detection Signals

Increase Land Animation score for:
- Animate land effects
- Creature-land payoff
- Land counter support
- Land protection
- Landfall
- Board wipe protection
- Commander animates lands
- Mass pump for animated lands

## Primary Gate

```python
def can_be_primary_land_animation(
    land_animation_count,
    animated_land_payoff_count,
    land_protection_count,
    commander_support
):
    return (
        commander_support
        and land_animation_count >= 5
        and animated_land_payoff_count >= 2
    ) or (
        land_animation_count >= 8
        and animated_land_payoff_count >= 3
        and land_protection_count >= 2
    )
```

## Cut Logic

Protect:
- Land animation effects
- Land protection
- Counter support for lands
- Landfall support
- Board wipe protection
- Finishers that pump animated lands

Review:
- Land animation without protection
- Payoffs with too few animated lands
- Creature board wipes that kill animated lands
- Lands that do not support the plan

## Replacement Categories

- More land protection
- More land animation
- More counter support
- More landfall
- More card draw
- More finishers

## Report Behavior

Include:
- “Animated land count”
- “Land protection”
- “Board wipe vulnerability”
- “Whether lands become win condition or value pieces”

---

# 5.1.48 Utility Lands Matter

## Definition

Utility Lands decks treat lands as repeatable spell-like resources: removal, draw, graveyard hate, sacrifice outlets, creature lands, combo pieces, or token engines.

## Detection Signals

Increase Utility Lands score for:
- Utility land count
- Land recursion
- Land tutors
- Land sacrifice
- Land toolbox
- Land untap support
- Commander rewards land use
- Field of the Dead/Dark Depths-style payoff

## Primary Gate

```python
def can_be_primary_utility_lands(
    utility_land_count,
    land_recursion_count,
    land_tutor_count,
    commander_support
):
    return (
        commander_support
        and utility_land_count >= 8
        and (land_recursion_count + land_tutor_count) >= 3
    ) or (
        utility_land_count >= 12
        and (land_recursion_count + land_tutor_count) >= 4
    )
```

## Cut Logic

Protect:
- Utility lands
- Land recursion
- Land tutors
- Lands that function as removal/draw/graveyard hate
- Land untap support
- Land sacrifice payoff

Review:
- Color-fixing lands that reduce utility too much
- Utility lands if color consistency suffers
- Land payoffs without enough utility lands
- Nonland spell versions if land toolbox is central

## Replacement Categories

- More land tutors
- More land recursion
- More utility lands
- More landfall payoff
- More color fixing
- More ways to play extra lands

## Report Behavior

Include:
- “Lands are spells in this deck”
- “Utility land count”
- “Color consistency risk”
- “Land recursion/tutor support”

---

# 5.1.49 Proliferate Poison

## Definition

Proliferate Poison gives opponents a few poison counters, then uses proliferate to increase them without repeated combat damage.

## Detection Signals

Increase Proliferate Poison score for:
- Poison enablers
- Proliferate
- Counter engines
- Control shell
- Poison payoff
- Commander supports proliferate
- Small poison sources

## Primary Gate

```python
def can_be_primary_proliferate_poison(
    poison_enabler_count,
    proliferate_count,
    poison_payoff_count,
    commander_support
):
    return (
        commander_support
        and poison_enabler_count >= 3
        and proliferate_count >= 5
    ) or (
        poison_enabler_count >= 4
        and proliferate_count >= 7
        and poison_payoff_count >= 2
    )
```

## Cut Logic

Protect:
- Small poison enablers
- Proliferate engines
- Counter-doubling/proliferate payoff
- Control pieces that buy time
- Poison payoff

Review:
- Poison creatures with no proliferate support
- Proliferate with no counters/poison
- Aggro poison cards in slow control shells
- Payoffs that do not support inevitability

## Replacement Categories

- More proliferate
- More poison enablers
- More control
- More card draw
- More protection
- More counter payoff

## Report Behavior

Include:
- “Poison by combat or poison by proliferate?”
- “Initial poison enabler count”
- “Proliferate density”
- “Inevitability engine”

---

# 5.1.50 Map Tokens / Explore

## Definition

Map tokens let creatures explore, which either draws lands or puts +1/+1 counters on creatures while filtering the top of the library.

## Detection Signals

Increase Map/Explore score for:
- Explore
- Map token generation
- +1/+1 counter payoff
- Topdeck filtering
- Land draw support
- Graveyard setup
- Merfolk explore support
- Commander rewards explore/maps

## Primary Gate

```python
def can_be_primary_map_explore(
    explore_count,
    map_token_count,
    counter_or_land_payoff_count,
    commander_support
):
    return (
        commander_support
        and (explore_count + map_token_count) >= 6
        and counter_or_land_payoff_count >= 2
    ) or (
        (explore_count + map_token_count) >= 9
        and counter_or_land_payoff_count >= 3
    )
```

## Cut Logic

Protect:
- Explore creatures
- Map token makers
- Counter payoff
- Landfall/land support
- Topdeck filtering synergy
- Graveyard setup if used

Review:
- Explore cards without counter/land payoff
- Map cards that are too slow
- Counter payoffs with too few counters
- Land support if explore count is low

## Replacement Categories

- More explore
- More Map token generation
- More counter payoff
- More landfall support
- More topdeck payoff
- More card draw

## Report Behavior

Include:
- “Explore as card selection, counter support, and land support”
- “Map token count”
- “Linked Merfolk/counter/land themes”
- “Payoff balance”

---

# 5.1.51 Constellation

## Definition

Constellation triggers when enchantments enter the battlefield. It overlaps with Enchantress but cares about ETB, not casting.

## Detection Signals

Increase Constellation score for:
- Constellation cards
- Enchantment ETB
- Enchantment token generation
- Role tokens
- Sagas
- Rooms
- Enchantment creatures
- Aura support
- Enchantment recursion
- Commander supports enchantment ETB

## Primary Gate

```python
def can_be_primary_constellation(
    enchantment_etb_count,
    constellation_payoff_count,
    enchantment_token_count,
    commander_support
):
    return (
        commander_support
        and enchantment_etb_count >= 8
        and constellation_payoff_count >= 2
    ) or (
        enchantment_etb_count >= 12
        and constellation_payoff_count >= 3
    ) or (
        enchantment_token_count >= 5
        and constellation_payoff_count >= 2
    )
```

## Distinction from Enchantress

Enchantress usually cares about casting enchantments.  
Constellation cares about enchantments entering the battlefield.

Cards that create enchantment tokens may support Constellation even if they are not enchantment spells.

## Cut Logic

Protect:
- Constellation payoffs
- Enchantment token makers
- Role token makers
- Sagas/Rooms/enchantment creatures
- Enchantment recursion
- Aura support if ETB matters

Review:
- Enchantress cast payoffs if deck mostly creates tokens
- Constellation payoffs with too few enchantments
- Auras if deck lacks creatures/protection
- Enchantment cards that do not trigger or support the engine

## Replacement Categories

- More enchantment ETB
- More constellation payoff
- More enchantment token makers
- More enchantment recursion
- More protection
- More card draw

## Report Behavior

Include:
- “Constellation cares about ETB, not just casting”
- “Enchantment token support”
- “Role/Saga/Room overlap”
- “Enchantress vs Constellation distinction”

---

# 5.1.52 Niche Theme Scoring Model

Use additive scoring before gates and suppression.

```yaml
score_inputs:
  commander_strongly_supports_theme:
    points: 5

  commander_lightly_supports_theme:
    points: 2

  theme_card:
    points: 1

  repeatable_enabler:
    points: 2

  payoff:
    points: 2

  narrow_but_necessary_density_piece:
    points: 1

  protection_for_fragile_theme:
    points: 1

  tutor_or_recursion_for_theme:
    points: 2

  clear_theme_win_condition:
    points: 3

  multi_role_bridge_card:
    points: 2

  mana_base_theme_piece:
    points: 2
```

Risk penalties:

```yaml
risk_penalties:
  payoff_without_enablers:
    points: -4

  enablers_without_payoff:
    points: -3

  one_shot_effect_in_repeatability_theme:
    points: -2

  mechanic_conflicts_with_primary_plan:
    points: -3

  theme_card_is_only_flavor:
    points: -2

  low_density_parasitic_mechanic:
    points: -4

  no_clear_win_condition:
    points: -5

  helps_opponents_more_than_pilot:
    points: -3

  bad_curve_or_resource_conflict:
    points: -2
```

Confidence bands:

```yaml
confidence:
  high:
    - passes_primary_gate
    - commander support moderate or strong
    - enabler/payoff balance is healthy
    - clear strategy shape
    - clear win condition

  medium:
    - passes secondary gate
    - some commander support or good density
    - payoff exists but execution may need support
    - theme supports primary plan

  low:
    - one or two theme cards
    - no commander support
    - payoff/enabler imbalance
    - unclear win condition
    - likely incidental package
```

---

# 5.1.53 Niche Report Behavior

When a niche theme is detected, include a dedicated section:

```markdown
## Niche Theme Read

Detected niche theme:
Role:
Confidence:
Commander support:
Theme density:
Enabler count:
Payoff count:
Generator/payoff balance:
Linked themes:
Main strategy shape:
Primary weakness:
Cards that support the niche theme:
Low-power cards that are actually important:
Cards that may be unsupported:
Possible cut candidates:
Cards I would protect from cuts:
Replacement categories:
```

The report should answer:

1. Is this niche theme commander-supported?
2. Is there enough density for it to matter?
3. Are there enough payoffs?
4. Are enablers and payoffs balanced?
5. Does the theme support the primary plan or distract from it?
6. Is the theme primary, secondary, minor, or manual review?
7. Are low-power cards actually necessary density pieces?
8. Are lands, tokens, counters, or card types part of the engine?
9. Does the mechanic require protection, recursion, or special mana support?
10. Does the theme have a clear win path?

---

# 5.1.54 Niche Warning Messages

Use warnings when appropriate.

## Unsupported Niche Warning

```markdown
Warning: This deck includes cards from a narrow theme, but the theme may not have enough support to function as a real package yet.
```

## Enabler/Payoff Imbalance Warning

```markdown
Warning: This theme has enablers and payoffs out of balance. Either the deck can generate the resource without enough payoff, or it has payoffs without enough ways to enable them.
```

## Parasitic Mechanic Warning

```markdown
Warning: This mechanic is parasitic. Cards from this theme become much weaker if the deck does not maintain enough generators and payoffs.
```

## Land Subtype Warning

```markdown
Warning: This is a land-subtype strategy. Replacing lands should preserve subtype density, recursion, or utility-land function when possible.
```

## Slow Engine Warning

```markdown
Warning: This niche theme can generate value, but it may need a clearer finisher or inevitability engine.
```

## Narrow but Supported Warning

```markdown
Note: This theme is narrow, but it appears supported. Do not treat its low-power enablers as generic filler without checking their role in the engine.
```

---

# 5.1.55 Final Section 5.1 Summary Rule

A niche theme is legitimate when the deck has:

```text
commander support + enough enablers + enough payoffs + execution support + a win path
```

The helper should not say:

```text
This card is weak because the theme is narrow.
```

The helper should say:

```text
This card is narrow, but it belongs if the deck has enough support for that niche mechanic.
```

A niche card should be protected from cuts when it:
- Enables a commander-supported niche mechanic
- Provides scarce support for a narrow theme
- Bridges multiple supported themes
- Supplies required density
- Fixes the theme’s known weakness
- Supports the deck’s mana base or token/counter/card-type engine
- Is part of the theme’s actual win path

A niche card should be reviewed as a possible cut when it:
- Appears without payoff support
- Is a payoff without enablers
- Conflicts with the primary plan
- Is only useful when already ahead
- Consumes resources needed by the main plan
- Is included for flavor but the user wants optimization
- Creates complexity without improving execution

The most important rule:

```text
Narrow does not mean bad.
Unsupported means bad.
```
