# Section 1: Macro-Archetypes in Commander

Version: v0.5.6-ready  
Purpose: Help the MTG Commander Deck Helper identify broad deck strategy, commander-defined game plans, synergy packages, off-plan cards, protected cards, cut pressure, and replacement needs.

Macro-archetypes are broad Commander deck identities such as Aggro, Midrange, Control, Combo, Stax, Tempo, Ramp, Toolbox, and Engine/Synergy Value.

Because Commander is multiplayer, singleton, 100-card, and commander-centered, macro-archetypes should be treated as broad strategic frames, not exact 60-card format labels.

A deck may have:
- One primary macro-archetype
- One or two secondary macro-archetypes
- Multiple mechanical micro-archetypes
- Several minor support packages

The helper should prefer commander-defined strategy over broad fallback archetypes.

---

## 1.1 Macro-Archetype Philosophy

Macro-archetypes should answer the question:

> What broad kind of Commander deck is this?

They should not override the more important question:

> What is this specific commander and decklist trying to do?

For example:
- A Ghalta and Mavren deck should usually read as Token Combat / Go-Wide-Go-Tall Combat, not generic Aggro.
- A Toggo partner deck with landfall artifact-token creation should preserve Commander-Created Landfall even if broad artifact or ramp signals are present.
- A Prosper deck should usually read as Exile Matters / Treasure Engine, not generic Midrange.

---

## 1.2 Macro-Archetype Priority Order

When identifying strategy, use this priority order:

1. Commander-defined strategy
2. Explicit decklist mechanical density
3. Recognizable hybrid archetype
4. Broad macro-archetype fallback
5. Minor package detection

Do not assign a broad macro-archetype as primary if a narrower, commander-supported strategy is clearly present.

Broad macro-archetypes that commonly overfire and should be suppressed unless strongly supported:
- Midrange / Value
- Ramp / Big Mana
- Control
- Engine / Synergy Value
- Combo-Adjacent Value

These may appear as secondary strategies or minor packages if the narrower commander plan is stronger.

---

## 1.3 Macro-Archetype Output Fields

For each detected macro-archetype, the helper should record:

```yaml
macro_archetype:
  name:
  role: primary | secondary | minor_package | support_package | manual_review
  confidence: low | medium | high
  evidence:
    commander_text:
    role_counts:
    card_patterns:
    synergy_packages:
  warning:
  cut_logic_impact:
  replacement_logic_impact:
```

---

## 1.4 Aggro

### Definition

Aggro decks pressure life totals through combat damage, commander damage, repeated attacks, tokens, or snowballing board presence.

### Commander-Specific Adjustment

Pure Aggro is uncommon in Commander because three opponents begin at 40 life each. Most Commander Aggro should be classified more narrowly as:
- Go-Wide Combat
- Go-Tall Combat
- Voltron
- Token Combat
- Extra Combat
- Combat Triggers
- Typal Aggro
- Commander Damage Control

### Detection Signals

Increase Aggro score when the deck has:
- High creature density
- Low-to-mid mana curve
- Attack triggers
- Combat damage triggers
- Anthems
- Evasion
- Haste enablers
- Extra combat effects
- Commander damage support
- Mass pump effects
- Token makers that support combat

### Suppression Rules

Suppress generic Aggro to secondary or minor if a narrower combat archetype exists.

Examples:
- Voltron present → use Voltron instead of Aggro
- Token density + anthems → use Go-Wide Combat
- Commander rewards attacking → use Combat Triggers
- Commander damage plan → use Voltron or Commander Damage Control

### Cut Logic Impact

Protect:
- Efficient attackers that trigger the commander
- Evasion pieces
- Haste enablers
- Anthems
- Extra combat effects
- Low-cost pressure pieces that support the plan

Review:
- Expensive creatures with no immediate combat impact
- Defensive cards that do not support aggression
- Value cards that slow the combat plan
- Off-theme haymakers

### Replacement Categories

- More haste
- More evasion
- More protection
- More anthem effects
- More extra combat support
- Lower mana curve
- More commander synergy

---

## 1.5 Midrange / Value

### Definition

Midrange decks use ramp, removal, card advantage, recursion, and efficient threats to accumulate resources and win through superior board position.

### Detection Signals

Increase Midrange score when the deck has:
- Balanced ramp, draw, removal, and threats
- Recursive value pieces
- Flexible interaction
- ETB value
- Graveyard recursion
- Strong standalone cards
- Repeated value engines
- No single dominant linear theme

### Primary Gate

Midrange may become primary only if:
- No commander-defined strategy is stronger
- No mechanical theme has high synergy density
- The deck appears intentionally flexible rather than unfocused

### Suppression Rules

Suppress Midrange if a stronger specific strategy exists, including:
- Aristocrats
- Reanimator
- Landfall
- Enchantress
- Artifacts
- Tokens
- Spellslinger
- Blink
- Lifegain
- Treasure
- Typal strategy

### Cut Logic Impact

Protect:
- Repeatable draw
- Flexible removal
- Recursion engines
- Commander-supported value pieces
- Efficient ramp
- Cards that bridge multiple roles

Review:
- Goodstuff cards that do not support commander plan
- Expensive value cards with low synergy
- Redundant midrange threats
- Cards that are generically strong but wrong for the shell

### Replacement Categories

- More card draw
- More targeted removal
- More ramp
- More recursion
- More board wipes
- More commander synergy

---

## 1.6 Control

### Definition

Control decks slow the table, answer threats, and establish inevitability through interaction, board wipes, pillowfort, counterspells, locks, or resilient finishers.

### Commander Adjustment

Commander control usually cannot rely only on one-for-one answers. It needs:
- Repeatable interaction
- Board wipes
- Strong card advantage
- Soft locks
- Pillowfort tools
- Clear win condition

### Detection Signals

Increase Control score when the deck has:
- High removal density
- Multiple board wipes
- Counterspells
- Pillowfort pieces
- Tax effects
- Graveyard hate
- Stack interaction
- Repeatable defensive engines
- Expensive finishers or inevitability engines

### Primary Gate

Control may become primary only if:
- Interaction density is high
- The deck has credible inevitability
- The commander supports control, card draw, taxation, or defensive value

### Suppression Rules

Suppress generic Control if the deck is more accurately:
- Stax / Prison
- Pillowfort
- Reanimator-Control
- Big Mana Control
- Commander Damage Control
- Spellslinger Control

### Cut Logic Impact

Protect:
- Board wipes
- Efficient interaction
- Repeatable control engines
- Card draw
- Finishers
- Protection for the control plan

Review:
- Low-impact creatures
- Combat-only cards with no control role
- Narrow answers with low relevance
- Expensive threats that do not stabilize or win

### Replacement Categories

- More board wipes
- More targeted removal
- More card draw
- More finishers
- More protection
- More graveyard hate
- More stack interaction

---

## 1.7 Combo

### Definition

Combo decks assemble card interactions that win immediately, create infinite resources, or generate overwhelming deterministic advantage.

### Detection Signals

Increase Combo score when the deck has:
- Known combo role patterns
- Infinite mana outlets
- Infinite sacrifice loops
- Infinite draw loops
- Compact two-card or three-card interactions
- Tutors
- Redundant combo pieces
- Protection for combo turn
- Fast mana
- Cost reducers
- Recursion loops

### Combo Classification

Separate combo into:

```yaml
combo_type:
  fair_synergy_combo:
  combo_adjacent_value:
  compact_combo:
  true_turbo_combo:
  deterministic_tutor_chain:
```

### Primary Gate

Combo should become primary only if:
- The deck has multiple combo pieces
- The commander supports assembly, tutoring, recursion, or payoff
- The deck has protection, tutors, redundancy, or speed
- The combo plan is more central than combat/value

### Suppression Rules

Do not classify as primary Combo just because a deck has:
- One alternate win condition
- One high-power value card
- One compact interaction
- One slow combo line without tutors
- One accidental infinite possibility

Instead label:
- Combo-adjacent value
- Possible combo package
- Manual review
- Bracket-pressure card

### Cut Logic Impact

Protect:
- Actual combo pieces
- Tutors
- Redundant enablers
- Protection
- Commander-supported combo outlets
- Draw/ramp that enables combo assembly

Review:
- Combo pieces with no support
- Slow alternate wins unsupported by the shell
- Tutors that raise bracket beyond user intent
- Narrow pieces that are dead outside combo

### Replacement Categories

- More tutors
- More protection
- More card selection
- More combo redundancy
- More mana acceleration
- More recursion
- Lower curve

---

## 1.8 Stax / Prison

### Definition

Stax and Prison decks restrict opponents through taxes, sacrifice requirements, untap denial, spell limits, graveyard hate, resource denial, or combat restrictions.

### Detection Signals

Increase Stax score when the deck has:
- Tax effects
- Rule-of-law effects
- Static hatebears
- Untap restriction
- Artifact/enchantment shutdown
- Graveyard hate
- Tutor hate
- Nonbasic land hate
- Sacrifice/resource denial
- Commander breaks parity

### Primary Gate

Stax should become primary only if:
- Multiple restriction pieces exist
- The deck can operate under its own restrictions
- The commander benefits from or ignores the restrictions

### Suppression Rules

If the deck has only a few hate pieces, classify as:
- Hatebear package
- Control support
- Meta call
- Bracket-pressure/manual review

### Cut Logic Impact

Protect:
- Stax pieces that the deck breaks parity on
- Low-cost hatebears
- Commander-supported restriction pieces
- Protection for lock pieces

Review:
- Symmetrical hate that hurts the deck equally
- Stax cards that conflict with commander plan
- High-salt pieces inappropriate for intended bracket
- Narrow hate with no local meta justification

### Replacement Categories

- More low-cost interaction
- More protection
- More parity-breaking support
- More card draw
- More finishers
- Less symmetrical hate if casual bracket

---

## 1.9 Tempo

### Definition

Tempo decks use cheap threats, evasion, disruption, bounce, and efficient interaction to stay ahead while pressuring opponents.

### Commander Adjustment

Tempo is uncommon as a standalone casual EDH macro-archetype and usually appears inside:
- Ninjas
- Rogues
- Faeries
- Pirates
- Saboteur
- Evasive combat
- Spellslinger tempo

### Detection Signals

Increase Tempo score when the deck has:
- Cheap evasive creatures
- Bounce spells
- Cheap counterspells
- Combat damage triggers
- Topdeck manipulation
- Flash threats
- Low curve
- Card draw from connecting
- Disruption plus pressure

### Suppression Rules

If a specific evasive/combat strategy exists, use that instead:
- Ninjutsu
- Saboteur
- Combat Damage Triggers
- Evasive Typal
- Yuriko-style Topdeck Damage

### Cut Logic Impact

Protect:
- Cheap evasive enablers
- Low-cost interaction
- Topdeck manipulation
- Cards that keep pressure while disrupting

Review:
- High-mana threats
- Clunky sorcery-speed cards
- Defensive cards that do not support pressure
- Expensive value pieces

### Replacement Categories

- More cheap evasive creatures
- More protection
- More bounce
- More card selection
- Lower curve
- More commander-trigger enablers

---

## 1.10 Ramp / Big Mana

### Definition

Ramp decks accelerate mana production to cast large threats, X-spells, haymakers, or activate mana-sink commanders.

### Detection Signals

Increase Ramp / Big Mana score when the deck has:
- High ramp count
- Mana doublers
- Mana dorks
- Land ramp
- Treasure ramp
- Cost reducers
- Untap-ramp
- Big mana payoffs
- X-spells
- High-MV threats
- Commander mana sink

### Primary Gate

Ramp / Big Mana may become primary only if:

```python
can_be_primary_ramp_big_mana = (
    role_counts["ramp"] >= RAMP_THRESHOLD
    and (
        role_counts["big_mana_payoff"]
        + role_counts["high_mv_payoff"]
        + role_counts["mana_sink"]
        + role_counts["x_spell"]
    ) >= PAYOFF_THRESHOLD
)
```

### Suppression Rules

Suppress generic Ramp / Big Mana if a narrower plan exists:
- Landfall
- Commander-Created Landfall
- Sea Monsters
- Eldrazi Ramp
- X-Spells
- Mana Sink Commander
- Stompy
- Big Mana Control
- Dragonstorm/Tiamat Tutor Chain
- Artifact Ramp

### Cut Logic Impact

Protect:
- Efficient ramp
- Mana doublers
- Untap-ramp with payoff support
- Payoffs that convert mana into wins
- Commander mana sinks
- Landfall enablers if commander cares about lands

Review:
- Ramp with too few payoffs
- Expensive payoffs with no immediate impact
- Mana rocks that do not support color needs
- Big threats that are off-plan

### Replacement Categories

- More payoff cards
- More card draw
- More lands
- Better ramp/fixing
- More mana sinks
- Lower curve if ramp is insufficient

---

## 1.11 Toolbox

### Definition

Toolbox decks use tutors, silver bullets, flexible answers, recursion, and modal cards to find the right piece for the current board state.

### Detection Signals

Increase Toolbox score when the deck has:
- Creature tutors
- Enchantment tutors
- Artifact tutors
- Legendary tutors
- Pod effects
- Recursion
- Silver-bullet answers
- Modal cards
- Flexible removal
- Commander tutoring ability

### Primary Gate

Toolbox may become primary if:
- Commander tutors or enables repeated access
- Deck has multiple narrow answers
- Deck has a clear search chain or silver-bullet package

### Suppression Rules

Separate from Combo:
- Toolbox finds answers and flexible value.
- Tutor Chain assembles a deterministic line.
- Turbo Combo uses tutors to win quickly.

### Cut Logic Impact

Protect:
- Flexible answers
- Tutor targets
- Cards that answer common board states
- Recursion engines
- Commander-supported silver bullets

Review:
- Silver bullets with no meta relevance
- Tutor targets that are too narrow
- Redundant answers
- Expensive one-shot effects

### Replacement Categories

- More flexible removal
- More tutor targets
- More recursion
- More card draw
- More protection
- More silver bullets only if meta-relevant

---

## 1.12 Engine / Synergy Value

### Definition

Engine/Synergy Value decks are built around repeated triggers or commander-supported value loops rather than a single classic macro-archetype.

### Detection Signals

Increase Engine/Synergy score when the commander or deck repeatedly rewards:
- Casting certain card types
- Creatures dying
- Gaining life
- Creating tokens
- Playing lands
- Drawing cards
- Sacrificing permanents
- Artifacts entering or leaving
- Enchantments being cast
- Cards being exiled or cast from exile

### Primary Gate

Engine/Synergy may become primary if:
- Commander is the central engine
- Multiple cards trigger the same engine
- The deck’s win condition emerges from repeated synergy

### Suppression Rules

Do not leave the deck labeled only as Engine/Synergy if a specific engine exists.

Prefer:
- Aristocrats
- Enchantress
- Artifacts
- Treasure
- Exile Matters
- Landfall
- Lifegain
- Tokens
- Spellslinger
- Blink
- Graveyard Matters

### Cut Logic Impact

Protect:
- Low-power but high-synergy enablers
- Repeatable triggers
- Engine payoffs
- Commander support cards
- Glue cards that connect multiple pieces

Review:
- Generically strong cards that do not trigger the engine
- Isolated synergy pieces
- Cards that require support not present in deck
- Expensive value cards that do not advance the engine

### Replacement Categories

- More commander synergy
- More engine enablers
- More payoff density
- More card draw
- More recursion
- More protection

---

# Global Macro-Archetype Scoring and Suppression Rules

## A. Commander-First Rule

The commander’s text should heavily influence archetype interpretation.

If commander supports a narrow strategy, that strategy should receive a commander support bonus.

Examples:
- Commander makes tokens on attack → Token Combat / Combat Triggers
- Commander cares about lands entering → Landfall / Lands Matter
- Commander rewards sacrifice → Aristocrats / Sacrifice
- Commander casts from exile → Exile Matters
- Commander rewards artifacts → Artifact Synergy
- Commander rewards enchantments → Enchantress
- Commander rewards lifegain → Lifegain / Lifedrain
- Commander rewards spells → Spellslinger

---

## B. Broad Archetype Suppression

After raw scores are calculated:

```python
if primary_candidate in broad_macro_archetypes:
    if narrower_commander_defined_strategy_exists:
        suppress_primary_candidate_to_secondary_or_minor()
```

Broad macro-archetypes include:
- Aggro
- Midrange / Value
- Control
- Ramp / Big Mana
- Engine / Synergy Value
- Combo-Adjacent Value

---

## C. Cut Review Principle

The helper should not say:
- “This card is bad.”

Prefer:
- “This card looks replaceable because it has lower commander synergy.”
- “This card is powerful, but it may belong to a different shell.”
- “This is a playtest-first review candidate.”
- “This is a bracket-pressure card, not an automatic cut.”
- “This card looks weak generically, but it supports the deck’s actual engine.”

---

## D. Replacement Logic Principle

Replacement recommendations should usually start with categories, not exact cards.

Use exact card suggestions only when:
- The user asks for them
- The collection system exists
- The card is a clear functional upgrade
- The bracket intent is known

Preferred replacement category output:
- More ramp
- More card draw
- More targeted removal
- More board wipes
- More sacrifice outlets
- More recursion
- More finishers
- More protection
- More lands
- Lower mana curve
- More commander synergy
- More token production
- More graveyard setup
- More artifact payoff
- More enchantment density
- More landfall enablers
- More combat payoff
