"""Teacher generation — distill a strong cloud model into the local one.

For knowledge distillation we want GOLD answers: a strong "teacher" (Claude)
answers the SAME grounded prompt the local layer assembles (engine-verified
context + mode + persona), and we save that answer as a training target. The
local qwen2.5:7b is later fine-tuned to imitate the teacher on our data.

This calls the Anthropic Messages API over stdlib urllib (no new dependency —
matching ai/ollama_client.py's posture). Like the Ollama client, it never
raises on a transport/HTTP failure: every failure becomes ok=False + a typed
message, so a long batch run skips a bad call instead of crashing.

Cost note (honest): the big shared system prompt is sent with cache_control,
but on Opus caching only applies above a ~4096-token prefix; our system prompt
is smaller, and the bulk of each call is the per-deck context (unique per deck,
not shareable). So caching helps only modestly here — the tool prints the real
cache_read / cost numbers per call so you can see it rather than trust it.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
TEACHER_MODEL = "claude-opus-4-8"  # the most capable model = best gold answers

# Opus 4.8 pricing per 1M tokens (for the rough cost estimate only).
_PRICE_IN_PER_M = 5.0
_PRICE_OUT_PER_M = 25.0
_PRICE_CACHE_READ_PER_M = 0.5   # ~0.1x input
_PRICE_CACHE_WRITE_PER_M = 6.25  # ~1.25x input


@dataclass
class TeacherResult:
    ok: bool
    text: str = ""
    error: str = ""
    kind: str = ""                       # "no_key" | "http_error" | "offline" | "bad_response"
    usage: dict = field(default_factory=dict)  # raw usage block from the API

    def cost_usd(self) -> float:
        u = self.usage or {}
        inp = u.get("input_tokens", 0) or 0
        out = u.get("output_tokens", 0) or 0
        cw = u.get("cache_creation_input_tokens", 0) or 0
        cr = u.get("cache_read_input_tokens", 0) or 0
        return (
            inp * _PRICE_IN_PER_M
            + out * _PRICE_OUT_PER_M
            + cw * _PRICE_CACHE_WRITE_PER_M
            + cr * _PRICE_CACHE_READ_PER_M
        ) / 1_000_000.0


class TeacherClient:
    """Offline-safe Anthropic Messages client (stdlib urllib).

    api_key defaults to the ANTHROPIC_API_KEY env var. _transport is injectable
    so tests exercise request-shaping and parsing with no network."""

    def __init__(self, *, api_key: str | None = None, model: str = TEACHER_MODEL,
                 timeout: float = 300.0, _transport=None) -> None:
        self.api_key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model
        self.timeout = timeout
        self._transport = _transport  # callable(url, headers, body_bytes) -> (status, text)

    def available(self) -> bool:
        return bool(self.api_key)

    def generate(self, system: str, user: str, *, max_tokens: int = 8000,
                 thinking: bool = True, effort: str = "medium") -> TeacherResult:
        if not self.api_key:
            return TeacherResult(
                ok=False, kind="no_key",
                error="ANTHROPIC_API_KEY is not set. Get a key from console.anthropic.com "
                      "and set it: $env:ANTHROPIC_API_KEY = \"sk-ant-...\" (PowerShell).",
            )

        body: dict = {
            "model": self.model,
            "max_tokens": max_tokens,
            # cache_control on the shared system prompt (no-op below Opus's ~4096-token
            # floor; harmless, and pays off if the prompt grows).
            "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            "messages": [{"role": "user", "content": user}],
        }
        if thinking:
            # Adaptive thinking keeps reasoning in (discarded) thinking blocks, so the
            # text block stays a clean answer — ideal as a training target.
            body["thinking"] = {"type": "adaptive"}
            body["output_config"] = {"effort": effort}

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }
        try:
            status, raw = self._send(headers, body)
        except _TransportError as exc:
            return TeacherResult(ok=False, kind=exc.kind, error=exc.message)

        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return TeacherResult(ok=False, kind="bad_response",
                                 error="The teacher response could not be parsed as JSON.")

        if status >= 400 or data.get("type") == "error":
            msg = (data.get("error") or {}).get("message", f"HTTP {status}")
            return TeacherResult(ok=False, kind="http_error", error=str(msg))

        text = "".join(
            b.get("text", "") for b in (data.get("content") or [])
            if isinstance(b, dict) and b.get("type") == "text"
        ).strip()
        return TeacherResult(ok=bool(text), text=text, usage=data.get("usage") or {},
                             error="" if text else "Teacher returned no text.")

    # -- transport -------------------------------------------------------------

    def _send(self, headers: dict, body: dict) -> tuple[int, str]:
        payload = json.dumps(body).encode("utf-8")
        if self._transport is not None:
            try:
                return self._transport(ANTHROPIC_URL, headers, payload)
            except Exception as exc:  # noqa: BLE001 - injected transport failure -> typed
                raise _TransportError("offline", f"Teacher request failed: {exc!r}.") from exc
        req = urllib.request.Request(ANTHROPIC_URL, data=payload, method="POST", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return resp.status, resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            # HTTP errors carry a JSON body we want to surface, not raise.
            try:
                return exc.code, exc.read().decode("utf-8", errors="replace")
            except Exception:  # noqa: BLE001
                raise _TransportError("http_error", f"HTTP {exc.code} from the teacher API.") from exc
        except urllib.error.URLError as exc:
            raise _TransportError("offline", f"Could not reach the Anthropic API: {exc.reason}.") from exc
        except Exception as exc:  # noqa: BLE001
            raise _TransportError("offline", f"Teacher request failed: {exc!r}.") from exc


class _TransportError(Exception):
    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind
        self.message = message


# --- cost estimation (NO api call, NO key needed) --------------------------

def estimate_for_deck(
    deck_path,
    *,
    config,
    scryfall_lookup,
    persona: str,
    prompt_plan,
    out_tokens: int = 3500,  # conservative: prose + JSON + thinking; errs high on purpose
) -> tuple[float, int]:
    """Estimate the teacher cost for one deck WITHOUT calling the API.

    Builds the real grounded prompts locally (free) and prices them at Opus
    rates, deliberately over-estimating output so the preview is a ceiling, not
    a floor. Returns (estimated_usd, prompt_count)."""
    from pathlib import Path

    import main
    from config import RuntimeConfig
    from parsing.deck_parser import parse_deck_file
    from ai.commander_ai_service import CommanderAIService
    from ai.schemas.ai_context import CommanderAIRequest

    parsed = parse_deck_file(Path(deck_path), scryfall_lookup=scryfall_lookup)
    runtime = RuntimeConfig(
        output_mode="normal", review_direction="both", build_up_config={},
        cut_depth_config={}, prompt_interaction_mode="guided",
        philosophy_key=persona, guide_preference="either",
        intended_bracket="Bracket 3", collection_mode="none",
    )
    analysis = main.build_analysis_context(parsed, runtime, scryfall_lookup, None)
    service = CommanderAIService(config, scryfall_lookup=scryfall_lookup)

    total = 0.0
    n = 0
    for mode, question in prompt_plan:
        _ctx, messages = service.build(CommanderAIRequest(user_text=question, mode=mode), analysis)
        in_chars = sum(len(str(m.get("content", ""))) for m in messages)
        in_tokens = in_chars / 4.0  # rough chars->tokens
        total += (in_tokens * _PRICE_IN_PER_M + out_tokens * _PRICE_OUT_PER_M) / 1_000_000.0
        n += 1
    return total, n


# --- per-deck gold generation ---------------------------------------------

def generate_teacher_for_deck(
    deck_path,
    *,
    teacher: TeacherClient,
    config,
    scryfall_lookup,
    persona: str,
    prompt_plan,
    on_event=None,
) -> tuple[list[dict], dict]:
    """Generate gold (teacher) answers for one deck across the prompt plan.

    Uses the project's own prompt assembly (CommanderAIService.build) so the
    teacher sees the EXACT grounded prompt the layer/inference uses, then runs
    the safety net on the teacher's answer and keeps only verified-clean ones —
    even a strong teacher gets a code-checked floor. Survivors are saved
    approved=True (gold), source=teacher."""
    from pathlib import Path

    import main
    from config import RuntimeConfig
    from parsing.deck_parser import parse_deck_file
    from ai.commander_ai_safety import verify_response
    from ai.commander_ai_service import CommanderAIService
    from ai.schemas.ai_context import CommanderAIRequest

    parsed = parse_deck_file(Path(deck_path), scryfall_lookup=scryfall_lookup)
    runtime = RuntimeConfig(
        output_mode="normal", review_direction="both", build_up_config={},
        cut_depth_config={}, prompt_interaction_mode="guided",
        philosophy_key=persona, guide_preference="either",
        intended_bracket="Bracket 3", collection_mode="none",
    )
    analysis = main.build_analysis_context(parsed, runtime, scryfall_lookup, None)
    service = CommanderAIService(config, scryfall_lookup=scryfall_lookup)

    kept: list[dict] = []
    stats = {"generated": 0, "kept": 0, "dropped": 0, "cost_usd": 0.0}
    for mode, question in prompt_plan:
        request = CommanderAIRequest(user_text=question, mode=mode)
        try:
            ctx, messages = service.build(request, analysis)
            system = messages[0]["content"]
            user = messages[-1]["content"]
            result = teacher.generate(system, user)
        except Exception as exc:  # noqa: BLE001 - one prompt can't abort the deck
            stats["dropped"] += 1
            if on_event:
                on_event("drop", deck=str(deck_path), mode=mode, reason=f"error: {exc!r}")
            continue

        stats["generated"] += 1
        stats["cost_usd"] += result.cost_usd()
        if not result.ok:
            stats["dropped"] += 1
            if on_event:
                on_event("drop", deck=str(deck_path), mode=mode, reason=result.error, kind=result.kind)
            continue

        # Code-checked floor: drop teacher answers that fabricate, even gold ones.
        report = verify_response(result.text, ctx, scryfall_lookup=scryfall_lookup, strict=False)
        if not report.ok:
            stats["dropped"] += 1
            if on_event:
                on_event("drop", deck=str(deck_path), mode=mode, reason="teacher answer failed safety check")
            continue

        kept.append({
            "commander": ctx.commander.get("commander", "") if isinstance(ctx.commander, dict) else "",
            "mode": mode,
            "persona": ctx.persona.get("key", persona) if isinstance(ctx.persona, dict) else persona,
            "guide_style": ctx.guide_style,
            "question": question,
            "answer": result.text,
            "context": ctx.to_json(),
            "approved": True,            # gold + safety-verified -> training-ready
            "source": "teacher",
        })
        stats["kept"] += 1
        if on_event:
            on_event("keep", deck=str(deck_path), mode=mode, cost=result.cost_usd())
    return kept, stats
