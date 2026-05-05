# Deck Building Philosophy Rules

## Purpose

Define how **The Dragon’s Touch** should use deck-building philosophy as a review lens during Commander deck analysis.

This rule file introduces the core player-philosophy layer:

- Timmy / Tammy
- Johnny / Jenny
- Spike
- Balanced / Unknown

These philosophies help the system understand **why** the pilot may value certain cards, lines, inefficiencies, packages, or deck-building choices.

This philosophy layer is a modifier. It must never replace strategy detection.

---

## Philosophy Layer Placement

### Core Rule

Deck-building philosophy is a review lens, not a strategy engine.

The system must still determine the deck’s primary strategy from:

- commander text
- partner commander interaction
- decklist roles
- archetype gates
- mechanical theme density
- payoff and enabler counts
- user-stated intent
- known Commander strategy patterns

The philosophy layer modifies how the system interprets and presents the review after strategy detection has already happened.

### What Philosophy May Modify

The philosophy layer may affect:

- cut pressure
- optional optimization cuts
- replacement priorities
- report tone
- pet-card tolerance
- tolerance for inefficiency
- power optimization pressure
- how aggressively generically strong upgrades are recommended
- how aggressively narrow cards are protected or questioned
- how much the report prioritizes experience, expression, power, or elegance

### What Philosophy Must Not Modify

The philosophy layer must not:

- override the commander’s actual mechanical identity
- invent a strategy not supported by the decklist
- force a deck into a philosophy that the user did not choose
- treat philosophy as an archetype
- make primary strategy names include the commander name
- excuse required legality fixes
- protect cards that violate the user’s stated goals
- ignore user instructions about power level, budget, pet cards, or desired play experience

---

## Unknown Philosophy Default

If the user does not provide a deck-building philosophy, use:

**Balanced / Unknown**

When philosophy is unknown, the system should avoid strong assumptions about the pilot’s motivation.

Do not assume the pilot wants maximum power.
Do not assume the pilot wants maximum spectacle.
Do not assume the pilot wants elaborate combo expression.
Do not assume the pilot wants to keep inefficient cards for emotional reasons.

Instead, use normal strategy-aware Commander review logic and explain uncertain cases as review points rather than hard conclusions.

---

# Philosophy Definitions

---

## Timmy / Tammy

### Core Motivation

Timmy / Tammy players are motivated by big experiences, emotional payoff, memorable moments, splashy plays, and the feeling of doing something awesome.

They often value the story created by the deck as much as the raw win percentage.

The deck does not need to be perfectly efficient if it creates the kind of game experience the pilot wants.

### What the Player Values

Timmy / Tammy players often value:

- huge creatures
- dramatic board states
- big combat steps
- memorable haymakers
- splashy spells
- high-impact finishers
- cards with emotional attachment
- cards that create table reactions
- pet cards with personal meaning
- win conditions that feel earned or cinematic
- funny, ridiculous, or once-in-a-lifetime plays

### What the System Should Protect

The system should be more willing to protect:

- pet cards the user identifies as emotionally important
- splashy finishers that support the deck’s intended experience
- large threats that align with the primary strategy
- high-mana cards that are inefficient but meaningful to the deck’s goal
- cards that create the pilot’s desired memorable moment
- cards that are not optimal but are central to the deck’s identity
- cards that support a clear table-story or big-play payoff

Protection does not mean the card is always correct. It means the system should avoid casually cutting it only because it is inefficient.

### What the System Should Review More Aggressively

The system should review more aggressively:

- low-impact cards that do not contribute to the big-play experience
- filler cards that neither ramp into nor protect the deck’s payoffs
- expensive cards that are not exciting, synergistic, or important
- cards that slow the deck down without increasing spectacle
- redundant small effects that do not help the deck reach its big moments
- generically efficient cards that make the deck less fun for this pilot

### Replacement Bias

Replacement recommendations should lean toward:

- bigger payoffs
- stronger finishers
- more ramp to reach expensive cards
- more protection for signature threats
- more ways to enable the deck’s biggest turns
- more dramatic win conditions
- more cards that support the pilot’s stated favorite play pattern

The system should avoid replacing every inefficient card with the most efficient staple unless the user requests optimization.

### Cut-Pressure Bias

Timmy / Tammy decks should apply lower optional cut pressure to cards that are:

- emotionally important
- splashy
- memorable
- on-plan
- tied to the pilot’s desired experience
- inefficient but functional in the deck’s intended game plan

They should apply higher cut pressure to cards that are:

- small and forgettable
- off-plan
- low-impact
- neither enabling nor rewarding the big-play plan
- efficient but emotionally or strategically irrelevant

### Report Tone

The report tone should be encouraging, experience-aware, and careful not to flatten the deck into pure optimization.

The system should acknowledge the pilot’s desired moments and frame improvements around helping those moments happen more often.

### Common False Positives

The system should avoid these mistakes:

- treating every expensive spell as a bad card
- cutting a beloved pet card because it is inefficient
- assuming the pilot wants the lowest possible curve
- replacing splashy finishers with generic value staples
- calling big, emotional cards wrong when they are central to the deck’s fun
- over-prioritizing competitive efficiency in a casual spectacle-focused deck

### Example Report Language

- “This card is not the most efficient option, but it clearly supports the kind of big moment this deck wants to create.”
- “I would not cut this just for curve reasons unless you decide the deck is failing to reach its late-game payoffs.”
- “The better upgrade path is not to make the deck smaller emotionally, but to add more ramp and protection so your biggest cards actually matter.”
- “This is a reasonable keep for a Timmy/Tammy build because it supports the deck’s table-impact goal.”

---

## Johnny / Jenny

### Core Motivation

Johnny / Jenny players are motivated by creativity, expression, clever interactions, unusual lines, hidden synergy, and making the deck do something distinctive.

They often value proving that a strange card or unusual package has a purpose.

The deck does not need to use the most obvious route if it expresses the pilot’s idea well.

### What the Player Values

Johnny / Jenny players often value:

- unusual synergies
- build-around cards
- clever engines
- strange interactions
- alternate win conditions
- puzzle-like sequencing
- cards that look weak until the deck context explains them
- hidden role compression
- unique commander interpretations
- synergy density over raw rate
- expressive deck identity

### What the System Should Protect

The system should be more willing to protect:

- narrow synergy pieces with clear deck relevance
- cards that enable the deck’s unique engine
- cards that look weak generically but are strong in context
- build-around cards named by the user
- unusual payoffs that support the user’s intended line
- combo-adjacent value pieces that are not obvious staples
- cards that bridge multiple internal packages
- role-players that support a nonstandard plan

Protection should be based on actual synergy evidence, not merely on the card being strange.

### What the System Should Review More Aggressively

The system should review more aggressively:

- generic goodstuff that does not support the deck’s unique idea
- cards that dilute the central engine
- redundant staples that crowd out synergy pieces
- cards that only increase raw power but weaken expression
- cards that appear clever but have too few enablers or payoffs
- cute interactions that are too unsupported to matter
- narrow cards with no clear path to usefulness

### Replacement Bias

Replacement recommendations should lean toward:

- better enablers
- better payoffs for the unique engine
- more tutors or selection if appropriate for the power level
- more redundancy for the key interaction
- more protection for fragile engine pieces
- more card flow that helps assemble the deck’s idea
- exact role replacements that preserve the deck’s identity

The system should prefer replacements that make the idea work better, not replacements that erase the idea.

### Cut-Pressure Bias

Johnny / Jenny decks should apply lower optional cut pressure to cards that are:

- narrow but clearly synergistic
- strange but intentional
- low-power but engine-critical
- part of the user’s stated build-around concept
- useful in a specific interaction that the deck can realistically assemble

They should apply higher cut pressure to cards that are:

- generically strong but off-plan
- unrelated staples
- cute but unsupported
- redundant without helping the core engine
- included only because they are powerful in other decks

### Report Tone

The report tone should be curious, precise, and synergy-aware.

The system should explain what the card appears to be doing before recommending it as a cut.

The report should separate:

- “this is weak”
- “this is unsupported”
- “this is clever but needs more density”
- “this is strange, but it belongs”

### Common False Positives

The system should avoid these mistakes:

- cutting narrow cards before checking the engine they support
- mistaking low raw power for low synergy
- recommending generic staples that reduce deck expression
- treating unusual win conditions as mistakes
- assuming every weird card is a pet card rather than a role-player
- calling a card off-theme because it supports the strategy indirectly

### Example Report Language

- “This looks weak by generic standards, but it appears to be part of the deck’s engine, so I would not treat it as a normal cut.”
- “This card is clever, but the deck may need more enablers before it becomes reliable.”
- “The better replacement is not a generic staple; it is another card that performs the same engine role more consistently.”
- “This is a Johnny/Jenny-style keep: narrow, intentional, and worth protecting if this interaction is part of the deck’s identity.”

---

## Spike

### Core Motivation

Spike players are motivated by performance, consistency, clean decision-making, strong card quality, efficient wins, and improving the deck’s ability to execute its plan.

Spike does not always mean competitive or cEDH. A casual Spike may still want the deck to perform as well as possible within a chosen power band, budget, or table agreement.

### What the Player Values

Spike players often value:

- consistency
- efficiency
- strong card quality
- low dead-card count
- clean mana curve
- reliable engines
- optimized role balance
- powerful interaction
- clear win conditions
- reduced variance
- cards that perform well from behind, at parity, or ahead
- upgrades that increase the deck’s actual win rate within constraints

### What the System Should Protect

The system should be more willing to protect:

- efficient ramp
- efficient draw
- premium interaction
- compact win conditions
- high-impact synergy pieces
- cards that increase consistency
- cards that improve velocity
- cards that protect the deck’s main path to victory
- flexible role-compression cards
- proven staples that strongly support the deck’s plan

Protection should be based on performance and relevance to the actual strategy, not name recognition alone.

### What the System Should Review More Aggressively

The system should review more aggressively:

- inefficient pet cards
- win-more cards
- high-cost cards with low immediate impact
- narrow effects without enough payoff
- unsupported subthemes
- cards that are only good when already ahead
- redundant expensive finishers
- slow engines that do not match the chosen power level
- cards included for flavor but not function
- cute lines that reduce consistency

### Replacement Bias

Replacement recommendations should lean toward:

- lower curve
- more efficient ramp
- more efficient draw
- better interaction
- stronger protection
- better mana base consistency
- more reliable finishers
- higher synergy density
- cleaner win paths
- cards that increase the deck’s ability to execute its primary plan

The system may recommend exact stronger cards more often for Spike decks, especially when the user welcomes optimization.

### Cut-Pressure Bias

Spike decks should apply higher optional cut pressure to cards that are:

- inefficient
- overly narrow
- slow
- redundant
- unsupported
- low-impact
- mostly emotional inclusions
- inconsistent with the stated power target

They should apply lower cut pressure to cards that are:

- efficient
- role-dense
- strategically necessary
- high-impact
- core to the deck’s primary game plan
- strong within the user’s chosen power band

### Report Tone

The report tone should be direct, practical, and performance-focused.

The system should still avoid insulting the user’s choices. It should frame cuts around performance pressure, not personal taste.

### Common False Positives

The system should avoid these mistakes:

- assuming Spike always means cEDH
- ignoring budget, table expectations, or user constraints
- cutting synergy cards only because they are not staples
- recommending raw power that conflicts with the deck’s actual plan
- overcorrecting a casual deck into a different power band
- treating every pet card as automatically wrong

### Example Report Language

- “This card is playable, but it has higher cut pressure in a Spike-leaning review because it is slower than the deck’s other options.”
- “The replacement should improve consistency rather than simply add another payoff.”
- “This is a good card, but it may be the wrong card if the goal is tighter execution of the primary plan.”
- “Within your stated power band, this upgrade increases reliability without changing the deck’s identity.”

---

## Balanced / Unknown

### Core Motivation

Balanced / Unknown represents either an unknown philosophy or a pilot who wants a middle-ground review.

The system should use the deck’s stated strategy, power target, budget, and user preferences without strongly weighting toward spectacle, expression, or optimization.

### What the Player Values

Balanced / Unknown players may value:

- functional deck performance
- commander synergy
- reasonable consistency
- keeping the deck’s identity intact
- avoiding obvious weak points
- preserving some fun or pet-card space
- improving the deck without over-optimizing it

### What the System Should Protect

The system should protect:

- commander support cards
- primary-plan enablers
- primary-plan payoffs
- important ramp and fixing
- important draw engines
- important interaction
- user-identified pet cards
- cards with clear contextual synergy
- cards that support the stated deck experience

### What the System Should Review More Aggressively

The system should review more aggressively:

- clearly off-plan cards
- low-impact cards
- unsupported subthemes
- replaceable filler
- redundant effects beyond the deck’s needs
- expensive cards with unclear payoff
- generically good cards that do not fit the deck

### Replacement Bias

Replacement recommendations should lean toward:

- stronger commander synergy
- better role balance
- more consistent ramp and draw
- enough interaction for the stated power level
- replacements that support the primary and secondary strategy
- upgrades that respect budget and user preference

### Cut-Pressure Bias

Balanced / Unknown decks should use normal cut pressure.

Do not protect cards only because they might be emotional.
Do not cut cards only because they are inefficient.
Do not assume the pilot wants maximum power.
Do not assume the pilot wants maximum uniqueness.

### Report Tone

The report tone should be neutral, helpful, and strategy-first.

The system should explain when a card is a possible cut, when it is protected, and when it needs manual review.

### Common False Positives

The system should avoid these mistakes:

- assuming an unknown pilot is a Spike
- assuming an unknown pilot wants to protect every pet card
- assuming an unknown pilot values weird synergy over consistency
- making strong claims without user-provided philosophy
- pushing the deck into a different identity

### Example Report Language

- “With no philosophy selected, I would treat this as a normal optional optimization candidate rather than a required cut.”
- “This card is not clearly wrong, but it is replaceable if you want to tighten the deck.”
- “I would review this manually because it may be a pet card, but the decklist alone does not prove that.”
- “This recommendation is based on strategy fit rather than an assumed player preference.”

---

# Interaction With Cut Logic

## General Rule

Philosophy modifies cut logic only after the system has already identified:

- required cuts
- optional optimization cuts
- protected cards
- possible cuts
- recommended cuts
- manual-review cards
- primary and secondary strategy fit
- role balance concerns

Philosophy should adjust the pressure and wording, not erase the underlying analysis.

---

## Required Cuts

Required cuts are legality fixes.

If a deck is over 100 cards, the system must still identify enough cuts to reach a legal Commander deck size.

Philosophy may change which cards are preferred as cuts, but it must not remove the need for required cuts.

### Timmy / Tammy Required Cuts

When required cuts are needed, avoid cutting the deck’s biggest emotional payoffs first unless they are completely unsupported.

Prefer cutting:

- low-impact filler
- off-plan utility cards
- small effects that do not help the deck reach its big moments
- redundant pieces that do not support the desired experience

### Johnny / Jenny Required Cuts

When required cuts are needed, avoid cutting unusual synergy pieces before checking whether they support the deck’s engine.

Prefer cutting:

- generic goodstuff that dilutes the concept
- unsupported clever cards
- off-plan staples
- redundant pieces that do not help assemble or protect the engine

### Spike Required Cuts

When required cuts are needed, prioritize performance and role efficiency.

Prefer cutting:

- slow cards
- low-impact cards
- inefficient pet cards
- redundant expensive cards
- narrow cards without enough payoff
- cards that lower consistency

### Balanced / Unknown Required Cuts

When required cuts are needed, use normal strategy-aware cut logic.

Prefer cutting:

- off-plan cards
- low-impact cards
- redundant cards
- unsupported packages
- cards with weak commander or strategy support

---

## Optional Optimization Cuts

Optional optimization cuts are not legality fixes.

They should be presented as review candidates, not mandatory changes.

### Timmy / Tammy Optional Cuts

Optional cut pressure should be lighter on splashy, memorable, or emotionally important cards.

The system should ask whether the card helps create the desired moment before treating it as replaceable.

### Johnny / Jenny Optional Cuts

Optional cut pressure should be lighter on narrow synergy pieces with clear engine relevance.

The system should distinguish unsupported clever cards from hidden-role synergy cards.

### Spike Optional Cuts

Optional cut pressure should be stronger.

The system should more readily identify replaceable cards when they reduce consistency, speed, or efficiency.

### Balanced / Unknown Optional Cuts

Optional cut pressure should remain moderate.

The system should identify possible optimization cuts without assuming the user wants an aggressively optimized list.

---

## Pet-Card Treatment

User-identified pet cards should always be handled carefully.

### Timmy / Tammy

Pet-card tolerance is high.

The system should protect pet cards unless they directly undermine the deck’s stated goals or required cuts leave no better options.

### Johnny / Jenny

Pet-card tolerance is moderate to high if the pet card also supports the deck’s concept, engine, or unique expression.

If the pet card is unsupported, recommend building more around it or clearly labeling it as a protected personal inclusion.

### Spike

Pet-card tolerance is lower, but not zero.

The system may recommend keeping a pet card if the user explicitly wants it, but should clearly explain the performance cost.

### Balanced / Unknown

Pet-card tolerance is moderate when the user identifies the card.

If the user has not identified pet cards, do not assume emotional attachment from the decklist alone.

---

## Synergy Protection

Philosophy changes how aggressively synergy pieces are protected.

### Timmy / Tammy

Protect synergy pieces that help create the deck’s biggest, most memorable moments.

### Johnny / Jenny

Protect synergy pieces that are part of the deck’s unique engine, even if they look weak generically.

### Spike

Protect synergy pieces that are efficient, consistent, and materially improve the deck’s ability to win.

### Balanced / Unknown

Protect synergy pieces that clearly support the commander, primary strategy, or secondary strategy.

---

## Power-First Recommendations

Power-first recommendations should be filtered through philosophy.

### Timmy / Tammy

Do not recommend pure efficiency upgrades if they make the deck less exciting or remove the intended big-play experience.

### Johnny / Jenny

Do not recommend generic staples if they erase the deck’s unique engine or expression.

### Spike

Power-first recommendations are more acceptable, but still must respect power band, budget, table norms, and the deck’s actual plan.

### Balanced / Unknown

Power-first recommendations should be offered cautiously and framed as optional.

---

# Interaction With Build-Up Mode

## General Rule

In Build-Up Mode, philosophy modifies how the system fills missing deck slots.

The system must still satisfy basic Commander construction needs:

- legal color identity
- sufficient lands
- sufficient ramp
- sufficient card draw
- sufficient interaction
- coherent primary strategy
- clear win conditions
- support for commander function
- respect for budget and power target

Philosophy should influence the flavor and priority of recommendations, not replace deck-building fundamentals.

---

## Timmy / Tammy Build-Up Bias

When the deck is under 100 cards, recommendations should help the deck create bigger and more memorable moments.

Prioritize:

- ramp that reaches large payoffs
- protection for signature threats
- splashy finishers
- big creatures or spells that support the strategy
- effects that multiply the deck’s best moments
- cards that help the pilot actually cast and enjoy expensive payoffs

Avoid overfilling with low-impact efficiency pieces unless they help the deck reach its big turns.

Example build-up language:

- “Because this is Timmy/Tammy-leaning, I would use some of the open slots to make sure your biggest payoffs actually happen, not just to lower the curve.”

---

## Johnny / Jenny Build-Up Bias

When the deck is under 100 cards, recommendations should help the deck’s unique idea become more consistent and expressive.

Prioritize:

- additional enablers
- additional payoffs
- redundancy for the unusual interaction
- role-players that support the central engine
- card selection or tutors if appropriate
- protection for fragile build-around pieces
- cards that make the deck’s unique line clearer

Avoid replacing the deck’s concept with generic goodstuff.

Example build-up language:

- “Because this is Johnny/Jenny-leaning, the open slots should reinforce the engine rather than simply add generically strong Commander staples.”

---

## Spike Build-Up Bias

When the deck is under 100 cards, recommendations should improve consistency, efficiency, and execution.

Prioritize:

- efficient ramp
- efficient card draw
- low-cost interaction
- clean win conditions
- mana consistency
- curve discipline
- role compression
- reliable redundancy for the main plan

Avoid adding expensive or cute cards unless they clearly improve the deck’s performance within the chosen power band.

Example build-up language:

- “Because this is Spike-leaning, I would use the open slots to tighten execution: more efficient ramp, cleaner interaction, and more reliable access to the primary game plan.”

---

## Balanced / Unknown Build-Up Bias

When the deck is under 100 cards and no philosophy is provided, use normal Commander role-balance logic.

Prioritize:

- commander synergy
- primary-strategy support
- enough lands
- enough ramp
- enough draw
- enough interaction
- clear finishers
- budget-conscious upgrades

Example build-up language:

- “With no philosophy selected, I would fill the open slots based on role balance and primary-strategy support first.”

---

# Interaction With Batch Mode

## Batch Auto Default

Batch auto mode should default to:

**Balanced / Unknown**

unless a philosophy is provided globally or included in the deck’s input metadata.

The system must not infer a player philosophy from a decklist alone with high confidence.

It may identify possible tendencies, but it should not apply strong philosophy-based cut or replacement pressure unless the user explicitly provides the philosophy.

---

## Global Philosophy Setting

If the user provides a global philosophy for a batch run, apply that philosophy consistently to every deck in the batch unless an individual deck overrides it.

Example:

- Global philosophy: Spike
- Deck-specific philosophy: Timmy / Tammy

In this case, the deck-specific philosophy wins for that deck.

---

## Batch Reporting

Batch reports should include the philosophy used for each deck.

Recommended wording:

- “Philosophy lens used: Balanced / Unknown.”
- “Philosophy lens used: Timmy / Tammy.”
- “Philosophy lens used: Johnny / Jenny.”
- “Philosophy lens used: Spike.”

If philosophy is Balanced / Unknown, the report should avoid statements like:

- “You clearly want maximum power.”
- “This is obviously a pet-card deck.”
- “The pilot is trying to express a unique combo puzzle.”

Instead, use neutral wording:

- “Based on the decklist alone, this card is a possible review point.”
- “Without a selected philosophy, I would treat this as an optional optimization candidate.”
- “This may be intentional, but the batch input does not provide enough pilot context to assume that.”

---

# Future Expansion: Philosophy Subsets

The three core philosophies are the foundation layer.

Future versions may define subsets within each philosophy.

Possible future branches may include, but are not limited to:

- Timmy / Tammy combat spectacle
- Timmy / Tammy battlecruiser
- Timmy / Tammy pet-card storyteller
- Johnny / Jenny combo architect
- Johnny / Jenny theme expressionist
- Johnny / Jenny engine tinkerer
- Spike efficiency optimizer
- Spike metagame tuner
- Spike high-power casual grinder

Until subsets are formally defined, the system should only apply the core philosophy rules in this file.

Do not invent subset rules during normal review.

---

# Implementation Notes

## Suggested Data Shape

The philosophy layer can be represented as structured rule data rather than hard-coded scattered logic.

Recommended conceptual fields:

```yaml
philosophy:
  id: timmy_tammy | johnny_jenny | spike | balanced_unknown
  display_name: string
  cut_pressure_modifier: low | normal | high
  pet_card_tolerance: low | moderate | high
  inefficiency_tolerance: low | moderate | high
  optimization_pressure: low | normal | high
  replacement_biases:
    - string
  protect_biases:
    - string
  aggressive_review_biases:
    - string
  report_tone: string
```

This makes the philosophy layer easier to expand when subsets are added later.

## Rule Priority

When rules conflict, use this priority order:

1. Commander legality and color identity
2. User explicit instructions
3. Required cuts to reach legal deck size
4. Commander text and primary strategy
5. Deck role balance
6. Pet-card protections explicitly named by the user
7. Philosophy lens
8. Generic optimization heuristics

The philosophy lens should influence review behavior, but it should not override higher-priority requirements.
