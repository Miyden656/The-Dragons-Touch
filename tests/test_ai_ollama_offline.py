"""Phase 2 tests: the Ollama client must fail SAFELY when Ollama is absent.

The whole point: a missing/broken Ollama must never raise into the caller and
must never crash a report. Every failure becomes a typed, friendly result.

We point the client at a closed port (127.0.0.1:1) so the connection is refused
immediately — no real Ollama required, fast and deterministic. Run via
tests/run_all.py.
"""
from __future__ import annotations

from _test_helpers import TestRun

from ai.commander_ai_config import from_settings
from ai.ollama_client import OllamaAvailability, OllamaChatResult, OllamaClient


def _offline_client() -> OllamaClient:
    # Port 1 is not an Ollama server; connection is refused immediately.
    config = from_settings(
        {
            "commander_ai_base_url": "http://127.0.0.1:1",
            "commander_ai_model": "llama3.1",
            "commander_ai_timeout_seconds": 5,
        }
    )
    return OllamaClient(config)


def main() -> None:
    t = TestRun("ai_ollama_offline")
    client = _offline_client()

    # --- is_available never raises and reports a clean offline status ---
    avail = None
    raised = ""
    try:
        avail = client.is_available()
    except Exception as exc:  # noqa: BLE001
        raised = repr(exc)
    t.eq("is_available did not raise", raised, "")
    t.true("is_available returns OllamaAvailability", isinstance(avail, OllamaAvailability))
    if isinstance(avail, OllamaAvailability):
        t.eq("offline -> ok False", avail.ok, False)
        t.true("offline message mentions Ollama", "Ollama" in avail.message, avail.message)

    # --- chat never raises and returns a typed failure ---
    res = None
    raised = ""
    try:
        res = client.chat([{"role": "user", "content": "hi"}])
    except Exception as exc:  # noqa: BLE001
        raised = repr(exc)
    t.eq("chat did not raise", raised, "")
    t.true("chat returns OllamaChatResult", isinstance(res, OllamaChatResult))
    if isinstance(res, OllamaChatResult):
        t.eq("chat ok False when offline", res.ok, False)
        t.eq("chat kind == offline", res.kind, "offline")
        t.true("chat error message is non-empty", bool(res.error), res.error)
        t.true("chat error mentions Ollama", "Ollama" in res.error, res.error)
        t.eq("chat text empty on failure", res.text, "")

    # --- list_models never raises and returns an empty tuple when offline ---
    raised = ""
    models = None
    try:
        models = client.list_models(timeout=1.0)
    except Exception as exc:  # noqa: BLE001
        raised = repr(exc)
    t.eq("list_models did not raise", raised, "")
    t.eq("list_models empty when offline", models, ())

    # --- complete() (the convenience path) also fails safely ---
    raised = ""
    cres = None
    try:
        cres = client.complete("system", "user prompt")
    except Exception as exc:  # noqa: BLE001
        raised = repr(exc)
    t.eq("complete did not raise", raised, "")
    t.true("complete ok False", isinstance(cres, OllamaChatResult) and cres.ok is False)

    # --- stream_chat never raises and returns a typed failure ---
    raised = ""
    sres = None
    deltas: list[str] = []
    try:
        sres = client.stream_chat(
            [{"role": "user", "content": "hi"}],
            on_delta=deltas.append,
        )
    except Exception as exc:  # noqa: BLE001
        raised = repr(exc)
    t.eq("stream_chat did not raise", raised, "")
    t.true("stream_chat ok False", isinstance(sres, OllamaChatResult) and sres.ok is False)
    t.eq("no deltas emitted when offline", deltas, [])

    t.report_and_exit()


if __name__ == "__main__":
    main()
