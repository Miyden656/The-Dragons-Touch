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
