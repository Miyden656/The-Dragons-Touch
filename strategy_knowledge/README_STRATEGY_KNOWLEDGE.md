# The Dragon's Touch — Strategy Knowledge Base Schema Lock Candidate

Version: v1.4.0 schema lock candidate

This folder defines the local strategy knowledge-base contract for future Strategy Deep Dive integration.

## Purpose

The strategy knowledge base is meant to improve:

- strategy recognition
- commander intent recognition
- role bucket mapping
- owned-card role classification
- cut logic
- protection logic
- replacement logic
- synergy detection
- off-plan card detection
- rough shell guidance
- full draft planning
- AI handoff prompt quality

## Current Boundary

This schema does not generate decks.
This schema does not choose final cards.
This schema does not build mana bases.
This schema only defines the contract future strategy files must satisfy.

## Active Contract Files

- `strategy_schema.json` — required YAML frontmatter schema
- `strategy_index.example.json` — index format example
- `tags/role_bucket_tags.json` — global role bucket registry
- `templates/strategy_file_template.md` — canonical markdown template

## Basic Land Policy

All strategy files must declare:

```yaml
basic_land_policy: "assume_available"
```

This preserves the v1.3 rule that users are assumed to have access to all needed basic lands.

## Nonbasic Land Policy

Nonbasic lands remain collection-first unless outside-collection upgrades are allowed:

```yaml
nonbasic_land_policy: "collection_first_unless_upgrades_allowed"
```

## Layer IDs

- `01_macro_archetypes`
- `02_mechanical_themes`
- `03_board_politics_and_table_roles`
- `04_typal_tribal`
- `05_niche_themes`
- `06_fringe_themes`
- `07_emergent_themes`

## Required Quality

Every runtime-ready strategy file should be at least 40KB and should include all required markdown sections from the template.
