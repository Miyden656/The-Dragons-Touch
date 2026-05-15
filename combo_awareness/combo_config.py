"""Runtime configuration contract for Dragon's Touch combo awareness.

v0.8.6.2-dev is still an isolated planning/config-contract step. This module does
not connect combo awareness to main.py, the PySide6 UI, normal reports, or any
network/API workflow. It gives future integration code a single safe shape for
combo-related settings.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class ComboAwarenessConfig:
    """Future runtime settings for combo awareness.

    Defaults intentionally keep combo awareness informational. Missing combo
    cards are findings, not recommendations, unless combo optimization is
    explicitly enabled later.
    """

    enabled: bool = True
    show_current_infinite_combos: bool = True
    show_potential_infinite_combos: bool = True
    show_collection_completable_combos: bool = True

    # Display controls for future normal-report integration.
    report_complete_limit: int = 10
    report_collection_limit: int = 10
    report_potential_detail_limit: int = 0
    breakdown_potential_limit: int = 25
    show_all_potentials: bool = False

    # Safety and relevance filters.
    hide_spoiler_tagged_combos: bool = True
    strict_color_identity: bool = True
    respect_must_be_commander: bool = True
    commander_legal_only_index: bool = True

    # Behavior controls.
    combo_optimization_mode: bool = False
    recommend_missing_combo_cards: bool = False
    prioritize_collection_completable: bool = True
    group_report_section_by_missing_card: bool = True

    # Future-proof metadata / debug controls.
    include_debug_counts: bool = False
    write_full_breakdown_artifact: bool = False
    write_reconciliation_artifact: bool = False
    source: str = "default_v0.8.6.2-dev"
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary."""
        data = asdict(self)
        data["notes"] = list(self.notes)
        return data

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any] | None) -> "ComboAwarenessConfig":
        """Create a config from a mapping while ignoring unknown future keys."""
        if not values:
            return cls()
        allowed = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        filtered: dict[str, Any] = {key: value for key, value in values.items() if key in allowed}
        if "notes" in filtered and isinstance(filtered["notes"], list):
            filtered["notes"] = tuple(str(item) for item in filtered["notes"])
        return cls(**filtered)

    def validate(self) -> list[str]:
        """Return human-readable config warnings.

        This does not raise. Future UI/main.py hooks can show these warnings or
        write them into a debug artifact without stopping the run.
        """
        warnings: list[str] = []
        non_negative_fields = {
            "report_complete_limit": self.report_complete_limit,
            "report_collection_limit": self.report_collection_limit,
            "report_potential_detail_limit": self.report_potential_detail_limit,
            "breakdown_potential_limit": self.breakdown_potential_limit,
        }
        for name, value in non_negative_fields.items():
            if value < 0:
                warnings.append(f"{name} should not be negative; got {value}.")
        if self.recommend_missing_combo_cards and not self.combo_optimization_mode:
            warnings.append(
                "recommend_missing_combo_cards is true while combo_optimization_mode is false; "
                "future integration should keep recommendations opt-in."
            )
        if self.show_all_potentials and self.report_potential_detail_limit == 0:
            warnings.append(
                "show_all_potentials is true, but report_potential_detail_limit is 0; "
                "normal reports should remain concise unless explicitly in audit mode."
            )
        return warnings

    def summary_lines(self) -> list[str]:
        """Return a concise text summary for logs/debug output."""
        return [
            f"Combo awareness enabled: {self.enabled}",
            f"Informational by default: {not self.recommend_missing_combo_cards}",
            f"Combo optimization mode: {self.combo_optimization_mode}",
            f"Show current infinite combos: {self.show_current_infinite_combos}",
            f"Show potential infinite combos: {self.show_potential_infinite_combos}",
            f"Show collection-completable combos: {self.show_collection_completable_combos}",
            f"Hide spoiler-tagged combos: {self.hide_spoiler_tagged_combos}",
            f"Strict color identity: {self.strict_color_identity}",
            f"Respect mustBeCommander: {self.respect_must_be_commander}",
            f"Group concise section by missing card: {self.group_report_section_by_missing_card}",
        ]


DEFAULT_COMBO_AWARENESS_CONFIG = ComboAwarenessConfig()


def default_combo_awareness_config() -> ComboAwarenessConfig:
    """Return the default v0.8.6.2-dev combo awareness config."""
    return DEFAULT_COMBO_AWARENESS_CONFIG
