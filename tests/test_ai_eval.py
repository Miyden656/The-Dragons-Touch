"""Eval-harness tests (training track, step 2). Ollama-free.

Verifies the objective scoring logic (legality via the safety-flag oracle,
non-empty, structured, mentions) and the run_eval loop with a FakeClient.
Run via tests/run_all.py.
"""
from __future__ import annotations

from collections import Counter
from types import SimpleNamespace as NS

from _test_helpers import TestRun

from ai.commander_ai_config import from_settings
from ai.commander_ai_service import CommanderAIService
from ai.ollama_client import OllamaChatResult
from ai.schemas.ai_response import CommanderAIResponse, CommanderAIStructured
from ai.training.eval import (
    CHECK_ALLOWLIST,
    CHECK_LEGALITY,
    CHECK_MENTIONS,
    CHECK_NONEMPTY,
    CHECK_SAFETY_CLEAN,
    CHECK_STRUCTURED,
    DEFAULT_EVAL_CASES,
    EvalCase,
    run_eval,
    score_response,
)


class FakeClient:
    def __init__(self, text: str) -> None:
        self.result = OllamaChatResult(ok=True, text=text, model="fake")

    def chat(self, messages, **kwargs):
        return self.result

    def stream_chat(self, messages, *, on_delta=None, **kwargs):
        if on_delta:
            on_delta(self.result.text)
        return self.result


def _resp(**over) -> CommanderAIResponse:
    base = dict(ok=True, text="Sol Ring is banned in Legacy.", safety_ok=True, safety_flags=())
    base.update(over)
    return CommanderAIResponse(**base)


def main() -> None:
    t = TestRun("ai_eval")

    # --- nonempty ---
    t.true("nonempty passes", score_response(_resp(), [{"type": CHECK_NONEMPTY}])[0].passed)
    t.true("empty fails", not score_response(_resp(text="  "), [{"type": CHECK_NONEMPTY}])[0].passed)

    # --- safety_clean ---
    t.true("safety clean passes", score_response(_resp(), [{"type": CHECK_SAFETY_CLEAN}])[0].passed)
    dirty = _resp(safety_ok=False, safety_flags=({"kind": "ban_contradicted", "card": "Sol Ring", "note": ""},))
    t.true("safety dirty fails", not score_response(dirty, [{"type": CHECK_SAFETY_CLEAN}])[0].passed)

    # --- structured ---
    t.true("structured present passes",
           score_response(_resp(structured=CommanderAIStructured(summary="x")), [{"type": CHECK_STRUCTURED}])[0].passed)
    t.true("structured absent fails", not score_response(_resp(), [{"type": CHECK_STRUCTURED}])[0].passed)

    # --- mentions any/none ---
    r = score_response(_resp(), [{"type": CHECK_MENTIONS, "any": ["sol ring"], "none": ["dies"]}])[0]
    t.true("mentions any+none passes", r.passed)
    r = score_response(_resp(), [{"type": CHECK_MENTIONS, "any": ["planeswalker"]}])[0]
    t.true("missing 'any' fails", not r.passed)
    r = score_response(_resp(), [{"type": CHECK_MENTIONS, "none": ["banned"]}])[0]
    t.true("forbidden phrase fails", not r.passed)

    # --- legality oracle: pass when card addressed and NO contradiction flag ---
    good = score_response(_resp(), [{"type": CHECK_LEGALITY, "card": "Sol Ring"}])[0]
    t.true("correct legality passes", good.passed)
    # model made a wrong legality claim -> safety flagged it -> eval fails
    wrong = _resp(safety_ok=False,
                  safety_flags=({"kind": "legality_contradicted", "card": "Sol Ring", "note": ""},))
    bad = score_response(wrong, [{"type": CHECK_LEGALITY, "card": "Sol Ring"}])[0]
    t.true("contradicted legality fails", not bad.passed)
    # didn't even mention the card -> fail
    silent = score_response(_resp(text="I'm not sure."), [{"type": CHECK_LEGALITY, "card": "Sol Ring"}])[0]
    t.true("unaddressed card fails", not silent.passed)
    # a contradiction about a DIFFERENT card shouldn't fail this card's check
    other = _resp(safety_ok=False,
                  safety_flags=({"kind": "ban_contradicted", "card": "Mana Crypt", "note": ""},))
    t.true("other-card contradiction doesn't fail this one",
           score_response(other, [{"type": CHECK_LEGALITY, "card": "Sol Ring"}])[0].passed)

    # --- allowlist: structured cuts must stay within engine candidates ---
    on_list = _resp(structured=CommanderAIStructured(possible_cuts=({"card": "Mind Stone"},)))
    cf = {"cut_candidates": {"mind stone", "divination"}}
    t.true("on-list cut passes",
           score_response(on_list, [{"type": CHECK_ALLOWLIST}], context_facts=cf)[0].passed)
    off_list = _resp(structured=CommanderAIStructured(possible_cuts=({"card": "Sol Ring"},)))
    r = score_response(off_list, [{"type": CHECK_ALLOWLIST}], context_facts=cf)[0]
    t.true("off-list cut fails", not r.passed)
    t.true("off-list detail names offender", "Sol Ring" in r.detail)
    t.true("no candidates -> allowlist fails",
           not score_response(on_list, [{"type": CHECK_ALLOWLIST}], context_facts={})[0].passed)
    no_cuts = _resp(structured=CommanderAIStructured(summary="no cuts"))
    t.true("no cuts named -> vacuously on-list",
           score_response(no_cuts, [{"type": CHECK_ALLOWLIST}], context_facts=cf)[0].passed)

    # --- unknown check type -> recorded as failed, not crash ---
    t.true("unknown check fails safely", not score_response(_resp(), [{"type": "nope"}])[0].passed)

    # --- run_eval loop with a FakeClient (no Ollama) ---
    cases = [
        EvalCase(id="c1", question="Is Sol Ring legal in Legacy?",
                 checks=[{"type": CHECK_NONEMPTY}, {"type": CHECK_LEGALITY, "card": "Sol Ring"}]),
        EvalCase(id="c2", question="review", mode="commander_review",
                 checks=[{"type": CHECK_NONEMPTY}]),
    ]
    svc = CommanderAIService(from_settings({}), client=FakeClient("Sol Ring is banned in Legacy."))
    report = run_eval(cases, service=svc, scryfall_lookup=None, model="fake")
    t.eq("report model", report.model, "fake")
    t.eq("two cases run", len(report.cases), 2)
    t.eq("all cases fully passed", report.cases_passed, 2)
    t.eq("checks total = 3", report.checks_total, 3)
    t.eq("checks passed = 3", report.checks_passed, 3)
    t.true("pass rate is 1.0", abs(report.pass_rate() - 1.0) < 1e-9)

    # a model failure is recorded, not raised
    class _BadClient:
        def chat(self, messages, **kwargs):
            return OllamaChatResult(ok=False, model="fake", error="offline", kind="offline")
        def stream_chat(self, messages, *, on_delta=None, **kwargs):
            return self.chat(messages)

    bad_report = run_eval([cases[0]], service=CommanderAIService(from_settings({}), client=_BadClient()),
                          model="bad")
    t.eq("failed case recorded", len(bad_report.cases), 1)
    t.true("failed case marked not ok", not bad_report.cases[0].ok)
    t.true("failed case carries error", bool(bad_report.cases[0].error))

    # --- the built-in eval set is well-formed ---
    t.true("default eval set non-empty", len(DEFAULT_EVAL_CASES) >= 5)
    t.true("every default case has checks", all(c.checks for c in DEFAULT_EVAL_CASES))
    t.true("every default case has an id", all(c.id for c in DEFAULT_EVAL_CASES))

    t.report_and_exit()


if __name__ == "__main__":
    main()
