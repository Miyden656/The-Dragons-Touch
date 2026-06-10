"""Gemini teacher — a second (free-tier) source of GOLD answers.

Same job as ai/training/teacher.py's TeacherClient, pointed at Google's Gemini
API instead of Anthropic's: the teacher answers the SAME grounded prompt the
local layer assembles, and the answer becomes a training target. Duck-typed to
match TeacherClient (available() / generate() -> TeacherResult), so
generate_teacher_for_deck works with either provider unchanged.

This calls the v1beta generateContent endpoint over stdlib urllib (no new
dependency — matching ai/ollama_client.py's posture). Like the Anthropic
client, it never raises on a transport/HTTP failure: every failure becomes
ok=False + a typed message, so a long batch run skips a bad call instead of
crashing.

Free-tier posture: calls are paced by a module-level minimum interval (~9
requests/minute) and a 429 gets exactly ONE retry honoring the Retry-After
header (30s fallback). Cost is reported as $0.00 — paid-tier Gemini pricing
isn't modeled.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

from ai.training.teacher import TeacherResult, _TransportError

GEMINI_URL_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_TEACHER_MODEL = "gemini-2.5-flash"

_MIN_INTERVAL_S = 6.5    # free-tier RPM headroom (~9 requests/minute)
_RETRY_FALLBACK_S = 30.0
_last_call_monotonic = 0.0
_sleep = time.sleep      # module-level so tests can stub the waits


def _throttle() -> None:
    """Enforce the free-tier minimum interval between calls (monotonic clock)."""
    global _last_call_monotonic
    wait = _MIN_INTERVAL_S - (time.monotonic() - _last_call_monotonic)
    if wait > 0:
        _sleep(wait)
    _last_call_monotonic = time.monotonic()


def _retry_after_seconds(headers) -> float:
    """Seconds to wait per a 429's Retry-After header (fallback 30s)."""
    raw = ""
    if hasattr(headers, "items"):
        for k, v in headers.items():
            if str(k).lower() == "retry-after":
                raw = str(v).strip()
                break
    try:
        secs = float(raw)
        return secs if secs > 0 else _RETRY_FALLBACK_S
    except (TypeError, ValueError):
        return _RETRY_FALLBACK_S


class GeminiTeacherClient:
    """Offline-safe Gemini generateContent client (stdlib urllib).

    api_key defaults to the GEMINI_API_KEY env var and travels in the
    x-goog-api-key header — never the URL, so it can't leak into logs.
    _transport is injectable so tests exercise request-shaping, parsing and
    the 429-retry path with no network."""

    def __init__(self, *, api_key: str | None = None, model: str = GEMINI_TEACHER_MODEL,
                 timeout: float = 300.0, _transport=None) -> None:
        self.api_key = api_key if api_key is not None else os.environ.get("GEMINI_API_KEY", "")
        self.model = model
        self.timeout = timeout
        self._transport = _transport  # callable(url, headers, body_bytes) -> (status, text, resp_headers)

    def available(self) -> bool:
        return bool(self.api_key)

    def generate(self, system: str, user: str, *, max_tokens: int = 8000) -> TeacherResult:
        if not self.api_key:
            return TeacherResult(
                ok=False, kind="no_key", cost=0.0,
                error="GEMINI_API_KEY is not set. Get a free key from aistudio.google.com "
                      "and set it: $env:GEMINI_API_KEY = \"AIza...\" (PowerShell).",
            )

        body: dict = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"maxOutputTokens": max_tokens},
        }
        headers = {
            "x-goog-api-key": self.api_key,
            "content-type": "application/json",
        }
        _throttle()
        try:
            status, raw, resp_headers = self._send(headers, body)
        except _TransportError as exc:
            return TeacherResult(ok=False, kind=exc.kind, error=exc.message, cost=0.0)

        if status == 429:
            # Exactly one retry, honoring Retry-After when the server sends it.
            _sleep(_retry_after_seconds(resp_headers))
            _throttle()
            try:
                status, raw, resp_headers = self._send(headers, body)
            except _TransportError as exc:
                return TeacherResult(ok=False, kind=exc.kind, error=exc.message, cost=0.0)

        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return TeacherResult(ok=False, kind="bad_response", cost=0.0,
                                 error="The teacher response could not be parsed as JSON.")

        if status >= 400 or data.get("error"):
            msg = (data.get("error") or {}).get("message", f"HTTP {status}")
            return TeacherResult(ok=False, kind="http_error", error=str(msg), cost=0.0)

        text = "".join(
            p.get("text", "")
            for cand in (data.get("candidates") or []) if isinstance(cand, dict)
            for p in ((cand.get("content") or {}).get("parts") or []) if isinstance(p, dict)
        ).strip()
        # Free tier: cost is $0.00 by design (paid-tier Gemini pricing isn't modeled).
        return TeacherResult(ok=bool(text), text=text, usage=data.get("usageMetadata") or {},
                             cost=0.0, error="" if text else "Teacher returned no text.")

    # -- transport -------------------------------------------------------------

    def _send(self, headers: dict, body: dict) -> tuple[int, str, dict]:
        url = f"{GEMINI_URL_BASE}/{self.model}:generateContent"
        payload = json.dumps(body).encode("utf-8")
        if self._transport is not None:
            try:
                return self._transport(url, headers, payload)
            except Exception as exc:  # noqa: BLE001 - injected transport failure -> typed
                raise _TransportError("offline", f"Teacher request failed: {exc!r}.") from exc
        req = urllib.request.Request(url, data=payload, method="POST", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return resp.status, resp.read().decode("utf-8", errors="replace"), dict(resp.headers)
        except urllib.error.HTTPError as exc:
            # HTTP errors carry a JSON body (and Retry-After) we want to surface, not raise.
            try:
                return exc.code, exc.read().decode("utf-8", errors="replace"), dict(exc.headers or {})
            except Exception:  # noqa: BLE001
                raise _TransportError("http_error", f"HTTP {exc.code} from the teacher API.") from exc
        except urllib.error.URLError as exc:
            raise _TransportError("offline", f"Could not reach the Gemini API: {exc.reason}.") from exc
        except Exception as exc:  # noqa: BLE001
            raise _TransportError("offline", f"Teacher request failed: {exc!r}.") from exc
