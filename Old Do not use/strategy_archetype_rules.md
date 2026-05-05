# MTG Deck Helper v0.5.6 Hotfix — Strategy Archetype Rules

## Purpose

This file is the operational strategy layer for MTG Deck Helper v0.5.6 hotfix.

It does **not** replace the deeper section rule files. It tells the deck helper how to apply those files when producing:

```text
Strategy Read
Archetype detection
Primary / secondary / minor package separation
Commander-defined plan recognition
Typal strategy interpretation
Political strategy interpretation
Niche / fringe / emergent theme handling
Broad archetype suppression
Strategy-aware cut review
Strategy-aware replacement guidance
Bracket / power modifier reporting
```

This file should be read together with:

```text
rules/card_attribute_rules.md
rules/cut_replacement_rules.md
rules/bracket_rules.md
rules/section_1_macro_archetypes_commander.md
rules/section_2_mechanical_themes_micro_archetypes.md
rules/section_3_strategic_board_politics.md
rules/section_4_typal_tribal_themes_rules.md
rules/section_5_1_niche_theme_rules.md
rules/section_5_2_fringe_theme_rules.md
rules/section_5_3_emergent_theme_rules.md
```

The main goal of this hotfix is:

```text
Stop broad archetypes and incidental packages from stealing primary strategy.
```

---

# 1. Core Hotfix Principle

## Broad labels are not deck identity by default

Macro-archetypes, common support packages, and bracket-pressure signals should not become primary strategy merely because their role tags appear often.

The deck helper must first ask:

```text
What is this commander and deck actually trying to make happen?
```

Only after that should it ask:

```text
Which broad macro-archetype frame best describes the deck?
```

Correct behavior:

```text
Ghalta and Mavren -> Token Combat / Go-Wide-Go-Tall Combat, not generic Ramp-Control.
Toggo partner decks -> Commander-Created Landfall / Artifact Token Landfall, not generic Ramp or Artifacts.
Prosper -> Exile Matters / Treasure Engine, not generic Midrange.
Magda -> Treasure Tutor Chain, not generic Treasure Ramp.
Tiamat -> Dragon Tutor Chain only if the package exists.
```

---

# 2. Layered Strategy Model

## Required evaluation order

Evaluate strategy in this exact order:

```text
1. Commander-defined emergent plan
2. Specific mechanical micro-archetype
3. Typal strategy shape if typal density/payoff support exists
4. Political strategy only if incentive/protection/payoff/inevitability are present
5. Niche theme if density/payoff/commander support pass gates
6. Fringe theme only if user intent or overwhelming support exists
7. Macro-archetype fallback
8. Minor package / support package / manual review
```

## Operational rule

```python
def choose_primary_strategy(candidates):
    # Candidates should already have score, gate_passed, layer, and suppression data.
    gated = [c for c in candidates if c.gate_passed]

    commander_defined = [c for c in gated if c.layer == "commander_defined_emergent"]
    if commander_defined:
        return highest_confidence(commander_defined)

    micro = [c for c in gated if c.layer == "mechanical_micro_archetype"]
    if micro:
        return highest_confidence(micro)

    typal = [c for c in gated if c.layer == "typal_strategy_shape"]
    if typal:
        return highest_confidence(typal)

    political = [c for c in gated if c.layer == "political_strategy"]
    if political:
        return highest_confidence(political)

    niche = [c for c in gated if c.layer == "niche_theme"]
    if niche:
        return highest_confidence(niche)

    fringe = [c for c in gated if c.layer == "fringe_theme"]
    if fringe:
        return highest_confidence(fringe)

    macro = [c for c in gated if c.layer == "macro_archetype"]
    if macro:
        return highest_confidence(macro)

    return "manual_review_primary_uncertain"
```

## Anti-stealing rule

```python
if primary_candidate.is_broad and narrower_commander_defined_strategy_exists:
    suppress primary_candidate to "secondary", "minor_package", or "support_package"
```

Do not let a broad macro label become primary when a narrower commander-defined or mechanically supported theme better explains the deck.

---

# 3. Strategy Layer Definitions

## 3.1 Commander-defined emergent plan

A commander-defined emergent plan exists when the commander directly:

```text
Creates a specific token/resource
Rewards a specific mechanic
Rewards a specific card type
Rewards a specific creature type
Converts a specific resource into damage/cards/mana/tutors/combat pressure
Enables a repeatable game action
Turns an unusual resource into the deck's engine
Defines a hybrid package that broad archetypes would miss
```

Examples:

```text
Toggo creating Rocks from landfall
Prosper converting cast-from-exile into Treasure
Magda converting Treasure into tutor chains
Ghalta and Mavren turning attacks into token combat scaling
Agatha reducing activated ability costs based on power
Unesh reducing Sphinx costs and creating repeated fact-or-fiction selection
Betor rewarding toughness/defender-style scaling
```

## 3.2 Mechanical micro-archetype

A mechanical micro-archetype is a specific mechanical plan such as:

```text
Aristocrats
Voltron
Spellslinger
Blink
Landfall
Reanimator
Artifacts
Enchantress
Tokens
+1/+1 Counters
Lifegain
Treasure
Exile Matters
Saboteur
Storm
Proliferate
Mill
Equipment
Auras
Hatebears
Clues
Food
Madness
Extra Combat
X-Spells
Untap
Vehicles
Legends Matter
Copy / Clones
Theft
Monarch
Energy
Alternate Win Conditions
```

These should beat macro-archetype labels when they pass their primary gate.

## 3.3 Typal strategy shape

Typal strategy is not just creature-type density. It must identify the tribe's actual plan.

Examples:

```text
Goblin Typal / Go-Wide Tokens
Vampire Tokens / Aristocrats / Drain
Dragon Treasure Ramp
Dragon Copy / Token-Copy Value
Zombie Reanimator
Elf Ball / Token Lifedrain
Sphinx Cost Reduction / Topdeck Fact-or-Fiction
Knight Equipment
Pirate Treasure Theft
Sliver Combo
```

## 3.4 Political strategy

Political strategy is a multiplayer incentive engine.

Do not call a deck political just because it has a few political cards.

A real political deck changes incentives, threat direction, resource flow, or table behavior.

## 3.5 Niche theme

A niche theme is narrow but legitimate if supported. Niche does not mean bad. Unsupported means bad.

## 3.6 Fringe theme

A fringe theme is buildable but fragile, low-support, meta-dependent, legality-sensitive, Rule Zero-sensitive, flavor-first, or user-intent-dependent.

Most fringe themes default to manual review unless the user declared the theme.

## 3.7 Macro-archetype fallback

Macro-archetypes are broad strategic frames:

```text
Aggro
Midrange / Value
Control
Ramp / Big Mana
Combo
Stax / Prison
Tempo
Toolbox
Engine / Synergy Value
Goodstuff
```

They should usually be fallback labels, secondary frames, or support packages unless no narrower plan passes its gate.

## 3.8 Bracket / power modifier

Bracket pressure is not a primary strategy. It is a report modifier.

Examples:

```text
Game Changer
Fast mana
Free interaction
Efficient tutor
Mass land denial
Hard lock
High-power value piece
Compact combo piece
Slow alternate win condition
```

Track these separately from archetype synergy.

---

# 4. Macro-Archetype Suppression

## 4.1 Macro-archetypes are strategic frames

Macro-archetypes explain broad play patterns. They should not override commander-defined strategy, micro-archetype density, typal shape, political plan, niche theme, or emergent package.

Broad labels that must be suppressed unless strongly supported:

```text
Aggro
Midrange / Value
Control
Ramp / Big Mana
Engine / Synergy Value
Combo-Adjacent Value
Generic Tokens
Generic Artifacts
Generic Goodstuff
```

## 4.2 Suppression function

```python
BROAD_MACRO_LABELS = {
    "Aggro",
    "Midrange / Value",
    "Control",
    "Ramp / Big Mana",
    "Ramp-Control / Big Mana Value",
    "Engine / Synergy Value",
    "Combo-Adjacent Value",
    "Generic Tokens",
    "Generic Artifacts",
    "Generic Goodstuff",
    "Generic Treasure",
    "Generic Lifegain",
    "Generic Topdeck Value",
}

def suppress_broad_if_narrower_exists(primary_candidate, narrower_candidates):
    if primary_candidate.name in BROAD_MACRO_LABELS:
        passing_narrower = [
            c for c in narrower_candidates
            if c.gate_passed and c.confidence in {"medium", "high"}
        ]
        if passing_narrower:
            return "suppressed_to_secondary_or_minor"
    return "keep_candidate"
```

## 4.3 Required examples

Use these as model behavior:

```text
Ghalta and Mavren:
- Generic Aggro and Ramp-Control may score.
- Suppress them if Token Combat / Go-Wide-Go-Tall Combat passes.
- Ramp becomes support unless control density is dominant.

Toggo partner decks:
- Preserve Commander-Created Landfall / Artifact Token Landfall.
- Generic Ramp, Artifacts, or Tokens should not steal primary.

Prosper:
- Preserve Exile Matters / Treasure Engine.
- Generic Midrange should be secondary or suppressed.

Magda:
- Preserve Treasure Tutor Chain.
- Generic Treasure Ramp and generic Artifacts should not steal primary.

Tiamat:
- Preserve Dragon Tutor Chain if package exists.
- Do not assign Dragon Tutor Chain if the deck is just Dragon Goodstuff.
```

---

# 5. Micro-Archetype Primary Gate

## 5.1 Density categories

Use these density categories for micro-archetypes:

```yaml
density:
  low: 1-3 supporting cards
  medium: 4-8 supporting cards
  high: 9+ supporting cards
```

Commander-created themes may count as medium density with fewer support cards only if the commander repeatedly creates the relevant game object, trigger, or resource.

## 5.2 Required primary gate

A micro-archetype may become primary only if it passes:

```yaml
primary_gate:
  commander_support: moderate_or_strong
  deck_density: medium_or_high
  payoff_present: true
  enabler_present: true
  win_path_present: true
```

Operational function:

```python
def can_be_primary_micro_archetype(
    commander_support,
    deck_density,
    payoff_present,
    enabler_present,
    win_path_present
):
    return (
        commander_support in {"moderate", "strong"}
        and deck_density in {"medium", "high"}
        and payoff_present
        and enabler_present
        and win_path_present
    )
```

## 5.3 If the gate fails

If the primary gate fails, classify the theme as one of:

```text
secondary
minor_package
support_package
manual_review
```

Do not promote it to primary only because it has a high raw score from generic tags.

## 5.4 Enabler/payoff balance rule

A micro-archetype with payoffs but no enablers is fragile.

A micro-archetype with enablers but no payoff is support, not primary.

```python
if payoff_present and not enabler_present:
    role = "manual_review_payoffs_without_engine"
elif enabler_present and not payoff_present:
    role = "support_package_enablers_without_conversion"
```

---

# 6. Political Strategy Gate

## 6.1 Politics is incentive engineering

Political strategies require a functional incentive engine.

Use the formula:

```text
political_plan = incentive + deterrence/protection + payoff + inevitability
```

A political deck should not score highly unless at least three of these four components are present.

## 6.2 Global political primary gate

```python
can_be_primary_politics = (
    political_signal_count >= 6
    and political_payoff_count >= 2
    and (
        commander_supports_political_axis
        or political_signal_count >= 9
    )
    and has_clear_win_path
)
```

## 6.3 Political suppression

Do not label a deck as primary:

```text
Politics
Group Hug
Group Slug
Pillowfort
Goad
Aikido
Secret Combo
Table Police
Villain
```

from one or two cards.

If the gate fails, classify as:

```text
political support package
minor political package
table-dependent manual review
salt/reputation warning
```

## 6.4 Political examples

```text
One goad card -> minor combat manipulation package.
One group draw card -> group-resource manual review.
One attack tax -> defensive support, not Pillowfort.
One punisher card -> possible Group Slug support, not Group Slug primary.
Repeated goad + payoff + protection + clear win path -> Forced Combat / Goad may be primary.
```

---

# 7. Typal Strategy Shape Gate

## 7.1 Typal plan formula

Typal analysis must not ask only:

```text
How many creatures share a type?
```

It must ask:

```text
Does the shared type create a real deck plan?
```

Use this formula:

```text
typal_plan = creature_type_density + payoff_density + commander_support + strategy_shape + win_condition
```

## 7.2 Effective typal density

Effective typal density should include:

```text
Direct creature type cards
Relevant token makers
Changelings
Type-granters
Commander-created tokens
Typal tutors
Typal recursion/reanimation
Multiple-copy exception cards
```

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

## 7.3 Typal strategy shapes

When a typal theme is detected, assign a strategy shape.

Valid shapes include:

```text
typal_go_wide
typal_go_tall
typal_aristocrats
typal_reanimator
typal_tokens
typal_combo
typal_treasure
typal_lifegain
typal_spellslinger
typal_artifacts
typal_landfall
typal_control
typal_hatebears
typal_equipment
typal_counters
typal_graveyard
typal_big_mana
typal_tempo
typal_saboteur
typal_goodstuff
keyword_typal
```

## 7.4 General typal primary gate

```python
def can_be_primary_typal(creature_type_count, typal_payoff_count, commander_typal_support):
    return (
        creature_type_count >= 18
        and typal_payoff_count >= 4
    ) or (
        commander_typal_support
        and creature_type_count >= 12
        and typal_payoff_count >= 3
    )
```

For token-based tribes, count token makers toward effective density.

## 7.5 Typal suppression

Suppress typal to secondary, minor, incidental, or manual review if:

```text
The creature type is common but unsupported.
There are few typal payoffs.
Commander does not care about the type.
The deck's real plan is mechanical, not typal.
The shared type is mostly random utility creatures.
The typal label would hide a better mechanical plan.
```

## 7.6 Typal examples

```text
Random Humans in a Selesnya deck are not Human Typal.
Random Wizards in a Spellslinger deck are not Wizard Typal.
A few Elf mana dorks are not Elf Typal.
A Dragon deck with Treasure, cost reduction, and high-MV Dragons may be Dragon Treasure Ramp.
A Vampire deck with tokens, sacrifice, death triggers, and drain is Vampire Aristocrats / Drain.
```

---

# 8. Niche Theme Gate

## 8.1 Niche does not mean bad

A niche theme is narrow but legitimate if supported.

The helper should not ask only:

```text
Is this card generically powerful?
```

It should ask:

```text
Does this card enable a narrow theme that the deck is actually built to support?
```

## 8.2 Niche primary gate

```python
def can_be_primary_niche_theme(theme_count, payoff_count, commander_support):
    return (
        commander_support and theme_count >= 6 and payoff_count >= 2
    ) or (
        theme_count >= 9 and payoff_count >= 3
    )
```

## 8.3 Niche secondary gate

```python
def can_be_secondary_niche_package(theme_count, payoff_count, commander_support):
    return (
        commander_support and theme_count >= 3 and payoff_count >= 1
    ) or (
        theme_count >= 5 and payoff_count >= 1
    )
```

## 8.4 Parasitic mechanic support

Parasitic mechanics need generator/payoff balance.

Apply this to:

```text
Energy
Food
Blood
Clues
Dice
Coin Flips
Mutate
Venture
Initiative
Incubate
Role tokens
Powerstones
Battles
Sagas
Ring temptation
Face-down mechanics
Rooms / Eerie
Manifest Dread
Survival
```

```python
def parasitic_theme_supported(generator_count, payoff_count):
    return generator_count >= 5 and payoff_count >= 2
```

## 8.5 If the niche gate fails

Classify as:

```text
secondary package
minor package
support package
manual review
```

Do not cut or protect niche cards blindly. Use context:

```text
Protect if the commander supports the mechanic and the card provides scarce density.
Review if the card is a payoff with too few generators.
Review if the card is an enabler with no conversion point.
```

---

# 9. Fringe Theme Gate

## 9.1 Fringe themes default to manual review

Fringe themes are playable, but usually fragile, low-support, meta-dependent, legality-sensitive, Rule Zero-sensitive, or user-intent-dependent.

Most fringe themes should not become primary without clear user intent.

## 9.2 Fringe primary gate

```python
def can_be_primary_fringe_theme(theme_count, payoff_count, commander_support, user_declared_theme):
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

## 9.3 Fringe secondary / minor gate

```python
def can_be_secondary_fringe_package(theme_count, payoff_count, commander_support, user_declared_theme):
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

## 9.4 If user intent is unknown

Classify as:

```text
manual_review_minor_package
possible cut if optimization is the goal
Rule Zero / legality review if needed
social-contract pressure review if needed
meta-dependent package if needed
flavor-first package if likely
```

Do not aggressively cut or protect fringe cards without user intent.

## 9.5 Required fringe language

Use this wording pattern:

```text
This looks like a fringe package rather than a core plan. I would not automatically cut it if this is intentional, but it needs manual review because the deck does not currently show enough support to make it reliable.
```

---

# 10. Emergent Package Gate

## 10.1 Emergent themes are the context layer

Emergent themes prevent the helper from asking only:

```text
What archetype is this closest to?
```

Instead ask:

```text
What is this deck actually trying to make happen, and what cards make that plan work?
```

## 10.2 Emergent primary gate

```python
def can_be_primary_emergent_package(package_count, payoff_count, commander_support, package_is_commander_defined):
    return (
        package_is_commander_defined
        and package_count >= 4
        and payoff_count >= 1
    ) or (
        commander_support
        and package_count >= 6
        and payoff_count >= 2
    ) or (
        package_count >= 9
        and payoff_count >= 3
    )
```

## 10.3 Emergent suppression rule

Emergent themes should suppress broad fallback labels if they explain the deck better.

```python
if emergent_package.gate_passed and broad_label.is_generic:
    broad_label.role = "suppressed_broad_archetype"
```

## 10.4 Explicit emergent packages to support

Support at least these emergent packages:

```text
Commander-Defined Single-Card Archetypes
Commander-Created Landfall
Commander-Created Artifact Token Landfall
Token Combat / Go-Wide-Go-Tall Hybrid
Plot / Crime / Outlaw Packages
Offspring
Gift
Forage
Expend
Rooms / Eerie
Manifest Dread
Survival
Treasure Tutor Chains
Artifact/Treasure Combo-Value
Slow Alternate Win Conditions
High-Power Value but Not Turbo Combo
Typal + Mechanic Hybrid
Bracket-Aware Stax / Hatebear Packages
Partner Pair-Defined Strategy
Background Pair-Defined Strategy
Multiple-Copy Exception Engines
```

---

# 11. Bracket and Power Are Modifiers, Not Primary Strategy

## 11.1 Do not add bracket signals to synergy score

The following should **not** add synergy score toward primary strategy:

```text
bracket_pressure
high_bracket_pressure
game_changer
fast_mana
free_interaction
efficient_tutor
high_power_value_piece
compact_combo_piece
slow_alt_win_condition
mass_land_denial
hard_lock
```

They should be tracked separately as:

```text
report_modifier
bracket_pressure
high_bracket_pressure
pregame_discussion
possible cut only if intended bracket is lower
```

## 11.2 Bracket pressure is not a cut by itself

A bracket-pressure card may be:

```text
Powerful and correct for the deck
Correct only at a higher bracket
Wrong for the intended table
Core but requiring pregame discussion
A possible cut only if lowering table power
```

Never automatically cut a card only because it has bracket pressure.

## 11.3 True turbo combo gate

Do not assign true turbo combo unless this gate passes:

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

If it fails, use:

```text
combo-adjacent value
compact backup combo
possible combo piece
manual combo review
possible bracket pressure
high-power value but not turbo combo
```

---

# 12. Required Candidate Role Assignment

Every detected strategy/theme/package should receive one of these roles:

```text
primary
secondary
minor_package
support_package
manual_review
suppressed_broad_archetype
report_modifier
```

## 12.1 Primary

Use only when:

```text
Gate passed
Commander support or overwhelming density exists
Payoff/enabler balance exists
Win path exists
The strategy explains the commander and deck structure
The strategy affects cut/protect logic
```

## 12.2 Secondary

Use when:

```text
It supports the primary plan
It shares resources with the primary plan
It provides backup finishers
It explains a meaningful group of cards
It is not merely incidental
```

## 12.3 Minor package

Use when:

```text
The package is real but small
It does not define the deck
It may support a few cards
It may be a budget/meta/pet package
It could become more relevant after upgrades
```

## 12.4 Support package

Use when:

```text
The package provides infrastructure
It helps execute the main plan
It is not a win condition by itself
```

Examples:

```text
Ramp in Token Combat
Protection in Voltron
Land ramp in Commander-Created Landfall
Mana fixing in Five-Color Legends
Cheap artifacts in Artifact Tap/Mana
```

## 12.5 Manual review

Use when:

```text
Evidence is thin
User intent matters
The theme is fringe
There is a resource conflict
A combo may be hidden
A card is both cuttable and protected
A package is salt/meta dependent
A Rule Zero or legality issue exists
```

## 12.6 Suppressed broad archetype

Use when:

```text
The broad label scored highly but a narrower gated strategy better explains the deck.
```

Always explain why.

## 12.7 Report modifier

Use when:

```text
The item changes power, bracket, legality, or table expectation but is not the deck's strategy.
```

---

# 13. Broad Archetype Suppression Details

## 13.1 Suppress Ramp-Control unless control density is real

Ramp-Control / Big Mana Value requires:

```text
High ramp density
Meaningful board wipe or mass removal density
Meaningful targeted removal or control density
High-mana finishers or mana sinks
A survival/stabilize/reset plan
Late-game inevitability
```

Suppress Ramp-Control when:

```text
Ramp supports combat/token/typal plan
Ramp supports activated abilities
Ramp supports Adventure/modal value
Ramp supports Dragon casting
Ramp supports landfall triggers
Ramp supports commander recasting
Removal density is normal Commander interaction only
Board wipe density is low
Commander directly supports a narrower plan
```

Use instead:

```text
Ramp support package
Ramp into Big Threats
Big Mana / Mana Storage
Mana acceleration support
```

## 13.2 Suppress Generic Tokens

Suppress Generic Tokens when a narrower token identity exists:

```text
Goblin Tokens
Vampire Tokens
Elf Tokens
Squirrel Tokens
Saproling Tokens
Thopter Tokens
Servo/Construct Artifact Tokens
Treasure / Clue / Food / Blood artifact-token economy
Commander-created token combat
Amass / Army
Offspring token-copy value
```

## 13.3 Suppress Generic Artifacts

Suppress Generic Artifacts when a narrower artifact identity exists:

```text
Equipment Voltron
Artifact Combat
Artifact Tap / Artifact Mana
Treasure Tutor Chain
Food Lifegain
Clue Draw Engine
Blood Discard / Madness
Vehicles
Powerstones
Artifact Token Economy
Commander-Created Artifact Token Landfall
```

## 13.4 Suppress Generic Goodstuff

Suppress Goodstuff unless:

```text
No mechanical plan passes a gate
No commander-defined plan is present
The deck is intentionally flexible
The commander rewards broad card quality rather than a specific engine
```

## 13.5 Suppress Generic Midrange

Suppress Midrange if the deck has a specific engine:

```text
Aristocrats
Reanimator
Landfall
Enchantress
Artifacts
Tokens
Spellslinger
Blink
Lifegain
Treasure
Exile Matters
Typal strategy
Commander-defined engine
```

## 13.6 Suppress Generic Combo

Suppress Combo if:

```text
Only one possible combo piece exists
The combo lacks tutors/protection/redundancy
The deck is mostly synergy value
The combo is backup only
The line is slow and visible
The combo conflicts with the deck's primary plan
```

Use:

```text
combo-adjacent value
possible combo package
compact backup combo
manual combo review
```

---

# 14. Operational Archetype-Specific Guardrails

## 14.1 Go-Wide / Go-Tall Token Combat

Use when commander/deck creates tokens and converts them into combat pressure, power scaling, counters, lifelink bodies, or attack-trigger value.

Primary priority rule:

```python
if commander_has_attack_trigger_payoff and commander_or_deck_makes_tokens:
    if token_maker_count + combat_synergy_count + counter_synergy_count + anthem_count + power_matters_count >= 6:
        prefer "Token Combat / Go-Wide-Go-Tall Hybrid"
        suppress "Ramp-Control" unless control_density_is_real
```

Protect:

```text
Token makers
Anthems
Power-matters payoffs
Go-wide finishers
Go-tall conversion pieces
Board protection
Haste
Combat draw
```

Review:

```text
Single-target buffs in mostly go-wide builds
Pure ramp with no conversion
Expensive threats that do not support token combat
Landfall cards if commander does not support landfall
```

## 14.2 Goblin Typal / Go-Wide Tokens

Use when Goblin density, Goblin tokens, Goblin commander support, sacrifice, damage, drain, or go-wide finishers are present.

Suppress Elf Typal unless actual Elf density exists.

Protect:

```text
Goblin token makers
Goblin lords
Sacrifice outlets
Death/damage payoffs
Haste enablers
Mana/sacrifice Goblins
Low-power Goblins that enable count or sacrifice
```

## 14.3 Vampire Tokens / Aristocrats / Drain

Use when commander-created tokens, death triggers, sacrifice, lifedrain, Blood tokens, or Vampire density shape the deck.

This beats Elf Typal and Ramp-Control when Vampire evidence is real.

Protect:

```text
Vampire token makers
Sacrifice outlets
Death-trigger payoffs
Lifedrain payoffs
Blood token support if connected
Vampire lords
Recursion
```

## 14.4 Pod / Creature Toolbox / Creature Chain

Use when the commander or deck repeatedly sacrifices, tutors, upgrades, or chains creatures by mana value or role.

This beats Elf Typal and Ramp-Control when creature chain structure exists.

Protect:

```text
Pod effects
Creature tutors
ETB creatures
Untap effects
Haste/protection for commander
Curve chain pieces
Silver bullets
Creature recursion
```

## 14.5 Activated Abilities / Power-Reduction Engine

Use when commander reduces activated ability costs, rewards activated abilities, uses power to discount abilities, or turns activated abilities into the main value engine.

This beats Ramp-Control if activated ability density and commander support exist.

Protect:

```text
Activated ability creatures/permanents
Power buffs
Mana sinks
Pingers
Untap effects
X abilities
Ability-copy effects
Commander protection
```

## 14.6 Equipment / Aura / Artifact Combat

Separate:

```text
Equipment Voltron: one primary equipped attacker, usually commander.
Aura Voltron: one primary enchanted attacker, usually commander.
Artifact Combat: multiple artifact/equipped/modified creatures attack as a board.
```

Suppress Ramp-Control and Legends Matter if Equipment/Aura density and commander combat payoff are real.

Protect:

```text
Equipment/Auras that provide protection, evasion, draw, or lethal pressure
Equip cost reduction
Auto-equip
Enchantress draw if Aura-focused
Artifact combat payoffs if board-focused
```

## 14.7 Adventure / Modal Value

Use when Adventure spells, modal permanent/spell dual-role cards, cost reduction, cast-from-exile, and Adventure payoff define the value engine.

This beats Ramp-Control for Beluna-style decks.

Protect:

```text
Adventure density
Adventure payoff
Cast-from-exile payoff
Cost reduction
Modal value cards
Cards that function as both early spell and later permanent
```

## 14.8 Dragon Typal / Dragon Copy / Dragon Tutor Chain

Separate:

```text
Dragon Copy / Token-Copy Value:
- Miirym-style commander copies Dragons.
- Dragon ETB/attack triggers and token copies are the value engine.

Dragon Tutor Chain / Dragonstorm:
- Tiamat, Dragonstorm, or Dragon tutor-chain package exists.
- Requires actual tutor-chain or fast combo package.

Dragon Treasure Ramp / Dragon Goodstuff:
- High-MV Dragon typal with ramp/cost reduction/Treasure.
```

Do not let Artifact/Treasure Tutor Chain steal Tiamat unless artifact economy is truly central.

Do not call Magda Dragonstorm/Tiamat unless actual Dragonstorm/Tiamat-style line exists.

## 14.9 Artifact Engine / Artifact Tap / Artifact Mana

Use for Urza/Meria-style decks where artifacts become mana, cards, creatures, constructs, or engine material.

This beats Ramp-Control if artifact tap/mana/card-advantage is the engine.

Protect:

```text
Cheap artifacts
Artifact tokens
Artifact card advantage
Construct token support
Tap-artifacts-for-mana support
Untap artifacts
Improvise/affinity support
Artifact recursion
```

## 14.10 Big Mana / Mana Storage / Mono-Green Mana Engine

Use for Omnath, Locus of Mana-style decks where mana storage, green mana production, mana sinks, untap mana, or large creature finishers define the deck.

This beats Ramp-Control when the deck is not control-oriented.

Protect:

```text
Mana doublers
Green mana production
Mana storage support
Mana sinks
Untap land/permanent effects
Large creature finishers
X spells if supported
```

## 14.11 Sphinx Typal / Cost Reduction / Topdeck Fact-or-Fiction

Use for Unesh-style decks where Sphinx density, cost reduction, topdeck/card selection, and repeated ETB fact-or-fiction effects define the plan.

This beats generic Topdeck Value.

Protect:

```text
Sphinx density
Sphinx cost reduction
ETB copy/blink if relevant
Topdeck selection
Card selection payoffs
High-MV Sphinxes with strong ETB/combat impact
```

## 14.12 Toughness Matters / Defender

Use when commander directly rewards toughness, defenders, high toughness, toughness-as-power, or toughness scaling.

This is high-priority commander-defined if commander directly rewards toughness.

Protect:

```text
High-toughness creatures
Defenders / Walls
Toughness payoff
Toughness-as-power effects
Toughness combat enablers
Commander protection
```

Suppress Ramp-Control and generic +1/+1 Counters if toughness is the commander-defined plan.

---

# 15. Package Classification Rules

## 15.1 Minor package examples

```text
A few landfall cards in a non-landfall commander deck -> minor Landfall package.
A small lifegain cluster in Vampire Drain -> support or minor package.
A couple graveyard recursion cards in Wheels -> support, not Graveyard deck.
A few political cards in a combat deck -> political support package.
One alternate win condition -> slow alternate win condition / manual review, not primary combo.
```

## 15.2 Support package examples

```text
Ramp in Dragon Typal
Land ramp in Commander-Created Landfall
Protection in Voltron
Cheap evasive creatures in Saboteur
Targeted interaction in Crime decks
Treasure in Prosper or Magda
Pillowfort in Superfriends
```

## 15.3 Manual review examples

```text
Fringe cards without user intent
Rule Zero components
Salt-heavy packages
Self-synergy conflicts
Combo-looking pieces without support
Powerful off-plan staples
Cards that are both cuttable and protected
```

---

# 16. Strategy-Aware Cut Logic

## 16.1 Cut by replaceability, not raw power

A possible cut is not always a bad card.

Cut pressure increases when a card is:

```text
Off commander plan
Off primary strategy
Off secondary strategy
A payoff without enablers
An enabler without payoff
Redundant in a crowded role
Too slow for the deck's engine
A broad goodstuff card in a focused shell
A fringe card without user intent
A bracket-pressure card above intended table
A package piece from a failed gate
```

## 16.2 Protect low-power high-synergy cards

Protect cards that are low raw power but structurally important:

```text
Cheap sacrifice fodder in Aristocrats
Small Elves in Elf Typal
Low-cost artifact token makers in Artifact Token Economy
Defenders in Toughness Matters
Cheap legends in Legendary Cascade
Cheap evasive creatures in Saboteur/Ninjas
Cheap artifacts in Artifact Tap/Mana
Relevant token makers in token typal decks
```

## 16.3 Wrong shell language

Use:

```text
This is a good card, but it may be the wrong shell because it does not support the commander, primary plan, or deck's main resource engine.
```

Do not use:

```text
This card is bad.
This card is useless.
```

## 16.4 Cut/protect conflict rule

If a card appears in both cut and protect logic:

```text
Move it to Conflict / Manual Review.
Explain why it is conflicted.
Do not present it as a final cut.
```

---

# 17. Replacement Logic

## 17.1 Categories before exact cards

Suggest replacement categories before exact cards unless the user has a collection database or asks for exact replacements.

Default categories:

```text
More ramp
More card draw
More targeted removal
More board wipes
More sacrifice outlets
More recursion
More finishers
More protection
More lands
Lower mana curve
More commander synergy
More token production
More graveyard setup
More artifact-token support
More typal density
More payoff density
More mana fixing
More enablers
More conversion points
```

## 17.2 Strategy-specific replacement priority

Use the primary strategy to choose replacements.

Examples:

```text
Token Combat -> more token makers, anthems, board protection, haste, combat payoff.
Treasure Tutor Chain -> more Treasure generation, tutor redundancy, protection, payoff.
Toughness Matters -> more high-toughness bodies, toughness payoffs, defender support.
Adventure Value -> more Adventure density, cast-from-exile support, modal value.
Political -> more incentive, protection, payoff, inevitability.
Niche parasitic mechanic -> more generators if payoff-heavy, more payoffs if generator-heavy.
Fringe theme -> theme-preserving replacements only if user intent is clear.
```

---

# 18. Required Report Behavior

The Strategy Read section must include:

```text
Strategy Read
------------------------------
Likely Primary Strategy:
Likely Secondary Strategy:
Possible Minor Packages:
Support Packages:
Manual Review Packages:
Suppressed Broad Archetypes:
Why Primary Beat Secondary:
Commander-Defined / Emergent Read:
Typal Strategy Read if relevant:
Political Strategy Read if relevant:
Bracket/Power Modifiers:
```

## 18.1 Likely Primary Strategy

State the highest-confidence gated strategy.

Example:

```text
Likely Primary Strategy:
Token Combat / Go-Wide-Go-Tall Hybrid
```

## 18.2 Likely Secondary Strategy

Only include if it meaningfully supports the primary plan.

Example:

```text
Likely Secondary Strategy:
Counters / Power-Matters Combat
```

## 18.3 Possible Minor Packages

Include real but non-defining packages.

Example:

```text
Possible Minor Packages:
- Landfall: present through several cards, but the commander does not directly reward landfall.
- Lifegain: appears as support, but it is not the primary win condition.
```

## 18.4 Support Packages

Include infrastructure that helps the main plan.

Example:

```text
Support Packages:
- Ramp: supports casting high-mana Dragons, but does not define a control shell.
- Protection: supports the Equipment Voltron plan.
```

## 18.5 Manual Review Packages

Include packages with uncertain intent, fringe status, missing payoff, legality/salt concerns, or hidden combo risk.

## 18.6 Suppressed Broad Archetypes

If a broad archetype scored high but was suppressed, explain why.

Example:

```text
Suppressed Broad Archetypes:
- Ramp / Big Mana scored highly from ramp and expensive threats, but it was suppressed because the commander and deck structure more directly support Token Combat / Go-Wide-Go-Tall Combat.
```

## 18.7 Why Primary Beat Secondary

Explain why the selected primary strategy beat plausible alternatives.

Example:

```text
Why Primary Beat Secondary:
Token Combat / Go-Wide-Go-Tall Hybrid was selected because the commander creates combat-based tokens and the deck contains token makers, combat payoffs, anthems, and power-scaling effects. Ramp was treated as support because it helps deploy threats but does not create a control plan.
```

## 18.8 Commander-Defined / Emergent Read

Include when commander text creates or strongly shapes a package.

Example:

```text
Commander-Defined / Emergent Read:
The commander is the engine for this package, so support cards that look generic, such as land ramp or token doublers, may be core to the deck's real plan.
```

## 18.9 Typal Strategy Read

Include if typal signals exist.

Template:

```text
Typal Strategy Read:
Creature Type:
Effective Typal Density:
Typal Payoff Count:
Strategy Shape:
Role:
Notes:
```

## 18.10 Political Strategy Read

Include if political signals exist.

Template:

```text
Political Strategy Read:
Political Axis:
Incentive:
Protection/Deterrence:
Payoff:
Inevitability:
Role:
Notes:
```

## 18.11 Bracket/Power Modifiers

Report bracket/power separately.

Template:

```text
Bracket/Power Modifiers:
- Game Changer / high-power value / fast mana / efficient tutor / mass land denial detected.
- This is a power or table-expectation modifier, not the deck's primary strategy.
- Consider pregame discussion or cuts only if the intended bracket is lower.
```

---

# 19. Scoring Model

Use additive scoring only before gates and suppression.

## 19.1 Positive score inputs

```yaml
score_inputs:
  commander_defined_engine:
    points: 6

  commander_strongly_supports_package:
    points: 5

  commander_lightly_supports_package:
    points: 2

  package_card:
    points: 1

  repeatable_enabler:
    points: 2

  payoff:
    points: 2

  conversion_point:
    points: 3

  clear_win_condition:
    points: 3

  bridge_card:
    points: 2

  high_synergy_low_power_context:
    points: 2

  typal_lord_or_typal_payoff:
    points: 2

  tutor_chain_piece:
    points: 2

  multiple_copy_exception_engine:
    points: 4
```

## 19.2 Zero-point report modifiers

These should not increase primary synergy score:

```yaml
zero_point_modifiers:
  bracket_pressure_card:
    points: 0
    note: Track separately from synergy score.

  fast_mana:
    points: 0
    note: Track as power-level signal.

  free_interaction:
    points: 0
    note: Track as power-level signal.

  game_changer:
    points: 0
    note: Track as bracket/pregame modifier.

  high_power_value_piece:
    points: 0
    note: Track as bracket/power modifier, not archetype identity.
```

## 19.3 Risk penalties

```yaml
risk_penalties:
  broad_fallback_stealing_primary:
    points: -5

  enablers_without_conversion:
    points: -3

  payoff_without_enablers:
    points: -4

  combo_piece_without_support_or_intent:
    points: -3

  bracket_pressure_above_intended_table:
    points: -3

  multiple_copy_exception_too_few_copies:
    points: -4

  slow_alt_win_without_protection:
    points: -4

  generically_good_wrong_shell:
    points: -3

  no_clear_win_condition:
    points: -5

  resource_conflict_between_linked_themes:
    points: -3

  incidental_common_creature_type:
    points: -3

  political_cards_without_incentive_engine:
    points: -4

  fringe_theme_without_user_intent:
    points: -4
```

## 19.4 Confidence bands

```yaml
confidence:
  high:
    - passes primary gate
    - commander support moderate or strong
    - enabler/payoff balance exists
    - clear win condition exists
    - broad fallback suppressed correctly
    - role in cut/replacement logic is clear

  medium:
    - partial gate success
    - commander support exists
    - density is medium
    - payoff exists but conversion may be unclear
    - likely secondary or strong minor package

  low:
    - isolated cards
    - weak commander support
    - no payoff or conversion point
    - likely manual review or minor package
```

---

# 20. Legacy Misclassification Guards to Preserve

Keep all previous v0.5.6 guardrails unless overridden by this hotfix.

## 20.1 Lathril-style decks

Expected:

```text
Primary: Elf Typal / Token Lifedrain
Secondary: Go-Wide Combat / +1/+1 Counters if supported
```

Do not classify as Voltron unless Equipment/Aura/go-tall density clearly exceeds Elf/token/lifedrain density.

## 20.2 Jodah-style decks

Expected:

```text
Primary: Legends Matter / Legendary Cascade
Secondary: Five-Color Legendary Value / Ramp into Big Threats
```

Do not classify as Creature Cost-Reduction without real cost-reduction or chain-casting density.

## 20.3 Magda-style decks

Expected:

```text
Primary: Treasure Tutor Chain
Secondary: Artifact Token Economy / Combo-Adjacent Value if supported
```

Do not classify as Dragonstorm/Tiamat without actual Dragonstorm/Tiamat package.

## 20.4 Nekusar-style decks

Expected:

```text
Primary: Wheels / Draw-Punisher
Secondary: Group Slug / Control if supported
```

Do not classify as Graveyard Recursion or Reanimator just because wheels fill graveyards.

## 20.5 Ghalta and Mavren-style decks

Expected:

```text
Primary: Token Combat / Go-Wide-Go-Tall Hybrid
Secondary: Counters, Lifegain, Ramp into Big Threats, or Big Creature Combat if supported
```

Do not trigger Toggo-style landfall/artifact-token logic.

## 20.6 Toggo-style partner decks

Expected:

```text
Primary or Secondary: Commander-Created Landfall / Artifact Token Landfall
```

Even if landfall density is low, commander text makes landfall/artifact-token support relevant.

## 20.7 Betor-style decks

Expected:

```text
Primary: Toughness Matters / Defender
```

Do not classify as generic +1/+1 Counters or Ramp-Control if toughness is commander-defined.

## 20.8 Prosper-style decks

Expected:

```text
Primary: Exile Matters / Treasure Engine
```

Do not classify as generic Midrange if cast-from-exile and Treasure conversion are central.

---

# 21. Final Hotfix Success Criteria

This file succeeds if the helper can:

```text
Use layered strategy detection instead of flat archetype scoring.
Keep broad macro-archetypes as frames, not default primary identities.
Promote micro-archetypes only when commander support, density, payoff, enabler, and win path exist.
Avoid calling one or two political cards a Politics deck.
Evaluate typal decks by strategy shape, not only creature type count.
Treat niche themes as valid only when supported.
Treat fringe themes as manual review unless user intent is clear.
Use emergent themes as the context layer for commander-defined packages.
Track bracket and power separately from primary strategy.
Suppress broad archetypes when narrower gated strategies explain the deck better.
Explain why a broad archetype was suppressed.
Explain why primary beat secondary.
Classify detected packages as primary, secondary, minor, support, manual review, suppressed, or report modifier.
Make cut recommendations based on replaceability and deck fit, not raw power.
Protect low-power/high-synergy cards when they support the real engine.
Flag powerful wrong-shell cards without calling them bad.
Avoid overfiring Ramp-Control, Elf Typal, Artifact/Treasure Tutor Chain, Generic Tokens, Generic Artifacts, and Generic Goodstuff.
```

---

# End of strategy_archetype_rules.md
