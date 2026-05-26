## Strategy Knowledge Integration Preview

Strategy Knowledge is active as report and AI-handoff context for this run.

### Strategy Brain Status
- Selected strategy system: strategy_knowledge_default_with_legacy_fallback
- Legacy fallback required: Yes
- Strategy profiles available: 5
- Scoring preview matches: 5 / 5
- Protected-context samples: 4
- Possible-cut samples: 2
- Replacement-need samples: 2

### Strategy-Aware Guidance Rules
- Use Strategy Knowledge as context for strategy recognition, role mapping, cuts, protection, replacement guidance, and report wording.
- Do not treat Strategy Knowledge as permission to generate a final deck list.
- Do not treat possible cuts as mandatory cuts.
- Separate bad card from wrong card for this deck.
- Separate low power from low synergy.
- Protect high-synergy low-raw-power cards when they support the commander's plan.
- Keep collection-first behavior unless the user allows outside upgrades.
- Assume basic lands are available; keep nonbasic lands collection-first unless outside upgrades are allowed.

### Loaded Strategy Role Profiles
- Aristocrats (`aristocrats`): primary roles = strategy_enablers, strategy_payoffs, recursion, finishers_win_conditions; strategy roles = free_sacrifice_outlets, repeatable_sacrifice_outlets, death_trigger_payoffs, token_fodder, creature_recursion, drain_finishers
- Landfall / Lands Matter (`landfall_lands_matter`): primary roles = ramp_mana_development, strategy_enablers, strategy_payoffs, mana_base_support; strategy roles = extra_land_drops, landfall_payoffs, land_recursion, fetch_lands_and_land_tutors, land_token_payoffs, big_mana_finishers
- Spellslinger (`spellslinger`): primary roles = strategy_enablers, strategy_payoffs, card_draw_card_advantage, finishers_win_conditions; strategy roles = cheap_cantrips, spell_payoffs, cost_reducers, copy_effects, graveyard_spell_recursion, spell_based_finishers
- Tokens (`tokens`): primary roles = strategy_enablers, strategy_payoffs, finishers_win_conditions, card_draw_card_advantage; strategy roles = repeatable_token_makers, burst_token_makers, anthem_payoffs, token_draw_payoffs, token_finishers, fodder_converters
- Voltron (`voltron`): primary roles = protection, strategy_enablers, strategy_payoffs, finishers_win_conditions; strategy roles = evasion_granting_cards, protection_spells, equipment_or_aura_payoffs, commander_damage_scalers, combat_card_draw, recovery_after_removal

### Boundary
- This section improves strategy interpretation, report readability, and AI handoff quality.
- It does not generate a deck, select exact cards, make final deck inclusion decisions, generate role counts, generate a mana base, insert lands, or create a full 100-card draft.

## Build From Collection Strategy Shell Planning

Strategy Knowledge is now producing rough shell-planning guidance for Build From Collection.

### Boundary
- This is rough shell guidance only.
- It does not select exact cards.
- It does not make final deck inclusion decisions.
- It does not generate role counts, a mana base, land insertion, or a full 100-card draft.

### Collection-First Rules
- Prefer owned cards first.
- Assume basic lands are available.
- Keep nonbasic lands collection-first unless outside upgrades are allowed.

### Strategy Shell Plans

#### Aristocrats (`aristocrats`)

- **strategy_enablers**: 10-16 sacrifice outlets, fodder engines, and repeatable death-enablers
- **strategy_payoffs**: 8-12 death triggers, drain payoffs, and sacrifice rewards
- **recursion**: 5-9 recursion pieces that rebuy creatures or engines
- **card_draw_card_advantage**: 8-12 draw/value pieces, preferably tied to death or sacrifice
- **finishers_win_conditions**: 3-6 finishers that convert death loops or wide boards into wins
- **protection**: 3-6 ways to protect engine pieces or recover from wipes

#### Landfall / Lands Matter (`landfall_lands_matter`)

- **ramp_mana_development**: 10-16 ramp, extra land drops, land search, and land recursion pieces
- **strategy_enablers**: 8-14 landfall triggers, land-recursion engines, and land-entry enablers
- **strategy_payoffs**: 8-12 landfall or lands-matter payoff cards
- **mana_base_support**: 8-14 lands/nonlands that support land entries, fixing, or utility
- **card_draw_card_advantage**: 7-11 draw/value pieces tied to lands or ramp
- **finishers_win_conditions**: 3-6 landfall finishers, big mana closers, or token-overrun wins

#### Spellslinger (`spellslinger`)

- **strategy_enablers**: 10-16 cheap instants/sorceries, cost reducers, copy engines, or spell-density enablers
- **strategy_payoffs**: 8-12 magecraft, storm-like, copy, token, or damage payoffs
- **card_draw_card_advantage**: 10-16 draw/selection pieces to keep spells flowing
- **targeted_removal**: 5-9 efficient interaction spells that also support spell count
- **finishers_win_conditions**: 3-6 spell-copy, storm, X-spell, or spell-damage finishers
- **protection**: 2-5 protection/countermagic pieces depending on bracket

#### Tokens (`tokens`)

- **strategy_enablers**: 10-16 repeatable token makers and go-wide engines
- **strategy_payoffs**: 8-12 anthem, drain, convoke, or attack-scaling payoffs
- **card_draw_card_advantage**: 8-12 draw/value pieces that reward creature count or tokens
- **finishers_win_conditions**: 3-6 overrun, aristocrat, impact-damage, or mass-pump finishers
- **protection**: 3-6 protection or rebuild tools for board wipes

#### Voltron (`voltron`)

- **strategy_enablers**: 10-16 equipment, auras, evasion, power boosts, or commander-damage support
- **strategy_payoffs**: 5-9 cards that reward suiting up, attacking alone, or commander combat
- **protection**: 8-14 protection, recursion, hexproof, indestructible, or anti-removal tools
- **targeted_removal**: 5-9 cheap interaction pieces to clear blockers or stop removal
- **card_draw_card_advantage**: 7-11 draw/value pieces tied to combat, equipment, or commander connection
- **finishers_win_conditions**: 2-5 commander-damage closers, extra combat, or lethal pump lines

## Exact Card Candidate Selection Preview

Strategy Knowledge can now nominate exact-card candidates for review.

### Boundary
- These are candidates, not final deck inclusions.
- This does not generate a deck.
- This does not generate final role counts, a mana base, land insertion, or a full 100-card draft.
- Off-plan / low-synergy cards should not be promoted just because they are generically strong.

### Candidate Sets

#### Aristocrats (`aristocrats`)

- **Blood Artist** — candidate roles: finishers_win_conditions, strategy_payoffs; score: 14; final inclusion: No
- **Viscera Seer** — candidate roles: strategy_enablers; score: 11; final inclusion: No
- **Impact Tremors** — candidate roles: finishers_win_conditions, strategy_payoffs; score: 8; final inclusion: No
- **Young Pyromancer** — candidate roles: strategy_enablers, strategy_payoffs; score: 7; final inclusion: No
- **Swiftfoot Boots** — candidate roles: protection, strategy_enablers; score: 6; final inclusion: No
- **Solve the Equation** — candidate roles: card_draw_card_advantage, strategy_enablers; score: 6; final inclusion: No
- **Secure the Wastes** — candidate roles: strategy_enablers; score: 6; final inclusion: No
- **All That Glitters** — candidate roles: finishers_win_conditions, strategy_payoffs; score: 6; final inclusion: No

#### Landfall / Lands Matter (`landfall_lands_matter`)

- **Evolving Wilds** — candidate roles: mana_base_support, strategy_enablers; score: 13; final inclusion: No
- **Cultivate** — candidate roles: mana_base_support, ramp_mana_development; score: 12; final inclusion: No
- **Young Pyromancer** — candidate roles: strategy_enablers, strategy_payoffs; score: 7; final inclusion: No
- **Impact Tremors** — candidate roles: finishers_win_conditions, strategy_payoffs; score: 7; final inclusion: No
- **Solve the Equation** — candidate roles: card_draw_card_advantage, strategy_enablers; score: 6; final inclusion: No
- **Blood Artist** — candidate roles: finishers_win_conditions, strategy_payoffs; score: 6; final inclusion: No
- **All That Glitters** — candidate roles: finishers_win_conditions, strategy_payoffs; score: 6; final inclusion: No
- **Secure the Wastes** — candidate roles: strategy_enablers; score: 5; final inclusion: No

#### Spellslinger (`spellslinger`)

- **Young Pyromancer** — candidate roles: strategy_enablers, strategy_payoffs; score: 11; final inclusion: No
- **Solve the Equation** — candidate roles: card_draw_card_advantage, strategy_enablers; score: 11; final inclusion: No
- **Swiftfoot Boots** — candidate roles: protection, strategy_enablers; score: 6; final inclusion: No
- **Impact Tremors** — candidate roles: finishers_win_conditions, strategy_payoffs; score: 6; final inclusion: No
- **Blood Artist** — candidate roles: finishers_win_conditions, strategy_payoffs; score: 6; final inclusion: No
- **All That Glitters** — candidate roles: finishers_win_conditions, strategy_payoffs; score: 6; final inclusion: No
- **Viscera Seer** — candidate roles: strategy_enablers; score: 4; final inclusion: No
- **Secure the Wastes** — candidate roles: strategy_enablers; score: 4; final inclusion: No

#### Tokens (`tokens`)

- **Impact Tremors** — candidate roles: finishers_win_conditions, strategy_payoffs; score: 11; final inclusion: No
- **Secure the Wastes** — candidate roles: strategy_enablers; score: 9; final inclusion: No
- **Young Pyromancer** — candidate roles: strategy_enablers, strategy_payoffs; score: 7; final inclusion: No
- **Swiftfoot Boots** — candidate roles: protection, strategy_enablers; score: 6; final inclusion: No
- **Solve the Equation** — candidate roles: card_draw_card_advantage, strategy_enablers; score: 6; final inclusion: No
- **Blood Artist** — candidate roles: finishers_win_conditions, strategy_payoffs; score: 6; final inclusion: No
- **All That Glitters** — candidate roles: finishers_win_conditions, strategy_payoffs; score: 6; final inclusion: No
- **Viscera Seer** — candidate roles: strategy_enablers; score: 4; final inclusion: No

#### Voltron (`voltron`)

- **All That Glitters** — candidate roles: finishers_win_conditions, strategy_payoffs; score: 14; final inclusion: No
- **Swiftfoot Boots** — candidate roles: protection, strategy_enablers; score: 13; final inclusion: No
- **Solve the Equation** — candidate roles: card_draw_card_advantage, strategy_enablers; score: 7; final inclusion: No
- **Young Pyromancer** — candidate roles: strategy_enablers, strategy_payoffs; score: 6; final inclusion: No
- **Impact Tremors** — candidate roles: finishers_win_conditions, strategy_payoffs; score: 6; final inclusion: No
- **Blood Artist** — candidate roles: finishers_win_conditions, strategy_payoffs; score: 6; final inclusion: No
- **Viscera Seer** — candidate roles: strategy_enablers; score: 4; final inclusion: No
- **Secure the Wastes** — candidate roles: strategy_enablers; score: 4; final inclusion: No

## Strategy-Based Role Count Generation

Strategy Knowledge can now generate strategy-based role target bands.

### Boundary
- These are target bands, not final deck counts.
- This does not make final deck inclusion decisions.
- This does not generate a final deck, mana base, land insertion, or full 100-card draft.
- Overlapping cards may satisfy multiple roles during review.

### Role Count Plans

#### Aristocrats (`aristocrats`)

- **ramp_mana_development**: 8–12 cards; target 10
- **card_draw_card_advantage**: 8–12 cards; target 10
- **targeted_removal**: 5–9 cards; target 7
- **board_wipes**: 2–4 cards; target 3
- **strategy_enablers**: 10–16 cards; target 13
- **strategy_payoffs**: 8–12 cards; target 10
- **recursion**: 5–9 cards; target 7
- **finishers_win_conditions**: 3–6 cards; target 4
- **protection**: 3–6 cards; target 4
- **lands**: 35–38 cards; target 37

#### Landfall / Lands Matter (`landfall_lands_matter`)

- **ramp_mana_development**: 10–16 cards; target 13
- **card_draw_card_advantage**: 7–11 cards; target 9
- **targeted_removal**: 4–8 cards; target 6
- **board_wipes**: 1–4 cards; target 2
- **strategy_enablers**: 8–14 cards; target 11
- **strategy_payoffs**: 8–12 cards; target 10
- **mana_base_support**: 8–14 cards; target 11
- **finishers_win_conditions**: 3–6 cards; target 4
- **lands**: 37–42 cards; target 39

#### Spellslinger (`spellslinger`)

- **ramp_mana_development**: 7–11 cards; target 9
- **card_draw_card_advantage**: 10–16 cards; target 13
- **targeted_removal**: 5–9 cards; target 7
- **board_wipes**: 1–4 cards; target 2
- **strategy_enablers**: 10–16 cards; target 13
- **strategy_payoffs**: 8–12 cards; target 10
- **finishers_win_conditions**: 3–6 cards; target 4
- **protection**: 2–6 cards; target 4
- **lands**: 34–37 cards; target 36

#### Tokens (`tokens`)

- **ramp_mana_development**: 8–12 cards; target 10
- **card_draw_card_advantage**: 8–12 cards; target 10
- **targeted_removal**: 5–9 cards; target 7
- **board_wipes**: 2–4 cards; target 3
- **strategy_enablers**: 10–16 cards; target 13
- **strategy_payoffs**: 8–12 cards; target 10
- **finishers_win_conditions**: 3–6 cards; target 5
- **protection**: 3–6 cards; target 5
- **lands**: 35–38 cards; target 37

#### Voltron (`voltron`)

- **ramp_mana_development**: 7–11 cards; target 9
- **card_draw_card_advantage**: 7–11 cards; target 9
- **targeted_removal**: 5–9 cards; target 7
- **board_wipes**: 1–3 cards; target 2
- **strategy_enablers**: 10–16 cards; target 13
- **strategy_payoffs**: 5–9 cards; target 7
- **finishers_win_conditions**: 2–5 cards; target 3
- **protection**: 8–14 cards; target 11
- **lands**: 34–38 cards; target 36

## Mana Base Planning

Strategy Knowledge can now provide mana-base planning guidance.

### Boundary
- This is mana-base planning guidance only.
- This does not generate a finished mana base.
- This does not insert lands.
- This does not make final deck inclusion decisions or generate a full deck.

### Global Land Rules
- Basic lands are assumed available.
- Nonbasic lands remain collection-first unless outside upgrades are allowed.

### Strategy Mana Plans

#### Aristocrats (`aristocrats`)

- Recommended land band: 35–38 lands; target 37
- Basic land policy: Assume needed basics are available; use them to stabilize colors after owned nonbasic review.
- Nonbasic priorities:
  - untapped duals/fixing lands from collection
  - sacrifice-friendly utility lands if already owned
  - graveyard/recursion utility lands only if color consistency remains stable
- Mana notes:
  - Do not overload colorless utility lands if early sacrifice outlets and payoffs have colored costs.
  - Prefer early untapped sources for engine setup.

#### Landfall / Lands Matter (`landfall_lands_matter`)

- Recommended land band: 37–42 lands; target 39
- Basic land policy: Assume needed basics are available; basics are especially important because many landfall enablers search for basic lands.
- Nonbasic priorities:
  - owned fetch-style lands and evolving/wilds effects
  - lands that enter and sacrifice or recur
  - utility lands that produce landfall value without damaging color consistency
- Mana notes:
  - Higher land count is normal for landfall and should not be treated as a problem by itself.
  - Nonbasic lands are valuable, but basics remain important for search effects.

#### Spellslinger (`spellslinger`)

- Recommended land band: 34–37 lands; target 36
- Basic land policy: Assume needed basics are available; use basics to keep colors stable after owned spell-support lands.
- Nonbasic priorities:
  - owned untapped fixing lands
  - spell-support lands only if color consistency remains strong
  - utility lands that copy/rebuy spells only when not slowing early interaction
- Mana notes:
  - Spellslinger decks need reliable colored mana for cheap interaction and draw.
  - Tapped lands are more punishing when the deck wants to double-spell early.

#### Tokens (`tokens`)

- Recommended land band: 35–38 lands; target 37
- Basic land policy: Assume needed basics are available; use basics to support stable early token production.
- Nonbasic priorities:
  - owned fixing lands that enter untapped early
  - utility lands that produce tokens only if they do not weaken color access
  - go-wide support lands if already owned and on-plan
- Mana notes:
  - Token decks often need early colored mana to start building board presence.
  - Avoid too many tapped lands if the strategy needs to curve out.

#### Voltron (`voltron`)

- Recommended land band: 34–38 lands; target 36
- Basic land policy: Assume needed basics are available; use basics to support reliable commander casting.
- Nonbasic priorities:
  - owned untapped fixing lands
  - utility lands that protect or give evasion only if colors remain stable
  - equipment-support lands if already owned and not too slow
- Mana notes:
  - Voltron decks need reliable early commander mana.
  - Too many tapped or colorless utility lands can delay the commander and weaken the plan.

## Land Insertion Preview

Strategy Knowledge can now preview land-slot insertion recommendations.

### Boundary
- This is a preview only.
- This does not write lands into a deck.
- This does not generate a finished mana base.
- This does not make final deck inclusion decisions or generate a full deck.

### Global Land Rules
- Basic lands are assumed available.
- Nonbasic lands remain collection-first unless outside upgrades are allowed.

### Strategy Land Slot Previews

#### Aristocrats (`aristocrats`)

- Target land slots: 37 within 35–38 land band
- Preview basic land floor: 18
- Preview nonbasic review slots: 19
- Notes:
  - Start from owned fixing lands, then use basics to stabilize colors.
  - Utility lands remain review-only and should support the main strategy.
  - Tapped lands should be limited if the deck needs early setup.

#### Landfall / Lands Matter (`landfall_lands_matter`)

- Target land slots: 39 within 37–42 land band
- Preview basic land floor: 19
- Preview nonbasic review slots: 20
- Notes:
  - Preview more land slots than normal because landfall wants higher land density.
  - Preserve basics for basic-search effects.
  - Review owned fetch-style lands, sacrifice lands, and land-recursion utility lands first.

#### Spellslinger (`spellslinger`)

- Target land slots: 36 within 34–37 land band
- Preview basic land floor: 18
- Preview nonbasic review slots: 18
- Notes:
  - Prioritize untapped colored sources for cheap spells and interaction.
  - Spell-support utility lands should not crowd out color consistency.
  - Tapped lands are previewed cautiously because double-spelling matters.

#### Tokens (`tokens`)

- Target land slots: 37 within 35–38 land band
- Preview basic land floor: 18
- Preview nonbasic review slots: 19
- Notes:
  - Start from owned fixing lands, then use basics to stabilize colors.
  - Utility lands remain review-only and should support the main strategy.
  - Tapped lands should be limited if the deck needs early setup.

#### Voltron (`voltron`)

- Target land slots: 36 within 34–38 land band
- Preview basic land floor: 18
- Preview nonbasic review slots: 18
- Notes:
  - Prioritize early untapped sources for reliable commander casting.
  - Review utility lands only if they do not delay the commander.
  - Protection/evasion lands are review candidates, not automatic insertions.

## Full 100-Card Draft Preview

Strategy Knowledge can now build a preview-only 100-slot Commander draft structure.

### Boundary
- This is a preview only.
- This does not export a final deck.
- This does not lock final deck inclusions.
- This does not generate a finished mana base or write lands into a deck.

### Draft Previews

#### Aristocrats (`aristocrats`)

- Total preview slots: 100
- Commander slots: 1
- Nonland main-deck slots: 62
- Land slots: 37
- Candidate cards previewed: 10
- Unfilled nonland role slots: 52

#### Landfall / Lands Matter (`landfall_lands_matter`)

- Total preview slots: 100
- Commander slots: 1
- Nonland main-deck slots: 60
- Land slots: 39
- Candidate cards previewed: 10
- Unfilled nonland role slots: 50

#### Spellslinger (`spellslinger`)

- Total preview slots: 100
- Commander slots: 1
- Nonland main-deck slots: 63
- Land slots: 36
- Candidate cards previewed: 10
- Unfilled nonland role slots: 53

#### Tokens (`tokens`)

- Total preview slots: 100
- Commander slots: 1
- Nonland main-deck slots: 62
- Land slots: 37
- Candidate cards previewed: 10
- Unfilled nonland role slots: 52

#### Voltron (`voltron`)

- Total preview slots: 100
- Commander slots: 1
- Nonland main-deck slots: 63
- Land slots: 36
- Candidate cards previewed: 10
- Unfilled nonland role slots: 53

## Final Inclusion Lock Integration

Strategy Knowledge can now produce opt-in final-inclusion lock artifacts.

### Boundary
- Final inclusion lock is enabled as an opt-in artifact.
- This does not export a final deck.
- This does not generate a finished mana base.
- This does not write lands into a deck.
- This does not remove the old strategy system.

### Lock Summary
- Strategy lock candidates: 5
- Requires opt-in: True
- Opt-in environment variable: `TDT_STRATEGY_KNOWLEDGE_LIVE_BRIDGE`

## Finished Mana Base Generation Integration

Strategy Knowledge can now generate opt-in finished mana-base artifacts.

### Boundary
- Finished mana-base generation is enabled as an artifact.
- This does not write lands into a deck.
- This does not export a final deck.
- This does not remove the old strategy system.

### Mana Base Summary
- Strategy mana bases generated: 5
- Requires opt-in: True
- Opt-in environment variable: `TDT_STRATEGY_KNOWLEDGE_LIVE_BRIDGE`

## Land Deck-Write Integration

Strategy Knowledge can now produce opt-in land deck-write artifacts.

### Boundary
- Land deck-write is enabled as an artifact.
- This does not export a final deck.
- This does not remove the old strategy system.

### Land Deck-Write Summary
- Strategy land-write entries generated: 5
- Requires opt-in: True
- Opt-in environment variable: `TDT_STRATEGY_KNOWLEDGE_LIVE_BRIDGE`

## Final Deck Export Integration

Strategy Knowledge can now produce opt-in final deck export artifacts.

### Boundary
- Final deck export is enabled as an artifact.
- This does not remove the old strategy system.
- Legacy fallback remains available.

### Final Deck Export Summary
- Strategy exports generated: 5
- Requires opt-in: True
- Opt-in environment variable: `TDT_STRATEGY_KNOWLEDGE_LIVE_BRIDGE`

## Old Strategy System Deprecation / Fallback Cleanup

Strategy Knowledge is now the preferred strategy export path.

### Boundary
- Old strategy system is deprecated, not deleted.
- Legacy fallback remains available.
- Rollback remains available.
- Strategy Knowledge live bridge still requires explicit opt-in.

### Deprecation Summary
- Strategy Knowledge preferred path enabled: True
- Old strategy system deprecated: True
- Old strategy system removed: False
- Legacy pipeline status: deprecated_fallback_only

## v1.4 Full Regression / Lock Candidate

Status: **LOCK_CANDIDATE_FAIL**

### Regression Checks
- Module compile passed: True
- Artifact presence passed: False
- Tool smoke tests passed: True
- Final chain passed: True

### Boundary
- Old strategy files were not deleted.
- Legacy fallback remains available.
- Rollback remains available.
- main.py was not changed by this patch.
