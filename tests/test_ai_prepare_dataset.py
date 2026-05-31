"""Training-dataset prep tests (training track, step 3). Ollama-free.

Verifies a corpus record round-trips into the exact inference-time prompt triple
(system + user + assistant), that unbuildable records are skipped (not emitted
broken), and that the corpus->dataset pipeline cleans + converts correctly.
Run via tests/run_all.py.
"""
from __future__ import annotations

import json

from _test_helpers import TestRun

from ai.schemas.ai_context import CommanderAIContext
from ai.training.prepare_dataset import corpus_to_dataset, record_to_example


def _ctx_json(**over) -> str:
    base = dict(
        user_request="What should I cut?",
        mode="cut_review",
        commander={"commander": "Krenko, Mob Boss", "color_identity": ["R"]},
        decklist=[{"name": "Sol Ring", "count": 1, "roles": ["ramp"]}],
        persona={"key": "pet_card", "label": "Pet Card"},
        guide_style="adventurer",
    )
    base.update(over)
    return CommanderAIContext(**base).to_json()


def _rec(**over) -> dict:
    base = {
        "commander": "Krenko, Mob Boss",
        "mode": "cut_review",
        "persona": "pet_card",
        "guide_style": "adventurer",
        "question": "What should I cut?",
        "answer": "Trim the weakest ramp piece.",
        "context": _ctx_json(),
        "approved": True,
    }
    base.update(over)
    return base


def main() -> None:
    t = TestRun("ai_prepare_dataset")

    # --- a good record -> a 3-message training example ---
    ex = record_to_example(_rec())
    t.true("example produced", ex is not None)
    msgs = ex["messages"]
    t.eq("three messages", len(msgs), 3)
    t.eq("first is system", msgs[0]["role"], "system")
    t.eq("second is user", msgs[1]["role"], "user")
    t.eq("third is assistant", msgs[2]["role"], "assistant")
    t.eq("assistant carries the answer", msgs[2]["content"], "Trim the weakest ramp piece.")

    # --- the rebuilt prompt mirrors the live layer (mode + persona + grounding) ---
    t.true("system has identity", "Dragon's Touch Commander Guide" in msgs[0]["content"])
    t.true("system has cut-review mode", "Mode: Cut Review" in msgs[0]["content"])
    t.true("system reflects persona", "Pet Card" in msgs[0]["content"])
    t.true("user embeds verified context json", "Krenko, Mob Boss" in msgs[1]["content"])
    t.true("user has the question", "What should I cut?" in msgs[1]["content"])

    # --- unbuildable records are skipped, not emitted broken ---
    t.eq("missing answer -> None", record_to_example(_rec(answer="")), None)
    t.eq("missing context -> None", record_to_example(_rec(context="")), None)
    t.eq("bad context json -> None", record_to_example(_rec(context="{not json")), None)
    t.eq("non-dict -> None", record_to_example("nope"), None)

    # --- corpus -> dataset: cleans (approved+valid+dedup) then converts ---
    records = [
        _rec(),
        _rec(),  # exact duplicate -> deduped
        _rec(question="Different?", answer="Different answer.", context=_ctx_json(user_request="Different?")),
        _rec(question="Unapproved?", approved=False),   # dropped by approved_only
        _rec(question="NoCtx?", context=""),             # valid record (empty ctx allowed) but unbuildable
    ]
    examples, report = corpus_to_dataset(records, approved_only=True)
    t.eq("report started count", report["started"], 5)
    t.true("dropped the unapproved", report["dropped_unapproved"] >= 1)
    t.true("dropped a duplicate", report["dropped_duplicate"] >= 1)
    t.true("dropped the unbuildable", report["dropped_unbuildable"] >= 1)
    t.true("produced at least the 2 good examples", report["examples"] >= 2)
    t.eq("examples count matches list", len(examples), report["examples"])
    t.true("every example is a messages object",
           all("messages" in e and len(e["messages"]) == 3 for e in examples))

    # --- emitted JSONL is valid json per line ---
    line = json.dumps(examples[0], ensure_ascii=False)
    t.true("example serializes to one json line", json.loads(line)["messages"][0]["role"] == "system")

    t.report_and_exit()


if __name__ == "__main__":
    main()
