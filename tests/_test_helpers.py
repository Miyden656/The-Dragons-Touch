"""Shared helpers for the test scripts. Keep this tiny and dependency-free.

Each test_*.py imports `assert_eq`, `assert_in`, `assert_true`, `report` from
here. Tests print one line per assertion (PASS/FAIL), then a final summary.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Allow `from <module> import ...` to resolve at the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestRun:
    """Tally PASS/FAIL across a single test script and exit with the right code."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.passed = 0
        self.failed = 0
        self.failures: list[str] = []
        print(f"\n=== {name} ===")

    def _ok(self, label: str) -> None:
        self.passed += 1
        print(f"  PASS  {label}")

    def _fail(self, label: str, detail: str = "") -> None:
        self.failed += 1
        msg = f"  FAIL  {label}"
        if detail:
            msg += f"\n          {detail}"
        print(msg)
        self.failures.append(label)

    def eq(self, label: str, actual: Any, expected: Any) -> None:
        if actual == expected:
            self._ok(label)
        else:
            self._fail(label, f"expected={expected!r} actual={actual!r}")

    def in_set(self, label: str, item: Any, container: Any) -> None:
        if item in container:
            self._ok(label)
        else:
            self._fail(label, f"{item!r} not in {container!r}")

    def not_in_set(self, label: str, item: Any, container: Any) -> None:
        if item not in container:
            self._ok(label)
        else:
            self._fail(label, f"{item!r} unexpectedly in {container!r}")

    def true(self, label: str, condition: bool, detail: str = "") -> None:
        if condition:
            self._ok(label)
        else:
            self._fail(label, detail)

    def report_and_exit(self) -> None:
        total = self.passed + self.failed
        status = "PASS" if self.failed == 0 else "FAIL"
        print(f"\n{status}: {self.passed}/{total} assertions for {self.name}")
        if self.failures:
            print(f"  Failed: {self.failures}")
        sys.exit(0 if self.failed == 0 else 1)


def load_scryfall_or_skip() -> dict[str, dict]:
    """Load scryfall_cards.json or print a skip message and exit 0."""
    import json
    path = PROJECT_ROOT / "data" / "scryfall_cards.json"
    if not path.exists():
        print(f"SKIP: {path} not found. Run app data setup first (Settings -> Data Setup -> Download/Update Scryfall).")
        sys.exit(0)
    raw = json.loads(path.read_text(encoding="utf-8"))
    cards = raw if isinstance(raw, list) else raw.get("data", raw.get("cards", list(raw.values())))
    return {(c.get("name") or "").lower(): c for c in cards if isinstance(c, dict)}


def load_combo_index_or_skip() -> dict:
    """Load combo_index.json or print a skip message and exit 0."""
    import json
    path = PROJECT_ROOT / "data" / "commander_spellbook" / "combo_index.json"
    if not path.exists():
        print(f"SKIP: {path} not found. Run app data setup first (Settings -> Data Setup -> Download/Update Combo Data + Build Combo Index).")
        sys.exit(0)
    return json.loads(path.read_text(encoding="utf-8"))


def load_owned_collection(scry: dict) -> list[dict]:
    """Parse all collection/*.txt files into the build_full_100_card_draft format."""
    import re
    owned: list[dict] = []
    seen: set[str] = set()
    coll_dir = PROJECT_ROOT / "collection"
    if not coll_dir.exists():
        return owned
    for fp in coll_dir.glob("*.txt"):
        for line in fp.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            m = re.match(r"^(\d+)\s+(.+?)\s+\([A-Z0-9]+\)\s+\S+(?:\s+\*F\*)?\s*$", line)
            if m:
                qty, name = int(m.group(1)), m.group(2).strip()
            else:
                m = re.match(r"^(\d+)\s+(.+)$", line)
                if not m:
                    continue
                qty, name = int(m.group(1)), m.group(2).strip()
            if name.lower() not in scry or name in seen:
                continue
            seen.add(name)
            card = scry[name.lower()]
            owned.append({
                "name": name,
                "owned_quantity": qty,
                "source_files": [fp.name],
                "oracle_text": card.get("oracle_text") or "",
                "type_line": card.get("type_line") or "",
            })
    return owned
