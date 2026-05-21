#!/usr/bin/env python3
"""Verify v0.12.6.1 clean handoff staging/scope hotfix."""
from pathlib import Path
import ast

REQUIRED = {
    "tools/create_source_run_beta_staging.py": [
        "Clean Source-Run Beta Staging Helper",
        "ACTIVE_FOLDERS",
        "FORBIDDEN_TOP_LEVEL_NAMES",
        "--overwrite",
        "verify_source_run_beta_package.py",
    ],
    "tools/verify_source_run_beta_package.py": [
        "Source-Run Beta Package Verifier",
        "Run this from the clean handoff/staging folder",
        "FORBIDDEN_TOP_LEVEL_NAMES",
        "create_source_run_beta_staging.py",
        "RESULT",
    ],
}


def main() -> int:
    print("v0.12.6.1 — Clean Handoff Staging / Verifier Scope Hotfix Verifier")
    print("==================================================================")
    blockers = 0
    for rel, phrases in REQUIRED.items():
        path = Path(rel)
        if not path.is_file():
            print(f"FAIL — Missing file: {rel}")
            blockers += 1
            continue
        print(f"PASS — {rel} exists")
        text = path.read_text(encoding="utf-8", errors="replace")
        for phrase in phrases:
            if phrase in text:
                print(f"PASS — {rel} contains required phrase: {phrase}")
            else:
                print(f"FAIL — {rel} missing required phrase: {phrase}")
                blockers += 1
        try:
            ast.parse(text)
            print(f"PASS — {rel} parses")
        except SyntaxError as exc:
            print(f"FAIL — {rel} does not parse: {exc}")
            blockers += 1
    print()
    if blockers:
        print(f"RESULT — FAIL ({blockers} blocker issue(s))")
        return 1
    print("RESULT — PASS")
    print("v0.12.6.1 hotfix is present and lockable.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
