"""Premium fixing lands for multi-color Commander decks (v1.6.2 Phase D).

WHY THIS FILE EXISTS
--------------------
The v1.6.1 audit on the Omnath, Locus of All 5-color build flagged that
nonbasic lands were chosen by alphabetical sort, not by color-fixing
utility. A 5-color deck would happily take 17 random mono-color utility
lands before a Command Tower or triome. This module is the curated
preference list the builder consults when the commander has 2+ colors.

POLICY
------
- Mono-color decks: this module is not used. The existing alphabetical
  sort works fine because mono-color decks need basics + utility, not
  fixing.
- Two-color and three-color decks: premium fixers tier 1 + tier 2.
- Four- and five-color decks: any tier-1 fixer is high priority.

When the bracket policy changes or new lands print, update PREMIUM_FIXERS
below and the test will catch any regressions.

PUBLIC API
----------
- PREMIUM_FIXERS                   : frozenset of card names (lower-case)
- TIER_1_FIXERS                    : frozenset — the "always include" set
- TIER_2_FIXERS                    : frozenset — strong fixers
- is_premium_fixer(card_name)      -> bool
- fixer_priority(card_name)        -> int (0 = best, higher = worse)
- prefers_premium_fixers(commander_color_count) -> bool
"""
from __future__ import annotations


# Tier 1 — top-priority fixers for any multi-color deck. Curated based on
# the standard Commander mana-base meta as of 2025: any-color producers,
# triomes, and shock-and-fetch staples. Always include these when
# available.
TIER_1_FIXERS: frozenset[str] = frozenset({
    # Any-color producers — first-pick in any multi-color deck.
    "command tower",
    "reflecting pool",
    "exotic orchard",
    "city of brass",
    "mana confluence",
    "forbidden orchard",
    "fabled passage",
    "prismatic vista",
    "path of ancestry",  # also tribal-relevant

    # Triomes (Ikoria + MOM + Bloomburrow + others).
    "indatha triome", "ketria triome", "raugrin triome", "savai triome",
    "zagoth triome", "jetmir's garden", "ketria triome", "ziatora's proving ground",
    "spara's headquarters", "raffine's tower", "xander's lounge",
    # MH3 surveil-triomes.
    "spara's headquarters",
    # The 4-color "nephilim" or other triome-style lands.

    # Shocklands.
    "hallowed fountain", "watery grave", "blood crypt", "stomping ground",
    "temple garden", "sacred foundry", "godless shrine", "breeding pool",
    "overgrown tomb", "steam vents",

    # Fetchlands (enemy).
    "polluted delta", "flooded strand", "bloodstained mire",
    "wooded foothills", "windswept heath",
    # Fetchlands (allied).
    "marsh flats", "scalding tarn", "verdant catacombs",
    "misty rainforest", "arid mesa",

    # Original duals (only if user owns; bracket filter at B1/B2 still
    # considers them fast mana via role tags).
    "tundra", "underground sea", "badlands", "taiga", "savannah",
    "scrubland", "volcanic island", "bayou", "plateau", "tropical island",

    # Battlebond duals.
    "sea of clouds", "morphic pool", "luxury suite", "spire garden",
    "bountiful promenade",
    # Surveil duals (MKM).
    "lush portico", "underground mortuary", "raucous theater",
    "shadowy backstreet", "thundering falls", "elegant parlor",
    "meticulous archive", "commercial district", "undercity sewers",
    "hedge maze",
})


# Tier 2 — strong but not as universal. Helpful when tier-1 has been
# exhausted or the commander is only 2 colors.
TIER_2_FIXERS: frozenset[str] = frozenset({
    # Check lands.
    "sunpetal grove", "rootbound crag", "sulfur falls", "hinterland harbor",
    "glacial fortress", "drowned catacomb", "isolated chapel",
    "dragonskull summit", "clifftop retreat", "woodland cemetery",

    # Bond lands / Spire of Industry.
    "spire of industry",

    # Pain lands.
    "adarkar wastes", "underground river", "sulfurous springs",
    "karplusan forest", "brushland", "yavimaya coast", "battlefield forge",
    "caves of koilos", "shivan reef", "llanowar wastes",

    # Filter lands.
    "graven cairns", "skycloud expanse", "wooded bastion", "fetid heath",
    "rugged prairie", "twilight mire", "fire-lit thicket", "mystic gate",
    "flooded grove", "sunken ruins",

    # Scry / temple lands.
    "temple of plenty", "temple of mystery", "temple of malady",
    "temple of triumph", "temple of malice", "temple of enlightenment",
    "temple of silence", "temple of epiphany", "temple of abandon",
    "temple of deceit",

    # Gain lands.
    "sandsteppe citadel", "frontier bivouac", "opulent palace",
    "mystic monastery", "nomad outpost", "arcane sanctum",
    "jungle shrine", "savage lands", "seaside citadel", "crumbling necropolis",

    # Castle / utility-fixer hybrids.
    "krosan verge", "terramorphic expanse", "evolving wilds",
    "rupture spire", "transguild promenade", "ash barrens",
})


PREMIUM_FIXERS: frozenset[str] = TIER_1_FIXERS | TIER_2_FIXERS


def is_premium_fixer(card_name: str | None) -> bool:
    """Return True if the card name is on either tier of premium fixers."""
    if not card_name:
        return False
    return card_name.strip().lower() in PREMIUM_FIXERS


def fixer_priority(card_name: str | None) -> int:
    """Return a priority sort key: 0 = tier 1, 1 = tier 2, 2 = neither.

    Lower number sorts first. Use as the primary sort key for nonbasic
    lands in multi-color decks; ties fall back to alphabetical.
    """
    if not card_name:
        return 2
    name = card_name.strip().lower()
    if name in TIER_1_FIXERS:
        return 0
    if name in TIER_2_FIXERS:
        return 1
    return 2


def prefers_premium_fixers(commander_color_count: int) -> bool:
    """Return True if the commander's deck should prefer premium fixers.

    Two- and higher-color decks benefit from the curated list. Mono-color
    and colorless decks use the existing alphabetical sort because they
    don't need color fixing.
    """
    return int(commander_color_count or 0) >= 2
