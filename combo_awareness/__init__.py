"""Combo awareness support for The Dragon's Touch."""

from .combo_config import (
    ComboAwarenessConfig,
    DEFAULT_COMBO_AWARENESS_CONFIG,
    default_combo_awareness_config,
)
from .combo_matcher import (
    DeckData,
    CollectionIndex,
    MatchResult,
    MatchSummary,
    parse_decklist,
    load_combo_index,
    load_collection_index,
    load_scryfall_name_identity_map,
    infer_commander_identity,
    match_deck_to_combo_index,
    build_combo_report_section_markdown,
    build_combo_breakdown_markdown,
)

__all__ = [
    "ComboAwarenessConfig",
    "DEFAULT_COMBO_AWARENESS_CONFIG",
    "default_combo_awareness_config",
    "DeckData",
    "CollectionIndex",
    "MatchResult",
    "MatchSummary",
    "parse_decklist",
    "load_combo_index",
    "load_collection_index",
    "load_scryfall_name_identity_map",
    "infer_commander_identity",
    "match_deck_to_combo_index",
    "build_combo_report_section_markdown",
    "build_combo_breakdown_markdown",
]
from .main_hook import write_optional_combo_awareness_artifacts

__all__.append("write_optional_combo_awareness_artifacts")

# v1.5.13 Combo Awareness core service boundary exports
try:
    from .service_boundary import (
        ComboAwarenessRequest,
        ComboAwarenessService,
        ComboAwarenessStatus,
        service_health,
    )
except Exception:
    # Keep package import tolerant for existing combo-awareness paths.
    ComboAwarenessRequest = None
    ComboAwarenessService = None
    ComboAwarenessStatus = None
    service_health = None

