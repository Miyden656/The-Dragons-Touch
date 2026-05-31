"""Ollama HTTP client for the Commander AI layer — stdlib only.

Why stdlib (urllib) and not `requests`: the project's requirements.txt is just
`PySide6`. Keeping the HTTP path dependency-free preserves the local-first,
low-footprint posture and avoids adding a wheel to the PyInstaller EXE build.

Hard guarantee (enforced by tests/test_ai_ollama_offline.py):
    No method here ever raises because Ollama is down, slow, missing the model,
    or returning garbage. Every failure becomes a typed OllamaChatResult /
    OllamaAvailability with ok=False, a machine-readable `kind`, and a friendly,
    user-facing `message`. A missing or broken Ollama must never crash a report.

Talks to the Ollama REST API:
    GET  {base_url}/api/tags   -> installed models (availability check)
    POST {base_url}/api/chat   -> chat completion (stream or non-stream)
"""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Callable, Iterable

from ai.commander_ai_config import CommanderAIConfig


# --- Result types ---------------------------------------------------------

# error kinds (machine-readable):
#   "" (ok) | "offline" | "model_missing" | "timeout" | "http_error" | "bad_response"

@dataclass(frozen=True)
class OllamaChatResult:
    ok: bool
    text: str = ""
    model: str = ""
    error: str = ""          # friendly, user-facing message when ok is False
    kind: str = ""           # machine-readable error kind (see above)
    raw: dict | None = None


@dataclass(frozen=True)
class OllamaAvailability:
    ok: bool                 # is the Ollama server reachable?
    message: str             # friendly status / problem description
    models: tuple[str, ...] = ()
    model_installed: bool = False  # is the configured model present?
    kind: str = ""


Message = dict  # {"role": "system"|"user"|"assistant", "content": str}


class OllamaClient:
    """A thin, offline-safe wrapper over the Ollama chat API."""

    def __init__(self, config: CommanderAIConfig) -> None:
        self.config = config

    # -- availability ------------------------------------------------------

    def is_available(self) -> OllamaAvailability:
        """Check that the server responds and report whether the model is present.

        Never raises. Returns ok=False with a friendly message when Ollama is
        unreachable.
        """
        try:
            body = self._get(self.config.tags_url)
        except _OllamaTransportError as exc:
            return OllamaAvailability(ok=False, message=exc.message, kind=exc.kind)

        try:
            data = json.loads(body)
            models = tuple(
                str(m.get("name", "")).strip()
                for m in data.get("models", [])
                if isinstance(m, dict) and m.get("name")
            )
        except (json.JSONDecodeError, AttributeError, TypeError):
            return OllamaAvailability(
                ok=False,
                message=(
                    f"Ollama responded at {self.config.base_url} but the model list "
                    "could not be read. Is this really an Ollama server?"
                ),
                kind="bad_response",
            )

        installed = _model_matches(self.config.model, models)
        if installed:
            message = f"Ollama is running and '{self.config.model}' is installed."
        else:
            pretty = ", ".join(models) if models else "(none installed)"
            message = (
                f"Ollama is running, but '{self.config.model}' is not installed. "
                f"Installed models: {pretty}. Install it with: ollama pull {self.config.model}"
            )
        return OllamaAvailability(
            ok=True,
            message=message,
            models=models,
            model_installed=installed,
            kind="" if installed else "model_missing",
        )

    # -- chat --------------------------------------------------------------

    def chat(
        self,
        messages: Iterable[Message],
        *,
        temperature: float | None = None,
    ) -> OllamaChatResult:
        """Non-streaming chat completion. Never raises."""
        payload = self._build_payload(messages, temperature, stream=False)
        try:
            body = self._post(self.config.chat_url, payload)
        except _OllamaTransportError as exc:
            return OllamaChatResult(ok=False, model=self.config.model, error=exc.message, kind=exc.kind)

        try:
            data = json.loads(body)
            text = str(data.get("message", {}).get("content", ""))
        except (json.JSONDecodeError, AttributeError, TypeError):
            return OllamaChatResult(
                ok=False,
                model=self.config.model,
                error="The local model returned a response that could not be parsed.",
                kind="bad_response",
            )
        return OllamaChatResult(ok=True, text=text, model=self.config.model, raw=data)

    def stream_chat(
        self,
        messages: Iterable[Message],
        *,
        temperature: float | None = None,
        on_delta: Callable[[str], None] | None = None,
    ) -> OllamaChatResult:
        """Streaming chat completion.

        Calls `on_delta(text)` for each chunk as it arrives (for live UI
        rendering) and returns the final accumulated typed result. Never raises;
        on transport failure returns ok=False just like chat().
        """
        payload = self._build_payload(messages, temperature, stream=True)
        chunks: list[str] = []
        last: dict | None = None
        try:
            for line in self._post_stream(self.config.chat_url, payload):
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                last = obj
                piece = str(obj.get("message", {}).get("content", ""))
                if piece:
                    chunks.append(piece)
                    if on_delta is not None:
                        on_delta(piece)
                if obj.get("done"):
                    break
        except _OllamaTransportError as exc:
            return OllamaChatResult(ok=False, model=self.config.model, error=exc.message, kind=exc.kind)

        return OllamaChatResult(ok=True, text="".join(chunks), model=self.config.model, raw=last)

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        on_delta: Callable[[str], None] | None = None,
    ) -> OllamaChatResult:
        """Convenience: build [system, user] messages and respect config.stream."""
        messages: list[Message] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        if self.config.stream:
            return self.stream_chat(messages, on_delta=on_delta)
        return self.chat(messages)

    # -- internals ---------------------------------------------------------

    def _build_payload(
        self,
        messages: Iterable[Message],
        temperature: float | None,
        *,
        stream: bool,
    ) -> dict:
        temp = self.config.temperature if temperature is None else temperature
        return {
            "model": self.config.model,
            "messages": list(messages),
            "stream": stream,
            "options": {"temperature": temp},
        }

    def _get(self, url: str) -> str:
        req = urllib.request.Request(url, method="GET")
        return self._open(req)

    def _post(self, url: str, payload: dict) -> str:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, method="POST", headers={"Content-Type": "application/json"}
        )
        return self._open(req)

    def _open(self, req: urllib.request.Request) -> str:
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001 - translate ALL transport failures
            raise self._translate(exc) from exc

    def _post_stream(self, url: str, payload: dict) -> Iterable[str]:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, method="POST", headers={"Content-Type": "application/json"}
        )
        try:
            resp = urllib.request.urlopen(req, timeout=self.config.timeout_seconds)
        except Exception as exc:  # noqa: BLE001
            raise self._translate(exc) from exc
        try:
            for raw_line in resp:
                yield raw_line.decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001 - mid-stream socket failure
            raise self._translate(exc) from exc
        finally:
            try:
                resp.close()
            except Exception:
                pass

    def _translate(self, exc: Exception) -> "_OllamaTransportError":
        """Map a raw transport exception to a typed, friendly error."""
        base = self.config.base_url
        model = self.config.model

        if isinstance(exc, urllib.error.HTTPError):
            if exc.code == 404:
                return _OllamaTransportError(
                    "model_missing",
                    f"Ollama is running but model '{model}' was not found. "
                    f"Install it with: ollama pull {model}",
                )
            return _OllamaTransportError(
                "http_error",
                f"Ollama returned an HTTP error ({exc.code}) from {base}.",
            )

        if isinstance(exc, (socket.timeout, TimeoutError)):
            return _OllamaTransportError(
                "timeout",
                f"The local model took longer than {self.config.timeout_seconds}s to "
                "respond. Try a smaller/faster model or raise the timeout in Settings.",
            )

        if isinstance(exc, urllib.error.URLError):
            reason = getattr(exc, "reason", exc)
            if isinstance(reason, (socket.timeout, TimeoutError)):
                return _OllamaTransportError(
                    "timeout",
                    f"The local model took longer than {self.config.timeout_seconds}s to "
                    "respond. Try a smaller/faster model or raise the timeout in Settings.",
                )
            return _OllamaTransportError(
                "offline",
                f"Ollama does not appear to be running at {base}. Start Ollama "
                "(run `ollama serve`) and try again, or disable Local Commander AI "
                "in Settings.",
            )

        return _OllamaTransportError(
            "offline",
            f"Could not reach Ollama at {base}. Start Ollama and try again, or disable "
            "Local Commander AI in Settings.",
        )


# --- internal transport error (never escapes this module) -----------------

class _OllamaTransportError(Exception):
    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind
        self.message = message


def _model_matches(wanted: str, installed: Iterable[str]) -> bool:
    """Match the configured model against installed names, tolerating tags.

    Ollama reports models as "llama3.1:latest"; users usually configure
    "llama3.1". Treat a missing tag as ":latest" and compare leniently.
    """
    wanted = (wanted or "").strip().lower()
    if not wanted:
        return False
    wanted_base = wanted.split(":", 1)[0]
    for name in installed:
        name = (name or "").strip().lower()
        if not name:
            continue
        if name == wanted:
            return True
        if name.split(":", 1)[0] == wanted_base:
            return True
    return False
