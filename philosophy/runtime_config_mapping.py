"""Runtime config mapping for The Dragon's Touch philosophy layer.

Version: v1.1.4

This module is the safe intake bridge between UI/runtime configuration-style
dictionaries and the validated philosophy data model.

Important boundary:
- This module does not change deck analysis behavior.
- This module does not apply cut pressure.
- This module does not generate reports.
- This module does not read or write settings files by itself.

It only converts a mapping into:
- PhilosophyProfile
- canonical philosophy registry metadata
- persona report context metadata
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from .philosophy_profile import (
    BALANCED_UNKNOWN,
    PhilosophyProfile,
    create_profile,
)
from .philosophy_registry import (
    get_lens_definition,
)
from .persona_registry import (
    get_persona_report_context,
)


LENS_KEYS: Tuple[str, ...] = (
    "selected_lens",
    "philosophy_lens",
    "philosophy",
    "selected_philosophy",
    "review_philosophy",
    "subtype",
    "philosophy_subtype",
    "selected_subtype",
    "guide_lens",
)

INTENSITY_KEYS: Tuple[str, ...] = (
    "intensity",
    "philosophy_intensity",
    "lens_intensity",
)

GUIDE_PRESENTATION_KEYS: Tuple[str, ...] = (
    "guide_presentation",
    "guide_style",
    "guide_preference",
    "persona_presentation",
    "persona_style",
    "named_guide_preference",
)

PILOT_NOTES_KEYS: Tuple[str, ...] = (
    "pilot_notes",
    "philosophy_notes",
    "playstyle_notes",
    "persona_notes",
    "notes",
)

PROTECTED_CARDS_KEYS: Tuple[str, ...] = (
    "protected_cards",
    "user_protected_cards",
    "pet_cards",
    "declared_pet_cards",
    "do_not_cut_cards",
)

DECLARED_CONSTRAINTS_KEYS: Tuple[str, ...] = (
    "declared_constraints",
    "constraints",
    "user_constraints",
    "deck_constraints",
    "self_imposed_constraints",
)

COMBO_TOLERANCE_KEYS: Tuple[str, ...] = (
    "combo_tolerance",
    "combo_policy",
    "combo_preference",
)

BUDGET_NOTE_KEYS: Tuple[str, ...] = (
    "budget_note",
    "budget",
    "budget_limit",
    "budget_preference",
)

TABLE_POWER_NOTE_KEYS: Tuple[str, ...] = (
    "table_power_note",
    "table_power",
    "power_level",
    "intended_power_level",
    "bracket",
    "intended_bracket",
)


@dataclass(frozen=True)
class RuntimePhilosophyContext:
    """Combined philosophy intake context for later integration points."""

    profile: PhilosophyProfile
    lens_definition: Dict[str, str]
    persona_context: Dict[str, Optional[str]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile": self.profile.to_dict(),
            "lens_definition": dict(self.lens_definition),
            "persona_context": dict(self.persona_context),
        }


def _lookup_first(config: Mapping[str, Any], keys: Iterable[str], default: Any = None) -> Any:
    for key in keys:
        if key in config and config[key] not in (None, ""):
            return config[key]
    return default


def _clean_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _clean_optional_text(value: Any) -> Optional[str]:
    text = _clean_text(value)
    return text or None


def _split_string_list(value: str) -> List[str]:
    text = value.replace(";", "\n").replace(",", "\n")
    return [part.strip() for part in text.splitlines() if part.strip()]


def _coerce_string_list(value: Any) -> List[str]:
    if value is None:
        return []

    if isinstance(value, str):
        return _split_string_list(value)

    if isinstance(value, Mapping):
        # Allows simple checkbox-style maps such as {"Sol Ring": True}.
        result: List[str] = []
        for key, enabled in value.items():
            if enabled:
                text = str(key).strip()
                if text:
                    result.append(text)
        return result

    try:
        iterator = iter(value)
    except TypeError:
        text = str(value).strip()
        return [text] if text else []

    result: List[str] = []
    for item in iterator:
        text = str(item).strip()
        if text:
            result.append(text)
    return result


def _resolve_guide_presentation(config: Mapping[str, Any]) -> str:
    raw = _lookup_first(config, GUIDE_PRESENTATION_KEYS, None)

    # UI/runtime configs may send a boolean instead of a guide-style enum.
    if "use_named_guide" in config:
        if config["use_named_guide"] is False:
            return "no_named_guide"
        if config["use_named_guide"] is True and raw in (None, ""):
            return "either"

    if "named_guide_enabled" in config:
        if config["named_guide_enabled"] is False:
            return "no_named_guide"
        if config["named_guide_enabled"] is True and raw in (None, ""):
            return "either"

    return _clean_text(raw, "no_named_guide") or "no_named_guide"


def normalize_runtime_config(config: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    """Normalize UI/runtime config aliases to PhilosophyProfile constructor keys.

    Unknown keys are intentionally ignored. This keeps the mapper safe for future
    UI/runtime configs that carry additional unrelated settings.
    """
    source: Mapping[str, Any] = config or {}

    normalized = {
        "selected_lens": _clean_text(_lookup_first(source, LENS_KEYS, BALANCED_UNKNOWN), BALANCED_UNKNOWN) or BALANCED_UNKNOWN,
        "intensity": _clean_text(_lookup_first(source, INTENSITY_KEYS, "normal"), "normal") or "normal",
        "guide_presentation": _resolve_guide_presentation(source),
        "pilot_notes": _clean_text(_lookup_first(source, PILOT_NOTES_KEYS, "")),
        "protected_cards": _coerce_string_list(_lookup_first(source, PROTECTED_CARDS_KEYS, [])),
        "declared_constraints": _coerce_string_list(_lookup_first(source, DECLARED_CONSTRAINTS_KEYS, [])),
        "combo_tolerance": _clean_optional_text(_lookup_first(source, COMBO_TOLERANCE_KEYS, None)),
        "budget_note": _clean_optional_text(_lookup_first(source, BUDGET_NOTE_KEYS, None)),
        "table_power_note": _clean_optional_text(_lookup_first(source, TABLE_POWER_NOTE_KEYS, None)),
    }

    # A specific subtype should win over a broad philosophy if both are present.
    explicit_subtype = _lookup_first(source, ("philosophy_subtype", "selected_subtype", "subtype"), None)
    if explicit_subtype not in (None, ""):
        normalized["selected_lens"] = _clean_text(explicit_subtype, BALANCED_UNKNOWN) or BALANCED_UNKNOWN

    return normalized


def profile_from_runtime_config(config: Optional[Mapping[str, Any]]) -> PhilosophyProfile:
    """Build a validated PhilosophyProfile from runtime/UI config data."""
    normalized = normalize_runtime_config(config)
    return create_profile(
        selected_lens=normalized["selected_lens"],
        intensity=normalized["intensity"],
        guide_presentation=normalized["guide_presentation"],
        pilot_notes=normalized["pilot_notes"],
        protected_cards=normalized["protected_cards"],
        declared_constraints=normalized["declared_constraints"],
        combo_tolerance=normalized["combo_tolerance"],
        budget_note=normalized["budget_note"],
        table_power_note=normalized["table_power_note"],
    )


def context_from_profile(profile: PhilosophyProfile) -> RuntimePhilosophyContext:
    """Build the combined runtime context from an existing profile."""
    lens_definition = get_lens_definition(profile.selected_lens).to_dict()
    persona_context = get_persona_report_context(
        profile.selected_lens,
        profile.guide_presentation,
    )
    return RuntimePhilosophyContext(
        profile=profile,
        lens_definition=lens_definition,
        persona_context=persona_context,
    )


def context_from_runtime_config(config: Optional[Mapping[str, Any]]) -> RuntimePhilosophyContext:
    """Build the combined runtime context from runtime/UI config data."""
    return context_from_profile(profile_from_runtime_config(config))


def runtime_config_to_report_context(config: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    """Return a plain dictionary for later report/prompt integration."""
    return context_from_runtime_config(config).to_dict()


def merge_runtime_config_defaults(
    config: Optional[Mapping[str, Any]],
    defaults: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Merge defaults and config before normalization.

    User/config values win over defaults. This is useful for future UI or batch
    mode integration where global philosophy defaults may be supplied.
    """
    merged: Dict[str, Any] = {}
    if defaults:
        merged.update(defaults)
    if config:
        merged.update(config)
    return merged


def profile_from_runtime_config_with_defaults(
    config: Optional[Mapping[str, Any]],
    defaults: Optional[Mapping[str, Any]] = None,
) -> PhilosophyProfile:
    """Build a profile after applying global/default runtime config values."""
    return profile_from_runtime_config(merge_runtime_config_defaults(config, defaults))


def context_from_runtime_config_with_defaults(
    config: Optional[Mapping[str, Any]],
    defaults: Optional[Mapping[str, Any]] = None,
) -> RuntimePhilosophyContext:
    """Build combined runtime context after applying global/default values."""
    return context_from_profile(
        profile_from_runtime_config_with_defaults(config, defaults)
    )
