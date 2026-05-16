from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()

REQUIRED = [
    ("main.py", "Backend CLI entry point"),
    ("ui", "Desktop UI package"),
    ("combo_awareness", "Combo Awareness package"),
    ("Decklists", "Example/test decklists"),
]

IMPORTANT = [
    ("data", "Data folder"),
    ("collection", "Collection folder for collection-aware tests"),
    ("data/commander_spellbook/combo_index.json", "Strict Combo Awareness index"),
    ("data/commander_spellbook/combo_index_parity.json", "Parity/debug combo index"),
    ("data/combo.json", "Raw Commander Spellbook data; only needed for rebuilding indexes"),
]

SENSITIVE_OR_HUGE = [
    ("data/combo.json", "Large raw combo data; usually omit from Git, include in ZIP only if rebuilding indexes is expected"),
    ("data/commander_spellbook/combo_index.json", "Large generated index; required for pickup-and-go Combo Awareness"),
    ("data/commander_spellbook/combo_index_parity.json", "Large generated parity index; optional unless Dev-Facing parity checks are desired"),
]


def check(path_text: str) -> bool:
    return (ROOT / path_text).exists()


def main() -> int:
    print("v0.8.10.1-alpha — Alpha Handoff Package Audit")
    print("=" * 56)
    print(f"Project root: {ROOT}")
    print()

    missing_required = []
    print("Required runtime files")
    print("----------------------")
    for path, note in REQUIRED:
        ok = check(path)
        print(f"{'PASS' if ok else 'FAIL'} — {path} — {note}")
        if not ok:
            missing_required.append(path)
    print()

    print("Important pickup-and-go files")
    print("-----------------------------")
    for path, note in IMPORTANT:
        ok = check(path)
        print(f"{'PASS' if ok else 'WARN'} — {path} — {note}")
    print()

    print("Large/local data reminder")
    print("-------------------------")
    for path, note in SENSITIVE_OR_HUGE:
        status = "present" if check(path) else "not present"
        print(f"- {path}: {status}. {note}")
    print()

    print("Interpretation")
    print("--------------")
    if missing_required:
        print("FAIL — Required files are missing. Do not ship this alpha ZIP yet.")
        return 1
    print("PASS — Required runtime files are present.")
    print("Review WARN items manually before zipping for testers.")
    print("Remember: generated combo indexes may be gitignored but still needed inside the alpha ZIP for pickup-and-go Combo Awareness.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
