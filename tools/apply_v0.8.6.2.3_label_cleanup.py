#!/usr/bin/env python3
"""
v0.8.6.2.3-dev — Module Split Version Label Cleanup

Purpose:
- Update stale v0.8.6.2-dev / v0.8.6.2.2-dev labels after the module split hotfixes.
- No parser logic changes.
- No matcher logic changes.
- No report wording changes except version labels.
- No main.py, UI, API, or normal report integration.

Run from the project root:
    py tools/apply_v0.8.6.2.3_label_cleanup.py
"""

from __future__ import annotations

from pathlib import Path

TARGET_VERSION = "v0.8.6.2.3-dev"
OLD_VERSIONS = [
    "v0.8.6.2-dev",
    "v0.8.6.2.1-dev",
    "v0.8.6.2.2-dev",
]

FILES_TO_UPDATE = [
    Path("tools/test_combo_matcher.py"),
    Path("combo_awareness/reporting.py"),
    Path("combo_awareness/combo_matcher.py"),
]

# Output filenames are intentionally updated so new test artifacts do not overwrite
# the v0.8.6.2.2 verification files unless the user manually chooses a path.
FILENAME_REPLACEMENTS = {
    "combo_matcher_test_summary_v0.8.6.2-dev.md": "combo_matcher_test_summary_v0.8.6.2.3-dev.md",
    "combo_matcher_reconciliation_v0.8.6.2-dev.md": "combo_matcher_reconciliation_v0.8.6.2.3-dev.md",
    "combo_awareness_breakdown_v0.8.6.2-dev.md": "combo_awareness_breakdown_v0.8.6.2.3-dev.md",
    "combo_matcher_stress_test_v0.8.6.2-dev.md": "combo_matcher_stress_test_v0.8.6.2.3-dev.md",
    "combo_awareness_report_section_v0.8.6.2-dev.md": "combo_awareness_report_section_v0.8.6.2.3-dev.md",
    "combo_index_parity_summary_v0.8.6.2-dev.md": "combo_index_parity_summary_v0.8.6.2.3-dev.md",
    "combo_matcher_test_summary_v0.8.6.2.2-dev.md": "combo_matcher_test_summary_v0.8.6.2.3-dev.md",
    "combo_matcher_reconciliation_v0.8.6.2.2-dev.md": "combo_matcher_reconciliation_v0.8.6.2.3-dev.md",
    "combo_awareness_breakdown_v0.8.6.2.2-dev.md": "combo_awareness_breakdown_v0.8.6.2.3-dev.md",
    "combo_matcher_stress_test_v0.8.6.2.2-dev.md": "combo_matcher_stress_test_v0.8.6.2.3-dev.md",
    "combo_awareness_report_section_v0.8.6.2.2-dev.md": "combo_awareness_report_section_v0.8.6.2.3-dev.md",
    "combo_index_parity_summary_v0.8.6.2.2-dev.md": "combo_index_parity_summary_v0.8.6.2.3-dev.md",
}


def update_file(path: Path) -> tuple[bool, int]:
    if not path.exists():
        return False, 0

    text = path.read_text(encoding="utf-8")
    original = text
    replacements = 0

    for old_version in OLD_VERSIONS:
        count = text.count(old_version)
        if count:
            text = text.replace(old_version, TARGET_VERSION)
            replacements += count

    for old_name, new_name in FILENAME_REPLACEMENTS.items():
        count = text.count(old_name)
        if count:
            text = text.replace(old_name, new_name)
            replacements += count

    if text != original:
        path.write_text(text, encoding="utf-8")
        return True, replacements
    return False, replacements


def main() -> int:
    print("v0.8.6.2.3-dev — Module Split Version Label Cleanup")
    print("====================================================")
    print("Scope: label/path cleanup only. No matcher/parser/report logic changes.\n")

    total_replacements = 0
    changed_files: list[str] = []
    missing_files: list[str] = []

    for path in FILES_TO_UPDATE:
        changed, replacements = update_file(path)
        if not path.exists():
            missing_files.append(str(path))
            continue
        total_replacements += replacements
        if changed:
            changed_files.append(str(path))
            print(f"Updated {path} ({replacements} replacement(s))")
        else:
            print(f"No stale labels found in {path}")

    if missing_files:
        print("\nMissing optional files:")
        for path in missing_files:
            print(f"- {path}")

    print("\nSummary")
    print("-------")
    print(f"Files changed: {len(changed_files)}")
    print(f"Total replacements: {total_replacements}")
    print("\nDone. No app integration was performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
