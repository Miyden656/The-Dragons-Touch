"""Phase 6b tests: structured-output parsing + prompt wiring + service path.

Verifies the trailing JSON block is split off cleanly, coerced defensively,
that a broken block degrades to text-only (never raises), and that the service
attaches the structured view while showing clean prose. Run via run_all.py.
"""
from __future__ import annotations

from types import SimpleNamespace as NS

from _test_helpers import TestRun

from ai.commander_ai_parsing import parse_structured_response
from ai.commander_ai_prompts import STRUCTURED_MODES, build_user_prompt
from ai.commander_ai_service import CommanderAIService
from ai.commander_ai_config import from_settings
from ai.ollama_client import OllamaChatResult
from ai.schemas.ai_context import (
    MODE_CUT_REVIEW,
    MODE_PERSONA_COACHING,
    CommanderAIContext,
    CommanderAIRequest,
)
from ai.schemas.ai_response import CommanderAIStructured


class FakeClient:
    def __init__(self, text: str) -> None:
        self.result = OllamaChatResult(ok=True, text=text, model="fake")

    def chat(self, messages, **kwargs):
        return self.result

    def stream_chat(self, messages, *, on_delta=None, **kwargs):
        if on_delta:
            on_delta(self.result.text)
        return self.result


_GOOD = """Here is my read: cut the weakest ramp.

```json
{
  "summary": "Trim two ramp pieces.",
  "confidence": "high",
  "possible_cuts": [
    {"card": "Mind Stone", "reason": "redundant ramp", "confidence": "medium", "cut_type": "optional"},
    {"reason": "no card named here"}
  ],
  "protected_cards": [{"card": "Sol Ring", "reason": "best rock"}],
  "replacement_needs": ["card draw", 42, ""],
  "follow_up_questions": ["What's your budget?"],
  "confidence_extra": "ignored"
}
```"""


def main() -> None:
    t = TestRun("ai_response_parsing")

    # --- clean parse: prose stripped of the fence, fields coerced ---
    prose, s, failed = parse_structured_response(_GOOD)
    t.true("prose kept", "cut the weakest ramp" in prose)
    t.true("fence removed from prose", "```" not in prose)
    t.eq("not a parse failure", failed, False)
    t.true("structured present", s is not None)
    t.eq("summary parsed", s.summary, "Trim two ramp pieces.")
    t.eq("confidence parsed", s.confidence, "high")
    t.eq("possible_cuts keeps only carded rows", len(s.possible_cuts), 1)
    t.eq("cut card name", s.possible_cuts[0]["card"], "Mind Stone")
    t.eq("protected parsed", s.protected_cards[0]["card"], "Sol Ring")
    t.eq("replacement_needs drops non-str/empty", tuple(s.replacement_needs), ("card draw", "42"))
    t.eq("follow ups parsed", len(s.follow_up_questions), 1)

    # --- confidence validation ---
    _, s2, _ = parse_structured_response('text\n```json\n{"summary":"x","confidence":"super-high"}\n```')
    t.eq("bad confidence -> empty", s2.confidence, "")

    # --- no fence: pure prose, no structure, not a failure ---
    prose3, s3, failed3 = parse_structured_response("Just a plain answer with no JSON.")
    t.eq("plain prose returned", prose3, "Just a plain answer with no JSON.")
    t.eq("no structure", s3, None)
    t.eq("no failure for plain prose", failed3, False)

    # --- malformed fence: degrade to text-only, flag the failure ---
    prose4, s4, failed4 = parse_structured_response("Answer.\n```json\n{not valid json,,}\n```")
    t.eq("malformed -> no structure", s4, None)
    t.eq("malformed -> parse_failed", failed4, True)
    t.true("malformed keeps full text", "Answer." in prose4)

    # --- empty/irrelevant object -> treated as no structure ---
    _, s5, failed5 = parse_structured_response('Hi.\n```json\n{}\n```')
    t.eq("empty object -> no structure", s5, None)
    t.eq("empty object -> not a failure", failed5, False)

    # --- last fence wins (model may stray) ---
    two = 'a\n```json\n{"summary":"first"}\n```\nb\n```json\n{"summary":"second"}\n```'
    _, s6, _ = parse_structured_response(two)
    t.eq("last fence wins", s6.summary, "second")

    # --- prompt wiring: structured modes get the output-format block ---
    cut_ctx = CommanderAIContext(mode=MODE_CUT_REVIEW)
    coach_ctx = CommanderAIContext(mode=MODE_PERSONA_COACHING)
    t.true("cut_review is a structured mode", MODE_CUT_REVIEW in STRUCTURED_MODES)
    t.true("coaching is not structured", MODE_PERSONA_COACHING not in STRUCTURED_MODES)
    cut_user = build_user_prompt(cut_ctx)
    coach_user = build_user_prompt(coach_ctx)
    t.true("output format in cut_review user prompt", "Output format" in cut_user)
    t.true("output format is last in user prompt", cut_user.rstrip().endswith("on its own."))
    t.true("no output format in coaching user prompt", "Output format" not in coach_user)

    # --- service path: clean prose shown, structured attached ---
    analysis = _min_analysis()
    service = CommanderAIService(from_settings({}), client=FakeClient(_GOOD))
    resp = service.answer(CommanderAIRequest(user_text="cuts?", mode=MODE_CUT_REVIEW), analysis)
    t.eq("service ok", resp.ok, True)
    t.true("service text is clean prose", "```" not in resp.text)
    t.true("service attaches structured", isinstance(resp.structured, CommanderAIStructured))
    t.eq("service structured confidence", resp.structured.confidence, "high")
    t.true("raw_text keeps the json", "```json" in resp.raw_text)
    d = resp.to_dict()
    t.true("to_dict carries structured", d["structured"] is not None and d["structured"]["confidence"] == "high")

    # malformed JSON through the service -> ok, no structure, parse_failed
    resp2 = service_with("Answer.\n```json\n{bad,,}\n```", MODE_CUT_REVIEW)
    t.eq("service survives bad json", resp2.ok, True)
    t.eq("service marks parse_failed", resp2.parse_failed, True)
    t.eq("service structured None on bad json", resp2.structured, None)

    t.report_and_exit()


def service_with(text: str, mode: str):
    return CommanderAIService(from_settings({}), client=FakeClient(text)).answer(
        CommanderAIRequest(user_text="q", mode=mode), _min_analysis()
    )


def _min_analysis() -> dict:
    """Smallest analysis dict the serializer tolerates (relies on safe_access)."""
    from collections import Counter

    return {
        "version_label": "TEST",
        "runtime_config": NS(intended_bracket="Bracket 3"),
        "parsed_deck": NS(commander_name="Krenko, Mob Boss", deck_card_count=100),
        "command_zone": NS(commander_name="Krenko, Mob Boss", commander_names=["Krenko, Mob Boss"],
                           companion_names=[], commander_color_identity=["R"]),
        "legality": NS(deck_size_legal=True, banned_cards=[], banned_commanders=[],
                       color_identity_violations=[], cards_not_found=[], illegal_duplicate_cards=[]),
        "role_summary": NS(role_counts=Counter(), type_counts=Counter(), card_roles=[], unknown_cards=[]),
        "strategy_summary": NS(primary_strategy="Goblins", confidence="high", warnings=[]),
        "bracket_summary": NS(estimated_bracket="Bracket 3", pressure_level="low", pressure_cards=[], notes=[]),
        "possible_cuts": NS(required_cut_candidates=[], optional_cut_candidates=[],
                            manual_review_candidates=[], playtest_first_candidates=[],
                            protected_from_cut=[], notes=[]),
    }


if __name__ == "__main__":
    main()
