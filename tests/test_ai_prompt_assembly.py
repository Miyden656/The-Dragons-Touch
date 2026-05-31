"""Phase 4 tests: prompt assembly (system + mode + persona + guide style + user).

Pure logic, no Ollama. Builds a CommanderAIContext directly and asserts the
assembled prompts contain the right fragments. Run via tests/run_all.py.
"""
from __future__ import annotations

from _test_helpers import TestRun

from ai.commander_ai_prompts import (
    build_messages,
    build_system_prompt,
    build_user_prompt,
    load_prompt_asset,
)
from ai.schemas.ai_context import CommanderAIContext


def _ctx(mode: str = "cut_review", guide_style: str = "strategist") -> CommanderAIContext:
    return CommanderAIContext(
        user_request="What should I cut?",
        mode=mode,
        commander={"commander": "Krenko, Mob Boss", "color_identity": ["R"]},
        decklist=[{"name": "Sol Ring", "count": 1, "roles": ["ramp"]}],
        legality={"banned_cards": []},
        strategy={"primary_strategy": "Goblins", "confidence": "high"},
        persona={
            "key": "pet_card", "label": "Pet Card", "guide_name": "Mia",
            "guide_role": "The Pet Card Mentor", "core_question": "Which cards matter to you?",
            "rules_summary": "Protect beloved cards.",
            "protect_bias": ["declared pet cards", "signature cards"],
            "review_bias": ["pure value cards"], "replacement_bias": ["synergy over power"],
        },
        guide_style=guide_style,
        pet_cards=["Goblin Bombardment"],
        user_constraints=["keep it mono-red"],
        warnings=["Deck size is not legal: 60 of 100 expected."],
        uncertainties=["Combo awareness was not run."],
    )


def main() -> None:
    t = TestRun("ai_prompt_assembly")

    # --- asset loader ---
    t.true("system_prompt.md loads non-empty", len(load_prompt_asset("system_prompt.md")) > 50)
    t.eq("missing asset -> empty string", load_prompt_asset("does_not_exist.md"), "")

    sys_prompt = build_system_prompt(_ctx(mode="cut_review", guide_style="strategist"))

    # --- system prompt composition ---
    t.true("identity present", "Dragon's Touch Commander Guide" in sys_prompt)
    t.true("guardrails present", "Do not invent" in sys_prompt)
    t.true("mode block present (cut review)", "Mode: Cut Review" in sys_prompt)
    t.true("persona block present", "Persona (deck-building philosophy)" in sys_prompt)
    t.true("persona protect bias rendered", "declared pet cards" in sys_prompt)
    t.true("persona guide name rendered", "Mia" in sys_prompt)
    t.true("guide style present (strategist)", "Guide style: Strategist" in sys_prompt)

    # --- mode switching ---
    review_prompt = build_system_prompt(_ctx(mode="commander_review"))
    t.true("commander review mode block", "Mode: Commander Review" in review_prompt)
    t.true("review mode excludes cut block", "Mode: Cut Review" not in review_prompt)

    # --- unknown mode falls back to commander review ---
    fallback = build_system_prompt(_ctx(mode="not_a_real_mode"))
    t.true("unknown mode -> commander review fallback", "Mode: Commander Review" in fallback)

    # --- guide style switching changes wording ---
    adventurer = build_system_prompt(_ctx(guide_style="adventurer"))
    minimal = build_system_prompt(_ctx(guide_style="minimal"))
    t.true("adventurer style present", "Guide style: Adventurer" in adventurer)
    t.true("minimal style present", "Guide style: Minimal" in minimal)
    t.true("styles differ", adventurer != minimal)

    # --- user prompt content ---
    user_prompt = build_user_prompt(_ctx())
    t.true("context json embedded", '"commander"' in user_prompt and "Krenko, Mob Boss" in user_prompt)
    t.true("user request present", "What should I cut?" in user_prompt)
    t.true("warnings surfaced", "Deck size is not legal" in user_prompt)
    t.true("uncertainties surfaced", "Combo awareness was not run" in user_prompt)
    t.true("pet cards surfaced", "Goblin Bombardment" in user_prompt)
    t.true("constraints surfaced", "keep it mono-red" in user_prompt)

    # --- messages assembly ---
    msgs = build_messages(_ctx())
    t.eq("two messages by default", len(msgs), 2)
    t.eq("first is system", msgs[0]["role"], "system")
    t.eq("last is user", msgs[-1]["role"], "user")

    history = [{"role": "user", "content": "earlier q"}, {"role": "assistant", "content": "earlier a"}]
    msgs_h = build_messages(_ctx(), history=history)
    t.eq("history inserted -> 4 messages", len(msgs_h), 4)
    t.eq("history sits between system and user", msgs_h[1]["content"], "earlier q")
    t.eq("user request still last", msgs_h[-1]["role"], "user")

    # --- empty-context safety (no persona) ---
    bare = build_system_prompt(CommanderAIContext(mode="replacement"))
    t.true("bare context still assembles a system prompt", "Dragon's Touch Commander Guide" in bare)
    t.true("bare context still has a guide style", "Guide style:" in bare)

    t.report_and_exit()


if __name__ == "__main__":
    main()
