"""Gemini teacher-client tests (second provider). No network.

Exercises request-shaping and response-parsing of the Gemini generateContent
client via an injected fake transport (no API key, no network), the free-tier
throttle and 429-retry path with a stubbed sleep, and the CLI's --provider
switch. Run via tests/run_all.py.
"""
from __future__ import annotations

import io
import json
import os
import time
from contextlib import redirect_stdout

from _test_helpers import TestRun

import ai.training.gemini_teacher as gemini_teacher
from ai.training.gemini_teacher import GeminiTeacherClient, _retry_after_seconds


def main() -> None:
    t = TestRun("ai_gemini_teacher")

    # Keys must not leak in from the environment; sleeps are recorded, not slept.
    os.environ.pop("GEMINI_API_KEY", None)
    os.environ.pop("ANTHROPIC_API_KEY", None)
    sleeps: list[float] = []
    gemini_teacher._sleep = sleeps.append

    # --- no API key -> graceful, typed failure (never raises) ---
    no_key = GeminiTeacherClient()
    t.eq("no env key -> not available", no_key.available(), False)
    r = no_key.generate("sys", "user")
    t.eq("no key -> not ok", r.ok, False)
    t.eq("no key -> kind", r.kind, "no_key")
    t.true("no key -> helpful message", "GEMINI_API_KEY" in r.error)
    t.eq("no key -> free cost", r.cost_usd(), 0.0)

    # --- request shaping: header key, systemInstruction, contents, maxOutputTokens ---
    captured = {}

    def fake_ok(url, headers, body_bytes):
        captured["url"] = url
        captured["headers"] = headers
        captured["body"] = json.loads(body_bytes.decode("utf-8"))
        resp = {
            "candidates": [{"content": {"role": "model", "parts": [
                {"text": "Cut the redundant ramp; "},
                {"text": "keep your wincons."},
            ]}, "finishReason": "STOP"}],
            "usageMetadata": {"promptTokenCount": 1000, "candidatesTokenCount": 200},
        }
        return 200, json.dumps(resp), {}

    client = GeminiTeacherClient(api_key="AIza-test", model="gemini-2.5-flash", _transport=fake_ok)
    res = client.generate("SYSTEM PROMPT", "USER PROMPT", max_tokens=4000)
    t.eq("ok answer", res.ok, True)
    t.eq("text extracted (parts joined)", res.text, "Cut the redundant ramp; keep your wincons.")
    t.eq("api key in header", captured["headers"]["x-goog-api-key"], "AIza-test")
    t.true("api key NOT in url", "AIza-test" not in captured["url"])
    t.true("v1beta generateContent url",
           "v1beta" in captured["url"] and captured["url"].endswith("gemini-2.5-flash:generateContent"))
    body = captured["body"]
    t.eq("system -> systemInstruction", body["systemInstruction"]["parts"][0]["text"], "SYSTEM PROMPT")
    t.eq("user -> contents", body["contents"][0]["parts"][0]["text"], "USER PROMPT")
    t.eq("contents role", body["contents"][0]["role"], "user")
    t.eq("maxOutputTokens in generationConfig", body["generationConfig"]["maxOutputTokens"], 4000)
    t.eq("free tier -> cost 0", res.cost_usd(), 0.0)
    t.eq("usage kept (usageMetadata)", res.usage.get("promptTokenCount"), 1000)

    # --- throttle: a second immediate call waits out the minimum interval ---
    gemini_teacher._last_call_monotonic = time.monotonic()
    sleeps.clear()
    client.generate("s", "u")
    t.true("throttle waits ~min interval between calls",
           len(sleeps) == 1 and 6.0 < sleeps[0] <= gemini_teacher._MIN_INTERVAL_S,
           f"sleeps={sleeps}")

    # --- 429 once -> one retry honoring Retry-After, then success ---
    gemini_teacher._last_call_monotonic = 0.0
    sleeps.clear()
    calls = {"n": 0}

    def fake_429_then_ok(url, headers, body_bytes):
        calls["n"] += 1
        if calls["n"] == 1:
            err = {"error": {"code": 429, "message": "quota", "status": "RESOURCE_EXHAUSTED"}}
            return 429, json.dumps(err), {"Retry-After": "12"}
        return fake_ok(url, headers, body_bytes)

    rretry = GeminiTeacherClient(api_key="AIza-test", _transport=fake_429_then_ok).generate("s", "u")
    t.eq("429 then ok -> ok", rretry.ok, True)
    t.eq("429 -> exactly one retry", calls["n"], 2)
    t.in_set("retry slept the Retry-After value", 12.0, sleeps)

    # --- 429 twice -> typed failure, still only one retry ---
    gemini_teacher._last_call_monotonic = 0.0
    sleeps.clear()
    calls["n"] = 0

    def fake_429_always(url, headers, body_bytes):
        calls["n"] += 1
        err = {"error": {"code": 429, "message": "quota", "status": "RESOURCE_EXHAUSTED"}}
        return 429, json.dumps(err), {}

    rcap = GeminiTeacherClient(api_key="AIza-test", _transport=fake_429_always).generate("s", "u")
    t.eq("429 twice -> not ok", rcap.ok, False)
    t.eq("429 twice -> http_error", rcap.kind, "http_error")
    t.eq("429 twice -> no second retry", calls["n"], 2)
    t.in_set("no Retry-After header -> 30s fallback slept", 30.0, sleeps)

    # --- Retry-After parsing (pure helper) ---
    t.eq("Retry-After seconds parsed", _retry_after_seconds({"Retry-After": "12"}), 12.0)
    t.eq("retry-after is case-insensitive", _retry_after_seconds({"retry-after": "7"}), 7.0)
    t.eq("missing header -> 30s fallback", _retry_after_seconds({}), 30.0)
    t.eq("None headers -> 30s fallback", _retry_after_seconds(None), 30.0)
    t.eq("garbage value -> 30s fallback", _retry_after_seconds({"Retry-After": "soon"}), 30.0)
    t.eq("HTTP-date value -> 30s fallback", _retry_after_seconds({"Retry-After": "Wed, 10 Jun 2026 12:00:00 GMT"}), 30.0)

    # --- API error body -> typed failure, not a raise ---
    def fake_err(url, headers, body_bytes):
        return 400, json.dumps({"error": {"code": 400, "message": "bad", "status": "INVALID_ARGUMENT"}}), {}

    rerr = GeminiTeacherClient(api_key="AIza-test", _transport=fake_err).generate("s", "u")
    t.eq("http error not ok", rerr.ok, False)
    t.eq("http error kind", rerr.kind, "http_error")
    t.true("http error surfaces message", "bad" in rerr.error)

    # --- transport raising -> caught as offline, never propagates ---
    def fake_boom(url, headers, body_bytes):
        raise RuntimeError("socket exploded")

    rboom = GeminiTeacherClient(api_key="AIza-test", _transport=fake_boom).generate("s", "u")
    t.eq("transport crash -> not ok", rboom.ok, False)
    t.eq("transport crash -> offline kind", rboom.kind, "offline")
    t.true("transport crash captured", bool(rboom.error))

    # --- empty/no text content -> ok False ---
    def fake_empty(url, headers, body_bytes):
        return 200, json.dumps({"candidates": [{"content": {"parts": []}}], "usageMetadata": {}}), {}

    rempty = GeminiTeacherClient(api_key="AIza-test", _transport=fake_empty).generate("s", "u")
    t.eq("no text -> not ok", rempty.ok, False)

    # --- CLI: --provider gemini accepted; no-key message names the right env var ---
    from ai.cli import generate_teacher as cli

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli.main(["--provider", "gemini"])
    t.eq("cli --provider gemini exits 0 without key", rc, 0)
    t.true("cli names GEMINI_API_KEY for gemini", "GEMINI_API_KEY" in buf.getvalue())
    t.not_in_set("cli does not name ANTHROPIC for gemini", "ANTHROPIC_API_KEY", buf.getvalue())

    buf2 = io.StringIO()
    with redirect_stdout(buf2):
        rc2 = cli.main([])
    t.eq("cli default provider exits 0 without key", rc2, 0)
    t.true("cli names ANTHROPIC_API_KEY by default", "ANTHROPIC_API_KEY" in buf2.getvalue())

    t.report_and_exit()


if __name__ == "__main__":
    main()
