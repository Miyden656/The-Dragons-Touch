"""Deck + legality views.

Consumes: parsed_deck (ParsedDeck), command_zone (CommandZoneSummary),
legality (CommanderLegalitySummary), role_summary (RoleAnalysisSummary).

The decklist is deliberately compact: name + count + role tags + mana value.
NO oracle text — full card facts are fetched on demand by the tools layer for
the few cards under discussion, never inlined for all 100.
"""

from __future__ import annotations

from typing import Any

from ai.context.safe_access import (
    as_dict,
    as_int,
    as_list,
    as_str,
    attr,
    card_name_of,
)


def build_deck_view(parsed_deck: Any, command_zone: Any, role_summary: Any) -> dict:
    color_identity = as_list(attr(command_zone, "commander_color_identity"))
    decklist = _build_decklist(role_summary)
    return {
        "commander": as_str(attr(command_zone, "commander_name", attr(parsed_deck, "commander_name"))),
        "commanders": [as_str(n) for n in as_list(attr(command_zone, "commander_names"))],
        "companions": [as_str(n) for n in as_list(attr(command_zone, "companion_names"))],
        "command_zone_rule": as_str(attr(command_zone, "command_zone_rule_detected"), "Unknown"),
        "color_identity": [as_str(c) for c in color_identity],
        "color_identity_text": as_str(attr(command_zone, "commander_color_identity_text"), "Unknown"),
        "deck_card_count": as_int(attr(parsed_deck, "deck_card_count")),
        "decklist": decklist,
        "role_counts": _counter_to_sorted(attr(role_summary, "role_counts")),
        "type_counts": _counter_to_sorted(attr(role_summary, "type_counts")),
        "unknown_cards": [as_str(n) for n in as_list(attr(role_summary, "unknown_cards"))],
    }


def build_legality_view(parsed_deck: Any, legality: Any) -> dict:
    return {
        "deck_size_legal": bool(attr(legality, "deck_size_legal", False)),
        "expected_deck_size": as_int(attr(legality, "expected_deck_size")),
        "deck_card_count": as_int(attr(parsed_deck, "deck_card_count")),
        "has_any_issues": bool(attr(legality, "has_any_issues", False)),
        "banned_cards": _names(attr(legality, "banned_cards")),
        "banned_commanders": _names(attr(legality, "banned_commanders")),
        "color_identity_violations": _names(attr(legality, "color_identity_violations")),
        "cards_not_found": [as_str(n) for n in as_list(attr(legality, "cards_not_found"))],
        "illegal_duplicate_cards": _names(attr(legality, "illegal_duplicate_cards")),
    }


def win_conditions_from_roles(role_summary: Any) -> list[str]:
    """Card names tagged as a win condition by the engine (verified, not guessed)."""
    out: list[str] = []
    for entry in as_list(attr(role_summary, "card_roles")):
        roles = [as_str(r).lower() for r in as_list(attr(entry, "detected_roles"))]
        if any("win" in r for r in roles):
            name = card_name_of(entry)
            if name:
                out.append(name)
    return out


# --- internals ------------------------------------------------------------

def _build_decklist(role_summary: Any) -> list[dict]:
    out: list[dict] = []
    for entry in as_list(attr(role_summary, "card_roles")):
        name = card_name_of(entry)
        if not name:
            continue
        out.append(
            {
                "name": name,
                "count": as_int(attr(entry, "quantity", 1)),
                "roles": [as_str(r) for r in as_list(attr(entry, "detected_roles"))],
                "mana_value": attr(entry, "mana_value"),
                "types": [as_str(t) for t in as_list(attr(entry, "card_types"))],
            }
        )
    return out


def _counter_to_sorted(counter: Any) -> dict:
    data = as_dict(counter)
    # keep it readable: high-to-low, names as strings, drop zero/None
    items = [(as_str(k), as_int(v)) for k, v in data.items() if as_int(v) > 0]
    items.sort(key=lambda kv: (-kv[1], kv[0]))
    return {k: v for k, v in items}


def _names(entries: Any) -> list[str]:
    out: list[str] = []
    for e in as_list(entries):
        name = card_name_of(e)
        if name:
            out.append(name)
    return out
