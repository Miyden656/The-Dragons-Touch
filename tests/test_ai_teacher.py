"""Teacher-client + review-logic tests (training track, step 5). No network.

Exercises request-shaping and response-parsing of the Anthropic Messages client
via an injected fake transport (no API key, no network), and the pure
review-decision applier. Run via tests/run_all.py.
"""
from __future__ import annotations

import json

from _test_helpers import TestRun

from ai.training.corpus import apply_review_decisions
from ai.training.teacher import TeacherClient


def main() -> None:
    t = TestRun("ai_teacher")

    # --- no API key -> graceful, typed failure (never raises) ---
    no_key = TeacherClient(api_key="")
    t.eq("no key -> not available", no_key.available(), False)
    r = no_key.generate("sys", "user")
    t.eq("no key -> not ok", r.ok, False)
    t.eq("no key -> kind", r.kind, "no_key")
    t.true("no key -> helpful message", "ANTHROPIC_API_KEY" in r.error)

    # --- request shaping: model, version header, system cache_control, user ---
    captured = {}

    def fake_ok(url, headers, body_bytes):
        captured["url"] = url
        captured["headers"] = headers
        captured["body"] = json.loads(body_bytes.decode("utf-8"))
        resp = {
            "type": "message",
            "content": [
                {"type": "thinking", "thinking": ""},
                {"type": "text", "text": "Cut the redundant ramp; keep your wincons."},
            ],
            "usage": {"input_tokens": 1000, "output_tokens": 200,
                      "cache_creation_input_tokens": 0, "cache_read_input_tokens": 800},
        }
        return 200, json.dumps(resp)

    client = TeacherClient(api_key="sk-test", model="claude-opus-4-8", _transport=fake_ok)
    res = client.generate("SYSTEM PROMPT", "USER PROMPT", max_tokens=4000)
    t.eq("ok answer", res.ok, True)
    t.eq("text extracted (text blocks only)", res.text, "Cut the redundant ramp; keep your wincons.")
    body = captured["body"]
    t.eq("model in body", body["model"], "claude-opus-4-8")
    t.eq("max_tokens in body", body["max_tokens"], 4000)
    t.eq("version header set", captured["headers"]["anthropic-version"], "2023-06-01")
    t.eq("api key header set", captured["headers"]["x-api-key"], "sk-test")
    t.true("system is a cached block",
           isinstance(body["system"], list)
           and body["system"][0]["cache_control"] == {"type": "ephemeral"}
           and body["system"][0]["text"] == "SYSTEM PROMPT")
    t.eq("user message passed", body["messages"][0]["content"], "USER PROMPT")
    t.true("adaptive thinking on by default", body.get("thinking") == {"type": "adaptive"})
    t.true("cost is positive and small", 0 < res.cost_usd() < 1.0)

    # thinking can be disabled
    res2 = client.generate("s", "u", thinking=False)
    t.true("thinking omitted when disabled", "thinking" not in captured["body"])
    t.eq("still ok", res2.ok, True)

    # --- API error body -> typed failure, not a raise ---
    def fake_err(url, headers, body_bytes):
        return 400, json.dumps({"type": "error", "error": {"type": "invalid_request_error", "message": "bad"}})

    rerr = TeacherClient(api_key="sk-test", _transport=fake_err).generate("s", "u")
    t.eq("http error not ok", rerr.ok, False)
    t.eq("http error kind", rerr.kind, "http_error")
    t.true("http error surfaces message", "bad" in rerr.error)

    # --- transport raising -> caught as offline, never propagates ---
    def fake_boom(url, headers, body_bytes):
        raise RuntimeError("socket exploded")

    rboom = TeacherClient(api_key="sk-test", _transport=fake_boom).generate("s", "u")
    t.eq("transport crash -> not ok", rboom.ok, False)
    t.true("transport crash captured", bool(rboom.error))

    # --- empty/no text content -> ok False ---
    def fake_empty(url, headers, body_bytes):
        return 200, json.dumps({"type": "message", "content": [{"type": "thinking", "thinking": "x"}], "usage": {}})

    rempty = TeacherClient(api_key="sk-test", _transport=fake_empty).generate("s", "u")
    t.eq("no text -> not ok", rempty.ok, False)

    # --- review decisions (pure) ---
    recs = [
        {"question": "a", "approved": False},
        {"question": "b", "approved": False},
        {"question": "c", "approved": False},
    ]
    updated, summary = apply_review_decisions(recs, {0: "keep", 1: "reject"})
    t.eq("kept count", summary["kept"], 1)
    t.eq("rejected count", summary["rejected"], 1)
    t.eq("remaining (b dropped)", len(updated), 2)
    t.eq("kept record approved flipped", updated[0]["approved"], True)
    t.true("rejected record gone", all(rr["question"] != "b" for rr in updated))
    t.eq("skipped record untouched", updated[1]["approved"], False)  # 'c' shifted to index 1
    # no decisions -> unchanged
    same, summ2 = apply_review_decisions(recs, {})
    t.eq("no decisions keeps all", len(same), 3)
    t.eq("no decisions kept 0", summ2["kept"], 0)

    t.report_and_exit()


if __name__ == "__main__":
    main()
