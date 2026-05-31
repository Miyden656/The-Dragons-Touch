"""End-to-end CLI for the URL importer (no GUI needed).

Examples (from project root):

    py -3 -m deck_import.cli --url https://www.moxfield.com/decks/<id>
    py -3 -m deck_import.cli --url https://archidekt.com/decks/<id> --print-text
    py -3 -m deck_import.cli --url https://www.mtggoldfish.com/deck/<id> --save Decklists/

Always exits 0; ok/fail is in the printed summary so this is friendly
for downstream callers (and matches the rest of the headless tooling).
"""

import argparse
import sys
from pathlib import Path

from deck_import import SUPPORTED_SOURCES, import_from_url


def _force_utf8_stdout():
    # Match ai/cli posture so the `·` / smart-quote characters in deck names
    # don't mojibake on a cp1252 Windows console.
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass


def _sanitize_filename(name: str) -> str:
    cleaned = []
    for ch in (name or "").strip():
        if ch.isalnum() or ch in " _-.,()'":
            cleaned.append(ch)
        else:
            cleaned.append("_")
    out = "".join(cleaned).strip().rstrip(".")
    return out or "imported_deck"


def main(argv=None) -> int:
    _force_utf8_stdout()
    parser = argparse.ArgumentParser(
        prog="deck_import",
        description="Import a Commander decklist from a supported URL.",
    )
    parser.add_argument("--url", required=True, help="Deck URL")
    parser.add_argument("--timeout", type=float, default=None,
                        help="Per-request timeout seconds (default 20)")
    parser.add_argument("--print-text", action="store_true",
                        help="Print the normalized decklist text after the summary")
    parser.add_argument("--save", default=None,
                        help="Folder to save the imported decklist to (next-number naming "
                             "is NOT applied; this writes to <folder>/<deck_name>.txt). "
                             "Use the app's Save button for next-number naming.")
    args = parser.parse_args(argv)

    result = import_from_url(args.url, timeout=args.timeout)

    print()
    print(f"Supported sources: {', '.join(SUPPORTED_SOURCES)}")
    print(f"URL              : {args.url}")
    print(f"Detected source  : {result.source or '(none)'}")
    print(f"Deck id          : {result.deck_id or '(none)'}")
    print(f"OK               : {result.ok}")

    if not result.ok:
        print(f"Error kind       : {result.error_kind}")
        print(f"Message          : {result.message}")
        return 0

    print(f"Deck name        : {result.deck_name}")
    print(f"Commander        : {result.commander or '(not detected)'}")
    if len(result.commanders) > 1:
        print(f"Commanders       : {', '.join(result.commanders)}")
    print(f"Total cards      : {result.card_count()}")
    print(f"Mainboard cards  : {result.mainboard_count()}")
    print(f"Message          : {result.message}")

    if args.print_text:
        print()
        print("--- Normalized decklist (Paste-tab format) ---")
        print(result.decklist_text)
        print("--- End of decklist ---")

    if args.save:
        folder = Path(args.save)
        folder.mkdir(parents=True, exist_ok=True)
        out = folder / f"{_sanitize_filename(result.deck_name)}.txt"
        out.write_text(result.decklist_text, encoding="utf-8")
        print()
        print(f"Saved -> {out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
