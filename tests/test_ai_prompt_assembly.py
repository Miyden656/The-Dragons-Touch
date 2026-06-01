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
            "tone": "respectful, honest, and emotionally safe",
            "family_tone": "warm, enthusiastic, emotionally validating, and honest about function",
            "family_label": "Timmy / Tammy",
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

    # --- persona drives VOICE: distilled per-guide voice profile blended over the
    # family register (from ai/prompts/persona_voices.md; pet_card == Milo / Mia) ---
    t.true("persona signature vocabulary rendered", "protected joy slot" in sys_prompt)
    t.true("persona example sentence rendered", "Sounds like:" in sys_prompt)
    t.true("persona phrases-to-avoid rendered", "Avoid sounding like:" in sys_prompt)
    t.true("persona family register still blended", "Timmy / Tammy family" in sys_prompt)
    t.true("voice shapes both priorities and voice", "BOTH your priorities and your voice" in sys_prompt)
    t.true("guide style no longer dictates tone", "Format:" in sys_prompt)

    # --- Layer 1: 4-player teaching is baked into the system + mode prompts ---
    t.true("multiplayer reality block present", "MULTIPLAYER REALITY" in sys_prompt)
    t.true("teaches sweeper-vs-spot value math", "answers three boards at once" in sys_prompt)
    t.true("cut-review pod-value tiebreaker present", "Multiplayer value as a tiebreaker" in sys_prompt)
    tutor_prompt = build_system_prompt(_ctx(mode="strategy_tutor"))
    t.true("strategy tutor pod piloting guidance", "Piloting at a 4-player table" in tutor_prompt)
    persona_prompt = build_system_prompt(_ctx(mode="persona_coaching"))
    t.true("persona coaching pod framing", "Persona at the table" in persona_prompt)

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

    # --- cut allow-list now carries the engine's own reasons (polish) ---
    cut_ctx = CommanderAIContext(
        mode="cut_review",
        cuts={
            "optional_cuts": [
                {"card": "Sylvan Library", "confidence": "Medium", "reasons": ["off-plan low synergy"]}
            ],
            "manual_review": [{"card": "Yawgmoth's Will", "confidence": "Low", "reasons": []}],
        },
    )
    cut_user = build_user_prompt(cut_ctx)
    t.true("cut allow-list header present", "ONLY cards you may recommend cutting" in cut_user)
    t.true("cut card listed", "Sylvan Library" in cut_user)
    t.true("engine reason rendered", "off-plan low synergy" in cut_user)
    t.true("engine confidence rendered", "engine confidence: Medium" in cut_user)
    t.true("told to use engine's reason", "do not substitute a reason of your own" in cut_user)

    # --- replacement: named verified candidates -> hard allow-list ---
    repl_named = CommanderAIContext(
        mode="replacement",
        replacements={
            "priority_categories": ["More ramp"],
            "candidates": [{"card": "Cultivate", "replacement_category": "ramp", "why_it_fits": "fixes mana"}],
        },
    )
    rn = build_user_prompt(repl_named)
    t.true("replacement allow-list header", "ONLY specific cards you may recommend adding" in rn)
    t.true("named candidate listed", "Cultivate" in rn)
    t.true("must come from list", "MUST come from this exact list" in rn)

    # --- replacement: categories only, no verified cards -> steer to categories ---
    repl_cats = CommanderAIContext(
        mode="replacement",
        replacements={"priority_categories": ["More ramp"], "need_details": [
            {"category": "More ramp", "reason": "low rock count"}]},
    )
    rc = build_user_prompt(repl_cats)
    t.true("categories-only header", "no specific verified cards available" in rc)
    t.true("category surfaced", "More ramp" in rc)
    t.true("told not to name cards", "do NOT name specific cards" in rc)

    # --- multiplayer pod-value focus: surfaced for review/strategy/persona modes ---
    mp_ctx = CommanderAIContext(
        mode="commander_review",
        multiplayer={
            "interaction": {"sweepers": 2, "spot_removal": 5, "counterspells": 1, "reach_band": "balanced"},
            "table_reach": {"band": "table_wide"},
            "archenemy": {"risk_band": "high"},
            "facts": [
                "Board wipes: 2 - each can answer all three opponents' boards at once.",
                "Archenemy / threat density: high - likely to attract focused removal.",
            ],
            "example_cards": {"sweepers": ["Culling Ritual", "Damnation"], "threats": ["Sol Ring"]},
        },
    )
    mp_user = build_user_prompt(mp_ctx)
    t.true("pod-value header present (review)", "Verified pod facts (4-player reasoning" in mp_user)
    t.true("pod fact rendered", "each can answer all three opponents" in mp_user)
    t.true("pod grounding instruction", "do not invent" in mp_user.lower())
    # The engine-identified card names ride in the focus block (needle), so a
    # small model names the real sweepers instead of inventing them.
    t.true("example sweeper names in focus", "Culling Ritual" in mp_user and "Damnation" in mp_user)
    t.true("told to use exact engine names", "use these EXACT names" in mp_user)

    # --- pod-value focus is NOT injected for cut_review (has its own allow-list) ---
    cut_no_mp = build_user_prompt(CommanderAIContext(
        mode="cut_review",
        multiplayer={"facts": ["Board wipes: 2 - sweepers scale up."]},
    ))
    t.true("no pod-focus block in cut_review", "Verified pod facts (4-player reasoning" not in cut_no_mp)

    # --- focus falls back to bands when no facts list is present ---
    mp_bands = build_user_prompt(CommanderAIContext(
        mode="strategy_tutor",
        multiplayer={"interaction": {"sweepers": 0, "spot_removal": 3, "counterspells": 0, "reach_band": "narrow"},
                     "table_reach": {"band": "single_target"}, "archenemy": {"risk_band": "low"}},
    ))
    t.true("pod-focus falls back to bands", "Archenemy risk: low" in mp_bands)

    # --- empty multiplayer -> no block, no crash ---
    mp_empty = build_user_prompt(CommanderAIContext(mode="commander_review", multiplayer={}))
    t.true("empty multiplayer -> no pod block", "Verified pod facts (4-player reasoning" not in mp_empty)

    # --- political focus: surfaced for review/strategy/persona when is_political ---
    pol_ctx = CommanderAIContext(
        mode="commander_review",
        political={
            "is_political": True,
            "primary": {"name": "Group Slug", "axis": "punish normal game actions",
                        "confidence": "medium", "commander_support": "strong",
                        "example_cards": ["Nekusar, the Mindrazer"]},
            "secondary": None,
            "table_dependency": "low", "salt_risk": "medium", "reputation_modifier": "none",
            "warnings": ["Salt risk: long games may frustrate the table."],
        },
    )
    pol_user = build_user_prompt(pol_ctx)
    t.true("political header present", "Verified political read (Section-3 archetypes" in pol_user)
    t.true("political primary named", "Group Slug" in pol_user)
    t.true("political example card surfaced", "Nekusar, the Mindrazer" in pol_user)
    t.true("political grounding instruction", "do not invent a political archetype" in pol_user)

    # --- NON-political deck -> no political block ---
    non_pol = build_user_prompt(CommanderAIContext(
        mode="commander_review", political={"is_political": False, "primary": None}))
    t.true("non-political -> no political block", "Verified political read (Section-3" not in non_pol)

    # --- political focus NOT injected for cut_review ---
    cut_no_pol = build_user_prompt(CommanderAIContext(
        mode="cut_review", political={"is_political": True, "primary": {"name": "Group Slug"}}))
    t.true("no political block in cut_review", "Verified political read (Section-3" not in cut_no_pol)

    t.report_and_exit()


if __name__ == "__main__":
    main()
