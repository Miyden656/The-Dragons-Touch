# The Dragon’s Touch

**The Dragon’s Touch** is a free local Magic: The Gathering Commander deck review assistant.

It helps players review decklists, identify strategy, understand cut pressure, protect important theme and synergy cards, evaluate replacement needs, and think through collection-only tuning options.

The goal is not to replace the player, Archidekt, Moxfield, EDHREC, or other deckbuilding tools. The goal is to help Commander players make better deckbuilding decisions while keeping the final choice in the player’s hands.

## Current Status

The Dragon’s Touch is currently in **v0.7 alpha tester handoff**.

It is not a polished public release yet. The current focus is private testing, workflow clarity, example documentation, and making sure the tool’s reports are understandable and useful to real Commander players.

## What It Does

The Dragon’s Touch can help review a Commander deck by identifying:

* likely primary and secondary strategy
* commander support level
* cut pressure
* optional optimization cuts
* protected cards
* replacement needs
* collection-only candidates
* playtest notes
* AI handoff prompts for guided deck review

The tool is designed to separate:

* “bad card” from “wrong card for this deck”
* “low power” from “low synergy”
* mandatory legality cuts from optional tuning cuts
* generic upgrades from cards that actually support the pilot’s stated plan

## What It Does Not Do

The Dragon’s Touch does not try to replace the player’s judgment.

It does not claim to solve decks, produce perfect cuts, or create objectively correct decklists. Its recommendations are review candidates and suggested test packages, not commands.

It is also not meant to replace deckbuilding sites, collection trackers, or card databases. It is meant to complement those tools by helping players think through what their deck is trying to do and which changes are worth testing.

## AI Transparency

The Dragon’s Touch is being built with heavy AI assistance.

I am not a professional software developer, and I would not be able to build this from scratch without AI helping with code, structure, debugging, documentation, and workflow design. This is one Commander player with an idea, a lot of testing, and access to tools that make the project possible.

The deckbuilding logic, project goals, test cases, philosophy rules, and review expectations are being shaped through repeated human testing and correction.

## Why I Started Building This

The Dragon’s Touch started because I love Commander deckbuilding, but I was spending more time preparing to play than actually playing.

I would lose hours researching cards, sorting through my collection, comparing possible upgrades, and trying to figure out which owned cards actually fit a deck. As work, family, and limited hobby time made that harder, I wanted a way to reduce the busywork without removing the creativity, theme, or final decision-making that makes Commander fun.

The goal is to help players spend less time buried in sorting and searching, and more time making meaningful deck decisions and actually playing the game.

## Example Review

### Example 001 — Phelia, Exuberant Shepherd: “Corgi Butt”

The first clean showcase example is a Phelia, Exuberant Shepherd deck called **Corgi Butt**.

This example demonstrates:

* legal 100-card deck review
* optional tuning instead of mandatory cuts
* collection-only / $0 budget recommendations
* Theme / Vibe philosophy lens
* pilot-corrected strategy
* protected theme and function cards
* suggested playtest package

The tool initially read the deck as:

* Primary strategy: Token Combat / Go-Wide-Go-Tall
* Secondary strategy: Cast From Outside Hand Value

During the guided review, the pilot corrected the secondary strategy to:

* ETB Control / Flicker Control

The final suggested test package was:

Out:

* Soul Tithe
* Divine Gambit
* Sisay’s Ring

In:

* Hanged Executioner
* Odric, Lunarch Marshal
* Ajani, Caller of the Pride

These are not presented as perfect or mandatory changes. They are suggested playtest swaps based on the pilot’s stated goal, collection-only budget, and desired deck identity.

## Unofficial Project Disclaimer

The Dragon’s Touch is an unofficial fan/community project.

It is not affiliated with, endorsed by, sponsored by, or approved by Wizards of the Coast, Hasbro, Archidekt, Moxfield, EDHREC, Scryfall, Cardmill, or any other Magic: The Gathering, deckbuilding, card database, or collection-management platform.

Magic: The Gathering and related names are property of their respective owners.

Part of the collection-focused direction was inspired by collection organization workflows such as Cardmill. The Dragon’s Touch is not affiliated with or endorsed by Cardmill.

## Current Limitations

The Dragon’s Touch is still in alpha testing.

Known limitations:

* reports may misread a deck’s strategy and require pilot correction
* recommendations should be treated as review candidates, not automatic upgrades
* collection-only suggestions depend on the quality and formatting of collection data
* the desktop UI is still being developed and refined
* some reports may be verbose or need cleanup before public sharing
* the tool is currently best suited for guided testing, not broad public release

## For Alpha Testers

When testing The Dragon’s Touch, please focus on whether the review is useful, understandable, and respectful of the deck’s intent.

Useful feedback includes:

* Did the strategy read make sense?
* Did the tool misunderstand the deck?
* Were the cut suggestions fair?
* Did it protect important theme, synergy, or pet cards?
* Were collection-only recommendations actually useful?
* Did anything feel too pushy, confusing, or overconfident?
* Did the final report help you decide what to test next?

The most helpful feedback is not “the tool was right.” The most helpful feedback is where the tool was unclear, wrong, too aggressive, or missing something important.
