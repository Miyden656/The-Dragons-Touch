"""Role tag cleanup helpers.

Round 5 cleanup goal:
- Keep raw role tagging separate from false-positive cleanup.
- Avoid making cut decisions here; this module only repairs noisy tags.
"""

from __future__ import annotations

from collections import Counter

from analysis.role_tags import CardRoleEntry, RoleAnalysisSummary

USER_FACING_TAG_RENAMES = {
    "targeted_removal": "targeted removal",
    "board_wipe": "board wipe",
    "card_draw": "card draw",
    "card_advantage": "card advantage",
    "sacrifice_outlet": "sacrifice outlet",
    "death_trigger_payoff": "death trigger payoff",
    "token_maker": "token maker",
    "artifact_token_synergy": "artifact token synergy",
    "commander_created_package": "commander-created package",
    "cast_from_outside_hand": "cast from outside hand",
    "nonhand_casting": "non-hand casting",
    "bracket_pressure": "bracket pressure",
    "high_bracket_pressure": "high bracket pressure",
}


def clean_role_tags_for_card(tags: list[str], card_types: list[str] | None = None) -> list[str]:
    """Conservative false-positive cleanup for one card's role tags."""
    card_types = card_types or []
    tag_set = set(tags)

    # A land that only produces mana should not be treated as activated-ability synergy.
    if "Land" in card_types and "activated_ability_synergy" in tag_set and not (tag_set & {"mana_sink", "utility_activated_ability"}):
        tag_set.discard("activated_ability_synergy")

    # Generic subtype presence should not be a payoff by itself.
    if "tribal_payoff" in tag_set and "typal_payoff" not in tag_set:
        tag_set.add("typal_payoff")

    # Combo language should stay cautious until a real combo module exists.
    if "combo_piece_possible" in tag_set and "win_condition" not in tag_set:
        tag_set.add("manual_review")

    # Do not let bracket tags become the only visible role.
    if tag_set <= {"bracket_pressure", "high_bracket_pressure"}:
        tag_set.add("manual_review")

    return sorted(tag_set)


def clean_user_facing_role_tags(tags: list[str]) -> list[str]:
    return [USER_FACING_TAG_RENAMES.get(tag, tag.replace("_", " ")) for tag in tags]


def apply_role_tag_cleanup(summary: RoleAnalysisSummary) -> RoleAnalysisSummary:
    """Return a cleaned copy-ish summary while preserving the dataclass shape."""
    cleaned_entries: list[CardRoleEntry] = []
    role_counts: Counter[str] = Counter()
    card_role_tags_by_card: dict[str, list[str]] = {}

    for entry in summary.card_roles:
        cleaned_tags = clean_role_tags_for_card(entry.detected_roles, entry.card_types)
        role_counts.update({tag: entry.quantity for tag in cleaned_tags})
        card_role_tags_by_card[entry.card_name] = cleaned_tags
        cleaned_entries.append(CardRoleEntry(
            card_name=entry.card_name,
            quantity=entry.quantity,
            found_in_scryfall=entry.found_in_scryfall,
            mana_value=entry.mana_value,
            card_types=entry.card_types,
            color_identity=entry.color_identity,
            detected_roles=cleaned_tags,
            confidence=entry.confidence,
            short_reason=entry.short_reason,
            type_line=entry.type_line,
        ))

    return RoleAnalysisSummary(
        card_roles=cleaned_entries,
        role_counts=role_counts,
        type_counts=summary.type_counts,
        card_role_tags_by_card=card_role_tags_by_card,
        unknown_cards=summary.unknown_cards,
    )
