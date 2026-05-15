# v0.8.7.2.1-dev — Commander Spellbook Combo Data Audit Path Cleanup

## Scope Guard

This audit is isolated research for The Dragon's Touch v0.8 Commander Spellbook / Combo Awareness.

- It does not modify the locked v0.7.22 alpha tester ZIP.
- It does not change `main.py`.
- It does not connect to the PySide6 UI.
- It does not add combo findings to reports yet.
- It does not call the Commander Spellbook API.
- It only inspects local `data/combo.json`.

## Source File

- Path: `data\combo.json`
- Size: 476.9 MB
- Audit generated: 2026-05-14T19:56:34

## Top-Level Metadata

- Combo data version: `5.4.7`
- Combo data timestamp: `2026-05-14T11:23:10.884507+00:00`
- Total variants: 88,116
- Aliases entries: 1377

## Key Counts

- Commander-legal variants: 86,728 (98.4%)
- Spoiler-tagged variants: 297 (0.3%)
- Variants with at least one must-be-commander card: 910 (1.0%)
- Variants with non-empty `requires`: 3,302
- Variants with non-empty `produces`: 88,112
- Use entries with quantity other than 1: 0
- Use entries missing card names: 0

### Status Distribution

| Value | Count |
|---|---:|
| OK | 88116 |

### Bracket Tag Distribution

| Value | Count |
|---|---:|
| E | 75507 |
| R | 5829 |
| S | 2845 |
| P | 2089 |
| B | 1388 |
| C | 244 |
| O | 214 |

### Combo Size Distribution Based on uses Count

| Value | Count |
|---|---:|
| 3 | 41264 |
| 4 | 36053 |
| 5 | 6217 |
| 2 | 4528 |
| 6 | 30 |
| 1 | 7 |
| 7 | 7 |
| 8 | 5 |
| 9 | 4 |
| 10 | 1 |

### Top Color Identity Values

| Value | Count |
|---|---:|
| GU | 5040 |
| WB | 4419 |
| U | 4196 |
| WUBRG | 3997 |
| UR | 3897 |
| BG | 3386 |
| BR | 3252 |
| GW | 3189 |
| WBG | 3074 |
| G | 3054 |
| UB | 3018 |
| RWB | 2969 |
| B | 2883 |
| RGW | 2811 |
| WU | 2793 |
| GWU | 2787 |
| RW | 2757 |
| GUR | 2653 |
| BRG | 2649 |
| BGU | 2545 |
| URW | 2537 |
| RG | 2444 |
| UBR | 2248 |
| W | 2198 |
| WUB | 2196 |
| R | 2174 |
| BRGW | 2042 |
| RGWU | 1901 |
| GWUB | 1459 |
| UBRG | 1418 |
| WUBR | 1323 |
| C | 807 |

### Top Produced Features

| Value | Count |
|---|---:|
| Infinite ETB | 56221 |
| Infinite LTB | 48873 |
| Infinite death triggers | 39656 |
| Infinite sacrifice triggers | 37903 |
| Infinite storm count | 19248 |
| Infinite colored mana | 11330 |
| Infinite creature tokens | 9396 |
| Infinite +1/+1 counters on a creature | 8669 |
| Infinite draw triggers | 8647 |
| Infinite colorless mana | 8187 |
| Infinite lifegain triggers | 8053 |
| Infinite landfall triggers | 7164 |
| Infinite card draw | 6631 |
| Infinite magecraft triggers | 6353 |
| Infinite lifegain | 6278 |
| Infinite damage | 6272 |
| Lock | 6085 |
| Near-infinite ETB | 5190 |
| Infinite untap of creatures you control | 4807 |
| Infinite mana creatures you control can produce | 4798 |
| Infinite turns | 4754 |
| Infinite self-mill | 4227 |
| Near-infinite LTB | 4219 |
| Near-infinite death triggers | 3459 |
| Near-infinite storm count | 3402 |
| Near-infinite sacrifice triggers | 3339 |
| Infinite tapped creature tokens | 3249 |
| Infinite self-discard triggers | 3119 |
| Infinite +1/+1 counters on creatures you control | 3058 |
| Infinite combat phases | 3055 |
| Infinite scry 1 | 2779 |
| Infinite lifeloss | 2715 |
| Infinite Treasure tokens | 2600 |
| Infinite creature tokens with haste | 2589 |
| Infinite red mana | 2570 |
| Infinite mana lands you control can produce | 2467 |
| Infinite mill | 2165 |
| Infinitely large creature until end of turn | 2016 |
| Infinite green mana | 2000 |
| Infinite combat damage | 1849 |

## Fields Observed

### Variant Top-Level Fields

```json
[
  "bracketTag",
  "description",
  "easyPrerequisites",
  "id",
  "identity",
  "includes",
  "legalities",
  "manaNeeded",
  "manaValueNeeded",
  "notablePrerequisites",
  "notes",
  "of",
  "popularity",
  "prices",
  "produces",
  "requires",
  "spoiler",
  "status",
  "uses",
  "variantCount"
]
```

### `uses` Entry Fields

```json
[
  "battlefieldCardState",
  "card",
  "exileCardState",
  "graveyardCardState",
  "libraryCardState",
  "mustBeCommander",
  "quantity",
  "zoneLocations"
]
```

### Nested `card` Fields

```json
[
  "id",
  "imageUriBackArtCrop",
  "imageUriBackLarge",
  "imageUriBackNormal",
  "imageUriBackPng",
  "imageUriBackSmall",
  "imageUriFrontArtCrop",
  "imageUriFrontLarge",
  "imageUriFrontNormal",
  "imageUriFrontPng",
  "imageUriFrontSmall",
  "layoutRotationFront",
  "name",
  "oracleId",
  "spoiler",
  "typeLine"
]
```

## First Index Candidate Fields

These are the fields that look useful for a future compact `combo_index.json`.

- `id`
- `status`
- `uses.card.name`
- `uses.card.oracleId`
- `uses.mustBeCommander`
- `uses.quantity`
- `uses.zoneLocations`
- `requires`
- `produces.feature.name`
- `identity`
- `easyPrerequisites`
- `notablePrerequisites`
- `description`
- `notes`
- `spoiler`
- `bracketTag`
- `legalities.commander`

## Fields to Exclude From First Index

- prices
- card image URI fields
- large nested frontend display data
- popularity, unless later used for sorting
- aliases, unless later needed for card-name normalization

## Sample Variants

Small samples only. Card images, prices, and large nested card payloads are intentionally omitted.

```json
[
  {
    "id": "1558-5471-7651",
    "status": "OK",
    "cards": [
      "Obeka, Splitter of Seconds",
      "Smaug the Magnificent",
      "Time Sieve"
    ],
    "must_be_commander": [],
    "identity": "UBR",
    "produces": [
      "Infinite turns",
      "Lock"
    ],
    "spoiler": true,
    "bracketTag": "R",
    "commander_legal": true,
    "description": "At the beginning of your upkeep, Smaug triggers, creating a Treasure token.\nDeal combat damage using Obeka, triggering its ability, causing you to get at least four extra upkeep steps.\nRepeat step 1 during each extra upkeep step, creating at least four additional Treasures.\nActivate Time Sieve by tapping it and sacrificing five Treasures, causing you to take an extra turn after this one.\nRepeat each turn.",
    "easyPrerequisites": "",
    "notablePrerequisites": "An opponent cannot block Obeka."
  },
  {
    "id": "3750-7283-7651",
    "status": "OK",
    "cards": [
      "Smaug the Magnificent",
      "Raphael, Ninja Destroyer",
      "Aggravated Assault"
    ],
    "must_be_commander": [],
    "identity": "R",
    "produces": [
      "Infinite combat phases",
      "Infinite damage",
      "Infinite mana creatures you control can produce",
      "Infinite red mana",
      "Infinite untap of creatures you control"
    ],
    "spoiler": true,
    "bracketTag": "E",
    "commander_legal": true,
    "description": "Declare Smaug as an attacker, triggering its ability, dealing at least 5 damage to Raphael.\nRaphael triggers, adding at least {R}{R}{R}{R}{R}.\nMove to your postcombat main phase.\nActivate Aggravated Assault by paying {3}{R}{R}, causing you to untap all creatures you control and get an additional combat and main phase after this one.\nRepeat",
    "easyPrerequisites": "",
    "notablePrerequisites": "You control at least five Treasures.\nRaphael is indestructible.\nAn opponent cannot block and kill Smaug."
  },
  {
    "id": "2034-3356-5003-7649",
    "status": "OK",
    "cards": [
      "Nim Deathmantle",
      "Ashnod's Altar",
      "Thorin, Mountain-king",
      "Polyraptor"
    ],
    "must_be_commander": [],
    "identity": "RG",
    "produces": [
      "Infinite ETB",
      "Infinite LTB",
      "Infinite death triggers",
      "Infinite sacrifice triggers"
    ],
    "spoiler": true,
    "bracketTag": "E",
    "commander_legal": true,
    "description": "Activate Ashnod's Altar by sacrificing Thorin, adding {C}{C}.\nWhen Thorin dies, Nim Deathmantle triggers, causing you to pay {4} to return Thorin from your graveyard to the battlefield and attach Nim Deathmantle to it.\nWhen Thorin enters, it triggers, attaching Nim Deathmantle to Polyraptor, and then having it deal damage to itself.\nPolyraptor triggers, creating a creature token.\nActivate Ashnod's Altar by sacrificing the creature token, adding {C}{C}.\nRepeat.",
    "easyPrerequisites": "",
    "notablePrerequisites": "Polyraptor has indestructible."
  }
]
```

## Non-Spoiler Sample Variants

```json
[
  {
    "id": "1912-4893-7426-7648",
    "status": "OK",
    "cards": [
      "Berta, Wise Extrapolator",
      "Assassin Den",
      "Training Grounds",
      "Biomancer's Familiar"
    ],
    "must_be_commander": [],
    "identity": "GU",
    "produces": [
      "Infinite +1/+1 counters on a creature"
    ],
    "spoiler": false,
    "bracketTag": "E",
    "commander_legal": true,
    "description": "Activate Assassin Den by paying {U} due to Training Grounds and Biomancer's Familiar, putting a +1/+1 counter on Berta.\nBerta triggers, adding {U}.\nRepeat.",
    "easyPrerequisites": "",
    "notablePrerequisites": ""
  },
  {
    "id": "2713-4893-7426-7648",
    "status": "OK",
    "cards": [
      "Berta, Wise Extrapolator",
      "Assassin Den",
      "Training Grounds",
      "Zirda, the Dawnwaker"
    ],
    "must_be_commander": [],
    "identity": "RGWU",
    "produces": [
      "Infinite +1/+1 counters on a creature"
    ],
    "spoiler": false,
    "bracketTag": "E",
    "commander_legal": true,
    "description": "Activate Assassin Den by paying {U} due to Training Grounds and Zirda, putting a +1/+1 counter on Berta.\nBerta triggers, adding {U}.\nRepeat.",
    "easyPrerequisites": "",
    "notablePrerequisites": ""
  },
  {
    "id": "186-4893-7426-7648",
    "status": "OK",
    "cards": [
      "Berta, Wise Extrapolator",
      "Assassin Den",
      "Training Grounds",
      "Heartstone"
    ],
    "must_be_commander": [],
    "identity": "GU",
    "produces": [
      "Infinite +1/+1 counters on a creature"
    ],
    "spoiler": false,
    "bracketTag": "E",
    "commander_legal": true,
    "description": "Activate Assassin Den by paying {U} due to Training Grounds and Heartstone, putting a +1/+1 counter on Berta.\nBerta triggers, adding {U}.\nRepeat.",
    "easyPrerequisites": "",
    "notablePrerequisites": ""
  }
]
```

## v0.8.1 Recommendation

Proceed to `v0.8.1-dev — Local Combo Index Builder` only after reviewing this audit.

The first index should be local/offline and should remove images, prices, and large frontend-only card data.

Recommended next generated file:

```text
data/commander_spellbook/combo_index.json
```

Recommended next script:

```text
tools/build_combo_index.py
```

Do not connect this to the main report, UI, or normal deck analysis yet.
