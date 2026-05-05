# Section 4: Typal / Tribal Themes Rules
Version: v0.5.6-ready
Purpose: Help the MTG Commander Deck Helper identify typal strategies, typal support cards, creature-type density, strategy shape, protected typal cards, off-plan cards, cut pressure, replacement categories, and report behavior.

Typal decks are built around one or more shared creature types. A strong typal deck is not merely a pile of creatures with the same type. It usually has a functional structure:

```text
typal_plan = creature_type_density + payoff_density + commander_support + strategy_shape + win_condition
```

Typal support is highly context-dependent. A card that looks weak by generic standards may be correct if it is:
- A lord
- A tribal tutor
- A cost reducer
- A token maker
- A recursion piece
- A payoff
- A changeling
- A density piece
- A combo piece
- A sacrifice body
- A typal enabler
- A multiple-copy exception card

The deck helper must avoid cutting low-raw-power typal cards if they are structurally important to the tribe’s plan.

---

# 4.1 Core Typal Philosophy

A typal deck should be evaluated through three layers:

1. Creature Type Identity
2. Typal Role Support
3. Typal Strategy Shape

The creature type tells the helper what the deck is built around.

The typal role tags explain why specific cards matter.

The strategy shape explains how the deck actually wins.

The helper should not stop at:

```text
This is a Dragon deck.
```

It should aim for:

```text
This is a Dragon Treasure Ramp deck because the commander and support package use Treasure, ramp, and cost reduction to deploy high-mana Dragons ahead of curve, then win through evasive combat and Dragon attack/ETB payoffs.
```

---

# 4.2 Typal Output Fields

For each detected typal theme, record:

```yaml
typal_strategy:
  creature_type:
  role: primary | secondary | minor_package | support_package | manual_review
  confidence: low | medium | high
  commander_support: none | light | moderate | strong
  creature_type_card_count:
  creature_type_token_maker_count:
  changeling_count:
  effective_typal_density:
  typal_payoff_count:
  typal_role_tags:
  strategy_shape:
  key_enablers:
  key_payoffs:
  protected_cards:
  possible_off_plan_cards:
  cut_pressure_notes:
  replacement_categories:
  report_notes:
```

---

# 4.3 Effective Typal Density

Typal density is not just the number of creature cards with the relevant type.

Effective typal density should include:

```yaml
effective_typal_density_sources:
  direct_creature_type_cards:
    description: Creature cards that naturally have the relevant type.

  token_makers:
    description: Cards that create tokens of the relevant creature type.

  changelings:
    description: Creatures with all creature types.

  type_granters:
    description: Cards that give creatures the relevant type.

  multiple_copy_exception_cards:
    description: Cards such as Rat Colony, Relentless Rats, Nazgûl, Shadowborn Apostle, Persistent Petitioners, Dragon's Approach, Hare Apparent, and similar exceptions.

  commander_created_tokens:
    description: Commander repeatedly creates relevant creature tokens.

  reanimation_or_recursion_of_type:
    description: Cards that repeatedly return relevant creatures.

  typal_tutors:
    description: Cards that find members of the tribe.
```

Suggested formula:

```python
effective_typal_density = (
    creature_type_card_count
    + creature_type_token_maker_count
    + changeling_count
    + type_granter_count
    + commander_created_token_bonus
    + multiple_copy_exception_bonus
)
```

Commander-created-token bonus should be meaningful because some decks are typal through token creation rather than creature-card count.

Examples:
- Soldier decks may have many Soldier token makers.
- Spirit decks may produce Spirit tokens repeatedly.
- Thopter decks may have few Thopter cards but many Thopter token makers.
- Amass decks may create or grow Army tokens.
- Goblin, Zombie, Squirrel, Saproling, Rabbit, Bat, and Faerie decks often rely heavily on tokens.

---

# 4.4 Typal Role Tags

Typal role tags are more important than raw creature type.

Use these tags when a card supports a tribe:

```yaml
typal_role_tags:
  typal_lord:
    description: Gives creatures of the type +1/+1, keywords, or combat bonuses.

  typal_cost_reducer:
    description: Reduces the cost of creatures or spells of the type.

  typal_token_maker:
    description: Creates tokens of the relevant creature type.

  typal_tutor:
    description: Searches for creatures or cards of the relevant type.

  typal_card_draw:
    description: Draws cards from casting, controlling, attacking with, or dealing damage with the relevant type.

  typal_recursion:
    description: Returns creatures of the relevant type from graveyard to hand or battlefield.

  typal_reanimation:
    description: Reanimates the relevant creature type.

  typal_sacrifice_payoff:
    description: Rewards sacrificing members of the tribe.

  typal_combat_payoff:
    description: Rewards attacking, dealing combat damage, or having a wide/tall board of the tribe.

  typal_counter_payoff:
    description: Places or rewards counters on the tribe.

  typal_lifegain_payoff:
    description: Rewards lifegain in a tribe tied to lifegain, such as Vampires, Clerics, Bats, Angels, Halflings, or Hobbits.

  typal_artifact_payoff:
    description: Supports artifact creature tribes such as Myr, Thopters, Constructs, Golems, Scarecrows, or artifact-creature swarms.

  typal_etb_payoff:
    description: Rewards creatures of the tribe entering the battlefield.

  typal_death_payoff:
    description: Rewards creatures of the tribe dying.

  typal_attack_trigger:
    description: Rewards members of the tribe attacking.

  typal_damage_trigger:
    description: Rewards the tribe dealing damage.

  typal_protection:
    description: Protects the tribe or gives the tribe resilience.

  typal_changeling_support:
    description: Changeling acts as typal glue, especially for low-density tribes.

  typal_multiple_copy_exception:
    description: Card has rules text allowing more than one copy in Commander or belongs to a known exception category.

  typal_density_piece:
    description: A low-power card included primarily to maintain tribe count.

  typal_cheat_effect:
    description: Puts tribal creatures into play without paying full mana cost.

  typal_cost_support:
    description: Ramp, cost reduction, or mana fixing specifically important to high-MV tribes.

  typal_payoff_artifact_or_enchantment:
    description: Noncreature permanent that rewards the tribe.

  typal_bridge_card:
    description: Card connects the tribe to a second strategy, such as Treasure, Lifegain, Equipment, Aristocrats, or Landfall.
```

---

# 4.5 Typal Strategy Shapes

The helper should always identify the tribe’s strategy shape.

```yaml
typal_strategy_shapes:
  typal_go_wide:
    description: Tribe creates many bodies and wins through anthems, mass pump, or combat triggers.

  typal_go_tall:
    description: Tribe builds one or a few large threats.

  typal_aristocrats:
    description: Tribe sacrifices its own bodies for drain, death triggers, recursion, or value.

  typal_reanimator:
    description: Tribe fills graveyard and returns members to battlefield.

  typal_tokens:
    description: Tribe is mostly created through token makers.

  typal_combo:
    description: Tribe assembles infinite or deterministic synergy lines.

  typal_treasure:
    description: Tribe uses Treasure for ramp, sacrifice, or payoff.

  typal_lifegain:
    description: Tribe gains or uses life as a resource.

  typal_spellslinger:
    description: Tribe supports or rewards casting instants, sorceries, or noncreature spells.

  typal_artifacts:
    description: Tribe is artifact-based or strongly artifact-supported.

  typal_landfall:
    description: Tribe connects to landfall, land recursion, or lands entering.

  typal_control:
    description: Tribe plays a control role through removal, taxes, counterspells, or tempo.

  typal_hatebears:
    description: Tribe disrupts opponents with small bodies.

  typal_equipment:
    description: Tribe uses Equipment as a central combat or draw engine.

  typal_counters:
    description: Tribe grows through +1/+1 counters or other counter synergies.

  typal_graveyard:
    description: Tribe uses self-mill, recursion, graveyard casting, or death triggers.

  typal_big_mana:
    description: Tribe needs ramp or mana engines to cast large creatures.

  typal_tempo:
    description: Tribe uses cheap threats, evasion, and interaction.

  typal_saboteur:
    description: Tribe rewards combat damage to players.

  typal_pillowfort:
    description: Tribe protects itself behind defenses while building advantage.

  typal_goodstuff:
    description: Tribe uses strong individual cards of the type more than deep synergy.

  keyword_typal:
    description: Deck functions like typal through a shared keyword, such as Flying or Deathtouch, rather than a creature type.
```

---

# 4.6 General Typal Primary Gate

A typal theme should not become primary just because several creatures share a type.

Use the general gate:

```python
def can_be_primary_typal(
    creature_type_count,
    typal_payoff_count,
    commander_typal_support
):
    return (
        creature_type_count >= 18
        and typal_payoff_count >= 4
    ) or (
        commander_typal_support
        and creature_type_count >= 12
        and typal_payoff_count >= 3
    )
```

If this gate fails, classify as:
- Secondary typal
- Minor typal package
- Incidental creature type overlap
- Manual review

---

# 4.7 Token-Based Typal Gate

Use this gate for tribes that commonly exist through tokens:

- Spirits
- Soldiers
- Zombies
- Goblins
- Saprolings
- Thopters
- Bats
- Rabbits
- Squirrels
- Faeries
- Insects
- Citizens
- Plants
- Orcs/Armies
- Drakes
- Flying token decks

```python
def can_be_primary_token_typal(
    creature_type_card_count,
    token_maker_count,
    typal_payoff_count,
    commander_typal_support
):
    return (
        commander_typal_support
        and (creature_type_card_count + token_maker_count) >= 14
        and typal_payoff_count >= 3
    ) or (
        (creature_type_card_count + token_maker_count) >= 18
        and typal_payoff_count >= 4
    )
```

Token makers that create the relevant type should count heavily.

Do not mark token makers as off-plan simply because they are not creature cards.

---

# 4.8 High-MV Typal Gate

Use this gate for tribes with naturally high mana value:

- Dragons
- Angels
- Demons
- Eldrazi
- Dinosaurs
- Giants
- Sea Monsters
- Elder Dragons
- Hydras if built as X-creature big mana
- Treefolk if high-curve toughness-based

```python
def can_be_primary_high_mv_typal(
    creature_type_count,
    ramp_count,
    cost_reducer_count,
    cheat_count,
    typal_payoff_count,
    commander_typal_support
):
    return (
        creature_type_count >= 12
        and typal_payoff_count >= 3
        and (ramp_count + cost_reducer_count + cheat_count) >= 8
        and commander_typal_support
    )
```

High-MV typal decks require a different cut lens.

Do not automatically cut expensive tribal creatures if:
- The deck has enough ramp.
- The commander cheats them into play.
- The deck has cost reducers.
- The creature has strong ETB, attack, cast, or death triggers.
- The tribe naturally operates at high mana value.

---

# 4.9 Multiple-Copy Exception Gate

Some Commander decks legally use multiple copies of certain cards because the cards explicitly permit it.

Use this logic:

```python
def has_multiple_copy_typal_exception(card):
    return (
        card.allows_multiple_copies
        or card.name in {
            "Rat Colony",
            "Relentless Rats",
            "Nazgûl",
            "Shadowborn Apostle",
            "Persistent Petitioners",
            "Dragon's Approach",
            "Hare Apparent"
        }
    )
```

These cards should be treated as:
- Legal multiple-copy exceptions
- Density engines
- Typal plan enablers
- Protected from normal singleton violation flags

If the deck includes these cards, report:
- Number of copies
- Whether the deck has payoff support
- Whether the exception card is the actual deck plan
- Whether the commander supports the exception plan

---

# 4.10 Changeling Rules

Changelings have every creature type and can support any tribe.

## Count Changelings When

Count changelings as typal density if:
- Tribe density is low or medium.
- Commander rewards the tribe.
- Deck contains multiple tribal payoffs.
- Tribe is niche or under-supported.
- Changelings enable multiple tribal payoffs.
- Changelings are needed for Reaper King, Morophon, Slivers, Party, Allies, or low-density typal shells.

## Increase Cut Pressure on Changelings When

Increase changeling cut pressure if:
- The tribe already has high density.
- The changeling has no other relevant role.
- The changeling is low impact.
- It does not support the actual strategy shape.
- It only exists as filler.

## Report Behavior

When changelings matter, include:

```markdown
Changelings appear to be functioning as typal glue. They should not be judged only by raw stats because they help maintain creature-type density and turn on tribal payoffs.
```

---

# 4.11 Typal Goodstuff Rules

Typal Goodstuff decks use a popular tribe but rely more on strong individual cards than tight synergy.

Common examples:
- Dragon Goodstuff
- Vampire Midrange
- Angel Midrange
- Demon Goodstuff
- Dinosaur Stompy
- Phyrexian Goodstuff
- Human Goodstuff
- Legendary tribal shells

## Detection Signals

Increase Typal Goodstuff score when:
- Tribe count is medium or high.
- Payoff count is low to medium.
- Cards are individually strong.
- Commander supports the type but not a narrow strategy.
- Deck has fewer synergy bridges.
- Deck lacks strong recursion/combo/token/counter/sacrifice identity.

## Suppression

Do not call something Typal Goodstuff if a stronger shape exists:
- Dragon Treasure Ramp
- Vampire Aristocrats
- Zombie Reanimator
- Goblin Tokens
- Elf Ball
- Knight Equipment
- Wizard ETB Combo
- Dinosaur Discover
- Spirit Tokens
- Sliver Combo

## Cut Logic

Protect:
- Strong tribe members
- Broad tribal payoffs
- Ramp/fixing
- Commander support

Review:
- Off-type cards with no support role
- Expensive tribe members with no impact
- Weak lords with low density
- Generic goodstuff that does not support tribe or role balance

## Replacement Categories

- More tribal payoff
- More ramp/fixing
- More card draw
- More interaction
- More strategy-defining support

---

# 4.12 General Typal Cut Rules

## Do Not Automatically Cut

Do not automatically cut:

- Low-stat creatures needed for tribal density
- Lords
- Cost reducers
- Tribal tutors
- Tribal token makers
- Tribal recursion
- Changelings in low-density tribes
- On-type sacrifice fodder in aristocrats typal decks
- On-type evasive one-drops in saboteur typal decks
- On-type mana dorks in Elf/Druid decks
- Expensive creatures in high-MV tribes if ramp, cheat, or cost reduction exists
- Token makers that create the relevant creature type
- Tribal payoff artifacts/enchantments
- Multiple-copy exception cards
- Utility creatures with the relevant type
- Cards that bridge the tribe into the deck’s strategy shape

## Increase Cut Pressure

Increase cut pressure on:

- Off-type creatures with no role synergy
- Generic goodstuff that does not support the tribe’s plan
- Tribal payoff cards with too little tribe density
- Lords for creature types with low representation
- Expensive tribal cards without ramp, cheat, or cost reduction
- Narrow tribal cards that only work when already ahead
- Token makers that create the wrong creature type
- Changelings when density is already high and the changeling has no other role
- Combat-only lords in noncombat tribal decks
- Graveyard tribal payoffs in typal decks without self-mill, sacrifice, discard, or recursion
- Equipment in typal decks with no Equipment strategy
- Lifegain payoffs in tribes without lifegain triggers
- Treasure payoffs in tribes with little Treasure production
- Type-specific cards for an incidental creature type

---

# 4.13 Typal Replacement Logic

Replacement suggestions should usually be category-based unless the user asks for exact cards or a collection database is available.

Common typal replacement categories:

```yaml
typal_replacement_categories:
  general_typal:
    - More tribal payoff
    - More on-type creatures
    - More card draw
    - More protection
    - More removal
    - Better mana fixing

  go_wide_typal:
    - More token makers
    - More anthem effects
    - More board protection
    - More mass pump finishers
    - More haste

  go_tall_typal:
    - More protection
    - More evasion
    - More counters
    - More Equipment or Auras
    - More commander support

  aristocrats_typal:
    - More sacrifice outlets
    - More death payoffs
    - More token makers
    - More recursion
    - More drain effects

  reanimator_typal:
    - More discard outlets
    - More self-mill
    - More reanimation
    - Better reanimation targets
    - More graveyard protection

  high_mv_typal:
    - More ramp
    - More cost reduction
    - More cheat effects
    - More card draw
    - More mana fixing

  typal_treasure:
    - More Treasure generation
    - More artifact payoff
    - More mana sinks
    - More sacrifice payoff
    - More card draw

  typal_lifegain:
    - More repeatable lifegain
    - More lifegain payoff
    - More lifedrain
    - More protection
    - More card draw

  typal_equipment:
    - More efficient Equipment
    - More equip cost reduction
    - More protection
    - More Equipment-based card draw
    - More evasion

  typal_spellslinger:
    - More cheap spells
    - More spell payoff
    - More card selection
    - More protection
    - More cost reduction

  typal_artifacts:
    - More artifact creatures
    - More artifact payoff
    - More artifact recursion
    - More token artifacts
    - More sacrifice outlets

  typal_counters:
    - More counter enablers
    - More counter payoff
    - More proliferate
    - More evasion
    - More protection

  typal_control:
    - More interaction
    - More card draw
    - More board wipes
    - More finishers
    - More protection

  typal_saboteur:
    - More cheap evasive creatures
    - More combat damage payoff
    - More topdeck manipulation
    - More protection
    - More tempo interaction
```

---

# 4.14 Elf Typal

## Definition

Elf decks combine mana dorks, creature ramp, token production, lords, card draw, and Overrun-style finishers.

## Detection Signals

Increase Elf Typal score for:
- Elf creature density
- Elf mana dorks
- Elf lords
- Elf token makers
- Elf card draw
- Untap effects
- Overrun finishers
- Commander rewards Elves
- Elf-specific drain or combat payoff

## Primary Gate

```python
def can_be_primary_elf_typal(role_counts, creature_type_counts, commander_tags):
    return (
        creature_type_counts["elf"] >= 18
        and (
            role_counts["typal_payoff"] >= 4
            or role_counts["elf_mana_dork"] >= 6
        )
        and (
            "elf_typal" in commander_tags
            or role_counts["elf_lord"] >= 2
            or role_counts["elf_token_maker"] >= 2
        )
    )
```

## Suppression Rules

Do not call a deck Elf Typal just because it has a few Elf mana dorks.

If Elf count is low and the Elves are mostly mana dorks, classify as:
- Creature ramp package
- Mana dork package
- Druid/Elf support
- Manual review

## Cut Logic

Protect:
- Elf mana dorks
- Elf lords
- Elf card draw
- Elf token makers
- Overrun effects
- Lathril-style tap/drain support
- Marwyn-style mana scaling pieces

Review:
- Non-Elf creatures with no role synergy
- Expensive cards that do not convert Elf mana into wins
- Generic ramp that is weaker than Elf-based ramp
- Elf payoffs with insufficient Elf density

## Replacement Categories

- More Elf mana dorks
- More Elf payoff
- More card draw
- More Overrun finishers
- More protection
- More untap support

---

# 4.15 Goblin Typal

## Definition

Goblin decks are explosive token/combat/sacrifice decks that often blend go-wide combat, aristocrats, damage triggers, and combo.

## Detection Signals

Increase Goblin Typal score for:
- Goblin creature density
- Goblin token makers
- Goblin lords
- Sacrifice outlets
- Impact Tremors-style damage
- Goblin tutors
- Goblin death payoffs
- Commander creates or rewards Goblins

## Primary Gate

```python
def can_be_primary_goblin_typal(role_counts, creature_type_counts, commander_tags):
    return (
        (
            creature_type_counts["goblin"] + role_counts["goblin_token_maker"]
        ) >= 16
        and role_counts["typal_payoff"] >= 3
        and (
            "goblin_typal" in commander_tags
            or role_counts["goblin_lord"] >= 2
            or role_counts["goblin_sacrifice_payoff"] >= 2
        )
    )
```

## Strategy Shapes

Common shapes:
- Goblin Go-Wide Tokens
- Goblin Aristocrats
- Goblin Combo
- Goblin Treasure/Artifacts
- Goblin Aggro

## Cut Logic

Protect:
- Goblin token makers
- Goblin lords
- Sacrifice outlets
- Goblin tutors
- Death/damage payoffs
- Low-power Goblins if commander scales with Goblin count

Review:
- Non-Goblin creatures with no sacrifice/combat role
- Expensive Goblins without payoff
- Token makers that do not create Goblins unless they support sacrifice
- Goblin payoffs with low Goblin density

## Replacement Categories

- More Goblin token makers
- More sacrifice outlets
- More death payoffs
- More lords
- More haste
- More card draw

---

# 4.16 Dragon Typal

## Definition

Dragon decks ramp into large flying threats and use cost reduction, Treasure, attack triggers, ETB triggers, and tribal payoffs.

## Detection Signals

Increase Dragon Typal score for:
- Dragon creature density
- Dragon cost reducers
- Treasure generation
- Dragon tutors
- Dragon attack triggers
- Dragon ETB triggers
- Dragon token copies
- Commander cheats or rewards Dragons
- Five-color Dragon support

## Primary Gate

```python
def can_be_primary_dragon_typal(
    creature_type_counts,
    role_counts,
    commander_tags
):
    return (
        creature_type_counts["dragon"] >= 12
        and role_counts["typal_payoff"] >= 3
        and (
            role_counts["ramp"]
            + role_counts["cost_reducer"]
            + role_counts["treasure_maker"]
            + role_counts["cheat_effect"]
        ) >= 8
        and (
            "dragon_typal" in commander_tags
            or role_counts["dragon_payoff"] >= 3
        )
    )
```

## Strategy Shapes

Common shapes:
- Dragon Treasure Ramp
- Dragon Goodstuff
- Dragon Combat
- Dragon Combo
- Dragonstorm/Tiamat Tutor Chain
- Dragon Reanimator

## Suppression Rules

Do not mark Treasure as off-plan if it helps cast expensive Dragons.

Do not overcut high-mana Dragons if the deck has:
- Ramp
- Treasure
- Cost reduction
- Cheat effects
- Reanimation
- Commander support

## Cut Logic

Protect:
- Dragon cost reducers
- Treasure makers
- Dragon tutors
- Dragon attack/ETB payoffs
- High-impact Dragons
- Cheat/reanimation effects

Review:
- Expensive Dragons with no immediate impact
- Off-type creatures with no ramp/support role
- Dragon payoffs with too few Dragons
- Big-mana cards that do not support Dragons

## Replacement Categories

- More ramp
- More Treasure generation
- More cost reduction
- More Dragon payoff
- More card draw
- More mana fixing

---

# 4.17 Zombie Typal

## Definition

Zombie decks are graveyard-centric, recursive, and attrition-based. They often combine tokens, lords, sacrifice, reanimation, self-mill, and death triggers.

## Detection Signals

Increase Zombie Typal score for:
- Zombie creature density
- Zombie token makers
- Zombie lords
- Zombie recursion
- Self-mill
- Sacrifice outlets
- Death triggers
- Decayed token production
- Commander rewards Zombies

## Primary Gate

```python
def can_be_primary_zombie_typal(role_counts, creature_type_counts, commander_tags):
    return (
        (
            creature_type_counts["zombie"]
            + role_counts["zombie_token_maker"]
            + role_counts["decayed_token_maker"]
        ) >= 16
        and role_counts["typal_payoff"] >= 3
        and (
            "zombie_typal" in commander_tags
            or role_counts["zombie_recursion"] >= 2
            or role_counts["zombie_lord"] >= 2
        )
    )
```

## Strategy Shapes

Common shapes:
- Zombie Aristocrats
- Zombie Reanimator
- Zombie Tokens
- Zombie Graveyard Value
- Zombie Swarm

## Cut Logic

Protect:
- Zombie recursion
- Zombie token makers
- Decayed token makers
- Sacrifice outlets
- Death payoffs
- Lords
- Self-mill if recursion exists

Review:
- Zombies with no recursion, sacrifice, or payoff
- Graveyard payoffs without setup
- Non-Zombie creatures with no graveyard role
- Expensive Zombies without impact

## Replacement Categories

- More Zombie token makers
- More recursion
- More sacrifice outlets
- More death payoffs
- More self-mill
- More lords

---

# 4.18 Sliver Typal

## Definition

Slivers share abilities across the board, creating a hive-style combat or combo engine.

## Detection Signals

Increase Sliver Typal score for:
- High Sliver density
- Mana Slivers
- Keyword Slivers
- Sliver tutors
- Sliver protection
- Sliver combo pieces
- Five-color fixing
- Commander rewards Slivers

## Primary Gate

```python
def can_be_primary_sliver_typal(role_counts, creature_type_counts, commander_tags):
    return (
        creature_type_counts["sliver"] >= 22
        and role_counts["sliver_payoff"] >= 4
        and (
            "sliver_typal" in commander_tags
            or role_counts["sliver_tutor"] >= 1
        )
    )
```

## Strategy Shapes

Common shapes:
- Sliver Go-Wide Combat
- Sliver Combo
- Sliver Cascade
- Sliver Goodstuff
- Sliver Tutor Chain

## Cut Logic

Protect:
- Mana Slivers
- Sliver tutors
- Protection Slivers
- Keyword Slivers
- Combo Slivers
- Five-color fixing

Review:
- Generic non-Sliver goodstuff
- Slivers that add redundant weak keywords
- High-MV Slivers without strong effect
- Cards that do not protect, fix, or advance the hive

## Replacement Categories

- More Sliver density
- More mana fixing
- More protection
- More Sliver tutors
- More finishers
- More combo support if intended

---

# 4.19 Merfolk Typal

## Definition

Merfolk decks combine lords, evasion, +1/+1 counters, tapping/untapping, card draw, tempo, and explore value.

## Detection Signals

Increase Merfolk Typal score for:
- Merfolk density
- Merfolk lords
- Islandwalk/evasion
- +1/+1 counters
- Explore
- Tap/untap Merfolk engines
- Commander rewards Merfolk

## Primary Gate

```python
def can_be_primary_merfolk_typal(role_counts, creature_type_counts, commander_tags):
    return (
        creature_type_counts["merfolk"] >= 16
        and role_counts["typal_payoff"] >= 3
        and (
            "merfolk_typal" in commander_tags
            or role_counts["merfolk_lord"] >= 2
            or role_counts["explore"] >= 3
            or role_counts["tap_untap_synergy"] >= 3
        )
    )
```

## Strategy Shapes

Common shapes:
- Merfolk Evasive Combat
- Merfolk Counters
- Merfolk Explore
- Merfolk Tap/Untap
- Merfolk Tempo

## Cut Logic

Protect:
- Merfolk lords
- Explore Merfolk
- Tap/untap enablers
- Evasive Merfolk
- Counter payoffs

Review:
- Generic creatures that do not support tempo/counters
- Merfolk payoffs with low density
- Slow cards that do not support combat or value
- Off-plan goodstuff

## Replacement Categories

- More Merfolk density
- More lords
- More counter synergy
- More evasion
- More card draw
- More tempo interaction

---

# 4.20 Vampire Typal

## Definition

Vampire decks blend lifegain, lifedrain, tokens, aristocrats, combat, Blood tokens, and reanimation.

## Detection Signals

Increase Vampire Typal score for:
- Vampire density
- Vampire token makers
- Vampire lords
- Lifegain/lifedrain
- Blood token creation
- Sacrifice/death payoffs
- Reanimation
- Commander rewards Vampires

## Primary Gate

```python
def can_be_primary_vampire_typal(role_counts, creature_type_counts, commander_tags):
    return (
        (
            creature_type_counts["vampire"]
            + role_counts["vampire_token_maker"]
        ) >= 16
        and role_counts["typal_payoff"] >= 3
        and (
            "vampire_typal" in commander_tags
            or role_counts["vampire_lord"] >= 2
            or role_counts["blood_token_maker"] >= 3
            or role_counts["lifedrain"] >= 3
        )
    )
```

## Strategy Shapes

Common shapes:
- Vampire Tokens
- Vampire Aristocrats
- Vampire Lifedrain
- Vampire Blood Tokens
- Vampire Reanimator
- Vampire Midrange

## Cut Logic

Protect:
- Vampire token makers
- Blood token enablers in Blood shells
- Lifegain/lifedrain payoffs
- Vampire lords
- Sacrifice outlets
- Reanimation pieces

Review:
- Non-Vampire creatures with no support role
- Lifegain cards with no payoff
- Blood cards without Blood payoff
- Expensive Vampires without impact
- Combat-only cards in aristocrats builds

## Replacement Categories

- More Vampire token makers
- More lifedrain payoff
- More Blood token support
- More sacrifice outlets
- More lords
- More card draw

---

# 4.21 Human Typal

## Definition

Human decks are flexible and can be go-wide combat, counters, hatebears, sacrifice, tokens, legends, or party-adjacent.

## Detection Signals

Increase Human Typal score for:
- Human density
- Human token makers
- Human lords
- Counters
- Hatebears
- Sacrifice support
- Commander rewards Humans
- Human mana engines

## Primary Gate

```python
def can_be_primary_human_typal(role_counts, creature_type_counts, commander_tags):
    return (
        creature_type_counts["human"] >= 20
        and role_counts["typal_payoff"] >= 4
        and (
            "human_typal" in commander_tags
            or role_counts["human_lord"] >= 2
            or role_counts["human_token_maker"] >= 2
            or role_counts["hatebear"] >= 4
        )
    )
```

## Suppression Rules

Humans are common incidental creature types.

Do not call a deck Human Typal if:
- Humans are mostly random utility creatures.
- There are few Human-specific payoffs.
- Commander does not care about Humans.
- Strategy is better described as Hatebears, Tokens, Counters, or Legends.

## Cut Logic

Protect:
- Human lords
- Human token makers
- Human hatebears
- Human mana engines
- Human counter payoffs

Review:
- Incidental Humans with no role synergy
- Human payoff cards with low actual Human density
- Off-type cards with no role support
- Weak combat pieces in noncombat Human builds

## Replacement Categories

- More Human payoff
- More role-specific Humans
- More token makers
- More counters
- More hatebears
- More card draw

---

# 4.22 Eldrazi Typal

## Definition

Eldrazi decks ramp into enormous colorless threats with cast triggers, annihilator-style pressure, exile effects, and high-impact combat.

## Detection Signals

Increase Eldrazi Typal score for:
- Eldrazi density
- Colorless ramp
- Colorless lands
- Eldrazi cost reduction
- Eldrazi cast triggers
- Annihilator/combat pressure
- Commander rewards colorless spells or Eldrazi
- Copy cast triggers

## Primary Gate

```python
def can_be_primary_eldrazi_typal(role_counts, creature_type_counts, commander_tags):
    return (
        creature_type_counts["eldrazi"] >= 10
        and role_counts["typal_payoff"] >= 3
        and (
            role_counts["colorless_ramp"]
            + role_counts["cost_reducer"]
            + role_counts["colorless_land_support"]
        ) >= 8
        and (
            "eldrazi_typal" in commander_tags
            or role_counts["eldrazi_cast_trigger_payoff"] >= 2
        )
    )
```

## Special Mana Rule

Eldrazi decks require unusual mana analysis.

Evaluate:
- Colorless source count
- Artifact ramp
- Eldrazi lands
- Cost reducers
- High-MV payoff count
- Whether the commander requires true colorless mana

## Cut Logic

Protect:
- Colorless ramp
- Colorless lands
- Eldrazi cost reducers
- Cast-trigger payoffs
- High-impact Eldrazi
- Copy cast-trigger support

Review:
- Colored cards that hurt colorless consistency
- Cheat effects if deck cares specifically about cast triggers
- High-MV Eldrazi without cast/attack impact
- Ramp that does not produce needed colorless mana

## Replacement Categories

- More colorless ramp
- More colorless sources
- More cost reduction
- More cast-trigger payoff
- More card draw
- More interaction

---

# 4.23 Dinosaur Typal

## Definition

Dinosaur decks use large creatures, ramp, cost reduction, discover, enrage triggers, and combat damage.

## Detection Signals

Increase Dinosaur Typal score for:
- Dinosaur density
- Dinosaur cost reduction
- Ramp
- Enrage
- Discover
- Fight/ping effects
- Big combat payoffs
- Commander rewards Dinosaurs

## Primary Gate

```python
def can_be_primary_dinosaur_typal(role_counts, creature_type_counts, commander_tags):
    return (
        creature_type_counts["dinosaur"] >= 12
        and role_counts["typal_payoff"] >= 3
        and (
            role_counts["ramp"]
            + role_counts["cost_reducer"]
            + role_counts["cheat_effect"]
            + role_counts["discover"]
        ) >= 7
        and (
            "dinosaur_typal" in commander_tags
            or role_counts["enrage"] >= 2
            or role_counts["discover"] >= 2
        )
    )
```

## Strategy Shapes

Common shapes:
- Dinosaur Stompy
- Dinosaur Discover
- Dinosaur Enrage
- Dinosaur Big Mana
- Dinosaur Combat

## Cut Logic

Protect:
- Ramp
- Cost reducers
- Discover support
- Enrage enablers
- Pingers/fight cards in Enrage builds
- High-impact Dinosaurs

Review:
- High-MV Dinosaurs without support
- Enrage cards without damage enablers
- Generic combat cards that do not support Dinosaurs
- Off-type creatures with no ramp/support role

## Replacement Categories

- More ramp
- More cost reduction
- More Dinosaurs
- More discover payoff
- More enrage enablers
- More card draw

---

# 4.24 Spirit Typal

## Definition

Spirit decks often use flying creatures, tokens, death triggers, enchantment synergies, exile/cast-from-exile, and tempo.

## Detection Signals

Increase Spirit Typal score for:
- Spirit density
- Spirit token makers
- Flying token support
- Spirit lords
- Death triggers
- Exile/cast-from-exile support
- Enchantment support
- Commander rewards Spirits

## Primary Gate

```python
def can_be_primary_spirit_typal(role_counts, creature_type_counts, commander_tags):
    return (
        (
            creature_type_counts["spirit"]
            + role_counts["spirit_token_maker"]
        ) >= 15
        and role_counts["typal_payoff"] >= 3
        and (
            "spirit_typal" in commander_tags
            or role_counts["spirit_lord"] >= 2
            or role_counts["flying_token_payoff"] >= 2
        )
    )
```

## Cut Logic

Protect:
- Spirit token makers
- Flying token payoffs
- Spirit lords
- Death-trigger support
- Exile support if commander cares
- Enchantment synergy if Spirit/enchantment hybrid

Review:
- Non-Spirit flyers with no payoff
- Spirit payoffs with low Spirit density
- Token makers that do not support flying or Spirits
- Combat-only cards in sacrifice/control builds

## Replacement Categories

- More Spirit token makers
- More flying payoff
- More lords
- More protection
- More card draw
- More tempo interaction

---

# 4.25 Angel Typal

## Definition

Angel decks use expensive flying creatures, lifegain, protection, recursion, and combat dominance.

## Detection Signals

Increase Angel Typal score for:
- Angel density
- Angel cost reduction
- Ramp
- Lifegain
- Flying combat
- Angel lords
- Protection
- Cheat-into-play effects
- Commander rewards Angels

## Primary Gate

```python
def can_be_primary_angel_typal(role_counts, creature_type_counts, commander_tags):
    return (
        creature_type_counts["angel"] >= 10
        and role_counts["typal_payoff"] >= 3
        and (
            role_counts["ramp"]
            + role_counts["cost_reducer"]
            + role_counts["cheat_effect"]
        ) >= 6
        and (
            "angel_typal" in commander_tags
            or role_counts["angel_lord"] >= 1
            or role_counts["lifegain_payoff"] >= 2
        )
    )
```

## Cut Logic

Protect:
- Angel cost reducers
- Lifegain payoffs
- Flying combat payoffs
- Protection
- Board wipes that the deck can recover from
- High-impact Angels

Review:
- Expensive Angels without impact
- Lifegain-only cards with no payoff
- Non-Angel creatures with no ramp/protection role
- Angel payoffs with low Angel count

## Replacement Categories

- More ramp
- More cost reduction
- More lifegain payoff
- More protection
- More card draw
- More removal

---

# 4.26 Demon Typal

## Definition

Demon decks use large black creatures with powerful effects and drawbacks, often overlapping with sacrifice, life payment, reanimation, and aristocrats.

## Detection Signals

Increase Demon Typal score for:
- Demon density
- Demon payoff
- Life payment
- Sacrifice support
- Reanimation
- Cost reduction
- Commander rewards Demons
- Large evasive threats

## Primary Gate

```python
def can_be_primary_demon_typal(role_counts, creature_type_counts, commander_tags):
    return (
        creature_type_counts["demon"] >= 9
        and role_counts["typal_payoff"] >= 3
        and (
            role_counts["reanimation"]
            + role_counts["sacrifice_outlet"]
            + role_counts["cost_reducer"]
            + role_counts["ramp"]
        ) >= 5
        and (
            "demon_typal" in commander_tags
            or role_counts["demon_payoff"] >= 2
        )
    )
```

## Cut Logic

Protect:
- Demon payoffs
- Reanimation
- Sacrifice outlets
- Life-payment payoff
- High-impact Demons

Review:
- Demons with severe drawbacks and low payoff
- Expensive Demons with no ETB/attack/value
- Demon typal cards with low Demon density
- Generic black goodstuff not supporting plan

## Replacement Categories

- More reanimation
- More sacrifice support
- More ramp
- More card draw
- More Demon payoff
- More life management

---

# 4.27 Knight Typal

## Definition

Knight decks use combat-focused creatures, Equipment, tokens, anthems, lifelink, and recursion.

## Detection Signals

Increase Knight Typal score for:
- Knight density
- Knight lords
- Equipment support
- Knight token makers
- Recursion
- Lifelink
- Commander rewards Knights
- Attack triggers

## Primary Gate

```python
def can_be_primary_knight_typal(role_counts, creature_type_counts, commander_tags):
    return (
        (
            creature_type_counts["knight"]
            + role_counts["knight_token_maker"]
        ) >= 15
        and role_counts["typal_payoff"] >= 3
        and (
            "knight_typal" in commander_tags
            or role_counts["equipment_synergy"] >= 3
            or role_counts["knight_lord"] >= 2
        )
    )
```

## Strategy Shapes

Common shapes:
- Knight Equipment
- Knight Go-Wide
- Knight Reanimator
- Knight Combat
- Knight Lifegain

## Cut Logic

Protect:
- Equipment in Syr Gwyn-style builds
- Knight lords
- Knight recursion
- Knight token makers
- Lifelink/combat payoff

Review:
- Equipment without enough carriers
- Non-Knight creatures with no Equipment or recursion role
- Combat-only cards in recursion builds
- Expensive Knights without impact

## Replacement Categories

- More Knight density
- More Equipment support
- More lords
- More recursion
- More protection
- More card draw

---

# 4.28 Soldier Typal

## Definition

Soldier decks are usually go-wide white-based combat decks with tokens, anthems, attack triggers, and sometimes tap/untap synergies.

## Detection Signals

Increase Soldier Typal score for:
- Soldier density
- Soldier token makers
- Soldier lords
- Anthems
- Attack triggers
- Tap/untap support
- Commander rewards Soldiers

## Primary Gate

```python
def can_be_primary_soldier_typal(role_counts, creature_type_counts, commander_tags):
    return (
        (
            creature_type_counts["soldier"]
            + role_counts["soldier_token_maker"]
        ) >= 16
        and role_counts["typal_payoff"] >= 3
        and (
            "soldier_typal" in commander_tags
            or role_counts["anthem"] >= 3
            or role_counts["attack_trigger"] >= 3
        )
    )
```

## Cut Logic

Protect:
- Soldier token makers
- Anthems
- Attack triggers
- Board protection
- Tap/untap payoffs if commander supports them

Review:
- Non-Soldier creatures without role support
- Single-target buffs in go-wide builds
- Expensive cards that do not support swarm
- Soldier payoffs with low Soldier/token density

## Replacement Categories

- More Soldier token makers
- More anthems
- More board protection
- More card draw
- More combat finishers

---

# 4.29 Warrior Typal

## Definition

Warrior decks focus on aggressive combat, attack triggers, Equipment, extra combat, and go-wide pressure.

## Detection Signals

Increase Warrior Typal score for:
- Warrior density
- Warrior token makers
- Attack triggers
- Equipment
- Extra combat
- Combat damage payoff
- Commander rewards Warriors

## Primary Gate

```python
def can_be_primary_warrior_typal(role_counts, creature_type_counts, commander_tags):
    return (
        (
            creature_type_counts["warrior"]
            + role_counts["warrior_token_maker"]
        ) >= 15
        and role_counts["typal_payoff"] >= 3
        and (
            "warrior_typal" in commander_tags
            or role_counts["attack_trigger"] >= 3
            or role_counts["extra_combat"] >= 2
        )
    )
```

## Suppression Rules

Najeela decks may be:
- Warrior Typal
- Five-color Combo
- Extra Combat Combo
- Warrior Tokens
- Goodstuff

Let commander, win conditions, and combo density decide primary label.

## Cut Logic

Protect:
- Warrior token makers
- Attack-trigger payoffs
- Extra combat support
- Equipment if supported
- Haste/evasion

Review:
- Warriors with no combat impact
- Non-Warrior creatures with no role
- Extra combat cards without enough attack payoff
- Equipment if deck lacks Equipment synergy

## Replacement Categories

- More Warrior density
- More attack payoffs
- More extra combat
- More protection
- More card draw

---

# 4.30 Rogue Typal

## Definition

Rogue decks use evasion, mill, combat damage triggers, theft, graveyard exploitation, and saboteur value.

## Detection Signals

Increase Rogue Typal score for:
- Rogue density
- Evasive creatures
- Combat damage triggers
- Mill
- Theft from graveyards
- Opponent graveyard payoff
- Commander rewards Rogues

## Primary Gate

```python
def can_be_primary_rogue_typal(role_counts, creature_type_counts, commander_tags):
    return (
        creature_type_counts["rogue"] >= 14
        and role_counts["typal_payoff"] >= 3
        and (
            "rogue_typal" in commander_tags
            or role_counts["mill"] >= 3
            or role_counts["saboteur"] >= 4
        )
    )
```

## Cut Logic

Protect:
- Cheap evasive Rogues
- Mill support
- Combat damage payoffs
- Theft/graveyard payoff
- Tempo interaction

Review:
- Non-evasive Rogues without payoff
- Mill cards with no graveyard payoff
- Non-Rogues without saboteur/tempo role
- Expensive creatures with no immediate value

## Replacement Categories

- More cheap evasive Rogues
- More mill payoff
- More saboteur payoff
- More theft/graveyard support
- More tempo interaction

---

# 4.31 Wizard Typal

## Definition

Wizard decks often center on instants/sorceries, card draw, spell copying, ETB abilities, control, and tap abilities.

## Detection Signals

Increase Wizard Typal score for:
- Wizard density
- Wizard ETB effects
- Spell support
- Tap-to-draw engines
- Wizard copy effects
- Commander rewards Wizards
- Wizard combo pieces

## Primary Gate

```python
def can_be_primary_wizard_typal(role_counts, creature_type_counts, commander_tags):
    return (
        creature_type_counts["wizard"] >= 14
        and role_counts["typal_payoff"] >= 3
        and (
            "wizard_typal" in commander_tags
            or role_counts["wizard_etb"] >= 3
            or role_counts["spellslinger"] >= 4
            or role_counts["tap_draw"] >= 2
        )
    )
```

## Strategy Shapes

Common shapes:
- Wizard Spellslinger
- Wizard ETB Combo
- Wizard Tap-Draw
- Wizard Control
- Wizard Tempo

## Cut Logic

Protect:
- Small utility Wizards
- Wizard ETB combo pieces
- Tap-to-draw Wizards
- Spell payoff Wizards
- Copy effects

Review:
- Wizards with no spell/ETB/control role
- Non-Wizard creatures with no role
- Expensive Wizards without immediate value
- Spellslinger cards if Wizard plan is creature-focused and spell density is low

## Replacement Categories

- More Wizard ETB pieces
- More spell support
- More card draw
- More interaction
- More combo protection

---

# 4.32 Cleric Typal

## Definition

Cleric decks combine lifegain, lifedrain, reanimation, sacrifice, party synergies, and defensive value.

## Detection Signals

Increase Cleric Typal score for:
- Cleric density
- Lifegain/lifedrain
- Cleric recursion
- Sacrifice outlets
- Death triggers
- Party support
- Commander rewards Clerics

## Primary Gate

```python
def can_be_primary_cleric_typal(role_counts, creature_type_counts, commander_tags):
    return (
        creature_type_counts["cleric"] >= 14
        and role_counts["typal_payoff"] >= 3
        and (
            "cleric_typal" in commander_tags
            or role_counts["lifegain_payoff"] >= 2
            or role_counts["recursion"] >= 3
            or role_counts["sacrifice_outlet"] >= 2
        )
    )
```

## Cut Logic

Protect:
- Cleric recursion
- Lifegain/lifedrain payoffs
- Sacrifice outlets
- Low-power Clerics that loop
- Party support if relevant

Review:
- Clerics with no life/death/recursion role
- Lifegain without payoff
- Sacrifice cards without fodder
- Non-Clerics with no support role

## Replacement Categories

- More Cleric recursion
- More lifedrain
- More sacrifice outlets
- More card draw
- More payoff density

---

# 4.33 Druid Typal

## Definition

Druid decks focus on mana production, lands, creature ramp, untap effects, and sometimes combo.

## Detection Signals

Increase Druid Typal score for:
- Druid density
- Mana dorks
- Untap effects
- Land ramp
- Creature mana payoff
- Commander rewards Druids
- Big mana sinks

## Primary Gate

```python
def can_be_primary_druid_typal(role_counts, creature_type_counts, commander_tags):
    return (
        creature_type_counts["druid"] >= 14
        and (
            role_counts["mana_dork"] >= 6
            or role_counts["typal_payoff"] >= 3
        )
        and (
            "druid_typal" in commander_tags
            or role_counts["untap_ramp"] >= 2
            or role_counts["mana_sink"] >= 2
        )
    )
```

## Cut Logic

Protect:
- Druid mana producers
- Untap-ramp
- Mana sinks
- Creature-ramp payoff
- Druid lords or type-specific mana engines

Review:
- Druids that do not produce mana or support plan
- Big mana with no payoff
- Non-Druid ramp if Druid density matters
- Untap effects with too few valuable targets

## Replacement Categories

- More Druid mana producers
- More untap effects
- More mana sinks
- More card draw
- More protection

---

# 4.34 Elemental Typal

## Definition

Elemental decks often use landfall, sacrifice, evoke, recursion, combat, or ETB triggers.

## Detection Signals

Increase Elemental Typal score for:
- Elemental density
- Elemental token makers
- Landfall
- Evoke
- Recursion
- ETB triggers
- Sacrifice payoffs
- Commander rewards Elementals

## Primary Gate

```python
def can_be_primary_elemental_typal(role_counts, creature_type_counts, commander_tags):
    return (
        (
            creature_type_counts["elemental"]
            + role_counts["elemental_token_maker"]
        ) >= 14
        and role_counts["typal_payoff"] >= 3
        and (
            "elemental_typal" in commander_tags
            or role_counts["landfall"] >= 3
            or role_counts["etb_payoff"] >= 3
            or role_counts["recursion"] >= 3
        )
    )
```

## Suppression Rules

If commander and deck strongly support Landfall, classify as:
- Landfall primary
- Elemental typal secondary

If Elemental payoffs dominate, classify as:
- Elemental primary
- Landfall support

## Cut Logic

Protect:
- Elemental token makers
- Landfall support if Elemental landfall shell
- Evoke recursion
- ETB payoffs
- Sacrifice outlets if supported

Review:
- Elementals with no ETB, landfall, or sacrifice role
- Landfall cards without land support
- Non-Elementals with no synergy
- Expensive Elementals without impact

## Replacement Categories

- More landfall support
- More Elemental payoff
- More recursion
- More ETB value
- More token makers

---

# 4.35 Cat / Dog Typal

## Definition

Cat and Dog decks are usually go-wide combat, lifegain, Equipment, token, or legends-adjacent decks.

## Detection Signals

Increase Cat/Dog Typal score for:
- Cat or Dog density
- Cat/Dog token makers
- Lords
- Lifegain
- Equipment
- Commander rewards Cats/Dogs
- Go-wide combat payoff

## Primary Gate

```python
def can_be_primary_cat_dog_typal(role_counts, creature_type_counts, commander_tags):
    return (
        (
            creature_type_counts["cat"]
            + creature_type_counts["dog"]
            + role_counts["cat_token_maker"]
            + role_counts["dog_token_maker"]
        ) >= 15
        and role_counts["typal_payoff"] >= 3
        and (
            "cat_typal" in commander_tags
            or "dog_typal" in commander_tags
            or role_counts["lifegain_payoff"] >= 2
            or role_counts["equipment_synergy"] >= 2
        )
    )
```

## Strategy Shapes

Common shapes:
- Cat Voltron
- Cat Go-Wide
- Cat/Dog Tokens
- Dog Legends
- Cat/Dog Lifegain

## Cut Logic

Protect:
- Cat/Dog token makers
- Equipment in Equipment-supported shells
- Lifegain payoffs
- Lords
- Low-cost on-type creatures

Review:
- Off-type creatures with no role
- Equipment without carriers
- Lifegain with no payoff
- Token makers that do not support tribe

## Replacement Categories

- More Cat/Dog token makers
- More lords
- More Equipment support
- More lifegain payoff
- More protection

---

# 4.36 Wolf / Werewolf Typal

## Definition

Wolf and Werewolf decks are combat-focused, using tokens, day/night mechanics, lords, fight effects, and attack triggers.

## Detection Signals

Increase Wolf/Werewolf score for:
- Wolf/Werewolf density
- Wolf token makers
- Day/night support
- Fight effects
- Lords
- Combat payoffs
- Commander rewards Wolves/Werewolves

## Primary Gate

```python
def can_be_primary_wolf_werewolf_typal(role_counts, creature_type_counts, commander_tags):
    return (
        (
            creature_type_counts["wolf"]
            + creature_type_counts["werewolf"]
            + role_counts["wolf_token_maker"]
        ) >= 15
        and role_counts["typal_payoff"] >= 3
        and (
            "wolf_typal" in commander_tags
            or "werewolf_typal" in commander_tags
            or role_counts["day_night_support"] >= 2
        )
    )
```

## Suppression Rules

Random Wolves alone should not make the deck Wolf Typal.

Werewolf decks need actual Werewolf density and day/night support.

## Cut Logic

Protect:
- Day/night support
- Wolf token makers
- Werewolf lords
- Fight effects if deck uses large creatures
- Combat payoffs

Review:
- Random Wolves with no synergy
- Day/night cards with low Werewolf density
- Fight effects without large bodies
- Combat-only cards without pressure

## Replacement Categories

- More Werewolf density
- More day/night support
- More lords
- More combat payoff
- More card draw

---

# 4.37 Rat / Nazgûl / Multiple-Copy Typal

## Definition

Rat and Nazgûl decks often use special deckbuilding exceptions or copy-heavy scaling to create density.

## Detection Signals

Increase score for:
- Rat Colony
- Relentless Rats
- Nazgûl
- Rat lords
- Wraith/Nazgûl payoff
- Multiple-copy exception text
- Fear/menace/evasion
- Poison if Karumonix-style
- Ring temptation for Nazgûl

## Primary Gate

```python
def can_be_primary_multiple_copy_typal(
    exception_card_count,
    payoff_count,
    commander_support
):
    return (
        exception_card_count >= 12
        and (
            payoff_count >= 3
            or commander_support
        )
    )
```

## Cut Logic

Protect:
- Multiple-copy exception cards
- Lords
- Evasion
- Counter payoffs for Nazgûl
- Poison payoffs for Karumonix
- Ring temptation support if Nazgûl deck

Review:
- Off-type creatures with no support
- Payoffs that do not scale with copy count
- Too many expensive support cards
- Non-exception cards that dilute density

## Replacement Categories

- More payoff for copy density
- More evasion
- More card draw
- More protection
- More removal

---

# 4.38 Snake Typal

## Definition

Snake decks use deathtouch, poison, tokens, counters, and combat deterrence.

## Detection Signals

Increase Snake score for:
- Snake density
- Snake token makers
- Deathtouch
- Poison
- -1/-1 counters
- +1/+1 counters
- Commander rewards Snakes
- Combat evasion

## Primary Gate

```python
def can_be_primary_snake_typal(role_counts, creature_type_counts, commander_tags):
    return (
        (
            creature_type_counts["snake"]
            + role_counts["snake_token_maker"]
        ) >= 14
        and role_counts["typal_payoff"] >= 3
        and (
            "snake_typal" in commander_tags
            or role_counts["deathtouch"] >= 4
            or role_counts["poison"] >= 2
            or role_counts["minus_one_counter"] >= 3
        )
    )
```

## Suppression Rules

Hapatra-style decks may be:
- -1/-1 Counters primary
- Snake Tokens secondary
- Aristocrats support

Do not force Snake primary if counters/aristocrats clearly dominate.

## Cut Logic

Protect:
- Snake token makers
- Deathtouch payoff
- Poison payoff
- -1/-1 counter engines
- Combat deterrents

Review:
- Random Snakes with no counter/deathtouch role
- Poison cards without poison density
- Counter cards without payoffs
- Off-type creatures with no support

## Replacement Categories

- More Snake token makers
- More deathtouch payoff
- More poison support
- More counter synergy
- More protection

---

# 4.39 Insect / Squirrel / Saproling / Fungus Typal

## Definition

These tribes are usually token-heavy and often overlap with sacrifice, Food, counters, graveyard, and aristocrats.

## Detection Signals

Increase score for:
- Relevant creature density
- Relevant token makers
- Token doublers
- Sacrifice outlets
- Death payoffs
- Food support for Squirrels
- Fungus/Saproling linked support
- Commander rewards the tribe

## Primary Gate

```python
def can_be_primary_small_token_typal(
    creature_type_card_count,
    token_maker_count,
    typal_payoff_count,
    commander_typal_support
):
    return (
        (creature_type_card_count + token_maker_count) >= 16
        and typal_payoff_count >= 3
        and commander_typal_support
    )
```

## Linked Type Rules

Treat these as linked when appropriate:
- Fungus + Saproling
- Squirrel + Food + Tokens
- Insect + Tokens + Graveyard
- Plant + Landfall + Counters

## Cut Logic

Protect:
- Token makers
- Sacrifice outlets
- Token doublers
- Aristocrats payoffs
- Food/token support if Squirrels
- Fungus cards that create Saprolings

Review:
- Token makers of the wrong type
- Sacrifice payoffs without fodder
- Lords without density
- Off-type creatures with no token/aristocrats role

## Replacement Categories

- More token makers
- More sacrifice outlets
- More death payoffs
- More token doublers
- More card draw

---

# 4.40 Faerie Typal

## Definition

Faerie decks are evasive, tempo-oriented, and often flash/control based.

## Detection Signals

Increase Faerie score for:
- Faerie density
- Faerie token makers
- Flash
- Flying
- Counterspells
- Combat damage triggers
- Faerie lords
- Commander rewards Faeries

## Primary Gate

```python
def can_be_primary_faerie_typal(role_counts, creature_type_counts, commander_tags):
    return (
        (
            creature_type_counts["faerie"]
            + role_counts["faerie_token_maker"]
        ) >= 14
        and role_counts["typal_payoff"] >= 3
        and (
            "faerie_typal" in commander_tags
            or role_counts["flash"] >= 3
            or role_counts["flying_payoff"] >= 2
            or role_counts["tempo_interaction"] >= 3
        )
    )
```

## Cut Logic

Protect:
- Cheap evasive Faeries
- Flash support
- Counterspell tempo pieces
- Flying payoffs
- Faerie lords/token makers

Review:
- Non-Faerie flyers with no role
- High-cost cards that disrupt tempo
- Faeries with no evasion/payoff
- Control cards if creature pressure is too low

## Replacement Categories

- More cheap Faeries
- More flash support
- More flying payoff
- More tempo interaction
- More card draw

---

# 4.41 Pirate Typal

## Definition

Pirate decks use Treasure, theft, combat damage, saboteur triggers, and sometimes Vehicles.

## Detection Signals

Increase Pirate score for:
- Pirate density
- Pirate token makers
- Treasure from Pirates
- Theft
- Saboteur triggers
- Combat damage payoff
- Commander rewards Pirates

## Primary Gate

```python
def can_be_primary_pirate_typal(role_counts, creature_type_counts, commander_tags):
    return (
        creature_type_counts["pirate"] >= 14
        and role_counts["typal_payoff"] >= 3
        and (
            "pirate_typal" in commander_tags
            or role_counts["treasure_maker"] >= 3
            or role_counts["theft"] >= 3
            or role_counts["saboteur"] >= 3
        )
    )
```

## Cut Logic

Protect:
- Pirate Treasure makers
- Theft support
- Evasive Pirates
- Saboteur payoffs
- Malcolm-style combo pieces if intended

Review:
- Non-Pirates with no Treasure/theft role
- Treasure payoffs without Treasure support
- Theft cards that are too slow
- Pirates with no evasion or payoff

## Replacement Categories

- More Pirate density
- More Treasure support
- More theft payoff
- More evasion
- More card draw

---

# 4.42 Ninja Typal

## Definition

Ninja decks use cheap evasive enablers and ninjutsu to generate combat-damage value.

## Detection Signals

Increase Ninja score for:
- Ninja density
- Ninjutsu
- Cheap evasive non-Ninja enablers
- Topdeck manipulation
- Combat damage triggers
- High-MV topdeck cards for Yuriko
- Commander rewards Ninjas

## Primary Gate

```python
def can_be_primary_ninja_typal(role_counts, creature_type_counts, commander_tags):
    return (
        creature_type_counts["ninja"] >= 10
        and role_counts["evasive_enabler"] >= 6
        and (
            role_counts["ninjutsu"] >= 5
            or commander_supports_ninjutsu
        )
        and role_counts["combat_damage_payoff"] >= 3
    )
```

## Special Rule

Cheap evasive non-Ninjas are core enablers, not off-typal filler.

## Cut Logic

Protect:
- Cheap evasive creatures
- Ninjutsu creatures
- Topdeck manipulation
- Combat damage payoffs
- Yuriko high-MV reveal support if relevant

Review:
- Expensive creatures that cannot be cheated or support topdeck plan
- Non-evasive attackers
- Combat cards with no saboteur value
- Ninjas that are too slow without payoff

## Replacement Categories

- More cheap evasive enablers
- More Ninjas
- More topdeck manipulation
- More protection
- More tempo interaction

---

# 4.43 Assassin Typal

## Definition

Assassin decks use deathtouch, targeted removal, combat damage, freerunning, legendary synergies, graveyard interaction, and reanimation attacks.

## Detection Signals

Increase Assassin score for:
- Assassin density
- Legendary Assassin support
- Freerunning
- Deathtouch
- Graveyard reanimation attack
- Targeted removal
- Combat damage triggers
- Commander rewards Assassins

## Primary Gate

```python
def can_be_primary_assassin_typal(role_counts, creature_type_counts, commander_tags):
    return (
        creature_type_counts["assassin"] >= 12
        and role_counts["typal_payoff"] >= 3
        and (
            "assassin_typal" in commander_tags
            or role_counts["legendary_synergy"] >= 3
            or role_counts["freerunning"] >= 2
            or role_counts["graveyard"] >= 3
        )
    )
```

## Cut Logic

Protect:
- Legendary Assassin support
- Graveyard/reanimation attack pieces
- Freerunning enablers
- Deathtouch/removal pieces
- Evasive Assassins

Review:
- Assassins with no combat/removal/graveyard role
- Legendary cards with no Assassin synergy
- Off-type cards that do not support historic/graveyard/combat
- Expensive Assassins without impact

## Replacement Categories

- More Assassin density
- More graveyard setup
- More legendary synergy
- More evasion
- More removal

---

# 4.44 Phyrexian Typal

## Definition

Phyrexian decks are broad and mechanically diverse, using poison, incubate, sacrifice, proliferate, artifacts, and -1/-1 counters depending on commander.

## Detection Signals

Increase Phyrexian score for:
- Phyrexian density
- Poison
- Proliferate
- Incubate
- Sacrifice
- Artifact support
- -1/-1 counters
- Commander rewards Phyrexians

## Primary Gate

```python
def can_be_primary_phyrexian_typal(role_counts, creature_type_counts, commander_tags):
    return (
        creature_type_counts["phyrexian"] >= 14
        and role_counts["typal_payoff"] >= 3
        and (
            "phyrexian_typal" in commander_tags
            or role_counts["incubate"] >= 3
            or role_counts["poison"] >= 3
            or role_counts["proliferate"] >= 3
        )
    )
```

## Suppression Rules

Separate Phyrexian Typal from Poison.

If the deck gives poison counters consistently:
- Poison may be primary.
- Phyrexian Typal may be secondary.

If the deck has Phyrexians but no typal payoff:
- Classify as Phyrexian Goodstuff or incidental.

## Cut Logic

Protect:
- Incubate support
- Proliferate
- Poison payoff if poison deck
- Artifact support if incubate/artifact shell
- Sacrifice outlets if aristocrats shell

Review:
- Phyrexians with no mechanical connection
- Poison cards without poison density
- Incubate without artifact/token payoff
- Proliferate without counters

## Replacement Categories

- More proliferate
- More poison support
- More incubate payoff
- More sacrifice support
- More card draw

---

# 4.45 Myr / Artifact Creature Typal

## Definition

Myr and artifact creature typal decks use mana Myr, artifact tokens, artifact creature payoffs, cost reduction, recursion, and combo.

## Detection Signals

Increase score for:
- Myr density
- Artifact creature density
- Mana Myr
- Artifact token makers
- Artifact creature lords
- Artifact recursion
- Commander rewards artifact creatures

## Primary Gate

```python
def can_be_primary_artifact_creature_typal(role_counts, creature_type_counts, commander_tags):
    return (
        (
            creature_type_counts["myr"]
            + role_counts["artifact_creature_count"]
            + role_counts["artifact_creature_token_maker"]
        ) >= 16
        and role_counts["artifact_payoff"] >= 4
        and (
            "myr_typal" in commander_tags
            or "artifact_creature_typal" in commander_tags
            or role_counts["artifact_lord"] >= 2
        )
    )
```

## Cut Logic

Protect:
- Mana Myr
- Artifact creature payoffs
- Artifact recursion
- Artifact token makers
- Cost reducers
- Combo pieces

Review:
- Nonartifact creatures with no role
- Artifact payoffs with low artifact density
- Expensive artifacts with low impact
- Myr cards with no ramp/payoff role

## Replacement Categories

- More artifact creatures
- More artifact payoff
- More artifact recursion
- More ramp
- More token makers

---

# 4.46 Construct / Golem / Thopter Artifact Typal

## Definition

These decks function as artifact typal or artifact-token typal rather than normal creature-type tribal.

## Detection Signals

Increase score for:
- Construct tokens
- Golem density
- Thopter token makers
- Artifact creature payoff
- Affinity/improvise
- Modular
- Artifact sacrifice
- Commander rewards artifact creatures/tokens

## Primary Gate

```python
def can_be_primary_artifact_token_typal(role_counts, commander_tags):
    return (
        (
            role_counts["artifact_creature_token_maker"]
            + role_counts["thopter_token_maker"]
            + role_counts["construct_token_maker"]
        ) >= 8
        and role_counts["artifact_payoff"] >= 4
        and (
            "artifact_typal" in commander_tags
            or "artifact_token_typal" in commander_tags
            or role_counts["artifact_lord"] >= 2
        )
    )
```

## Cut Logic

Protect:
- Thopter/Construct token makers
- Artifact creature payoffs
- Artifact sacrifice payoffs
- Artifact recursion
- Token doublers

Review:
- Nonartifact creatures with no role
- Token makers that create nonartifact tokens unless they support the plan
- Artifact payoffs with low artifact count
- High-cost artifact creatures without synergy

## Replacement Categories

- More artifact token makers
- More artifact payoff
- More sacrifice outlets
- More recursion
- More card draw

---

# 4.47 Hydra Typal

## Definition

Hydra decks use X-cost creatures, +1/+1 counters, ramp, and doubling effects.

## Detection Signals

Increase Hydra score for:
- Hydra density
- X-spells/X-creatures
- +1/+1 counters
- Counter doublers
- Ramp
- Mana sinks
- Commander rewards Hydras or X-spells

## Primary Gate

```python
def can_be_primary_hydra_typal(role_counts, creature_type_counts, commander_tags):
    return (
        creature_type_counts["hydra"] >= 8
        and (
            role_counts["x_spell"] + role_counts["x_creature"]
        ) >= 6
        and (
            role_counts["ramp"] + role_counts["counter_doubler"]
        ) >= 6
        and (
            "hydra_typal" in commander_tags
            or role_counts["x_spell_payoff"] >= 2
        )
    )
```

## Cut Logic

Protect:
- Ramp
- X-creature payoffs
- Counter doublers
- Mana sinks
- Hydra support

Review:
- Hydras in decks without ramp
- X-spells without mana support
- Counter cards without counter payoff
- Non-Hydra threats with no X/counter role

## Replacement Categories

- More ramp
- More X-spells
- More counter doublers
- More protection
- More card draw

---

# 4.48 Treefolk Typal

## Definition

Treefolk decks use high-toughness creatures, forests, toughness-matters effects, and slow combat value.

## Detection Signals

Increase Treefolk score for:
- Treefolk density
- Toughness matters
- Forest synergy
- High-toughness creatures
- Recursion/attrition
- Commander rewards Treefolk or toughness

## Primary Gate

```python
def can_be_primary_treefolk_typal(role_counts, creature_type_counts, commander_tags):
    return (
        creature_type_counts["treefolk"] >= 10
        and role_counts["typal_payoff"] >= 3
        and (
            "treefolk_typal" in commander_tags
            or role_counts["toughness_matters"] >= 3
            or role_counts["forest_synergy"] >= 2
        )
    )
```

## Cut Logic

Protect:
- Toughness-matters pieces
- Treefolk payoffs
- Forest synergy
- Slow but resilient bodies if on-plan
- Attrition pieces

Review:
- Expensive Treefolk without toughness payoff
- Generic high-toughness cards with no payoff
- Forest synergy with low Forest count
- Non-Treefolk creatures with no support

## Replacement Categories

- More Treefolk payoff
- More toughness synergy
- More ramp
- More recursion
- More card draw

---

# 4.49 Giant / Minotaur / Beast / Berserker Typal

## Definition

These combat tribes are usually more support-limited than top-tier typal decks and often need generic combat support.

## Detection Signals

Increase score for:
- Relevant creature density
- Lords
- Combat payoffs
- Cost reduction for high-MV tribes
- Menace/discard for Minotaurs
- Stompy support for Beasts
- Attack triggers for Berserkers
- Commander support

## Primary Gate

```python
def can_be_primary_limited_support_combat_typal(
    creature_type_count,
    typal_payoff_count,
    commander_typal_support,
    combat_payoff_count
):
    return (
        creature_type_count >= 14
        and (
            typal_payoff_count >= 3
            or combat_payoff_count >= 5
        )
        and commander_typal_support
    )
```

## Cut Logic

Protect:
- Generic combat support if tribe lacks enough specific support
- Lords
- Cost reducers for high-MV tribe
- Evasion/menace
- Combat finishers

Review:
- Off-plan goodstuff
- Expensive creatures without ramp
- Weak lords with low density
- Combat cards that do not scale

## Replacement Categories

- More combat payoff
- More ramp/cost reduction
- More evasion
- More card draw
- More protection

---

# 4.50 Scarecrow / Changeling / All-Typal

## Definition

Scarecrow, Changeling, and All-Typal decks use changelings, cost reducers, tribal payoffs, and multiple creature-type synergies.

## Detection Signals

Increase score for:
- Changelings
- Multiple tribal payoffs
- Reaper King-style triggers
- Morophon-style cost reduction
- Five-color fixing
- Type-granting effects
- Tribal payoff stacking

## Primary Gate

```python
def can_be_primary_changeling_all_typal(
    changeling_count,
    tribal_payoff_count,
    commander_support
):
    return (
        changeling_count >= 8
        and tribal_payoff_count >= 5
        and commander_support
    )
```

## Cut Logic

Protect:
- Changelings
- Multi-tribal payoffs
- Cost reducers
- Five-color fixing
- Reaper King-style payoff pieces

Review:
- Single-tribe payoffs with low support
- Changelings with no payoff
- Five-color cards that do not support tribal plan
- Expensive goodstuff

## Replacement Categories

- More changelings
- More multi-tribal payoff
- More mana fixing
- More protection
- More card draw

---

# 4.51 Ally Typal

## Definition

Ally decks trigger whenever Allies enter the battlefield and often chain ETB/rally effects.

## Detection Signals

Increase Ally score for:
- Ally density
- Ally ETB triggers
- Blink
- Rally effects
- Token/copy support
- Commander rewards Allies
- Party overlap

## Primary Gate

```python
def can_be_primary_ally_typal(role_counts, creature_type_counts, commander_tags):
    return (
        creature_type_counts["ally"] >= 16
        and role_counts["ally_etb_payoff"] >= 4
        and (
            "ally_typal" in commander_tags
            or role_counts["blink"] >= 2
            or role_counts["rally"] >= 3
        )
    )
```

## Cut Logic

Protect:
- Ally ETB payoffs
- Blink effects
- Ally density pieces
- Recursion
- Token/copy effects if they retrigger Ally value

Review:
- Allies with weak ETB effects
- Blink with too few Allies
- Non-Allies with no ETB support
- Generic combat cards if ETB plan is primary

## Replacement Categories

- More Ally ETB payoffs
- More blink
- More recursion
- More card draw
- More protection

---

# 4.52 Party Typal

## Definition

Party decks care about having Cleric, Rogue, Warrior, and Wizard. This is a multi-type composition puzzle, not a normal single-tribe deck.

## Detection Signals

Increase Party score for:
- Cleric count
- Rogue count
- Warrior count
- Wizard count
- Party payoff
- Dungeon/initiative support
- Treasure from Party
- Commander rewards full party

## Primary Gate

```python
def can_be_primary_party_typal(role_counts, creature_type_counts, commander_tags):
    party_roles_represented = sum([
        creature_type_counts["cleric"] > 0,
        creature_type_counts["rogue"] > 0,
        creature_type_counts["warrior"] > 0,
        creature_type_counts["wizard"] > 0
    ])

    return (
        party_roles_represented >= 4
        and role_counts["party_payoff"] >= 4
        and (
            "party_typal" in commander_tags
            or role_counts["party_tutor"] >= 1
        )
    )
```

## Evaluation Rule

Party decks should be evaluated by role spread, not one creature type’s density.

## Cut Logic

Protect:
- Underrepresented party roles
- Party payoff cards
- Party tutors
- Creatures that fill multiple roles
- Dungeon/initiative if party-supported

Review:
- Overrepresented party roles if balance is poor
- Creatures that do not fill party roles
- Party payoffs without full-party consistency
- Generic creatures with no role

## Replacement Categories

- More missing party roles
- More party payoff
- More card draw
- More protection
- More flexible role creatures

---

# 4.53 Samurai / Monk / Mouse / Otter Typal-Spellslinger or Combat Hybrids

## Definition

These tribes often function as hybrid shells rather than pure typal decks.

- Samurai: single-attacker combat, Equipment, extra combats
- Monks: prowess, noncreature spells, combat tricks
- Mice: targeting, Valiant, go-wide/go-tall combat
- Otters: spellslinger, prowess, spell-copy

## Detection Signals

Increase score for:
- Tribe density
- Commander support
- Strategy-shape support
- Equipment for Samurai
- Noncreature spells for Monks/Otters
- Targeting/pump spells for Mice
- Combat tricks and attack triggers

## Primary Gate

```python
def can_be_primary_hybrid_small_typal(
    creature_type_count,
    typal_payoff_count,
    strategy_shape_support_count,
    commander_typal_support
):
    return (
        creature_type_count >= 10
        and (
            typal_payoff_count >= 3
            or strategy_shape_support_count >= 6
        )
        and commander_typal_support
    )
```

## Suppression Rules

Suppress pure typal label if strategy shape is stronger:
- Monk → Spellslinger or Prowess
- Otter → Spellslinger
- Samurai → Single-Attacker Combat or Equipment
- Mouse → Valiant/Targeting Combat

## Cut Logic

Protect:
- Strategy-shape support cards
- Tribe-specific payoff
- Low-cost enablers
- Combat tricks if commander rewards targeting
- Noncreature spells in Otter/Monk shells

Review:
- Tribe members with no connection to strategy shape
- Generic spells that do not trigger payoffs
- Equipment in non-Equipment versions
- Combat tricks with too few targets/payoffs

## Replacement Categories

- More strategy-shape support
- More on-type creatures
- More protection
- More card draw
- More efficient enablers

---

# 4.54 Halfling / Hobbit Typal

## Definition

Halfling and Hobbit decks often combine Food, lifegain, tokens, Ring temptation, and small-creature value.

## Detection Signals

Increase score for:
- Halfling/Hobbit density
- Food creation
- Lifegain
- Small-creature value
- Ring temptation
- Token support
- Commander rewards Halflings/Hobbits/Food/life

## Primary Gate

```python
def can_be_primary_halfling_hobbit_typal(role_counts, creature_type_counts, commander_tags):
    return (
        (
            creature_type_counts["halfling"]
            + creature_type_counts["hobbit"]
        ) >= 10
        and (
            role_counts["food"] >= 4
            or role_counts["lifegain"] >= 4
            or role_counts["typal_payoff"] >= 3
        )
        and (
            "halfling_typal" in commander_tags
            or "hobbit_typal" in commander_tags
            or role_counts["food_payoff"] >= 2
        )
    )
```

## Linked Type Rule

Treat Hobbit and Halfling together unless deck clearly separates them.

## Cut Logic

Protect:
- Food support
- Lifegain payoffs
- Small-creature value
- Ring temptation support if relevant
- Token support

Review:
- Food cards with no payoff
- Lifegain with no payoff
- Off-type small creatures with no role
- Halfling/Hobbit cards that do not support the engine

## Replacement Categories

- More Food generation
- More lifegain payoff
- More small-creature value
- More protection
- More card draw

---

# 4.55 Orc / Army / Amass Typal

## Definition

Orc and Army decks often use Amass, sacrifice, combat, and spell triggers. They may create or grow a single Army token rather than play many creature cards.

## Detection Signals

Increase score for:
- Orc density
- Amass
- Army token support
- Sacrifice
- Spell triggers
- Commander rewards Orcs/Armies
- Grixis control support

## Primary Gate

```python
def can_be_primary_orc_army_typal(role_counts, creature_type_counts, commander_tags):
    return (
        (
            creature_type_counts["orc"]
            + role_counts["amass"]
            + role_counts["army_token_support"]
        ) >= 12
        and (
            role_counts["typal_payoff"] >= 3
            or role_counts["amass_payoff"] >= 3
        )
        and (
            "orc_typal" in commander_tags
            or "army_typal" in commander_tags
            or role_counts["amass"] >= 4
        )
    )
```

## Special Rule

Army typal should be evaluated differently because the deck may have only one Army token at a time.

## Cut Logic

Protect:
- Amass cards
- Army payoff
- Sacrifice support if Army tokens are used as fodder
- Spell-trigger Amass
- Commander support

Review:
- Orcs with no Amass/sacrifice/combat role
- Army payoff without Amass
- Token payoffs that require many bodies if deck only grows one Army
- Off-plan Grixis goodstuff

## Replacement Categories

- More Amass
- More Army payoff
- More sacrifice support
- More spell support
- More protection

---

# 4.56 Bat / Rabbit / Bloomburrow-Style Small Typal

## Definition

Newer small-creature tribes often rely on tokens, lifegain, targeting, counters, offspring, or go-wide combat more than deep historic tribal support.

Examples:
- Bats: lifegain/lifedrain/flying tokens/aristocrats
- Rabbits: tokens/go-wide/counters/anthem
- Mice: targeting/Valiant/combat tricks/Equipment
- Otters: spellslinger/prowess/spell-copy
- Raccoons: expend/big-mana/artifact-Food value
- Squirrels: tokens/Food/aristocrats

## Detection Signals

Increase score for:
- Creature type density
- Commander support
- Token makers
- Main set mechanic support
- Strategy-shape payoffs
- Food/lifegain/targeting/expend/spell support as appropriate

## Primary Gate

```python
def can_be_primary_new_small_typal(
    creature_type_count,
    token_maker_count,
    mechanic_support_count,
    typal_payoff_count,
    commander_typal_support
):
    return (
        (creature_type_count + token_maker_count) >= 12
        and (
            typal_payoff_count >= 3
            or mechanic_support_count >= 5
        )
        and commander_typal_support
    )
```

## Cut Logic

Protect:
- Low-power on-type creatures if they trigger commander
- Mechanic enablers
- Token makers
- Payoffs tied to Food, lifegain, targeting, spells, or expend
- Board protection

Review:
- Cards with only creature type but no strategy role
- Off-type enablers if they do not support mechanic
- Payoffs with too few triggers
- Cute flavor cards with no function unless user prioritizes theme

## Replacement Categories

- More on-type enablers
- More mechanic payoff
- More token makers
- More protection
- More card draw

---

# 4.57 Keyword Typal

## Definition

Keyword Typal decks function like typal decks through a shared keyword rather than a creature type.

Common examples:
- Flying Typal
- Flying Token Typal
- Deathtouch Typal
- Lifelink Typal
- Defender Typal
- Prowess Typal
- Menace Typal
- Trample/Power Typal

## Detection Signals

Increase Keyword Typal score for:
- High density of shared keyword
- Keyword lords/payoffs
- Commander rewards keyword
- Token makers with keyword
- Combat payoff tied to keyword

## Primary Gate

```python
def can_be_primary_keyword_typal(
    keyword_count,
    keyword_payoff_count,
    commander_keyword_support
):
    return (
        keyword_count >= 16
        and keyword_payoff_count >= 3
    ) or (
        commander_keyword_support
        and keyword_count >= 10
        and keyword_payoff_count >= 2
    )
```

## Suppression Rules

Use Keyword Typal instead of forcing a creature type when:
- The deck has many creature types but one shared keyword.
- Token makers create different creature types with the same keyword.
- The commander rewards the keyword.
- The payoff cares about Flying, Deathtouch, Defender, etc., not the creature type.

## Cut Logic

Protect:
- Keyword enablers
- Keyword payoff cards
- Token makers with keyword
- Commander support

Review:
- Creatures without the relevant keyword
- Keyword payoff with low keyword density
- Tribal cards that do not support the keyword plan
- Off-plan combat cards

## Replacement Categories

- More keyword density
- More keyword payoff
- More token makers with keyword
- More protection
- More card draw

---

# 4.58 Typal Suppression Rules

Typal over-detection is common. Use these suppression rules.

## Suppress Typal if Incidental

Suppress typal to incidental if:
- The creature type is common but unsupported.
- There are few typal payoffs.
- Commander does not care about the type.
- The deck’s real plan is mechanical, not typal.

Examples:
- Random Humans in a Selesnya deck are not necessarily Human Typal.
- Random Wizards in a spellslinger deck are not necessarily Wizard Typal.
- Random Phyrexians in a poison deck may not make Phyrexian Typal primary.
- Random Dragons in a big-mana deck may be Dragon Goodstuff, not Dragon Typal.

## Suppress Typal Behind Stronger Mechanical Plan

If the mechanical plan has stronger support, use the mechanical plan primary and typal secondary.

Examples:
- Hapatra → -1/-1 Counters primary, Snake Tokens secondary
- Kykar → Token Spellslinger primary, Spirit Tokens secondary
- Talrand → Token Spellslinger primary, Drake Tokens secondary
- Alela → Flying Tokens/Artifacts/Enchantments primary depending build, Faerie secondary
- Monks/Otters → Spellslinger primary unless typal payoff density is high
- Party → Party primary, not Cleric/Rogue/Warrior/Wizard primary
- Army → Amass/Army primary, not normal Orc typal if Amass dominates

## Suppress Broad Typal Goodstuff

If a narrower typal strategy shape exists, suppress Typal Goodstuff.

Prefer:
- Dragon Treasure Ramp
- Vampire Aristocrats
- Goblin Tokens
- Zombie Reanimator
- Elf Ball
- Knight Equipment
- Wizard ETB Combo
- Sliver Combo
- Pirate Treasure Theft
- Dinosaur Discover
- Squirrel Token Aristocrats

---

# 4.59 Typal Scoring Model

Use additive scoring before gates and suppression.

```yaml
score_inputs:
  creature_type_card:
    points: 1

  relevant_token_maker:
    points: 1

  repeatable_relevant_token_maker:
    points: 2

  changeling:
    points: 1
    note: Higher value if tribe is low-density or commander cares.

  typal_lord:
    points: 2

  typal_tutor:
    points: 3

  typal_cost_reducer:
    points: 2

  typal_card_draw:
    points: 2

  typal_recursion:
    points: 2

  typal_payoff:
    points: 2

  commander_strongly_supports_type:
    points: 5

  commander_lightly_supports_type:
    points: 2

  strategy_shape_support:
    points: 1

  clear_typal_win_condition:
    points: 3

  multiple_copy_exception_engine:
    points: 4
```

Risk penalties:

```yaml
risk_penalties:
  low_creature_type_density:
    points: -4

  typal_payoff_without_density:
    points: -3

  high_mv_tribe_without_ramp:
    points: -4

  token_typal_without_token_payoff:
    points: -2

  incidental_common_creature_type:
    points: -3

  off_type_goodstuff_overload:
    points: -3

  no_clear_win_condition:
    points: -5

  commander_does_not_support_type:
    points: -2
```

Confidence bands:

```yaml
confidence:
  high:
    - passes_primary_gate
    - commander support moderate or strong
    - medium/high effective density
    - multiple typal payoffs
    - clear strategy shape
    - clear win condition

  medium:
    - partial gate success
    - medium density
    - some payoffs
    - strategy shape present
    - commander support light or moderate

  low:
    - low density
    - few payoffs
    - commander does not support type
    - common incidental type
    - unclear win condition
```

---

# 4.60 Typal Report Behavior

When a typal theme is detected, include a dedicated section:

```markdown
## Typal Strategy Read

Primary tribe:
Secondary tribe or linked type:
Typal role:
Confidence:
Commander support:
Effective typal density:
Creature cards of type:
Token makers of type:
Changelings/type-granters:
Typal payoffs:
Strategy shape:
Main resource engine:
Likely finishers:
Cards that support the tribe:
Low-power cards that are actually important:
Possible off-type cards:
Possible typal payoff cards with too little support:
Cards I would protect from cuts:
Cards worth reviewing:
Replacement categories:
```

The report should answer:

1. What creature type is the deck built around?
2. Is the tribe primary, secondary, minor, or incidental?
3. What is the strategy shape?
4. Does the commander directly support the tribe?
5. Are token makers contributing to typal density?
6. Are changelings important glue or unnecessary filler?
7. Are low-power cards actually density/payoff pieces?
8. Are expensive creatures supported by ramp, cost reduction, cheat effects, or reanimation?
9. Are off-type cards helping the tribal plan or distracting from it?
10. Does the deck have enough payoff density to justify being typal?

---

# 4.61 Typal Warning Messages

Use warnings when relevant.

## Incidental Type Warning

```markdown
Warning: This deck contains several creatures of the same type, but the type may be incidental. Typal should not become the primary strategy unless payoff density or commander support is stronger.
```

## Low Payoff Warning

```markdown
Warning: The deck has creature-type density, but it may not have enough typal payoff cards to make the tribe the primary strategy.
```

## High-MV Support Warning

```markdown
Warning: This is a high-mana-value tribe. Expensive creatures should be judged alongside ramp, cost reduction, cheat effects, and reanimation support.
```

## Token Typal Warning

```markdown
Warning: This tribe may be token-based. Token makers should count toward effective typal density even if the deck has fewer creature cards of that type.
```

## Changeling Glue Warning

```markdown
Warning: Changelings appear to be typal glue. They may look weak individually but help maintain density and activate tribal payoffs.
```

## Off-Type Goodstuff Warning

```markdown
Warning: Some off-type cards may be powerful but should be reviewed if they do not support the tribe’s strategy shape, role balance, or win condition.
```

## Multiple-Copy Exception Warning

```markdown
Note: This deck appears to use a multiple-copy exception card. These cards should not be treated as Commander singleton violations if their rules text permits multiple copies.
```

---

# 4.62 Final Section 4 Summary Rule

Typal analysis should not ask only:

```text
How many creatures share a type?
```

It should ask:

```text
Does the shared type create a real deck plan?
```

A typal card should be protected from cuts when it:
- Maintains necessary tribe density
- Acts as a lord
- Reduces costs
- Tutors for the tribe
- Creates relevant tokens
- Recurs the tribe
- Enables the tribe’s main strategy shape
- Bridges the tribe into another supported theme
- Supports a commander-defined typal plan
- Is part of a multiple-copy exception plan

A typal card should be reviewed as a possible cut when it:
- Only shares a type but has no useful role
- Is a payoff for a tribe with too little density
- Is off-type and does not support the strategy
- Is expensive without ramp, cheat, or impact
- Supports a different typal plan than the deck is actually playing
- Is generic goodstuff that weakens synergy density

A strong typal read should sound like:

```text
This is not just a Vampire deck. This is a Vampire Blood/Aristocrats deck where Blood tokens, sacrifice outlets, and Vampire death/lifegain payoffs are the actual engine.
```

That distinction is what prevents bad cut recommendations.
