"""Entry point: take any URL, return a normalized DeckImportResult.

Never raises. The whole module is intentionally small — the per-site
work lives in deck_import/sources/.
"""

from urllib.parse import urlparse

from deck_import.sources import archidekt, moxfield, mtggoldfish
from deck_import.types import DeckImportResult, make_error


_ADAPTERS = (moxfield, archidekt, mtggoldfish)

SUPPORTED_SOURCES = tuple(a.NAME for a in _ADAPTERS)
SUPPORTED_DOMAINS = tuple(domain for a in _ADAPTERS for domain in a.DOMAINS)


def _normalize_url(url: str) -> str:
    text = (url or "").strip()
    if not text:
        return ""
    # Accept bare hostnames like "moxfield.com/decks/abc" — prepend scheme.
    if "://" not in text:
        text = "https://" + text
    return text


def detect_source(url: str):
    """Return the adapter module that claims the URL, or None.

    Used by the UI to show a friendly "Detected: Moxfield" hint before
    the user clicks Import.
    """
    text = _normalize_url(url)
    if not text:
        return None
    try:
        parsed = urlparse(text)
    except Exception:
        return None
    host = (parsed.netloc or "").lower()
    if ":" in host:
        host = host.split(":", 1)[0]
    if not host:
        return None
    for adapter in _ADAPTERS:
        for domain in adapter.DOMAINS:
            if host == domain or host.endswith("." + domain):
                return adapter
    return None


def import_from_url(url: str, *, timeout: float | None = None, fetcher=None) -> DeckImportResult:
    """Fetch and normalize a deck from a supported site.

    `fetcher` is the same shape as deck_import.http.fetch — accept this
    so callers (and tests) can inject a fake transport.
    """
    raw = (url or "").strip()
    if not raw:
        return make_error(
            error_kind="invalid_url",
            message="Paste a deck URL first.",
            source_url=raw,
        )

    text = _normalize_url(raw)
    try:
        parsed = urlparse(text)
    except Exception:
        return make_error(
            error_kind="invalid_url",
            message="That doesn't look like a valid URL.",
            source_url=raw,
        )

    adapter = detect_source(text)
    if adapter is None:
        supported = ", ".join(SUPPORTED_SOURCES)
        return make_error(
            error_kind="unsupported_site",
            message=f"That site isn't supported yet. Supported: {supported}.",
            source_url=raw,
        )

    deck_id = adapter.extract_deck_id(parsed)
    if not deck_id:
        return make_error(
            error_kind="invalid_url",
            message=f"Couldn't find a deck id in that {adapter.NAME} URL.",
            source=adapter.NAME,
            source_url=raw,
        )

    result = adapter.import_deck(deck_id, timeout=timeout, fetcher=fetcher)
    if result is None:
        return make_error(
            error_kind="bad_response",
            message=f"The {adapter.NAME} adapter returned no result.",
            source=adapter.NAME,
            source_url=raw,
        )
    # Preserve the original URL for downstream consumers (UI / save flow).
    result.source_url = raw
    return result
