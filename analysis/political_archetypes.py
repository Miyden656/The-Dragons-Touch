"""Political archetype classifier (Section 3 — Strategic & Board Politics).

Consumes the political signal profile (analysis/political_signals.py) and
classifies a deck against all ~42 Section-3 political archetypes:

    Group Hug, Group Slug, Chaos, Aikido, Forced Combat/Goad, Pillowfort,
    Politics/Deal-Making, Voting, Monarch, Curses, Bounty, Theft, Threat
    Redistribution, Kingmaker, Donate/Bad Gifts, Rattlesnake, Turbo-Fog, Table
    Police, Punisher, Attack-Elsewhere, Goad-Control, Hidden Asymmetry, Social
    Contract, Archenemy/Villain, Secret Combo, Sandbag Control, Revenge, Shared
    Combat, Combat Manipulation, Tablewide Acceleration, Anti-Combo, Do-Not-
    Touch-Me, Board-Reset Politics, Life Politics, Information Politics, Shared
    Enemy, Fairness, Negotiated Removal, Soft Lock, Gift Politics, Combo
    Deterrence, Reputation (modifier).

This is a PARALLEL, ADDITIVE classification. It does NOT modify the v1.6 strategy
read (analysis/strategy_scoring.py) — a deck keeps its construction-based primary
strategy AND gains this political profile. The two coexist.

Each archetype carries its Primary Gate VERBATIM from the spec (as a predicate
over the signal counts + engine flags). Scoring follows §3.53 (additive density +
commander support, minus risk penalties); role assignment follows §3.3/§3.4;
suppression follows §3.6. Output fields follow §3.2; warnings follow §3.52.

Detection quality is inherited from political_signals.py and is iterative — a
missed signal can only fail to fire an archetype, never fabricate one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from analysis.political_signals import PoliticalSignalProfile


def _d(counts: Any, *tags: str) -> int:
    """Density: total count across the given signal tags."""
    return sum(int(counts.get(t, 0) or 0) for t in tags)


@dataclass(frozen=True)
class PoliticalArchetype:
    key: str
    name: str
    section: str
    axis: str
    gate: Callable[[Any, dict], bool]  # (counts, flags) -> primary gate result
    anchors: tuple[str, ...]           # defining incentive/deterrence signals
    payoff: tuple[str, ...] = ()       # how it converts to advantage/a win
    protection: tuple[str, ...] = ()   # how it survives
    inevitability: tuple[str, ...] = ()  # closing/repeatable engine signals
    commander_flag: str = ""           # which flags[...] grants commander support
    table_dependency: str = "medium"
    salt_risk: str = "low"
    modifier_only: bool = False        # never a primary strategy (3.29, 3.48)
    suppress_if_thin: bool = False     # easy to over-detect (3.6)
    generic: bool = False              # the catch-all "Politics" theme (3.13)


# Verbatim primary gates from rules/section_3_strategic_board_politics.md.
POLITICAL_ARCHETYPES: tuple[PoliticalArchetype, ...] = (
    PoliticalArchetype(
        "group_hug", "Group Hug", "3.7", "give resources to the table",
        lambda c, f: (
            (_d(c, "group_draw") >= 3 or _d(c, "group_ramp") >= 3 or _d(c, "gift_resource") >= 4)
            and (_d(c, "hug_payoff") >= 2 or _d(c, "asymmetrical_payoff") >= 2
                 or _d(c, "alternate_win_condition") >= 1 or _d(c, "pillowfort") >= 3)
            and f.get("has_clear_win_path", False)
        ),
        anchors=("group_draw", "group_ramp", "gift_resource", "group_resource"),
        payoff=("hug_payoff", "asymmetrical_payoff"), protection=("pillowfort", "fort_protection"),
        inevitability=("alternate_win_condition", "win_condition"),
        table_dependency="high", salt_risk="low", suppress_if_thin=True,
    ),
    PoliticalArchetype(
        "group_slug", "Group Slug", "3.8", "punish normal game actions",
        lambda c, f: (
            (_d(c, "table_damage") >= 4 or _d(c, "punisher") >= 4 or _d(c, "life_loss_engine") >= 4)
            and (_d(c, "damage_amplifier") >= 1 or _d(c, "lifegain_buffer") >= 2
                 or _d(c, "drain_payoff") >= 2 or _d(c, "protection") >= 2)
        ),
        anchors=("table_damage", "punisher", "life_loss_engine"),
        payoff=("drain_payoff", "damage_amplifier"), protection=("lifegain_buffer", "protection"),
        inevitability=("table_damage", "drain_payoff"),
        table_dependency="low", salt_risk="medium", suppress_if_thin=True,
    ),
    PoliticalArchetype(
        "chaos", "Chaos", "3.9", "destabilize the game",
        lambda c, f: (
            (_d(c, "random_effect") >= 4 or _d(c, "coin_flip") >= 4 or _d(c, "dice_roll") >= 4
             or _d(c, "chaos_effect") >= 5)
            and (_d(c, "chaos_payoff") >= 2 or f.get("has_clear_win_path", False))
        ),
        anchors=("random_effect", "coin_flip", "dice_roll", "chaos_effect"),
        payoff=("chaos_payoff",), inevitability=("win_condition",),
        table_dependency="medium", salt_risk="high", suppress_if_thin=True,
    ),
    PoliticalArchetype(
        "aikido", "Aikido / Judo", "3.10", "turn aggression against attackers",
        lambda c, f: (
            (_d(c, "damage_reflection") >= 3 or _d(c, "attack_punisher") >= 4 or _d(c, "revenge_trigger") >= 4)
            and (_d(c, "rattlesnake") >= 2 or _d(c, "card_draw") >= 5 or _d(c, "forced_combat") >= 2
                 or f.get("has_proactive_win_path", False))
        ),
        anchors=("damage_reflection", "attack_punisher", "revenge_trigger"),
        payoff=("forced_combat",), protection=("rattlesnake",), inevitability=("win_condition",),
        table_dependency="medium", salt_risk="low",
    ),
    PoliticalArchetype(
        "forced_combat", "Forced Combat / Goad", "3.11", "make opponents attack each other",
        lambda c, f: (
            (_d(c, "goad") >= 4 or _d(c, "forced_attack") >= 4 or _d(c, "attack_elsewhere_incentive") >= 4)
            and (_d(c, "combat_payoff") >= 3 or _d(c, "attack_elsewhere_incentive") >= 2 or _d(c, "table_damage") >= 2)
        ),
        anchors=("goad", "forced_attack", "attack_elsewhere_incentive"),
        payoff=("combat_payoff", "table_damage"), inevitability=("combat_payoff",),
        commander_flag="commander_supports_attack_elsewhere",
        table_dependency="medium", salt_risk="low", suppress_if_thin=True,
    ),
    PoliticalArchetype(
        "pillowfort", "Pillowfort", "3.12", "make attacking you pointless",
        lambda c, f: (
            (_d(c, "attack_tax") >= 3 or _d(c, "combat_prevention") >= 3 or _d(c, "fort_protection") >= 5)
            and (_d(c, "alternate_win_condition") >= 1 or _d(c, "planeswalker") >= 4
                 or _d(c, "enchantment_payoff") >= 4 or _d(c, "combo_piece") >= 2
                 or f.get("has_clear_inevitability_engine", False))
        ),
        anchors=("attack_tax", "combat_prevention", "fort_protection"),
        payoff=("enchantment_payoff",), protection=("fort_protection",),
        inevitability=("alternate_win_condition", "planeswalker", "combo_piece"),
        table_dependency="low", salt_risk="medium", suppress_if_thin=True,
    ),
    PoliticalArchetype(
        "deal_politics", "Politics / Deal-Making", "3.13", "manipulate player choices",
        lambda c, f: (
            (_d(c, "political_choice") >= 4 or _d(c, "deal_incentive") >= 4 or _d(c, "negotiated_removal") >= 3)
            and (_d(c, "political_payoff") >= 2 or f.get("commander_supports_political_axis", False))
        ),
        anchors=("political_choice", "deal_incentive", "negotiated_removal"),
        payoff=("political_payoff",), inevitability=("win_condition",),
        commander_flag="commander_supports_political_axis",
        table_dependency="high", salt_risk="low", generic=True,
    ),
    PoliticalArchetype(
        "voting", "Voting / Council's Dilemma", "3.14", "benefit regardless of the vote",
        lambda c, f: (_d(c, "vote") >= 4 and (_d(c, "vote_payoff") >= 2 or f.get("commander_supports_voting", False))),
        anchors=("vote",), payoff=("vote_payoff",), commander_flag="commander_supports_voting",
        table_dependency="high", salt_risk="low",
    ),
    PoliticalArchetype(
        "monarch", "Monarch Politics", "3.15", "take and keep the crown",
        lambda c, f: (
            (_d(c, "monarch") >= 3 or f.get("commander_supports_monarch", False))
            and (_d(c, "crown_defense") >= 3 or _d(c, "evasive_creature") >= 3 or _d(c, "pillowfort") >= 2)
        ),
        anchors=("monarch",), payoff=("card_draw",),
        protection=("crown_defense", "evasive_creature", "pillowfort"),
        commander_flag="commander_supports_monarch", table_dependency="medium", salt_risk="low",
    ),
    PoliticalArchetype(
        "curses", "Curse Politics", "3.16", "redirect threat with curses",
        lambda c, f: (
            _d(c, "curse") >= 5
            and (_d(c, "curse_payoff") >= 2 or f.get("commander_supports_curses", False)
                 or _d(c, "enchantment_recursion") >= 2)
        ),
        anchors=("curse",), payoff=("curse_payoff",), inevitability=("enchantment_recursion",),
        commander_flag="commander_supports_curses", table_dependency="medium", salt_risk="medium",
    ),
    PoliticalArchetype(
        "bounty", "Bounty / Incentivized Combat", "3.17", "reward attacking your enemies",
        lambda c, f: (
            (_d(c, "bounty") >= 3 or _d(c, "attack_reward") >= 4)
            and (_d(c, "political_payoff") >= 2 or f.get("commander_supports_bounty", False))
        ),
        anchors=("bounty", "attack_reward"), payoff=("political_payoff",),
        commander_flag="commander_supports_bounty", table_dependency="high", salt_risk="low",
    ),
    PoliticalArchetype(
        "theft", "Theft / Clone Politics", "3.18", "steal opponents' resources",
        lambda c, f: (
            (_d(c, "theft") >= 4 or _d(c, "clone_opponent") >= 4 or _d(c, "cast_opponent_card") >= 4)
            and (_d(c, "theft_payoff") >= 2 or f.get("commander_supports_theft", False))
        ),
        anchors=("theft", "clone_opponent", "cast_opponent_card"), payoff=("theft_payoff",),
        commander_flag="commander_supports_theft", table_dependency="medium", salt_risk="medium",
    ),
    PoliticalArchetype(
        "threat_redistribution", "Threat Redistribution", "3.19", "make others look threatening",
        lambda c, f: (
            (_d(c, "threat_redirect") >= 5
             or (_d(c, "goad") >= 2 and _d(c, "pillowfort") >= 2 and _d(c, "political_incentive") >= 2))
            and f.get("has_clear_win_path", False)
        ),
        anchors=("threat_redirect", "goad"), protection=("pillowfort",), payoff=("political_incentive",),
        table_dependency="high", salt_risk="low",
    ),
    PoliticalArchetype(
        "table_balancer", "Kingmaker / Table-Balancer", "3.20", "punish the leader / help the behind",
        lambda c, f: (
            (_d(c, "catch_up_mechanic") >= 3 or _d(c, "leader_punisher") >= 3 or _d(c, "parity_tool") >= 4)
            and (_d(c, "self_advancement") >= 3 or f.get("has_clear_win_path", False))
        ),
        anchors=("catch_up_mechanic", "leader_punisher", "parity_tool"), payoff=("self_advancement",),
        table_dependency="high", salt_risk="medium",
    ),
    PoliticalArchetype(
        "resource_redistribution", "Donate / Bad Gifts", "3.21", "hand opponents harmful permanents",
        lambda c, f: (
            (_d(c, "donate") >= 3 or _d(c, "bad_gift") >= 4 or _d(c, "resource_swap") >= 4)
            and (_d(c, "donate_payoff") >= 2 or f.get("commander_supports_donate", False))
        ),
        anchors=("donate", "bad_gift", "resource_swap"), payoff=("donate_payoff",),
        protection=("pillowfort",), commander_flag="commander_supports_donate",
        table_dependency="high", salt_risk="low",
    ),
    PoliticalArchetype(
        "rattlesnake", "Rattlesnake", "3.22", "deter attacks with visible threats",
        lambda c, f: (
            (_d(c, "rattlesnake") >= 5 or _d(c, "attack_punisher") >= 4)
            and (_d(c, "card_draw") >= 4 or _d(c, "value_engine") >= 3 or f.get("has_clear_win_path", False))
        ),
        anchors=("rattlesnake", "attack_punisher"), payoff=("value_engine", "card_draw"),
        table_dependency="medium", salt_risk="low",
    ),
    PoliticalArchetype(
        "turbo_fog", "Fog / Turbo-Fog Politics", "3.23", "survive combat and win another way",
        lambda c, f: (
            (_d(c, "fog") >= 5 or _d(c, "combat_prevention") >= 5)
            and (_d(c, "alternate_win_condition") >= 1 or _d(c, "planeswalker") >= 4
                 or _d(c, "mill") >= 3 or f.get("has_clear_inevitability_engine", False))
        ),
        anchors=("fog", "combat_prevention"), protection=("fort_protection",),
        inevitability=("alternate_win_condition", "planeswalker", "mill"),
        table_dependency="low", salt_risk="medium", suppress_if_thin=True,
    ),
    PoliticalArchetype(
        "table_police", "Table Police / Rule Enforcer", "3.24", "enforce rules on the table",
        lambda c, f: (
            (_d(c, "behavior_punisher") >= 4 or _d(c, "rule_enforcer") >= 4 or _d(c, "anti_combo") >= 4)
            and (_d(c, "win_condition") >= 2 or _d(c, "value_engine") >= 3)
        ),
        anchors=("behavior_punisher", "rule_enforcer", "anti_combo"),
        payoff=("value_engine",), inevitability=("win_condition",),
        table_dependency="low", salt_risk="high",
    ),
    PoliticalArchetype(
        "punisher", "Punisher / Choice Punisher", "3.25", "every choice hurts the opponent",
        lambda c, f: (
            (_d(c, "punisher") >= 5 or _d(c, "choice_punisher") >= 4)
            and (_d(c, "damage_amplifier") >= 1 or _d(c, "table_damage") >= 3 or _d(c, "drain_payoff") >= 2)
        ),
        anchors=("punisher", "choice_punisher"), payoff=("drain_payoff", "table_damage"),
        table_dependency="low", salt_risk="medium",
    ),
    PoliticalArchetype(
        "attack_elsewhere", "Attack Elsewhere Incentive", "3.26", "profit when opponents fight",
        lambda c, f: (
            (_d(c, "attack_elsewhere_incentive") >= 4 or f.get("commander_supports_attack_elsewhere", False))
            and (_d(c, "defensive_support") >= 2 or _d(c, "political_payoff") >= 2)
        ),
        anchors=("attack_elsewhere_incentive",), payoff=("political_payoff",),
        protection=("fort_protection",), commander_flag="commander_supports_attack_elsewhere",
        table_dependency="high", salt_risk="low",
    ),
    PoliticalArchetype(
        "goad_control", "Goad-Control", "3.27", "goad plus removal backup",
        lambda c, f: (
            _d(c, "goad") >= 4
            and (_d(c, "targeted_removal") >= 3 or _d(c, "board_wipe") >= 2 or _d(c, "control_piece") >= 4)
        ),
        anchors=("goad",), payoff=("board_wipe", "targeted_removal"), protection=("control_piece",),
        table_dependency="medium", salt_risk="low",
    ),
    PoliticalArchetype(
        "hidden_asymmetry", "Mutual Benefit / Hidden Asymmetry", "3.28", "shared resources, asymmetric payoff",
        lambda c, f: (_d(c, "group_resource") >= 4 and _d(c, "asymmetrical_payoff") >= 2),
        anchors=("group_resource", "group_draw", "group_ramp"), payoff=("asymmetrical_payoff",),
        table_dependency="high", salt_risk="low",
    ),
    PoliticalArchetype(
        "social_contract", "Social Contract / Rule Zero", "3.29", "table experience over optimization",
        lambda c, f: False,  # classification rule: never a normal optimization archetype
        anchors=(), modifier_only=True, table_dependency="high", salt_risk="low",
    ),
    PoliticalArchetype(
        "villain", "Archenemy / Villain Deck", "3.30", "be the table's obvious threat",
        lambda c, f: (
            (_d(c, "oppressive_effect") >= 4 or f.get("commander_has_high_threat_reputation", False))
            and (_d(c, "resilience") >= 3 or _d(c, "protection") >= 3 or _d(c, "fast_win") >= 1)
        ),
        anchors=("oppressive_effect",), payoff=("fast_win",), protection=("resilience", "protection"),
        inevitability=("fast_win", "win_condition"), table_dependency="low", salt_risk="high",
    ),
    PoliticalArchetype(
        "secret_combo", "Secret Combo / Low-Threat Combo", "3.31", "win suddenly from a harmless board",
        lambda c, f: (
            _d(c, "combo_piece") >= 3
            and (_d(c, "pillowfort") >= 2 or (_d(c, "group_draw") + _d(c, "group_ramp")) >= 2
                 or _d(c, "low_threat_value") >= 4)
            and (_d(c, "tutor") >= 2 or _d(c, "card_selection") >= 4)
        ),
        anchors=("combo_piece",), payoff=("win_condition",), protection=("pillowfort",),
        inevitability=("tutor", "card_selection"), table_dependency="low", salt_risk="high",
        suppress_if_thin=True,
    ),
    PoliticalArchetype(
        "sandbag_control", "Sandbag / Reactive Control", "3.32", "hold up answers, win late",
        lambda c, f: (
            _d(c, "instant_speed_interaction") >= 6
            and (_d(c, "card_draw") >= 5 or f.get("commander_supports_reactive_play", False))
            and f.get("has_clear_win_path", False)
        ),
        anchors=("instant_speed_interaction",), payoff=("card_draw",), inevitability=("win_condition",),
        commander_flag="commander_supports_reactive_play", table_dependency="low", salt_risk="medium",
    ),
    PoliticalArchetype(
        "retaliation", "Revenge / Retaliation", "3.33", "punish being attacked or targeted",
        lambda c, f: (
            (_d(c, "revenge_trigger") >= 4 or _d(c, "attack_punisher") >= 4)
            and (_d(c, "proactive_pressure") >= 2 or _d(c, "card_draw") >= 4 or _d(c, "forced_combat") >= 2)
        ),
        anchors=("revenge_trigger", "attack_punisher"), payoff=("proactive_pressure",),
        table_dependency="medium", salt_risk="low",
    ),
    PoliticalArchetype(
        "shared_combat", "Shared Combat Incentive", "3.34", "reward the whole table for attacking",
        lambda c, f: (
            (_d(c, "shared_combat_incentive") >= 4 or _d(c, "forced_attack") >= 4)
            and (_d(c, "combat_payoff") >= 3 or _d(c, "attack_trigger") >= 3)
        ),
        anchors=("shared_combat_incentive", "forced_attack"), payoff=("combat_payoff", "attack_trigger"),
        table_dependency="high", salt_risk="low",
    ),
    PoliticalArchetype(
        "combat_manipulation", "Forced Blocking / Combat Manipulation", "3.35", "control how combat resolves",
        lambda c, f: (
            (_d(c, "forced_block") >= 3 or _d(c, "cant_block") >= 3 or _d(c, "combat_manipulation") >= 5)
            and (_d(c, "combat_payoff") >= 3 or _d(c, "saboteur") >= 3)
        ),
        anchors=("forced_block", "cant_block", "combat_manipulation"), payoff=("combat_payoff", "saboteur"),
        table_dependency="medium", salt_risk="low",
    ),
    PoliticalArchetype(
        "tablewide_acceleration", "Tablewide Resource Acceleration", "3.36", "accelerate everyone, profit most",
        lambda c, f: (
            (_d(c, "group_ramp") >= 3 or _d(c, "group_draw") >= 3 or _d(c, "tablewide_acceleration") >= 4)
            and (_d(c, "asymmetrical_payoff") >= 2 or _d(c, "protection") >= 3 or _d(c, "fast_payoff") >= 2)
        ),
        anchors=("group_ramp", "group_draw", "tablewide_acceleration"), payoff=("asymmetrical_payoff",),
        protection=("protection",), table_dependency="high", salt_risk="low",
    ),
    PoliticalArchetype(
        "anti_combo", "Anti-Combo Social Police", "3.37", "punish greed and combo",
        lambda c, f: (
            (_d(c, "anti_combo") >= 5
             or (_d(c, "tutor_hate") >= 2 and _d(c, "graveyard_hate") >= 2 and _d(c, "rule_limiter") >= 2))
            and f.get("has_clear_win_path", False)
        ),
        anchors=("anti_combo", "tutor_hate", "graveyard_hate", "rule_limiter"),
        inevitability=("win_condition",), table_dependency="low", salt_risk="high",
    ),
    PoliticalArchetype(
        "do_not_touch_me", "Do Not Touch Me Control", "3.38", "protect the engine, win behind it",
        lambda c, f: (
            (_d(c, "anti_targeting") >= 4 or _d(c, "board_protection") >= 5)
            and (_d(c, "protected_win_condition") >= 2 or _d(c, "voltron") >= 3 or _d(c, "value_engine") >= 3)
        ),
        anchors=("anti_targeting", "board_protection"), payoff=("value_engine",),
        protection=("protected_win_condition",), table_dependency="low", salt_risk="low",
    ),
    PoliticalArchetype(
        "board_reset_politics", "Mutual Destruction / Board Reset", "3.39", "reset the board, break parity",
        lambda c, f: (
            (_d(c, "board_wipe") >= 4 or _d(c, "board_reset") >= 4)
            and (_d(c, "break_parity") >= 2 or _d(c, "recursion") >= 3 or _d(c, "planeswalker") >= 3
                 or f.get("commander_supports_board_reset", False))
        ),
        anchors=("board_wipe", "board_reset"), payoff=("break_parity",),
        protection=("recursion",), inevitability=("planeswalker", "win_condition"),
        commander_flag="commander_supports_board_reset", table_dependency="low", salt_risk="high",
    ),
    PoliticalArchetype(
        "life_politics", "Life Total Politics", "3.40", "weaponize life totals",
        lambda c, f: (
            (_d(c, "life_manipulation") >= 4 or _d(c, "life_exchange") >= 2)
            and (_d(c, "life_payoff") >= 2 or _d(c, "lifedrain") >= 3 or _d(c, "alternate_win_condition") >= 1)
        ),
        anchors=("life_manipulation", "life_exchange"), payoff=("life_payoff", "lifedrain"),
        inevitability=("alternate_win_condition",), table_dependency="medium", salt_risk="low",
    ),
    PoliticalArchetype(
        "information_politics", "Information Politics / Hidden Threats", "3.41", "win from hidden information",
        lambda c, f: (
            (_d(c, "hidden_information") >= 5 or _d(c, "face_down") >= 5)
            and (_d(c, "hidden_payoff") >= 2 or f.get("commander_supports_hidden_information", False))
        ),
        anchors=("hidden_information", "face_down"), payoff=("hidden_payoff",),
        commander_flag="commander_supports_hidden_information", table_dependency="medium", salt_risk="low",
    ),
    PoliticalArchetype(
        "shared_enemy", "Shared Enemy / Table Alliance", "3.42", "ally the table against the leader",
        lambda c, f: (
            (_d(c, "shared_enemy_incentive") >= 4 or _d(c, "leader_punisher") >= 3)
            and (_d(c, "self_advancement") >= 3 or _d(c, "political_payoff") >= 2)
        ),
        anchors=("shared_enemy_incentive", "leader_punisher"), payoff=("self_advancement", "political_payoff"),
        table_dependency="high", salt_risk="medium",
    ),
    PoliticalArchetype(
        "fairness", "Fairness / Symmetrical Rules", "3.43", "symmetry you alone break",
        lambda c, f: (
            (_d(c, "symmetrical_rule") >= 4 or _d(c, "rule_limiter") >= 4)
            and (_d(c, "break_parity") >= 2 or f.get("commander_breaks_parity", False))
        ),
        anchors=("symmetrical_rule", "rule_limiter"), payoff=("break_parity",),
        table_dependency="low", salt_risk="high",
    ),
    PoliticalArchetype(
        "negotiated_removal", "Negotiated Removal", "3.44", "removal as leverage",
        lambda c, f: (
            _d(c, "flexible_removal") >= 6
            and (_d(c, "political_payoff") >= 2 or f.get("commander_supports_politics", False))
        ),
        anchors=("flexible_removal",), payoff=("political_payoff",),
        commander_flag="commander_supports_politics", table_dependency="high", salt_risk="low",
    ),
    PoliticalArchetype(
        "soft_lock", "Soft Lock Politics", "3.45", "discourage opponents' best actions",
        lambda c, f: (
            (_d(c, "soft_lock") >= 4 or (_d(c, "tax") >= 3 and _d(c, "restriction") >= 3))
            and (_d(c, "win_condition") >= 2 or f.get("has_clear_inevitability_engine", False))
        ),
        anchors=("soft_lock", "tax", "restriction"), inevitability=("win_condition",),
        table_dependency="low", salt_risk="high",
    ),
    PoliticalArchetype(
        "gift_politics", "Bribery / Gift-Based Politics", "3.46", "targeted, transactional gifts",
        lambda c, f: (
            (_d(c, "targeted_gift") >= 4 or f.get("commander_supports_gifting", False))
            and (_d(c, "gift_payoff") >= 2 or _d(c, "political_payoff") >= 2)
        ),
        anchors=("targeted_gift",), payoff=("gift_payoff", "political_payoff"),
        commander_flag="commander_supports_gifting", table_dependency="high", salt_risk="low",
    ),
    PoliticalArchetype(
        "combo_deterrence", "Political Combo Deterrence", "3.47", "open answers discourage combo",
        lambda c, f: (
            _d(c, "visible_interaction") >= 3 and _d(c, "anti_combo") >= 3 and f.get("has_clear_win_path", False)
        ),
        anchors=("visible_interaction", "anti_combo"), inevitability=("win_condition",),
        table_dependency="low", salt_risk="medium",
    ),
    PoliticalArchetype(
        "reputation", "Social Pressure / Reputation", "3.48", "fear before the game starts",
        lambda c, f: False,  # classification rule: a report modifier, not an archetype
        anchors=(), modifier_only=True, table_dependency="low", salt_risk="medium",
    ),
)

ARCHETYPES_BY_KEY: dict[str, PoliticalArchetype] = {a.key: a for a in POLITICAL_ARCHETYPES}

# §3.50 Political Replacement Logic — per-archetype replacement CATEGORIES (not
# specific cards; political replacement is category-based unless the user asks for
# exact cards). Surfaced advisorily to the report + AI coach; the v1.6 replacement
# engine is unchanged.
POLITICAL_REPLACEMENT_CATEGORIES: dict[str, tuple[str, ...]] = {
    "group_hug": ("More asymmetrical payoff", "More pillowfort", "More alternate win support", "More protection", "More win conditions"),
    "group_slug": ("More lifegain buffer", "More damage amplification", "More table drain", "More removal", "Faster clock"),
    "chaos": ("More chaos payoff", "More card draw", "More protection", "More reliable win conditions", "More damage payoff"),
    "aikido": ("More proactive pressure", "More card draw", "More forced combat", "More instant-speed interaction", "More finishers"),
    "forced_combat": ("More repeatable goad", "More removal for noncreature threats", "More defensive tools", "More attack payoff", "More board wipes"),
    "pillowfort": ("More inevitability", "More alternate win support", "More enchantment payoff", "More card draw", "Fewer redundant fort pieces if the win path is weak"),
    "deal_politics": ("More flexible removal", "More card advantage", "More reliable payoff", "More protection", "More finishers"),
    "voting": ("More vote payoff", "More artifact/token payoff", "More control", "More protection", "More reliable win conditions"),
    "monarch": ("More evasive creatures", "More pillowfort", "More deathtouch/blockers", "More removal", "More card draw"),
    "curses": ("More curse payoff", "More enchantment recursion", "More pillowfort", "More tablewide pressure", "More removal"),
    "bounty": ("More meaningful incentives", "More removal", "More card advantage", "More protection", "More finishers"),
    "theft": ("More repeatable theft", "More clone value", "More sacrifice outlets", "More mana fixing", "More protection"),
    "threat_redistribution": ("More attack redirection", "More flexible removal", "More card advantage", "More finishers", "More defensive support"),
    "table_balancer": ("More self-advancing value", "More finishers", "More card draw", "More protection", "More asymmetrical payoff"),
    "resource_redistribution": ("More bad gifts", "More donate effects", "More protection", "More pillowfort", "More win conditions"),
    "rattlesnake": ("Stronger deterrents", "More card draw", "More removal", "More win conditions", "More protection"),
    "turbo_fog": ("More inevitability", "More alternate win support", "More card draw", "More noncombat interaction", "More recursion"),
    "table_police": ("More meta-relevant hate", "More card draw", "More protection", "More finishers", "More flexible interaction"),
    "punisher": ("More damage amplification", "More guaranteed drain", "More removal", "More card draw", "More pressure"),
    "attack_elsewhere": ("More meaningful incentives", "More goad", "More defensive support", "More removal", "More finishers"),
    "goad_control": ("More targeted removal", "More board wipes", "More repeatable goad", "More card draw", "More noncreature interaction"),
    "hidden_asymmetry": ("More asymmetrical payoff", "More protection", "More win conditions", "More card draw", "More interaction"),
    "social_contract": ("More theme support", "More table-friendly interaction", "More clarity of win condition", "More pregame communication support"),
    "villain": ("More protection", "More resilience", "More efficient win conditions", "More card draw", "More removal"),
    "secret_combo": ("More card selection", "More protection", "More combo redundancy", "More survivability", "More bracket-appropriate alternatives"),
    "sandbag_control": ("More instant-speed draw", "More flexible answers", "More finishers", "More mana efficiency", "More protection"),
    "retaliation": ("More proactive threats", "More forced combat", "More card draw", "More protection", "More removal"),
    "shared_combat": ("More combat payoff", "More protection", "More goad", "More board control", "More finishers"),
    "combat_manipulation": ("More payoff", "More evasion", "More removal", "More protection", "More backup win conditions"),
    "tablewide_acceleration": ("More asymmetrical payoff", "More protection", "More interaction", "More win conditions", "More table control"),
    "anti_combo": ("More flexible interaction", "More pressure", "More card draw", "More protection", "More meta-appropriate hate"),
    "do_not_touch_me": ("More win conditions", "More card draw", "More board-wipe resilience", "More protected threats", "More interaction"),
    "board_reset_politics": ("More parity-breaking tools", "More finishers", "More recursion", "More card draw", "Fewer redundant wipes if the deck cannot close"),
    "life_politics": ("More lifegain payoff", "More lifedrain", "More alternate win support", "More protection", "More card draw"),
    "information_politics": ("More hidden payoff", "More protection", "More card draw", "More surprise finishers", "More interaction"),
    "shared_enemy": ("More self-advancing value", "More flexible interaction", "More finishers", "More protection", "More political payoff"),
    "fairness": ("More parity-breaking support", "More win conditions", "More protection", "More card draw", "More table-appropriate alternatives"),
    "negotiated_removal": ("More flexible interaction", "More win conditions", "More card draw", "More political payoff", "More protection"),
    "soft_lock": ("More finishers", "More protection", "More card draw", "More parity-breaking tools", "Less oppressive alternatives if a lower bracket"),
    "gift_politics": ("More gift payoff", "More protection", "More card draw", "More defensive tools", "More finishers"),
    "combo_deterrence": ("More card draw", "More protection", "More flexible answers", "More finishers", "More meta-appropriate hate"),
    "reputation": ("More resilience", "More table-friendly alternatives", "More protection", "More lower-bracket replacements", "More clear theme support"),
}

# §3.49 Political Cut Review Rules — GENERIC guidance for any political deck.
# Advisory only: the v1.6 cut engine still produces the mechanical cut list; this
# tells the human/AI how to review political cards differently.
POLITICAL_CUT_GUIDANCE: dict[str, tuple[str, ...]] = {
    "do_not_auto_cut": (
        "Low-power deterrent pieces if they protect the political plan",
        "Group Hug pieces if the deck has asymmetrical payoffs",
        "Goad cards if the commander rewards opponents attacking each other",
        "Pillowfort cards if the win condition is slow",
        "Curse or bounty cards if they redirect threat effectively",
        "Bad-gift cards if the deck has donate effects",
        "Rattlesnake cards if they are the deck's primary defense",
        "Monarch support if the deck can defend or reclaim the crown",
        "Fog cards if the deck has inevitability",
        "Rule-setting cards if the deck breaks parity",
    ),
    "raise_cut_pressure": (
        "Group Hug / group ramp with no payoff or that helps opponents win first",
        "Chaos cards with no win condition",
        "Political cards that rely on opponents making obviously bad choices",
        "Pillowfort cards in a deck with no inevitability",
        "Goad cards in creature-light metas",
        "Curses that annoy one player without scaling",
        "Punisher cards where opponents pick a harmless mode",
        "Symmetrical effects the deck does not break",
        "Rattlesnake cards too weak to deter attacks",
        "Excessive board wipes with no closer",
        "Table-police cards inappropriate for the intended bracket",
    ),
}

# §3.4 Global Political Primary Gate: "a deck should not be labeled Politics just
# because it contains political cards." We enforce this with a minimum density of
# UNIQUELY-POLITICAL signals before any archetype may be primary/secondary.
# Structural/value signals (protection, card draw, removal, combo pieces, instant
# interaction, …) are shared by ordinary decks and are EXCLUDED from the count, so
# a value deck that merely trips a structural gate (e.g. "Do Not Touch Me" via
# incidental hexproof) is NOT mislabeled political.
_STRUCTURAL_SIGNALS: frozenset[str] = frozenset({
    "board_wipe", "board_reset", "targeted_removal", "visible_interaction", "control_piece",
    "protection", "recursion", "win_condition", "card_draw", "tutor", "card_selection",
    "anti_targeting", "board_protection", "protected_win_condition", "voltron", "value_engine",
    "combo_piece", "low_threat_value", "instant_speed_interaction", "mill", "planeswalker",
    "fast_win", "fast_payoff", "self_advancement", "alternate_win_condition", "flexible_removal",
})

def _build_core_signals() -> frozenset[str]:
    """All political signals any archetype is built from (anchors + payoff +
    protection + inevitability), minus the structural/value signals shared by
    ordinary decks. This is the §3.4 'political_signal_count' vocabulary."""
    core: set[str] = set()
    for arch in POLITICAL_ARCHETYPES:
        core |= set(arch.anchors)
        core |= set(arch.payoff)
        core |= set(arch.protection)
        core |= set(arch.inevitability)
    return frozenset(core - _STRUCTURAL_SIGNALS)


# Uniquely-political signal vocabulary (archetype anchors + payoff + protection +
# inevitability, minus structural/value signals). Used to report a deck's overall
# political density (§3.4 political_signal_count) and to guard per-archetype
# eligibility against value decks that merely trip a structural gate.
CORE_POLITICAL_SIGNALS: frozenset[str] = _build_core_signals()


@dataclass(slots=True)
class DetectedPoliticalArchetype:
    key: str
    name: str
    section: str
    axis: str
    role: str               # primary | secondary | minor_package | support | manual_review | modifier
    confidence: str         # low | medium | high
    score: int
    commander_support: str  # none | light | moderate | strong
    gate_passed: bool
    incentive_present: bool
    protection_present: bool
    payoff_present: bool
    inevitability_present: bool
    evidence: list[str] = field(default_factory=list)
    example_cards: list[str] = field(default_factory=list)
    replacement_categories: list[str] = field(default_factory=list)  # §3.50


@dataclass(slots=True)
class PoliticalArchetypeSummary:
    is_political: bool
    primary: DetectedPoliticalArchetype | None
    secondary: DetectedPoliticalArchetype | None
    detected: list[DetectedPoliticalArchetype]
    reputation_modifier: str   # none | low | medium | high
    table_dependency: str      # low | medium | high
    salt_risk: str             # low | medium | high
    political_density: int     # §3.4 count of uniquely-political signals
    confidence: str
    warnings: list[str] = field(default_factory=list)
    cut_guidance: dict = field(default_factory=dict)  # §3.49 generic cut rules


def _commander_support(arch: PoliticalArchetype, flags: dict, anchor_density: int) -> str:
    if arch.commander_flag and flags.get(arch.commander_flag, False):
        return "strong" if anchor_density >= 3 else "moderate"
    return "none"


def _support_score(support: str) -> int:
    return {"strong": 4, "moderate": 2, "light": 1, "none": 0}.get(support, 0)


def _example_cards(arch: PoliticalArchetype, signals_by_card: dict[str, list[str]]) -> list[str]:
    wanted = set(arch.anchors) | set(arch.payoff)
    out: list[str] = []
    for name, sigs in signals_by_card.items():
        if wanted & set(sigs):
            out.append(name)
        if len(out) >= 6:
            break
    return out


def _score_archetype(arch: PoliticalArchetype, counts: Any, flags: dict) -> dict:
    anchor_density = _d(counts, *arch.anchors) if arch.anchors else 0
    payoff_density = _d(counts, *arch.payoff) if arch.payoff else 0
    protection_density = _d(counts, *arch.protection) if arch.protection else 0
    inev_density = _d(counts, *arch.inevitability) if arch.inevitability else 0

    support = _commander_support(arch, flags, anchor_density)
    win_present = flags.get("has_clear_win_path", False) or inev_density >= 1

    # §3.53 additive density + commander support, minus risk penalties.
    score = anchor_density * 2 + payoff_density * 2 + protection_density * 1 + inev_density * 3
    score += _support_score(support)
    if payoff_density == 0 and not arch.modifier_only:
        score -= 4  # no_payoff
    if not win_present and not arch.modifier_only:
        score -= 5  # no_win_condition

    gate_passed = bool(arch.gate(counts, flags))
    return {
        "anchor_density": anchor_density,
        "payoff_density": payoff_density,
        "protection_density": protection_density,
        "inev_density": inev_density,
        "support": support,
        "win_present": win_present,
        "score": int(score),
        "gate_passed": gate_passed,
    }


def _confidence(s: dict) -> str:
    if s["gate_passed"] and s["support"] == "strong" and s["payoff_density"] >= 1 and s["win_present"]:
        return "high"
    if s["gate_passed"] or (s["anchor_density"] >= 2 and s["payoff_density"] >= 1):
        return "medium"
    return "low"


def classify_political_archetypes(profile: PoliticalSignalProfile) -> PoliticalArchetypeSummary:
    """Classify a deck against all Section-3 political archetypes."""
    counts = getattr(profile, "counts", None) or {}
    flags = getattr(profile, "flags", None) or {}
    signals_by_card = getattr(profile, "signals_by_card", None) or {}

    scored: list[tuple[PoliticalArchetype, dict]] = []
    for arch in POLITICAL_ARCHETYPES:
        if arch.modifier_only:
            continue
        s = _score_archetype(arch, counts, flags)
        scored.append((arch, s))

    # Primary eligibility = the archetype's own verbatim gate passed AND it shows
    # real density in its OWN uniquely-political footprint (anchors + payoff +
    # protection, minus structural signals). This stops an archetype whose
    # footprint is purely structural (e.g. "Do Not Touch Me" = incidental hexproof)
    # from claiming a political primary, while still allowing commander-driven
    # archetypes (e.g. Monarch, whose political cards are crown-defense pieces).
    def _core_component_density(arch: PoliticalArchetype) -> int:
        footprint = (set(arch.anchors) | set(arch.payoff) | set(arch.protection)) - _STRUCTURAL_SIGNALS
        return _d(counts, *footprint)

    eligible = [
        (a, s) for a, s in scored
        if s["gate_passed"] and _core_component_density(a) >= 2
    ]
    eligible.sort(key=lambda it: it[1]["score"], reverse=True)

    # §3.6 suppression: if a SPECIFIC political archetype is primary-eligible, the
    # generic "Politics / Deal-Making" theme is demoted out of the primary slot.
    specific_eligible = [a for a, _ in eligible if not a.generic]
    if specific_eligible:
        eligible = [(a, s) for a, s in eligible if not a.generic] + \
                   [(a, s) for a, s in eligible if a.generic]

    detected: list[DetectedPoliticalArchetype] = []

    def _build(arch: PoliticalArchetype, s: dict, role: str) -> DetectedPoliticalArchetype:
        evidence: list[str] = []
        if s["anchor_density"]:
            evidence.append(f"{s['anchor_density']} core political signal(s)")
        if s["payoff_density"]:
            evidence.append(f"{s['payoff_density']} payoff signal(s)")
        if s["protection_density"]:
            evidence.append(f"{s['protection_density']} protection signal(s)")
        if s["support"] != "none":
            evidence.append(f"commander support: {s['support']}")
        if not s["win_present"]:
            evidence.append("no clear win path detected (review payoff)")
        return DetectedPoliticalArchetype(
            key=arch.key, name=arch.name, section=arch.section, axis=arch.axis,
            role=role, confidence=_confidence(s), score=s["score"],
            commander_support=s["support"], gate_passed=s["gate_passed"],
            incentive_present=s["anchor_density"] >= 1,
            protection_present=s["protection_density"] >= 1,
            payoff_present=s["payoff_density"] >= 1,
            inevitability_present=s["inev_density"] >= 1,
            evidence=evidence,
            example_cards=_example_cards(arch, signals_by_card),
            replacement_categories=list(POLITICAL_REPLACEMENT_CATEGORIES.get(arch.key, ())),
        )

    primary = None
    secondary = None
    used: set[str] = set()
    if eligible:
        primary = _build(*eligible[0], role="primary")
        used.add(eligible[0][0].key)
        detected.append(primary)
        if len(eligible) > 1:
            secondary = _build(*eligible[1], role="secondary")
            used.add(eligible[1][0].key)
            detected.append(secondary)
            for arch, s in eligible[2:]:
                detected.append(_build(arch, s, role="minor_package"))
                used.add(arch.key)

    # Non-eligible but present themes -> support / minor / manual review.
    for arch, s in scored:
        if arch.key in used:
            continue
        if arch.suppress_if_thin and s["anchor_density"] < 2:
            continue
        if s["anchor_density"] >= 3 and s["payoff_density"] >= 1:
            detected.append(_build(arch, s, role="support"))
        elif s["anchor_density"] >= 2:
            detected.append(_build(arch, s, role="manual_review"))

    # Modifier-only themes (Social Contract, Reputation).
    reputation_modifier = "none"
    rep_arch = ARCHETYPES_BY_KEY.get("reputation")
    if flags.get("commander_has_high_threat_reputation", False) or _d(counts, "oppressive_effect") >= 4:
        reputation_modifier = "high" if flags.get("commander_has_high_threat_reputation", False) else "medium"
        if rep_arch:
            detected.append(DetectedPoliticalArchetype(
                key=rep_arch.key, name=rep_arch.name, section=rep_arch.section, axis=rep_arch.axis,
                role="modifier", confidence="medium", score=0, commander_support="none",
                gate_passed=False, incentive_present=True, protection_present=False,
                payoff_present=False, inevitability_present=False,
                evidence=[f"reputation modifier: {reputation_modifier}"], example_cards=[],
            ))

    is_political = primary is not None or secondary is not None
    table_dependency, salt_risk = _table_and_salt(primary, detected)
    warnings = _warnings(primary, reputation_modifier, table_dependency, salt_risk)
    overall_conf = primary.confidence if primary else "low"
    political_density = _d(counts, *CORE_POLITICAL_SIGNALS)
    # §3.49 generic cut guidance — only meaningful when the deck is political.
    cut_guidance = {k: list(v) for k, v in POLITICAL_CUT_GUIDANCE.items()} if is_political else {}

    return PoliticalArchetypeSummary(
        is_political=is_political,
        primary=primary,
        secondary=secondary,
        detected=detected,
        reputation_modifier=reputation_modifier,
        table_dependency=table_dependency,
        salt_risk=salt_risk,
        political_density=political_density,
        confidence=overall_conf,
        warnings=warnings,
        cut_guidance=cut_guidance,
    )


def _table_and_salt(primary, detected) -> tuple[str, str]:
    if primary is not None:
        arch = ARCHETYPES_BY_KEY.get(primary.key)
        if arch:
            return arch.table_dependency, arch.salt_risk
    # No primary: take the strongest detected theme's profile, else low/low.
    for d in detected:
        arch = ARCHETYPES_BY_KEY.get(d.key)
        if arch and not arch.modifier_only:
            return arch.table_dependency, arch.salt_risk
    return "low", "low"


_KINGMAKER_KEYS = {"group_hug", "resource_redistribution", "tablewide_acceleration", "table_balancer", "gift_politics"}
_STALL_KEYS = {"pillowfort", "turbo_fog", "soft_lock"}


def _warnings(primary, reputation_modifier: str, table_dependency: str, salt_risk: str) -> list[str]:
    out: list[str] = []
    if primary is not None:
        if not primary.payoff_present or not primary.inevitability_present:
            out.append(
                "No-payoff risk: the deck changes table behavior but may lack enough payoff to convert it into a win."
            )
        if primary.key in _KINGMAKER_KEYS:
            out.append(
                "Kingmaker risk: some cards may help opponents more than the pilot - review, do not auto-cut."
            )
        if primary.key in _STALL_KEYS:
            out.append(
                "Stall risk: the deck can slow or redirect the game but needs a clearer way to close once stable."
            )
    if salt_risk == "high":
        out.append("Salt risk: this deck uses effects that may create table frustration, especially in long games.")
    if table_dependency == "high":
        out.append("Table dependency: this strategy leans on opponent behavior and can perform very differently across pods.")
    if reputation_modifier in {"medium", "high"}:
        out.append("Reputation: this commander/card package may draw early attention regardless of actual power level.")
    return out
