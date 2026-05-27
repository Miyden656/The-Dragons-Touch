"""Rough Shell role guidance data (Bin B Phase 3 v1.5.36).

For each strategy archetype, ARCHETYPE_DEFINITIONS in analysis/strategy_scoring.py
lists role-tag IDs under anchors / payoffs / enablers. This module translates
those role-tag IDs into human-readable "what to look for in your collection"
guidance: a friendly label, what the role does in plain English, oracle-text
keywords likely to indicate the role, common card types, and example effects.

The Rough Shell Output uses this to tell the user what to scan their collection
for when building around a commander + selected strategy. This is guidance only:
it does NOT select cards, generate a shell, or write a deck list.
"""
from __future__ import annotations

from typing import Any


# Each entry: friendly label + 3 user-facing fields.
ROLE_GUIDANCE: dict[str, dict[str, Any]] = {
    "ramp": {
        "label": "Ramp / Mana Acceleration",
        "what_it_does": "Gets you more mana faster so big plays land earlier.",
        "oracle_keywords": [
            "search your library for a basic land",
            "search your library for a land",
            "add {C} or add one mana",
            "put a land from your hand onto the battlefield",
        ],
        "card_types": ["Sorcery", "Instant", "Artifact (mana rock)", "Creature (mana dork)"],
        "examples": [
            "Land searches: Cultivate, Kodama's Reach, Rampant Growth, Three Visits",
            "Mana rocks: Sol Ring, Arcane Signet, Talisman cycle, Signet cycle",
            "Mana dorks: Llanowar Elves, Birds of Paradise, Elvish Mystic",
            "Cheats: Skyshroud Claim, Explosive Vegetation",
        ],
    },
    "mana_rock": {
        "label": "Mana Rocks",
        "what_it_does": "Artifacts that tap for mana — repeatable acceleration.",
        "oracle_keywords": ["{T}: Add", "tap to add", "add {C}", "add one mana of any color"],
        "card_types": ["Artifact"],
        "examples": ["Sol Ring", "Arcane Signet", "Mind Stone", "Talisman of Curiosity", "Thran Dynamo"],
    },
    "mana_dork": {
        "label": "Mana Dorks",
        "what_it_does": "1-2 CMC creatures that tap for mana.",
        "oracle_keywords": ["{T}: Add", "tap to add"],
        "card_types": ["Creature"],
        "examples": ["Llanowar Elves", "Elvish Mystic", "Birds of Paradise", "Sylvan Caryatid"],
    },
    "extra_land_play": {
        "label": "Extra Land Drops",
        "what_it_does": "Lets you play more than one land per turn.",
        "oracle_keywords": ["may play an additional land", "play an extra land", "you may play any number of additional lands"],
        "card_types": ["Land", "Enchantment", "Creature"],
        "examples": ["Exploration", "Azusa, Lost but Seeking", "Oracle of Mul Daya", "Dryad of the Ilysian Grove"],
    },
    "mana_doubler": {
        "label": "Mana Doublers",
        "what_it_does": "Doubles or multiplies mana production from lands or other sources.",
        "oracle_keywords": ["produce twice", "produce that much mana", "double the mana"],
        "card_types": ["Land", "Enchantment", "Artifact"],
        "examples": ["Cabal Coffers", "Mana Reflection", "Caged Sun", "Nyxbloom Ancient"],
    },
    "card_draw": {
        "label": "Card Draw",
        "what_it_does": "Refills your hand so you don't run out of plays.",
        "oracle_keywords": ["draw a card", "draw two cards", "draw cards equal to"],
        "card_types": ["Instant", "Sorcery", "Enchantment", "Creature"],
        "examples": ["Rhystic Study", "Mystic Remora", "Esper Sentinel", "Sign in Blood"],
    },
    "card_advantage": {
        "label": "Card Advantage Engines",
        "what_it_does": "Repeatable draw or selection that pulls ahead over time.",
        "oracle_keywords": ["whenever ... draw", "at the beginning of your upkeep, draw", "draw a card. then"],
        "card_types": ["Enchantment", "Artifact", "Creature"],
        "examples": ["Rhystic Study", "Smothering Tithe", "Sylvan Library", "Greater Good"],
    },
    "card_selection": {
        "label": "Card Selection / Filtering",
        "what_it_does": "Scry, surveil, or top-deck manipulation to find what you need.",
        "oracle_keywords": ["scry", "surveil", "look at the top", "reveal the top"],
        "card_types": ["Instant", "Sorcery", "Enchantment"],
        "examples": ["Brainstorm", "Ponder", "Preordain", "Sylvan Library"],
    },
    "targeted_removal": {
        "label": "Targeted Removal",
        "what_it_does": "Answers one specific threat — a creature, a planeswalker, etc.",
        "oracle_keywords": ["destroy target", "exile target", "deal damage to target", "counter target"],
        "card_types": ["Instant", "Sorcery"],
        "examples": ["Swords to Plowshares", "Path to Exile", "Beast Within", "Generous Gift"],
    },
    "board_wipe": {
        "label": "Board Wipes",
        "what_it_does": "Sweeps the board to reset against go-wide opponents.",
        "oracle_keywords": ["destroy all creatures", "exile all creatures", "each creature gets -X/-X", "all creatures get"],
        "card_types": ["Sorcery", "Instant"],
        "examples": ["Wrath of God", "Damnation", "Toxic Deluge", "Cyclonic Rift"],
    },
    "counterspell": {
        "label": "Counterspells",
        "what_it_does": "Stops spells before they resolve.",
        "oracle_keywords": ["counter target", "counter that spell", "counter target spell"],
        "card_types": ["Instant"],
        "examples": ["Counterspell", "Swan Song", "Negate", "An Offer You Can't Refuse"],
    },
    "protection": {
        "label": "Protection / Commander Defense",
        "what_it_does": "Keeps your commander or key engine pieces alive.",
        "oracle_keywords": ["hexproof", "indestructible", "protection from", "shroud", "ward"],
        "card_types": ["Instant", "Enchantment", "Equipment"],
        "examples": ["Lightning Greaves", "Swiftfoot Boots", "Heroic Intervention", "Teferi's Protection"],
    },
    "pillowfort": {
        "label": "Pillowfort / Threat Deterrence",
        "what_it_does": "Discourages opponents from attacking you.",
        "oracle_keywords": ["can't attack you", "attacks each opponent", "must attack a player other than you"],
        "card_types": ["Enchantment"],
        "examples": ["Ghostly Prison", "Propaganda", "Sphere of Safety", "Crawlspace"],
    },
    "recursion": {
        "label": "Recursion / Graveyard Return",
        "what_it_does": "Brings cards back from the graveyard for repeat value.",
        "oracle_keywords": ["return target ... from your graveyard", "return ... from your graveyard to your hand", "from your graveyard to the battlefield"],
        "card_types": ["Sorcery", "Instant", "Creature", "Enchantment"],
        "examples": ["Eternal Witness", "Regrowth", "Reanimate", "Animate Dead"],
    },
    "etb_value": {
        "label": "Enter-the-Battlefield (ETB) Value",
        "what_it_does": "Triggers that fire when a creature enters, generating value each time.",
        "oracle_keywords": ["enters the battlefield", "when ... enters", "whenever a creature enters"],
        "card_types": ["Creature", "Enchantment"],
        "examples": ["Mulldrifter", "Reflector Mage", "Solemn Simulacrum", "Panharmonicon"],
    },
    "sacrifice_outlet": {
        "label": "Sacrifice Outlets",
        "what_it_does": "Lets you sacrifice creatures at will to trigger payoffs.",
        "oracle_keywords": ["sacrifice a creature: ", "sacrifice another creature", "as an additional cost ... sacrifice"],
        "card_types": ["Creature", "Artifact", "Enchantment"],
        "examples": ["Viscera Seer", "Ashnod's Altar", "Phyrexian Altar", "Goblin Bombardment"],
    },
    "free_sacrifice_outlet": {
        "label": "Free Sacrifice Outlets",
        "what_it_does": "Sacrifice outlets with no activation cost beyond the sacrifice itself.",
        "oracle_keywords": ["sacrifice a creature:", "sacrifice another creature:"],
        "card_types": ["Creature", "Artifact"],
        "examples": ["Viscera Seer", "Carrion Feeder", "Yahenni, Undying Partisan"],
    },
    "death_trigger_payoff": {
        "label": "Death-Trigger Payoffs",
        "what_it_does": "Cards that reward creatures dying.",
        "oracle_keywords": ["whenever a creature dies", "whenever ... dies", "dies trigger"],
        "card_types": ["Creature", "Enchantment"],
        "examples": ["Zulaport Cutthroat", "Blood Artist", "Grave Pact", "Pitiless Plunderer"],
    },
    "sacrifice_payoff": {
        "label": "Sacrifice Payoffs",
        "what_it_does": "Cards that reward you for sacrificing.",
        "oracle_keywords": ["whenever you sacrifice", "if you would sacrifice", "you sacrifice another creature"],
        "card_types": ["Creature", "Enchantment"],
        "examples": ["Mayhem Devil", "Korvold, Fae-Cursed King", "Pitiless Plunderer"],
    },
    "token_maker": {
        "label": "Token Generators",
        "what_it_does": "Creates creature tokens for go-wide strategies or as fodder.",
        "oracle_keywords": ["create a creature token", "create X creature tokens", "create a token"],
        "card_types": ["Sorcery", "Instant", "Enchantment", "Creature"],
        "examples": ["Bitterblossom", "Dragon Tempest (with dragons)", "Cathars' Crusade lines", "Anointed Procession + token producer"],
    },
    "anthem": {
        "label": "Anthems / Team-Wide Buffs",
        "what_it_does": "Pumps all your creatures, scaling with board width.",
        "oracle_keywords": ["creatures you control get +", "other creatures you control get +", "as long as you control"],
        "card_types": ["Enchantment", "Creature"],
        "examples": ["Glorious Anthem", "Crusade-style effects", "Coat of Arms", "Door of Destinies"],
    },
    "combat_synergy": {
        "label": "Combat Synergy",
        "what_it_does": "Triggers and bonuses that activate when creatures attack or deal damage.",
        "oracle_keywords": ["whenever ... attacks", "whenever a creature you control attacks", "deals combat damage"],
        "card_types": ["Creature", "Enchantment"],
        "examples": ["Reconnaissance Mission", "Bident of Thassa", "Edric, Spymaster of Trest"],
    },
    "attack_trigger_payoff": {
        "label": "Attack-Trigger Payoffs",
        "what_it_does": "Cards that reward attacking with creatures.",
        "oracle_keywords": ["whenever ... attacks", "attacks alone", "attacks and isn't blocked"],
        "card_types": ["Creature", "Enchantment"],
        "examples": ["Edric, Spymaster of Trest", "Reconnaissance Mission", "Coastal Piracy"],
    },
    "damage_payoff": {
        "label": "Damage Payoffs",
        "what_it_does": "Cards that reward dealing damage to opponents.",
        "oracle_keywords": ["whenever ... deals damage", "deals combat damage to a player", "deals damage to a player"],
        "card_types": ["Creature", "Enchantment"],
        "examples": ["Rage Forger", "Bident of Thassa", "Edric"],
    },
    "lifedrain_payoff": {
        "label": "Life-Drain Payoffs",
        "what_it_does": "Pings each opponent for life — death by a thousand cuts.",
        "oracle_keywords": ["each opponent loses", "loses 1 life", "drain each opponent"],
        "card_types": ["Creature", "Enchantment"],
        "examples": ["Zulaport Cutthroat", "Blood Artist", "Cruel Celebrant"],
    },
    "graveyard_enabler": {
        "label": "Graveyard Setup",
        "what_it_does": "Fills the graveyard with cards you can reanimate or recur.",
        "oracle_keywords": ["mill", "discard", "put the top cards into your graveyard", "self-mill"],
        "card_types": ["Sorcery", "Instant", "Creature", "Enchantment"],
        "examples": ["Stitcher's Supplier", "Buried Alive", "Entomb", "Underworld Breach setup"],
    },
    "spell_payoff": {
        "label": "Spell Payoffs / Spellslinger",
        "what_it_does": "Triggers that fire whenever you cast instants or sorceries.",
        "oracle_keywords": ["whenever you cast an instant or sorcery", "whenever you cast a noncreature spell", "prowess"],
        "card_types": ["Creature", "Enchantment"],
        "examples": ["Young Pyromancer", "Talrand, Sky Summoner", "Guttersnipe"],
    },
    "cost_reducer": {
        "label": "Cost Reducers",
        "what_it_does": "Discounts spells of a specific type — engine accelerant.",
        "oracle_keywords": ["spells you cast cost", "less to cast", "cost ... less"],
        "card_types": ["Creature", "Enchantment", "Artifact"],
        "examples": ["Goblin Electromancer", "Herald's Horn (typal)", "Urza's Incubator (typal)"],
    },
    "blink_flicker": {
        "label": "Blink / Flicker",
        "what_it_does": "Exiles and returns creatures, re-triggering ETB effects.",
        "oracle_keywords": ["exile target creature, then return", "flicker", "blink", "exile then return to the battlefield"],
        "card_types": ["Instant", "Sorcery", "Creature"],
        "examples": ["Ephemerate", "Eerie Interlude", "Cloudshift", "Conjurer's Closet"],
    },
    "landfall": {
        "label": "Landfall Triggers",
        "what_it_does": "Cards that trigger whenever a land enters the battlefield.",
        "oracle_keywords": ["landfall", "whenever a land enters the battlefield", "whenever a land you control enters"],
        "card_types": ["Creature", "Enchantment"],
        "examples": ["Lotus Cobra", "Tireless Provisioner", "Roil Elemental", "Avenger of Zendikar"],
    },
    "landfall_payoff": {
        "label": "Landfall Payoffs",
        "what_it_does": "Strong rewards for landfall triggers — value engines and finishers.",
        "oracle_keywords": ["whenever a land enters", "landfall —", "landfall ability"],
        "card_types": ["Creature", "Enchantment"],
        "examples": ["Avenger of Zendikar", "Rampaging Baloths", "Felidar Retreat"],
    },
    "artifact_payoff": {
        "label": "Artifact Payoffs",
        "what_it_does": "Triggers and bonuses keyed off artifacts.",
        "oracle_keywords": ["whenever an artifact", "whenever you cast an artifact", "for each artifact"],
        "card_types": ["Creature", "Enchantment"],
        "examples": ["Sai, Master Thopterist", "Reckless Fireweaver", "Cranial Plating"],
    },
    "lifegain_payoff": {
        "label": "Lifegain Payoffs",
        "what_it_does": "Triggers that reward gaining life.",
        "oracle_keywords": ["whenever you gain life", "if you would gain life", "lifelink"],
        "card_types": ["Creature", "Enchantment"],
        "examples": ["Karlov of the Ghost Council", "Trudge Garden", "Sanguine Bond"],
    },
    "win_condition": {
        "label": "Win Conditions / Finishers",
        "what_it_does": "Cards that actually close out the game.",
        "oracle_keywords": ["each opponent loses the game", "wins the game", "deals damage to each opponent equal to"],
        "card_types": ["Creature", "Instant", "Sorcery", "Enchantment"],
        "examples": ["Craterhoof Behemoth", "Torment of Hailfire", "Insurrection", "Triumph of the Hordes"],
    },
    "commander_payoff_amplifier": {
        "label": "Commander Payoff Amplifiers",
        "what_it_does": "Cards that double or amplify the commander's payoff effect.",
        "oracle_keywords": ["double", "twice", "create copies", "if you would create a token"],
        "card_types": ["Creature", "Enchantment", "Artifact"],
        "examples": ["Panharmonicon", "Doubling Season", "Strionic Resonator", "Roaming Throne"],
    },
    "copy_clone_value": {
        "label": "Copy / Clone Value",
        "what_it_does": "Effects that copy cards, tokens, or abilities for extra value.",
        "oracle_keywords": ["create a token copy", "create copies", "copy target", "becomes a copy of"],
        "card_types": ["Sorcery", "Instant", "Creature", "Enchantment"],
        "examples": ["Reflections of Littjara", "Helm of the Host", "Cackling Counterpart"],
    },
    "dragon_typal": {
        "label": "Dragon Tribal Support",
        "what_it_does": "Cards that specifically help Dragon decks.",
        "oracle_keywords": ["Dragon", "Dragons you control"],
        "card_types": ["Creature (Dragon)", "Enchantment", "Artifact"],
        "examples": ["Dragon Tempest", "Herald's Horn", "Sarkhan, Dragonsoul", "Crucible of Fire"],
    },
    "equipment_synergy": {
        "label": "Equipment Synergy",
        "what_it_does": "Cards that work with or reward equipping.",
        "oracle_keywords": ["equip", "equipped creature", "whenever ... becomes equipped", "attach"],
        "card_types": ["Artifact (Equipment)", "Creature"],
        "examples": ["Stoneforge Mystic", "Sigarda's Aid", "Puresteel Paladin", "Brass Squire"],
    },
    "tutor": {
        "label": "Tutors / Card Search",
        "what_it_does": "Finds a specific card from your library — consistency engine.",
        "oracle_keywords": ["search your library for a card", "search your library for", "Demonic Tutor", "Vampiric Tutor"],
        "card_types": ["Sorcery", "Instant", "Creature"],
        "examples": ["Demonic Tutor", "Mystical Tutor", "Worldly Tutor", "Eladamri's Call"],
    },
    "treasure_synergy": {
        "label": "Treasure Synergy",
        "what_it_does": "Creates or rewards Treasure tokens — flexible ramp and payoff.",
        "oracle_keywords": ["create a treasure token", "treasure token"],
        "card_types": ["Sorcery", "Instant", "Creature", "Enchantment"],
        "examples": ["Smothering Tithe", "Dockside Extortionist", "Captain Lannery Storm"],
    },
}


def role_guidance_for(role_tag: str) -> dict[str, Any]:
    """Return guidance for a single role tag, synthesizing a fallback if needed."""
    if role_tag in ROLE_GUIDANCE:
        return ROLE_GUIDANCE[role_tag]
    # Fall back to a name-based stub so unknown roles still get a section.
    label = role_tag.replace("_", " ").title()
    return {
        "label": label,
        "what_it_does": f"Cards that fill the '{label}' role in this strategy.",
        "oracle_keywords": [],
        "card_types": [],
        "examples": [],
    }


def build_rough_shell_markdown(
    *,
    commander_name: str,
    color_identity: str,
    primary_strategy: str,
    secondary_strategy: str,
    main_philosophy: str,
    sub_philosophy: str,
    bracket_preference: str,
    collection_first_preference: str,
) -> str:
    """Build the Rough Shell user-facing markdown report.

    Pulls anchors/payoffs/enablers from analysis.strategy_scoring.ARCHETYPE_DEFINITIONS
    for the primary (and optional secondary) strategy, translates each role tag via
    role_guidance_for(), and emits a "what to look for in your collection" report.
    """
    # v1.5.38 (Task #39): Try the Strategy Knowledge 249-profile catalog first
    # so the Rough Shell guidance reflects whichever specific strategy the user
    # picked, not just the matching macro archetype.
    def _resolve_strategy_tags(name: str) -> set[str]:
        if not name or name in ("Not selected yet", "None"):
            return set()
        try:
            from strategy_knowledge.strategy_selector_catalog import role_tags_for_display_name
            tags = role_tags_for_display_name(name)
            if tags:
                return tags
        except Exception:
            pass
        bare = name
        if bare.startswith("[") and "]" in bare:
            bare = bare.split("]", 1)[1].strip()
        arch = ARCHETYPE_DEFINITIONS.get(bare, {}) or {}
        tags = set()
        for key in ("anchors", "payoffs", "enablers"):
            for tag in (arch.get(key) or set()):
                tags.add(str(tag))
        return tags

    try:
        from analysis.strategy_scoring import ARCHETYPE_DEFINITIONS
    except Exception:
        ARCHETYPE_DEFINITIONS = {}

    lines: list[str] = [
        f"# Rough Shell — What to Look For",
        "",
        "This report tells you what kinds of cards to dig for in your collection ",
        f"when building a Commander deck around **{commander_name}**. ",
        "It is guidance — not a deck list, not a card selection, and not a final inclusion decision.",
        "",
        "## Commander Context",
        "",
        f"- Commander: **{commander_name}**",
        f"- Color identity: {color_identity}",
        f"- Primary strategy: **{primary_strategy or 'Not selected yet'}**",
        f"- Secondary strategy: **{secondary_strategy or 'None'}**",
        f"- Main philosophy: {main_philosophy or 'Not selected yet'}",
        f"- Sub-philosophy / persona: {sub_philosophy or 'Not selected yet'}",
        f"- Bracket preference: {bracket_preference or 'Not selected yet'}",
        f"- Collection preference: {collection_first_preference}",
        "",
    ]

    def _emit_role_section(role_tag: str, bucket_label: str) -> None:
        guidance = role_guidance_for(role_tag)
        lines.append(f"### {guidance['label']}  _({bucket_label})_")
        lines.append("")
        if guidance.get("what_it_does"):
            lines.append(f"**What it does:** {guidance['what_it_does']}")
            lines.append("")
        keywords = guidance.get("oracle_keywords") or []
        if keywords:
            lines.append("**Oracle text to look for:**")
            for kw in keywords:
                lines.append(f"- `{kw}`")
            lines.append("")
        card_types = guidance.get("card_types") or []
        if card_types:
            lines.append(f"**Common card types:** {', '.join(card_types)}")
            lines.append("")
        examples = guidance.get("examples") or []
        if examples:
            lines.append("**Example cards / effects:**")
            for ex in examples:
                lines.append(f"- {ex}")
            lines.append("")

    # Resolve role tags for primary + secondary. Legacy ARCHETYPE_DEFINITIONS
    # entries have structured anchors/payoffs/enablers; new 249-catalog entries
    # have a flat role_tags list — we support both.
    def _primary_strategy_bare(name: str) -> str:
        if not name:
            return ""
        bare = name
        if bare.startswith("[") and "]" in bare:
            bare = bare.split("]", 1)[1].strip()
        return bare

    primary_bare = _primary_strategy_bare(primary_strategy or "")
    secondary_bare = _primary_strategy_bare(secondary_strategy or "")
    primary_def = ARCHETYPE_DEFINITIONS.get(primary_bare, {}) or {}
    secondary_def = ARCHETYPE_DEFINITIONS.get(secondary_bare, {}) or {}

    seen_roles: set[str] = set()
    sections: list[tuple[str, str]] = []  # (role_tag, bucket_label)

    if primary_def:
        # Legacy 22-archetype path with anchor/payoff/enabler breakdown.
        for label, key in (("Primary strategy anchor", "anchors"), ("Primary strategy payoff", "payoffs"), ("Primary strategy enabler", "enablers")):
            for role in primary_def.get(key, set()) or set():
                if role not in seen_roles:
                    seen_roles.add(role)
                    sections.append((role, label))
    else:
        # 249-catalog path: flat role_tags labeled generically.
        for role in _resolve_strategy_tags(primary_strategy or ""):
            if role not in seen_roles:
                seen_roles.add(role)
                sections.append((role, "Primary strategy role"))

    if secondary_strategy and secondary_strategy not in {"None", "Not selected yet", ""}:
        if secondary_def:
            for label, key in (("Secondary anchor", "anchors"), ("Secondary payoff", "payoffs"), ("Secondary enabler", "enablers")):
                for role in secondary_def.get(key, set()) or set():
                    if role not in seen_roles:
                        seen_roles.add(role)
                        sections.append((role, label))
        else:
            for role in _resolve_strategy_tags(secondary_strategy):
                if role not in seen_roles:
                    seen_roles.add(role)
                    sections.append((role, "Secondary strategy role"))

    # Always include core utility roles even if not in the strategy definition,
    # so every deck gets ramp/draw/removal/protection guidance.
    for core_role in ("ramp", "card_draw", "targeted_removal", "protection"):
        if core_role not in seen_roles:
            seen_roles.add(core_role)
            sections.append((core_role, "Core deck utility"))

    if sections:
        lines.append("## Role Buckets To Look For")
        lines.append("")
        for role_tag, bucket_label in sections:
            _emit_role_section(role_tag, bucket_label)
    else:
        lines.append("## Role Buckets To Look For")
        lines.append("")
        lines.append("_Pick a Primary strategy in the Build Setup Panel to populate this section._")
        lines.append("")

    lines.extend([
        "## How To Use This",
        "",
        "1. Open the **Owned Cards By Role Output** report alongside this one.",
        "2. For each role bucket above, find the matching section in your owned-card report.",
        "3. Pick cards from your collection that match the oracle keywords or example effects.",
        "4. If your collection is thin in a role, that's the area to upgrade — but stay within your bracket and budget.",
        "",
        "## Boundaries",
        "",
        "- This is guidance only. It does NOT pick exact cards for your deck.",
        "- It does NOT generate a 100-card list.",
        "- It does NOT build a mana base.",
        "- Pilot judgement still decides every final inclusion.",
        "",
    ])

    return "\n".join(lines)
