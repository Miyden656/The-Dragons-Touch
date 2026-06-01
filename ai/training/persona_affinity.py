"""Deck-derived persona affinity — pick the personas a deck naturally wants.

WHY THIS EXISTS
---------------
Candidate generation used to pair every deck with a hand-typed persona list (the
caller's `--personas` flag). That guesses. This module instead reads the engine's
OWN verified read of a deck — its detected strategy, bracket/power level, the
multiplayer pod signal, and the Section-3 POLITICAL archetype — and maps that to
the 1-2 deck-building philosophies the deck actually fits, plus the neutral
baseline. So each deck's training candidates reflect what the deck is trying to
do (including how it manipulates the table), not an arbitrary lens.

Axes, in priority order for the two non-baseline slots: strategy (what the deck
builds) -> political (how it manipulates the table, when political) -> power (how
hard/casual it plays). The political axis is absent for non-political decks, so
their picks are unchanged.

TWO KINDS OF PERSONA
--------------------
- Strategy / performance lenses (aggressive, combo, control, engine, etc.) CAN be
  inferred from the cards. Those are what this module picks from.
- INTENT lenses (pet card, theme/vibe, "let me do my thing", self-imposed
  constraints) are pure PLAYER INTENT — nothing in a decklist reveals them. They
  are deliberately EXCLUDED here and covered by a separate guaranteed pass
  (see ai/cli/generate_corpus.py --intent-sample) so the corpus never loses a
  voice. `INTENT_PERSONAS` is the canonical list of those four.

This is a transparent heuristic table, not a black box: every pick carries a
`why`, and a low-confidence / unrecognized read falls back to sensible defaults
(mirroring how the engine itself degrades to Balanced when unsure).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Player-intent lenses that a decklist cannot reveal. Excluded from deck-derived
# picks; covered by the dedicated intent-sample pass + the coverage report.
INTENT_PERSONAS: tuple[str, ...] = (
    "pet_card",
    "theme_vibe",
    "let_me_do_my_thing",
    "constraint_builder",
)

BASELINE_PERSONA = "balanced_unknown"


@dataclass(slots=True)
class PersonaPick:
    """One chosen persona key plus the human-readable reason it was chosen."""

    key: str
    why: str


def _attr(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


# Strategy archetype -> best-fit deck-derivable persona. Matched as a lowercased
# substring of the engine's primary (then secondary) strategy label, so it is
# robust to the exact wording in ARCHETYPE_DEFINITIONS. Order matters: more
# specific reads come first.
_STRATEGY_AFFINITY: tuple[tuple[str, str], ...] = (
    ("combo", "combo_builder"),
    ("control", "interaction_controller"),
    ("draw-punisher", "interaction_controller"),
    ("group slug", "interaction_controller"),
    ("wheel", "interaction_controller"),
    ("voltron", "big_creature_stompy"),
    ("go-tall", "big_creature_stompy"),
    ("stompy", "big_creature_stompy"),
    ("big mana", "big_creature_stompy"),
    ("ramp", "big_creature_stompy"),
    ("toughness", "big_creature_stompy"),
    ("defender", "big_creature_stompy"),
    ("token", "big_moment"),
    ("go-wide", "big_moment"),
    ("dragon", "commander_exploiter"),       # commander-defined emergent plans
    ("typal", "big_creature_stompy"),
    ("tribal", "big_creature_stompy"),
    ("aristocrat", "engine_builder"),
    ("sacrifice", "engine_builder"),
    ("spellslinger", "engine_builder"),
    ("noncreature", "engine_builder"),
    ("graveyard", "engine_builder"),
    ("reanimat", "engine_builder"),
    ("blink", "engine_builder"),
    ("flicker", "engine_builder"),
    ("artifact", "engine_builder"),
    ("landfall", "engine_builder"),
    ("lands matter", "engine_builder"),
    ("lifegain", "engine_builder"),
    ("lifedrain", "engine_builder"),
    ("commander", "commander_exploiter"),    # "...Commander Engine", emergent
    ("midrange", "engine_builder"),
    ("value", "engine_builder"),
)

# Tried in order to backfill if the strategy/power axes collapse to one pick.
_FALLBACK_FITS: tuple[str, ...] = ("engine_builder", "consistency_maximizer", "big_moment")

# Section-3 political archetype KEY -> best-fit deck-derivable persona. The engine's
# political classifier (analysis/political_archetypes.py) detects HOW a deck
# manipulates the table; this maps that table plan onto the closest existing
# coaching lens. There is no dedicated "politician" philosophy, so:
#   - table-control / punishment / deterrence / combat-direction -> interaction_controller
#   - social incentive ENGINES (give resources, votes, deals, bounties) -> engine_builder
#   - plus a few specials (secret combo, chaos spectacle, hidden info, villain, theft).
# Modifier-only archetypes (social_contract, reputation) are never a primary, so
# they are intentionally omitted (no political pick fires for them).
_POLITICAL_AFFINITY: dict[str, str] = {
    # table control / punishment / deterrence
    "group_slug": "interaction_controller",
    "punisher": "interaction_controller",
    "aikido": "interaction_controller",
    "rattlesnake": "interaction_controller",
    "table_police": "interaction_controller",
    "anti_combo": "interaction_controller",
    "goad_control": "interaction_controller",
    "negotiated_removal": "interaction_controller",
    "combo_deterrence": "interaction_controller",
    "pillowfort": "interaction_controller",
    "turbo_fog": "interaction_controller",
    "do_not_touch_me": "interaction_controller",
    "soft_lock": "interaction_controller",
    "sandbag_control": "interaction_controller",
    "board_reset_politics": "interaction_controller",
    "retaliation": "interaction_controller",
    "fairness": "interaction_controller",
    "monarch": "interaction_controller",
    "curses": "interaction_controller",
    # combat direction
    "forced_combat": "interaction_controller",
    "combat_manipulation": "interaction_controller",
    "shared_combat": "interaction_controller",
    "threat_redistribution": "interaction_controller",
    "attack_elsewhere": "interaction_controller",
    # social incentive engines
    "group_hug": "engine_builder",
    "deal_politics": "engine_builder",
    "voting": "engine_builder",
    "bounty": "engine_builder",
    "resource_redistribution": "engine_builder",
    "gift_politics": "engine_builder",
    "table_balancer": "engine_builder",
    "shared_enemy": "engine_builder",
    "hidden_asymmetry": "engine_builder",
    "tablewide_acceleration": "engine_builder",
    "life_politics": "engine_builder",
    # specials
    "secret_combo": "combo_builder",
    "information_politics": "johnny_jenny",
    "theft": "commander_exploiter",
    "chaos": "battlecruiser",
    "villain": "competitive_closer",
}


def _strategy_persona(strategy_label: str) -> tuple[str, str] | None:
    low = (strategy_label or "").lower()
    for needle, persona in _STRATEGY_AFFINITY:
        if needle in low:
            return persona, f"primary strategy '{strategy_label}' fits the {persona} lens"
    return None


def _political_persona(political_summary: Any) -> tuple[str, str] | None:
    """Map a detected political archetype to its best-fit coaching lens.

    Returns None when the deck is not political (so non-political decks are
    unaffected). The political read is a SPECIFIC table-plan signal, so callers
    weight it ahead of the generic power lens.
    """
    if not political_summary:
        return None
    if not _attr(political_summary, "is_political", False):
        return None
    primary = _attr(political_summary, "primary")
    if primary is None:
        return None
    key = _attr(primary, "key", "") or ""
    persona = _POLITICAL_AFFINITY.get(key)
    if not persona:
        return None
    name = _attr(primary, "name", key) or key
    return persona, f"political archetype '{name}' fits the {persona} lens"


def _power_persona(bracket: str, threat_band: str, pressure: str) -> tuple[str, str]:
    """Map power level (bracket + pod threat density + bracket pressure) to a
    performance/experience lens."""
    b = (bracket or "").lower()
    pr = (pressure or "").lower()
    high = ("4" in b or "5" in b or "cedh" in b or threat_band == "high" or pr in {"high", "very_high"})
    low = (("1" in b or "2" in b) and threat_band != "high" and pr in {"", "none", "low"})
    if high:
        return "competitive_closer", "high power / threat level fits a performance-closing lens"
    if low:
        return "battlecruiser", "lower-power / casual table fits a battlecruiser spectacle lens"
    return "consistency_maximizer", "mid-power table fits a consistency-focused lens"


def _valid_keys() -> set[str]:
    """The real philosophy keys, so a typo here can never emit a bogus persona."""
    try:
        from analysis.deck_building_philosophies import PHILOSOPHY_PROFILES
        return set(PHILOSOPHY_PROFILES.keys())
    except Exception:  # noqa: BLE001 - validation is best-effort
        return set()


def derive_personas_for_deck(analysis: Any) -> list[PersonaPick]:
    """Return the neutral baseline + up to 2 best-fit (deck-derivable) personas.

    `analysis` is the dict from main.build_analysis_context (or any object exposing
    strategy_summary / bracket_summary / multiplayer_summary). Read defensively;
    a missing/garbage analysis still returns a valid baseline-plus-fallback list.
    """
    strat = _attr(analysis, "strategy_summary")
    bracket = _attr(analysis, "bracket_summary")
    mp = _attr(analysis, "multiplayer_summary")
    pol = _attr(analysis, "political_summary")

    primary = _attr(strat, "primary_strategy", "") or ""
    secondary = _attr(strat, "secondary_strategy", "") or ""
    est_bracket = _attr(bracket, "estimated_bracket", "") or _attr(bracket, "intended_bracket", "") or ""
    pressure = _attr(bracket, "pressure_level", "") or ""
    threat_band = _attr(mp, "archenemy_risk_band", "low") or "low"

    valid = _valid_keys()

    def _ok(key: str) -> bool:
        return key not in INTENT_PERSONAS and (not valid or key in valid)

    picks: list[PersonaPick] = [PersonaPick(BASELINE_PERSONA, "neutral baseline lens")]
    chosen = {BASELINE_PERSONA}

    # Strategy axis: what is the deck trying to do?
    sp = _strategy_persona(primary) or _strategy_persona(secondary)
    if sp and sp[0] not in chosen and _ok(sp[0]):
        picks.append(PersonaPick(*sp))
        chosen.add(sp[0])

    # Political axis: HOW does the deck manipulate the table? This is a specific,
    # high-signal table-plan lens, so it is weighted ahead of the generic power
    # lens for political decks (and is simply absent for non-political decks).
    polp = _political_persona(pol)
    if polp and len(picks) < 3 and polp[0] not in chosen and _ok(polp[0]):
        picks.append(PersonaPick(*polp))
        chosen.add(polp[0])

    # Power axis: how hard / casual is it meant to play?
    pp = _power_persona(est_bracket, threat_band, pressure)
    if pp[0] not in chosen and _ok(pp[0]):
        picks.append(PersonaPick(*pp))
        chosen.add(pp[0])

    # Backfill to a full "baseline + 2 fit" set when an axis was unreadable.
    for fb in _FALLBACK_FITS:
        if len(picks) >= 3:
            break
        if fb not in chosen and _ok(fb):
            picks.append(PersonaPick(fb, "fallback fit (low-confidence read)"))
            chosen.add(fb)

    return picks[:3]


def intent_persona_sample(deck_paths: list, sample_size: int = 12) -> list:
    """Deterministic, evenly-spaced sample of decks for the intent-persona pass.

    Deterministic (no RNG) so a re-run covers the same decks. Returns all decks if
    there are fewer than sample_size; empty if sample_size <= 0.
    """
    if sample_size <= 0 or not deck_paths:
        return []
    n = len(deck_paths)
    if n <= sample_size:
        return list(deck_paths)
    step = n / sample_size
    return [deck_paths[int(i * step)] for i in range(sample_size)]
