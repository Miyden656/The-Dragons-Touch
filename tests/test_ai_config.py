"""Phase 2 tests: Commander AI config validation/normalization.

Pure logic — no Ollama, no network. Run via tests/run_all.py.
"""
from __future__ import annotations

from _test_helpers import TestRun

from ai.commander_ai_config import (
    AI_SETTINGS_DEFAULTS,
    DEFAULT_MODEL,
    CommanderAIConfig,
    from_settings,
    normalize_guide_style,
    to_settings,
)


def main() -> None:
    t = TestRun("ai_config")

    # --- defaults from an empty dict ---
    d = from_settings({})
    t.eq("empty -> enabled False", d.enabled, False)
    t.eq("empty -> model default", d.model, DEFAULT_MODEL)
    t.eq("empty -> base_url default", d.base_url, "http://localhost:11434")
    t.eq("empty -> temperature default", d.temperature, 0.4)
    t.eq("empty -> stream False", d.stream, False)
    t.eq("empty -> timeout default", d.timeout_seconds, 120)
    t.eq("empty -> strict True", d.strict_fact_check, True)
    t.eq("empty -> guide_style default", d.guide_style, "adventurer")

    # --- None is tolerated ---
    t.eq("None input -> defaults", from_settings(None).model, DEFAULT_MODEL)

    # --- URL helpers ---
    t.eq("chat_url", d.chat_url, "http://localhost:11434/api/chat")
    t.eq("tags_url", d.tags_url, "http://localhost:11434/api/tags")
    trailing = from_settings({"commander_ai_base_url": "http://host:11434/"})
    t.eq("trailing slash trimmed in chat_url", trailing.chat_url, "http://host:11434/api/chat")

    # --- bool coercion ---
    t.eq("enabled 'yes' -> True", from_settings({"commander_ai_enabled": "yes"}).enabled, True)
    t.eq("enabled 'false' -> False", from_settings({"commander_ai_enabled": "false"}).enabled, False)
    t.eq("enabled 1 -> True", from_settings({"commander_ai_enabled": 1}).enabled, True)

    # --- temperature parse + clamp ---
    t.eq("temp '0.9' -> 0.9", from_settings({"commander_ai_temperature": "0.9"}).temperature, 0.9)
    t.eq("temp 5.0 clamped to 1.5", from_settings({"commander_ai_temperature": 5.0}).temperature, 1.5)
    t.eq("temp -1 clamped to 0.0", from_settings({"commander_ai_temperature": -1}).temperature, 0.0)
    t.eq("temp garbage -> default", from_settings({"commander_ai_temperature": "hot"}).temperature, 0.4)

    # --- timeout parse + clamp ---
    t.eq("timeout 3 clamped to 5", from_settings({"commander_ai_timeout_seconds": 3}).timeout_seconds, 5)
    t.eq("timeout 9999 clamped to 600", from_settings({"commander_ai_timeout_seconds": 9999}).timeout_seconds, 600)
    t.eq("timeout '90' -> 90", from_settings({"commander_ai_timeout_seconds": "90"}).timeout_seconds, 90)

    # --- guide style normalization ---
    t.eq("guide 'Strategist' -> strategist", normalize_guide_style("Strategist"), "strategist")
    t.eq("guide 'Archivist Guide' -> archivist", normalize_guide_style("Archivist Guide"), "archivist")
    t.eq("guide 'BOGUS' -> adventurer", normalize_guide_style("BOGUS"), "adventurer")
    t.eq("guide None -> adventurer", normalize_guide_style(None), "adventurer")
    t.eq("guide 'minimal' -> minimal", from_settings({"commander_ai_guide_style": "minimal"}).guide_style, "minimal")

    # num_ctx: defaults large enough to hold the grounded prompt, and clamps.
    from ai.commander_ai_config import DEFAULT_NUM_CTX, NUM_CTX_MAX, NUM_CTX_MIN
    t.eq("num_ctx defaults to DEFAULT_NUM_CTX", from_settings({}).num_ctx, DEFAULT_NUM_CTX)
    t.true("default num_ctx holds a large grounded prompt (>=8192)", DEFAULT_NUM_CTX >= 8192)
    t.eq("num_ctx parsed from settings", from_settings({"commander_ai_num_ctx": 12000}).num_ctx, 12000)
    t.eq("num_ctx clamps high", from_settings({"commander_ai_num_ctx": 999999}).num_ctx, NUM_CTX_MAX)
    t.eq("num_ctx clamps low", from_settings({"commander_ai_num_ctx": 1}).num_ctx, NUM_CTX_MIN)
    t.eq("num_ctx round-trips", to_settings(CommanderAIConfig())["commander_ai_num_ctx"], DEFAULT_NUM_CTX)

    # --- defaults dict shape / round-trip ---
    expected_keys = {
        "commander_ai_enabled", "commander_ai_base_url", "commander_ai_model",
        "commander_ai_temperature", "commander_ai_stream",
        "commander_ai_timeout_seconds", "commander_ai_strict_fact_check",
        "commander_ai_guide_style", "commander_ai_num_ctx",
    }
    t.eq("AI_SETTINGS_DEFAULTS has exactly the expected keys", set(AI_SETTINGS_DEFAULTS), expected_keys)
    t.eq("to_settings keys round-trip", set(to_settings(CommanderAIConfig())), expected_keys)
    # defaults dict must itself normalize to the default config (no drift)
    t.eq("defaults are self-consistent", from_settings(dict(AI_SETTINGS_DEFAULTS)), CommanderAIConfig())

    t.report_and_exit()


if __name__ == "__main__":
    main()
