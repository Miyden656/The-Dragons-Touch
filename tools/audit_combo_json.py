#!/usr/bin/env python3
"""
v0.8.7.2.1-dev — Commander Spellbook Combo Data Audit Path Cleanup

Purpose:
    Safely inspect the local Commander Spellbook combo data file and produce a
    small human-readable audit report for The Dragon's Touch.

Scope guard:
    - This script is isolated.
    - This script does not import or modify main.py.
    - This script does not connect to the PySide6 UI.
    - This script does not run deck analysis.
    - This script does not call the Commander Spellbook API.
    - This script does not build the combo index yet.
    - This script does not add combo findings to normal reports.

Usage:
    python tools/audit_combo_json.py
    python tools/audit_combo_json.py --combo-json data/combo.json
    python tools/audit_combo_json.py --output docs/combo_data_audit_v0.8.0-dev.md

Notes:
    data/combo.json is large. This script uses only the Python standard library, but
    it does load the local JSON file into memory for this first audit pass.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


DEFAULT_COMBO_JSON_PATHS = [
    Path("data/combo.json"),
]

DEFAULT_OUTPUT_PATH = Path("docs/combo_data_audit_v0.8.7.2.1-dev.md")

INDEX_CANDIDATE_FIELDS = [
    "id",
    "status",
    "uses.card.name",
    "uses.card.oracleId",
    "uses.mustBeCommander",
    "uses.quantity",
    "uses.zoneLocations",
    "requires",
    "produces.feature.name",
    "identity",
    "easyPrerequisites",
    "notablePrerequisites",
    "description",
    "notes",
    "spoiler",
    "bracketTag",
    "legalities.commander",
]

FIELDS_TO_EXCLUDE_FROM_FIRST_INDEX = [
    "prices",
    "card image URI fields",
    "large nested frontend display data",
    "popularity, unless later used for sorting",
    "aliases, unless later needed for card-name normalization",
]


def find_default_combo_json() -> Path | None:
    for candidate in DEFAULT_COMBO_JSON_PATHS:
        if candidate.exists():
            return candidate
    return None


def load_combo_data(combo_json_path: Path) -> dict[str, Any]:
    try:
        with combo_json_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise RuntimeError(f"Combo JSON file not found: {combo_json_path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Combo JSON could not be parsed: {exc}") from exc

    if not isinstance(data, dict):
        raise RuntimeError("Expected top-level data/combo.json structure to be a JSON object.")
    if "variants" not in data:
        raise RuntimeError("Expected data/combo.json to contain a top-level 'variants' key.")
    if not isinstance(data.get("variants"), list):
        raise RuntimeError("Expected data/combo.json 'variants' value to be a list.")

    return data


def as_bool(value: Any) -> bool:
    return bool(value) is True


def top_items(counter: collections.Counter, limit: int = 20) -> list[tuple[Any, int]]:
    return counter.most_common(limit)


def collect_variant_audit(data: dict[str, Any]) -> dict[str, Any]:
    variants = data.get("variants", [])
    aliases = data.get("aliases", {})

    status_counts: collections.Counter[str] = collections.Counter()
    bracket_counts: collections.Counter[str] = collections.Counter()
    identity_counts: collections.Counter[str] = collections.Counter()
    combo_size_counts: collections.Counter[int] = collections.Counter()
    produces_counts: collections.Counter[str] = collections.Counter()
    top_level_field_counts: collections.Counter[str] = collections.Counter()
    use_field_counts: collections.Counter[str] = collections.Counter()
    card_field_counts: collections.Counter[str] = collections.Counter()

    commander_legal_count = 0
    spoiler_count = 0
    must_be_commander_variant_count = 0
    requires_nonempty_count = 0
    produces_nonempty_count = 0
    quantity_gt_one_count = 0
    missing_card_name_count = 0

    sample_variants: list[dict[str, Any]] = []
    non_spoiler_sample_variants: list[dict[str, Any]] = []

    for variant in variants:
        if not isinstance(variant, dict):
            continue

        top_level_field_counts.update(variant.keys())

        status_counts[str(variant.get("status", "<missing>"))] += 1
        bracket_counts[str(variant.get("bracketTag", "<missing>"))] += 1
        identity_counts[str(variant.get("identity", ""))] += 1

        legalities = variant.get("legalities") or {}
        if isinstance(legalities, dict) and legalities.get("commander") is True:
            commander_legal_count += 1

        if variant.get("spoiler") is True:
            spoiler_count += 1

        uses = variant.get("uses") or []
        if isinstance(uses, list):
            combo_size_counts[len(uses)] += 1
            variant_has_must_be_commander = False
            for use in uses:
                if not isinstance(use, dict):
                    continue
                use_field_counts.update(use.keys())
                if use.get("mustBeCommander") is True:
                    variant_has_must_be_commander = True
                if (use.get("quantity") or 1) != 1:
                    quantity_gt_one_count += 1
                card = use.get("card") or {}
                if isinstance(card, dict):
                    card_field_counts.update(card.keys())
                    if not card.get("name"):
                        missing_card_name_count += 1
            if variant_has_must_be_commander:
                must_be_commander_variant_count += 1

        requires = variant.get("requires") or []
        if requires:
            requires_nonempty_count += 1

        produces = variant.get("produces") or []
        if produces:
            produces_nonempty_count += 1
            if isinstance(produces, list):
                for item in produces:
                    if not isinstance(item, dict):
                        continue
                    feature = item.get("feature") or {}
                    if isinstance(feature, dict):
                        name = feature.get("name")
                        if name:
                            produces_counts[str(name)] += 1

        if len(sample_variants) < 3:
            sample_variants.append(make_small_sample_variant(variant))
        if variant.get("spoiler") is not True and len(non_spoiler_sample_variants) < 3:
            non_spoiler_sample_variants.append(make_small_sample_variant(variant))

    return {
        "timestamp": data.get("timestamp"),
        "version": data.get("version"),
        "variant_count": len(variants),
        "aliases_count": len(aliases) if isinstance(aliases, (dict, list)) else "unknown",
        "commander_legal_count": commander_legal_count,
        "spoiler_count": spoiler_count,
        "must_be_commander_variant_count": must_be_commander_variant_count,
        "requires_nonempty_count": requires_nonempty_count,
        "produces_nonempty_count": produces_nonempty_count,
        "quantity_gt_one_count": quantity_gt_one_count,
        "missing_card_name_count": missing_card_name_count,
        "status_counts": status_counts,
        "bracket_counts": bracket_counts,
        "identity_counts": identity_counts,
        "combo_size_counts": combo_size_counts,
        "produces_counts": produces_counts,
        "top_level_fields": sorted(top_level_field_counts.keys()),
        "use_fields": sorted(use_field_counts.keys()),
        "card_fields": sorted(card_field_counts.keys()),
        "sample_variants": sample_variants,
        "non_spoiler_sample_variants": non_spoiler_sample_variants,
    }


def make_small_sample_variant(variant: dict[str, Any]) -> dict[str, Any]:
    uses = variant.get("uses") or []
    cards = []
    must_be_commander = []

    if isinstance(uses, list):
        for use in uses:
            if not isinstance(use, dict):
                continue
            card = use.get("card") or {}
            card_name = card.get("name") if isinstance(card, dict) else None
            if card_name:
                cards.append(card_name)
                if use.get("mustBeCommander") is True:
                    must_be_commander.append(card_name)

    produces = []
    raw_produces = variant.get("produces") or []
    if isinstance(raw_produces, list):
        for item in raw_produces:
            if not isinstance(item, dict):
                continue
            feature = item.get("feature") or {}
            if isinstance(feature, dict) and feature.get("name"):
                produces.append(feature["name"])

    return {
        "id": variant.get("id"),
        "status": variant.get("status"),
        "cards": cards,
        "must_be_commander": must_be_commander,
        "identity": variant.get("identity"),
        "produces": produces,
        "spoiler": variant.get("spoiler"),
        "bracketTag": variant.get("bracketTag"),
        "commander_legal": (variant.get("legalities") or {}).get("commander"),
        "description": variant.get("description"),
        "easyPrerequisites": variant.get("easyPrerequisites"),
        "notablePrerequisites": variant.get("notablePrerequisites"),
    }


def markdown_counter_table(counter: collections.Counter, label: str, limit: int = 20) -> str:
    lines = [f"### {label}", "", "| Value | Count |", "|---|---:|"]
    for value, count in top_items(counter, limit=limit):
        display = str(value) if str(value) else "<colorless/empty>"
        lines.append(f"| {display} | {count} |")
    lines.append("")
    return "\n".join(lines)


def fenced_json(value: Any) -> str:
    return "```json\n" + json.dumps(value, indent=2, ensure_ascii=False) + "\n```"


def build_markdown_report(combo_json_path: Path, audit: dict[str, Any]) -> str:
    variant_count = audit["variant_count"] or 0
    commander_legal_pct = (audit["commander_legal_count"] / variant_count * 100) if variant_count else 0
    spoiler_pct = (audit["spoiler_count"] / variant_count * 100) if variant_count else 0
    must_commander_pct = (audit["must_be_commander_variant_count"] / variant_count * 100) if variant_count else 0

    file_size_mb = combo_json_path.stat().st_size / (1024 * 1024)

    lines = [
        "# v0.8.7.2.1-dev — Commander Spellbook Combo Data Audit Path Cleanup",
        "",
        "## Scope Guard",
        "",
        "This audit is isolated research for The Dragon's Touch v0.8 Commander Spellbook / Combo Awareness.",
        "",
        "- It does not modify the locked v0.7.22 alpha tester ZIP.",
        "- It does not change `main.py`.",
        "- It does not connect to the PySide6 UI.",
        "- It does not add combo findings to reports yet.",
        "- It does not call the Commander Spellbook API.",
        "- It only inspects local `data/combo.json`.",
        "",
        "## Source File",
        "",
        f"- Path: `{combo_json_path}`",
        f"- Size: {file_size_mb:.1f} MB",
        f"- Audit generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Top-Level Metadata",
        "",
        f"- Combo data version: `{audit['version']}`",
        f"- Combo data timestamp: `{audit['timestamp']}`",
        f"- Total variants: {audit['variant_count']:,}",
        f"- Aliases entries: {audit['aliases_count']}",
        "",
        "## Key Counts",
        "",
        f"- Commander-legal variants: {audit['commander_legal_count']:,} ({commander_legal_pct:.1f}%)",
        f"- Spoiler-tagged variants: {audit['spoiler_count']:,} ({spoiler_pct:.1f}%)",
        f"- Variants with at least one must-be-commander card: {audit['must_be_commander_variant_count']:,} ({must_commander_pct:.1f}%)",
        f"- Variants with non-empty `requires`: {audit['requires_nonempty_count']:,}",
        f"- Variants with non-empty `produces`: {audit['produces_nonempty_count']:,}",
        f"- Use entries with quantity other than 1: {audit['quantity_gt_one_count']:,}",
        f"- Use entries missing card names: {audit['missing_card_name_count']:,}",
        "",
        markdown_counter_table(audit["status_counts"], "Status Distribution", limit=20),
        markdown_counter_table(audit["bracket_counts"], "Bracket Tag Distribution", limit=20),
        markdown_counter_table(audit["combo_size_counts"], "Combo Size Distribution Based on uses Count", limit=30),
        markdown_counter_table(audit["identity_counts"], "Top Color Identity Values", limit=40),
        markdown_counter_table(audit["produces_counts"], "Top Produced Features", limit=40),
        "## Fields Observed",
        "",
        "### Variant Top-Level Fields",
        "",
        fenced_json(audit["top_level_fields"]),
        "",
        "### `uses` Entry Fields",
        "",
        fenced_json(audit["use_fields"]),
        "",
        "### Nested `card` Fields",
        "",
        fenced_json(audit["card_fields"]),
        "",
        "## First Index Candidate Fields",
        "",
        "These are the fields that look useful for a future compact `combo_index.json`.",
        "",
    ]

    for field in INDEX_CANDIDATE_FIELDS:
        lines.append(f"- `{field}`")

    lines.extend([
        "",
        "## Fields to Exclude From First Index",
        "",
    ])

    for field in FIELDS_TO_EXCLUDE_FROM_FIRST_INDEX:
        lines.append(f"- {field}")

    lines.extend([
        "",
        "## Sample Variants",
        "",
        "Small samples only. Card images, prices, and large nested card payloads are intentionally omitted.",
        "",
        fenced_json(audit["sample_variants"]),
        "",
        "## Non-Spoiler Sample Variants",
        "",
        fenced_json(audit["non_spoiler_sample_variants"]),
        "",
        "## v0.8.1 Recommendation",
        "",
        "Proceed to `v0.8.1-dev — Local Combo Index Builder` only after reviewing this audit.",
        "",
        "The first index should be local/offline and should remove images, prices, and large frontend-only card data.",
        "",
        "Recommended next generated file:",
        "",
        "```text",
        "data/commander_spellbook/combo_index.json",
        "```",
        "",
        "Recommended next script:",
        "",
        "```text",
        "tools/build_combo_index.py",
        "```",
        "",
        "Do not connect this to the main report, UI, or normal deck analysis yet.",
        "",
    ])

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit local Commander Spellbook combo data from data/combo.json.")
    parser.add_argument(
        "--combo-json",
        type=Path,
        default=None,
        help="Path to local Commander Spellbook combo JSON. Defaults to data/combo.json.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=f"Markdown audit output path. Default: {DEFAULT_OUTPUT_PATH}",
    )
    parser.add_argument(
        "--no-output-file",
        action="store_true",
        help="Print summary only and do not write the markdown audit file.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    combo_json_path = args.combo_json or find_default_combo_json()
    if combo_json_path is None:
        print("ERROR: Could not find data/combo.json.", file=sys.stderr)
        print("Expected one of:", file=sys.stderr)
        for path in DEFAULT_COMBO_JSON_PATHS:
            print(f"  - {path}", file=sys.stderr)
        return 2

    print("v0.8.7.2.1-dev — Commander Spellbook Combo Data Audit Path Cleanup")
    print("===================================================")
    print(f"Combo JSON: {combo_json_path}")
    print("Loading local JSON data. No API calls will be made...")

    try:
        data = load_combo_data(combo_json_path)
        audit = collect_variant_audit(data)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print()
    print("Audit Summary")
    print("-------------")
    print(f"Version: {audit['version']}")
    print(f"Timestamp: {audit['timestamp']}")
    print(f"Total variants: {audit['variant_count']:,}")
    print(f"Commander-legal variants: {audit['commander_legal_count']:,}")
    print(f"Spoiler-tagged variants: {audit['spoiler_count']:,}")
    print(f"mustBeCommander variants: {audit['must_be_commander_variant_count']:,}")
    print(f"Top status values: {top_items(audit['status_counts'], 5)}")
    print(f"Top bracket tags: {top_items(audit['bracket_counts'], 10)}")
    print(f"Top combo sizes: {top_items(audit['combo_size_counts'], 10)}")

    if not args.no_output_file:
        report = build_markdown_report(combo_json_path, audit)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print()
        print(f"Wrote audit report: {args.output}")

    print()
    print("Done. No app integration was performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
