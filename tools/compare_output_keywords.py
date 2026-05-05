"""Simple keyword comparison helper for monolith vs modular output folders.

Usage:
    python tools/compare_output_keywords.py path/to/old/output path/to/new/output

This does not prove full parity. It helps spot missing major sections or concepts.
"""

from __future__ import annotations

import sys
from pathlib import Path

KEYWORDS = [
    "Commander",
    "Color Identity",
    "Deck Size",
    "Legality",
    "Primary Strategy",
    "Secondary Strategy",
    "Bracket",
    "Required Cuts",
    "Optional",
    "Protected",
    "Replacement",
    "Prompt",
    "User Intent",
]


def read_all_markdown(folder: Path) -> str:
    parts = []
    for path in sorted(folder.rglob("*.md")):
        try:
            parts.append(f"\n\n--- FILE: {path.name} ---\n")
            parts.append(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            pass
    return "\n".join(parts)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("Usage: python tools/compare_output_keywords.py OLD_OUTPUT_FOLDER NEW_OUTPUT_FOLDER")
        return 2

    old_folder = Path(argv[1])
    new_folder = Path(argv[2])
    if not old_folder.exists() or not new_folder.exists():
        print("Both folders must exist.")
        return 2

    old_text = read_all_markdown(old_folder)
    new_text = read_all_markdown(new_folder)

    print("Keyword presence comparison")
    print("===========================")
    for keyword in KEYWORDS:
        old_has = keyword.lower() in old_text.lower()
        new_has = keyword.lower() in new_text.lower()
        status = "OK" if old_has == new_has or new_has else "CHECK"
        print(f"{status:5} {keyword:24} old={old_has!s:5} new={new_has!s:5}")

    print()
    print("Markdown file counts:")
    print(f"- Old: {len(list(old_folder.rglob('*.md')))}")
    print(f"- New: {len(list(new_folder.rglob('*.md')))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
