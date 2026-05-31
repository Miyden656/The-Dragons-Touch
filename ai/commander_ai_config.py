"""Commander AI configuration — the single source of truth for AI settings.

This module is intentionally pure:
    - no file I/O
    - no network
    - no imports from `ui/` or the deck engine
    - stdlib only

It defines the typed `CommanderAIConfig`, the persisted default values
(`AI_SETTINGS_DEFAULTS`, consumed by ui/services/user_settings.py so the
defaults live in exactly one place), and `from_settings()` which turns a loaded
settings dict into a validated, normalized config object.

Persisted setting keys (stored in the existing ui/user_settings.json store):
    commander_ai_enabled            bool   default False
    commander_ai_base_url           str    default "http://localhost:11434"
    commander_ai_model              str    default "qwen2.5:7b"
    commander_ai_temperature        float  default 0.4   (clamped 0.0-1.5)
    commander_ai_stream             bool   default False
    commander_ai_timeout_seconds    int    default 120   (clamped 5-600)
    commander_ai_strict_fact_check  bool   default True
    commander_ai_guide_style        str    default "adventurer"

NOTE ON GUIDE STYLE NAMING: the four guide-style tokens (adventurer / archivist
/ strategist / minimal) are a *response tone+format* axis. They are deliberately
NOT the same field as `guide_presentation` in user_settings.py, which controls
the masculine/feminine/random/none guide NAME. The labels "Adventurer Guide"
etc. were briefly used for guide_presentation in v0.10.5.1 and then retired; any
future Settings UI must label this field "Response style" (not "Guide") to avoid
re-confusing the two concepts.
"""

from __future__ import annotations

from dataclasses import dataclass


# --- Allowed values -------------------------------------------------------

GUIDE_STYLES = ("adventurer", "archivist", "strategist", "minimal")
DEFAULT_GUIDE_STYLE = "adventurer"

DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:7b"  # benchmarked stronger than llama3.1 (legality + hallucination) 2026-05-31
DEFAULT_TEMPERATURE = 0.4
DEFAULT_TIMEOUT_SECONDS = 120

# Clamp ranges keep a malformed settings file from producing nonsense.
TEMPERATURE_MIN = 0.0
TEMPERATURE_MAX = 1.5
TIMEOUT_MIN_SECONDS = 5
TIMEOUT_MAX_SECONDS = 600


# --- Persisted defaults (single source of truth) --------------------------
# ui/services/user_settings.py imports this so default values are defined once.
AI_SETTINGS_DEFAULTS: dict[str, object] = {
    "commander_ai_enabled": False,
    "commander_ai_base_url": DEFAULT_BASE_URL,
    "commander_ai_model": DEFAULT_MODEL,
    "commander_ai_temperature": DEFAULT_TEMPERATURE,
    "commander_ai_stream": False,
    "commander_ai_timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
    "commander_ai_strict_fact_check": True,
    "commander_ai_guide_style": DEFAULT_GUIDE_STYLE,
}


@dataclass(frozen=True)
class CommanderAIConfig:
    """Validated, normalized Commander AI configuration."""

    enabled: bool = False
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    temperature: float = DEFAULT_TEMPERATURE
    stream: bool = False
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    strict_fact_check: bool = True
    guide_style: str = DEFAULT_GUIDE_STYLE

    @property
    def chat_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/api/chat"

    @property
    def tags_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/api/tags"


# --- Normalizers ----------------------------------------------------------

def _as_bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value if value is not None else "").strip().lower()
    if not text:
        return default
    if text in {"y", "yes", "true", "1", "on"}:
        return True
    if text in {"n", "no", "false", "0", "off"}:
        return False
    return default


def _as_float(value: object, default: float, low: float, high: float) -> float:
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
    if result != result:  # NaN guard
        return default
    return max(low, min(high, result))


def _as_int(value: object, default: int, low: int, high: int) -> int:
    try:
        result = int(float(value))  # tolerate "120" and 120.0
    except (TypeError, ValueError):
        return default
    return max(low, min(high, result))


def _as_str(value: object, default: str) -> str:
    text = str(value if value is not None else "").strip()
    return text or default


def normalize_guide_style(value: object) -> str:
    """Map any input to one of GUIDE_STYLES, defaulting to adventurer.

    Accepts bare tokens ("strategist"), title case ("Strategist"), and the
    retired "<X> Guide" labels, all coerced to the lowercase token.
    """
    text = str(value if value is not None else "").strip().lower()
    text = text.replace(" guide", "").strip()
    return text if text in GUIDE_STYLES else DEFAULT_GUIDE_STYLE


def from_settings(data: dict | None) -> CommanderAIConfig:
    """Build a validated config from a loaded settings dict.

    Unknown/missing keys fall back to AI_SETTINGS_DEFAULTS. Out-of-range values
    are clamped. This never raises on bad input.
    """
    data = data or {}
    return CommanderAIConfig(
        enabled=_as_bool(data.get("commander_ai_enabled"), False),
        base_url=_as_str(data.get("commander_ai_base_url"), DEFAULT_BASE_URL),
        model=_as_str(data.get("commander_ai_model"), DEFAULT_MODEL),
        temperature=_as_float(
            data.get("commander_ai_temperature"),
            DEFAULT_TEMPERATURE,
            TEMPERATURE_MIN,
            TEMPERATURE_MAX,
        ),
        stream=_as_bool(data.get("commander_ai_stream"), False),
        timeout_seconds=_as_int(
            data.get("commander_ai_timeout_seconds"),
            DEFAULT_TIMEOUT_SECONDS,
            TIMEOUT_MIN_SECONDS,
            TIMEOUT_MAX_SECONDS,
        ),
        strict_fact_check=_as_bool(data.get("commander_ai_strict_fact_check"), True),
        guide_style=normalize_guide_style(data.get("commander_ai_guide_style")),
    )


def to_settings(config: CommanderAIConfig) -> dict[str, object]:
    """Serialize a config back to the persisted-settings key shape."""
    return {
        "commander_ai_enabled": config.enabled,
        "commander_ai_base_url": config.base_url,
        "commander_ai_model": config.model,
        "commander_ai_temperature": config.temperature,
        "commander_ai_stream": config.stream,
        "commander_ai_timeout_seconds": config.timeout_seconds,
        "commander_ai_strict_fact_check": config.strict_fact_check,
        "commander_ai_guide_style": config.guide_style,
    }
