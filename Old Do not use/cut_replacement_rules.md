# MTG Deck Helper v0.5.6 Hotfix — Cut and Replacement Rules

## Purpose

This file governs how the MTG Deck Helper evaluates possible cuts, recommended cuts, protected cards, playtest-first cards, conflict/manual review cards, bracket-pressure cards, and replacement needs for Commander decks.

This hotfix updates the v0.5.6 cut logic so it follows the layered strategy model created by the deeper section rule files:

- Section 1: Macro-Archetypes in Commander
- Section 2: Mechanical Themes & Micro-Archetypes
- Section 3: Strategic & Board Politics
- Section 4: Typal / Tribal Themes
- Section 5.1: Niche Themes
- Section 5.2: Fringe Themes
- Section 5.3: Emergent Themes

Do not duplicate or rewrite those section files here.

Instead, this file explains how cut and replacement logic should use the classifications produced by those files.

The core purpose is to prevent the helper from cutting cards merely because they are weak in a vacuum, broad, political, fringe, low-power, or strange-looking, while also preventing the helper from automatically protecting cards whose packages are unsupported.

---

# Core Principle

## 1. Cut decisions are contextual

A card should not be cut only because it looks weak in a generic Commander vacuum.

A card should be evaluated by how well it supports the specific deck.

Important question:

```text
Is this card bad, or is it just low-power but important to this deck's plan?
```

Cards may be correct to keep even when they are:

- Low mana value but low raw power
- Narrow
- Weak alone
- Dependent on other cards
- Only good in a specific board state
- Strange-looking by generic Commander standards
- Political
- Fringe
- Niche
- Typal density
- High-mana-value typal payoff
- A bridge card between two supported strategies
- A user-intent card
- A bracket-sensitive card
- A commander-defined engine piece

Cards may be correct to cut even when they are:

- Powerful in a vacuum
- Popular Commander staples
- Efficient on rate
- Expensive in real-world price
- Strong in a different archetype
- Generically flexible
- Commonly played in the commander's colors
- A good card that supports only an unsupported minor package
- A broad-archetype card from a strategy that was suppressed in favor of a narrower commander-defined plan
- A generically good card in the wrong shell

The deck helper must judge cards by deck fit, not generic card quality.

---

## 2. v0.5 Move-On Standard

The cut review is working when the agent can clearly say:

```text
These are not guaranteed cuts. These are the cards most worth reviewing based on curve, synergy, redundancy, role balance, and your deck's actual plan.
```

The goal is not to generate the longest possible cut list.

The goal is to produce the safest, clearest, most useful, and most context-aware cut advice possible.

---

# Layered Cut Review

## 3. Layered Cut Review Requirement

Before cutting, the agent must classify the card's strategic layer.

A card should be assigned one or more of the following layers:

```yaml
card_cut_layer:
  - commander/core engine
  - primary strategy card
  - secondary strategy card
  - minor package card
  - support package card
  - typal density/payoff card
  - political strategy card
  - niche theme card
  - fringe/manual-review card
  - emergent commander-defined card
  - bracket/power modifier card
  - generic goodstuff card
  - no-role or role-uncertain card
  - user-intent dependent card
```

Cut pressure depends on layer.

A card may have multiple layers.

Example:

```yaml
card_name:
  layers:
    - typal density/payoff card
    - high-synergy low-power card
    - primary strategy card
  cut_pressure: low
  protection_pressure: high
```

Example:

```yaml
card_name:
  layers:
    - generic goodstuff card
    - broad fallback card
    - off primary plan
  cut_pressure: medium
  protection_pressure: low
```

The layer classification must happen before the card is placed into Recommended Cuts, Possible Cuts, Refined Deck Review Candidates, Conflict / Manual Review, or Protected From Cut.

---

## 4. Layer-Based Cut Pressure

Use this general cut-pressure guide:

### Very Low Cut Pressure

Use very low cut pressure for:

- Commander/core engine cards
- Primary strategy cards with strong evidence
- Commander-defined engine pieces
- Core win conditions
- High-synergy low-power cards
- Cards that enable the deck's main resource engine
- Cards that are necessary density pieces for a supported typal, niche, or emergent plan

These cards should usually be Protected From Cut or Conflict / Manual Review if there is bracket pressure.

### Low Cut Pressure

Use low cut pressure for:

- Secondary strategy cards
- Support package cards
- Functional political pieces
- Supported niche engine pieces
- Intentional fringe theme pieces
- Typal density pieces with real payoff support
- Bridge cards between supported strategies
- Conversion points that turn resources into progress

These cards may be Playtest First if there is uncertainty, but should not be recommended cuts without strong evidence.

### Medium Cut Pressure

Use medium cut pressure for:

- Minor package cards that do not clearly support the main plan
- Table-dependent political pieces
- Niche cards with incomplete enabler/payoff balance
- Fringe cards with unknown user intent
- Typal cards with uncertain density
- Bracket-pressure cards that may exceed the intended bracket
- Redundant support cards beyond role needs
- Generic goodstuff cards that do not clearly advance the commander-defined plan

These should usually be Possible Cuts, Refined Deck Review Candidates, or Conflict / Manual Review.

### High Cut Pressure

Use high cut pressure for:

- Off-plan cards
- Unsupported payoffs
- Enablers with no payoff
- No-role high-mana-value cards with no commander or deck-plan support
- Generically good wrong-shell cards
- Broad fallback cards from suppressed archetypes
- Redundant role cards beyond what the deck needs
- Minor-package cards with no support or payoff
- Political cards that help opponents more than the pilot
- Typal payoffs with too little typal density
- Niche/fringe cards that conflict with the primary plan
- Bracket-pressure cards that push above the intended bracket and are not core

These may become recommended cuts if confidence is Medium or High and there is no protection conflict.

---

# Strategy-Aware Cut Principle

## 5. Protect Actual Primary Plan Support

A card should not be cut if it supports the deck's actual primary plan, even if it looks weak generically.

This applies to:

- Low-stat typal density creatures
- Narrow commander enablers
- Cheap political incentives with payoff support
- Strange-looking resource conversion pieces
- Low-power synergy cards
- Minor-looking cards that are actually bridge cards
- Cards that turn the commander's text into a real engine

Required principle:

```text
Do not cut a card just because it is weak in a vacuum if it supports the actual primary plan.
```

Example:

```text
This card looks weak by generic standards, but it belongs because it supports the deck's sacrifice-recursion engine.
```

---

## 6. Increase Cut Pressure on Suppressed Broad-Plan Cards

A card should receive higher cut pressure if it supports a broad or generic plan that was suppressed in favor of a narrower commander-defined strategy.

Examples:

- A generic ramp/control haymaker in a Token Combat deck
- A generic value creature in a commander-created landfall artifact-token deck
- A generic artifact payoff in a deck where Treasures are only a support package
- A generic midrange threat in a precise typal aristocrats shell
- A generic control card in a political deck that needs incentive, deterrence, payoff, and inevitability
- A generic big-mana payoff in a deck that is actually landfall tokens or commander-trigger combat

Cut label:

```text
Generically Good Wrong Shell
```

or

```text
Broad Fallback Card Review
```

Good wording:

```text
This may be a strong card in a vacuum, but it appears to support a broad fallback plan that was suppressed in favor of the deck's narrower commander-defined strategy.
```

---

# Deck Size Logic

## 7. Required Cuts

Required cuts are legality fixes only when the deck contains more than 100 cards.

The agent must calculate:

```text
required_cuts = max(0, deck_card_count - 100)
```

If `deck_card_count > 100`, the report must clearly state that the deck is over the legal Commander deck size and needs that many cuts.

Example:

```text
Current deck size: 104
Required cuts: 4
```

Required cuts should be selected only from confident cut candidates.

The agent must not fill required cut slots with protected/core cards just to reach the required number.

Required wording when confident candidates are insufficient:

```text
The deck needs X more cuts, but I cannot identify those cuts confidently without risking core synergy pieces. These should be reviewed manually.
```

This is better than forcing bad advice.

---

## 8. Underfilled Decks

If `deck_card_count < 100`, the deck is short cards.

Underfilled decks should not produce required cuts.

The agent should instead report:

```text
Deck Size Status:
- Current deck size: X
- Required cuts: 0
- Deck is short: Y cards
```

Underfilled decks should produce replacement/addition needs, not cut pressure.

Good language:

```text
The deck is short X cards, so there are no required cuts. The priority is identifying what roles need more support before removing anything.
```

Bad language:

```text
The deck is under 100 cards, but here are required cuts.
```

---

## 9. Optional Optimization Cuts

Optional optimization cuts are used when the deck is already legal at 100 cards or fewer, or when the user wants to improve an already legal list.

Optional optimization cuts are not mandatory.

Default behavior:

```text
optional_cut_target = 5
```

Strict mode behavior:

```text
optional_cut_target = 10
```

The agent should still look for optional cuts when the deck is exactly 100 cards.

Important:

```text
Legal does not mean optimized.
```

Optional cuts should be presented as review candidates unless the evidence is strong enough to recommend them.

Good language:

```text
These are not required cuts. These are the cards most worth reviewing based on curve, synergy, redundancy, role balance, and the deck's actual plan.
```

Bad language:

```text
Cut these cards.
```

---

# Massive Over-Limit Handling

## 10. Massive Over-Limit Deck Handling

Some decks may be far above 100 cards.

When `required_cuts` is high and confident candidates are fewer than required cuts, the report must separate confident cuts from manual-review pressure.

Use these sections:

```text
## Required Cuts Found Confidently

## Required Cuts Requiring Manual Review

## Protected/Core Cards Not Forced Into Cuts

## Additional Cuts Still Needed
```

The agent must not present fallback candidates with negative replaceability scores as normal recommended cuts.

Massive over-limit decks should be handled as triage, not as a polished optimization review.

---

## 11. Layered Triage for Massive Over-Limit Decks

### Required Cuts Found Confidently

Use this section for cards that are clearly removable without damaging the deck's core function.

These are usually:

- Off-plan cards
- Unsupported payoffs
- No-role high-mana-value cards
- Generically good wrong-shell cards
- Broad fallback cards from suppressed archetypes
- Redundant role cards beyond role needs
- Minor-package cards with no support
- Bracket-pressure cards that conflict with a known intended bracket and are not core

### Required Cuts Requiring Manual Review

Use this section for mixed-signal cards that may need to be cut because the deck is far over 100, but should not be treated as final recommendations.

These include:

- Fringe cards
- Political cards
- Minor package cards
- Uncertain typal cards
- Bracket-pressure cards
- Niche cards with missing support
- Role-uncertain cards
- Cards with possible user-intent dependence
- Cards that are narrow but may be important if the package is intentional

Good language:

```text
This card may need to be reviewed because the deck is far over 100 cards, but it is not a confident cut.
```

### Protected/Core Cards Not Forced Into Cuts

Use this section for cards that the agent refuses to force into cuts despite deck-size pressure.

These include:

- Commander-defined engine pieces
- Primary plan cards
- Core win conditions
- Typal density pieces in supported typal decks
- High-synergy low-power cards
- Resource-engine cards
- Bridge cards
- Conversion points
- Cards that enable the commander to function

Example:

```text
Protected/Core Cards Not Forced Into Cuts

Card Name
- Reason: This card appears low-power in isolation, but it is part of the deck's commander-defined engine.
- Verdict: Do not force into required cuts unless the user changes the deck's strategy.
```

### Additional Cuts Still Needed

If required cuts exceed confident and manual-review candidates, say how many cuts remain unresolved.

Required wording:

```text
The deck still needs X more cuts, but I cannot identify those cuts confidently without risking core synergy pieces.
```

This is a successful output, not a failure.

Accuracy is more important than filling a quota.

---

# Refined Deck Handling

## 12. Refined Deck Review Candidates

Sometimes a legal deck is already refined enough that no confident recommended cuts are found.

If a legal deck has:

- No required cuts
- No recommended cuts
- No optional optimization cuts

Then the agent must not force bad cuts.

Instead, add a section called:

```text
## Refined Deck Review Candidates
```

Required wording:

```text
No confident cuts found. This appears refined. The cards below are not recommended cuts; they are the only cards worth watching through playtesting.
```

List 3–5 cards if available from these groups:

- Minor packages
- Bracket pressure cards
- Table-dependent political cards
- Fringe/manual-review cards
- Typal cards with uncertain density
- Generically good wrong-shell candidates
- Resource conflict cards
- Redundant support cards
- Context-dependent cards
- Low-confidence synergy cards
- Narrow cards that need playtesting

These should be labeled:

```text
Playtest-first review candidates
```

They are not recommended cuts.

Example:

```text
## Refined Deck Review Candidates

No confident cuts found. This appears refined. The cards below are not recommended cuts; they are the only cards worth watching through playtesting.

Card Name
- Label: Playtest-first review candidate
- Why to watch: This card supports a minor package, but it may not advance the deck's main plan often enough.
- Watch For: Does this card meaningfully affect games when drawn, or does it sit in hand behind stronger engine pieces?
```

This section prevents the tool from becoming too passive while also preventing it from inventing bad cuts.

---

# General Cut Categories

## 13. Possible Cuts

Possible cuts are cards worth reviewing but not automatically recommended for removal.

A card can be a possible cut because it appears replaceable, inefficient, redundant, off-plan, bracket-sensitive, poorly supported, or mismatched to the actual strategy layer.

Possible cut categories:

- Possible Efficiency Cut
- Possible Curve Cut
- Possible Off-Theme Cut
- Possible Redundancy Cut
- Possible Low-Impact Cut
- Possible Bracket Pressure Cut
- Possible Mana Base Concern
- Possible Manual Review
- Possible Wrong-Shell Card
- Possible Win-More Card
- Possible Narrow Payoff
- Possible Unsupported Typal Payoff
- Possible Incidental Type Card
- Possible Off-Type Goodstuff
- Possible Unsupported Subtheme Card
- Possible Minor Package Cut
- Possible Role-Uncertain Cut
- Political Card With No Payoff
- Unsupported Niche Payoff
- Niche Enabler Without Payoff
- Niche Payoff Without Enabler
- Fringe Manual Review
- Resource Conflict Review
- Broad Fallback Card Review

Possible cuts must include:

- Card name
- Card layer
- Cut type
- Confidence
- Reason
- Replacement category if appropriate
- Whether the card is safe to cut or should be playtested first

Example:

```text
Possible Cut: Card Name
Card Layer: Minor package card
Cut Type: Possible Minor Package Cut
Confidence: Medium
Reason: This may be a good card, but it appears to support a minor package rather than the deck's main plan.
Replacement Category: More primary-plan support
Verdict: Review before cutting
```

---

## 14. Recommended Cuts

Recommended cuts are stronger than possible cuts.

A card should only be listed as a recommended cut when there is enough evidence that removing it improves the deck.

Recommended cuts should usually meet several of these conditions:

- Low commander synergy
- Low primary strategy synergy
- Low secondary strategy synergy
- Poor fit with the deck's main resource engine
- Redundant beyond what the deck likely needs
- Too expensive for its effect
- Low impact at its mana value
- Unsupported payoff
- Requires a subtheme the deck does not have
- Supports only a minor package and not the deck's main plan
- Pulls the deck toward a different strategy
- Raises bracket pressure above the intended bracket without being core
- Is replaceable by a broader, cleaner, or more synergistic role card
- Is only good when already ahead
- Has no role tags, no commander synergy, high mana value, and no deck-plan support
- Is a generically good wrong-shell card
- Belongs to a broad fallback strategy that was suppressed in favor of the actual plan

A recommended cut must not be protected, core, or unresolved by conflict logic.

Recommended cut confidence levels:

- High: Strong evidence the card is replaceable or off-plan
- Medium: Good evidence, but deck preference or play pattern could matter
- Low: Do not list as a recommended cut; list as possible cut, refined deck review candidate, playtest first, or manual review instead

Rule:

```text
Low-confidence cuts should not be presented as recommended cuts.
```

---

# Role Uncertainty

## 15. Role-Tag Uncertainty Is Not Automatic Cut Pressure

A card with no role tags or a manual-review role tag is not automatically a cut.

The tool must not assume:

```text
No role tag = bad card
```

A card may have no role tag because:

- The role tagger missed a real role
- The card is modal or context-dependent
- The card supports a niche package
- The card is a flexible answer
- The card is a meta call
- The card is a theme or pet card
- The card supports an archetype not yet fully recognized
- The card is political or table-dependent
- The card is an emergent bridge card

However, a no-role card may become a low- or medium-confidence possible cut if it has several negative signals.

A no-role card may become a possible cut when it has:

- No role tags
- No commander synergy
- No primary-plan support
- No secondary-plan support
- No support role
- No ramp/fixing role
- No draw role
- No interaction role
- No win-condition role
- High mana value
- Low board impact
- No evidence of deck-plan support

Good language:

```text
This card has no clear detected role, but that alone does not make it a cut. Because it also has no commander synergy, no deck-plan support, and a high mana value, it is worth reviewing as a low-confidence possible cut.
```

Bad language:

```text
This card has no role tags, so cut it.
```

---

# Minor Package Cut Logic

## 16. Minor Package Cards

A minor package is a small theme, subtheme, or synergy cluster that is present in the deck but does not appear to be the deck's commander plan, primary plan, or secondary plan.

Examples of minor packages:

- A small lifegain package in a non-lifegain deck
- A small artifact package in a non-artifact deck
- A small typal package without enough creature density
- A small graveyard package in a deck without recursion payoffs
- A few token payoffs in a deck that does not reliably make tokens
- A small equipment package in a non-Voltron deck
- A narrow adventure/modal package in a deck that does not otherwise reward it
- A pod-chain package without enough chain density or sacrifice support
- A landfall package without landfall commander support or land-entry density
- A political mini-package without payoff or inevitability
- A fringe mini-package without declared user intent

A card that supports only a minor package may be a possible cut if it does not also support:

- Commander
- Primary plan
- Secondary plan
- Support role
- Win condition
- Required density
- Bracket goal
- User-provided custom category

Cut label:

```text
Possible Minor Package Cut
```

Required wording:

```text
This may be a good card, but it appears to support a minor package rather than the deck's main plan.
```

A minor-package card should usually be Possible Cut, Refined Deck Review Candidate, or Playtest First, not automatically Recommended Cut.

It may become a recommended cut only if the minor package is clearly unsupported and the card has low impact outside that package.

---

# Typal Cut Logic

## 17. Typal Cut Principle

Typal decks are evaluated through:

```text
typal_plan = creature_type_density + payoff_density + commander_support + strategy_shape + win_condition
```

Do not cut typal cards simply because their raw stats are weak.

Typal cards may be structurally important because they provide:

- Density
- Lords
- Cost reduction
- Typal tutoring
- Token creation
- Recursion
- Protection
- Strategy-shape support
- Changelings for low-density tribes
- Multiple-copy exception density
- Bridge support into another mechanic

---

## 18. Typal Cards Not Automatically Cut

Do not automatically cut:

- Low-stat typal density pieces
- Lords
- Cost reducers
- Typal tutors
- Relevant token makers
- Typal recursion
- Typal protection
- Changelings in low-density tribes
- Multiple-copy exception cards
- High-MV tribal creatures if ramp, cost reduction, cheat effects, or reanimation exists
- Off-type cards that bridge into the tribe's actual strategy shape
- On-type sacrifice fodder in typal aristocrats decks
- On-type evasive creatures in typal saboteur decks
- On-type mana dorks in Elf/Druid decks
- Token makers that create the relevant creature type
- Typal payoff artifacts or enchantments
- Utility creatures with the relevant type

Use labels:

- Playtest-First Typal Density Piece
- Protected Typal Engine Piece

Example:

```text
Protected Typal Engine Piece: Card Name
Reason: This card looks modest by raw power, but it provides necessary typal density and supports the deck's actual typal strategy shape.
```

---

## 19. Typal Cut Pressure Increases When

Increase cut pressure on:

- Off-type cards with no support role
- Typal payoffs with too little density
- Lords for incidental creature types
- Expensive tribal cards without ramp, cheat, cost reduction, reanimation, or immediate impact
- Generic goodstuff that weakens typal synergy density
- Cards supporting a different typal strategy shape than the deck is actually playing
- Combat-only lords in noncombat typal decks
- Graveyard typal payoffs in typal decks without self-mill, sacrifice, discard, or recursion
- Equipment in typal decks with no Equipment strategy
- Lifegain payoffs in tribes without lifegain triggers
- Treasure payoffs in tribes with little Treasure production
- Type-specific cards for an incidental creature type
- Token makers that create the wrong creature type unless they support another real plan

Use labels:

- Possible Unsupported Typal Payoff
- Possible Incidental Type Card
- Possible Off-Type Goodstuff

Example:

```text
Possible Unsupported Typal Payoff: Card Name
Reason: This payoff appears to care about a creature type that is not present at enough density to support it.
```

---

## 20. Typal Strategy Shape Rule

A typal card is not judged only by whether it has the correct creature type.

The helper must ask what shape the typal deck is playing.

Examples:

- Vampire Aristocrats
- Zombie Reanimator
- Dragon Treasure Ramp
- Goblin Tokens
- Merfolk Tempo
- Knight Equipment
- Elf Ball
- Typal Lifegain
- Typal Artifacts
- Typal Counters
- Typal Control

A card supporting the wrong typal shape should receive higher cut pressure.

Example:

```text
This card is on-type, but it appears to support typal combat while the deck is functioning more like typal aristocrats. Review as a possible wrong-shape typal card.
```

---

# Political Cut Logic

## 21. Political Cut Principle

Political cards are not automatically cuts.

Political cards should be reviewed based on:

- Incentive
- Deterrence/protection
- Payoff
- Inevitability
- Table dependency
- Kingmaker risk
- Salt risk
- Whether the deck can close the game

Political strategies should be treated as incentive engines, not as random group effects.

A strong political card changes the table's incentives while helping the pilot advance.

A weak political card merely asks opponents to cooperate or creates chaos without progress.

---

## 22. Political Cut Labels

Use these labels:

- Functional Political Piece
- Table-Dependent Political Piece
- Kingmaker Risk Review
- Salt Risk Review
- Stall Risk Review
- Political Card With No Payoff
- Pregame Discussion Piece

---

## 23. Political Cards to Protect or Preserve

Protect or preserve political cards when they:

- Create real incentives
- Redirect threats away from the pilot
- Deter attacks or removal
- Produce asymmetrical payoff
- Help the pilot more than opponents
- Support the commander's political axis
- Create inevitability
- Help the deck survive long enough to win
- Function even if opponents do not cooperate
- Fit the stated table or theme intent

Use label:

```text
Functional Political Piece
```

Example:

```text
Functional Political Piece: Card Name
Reason: This card gives opponents an incentive to fight each other while advancing the pilot's board or card advantage.
```

---

## 24. Political Cut Pressure Increases When

Political card cut pressure increases when the card:

- Helps opponents more than pilot
- Requires opponents to make bad choices
- Creates salt without progress
- Stalls without win condition
- Does not support the actual win path
- Is funny but not functional unless the user values theme
- Makes the pilot a kingmaker without increasing the pilot's chance to win
- Depends heavily on table talk in pods where that may not happen
- Accelerates opponents without asymmetrical payoff
- Gives the leading player too much advantage

Use careful language:

```text
This card may be fun or political, but it does not currently show enough payoff or inevitability to support the deck's win path.
```

Do not call political cards bad merely because they are political.

---

# Niche Theme Cut Logic

## 25. Niche Theme Principle

Niche does not mean bad.

Unsupported means bad.

A niche card should be evaluated by:

```text
niche_theme_strength = commander_support + enabler_density + payoff_density + execution_support + win_path
```

A niche card may look weak generically but be correct if it provides density, enables a narrow mechanic, bridges multiple supported themes, or is one of the few available pieces for the theme.

---

## 26. Protect Niche Cards When

Protect niche cards when:

- Commander supports the mechanic
- Enough enablers and payoffs exist
- Card is one of few available density pieces
- Card bridges multiple supported themes
- Card is necessary for execution
- Card fixes a known weakness of the theme
- Card contributes to the deck's mana base, card type structure, or token economy
- Card is narrow but necessary
- Card supports the actual win path

Use label:

```text
Supported Niche Engine Piece
```

Example:

```text
Supported Niche Engine Piece: Card Name
Reason: This card is narrow, but it is one of the deck's few reliable enablers for a supported niche mechanic.
```

---

## 27. Niche Cut Pressure Increases When

Increase cut pressure when:

- Payoff exists but enablers are missing
- Enablers exist but no payoff exists
- Theme conflicts with primary plan
- Card is isolated
- Card consumes resources needed for primary plan
- Theme has one or two cards but no package
- Card is a low-impact one-shot in a theme that needs repeatability
- Card is only good when already ahead
- Card is too narrow for the deck's actual commander

Use labels:

- Unsupported Niche Payoff
- Niche Enabler Without Payoff
- Niche Payoff Without Enabler
- Niche Manual Review

Example:

```text
Niche Payoff Without Enabler: Card Name
Reason: This card rewards a narrow mechanic, but the deck does not appear to have enough reliable enablers to make the payoff consistent.
```

---

# Fringe Theme Cut Logic

## 28. Fringe Theme Principle

Fringe themes are user-intent dependent.

A fringe card is not automatically a cut.

But a fringe card without user intent, payoff support, commander support, or table context should be reviewed before it is protected.

Correct framing:

```text
This looks like a fringe package rather than a core plan. I would not automatically cut it if this is intentional, but it needs manual review because the deck does not currently show enough support to make it reliable.
```

---

## 29. If User Declared the Fringe Theme

If the user declared the fringe theme:

- Preserve the theme
- Recommend improvements within the theme first
- Separate power optimization from theme preservation
- Avoid over-optimizing away the theme
- Protect cards necessary to make the theme function
- Use replacements that preserve the theme where possible

Use label:

```text
Intentional Fringe Theme Piece
```

Example:

```text
Intentional Fringe Theme Piece: Card Name
Reason: This card is not generically powerful, but it supports the user's declared fringe theme and should not be removed for generic optimization unless the user asks for power-first cuts.
```

---

## 30. If User Intent Is Unknown

If user intent is unknown:

- Flag manual review
- Do not aggressively cut
- Do not aggressively protect
- Explain what support is missing
- Identify whether the card is flavor-first, legality-sensitive, social-contract sensitive, meta-dependent, or package-dependent

Use labels:

- Fringe Manual Review
- Rule Zero / Legality Review
- Social Contract Pressure Review
- Meta-Dependent Hate Piece
- Flavor-First Piece
- Package Dependency Review

Example:

```text
Fringe Manual Review: Card Name
Reason: This card appears to support a fringe package, but user intent is unknown and the deck does not show enough support to treat it as core.
```

---

## 31. Fringe Cut Pressure Increases When

Increase cut pressure when:

- The fringe card appears without payoff support
- The card creates legality or Rule Zero issues the user did not ask for
- The card conflicts with the deck's own main plan
- The theme is only represented by one or two isolated cards
- The card is meta-dependent but no meta reason was provided
- The card creates table-salt pressure without helping the deck win
- The card requires another specific card that is missing
- The card is only funny once but weak repeatedly
- The card makes replacements harder without sufficient payoff
- The card consumes resources the primary plan needs

Do not confuse fringe with bad.

Use manual review when intent is unclear.

---

# Emergent Theme Cut Logic

## 32. Emergent Theme Principle

Emergent themes are where weak-looking cards can be essential.

Emergent themes include:

- Commander-defined strategies
- Hybrid strategy packages
- Bridge cards between mechanics
- Resource conversion engines
- Modern mechanic packages
- Compact combo-adjacent packages
- Bracket-pressure signals
- Special deckbuilding exceptions
- Cards that look weak but make the commander function

The helper should ask:

```text
What is this deck actually trying to make happen?
```

not merely:

```text
What archetype is this closest to?
```

---

## 33. Protect Emergent Engine Cards

Protect:

- Commander-defined enablers
- Bridge cards
- Conversion pieces
- Resource-engine cards
- High-synergy low-power cards
- Cards that turn the commander's unique text into a real engine
- Cards that connect primary and secondary plans
- Cards that create the deck's main game object
- Cards that convert that game object into cards, mana, damage, tokens, combat pressure, or a win

Use labels:

- High-Synergy Low-Power Card
- Commander-Defined Engine Piece
- Bridge Card
- Conversion Point

Example:

```text
Commander-Defined Engine Piece: Card Name
Reason: This card looks replaceable generically, but it directly turns the commander's text into the deck's main engine.
```

Example:

```text
Bridge Card: Card Name
Reason: This card connects the deck's artifact-token package to its sacrifice/value plan, so it should not be judged as a generic artifact card.
```

---

## 34. Emergent Cut Pressure Increases When

Review:

- Generically good wrong-shell cards
- Broad archetype cards from suppressed archetypes
- Resource-conflict cards
- Payoff without enabler
- Enabler without conversion
- Combo piece without support or intent
- Cards that consume the same resource the primary engine needs
- Cards that support a broad fallback strategy rather than the commander-defined plan
- Cards that are powerful but do not participate in the engine

Use labels:

- Generically Good Wrong Shell
- Resource Conflict Review
- Broad Fallback Card Review
- Unsupported Payoff
- Enabler Without Conversion
- Combo Piece Without Support

Example:

```text
Generically Good Wrong Shell: Card Name
Reason: This is a strong card, but it appears to support a generic value plan rather than the deck's commander-defined artifact-token landfall engine.
```

---

# Bracket Pressure Cut Logic

## 35. Bracket Pressure Is Not the Same as a Cut

Bracket pressure is not the same as a cut.

A bracket-pressure card may be:

- Correct at a higher bracket
- Core but table-sensitive
- Off-plan and too strong
- A possible cut only if lowering power
- A pregame discussion card
- Powerful and correct for the deck
- Correct only at a higher bracket
- Wrong for the intended table

Never automatically cut a card only because it has bracket pressure.

Do not call bracket-pressure cards bad.

Good language:

```text
This is a strong card, not a bad card. The question is whether it fits the intended bracket and table experience.
```

Bad language:

```text
This card is bad because it is too strong.
```

---

## 36. Bracket-Pressure Card Is Core

If a bracket-pressure card is core, move it to:

```text
Conflict / Manual Review
```

Do not put it in Protected From Cut and do not put it in Recommended Cuts.

Required wording:

```text
This card strongly supports the deck's plan, but it may push the deck above the intended bracket.
```

Example:

```text
Conflict / Manual Review: Card Name
Cut Pressure: Medium
Protection Pressure: High
Why it looked cuttable: This card may push the deck above the intended bracket.
Why it may belong: This card strongly supports the deck's plan, but it may push the deck above the intended bracket.
Current Recommendation: Do not cut automatically. Decide whether the bracket target or the engine identity matters more.
```

---

## 37. Known Intended Bracket

If the intended bracket is known, bracket-pressure cards should be handled based on whether they support or undermine that target.

If a bracket-pressure card pushes above the intended bracket and is not core, move it to:

```text
## Bracket-Driven Cuts / Bracket Pressure Review
```

If a bracket-pressure card is core but high pressure, move it to:

```text
## Conflict / Manual Review
```

A bracket-pressure card may become a possible cut only if the user is lowering power or preserving a lower bracket.

Example:

```text
Bracket Pressure Review: Card Name
Confidence: Medium
Reason: This card may push the deck above the stated Bracket 2 target by increasing consistency too much.
Verdict: Consider cutting only if the goal is to keep the deck within Bracket 2.
```

---

## 38. Unknown Intended Bracket

If the intended bracket is unknown, bracket-pressure cards should be treated as review flags, not automatic cuts.

Use:

```text
Bracket Pressure Review
```

or

```text
Conflict / Manual Review
```

Do not list a card as a recommended cut solely because it has bracket pressure when the bracket target is unknown.

Good language:

```text
The intended bracket is unknown, so this is a review flag rather than an automatic cut.
```

---

# Protected and Core Card Logic

## 39. Protected Cards

Protected cards are cards the agent should avoid cutting unless there is overwhelming evidence or the user specifically asks for power-first optimization.

A card should be protected when it does one or more of the following:

- Directly supports the commander
- Enables the commander to function
- Advances the primary strategy
- Advances the secondary strategy
- Is part of the main resource engine
- Is a key payoff
- Is a key enabler
- Is a likely win condition
- Provides necessary ramp or fixing
- Provides necessary card draw
- Provides necessary removal
- Provides necessary protection
- Provides important recursion
- Provides required typal density
- Provides a typal payoff in a supported typal deck
- Provides a bridge into the deck's actual strategy shape
- Provides a sacrifice outlet in a sacrifice deck
- Provides a token engine in a tokens deck
- Provides lifegain payoff in a lifegain deck
- Provides graveyard setup in a graveyard deck
- Provides artifact count, token economy, or treasure support in an artifact/treasure deck
- Provides activated ability support in an activated-ability deck
- Provides pod-chain support in a pod or toolbox deck
- Provides equipment/aura support in a Voltron or aura/equipment deck
- Provides adventure/modal support in a deck that rewards alternate casting, modal value, or spell/permanent flexibility
- Provides functional political incentive, deterrence, payoff, or inevitability
- Provides supported niche-theme density
- Provides intentional fringe-theme support
- Is weak alone but strong in the deck's actual engine
- Is low-power but high-synergy
- Helps the deck function at the intended bracket level

Protected cards should be listed separately from cuts.

Example:

```text
Protected From Cut: Card Name
Reason: This card looks modest by raw power, but it is a key sacrifice outlet that enables the deck's recursion engine.
```

---

## 40. Core Cards

Core cards are stronger than protected cards.

A core card should be treated as central to the deck's game plan.

A card may be core if it is:

- A primary engine piece
- A major commander synergy piece
- A central payoff
- A central enabler
- A main win condition
- A key combo-adjacent value piece
- A card the deck appears built around
- A critical role-player that holds the strategy together
- A commander-defined engine piece
- A conversion point
- A necessary typal engine card
- A necessary political inevitability card
- A necessary niche/fringe execution card when user intent is known

Core cards should almost never appear in a cut list.

If a core card appears replaceable due to curve, redundancy, or bracket pressure, it must be moved to Conflict / Manual Review instead of being cut.

---

## 41. Playtest-First Cards

Some cards should not be immediately cut even if the tool is unsure about them.

A card should be marked playtest-first when it is:

- Narrow but potentially high-synergy
- Weak alone but strong with the commander
- Dependent on board texture
- A possible hidden engine piece
- A payoff for a subtheme with uncertain density
- A card the deck may need for its intended play pattern
- A bracket-sensitive card where the user's desired power level matters
- A card that looks strange but may be included for local meta reasons
- A synergy piece that requires more games to evaluate
- A pet card or theme card if the user indicates it matters
- A refined-deck review candidate
- A minor-package card that may still be intentional
- A no-role or manual-review card with uncertain context
- A political card with table dependency
- A fringe card with unknown user intent
- A typal density piece with uncertain payoff support
- A resource-conflict card whose importance depends on actual play patterns

Playtest-first cards are not protected forever. They are cards the agent should flag for observation.

Example:

```text
Playtest First: Card Name
Reason: This card may be too narrow, but it supports the deck's toughness-matters payoff package. Track whether it is useful when drawn.
Watch For: Does it advance the board, enable the commander, or sit dead in hand?
```

---

# Conflict Handling

## 42. Cut / Protect Conflict Rule

This is one of the most important v0.5.6 hotfix rules.

A card must not be presented as both a final cut and a protected/core card.

If a card appears in both a cut list and a protected/core list, the agent must remove it from final advice and move it to:

```text
Conflict / Manual Review
```

Required rule:

```text
If a card appears in both a cut list and a protected/core list, do not present both as final advice. Move it to Conflict / Manual Review.
```

This prevents contradictory recommendations.

Bad output:

```text
Recommended Cut: Card Name
Protected From Cut: Card Name
```

Correct output:

```text
Conflict / Manual Review: Card Name
Why it was considered for cutting: It is expensive and narrow.
Why it may be protected: It directly supports the commander's main engine.
Verdict: Do not cut automatically. Playtest or review manually.
```

---

## 43. Conflict / Manual Review

A card should be moved to Conflict / Manual Review when the tool has meaningful evidence both for and against cutting it.

Examples of conflict:

- The card is expensive but is a key payoff
- The card is narrow but supports the commander directly
- The card is low-power but has high synergy
- The card is redundant but redundancy may be necessary
- The card is off-plan generically but supports a declared custom category
- The card is a typal payoff but density is uncertain
- The card is a combo piece but the deck is not clearly a combo deck
- The card raises bracket pressure but may be the deck's only finisher
- The card raises bracket pressure but is core to the engine
- The card is a mana rock/ramp spell that looks replaceable but the deck is short on ramp
- The card is removal that looks inefficient but the deck is short on interaction
- The card is a board wipe that looks slow but the deck lacks reset buttons
- The card has no clean role tag but may have missed synergy
- The card supports a minor package that may be intentional
- The card is political and table-dependent
- The card is fringe and user intent is unknown
- The card is niche but support density is unclear
- The card creates a resource conflict but may still be a conversion point

Conflict / Manual Review entries should include:

- Why it looked cuttable
- Why it may need protection
- What data would resolve the question
- Whether to playtest, replace, or keep for now

Example:

```text
Conflict / Manual Review: Card Name
Cut Pressure: Medium
Protection Pressure: Medium
Why it looked cuttable: The card is slow and does not affect the board immediately.
Why it may belong: It is one of the deck's few repeatable graveyard recursion engines.
How to decide: Track whether it creates meaningful value within two turns of being played.
Current Recommendation: Playtest first, do not cut automatically.
```

---

# Confidence Rules

## 44. Cut Confidence

Every possible or recommended cut must have a confidence label.

Use:

- High
- Medium
- Low

High confidence means the agent has strong evidence the card is replaceable or off-plan.

Medium confidence means the card is probably replaceable, but context could change the decision.

Low confidence means the card should not be recommended as a cut. It may appear only as Possible Cut, Refined Deck Review Candidate, Playtest First, or Manual Review.

Confidence should be based on:

- Commander synergy
- Card layer
- Primary strategy support
- Secondary strategy support
- Role importance
- Curve impact
- Redundancy
- Deck density
- Payoff/enabler balance
- Bracket pressure
- Role-tag certainty
- Whether the card supports only a minor package
- Whether the card is protected
- Whether the card is core
- Whether the card has unresolved conflict
- Whether user intent is known
- Whether the package is supported

---

## 45. Protection Confidence

Protected cards may also have confidence.

Use:

- High protection confidence
- Medium protection confidence
- Low protection confidence

High protection confidence:

- Card directly supports the commander or core engine
- Card appears critical to the primary game plan
- Card is one of few cards filling an essential role
- Card is a commander-defined engine piece
- Card is a conversion point
- Card is required density for supported typal/niche/fringe theme

Medium protection confidence:

- Card supports the strategy but may be replaceable
- Card is good in context but not essential
- Card may depend on density or board state
- Card is a functional political piece but table-dependent

Low protection confidence:

- Card has some synergy, but not enough to avoid review
- Card belongs in Playtest First or Conflict / Manual Review
- Card may support a minor or fringe package but intent/support is unclear

---

# Replaceability Rules

## 46. Rank by Replaceability, Not Raw Power

The agent should rank cut candidates by replaceability.

Replaceability increases when a card is:

- Low synergy with the commander
- Off the primary strategy
- Off the secondary strategy
- Not part of the main resource engine
- Redundant beyond need
- Narrow without sufficient payoff
- Too expensive for its impact
- Low impact at its mana value
- A payoff without enough enablers
- An enabler without enough payoffs
- Typal support with low typal density
- A generic goodstuff card in a synergy deck
- A synergy card in a deck that does not support that synergy
- A minor-package card that does not support the deck's main plan
- A win-more card
- Only good when ahead
- A bracket-escalating card that does not support the intended deck experience
- A card whose role is already covered by stronger or more synergistic cards
- A no-role card with no commander synergy, no deck-plan support, high mana value, and low board impact
- A political card with no payoff, incentive, deterrence, or win path
- A niche/fringe payoff without enabler support
- A broad fallback card from a suppressed archetype

Replaceability decreases when a card is:

- Commander-facing
- Engine-facing
- A key enabler
- A key payoff
- One of few cards filling an essential role
- Low-power but high-synergy
- Part of a critical density package
- Important to the user's declared theme
- Important to the deck's primary or secondary plan
- A flexible answer in a deck light on interaction
- Necessary ramp/fixing in a deck short on mana support
- A finisher in a deck short on ways to close the game
- A bracket-pressure card that is also core to the deck's identity
- A role-uncertain card with plausible hidden synergy
- A typal density piece in a supported typal deck
- A functional political piece
- A supported niche engine piece
- An intentional fringe theme piece
- A commander-defined engine piece
- A bridge card
- A conversion point

Negative replaceability means the card should not be treated as a normal recommended cut.

If required cuts are high, negative-replaceability cards may be listed only in Conflict / Manual Review or Protected/Core Cards Not Forced Into Cuts.

---

# Deck Role Balance

## 47. Do Not Cut Essential Role Density Blindly

Before recommending cuts, the agent should check whether cutting the card would weaken an already thin role.

Do not recommend cutting from a role if the deck is already low in that role unless the card is clearly off-plan, illegal, unsupported, or replaceable by a better card in the same role.

Important role groups:

- Lands
- Ramp
- Card draw
- Targeted removal
- Board wipes
- Protection
- Recursion
- Finishers
- Commander enablers
- Primary strategy enablers
- Primary strategy payoffs
- Secondary strategy support
- Mana fixing
- Graveyard setup
- Sacrifice outlets
- Token makers
- Lifegain enablers
- Lifegain payoffs
- Artifact/enchantment density pieces
- Typal density pieces
- Activated ability support
- Pod-chain support
- Equipment/aura support
- Adventure/modal support
- Political payoff
- Political protection/deterrence
- Niche enablers
- Niche payoffs
- Fringe support if intentional
- Bridge cards
- Conversion points
- Resource generation

Example:

```text
This removal spell is not especially efficient, but the deck appears light on interaction. Do not cut it unless another removal spell replaces it.
```

---

# Replacement Logic

## 48. Replacement Categories

The agent should usually suggest replacement categories before suggesting exact cards.

Replacement categories help the user understand what the deck needs.

Use these preferred replacement categories:

- More commander synergy
- More commander-specific enablers
- More primary-plan support
- More secondary-plan support
- More role compression
- Lower mana curve
- More lands
- More ramp
- More card draw
- More targeted removal
- More board wipes
- More protection
- More finishers
- More token production
- More sacrifice outlets
- More recursion
- More artifact support
- More enchantment support
- More typal density
- More typal payoff
- More on-type creatures
- More typal-mechanic bridge cards
- More activated ability support
- More pod-chain support
- More equipment/aura support
- More adventure/modal support
- More engine density
- More bridge cards
- More conversion points
- More political payoff
- More asymmetrical payoff
- More table-friendly interaction
- More niche enablers
- More niche payoffs
- More fringe support if intentional
- Commander-legal alternatives
- Lower-salt alternatives
- More bracket-appropriate alternatives
- More protection/setup for slow alternate wins
- More payoff density
- More resource generation

Additional acceptable replacement categories when needed:

- Better fixing
- More graveyard setup
- More lifegain payoffs
- More lifegain enablers
- More instant/sorcery density
- More creature density
- More toughness-matters payoffs
- More defender support
- More discard outlets
- More reanimation targets
- More blink targets
- More blink enablers
- More +1/+1 counter payoffs
- More evasion
- More combat finishers
- More mana sinks
- More utility lands
- More bracket-appropriate interaction
- More table-safe value pieces
- Fewer bracket-escalating cards

Replacement categories should be tied to the deck's actual problems.

Bad replacement category:

```text
Add better cards.
```

Good replacement category:

```text
Replacement Category: More role compression
Reason: The deck needs cards that advance the primary plan while also covering interaction or card advantage.
```

Good replacement category:

```text
Replacement Category: More bridge cards
Reason: The deck has two supported themes, but it needs more cards that connect the token engine to the sacrifice payoff package.
```

Good replacement category:

```text
Replacement Category: More asymmetrical payoff
Reason: The political package gives opponents resources, so the deck needs cards that let the pilot benefit more than the table.
```

---

## 49. When to Suggest Exact Replacements

Exact replacement card suggestions are optional.

The agent should suggest exact replacements only when all of the following are true:

- Color identity is verified
- The replacement supports the primary or secondary plan
- The bracket target is known or the suggestion is clearly safe for the likely bracket
- The budget or collection constraint is known, or the user allows general suggestions
- The replacement does not conflict with the commander game plan
- The replacement does not require an unsupported subtheme
- The replacement does not replace synergy with generic power
- The replacement is not banned
- The agent has enough card knowledge or Scryfall data to avoid illegal suggestions

Exact replacement suggestions are most appropriate when:

- The user asks for exact cards
- The deck has an obvious role gap
- The replacement category is clear
- The replacement supports the commander directly
- The user has provided a collection list or allowed general database suggestions
- The deck's intended bracket and budget are known

Exact replacement suggestions should include a reason.

Example:

```text
Possible Replacement: Card Name
Replacement Category: More sacrifice outlets
Reason: This gives the deck a repeatable way to trigger death payoffs while supporting the commander's primary plan.
```

---

## 50. When Not to Suggest Exact Replacements

The agent should not suggest exact replacements when the available information is insufficient.

Do not suggest exact cards when:

- Color identity is not verified
- The deck's bracket goal is unknown and the replacement may raise power too much
- The user's budget is unknown and the card may be expensive
- The user's collection constraint is unknown and the user wants collection-based replacements
- The deck's meta is unknown and the answer depends on local play patterns
- The card pool is uncertain
- The commander identity is uncertain
- The deck's primary strategy is uncertain
- The deck's custom categories suggest a theme the agent has not parsed
- The replacement would require a different build direction
- The role need can be explained better as a category
- The agent cannot verify legality or color identity
- The replacement would be a generic staple with unclear synergy

Use this language instead:

```text
I would not suggest exact replacements yet. The better next step is to decide whether this slot should become more ramp, more draw, more removal, more protection, more role compression, or another synergy piece.
```

For future collection-aware versions, prefer:

```text
Exact replacements should come from the user's collection when collection data is available. Until then, use replacement categories unless the user allows general card suggestions.
```

---

# Custom Category and User Intent Respect

## 51. Respect User-Provided Deck Categories

If the user provides custom deck categories, the agent must use them as evidence.

A card that looks off-plan by generic analysis may be on-plan according to the user's custom category.

Example custom categories:

- Sacrifice Outlets
- Drain Payoffs
- Token Makers
- Graveyard Setup
- Protection
- Finishers
- Pet Cards
- Theme Cards
- Mana Base
- Ramp
- Draw
- Removal
- Combo Pieces
- Bracket Concerns
- Do Not Cut
- Playtest First
- Maybe Board
- Flex Slots
- Package Cards

If a card is in a custom category that implies importance, the agent should not cut it without explaining the conflict.

If a card is in "Do Not Cut," "Pet Card," or equivalent, the agent should not recommend it as a cut.

It may still provide a gentle note if the card has low synergy:

```text
User-Protected Card: Card Name
Note: This card appears lower synergy than other options, but it is user-protected and should not be listed as a cut.
```

If a card is in "Flex Slots," "Maybe Board," or equivalent, the agent may treat it as more cuttable than core cards, but still must evaluate its actual role and synergy.

---

# Output Requirements

## 52. Standard Cut Review Output Structure

The cut review should use this structure when the deck is legal or only slightly over the limit:

```text
## Cut Pressure Review

Deck Size Status:
- Current deck size:
- Required cuts:
- Deck is short:
- Optional optimization cuts reviewed:
- Cut strictness:
- Intended bracket:

Layered Strategy Context:
- Primary strategy:
- Secondary strategy:
- Suppressed broad fallback strategies:
- Minor packages:
- Manual-review packages:

## Recommended Cuts

Card Name
- Card Layer:
- Cut Type:
- Confidence:
- Reason:
- Replacement Category:
- Notes:

## Possible Cuts

Card Name
- Card Layer:
- Cut Type:
- Confidence:
- Reason:
- Replacement Category:
- Verdict:

## Bracket-Driven Cuts / Bracket Pressure Review

Card Name
- Card Layer:
- Bracket Concern:
- Intended Bracket:
- Confidence:
- Reason:
- Verdict:

## Refined Deck Review Candidates

Card Name
- Card Layer:
- Label: Playtest-first review candidate
- Why to watch:
- Watch For:

## Conflict / Manual Review

Card Name
- Card Layer:
- Cut Pressure:
- Protection Pressure:
- Why it looked cuttable:
- Why it may belong:
- How to decide:
- Current Recommendation:

## Playtest First

Card Name
- Card Layer:
- Reason:
- Watch For:

## Protected From Cut

Card Name
- Card Layer:
- Protection Reason:
- Protection Confidence:

## Replacement Needs

- Category:
- Why the deck may need it:
- Suggested priority:
```

If a section has no entries, the agent should say:

```text
No clear entries identified.
```

---

## 53. Massive Over-Limit Output Structure

When the deck is massively over 100 cards and required cuts exceed confident candidates, use this structure:

```text
## Cut Pressure Review

Deck Size Status:
- Current deck size:
- Required cuts:
- Confident required cuts found:
- Required cuts needing manual review:
- Additional cuts still needed:
- Cut strictness:
- Intended bracket:

Layered Strategy Context:
- Primary strategy:
- Secondary strategy:
- Suppressed broad fallback strategies:
- Minor packages:
- Manual-review packages:

## Required Cuts Found Confidently

Card Name
- Card Layer:
- Cut Type:
- Confidence:
- Reason:
- Replacement Category:
- Notes:

## Required Cuts Requiring Manual Review

Card Name
- Card Layer:
- Cut Pressure:
- Protection Pressure:
- Why it may need to be cut:
- Why it may belong:
- How to decide:

## Protected/Core Cards Not Forced Into Cuts

Card Name
- Card Layer:
- Protection Reason:
- Why it was not forced into cuts:

## Additional Cuts Still Needed

The deck still needs X more cuts, but I cannot identify those cuts confidently without risking core synergy pieces.

## Bracket-Driven Cuts / Bracket Pressure Review

Card Name
- Card Layer:
- Bracket Concern:
- Intended Bracket:
- Confidence:
- Reason:
- Verdict:

## Replacement Needs

- Category:
- Why the deck may need it:
- Suggested priority:
```

This structure prevents massive over-limit decks from producing messy, overconfident, or contradictory cut advice.

---

# Final Advice Rules

## 54. Do Not Overstate Certainty

The agent should use careful language.

Good language:

- "Possible cut"
- "Recommended cut"
- "Review this slot"
- "This may be replaceable"
- "This looks off-plan based on the current strategy read"
- "Playtest first"
- "Manual review recommended"
- "Do not cut automatically"
- "This appears refined"
- "This is a bracket-pressure review flag"
- "This may support a minor package rather than the main plan"
- "This may be a good card, but it appears to support a minor package rather than the deck's main plan"
- "This card strongly supports the deck's plan, but it may push the deck above the intended bracket"

Bad language:

- "This card is bad"
- "Always cut this"
- "Never play this"
- "This is useless"
- "This is strictly worse"
- "This card does nothing"
- "This card is bad because it is too strong"
- "No role tag means cut"
- "Political cards are bad"
- "Fringe cards are bad"
- "Low-power means bad"

The deck helper should sound like a careful deck-building assistant, not a harsh judge.

---

## 55. Final Verdict Requirements

The final verdict should include:

- Whether the deck is legal by card count
- Whether the deck is over or short cards
- How many required cuts remain
- Whether recommended cuts are confident enough
- Whether any conflicts need manual review
- Whether the deck appears refined
- Whether bracket-pressure cards were treated as cuts or review flags
- Whether typal, political, niche, fringe, or emergent cards required manual review
- What replacement categories matter most
- Whether exact replacements were suggested or intentionally avoided

Example for over-limit deck:

```text
Final Verdict:
The deck is currently 103 cards, so it needs 3 required cuts. I found 2 high-confidence recommended cuts. The deck still needs 1 more cut, but I cannot identify that final cut confidently without risking a card that may be part of the deck's core engine. Review the Conflict / Manual Review section before making the final decision.
```

Example for refined legal deck:

```text
Final Verdict:
The deck is currently legal and no confident cuts were found. This appears refined. The listed review candidates are not recommended cuts; they are the only cards worth watching through playtesting.
```

Example for underfilled deck:

```text
Final Verdict:
The deck is currently short X cards, so there are no required cuts. The next step is to add cards that improve the highest-priority replacement categories before removing anything.
```

Example for bracket conflict:

```text
Final Verdict:
Several cards strongly support the deck's plan but may push the deck above the intended bracket. These were moved to Conflict / Manual Review rather than being treated as protected cards or recommended cuts.
```

---

# Safety Rails for v0.5.6 Hotfix

## 56. Never Do These

The agent must not:

- Present the same card as both a final cut and protected card
- Force core cards into cuts to satisfy required cut count
- Treat legal deck size as optimized deck quality
- Treat underfilled decks as needing required cuts
- Cut narrow synergy pieces without checking deck context
- Cut low-power cards just because they are low power
- Cut no-role cards only because they have no role tags
- Cut political cards just because they are political
- Cut fringe cards just because they are fringe
- Cut typal density pieces just because they are weak in a vacuum
- Cut niche cards just because the theme is uncommon
- Protect unsupported packages automatically
- Protect powerful cards just because they are powerful
- Suggest exact replacements when color identity is unverified
- Suggest exact replacements when bracket target or safety is unclear
- Suggest exact replacements when budget/collection constraints are unknown unless the user allows general suggestions
- Suggest cards outside the commander's color identity
- Suggest banned cards
- Ignore user-provided categories
- Ignore bracket goals
- Treat unknown bracket pressure as automatic cut pressure
- Replace synergy with generic staples by default
- Overstate confidence
- Hide uncertainty
- Treat possible cuts as final cuts
- Treat refined deck review candidates as recommended cuts
- Treat manual review cards as final recommendations
- Present fallback candidates with negative replaceability scores as normal recommended cuts
- Call bracket-pressure cards bad
- Call minor-package cards bad only because they are minor-package cards
- Let broad fallback archetypes override narrower commander-defined strategies
- Cut bridge cards without checking both connected themes
- Cut conversion points without checking whether the deck has another way to convert resources into progress

---

# v0.5.6 Hotfix Success Standard

This rule is working when the agent can say:

```text
These are not guaranteed cuts. These are the cards most worth reviewing based on curve, synergy, redundancy, role balance, and your deck's actual plan.
```

And when it can correctly explain:

```text
This card looks weak by generic standards, but it belongs because it supports your deck's sacrifice-recursion engine.
```

And when it can identify refined decks without forcing cuts:

```text
No confident cuts found. This appears refined. The cards below are not recommended cuts; they are the only cards worth watching through playtesting.
```

And when it refuses to force bad cuts:

```text
The deck needs X more cuts, but I cannot identify those cuts confidently without risking core synergy pieces.
```

And when it handles bracket pressure carefully:

```text
This is a strong card, not a bad card. The question is whether it fits the intended bracket and table experience.
```

And when it handles core bracket-pressure conflict correctly:

```text
This card strongly supports the deck's plan, but it may push the deck above the intended bracket.
```

And when it correctly separates unsupported packages from supported ones:

```text
Niche does not mean bad. Unsupported means bad.
```

And when it treats fringe themes as user-intent dependent:

```text
This looks like a fringe package rather than a core plan. I would not automatically cut it if this is intentional, but it needs manual review because the deck does not currently show enough support to make it reliable.
```

The goal is not to produce the longest cut list.

The goal is to produce the safest, clearest, most useful, and most context-aware cut advice possible.
