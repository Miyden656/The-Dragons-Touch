# MTG Deck Helper v0.5.6 Hotfix — Card Attribute Rules

## Purpose

This file gives the MTG Deck Helper agent a shared vocabulary for evaluating Commander cards by attributes, roles, synergy, strategy support, bracket pressure, and deck function.

The agent must classify cards based on what they generally do, using Scryfall data, Oracle text, type line, color identity, mana value, keywords, produced mana, legality data, and deck context.

The agent must not protect, cut, or judge a card because of exact card names.

This file must be read before card classification, deck review, cut suggestions, replacement suggestions, keep/protect recommendations, bracket review, commander synergy analysis, or strategy archetype classification.

For v0.5.6 hotfix, this file exists to make the role tagger strong enough to support the deeper section rule files for macro-archetypes, micro-archetypes, politics, typal themes, niche themes, fringe themes, emergent commander-defined packages, bracket review, and smarter cut/replacement logic.

This file provides card-level role tags only. It does not replace the deeper section files. The section files decide whether a deck is truly a macro-archetype, micro-archetype, political strategy, typal strategy, niche/fringe theme, or emergent commander-defined package.

---

# Core Principles

## 1. Do not use exact card-name rules

Do not protect, cut, or judge a card because its name appears on a hardcoded list.

Bad logic:

- “Always keep Gravecrawler.”
- “Always cut Panharmonicon.”
- “Always protect Sol Ring.”
- “Always cut this creature because it has low power.”

Good logic:

- “This card has recursion and tribal dependency.”
- “This card is a synergy piece because it doubles triggered abilities.”
- “This card is ramp because it produces extra mana.”
- “This card supports typal density because the deck has a real tribe.”
- “This card is manual review because it is unknown/custom but has recognizable role text.”

The agent may mention known card examples in explanations, but classification must come from card text, role tags, commander context, and deck context.

---

## 2. A card can have multiple roles

Many cards should receive more than one tag.

Examples:

- A creature that draws cards when creatures die may be: `creature`, `card_draw`, `repeatable_card_draw`, `death_trigger_payoff`, `aristocrat_payoff_possible`, `micro_archetype_support`, `commander_synergy_possible`.
- A Dragon that deals damage when Dragons are damaged may be: `creature`, `tribal_payoff`, `typal_damage_trigger`, `dragon_typal`, `damage_payoff`, `synergy_piece`, `typal_support`, `commander_synergy_possible`.
- A card that untaps target land may be: `untap_ramp`, `land_untapper`, `mana_engine_support_possible`, `commander_synergy_possible` if the commander or deck uses tap abilities or mana engines.
- A low-text Goblin in a Goblin commander deck may be: `creature`, `tribal_body`, `typal_density`, `goblin_typal`, `typal_density_piece`, and possibly `attack_body` or `sacrifice_body` if deck context supports it.

The agent should prefer rich role tagging over single-label classification.

---

## 3. Unknown does not mean bad

If a card cannot be confidently validated or parsed, tag it as `manual_review`.

Do not automatically cut unknown, custom, unusual, niche, old-template, or complex cards.

If an unknown/custom card contains recognizable role text, keep the parsed role tags and add `manual_review`.

Examples:

- Unknown card says “Whenever you gain life, each opponent loses 1 life.” Tags: `lifegain_payoff`, `lifedrain_payoff`, `group_slug`, `manual_review`.
- Unknown card says “Untap target land.” Tags: `untap_ramp`, `land_untapper`, `mana_engine_support_possible`, `manual_review`.
- Unknown card says “Sacrifice another creature: Search your library for a creature card.” Tags: `pod_effect`, `creature_tutor`, `sacrifice_as_cost`, `manual_review`.

Manual review is not a cut recommendation.

---

## 4. Commander context matters

The same card may be weak in one deck and excellent in another.

The agent should consider commander color identity, mana value, card type, creature type, triggered abilities, activated abilities, static abilities, combat plan, graveyard plan, token plan, sacrifice plan, spellcasting plan, tribal plan, artifact plan, enchantment plan, lifegain/lifedrain plan, toughness/defender plan, blink/ETB plan, activated-ability plan, tap/untap plan, Equipment/Aura/Voltron plan, political axis, niche/fringe mechanic support, commander-created resources, and commander protection needs.

A card should be protected because it supports the deck plan, not because it is generically popular.

---

## 5. Do not treat card type as a complete explanation

A card being a creature, artifact, enchantment, instant, sorcery, battle, planeswalker, or land is not enough.

The agent should ask:

- What does this card do?
- What role does it fill?
- What deck plan does it support?
- Is it an enabler, payoff, protection piece, interaction piece, resource engine, or finisher?
- Is it redundant with better cards?
- Is it only good with unsupported synergy?
- Is it high mana value without enough payoff?
- Is it weak alone but important to the deck’s engine?
- Is it a good card in the wrong shell?
- Is it a bracket modifier rather than strategy evidence?
- Is it a package card requiring manual review?

---

## 6. Cut suggestions require role classification first

Before suggesting cuts, the agent must classify each card by role tags.

Do not mark a card as `no useful role`, `low impact`, `off-plan`, `replaceable`, `recommended cut`, or `high-confidence cut` until role classification is complete.

A narrow card may be essential if it supports the commander, primary strategy, secondary strategy, resource engine, or win condition.

---

## 7. v0.5.6 cut language must be careful

Use careful phrasing:

- Possible cut
- Review candidate
- Replaceable but playable
- Low synergy in this shell
- Good card, wrong shell
- Needs more support
- Manual review before cutting
- Cut confidence: Low / Medium / High

Avoid reckless phrasing:

- This card is bad
- Always cut this
- Never cut this
- Strictly worse
- Useless
- Trash

The agent should separate possible cuts from recommended cuts.

---

## 8. Avoid over-tagging unrelated cards

Role tags should come from clear card text, type line, commander context, or deck density.

Do not create major strategy labels from weak evidence.

Safeguards:

- Do not call a deck tribal because it has one creature of a type.
- Do not call a deck political because it has one group draw/goad/vote card.
- Do not call a deck Group Hug because it has one symmetrical resource card.
- Do not call a deck Group Slug because it has one punisher card.
- Do not call a deck Chaos because it has one wheel or random card.
- Do not call a deck true turbo combo because it has one alternate win condition, one compact combo piece, or one high-power value card.
- Do not call an untap effect ramp unless it can realistically untap mana or value permanents.
- Do not call a simple creature no-role until checking typal density, sacrifice body, token body, attack body, commander-required density, and niche/fringe/emergent support.

When in doubt, use lower confidence and `manual_review` rather than forcing a high-confidence strategy label.

---

## 9. Role tags feed strategy scoring but do not decide strategy alone

Tags such as `typal_support`, `political_card`, `niche_theme_support`, `fringe_theme_support`, `emergent_theme_support`, and `macro_archetype_support` are evidence, not final strategy labels.

The strategy system must still check commander support, density, enabler/payoff balance, win path, support package status, suppression rules, bracket/power context, and user intent.

---

## 10. Bracket modifiers are separate from synergy evidence

Fast mana, free interaction, Game Changers, efficient tutors, bracket pressure, and high bracket pressure are power-level modifiers.

They do not increase strategy synergy scores by themselves.

Examples:

- A fast mana card is ramp and bracket pressure, but it does not prove Ramp-Control.
- A Game Changer is a bracket signal, not proof of the deck’s strategy.
- An efficient tutor is consistency and bracket pressure, not proof of Combo unless combo support exists.
- A slow alternate win condition is not true turbo combo unless the true turbo gate passes.
- A high-power value piece may be correct in the deck without being a combo card.

---

# Required Input Sources

The agent should classify cards using these sources when available:

1. Scryfall card name validation
2. Scryfall Oracle text
3. Scryfall type line
4. Scryfall mana cost
5. Scryfall mana value
6. Scryfall color identity
7. Scryfall keywords
8. Scryfall produced mana, if available
9. Scryfall legality data, if available
10. Commander identity and text
11. Full decklist
12. User-provided category labels, if present
13. User-stated bracket or power target, if present
14. Strategy archetype rules file, if present
15. Cut replacement rules file, if present
16. Bracket rules file, if present
17. Section 1 macro-archetype rules, if present
18. Section 2 micro-archetype rules, if present
19. Section 3 politics rules, if present
20. Section 4 typal rules, if present
21. Section 5.1 niche rules, if present
22. Section 5.2 fringe rules, if present
23. Section 5.3 emergent rules, if present
24. This `card_attribute_rules.md` file

---

# Classification Output Expectations

Each card should receive these fields when possible:

## Required fields

- card_name
- mana_value
- card_types
- color_identity
- detected_roles
- confidence
- short_reason

## Recommended fields

- commander_synergy_score
- deck_plan_fit
- cut_risk
- cut_confidence
- cut_type
- keep_reason
- protected_reason
- replacement_category
- manual_review_reason
- possible_false_positive_warning
- support_density_note
- strategy_relevance_note
- strategy_layer
- typal_role
- political_role
- niche_or_fringe_role
- emergent_role
- bracket_modifier

Example:

```json
{
  "card_name": "Example Card",
  "mana_value": 3,
  "card_types": ["Creature"],
  "color_identity": ["B", "G"],
  "detected_roles": ["creature", "sacrifice_outlet", "graveyard_enabler"],
  "strategy_layer": ["micro_archetype_support", "support_package_card"],
  "typal_role": [],
  "political_role": [],
  "niche_or_fringe_role": [],
  "emergent_role": [],
  "bracket_modifier": [],
  "confidence": "medium",
  "short_reason": "Creature can sacrifice permanents and supports graveyard/death-trigger plans.",
  "commander_synergy_score": "high",
  "deck_plan_fit": "supports primary sacrifice-recursion plan",
  "cut_risk": "low",
  "cut_confidence": "low",
  "protected_reason": "Supports the main resource engine."
}
```

---

# Confidence Scale

## High confidence

Use when the card text clearly matches one or more role tags and the deck context supports the classification.

## Medium confidence

Use when the card text likely matches a role, but deck context, support density, or parser output is incomplete.

## Low confidence

Use when classification depends heavily on context, hidden synergy, user intent, old wording, custom categories, unusual mechanics, or manual judgment.

Low-confidence cards should usually be placed into manual review instead of recommended cuts.

---

# Strategy-Layer Tags

These tags tell the later strategy system where a card’s role belongs.

They should not become primary strategy labels by themselves.

## macro_archetype_support

A card that supports a broad macro-archetype such as Aggro, Midrange, Control, Combo, Stax, Tempo, Ramp/Big Mana, Toolbox, or Engine/Synergy Value.

Use when the card clearly supports broad structure:

- Aggro support: efficient attackers, haste, anthems, evasion, extra combat
- Control support: removal, board wipes, counterspells, pillowfort, inevitability
- Ramp support: ramp, mana doublers, mana sinks, high-MV payoff
- Stax support: tax effects, hard restrictions, parity-breaking support
- Toolbox support: tutors, modal cards, silver bullets, recursion
- Combo support: compact combo pieces, tutors, protection, fast mana

Do not use this tag to override a narrower commander-defined plan.

## micro_archetype_support

A card that supports a mechanical micro-archetype such as Aristocrats, Voltron, Spellslinger, Blink, Landfall, Reanimator, Artifacts, Enchantress, Tokens, Counters, Lifegain, Treasure, Exile Matters, Saboteur, Storm, Vehicles, Equipment, Auras, or X-Spells.

## typal_support

A card that supports a creature type strategy through density, payoff, protection, recursion, token creation, tutoring, cost reduction, combat, sacrifice, or bridge synergy.

Do not use this tag as proof that typal is primary. Typal primary requires Section 4 density and payoff gates.

## niche_theme_support

A card that supports a narrow but legitimate niche theme such as Energy, Gates, Shrines, Venture, Initiative, Vehicles, Mill, Infect, Toxic, Dice, Coin Flips, Mutate, Cast-from-Exile, Adventures, Foretell, Suspend, Cascade, Discover, Food, Blood, Clues, or similar themes.

## fringe_theme_support

A card that supports a fragile, low-support, legality-sensitive, user-intent-dependent, or table-context-dependent theme.

Most fringe support should be manual review unless user intent is known.

## emergent_theme_support

A card that supports a modern hybrid package, commander-created strategy, resource conversion engine, or context-specific emergent plan.

Examples:

- Commander-created landfall
- Token Combat / Go-Wide-Go-Tall Hybrid
- Crime/Outlaw package
- Offspring ETB token value
- Gift political value
- Forage Food/graveyard engine
- Expend mana-spent engine
- Rooms/Eerie enchantment engine
- Manifest Dread face-down/graveyard bridge
- Survival tapped-creature payoff
- Treasure tutor chain
- Artifact/Treasure combo-value

## commander_defined_support

A card that directly supports a strategy created or heavily enabled by the commander.

Examples:

- Land ramp in a commander-created landfall deck
- Artifact payoffs for commander-created artifact tokens
- Untap support for tap commander
- Attack safety for attack-trigger commander
- Low-cost bodies for commanders requiring creature density
- Lifegain sources/payoffs for lifegain commanders
- Wheels or forced draw for draw-punisher commanders

## support_package_card

A card that supports the deck’s main engine but is not a payoff or win condition by itself.

Examples:

- Ramp in high-MV typal decks
- Sacrifice fodder in aristocrats
- Enablers for venture, energy, or mutate
- Political protection for slower table-incentive decks
- Topdeck manipulation for clash or saboteur topdeck damage

## minor_package_card

A card that belongs to a small package that may not be central to the deck.

Use when:

- There are 1-3 related cards.
- The card has real synergy but low density.
- The package should not define the deck.
- Cut review should ask whether the user wants the package preserved.

## manual_review_package_card

A card that belongs to a package that cannot be judged confidently without user intent, support density, legality/table context, or missing package pieces.

Common sources:

- Fringe mechanics
- Rule Zero cards
- Political cards
- Meta hate
- Isolated combo pieces
- Unclear custom/unknown card text
- Unsupported niche payoffs
- Package-dependent cards

Manual review is not a cut recommendation.

---

# Core Role Tags

## mana_source

A card that can produce mana or function as a mana source.

Includes lands, mana rocks, mana dorks, Treasure producers, rituals, cost reducers, mana doublers, land-search cards, and effects that untap lands or mana permanents.

Detection patterns:

- “Add {mana}”
- “Search your library for a land”
- “Untap target land”
- “Costs less to cast”
- “Whenever you tap a land for mana, add”
- “Create a Treasure token”

Related tags: `ramp`, `mana_rock`, `mana_dork`, `treasure_maker`, `ritual`, `cost_reducer`, `mana_doubler`, `land_ramp`, `untap_ramp`, `mana_engine_support`.

## ramp

A card that increases the player’s available mana over time.

Includes land ramp, mana rocks, mana dorks, Treasure generation, cost reduction, mana doubling, permanent-based mana acceleration, and untap-ramp when valid tap targets exist.

Detection patterns:

- “Search your library for a basic land”
- “Put a land card onto the battlefield”
- “Add one mana of any color”
- “Create a Treasure token”
- “Spells you cast cost {1} less”
- “Whenever you tap a land for mana, add one mana”
- “Untap target land” with relevant mana or utility land context

Subtags: `land_ramp`, `artifact_ramp`, `creature_ramp`, `treasure_ramp`, `cost_reducer`, `burst_ramp`, `mana_doubler`, `untap_ramp`.

Review notes:

- One-shot Treasure or ritual effects should be tagged as ramp, but may be lower-value in casual Commander unless they support a burst/combo plan.
- Cost reducers should be evaluated based on how many cards they affect.
- Ramp that supports an expensive commander should receive `commander_synergy_possible`.
- Untap-ramp must be context checked. It is strongest with lands/artifacts/creatures that tap for more than one mana or meaningful value.
- Fast mana may also receive `bracket_pressure`, but bracket pressure is not strategy evidence by itself.

## untap_ramp

A card that increases available mana or reusable value by untapping lands, artifacts, creatures, commanders, or permanents that tap for mana or other resources.

Detection patterns:

- “Untap target land”
- “Untap up to one target land”
- “Untap target permanent”
- “Untap another target permanent”
- “Untap target artifact”
- “Untap target creature” when the deck has mana dorks, tap commanders, or tap-value creatures
- “Whenever this becomes tapped, untap...”
- “Untap all lands you control”
- “Untap all artifacts you control”
- “Untap each permanent you control”

Subtags: `land_untapper`, `permanent_untapper`, `artifact_untapper`, `creature_untapper`, `commander_untapper`, `mana_engine_support`, `tap_ability_engine`.

Review notes:

- Count as ramp/support when the deck has mana doublers, bounce lands, lands that tap for multiple mana, mana rocks, mana dorks, artifacts that tap for value, or commander activated abilities.
- Do not treat untap-ramp as full ramp if the deck lacks valuable tap targets.
- Add `commander_synergy_possible` when the commander has a tap ability, cares about tapped permanents, or enables mana engines.
- Add `combo_piece_possible` only when paired with repeatable mana production, cost reduction, or loops. Do not assume combo by default.

## land_untapper

A card that untaps one or more lands.

Detection patterns:

- “Untap target land”
- “Untap up to one target land”
- “Untap all lands you control”
- “Untap each land you control”
- “Whenever this becomes tapped, untap target land”

Review notes:

- Stronger with lands that produce more than one mana, land auras, mana doublers, utility lands, and commanders that care about lands becoming tapped or untapped.
- If the deck only uses normal one-mana lands and has no land synergy, classify as support but not necessarily strong ramp.

## permanent_untapper

A card that untaps one or more permanents of flexible types.

Detection patterns:

- “Untap target permanent”
- “Untap another target permanent”
- “Untap each permanent you control”
- “Untap up to X target permanents”

Review notes:

- Permanent untappers may support lands, artifacts, creatures, commanders, and utility engines.
- Check for tap abilities across the deck before judging role strength.
- These cards often belong in manual review if the parser cannot identify tap targets.

## artifact_untapper

A card that untaps artifacts or improves repeated artifact activation.

Detection patterns:

- “Untap target artifact”
- “Untap all artifacts you control”
- “Whenever an artifact becomes tapped, untap...”
- “Untap another target artifact”

Review notes:

- Artifact untappers are ramp/support when the deck has mana rocks, artifact creatures with tap abilities, Vehicles, artifacts that tap for value, or artifact-combo engines.
- Do not tag `artifact_untapper` as a primary strategy by itself.

## mana_engine_support

A card that does not directly produce mana by itself but improves a mana engine, repeatable tap engine, or resource-producing permanent.

Detection patterns:

- Untaps mana-producing permanents
- Reduces activation costs
- Copies activated abilities that produce mana or resources
- Increases mana produced by lands, creatures, or artifacts
- Rewards permanents becoming tapped or untapped
- Supports commanders or permanents with tap abilities

Review notes:

- This tag protects cards that make the deck’s resource engine work even if they look low-impact alone.
- Use Medium or Low confidence if the deck’s tap targets or mana engine pieces are unclear.
- Do not over-tag generic untap or vigilance cards as mana_engine_support unless there are actual mana/value tap targets.

## card_draw

A card that directly draws cards or creates repeatable card advantage.

Detection patterns:

- “Draw a card”
- “Draw two cards”
- “Whenever you... draw”
- “At the beginning of your upkeep, draw”
- “Whenever a creature dies, draw”
- “Whenever you cast... draw”

Subtags: `one_shot_draw`, `repeatable_draw`, `conditional_draw`, `combat_damage_draw`, `death_trigger_draw`, `spellcast_draw`, `creature_cast_draw`, `repeatable_card_draw`.

Review notes:

- Looting, rummaging, impulse draw, and card selection are not always true card advantage.
- Forced opponent draw should not be treated as card_draw for the deck pilot unless it also benefits the pilot.

## repeatable_card_draw

A card that can draw cards more than once over multiple turns or repeated triggers.

Detection patterns:

- “Whenever...” draw triggers
- Activated ability that draws cards
- “At the beginning of...” draw effects
- “Whenever you activate/cast/sacrifice/attack, draw”

Review notes:

- Repeatable draw should be valued more highly than one-shot cantrips.
- If the trigger condition matches the commander or main strategy, increase commander synergy score.

## card_selection

A card that improves card quality without necessarily increasing total card count.

Detection patterns:

- “Scry”
- “Surveil”
- “Look at the top”
- “Put one into your hand and the rest”
- “Discard a card, then draw a card”
- “Draw a card, then discard a card”

Subtags: `scry`, `surveil`, `loot`, `rummage`, `impulse_selection`, `topdeck_manipulation`.

## impulse_draw

A card that exiles cards and allows them to be played temporarily.

Detection patterns:

- “Exile the top card”
- “You may play that card this turn”
- “Until the end of your next turn, you may play”
- “You may cast that card from exile”

Review notes:

- Stronger in low-curve decks.
- Weaker if the deck has many expensive cards or restrictive timing.
- Also consider `cast_from_exile` if the card cares about or enables casting from exile.

## targeted_removal

A card that removes one or more specific opposing permanents or spells.

Detection patterns:

- “Destroy target”
- “Exile target”
- “Return target permanent”
- “Counter target spell”
- “Target creature gets -X/-X”
- “Fight target creature”
- “Deals damage to target creature”
- “Target player sacrifices”

Subtags: `creature_removal`, `artifact_removal`, `enchantment_removal`, `planeswalker_removal`, `land_removal`, `graveyard_removal`, `stack_interaction`, `bounce`, `edict`, `fight_removal`, `damage_removal`, `negotiated_removal`, `crime_enabler` if it targets an opponent, their permanent, or a card in their graveyard.

Review notes:

- Removal attached to creatures may also be ETB synergy.
- Targeted interaction may be protected in Crime decks because it fuels the engine.

## repeatable_removal

A card that can repeatedly remove, damage, bounce, exile, fight, tap down, or otherwise neutralize opposing permanents.

Detection patterns:

- Activated ability that destroys, exiles, bounces, fights, taps, or deals repeatable damage
- Triggered ability that repeatedly removes or controls permanents
- “Whenever you activate/cast/attack, destroy/exile/tap” repeated engine

## board_wipe

A card that removes many permanents at once.

Detection patterns:

- “Destroy all”
- “Exile all”
- “Each creature”
- “All creatures get”
- “For each creature”
- “Sacrifice all”
- “Return all”

Subtags: `creature_board_wipe`, `artifact_board_wipe`, `enchantment_board_wipe`, `asymmetrical_board_wipe`, `damage_based_wipe`, `toughness_based_wipe`, `exile_wipe`, `bounce_wipe`, `board_reset`.

## protection

A card that protects the commander, important permanents, or the board.

Detection patterns:

- “Hexproof”
- “Indestructible”
- “Phase out”
- “Protection from”
- “Regenerate”
- “Prevent all damage”
- “Counter target spell that targets”
- “Permanents you control gain”
- “Creatures you control gain”

Subtags: `commander_protection`, `board_protection`, `instant_speed_protection`, `protection_static`, `counter_protection`, `blink_protection`, `phase_protection`, `voltron_protection`, `typal_protection`.

## recursion

A card that returns cards from the graveyard or allows them to be cast from the graveyard.

Detection patterns:

- “Return target card from your graveyard”
- “Return target creature card”
- “You may cast this card from your graveyard”
- “Escape”
- “Flashback”
- “Unearth”
- “Disturb”
- “Aftermath”
- “Retrace”
- “Whenever a creature dies, return”
- “At the beginning of your end step, return”

Subtags: `creature_recursion`, `permanent_recursion`, `spell_recursion`, `self_recursion`, `repeatable_recursion`, `one_shot_recursion`, `graveyard_casting`, `typal_recursion`, `typal_reanimation`.

## graveyard_enabler

A card that puts cards into the graveyard intentionally.

Detection patterns:

- “Mill”
- “Surveil”
- “Discard”
- “Sacrifice”
- “Put the top cards of your library into your graveyard”
- “Search your library for a card and put it into your graveyard”

Subtags: `self_mill`, `surveil`, `discard_outlet`, `sacrifice_outlet`, `tutor_to_graveyard`, `manifest_dread`.

## reanimation

A card that returns creatures or permanents directly from the graveyard to the battlefield.

Detection patterns:

- “Return target creature card from your graveyard to the battlefield”
- “Put target creature card from a graveyard onto the battlefield”
- “Return it to the battlefield”
- “Whenever this creature dies, return it to the battlefield”

Subtags: `one_shot_reanimation`, `repeatable_reanimation`, `mass_reanimation`, `opponent_graveyard_reanimation`, `typal_reanimation`.

## token_maker

A card that creates creature or noncreature tokens.

Detection patterns:

- “Create a token”
- “Create X tokens”
- “Create a Treasure token”
- “Create a Food token”
- “Create a Clue token”
- “Create a Blood token”
- “Create a Map token”
- “Create a copy”

Subtags: `creature_token_maker`, `treasure_maker`, `food_maker`, `clue_maker`, `blood_maker`, `map_maker`, `copy_token_maker`, `repeatable_token_maker`, `death_trigger_token_maker`, `combat_token_maker`, `token_body`, `typal_token_maker`.

## token_body

A token or token-making effect whose main value is creating bodies for combat, sacrifice, convoke, tapping, typal density, or death triggers.

Detection patterns:

- “Create a [creature] token”
- “Create X creature tokens”
- Repeated token production
- Token type matches commander tribe or payoff package

## sacrifice_outlet

A card that allows the player to sacrifice permanents.

Detection patterns:

- “Sacrifice a creature:”
- “Sacrifice another creature:”
- “Sacrifice an artifact:”
- “Sacrifice a permanent:”
- “As an additional cost to cast this spell, sacrifice”
- “Whenever you sacrifice”

Subtags: `free_sacrifice_outlet`, `mana_sacrifice_outlet`, `card_draw_sacrifice_outlet`, `damage_sacrifice_outlet`, `aristocrat_sacrifice_outlet`, `artifact_sacrifice_outlet`, `creature_sacrifice_outlet`, `sacrifice_as_cost`, `pod_effect`.

## sacrifice_as_cost

A card that requires sacrificing a creature or permanent as part of the cost to activate or cast an effect.

Detection patterns:

- “As an additional cost to cast this spell, sacrifice...”
- “Sacrifice another creature:”
- “Sacrifice a creature:”
- “Sacrifice an artifact:”
- “Sacrifice a permanent:”

Review notes:

- Sacrifice as cost can be an enabler, not merely a drawback.
- It supports aristocrats, death triggers, recursion, graveyard setup, and pod chains.

## free_sacrifice_outlet

A sacrifice outlet that does not require mana to activate.

Detection patterns:

- “Sacrifice a creature:”
- “Sacrifice another creature:”
- Activation cost has no mana symbol

## sacrifice_body

A creature or token that is valuable because it can be sacrificed, recur, die profitably, or trigger death/sacrifice payoffs.

Detection patterns:

- Cheap creature body in aristocrats/sacrifice decks
- Self-recurring creature
- Token body in a sacrifice deck
- Creature with death trigger or expendable ETB value

Requires deck context: sacrifice outlets, death triggers, recursion, or aristocrat payoffs.

## death_trigger_payoff

A card that rewards creatures or permanents dying.

Detection patterns:

- “Whenever a creature dies”
- “Whenever another creature dies”
- “Whenever a creature you control dies”
- “Whenever an artifact is put into a graveyard”
- “Whenever you sacrifice”
- “Whenever one or more creatures die”

Subtags: `aristocrat_payoff`, `death_draw`, `death_drain`, `death_token_maker`, `death_treasure_maker`, `death_counter_payoff`, `typal_death_payoff`.

## aristocrat_payoff

A card that drains, damages, draws, creates resources, or otherwise rewards sacrificing or creatures dying.

Detection patterns:

- “Whenever another creature dies, each opponent loses”
- “Whenever you sacrifice”
- “Whenever a creature you control dies”
- “Target opponent loses life and you gain life”
- “Each opponent loses 1 life”

## lifegain

A card that gains life or rewards life gain.

Detection patterns:

- “You gain life”
- “Gain X life”
- “Whenever you gain life”
- “Lifelink”
- “Each opponent loses life and you gain life”

Subtags: `lifegain_source`, `lifegain_payoff`, `drain`, `lifelink`, `life_total_matters`.

## lifegain_payoff

A card that rewards the player for gaining life.

Detection patterns:

- “Whenever you gain life”
- “If you would gain life”
- “You gain twice that much life instead”
- “Whenever you gain life, put a +1/+1 counter”
- “Whenever you gain life, draw a card”
- “Whenever you gain life, each opponent loses life”
- “At the beginning of your end step, if you gained life this turn”

Subtags: `life_gain_doubler`, `life_counter_payoff`, `life_token_payoff`, `life_draw_payoff`, `lifedrain_payoff`, `alternate_win_condition`, `typal_lifegain_payoff`.

## lifedrain_payoff

A card that rewards life loss, life gain, or life exchange patterns by draining opponents.

Detection patterns:

- “Each opponent loses life and you gain life”
- “Whenever you gain life, each opponent loses”
- “Whenever an opponent loses life, you gain”
- “Whenever an opponent loses life”
- “Each opponent loses X life”
- “Target opponent loses life and you gain life”

## life_total_manipulation

A card that changes, doubles, exchanges, sets, or weaponizes life totals.

Detection patterns:

- “Exchange life totals”
- “Target player's life total becomes”
- “Your life total becomes”
- “Each player's life total becomes”
- “You gain twice that much life instead”
- “Half your life total”
- “Pay life”
- “Lose half your life”
- “Equal to the difference between life totals”

Subtags: `life_exchange`, `life_payment`, `life_total_setting`.

## drain

A card that causes opponents to lose life while you gain life.

Detection patterns:

- “Each opponent loses life and you gain life”
- “Target opponent loses life and you gain life”
- “Whenever... each opponent loses 1 life”

## damage_payoff

A card that rewards damage being dealt.

Detection patterns:

- “Whenever a source you control deals damage”
- “Whenever this creature deals combat damage”
- “Whenever a creature is dealt damage”
- “Whenever you deal noncombat damage”

Subtags: `combat_damage_payoff`, `noncombat_damage_payoff`, `creature_damage_payoff`, `typal_damage_trigger`.

## combat_payoff

A card that rewards attacking or dealing combat damage.

Detection patterns:

- “Whenever this creature attacks”
- “Whenever one or more creatures attack”
- “Whenever a creature you control deals combat damage”
- “Whenever this creature deals combat damage to a player”
- “Whenever you attack”

Subtags: `attack_trigger`, `combat_damage_trigger`, `goad_payoff`, `extra_combat_possible`, `evasion_payoff`, `typal_combat_payoff`, `typal_attack_trigger`.

## combat_damage_trigger

A card with an effect that triggers when a creature deals combat damage to a player, opponent, or any target.

Detection patterns:

- “Whenever this creature deals combat damage to a player”
- “Whenever equipped creature deals combat damage”
- “Whenever one or more creatures you control deal combat damage”
- “Whenever a creature you control deals combat damage to a player”

## attack_body

A creature or token whose main value is providing an attacker for go-wide combat, attack triggers, combat-damage triggers, battalion-style effects, or tap/combat pressure.

Requires deck context.

## combat_reset

A card that removes creatures from combat, untaps attacking creatures, prevents combat damage, or lets creatures attack safely while avoiding normal combat consequences.

Detection patterns:

- “Remove target attacking creature from combat”
- “Untap all creatures you control”
- “Untap target attacking creature”
- “Prevent all combat damage”
- “After this combat phase, there is an additional combat phase”
- “At end of combat, untap”
- “Creatures you control gain vigilance”
- “Attacking doesn't cause creatures you control to tap”

## attack_safety

A card that makes attacking safer or reduces the downside of attacking.

Detection patterns:

- “Attacking doesn't cause creatures to tap”
- “Creatures you control have vigilance”
- “Prevent all combat damage that would be dealt to attacking creatures”
- “Remove attacking creature from combat”
- “Untap attacking creature”
- “Creatures you control gain indestructible until end of turn”
- “Creatures you control gain protection until end of turn”
- “Whenever a creature attacks, untap it”

## evasion

A card or creature with keywords that make blocking difficult.

Detection patterns:

- Flying
- Menace
- Trample
- Unblockable
- Shadow
- Skulk
- Fear
- Intimidate
- Horsemanship
- “Can’t be blocked”
- “Can’t be blocked except by”

## anthem

A card that increases the stats of multiple creatures.

Detection patterns:

- “Creatures you control get +1/+1”
- “[Creature type] creatures you control get”
- “Tokens you control get”
- “Other creatures you control get”

Subtags: `tribal_anthem`, `typal_lord`, `token_anthem`, `team_pump`, `counter_anthem`.

## counter_synergy

A card that creates, doubles, moves, or rewards counters.

Detection patterns:

- “Put a +1/+1 counter”
- “Double the number of counters”
- “Proliferate”
- “Whenever one or more counters”
- “Enters with counters”
- “For each counter”

Subtags: `plus_one_counter_source`, `plus_one_counter_payoff`, `proliferate`, `counter_doubler`, `loyalty_counter_synergy`, `charge_counter_synergy`, `oil_counter_synergy`, `typal_counter_payoff`.

## blink

A card that exiles and returns permanents, usually to reuse ETB abilities or protect creatures.

Detection patterns:

- “Exile target creature you control, then return it”
- “Exile any number of creatures you control, then return”
- “At the beginning of the next end step, return”

Subtags: `one_shot_blink`, `repeatable_blink`, `mass_blink`, `blink_protection`, `etb_reuse`.

## mass_blink

A card that exiles and returns multiple creatures or permanents.

Detection patterns:

- “Exile any number of creatures you control, then return them”
- “Exile all creatures you control, then return them”
- “Exile each creature you control, then return”
- “Exile any number of target creatures”
- “Return those cards to the battlefield”
- “At the beginning of the next end step, return them”

## ETB_synergy

A card that has or rewards enters-the-battlefield abilities.

Detection patterns:

- “When this enters”
- “Whenever another creature enters”
- “Whenever a permanent enters”
- “If a triggered ability of a permanent entering causes”
- “Triggers an additional time”

Subtags: `etb_effect`, `etb_payoff`, `etb_doubler`, `blink_synergy`, `token_etb_payoff`, `typal_etb_payoff`.

## synergy_piece

A card that amplifies a common deck action or makes other cards stronger.

Detection patterns:

- “If a triggered ability... triggers, it triggers an additional time”
- “Copy target triggered ability”
- “Copy target activated ability”
- “Double the number of”
- “Twice that many”
- “Whenever you cast”
- “Whenever you sacrifice”
- “Whenever a creature enters”
- “Whenever a creature dies”
- “Creatures you control have”
- “Tokens you control have”

## commander_synergy_possible

A card that appears to support the commander’s likely game plan.

This tag means “check commander fit.” It does not automatically mean the card should be protected.

## win_condition_possible

A card that can realistically help close the game.

Detection patterns:

- “Each opponent loses”
- “You win the game”
- “Double damage”
- “Extra combat”
- “Creatures you control get +X/+X”
- “Drain each opponent”
- “Whenever... each opponent loses life”
- “Create many tokens”
- “Combo-piece text”
- “Mass reanimation”
- “Overrun-style effect”

Subtags: `alternate_win_condition`, `slow_alt_win_condition`, `visible_win_condition`, `combat_finisher`, `drain_finisher`, `combo_finisher`, `token_finisher`, `aristocrat_finisher`, `commander_damage_finisher`, `toughness_combat_finisher`, `draw_punisher_finisher`.

---

# Activated Ability and Tap Engine Roles

## activated_ability_payoff

A card that rewards activated abilities being activated or makes activated abilities more valuable.

Detection patterns:

- “Whenever you activate an ability”
- “Activated abilities you activate”
- “Copy target activated ability”
- “Whenever an ability of [source] is activated”
- “The first activated ability you activate each turn”

## activated_ability_cost_reduction

A card that reduces the cost of activated abilities.

Detection patterns:

- “Activated abilities you activate cost {X} less”
- “This effect can’t reduce the mana in that cost to less than one mana”
- “Abilities of creatures/artifacts you control cost less to activate”

## power_based_cost_reduction

A card that reduces activated ability costs based on creature power or another power-like scaling value.

Detection patterns:

- “Costs {X} less to activate, where X is this creature’s power”
- “Reduce the cost by the greatest power among creatures you control”
- Power-based activation reduction

Review notes:

- Important for Agatha-style activated ability engines.
- Check power scaling, +1/+1 counters, Equipment, Auras, and go-tall support.

## mana_sink

A card that converts excess mana into value, damage, cards, tokens, counters, or a win condition.

Detection patterns:

- Repeated activated ability with mana cost
- X-spell
- “{X}:”
- Level up
- Monstrosity
- Firebreathing-style pump
- Token production ability
- Draw/discard activated ability
- Commander activated ability with meaningful scaling

## pinger

A card with a repeatable damage-dealing tap or activated ability.

Detection patterns:

- “{T}: This deals 1 damage”
- “Deals damage to any target”
- “Deals damage to target creature or player”
- “Whenever this becomes tapped, it deals damage”

## tap_ability_engine

A card that creates value from tapping or untapping permanents.

Detection patterns:

- “{T}:” activated abilities
- “Whenever this becomes tapped”
- “Whenever a creature becomes tapped”
- “Tap an untapped creature you control:”
- “Untap target permanent”
- “Whenever you untap”

---

# Pod / Creature Chain Roles

## pod_effect

A card that sacrifices or converts a creature into another creature from library or battlefield.

Detection patterns:

- “Sacrifice another creature: Search your library for a creature card”
- “Sacrifice a creature: Search your library for a creature card”
- “Mana value equal to 1 plus the sacrificed creature’s mana value”
- “Mana value less than or equal to”
- “Put that card onto the battlefield”

## creature_tutor

A card that searches for creature cards.

Detection patterns:

- “Search your library for a creature card”
- “Reveal a creature card”
- “Put a creature card into your hand”
- “Put a creature card onto the battlefield”
- “Search for a creature card with mana value...”

## creature_chain

A package that uses creature tutors, pod effects, recursion, or ETB lines to move through a creature curve or toolbox.

Detection patterns:

- Pod-style mana value progression
- Creature tutors with repeated activation
- Recursion plus sacrifice/tutor loop
- ETB toolbox chain
- Commander untap support for repeated chain activations

## etb_toolbox

A package of ETB creatures used as searchable answers or value pieces.

Detection patterns:

- Creature tutor effects
- Pod effects
- Multiple ETB creatures that remove, draw, ramp, or recur
- Blink or recursion support

## untap_commander_support

A card that untaps or reuses the commander’s activated ability.

Detection patterns:

- “Untap target creature”
- “Untap target permanent”
- “Untap another target permanent”
- “Whenever this becomes tapped, untap”
- “You may activate this ability an additional time”

---

# Equipment / Aura / Voltron Roles

## equipment_synergy

A card that uses, searches, attaches, or rewards Equipment.

Detection patterns:

- “Attach target Equipment”
- “Equip abilities cost”
- “Search your library for an Equipment”
- “Whenever equipped creature”
- “For each Equipment attached”
- “Living weapon”
- “For Mirrodin!”

Subtags: `equipment_tutor`, `equipment_cost_reducer`, `equip_cost_reduction`, `auto_equip`, `voltron_support`, `equipment_payoff`, `attachment_synergy`, `artifact_combat`.

## aura_synergy

A card that uses or rewards Auras.

Detection patterns:

- “Enchant creature”
- “Whenever an Aura becomes attached”
- “Aura spells you cast cost less”
- “Return Aura”
- “Totem armor”
- “Bestow”

Subtags: `aura_payoff`, `aura_recursion`, `voltron_support`, `enchantment_synergy`, `attachment_synergy`.

## equipment_payoff

A card that rewards Equipment being controlled, attached, cast, or used.

## aura_payoff

A card that rewards Auras being cast, attached, or controlled.

## equip_cost_reduction

A card that reduces equip costs or attaches equipment for free.

## attachment_synergy

A card that cares about Auras, Equipment, or other attachments being attached to permanents.

## commander_damage_support

A card that helps win through commander damage.

## voltron_protection

Protection specifically for a single built-up threat.

## artifact_combat

A card that uses artifacts, Equipment, Vehicles, or artifact creatures for combat pressure.

---

# Adventure / Modal / Alternate Face Roles

## modal_card

A card with multiple modes, faces, or cast options.

Includes split cards, MDFCs, Adventure cards, Aftermath, Fuse, Prototype, Kicker, Escalate, Entwine, Channel, Cycling, and Spree.

## adventure_spell

A card with an Adventure spell side.

Classify both halves. Adventure cards may support creature density, spellslinger, cast-from-exile, exile payoff, and value plans.

## adventure_payoff

A card that rewards Adventure spells or cards cast from exile after Adventure.

## modal_value

A card whose flexibility is a meaningful role.

## cast_from_exile

A card that allows, rewards, or depends on casting cards from exile.

Detection patterns:

- “You may cast that card from exile”
- “You may play that card this turn”
- “Whenever you cast a spell from exile”
- Adventure, suspend, foretell, plot, impulse draw, cascade, discover

## alternate_face_value

A card with a second face or alternate face that contributes meaningful value.

## spell_permanent_hybrid

A card that functions as both a spell and a permanent.

---

# Typal / Tribal Role Tags

## Critical typal rule

A creature sharing a type is not automatically a typal payoff.

Separate:

- `creature_type_density`: Card contributes body count/type count.
- `typal_payoff`: Card rewards or supports the type.
- `typal_support`: Card helps the typal plan through cost reduction, tutoring, recursion, protection, token creation, or bridge synergy.
- `incidental_creature_type`: Card has the type but does not appear to support a real typal plan.

Do not use type overlap as primary strategy evidence unless density/payoff gates are met.

## tribal_body

A creature that contributes to creature type count or commander-required body density.

Use only when deck context suggests the creature type or creature count matters.

## typal_density

A card that increases effective count for a creature type.

Sources include natural creature type on a card, token maker for the type, changeling, type-granter, commander-created tokens, multiple-copy exception cards, and repeatable recursion/tutoring of the type.

## typal_lord

A card that grants stat bonuses, keywords, or abilities to a creature type.

Detection patterns:

- “[Creature type] creatures you control get”
- “Other [Creature type] creatures you control”
- “Creatures of the chosen type get”
- “Creatures you control of the chosen type have”

## typal_cost_reducer

A card that reduces the cost of creatures or spells of a creature type.

## typal_token_maker

A card that creates creature tokens of the relevant type.

## typal_tutor

A card that searches for cards of a creature type.

## typal_card_draw

A card that draws or generates card advantage from a creature type.

## typal_recursion

A card that returns a creature type from graveyard to hand or library.

## typal_reanimation

A card that returns a creature type directly from graveyard to battlefield.

## typal_sacrifice_payoff

A card that rewards sacrificing or losing members of a creature type.

## typal_combat_payoff

A card that rewards combat involving a creature type.

## typal_counter_payoff

A card that puts, doubles, or rewards counters on a creature type.

## typal_lifegain_payoff

A card that connects a creature type to life gain, life drain, or lifelink.

## typal_artifact_payoff

A card that supports artifact creature tribes or creature types connected to artifacts.

## typal_etb_payoff

A card that rewards a creature type entering the battlefield.

## typal_death_payoff

A card that rewards a creature type dying.

## typal_attack_trigger

A card that rewards a creature type attacking.

## typal_damage_trigger

A card that rewards a creature type dealing damage or being damaged.

## typal_protection

A card that protects or grants resilience to a creature type.

## typal_changeling_support

A changeling or all-creature-types card used as typal glue.

## typal_multiple_copy_exception

A typal or deckbuilding exception card that permits multiple copies.

## typal_density_piece

A low-power or simple card included mainly to preserve creature type density.

## typal_cheat_effect

A card that puts creatures of a type onto the battlefield without paying full mana cost.

## typal_cost_support

Ramp, fixing, cost reduction, or cheat effects needed by high-MV tribes.

## typal_bridge_card

A card that connects a tribe to another strategy.

Examples:

- Vampire + Blood tokens
- Zombie + Reanimator
- Goblin + Aristocrats
- Dragon + Treasure Ramp
- Wizard + Spellslinger
- Soldier + Tokens
- Dwarf + Artifacts/Vehicles
- Sphinx + Card Draw
- Merfolk + Counters/Tap-Untap
- Angel + Lifegain
- Myr/Thopter/Construct + Artifacts

## Effective typal density tags

Use these so the strategy system can distinguish real typal plans from incidental type overlap.

- `changeling`: Card has Changeling or every creature type.
- `type_granter`: Card changes or grants creature types.
- `commander_created_typal_token`: Commander repeatedly creates creature tokens of a specific type.
- `token_typal_density`: Token maker contributes to typal density because it creates the relevant creature type.
- `multiple_copy_exception_density`: Multiple-copy exception contributes heavily to density if deck contains multiple copies.
- `typal_density_piece`: Low-power/simple card included mainly for type density.
- `incidental_creature_type`: Card has a creature type but no real typal relevance.

## Creature-type-specific support tags

Use these tags when the card meaningfully supports that type, contributes density to a supported typal plan, or is a payoff for the type.

Do not use these tags to make typal primary by themselves.

- `elf_typal`
- `goblin_typal`
- `vampire_typal`
- `zombie_typal`
- `dragon_typal`
- `sphinx_typal`
- `dwarf_typal`
- `human_typal`
- `soldier_typal`
- `wizard_typal`
- `sliver_typal`
- `merfolk_typal`
- `angel_typal`
- `demon_typal`
- `eldrazi_typal`
- `dinosaur_typal`
- `spirit_typal`
- `myr_typal`
- `artifact_creature_typal`
- `changeling_all_typal`

## Better tribal dependency extraction

Only create `tribal_dependency` from strong patterns:

- “[CreatureType] you control”
- “Other [CreatureType]s”
- “Whenever a [CreatureType]”
- “Whenever another [CreatureType]”
- “Choose a creature type”
- “Equipped [CreatureType]”
- “[CreatureType] spells you cast”
- “Create a [CreatureType] token”
- “Reveal a [CreatureType] card”
- “Search your library for a [CreatureType] card”

Do not infer tribal_dependency from generic English words.

Non-tribal exclusion list:

- time
- times
- turn
- turns
- phase
- phases
- combat
- card
- cards
- spell
- spells
- token
- tokens
- counter
- counters
- damage
- life
- mana
- artifact
- creature
- permanent
- opponent
- player

## tribal_payoff

A card that rewards having a specific creature type.

Detection patterns:

- “Dragons you control get”
- “Whenever a Dragon you control”
- “For each Elf you control”
- “Other Goblins get”
- “Whenever you cast a [creature type] spell”

Review notes:

- Tribal payoffs need enough tribe density.
- Creature type alone is density, not payoff.

---

# Political Role Tags

Political tags feed Section 3 political strategy gates. They do not make Politics primary by themselves.

Do not tag politics from one isolated group card as a primary strategy.

## group_draw

A card that causes multiple players or opponents to draw cards.

## group_ramp

A card that gives lands, mana, Treasure, or acceleration to multiple players.

## gift_resource

A card that gives an opponent or the table a resource in exchange for benefit, politics, or asymmetry.

## tablewide_acceleration

A card that accelerates the whole table.

## table_damage

A card that repeatedly damages or drains multiple opponents or all players.

## punisher

A card that punishes opponents or players for normal game actions.

Subtags: `spell_punisher`, `draw_punisher`, `attack_punisher`, `land_punisher`, `group_slug`.

## spell_punisher

Punishes casting spells.

## draw_punisher

Punishes drawing cards.

## attack_punisher

Punishes attacking.

## goad

A card that goads creatures.

## forced_attack

A card that forces creatures to attack.

## attack_elsewhere_incentive

A card that encourages attacking other players instead of the pilot.

## combat_restriction

A card that restricts attacks, blocks, or combat behavior.

## pillowfort

A card that discourages attacks against the player or taxes attackers.

## attack_tax

A card that requires opponents to pay to attack.

## combat_prevention

A card that prevents combat damage.

## rattlesnake

A card that discourages opponents from attacking, targeting, or harming you by threatening retaliation.

## revenge_trigger

A card that punishes opponents for damaging, attacking, targeting, or destroying your permanents.

## voting

A card that uses Will of the Council, Council’s Dilemma, or voting.

## monarch

A card that introduces or rewards monarch.

## initiative

A card that takes or rewards the initiative.

## bounty

A card that marks, rewards, or incentivizes attacking/killing specific players or permanents.

## curse

A Curse Aura or card that enchants an opponent and creates incentives/punishment.

## negotiated_removal

Removal or interaction that gives choices, deals, or opponent agency.

## threat_redistribution

A card that changes who gets attacked, targeted, or perceived as dangerous.

## donate_bad_gift

A card that gives opponents harmful permanents, drawbacks, or cursed resources.

## resource_redistribution

A card that redistributes permanents, hands, life totals, or resources.

## symmetrical_rule

A card that applies the same rule or restriction to all players.

## table_police

A card that punishes or restricts certain behaviors across the table, often as a meta-control piece.

## soft_lock

A card that contributes to a non-hard lock or recurring restriction.

## board_reset

A board wipe, mass bounce, or reset effect used as political/control reset.

## secret_combo_support

A card that helps a deck appear harmless while enabling a sudden combo or hidden win.

Use only when actual combo pieces or hidden win path exist.

## villain_pressure

A card or package likely to make the pilot the archenemy.

## reputation_pressure

A card that may carry social/table reputation pressure even if mechanically correct.

## kingmaker_risk

A card that may help one opponent too much or decide the game in another player’s favor.

## table_dependency

A card whose strength depends heavily on opponent behavior, table talk, meta, or pod composition.

## salt_risk

A card that may create frustration, resentment, or pregame discussion needs.

---

# Niche and Parasitic Theme Tags

These tags support Section 5.1. They identify narrow but legitimate themes and parasitic generator/payoff packages.

Do not make a niche theme primary from one or two cards unless the commander clearly creates the theme and the deeper section gate allows it.

## Energy

- `energy_generator`: Creates energy counters. Pattern: “You get {E}”.
- `energy_payoff`: Rewards energy production/count.
- `energy_sink`: Spends energy for effects.

## Food

- `food_generator`: Creates Food tokens.
- `food_payoff`: Rewards Food creation, control, or sacrifice.

## Blood

- `blood_generator`: Creates Blood tokens.
- `blood_payoff`: Rewards Blood tokens, discard, sacrifice, or Vampire/Blood synergy.

## Clues

- `clue_generator`: Creates Clue tokens or investigates.
- `clue_payoff`: Rewards Clues, Investigating, artifacts, or sacrificing Clues.

## Dice

- `dice_roll`: Rolls dice.
- `dice_payoff`: Rewards dice rolling.
- `dice_modifier`: Changes, improves, or multiplies die rolls.

## Coin flips

- `coin_flip`: Flips coins.
- `coin_flip_payoff`: Rewards flipping coins or winning flips.
- `coin_flip_multiplier`: Increases coin flips or modifies results.

## Mutate

- `mutate`: Card has mutate or supports mutate.
- `mutate_payoff`: Rewards mutating.
- `non_human_mutate_base`: Non-Human creature suitable as a mutate base. Requires mutate deck context.

## Dungeons / Initiative

- `venture`: Ventures into the dungeon.
- `repeatable_venture`: Can venture repeatedly.
- `dungeon_payoff`: Rewards completing dungeons or dungeon progression.
- `initiative_enabler`: Takes the initiative.
- `initiative_payoff`: Rewards having or progressing through initiative/Undercity.

## Vehicles

- `vehicle`: Type line includes Vehicle or Crew.
- `crew_enabler`: Helps crew Vehicles.
- `pilot_token`: Creates or uses Pilot tokens.

## Gates / Shrines

- `gate`: Land with Gate subtype or Gate-count role.
- `gate_payoff`: Rewards Gates.
- `shrine`: Enchantment with Shrine subtype.
- `shrine_payoff`: Rewards Shrines or Shrine count.

## Mill / Poison

- `opponent_mill`: Mills opponents.
- `repeatable_mill`: Can mill repeatedly.
- `infect`: Infect card or support.
- `toxic`: Toxic card or support.
- `corrupted_payoff`: Rewards opponents having three or more poison counters.
- `poison_payoff`: Rewards poison counters, poison damage, toxic, infect, or poisoned opponents.
- `proliferate`: Proliferates.

## Exile / delayed casting

- `adventure_spell`: Adventure spell side.
- `adventure_payoff`: Rewards Adventure.
- `foretell`: Foretell card or support.
- `suspend`: Suspend card or support.
- `time_counter_support`: Adds/removes/manipulates/rewards time counters.
- `cascade`: Cascade card or support.
- `discover`: Discover card or support.
- `cast_from_exile`: Allows/rewards casting from exile.
- `exile_payoff`: Rewards exile, casting from exile, or cards leaving exile.

---

# Fringe Theme Tags

These tags support Section 5.2. They usually lead to manual review unless user intent is provided.

- `rule_zero_only`: Likely requires explicit table permission.
- `nonstandard_legality`: Outside normal Commander legality expectations or requiring legality confirmation.
- `outside_game_component`: Requires stickers, Attractions, Contraptions, side decks, or other external components.
- `acorn_card`: Acorn card not normally legal in Commander.
- `silver_border`: Silver-bordered card not normally legal in Commander.
- `attractions`: Uses Attractions.
- `stickers`: Uses stickers or sticker sheets.
- `contraptions`: Uses Contraptions or sprockets.
- `social_contract_pressure`: May require pregame discussion due to salt, locks, mass land denial, repeated extra turns, or oppressive play.
- `meta_dependent_hate`: Strong only in certain metas.
- `self_synergy_conflict_possible`: May conflict with the deck’s own plan.
- `flavor_first_piece`: Likely included for flavor, theme, story, pet-card reasons, or casual identity.
- `package_dependency_piece`: Requires another specific card or package to function.
- `missing_package_piece_possible`: Appears to need another piece not found in the deck.
- `color_hate`: Hates a specific color or color pair.
- `life_exchange`: Exchanges life totals.
- `hellbent`: Hellbent or low-hand-size payoff.
- `level_up`: Level Up or level counters.
- `class_enchantment`: Class enchantment.
- `cave`: Cave subtype or Cave payoff.
- `locus`: Locus subtype or Locus payoff.
- `splice_arcane`: Splice onto Arcane or Arcane subtype support.
- `clash`: Clash.
- `fateseal`: Fateseal or opponent topdeck control.
- `adamant`: Adamant.
- `renown`: Renown.
- `bloodthirst`: Bloodthirst.

Fringe review rule:

- Do not automatically cut fringe cards when user explicitly declared the theme, commander clearly supports the theme, the card is one of the few available payoff pieces, the card is part of a required package, the deck is flavor-first, the card is meta tech, or the card preserves a deckbuilding restriction.
- Apply higher cut pressure when the card appears without payoff support, creates legality/table issues the user did not ask for, conflicts with the deck’s main plan, is represented by one or two isolated cards, or requires a missing package piece.

---

# Emergent Theme Tags

These tags support Section 5.3. They identify modern hybrid strategies, commander-created plans, and context corrections.

## commander_defined_engine

A card or package directly created by the commander’s rules text.

## commander_defined_support

A card that supports a commander-defined engine.

## resource_conversion

A card that converts one resource into another.

Examples: Treasure into tutoring, Food into cards/life/drain, tokens into mana/cards/damage, graveyard into creatures, life into cards/damage, Energy into tokens/damage/counters.

## conversion_point

A card that turns a deck’s generated resource into a win or meaningful advantage.

## bridge_card

A card that connects two or more strategies.

## high_synergy_low_power

A card that looks weak by generic standards but is important to the deck engine.

## generically_good_wrong_shell

A card that is powerful generally but does not fit the deck’s actual plan.

## commander_created_landfall

A commander-defined plan where lands entering create resources, tokens, artifacts, damage, or other value.

## token_combat_hybrid

A deck/card role where tokens are the resource engine and combat is the conversion point.

## go_wide_go_tall_hybrid

A strategy where the deck creates many bodies, then converts them into one/few massive threats or board-wide combat pressure.

## crime_trigger

A card that rewards committing crimes.

Detection pattern: “Whenever you commit a crime.”

## crime_enabler

A card that targets an opponent, something they control, or a card in their graveyard.

## outlaw_typal

A card supporting Assassin, Mercenary, Pirate, Rogue, or Warlock batching.

## plot

A card with Plot or plot support.

## offspring

A card with Offspring or payoff for token copies created by Offspring.

## gift

A card with Gift or support for gifting resources.

## forage

A card with Forage or support for Food/graveyard resource costs.

## expend

A card with Expend or mana-spent-matters payoff.

## room

A Room enchantment.

## eerie

A card with Eerie or enchantment-entry/unlocked Room payoff.

## manifest_dread

A card with Manifest Dread.

## face_down_support

A card that supports morph, manifest, disguise, cloak, face-down creatures, or turning face-down creatures face up.

## survival

A card with Survival.

## tapped_creature_payoff

A card that rewards creatures being tapped at a certain time or tapped status.

## treasure_tutor_chain

A package where Treasure production acts as both mana and tutor/conversion currency.

Do not classify as generic Treasure Ramp if the commander or deck converts Treasure into tutor chains.

## artifact_treasure_combo_value

A hybrid artifact/Treasure package that uses Treasure as artifact count, mana, sacrifice fodder, or combo fuel.

## slow_alt_win_condition

A visible or multi-turn alternate win condition. Not true turbo combo unless fast/tutor/protection gates pass.

## visible_win_condition

A win condition opponents can see coming and interact with.

## protected_setup_required

A card that needs protection or time to become effective.

## high_power_value_piece

A powerful value card that may affect bracket but is not inherently combo.

## compact_combo_piece

A card that can form a small combo with one or two other pieces.

## fast_combo_enabler

A card that accelerates combo assembly or execution.

Examples: fast mana that specifically supports combo, efficient tutors, free protection, cost reducers, repeatable untap engines.

## true_turbo_combo

Use only if the true turbo gate passes.

Suggested gate:

```python
can_be_true_turbo_combo = (
    fast_mana_count >= 3
    and efficient_tutor_count >= 3
    and compact_combo_count >= 1
    and protection_count >= 2
)
```

Do not tag true_turbo_combo from one alternate win, one high-power value card, or one compact interaction.

---

# Combo / Bracket / Power Modifier Tags

These tags support bracket and power review. They are not strategy evidence by themselves.

## combo_piece_possible

A card with text patterns commonly involved in combos.

Detection patterns:

- Repeatable untap
- Repeatable sacrifice
- Repeatable recursion
- Repeatable token creation
- Cost reduction to zero
- Copying activated abilities
- Copying triggered abilities
- Casting from graveyard repeatedly
- Mana production tied to untap loops
- “Whenever you cast” with mana generation
- “Whenever a creature enters” with token generation
- “Whenever a creature dies” with recursion
- “You may cast this card from your graveyard”

Review notes:

- Do not assume the combo exists.
- Check whether other combo pieces are present.
- If one piece appears missing, mark `combo_near_miss_possible`.
- Combo potential should not automatically make a card a keep in Bracket 2 decks.

## compact_combo_piece

A card that participates in a two-card or three-card compact combo.

Compact combo is not the same as true turbo combo.

## fast_combo_enabler

A card that improves fast combo execution.

Examples: fast mana, efficient tutors, free interaction/protection, cost reducers, repeatable untap engines, free sacrifice outlets.

## true_turbo_combo

Use only for fast, compact, redundant, protected combo plans.

Do not use for slow alternate win conditions, high-power value pieces, casual compact combos, visible multi-turn wins, or combo-adjacent value loops.

## slow_alt_win_condition

A card that can win eventually but requires visible setup, time, or conditions.

## high_power_value_piece

A strong standalone value card that may affect bracket but is not a combo by itself.

## bracket_pressure

A card or package that may increase the deck’s perceived power.

Common causes:

- Fast mana
- Efficient tutors
- Free interaction
- Compact combo
- Mass land denial
- Hard stax
- Repeated extra turns
- Game Changers
- Highly optimized win conditions

## high_bracket_pressure

A card or package that strongly suggests higher-power table expectations.

## game_changer

A card identified by the current Commander bracket/game-changer system as a Game Changer.

Review notes:

- Flag clearly.
- Do not automatically cut.
- Game Changer is a bracket signal, not proof of deck strategy.

## fast_mana

A card that accelerates mana unusually efficiently, often at low cost.

Fast mana is ramp and bracket pressure. Fast mana alone does not prove Ramp/Big Mana.

## efficient_tutor

A low-cost, flexible, or highly efficient tutor.

Efficient tutors increase consistency and may create bracket pressure. A tutor is not proof of combo unless combo pieces or tutor chains exist.

## free_interaction

Interaction that can be cast for zero or alternate cost.

---

# Other Mechanical Tags

## artifact_synergy

A card that cares about artifacts.

Detection patterns:

- “Whenever an artifact enters”
- “Artifacts you control”
- “Sacrifice an artifact”
- “For each artifact you control”
- “Affinity for artifacts”
- “Improvise”
- “Metalcraft”
- “Treasure tokens”

Subtags: `artifact_payoff`, `artifact_token_synergy`, `artifact_sacrifice`, `artifact_recursion`, `artifact_cost_reduction`, `artifact_treasure_combo_value`.

## enchantment_synergy

A card that cares about enchantments.

Detection patterns:

- “Whenever you cast an enchantment”
- “Whenever an enchantment enters”
- “Enchantments you control”
- “Constellation”
- “Aura”
- “Shrine”
- “Room”
- “Eerie”

Subtags: `enchantment_payoff`, `aura_synergy`, `constellation`, `enchantress_draw`, `enchantment_recursion`, `room`, `eerie`.

## spell_synergy

A card that rewards casting instants, sorceries, or noncreature spells.

Detection patterns:

- “Whenever you cast an instant or sorcery”
- “Whenever you cast a noncreature spell”
- “Magecraft”
- “Copy target instant or sorcery”
- “Spells you cast cost less”
- “Storm”

Subtags: `spellslinger_payoff`, `magecraft`, `spell_copy`, `instant_sorcery_discount`, `storm_possible`, `prowess`.

## stax_piece

A card that restricts what players can do.

Detection patterns:

- “Players can’t”
- “Opponents can’t”
- “Each player can cast only”
- “Spells cost more”
- “Activated abilities can’t be activated”
- “Creatures enter tapped”
- “Nonbasic lands don’t untap”

Subtags: `tax_effect`, `rule_restriction`, `graveyard_hate`, `spell_limit`, `untap_restriction`, `attack_restriction`, `soft_lock`, `social_contract_pressure`.

## graveyard_hate

A card that removes or restricts graveyards.

Detection patterns:

- “Exile target card from a graveyard”
- “Exile all graveyards”
- “Cards in graveyards can’t”
- “If a card would be put into a graveyard, exile it instead”

## forced_draw

A card that makes opponents or players draw cards, often as part of wheel, group hug, or draw-punisher plans.

Related tags: `group_draw`, `wheel_effect`, `opponent_draw_payoff`, `draw_punisher`, `group_slug`, `group_hug_possible`.

## wheel_effect

A card that causes players to discard, shuffle, or put away hands and then draw new cards.

Detection patterns:

- “Each player discards their hand, then draws”
- “Each player shuffles their hand and graveyard into their library, then draws”
- “Discard your hand, then draw”
- “Each player draws seven cards”
- “For each card discarded this way”

## opponent_draw_payoff

A card that specifically rewards or punishes opponents drawing cards.

## group_slug

A card that pressures all opponents through repeated damage, life loss, taxes, punishment, or resource pressure.

## group_hug_possible

A card that gives resources to multiple players, especially opponents.

## political_card

A card that encourages negotiation, voting, table deals, goad, monarch, initiative, tempting offers, or opponent choice.

## pillow_fort

Equivalent to `pillowfort`. Prefer `pillowfort` for consistent Section 3 tagging.

---

# Defender / Toughness Roles

## defender_payoff

A card that rewards having creatures with defender or Walls.

Detection patterns:

- “Creatures with defender”
- “Defender creatures you control”
- “Whenever a creature with defender”
- “Each creature with defender”
- “Walls you control”
- “Whenever a Wall”
- “For each creature with defender”

## toughness_payoff

A card that rewards high toughness or uses toughness as a resource.

Detection patterns:

- “Equal to its toughness”
- “Power equal to toughness”
- “Assigns combat damage equal to its toughness”
- “Whenever a creature with toughness”
- “Target creature assigns damage equal to its toughness”
- “Where X is the greatest toughness”
- “Life total becomes target creature's toughness”
- “You gain life equal to its toughness”

## toughness_combat

A card that allows creatures to deal combat damage using toughness instead of power, or otherwise turns toughness into offensive pressure.

Detection patterns:

- “Assigns combat damage equal to its toughness rather than its power”
- “Creatures you control assign combat damage equal to their toughness”
- “Each creature with defender can attack”
- “Creatures with defender can attack”
- “Can attack as though it didn't have defender”
- “Power becomes equal to toughness”
- “Switch target creature's power and toughness”

## wall_typal

A card that specifically cares about Walls, Defenders, or a Wall-like creature base.

---

# Modal and Special Parsing Rules

## land_possible

A card that can function as a land or has a land face.

## fixing

A card that improves color access.

## utility_land

A land that does more than produce mana.

## high_mana_value

A card with mana value 5 or greater.

High mana value does not mean bad. High mana value cards should justify their cost through immediate board impact, card advantage, win condition, protection, synergy payoff, commander synergy, or recursion/reanimation plan.

## low_impact_card

A card that appears to have minimal effect relative to its mana cost or deck needs.

Do not assign this tag until expanded role checks have been completed.

## vanilla_or_french_vanilla_creature

A creature with no rules text or only combat keywords.

Do not automatically cut. Check creature type, keyword relevance, commander synergy, typal need, equipment/aura/Voltron role, devotion/pips, sacrifice body role, attack body role, token body role, commander-required density, and niche/fringe/emergent support.

## creature_no_role_review

Use this only after all functional role checks have failed.

Do not automatically cut the card.

## manual_review

Use this when the card cannot be confidently classified or needs human judgment.

Common reasons:

- Custom card
- Missing Oracle text
- Very complex wording
- Unusual rules interaction
- Multiple faces not parsed correctly
- Split card ambiguity
- Partner/background/commander identity ambiguity
- Unsupported or unknown mechanic
- Low confidence from Scryfall lookup
- Name mismatch
- Category mismatch
- Fringe package without user intent
- Political card with table-dependent value
- Bracket/social contract concern
- Missing package piece
- Possible self-synergy conflict

Manual review is not a cut recommendation.

---

# Commander-Specific Tags

## commander_protection

A card that protects the commander.

Useful for creature commanders, Voltron commanders, high mana value commanders, commanders that must stay in play, commanders with tap abilities, and commanders with attack/combat damage triggers.

## commander_enabler

A card that helps the commander do its thing.

Examples:

- Haste for attack commanders
- Evasion for combat damage commanders
- Untap effects for tap ability commanders
- Ramp for expensive commanders
- Protection for fragile commanders
- Tokens for sacrifice commanders
- Lifegain for lifegain commanders
- ETB support for ETB commanders
- Graveyard fill for graveyard commanders
- Defender/toughness support for toughness commanders
- Forced draw/wheels for draw-punisher commanders
- Crime enablers for crime commanders
- Land ramp for landfall commanders
- Food/graveyard support for forage commanders

## commander_payoff

A card that directly rewards the commander’s main action.

---

# Deck Structure and Legality Tags

## color_identity_violation

A card whose color identity is outside the commander’s color identity.

This should be flagged strongly.

## banned_card

A card banned in Commander.

Flag strongly. Do not recommend keeping in a legal Commander deck unless user uses house-rule or Rule 0 context.

## multiple_copy_exception

A card that allows more than one copy in a Commander deck.

Detection patterns:

- “A deck can have any number of cards named”
- “You can have any number of”
- “A deck can have up to seven cards named”
- Basic lands
- Other explicit deckbuilding exceptions

## duplicate_nonexception

A nonbasic, nonexception card that appears more than once in a Commander deck.

Flag as Commander legality issue, not a normal cut suggestion.

---

# Special Parsing Rules

## Partner commanders

If the deck has Partner, Friends forever, Doctor’s companion, Choose a Background, Background, or similar commander-pairing mechanics:

- Parse both commander cards.
- Combine their color identities.
- Analyze both commander texts.
- Detect synergies with either commander.
- Do not treat the second commander/background as a normal maindeck card.
- Do not flag the second commander/background as illegal solely because there are two commanders.

Tags: `commander_pair`, `partner_commander`, `background_commander`, `combined_color_identity`.

## Backgrounds

For Background commanders, treat the Background as part of the commander identity if the commander has “Choose a Background.”

## Split cards

For split cards, classify each half by its own function. Do not treat the card as though both halves are always cast together.

Tags: `split_card`, `modal_card`, `multi_mana_value_review`.

## Adventure cards

For Adventure cards, classify the creature side and the Adventure spell side.

Tags: `adventure_card`, `adventure_spell`, `modal_card`, `creature_spell_flexibility`, `spell_permanent_hybrid`, `cast_from_exile_possible`.

## Modal double-faced cards

For MDFCs, classify front face and back face. If one face is a land, tag `land_possible`.

Tags: `modal_dfc`, `land_possible`, `spell_possible`, `modal_card`, `alternate_face_value`.

## Transforming double-faced cards

For transforming DFCs, classify front face and back face if available. Do not assume the back face is always available.

Tags: `transform_card`, `manual_review_possible`, `alternate_face_value`.

## Prototype cards

For Prototype cards, track normal mana value and prototype cost if available.

Tags: `prototype_card`, `alternate_cost`, `modal_card`.

## X-spells

For X-spells, mana value may appear low when X is zero, but practical mana investment can be high.

Tags: `x_spell`, `scalable_effect`, `mana_sink`.

---

# Cut Risk Tags

## unsupported_synergy_piece

A synergy card with too few matching support cards.

Examples:

- ETB doubler with very few ETB permanents
- Typal payoff with too few type members
- Sacrifice payoff with no sacrifice outlets
- Lifegain payoff with few lifegain sources
- Defender payoff with few defenders
- Draw punisher with few forced draw or wheel effects
- Energy payoff with too few generators
- Gate payoff with too few Gates

## unsupported_tribal_dependency

A card that requires a tribe but the deck has too few members of that tribe.

## narrow_card

A card that is useful only in limited situations.

## redundant_card

A card whose role is already heavily represented in the deck.

## off_plan_card

A card that may be individually strong but does not support the deck’s main plan.

## high_mv_low_impact

A high mana value card that does not appear to provide enough payoff.

## self_nonbo_possible

A card that may conflict with the deck’s own plan.

## replaceable_but_playable

A card that is not bad, but may be one of the easier cards to upgrade or cut.

## good_card_wrong_shell

A card that is powerful or playable in Commander generally, but does not fit this deck’s strategy well.

## weak_alone_strong_in_context

A card that looks unimpressive by raw power but supports a key deck engine.

---

# Cut Categories

When producing cut suggestions, classify each possible cut using one or more of these cut types:

- Possible Efficiency Cut
- Possible Curve Cut
- Possible Off-Theme Cut
- Possible Redundancy Cut
- Possible Low-Impact Cut
- Possible Bracket Pressure Cut
- Possible Mana Base Concern
- Possible Manual Review

---

# Cut Confidence Rules

## High cut confidence

Use only when most of these are true:

- The card has low synergy with commander and primary strategy.
- The card does not support the secondary strategy.
- The card has low role importance.
- The card is redundant or inefficient.
- The card is not protected by key engine logic.
- The card has no strong context-dependent reason to remain.

## Medium cut confidence

Use when:

- The card has a role, but appears replaceable.
- The card may be off-plan but still playable.
- The card needs support the deck may not have enough of.
- The card is probably a reasonable review candidate.

## Low cut confidence

Use when:

- The card may be part of a hidden synergy.
- The card has narrow but real synergy.
- The card is weak alone but potentially strong in context.
- The card has manual-review concerns.
- The card is a pet card candidate or unusual archetype piece.
- The card belongs to a fringe or political package and user intent is unclear.

Low-confidence cut candidates should not be framed as recommended cuts.

---

# Protected From Cut Logic

A card should be protected from cuts if it has one or more of the following:

- Strong commander synergy
- Multiple useful role tags
- Efficient ramp
- Efficient card draw
- Flexible removal
- Board wipe role needed by the deck
- Protection role for a commander-centric deck
- Win condition role
- Combo relevance in a combo-aware shell
- Typal payoff with enough type support
- Typal density piece in low-density but real typal deck
- Recursion with graveyard support
- Sacrifice outlet with death/token support
- Token production with payoffs
- High synergy with deck’s main plan
- Unique effect the deck needs
- Low-power but strategy-critical role
- Defender/toughness payoff in defender decks
- Wheel/draw-punisher payoff in forced-draw decks
- Lifegain/lifedrain payoff in life-total decks
- Mass blink in ETB/blink decks
- Combat reset or attack safety in combat-trigger decks
- Untap-ramp with valid mana engine support
- Activated ability support in activated-ability commander decks
- Political protection or incentive in actual political decks
- Niche/fringe/emergent support when user intent or commander support is clear

The agent should explain the keep reason using role tags, not card name reputation.

---

# Context-Dependent Manual Review Logic

Place a card into Context-Dependent Manual Review when it has a narrow role that may be important but requires deck density or user intent.

Common examples:

- Typal support with borderline type count
- Sacrifice outlets with low death payoff count
- Recursion with unclear graveyard setup
- Narrow payoffs
- Low-power synergy pieces
- Defender/toughness enablers
- Forced draw without enough draw punishers
- Draw punisher without enough forced draw
- Lifegain payoff with incidental lifegain only
- Combat safety in a noncombat deck
- Political/group hug cards
- Fringe mechanics without user intent
- Rule Zero components
- Bracket/social contract pressure cards
- Isolated compact combo pieces
- Package-dependent cards with missing piece possible

Manual review cards should not be high-confidence cuts unless the support mismatch is obvious.

---

# Replacement Category Tags

When suggesting replacements, suggest categories first. Suggest exact cards only when appropriate.

Use these replacement categories:

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
- More lifegain payoffs
- More lifegain sources
- More lifedrain finishers
- More typal density
- More typal payoffs
- More blink effects
- More ETB creatures
- More toughness payoffs
- More defenders/Walls
- More wheel effects
- More draw punishers
- More artifact support
- More enchantment support
- More combat protection
- More evasion
- More untap support
- More activated ability support
- More mana sinks
- More creature-chain support
- More Equipment support
- More Aura support
- More political payoff
- More asymmetrical payoff
- More niche enablers
- More niche payoffs
- More fringe support if intentional
- More emergent package support
- More bracket-appropriate alternatives
- More table-friendly alternatives

Replacement suggestions should not conflict with the deck’s primary plan.

---

# Expanded Role Check Before Cuts

Before marking a card as a possible cut, the agent must check whether the card has any of the expanded v0.5.6 hotfix role tags.

Do not mark a card as low-impact, no-role, or off-plan until checking for:

- strategy-layer tags
- typal role tags
- effective typal density tags
- political role tags
- niche/parasitic theme tags
- fringe theme tags
- emergent theme tags
- bracket/power modifier tags
- activated ability roles
- untap-ramp roles
- pod/creature-chain roles
- equipment/aura/Voltron roles
- adventure/modal roles
- slow alt win vs turbo combo distinctions

If one or more of these tags are present, the card should be reviewed in context before being suggested as a cut.

The agent should ask:

1. Does this tag support the commander?
2. Does this tag support the primary strategy?
3. Does this tag support the secondary strategy?
4. Does the deck have enough density to make this role reliable?
5. Is this card a payoff, enabler, protection piece, resource converter, or win condition?
6. Is the card weak generically but strong in this shell?
7. Is the card narrow but necessary?
8. Is this a bracket modifier rather than strategy evidence?
9. Is this a package card requiring user intent or manual review?

Cards with narrow or context-dependent tags should usually be placed into one of these categories:

- Protected From Cut
- Possible Manual Review
- Context-Dependent Card
- Possible Cut only if support density is low

The agent should avoid recommending cuts to these cards with High confidence unless it can clearly explain that the deck lacks the required support package.

---

# Detection Safeguards Summary

The agent must apply these safeguards:

1. Do not tag politics from one isolated group card.
2. Do not tag typal payoff from incidental creature type words.
3. Do not tag fringe primary support without user intent.
4. Do not tag true_turbo_combo from one alternate win condition or one high-power value card.
5. Do not tag a creature as no-role until checking typal density, sacrifice body, attack body, token body, commander-required density, and niche/fringe/emergent support.
6. Do not use bracket pressure as synergy evidence by itself.
7. Do not treat manual_review as a cut recommendation.
8. Do not treat a powerful card as on-plan unless it supports the deck’s commander, strategy, or needed role balance.
9. Do not suppress commander-defined packages just because broad archetype counts are higher.
10. Do not overprotect narrow package cards if support density is absent and user intent is unknown.

---

# Example Classification Guidance

These are example classifications only. Do not hardcode these card names as automatic keeps or cuts.

| Card Pattern | Likely Tags | Review Guidance |
|---|---|---|
| Panharmonicon-style card | synergy_piece, ETB_synergy, etb_doubler, micro_archetype_support | Protect only if ETB density or commander ETB synergy exists. |
| Wrathful Red Dragon-style card | creature, tribal_payoff, typal_damage_trigger, dragon_typal, synergy_piece | Strong in Dragon/damage decks. Review if Dragon density is low. |
| Gravecrawler-style card | creature, recursion, self_recursion, tribal_dependency, zombie_typal, sacrifice_body, combo_piece_possible | Check tribe count, sacrifice outlets, death payoffs, and graveyard loops. |
| Untap target land card | untap_ramp, land_untapper, mana_engine_support_possible | Strong with mana doublers, utility lands, bounce lands, or tap commanders. |
| Low-text on-type creature | tribal_body, typal_density, typal_density_piece, possible attack_body or sacrifice_body | Do not call no-role until typal density and body roles are checked. |
| Exquisite Blood-style card | lifedrain_payoff, life_total_manipulation, win_condition_possible, compact_combo_piece_possible | Protect in lifegain/lifedrain shells. Review for combo/bracket pressure. |
| Radiant Destiny-style card | typal_lord, tribal_anthem, typal_protection, typal_support | Protect if type density is high. Review if density is low. |
| Reconnaissance-style card | combat_reset, attack_safety, commander_protection_possible, combat_payoff_support | Strong in attack-trigger, combat-damage, Voltron, or go-wide decks. |
| Another Round-style card | mass_blink, ETB_synergy, blink_protection_possible, synergy_piece | Strong with ETB density. Review if deck lacks ETB creatures. |
| Rhox Faithmender-style card | lifegain_payoff, life_total_manipulation | Strong with repeated life gain. Review if lifegain is incidental only. |
| Tree of Perdition-style card | life_total_manipulation, toughness_payoff_possible, slow_alt_win_condition | Context-dependent. Not turbo combo by itself. |
| Assault Formation-style card | toughness_combat, toughness_payoff, defender_payoff, win_condition_possible | Core card in defender/toughness combat decks. |
| Axebane Guardian-style card | defender_payoff, wall_typal, mana_source, ramp, mana_engine_support | Core ramp in defender decks. Weak only if defender density is low. |
| Wheel-style card | wheel_effect, forced_draw, graveyard_enabler, opponent_draw_payoff_possible | Strong with draw punishers, discard payoffs, graveyard use, or hand refill needs. |
| Group draw card | group_draw, forced_draw, group_hug_possible, manual_review_package_card | Do not make Politics primary from one card. Check payoff/asymmetry. |
| Crime interaction card | targeted_removal, crime_enabler, micro_archetype_support | Protect in crime commanders; otherwise normal interaction. |
| Attraction/sticker/contraption card | attractions/stickers/contraptions, outside_game_component, rule_zero_only, manual_review | Requires legality/table permission review. |
| Multiple-copy exception card | multiple_copy_exception, typal_multiple_copy_exception, multiple_copy_exception_density | Do not flag duplicates as illegal if text allows them. Still evaluate support density. |
| Fast mana card | ramp, fast_mana, bracket_pressure | Does not make the deck Ramp/Big Mana by itself. |
| Efficient tutor | tutor, efficient_tutor, bracket_pressure | Does not prove combo unless combo pieces/tutor chain exist. |
| Slow alternate win | slow_alt_win_condition, visible_win_condition, protected_setup_required | Not true_turbo_combo unless turbo gate passes. |

---

# Recommended Role Summary Output

After classification, the agent should produce a Card Role Tag Summary.

Example:

```text
Card Role Tag Summary

Ramp: 12
Untap Ramp / Mana Engine Support: 3
Card Draw / Advantage: 9
Repeatable Card Draw: 4
Targeted Removal: 7
Repeatable Removal: 2
Board Wipes: 3
Protection: 4
Token Makers: 8
Token Bodies: 6
Sacrifice Outlets: 5
Sacrifice Bodies: 7
Death Payoffs: 4
Recursion: 6
Graveyard Enablers: 5
Typal Density Pieces: 18
Typal Payoffs: 7
Typal Protection / Lords: 4
Lifegain Sources: 5
Lifegain Payoffs: 3
Lifedrain Payoffs: 2
Combat Safety / Reset: 2
Blink / ETB Support: 6
Defender / Toughness Payoffs: 4
Wheels / Forced Draw: 3
Draw Punishers: 3
Activated Ability Support: 4
Pod / Creature Chain Support: 2
Equipment / Aura / Voltron Support: 5
Political Role Cards: 4
Niche Theme Cards: 3
Fringe Theme Cards: 1
Emergent Package Cards: 5
Bracket Modifiers: 3
Commander Synergy Possible: 18
Combo Piece Possible: 4
Manual Review: 2
```

Then it should explain:

- Areas of strength
- Areas of weakness
- Cards with unclear roles
- Cards with unsupported roles
- Cards that deserve human review before cutting
- Cards protected from cuts
- Cards that are possible cuts but not guaranteed cuts
- Replacement categories the deck may need
- Bracket/power modifiers separate from strategy evidence
- Possible false positives from over-tagging safeguards

---

# Possible Cut Review Output

The agent should output possible cuts in this structure:

```text
Possible Cut Review

These are not guaranteed cuts. These are the cards most worth reviewing based on curve, synergy, redundancy, role balance, and the deck’s actual plan.

Card: [Card Name]
Cut Type: Possible Off-Theme Cut / Possible Redundancy Cut / Possible Efficiency Cut / etc.
Confidence: Low / Medium / High
Detected Roles: [role tags]
Reason: [Explain using role tags and deck context.]
Replacement Category: [More ramp / More draw / More commander synergy / etc.]
```

The agent should also include:

```text
Protected From Cut

Card: [Card Name]
Detected Roles: [role tags]
Reason: [Supports commander / primary plan / core engine / win condition / essential role.]
```

And when necessary:

```text
Context-Dependent Cards to Review Manually

Card: [Card Name]
Detected Roles: [role tags]
Reason: [May be important if the deck is intentionally supporting this package.]
```

---

# Minimum v0.5.6 Hotfix Success Standard

The v0.5.6 hotfix agent is successful when:

1. It reads this file before classification.
2. It no longer relies on hardcoded card-name keep/cut rules.
3. It assigns multiple role tags when appropriate.
4. It recognizes narrow synergy cards before calling them low-impact.
5. It flags no-role creatures for review instead of automatic cuts.
6. It recognizes synergy pieces by text pattern.
7. It recognizes typal density and typal payoff separately.
8. It recognizes effective typal density from tokens, changelings, type-granters, commander-created tokens, and multiple-copy exceptions.
9. It supports the Section 4 typal vocabulary without making typal primary from incidental type overlap.
10. It supports Section 3 political tags without making Politics primary from one isolated political card.
11. It supports Section 5.1 niche and parasitic mechanics through generator/payoff tags.
12. It supports Section 5.2 fringe themes with manual review and user-intent caution.
13. It supports Section 5.3 emergent commander-defined packages.
14. It separates bracket/power modifiers from strategy evidence.
15. It distinguishes slow alternate win conditions, high-power value pieces, compact combo pieces, fast combo enablers, and true turbo combo.
16. It handles split cards, MDFCs, Adventure cards, Backgrounds, and Partner commanders carefully.
17. It flags color identity violations.
18. It flags banned cards, duplicate issues, and multiple-copy exceptions.
19. It produces a Card Role Tag Summary.
20. It separates possible cuts from recommended cuts.
21. It gives cut confidence: Low, Medium, or High.
22. It protects core cards from cuts.
23. It identifies cards needing more playtesting before cutting.
24. It suggests replacement categories before exact replacement cards.
25. It avoids cutting narrow synergy pieces without checking support density.
26. It avoids cutting low-power strategy-critical cards.
27. It avoids recommending replacements that conflict with the deck’s main plan.
28. It can explain: “This card looks weak by generic standards, but it belongs because it supports the deck’s actual engine.”

---

# Agent Prompt Reminder

Before assigning cut candidates, read and apply `card_attribute_rules.md`.

Classify each card by detected role tags first.

Do not classify a card as “no useful role,” “low impact,” “off-plan,” or “possible cut” until checking:

- strategy-layer tags
- typal tags
- effective typal density tags
- political tags
- niche tags
- fringe tags
- emergent tags
- bracket modifiers
- activated ability support
- untap-ramp support
- pod/creature-chain support
- equipment/aura/Voltron support
- adventure/modal support
- body roles

Pay special attention to cards that may belong to:

- Lifegain/lifedrain
- Life total manipulation
- Typal anthem/protection/density
- Combat safety
- Blink/flicker
- Defender/Wall/toughness matters
- Wheels/forced draw/draw punisher
- Group slug
- Political/goad/pillowfort
- Untap-ramp / mana engines
- Activated ability commanders
- Creature-chain / pod decks
- Equipment/Aura/Voltron
- Adventure/modal/cast-from-exile
- Niche/parasitic mechanics
- Fringe mechanics
- Emergent commander-created packages
- Bracket/power pressure

A card with narrow synergy should not be treated as bad by default.

If the support package exists, protect the card or mark it as context-dependent.

If the support package does not exist, mark it as a possible cut with Low or Medium confidence, not High confidence, unless the mismatch is obvious.

Manual review is not a cut recommendation.

Bracket pressure is not strategy evidence by itself.
