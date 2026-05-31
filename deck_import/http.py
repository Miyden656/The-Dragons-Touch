"""Thin stdlib-urllib HTTP helper for the importer.

Mirrors the posture of ai/ollama_client.py — no third-party deps, every
failure is captured into a typed result rather than raised. Sites that
return JSON OR plain text both go through `fetch`.
"""

import json as _json
import socket
from dataclasses import dataclass
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request


DEFAULT_TIMEOUT_SECONDS = 20
USER_AGENT = "DragonsTouch-DeckImporter/1.0 (+https://github.com/Miyden656/The-Dragons-Touch)"


@dataclass(frozen=True)
class FetchResult:
    ok: bool
    status: int = 0
    text: str = ""
    error_kind: str = ""       # offline | timeout | not_found | blocked | http_error | bad_response
    message: str = ""

    def json(self) -> Any:
        if not self.text:
            return None
        try:
            return _json.loads(self.text)
        except Exception:
            return None


def fetch(
    url: str,
    *,
    timeout: float | None = None,
    headers: dict[str, str] | None = None,
) -> FetchResult:
    """GET a URL with friendly error handling. Never raises.

    Returns FetchResult with ok=True only when the server returned a 2xx
    and the body decoded as text. All other outcomes carry an error_kind
    in {offline, timeout, not_found, blocked, http_error, bad_response}.
    """
    t = float(timeout) if timeout else DEFAULT_TIMEOUT_SECONDS
    hdrs = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if headers:
        hdrs.update(headers)

    req = urllib_request.Request(url, headers=hdrs, method="GET")
    try:
        with urllib_request.urlopen(req, timeout=t) as resp:
            raw = resp.read()
            charset = "utf-8"
            content_type = resp.headers.get("Content-Type", "") or ""
            for piece in content_type.split(";"):
                piece = piece.strip().lower()
                if piece.startswith("charset="):
                    charset = piece.split("=", 1)[1].strip() or "utf-8"
            try:
                text = raw.decode(charset, errors="replace")
            except LookupError:
                text = raw.decode("utf-8", errors="replace")
            return FetchResult(ok=True, status=int(getattr(resp, "status", 200) or 200), text=text)
    except urllib_error.HTTPError as exc:
        status = int(getattr(exc, "code", 0) or 0)
        if status == 404:
            return FetchResult(ok=False, status=status, error_kind="not_found",
                               message="The deck was not found at that URL.")
        if status in (401, 403):
            return FetchResult(ok=False, status=status, error_kind="blocked",
                               message="The site refused the request — the deck may be private or rate-limited.")
        return FetchResult(ok=False, status=status, error_kind="http_error",
                           message=f"The site returned HTTP {status}.")
    except urllib_error.URLError as exc:
        reason = getattr(exc, "reason", "")
        if isinstance(reason, socket.timeout):
            return FetchResult(ok=False, error_kind="timeout",
                               message="The request timed out before the site responded.")
        return FetchResult(ok=False, error_kind="offline",
                           message=f"Could not reach the site: {reason}")
    except socket.timeout:
        return FetchResult(ok=False, error_kind="timeout",
                           message="The request timed out before the site responded.")
    except Exception as exc:
        return FetchResult(ok=False, error_kind="bad_response",
                           message=f"Unexpected error while fetching the deck: {exc}")
