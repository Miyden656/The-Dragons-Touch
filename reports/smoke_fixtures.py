"""Report output smoke fixtures.

v1.5.23.1 fixes the fixture strings so they use real newline characters,
not literal backslash-n sequences. These fixtures are passive and do not run
the full analysis pipeline, launch the UI, or download data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class SmokeCardRecord:
    name: str
    role: str = "unknown"
    source: str = "fixture"

    def as_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "role": self.role, "source": self.source}


@dataclass
class SmokeReportContext:
    deck_name: str = "v1.5.23 Smoke Fixture Deck"
    commander_name: str = "Smoke Fixture Commander"
    strategy_name: str = "Smoke Fixture Strategy"
    cards: List[SmokeCardRecord] = field(default_factory=list)
    replacement_needs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "deck_name": self.deck_name,
            "commander_name": self.commander_name,
            "strategy_name": self.strategy_name,
            "cards": [card.as_dict() for card in self.cards],
            "replacement_needs": list(self.replacement_needs),
            "metadata": dict(self.metadata),
        }


def make_smoke_context() -> SmokeReportContext:
    """Return a small generic context for future report smoke tests."""

    return SmokeReportContext(
        cards=[
            SmokeCardRecord("Arcane Signet", "ramp"),
            SmokeCardRecord("Beast Within", "interaction"),
            SmokeCardRecord("Heroic Intervention", "protection"),
        ],
        replacement_needs=[
            "board protection",
            "table-stabilizing interaction",
        ],
        metadata={
            "fixture_version": "v1.5.23.1",
            "purpose": "report smoke baseline",
        },
    )


def make_postprocessor_smoke_report() -> str:
    """Return report text that exercises the extracted final postprocessor."""

    return """## Replacement / Addition Needs

- board protection
- table-stabilizing interaction

## Full-Card-Pool Fallback Preview

### Fallback Categories to Explore Later
- Better role coverage — triggered by: ReplacementNeedSummary(foo)

### Exact Full-Pool Candidate Preview
#### Better role coverage
- Flexible removal (color identity not verified) — budget not checked; bracket not checked; table fit not checked

### Exact Preview Safety Boundaries
- Automatic swaps: No.
"""


def make_dragon_gate_smoke_report() -> str:
    """Return text with Dragon-gate/strong-owned wording for future comparisons."""

    return """## Strong Existing Cards / Owned Pool

- Dragon Tempest — strong owned Dragon payoff.
- Scourge of Valkas — strong owned Dragon payoff.

## Candidate Review

Dragon-gate language should remain stable unless an explicit Dragon-gate patch changes it.
"""
