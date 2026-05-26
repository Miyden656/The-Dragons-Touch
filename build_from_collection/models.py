"""Selected-commander handoff models for Build From Collection v1.3.

These dataclasses define the safe handoff shape from The Commander's Call
into future build-from-collection work. v1.3.0 is a foundation only: it
preserves v1.2 Commander Discovery behavior and does not build a deck.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class StrategySelection:
    """Player-facing strategy choices for a future commander shell."""

    primary_strategy: str = ""
    secondary_strategy: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PhilosophySelection:
    """Main philosophy and optional persona/sub-philosophy handoff."""

    main_philosophy: str = ""
    sub_philosophy: str = ""
    persona: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DiscoveryModeSelection:
    """Optional discovery/build-up mode context for future shell planning."""

    discovery_mode: str = ""
    build_up_mode: str = ""
    prompt_mode: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class BracketPreference:
    """Commander bracket preference handoff without changing bracket logic."""

    intended_bracket: str = ""
    bracket_notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CommanderBuildScope:
    """Explicit v1.3.0 boundaries for future build-from-collection work."""

    version: str = "v1.3.0"
    scope_name: str = "Commander Selection Handoff / Build Scope Baseline"
    answers_now: str = "What commander did the user select to start building around?"
    answers_later: str = "What can I build from what I own?"
    full_deck_generation_allowed: bool = False
    one_hundred_card_shell_allowed: bool = False
    normal_deck_review_changes_allowed: bool = False
    archidekt_integration_allowed: bool = False
    account_login_allowed: bool = False
    notes: list[str] = field(default_factory=lambda: [
        "Use the selected commander as future build context.",
        "Prefer collection-first shell planning before full deck generation.",
        "Keep v1.2 Commander Discovery behavior stable unless a bug is found.",
    ])

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CommanderSelectionHandoff:
    """Safe data shape passed from Commander Discovery into v1.3 planning."""

    commander_name: str
    color_identity_key: str = ""
    color_identity_text: str = "Colorless"
    color_identity_group: str = "Colorless"
    color_count: int = 0
    owned_quantity: int = 0
    type_line: str = ""
    oracle_text_preview: str = ""
    eligibility_status: str = ""
    eligibility_rule: str = ""
    is_mvp_eligible: bool = False
    is_special_rule_candidate: bool = False
    source_files: list[str] = field(default_factory=list)
    strategy: StrategySelection = field(default_factory=StrategySelection)
    philosophy: PhilosophySelection = field(default_factory=PhilosophySelection)
    discovery: DiscoveryModeSelection = field(default_factory=DiscoveryModeSelection)
    bracket: BracketPreference = field(default_factory=BracketPreference)
    scope: CommanderBuildScope = field(default_factory=CommanderBuildScope)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["v1_3_0_boundary"] = (
            "Selected commander handoff only. No 100-card shell generation, "
            "no normal deck review changes, and no scoring/cut/replacement changes."
        )
        return data


def _candidate_get(candidate: Any, key: str, default: Any = "") -> Any:
    if isinstance(candidate, dict):
        return candidate.get(key, default)
    return getattr(candidate, key, default)


def build_commander_selection_handoff(
    candidate: Any,
    *,
    strategy: StrategySelection | None = None,
    philosophy: PhilosophySelection | None = None,
    discovery: DiscoveryModeSelection | None = None,
    bracket: BracketPreference | None = None,
) -> CommanderSelectionHandoff:
    """Create a v1.3 selected-commander handoff from a candidate dict/model.

    The input can be a CommanderDiscovery candidate summary dict or an object
    with similarly named attributes. This helper intentionally returns data
    only; it does not write files, run analysis, or build a deck shell.
    """

    commander_name = str(_candidate_get(candidate, "card_name", "") or "").strip()
    if not commander_name:
        raise ValueError("CommanderSelectionHandoff requires a selected commander name.")

    return CommanderSelectionHandoff(
        commander_name=commander_name,
        color_identity_key=str(_candidate_get(candidate, "color_identity_key", "") or ""),
        color_identity_text=str(_candidate_get(candidate, "color_identity_text", "Colorless") or "Colorless"),
        color_identity_group=str(_candidate_get(candidate, "color_identity_group", "Colorless") or "Colorless"),
        color_count=int(_candidate_get(candidate, "color_count", 0) or 0),
        owned_quantity=int(_candidate_get(candidate, "owned_quantity", 0) or 0),
        type_line=str(_candidate_get(candidate, "type_line", "") or ""),
        oracle_text_preview=str(_candidate_get(candidate, "oracle_text_preview", "") or ""),
        eligibility_status=str(_candidate_get(candidate, "eligibility_status", "") or ""),
        eligibility_rule=str(_candidate_get(candidate, "eligibility_rule", "") or ""),
        is_mvp_eligible=bool(_candidate_get(candidate, "is_mvp_eligible", False)),
        is_special_rule_candidate=bool(_candidate_get(candidate, "is_special_rule_candidate", False)),
        source_files=list(_candidate_get(candidate, "source_files", []) or []),
        strategy=strategy or StrategySelection(),
        philosophy=philosophy or PhilosophySelection(),
        discovery=discovery or DiscoveryModeSelection(),
        bracket=bracket or BracketPreference(),
    )
