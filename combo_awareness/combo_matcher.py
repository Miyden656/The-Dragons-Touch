#!/usr/bin/env python3
"""v0.8.7-dev — compatibility wrapper for combo awareness modules.

The old combo_awareness/combo_matcher.py file was split into focused modules in
v0.8.7-dev. This wrapper preserves the existing import path used by
tools/test_combo_matcher.py and future guarded integration work.

Scope guard:
- No API calls.
- No main.py integration.
- No UI integration.
- No normal report integration.
- No matcher/parser/report behavior changes.
"""

from __future__ import annotations

from .normalization import (
    MANA_SYMBOL_ORDER,
    normalize_card_name,
    clean_card_name,
    normalize_header_text,
    canonical_identity,
    identity_to_string,
    is_subset_identity,
)
from .models import (
    DeckData,
    CollectionCard,
    CollectionIndex,
    MatchResult,
    MatchSummary,
)
from .deck_parser import (
    COMMANDER_HEADERS,
    MAIN_DECK_HEADERS,
    MAYBEBOARD_HEADERS,
    TOKEN_HEADERS,
    DECK_MANAGEMENT_EXCLUDE_HEADERS,
    CUSTOM_CATEGORY_HEADERS,
    NON_CARD_HEADERS,
    is_known_non_card_header,
    extract_card_name_from_line,
    parse_decklist,
)
from .collection_loader import (
    load_collection_index,
    read_csv_collection_file,
    read_text_collection_file,
)
from .index_loader import (
    load_combo_index,
    load_scryfall_name_identity_map,
    infer_commander_identity,
)
from .matcher import (
    combo_must_be_commander_satisfied,
    combo_card_names,
    match_deck_to_combo_index,
)
from .reporting import (
    format_combo_result,
    build_markdown_summary,
    prioritize_potential_results,
    build_combo_report_section_markdown,
    build_combo_breakdown_markdown,
)

__all__ = [
    "MANA_SYMBOL_ORDER",
    "DeckData",
    "CollectionCard",
    "CollectionIndex",
    "MatchResult",
    "MatchSummary",
    "normalize_card_name",
    "clean_card_name",
    "normalize_header_text",
    "canonical_identity",
    "identity_to_string",
    "is_subset_identity",
    "COMMANDER_HEADERS",
    "MAIN_DECK_HEADERS",
    "MAYBEBOARD_HEADERS",
    "TOKEN_HEADERS",
    "DECK_MANAGEMENT_EXCLUDE_HEADERS",
    "CUSTOM_CATEGORY_HEADERS",
    "NON_CARD_HEADERS",
    "is_known_non_card_header",
    "extract_card_name_from_line",
    "parse_decklist",
    "load_collection_index",
    "read_csv_collection_file",
    "read_text_collection_file",
    "load_combo_index",
    "load_scryfall_name_identity_map",
    "infer_commander_identity",
    "combo_must_be_commander_satisfied",
    "combo_card_names",
    "match_deck_to_combo_index",
    "format_combo_result",
    "build_markdown_summary",
    "prioritize_potential_results",
    "build_combo_report_section_markdown",
    "build_combo_breakdown_markdown",
]
