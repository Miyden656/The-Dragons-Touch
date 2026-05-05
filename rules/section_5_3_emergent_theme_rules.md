# Section 5.3: Emergent Theme Rules
Version: v0.5.6-ready
Purpose: Help the MTG Commander Deck Helper recognize modern hybrid packages, commander-defined plans, cross-mechanic engines, bracket-pressure signals, special deckbuilding exceptions, and context-dependent card roles.

Emergent themes are not always traditional archetypes.

An emergent theme may be:
- A newer mechanic package
- A commander-defined strategy
- A hybrid of two older themes
- A power-level signal
- A bracket-pressure package
- A deckbuilding exception
- A modern Commander trend
- A context correction that prevents bad cut recommendations

The goal is not just to say:

```text
This is a token deck.
```

The goal is to say:

```text id="5ghivu"
This is a commander-created token combat deck that uses tokens as both go-wide pressure and go-tall scaling.
```

That level of context prevents the helper from cutting cards that look weak generically but are important to the actual deck plan.

---

# 5.3.1 Core Emergent Theme Philosophy

Emergent themes are the context layer of Commander analysis.

They answer questions like:

- Is this deck’s real plan created by the commander?
- Is this a hybrid of typal plus mechanic?
- Is Treasure being used as ramp, sacrifice fodder, tutor currency, artifact count, or combo fuel?
- Is this card powerful but wrong for the shell?
- Is this card weak by raw power but essential to the engine?
- Is this deck combo-primary, combo-adjacent, or just carrying a compact backup combo?
- Is bracket pressure present without requiring a cut?
- Is a broad archetype label hiding the actual strategy?
- Is the deck using a special multiple-copy exception?
- Should replacement suggestions eventually come from the user’s collection?

The most important rule:

```text id="fvvkjl"
Emergent themes are where the deck helper stops asking, “What archetype is this closest to?” and starts asking, “What is this deck actually trying to make happen?”
```

---

# 5.3.2 Emergent Theme Output Fields

For each detected emergent theme, record:

```yaml id="emergent_output_fields"
emergent_theme:
  name:
  role: primary | secondary | minor_package | support_package | manual_review | report_modifier
  confidence: low | medium | high
  commander_defined: true | false
  commander_support: none | light | moderate | strong
  package_count:
  payoff_count:
  enabler_count:
  conversion_point:
  linked_themes:
  broad_archetype_suppressed:
  strategy_shape:
  bracket_pressure: none | low | medium | high
  combo_centrality: none | possible_piece | combo_adjacent | backup_combo | combo_primary | true_turbo_combo
  special_legality_or_deckbuilding_rule: true | false
  high_synergy_low_power_cards:
  generically_good_wrong_shell_cards:
  protected_cards:
  possible_cut_candidates:
  replacement_categories:
  report_notes:
```

---

# 5.3.3 Commander-Defined Strategy Override

Commander-defined strategy should override broad fallback labels.

```python id="commander_defined_strategy_exists"
def commander_defined_strategy_exists(commander_tags):
    return bool(commander_tags.get("commander_defined_themes"))
```

```python id="suppress_broad_fallback_if_commander_defined"
def suppress_broad_fallback_if_commander_defined(primary_candidate, commander_tags):
    broad_fallbacks = {
        "Ramp-Control / Big Mana Value",
        "Generic Tokens",
        "Generic Artifacts",
        "Generic Midrange",
        "Generic Goodstuff",
        "Generic Combo-Adjacent Value",
        "Generic Control"
    }

    if primary_candidate in broad_fallbacks and commander_defined_strategy_exists(commander_tags):
        return "suppress_to_minor_package"

    return "keep_primary_candidate"
```

Do not let broad archetypes steal primary from narrower commander-defined plans.

Examples:
- Toggo partner decks should preserve Commander-Created Landfall / Artifact Token Landfall.
- Ghalta and Mavren should preserve Token Combat / Go-Wide-Go-Tall Combat.
- Prosper should preserve Exile Matters / Treasure Engine.
- Magda should preserve Treasure Tutor Chain, not generic Treasure Ramp.
- Tiamat decks may be Dragon Tutor Chain, not generic Dragon Goodstuff.

---

# 5.3.4 Emergent Package Primary Gate

Use this for commander-defined packages and modern hybrid engines.

```python id="emergent_primary_gate"
def can_be_primary_emergent_package(
    package_count,
    payoff_count,
    commander_support,
    package_is_commander_defined
):
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

If this gate fails, classify the emergent package as:
- Secondary package
- Minor package
- Support package
- Manual review

---

# 5.3.5 Emergent Suppression Rules

## Suppress Broad Fallback Labels

Suppress broad labels if a narrower emergent plan exists.

Broad labels to suppress:
- Generic Ramp
- Generic Tokens
- Generic Artifacts
- Generic Treasure
- Generic Midrange
- Generic Goodstuff
- Generic Combo
- Generic Control
- Generic Value

Prefer:
- Commander-Created Landfall
- Token Combat / Go-Wide-Go-Tall Hybrid
- Treasure Tutor Chain
- Artifact/Treasure Combo-Value
- Typal-Mechanic Hybrid
- Compact Combo but Not Full Combo
- Combo-Adjacent Value
- High-Power Value but Not Turbo Combo
- Commander Recast / Death Loop
- Partner Pair-Defined Strategy

## Do Not Suppress Commander-Defined Packages

If the commander directly creates the package or rewards the behavior, preserve the emergent theme as at least secondary even if density looks modest.

Example:
- If the commander creates artifact tokens from lands entering, land ramp and land recursion are commander support even if the deck has few printed landfall cards.

---

# 5.3.6 Bracket Pressure Is Not a Cut Recommendation

Bracket pressure should be tracked separately from cut recommendations.

```python id="bracket_pressure_review"
def bracket_pressure_review(card_tags, user_intended_bracket):
    if "game_changer" in card_tags or "high_bracket_pressure" in card_tags:
        return "pregame_discussion_or_bracket_review"

    if "bracket_pressure" in card_tags:
        return "review_for_table_fit"

    return "no_bracket_pressure_flag"
```

A bracket-pressure card may be:
- Powerful and correct for the deck
- Correct only at a higher bracket
- Wrong for the intended table
- Core but requiring pregame discussion
- A possible cut only if lowering table power

Never automatically cut a card only because it has bracket pressure.

---

# 5.3.7 Combo Centrality Detection

Separate “has combo” from “is combo.”

```python id="combo_centrality_detection"
def classify_combo_centrality(
    combo_piece_count,
    tutor_count,
    protection_count,
    commander_combo_support
):
    if commander_combo_support and combo_piece_count >= 2 and tutor_count >= 3:
        return "combo_primary"

    if combo_piece_count >= 2 and tutor_count >= 2 and protection_count >= 2:
        return "combo_primary_or_high_pressure"

    if combo_piece_count >= 2:
        return "combo_adjacent_value"

    if combo_piece_count == 1:
        return "possible_combo_piece_manual_review"

    return "no_combo_detected"
```

Use cautious language:
- “Combo-adjacent value”
- “Compact backup combo”
- “Possible combo piece”
- “Manual combo review”
- “True turbo combo”

Do not call a deck turbo combo just because it contains a compact combo or alternate win condition.

---

# 5.3.8 True Turbo Combo Gate

Use a hard gate before assigning `true_turbo_combo`.

```python id="true_turbo_combo_gate"
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

This prevents the helper from mislabeling:
- Slow alternate win conditions
- High-power value engines
- Casual compact combos
- Combo-adjacent value loops
- Visible multi-turn win conditions

as turbo combo.

---

# 5.3.9 Multiple-Copy Exception Legality

Some Commander decks legally run multiple copies of specific cards.

```python id="multiple_copy_exceptions"
MULTIPLE_COPY_EXCEPTIONS = {
    "Rat Colony",
    "Relentless Rats",
    "Nazgûl",
    "Shadowborn Apostle",
    "Persistent Petitioners",
    "Dragon's Approach",
    "Hare Apparent",
    "Seven Dwarves"
}
```

```python id="is_legal_duplicate_exception"
def is_legal_duplicate_exception(card_name):
    return card_name in MULTIPLE_COPY_EXCEPTIONS
```

Do not flag legal repeated copies as Commander singleton violations.

For multiple-copy exception decks, evaluate:
- Copy count
- Commander support
- Payoff support
- Tutor/draw consistency
- Whether the repeated card is the actual engine
- Whether the deck has enough copies to function

---

# 5.3.10 Commander-Created Landfall

## Definition

Commander-Created Landfall decks are decks where the commander directly cares about lands entering, creates tokens/artifacts from landfall, or turns land drops into the main engine.

This matters even when the 99 has only moderate landfall density.

## Detection Signals

Increase Commander-Created Landfall score for:
- Commander has landfall trigger
- Commander creates tokens from lands entering
- Commander creates artifact tokens from lands entering
- Commander rewards land drops
- Land recursion
- Extra land drops
- Fetch lands
- Bounce lands
- Land ramp
- Artifact-token payoff if commander creates artifact tokens
- Damage or combat payoff from landfall tokens

## Primary Gate

```python id="commander_created_landfall_gate"
def can_be_primary_commander_created_landfall(
    land_drop_support_count,
    land_recursion_count,
    commander_landfall_engine,
    payoff_count
):
    return (
        commander_landfall_engine
        and (land_drop_support_count + land_recursion_count) >= 6
        and payoff_count >= 1
    )
```

## Suppression Rules

Do not suppress landfall just because printed landfall density in the 99 is low if the commander is the engine.

Suppress broad labels like:
- Generic Ramp
- Generic Artifacts
- Generic Tokens

when the commander turns land drops into the deck’s main resource engine.

## Cut Logic

Protect:
- Land ramp
- Fetch effects
- Bounce lands
- Land recursion
- Extra land drops
- Artifact-token payoff if commander creates artifact tokens
- Token payoff if commander creates creature tokens
- Landfall payoff

Review:
- Mana rocks that are worse than land ramp in this shell
- Artifact payoffs if commander does not create enough artifact tokens
- Generic ramp that does not trigger commander
- Landfall cards with too little land support

## Replacement Categories

- More land ramp
- More land recursion
- More extra land drops
- More fetch effects
- More artifact-token payoff
- More token payoff
- More commander protection

## Report Behavior

Include:
- “Commander is the landfall engine”
- “Land ramp is commander support”
- “Land recursion and bounce lands may be engine pieces”
- “Do not judge only by printed landfall card count”

---

# 5.3.11 Token Combat / Go-Wide-Go-Tall Hybrid

## Definition

These decks create a wide board of tokens, then convert that board into mass combat pressure, one or more enormous attackers, mana, card draw, or power-scaling payoffs.

They are not pure token swarm and not pure Voltron.

## Detection Signals

Increase Token Combat Hybrid score for:
- Commander creates tokens
- Token makers
- Anthems
- Power-matters payoff
- Go-wide combat payoff
- Go-tall scaling
- Counters on tokens
- Tap tokens for value
- Sacrifice tokens for value
- Combat conversion cards
- Commander rewards token count or power

## Primary Gate

```python id="token_combat_hybrid_gate"
def can_be_primary_token_combat_hybrid(
    token_maker_count,
    combat_payoff_count,
    power_scaling_count,
    commander_support
):
    return (
        commander_support
        and token_maker_count >= 5
        and (combat_payoff_count + power_scaling_count) >= 3
    ) or (
        token_maker_count >= 8
        and combat_payoff_count >= 3
        and power_scaling_count >= 2
    )
```

## Suppression Rules

Do not split too aggressively into only:
- Tokens
- Combat
- Voltron
- Counters

The key read is:

```text id="6ev90y"
Tokens are the resource engine. Combat is the conversion point.
```

## Cut Logic

Protect:
- Token makers
- Anthems
- Power-scaling effects
- Go-wide finishers
- Go-tall conversion pieces
- Board protection
- Commander support cards

Review:
- Single-target buffs if deck is mostly go-wide
- Pure go-wide cards if deck needs go-tall conversion
- Token makers that do not scale with commander
- Expensive creatures that do not support token combat

## Replacement Categories

- More token makers
- More combat payoff
- More anthem effects
- More board protection
- More power-scaling payoff
- More haste
- More card draw

## Report Behavior

Include:
- “Tokens are both resource and combat material”
- “Go-wide and go-tall roles”
- “Combat conversion point”
- “Cards that are token makers but also ramp/draw/sacrifice fodder”

---

# 5.3.12 Plot / Crime / Outlaw Packages

## Definition

These decks combine plotted spells, crime triggers, and Outlaw batching.

Outlaws include:
- Assassins
- Mercenaries
- Pirates
- Rogues
- Warlocks

Crimes are committed when targeting an opponent, something they control, or a card in their graveyard.

## Detection Signals

Increase Plot/Crime/Outlaw score for:
- Crime triggers
- Cards that target opponents
- Cards that target opponent permanents
- Cards that target cards in opponent graveyards
- Targeted removal
- Targeted discard
- Theft effects
- Outlaw creature density
- Plot cards
- Commander rewards crime or Outlaws
- Interaction-as-engine patterns

## Primary Gate

```python id="crime_outlaw_gate"
def can_be_primary_crime_outlaw(
    crime_trigger_count,
    reliable_crime_enabler_count,
    outlaw_count,
    payoff_count,
    commander_support
):
    return (
        commander_support
        and (crime_trigger_count + outlaw_count) >= 6
        and reliable_crime_enabler_count >= 5
        and payoff_count >= 2
    ) or (
        crime_trigger_count >= 6
        and reliable_crime_enabler_count >= 8
        and payoff_count >= 3
    )
```

## Multi-Role Rule

Targeted interaction may count as:
- Removal
- Crime enabler
- Political pressure
- Graveyard interaction
- Commander engine fuel

## Cut Logic

Protect:
- Targeted interaction that triggers crime
- Outlaw density pieces
- Crime payoffs
- Plot cards if they support big turns
- Theft/graveyard targeting cards if commander rewards them

Review:
- Untargeted board wipes if crime triggers matter
- Outlaws with no crime/combat role
- Plot cards with no payoff
- Interaction that does not target opponents/resources if crime density is low

## Replacement Categories

- More targeted interaction
- More crime payoffs
- More Outlaw density
- More theft support
- More plot support
- More card draw

## Report Behavior

Include:
- “Interaction is part of the engine”
- “Crime enabler count”
- “Outlaw density”
- “Targeted removal may be protected from cuts”

---

# 5.3.13 Offspring

## Definition

Offspring is an optional additional cost on creature spells that creates a 1/1 token copy of the creature when it enters.

Offspring overlaps with:
- ETB value
- Token copies
- Sacrifice fodder
- Go-wide combat
- Small-creature scaling
- Token/counter strategies

## Detection Signals

Increase Offspring score for:
- Offspring cards
- ETB payoffs
- Token copy payoff
- Sacrifice outlets
- Small-creature payoff
- Token/counter scaling
- Commander rewards small creatures or token copies
- Panharmonicon-style effects if ETB matters

## Primary Gate

```python id="offspring_gate"
def can_be_primary_offspring(
    offspring_count,
    etb_or_token_payoff_count,
    commander_support
):
    return (
        commander_support
        and offspring_count >= 5
        and etb_or_token_payoff_count >= 2
    ) or (
        offspring_count >= 8
        and etb_or_token_payoff_count >= 3
    )
```

## Multi-Role Rule

Offspring cards may count as:
- Creature density
- Token maker
- ETB multiplier
- Sacrifice fodder
- Small-creature support
- Token-copy support

## Cut Logic

Protect:
- Offspring cards with strong ETB effects
- Token payoffs
- Sacrifice outlets
- ETB doublers
- Small-creature scaling
- Commander synergy pieces

Review:
- Offspring cards where the 1/1 copy has low value
- ETB payoff with too few ETB creatures
- Token payoff with low token density
- Expensive offspring costs that the deck cannot support

## Replacement Categories

- More Offspring cards
- More ETB payoff
- More token payoff
- More sacrifice outlets
- More small-creature support
- More ramp

## Report Behavior

Include:
- “Offspring cards count as creature, token maker, and ETB multiplier”
- “Can the deck pay offspring costs?”
- “Does the 1/1 copy matter?”

---

# 5.3.14 Gift

## Definition

Gift lets the player promise an opponent a resource as a spell is cast. If the gift is promised, the caster gets an additional or upgraded effect.

Gift sits between:
- Group Hug
- Political value
- Spell efficiency
- Table leverage

## Detection Signals

Increase Gift score for:
- Gift cards
- Opponent resource gifts
- Political spell payoffs
- Asymmetrical bonus
- Group hug adjacent effects
- Commander rewards giving resources
- Counter/token payoff from gifting
- Table leverage

## Primary Gate

```python id="gift_gate"
def can_be_primary_gift(
    gift_count,
    asymmetrical_payoff_count,
    commander_support
):
    return (
        commander_support
        and gift_count >= 5
        and asymmetrical_payoff_count >= 2
    ) or (
        gift_count >= 8
        and asymmetrical_payoff_count >= 3
    )
```

## Asymmetry Rule

Evaluate every Gift card by asking:

```text id="r10dsc"
Is the upgraded effect worth giving an opponent a resource?
```

If no, increase cut pressure.

## Cut Logic

Protect:
- Gift cards with strong asymmetrical payoff
- Political support pieces
- Cards where gift helps the pilot more than recipient
- Group Hug payoff if linked

Review:
- Gift cards where opponent benefit is too high
- Gift cards with low upgraded payoff
- Cards that help the leading player
- Political cards without payoff

## Replacement Categories

- More asymmetrical payoff
- More political support
- More protection
- More card draw
- More lower-risk value cards
- More table-friendly interaction

## Report Behavior

Include:
- “Gift is political value, not free value”
- “Asymmetry check”
- “Risk of helping the wrong opponent”

---

# 5.3.15 Forage

## Definition

Forage lets a player pay costs by exiling cards from graveyard or sacrificing Food.

Forage connects:
- Food
- Graveyard resources
- Sacrifice
- Resource conversion
- Aristocrats
- Squirrel/Food shells

## Detection Signals

Increase Forage score for:
- Forage cards
- Food generation
- Graveyard fuel
- Self-mill
- Sacrifice payoff
- Food payoff
- Graveyard payoff
- Commander supports forage/Food/graveyard

## Primary Gate

```python id="forage_gate"
def can_be_primary_forage(
    forage_count,
    food_or_graveyard_fuel_count,
    payoff_count,
    commander_support
):
    return (
        commander_support
        and forage_count >= 4
        and food_or_graveyard_fuel_count >= 6
        and payoff_count >= 2
    ) or (
        forage_count >= 7
        and food_or_graveyard_fuel_count >= 8
        and payoff_count >= 3
    )
```

## Resource Conflict Rule

Forage can conflict with:
- Reanimator
- Escape
- Delve
- Flashback
- Muldrotha-style recursion
- Graveyard Matters
- Food lifegain or sacrifice engines

Flag if multiple engines compete for the same graveyard or Food resources.

## Cut Logic

Protect:
- Food generators
- Graveyard fuel
- Forage payoff
- Cards that produce expendable resources
- Squirrel/Food bridge pieces

Review:
- Forage cards without fuel
- Graveyard-consuming cards if recursion is primary
- Food-consuming cards if Food payoff needs tokens intact
- Payoffs without enough resource generation

## Replacement Categories

- More Food generation
- More graveyard setup
- More forage payoff
- More sacrifice payoff
- More recursion if compatible
- More resource generation

## Report Behavior

Include:
- “Forage consumes Food or graveyard resources”
- “Resource conflict check”
- “Food/graveyard balance”

---

# 5.3.16 Expend

## Definition

Expend rewards spending a certain amount of mana in a turn.

It is a hybrid of:
- Ramp
- Midrange
- Mana sinks
- Big-turn value
- Resource conversion

## Detection Signals

Increase Expend score for:
- Expend cards
- Mana spent matters
- Ramp
- Mana sinks
- Big spells
- Activated abilities
- Commander supports expend
- Cards that spend 4+ mana reliably

## Primary Gate

```python id="expend_gate"
def can_be_primary_expend(
    expend_count,
    ramp_count,
    mana_sink_count,
    payoff_count,
    commander_support
):
    return (
        commander_support
        and expend_count >= 5
        and (ramp_count + mana_sink_count) >= 7
        and payoff_count >= 2
    ) or (
        expend_count >= 8
        and (ramp_count + mana_sink_count) >= 9
        and payoff_count >= 3
    )
```

## Cut Logic

Protect:
- Ramp
- Mana sinks
- Expend payoff
- Big-turn enablers
- Cards that reliably spend required mana

Review:
- Expend payoffs in very low-curve decks
- Mana sinks with no payoff
- Expensive cards that do not trigger or reward expend
- Ramp without conversion point

## Replacement Categories

- More ramp
- More mana sinks
- More expend payoff
- More card draw
- More big-turn finishers
- More protection

## Report Behavior

Include:
- “Can the deck reliably spend enough mana?”
- “Ramp and mana sinks are engine support”
- “Very low curve may fail to trigger expend”

---

# 5.3.17 Rooms / Eerie

## Definition

Rooms are enchantments with two unlockable halves. Eerie triggers when enchantments enter or when Rooms are fully unlocked.

Rooms and Eerie overlap with:
- Enchantress
- Constellation
- Enchantment tokens
- Staged mana sinks
- Control/value
- Long-game enchantment engines

## Detection Signals

Increase Rooms/Eerie score for:
- Room cards
- Eerie triggers
- Enchantment enters triggers
- Room unlock effects
- Enchantment token generation
- Role tokens
- Enchantment recursion
- Commander supports Rooms/Eerie/enchantments

## Primary Gate

```python id="rooms_eerie_gate"
def can_be_primary_rooms_eerie(
    room_count,
    eerie_count,
    enchantment_support_count,
    commander_support
):
    return (
        commander_support
        and (room_count + eerie_count) >= 6
        and enchantment_support_count >= 5
    ) or (
        (room_count + eerie_count) >= 10
        and enchantment_support_count >= 6
    )
```

## Multi-Role Rule

Rooms may count as:
- Enchantments
- Staged mana sinks
- Eerie enablers
- Long-game value cards
- Enchantment recursion targets

Role tokens and other enchantment tokens may support Eerie.

## Cut Logic

Protect:
- Rooms
- Eerie payoffs
- Enchantment token makers
- Enchantment recursion
- Enchantress/Constellation support
- Staged mana-sink support

Review:
- Rooms with too high unlock cost and low payoff
- Eerie payoffs with low enchantment entry density
- Enchantment support that does not trigger the actual engine
- Too many slow staged cards

## Replacement Categories

- More enchantment support
- More Eerie payoff
- More Room support
- More enchantment tokens
- More recursion
- More card draw

## Report Behavior

Include:
- “Rooms are enchantments and staged mana sinks”
- “Eerie is an enchantment-entry/unlock axis”
- “Role tokens may support Eerie”

---

# 5.3.18 Manifest Dread

## Definition

Manifest Dread chooses one of two cards to manifest face down and puts the other into the graveyard.

It bridges:
- Face-down mechanics
- Graveyard setup
- Card selection
- Recursion
- Manifest/Morph/Disguise/Cloak shells

## Detection Signals

Increase Manifest Dread score for:
- Manifest Dread cards
- Face-down payoffs
- Graveyard setup payoffs
- Face-up synergy
- Recursion
- Self-mill
- Commander supports face-down creatures
- Commander supports graveyard value

## Primary Gate

```python id="manifest_dread_gate"
def can_be_primary_manifest_dread(
    manifest_dread_count,
    face_down_payoff_count,
    graveyard_payoff_count,
    commander_support
):
    return (
        commander_support
        and manifest_dread_count >= 5
        and (face_down_payoff_count + graveyard_payoff_count) >= 3
    ) or (
        manifest_dread_count >= 8
        and face_down_payoff_count >= 2
        and graveyard_payoff_count >= 2
    )
```

## Multi-Role Rule

Manifest Dread counts as:
- Face-down support
- Graveyard setup
- Card selection
- Creature board development

## Cut Logic

Protect:
- Manifest Dread enablers
- Face-down payoff
- Graveyard payoff
- Recursion
- Face-up trigger cards

Review:
- Manifest Dread cards with no face-down or graveyard payoff
- Graveyard payoffs with too little graveyard setup
- Face-down payoffs with too few face-down cards
- Cards that exile graveyards if graveyard setup is important

## Replacement Categories

- More face-down payoff
- More graveyard payoff
- More Manifest Dread
- More recursion
- More card draw
- More protection

## Report Behavior

Include:
- “Manifest Dread is both face-down and graveyard setup”
- “Face-down/graveyard bridge”
- “Cards that look like self-mill may be engine pieces”

---

# 5.3.19 Survival

## Definition

Survival rewards having creatures tapped at the beginning of your second main phase.

Survival overlaps with:
- Attacking
- Tap abilities
- Token creatures
- Convoke-style play
- Tap-matters
- Vigilance/tap manipulation

## Detection Signals

Increase Survival score for:
- Survival cards
- Tapped-creature payoff
- Attack enablers
- Safe tap abilities
- Token makers
- Vigilance manipulation
- Convoke-style tapping
- Commander supports tapped creatures

## Primary Gate

```python id="survival_gate"
def can_be_primary_survival(
    survival_count,
    tap_support_count,
    tapped_creature_payoff_count,
    commander_support
):
    return (
        commander_support
        and survival_count >= 5
        and tap_support_count >= 6
        and tapped_creature_payoff_count >= 2
    ) or (
        survival_count >= 8
        and tap_support_count >= 8
        and tapped_creature_payoff_count >= 3
    )
```

## Cut Logic

Protect:
- Survival payoffs
- Token makers
- Creatures with tap abilities
- Safe attackers
- Vigilance/tap manipulation
- Convoke-style support

Review:
- Survival cards without reliable tapping
- Tap support with no payoff
- Combat-only cards if deck wants noncombat tapping
- Creatures that cannot safely attack or tap

## Replacement Categories

- More tap enablers
- More token bodies
- More Survival payoff
- More vigilance/tap manipulation
- More protection
- More card draw

## Report Behavior

Include:
- “Survival does not require combat damage”
- “Tapped creature support”
- “Combat/tap hybrid role”

---

# 5.3.20 Treasure Tutor Chains

## Definition

Treasure Tutor Chain decks use Treasure production as both mana and tutoring/conversion resource.

This is not just Treasure Ramp.

Treasure may be:
- Ramp
- Tutor currency
- Artifact count
- Sacrifice fodder
- Combo fuel
- Mana fixing
- Storm resource

## Detection Signals

Increase Treasure Tutor Chain score for:
- Treasure generation
- Treasure sacrifice payoff
- Artifact tutors
- Dragon tutors
- Magda-style tutor lines
- Tiamat-style Dragon tutor chain
- Deterministic Treasure conversion
- Combo pieces that use Treasures
- Commander rewards Treasure

## Primary Gate

```python id="treasure_tutor_chain_gate"
def can_be_primary_treasure_tutor_chain(
    treasure_generator_count,
    tutor_chain_piece_count,
    payoff_count,
    commander_support
):
    return (
        commander_support
        and treasure_generator_count >= 5
        and tutor_chain_piece_count >= 2
        and payoff_count >= 2
    ) or (
        treasure_generator_count >= 8
        and tutor_chain_piece_count >= 3
        and payoff_count >= 3
    )
```

## Suppression Rules

Suppress:
- Generic Treasure Ramp
- Generic Artifacts
- Generic Ramp-Control

if Treasure is being converted into a specific tutor chain or deterministic engine.

## Cut Logic

Protect:
- Treasure generators
- Tutor pieces
- Artifact/Dragon payoff
- Treasure sacrifice payoff
- Combo fuel cards
- Commander support

Review:
- Treasure payoffs with too few Treasures
- Treasure makers that do not support tutor chain
- Generic ramp if Treasure specifically matters
- Tutor chain cards if payoff package is missing

## Replacement Categories

- More Treasure generation
- More tutor chain redundancy
- More artifact/Dragon payoff
- More sacrifice payoff
- More protection
- More finishers

## Report Behavior

Include:
- “Treasure is being converted into specific cards or lines”
- “Not just ramp”
- “Tutor chain density”
- “Deterministic line or fair value?”

---

# 5.3.21 Artifact/Treasure Combo-Value

## Definition

These decks use artifact tokens, especially Treasures, as material for value engines or compact combos.

Artifact tokens may function as:
- Ramp
- Artifact count
- Sacrifice fodder
- Death trigger fuel
- Storm resource
- Combo material

## Detection Signals

Increase Artifact/Treasure Combo-Value score for:
- Artifact token generation
- Treasure generation
- Artifact sacrifice
- Artifact recursion
- Artifact drain
- Token artifact count payoff
- Compact artifact combo
- Commander rewards artifacts/Treasures

## Primary Gate

```python id="artifact_treasure_combo_value_gate"
def can_be_primary_artifact_treasure_combo_value(
    artifact_token_count,
    artifact_sacrifice_count,
    artifact_payoff_count,
    commander_support
):
    return (
        commander_support
        and artifact_token_count >= 6
        and (artifact_sacrifice_count + artifact_payoff_count) >= 4
    ) or (
        artifact_token_count >= 10
        and artifact_sacrifice_count >= 3
        and artifact_payoff_count >= 3
    )
```

## Cut Logic

Protect:
- Artifact token makers
- Treasure makers
- Artifact sacrifice outlets
- Artifact drain payoffs
- Artifact recursion
- Combo pieces if intended

Review:
- Artifact payoffs with too few artifacts
- Treasure makers if deck has no conversion point
- Combo pieces without support
- Nonartifact goodstuff that dilutes engine density

## Replacement Categories

- More artifact tokens
- More artifact sacrifice
- More artifact payoff
- More recursion
- More combo redundancy
- More card draw

## Report Behavior

Include:
- “Artifact tokens have multiple roles”
- “Value engine or compact combo?”
- “Treasure as artifact material, not only ramp”

---

# 5.3.22 Slow Alternate Win Conditions

## Definition

Slow alternate win condition decks use alternate win cards that require setup over multiple turns or a protected board state.

Examples:
- Approach of the Second Sun
- Felidar Sovereign
- Mechanized Production
- Maze’s End
- Revel in Riches
- Simic Ascendancy

## Detection Signals

Increase Slow Alt Win score for:
- Alternate win condition
- Visible win condition
- Multi-turn setup
- Pillowfort support
- Control support
- Lifegain support
- Artifact/enchantment/land support
- Tutors or protection

## Primary Gate

```python id="slow_alt_win_gate"
def can_be_primary_slow_alt_win(
    alt_win_count,
    protection_or_stall_count,
    setup_support_count,
    commander_support
):
    return (
        alt_win_count >= 1
        and protection_or_stall_count >= 4
        and setup_support_count >= 3
    ) or (
        commander_support
        and alt_win_count >= 1
        and setup_support_count >= 2
    )
```

## Suppression Rule

Do not label slow alternate wins as true turbo combo.

Tag separately:
- `slow_alt_win_condition`
- `visible_win_condition`
- `protected_setup_required`
- `not_turbo_combo`

## Cut Logic

Protect:
- Alt-win card if deck is built to support it
- Tutors/card selection
- Protection
- Pillowfort/control support
- Setup enablers

Review:
- Unsupported alt-win cards
- Slow alt-win with no protection
- Alt-win that conflicts with primary plan
- Cards that only win if opponents ignore them

## Replacement Categories

- More protection
- More tutors/card selection
- More control
- More pillowfort
- More setup support
- More backup win conditions

## Report Behavior

Include:
- “Slow alternate win, not turbo combo”
- “Visibility and interaction risk”
- “Protection/setup support”
- “Is this a main plan or backup?”

---

# 5.3.23 Game Changer / Bracket Pressure Packages

## Definition

These packages include cards that strongly affect Commander power perception, even if they are not combo pieces.

Bracket pressure is a report modifier, not an archetype and not an automatic cut.

## Detection Signals

Increase Bracket Pressure score for:
- Game Changer cards
- Fast mana
- Efficient tutors
- Free interaction
- Compact combo
- Mass land denial
- High-power value pieces
- Deterministic tutor chains
- Combo protection
- High-efficiency engines

## Classification

```yaml id="bracket_pressure_classification"
bracket_pressure_types:
  game_changer:
  bracket_pressure:
  high_bracket_pressure:
  slow_alt_win_condition:
  high_power_value_piece:
  compact_combo_piece:
  fast_combo_enabler:
  true_turbo_combo:
  mass_land_denial:
  efficient_tutor:
  tutor_chain:
  combo_protection:
```

## Cut Logic

Never automatically cut a bracket-pressure card.

Classify as:
- Core but bracket-pushing
- Correct at higher bracket
- Pregame discussion recommended
- Possible cut if lowering power
- Manual review

## Replacement Categories

- Lower-bracket alternative
- Slower tutor
- Fairer draw engine
- More thematic replacement
- Less efficient but table-friendlier card
- More pregame discussion clarity

## Report Behavior

Include:
- “Bracket pressure is not the same as a cut”
- “Table-fit review”
- “Pregame discussion recommended if intended bracket is lower”
- “Card may be powerful and correct but still bracket-relevant”

---

# 5.3.24 High-Power Value but Not Turbo Combo

## Definition

These decks use efficient engines, tutors, fast mana, and high-quality interaction, but they are not necessarily built to win as fast as possible through deterministic combo.

## Detection Signals

Increase High-Power Value score for:
- Efficient value engines
- Strong card advantage
- Fast mana
- Efficient tutors
- Free interaction
- High-impact commander
- Compact combo backup
- Low curve with strong resource conversion

## Primary Gate

```python id="high_power_value_gate"
def can_be_high_power_value_not_turbo(
    efficient_engine_count,
    fast_mana_count,
    efficient_tutor_count,
    compact_combo_count,
    true_turbo_combo_result
):
    return (
        efficient_engine_count >= 4
        and (fast_mana_count + efficient_tutor_count) >= 3
        and not true_turbo_combo_result
    )
```

## Suppression Rule

Do not mislabel as turbo combo if true turbo combo gate fails.

Use:
- `high_power_value`
- `high_power_value_piece`
- `not_turbo_combo`
- `bracket_pressure`

## Cut Logic

Protect:
- Efficient engine pieces if intended bracket supports them
- High-quality interaction
- Value engines
- Commander support

Review:
- High-power staples if user wants lower bracket
- Efficient tutors if they over-centralize deck
- Fast mana if deck’s intended table is casual
- Powerful cards that are wrong shell

## Replacement Categories

- Lower-bracket alternatives
- More thematic value
- Slower but synergistic draw
- Less efficient tutors
- More table-appropriate interaction

## Report Behavior

Include:
- “High-power value, not necessarily turbo combo”
- “Bracket fit”
- “Value engine density”
- “Whether compact combo is primary or backup”

---

# 5.3.25 Compact Combo but Not Full Combo Deck

## Definition

Some decks include one or two compact combos while mostly playing fair value, combat, or synergy.

## Detection Signals

Increase Compact Combo Backup score for:
- Two-card combo
- Three-card combo
- Infinite mana outlet
- Infinite drain/token/damage loop
- Commander is one combo piece
- Low tutor density
- Low protection density
- Fair primary plan present

## Primary Gate

```python id="compact_combo_backup_gate"
def classify_compact_combo_backup(
    combo_piece_count,
    tutor_count,
    protection_count,
    fair_plan_strength
):
    if combo_piece_count >= 2 and tutor_count <= 2 and fair_plan_strength >= 5:
        return "compact_combo_backup"

    if combo_piece_count >= 2 and tutor_count >= 3 and protection_count >= 2:
        return "combo_primary_or_high_pressure"

    return "manual_combo_review"
```

## Cut Logic

Protect:
- Combo pieces if user wants combo backup
- Combo pieces that are also good in fair plan
- Tutors/protection if bracket supports combo

Review:
- Combo pieces that are dead outside combo
- Unsupported combo pieces
- Combo pieces that raise bracket above user intent
- Pieces with no tutor/protection support

## Replacement Categories

- More combo redundancy if user wants combo
- More fair-plan synergy if user does not
- More protection
- More tutors/card selection
- Lower-bracket alternatives

## Report Behavior

Include:
- “Has combo does not mean is combo”
- “Combo centrality”
- “Backup finish or primary plan?”
- “Bracket implication”

---

# 5.3.26 Combo-Adjacent Value

## Definition

Combo-Adjacent Value decks are primarily value decks but include pieces that can accidentally or intentionally loop.

## Detection Signals

Increase Combo-Adjacent score for:
- Recursion loops
- Artifact loops
- Sacrifice loops
- Infinite-adjacent engines
- Commander doubles triggers
- Value pieces that can loop
- Low tutor density
- Value-first primary plan

## Primary Gate

```python id="combo_adjacent_value_gate"
def can_be_combo_adjacent_value(
    potential_loop_count,
    tutor_count,
    fair_value_engine_count
):
    return (
        potential_loop_count >= 2
        and fair_value_engine_count >= 4
        and tutor_count <= 2
    )
```

## Cut Logic

Protect:
- Value pieces that are strong outside combo
- Engine pieces that support primary plan
- Commander synergy pieces

Review:
- Loop pieces that do nothing alone
- Accidental combo if user wants lower power
- Pieces that create bracket pressure without being central
- Redundant combo-only cards

## Replacement Categories

- More fair value
- More loop redundancy if desired
- More protection
- More card draw
- Lower-bracket alternatives
- Manual combo review

## Report Behavior

Include:
- “Combo-adjacent does not mean turbo combo”
- “Value first, combo second”
- “Potential loop review”
- “Ask whether combo is desired if user intent unclear”

---

# 5.3.27 Commander Tax Advantage

## Definition

These decks benefit from repeatedly casting their commander, reducing commander tax, or turning commander tax into a manageable resource.

## Detection Signals

Increase Commander Tax Advantage score for:
- Commander cast triggers
- Commander recast effects
- Commander cost reduction
- Sacrifice/recast loops
- Commander storm count
- Commander can be cast cheaply
- Commander returns to hand
- Commander tax mitigation
- Commander death/cast payoff

## Primary Gate

```python id="commander_tax_advantage_gate"
def can_be_primary_commander_tax_advantage(
    commander_cast_payoff_count,
    commander_recast_support_count,
    commander_cost_reduction_count,
    commander_support
):
    return (
        commander_support
        and commander_cast_payoff_count >= 2
        and (commander_recast_support_count + commander_cost_reduction_count) >= 4
    )
```

## Cut Logic

Protect:
- Commander cost reducers
- Commander recast support
- Sacrifice outlets if recasting matters
- Commander cast payoffs
- Mana engines that support recasting

Review:
- Expensive commander recast plan without ramp/cost reduction
- Commander protection if deck actually wants commander to die
- Cards that only avoid commander tax when deck wants to exploit it
- Recast payoffs with no recast support

## Replacement Categories

- More commander cost reduction
- More recast support
- More sacrifice/bounce support
- More ramp
- More commander cast payoff
- More protection if needed

## Report Behavior

Include:
- “Commander tax may be a resource, not only a penalty”
- “Recast support”
- “Do not over-penalize commander recast plan”

---

# 5.3.28 Commander Recast / Death Loops

## Definition

These decks sacrifice, kill, bounce, or recast their commander repeatedly to trigger ETB, death, cast, or leaves-the-battlefield effects.

## Detection Signals

Increase Commander Recast/Death Loop score for:
- Commander death triggers
- Commander ETB triggers
- Commander cast triggers
- Sacrifice outlets
- Commander recursion
- Bounce/recast support
- Board reset commander
- Aristocrats payoff
- Commander-zone replacement decisions matter

## Primary Gate

```python id="commander_death_loop_gate"
def can_be_primary_commander_death_loop(
    commander_trigger_count,
    sacrifice_or_bounce_count,
    recursion_or_recast_support_count,
    payoff_count
):
    return (
        commander_trigger_count >= 1
        and sacrifice_or_bounce_count >= 4
        and recursion_or_recast_support_count >= 3
        and payoff_count >= 2
    )
```

## Cut Logic

Protect:
- Sacrifice outlets
- Commander recursion
- Recast support
- Aristocrats payoffs
- ETB/death payoff support
- Board reset parity breakers if commander resets board

Review:
- Commander protection if death is part of plan
- Sacrifice outlets without payoff
- Recursion if commander returns to command zone too often
- Expensive support that does not advance loop

## Replacement Categories

- More sacrifice outlets
- More recursion
- More commander recast support
- More payoff density
- More ramp
- More protection for engine pieces

## Report Behavior

Include:
- “Commander is an engine piece”
- “Death/recast loop support”
- “Commander-zone replacement decisions matter”

---

# 5.3.29 Partner / Background Pair-Defined Decks

## Definition

Partner, Background, Friends Forever, and Doctor’s Companion decks are defined by interaction between two commander-zone cards.

The strategy may not be visible from either card alone.

## Detection Signals

Increase Pair-Defined score for:
- Partner pair
- Background pair
- Friends Forever pair
- Doctor’s Companion pair
- Commander pair synergy
- One commander enables the other
- Pair creates commander-zone combo
- Pair defines colors and strategy

## Primary Gate

```python id="pair_defined_gate"
def can_be_primary_pair_defined(
    has_commander_pair,
    pair_synergy_count,
    payoff_count
):
    return (
        has_commander_pair
        and pair_synergy_count >= 2
        and payoff_count >= 1
    )
```

## Analysis Rule

Analyze the commander pair as a combined engine before assigning primary strategy.

Do not evaluate either commander in isolation.

## Cut Logic

Protect:
- Cards that connect both commanders
- Cards that support the pair’s shared plan
- Commander protection
- Commander-zone combo pieces if intended

Review:
- Cards that support only one commander weakly
- Cards that ignore the pair’s actual synergy
- Broad goodstuff that dilutes pair plan

## Replacement Categories

- More pair synergy
- More commander protection
- More shared engine support
- More card draw
- More removal
- More finishers

## Report Behavior

Include:
- “Commander pair creates strategy”
- “Do not evaluate commanders separately”
- “Pair synergy support cards”

---

# 5.3.30 Doctor’s Companion / Time Counter Shells

## Definition

Doctor’s Companion decks combine a Doctor and companion, often using historic spells, legends, suspend, time counters, or cast-from-exile themes.

## Detection Signals

Increase Doctor/Time Counter score for:
- Doctor’s Companion
- Time counters
- Suspend support
- Historic support
- Legendary support
- Cast-from-exile support
- Commander pair synergy
- Time counter manipulation

## Primary Gate

```python id="doctor_time_counter_gate"
def can_be_primary_doctor_time_counter(
    doctors_companion_pair,
    time_counter_support_count,
    historic_or_exile_support_count,
    payoff_count
):
    return (
        doctors_companion_pair
        and (time_counter_support_count + historic_or_exile_support_count) >= 6
        and payoff_count >= 2
    )
```

## Cut Logic

Protect:
- Time counter support
- Suspend cards
- Historic support
- Cast-from-exile payoffs
- Commander pair synergy pieces
- Legendary support if relevant

Review:
- Time counter cards with no payoff
- Suspend cards without commander connection
- Historic cards that do not support pair plan
- Generic goodstuff that dilutes commander pair engine

## Replacement Categories

- More time counter support
- More suspend support
- More historic triggers
- More cast-from-exile payoff
- More commander pair protection
- More card draw

## Report Behavior

Include:
- “Tie time counters back to commander pair”
- “Doctor’s Companion creates hybrid identity”
- “Historic/suspend/exile overlap”

---

# 5.3.31 Multiple-Copy Exception Decks

## Definition

These decks intentionally run multiple copies of cards that override Commander singleton rules or have special deckbuilding exceptions.

## Detection Signals

Increase Multiple-Copy Exception score for:
- Legal duplicate exception cards
- Repeated card strategy
- Copy count above singleton
- Commander supports repeated card
- Typal scaling
- Tutor/draw consistency
- Payoffs for repeated card

## Primary Gate

```python id="multiple_copy_exception_primary_gate"
def can_be_primary_multiple_copy_exception(
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

## Legality Rule

Do not flag legal duplicate exceptions as illegal.

## Cut Logic

Protect:
- Repeated exception card
- Payoff cards
- Commander synergy
- Tutors/draw that find repeated card
- Typal support if relevant

Review:
- Too few copies to function
- Payoffs with too little repeated-card density
- Off-plan goodstuff that dilutes exception density
- Duplicate cards without exception text

## Replacement Categories

- More copies of exception card
- More payoff support
- More card draw
- More protection
- More tutor effects
- More role support

## Report Behavior

Include:
- “Legal duplicate exception detected”
- “Copy count matters”
- “Do not apply singleton violation if card permits copies”

---

# 5.3.32 Nazgûl / Wraith Ring Hybrid

## Definition

Nazgûl decks use up to nine copies of Nazgûl, Ring temptation, +1/+1 counters, and Wraith support.

This is:
- Multiple-copy exception
- Wraith typal
- Ring temptation package
- Counter scaling engine

## Detection Signals

Increase Nazgûl/Wraith score for:
- Nazgûl copies
- Wraith support
- Ring temptation
- Ring-bearer payoff
- +1/+1 counter scaling
- Evasion
- Commander supports Wraiths/Ring
- Legendary/Ring support

## Primary Gate

```python id="nazgul_wraith_ring_gate"
def can_be_primary_nazgul_wraith_ring(
    nazgul_count,
    ring_temptation_count,
    counter_payoff_count,
    commander_support
):
    return (
        nazgul_count >= 5
        and ring_temptation_count >= 4
        and (
            counter_payoff_count >= 2
            or commander_support
        )
    )
```

## Cut Logic

Protect:
- Nazgûl copies
- Ring temptation cards
- Wraith payoff
- Counter scaling
- Evasive support
- Ring-bearer support

Review:
- Too few Nazgûl copies
- Ring support with too few tempt triggers
- Generic Wraiths with no payoff
- Counter cards that do not support the swarm

## Replacement Categories

- More Nazgûl copies up to legal limit
- More Ring temptation
- More counter support
- More Wraith payoff
- More evasion
- More protection

## Report Behavior

Include:
- “Nazgûl copy exception”
- “Ring temptation is core support”
- “Wraith/counter hybrid”

---

# 5.3.33 Hare Apparent / Rabbit Swarm

## Definition

Hare Apparent decks use multiple copies of Hare Apparent and Rabbit/token payoffs to create a white or Selesnya go-wide swarm.

## Detection Signals

Increase Hare/Rabbit score for:
- Hare Apparent copies
- Rabbit token support
- Go-wide token payoff
- Anthems
- Counters
- Commander supports Rabbits/tokens
- White token density

## Primary Gate

```python id="hare_rabbit_swarm_gate"
def can_be_primary_hare_rabbit_swarm(
    hare_apparent_count,
    token_payoff_count,
    commander_support
):
    return (
        hare_apparent_count >= 8
        and (
            token_payoff_count >= 3
            or commander_support
        )
    )
```

## Cut Logic

Protect:
- Hare Apparent copies
- Rabbit payoffs
- Token payoffs
- Anthems
- Board protection
- Commander support

Review:
- Too few Hare Apparent copies
- Token payoffs with low token density
- Non-Rabbit creatures with no support role
- Cards that dilute copy density

## Replacement Categories

- More Hare Apparent copies
- More Rabbit/token payoff
- More anthems
- More board protection
- More card draw
- More go-wide finishers

## Report Behavior

Include:
- “Hare Apparent copy exception”
- “Rabbit swarm density”
- “Token combat plan”

---

# 5.3.34 Shadowborn Apostle / Demon Tutor Engine

## Definition

Shadowborn Apostle decks run many copies of Shadowborn Apostle, sacrifice six Apostles, and tutor Demons directly to the battlefield.

This is:
- Multiple-copy exception
- Sacrifice engine
- Demon tutor engine
- Aristocrats/reanimation hybrid

## Detection Signals

Increase Apostle Engine score for:
- Shadowborn Apostle copies
- Demon payoff
- Sacrifice outlets
- Death payoffs
- Recursion
- Aristocrats drain
- Commander supports Apostles/death/Demons

## Primary Gate

```python id="shadowborn_apostle_gate"
def can_be_primary_shadowborn_apostle(
    apostle_count,
    demon_payoff_count,
    recursion_or_sacrifice_count,
    commander_support
):
    return (
        apostle_count >= 18
        and demon_payoff_count >= 2
        and (
            recursion_or_sacrifice_count >= 4
            or commander_support
        )
    )
```

## Cut Logic

Protect:
- Shadowborn Apostle copies
- Demon targets
- Sacrifice outlets
- Recursion
- Death payoffs
- Aristocrats payoffs

Review:
- Too few Apostle copies
- Demon targets that are low impact
- Off-plan creatures that dilute Apostle density
- Sacrifice payoffs with insufficient fodder

## Replacement Categories

- More Apostle copies
- Better Demon targets
- More recursion
- More sacrifice payoff
- More card draw
- More protection

## Report Behavior

Include:
- “Apostle count is critical”
- “Demon tutor engine”
- “Do not treat copies as illegal duplicates”

---

# 5.3.35 Persistent Petitioners / Advisor Mill

## Definition

Persistent Petitioners decks run many copies of Persistent Petitioners and tap Advisors to mill opponents.

## Detection Signals

Increase Petitioners score for:
- Persistent Petitioners copies
- Advisor density
- Tap-to-mill
- Mill doublers
- Defender/toughness synergy
- Untap effects
- Commander supports mill/toughness/Advisors

## Primary Gate

```python id="persistent_petitioners_gate"
def can_be_primary_persistent_petitioners(
    petitioner_count,
    mill_payoff_count,
    untap_or_defender_support_count,
    commander_support
):
    return (
        petitioner_count >= 15
        and (
            mill_payoff_count >= 2
            or untap_or_defender_support_count >= 3
            or commander_support
        )
    )
```

## Cut Logic

Protect:
- Persistent Petitioners copies
- Advisor support
- Mill doublers
- Untap effects
- Defender/toughness payoff if relevant

Review:
- Too few Petitioners
- Mill support without enough mill density
- Non-Advisors that do not support mill/tap plan
- Cards that do not help against three 100-card libraries

## Replacement Categories

- More Petitioners
- More mill payoff
- More untap effects
- More protection
- More card draw
- More defender/toughness support

## Report Behavior

Include:
- “Petitioners solve singleton consistency”
- “Copy count matters”
- “Tap-to-mill engine”

---

# 5.3.36 Dragon’s Approach / Spell-Density Dragon Tutor

## Definition

Dragon’s Approach decks run many copies of Dragon’s Approach to deal damage and eventually exile copies from the graveyard to tutor Dragons.

This is:
- Spell-density deck
- Burn deck
- Graveyard setup deck
- Dragon tutor deck

## Detection Signals

Increase Dragon’s Approach score for:
- Dragon’s Approach copies
- Spell-copy support
- Cost reduction
- Graveyard count matters
- Dragon targets
- Burn payoff
- Storm-adjacent support
- Commander supports instants/sorceries or Dragons

## Primary Gate

```python id="dragons_approach_gate"
def can_be_primary_dragons_approach(
    approach_count,
    dragon_target_count,
    spell_support_count,
    commander_support
):
    return (
        approach_count >= 15
        and dragon_target_count >= 2
        and (
            spell_support_count >= 4
            or commander_support
        )
    )
```

## Multi-Role Rule

Dragon’s Approach counts as:
- Burn
- Spell density
- Graveyard fuel
- Dragon tutor infrastructure
- Multiple-copy exception

## Cut Logic

Protect:
- Dragon’s Approach copies
- Dragon targets
- Spell-copy support
- Cost reducers
- Graveyard setup
- Burn/spellslinger payoffs

Review:
- Too few Approach copies
- Dragon targets with low impact
- Graveyard hate that shuts off own plan
- Non-spell cards that dilute density

## Replacement Categories

- More Dragon’s Approach copies
- Better Dragon targets
- More spell-copy support
- More cost reduction
- More graveyard protection
- More card draw

## Report Behavior

Include:
- “Spell-density exception”
- “Approach count matters”
- “Dragon tutor infrastructure”
- “Graveyard support/conflict”

---

# 5.3.37 Typal-Mechanic Hybrids

## Definition

Typal-mechanic hybrids are decks where creature type and mechanic are inseparable.

Examples:
- Vampire + Blood
- Zombie + Decayed
- Dinosaur + Discover
- Merfolk + Explore
- Rabbit + Tokens
- Squirrel + Food
- Phyrexian + Incubate
- Wraith + Ring Temptation

## Detection Signals

Increase Typal-Mechanic Hybrid score for:
- Typal density
- Mechanic density
- Commander supports both
- Mechanic creates relevant creature type
- Typal payoff uses mechanic
- Mechanic payoff uses creature type
- Shared resource engine

## Primary Gate

```python id="typal_mechanic_hybrid_gate"
def can_be_primary_typal_mechanic_hybrid(
    typal_density,
    mechanic_density,
    shared_payoff_count,
    commander_support
):
    return (
        commander_support
        and typal_density >= 8
        and mechanic_density >= 4
        and shared_payoff_count >= 2
    ) or (
        typal_density >= 12
        and mechanic_density >= 6
        and shared_payoff_count >= 3
    )
```

## Suppression Rule

Do not call the deck only by the tribe if the mechanic is essential.

Use both tags:
- `vampire_blood`
- `zombie_decayed`
- `dinosaur_discover`
- `merfolk_explore`
- `rabbit_tokens`
- `squirrel_food`
- `phyrexian_incubate`

## Cut Logic

Protect:
- Cards that bridge tribe and mechanic
- Mechanic enablers that create tribe members
- Typal payoffs that reward mechanic output
- Commander support

Review:
- Generic tribe cards that ignore the mechanic
- Mechanic cards that do not support the tribe
- Off-plan goodstuff
- Payoffs with low shared density

## Replacement Categories

- More typal-mechanic bridge cards
- More mechanic enablers
- More typal payoff
- More shared payoff
- More protection
- More card draw

## Report Behavior

Include:
- “This is not just typal; it is typal plus mechanic”
- “Bridge cards are high priority”
- “Do not cut mechanic enablers as off-type”

---

# 5.3.38 Commander-Defined Single-Card Archetypes

## Definition

Some commanders create unique deckbuilding rules or play patterns that do not fit cleanly into established archetypes.

The commander itself defines the deck’s strategy.

## Detection Signals

Increase Commander-Defined Strategy score for:
- Commander text creates unique resource conversion
- Commander imposes unusual deckbuilding incentives
- Commander creates a unique loop
- Commander transforms normal card roles
- Commander makes bad-looking cards good
- Commander strategy does not fit broad archetype cleanly

## Primary Gate

```python id="commander_defined_single_card_gate"
def can_be_primary_commander_defined_strategy(
    commander_unique_engine,
    support_card_count,
    payoff_count
):
    return (
        commander_unique_engine
        and support_card_count >= 4
        and payoff_count >= 1
    )
```

## Suppression Rule

Commander-defined strategy should override broad fallback labels when the commander’s rules text clearly defines the plan.

## Cut Logic

Protect:
- Commander-specific enablers
- Cards that look weak but enable commander
- Unique engine pieces
- Commander protection
- Payoff cards that only make sense with commander

Review:
- Generic goodstuff that does not support commander engine
- Cards that belong to a broad archetype but not this commander
- Powerful cards that pull deck away from commander plan

## Replacement Categories

- More commander-specific enablers
- More protection
- More engine redundancy
- More payoff density
- More card draw
- More role coverage inside commander plan

## Report Behavior

Include:
- “Commander defines the archetype”
- “Broad fallback labels suppressed”
- “Evaluate card roles through commander text”

---

# 5.3.39 Bracket-Aware Stax / Hatebear Packages

## Definition

These decks use tax effects, Rule of Law effects, graveyard hate, artifact hate, tutor hate, and other hatebears.

A few hatebears can be interaction.
A dense hatebear/stax package changes bracket expectations.

## Detection Signals

Increase Bracket-Aware Stax score for:
- Tax effects
- Rule of Law effects
- Graveyard hate
- Artifact hate
- Tutor hate
- Hatebear density
- Lock pieces
- Commander breaks parity
- Social contract pressure

## Primary Gate

```python id="bracket_aware_stax_gate"
def can_be_primary_bracket_aware_stax(
    hatebear_count,
    lock_piece_count,
    parity_breaker_count,
    win_condition_count
):
    return (
        (hatebear_count + lock_piece_count) >= 8
        and parity_breaker_count >= 2
        and win_condition_count >= 2
    )
```

## Suppression Rule

Separate:
- Healthy interaction
- Meta hate package
- Bracket-pressure lock package
- Full Stax strategy

## Cut Logic

Protect:
- Hatebears that match intended meta
- Lock pieces the deck breaks parity on
- Pressure pieces
- Win conditions under lock

Review:
- Hate pieces that shut off own plan
- Lock pieces with no win condition
- Social-contract pressure in casual brackets
- Meta hate without known meta

## Replacement Categories

- More parity breakers
- More pressure
- More flexible interaction
- Lower-salt alternatives
- More card draw
- More finishers

## Report Behavior

Include:
- “Healthy interaction or lock package?”
- “Bracket/social pressure”
- “Does deck break parity?”
- “Does deck win after slowing table?”

---

# 5.3.40 Fast Mana / Explosive Start Package

## Definition

Fast mana packages use zero- or one-mana acceleration, rituals, burst mana, or highly efficient lands to accelerate far ahead of the table.

Fast mana is not automatically a cut, but it is always a power-level signal.

## Detection Signals

Increase Fast Mana score for:
- Zero-mana rocks
- One-mana high-efficiency acceleration
- Rituals
- Burst mana
- Ancient Tomb-style lands
- Commander fast deployment
- Early lock/combo/value snowball
- Fast mana plus tutor/combo density

## Primary Gate

Fast mana is usually a report modifier, not a primary archetype.

```python id="fast_mana_pressure_gate"
def fast_mana_pressure_level(
    fast_mana_count,
    early_payoff_count,
    combo_or_lock_count
):
    if fast_mana_count >= 4 and (early_payoff_count + combo_or_lock_count) >= 3:
        return "high_bracket_pressure"
    if fast_mana_count >= 2:
        return "bracket_pressure"
    return "low_or_none"
```

## Cut Logic

Protect:
- Fast mana if intended bracket supports it
- Fast mana that enables commander’s actual plan
- Explosive start pieces in high-power decks

Review:
- Fast mana in low-bracket casual deck
- Fast mana that accelerates off-plan cards
- Fast mana increasing threat perception without needed payoff
- Explosive starts with no resilience

## Replacement Categories

- Slower ramp
- More thematic ramp
- Lower-bracket alternatives
- More lands
- More commander-synergy ramp
- More table-appropriate acceleration

## Report Behavior

Include:
- “Fast mana is a power-level signal”
- “Not automatically a cut”
- “Review for intended bracket”

---

# 5.3.41 Free Interaction / Protection Package

## Definition

Free or alternate-cost interaction protects wins, stops opponents, or maintains tempo while tapped out.

## Detection Signals

Increase Free Interaction score for:
- Free counterspells
- Free protection
- Alternate-cost removal
- Pitch spells
- Free sacrifice protection
- Combo protection
- Tempo protection
- High-power interaction density

## Primary Gate

Usually a report modifier, not a primary archetype.

```python id="free_interaction_pressure_gate"
def free_interaction_pressure_level(
    free_interaction_count,
    combo_piece_count,
    high_power_engine_count
):
    if free_interaction_count >= 3 and (combo_piece_count >= 2 or high_power_engine_count >= 3):
        return "high_bracket_pressure"
    if free_interaction_count >= 2:
        return "bracket_pressure"
    return "low_or_none"
```

## Cut Logic

Protect:
- Free interaction if intended bracket supports it
- Protection for combo or key commander
- Alternate-cost interaction that covers deck weakness

Review:
- Free interaction if user wants lower bracket
- Protection density if combo is not intended
- High-power interaction that does not support plan
- Cards that create bracket mismatch

## Replacement Categories

- Lower-bracket protection
- Normal-cost interaction
- More thematic protection
- More commander protection
- More flexible removal
- More table-appropriate answers

## Report Behavior

Include:
- “Free interaction changes combo safety”
- “Bracket-pressure signal”
- “Separate from ordinary removal”

---

# 5.3.42 Tutor Density / Tutor Chain Pressure

## Definition

Tutor density measures how much a deck uses search effects as structure, not just utility.

High tutor density can make a deck functionally more consistent and push bracket.

## Detection Signals

Increase Tutor Density score for:
- Efficient tutors
- Repeated tutors
- Commander tutors
- Tutor chains
- Toolbox tutors
- Deterministic search lines
- Silver bullets
- Combo assembly
- Legendary/artifact/enchantment chain access

## Classification

```python id="classify_tutor_use"
def classify_tutor_use(
    tutor_count,
    deterministic_line_count,
    silver_bullet_count,
    combo_piece_count
):
    if deterministic_line_count >= 2 or (tutor_count >= 5 and combo_piece_count >= 2):
        return "deterministic_tutor_chain"

    if tutor_count >= 4 and silver_bullet_count >= 3:
        return "toolbox_tutor_package"

    if tutor_count >= 3:
        return "tutor_density_pressure"

    return "normal_tutor_use"
```

## Cut Logic

Protect:
- Tutors if toolbox/combo strategy is intended
- Tutor targets
- Silver bullets if meta-relevant
- Commander-supported search lines

Review:
- Efficient tutors if user wants lower bracket
- Tutors with no clear targets
- Deterministic lines that raise bracket beyond intent
- Silver bullets with no meta relevance

## Replacement Categories

- More toolbox targets
- Fewer efficient tutors for lower bracket
- More card draw instead of tutors
- More thematic tutors
- More redundant enablers
- More pregame discussion clarity

## Report Behavior

Include:
- “Fair toolbox or deterministic tutor chain?”
- “Tutor density changes functional consistency”
- “Bracket pressure review”

---

# 5.3.43 High-Synergy Low-Raw-Power Cards

## Definition

These are cards that look weak by generic evaluation but are excellent in a specific shell because they provide density, enable the commander, or complete a synergy package.

## Detection Signals

Increase High-Synergy Low-Power score for:
- Card directly supports commander trigger
- Card provides scarce density
- Card is a cheap enabler
- Card bridges multiple themes
- Card enables core engine
- Card is weak alone but strong in context
- Card supports sacrifice/recursion/token/landfall engine

## Protection Rule

```python id="protect_high_synergy_low_power"
def should_protect_high_synergy_low_power(
    commander_synergy,
    core_engine_support,
    density_piece,
    bridge_card
):
    return (
        commander_synergy
        or core_engine_support
        or density_piece
        or bridge_card
    )
```

## Cut Logic

Protect:
- Low-power commander enablers
- Density pieces
- Bridge cards
- Engine glue
- Cards that turn on payoffs

Review:
- Low-power cards with no commander/engine support
- Cards that only look synergistic but do not trigger payoffs
- Narrow cards with low density and low payoff

## Replacement Categories

- Same-role but better synergy
- More engine density
- More commander enablers
- More bridge cards
- More protection
- More card draw

## Report Behavior

Include:
- “This card looks weak by generic standards but supports the actual engine”
- “Do not cut solely for low raw power”
- “Explain the context role”

---

# 5.3.44 Generically Good but Wrong Shell

## Definition

These are powerful cards that do not support the deck’s actual plan.

They may be staples, Game Changers, efficient value pieces, or high-power cards, but they can still be replaceable if they pull the deck away from its strategy.

## Detection Signals

Increase Wrong Shell score for:
- High raw power
- Low commander synergy
- Does not support primary/secondary plan
- Raises bracket without supporting intent
- Generic staple with no role need
- Competes with core engine
- Duplicates role already saturated
- Pulls deck toward different archetype

## Cut Logic

Increase cut pressure if:
- Card is powerful but off-plan
- Card raises bracket beyond intended table
- Card does not support commander
- Card conflicts with strategy shape
- Card is replaceable by a more synergistic option

Do not call the card bad.

Use language:
```text id="hou5d1"
This is a strong card, but it may be a wrong-shell inclusion for this deck’s actual plan.
```

## Replacement Categories

- More commander synergy
- More primary-plan support
- More role-appropriate card draw
- More strategy-aligned removal
- More lower-bracket alternatives
- More collection-aware replacement later

## Report Behavior

Include:
- “Strong card, wrong shell”
- “Replaceability is about plan alignment, not raw power”
- “Optional cut candidate if optimizing synergy”

---

# 5.3.45 Refined Deck Review Candidates

## Definition

This is not a deck archetype. It is a deck-helper output category for legal, refined decks where no obvious cuts exist.

Instead of forcing bad cuts, list cards worth playtesting.

## Trigger Condition

Use this when:
- Deck is legal
- Deck is focused
- No mandatory cuts are needed
- No obvious bad cuts exist
- Recommended cuts would be speculative
- Optional optimization still has value

```python id="refined_deck_review_trigger"
def should_use_refined_deck_review(
    required_cuts,
    recommended_cut_count,
    deck_focus_score
):
    return (
        required_cuts == 0
        and recommended_cut_count == 0
        and deck_focus_score >= 8
    )
```

## Candidate Sources

List 3–5 playtest-first candidates from:
- Context-dependent cards
- Minor-package cards
- Low-confidence synergy cards
- Bracket-pressure cards
- Redundant role cards
- Narrow cards that need playtesting
- Generically good but wrong-shell cards
- Cards with uncertain table fit

## Report Language

Use:
```text id="0i2sxt"
These are not guaranteed cuts. These are playtest-first review candidates based on curve, synergy, redundancy, role balance, and your deck’s actual plan.
```

## Replacement Categories

- More commander synergy
- More role balance
- More protection
- More card draw
- More interaction
- More strategy-aligned upgrade
- Collection-aware replacement later

---

# 5.3.46 Collection-Aware Replacement Planning

## Definition

Collection-aware replacement planning means replacement suggestions should eventually come from the user’s actual owned cards rather than the whole Magic database.

This is a future-facing support layer.

## Detection Signals

Use when:
- User has collection database
- User asks for replacements from owned cards
- Deck helper has collection folder/data
- Replacement categories are known
- Exact cards should be filtered by ownership

## Future Logic

```python id="collection_aware_replacement_logic"
def collection_aware_replacements(
    replacement_category,
    user_collection,
    color_identity,
    bracket_intent,
    deck_strategy_tags
):
    candidates = filter_by_collection(user_collection)
    candidates = filter_by_color_identity(candidates, color_identity)
    candidates = filter_by_strategy_tags(candidates, deck_strategy_tags)
    candidates = filter_by_bracket_intent(candidates, bracket_intent)
    return rank_by_synergy_and_role_fit(candidates, replacement_category)
```

## Current v0.5.6 Behavior

Until collection data exists:
- Suggest replacement categories first.
- Avoid pretending to know the user’s collection.
- Mention exact cards only when user asks or source data supports it.
- Keep replacement planning role-based.

## Report Behavior

Include:
- “Replacement category now, exact owned-card suggestion later”
- “Collection data required”
- “Owned-card priority is a future feature”

---

# 5.3.47 Global Emergent Cut Review Rules

## Do Not Automatically Cut Emergent-Package Cards When

Do not automatically cut cards when:
- The commander directly creates or rewards the package.
- The card is low raw power but high synergy.
- The card is part of a commander-defined plan.
- The card enables a multiple-copy exception deck.
- The card is part of a compact combo the user intentionally wants.
- The card is a bracket-pressure card but core to the intended deck level.
- The card supports a newer mechanic package the helper recognizes.
- The card is a bridge between typal and mechanic identities.
- The card converts one resource into the deck’s main win condition.
- The card is a context-dependent role player in a refined deck.

## Apply Higher Cut Pressure When

Apply higher cut pressure when:
- A broad fallback archetype is stealing primary from a narrower commander-defined plan.
- The card is generically good but off-plan.
- The card creates bracket pressure above the user’s intended table.
- The card is a compact combo piece without support, tutors, or user intent.
- The deck has a mechanic payoff but not enough enablers.
- The deck has enablers but no conversion point.
- A multiple-copy exception deck has too few copies to function.
- A slow alternate win lacks protection, tutoring, or enough stall.
- A modern mechanic package has no payoff density.
- A card supports the wrong half of a hybrid theme.

---

# 5.3.48 Global Emergent Replacement Logic

Replacement suggestions should prefer role/category first.

```yaml id="emergent_replacement_categories"
emergent_replacement_categories:
  commander_defined_strategy:
    - More commander-specific enablers
    - More commander protection
    - More engine redundancy
    - More payoff density
    - More role coverage inside commander plan

  commander_created_landfall:
    - More land ramp
    - More land recursion
    - More extra land drops
    - More fetch effects
    - More artifact-token payoff
    - More token payoff

  token_combat_hybrid:
    - More token makers
    - More combat payoff
    - More anthem effects
    - More board protection
    - More power-scaling payoff
    - More haste

  crime_outlaw_plot:
    - More targeted interaction
    - More crime payoffs
    - More Outlaw density
    - More theft support
    - More plot support

  offspring:
    - More Offspring cards
    - More ETB payoff
    - More token payoff
    - More sacrifice outlets
    - More small-creature support

  gift:
    - More asymmetrical payoff
    - More political support
    - More protection
    - More lower-risk value cards
    - More table-friendly interaction

  forage:
    - More Food generation
    - More graveyard setup
    - More forage payoff
    - More sacrifice payoff
    - More resource generation

  expend:
    - More ramp
    - More mana sinks
    - More expend payoff
    - More big-turn finishers
    - More card draw

  rooms_eerie:
    - More enchantment support
    - More Eerie payoff
    - More Room support
    - More enchantment tokens
    - More recursion

  treasure_tutor_chain:
    - More Treasure generation
    - More tutor chain redundancy
    - More artifact or Dragon payoff
    - More sacrifice payoff
    - More protection

  artifact_treasure_combo_value:
    - More artifact tokens
    - More artifact sacrifice
    - More artifact payoff
    - More recursion
    - More combo redundancy

  slow_alt_win:
    - More protection
    - More tutors or card selection
    - More control
    - More pillowfort
    - More setup support

  bracket_pressure:
    - Lower-bracket alternative
    - Slower tutor
    - Fairer draw engine
    - More thematic replacement
    - Less efficient but table-friendlier card

  high_synergy_low_power:
    - Same-role but better synergy
    - More engine density
    - More commander enablers
    - More bridge cards

  generically_good_wrong_shell:
    - More commander synergy
    - More primary-plan support
    - More strategy-aligned removal
    - More role-appropriate draw
```

---

# 5.3.49 Emergent Theme Scoring Model

Use additive scoring before gates and suppression.

```yaml id="emergent_scoring_model"
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

  bridge_card:
    points: 2

  high_synergy_low_power_context:
    points: 2

  legal_multiple_copy_exception:
    points: 4

  tutor_chain_piece:
    points: 2

  compact_combo_piece:
    points: 2

  bracket_pressure_card:
    points: 0
    note: Track separately from synergy score.

  fast_mana:
    points: 0
    note: Track as power-level signal.

  free_interaction:
    points: 0
    note: Track as power-level signal.
```

Risk penalties:

```yaml id="emergent_risk_penalties"
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
```

Confidence bands:

```yaml id="emergent_confidence_bands"
confidence:
  high:
    - commander-defined package exists
    - package passes primary gate
    - payoff and conversion point present
    - broad fallback suppressed
    - role in cut/replacement logic is clear

  medium:
    - package density is moderate
    - commander support exists
    - payoff exists but conversion may be unclear
    - likely secondary package

  low:
    - isolated emergent cards
    - weak commander support
    - no payoff or conversion point
    - likely manual review or minor package
```

---

# 5.3.50 Emergent Report Behavior

When emergent themes appear, include a dedicated section:

```markdown id="emergent_report_template"
## Emergent Strategy Read

Detected emergent theme:
Role:
Confidence:
Commander-defined plan:
Broad archetype suppressed:
Package density:
Enabler count:
Payoff count:
Conversion point:
Linked themes:
Bracket pressure:
Combo centrality:
Special deckbuilding rules:
Cards that look weak but are high-synergy:
Cards that are powerful but possibly wrong-shell:
Cards I would protect from cuts:
Cards worth reviewing:
Replacement categories:
```

The report should answer:

1. Is this deck’s real plan created by the commander?
2. Is this a hybrid theme that broad archetype labels would miss?
3. What resource is the deck generating?
4. What does that resource convert into?
5. Is the deck using Treasure, tokens, lands, artifacts, or graveyard cards in more than one role?
6. Is there bracket pressure without an automatic cut?
7. Is combo primary, backup, adjacent, or only a possible piece?
8. Is a slow alternate win being mistaken for turbo combo?
9. Is the deck using a multiple-copy exception?
10. Are any weak-looking cards actually essential context pieces?
11. Are any powerful cards wrong for the shell?

---

# 5.3.51 Emergent Warning Messages

Use warnings when appropriate.

## Broad Fallback Warning

```markdown id="broad_fallback_warning"
Warning: A broad archetype label may be hiding the deck’s actual commander-defined plan. Use the narrower emergent strategy for cut and replacement logic.
```

## Bracket Pressure Warning

```markdown id="bracket_pressure_warning"
Note: This card or package creates bracket pressure. That is not the same as a cut recommendation, but it may require table-fit review.
```

## Combo Centrality Warning

```markdown id="combo_centrality_warning"
Warning: This deck has combo pieces, but that does not automatically mean combo is the primary strategy. Review tutor density, protection, commander support, and speed.
```

## Slow Alternate Win Warning

```markdown id="slow_alt_win_warning"
Note: This appears to be a slow alternate win condition, not true turbo combo. It needs protection, setup, and time.
```

## High-Synergy Low-Power Warning

```markdown id="high_synergy_low_power_warning"
Note: This card looks weak by generic standards, but it appears to support the deck’s actual engine. Do not cut it solely for low raw power.
```

## Wrong Shell Warning

```markdown id="wrong_shell_warning"
Note: This is a powerful card, but it may be a wrong-shell inclusion if it does not support the commander, primary plan, or intended bracket.
```

## Multiple-Copy Exception Warning

```markdown id="multiple_copy_exception_warning"
Note: This deck appears to use a legal multiple-copy exception. Do not treat permitted repeated copies as singleton violations.
```

## Collection-Aware Replacement Warning

```markdown id="collection_aware_warning"
Note: Exact replacement suggestions should eventually be filtered through the user’s collection. Until then, recommend replacement categories first.
```

---

# 5.3.52 Final Section 5.3 Summary Rule

Emergent themes are the deck helper’s context-correction layer.

They prevent mistakes like:
- Calling commander-created landfall “generic ramp”
- Calling Treasure tutor chains “Treasure ramp”
- Calling slow alternate wins “turbo combo”
- Cutting low-power commander enablers
- Protecting powerful off-plan staples
- Missing legal multiple-copy exception decks
- Ignoring bracket pressure
- Treating combo presence as combo centrality
- Treating partner/background decks as two unrelated commanders

The helper should not ask only:

```text id="wrong_question"
What archetype is this closest to?
```

It should ask:

```text id="right_question"
What is this deck actually trying to make happen, and what cards make that plan work?
```

An emergent card should be protected from cuts when it:
- Supports a commander-defined engine
- Provides scarce package density
- Converts the deck’s main resource into a win
- Bridges typal and mechanic identities
- Is legal repeated-copy infrastructure
- Is high-synergy despite low raw power
- Supports the intended bracket or combo plan
- Is part of a refined deck’s context-dependent package

An emergent card should be reviewed as a possible cut when it:
- Is powerful but off-plan
- Raises bracket above user intent
- Is a combo piece without support or intent
- Is an enabler with no conversion point
- Is a payoff with no enablers
- Dilutes a multiple-copy exception deck
- Makes a broad fallback label steal the real strategy
- Looks good generically but does not serve the commander’s plan

Most important language rule:

```text id="emergent_language_rule"
Do not say “this card is bad” when the real issue is context. Say whether it is high-synergy, wrong-shell, bracket-pressure, unsupported, or core to the commander-defined plan.
```
