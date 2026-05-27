"""Strategy Selector Catalog (Task #39 v1.5.38).

Loads the 249-profile strategy index produced by Strategy Knowledge and exposes
it as flat selector options for the Build Setup Panel.

The Build Setup Panel previously offered 22 macro archetypes from
`analysis.strategy_scoring.ARCHETYPE_DEFINITIONS`. This module surfaces the
full 249-profile catalog so users can pick the specific strategy that fits
their commander (e.g., "Dragon Typal" under Typal/Tribal, or "Goad Combat"
under Strategic/Board/Politics) instead of only the broad macro bucket.

Boundaries:
- Read-only access to the existing index file.
- Does NOT mutate the index.
- Does NOT alter the legacy scoring path (analysis/strategy_scoring.py and the
  main deck report continue to use ARCHETYPE_DEFINITIONS unchanged).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


# Friendly labels for each layer ID — these appear as the bracketed prefix in
# the Build Setup Panel dropdown so users can tell at a glance which category
# a strategy falls into.
LAYER_DISPLAY_PREFIX: dict[str, str] = {
    "01_macro_archetypes": "Macro",
    "02_mechanical_themes": "Mechanical",
    "03_strategic_board_politics": "Strategic",
    "04_typal_tribal_themes": "Typal",
    "05_1_niche_theme_rules": "Niche",
    "05_2_fringe_theme_rules": "Fringe",
    "05_3_emergent_theme_rules": "Emergent",
}

# Display order for grouping in the dropdown.
LAYER_ORDER: tuple[str, ...] = (
    "01_macro_archetypes",
    "02_mechanical_themes",
    "03_strategic_board_politics",
    "04_typal_tribal_themes",
    "05_1_niche_theme_rules",
    "05_2_fringe_theme_rules",
    "05_3_emergent_theme_rules",
)


def _index_path() -> Path:
    return (
        Path(__file__).resolve().parent
        / "index"
        / "strategy_profile_index.latest.json"
    )


@lru_cache(maxsize=1)
def _load_index() -> dict[str, Any]:
    """Load and cache the strategy profile index JSON."""
    try:
        return json.loads(_index_path().read_text(encoding="utf-8"))
    except Exception:
        return {"strategy_profiles": []}


def all_strategy_profiles() -> list[dict[str, Any]]:
    """Return all 249 profiles in display order (macro → mechanical → ... → emergent)."""
    idx = _load_index()
    profiles = list(idx.get("strategy_profiles") or [])
    order_map = {layer: i for i, layer in enumerate(LAYER_ORDER)}
    profiles.sort(key=lambda p: (
        order_map.get(p.get("layer", ""), 99),
        str(p.get("display_name") or "").lower(),
    ))
    return profiles


def selector_options_for_primary() -> list[str]:
    """Build the dropdown items for the Primary Strategy selector.

    Format: "[LayerPrefix] Display Name" so the user sees the category inline.
    Leads with 'Not selected yet' so the dropdown has a neutral default.
    """
    options = ["Not selected yet"]
    for profile in all_strategy_profiles():
        layer = profile.get("layer", "")
        prefix = LAYER_DISPLAY_PREFIX.get(layer, layer or "Other")
        name = profile.get("display_name") or profile.get("strategy_id") or "Unknown"
        options.append(f"[{prefix}] {name}")
    return options


def selector_options_for_secondary() -> list[str]:
    """Same as primary, but leads with 'None' so 'no secondary' is allowed."""
    options = ["None"]
    for profile in all_strategy_profiles():
        layer = profile.get("layer", "")
        prefix = LAYER_DISPLAY_PREFIX.get(layer, layer or "Other")
        name = profile.get("display_name") or profile.get("strategy_id") or "Unknown"
        options.append(f"[{prefix}] {name}")
    return options


def display_name_from_selector_value(value: str) -> str:
    """Strip the "[LayerPrefix] " prefix to get the bare strategy display name.

    Returns the input unchanged if it doesn't have a layer prefix (e.g. the
    legacy 22 names from ARCHETYPE_DEFINITIONS, or 'Not selected yet'/'None').
    """
    if not value:
        return ""
    text = str(value).strip()
    if text.startswith("[") and "]" in text:
        return text.split("]", 1)[1].strip()
    return text


def profile_for_display_name(display_name: str) -> dict[str, Any] | None:
    """Look up a profile by its display name (case-insensitive)."""
    if not display_name:
        return None
    target = display_name.strip().lower()
    for profile in all_strategy_profiles():
        if str(profile.get("display_name") or "").strip().lower() == target:
            return profile
    return None


def role_tags_for_display_name(display_name: str) -> set[str]:
    """Return the role tags for a strategy by display name.

    Tries the strategy knowledge 249-profile catalog first, then falls back
    to the legacy ARCHETYPE_DEFINITIONS so old saved choices still work.
    """
    bare = display_name_from_selector_value(display_name)
    if not bare or bare in ("Not selected yet", "None"):
        return set()
    profile = profile_for_display_name(bare)
    if profile is not None:
        return {str(t) for t in (profile.get("role_tags") or []) if t}
    # Legacy fallback: ARCHETYPE_DEFINITIONS uses anchors/payoffs/enablers.
    try:
        from analysis.strategy_scoring import ARCHETYPE_DEFINITIONS
    except Exception:
        return set()
    arch = ARCHETYPE_DEFINITIONS.get(bare, {}) or {}
    tags: set[str] = set()
    for key in ("anchors", "payoffs", "enablers"):
        for tag in (arch.get(key) or set()):
            tags.add(str(tag))
    return tags


def layer_label_for_display_name(display_name: str) -> str:
    """Return the friendly layer label for a strategy, or '' if unknown."""
    bare = display_name_from_selector_value(display_name)
    profile = profile_for_display_name(bare)
    if profile is None:
        return ""
    return LAYER_DISPLAY_PREFIX.get(profile.get("layer", ""), "")


def strategy_selector_catalog_health() -> dict[str, Any]:
    """Diagnostic health check — returns profile count + layer breakdown."""
    profiles = all_strategy_profiles()
    layer_counts: dict[str, int] = {}
    for profile in profiles:
        layer = profile.get("layer", "")
        layer_counts[layer] = layer_counts.get(layer, 0) + 1
    return {
        "total_profiles": len(profiles),
        "layer_counts": layer_counts,
        "index_exists": _index_path().exists(),
        "version": "v1.5.38",
    }
