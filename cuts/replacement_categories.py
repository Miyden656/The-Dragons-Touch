"""Replacement category and role-need helpers.

Patch Batch 4 cleanup:
- Replacement needs should be based on role gaps relative to the deck plan, not
  generic Commander defaults only.
- Avoid misleading categories like more board wipes in proactive creature decks
  unless the shortage is severe.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from analysis.strategy_scoring import StrategySummary


@dataclass(slots=True)
class ReplacementNeedDetail:
    # v0.9.2 structured replacement-need profile entry.
    category: str
    priority: str = "Medium"
    need_type: str = "role_gap"
    source: str = "heuristic"
    reason: str = ""
    deck_evidence: list[str] = field(default_factory=list)
    suggested_replacement_shape: str = ""
    caution: str = ""


@dataclass(slots=True)
class ReplacementNeedSummary:
    priority_categories: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    need_details: list[ReplacementNeedDetail] = field(default_factory=list)
    role_gap_summary: list[str] = field(default_factory=list)
    strategy_need_summary: list[str] = field(default_factory=list)
    detection_version: str = "v0.9.2-dev"


def _add(categories: list[str], *values: str) -> None:
    for value in values:
        if value and value not in categories:
            categories.append(value)


def _is_proactive_creature_strategy(primary: str) -> bool:
    primary = primary.lower()
    return any(token in primary for token in [
        "typal", "token", "go-wide", "go-tall", "combat", "stompy", "creature", "mutate",
        "equipment", "voltron", "counters",
    ])


def _is_control_or_slow_setup_strategy(primary: str, secondary: str) -> bool:
    joined = f"{primary} {secondary}".lower()
    return any(token in joined for token in ["control", "superfriends", "pillowfort", "slow alternate", "stax"])


def _need_priority(category: str) -> str:
    cat = category.lower()
    if "build / complete" in cat or "addition:" in cat:
        return "Required"
    if any(token in cat for token in ["targeted removal", "protection", "card draw", "ramp", "lands"]):
        return "High"
    if any(token in cat for token in ["spell payoff", "card selection", "instant/sorcery", "commander protection"]):
        return "High"
    if any(token in cat for token in ["payoff", "density", "recursion", "token production", "combat finishers"]):
        return "Medium"
    return "Medium"


def _need_type(category: str) -> str:
    cat = category.lower()
    if "build / complete" in cat or "addition:" in cat:
        return "deck_completion"
    if any(token in cat for token in ["ramp", "card draw", "targeted removal", "board wipes", "table-stabilizing", "protection", "lands"]):
        return "generic_role_gap"
    if any(token in cat for token in ["instant/sorcery", "spell payoff", "card selection"]):
        return "strategy_specific_need"
    if any(token in cat for token in ["token", "combat", "typal", "dragon", "graveyard", "recursion", "landfall", "sacrifice", "mutate", "toughness", "defender"]):
        return "strategy_specific_need"
    return "review_need"


def _need_source(category: str, primary: str, secondary: str) -> str:
    cat = category.lower()
    joined = f"{primary} {secondary}".lower()
    if "build / complete" in cat or "addition:" in cat:
        return "deck_size"
    if "spellslinger" in joined and any(token in cat for token in ["instant/sorcery", "spell payoff", "card selection"]):
        return "primary_strategy"
    if any(token in joined for token in ["token", "go-wide", "go-tall"]) and any(token in cat for token in ["token", "combat", "protection"]):
        return "primary_or_secondary_strategy"
    if ("landfall" in joined or "lands" in joined) and "land" in cat:
        return "primary_strategy"
    if ("dragon" in joined or "typal" in joined) and ("dragon" in cat or "typal" in cat):
        return "primary_strategy"
    if any(token in cat for token in ["ramp", "card draw", "targeted removal", "board wipes", "table-stabilizing", "protection"]):
        return "role_count_gap"
    return "heuristic"


def _replacement_shape(category: str) -> str:
    cat = category.lower()
    if "targeted removal" in cat or "interaction" in cat or "answer" in cat:
        return "Prefer flexible, low-opportunity-cost interaction that fits the deck's colors and does not dilute the main engine."
    if "protection" in cat:
        return "Prefer protection that shields the commander, key engine pieces, or the board; avoid treating self-protection bodies as automatic fixes."
    if "instant/sorcery" in cat:
        return "Prefer instants and sorceries that also draw, interact, copy, protect, or advance the deck's primary spell plan."
    if "card selection" in cat:
        return "Prefer cheap filtering, selection, or tutors that help the deck find engine pieces without becoming off-plan goodstuff."
    if "spell payoff" in cat:
        return "Prefer cards that reward casting or copying noncreature spells and help convert spell volume into advantage or a win."
    if "ramp" in cat or "mana" in cat:
        return "Prefer ramp that supports the deck's curve and commander timing rather than slow, off-plan mana pieces."
    if "card draw" in cat or "card advantage" in cat:
        return "Prefer draw that triggers from, supports, or keeps pace with the deck's primary game plan."
    if "token" in cat:
        return "Prefer token makers that support the actual win condition or commander engine, not incidental utility tokens only."
    if "combat" in cat or "evasion" in cat or "trample" in cat:
        return "Prefer finishers or combat support that convert the existing board into a win rather than standalone attackers."
    if "graveyard" in cat or "recursion" in cat:
        return "Prefer graveyard setup or recursion that directly supports the deck's engine and expected play pattern."
    if "lands" in cat or "landfall" in cat:
        return "Prefer land count, land ramp, extra land drops, or landfall payoffs only when they support the detected land plan."
    if "build / complete" in cat or "addition:" in cat:
        return "Prioritize legal deck completion before optional tuning."
    return "Prefer cards that directly solve this role while supporting the detected commander plan."


def _need_caution(category: str) -> str:
    cat = category.lower()
    if "protection" in cat:
        return "Do not let generic/self-only protection masquerade as commander or board protection."
    if "board wipes" in cat or "table-stabilizing" in cat:
        return "Do not overload proactive decks with wipes unless the table plan actually needs them."
    if "spell payoff" in cat or "instant/sorcery" in cat:
        return "Do not add generic spells that raise density but fail to support the commander or win condition."
    if "token" in cat:
        return "Treasure, Clue, Food, and Map tokens should not satisfy creature-token/go-wide needs by themselves."
    if "combat" in cat or "evasion" in cat:
        return "Avoid standalone beaters unless the pilot explicitly wants more independent threats."
    return "Treat this as a role target for review, not an automatic card recommendation."


def _detail_for_category(category: str, role_counts: Counter[str], primary_strategy: str, secondary_strategy: str, deck_card_count: int) -> ReplacementNeedDetail:
    cat = category.lower()
    evidence: list[str] = []

    land_count = role_counts.get("land", 0)
    ramp_count = role_counts.get("ramp", 0) + role_counts.get("land_ramp", 0)
    draw_count = role_counts.get("card_draw", 0) + role_counts.get("card_advantage", 0)
    removal_count = role_counts.get("targeted_removal", 0) + role_counts.get("repeatable_removal", 0)
    wipe_count = role_counts.get("board_wipe", 0)
    protection_count = role_counts.get("protection", 0) + role_counts.get("commander_protection", 0)

    if "build / complete" in cat or "addition:" in cat:
        missing = max(0, 100 - deck_card_count)
        evidence.append(f"Deck is short {missing} card(s).")
    if "ramp" in cat or "mana" in cat:
        evidence.append(f"Ramp count detected: {ramp_count}.")
    if "card draw" in cat or "card advantage" in cat or "selection" in cat:
        evidence.append(f"Draw/card-advantage count detected: {draw_count}.")
    if "targeted removal" in cat or "interaction" in cat or "answer" in cat:
        evidence.append(f"Targeted/repeatable removal count detected: {removal_count}.")
    if "board wipe" in cat or "table-stabilizing" in cat:
        evidence.append(f"Board wipe count detected: {wipe_count}.")
    if "protection" in cat:
        evidence.append(f"Protection count detected: {protection_count}.")
    if ("land" in cat and "landfall" in cat) or cat == "more lands":
        evidence.append(f"Land count detected: {land_count}.")
    if "instant/sorcery" in cat or "spell payoff" in cat:
        evidence.append(f"Primary strategy detected: {primary_strategy}.")
    if "token" in cat or "combat" in cat or "go-wide" in cat or "go-tall" in cat:
        evidence.append(f"Secondary strategy detected: {secondary_strategy}.")
    if not evidence:
        evidence.append("Detected from replacement-category heuristics and current strategy context.")

    reason = f"{category} was detected from {_need_source(category, primary_strategy, secondary_strategy)}."
    return ReplacementNeedDetail(
        category=category,
        priority=_need_priority(category),
        need_type=_need_type(category),
        source=_need_source(category, primary_strategy, secondary_strategy),
        reason=reason,
        deck_evidence=evidence,
        suggested_replacement_shape=_replacement_shape(category),
        caution=_need_caution(category),
    )


def _build_need_details(categories: list[str], role_counts: Counter[str], primary_strategy: str, secondary_strategy: str, deck_card_count: int) -> list[ReplacementNeedDetail]:
    return [
        _detail_for_category(category, role_counts, primary_strategy, secondary_strategy, deck_card_count)
        for category in categories
    ]


def build_replacement_need_summary(role_counts: Counter[str], strategy_summary: StrategySummary, deck_card_count: int) -> ReplacementNeedSummary:
    categories: list[str] = []
    notes: list[str] = []
    primary = strategy_summary.primary_strategy.lower()
    secondary = strategy_summary.secondary_strategy.lower()
    land_count = role_counts.get("land", 0)
    ramp_count = role_counts.get("ramp", 0) + role_counts.get("land_ramp", 0)
    draw_count = role_counts.get("card_draw", 0) + role_counts.get("card_advantage", 0)
    removal_count = role_counts.get("targeted_removal", 0) + role_counts.get("repeatable_removal", 0)
    wipe_count = role_counts.get("board_wipe", 0)
    protection_count = role_counts.get("protection", 0) + role_counts.get("commander_protection", 0)

    if deck_card_count < 100:
        missing = 100 - deck_card_count
        _add(categories, "Build / complete deck to 100", "Addition: reach 100 cards before cutting")
        notes.append(f"Deck is short {missing} card(s); prioritize additions before cuts unless intentionally rebuilding.")

    # Generic role gaps, with more context-sensitive thresholds.
    if ramp_count < 8:
        _add(categories, "More ramp")
    if draw_count < 8:
        _add(categories, "More card draw")
    if removal_count < 5:
        _add(categories, "More targeted removal")

    if wipe_count < 2:
        if _is_control_or_slow_setup_strategy(primary, secondary):
            _add(categories, "More board wipes")
        elif _is_proactive_creature_strategy(primary) and wipe_count == 0:
            _add(categories, "More table-stabilizing interaction")
            notes.append("Proactive creature decks may prefer asymmetrical wipes, protection, or flexible interaction over generic board wipes.")
        elif not _is_proactive_creature_strategy(primary):
            _add(categories, "More board wipes")

    if protection_count < 3:
        _add(categories, "More protection")

    # Strategy-aware categories.
    if "aristocrats" in primary or "sacrifice" in primary:
        _add(categories, "More sacrifice outlets", "More token production", "More recursion", "More death payoffs")

    if "landfall" in primary or "lands" in primary:
        if land_count < 38 and deck_card_count >= 100:
            _add(categories, "More lands")
        _add(categories, "More land ramp", "More extra land drops", "More land recursion", "More landfall payoff")

    if "dragon typal" in primary:
        if role_counts.get("dragon_typal", 0) < 25:
            _add(categories, "More Dragon density")
        _add(categories, "More Dragon payoff", "More copy-token payoff", "More commander protection")

    elif "typal" in primary:
        if role_counts.get("typal_density_piece", 0) < 28:
            _add(categories, "More typal density")
        _add(categories, "More typal payoff", "More on-type role players")

    if "token combat" in primary or "tokens" in primary:
        _add(categories, "More token production", "More combat finishers", "More board protection")

    if "go-wide-go-tall" in primary or "go-tall" in primary or "combat" in primary:
        _add(categories, "More combat payoff", "More evasion/trample", "More protection")

    if "spellslinger" in primary:
        _add(categories, "More instant/sorcery density", "More card selection", "More spell payoff")

    if "mutate" in primary or "creature stack" in primary:
        _add(categories, "More mutate enablers", "More mutate payoff", "More protection for stacked creatures")

    if "graveyard" in primary:
        _add(categories, "More graveyard setup", "More recursion", "More protection from graveyard hate")

    if "draw-punisher" in primary or "wheels" in primary or "group slug" in primary:
        _add(categories, "More draw-punisher payoff", "More wheel effects", "More table-damage protection")

    if "toughness" in primary or "defender" in primary:
        _add(categories, "More toughness-matters payoffs", "More defender support")

    if not categories:
        notes.append("No urgent generic replacement category was detected by the checkpoint heuristics.")
    else:
        notes.append("Replacement categories are role needs, not exact card recommendations yet.")

    categories = categories[:12]
    need_details = _build_need_details(
        categories,
        role_counts,
        strategy_summary.primary_strategy,
        strategy_summary.secondary_strategy,
        deck_card_count,
    )

    role_gap_summary = [
        f"{detail.category} ({detail.priority}; {detail.source})"
        for detail in need_details
        if detail.need_type == "generic_role_gap"
    ]
    strategy_need_summary = [
        f"{detail.category} ({detail.priority}; {detail.source})"
        for detail in need_details
        if detail.need_type == "strategy_specific_need"
    ]

    if need_details:
        notes.append("v0.9.2 replacement need profile active: role gaps and strategy-specific needs are now described with evidence and caution text.")

    return ReplacementNeedSummary(
        priority_categories=categories,
        notes=notes,
        need_details=need_details,
        role_gap_summary=role_gap_summary,
        strategy_need_summary=strategy_need_summary,
    )
