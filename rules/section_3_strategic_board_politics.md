# Section 3: Strategic & Board Politics Rules
Version: v0.5.6-ready
Purpose: Help the MTG Commander Deck Helper identify political strategies, multiplayer incentive engines, threat-redirection tools, social-pressure cards, and politics-specific cut/replacement logic.

Strategic and board-politics archetypes are not always defined by a single mechanic. They are defined by how the deck manipulates:
- Threat perception
- Combat direction
- Table incentives
- Resource flow
- Player behavior
- Punishment structures
- Negotiation leverage
- Defensive posture
- Social contract expectations

These themes should not be detected from one isolated card. Political strategies require enough density, payoff, and commander/deck support to meaningfully shape how the table behaves.

---

# 3.1 Core Philosophy: Politics as Incentive Engineering

Political Commander decks should be evaluated as incentive engines.

A political deck tries to answer one or more of these questions:

- Why should opponents attack someone else instead of me?
- Why should opponents spend removal on another player’s board?
- Why should opponents accept my deal?
- Why should opponents avoid targeting me?
- Why does giving resources to the table benefit me more?
- How do I profit when opponents fight each other?
- How do I punish normal game actions?
- How do I look less threatening while progressing toward a win?
- How do I survive being the obvious villain?

A weak political deck only asks the table for mercy.

A strong political deck changes the table’s incentives so that opponents naturally make choices that benefit the pilot.

Core political structure:

```yaml
political_engine:
  incentive:
  protection:
  payoff:
  inevitability:
```

A political deck should not be scored highly unless it has at least three of these four components.

---

# 3.2 Section 3 Output Fields

For each detected political strategy, record:

```yaml
political_strategy:
  name:
  role: primary | secondary | minor_package | support_package | manual_review
  confidence: low | medium | high
  commander_support: none | light | moderate | strong
  political_axis:
  incentive_type:
  payoff_type:
  protection_type:
  inevitability_present: true | false
  table_dependency: low | medium | high
  salt_risk: low | medium | high
  bracket_pressure: none | low | medium | high
  evidence:
    commander_text:
    role_counts:
    card_patterns:
    synergy_packages:
  cut_logic_impact:
  replacement_logic_impact:
  report_notes:
```

---

# 3.3 Political Strategy Role Definitions

## Primary Political Strategy

A political strategy may be primary only if:
- The commander supports the political axis, or the deck has very high political density.
- The deck contains repeated incentives or deterrents.
- The deck has clear payoff cards.
- The deck has a real win path.
- The political cards are not just incidental utility.

## Secondary Political Strategy

A political strategy should be secondary if:
- It meaningfully supports the primary game plan.
- It has moderate density.
- It changes combat, targeting, resource flow, or threat perception.
- It does not fully define the deck.

## Minor Political Package

A political package is minor if:
- It has a small number of political cards.
- It supports the main strategy but does not define the deck.
- It may be meta-dependent or table-dependent.

## Manual Review

Use manual review if:
- The deck contains isolated political cards.
- The political cards depend heavily on table behavior.
- The deck may be using cards for flavor or social reasons.
- The political theme could be accidental.

---

# 3.4 Global Political Primary Gate

A deck should not be labeled “Politics” as a primary strategy just because it contains political cards.

Use this gate:

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

If this gate fails, classify the theme as:
- Secondary political package
- Minor political package
- Manual review
- Support package

---

# 3.5 Political Signal Categories

Political signal cards may include:

```yaml
political_signal_categories:
  group_resource:
    - group_draw
    - group_ramp
    - gift_resource
    - tablewide_acceleration

  punishment:
    - table_damage
    - punisher
    - life_loss_engine
    - spell_punisher
    - draw_punisher
    - attack_punisher

  combat_direction:
    - goad
    - forced_attack
    - attack_elsewhere_incentive
    - forced_block
    - combat_restriction
    - shared_combat_incentive

  defense_and_deterrence:
    - pillowfort
    - attack_tax
    - combat_prevention
    - rattlesnake
    - fog
    - do_not_touch_me
    - revenge_trigger

  table_manipulation:
    - voting
    - monarch
    - initiative
    - bounty
    - curse
    - negotiated_removal
    - threat_redistribution

  resource_control:
    - donate_bad_gift
    - resource_redistribution
    - symmetrical_rule
    - table_police
    - soft_lock
    - board_reset

  hidden_positioning:
    - sandbag_control
    - secret_combo
    - hidden_threat
    - information_politics
    - low_threat_combo

  social_contract:
    - villain_deck
    - reputation_pressure
    - rule_zero
    - archenemy
```

---

# 3.6 Suppression Rules for Political Themes

Political themes are easy to over-detect. Use suppression aggressively.

## Suppress Generic Politics

If a more specific political strategy exists, suppress generic `politics` to secondary or support.

Prefer:
- `group_hug`
- `group_slug`
- `forced_combat`
- `goad`
- `pillowfort`
- `rattlesnake`
- `monarch_politics`
- `curse_politics`
- `voting_politics`
- `table_police`
- `donate_bad_gifts`
- `secret_combo`
- `villain_deck`

## Suppress Group Hug

Do not call a deck Group Hug if it only has:
- One group draw card
- One group ramp card
- A commander that incidentally helps others
- Symmetrical draw with no payoff

Instead classify as:
- Group resource minor package
- Mutual benefit support
- Manual review

## Suppress Group Slug

Do not call a deck Group Slug if it only has:
- One table damage card
- One punisher effect
- A single damage amplifier
- Incidental life loss

Instead classify as:
- Passive clock package
- Punisher minor package
- Lifedrain support
- Manual review

## Suppress Pillowfort

Do not call a deck Pillowfort if it only has:
- One attack tax
- One fog
- A single defensive enchantment
- Generic protection

Instead classify as:
- Defensive support package
- Control support
- Superfriends protection
- Manual review

## Suppress Chaos

Do not call a deck Chaos unless randomness, redirection, swapping, or instability is a meaningful part of the deck.

A deck with one wheel or one random effect is not a Chaos deck.

## Suppress Secret Combo

Do not call a deck Secret Combo unless:
- It has actual combo pieces.
- It has political camouflage or low-threat posture.
- The deck appears to win suddenly after looking harmless.

Otherwise classify as:
- Combo-adjacent value
- Hidden win package
- Manual review

---

# 3.7 Group Hug

## Definition

Group Hug decks give resources to everyone, such as cards, mana, lands, creatures, or life. They usually present as friendly while attempting to convert shared resources into a stronger endgame.

## Detection Signals

Increase Group Hug score for:
- Group draw
- Group ramp
- Extra land drops for multiple players
- Gifted creatures or tokens
- Life given to opponents
- Symmetrical resource acceleration
- Commander gives resources to opponents
- Tablewide benefit effects

## Primary Gate

```python
can_be_primary_group_hug = (
    (
        role_counts["group_draw"] >= 3
        or role_counts["group_ramp"] >= 3
        or role_counts["gift_resource"] >= 4
    )
    and (
        role_counts["hug_payoff"] >= 2
        or role_counts["asymmetrical_payoff"] >= 2
        or role_counts["alternate_win_condition"] >= 1
        or role_counts["pillowfort"] >= 3
    )
    and has_clear_win_path
)
```

## Payoff Requirements

Group Hug should have at least one payoff category:
- Draw payoff
- Token payoff from opponents drawing
- Pillowfort protection
- Alternate win condition
- Combo finish
- Asymmetrical resource conversion
- Political table leverage

## Cut Logic

Protect:
- Group resource cards with payoff support
- Asymmetrical payoffs
- Pillowfort pieces that protect the slower plan
- Alternate win conditions
- Commander-synergy group draw/ramp

Review:
- Group draw with no payoff
- Group ramp with no protection
- Cards that help opponents more than the pilot
- Cute symmetrical cards with no conversion plan
- Cards that accidentally kingmake

## Replacement Categories

- More asymmetrical payoff
- More pillowfort
- More alternate win support
- More card draw payoff
- More protection
- More win conditions

## Report Behavior

If detected, include:
- “How the deck benefits more than the table”
- “Risk of accelerating opponents”
- “Whether the deck has enough inevitability”
- “Cards that may accidentally help opponents too much”

---

# 3.8 Group Slug

## Definition

Group Slug decks punish everyone for normal game actions, such as drawing, casting spells, attacking, sacrificing, or playing lands.

## Detection Signals

Increase Group Slug score for:
- Tablewide damage
- Life-loss engines
- Spell punishment
- Draw punishment
- Attack punishment
- Landfall punishment
- Sacrifice punishment
- Damage amplification
- Lifegain buffers

## Primary Gate

```python
can_be_primary_group_slug = (
    (
        role_counts["table_damage"] >= 4
        or role_counts["punisher"] >= 4
        or role_counts["life_loss_engine"] >= 4
    )
    and (
        role_counts["damage_amplifier"] >= 1
        or role_counts["lifegain_buffer"] >= 2
        or role_counts["drain_payoff"] >= 2
        or role_counts["protection"] >= 2
    )
)
```

## Cut Logic

Protect:
- Repeatable table damage
- Damage amplifiers
- Lifegain buffers
- Drain engines
- Punisher pieces that always matter

Review:
- One-shot damage
- Punisher cards where opponents choose the harmless mode
- Expensive enchantments that do not immediately pressure life totals
- Slug cards without protection or clock
- Cards that damage you faster than opponents

## Replacement Categories

- More lifegain buffer
- More damage amplification
- More table drain
- More removal
- More protection
- Faster clock

## Report Behavior

Include:
- “How quickly the deck creates a table clock”
- “Whether the pilot can survive their own symmetrical damage”
- “Expected table hate level”
- “Cards that punish but do not advance lethal pressure”

---

# 3.9 Chaos

## Definition

Chaos decks destabilize the game through randomness, swaps, wheels, redirection, dice, coin flips, forced attacks, or unpredictable rule changes.

## Detection Signals

Increase Chaos score for:
- Randomized effects
- Coin flips
- Dice rolling
- Permanent swaps
- Spell redirection
- Wheels
- Forced chaos combat
- Global rule-changing effects
- Commander rewards randomness

## Primary Gate

```python
can_be_primary_chaos = (
    role_counts["random_effect"] >= 4
    or role_counts["coin_flip"] >= 4
    or role_counts["dice_roll"] >= 4
    or role_counts["chaos_effect"] >= 5
) and (
    role_counts["chaos_payoff"] >= 2
    or has_clear_win_path
)
```

## Cut Logic

Protect:
- Chaos pieces with payoff
- Random effects that generate value
- Dice/coin payoff cards
- Win conditions that benefit from instability

Review:
- Random effects with no payoff
- Cards that prolong the game without advancing the pilot
- Board-scrambling cards that help opponents more
- Chaos pieces that create salt but no win path

## Replacement Categories

- More chaos payoff
- More card draw
- More protection
- More reliable win conditions
- More damage payoff

## Report Behavior

Include:
- “Whether chaos is functional or just disruptive”
- “Salt/frustration risk”
- “How the deck actually wins”
- “Cards that create randomness without advantage”

---

# 3.10 Aikido / Judo

## Definition

Aikido decks use opponents’ aggression against them through damage reflection, attack punishment, revenge effects, redirection, and reactive blowouts.

## Detection Signals

Increase Aikido score for:
- Damage reflection
- Redirect damage
- Punish attackers
- Copy opponents’ large effects
- Revenge triggers
- Attack deterrents
- Instant-speed retaliation
- Commander rewards being attacked or opponents attacking

## Primary Gate

```python
can_be_primary_aikido = (
    role_counts["damage_reflection"] >= 3
    or role_counts["attack_punisher"] >= 4
    or role_counts["revenge_trigger"] >= 4
) and (
    role_counts["rattlesnake"] >= 2
    or role_counts["card_draw"] >= 5
    or role_counts["forced_combat"] >= 2
    or has_proactive_win_path
)
```

## Cut Logic

Protect:
- Damage reflection
- Attack punishers
- Rattlesnake permanents
- Forced combat cards that make opponents attack
- Card draw that prevents reactive hand depletion

Review:
- Reactive cards with no proactive backup
- Revenge effects that opponents can ignore
- Expensive redirection spells
- Cards that only work when losing

## Replacement Categories

- More proactive pressure
- More card draw
- More forced combat
- More instant-speed interaction
- More finishers

## Report Behavior

Include:
- “Can the deck win if opponents ignore it?”
- “Does the deck have enough proactive pressure?”
- “Which cards rely on opponents choosing to attack?”

---

# 3.11 Forced Combat / Goad

## Definition

Forced Combat and Goad decks make opponents attack, usually away from the pilot. They weaponize opposing creatures and use combat direction as removal, pressure, or table control.

## Detection Signals

Increase Forced Combat/Goad score for:
- Goad
- Forced attack
- Must attack each combat
- Attack elsewhere incentives
- Combat punishment
- Attack-trigger payoffs
- Opponent combat manipulation
- Commander goads or rewards attacking

## Primary Gate

```python
can_be_primary_forced_combat = (
    role_counts["goad"] >= 4
    or role_counts["forced_attack"] >= 4
    or role_counts["attack_elsewhere_incentive"] >= 4
) and (
    role_counts["combat_payoff"] >= 3
    or role_counts["attack_elsewhere_incentive"] >= 2
    or role_counts["table_damage"] >= 2
)
```

## Suppression Rules

If goad count is low, classify as:
- Combat manipulation support
- Let Them Fight package
- Threat redistribution package
- Manual review

## Cut Logic

Protect:
- Repeatable goad
- Forced attack effects
- Attack elsewhere incentives
- Combat damage payoffs
- Defensive cards that keep attacks away from pilot

Review:
- Goad cards in creature-light metas
- One-shot forced combat effects
- Combat manipulation with no payoff
- Cards that cannot answer combo/noncreature engines

## Replacement Categories

- More repeatable goad
- More removal for noncreature threats
- More defensive tools
- More attack payoff
- More card draw
- More board wipes

## Report Behavior

Include:
- “How well the deck handles creature-light pods”
- “Whether goad substitutes for removal too much”
- “How the deck closes after opponents weaken each other”

---

# 3.12 Pillowfort

## Definition

Pillowfort decks make attacking the pilot difficult, expensive, or pointless through taxes, prevention effects, fogs, blockers, and combat restrictions.

## Detection Signals

Increase Pillowfort score for:
- Attack taxes
- Propaganda effects
- Combat prevention
- Fogs
- Defensive enchantments
- Combat restrictions
- Deterrent blockers
- Commander supports defensive posture

## Primary Gate

```python
can_be_primary_pillowfort = (
    role_counts["attack_tax"] >= 3
    or role_counts["combat_prevention"] >= 3
    or role_counts["fort_protection"] >= 5
) and (
    role_counts["alternate_win_condition"] >= 1
    or role_counts["planeswalker"] >= 4
    or role_counts["enchantment_payoff"] >= 4
    or role_counts["combo_piece"] >= 2
    or has_clear_inevitability_engine
)
```

## Cut Logic

Protect:
- Attack taxes
- Repeatable combat prevention
- Enchantment-based defenses
- Win conditions that need time
- Pillowfort pieces protecting planeswalkers or combo

Review:
- Fort cards with no win condition
- Excessive fogs without recursion
- Defensive cards that do not stack meaningfully
- Pillowfort in a deck trying to win fast through combat

## Replacement Categories

- More inevitability
- More alternate win support
- More enchantment payoff
- More card draw
- More removal
- Fewer redundant fort pieces if win path is weak

## Report Behavior

Include:
- “Can the deck win from behind the fort?”
- “Does the deck have a real clock?”
- “Which cards only stall without advancing a win?”

---

# 3.13 Politics / Deal-Making

## Definition

Politics and Deal-Making decks create incentives, bargains, votes, gifts, monarch dynamics, curses, or removal leverage to manipulate player choices.

## Detection Signals

Increase Politics score for:
- Vote cards
- Monarch
- Bounties
- Gifts
- Curses
- Negotiated removal
- Cards that reward opponents for specific behavior
- Flexible answers
- Commander encourages deals

## Primary Gate

```python
can_be_primary_deal_politics = (
    role_counts["political_choice"] >= 4
    or role_counts["deal_incentive"] >= 4
    or role_counts["negotiated_removal"] >= 3
) and (
    role_counts["political_payoff"] >= 2
    or commander_supports_political_axis
)
```

## Cut Logic

Protect:
- Flexible interaction
- Political reward cards
- Vote payoffs
- Monarch engines
- Bounty cards with meaningful incentives

Review:
- Political cards that rely on opponents making bad choices
- Cards that are weak in silent/optimized pods
- Cute negotiation cards without payoff
- Cards that give opponents too much agency

## Replacement Categories

- More flexible removal
- More card advantage
- More reliable payoff
- More protection
- More finishers

## Report Behavior

Include:
- “How table-dependent this deck is”
- “Whether the deck works without negotiation”
- “Which cards may underperform in optimized or quiet pods”

---

# 3.14 Voting / Council’s Dilemma

## Definition

Voting decks use cards that make players vote on outcomes and attempt to benefit regardless of the choice.

## Detection Signals

Increase Voting score for:
- Vote cards
- Council’s Dilemma effects
- Will of the Council effects
- Vote manipulation
- Commander rewards voting
- Artifact/token generation from voting

## Primary Gate

```python
can_be_primary_voting = (
    role_counts["vote"] >= 4
    and (
        role_counts["vote_payoff"] >= 2
        or commander_supports_voting
    )
)
```

## Cut Logic

Protect:
- Vote cards with strong payoff
- Vote manipulation
- Commander-synergy voting pieces
- Cards where both outcomes benefit the pilot

Review:
- Cute vote cards with low impact
- Voting cards that give opponents too much control
- Vote cards without enough payoff density

## Replacement Categories

- More vote payoff
- More artifact/token payoff if voting creates tokens
- More control
- More protection
- More reliable win conditions

## Report Behavior

Include:
- “Does the pilot benefit either way?”
- “Are there enough vote payoffs?”
- “How much agency opponents get over your cards”

---

# 3.15 Monarch Politics

## Definition

Monarch decks use the monarch emblem to create card advantage and a combat mini-game around the crown.

## Detection Signals

Increase Monarch score for:
- Monarch introduction
- Monarch payoff
- Deathtouch blockers
- Pillowfort
- Goad
- Evasive creatures
- Commander supports monarch

## Primary Gate

```python
can_be_primary_monarch = (
    role_counts["monarch"] >= 3
    or commander_supports_monarch
) and (
    role_counts["crown_defense"] >= 3
    or role_counts["evasive_creature"] >= 3
    or role_counts["pillowfort"] >= 2
)
```

## Cut Logic

Protect:
- Monarch enablers
- Deathtouch blockers
- Evasive crown reclaimers
- Pillowfort
- Goad effects that protect crown

Review:
- Monarch cards if deck cannot defend/reclaim crown
- Expensive monarch cards
- Combat cards that do not support crown control

## Replacement Categories

- More evasive creatures
- More pillowfort
- More deathtouch/blockers
- More removal
- More card draw

## Report Behavior

Include:
- “Can the deck keep or reclaim monarch?”
- “Does monarch help opponents too much?”
- “How the deck uses the crown politically”

---

# 3.16 Curse Politics

## Definition

Curse decks enchant opponents with negative effects, incentives, or punishments, often making one player the preferred target.

## Detection Signals

Increase Curse score for:
- Curse Auras
- Curse recursion
- Enchantment payoff
- Attack cursed player incentives
- Damage or drain curses
- Commander rewards curses

## Primary Gate

```python
can_be_primary_curses = (
    role_counts["curse"] >= 5
    and (
        role_counts["curse_payoff"] >= 2
        or commander_supports_curses
        or role_counts["enchantment_recursion"] >= 2
    )
)
```

## Cut Logic

Protect:
- Repeatable curse engines
- Curse recursion
- Curses that scale tablewide
- Enchantment payoff
- Curses that redirect attacks effectively

Review:
- Curses that only annoy one player
- Low-impact curses
- Curses with no payoff
- Cards that create grudges without advancing the plan

## Replacement Categories

- More curse payoff
- More enchantment recursion
- More pillowfort
- More tablewide pressure
- More removal

## Report Behavior

Include:
- “Does the deck spread pressure or bully one player?”
- “Are curses meaningful enough to redirect behavior?”
- “Salt/grudge risk”

---

# 3.17 Bounty / Incentivized Combat

## Definition

Bounty decks reward opponents for attacking, killing, or pressuring specific players or creatures.

## Detection Signals

Increase Bounty score for:
- Bounty counters
- Rewards for attacking opponents
- Rewards for killing creatures
- Opponent-targeted incentives
- Commander creates bounties
- Political card draw from combat choices

## Primary Gate

```python
can_be_primary_bounty = (
    role_counts["bounty"] >= 3
    or role_counts["attack_reward"] >= 4
) and (
    role_counts["political_payoff"] >= 2
    or commander_supports_bounty
)
```

## Cut Logic

Protect:
- Meaningful bounty rewards
- Repeatable bounty placement
- Attack reward effects
- Political draw engines

Review:
- Rewards too small to change behavior
- Cards that help opponents without enough return
- Bounty cards that do not scale
- Incentives that help the leading player

## Replacement Categories

- More meaningful incentives
- More removal
- More card advantage
- More protection
- More finishers

## Report Behavior

Include:
- “Are the rewards big enough to affect choices?”
- “Does the deck accidentally help the current threat?”
- “How the deck profits from bounties”

---

# 3.18 Theft / Clone Politics

## Definition

Theft and Clone Politics decks scale to the table by stealing or copying the strongest opposing resources.

## Detection Signals

Increase Theft/Clone Politics score for:
- Steal creatures
- Clone opponents’ creatures
- Cast from opponents’ decks
- Reanimate opponents’ graveyards
- Copy opponents’ spells
- Commander rewards stolen cards

## Primary Gate

```python
can_be_primary_theft_politics = (
    role_counts["theft"] >= 4
    or role_counts["clone_opponent"] >= 4
    or role_counts["cast_opponent_card"] >= 4
) and (
    role_counts["theft_payoff"] >= 2
    or commander_supports_theft
)
```

## Cut Logic

Protect:
- Repeatable theft
- Clone effects with strong targets
- Mana fixing for stolen spells
- Theft payoff
- Graveyard theft engines

Review:
- Theft cards that rely on opponents having good targets
- One-shot steal without sacrifice or payoff
- High-cost clones
- Cards that create backlash but low advantage

## Replacement Categories

- More repeatable theft
- More clone value
- More sacrifice outlets
- More mana fixing
- More protection

## Report Behavior

Include:
- “How table-dependent the deck is”
- “Whether the deck can win if opponents’ cards are weak”
- “Emotional backlash risk”

---

# 3.19 Threat Redistribution

## Definition

Threat Redistribution decks manipulate who appears dangerous and who gets attacked through goad, curses, monarch, bounties, pillowfort, and selective removal.

## Detection Signals

Increase Threat Redistribution score for:
- Goad
- Curses
- Bounties
- Monarch
- Attack elsewhere incentives
- Selective removal
- Pillowfort
- Table talk support cards

## Primary Gate

```python
can_be_primary_threat_redistribution = (
    role_counts["threat_redirect"] >= 5
    or (
        role_counts["goad"] >= 2
        and role_counts["pillowfort"] >= 2
        and role_counts["political_incentive"] >= 2
    )
) and has_clear_win_path
```

## Cut Logic

Protect:
- Cards that redirect attacks
- Cards that make other players look threatening
- Selective removal
- Defensive cards that keep pilot safe
- Incentive cards that reward attacking elsewhere

Review:
- Threat-redirection cards with no payoff
- Cards that only work if opponents cooperate
- Political cards that become dead when pilot is ahead

## Replacement Categories

- More attack redirection
- More flexible removal
- More card advantage
- More finishers
- More defensive support

## Report Behavior

Include:
- “How the deck avoids becoming the threat”
- “What happens when the deck becomes obviously ahead”
- “Whether the strategy still works after table perception shifts”

---

# 3.20 Kingmaker / Table-Balancer

## Definition

Kingmaker or Table-Balancer decks help weaker players, punish leaders, and prevent runaway board states.

## Detection Signals

Increase Table-Balancer score for:
- Help-behind effects
- Punish-leading-player effects
- Symmetrical resets
- Political removal
- Shared resources
- Catch-up mechanics
- Commander supports parity

## Primary Gate

```python
can_be_primary_table_balancer = (
    role_counts["catch_up_mechanic"] >= 3
    or role_counts["leader_punisher"] >= 3
    or role_counts["parity_tool"] >= 4
) and (
    role_counts["self_advancement"] >= 3
    or has_clear_win_path
)
```

## Cut Logic

Protect:
- Catch-up cards that also advance pilot
- Leader-punishing effects
- Flexible removal
- Value engines that benefit from parity

Review:
- Cards that only help other players
- Effects that decide who wins without helping pilot
- Symmetrical cards the deck does not break
- Parity tools with no win condition

## Replacement Categories

- More self-advancing value
- More finishers
- More card draw
- More protection
- More asymmetrical payoff

## Report Behavior

Include:
- “Does this deck win, or only prevent others from winning?”
- “Kingmaker risk”
- “How the deck converts balance into victory”

---

# 3.21 Resource Redistribution / Donate / Bad Gifts

## Definition

Resource Redistribution decks give, take, exchange, donate, or rebalance resources. Donate/Bad Gifts decks give opponents harmful permanents.

## Detection Signals

Increase score for:
- Donate effects
- Harmful permanents to give away
- Permanent exchange
- Resource swapping
- Hand swapping
- Symmetrical equalizing
- Commander rewards giving permanents away

## Primary Gate

```python
can_be_primary_resource_redistribution = (
    role_counts["donate"] >= 3
    or role_counts["bad_gift"] >= 4
    or role_counts["resource_swap"] >= 4
) and (
    role_counts["donate_payoff"] >= 2
    or commander_supports_donate
)
```

## Cut Logic

Protect:
- Donate effects
- Bad gifts
- Cards that reward giving permanents away
- Protection from backlash
- Pillowfort support

Review:
- Bad gifts without donate effects
- Donate effects without meaningful gifts
- Symmetrical redistribution the deck does not break
- Cute but low-impact swap effects

## Replacement Categories

- More bad gifts
- More donate effects
- More protection
- More card draw
- More pillowfort
- More win conditions

## Report Behavior

Include:
- “Does the deck have enough gifts and enough ways to give them?”
- “Does the deck survive backlash?”
- “Are the gifts actually harmful enough?”

---

# 3.22 Rattlesnake

## Definition

Rattlesnake decks use visible deterrents that make attacking or targeting the pilot costly.

## Detection Signals

Increase Rattlesnake score for:
- Deathtouch blockers
- Revenge damage
- Attack punishment
- Sacrifice deterrents
- Instant-speed visible interaction
- Destroy-on-attack effects
- Commander discourages attacks

## Primary Gate

```python
can_be_primary_rattlesnake = (
    role_counts["rattlesnake"] >= 5
    or role_counts["attack_punisher"] >= 4
) and (
    role_counts["card_draw"] >= 4
    or role_counts["value_engine"] >= 3
    or has_clear_win_path
)
```

## Cut Logic

Protect:
- Strong deterrents
- Deathtouch blockers
- Attack punishers
- Visible interaction
- Value engines that grow while opponents avoid you

Review:
- Weak deterrents opponents can ignore
- Reactive cards with no payoff
- Cards that only work after damage is already done
- Rattlesnake cards without a win path

## Replacement Categories

- Stronger deterrents
- More card draw
- More removal
- More win conditions
- More protection

## Report Behavior

Include:
- “Are deterrents strong enough to matter?”
- “What happens if opponents ignore the warning?”
- “How safety becomes victory”

---

# 3.23 Fog / Turbo-Fog Politics

## Definition

Fog decks repeatedly prevent combat damage and manipulate combat math, often buying time for alternate wins, planeswalkers, mill, or inevitability.

## Detection Signals

Increase Fog score for:
- Fog effects
- Repeatable combat prevention
- Fog recursion
- Pillowfort
- Planeswalkers
- Alternate win conditions
- Commander supports fog strategy

## Primary Gate

```python
can_be_primary_turbo_fog = (
    role_counts["fog"] >= 5
    or role_counts["combat_prevention"] >= 5
) and (
    role_counts["alternate_win_condition"] >= 1
    or role_counts["planeswalker"] >= 4
    or role_counts["mill"] >= 3
    or has_clear_inevitability_engine
)
```

## Cut Logic

Protect:
- Repeatable fogs
- Fog recursion
- Alternate win conditions
- Planeswalkers
- Pillowfort pieces

Review:
- One-shot fogs with no recursion
- Fogs in creature-light metas
- Fog density with no win condition
- Defensive cards that do not stop noncombat wins

## Replacement Categories

- More inevitability
- More alternate win support
- More card draw
- More noncombat interaction
- More recursion

## Report Behavior

Include:
- “Can the deck win before opponents stop relying on combat?”
- “Does the deck answer noncombat wins?”
- “Fog density vs payoff density”

---

# 3.24 Table Police / Rule Enforcer

## Definition

Table Police decks punish specific behaviors such as tutoring, drawing too many cards, casting too many spells, graveyard abuse, or comboing.

## Detection Signals

Increase Table Police score for:
- Tutor hate
- Draw punishment
- Spell limits
- Graveyard hate
- Stack interaction
- Tax effects
- Anti-combo permanents
- Commander enforces rules

## Primary Gate

```python
can_be_primary_table_police = (
    role_counts["behavior_punisher"] >= 4
    or role_counts["rule_enforcer"] >= 4
    or role_counts["anti_combo"] >= 4
) and (
    role_counts["win_condition"] >= 2
    or role_counts["value_engine"] >= 3
)
```

## Cut Logic

Protect:
- Relevant hate pieces
- Rule-setting permanents that do not hurt the deck
- Anti-combo tools
- Tax damage engines
- Control finishers

Review:
- Hate pieces irrelevant to the expected meta
- Cards that shut off the deck’s own plan
- High-salt cards at casual tables
- Restriction pieces without a win condition

## Replacement Categories

- More meta-relevant hate
- More card draw
- More protection
- More finishers
- More flexible interaction

## Report Behavior

Include:
- “What behavior the deck punishes”
- “Whether the restriction package matches intended table”
- “Salt risk”
- “Whether the deck becomes Stax in practice”

---

# 3.25 Punisher / Choice Punisher

## Definition

Punisher decks give opponents bad choices, such as taking damage, sacrificing permanents, letting the pilot draw, or suffering a worse effect.

## Detection Signals

Increase Punisher score for:
- Opponent chooses damage or sacrifice
- Opponent chooses card draw or life loss
- Choice-based punishment
- Commander punishes actions
- Damage amplification
- Table drain

## Primary Gate

```python
can_be_primary_punisher = (
    role_counts["punisher"] >= 5
    or role_counts["choice_punisher"] >= 4
) and (
    role_counts["damage_amplifier"] >= 1
    or role_counts["table_damage"] >= 3
    or role_counts["drain_payoff"] >= 2
)
```

## Cut Logic

Protect:
- Punisher effects where all choices are bad
- Damage amplifiers
- Repeatable punishment
- Table drain
- Lifegain buffers

Review:
- Punisher cards with one harmless mode
- Cards where opponents choose the least relevant penalty
- Expensive punisher pieces
- Punishment without lethal pressure

## Replacement Categories

- More damage amplification
- More guaranteed drain
- More removal
- More card draw
- More pressure

## Report Behavior

Include:
- “Are both choices actually bad?”
- “Can opponents ignore the punishment?”
- “Does the deck convert punishment into a clock?”

---

# 3.26 Attack Elsewhere Incentive

## Definition

Attack Elsewhere decks reward opponents for attacking players other than the pilot.

## Detection Signals

Increase Attack Elsewhere score for:
- Draw when opponents attack each other
- Counters for attacking others
- Treasure/rewards for attacking elsewhere
- Goad support
- Commander rewards opponents attacking each other

## Primary Gate

```python
can_be_primary_attack_elsewhere = (
    role_counts["attack_elsewhere_incentive"] >= 4
    or commander_supports_attack_elsewhere
) and (
    role_counts["defensive_support"] >= 2
    or role_counts["political_payoff"] >= 2
)
```

## Cut Logic

Protect:
- Attack elsewhere rewards
- Defensive support
- Cards that scale when opponents fight
- Goad or forced combat support

Review:
- Incentives too small to change behavior
- Cards that help the current threat too much
- Incentives without protection
- Cards that fail in creature-light pods

## Replacement Categories

- More meaningful incentives
- More goad
- More defensive support
- More removal
- More finishers

## Report Behavior

Include:
- “Are the incentives large enough?”
- “Does the deck profit from opponents fighting?”
- “What happens against noncombat decks?”

---

# 3.27 Goad-Control

## Definition

Goad-Control uses goad as a form of board control, turning opposing creatures into pressure against other players instead of killing them directly.

## Detection Signals

Increase Goad-Control score for:
- Goad
- Forced attack
- Removal-lite combat manipulation
- Board wipes after combat
- Attack punishment
- Commander goads repeatedly
- Noncreature interaction backup

## Primary Gate

```python
can_be_primary_goad_control = (
    role_counts["goad"] >= 4
    and (
        role_counts["targeted_removal"] >= 3
        or role_counts["board_wipe"] >= 2
        or role_counts["control_piece"] >= 4
    )
)
```

## Cut Logic

Protect:
- Repeatable goad
- Removal for utility creatures
- Board wipes
- Defensive pieces
- Cards that turn combat into removal

Review:
- Goad cards with no control backup
- One-shot goad effects
- Combat-only answers in combo-heavy pods
- Cards that cannot handle noncreature engines

## Replacement Categories

- More targeted removal
- More board wipes
- More repeatable goad
- More card draw
- More noncreature interaction

## Report Behavior

Include:
- “Does the deck mistake goad for complete removal?”
- “Can it answer combo and utility creatures?”
- “How combat pressure becomes control”

---

# 3.28 Mutual Benefit With Hidden Asymmetry

## Definition

These decks appear symmetrical but are built so the pilot benefits more from shared resources than opponents do.

## Detection Signals

Increase score for:
- Group draw plus draw payoff
- Group ramp plus larger payoffs
- Shared tokens plus token payoff
- Shared life plus lifegain payoff
- Tablewide acceleration plus asymmetrical payoff
- Commander rewards shared action

## Primary Gate

```python
can_be_primary_hidden_asymmetry = (
    role_counts["group_resource"] >= 4
    and role_counts["asymmetrical_payoff"] >= 2
)
```

## Cut Logic

Protect:
- Shared resource effects with payoff
- Asymmetrical payoffs
- Cards that convert opponent benefit into pilot advantage
- Protection from accelerated opponents

Review:
- Symmetrical cards with no asymmetry
- Cards that accelerate opponents into wins
- Group hug pieces without payoff
- Payoffs too slow to matter

## Replacement Categories

- More asymmetrical payoff
- More protection
- More win conditions
- More card draw
- More interaction

## Report Behavior

Include:
- “How the deck benefits more”
- “What resources are being shared”
- “Risk of helping opponents too much”

---

# 3.29 Social Contract / Rule Zero Decks

## Definition

Social Contract decks are built around table experience, theme restrictions, joke mechanics, acorn/silver-border cards, or deliberately unusual game experiences.

## Detection Signals

Increase Social Contract score for:
- Acorn/silver-border references
- Attractions
- Joke mechanics
- Extreme theme restriction
- Rule Zero-required cards
- Commander chosen for table experience over optimization

## Classification Rule

Never treat Social Contract as a normal optimization archetype.

Classify as:
- Rule Zero / social contract
- Manual review
- User-intent dependent

## Cut Logic

Protect:
- Theme-defining cards
- Rule Zero identity cards
- Cards the user intentionally included for experience

Review:
- Only if the user asks for optimization
- Cards that undermine the stated table experience
- Cards that may violate table expectations

## Replacement Categories

- More theme support
- More table-friendly interaction
- More clarity of win condition
- More pregame communication support

## Report Behavior

Include:
- “Requires pregame communication”
- “Optimization may not be the goal”
- “Ask user whether fun/theme or power matters more”

---

# 3.30 Archenemy / Villain Deck

## Definition

Villain decks intentionally become the table’s main threat through oppressive commanders, huge board states, discard, theft, mass sacrifice, or scary inevitability.

## Detection Signals

Increase Villain score for:
- High-reputation commander
- Mass discard
- Mass sacrifice
- Oppressive theft
- Large board presence
- Hard control
- Obvious combo threat
- Commander creates fear on sight

## Primary Gate

```python
can_be_primary_villain = (
    role_counts["oppressive_effect"] >= 4
    or commander_has_high_threat_reputation
) and (
    role_counts["resilience"] >= 3
    or role_counts["protection"] >= 3
    or role_counts["fast_win"] >= 1
)
```

## Cut Logic

Protect:
- Resilience
- Protection
- Fast win conditions
- Board rebuild tools
- Cards that justify archenemy pressure

Review:
- Slow villain cards with no protection
- High-salt cards that do not help win
- Threatening cards that make the deck archenemy too early
- Cards that increase reputation but lower consistency

## Replacement Categories

- More protection
- More resilience
- More efficient win conditions
- More card draw
- More removal

## Report Behavior

Include:
- “Expected archenemy pressure”
- “Can the deck survive three opponents?”
- “Pregame communication recommended if commander has high reputation”

---

# 3.31 Secret Combo / Low-Threat Combo

## Definition

Secret Combo decks appear harmless, political, or value-oriented while quietly assembling a sudden win.

## Detection Signals

Increase Secret Combo score for:
- Compact combo pieces
- Low-threat posture
- Group hug/pillowfort shell
- Tutors
- Card selection
- Political camouflage
- Alternate win conditions
- Commander enables hidden combo

## Primary Gate

```python
can_be_primary_secret_combo = (
    role_counts["combo_piece"] >= 3
    and (
        role_counts["pillowfort"] >= 2
        or role_counts["group_hug"] >= 2
        or role_counts["low_threat_value"] >= 4
    )
    and (
        role_counts["tutor"] >= 2
        or role_counts["card_selection"] >= 4
    )
)
```

## Cut Logic

Protect:
- Combo pieces
- Tutors
- Card selection
- Political camouflage
- Protection

Review:
- Combo pieces with no support
- Camouflage cards that do not advance combo or survival
- Slow value cards that delay win too much
- Bracket-pressure cards if user wants lower power

## Replacement Categories

- More card selection
- More protection
- More combo redundancy
- More survivability
- More bracket-appropriate alternatives

## Report Behavior

Include:
- “How hidden the win really is”
- “Whether the table will recognize the combo”
- “Bracket/pregame discussion risk”

---

# 3.32 Sandbag / Reactive Control Politics

## Definition

Sandbag decks avoid looking threatening, hold up interaction, and intervene only when a player is about to win.

## Detection Signals

Increase Sandbag score for:
- Instant-speed interaction
- Flash threats
- Counterspells
- Minimal board presence
- Card draw at instant speed
- Reactive commander
- Control finishers

## Primary Gate

```python
can_be_primary_sandbag_control = (
    role_counts["instant_speed_interaction"] >= 6
    and (
        role_counts["card_draw"] >= 5
        or commander_supports_reactive_play
    )
    and has_clear_win_path
)
```

## Cut Logic

Protect:
- Instant-speed interaction
- Flash threats
- Flexible answers
- Card draw
- Finishers

Review:
- Sorcery-speed threats that expose the pilot
- Narrow answers
- Cards that require tapping out without payoff
- Reactive cards if deck lacks win condition

## Replacement Categories

- More instant-speed draw
- More flexible answers
- More finishers
- More mana efficiency
- More protection

## Report Behavior

Include:
- “Does the deck develop while holding answers?”
- “Can it stop one threat and still survive the next?”
- “Is there a clear endgame?”

---

# 3.33 Revenge / Retaliation

## Definition

Retaliation decks punish opponents for attacking, targeting, or damaging the pilot or their permanents.

## Detection Signals

Increase Retaliation score for:
- Revenge triggers
- Punish attackers
- Punish targeting
- Destroy creatures that hit you
- Drain after damage
- Commander rewards being attacked

## Primary Gate

```python
can_be_primary_retaliation = (
    role_counts["revenge_trigger"] >= 4
    or role_counts["attack_punisher"] >= 4
) and (
    role_counts["proactive_pressure"] >= 2
    or role_counts["card_draw"] >= 4
    or role_counts["forced_combat"] >= 2
)
```

## Cut Logic

Protect:
- Revenge triggers
- Attack punishers
- Forced combat support
- Card draw
- Defensive pieces

Review:
- Cards that only work after falling behind
- Retaliation without proactive plan
- Effects opponents can ignore
- Expensive revenge cards

## Replacement Categories

- More proactive threats
- More forced combat
- More card draw
- More protection
- More removal

## Report Behavior

Include:
- “Can the deck win if ignored?”
- “Are opponents forced to trigger your revenge cards?”
- “Does retaliation become pressure?”

---

# 3.34 Shared Combat Incentive

## Definition

Shared Combat Incentive decks make combat profitable for everyone to speed up the game and push opponents into fighting each other.

## Detection Signals

Increase score for:
- Everyone attacks effects
- Combat rewards to multiple players
- Forced combat
- Attack triggers
- Goad
- Commander rewards tablewide combat

## Primary Gate

```python
can_be_primary_shared_combat = (
    role_counts["shared_combat_incentive"] >= 4
    or role_counts["forced_attack"] >= 4
) and (
    role_counts["combat_payoff"] >= 3
    or role_counts["attack_trigger"] >= 3
)
```

## Cut Logic

Protect:
- Shared attack incentives
- Combat payoff
- Goad
- Haste
- Defensive tools

Review:
- Cards that help enemy combat decks more
- Combat incentives without protection
- Effects that force pilot into bad attacks
- Weak attack payoffs

## Replacement Categories

- More combat payoff
- More protection
- More goad
- More board control
- More finishers

## Report Behavior

Include:
- “Who benefits most from everyone attacking?”
- “Can the deck survive the faster game?”
- “Does it backfire against stronger combat decks?”

---

# 3.35 Forced Blocking / Combat Manipulation

## Definition

Combat Manipulation decks force bad blocks, prevent blocks, manipulate combat decisions, or make combat math unfavorable for opponents.

## Detection Signals

Increase score for:
- Forced blocks
- Lure effects
- Menace support
- Can’t-block effects
- Combat damage triggers
- Goad
- Commander manipulates combat

## Primary Gate

```python
can_be_primary_combat_manipulation = (
    role_counts["forced_block"] >= 3
    or role_counts["cant_block"] >= 3
    or role_counts["combat_manipulation"] >= 5
) and (
    role_counts["combat_payoff"] >= 3
    or role_counts["saboteur"] >= 3
)
```

## Cut Logic

Protect:
- Combat manipulation tied to payoff
- Evasion
- Lure effects if deck benefits
- Deathtouch if forcing blocks
- Attack-trigger payoffs

Review:
- Combat manipulation in noncombat decks
- Forced block effects without payoff
- Cards weak against spell-combo decks
- Effects that do not scale in multiplayer

## Replacement Categories

- More payoff
- More evasion
- More removal
- More protection
- More backup win conditions

## Report Behavior

Include:
- “Does the deck have a noncombat backup?”
- “Are combat tricks advancing the win condition?”
- “How the deck handles creature-light pods”

---

# 3.36 Tablewide Resource Acceleration

## Definition

These decks accelerate the entire table with extra lands, cards, mana, or other resources but are built to exploit the faster game better.

## Detection Signals

Increase score for:
- Group ramp
- Group draw
- Shared mana
- Tablewide cost reduction
- Extra land effects
- Commander benefits from acceleration

## Primary Gate

```python
can_be_primary_tablewide_acceleration = (
    role_counts["group_ramp"] >= 3
    or role_counts["group_draw"] >= 3
    or role_counts["tablewide_acceleration"] >= 4
) and (
    role_counts["asymmetrical_payoff"] >= 2
    or role_counts["protection"] >= 3
    or role_counts["fast_payoff"] >= 2
)
```

## Cut Logic

Protect:
- Group acceleration with strong payoff
- Asymmetrical payoff
- Protection from fast opponents
- Payoffs that scale better than opponents

Review:
- Acceleration without payoff
- Group ramp in combo-heavy pods
- Cards that let opponents win first
- Symmetrical cards with no asymmetry

## Replacement Categories

- More asymmetrical payoff
- More protection
- More interaction
- More win conditions
- More table control

## Report Behavior

Include:
- “Does the deck exploit the acceleration better?”
- “Risk of giving opponents too much”
- “How soon the deck converts shared resources into a win”

---

# 3.37 Anti-Combo Social Police

## Definition

Anti-Combo Social Police decks stop fast combos and explosive lines through hatebears, graveyard hate, tutor hate, stack interaction, and taxes.

## Detection Signals

Increase score for:
- Rule of law effects
- Tutor hate
- Graveyard hate
- Stack interaction
- Anti-free-spell effects
- Anti-storm cards
- Commander punishes greed

## Primary Gate

```python
can_be_primary_anti_combo = (
    role_counts["anti_combo"] >= 5
    or (
        role_counts["tutor_hate"] >= 2
        and role_counts["graveyard_hate"] >= 2
        and role_counts["rule_limiter"] >= 2
    )
) and has_clear_win_path
```

## Cut Logic

Protect:
- Relevant anti-combo hate
- Stack interaction
- Tutor hate
- Graveyard hate
- Rule limiters that do not hurt pilot

Review:
- Hate irrelevant to the intended bracket
- Cards that over-police casual tables
- Anti-combo pieces that shut off the pilot’s plan
- Hate with no pressure behind it

## Replacement Categories

- More flexible interaction
- More pressure
- More card draw
- More protection
- More meta-appropriate hate

## Report Behavior

Include:
- “Is anti-combo appropriate for the intended bracket?”
- “Does the deck still win?”
- “Does the deck become oppressive in low-power pods?”

---

# 3.38 Do Not Touch Me Control

## Definition

These decks punish targeting, attacking, or interacting with the pilot or their board through ward, hexproof, protection, damage reflection, and defensive triggers.

## Detection Signals

Increase score for:
- Ward
- Hexproof
- Protection
- Anti-targeting effects
- Punish targeting
- Defensive triggers
- Rattlesnake permanents

## Primary Gate

```python
can_be_primary_do_not_touch_me = (
    role_counts["anti_targeting"] >= 4
    or role_counts["board_protection"] >= 5
) and (
    role_counts["protected_win_condition"] >= 2
    or role_counts["voltron"] >= 3
    or role_counts["value_engine"] >= 3
)
```

## Cut Logic

Protect:
- Protection layers
- Anti-targeting effects
- Protected win conditions
- Commander protection

Review:
- Protection without pressure
- Redundant protection beyond need
- Defensive cards that do not protect key engine
- Cards that fail against board wipes

## Replacement Categories

- More win conditions
- More card draw
- More board wipe resilience
- More protected threats
- More interaction

## Report Behavior

Include:
- “Does protection convert into victory?”
- “Does the deck fold to board wipes?”
- “Which cards are defensive but not advancing the plan?”

---

# 3.39 Mutual Destruction / Board Reset Politics

## Definition

Board Reset Politics decks repeatedly reset the board, punish overextension, or threaten wipes to control player behavior.

## Detection Signals

Increase score for:
- Board wipes
- Repeatable board resets
- Commander death/reset trigger
- Indestructible own permanents
- Graveyard rebuild
- Planeswalkers
- Threaten-to-reset effects

## Primary Gate

```python
can_be_primary_board_reset_politics = (
    role_counts["board_wipe"] >= 4
    or role_counts["board_reset"] >= 4
) and (
    role_counts["break_parity"] >= 2
    or role_counts["recursion"] >= 3
    or role_counts["planeswalker"] >= 3
    or commander_supports_board_reset
)
```

## Cut Logic

Protect:
- Board wipes the deck breaks parity on
- Recursion
- Indestructible/protected threats
- Planeswalkers
- Commander-supported reset pieces

Review:
- Excessive wipes with no win condition
- Wipes that hurt the pilot more
- Reset cards that create miserable stalls
- Board wipes in creature-heavy own decks

## Replacement Categories

- More parity-breaking tools
- More finishers
- More recursion
- More card draw
- Fewer redundant wipes if deck cannot close

## Report Behavior

Include:
- “How the deck breaks parity”
- “Whether board resets lead to victory”
- “Game-stall/salt risk”

---

# 3.40 Life Total Politics

## Definition

Life Total Politics decks manipulate life totals as a political or strategic resource.

## Detection Signals

Increase score for:
- Large lifegain
- Life exchange
- Life payment
- Life total alternate wins
- Lifedrain
- Punish high/low life totals
- Commander manipulates life

## Primary Gate

```python
can_be_primary_life_politics = (
    role_counts["life_manipulation"] >= 4
    or role_counts["life_exchange"] >= 2
) and (
    role_counts["life_payoff"] >= 2
    or role_counts["lifedrain"] >= 3
    or role_counts["alternate_win_condition"] >= 1
)
```

## Cut Logic

Protect:
- Repeatable life manipulation
- Lifegain payoff
- Lifedrain
- Alternate win conditions
- Life exchange finishers

Review:
- Lifegain without payoff
- Life exchange cards with no support
- Cards that make pilot look too safe without advancing win
- One-shot life gain

## Replacement Categories

- More lifegain payoff
- More lifedrain
- More alternate win support
- More protection
- More card draw

## Report Behavior

Include:
- “How life total becomes a resource”
- “Whether high life makes pilot a target”
- “Does life gain convert into a win?”

---

# 3.41 Information Politics / Hidden Threats

## Definition

Information Politics decks use hidden zones, face-down creatures, instant-speed play, traps, or unknown combo pieces to make opponents uncertain.

## Detection Signals

Increase score for:
- Morph/disguise/manifest
- Flash
- Hidden combo
- Face-down payoffs
- Trap effects
- Instant-speed interaction
- Commander rewards hidden information

## Primary Gate

```python
can_be_primary_information_politics = (
    role_counts["hidden_information"] >= 5
    or role_counts["face_down"] >= 5
) and (
    role_counts["hidden_payoff"] >= 2
    or commander_supports_hidden_information
)
```

## Cut Logic

Protect:
- Face-down payoff
- Hidden information enablers
- Flash interaction
- Surprise win pieces
- Cards that punish wrong guesses

Review:
- Hidden cards with low payoff
- Face-down cards that are inefficient alone
- Tricks that do not scale to multiplayer
- Hidden threats with no closing power

## Replacement Categories

- More hidden payoff
- More protection
- More card draw
- More surprise finishers
- More interaction

## Report Behavior

Include:
- “Does hidden information matter?”
- “Can the deck punish wrong guesses?”
- “Are face-down cards strong enough?”

---

# 3.42 Shared Enemy / Table Alliance

## Definition

Shared Enemy decks create temporary alliances against the leading player through bounties, curses, removal, gifts, or attack incentives.

## Detection Signals

Increase score for:
- Leader-punishing cards
- Bounties
- Curses
- Attack incentives
- Flexible removal
- Gift-based alliance
- Commander rewards attacking the leader

## Primary Gate

```python
can_be_primary_shared_enemy = (
    role_counts["shared_enemy_incentive"] >= 4
    or role_counts["leader_punisher"] >= 3
) and (
    role_counts["self_advancement"] >= 3
    or role_counts["political_payoff"] >= 2
)
```

## Cut Logic

Protect:
- Cards that identify or pressure the leader
- Flexible removal
- Bounty/curse cards with payoff
- Political draw engines

Review:
- Cards that only help allies
- Tools that do not advance pilot
- Effects that fail when pilot becomes the threat
- Weak incentives

## Replacement Categories

- More self-advancing value
- More flexible interaction
- More finishers
- More protection
- More political payoff

## Report Behavior

Include:
- “What happens when the pilot becomes the next threat?”
- “Does alliance-building advance the pilot?”
- “Kingmaker risk”

---

# 3.43 Fairness / Symmetrical Rules

## Definition

Fairness decks use symmetrical rules that seem equal but are built to break parity.

## Detection Signals

Increase score for:
- Everyone sacrifices
- Everyone draws
- Everyone taxed
- Everyone limited to one spell
- Creatures enter tapped
- Symmetrical restrictions
- Commander breaks parity

## Primary Gate

```python
can_be_primary_fairness = (
    role_counts["symmetrical_rule"] >= 4
    or role_counts["rule_limiter"] >= 4
) and (
    role_counts["break_parity"] >= 2
    or commander_breaks_parity
)
```

## Cut Logic

Protect:
- Symmetrical effects the deck breaks
- Parity-breaking engines
- Cards that punish opponents more than pilot
- Win conditions under the restrictions

Review:
- Symmetrical cards the deck does not break
- Restrictions that hurt pilot equally
- High-salt effects without win condition
- Cards that make the deck Stax unintentionally

## Replacement Categories

- More parity-breaking support
- More win conditions
- More protection
- More card draw
- More table-appropriate alternatives

## Report Behavior

Include:
- “How the deck breaks parity”
- “Does this feel fair only to the pilot?”
- “Salt and bracket risk”

---

# 3.44 Negotiated Removal

## Definition

Negotiated Removal decks use flexible answers as bargaining chips, turning interaction into social leverage.

## Detection Signals

Increase score for:
- Flexible removal
- Modal interaction
- Instant-speed removal
- Political commander
- Vote/removal overlap
- Table-talk-dependent cards

## Primary Gate

```python
can_be_primary_negotiated_removal = (
    role_counts["flexible_removal"] >= 6
    and (
        role_counts["political_payoff"] >= 2
        or commander_supports_politics
    )
)
```

## Cut Logic

Protect:
- Flexible removal
- Modal answers
- Instant-speed interaction
- Political payoff

Review:
- Narrow removal
- Removal that cannot be leveraged politically
- Too much interaction without win condition
- Cards that require explicit table bargaining in pods that dislike it

## Replacement Categories

- More flexible interaction
- More win conditions
- More card draw
- More political payoff
- More protection

## Report Behavior

Include:
- “Does removal become leverage?”
- “Does the deck work if players refuse deals?”
- “Interaction-to-win-condition balance”

---

# 3.45 Soft Lock Politics

## Definition

Soft Lock decks create board states where opponents can technically act, but their best actions are discouraged or inefficient.

## Detection Signals

Increase score for:
- Taxes
- Repeatable bounce
- Pillowfort
- Combat restrictions
- Graveyard denial
- Tap/untap restriction
- Rule-setting pieces
- Commander supports lock

## Primary Gate

```python
can_be_primary_soft_lock = (
    role_counts["soft_lock"] >= 4
    or (
        role_counts["tax"] >= 3
        and role_counts["restriction"] >= 3
    )
) and (
    role_counts["win_condition"] >= 2
    or has_clear_inevitability_engine
)
```

## Cut Logic

Protect:
- Soft lock pieces
- Protection for lock pieces
- Win conditions under lock
- Card draw engines

Review:
- Locks that do not advance victory
- Restriction pieces that hurt pilot
- Salt-heavy locks in casual bracket
- Redundant lock pieces with no finisher

## Replacement Categories

- More finishers
- More protection
- More card draw
- More parity-breaking tools
- Less oppressive alternatives if lower bracket

## Report Behavior

Include:
- “Can the deck end the game after establishing control?”
- “Does the lock hurt the pilot?”
- “Salt/stall risk”

---

# 3.46 Bribery / Gift-Based Politics

## Definition

Gift-Based Politics decks give specific resources to specific opponents to influence behavior. Unlike Group Hug, gifts are targeted and transactional.

## Detection Signals

Increase score for:
- Targeted gifts
- Gift counters
- Granting cards/resources to one opponent
- Commander gives resources selectively
- Cards that reward giving
- Political incentives

## Primary Gate

```python
can_be_primary_gift_politics = (
    role_counts["targeted_gift"] >= 4
    or commander_supports_gifting
) and (
    role_counts["gift_payoff"] >= 2
    or role_counts["political_payoff"] >= 2
)
```

## Cut Logic

Protect:
- Gifts with meaningful payoff
- Targeted incentives
- Cards that create alliances
- Cards that benefit pilot more than recipient

Review:
- Gifts that help the current threat
- Gifts with no payoff
- Cards that rely on opponents remembering favors
- Low-impact bribes

## Replacement Categories

- More gift payoff
- More protection
- More card draw
- More defensive tools
- More finishers

## Report Behavior

Include:
- “Does gifting help the pilot more?”
- “Risk of helping the wrong opponent”
- “Table-dependency level”

---

# 3.47 Political Combo Deterrence

## Definition

Political Combo Deterrence decks use open information to discourage opponents from attempting combo wins.

## Detection Signals

Increase score for:
- Visible counterspells or activated counters
- Graveyard hate
- Tax permanents
- Sacrifice deterrents
- Anti-combo hatebears
- Commander can interrupt wins

## Primary Gate

```python
can_be_primary_combo_deterrence = (
    role_counts["visible_interaction"] >= 3
    and role_counts["anti_combo"] >= 3
) and has_clear_win_path
```

## Cut Logic

Protect:
- Visible deterrents
- Anti-combo hate
- Stack interaction
- Graveyard hate
- Tax pieces

Review:
- Deterrents that only delay opponents
- Hate that draws removal without backup
- Anti-combo pieces irrelevant to intended bracket
- Interaction with no win condition

## Replacement Categories

- More card draw
- More protection
- More flexible answers
- More finishers
- More meta-appropriate hate

## Report Behavior

Include:
- “Can the deck stop combo or only delay it?”
- “Will opponents remove shields first?”
- “Does the deck have enough win pressure?”

---

# 3.48 Social Pressure / Reputation Decks

## Definition

Some commanders create political pressure before the game begins because of their reputation.

## Detection Signals

Increase Reputation score for:
- High-reputation commander
- Known hated archetype
- Discard/theft/poison/turbo-combo reputation
- Fast mana and high-pressure cards
- Commander commonly associated with oppressive play

## Classification Rule

Reputation is not an archetype by itself. It is a report modifier.

```yaml
reputation_modifier:
  none
  low
  medium
  high
```

## Cut Logic

Protect:
- Resilience if deck draws early hate
- Pregame communication notes
- Defensive setup
- Cards needed to survive reputation pressure

Review:
- Cards that worsen reputation without improving deck function
- High-salt cards off-plan
- Bracket-pressure cards not central to strategy
- Oppressive pieces in casual-intended decks

## Replacement Categories

- More resilience
- More table-friendly alternatives
- More protection
- More lower-bracket replacements
- More clear theme support

## Report Behavior

Include:
- “This commander/card package may draw attention before the game starts.”
- “Pregame explanation recommended.”
- “Deck may need extra resilience due to reputation.”

---

# 3.49 Political Cut Review Rules

Political decks require different cut logic than generic value decks.

## Do Not Automatically Cut

Do not automatically cut:
- Low-power deterrent pieces if they protect the political plan
- Group Hug pieces if the deck has asymmetrical payoffs
- Goad cards if commander rewards opponents attacking each other
- Pillowfort cards if the win condition is slow
- Curse or bounty cards if they redirect threat effectively
- Bad gift cards if the deck has donate effects
- Rattlesnake cards if they are the deck’s primary defense
- Monarch support if the deck can defend or reclaim the crown
- Fog cards if the deck has inevitability
- Rule-setting cards if the deck breaks parity

## Higher Cut Pressure

Increase cut pressure on:
- Group Hug cards with no payoff
- Group ramp that helps opponents win first
- Chaos cards with no win condition
- Political cards that rely on opponents making obviously bad choices
- Pillowfort cards in decks with no inevitability
- Goad cards in creature-light metas
- Curses that annoy one player without scaling
- Punisher cards with harmless opponent choices
- Symmetrical effects the deck does not break
- Rattlesnake cards too weak to deter attacks
- Excessive board wipes with no closer
- Table-police cards inappropriate for intended bracket

---

# 3.50 Political Replacement Logic

Replacement suggestions should usually be category-based unless the user asks for exact cards.

## Common Replacement Categories

```yaml
political_replacement_categories:
  group_hug:
    - More asymmetrical payoff
    - More pillowfort
    - More alternate win support
    - More protection
    - More interaction

  group_slug:
    - More damage amplification
    - More lifegain buffer
    - More table drain
    - More removal
    - Faster clock

  forced_combat:
    - More repeatable goad
    - More attack payoff
    - More defensive tools
    - More removal for noncreature threats
    - More finishers

  pillowfort:
    - More inevitability
    - More alternate win conditions
    - More enchantment payoff
    - More card draw
    - More noncombat interaction

  politics:
    - More flexible removal
    - More reliable payoff
    - More card advantage
    - More protection
    - More finishers

  curses_bounties:
    - More scalable incentives
    - More enchantment recursion
    - More tablewide pressure
    - More protection
    - More removal

  donate_bad_gifts:
    - More bad gifts
    - More donate effects
    - More protection
    - More pillowfort
    - More win conditions

  rattlesnake:
    - Stronger deterrents
    - More card draw
    - More removal
    - More win conditions
    - More protection

  table_police:
    - More meta-relevant hate
    - More pressure
    - More flexible interaction
    - More card draw
    - More finishers

  secret_combo:
    - More card selection
    - More protection
    - More combo redundancy
    - More survivability
    - More bracket-appropriate alternatives
```

---

# 3.51 Report Behavior for Political Decks

When reporting on political decks, include a dedicated section:

```markdown
## Political Strategy Read

Primary political axis:
Secondary political packages:
Commander support:
Table dependency:
Salt/reputation risk:
How the deck redirects attention:
How the deck protects itself:
How the deck converts politics into a win:
Cards that support the political plan:
Cards that may accidentally help opponents:
Cards that are politically useful but low raw power:
Cards that may be cut only if lowering table politics:
```

## Required Report Notes

For any political deck, the report should answer:

1. What behavior is the deck trying to encourage or punish?
2. Does the commander support that behavior?
3. Does the deck have enough payoff?
4. Does the deck have enough protection?
5. Does the deck have a clear win condition?
6. What happens if opponents refuse to cooperate?
7. What happens if the table identifies the pilot as the threat?
8. Are any cards likely to create salt or require pregame discussion?

---

# 3.52 Political Deck Warnings

Use warnings when appropriate.

## No Payoff Warning

```markdown
Warning: This deck gives resources or changes table behavior, but it may not have enough payoff cards to convert that into a win.
```

## Kingmaker Warning

```markdown
Warning: Some cards may help opponents more than they help this deck. These are not automatic cuts, but they should be reviewed for kingmaker risk.
```

## Stall Warning

```markdown
Warning: This deck can slow or redirect the game, but it needs a clearer way to close once it stabilizes.
```

## Salt Risk Warning

```markdown
Warning: This deck uses effects that may create table frustration, especially if the game slows without ending.
```

## Table Dependency Warning

```markdown
Warning: This strategy depends heavily on opponent behavior. It may perform very differently across pods.
```

## Reputation Warning

```markdown
Warning: This commander or card package may draw early attention regardless of the deck’s actual power level.
```

---

# 3.53 Political Scoring Model

Use additive scoring, then apply gates and suppression.

## Suggested Score Inputs

```yaml
score_inputs:
  commander_support:
    none: 0
    light: 1
    moderate: 2
    strong: 4

  density:
    each_relevant_card: 1
    repeatable_engine: 2
    commander_engine: 3
    payoff_card: 2
    protection_piece: 1
    clear_win_condition: 3

  risks:
    no_payoff: -4
    no_win_condition: -5
    helps_opponents_more: -3
    relies_on_bad_opponent_choices: -2
    creature_light_meta_dependency: -2
    high_salt_without_closer: -3
```

## Confidence Bands

```yaml
confidence:
  high:
    - passes_primary_gate
    - strong commander support
    - high density
    - payoff present
    - win condition present

  medium:
    - partial gate success
    - moderate commander support
    - medium density
    - payoff present but win path unclear

  low:
    - isolated cards
    - low density
    - weak commander support
    - no clear payoff
    - high table dependency
```

---

# 3.54 Final Section 3 Summary Rule

Strategic and board-politics decks should be judged by this formula:

```text
political_plan = incentive + deterrence/protection + payoff + inevitability
```

A political card should be protected from cuts when it meaningfully contributes to that formula.

A political card should be reviewed as a possible cut when it:
- Helps opponents more than the pilot
- Does not change behavior meaningfully
- Creates salt without progress
- Requires opponents to make bad choices
- Does not support the deck’s actual win condition
- Is only funny but not functional, unless the user values theme over optimization

The helper should distinguish:

```yaml
political_card_types:
  functional_political_piece:
  table_dependent_piece:
  salt_risk_piece:
  kingmaker_risk_piece:
  low_power_but_plan_correct:
  funny_but_low_function:
  bracket_pressure_piece:
  pregame_discussion_piece:
```

A strong political deck does not simply ask opponents to behave favorably.

It builds a board state where favorable opponent behavior becomes the easiest, safest, or most rewarding choice.
