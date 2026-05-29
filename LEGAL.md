# Legal & Acknowledgments

The Dragon's Touch is a free, unofficial, community-built Commander deck-building support tool for *Magic: The Gathering*. This document covers trademark notices, data-source attributions, third-party software credits, and the project's own intellectual property.

If you spot a missing or incorrect attribution, please open an issue on the project repository.

---

## Wizards of the Coast — Fan Site notice

This project is not affiliated with, endorsed, sponsored, or specifically approved by Wizards of the Coast LLC. The Dragon's Touch uses the trademarks and other intellectual property of Wizards of the Coast LLC under the terms of Wizards' [Fan Content Policy](https://company.wizards.com/en/legal/fancontentpolicy) and Fan Site Kit.

**MAGIC: THE GATHERING**® is a trademark of Wizards of the Coast LLC, a subsidiary of Hasbro, Inc.

Card names, card images, card text, card mechanics, set names, and all other Magic-related intellectual property are © Wizards of the Coast LLC. No claim of ownership is made over any Magic: The Gathering content surfaced by this tool.

This project does not sell goods or services using Wizards of the Coast trademarks, does not imply endorsement, does not distribute card images outside of the player's local context, and does not redistribute Wizards-owned intellectual property as primary content.

---

## Data sources

### Scryfall

Card data (names, mana costs, type lines, oracle text, color identity, set legality, image URIs, and related metadata) is provided by [Scryfall](https://scryfall.com/), used under the terms of their [data licensing](https://scryfall.com/docs/api).

> *"This product uses data and images from Scryfall but is unofficial and not endorsed by Scryfall."*

The Dragon's Touch downloads Scryfall's bulk-data JSON via Scryfall's documented bulk-data endpoint, caches it locally, and never re-publishes the bulk dataset.

### Commander Spellbook

Combo detection and combo data is based on the [Commander Spellbook](https://commanderspellbook.com/) database, an open community-maintained catalog of Magic: The Gathering combos.

> *"This product uses combo data from Commander Spellbook but is unofficial and not endorsed by the Commander Spellbook project."*

The Dragon's Touch reads the Commander Spellbook bulk JSON, builds a local index for offline lookup, and does not re-publish the combo dataset.

---

## Third-party software

### PySide6 / Qt for Python

The desktop UI is built on [PySide6](https://wiki.qt.io/Qt_for_Python), the official Python bindings for the [Qt](https://www.qt.io/) framework, licensed under the LGPL-3.0.

PySide6 and Qt are © The Qt Company Ltd. and contributors. Their license is preserved in this distribution; nothing about The Dragon's Touch modifies or sublicenses PySide6 or Qt.

### Python Standard Library

Various modules from the Python standard library are used (pathlib, json, runpy, subprocess, etc.). Python is licensed under the [Python Software Foundation License](https://docs.python.org/3/license.html).

---

## What's mine (project copyright)

Copyright © 2026 Bruce — the creator of The Dragon's Touch.

The following original work is part of The Dragon's Touch and copyright of the project author:

- The name **"The Dragon's Touch"** and the dragon-mascot identity used to brand the app
- The **six-signal scoring chain** design that combines bracket filtering, commander-text amplification, philosophy/persona bias, combo-awareness, role-tag overrides, and curated strategy-profile matching (see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the technical description)
- The **18 sub-philosophy personas** that drive deck-building intent (Engine Builder, Combo Builder, Battlecruiser, Big Moment, Efficiency Optimizer, Power-Level Calibrator, etc.)
- The **249-profile strategy catalog** with 46 hand-curated strategy-defining tag sets
- The **role-tagging system** including 51 EDH-staple overrides
- The **Commander's Call** workflow design (collection-first scan → role bucketing → rough shell guidance → full 100-card draft)
- The **UI design** — theme system, page layouts, the "Dragon Forge" theme, card-style report panels, and original mascot art
- All original Python source code authored for the project

You are welcome to:
- Use this tool for your personal Commander deck-building
- Share screenshots of generated reports for personal commentary, deck-tech videos, or discussion
- Reference The Dragon's Touch's scoring chain or persona system in articles and discussion with credit

You are asked NOT to:
- Repackage and redistribute The Dragon's Touch under a different name or claim authorship
- Use the "Dragon's Touch" name to brand a competing or derivative tool
- Sell access to The Dragon's Touch or charge for builds derived from it
- Strip the trademark notices in this file from any redistribution

If you'd like to fork, contribute, or build something related, please reach out via the project repository — collaboration is welcome on the right terms.

---

## No warranty

The Dragon's Touch is provided as-is, without warranty of any kind. The deck recommendations, cut suggestions, replacement candidates, role-bucket placements, and combo flags surfaced by this tool are heuristic and exploratory — they are not authoritative card-evaluation rulings. Pilot judgement remains the final authority on every deck-building decision.

The Dragon's Touch does not provide legal, financial, or rules advice. Magic: The Gathering rules questions should be directed to the [official MTG comprehensive rules](https://magic.wizards.com/en/rules) or a certified judge.

---

## Contact

For trademark concerns, takedown requests, or attribution corrections, please open an issue on the project repository.
