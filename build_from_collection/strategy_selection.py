"""Strategy Selection / Override Preview for Build From Collection v1.3.14.

This module lets Commander’s Call infer likely commander strategies while also
allowing the user to override primary and secondary strategy before later build
execution. It is preview-only: no exact card selection, no role-count target
generation, no mana-base generation, no land insertion, no shell generation, and
no deck generation.

Marker: Strategy Selection / Override Preview.
Marker: inferred strategy suggestions.
Marker: user strategy override.
Marker: primary_strategy.
Marker: secondary_strategy.
Marker: No exact card selection.
Marker: No role-count target generation.
Marker: No mana-base generation.
Marker: No land insertion.
Marker: No shell generation.
Marker: No deck generation.
Marker: Basic lands are assumed available.
Marker: Nonbasic lands remain collection-first unless outside-collection upgrades are allowed by the user.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .strategy_role_mapping import STRATEGY_TO_ROLE_BUCKET_MAPPING, create_strategy_role_bucket_mapping_preview, normalize_strategy_key

STRATEGY_SELECTION_LABELS: tuple[str, ...] = (
    "Use inferred strategy",
    "Aristocrats",
    "Tokens",
    "Lifegain",
    "Voltron",
    "Spellslinger",
    "Graveyard Recursion",
    "Reanimator",
    "Go-Wide Combat",
    "+1/+1 Counters",
    "Artifacts",
    "Enchantress",
    "Landfall",
    "Sacrifice",
    "Blink / Flicker",
    "Ramp Into Big Threats",
    "Control",
    "Combo-Adjacent Value",
    "Tribal / Typal",
    "Custom / Not Sure Yet",
)

STRATEGY_LABEL_BY_KEY: dict[str, str] = {
    "aristocrats": "Aristocrats",
    "tokens": "Tokens",
    "lifegain": "Lifegain",
    "voltron": "Voltron",
    "spellslinger": "Spellslinger",
    "graveyard_recursion": "Graveyard Recursion",
    "reanimator": "Reanimator",
    "go_wide_combat": "Go-Wide Combat",
    "plus_one_plus_one_counters": "+1/+1 Counters",
    "artifacts": "Artifacts",
    "enchantress": "Enchantress",
    "landfall": "Landfall",
    "sacrifice": "Sacrifice",
    "blink_flicker": "Blink / Flicker",
    "ramp_into_big_threats": "Ramp Into Big Threats",
    "control": "Control",
    "combo_adjacent_value": "Combo-Adjacent Value",
    "tribal": "Tribal / Typal",
    "custom_or_unknown": "Custom / Not Sure Yet",
}


def strategy_selection_labels() -> tuple[str, ...]:
    """Return user-facing strategy choices for Commander’s Call."""
    return STRATEGY_SELECTION_LABELS


def normalize_strategy_selection_label(label: str | None) -> str:
    """Normalize a UI strategy label into a strategy key."""
    if not label:
        return ""
    cleaned = str(label).strip()
    if not cleaned or cleaned == "Use inferred strategy":
        return ""
    if cleaned == "Custom / Not Sure Yet":
        return "custom_or_unknown"
    return normalize_strategy_key(cleaned)


def strategy_label_for_key(strategy_key: str | None) -> str:
    """Return a friendly label for a normalized strategy key."""
    key = normalize_strategy_key(strategy_key)
    return STRATEGY_LABEL_BY_KEY.get(key, str(strategy_key or "Custom / Not Sure Yet"))


def _candidate_text(selected_commander: Any) -> str:
    if selected_commander is None:
        return ""
    if hasattr(selected_commander, "to_dict"):
        selected_commander = selected_commander.to_dict()
    if isinstance(selected_commander, dict):
        parts = [
            selected_commander.get("commander_name"),
            selected_commander.get("card_name"),
            selected_commander.get("type_line"),
            selected_commander.get("oracle_text"),
            selected_commander.get("rules_text"),
            selected_commander.get("commander_eligibility_reason"),
            selected_commander.get("special_commander_rule"),
        ]
        return " ".join(str(part or "") for part in parts).lower()
    return str(selected_commander).lower()


def infer_strategy_candidates_from_commander(selected_commander: Any) -> tuple[str, ...]:
    """Infer likely strategy keys from commander name/type/text.

    This is intentionally lightweight for v1.3.14. v1.4 Strategy Deep Dive can
    replace or enrich this later. User override remains allowed.
    """
    text = _candidate_text(selected_commander)
    inferred: list[str] = []

    def add(key: str) -> None:
        if key not in inferred:
            inferred.append(key)

    if any(word in text for word in ("token", "create", "creature token")):
        add("tokens")
    if any(word in text for word in ("sacrifice", "dies", "whenever another creature dies")):
        add("aristocrats")
        add("sacrifice")
    if any(word in text for word in ("gain life", "lifegain", "life total")):
        add("lifegain")
    if any(word in text for word in ("equipment", "aura", "attach", "enchanted creature", "equipped creature")):
        add("voltron")
    if any(word in text for word in ("instant", "sorcery", "cast", "copy target spell")):
        add("spellslinger")
    if any(word in text for word in ("graveyard", "return target", "from your graveyard")):
        add("graveyard_recursion")
    if any(word in text for word in ("reanimate", "return a creature card", "put target creature card")):
        add("reanimator")
    if any(word in text for word in ("+1/+1 counter", "counter on", "proliferate")):
        add("plus_one_plus_one_counters")
    if "artifact" in text:
        add("artifacts")
    if any(word in text for word in ("enchantment", "enchantress", "aura")):
        add("enchantress")
    if any(word in text for word in ("landfall", "land enters", "lands you control", "play an additional land")):
        add("landfall")
    if any(word in text for word in ("exile", "return it to the battlefield", "blink", "flicker")):
        add("blink_flicker")
    if any(word in text for word in ("draw", "counter target", "destroy target", "exile target")):
        add("control")
    if "creatures you control" in text or "creature type" in text:
        add("tribal")
        add("go_wide_combat")
    if any(word in text for word in ("mana", "add ", "power 5", "power 4 or greater")):
        add("ramp_into_big_threats")

    if not inferred:
        add("combo_adjacent_value")
    return tuple(inferred[:3])


@dataclass(slots=True)
class StrategySelectionOverridePreview:
    """Preview-only strategy inference plus user override selection."""

    selected_commander: Any = None
    inferred_strategy_keys: tuple[str, ...] = field(default_factory=tuple)
    primary_strategy: str = ""
    secondary_strategy: str = ""
    primary_strategy_source: str = "inferred"
    secondary_strategy_source: str = "inferred"
    user_override_allowed: bool = True
    strategy_mapping_preview: Any = None
    preview_name: str = "Strategy Selection / Override Preview"
    preview_version: str = "v1.3.14"
    preview_only: bool = True
    exact_card_selection: bool = False
    role_count_target_generated: bool = False
    mana_base_generated: bool = False
    land_inserted: bool = False
    shell_generated: bool = False
    deck_generated: bool = False
    deferred_behavior: tuple[str, ...] = (
        "No exact card selection",
        "No role-count target generation",
        "No mana-base generation",
        "No land insertion",
        "No shell generation",
        "No deck generation",
        "No normal deck review changes",
        "Strategy Deep Dive remains future v1.4 expansion",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "preview_name": self.preview_name,
            "preview_version": self.preview_version,
            "preview_only": self.preview_only,
            "selected_commander": self.selected_commander.to_dict() if hasattr(self.selected_commander, "to_dict") else self.selected_commander,
            "inferred_strategy_keys": list(self.inferred_strategy_keys),
            "inferred_strategy_labels": [strategy_label_for_key(key) for key in self.inferred_strategy_keys],
            "primary_strategy": self.primary_strategy,
            "primary_strategy_key": normalize_strategy_key(self.primary_strategy),
            "primary_strategy_source": self.primary_strategy_source,
            "secondary_strategy": self.secondary_strategy,
            "secondary_strategy_key": normalize_strategy_key(self.secondary_strategy),
            "secondary_strategy_source": self.secondary_strategy_source,
            "user_override_allowed": self.user_override_allowed,
            "strategy_mapping_preview": self.strategy_mapping_preview.to_dict() if self.strategy_mapping_preview else {},
            "exact_card_selection": self.exact_card_selection,
            "role_count_target_generated": self.role_count_target_generated,
            "mana_base_generated": self.mana_base_generated,
            "land_inserted": self.land_inserted,
            "shell_generated": self.shell_generated,
            "deck_generated": self.deck_generated,
            "deferred_behavior": list(self.deferred_behavior),
            "v1_3_14_boundary": (
                "Strategy Selection / Override Preview infers likely strategies and lets the user override primary and secondary strategy. "
                "It does not select exact cards, create role-count targets, generate a mana base, insert lands, generate a shell, generate a deck, score cards, recommend cuts, or change normal deck review behavior. "
                "Basic lands are assumed available; nonbasic lands remain collection-first unless outside-collection upgrades are allowed by the user."
            ),
        }


def create_strategy_selection_override_preview(
    selected_commander: Any = None,
    primary_strategy: str = "",
    secondary_strategy: str = "",
    user_override_allowed: bool = True,
) -> StrategySelectionOverridePreview:
    """Create a preview-only strategy selection payload with inferred defaults and user override."""
    inferred_keys = infer_strategy_candidates_from_commander(selected_commander)
    selected_primary_key = normalize_strategy_selection_label(primary_strategy) or (inferred_keys[0] if inferred_keys else "combo_adjacent_value")
    selected_secondary_key = normalize_strategy_selection_label(secondary_strategy)
    if not selected_secondary_key and len(inferred_keys) > 1:
        selected_secondary_key = inferred_keys[1]

    selected_primary = strategy_label_for_key(selected_primary_key)
    selected_secondary = strategy_label_for_key(selected_secondary_key) if selected_secondary_key else ""
    mapping_preview = create_strategy_role_bucket_mapping_preview(
        primary_strategy=selected_primary,
        secondary_strategy=selected_secondary,
    )
    return StrategySelectionOverridePreview(
        selected_commander=selected_commander,
        inferred_strategy_keys=inferred_keys,
        primary_strategy=selected_primary,
        secondary_strategy=selected_secondary,
        primary_strategy_source="user override" if normalize_strategy_selection_label(primary_strategy) else "inferred",
        secondary_strategy_source="user override" if normalize_strategy_selection_label(secondary_strategy) else "inferred" if selected_secondary else "not selected",
        user_override_allowed=user_override_allowed,
        strategy_mapping_preview=mapping_preview,
    )


def strategy_selection_preview_lines(preview: StrategySelectionOverridePreview) -> tuple[str, ...]:
    """Return concise UI/report lines for strategy inference and override preview."""
    data = preview.to_dict()
    return (
        "Strategy Selection / Override Preview created.",
        "This is strategy setup context only; it does not build the deck.",
        "Inferred strategy suggestions: " + (", ".join(data.get("inferred_strategy_labels", [])) or "None"),
        f"Primary strategy: {data.get('primary_strategy') or 'Not selected yet'} ({data.get('primary_strategy_source')})",
        f"Secondary strategy: {data.get('secondary_strategy') or 'Not selected yet'} ({data.get('secondary_strategy_source')})",
        "User override allowed: True",
        "No exact card selection.",
        "No role-count target generation.",
        "No mana-base generation.",
        "No land insertion.",
        "No shell generation.",
        "No deck generation.",
    )
