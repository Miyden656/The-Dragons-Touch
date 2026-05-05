# Section 2: Mechanical Themes & Micro-Archetypes

Version: v0.5.6-ready  
Purpose: Help the MTG Commander Deck Helper identify specific deck mechanics, synergy packages, protected cards, off-plan cards, cut-review candidates, and replacement categories.

Mechanical themes and micro-archetypes are more specific than macro-archetypes. They describe what the deck actually does.

Examples:
- Aristocrats
- Voltron
- Spellslinger
- Blink
- Landfall
- Reanimator
- Artifacts
- Enchantress
- Tokens
- +1/+1 Counters
- Lifegain
- Treasure
- Exile Matters
- Saboteur
- Storm
- Proliferate
- Mill
- Equipment
- Auras
- Hatebears
- Clues
- Food
- Madness
- Extra Combat
- X-Spells
- Untap
- Vehicles
- Legends Matter
- Copy/Clones
- Theft
- Monarch
- Energy
- Alternate Win Conditions

A deck helper should rely heavily on micro-archetypes for strategy-aware cuts because micro-archetypes usually determine whether a card is “wrong” or “secretly important.”

---

## 2.1 Micro-Archetype Philosophy

Micro-archetypes should answer:

> What mechanical plan does this deck actually use to generate advantage and win?

A deck may have:
- One primary micro-archetype
- One or more secondary micro-archetypes
- Minor packages
- Support packages
- Manual-review packages

The helper should separate these clearly instead of flattening every theme into one label.

---

## 2.2 Micro-Archetype Detection Output

For each detected micro-archetype:

```yaml
micro_archetype:
  name:
  role: primary | secondary | minor_package | support_package | manual_review
  confidence: low | medium | high
  commander_support: none | light | moderate | strong
  density: low | medium | high
  key_enablers:
  key_payoffs:
  protected_cards:
  possible_off_plan_cards:
  replacement_categories:
```

---

## 2.3 Primary vs Secondary vs Minor Package

### Primary

The main plan of the deck. The commander and decklist both support it.

### Secondary

A meaningful backup or parallel plan. It has real card density but is not the main plan.

### Minor Package

A small cluster of synergy cards. It may support the main plan but should not define the deck.

### Support Package

Cards that help the deck function but are not a win condition.

### Manual Review

The deck has hints of the theme, but not enough information to confidently score it.

---

## 2.4 Density Rule

A theme should not become primary from one or two cards unless the commander itself strongly creates that theme.

Use approximate density categories:

```yaml
density:
  low: 1-3 supporting cards
  medium: 4-8 supporting cards
  high: 9+ supporting cards
```

Commander-created themes may be treated as medium density even with fewer support cards if the commander repeatedly creates the relevant game object or trigger.

---

## 2.5 Primary Archetype Gate

Before assigning a primary micro-archetype, confirm:

```yaml
primary_gate:
  commander_support: moderate_or_strong
  deck_density: medium_or_high
  payoff_present: true
  enabler_present: true
  win_path_present: true
```

If these are not met, classify the archetype as secondary, minor package, or manual review.

---

## 2.6 Aristocrats

### Definition

Aristocrats decks sacrifice creatures or other permanents for value, triggering death payoffs, drain effects, token production, recursion, or card draw.

### Detection Signals

- Sacrifice outlets
- Death triggers
- Blood Artist-style drain
- Token fodder
- Recursion
- Creature death payoff
- Dies triggers
- Grave Pact-style control
- Treasure or artifact sacrifice if supported

### Required Components

A strong Aristocrats deck usually needs:
- Fodder
- Sacrifice outlets
- Payoffs
- Recursion or repeatable token production

### Cut Logic

Protect:
- Free/repeatable sacrifice outlets
- Death-trigger payoffs
- Token makers
- Recursion
- Low-power enablers that keep the engine running

Review:
- Creatures that do not provide fodder, payoff, or recursion
- Expensive sacrifice payoffs with no immediate impact
- One-shot sacrifice effects
- Combat-only creatures in a drain-focused build

### Replacement Categories

- More sacrifice outlets
- More token production
- More recursion
- More death payoffs
- More card draw

---

## 2.7 Voltron

### Definition

Voltron decks build one major threat, usually the commander, with Auras, Equipment, counters, protection, or combat buffs.

### Detection Signals

- Equipment
- Auras
- Commander damage support
- Double strike
- Evasion
- Hexproof/indestructible/protection
- Power buffs
- Combat protection
- Low creature count but high buff density

### Cut Logic

Protect:
- Protection spells
- Evasion
- Efficient buffs
- Commander-focused draw
- Double strike or lethal damage enablers

Review:
- Go-wide payoffs
- Expensive non-commander threats
- Board wipes that reset your own commander too often
- Buffs that do not grant evasion or protection

### Replacement Categories

- More protection
- More evasion
- More card draw
- More efficient Equipment/Auras
- Lower curve

---

## 2.8 Spellslinger

### Definition

Spellslinger decks cast instants and sorceries to trigger draw, damage, token creation, spell copying, storm, or magecraft-style payoffs.

### Detection Signals

- High instant/sorcery count
- Cantrips
- Rituals
- Cost reducers
- Spell-copy effects
- Magecraft/prowess
- Noncreature spell triggers
- Graveyard spell recursion

### Cut Logic

Protect:
- Cheap cantrips
- Cost reducers
- Spell payoffs
- Spell recursion
- Copy effects
- Interaction that triggers the commander

Review:
- Creature-heavy cards that do not support spell plan
- Expensive sorceries without strong payoff
- Combat-only creatures
- Off-plan permanents

### Replacement Categories

- More cheap spells
- More card selection
- More cost reduction
- More spell payoff
- More interaction
- More recursion

---

## 2.9 Blink / Flicker

### Definition

Blink decks exile and return permanents to reuse ETB effects.

### Detection Signals

- ETB creatures
- Blink spells
- Repeatable blink engines
- Panharmonicon-style effects
- Bounce/recast loops
- Value creatures
- Commander flicker ability

### Cut Logic

Protect:
- Strong ETB creatures
- Repeatable blink pieces
- ETB payoff doublers
- Creatures that provide ramp, draw, removal, or tokens on ETB

Review:
- Creatures with no ETB effect
- Auras or Equipment that fall off during blink
- Expensive creatures with weak ETB effects
- Cards that only care about attacking if deck is not combat-focused

### Replacement Categories

- More ETB effects
- More blink engines
- More protection
- More card draw
- More removal stapled to permanents

---

## 2.10 Landfall / Lands Matter

### Definition

Landfall decks reward lands entering the battlefield. Lands Matter includes extra land drops, land recursion, land sacrifice, utility lands, and land animation.

### Detection Signals

- Landfall triggers
- Extra land drops
- Fetch lands
- Land recursion
- Ramp spells that put lands onto battlefield
- Land sacrifice
- Land animation
- Utility land payoff
- Commander creates value from lands entering

### Commander-Created Landfall Rule

If the commander creates tokens, damage, mana, or other resources from lands entering, preserve Landfall as a relevant strategy even if overall landfall density is low.

This is especially important for partner commanders or commanders like Toggo, Goblin Weaponsmith.

### Cut Logic

Protect:
- Extra land drops
- Landfall payoffs
- Ramp that puts lands onto battlefield
- Fetch effects
- Land recursion
- Commander landfall enablers

Review:
- Mana rocks that are weaker than land ramp in landfall shells
- Expensive payoffs unrelated to lands
- Low-synergy combat creatures
- Landfall cards without enough land support

### Replacement Categories

- More land ramp
- More extra land drops
- More land recursion
- More payoff density
- More lands
- More token/artifact payoff if commander creates artifact tokens

---

## 2.11 Superfriends / Planeswalkers

### Definition

Superfriends decks use many planeswalkers and protect them through board wipes, pillowfort, proliferate, and defensive tools.

### Detection Signals

- High planeswalker count
- Proliferate
- Doubling loyalty
- Pillowfort
- Board wipes
- Token blockers
- Commander supports planeswalkers

### Cut Logic

Protect:
- Board wipes
- Proliferate
- Planeswalker protection
- Pillowfort
- Token makers
- Strong planeswalkers

Review:
- Creatures that do not defend walkers
- Combat cards with no walker synergy
- Low-impact planeswalkers
- Unsupported proliferate cards

### Replacement Categories

- More board wipes
- More pillowfort
- More proliferate
- More token blockers
- More card draw

---

## 2.12 Reanimator

### Definition

Reanimator decks put large or valuable creatures into the graveyard and return them to the battlefield for less mana.

### Detection Signals

- Reanimation spells
- Discard outlets
- Self-mill
- Large creatures
- Entomb effects
- Graveyard tutors
- Mass reanimation
- Commander recursion

### Cut Logic

Protect:
- Reanimation spells
- Graveyard setup
- Discard outlets
- High-impact reanimation targets
- Self-mill if controlled

Review:
- Big creatures that are not worth reanimating
- Expensive creatures with no ETB/protection
- Fair-value creatures that dilute the graveyard plan
- Graveyard cards without enough recursion

### Replacement Categories

- More discard outlets
- More self-mill
- More reanimation
- Better reanimation targets
- More protection from graveyard hate

---

## 2.13 Graveyard Matters

### Definition

Graveyard Matters decks use the graveyard as a resource through self-mill, recursion, flashback, escape, dredge, threshold, or death triggers.

### Detection Signals

- Self-mill
- Recursion
- Flashback/escape
- Graveyard size payoffs
- Recast from graveyard
- Death triggers
- Delirium/threshold
- Commander plays from graveyard

### Cut Logic

Protect:
- Repeatable self-mill
- Recursion engines
- Graveyard payoff cards
- Cards castable from graveyard
- Sacrifice outlets if death-based

Review:
- Graveyard payoffs without enablers
- One-shot mill with no payoff
- Cards vulnerable to graveyard hate but not central
- High-MV cards without recursion value

### Replacement Categories

- More recursion
- More self-mill
- More graveyard payoff
- More protection
- More sacrifice outlets

---

## 2.14 Artifact Synergy

### Definition

Artifact decks use artifacts as ramp, bodies, combo pieces, sacrifice fodder, cost reducers, or value engines.

### Detection Signals

- High artifact count
- Artifact tokens
- Artifact sacrifice
- Cost reduction
- Artifact recursion
- Affinity/improvise
- Artifact creature payoffs
- Commander rewards artifacts

### Cut Logic

Protect:
- Artifact ramp
- Artifact token makers
- Artifact payoffs
- Artifact recursion
- Cost reducers
- Sacrifice outlets for artifacts

Review:
- Nonartifact cards that do not support artifact plan
- Expensive artifacts with low impact
- Artifact payoffs with low artifact density
- Generic goodstuff cards

### Replacement Categories

- More artifact payoff
- More artifact ramp
- More token artifacts
- More artifact recursion
- More sacrifice outlets

---

## 2.15 Enchantress

### Definition

Enchantress decks cast enchantments to draw cards, make tokens, tax opponents, grow creatures, or build pillowfort.

### Detection Signals

- High enchantment count
- Draw on enchantment cast
- Constellation
- Aura support
- Pillowfort enchantments
- Enchantment recursion
- Commander rewards enchantments

### Cut Logic

Protect:
- Enchantress draw engines
- Low-cost enchantments
- Constellation payoffs
- Enchantment recursion
- Protective enchantments

Review:
- Non-enchantment cards with no synergy
- Expensive enchantments with little payoff
- Aura cards in non-Voltron enchantress decks
- Creatures that do not support enchantments

### Replacement Categories

- More enchantment draw
- More low-cost enchantments
- More protection
- More enchantment recursion
- More finishers

---

## 2.16 Tokens

### Definition

Token decks create many creature or artifact tokens, then use anthems, sacrifice outlets, convoke, populate, or mass pump to win.

### Detection Signals

- Token makers
- Anthems
- Populate
- Convoke
- Sacrifice fodder
- Go-wide payoff
- Token doublers
- Impact Tremors-style effects
- Commander makes tokens

### Cut Logic

Protect:
- Repeatable token makers
- Token doublers
- Anthems
- Sacrifice outlets if aristocrats-adjacent
- Mass pump finishers

Review:
- Single large creatures that do not support tokens
- Token payoffs with too few token makers
- Expensive token spells that are inefficient
- Off-plan value cards

### Replacement Categories

- More token makers
- More anthem effects
- More sacrifice payoffs
- More board protection
- More finishers

---

## 2.17 +1/+1 Counters

### Definition

+1/+1 Counter decks place, multiply, move, or exploit counters on creatures.

### Detection Signals

- +1/+1 counter placement
- Counter doublers
- Modified payoffs
- Proliferate
- Creatures entering with counters
- Commander distributes counters
- Combat payoff for counters

### Cut Logic

Protect:
- Counter enablers
- Counter payoff cards
- Proliferate
- Creatures that scale with counters
- Counter-based protection or evasion

Review:
- Creatures that do not interact with counters
- Expensive counter payoffs with no board impact
- Isolated proliferate cards
- Non-synergy combat tricks

### Replacement Categories

- More counter enablers
- More counter payoff
- More evasion
- More protection
- More proliferate

---

## 2.18 Lifegain

### Definition

Lifegain decks repeatedly gain life and convert that life into damage, counters, tokens, card draw, or alternate wins.

### Detection Signals

- Repeatable lifegain
- Life payoff
- Lifelink
- Life-to-damage conversion
- Life-to-counters conversion
- Life total alternate wins
- Commander rewards life gain

### Cut Logic

Protect:
- Repeatable lifegain sources
- Payoffs that convert life into progress
- Lifegain-drain bridges
- Life-based card draw
- Counter payoffs if lifegain counters shell

Review:
- Lifegain cards with no payoff
- One-shot life gain
- High-MV cards that only gain life
- Payoffs without enough lifegain triggers

### Replacement Categories

- More repeatable lifegain
- More payoff density
- More draw
- More lifedrain
- More protection

---

## 2.19 Lifedrain

### Definition

Lifedrain decks cause opponents to lose life while you gain life, creating table-wide life swings.

### Detection Signals

- Opponent life loss
- Drain triggers
- Extort-style effects
- Blood Artist effects
- Lifegain-to-damage conversion
- Commander drains opponents

### Cut Logic

Protect:
- Repeatable drain effects
- Aristocrats drain payoffs
- Lifegain-drain converters
- Token/death enablers if needed

Review:
- Lifegain-only cards
- Combat-only cards with no drain
- Expensive drain effects with low output
- Isolated payoffs

### Replacement Categories

- More drain payoff
- More repeatable triggers
- More token/sacrifice support
- More card draw
- More protection

---

## 2.20 Treasure

### Definition

Treasure decks create artifact tokens that sacrifice for mana and may also support artifact count, sacrifice, storm, or combo.

### Detection Signals

- Treasure makers
- Artifact sacrifice payoff
- Mana burst payoff
- Commander creates or rewards Treasure
- Token doubling
- Artifact token synergies
- Tutor chain support

### Cut Logic

Protect:
- Repeatable Treasure makers
- Artifact sacrifice payoffs
- Mana-sink payoffs
- Treasure payoff cards
- Commander support

Review:
- Treasure payoffs without Treasure density
- Expensive cards that do not convert mana into wins
- Generic artifacts not supporting Treasure plan
- High-bracket tutor chains if table intent is lower power

### Replacement Categories

- More Treasure generation
- More artifact payoff
- More card draw
- More mana sinks
- More sacrifice payoff

---

## 2.21 Exile Matters / Cast From Exile

### Definition

Exile Matters decks generate value when cards are exiled or cast from exile.

### Detection Signals

- Impulse draw
- Cast from exile triggers
- Foretell
- Suspend
- Adventure
- Plot
- Discover/cascade support
- Commander rewards exile

### Cut Logic

Protect:
- Repeatable impulse draw
- Cast-from-exile payoff
- Exile-trigger token makers
- Treasure support in Prosper-style decks

Review:
- Cards that exile but cannot be cast reliably
- Payoffs without enablers
- Generic draw that does not support exile plan
- Overcosted exile effects

### Replacement Categories

- More impulse draw
- More cast-from-exile payoff
- More Treasure/ramp
- More card selection
- More protection

---

## 2.22 Saboteur / Combat Damage Triggers

### Definition

Saboteur decks reward creatures dealing combat damage to players.

### Detection Signals

- Combat damage triggers
- Evasion
- Unblockable
- Menace/flying/shadow
- Ninjutsu
- Double strike
- Extra combats
- Commander rewards connecting

### Cut Logic

Protect:
- Cheap evasive creatures
- Combat damage payoff
- Evasion granters
- Topdeck manipulation if relevant
- Protection for attackers

Review:
- Ground creatures with no evasion
- Expensive attackers with no immediate payoff
- Defensive cards that do not help connect
- Combat tricks with low synergy

### Replacement Categories

- More evasive creatures
- More protection
- More card selection
- More extra combat
- More commander-trigger support

---

## 2.23 Storm

### Definition

Storm decks cast many spells in one turn, often with rituals, cost reducers, cantrips, wheels, and recursion.

### Detection Signals

- Rituals
- Cantrips
- Cost reducers
- Spell recursion
- Storm cards
- Magecraft/prowess
- Draw engines
- Artifact untap/mana engines

### Cut Logic

Protect:
- Cheap spells
- Rituals
- Cost reducers
- Draw engines
- Storm payoffs
- Recursion

Review:
- Expensive spells that do not continue the chain
- Creatures with no spell synergy
- Slow value cards
- High-MV win conditions without setup

### Replacement Categories

- More cheap spells
- More rituals
- More cost reduction
- More draw
- More storm payoff

---

## 2.24 Proliferate

### Definition

Proliferate decks add counters to permanents or players, supporting +1/+1 counters, planeswalkers, poison, charge counters, and sagas.

### Detection Signals

- Proliferate
- Counters on creatures
- Planeswalkers
- Poison
- Charge counters
- Sagas
- Commander rewards counters

### Cut Logic

Protect:
- Repeatable proliferate
- Counter payoff
- Planeswalker support
- Poison enablers if poison deck
- Sagas if saga deck

Review:
- Proliferate without counters
- Counter cards without payoff
- Slow proliferate pieces
- Unsupported poison cards

### Replacement Categories

- More counter sources
- More proliferate
- More payoff cards
- More protection
- More draw

---

## 2.25 Mill

### Definition

Mill decks put cards from opponents’ libraries into their graveyards.

### Detection Signals

- Opponent mill
- Mill doublers
- Graveyard theft
- Horror/Rogue mill support
- Commander mills
- Reanimation from opponents’ graveyards

### Cut Logic

Protect:
- Repeatable mill engines
- Mill payoff
- Graveyard theft
- Graveyard exile if needed
- Defensive tools

Review:
- Small one-shot mill
- Self-mill cards unless graveyard hybrid
- Creatures with no mill support
- Mill cards without payoff or scale

### Replacement Categories

- More repeatable mill
- More payoff
- More protection
- More graveyard theft
- More board control

---

## 2.26 Equipment

### Definition

Equipment decks use Equipment to enhance creatures, often through Voltron or go-wide equipped combat.

### Detection Signals

- Equipment count
- Equip cost reduction
- Auto-equip
- Equipped creature payoff
- Commander rewards Equipment
- Double strike/evasion

### Cut Logic

Protect:
- Efficient Equipment
- Equip cost reducers
- Equipment draw engines
- Protection Equipment
- Evasion Equipment

Review:
- Equipment with high equip cost and low impact
- Creatures that do not carry Equipment well
- Go-wide cards if deck is Voltron
- Voltron-only cards if deck is go-wide Equipment

### Replacement Categories

- More efficient Equipment
- More protection
- More evasion
- More card draw
- More equip cost reduction

---

## 2.27 Auras

### Definition

Aura decks use Auras to enhance creatures, protect commanders, trigger enchantress effects, or build Voltron pressure.

### Detection Signals

- Aura count
- Enchantress draw
- Aura tutors
- Commander rewards Auras
- Protection Auras
- Evasion Auras
- Voltron damage

### Cut Logic

Protect:
- Aura tutors
- Efficient protection/evasion Auras
- Enchantress draw
- Commander-damage Auras

Review:
- Auras that do not protect or advance lethal damage
- High-cost Auras
- Creatures that are poor Aura carriers
- Non-enchantment cards in enchantress-heavy shells

### Replacement Categories

- More protection Auras
- More evasion
- More enchantress draw
- More recursion
- Lower curve

---

## 2.28 Go-Wide Combat

### Definition

Go-Wide decks build many creatures and win through mass combat damage, anthems, Overrun effects, or extra combats.

### Detection Signals

- Token makers
- Anthems
- Mass pump
- Extra combat
- Wide board payoff
- Commander makes attackers

### Cut Logic

Protect:
- Repeatable token makers
- Anthems
- Mass pump finishers
- Board protection
- Attack-trigger payoffs

Review:
- Single-target buffs
- Expensive lone threats
- Noncombat value cards
- Payoffs that require tall boards instead of wide boards

### Replacement Categories

- More token makers
- More anthems
- More board protection
- More finishers
- More haste

---

## 2.29 Go-Tall Combat

### Definition

Go-Tall decks focus on making one or a few creatures enormous.

### Detection Signals

- Power buffs
- Counters
- Auras/Equipment
- Trample
- Double strike
- Fling effects
- Commander damage

### Cut Logic

Protect:
- Evasion
- Trample
- Protection
- Power scaling
- Double strike
- Commander support

Review:
- Go-wide payoffs
- Small token makers without payoff
- Defensive cards that do not protect tall threat
- Expensive unrelated creatures

### Replacement Categories

- More evasion
- More protection
- More power scaling
- More card draw
- More trample/double strike

---

## 2.30 Hatebears

### Definition

Hatebear decks use small creatures that disrupt opponents while applying pressure or supporting a value plan.

### Detection Signals

- Small tax creatures
- Graveyard hate creatures
- Tutor hate
- Artifact/enchantment hate
- Nonbasic land hate
- Rule-setting creatures
- Commander supports creatures or hate pieces

### Cut Logic

Protect:
- Hatebears that do not hurt the deck
- Low-cost disruptive creatures
- Recursion for hate pieces
- Protection

Review:
- Hatebears that shut off your own plan
- Narrow meta calls
- High-salt cards if casual bracket
- Low-impact bodies without relevant disruption

### Replacement Categories

- More relevant hate
- More protection
- More card draw
- More recursion
- More win conditions

---

## 2.31 Clues / Investigate

### Definition

Clue decks create artifact tokens that can be sacrificed to draw cards.

### Detection Signals

- Investigate
- Clue token creation
- Artifact token payoff
- Sacrifice payoff
- Commander rewards Clues/artifacts
- Token doubling

### Cut Logic

Protect:
- Repeatable Clue makers
- Artifact payoff
- Sacrifice payoff
- Token payoff
- Card draw engines

Review:
- Artifact payoffs with low artifact density
- One-shot investigate cards
- Expensive draw-only effects
- Cards that ignore token/artifact plan

### Replacement Categories

- More Clue generation
- More artifact payoff
- More sacrifice payoff
- More token payoff
- More mana/ramp

---

## 2.32 Food

### Definition

Food decks create Food artifact tokens for lifegain, sacrifice value, artifact count, or creature generation.

### Detection Signals

- Food creation
- Food sacrifice payoff
- Lifegain payoff
- Artifact payoff
- Commander rewards Food
- Token doubling

### Cut Logic

Protect:
- Repeatable Food makers
- Food payoff
- Artifact sacrifice payoff
- Lifegain payoff if supported
- Token doublers

Review:
- Lifegain-only cards without Food synergy
- Food cards with no payoff
- Expensive artifact cards unrelated to Food
- Low-output token makers

### Replacement Categories

- More Food generation
- More artifact sacrifice payoff
- More lifegain payoff
- More card draw
- More finishers

---

## 2.33 Blood Tokens / Madness / Discard Value

### Definition

Blood and Madness decks use discard as a resource through rummage, madness casting, graveyard setup, or artifact-token value.

### Detection Signals

- Blood token creation
- Discard outlets
- Madness cards
- Reanimation
- Graveyard payoff
- Artifact token payoff
- Commander rewards discard

### Cut Logic

Protect:
- Repeatable discard outlets
- Madness payoff
- Graveyard recursion
- Blood token engines
- Artifact sacrifice payoff

Review:
- Cards that discard without payoff
- Madness cards without discard outlets
- Blood cards without artifact or discard payoff
- High-MV cards that clog the hand

### Replacement Categories

- More discard outlets
- More madness payoff
- More recursion
- More artifact payoff
- More card draw

---

## 2.34 Extra Combat

### Definition

Extra Combat decks generate additional combat phases to multiply attack triggers, combat damage, or commander damage.

### Detection Signals

- Extra combat spells
- Attack triggers
- Mana generated through combat
- Untap attackers
- Double strike
- Commander rewards attacking

### Cut Logic

Protect:
- Extra combat effects
- Attack-trigger payoffs
- Combat mana engines
- Haste
- Protection

Review:
- Combat cards that do not scale with multiple combats
- Defensive cards
- Slow value cards
- Expensive creatures without attack triggers

### Replacement Categories

- More haste
- More attack triggers
- More protection
- More extra combat
- More mana generation

---

## 2.35 X-Spells / Big Spells

### Definition

X-Spells and Big Spells decks generate large mana and convert it into scalable spells or copied haymakers.

### Detection Signals

- X-spells
- Mana doublers
- Cost reducers
- Spell copy
- Big mana ramp
- Commander rewards X-spells
- Mana sink payoff

### Cut Logic

Protect:
- Big mana enablers
- X-spell payoffs
- Spell copy
- Cost reduction
- Mana sinks

Review:
- Low-impact small spells
- Big spells without ramp support
- Ramp without payoff
- Expensive cards that do not scale

### Replacement Categories

- More ramp
- More X-spells
- More card draw
- More spell copy
- More protection

---

## 2.36 Untap / Tap Matters

### Definition

Untap decks use permanents that tap for mana or value and untap them repeatedly.

### Detection Signals

- Untap target land
- Untap target permanent
- Untap target artifact
- Mana dorks
- Tap abilities
- Land untappers
- Artifact untappers
- Commander activated abilities
- Mana doublers

### Cut Logic

Protect:
- Untap-ramp
- Mana dorks
- Utility permanents with tap abilities
- Mana doublers
- Activated ability payoffs

Review:
- Untap effects without valuable targets
- Tap creatures with no payoff
- Mana engines without mana sinks
- Isolated combo pieces

### Replacement Categories

- More mana sinks
- More tap-value permanents
- More untappers
- More protection
- More card draw

---

## 2.37 Vehicles

### Definition

Vehicle decks use creatures to crew artifact Vehicles and generate combat or artifact synergy.

### Detection Signals

- Vehicles
- Crew support
- Pilot tokens
- Artifact synergy
- Commander supports Vehicles
- Tap/untap vehicle support

### Cut Logic

Protect:
- Efficient Vehicles
- Crew enablers
- Pilot/token makers
- Artifact payoffs
- Commander vehicle support

Review:
- Vehicles with poor rate
- Creatures that do not crew well
- Artifact payoffs with low artifact density
- Noncombat cards that do not support plan

### Replacement Categories

- More crew support
- More Vehicles
- More artifact payoff
- More token pilots
- More card draw

---

## 2.38 Legends Matter / Historic

### Definition

Legends Matter decks reward legendary permanents. Historic decks reward artifacts, legendaries, and Sagas.

### Detection Signals

- High legendary count
- Historic triggers
- Legendary tutors
- Commander rewards legends
- Legendary cost reduction
- Sagas/artifacts if historic

### Cut Logic

Protect:
- Legendary synergy pieces
- Historic draw engines
- Legendary tutors
- Cards that support commander trigger

Review:
- Nonlegendary cards with no support role
- Legendary cards included only for type line
- Historic payoffs with low density
- Expensive legends with low impact

### Replacement Categories

- More legendary synergy
- More historic enablers
- More card draw
- More removal on-theme
- More mana fixing

---

## 2.39 Copy / Clones

### Definition

Copy decks copy creatures, artifacts, spells, tokens, or triggered abilities.

### Detection Signals

- Clone effects
- Token copies
- Spell copy
- Trigger copying
- Commander copy ability
- High-value ETB targets

### Cut Logic

Protect:
- High-value copy targets
- Copy engines
- ETB creatures
- Token doublers
- Commander copy support

Review:
- Clone effects without good targets
- Expensive copy cards
- Non-synergy creatures
- Copy spells that do not advance win condition

### Replacement Categories

- More copy targets
- More protection
- More ETB payoff
- More token support
- More card draw

---

## 2.40 Theft

### Definition

Theft decks use opponents’ cards against them by stealing creatures, casting from libraries, or reanimating opposing graveyards.

### Detection Signals

- Steal creatures
- Cast opponents’ spells
- Graveyard theft
- Exile theft
- Act of Treason effects
- Commander rewards theft

### Cut Logic

Protect:
- Repeatable theft
- Theft payoff
- Sacrifice outlets if temporary theft
- Mana fixing for stolen spells
- Graveyard theft payoffs

Review:
- One-shot theft with no sacrifice outlet
- Theft cards with no payoff
- Expensive unreliable theft
- Cards that need opponents to have specific resources

### Replacement Categories

- More sacrifice outlets
- More repeatable theft
- More mana fixing
- More protection
- More payoff

---

## 2.41 Alternate Win Conditions

### Definition

Alternate Win Condition decks use cards that say a player wins the game if a condition is met.

### Detection Signals

- Approach-style effects
- Laboratory Maniac effects
- Treasure-count wins
- Life-total wins
- Maze’s End
- Mechanized Production
- Commander tutors for alt-win pieces

### Classification Rule

Separate:
- Slow alternate win condition
- Supported alternate win plan
- Compact combo win
- True turbo combo

Do not treat slow alternate wins as turbo combo by default.

### Cut Logic

Protect:
- Alt-win pieces if deck is built around them
- Tutors if appropriate to bracket
- Protection
- Enablers that satisfy the condition

Review:
- Unsupported alt-win cards
- Slow alt-wins with no protection
- Bracket-pressure alt-wins if table intent is lower
- Cards that do not support main plan outside alt-win

### Replacement Categories

- More protection
- More tutors/card selection
- More enablers
- More control
- More redundancy

---

## 2.42 Bracket-Pressure / High-Power Value

### Definition

Bracket-pressure cards are not an archetype by themselves. They are cards or packages that may push a deck above its intended power bracket.

### Important Rule

Bracket pressure is not the same as a cut.

A bracket-pressure card may be:
- Powerful and correct for the deck
- Correct only at a higher bracket
- Wrong for the intended table
- Core but requiring pregame discussion
- A possible cut only if the user wants a lower bracket

### Detection Signals

- Fast mana
- Efficient tutors
- Free interaction
- Compact combos
- True turbo combo enablers
- Mass land denial
- High-power value engines
- Deterministic tutor chains
- Combo protection

### Cut Logic

Never automatically cut a bracket-pressure card.

Instead label:
- Core but bracket-pushing
- Correct at higher bracket
- Pregame discussion recommended
- Possible cut if lowering power
- Manual review

### Replacement Categories

- Lower-bracket alternative
- Slower tutor
- Fairer draw engine
- More thematic replacement
- Less efficient but more casual card

---

# Global Micro-Archetype Scoring and Suppression Rules

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

## B. Minor Package Protection

Minor package cards should not automatically become cut candidates.

A minor package may be valid if it:
- Supports the commander
- Supports the primary strategy
- Provides needed role coverage
- Bridges two themes
- Enables a backup win condition
- Provides bracket-appropriate flexibility

Label these as:
- Minor package support
- Context-dependent
- Playtest-first review
- Protected if commander-supported

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
