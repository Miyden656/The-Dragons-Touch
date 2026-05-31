"""Candidate-generator tests (training track, step 4). Ollama-free.

Tests the pure quality gate (keep_candidate) and record shaping. The deck->
analysis->answer loop is integration (needs the engine + a model) and is
exercised by a real `generate_corpus --limit` run, not here. Run via run_all.py.
"""
from __future__ import annotations

from types import SimpleNamespace as NS

from _test_helpers import TestRun

from ai.training.generate import candidate_record, keep_candidate


def _resp(ok=True, safety_ok=True, structured=object(), raw_text="An answer."):
    return NS(ok=ok, safety_ok=safety_ok, structured=structured, raw_text=raw_text)


def main() -> None:
    t = TestRun("ai_generate")

    # --- keep_candidate gate ---
    keep, _ = keep_candidate(_resp(), "cut_review")
    t.true("clean structured answer kept", keep)

    keep, reason = keep_candidate(_resp(ok=False), "cut_review")
    t.true("not-ok dropped", not keep)
    t.true("not-ok reason mentions error", "error" in reason or "no answer" in reason)

    keep, reason = keep_candidate(_resp(safety_ok=False), "cut_review")
    t.true("unsafe dropped", not keep)
    t.true("unsafe reason mentions safety", "safety" in reason.lower())

    # structured modes require structured output...
    keep, reason = keep_candidate(_resp(structured=None), "cut_review")
    t.true("structured mode w/o JSON dropped", not keep)
    t.true("reason mentions structured", "structured" in reason.lower())

    # ...but conversational modes don't
    keep, _ = keep_candidate(_resp(structured=None), "strategy_tutor")
    t.true("conversational mode w/o JSON kept", keep)

    keep, reason = keep_candidate(_resp(raw_text="   "), "strategy_tutor")
    t.true("empty answer dropped", not keep)

    keep, reason = keep_candidate(None, "commander_review")
    t.true("None response dropped safely", not keep)

    # --- candidate_record shape ---
    rec = candidate_record(
        commander="Krenko, Mob Boss", mode="cut_review", persona="pet_card",
        guide_style="adventurer", question="cuts?", answer="trim ramp",
        context_json='{"mode":"cut_review"}',
    )
    t.eq("record commander", rec["commander"], "Krenko, Mob Boss")
    t.eq("record is unapproved (candidate)", rec["approved"], False)
    t.eq("record marked auto-generated", rec["source"], "auto-generated")
    t.true("record has all corpus fields",
           all(k in rec for k in ("commander", "mode", "persona", "guide_style", "question", "answer", "context", "approved")))

    t.report_and_exit()


if __name__ == "__main__":
    main()
