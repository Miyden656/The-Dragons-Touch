"""URL-based decklist importer for The Dragon's Touch.

Fetches a deck from a supported deckbuilding site (Moxfield, Archidekt,
MTGGoldfish) and normalizes it into the plain-text format the engine
already consumes from the Paste Decklist tab. Stdlib-only, never raises
on network/parse failures — returns a typed DeckImportResult with a
machine-readable error_kind.
"""

from deck_import.types import (
    DeckImportResult,
    ImportedCard,
    ERROR_KINDS,
)
from deck_import.url_importer import (
    import_from_url,
    detect_source,
    SUPPORTED_SOURCES,
)

__all__ = [
    "DeckImportResult",
    "ImportedCard",
    "ERROR_KINDS",
    "import_from_url",
    "detect_source",
    "SUPPORTED_SOURCES",
]
