"""Per-site adapters. Each module exposes:

    NAME: str                           # canonical short name, e.g. "moxfield"
    DOMAINS: tuple[str, ...]            # hostnames this adapter claims
    extract_deck_id(parsed_url) -> str  # returns "" if URL isn't a deck page
    import_deck(deck_id, *, timeout=None, fetcher=None) -> DeckImportResult

`fetcher` is injectable for tests (default: deck_import.http.fetch).
"""
