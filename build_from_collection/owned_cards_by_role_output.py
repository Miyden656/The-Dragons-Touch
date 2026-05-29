"""Owned Cards By Role Output.

Depth-C output: groups the user's owned cards into 11 possible role
buckets (Ramp, Card Draw, Targeted Removal, Board Wipes, Protection,
Recursion, Strategy Enablers, Strategy Payoffs, Finishers, Mana Base
Support, Flex). Each card may appear in multiple buckets if its oracle
text matches more than one role pattern.

This is a role-bucketing summary — it tells the user which owned cards
could fill which roles. It is not a generated deck. The deck-generation
feature lives at depth E (Full 100-Card Draft).

Land policy:
- Basic lands are assumed available.
- Nonbasic lands remain collection-first unless outside-collection upgrades are allowed by the user.

The dataclass boundary flags (generates_deck, generates_shell, etc.) remain
False because role bucketing is intentionally not deck selection. Do not
flip them without auditing dev-mode contract callers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


ROLE_BUCKETS: tuple[str, ...] = (
    "Ramp / Mana Development",
    "Card Draw / Card Advantage",
    "Targeted Removal",
    "Board Wipes",
    "Protection",
    "Recursion",
    "Strategy Enablers",
    "Strategy Payoffs",
    "Finishers / Win Conditions",
    "Mana Base Support",
    "Flex / Theme Slots",
)


def _text_from_card(card: Any) -> str:
    if isinstance(card, dict):
        parts = [
            str(card.get("name", "")),
            str(card.get("oracle_text", "")),
            str(card.get("type_line", "")),
            str(card.get("tags", "")),
        ]
        return " ".join(parts).lower()
    return str(card).lower()


def _name_from_card(card: Any) -> str:
    if isinstance(card, dict):
        return str(card.get("name") or card.get("card_name") or "Unknown Card")
    return str(card)


def _quantity_from_card(card: Any) -> int:
    if isinstance(card, dict):
        value = card.get("owned_quantity", card.get("quantity", 1))
        try:
            return int(value)
        except (TypeError, ValueError):
            return 1
    return 1


def infer_possible_roles_for_owned_card(card: Any, text: str | None = None) -> list[str]:
    """Infer possible role buckets for an owned card.

    This is a preview-only heuristic. It does not select a card for the deck.
    """
    source = (text if text is not None else _text_from_card(card)).lower()
    name = _name_from_card(card).lower()
    combined = f"{name} {source}"

    roles: list[str] = []

    if any(word in combined for word in ("sol ring", "arcane signet", "ramp", "add mana", "treasure", "mana rock", "land search")):
        roles.append("Ramp / Mana Development")
    if any(word in combined for word in ("draw", "investigate", "clue", "impulse", "card advantage")):
        roles.append("Card Draw / Card Advantage")
    if any(word in combined for word in ("destroy target", "exile target", "counter target", "fight target", "damage to target")):
        roles.append("Targeted Removal")
    if any(word in combined for word in ("destroy all", "exile all", "each creature", "all creatures", "board wipe")):
        roles.append("Board Wipes")
    if any(word in combined for word in ("hexproof", "indestructible", "protection", "phase out", "teferi's protection", "save")):
        roles.append("Protection")
    if any(word in combined for word in ("return from your graveyard", "reanimate", "recursion", "escape", "flashback")):
        roles.append("Recursion")
    if any(word in combined for word in ("token", "sacrifice", "whenever", "dies", "enters", "landfall", "cast an instant", "cast a sorcery")):
        roles.append("Strategy Enablers")
    if any(word in combined for word in ("double", "copy", "payoff", "whenever you", "drain", "lifegain", "counters")):
        roles.append("Strategy Payoffs")
    if any(word in combined for word in ("win the game", "extra combat", "overrun", "x spell", "damage to each opponent", "commander damage")):
        roles.append("Finishers / Win Conditions")
    if any(word in combined for word in ("plains", "island", "swamp", "mountain", "forest", "wastes", "land", "command tower")):
        roles.append("Mana Base Support")

    if not roles:
        roles.append("Flex / Theme Slots")

    return list(dict.fromkeys(roles))


@dataclass
class OwnedCardsByRoleEntry:
    """Preview entry for an owned card and its possible role fits."""

    card_name: str
    owned_quantity: int = 1
    possible_roles: list[str] = field(default_factory=list)
    source: str = "collection"
    notes: list[str] = field(default_factory=list)
    # v1.5.35: Bin B Owned Cards by Role — per-card collection source filenames
    # so the user can locate the card in their physical/folder collection.
    source_files: list[str] = field(default_factory=list)
    # Runtime boundary aliases.
    selects_exact_card: bool = False
    selected_for_deck: bool = False
    final_deck_inclusion: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "card_name": self.card_name,
            "owned_quantity": self.owned_quantity,
            "possible_roles": list(self.possible_roles),
            "source": self.source,
            "notes": list(self.notes),
            "source_files": list(self.source_files),
            "selects_exact_card": self.selects_exact_card,
            "selected_for_deck": self.selected_for_deck,
            "final_deck_inclusion": self.final_deck_inclusion,
        }


@dataclass
class OwnedCardsByRoleOutput:
    """Depth-C output: owned cards grouped by possible role fits.

    v1.3.21.4 explicit depth-C and output boundary aliases.
    """

    output_name: str = "Owned Cards By Role Output"
    build_depth_key: str = "C"
    depth_key: str = "C"
    selected_build_depth_key: str = "C"
    build_depth_label: str = "C - Owned Cards By Role"
    selected_commander: str = "Selected Commander"
    primary_strategy: str = "Custom / Not Sure Yet"
    secondary_strategy: str = "Custom / Not Sure Yet"
    entries: list[OwnedCardsByRoleEntry] = field(default_factory=list)
    grouped_by_role: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    preview_only: bool = True
    collection_first: bool = True
    possible_role_fits_only: bool = True
    not_final_deck_inclusions: bool = True

    # Runtime boundary aliases used by report writers and verifiers.
    generates_deck: bool = False
    generates_shell: bool = False
    generates_mana_base: bool = False
    inserts_lands: bool = False
    selects_exact_cards: bool = False
    makes_final_deck_inclusion_decisions: bool = False
    generates_role_count_targets: bool = False

    def __post_init__(self) -> None:
        self.build_depth_key = "C"
        self.depth_key = "C"
        self.selected_build_depth_key = "C"
        self.build_depth_label = "C - Owned Cards By Role"
        if not self.grouped_by_role:
            self.grouped_by_role = _group_entries_by_role(self.entries)

    def to_dict(self) -> dict[str, Any]:
        return {
            "output_name": self.output_name,
            "build_depth_key": self.build_depth_key,
            "depth_key": self.depth_key,
            "selected_build_depth_key": self.selected_build_depth_key,
            "build_depth_label": self.build_depth_label,
            "selected_commander": self.selected_commander,
            "primary_strategy": self.primary_strategy,
            "secondary_strategy": self.secondary_strategy,
            "entries": [entry.to_dict() for entry in self.entries],
            "grouped_by_role": self.grouped_by_role,
            "preview_only": self.preview_only,
            "collection_first": self.collection_first,
            "possible_role_fits_only": self.possible_role_fits_only,
            "not_final_deck_inclusions": self.not_final_deck_inclusions,
            "generates_deck": self.generates_deck,
            "generates_shell": self.generates_shell,
            "generates_mana_base": self.generates_mana_base,
            "inserts_lands": self.inserts_lands,
            "selects_exact_cards": self.selects_exact_cards,
            "makes_final_deck_inclusion_decisions": self.makes_final_deck_inclusion_decisions,
            "generates_role_count_targets": self.generates_role_count_targets,
        }

    def to_markdown(self) -> str:
        return "\n".join(owned_cards_by_role_output_lines(self))


def create_owned_cards_by_role_entry(
    card: Any = None,
    *,
    card_name: str | None = None,
    owned_quantity: int | None = None,
    possible_roles: Iterable[str] | None = None,
    source: str = "collection",
    notes: Iterable[str] | None = None,
    source_files: Iterable[str] | None = None,
    **_: Any,
) -> OwnedCardsByRoleEntry:
    """Create a preview-only owned-card role entry."""
    raw_card = card if card is not None else {"name": card_name or "Unknown Card", "quantity": owned_quantity or 1}
    name = card_name or _name_from_card(raw_card)
    quantity = owned_quantity if owned_quantity is not None else _quantity_from_card(raw_card)
    roles = list(possible_roles) if possible_roles is not None else infer_possible_roles_for_owned_card(raw_card)
    # If source_files wasn't passed explicitly, look it up off the card dict.
    if source_files is None and isinstance(raw_card, dict):
        source_files = raw_card.get("source_files") or []
    return OwnedCardsByRoleEntry(
        card_name=name,
        owned_quantity=quantity,
        possible_roles=list(dict.fromkeys(roles)),
        source=source,
        notes=list(notes or ["Possible role fit only; not a final deck inclusion."]),
        source_files=list(source_files or []),
    )


def _group_entries_by_role(entries: Iterable[OwnedCardsByRoleEntry]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {role: [] for role in ROLE_BUCKETS}
    for entry in entries:
        for role in entry.possible_roles or ["Flex / Theme Slots"]:
            grouped.setdefault(role, []).append(entry.to_dict())
    return {role: cards for role, cards in grouped.items() if cards}


def create_owned_cards_by_role_output(
    owned_cards: Iterable[Any] | None = None,
    *,
    candidate_cards: Iterable[Any] | None = None,
    entries: Iterable[OwnedCardsByRoleEntry | dict[str, Any] | Any] | None = None,
    selected_commander: str | None = None,
    commander_name: str | None = None,
    primary_strategy: str = "Custom / Not Sure Yet",
    secondary_strategy: str = "Custom / Not Sure Yet",
    **_: Any,
) -> OwnedCardsByRoleOutput:
    """Create depth-C Owned Cards By Role output.

    This groups owned cards as possible role fits only. It does not make
    final deck inclusion decisions.
    """
    raw_entries: list[OwnedCardsByRoleEntry] = []
    if entries is not None:
        for entry in entries:
            if isinstance(entry, OwnedCardsByRoleEntry):
                raw_entries.append(entry)
            else:
                raw_entries.append(create_owned_cards_by_role_entry(entry))
    else:
        cards = list(candidate_cards if candidate_cards is not None else (owned_cards or []))
        if not cards:
            cards = [
                {"name": "Sol Ring", "quantity": 1, "oracle_text": "Add two colorless mana."},
                {"name": "Example Card Draw Spell", "quantity": 1, "oracle_text": "Draw two cards."},
            ]
        raw_entries = [create_owned_cards_by_role_entry(card) for card in cards]

    return OwnedCardsByRoleOutput(
        selected_commander=selected_commander or commander_name or "Selected Commander",
        primary_strategy=primary_strategy,
        secondary_strategy=secondary_strategy,
        entries=raw_entries,
    )


def owned_cards_by_role_output_lines(output: OwnedCardsByRoleOutput) -> list[str]:
    """Create human-readable lines for depth-C output."""
    lines = [
        "# Owned Cards By Role",
        "",
        f"Build depth: {output.build_depth_label}",
        f"Commander: {output.selected_commander}",
        f"Primary strategy: {output.primary_strategy}",
        f"Secondary strategy: {output.secondary_strategy}",
        "",
        "Possible role fits from your collection — a card may appear in more than one bucket.",
        "This is a role-bucketing summary, not a generated decklist. Use the Full 100-Card Draft button to generate an actual deck.",
        "",
    ]

    grouped = output.grouped_by_role or _group_entries_by_role(output.entries)
    # Sort role buckets by ROLE_BUCKETS order, then any extras at the end.
    seen_roles = [role for role in ROLE_BUCKETS if grouped.get(role)]
    extras = [role for role in grouped if role not in seen_roles and grouped.get(role)]
    for role in seen_roles + extras:
        cards = grouped.get(role, [])
        if not cards:
            continue
        lines.append(f"## {role}")
        lines.append(f"_{len(cards)} owned card(s)_")
        lines.append("")
        for card in cards:
            name = card.get("card_name", "Unknown Card")
            qty = card.get("owned_quantity", 1)
            sources = card.get("source_files") or []
            if sources:
                # Show one card per line with its source file(s); deduplicate.
                seen: list[str] = []
                for src in sources:
                    if src and src not in seen:
                        seen.append(src)
                source_text = "; ".join(seen)
                lines.append(f"- **{name}** ×{qty} — found in: `{source_text}`")
            else:
                lines.append(f"- **{name}** ×{qty}")
        lines.append("")

    if not grouped:
        lines.append("No owned card candidates were available for role preview.")

    return lines


def owned_cards_by_role_handoff_prompt(output: OwnedCardsByRoleOutput) -> str:
    """Create an AI handoff prompt for depth-C output."""
    return "\n".join(
        [
            "AI Handoff Prompt - Owned Cards By Role",
            "",
            "This file lists the user's owned cards grouped into possible role buckets.",
            "It is a role-bucketing summary, not a generated decklist — a card may fit several buckets.",
            "",
            f"Commander: {output.selected_commander}",
            f"Build depth: {output.build_depth_label}",
            f"Primary strategy: {output.primary_strategy}",
            f"Secondary strategy: {output.secondary_strategy}",
            "",
            "Useful follow-ups for the user:",
            "- Suggest which cards from each bucket are the strongest fits for the commander + strategy.",
            "- Flag buckets that look thin and recommend affordable additions.",
            "- Help the user prioritize when a card could plausibly fill multiple roles.",
            "",
            "Owned cards by possible role:",
            *owned_cards_by_role_output_lines(output),
        ]
    )


# v1.3.21.7 writer depth label compatibility alias.
def _v13217_owned_cards_by_role_depth_label(self):
    return getattr(self, "build_depth_label", "C - Owned Cards By Role")

if not hasattr(OwnedCardsByRoleOutput, "depth_label"):
    OwnedCardsByRoleOutput.depth_label = property(_v13217_owned_cards_by_role_depth_label)

_v13217_original_owned_cards_by_role_to_dict = OwnedCardsByRoleOutput.to_dict

def _v13217_owned_cards_by_role_to_dict(self):
    data = _v13217_original_owned_cards_by_role_to_dict(self)
    data["depth_label"] = getattr(self, "depth_label", getattr(self, "build_depth_label", "C - Owned Cards By Role"))
    data["build_depth_label"] = getattr(self, "build_depth_label", data["depth_label"])
    return data

OwnedCardsByRoleOutput.to_dict = _v13217_owned_cards_by_role_to_dict
