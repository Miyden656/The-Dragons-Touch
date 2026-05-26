# Deck Building Philosophy Rules

## Purpose

This file defines how **The Dragon’s Touch** should use Timmy/Tammy, Johnny/Jenny, Spike, their subtype philosophies, and Balanced / Unknown as a review lens for Commander deck analysis.

This philosophy layer must **not** replace strategy detection.

The deck’s primary strategy should still come from:
- commander text
- command-zone relationship
- decklist roles
- archetype gates
- card density
- payoff/enabler structure
- role tags
- user intent

The philosophy layer modifies:
- cut pressure
- replacement priorities
- report tone
- pet-card tolerance
- power optimization pressure
- acceptable inefficiency
- guide-specific questions
- protected-card explanation
- optional optimization focus

If philosophy is unknown, use **Balanced / Unknown** and avoid strong assumptions.

## Core Design Rule

> Strategy tells The Dragon’s Touch what the deck is trying to do.  
> Philosophy tells The Dragon’s Touch how the pilot wants that deck to be judged, protected, challenged, and guided.

A selected philosophy should never override:
- Commander legality
- color identity
- deck size rules
- required cuts
- user-declared constraints
- budget
- combo tolerance
- bracket/table goals
- strategy detection

---

# Philosophy Depth

The system should support three philosophy depths.

## 1. Balanced / Unknown

Use when:
- the user does not choose a philosophy
- batch mode is running without a global philosophy setting
- the deck’s pilot is unsure what they want
- the tool is discovering the deck’s natural direction

Balanced / Unknown should:
- avoid strong assumptions
- apply no subtype-specific protection by default
- review the deck through strategy, role balance, legality, and user intent
- optionally report possible philosophy lean without treating it as selected

## 2. Big 3 Philosophy

The user chooses one broad philosophy:
- Timmy / Tammy
- Johnny / Jenny
- Spike

This changes the broad review lens without applying a specific subtype.

## 3. Specific Philosophy Subtype

The user chooses one of the 18 subtypes.

The subtype is the rules object.  
The persona is the user-facing mentor voice.

---

# Big 3 Philosophies

## Timmy / Tammy

### Core Motivation

Timmy / Tammy wants the deck to feel good to play.

The deck is judged by the experience it creates: spectacle, theme, emotional resonance, big moments, favorite cards, table stories, and personal satisfaction.

### What The Player Values

- memorable plays
- emotional payoff
- theme and vibe
- splashy cards
- big board states
- favorite cards
- personal expression
- table reactions
- getting to do the thing

### What The System Should Protect

- declared pet cards
- theme-defining cards
- big payoff cards
- splashy finishers
- cards that create the desired experience
- support cards that help the deck reach the experience
- flavor cards with real mechanical role

### What The System Should Review More Aggressively

- cards that are big but not meaningful
- theme cards that prevent the deck from functioning
- splashy cards with too little support
- unsupported haymakers
- cards that do not help the pilot experience the deck’s goal
- generic upgrades that erase the deck’s identity

### Replacement Bias

Prefer cards that:
- preserve the deck’s experience
- make the desired moment happen more often
- support the theme
- protect important payoffs
- improve function without erasing joy

### Cut-Pressure Bias

Lower cut pressure on:
- cards that create the intended experience
- declared pet cards
- theme-defining cards
- payoff cards central to the deck’s identity

Increase cut pressure on:
- off-theme cards
- unsupported expensive cards
- cards that delay the deck’s desired experience
- generic good-stuff that weakens identity

### Report Tone

Warm, encouraging, emotionally validating, and honest about function.

### Common False Positives

Avoid:
- treating Timmy/Tammy as bad deck-building
- cutting every expensive card
- assuming the user does not care about winning
- protecting every splashy card automatically
- ignoring curve, ramp, draw, or interaction

### Example Report Language

> This card is not the most efficient option, but it strongly supports the deck’s intended experience. I would only cut it if it consistently prevents the deck from functioning or fails to create the moment the pilot wants.

---

## Johnny / Jenny

### Core Motivation

Johnny / Jenny wants the deck to prove an idea.

The deck is judged by whether it expresses and supports a specific engine, interaction, combo, constraint, commander exploit, weird card, or mechanical concept.

### What The Player Values

- clever interactions
- engines
- combos
- unusual cards
- hidden synergies
- self-imposed restrictions
- commander-specific text
- mechanical invention
- proving an idea works

### What The System Should Protect

- declared build-around cards
- engine pieces
- combo pieces
- connector cards
- weird cards with clear contextual purpose
- cards that bridge multiple themes
- constraint-compliant role-fillers
- low-power cards that are essential in context

### What The System Should Review More Aggressively

- synergy cards that do not actually connect
- unsupported build-arounds
- partial combos with no support
- weird cards that are just weird
- isolated mini-packages
- overcomplicated lines with too little payoff
- cards that violate the chosen restriction

### Replacement Bias

Prefer cards that:
- strengthen the deck’s idea
- improve engine consistency
- add redundancy for key interactions
- bridge packages together
- support the commander’s exact text
- preserve constraints
- make weird cards function

### Cut-Pressure Bias

Lower cut pressure on:
- weak-alone but strong-in-context cards
- engine connectors
- declared combo pieces
- bridge cards
- constraint-compliant role-fillers

Increase cut pressure on:
- unsupported oddities
- disconnected packages
- dead combo fragments
- clever-looking cards with no real function

### Report Tone

Curious, precise, puzzle-oriented, and careful with context-dependent cards.

### Common False Positives

Avoid:
- assuming Johnny/Jenny only means combo
- cutting weak-looking cards without checking their role
- calling every strange card synergy
- forcing the deck into a stock archetype
- ignoring density and support requirements

### Example Report Language

> This card looks weak by generic standards, but it may be a key connector in the deck’s engine. I would only cut it if the surrounding support does not make the interaction reliable.

---

## Spike

### Core Motivation

Spike wants the deck to perform.

The deck is judged by how well its choices convert into consistency, efficiency, interaction, win conversion, resilience, and appropriate power for the intended table.

Spike does not automatically mean cEDH.

### What The Player Values

- consistency
- efficiency
- role compression
- smooth mana
- strong card quality
- interaction
- clear win conditions
- table-appropriate power
- reducing dead draws
- avoiding preventable losses

### What The System Should Protect

- efficient ramp
- efficient draw
- flexible interaction
- clean role-fillers
- strong finishers
- reliable mana
- redundancy for the main plan
- power-level appropriate cards
- cards that improve the deck’s performance without violating constraints

### What The System Should Review More Aggressively

- overcosted effects
- narrow cards
- unsupported payoffs
- win-more cards
- clunky top-end
- low-impact cards
- bad-from-behind cards
- cards mismatched to the table
- cards that cannot justify their slot

### Replacement Bias

Prefer cards that:
- improve consistency
- lower curve pressure
- increase interaction quality
- convert advantage into wins
- improve role compression
- reduce dead draws
- fit the stated power band

### Cut-Pressure Bias

Lower cut pressure on:
- efficient role-fillers
- key interaction
- strong infrastructure
- consistent enablers
- clean finishers

Increase cut pressure on:
- inefficient, narrow, clunky, unsupported, or low-impact cards

### Report Tone

Direct, practical, performance-focused, and still respectful of user intent.

### Common False Positives

Avoid:
- applying cEDH standards unless requested
- cutting synergy pieces only because they look weak alone
- assuming stronger always means better
- ignoring table fit
- erasing the deck’s identity

### Example Report Language

> This card is playable, but it has high replaceability because it costs more mana than comparable effects and does not provide enough commander-specific synergy to justify the slot.

---

# Specific Philosophy Subtypes

## Timmy / Tammy Subtypes

### 1. Big Moment

Guide persona: Michael / Michelle

Core philosophy:
The player wants the deck to create one unforgettable, table-shaking payoff moment.

Protect:
- declared big-moment cards
- splashy finishers
- high-impact haymakers central to the deck’s desired experience
- X-spells or scalable payoffs
- copy, doubling, or amplification effects
- ramp and protection that make the big moment realistic

Challenge:
- expensive cards that do not create a memorable payoff
- unsupported haymakers
- win-more cards
- large cards unrelated to the intended moment
- clunky cards that do not improve the payoff

Recommendation bias:
- better ramp
- payoff support
- protection
- haste/evasion/trample for combat moments
- copy/doubling effects
- card draw or selection to find the payoff

Example:
> This card is expensive, but it supports the deck’s Big Moment philosophy because it creates the table-shaking payoff the pilot wants.

---

### 2. Big Creature / Stompy

Guide persona: Alexander / Alexandria

Core philosophy:
The player wants to cast huge threats, dominate combat, and win through overwhelming board presence.

Protect:
- large creatures central to the deck’s identity
- ramp into major threats
- trample, haste, evasion, and protection support
- power/toughness payoff cards
- creature-based card draw or removal
- attack/combat damage payoffs

Challenge:
- large creatures with no evasion, protection, or immediate impact
- redundant top-end threats
- ramp-light builds with too many expensive cards
- small value cards that dilute the stompy plan
- big creatures disconnected from the commander or strategy

Recommendation bias:
- ramp
- creature-based draw
- trample/evasion/haste
- protection
- more impactful threats
- cards that convert size into damage, draw, or removal

Example:
> This card fits the deck’s Big Creature / Stompy philosophy because it turns mana into visible board pressure.

---

### 3. Theme / Vibe

Guide persona: Benjamin / Bethany

Core philosophy:
The player wants the deck to feel like a specific story, aesthetic, tribe, character, joke, or emotional concept.

Protect:
- declared theme cards
- commander-lore cards
- typal identity pieces
- flavor cards with mechanical relevance
- cards that preserve the deck’s emotional identity
- cards that make the pilot happy to draw them

Challenge:
- flavorful but nonfunctional cards
- vague theme inclusions
- too many low-impact theme cards in key role slots
- generic staples that clash with the deck’s stated theme
- cards that pull the deck into the wrong identity

Recommendation bias:
- on-theme role-fillers
- flavorful removal/draw/ramp
- mechanically useful cards that preserve vibe
- finishers that match the deck’s story
- upgrades that improve function without erasing identity

Example:
> This card may be below rate, but it strongly supports the deck’s Theme / Vibe philosophy.

---

### 4. Pet Card

Guide persona: Milo / Mia

Core philosophy:
The player wants specific beloved cards protected because they matter personally, even if they are not optimal.

Protect:
- explicitly declared pet cards
- cards the pilot refuses to cut
- cards the pilot wants to experience at least once
- cards with stated personal or emotional value
- support pieces that intentionally make the pet card functional

Challenge:
- undeclared cards that look like pet cards but lack support
- pet-card packages that consume too much space
- support cards that are weak everywhere except one pet-card line
- pet cards that cause severe mana, curve, or color issues

Recommendation bias:
- improve the surrounding shell
- support the pet card if requested
- cut unrelated cards before declared pet cards
- clearly label performance cost without shaming the pilot

Example:
> This is a declared pet card, so I would not treat it as a normal cut candidate.

---

### 5. Let Me Do My Thing

Guide persona: William / Willow

Core philosophy:
The player wants the deck to reliably reach and execute the experience it was built to create.

Protect:
- core enablers
- ramp
- card draw
- protection
- redundancy for the stated plan
- setup pieces that make the deck function
- interaction that prevents the deck from being shut out

Challenge:
- off-plan cards that delay the main experience
- cute cards that do not help the deck do its thing
- splashy unrelated cards
- redundant payoffs without enablers
- packages that distract from the core plan

Recommendation bias:
- reliable enablers
- ramp/draw/protection
- commander support
- redundancy
- interaction that keeps the pilot alive long enough to participate

Example:
> This card supports the Let Me Do My Thing philosophy because it helps the deck reach its intended experience more often.

---

### 6. Battlecruiser

Guide persona: Aaron / Ariana

Core philosophy:
The player wants longer, larger Commander games where players build boards, cast powerful spells, and experience dramatic late-game turns.

Protect:
- big mana engines
- expensive payoffs that define the late game
- splashy fair finishers
- scalable spells
- recovery tools
- late-game card draw engines
- resilient threats
- interaction that keeps the game from ending too early

Challenge:
- fast combos that bypass the desired experience
- oppressive locks
- slow cards that are not impactful
- too many high-cost cards without enough ramp
- low-impact setup with no payoff
- upgrades that erase the Battlecruiser identity

Recommendation bias:
- better ramp
- late-game draw
- fair finishers
- board-based wins
- recovery tools
- splashy but functional interaction

Example:
> This card is slow by optimized standards, but it supports the deck’s Battlecruiser philosophy by creating a large-scale late-game Commander experience.

---

## Johnny / Jenny Subtypes

### 7. Engine Builder

Guide persona: Brad / Bria

Core philosophy:
The player wants the deck to assemble a repeatable machine where resources convert into more resources, value, inevitability, or a win.

Protect:
- core engine pieces
- repeatable enablers
- repeatable payoffs
- resource converters
- sacrifice outlets
- recursion pieces
- draw/mana engines
- weak-alone engine connectors

Challenge:
- one-shot effects that do not feed the engine
- payoffs without enough enablers
- enablers without enough payoffs
- resources the deck cannot use
- cards that only look synergistic

Recommendation bias:
- engine redundancy
- lower-cost enablers
- repeatable effects
- bridge cards
- protection/recursion for engine pieces
- finishers that emerge from the engine

Example:
> This card may look low-impact by itself, but it acts as an engine connector.

---

### 8. Commander Exploiter

Guide persona: Kyle / Katie

Core philosophy:
The player wants to push the commander’s specific text, wording, trigger, activated ability, restriction, or unusual angle as far as possible.

Protect:
- cards that directly interact with commander text
- trigger amplifiers
- ability enablers
- commander protection
- copy, untap, blink, recur, or reset effects when relevant
- cards that convert commander-generated resources
- backup pieces that imitate the commander’s role

Challenge:
- generic staples that ignore commander text
- cards that match colors but not the commander’s plan
- support for commander abilities the deck is not using
- commander-dependent cards without protection or backup

Recommendation bias:
- stronger commander synergy
- commander protection
- redundancy for key commander effects
- cards that multiply commander triggers or abilities
- backup engines for commander removal

Example:
> This card supports the Commander Exploiter philosophy because it interacts with the commander’s specific text rather than just the broader archetype.

---

### 9. Weird Card Rescuer

Guide persona: Elund / Emily

Core philosophy:
The player wants to make an overlooked, strange, bad-looking, or dismissed card meaningful in the right shell.

Protect:
- declared weird-card build-arounds
- strange cards with unique effects the deck clearly supports
- low-power cards with a specific engine role
- unusual cards with commander-specific relevance
- cards that are part of the declared experiment

Challenge:
- weird cards with no visible support
- unusual cards that do not advance the deck
- build-arounds requiring too much support for too little payoff
- cards that look clever but do not function
- support packages that weaken the deck without making the experiment reliable

Recommendation bias:
- support for the rescued card
- redundancy for its role
- protection/recursion for the build-around
- bridge cards that connect the weird card to the main strategy
- replacements that preserve the experiment

Example:
> This card looks weak by normal Commander standards, but it appears to be part of the deck’s Weird Card Rescuer philosophy.

---

### 10. Theme Mechanic Inventor

Guide persona: Brandon / Brenda

Core philosophy:
The player wants to combine mechanics, archetypes, or themes that do not normally go together and make the overlap work.

Protect:
- bridge cards
- hybrid payoffs
- flexible enablers
- cards that count toward multiple packages
- commander-specific cards that justify the blend
- support pieces that keep the hybrid identity coherent

Challenge:
- isolated mini-packages
- cards that only support one half of the deck
- themes that compete without overlap
- payoffs with too few enablers
- hybrid concepts where one side is ornamental
- cards that make the deck feel like two half-decks

Recommendation bias:
- cards that support both themes
- bridge payoffs
- overlap enablers
- flexible role-fillers
- cards that reduce theme dilution

Example:
> This card is valuable because it bridges the deck’s two mechanical themes rather than supporting one isolated package.

---

### 11. Self-Imposed Constraint Builder

Guide persona: Clark / Clarissa

Core philosophy:
The player wants the deck to succeed while obeying a chosen restriction, limitation, budget, card pool, or deck-building rule.

Protect:
- constraint-compliant role-fillers
- scarce legal options for needed roles
- unusual choices required by the limitation
- cards that preserve the premise
- weaker cards that are correct within the restricted pool

Challenge:
- cards that violate the stated restriction
- recommendations that ignore the restriction
- cards that technically fit but do not help the deck function
- weak role-fillers when better legal options exist within the constraint
- constraints that create structural weakness

Recommendation bias:
- legal upgrades inside the constraint
- creative substitutes
- constraint-compliant ramp/draw/removal/fixing
- honest weakness notes caused by the constraint

Example:
> This card is weaker than the unrestricted best-in-slot option, but it satisfies the deck’s constraint while filling a necessary role.

---

### 12. Combo Builder

Guide persona: Jasper / Jennifer

Core philosophy:
The player wants the deck to assemble specific card interactions, loops, or packages that produce a planned payoff.

Protect:
- declared combo pieces
- combo enablers
- tutors if allowed
- combo redundancy
- protection for the combo turn
- recursion for removed pieces
- weak-alone combo role players
- mana converters, sacrifice outlets, untappers, cost reducers, token converters, and win outlets required by the combo

Challenge:
- unsupported combo fragments
- combo cards dead outside one narrow line
- packages that consume too many slots
- combos that violate user tolerance
- combo pieces that pull away from the commander’s plan
- redundant combo pieces after enough support exists
- cards that look like combo pieces but do not complete a functional line

Recommendation bias:
- missing combo pieces
- redundancy
- power-appropriate tutors
- protection
- recursion
- lower-cost enablers
- clear win outlets
- cards that overlap with the main strategy when not comboing

Example:
> This card has low standalone impact, but it appears to be a required combo role-player.

---

## Spike Subtypes

### 13. Consistency Maximizer

Guide persona: Avery

Core philosophy:
The player wants the deck to do its intended thing more often by reducing non-games, dead draws, awkward hands, unsupported packages, and high-variance choices.

Protect:
- role-fillers that make the deck function
- ramp and fixing
- draw and selection
- redundant enablers
- backup versions of key effects
- flexible interaction
- cards that reduce fail states

Challenge:
- high-variance cards
- unsupported payoffs
- cards good only in ideal states
- bad-from-behind cards
- narrow dead cards
- isolated packages
- redundant top-end without setup

Recommendation bias:
- redundancy
- draw/selection
- reliable ramp/fixing
- lower-curve setup
- flexible interaction
- backup enablers
- higher-floor cards

Example:
> This card is powerful when everything lines up, but it creates consistency pressure because the deck does not have enough support to make that scenario happen often.

---

### 14. Efficiency Optimizer

Guide persona: Jordan

Core philosophy:
The player wants every card to justify its slot through strong rate, low opportunity cost, flexibility, clean role fulfillment, and meaningful contribution.

Protect:
- efficient ramp
- efficient draw
- flexible removal
- role-compression cards
- low-cost enablers
- strong floor/useful ceiling cards
- efficient synergy pieces

Challenge:
- overcosted effects
- narrow cards
- win-more cards
- low-impact haymakers
- cards requiring too much setup
- weaker versions of available effects
- playable but highly replaceable cards

Recommendation bias:
- lower mana value
- flexible effects
- better rate
- stronger role compression
- cheaper interaction
- efficient card advantage
- upgrades that reduce dead slots

Example:
> This card is playable, but it has high replaceability because it costs more mana than comparable effects.

---

### 15. Curve and Mana Discipline

Guide persona: River

Core philosophy:
The player wants the deck’s mana base, ramp, curve, and sequencing to support the plan cleanly from opening hand through late game.

Protect:
- lands and fixing
- ramp that matches the curve
- early setup
- cheap role-fillers
- curve bridges
- mana sinks when supported
- meaningful cost reducers
- boring infrastructure that prevents stumbling

Challenge:
- too many cards at five or more mana
- redundant expensive payoffs
- low land counts
- ramp that does not match deck needs
- color-intensive cards in shaky mana bases
- tapped lands in faster/color-sensitive decks
- early turns with nothing to do
- crowded curve slots

Recommendation bias:
- correct land count
- better fixing
- appropriate ramp
- curve smoothing
- early interaction/setup
- color requirement cleanup
- reducing top-end crowding

Example:
> This card may be powerful, but it adds pressure to an already crowded mana value.

---

### 16. Competitive Closer

Guide persona: Charlie

Core philosophy:
The player wants the deck to convert advantage into a decisive win instead of endlessly generating value without closing.

Protect:
- clear finishers
- compact win packages if allowed
- resource-to-lethal conversion
- combat closers
- inevitability pieces
- payoff cards that end games
- commander-damage support
- drain, burn, mill, overrun, alternate-win, or combo outlets when appropriate

Challenge:
- value engines with no payoff
- redundant setup after enough exists
- cards that prolong the game without advancing a win
- slow win conditions
- unrealistic payoff states
- finishers that violate power or combo tolerance

Recommendation bias:
- clearer finishers
- payoff cards that convert the main resource into victory
- compact win outlets
- combat finishers for board decks
- evasion/haste/trample for combat kills
- fewer pure value cards after enough setup exists

Example:
> The deck appears able to generate resources, but this card adds more value without helping convert that value into a win.

---

### 17. Power-Level Calibrator

Guide persona: Kai

Core philosophy:
The player wants the deck to land at the correct strength for the intended table, not simply become as strong as possible.

Protect:
- cards that fit the stated power band
- fair but effective win conditions
- table-appropriate interaction
- cards that preserve identity
- synergy pieces correct for the target environment
- pet/theme/splashy cards if the user accepts the performance cost
- cards aligned with pod expectations

Challenge:
- cards too weak for the stated power level
- cards too strong for the stated table
- compact combos that violate tolerance
- oppressive stax/lock/denial pieces if socially mismatched
- fast mana/tutors that overshoot
- slow cards in faster environments
- upgrades that erase deck identity

Recommendation bias:
- power-appropriate upgrades
- synergy and consistency over raw power when requested
- table-speed interaction
- finishers that fit combo tolerance
- alternatives that improve without overshooting
- optional upgrade tiers

Example:
> This card is powerful, but it may push the deck above the stated table expectation.

---

### 18. Interaction Controller

Guide persona: Riley

Core philosophy:
The player wants the deck to survive, answer threats, protect its plan, and avoid losing to preventable problems.

Protect:
- efficient removal
- flexible answers
- protection spells
- appropriate board wipes
- graveyard hate when relevant
- artifact/enchantment answers
- stack interaction when appropriate
- commander or engine protection
- interaction stapled to synergy pieces

Challenge:
- decks with too little interaction
- narrow answers without meta reason
- expensive removal
- sorcery-speed answers where instant speed matters
- commander-dependent decks with little protection
- decks that fold to common threats
- excessive interaction that erases the proactive plan

Recommendation bias:
- flexible removal
- efficient protection
- interaction matching deck colors
- answers that support the main strategy
- board wipes that spare or benefit the deck when possible
- resilience against likely failure points

Example:
> This deck is proactive, but it currently has limited ways to answer opposing engines once they resolve.

---

# Interaction With Cut Logic

Philosophy modifies optional cut logic, but it must not override required deck legality.

## Required Cuts

If the deck is over 100 cards:
- required cuts remain mandatory
- philosophy should help choose the least painful cuts
- protected cards should be cut only after lower-priority options are exhausted
- if all remaining cuts conflict with philosophy protection, label the conflict clearly

## Optional Optimization Cuts

If the deck is legal:
- philosophy can increase or reduce optional cut pressure
- Timmy/Tammy should be more tolerant of emotionally important or experiential cards
- Johnny/Jenny should be more tolerant of weak-alone context cards
- Spike should apply more pressure to inefficient, narrow, or low-impact cards
- Balanced / Unknown should avoid aggressive assumptions

## Pet-Card Treatment

Declared pet cards:
- should be protected from normal cut recommendations
- may receive performance notes
- may be listed as protected or manual-review cards
- should only be recommended as cuts if the user asks for no-mercy optimization

## Synergy Protection

High-synergy, low-raw-power cards:
- should not be cut by raw power logic alone
- should be protected if they serve the commander, primary strategy, or selected philosophy
- should be reviewed if the support package is too thin

## Power-First Recommendations

Power-first recommendations should be filtered by:
- selected philosophy
- table power level
- combo tolerance
- budget
- user constraints
- deck identity

Stronger does not always mean better for the selected philosophy.

---

# Interaction With Build-Up Mode

In build-up mode, philosophy shapes what missing pieces matter most.

## Timmy / Tammy Build-Up Bias

Recommend cards that:
- create the desired experience
- support big moments
- preserve theme
- protect pet cards
- make the deck feel like itself
- let the deck do its thing

## Johnny / Jenny Build-Up Bias

Recommend cards that:
- complete engines
- support unusual interactions
- add redundancy to build-arounds
- preserve constraints
- bridge hybrid themes
- clarify combo lines

## Spike Build-Up Bias

Recommend cards that:
- improve consistency
- fill role gaps
- smooth curve and mana
- increase interaction
- add clearer finishers
- match intended power level

## Balanced / Unknown Build-Up Bias

Recommend broadly useful role-fillers while identifying possible philosophy directions.

Do not overcommit to a philosophy unless the user chooses one.

---

# Interaction With Batch Mode

Batch auto should default to **Balanced / Unknown** unless a philosophy is provided globally.

If batch mode has no philosophy:
- use Rowan / Balanced Unknown
- avoid strong assumptions
- do not apply subtype-specific protection
- may report likely philosophy lean
- may recommend that the user rerun a deck with a specific guide if desired

If batch mode has a global philosophy:
- apply that philosophy to every deck
- clearly label the global philosophy in each report
- avoid assuming individual deck pilots share that philosophy unless the user says so

If batch mode has per-deck philosophy metadata:
- apply each deck’s selected philosophy independently
- include the selected guide in each report

---

# Report Requirements

Every report with philosophy enabled should include:

```md
## Philosophy Guide

**Selected Lens:** <philosophy or subtype>
**Guide:** <resolved persona name or none>
**Parent Philosophy:** <Timmy/Tammy, Johnny/Jenny, Spike, or Balanced/Unknown>
**Primary Question:** <guide question>

<brief explanation of how the guide affects this review>
```

If no philosophy is selected:

```md
## Philosophy Guide

**Selected Lens:** Balanced / Unknown
**Guide:** Rowan
**Primary Question:** What path does this deck naturally want to follow?

No specific philosophy was selected, so this report avoids strong assumptions and reviews the deck through a balanced exploratory lens.
```
---

# Implementation Status — v1.1.9

As of **v1.1.9**, the philosophy system has moved from design-only guidance into a safe, modular support layer.

The active implementation layer currently provides:

- `philosophy_profile.py` — structured user philosophy profile data
- `philosophy_registry.py` — canonical philosophy and subtype registry
- `persona_registry.py` — user-facing guide/persona registry
- `runtime_config_mapping.py` — safe runtime/config-to-profile mapping
- `report_section.py` — reusable `## Philosophy Guide` report section formatting
- `cut_language.py` — philosophy-aware cut-pressure language helpers
- `protected_language.py` — philosophy-aware protected-card language helpers
- `replacement_language.py` — philosophy-aware replacement-direction language helpers
- `report_integration_preview.py` — preview-only report integration helpers

## Current Runtime Boundary

As of v1.1.9, the philosophy layer **does not yet**:

- change cut scoring
- choose cut candidates
- change deck analysis
- change strategy detection
- change replacement candidate selection
- recommend exact replacement cards
- modify generated reports automatically
- modify UI behavior automatically
- override commander legality
- override color identity
- override deck size rules
- override user-declared constraints
- override bracket, budget, table-power, or combo-tolerance settings

## Current Intended Use

The implemented philosophy layer is currently safe to use for:

- validating philosophy/profile data
- resolving guide/persona presentation
- producing a philosophy guide report section
- producing preview-only philosophy-aware report language
- generating cut-pressure phrasing
- generating protected-card phrasing
- generating replacement-direction phrasing

The implementation is intentionally staged so philosophy can be integrated into actual reports before it influences cut or replacement behavior.

## Integration Rule

Until a later patch explicitly wires philosophy into active analysis behavior, these markdown rules remain the design authority and the Python philosophy modules remain support utilities.

The philosophy layer should continue to obey the core rule:

> Strategy tells The Dragon’s Touch what the deck is trying to do.  
> Philosophy tells The Dragon’s Touch how the pilot wants that deck to be judged, protected, challenged, and guided.
