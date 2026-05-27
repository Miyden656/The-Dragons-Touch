"""Run every test_*.py in this directory, report combined pass/fail.

From project root:
    py -3 tests/run_all.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent


def main() -> int:
    test_files = sorted(TESTS_DIR.glob("test_*.py"))
    if not test_files:
        print("No tests found.")
        return 0
    print(f"Running {len(test_files)} test scripts from {TESTS_DIR}...\n")
    failures: list[str] = []
    for f in test_files:
        rc = subprocess.call([sys.executable, str(f)], cwd=str(PROJECT_ROOT))
        if rc != 0:
            failures.append(f.name)
    print()
    print("=" * 60)
    if failures:
        print(f"FAIL: {len(failures)}/{len(test_files)} test scripts had failures:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"PASS: all {len(test_files)} test scripts succeeded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
