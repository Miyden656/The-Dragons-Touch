"""Phase 4.5 tests: the orchestration service.

Uses an injected fake Ollama client so the full chain (serialize -> assemble ->
'model' -> safety) runs with no Ollama. Run via tests/run_all.py.
"""
from __future__ import annotations

from collections import Counter
from types import SimpleNamespace as NS

from _test_helpers import TestRun

from ai.commander_ai_config import from_settings
from ai.commander_ai_service import CommanderAIService
from ai.commander_ai_sessions import SessionStore
from ai.ollama_client import OllamaAvailability, OllamaChatResult
from ai.schemas.ai_context import CommanderAIRequest


class FakeClient:
    """Stand-in for OllamaClient that returns a canned result and records input."""

    def __init__(self, result: OllamaChatResult) -> None:
        self.result = result
        self.captured_messages = None
        self.stream_called = False

    def chat(self, messages, **kwargs):
        self.captured_messages = messages
        return self.result

    def stream_chat(self, messages, *, on_delta=None, **kwargs):
        self.stream_called = True
        self.captured_messages = messages
        if on_delta and self.result.ok:
            on_delta(self.result.text)
        return self.result

    def is_available(self):
        return OllamaAvailability(ok=True, message="fake up", model_installed=True)


def _analysis() -> dict:
    return {
        "version_label": "TEST",
        "runtime_config": NS(intended_bracket="Bracket 3"),
        "parsed_deck": NS(commander_name="Krenko, Mob Boss", deck_card_count=100),
        "command_zone": NS(commander_name="Krenko, Mob Boss", commander_names=["Krenko, Mob Boss"],
                           companion_names=[], command_zone_rule_detected="basic_legendary_creature",
                           commander_color_identity=["R"], commander_color_identity_text="Mono-Red"),
        "legality": NS(deck_size_legal=True, expected_deck_size=100, has_any_issues=False,
                       banned_cards=[], banned_commanders=[], color_identity_violations=[],
                       cards_not_found=[], illegal_duplicate_cards=[]),
        "role_summary": NS(role_counts=Counter({"Ramp": 10}), type_counts=Counter({"Creature": 30}),
                           card_roles=[NS(card_name="Sol Ring", quantity=1, detected_roles=["ramp"],
                                          mana_value=1, card_types=["Artifact"])], unknown_cards=[]),
        "strategy_summary": NS(primary_strategy="Goblins", secondary_strategy="", confidence="high",
                               warnings=[], core_synergy_packages=[], candidates=[]),
        "plan_fit_summary": NS(strong_synergy_cards=[], possible_off_plan_cards=[]),
        "bracket_summary": NS(estimated_bracket="Bracket 3", pressure_level="low",
                              pressure_cards=[], notes=[]),
        "possible_cuts": NS(required_cut_candidates=[], optional_cut_candidates=[],
                            manual_review_candidates=[], playtest_first_candidates=[],
                            protected_from_cut=[], notes=[]),
        "protected_cards": [],
        "replacement_needs": NS(priority_categories=[], need_details=[]),
        "replacement_candidates": NS(top_ranked_candidates=[], candidates=[]),
        "collection_candidates": NS(candidate_matching_active=True,
                                    strong_candidates=[NS(card_name="Goblin Chieftain", quantity_owned=1,
                                                          confidence="High", matched_needs=[], reason="owned")],
                                    possible_candidates=[]),
        "collection_summary": NS(loaded=True, active=True, ready_for_matching=True, total_cards=100,
                                 unique_cards=80, found_cards=100, not_found_cards=[]),
        "philosophy_context": {"key": "pet_card", "label": "Pet Card", "guide_name": "Mia",
                               "guide_role": "The Pet Card Mentor", "core_question": "?",
                               "protect_bias": ["pet cards"], "review_bias": [], "replacement_bias": []},
    }


def _config(**over):
    base = {"commander_ai_model": "testmodel", "commander_ai_guide_style": "strategist",
            "commander_ai_strict_fact_check": True}
    base.update(over)
    return from_settings(base)


def main() -> None:
    t = TestRun("ai_service")
    analysis = _analysis()
    req = CommanderAIRequest(user_text="What should I cut?", mode="cut_review")

    # --- happy path with a fabricated ownership claim in the reply ---
    fake = FakeClient(OllamaChatResult(ok=True, model="testmodel",
                                       text="You already own Dockside Extortionist, so add it."))
    svc = CommanderAIService(_config(), client=fake)
    resp = svc.answer(req, analysis)
    t.eq("response ok", resp.ok, True)
    t.eq("model carried", resp.model, "testmodel")
    t.eq("mode carried", resp.mode, "cut_review")
    t.eq("guide style from config", resp.guide_style, "strategist")
    t.eq("raw text is the model text", resp.raw_text, "You already own Dockside Extortionist, so add it.")
    t.eq("safety caught fabrication", resp.safety_ok, False)
    t.true("safety flags populated", len(resp.safety_flags) >= 1)
    t.true("annotated text has footer", "Fact-check notes" in resp.text)

    # messages the service built
    msgs = fake.captured_messages
    t.eq("system is first", msgs[0]["role"], "system")
    t.eq("user is last", msgs[-1]["role"], "user")
    t.true("context reached the model", "Krenko, Mob Boss" in msgs[-1]["content"])
    t.true("cut-review mode block in system", "Mode: Cut Review" in msgs[0]["content"])

    # --- offline failure becomes a typed response, never an exception ---
    off = FakeClient(OllamaChatResult(ok=False, model="testmodel",
                                      error="Ollama does not appear to be running.", kind="offline"))
    svc_off = CommanderAIService(_config(), client=off)
    r = svc_off.answer(req, analysis)
    t.eq("offline -> ok False", r.ok, False)
    t.eq("offline kind carried", r.error_kind, "offline")
    t.true("offline error in text", "Ollama" in r.text)
    t.eq("offline safety not flagged", r.safety_ok, True)

    # --- strict=False: flags recorded but no footer appended ---
    fake2 = FakeClient(OllamaChatResult(ok=True, model="m",
                                        text="You already own Dockside Extortionist."))
    svc_lax = CommanderAIService(_config(commander_ai_strict_fact_check=False), client=fake2)
    r2 = svc_lax.answer(req, analysis)
    t.eq("lax still records safety flags", r2.safety_ok, False)
    t.true("lax leaves text unannotated", "Fact-check notes" not in r2.text)

    # --- session continuity across turns ---
    store = SessionStore()
    sess = store.get_or_create("s1", deck_key="krenko")
    fake3 = FakeClient(OllamaChatResult(ok=True, model="m", text="A helpful clean answer about tokens."))
    svc3 = CommanderAIService(_config(), client=fake3)
    svc3.answer(CommanderAIRequest(user_text="first question", mode="commander_review"), analysis, session=sess)
    t.eq("session has 2 turns after one answer", len(sess), 2)
    svc3.answer(CommanderAIRequest(user_text="second question", mode="commander_review"), analysis, session=sess)
    msgs2 = fake3.captured_messages
    t.true("second turn included prior history", any(
        m.get("content") == "first question" for m in msgs2))
    t.eq("second turn message count = system + 2 history + user", len(msgs2), 4)
    t.eq("session has 4 turns after two answers", len(sess), 4)

    # --- streaming path invokes on_delta and still returns a typed response ---
    deltas: list[str] = []
    fake4 = FakeClient(OllamaChatResult(ok=True, model="m", text="streamed answer"))
    svc4 = CommanderAIService(_config(), client=fake4)
    r4 = svc4.answer(req, analysis, on_delta=deltas.append)
    t.true("stream path used", fake4.stream_called)
    t.eq("delta delivered", deltas, ["streamed answer"])
    t.eq("stream response ok", r4.ok, True)

    # --- build() (dry-run) returns ctx + messages without calling the model ---
    fake5 = FakeClient(OllamaChatResult(ok=True, model="m", text="should not be used"))
    svc5 = CommanderAIService(_config(), client=fake5)
    ctx, built = svc5.build(req, analysis)
    t.eq("build did not call model", fake5.captured_messages, None)
    t.eq("build produced system+user", len(built), 2)
    t.eq("build ctx commander", ctx.commander.get("commander"), "Krenko, Mob Boss")

    # --- response.to_dict is UI-safe ---
    d = resp.to_dict()
    t.true("to_dict has text", "text" in d and isinstance(d["safety_flags"], list))

    t.report_and_exit()


if __name__ == "__main__":
    main()
