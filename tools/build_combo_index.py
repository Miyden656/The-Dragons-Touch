#!/usr/bin/env python3
"""
v0.8.7.2.1-dev — Local Combo Index Builder Data Path Cleanup for The Dragon's Touch.

Purpose:
- Read local Commander Spellbook combo data from data/combo.json.
- Build a smaller local combo_index.json for future offline combo awareness.
- Strip out card images, prices, and large nested display data.

Scope guard:
- No API calls.
- No main.py integration.
- No UI integration.
- No report integration.
- No deck matching yet.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RAW_COMBO_JSON_PATH = Path("data/combo.json")
OUTPUT_INDEX_PATH = Path("data/commander_spellbook/combo_index.json")
SUMMARY_OUTPUT_PATH = Path("docs/combo_index_summary_v0.8.7.2.1-dev.md")

COMMANDER_LEGAL_ONLY = True
KEEP_SPOILER_TAGGED_IN_INDEX = True
ALLOWED_STATUS_VALUES = {"OK"}
MAX_TEXT_FIELD_CHARS = 700


def normalize_card_name(name: str) -> str:
    return " ".join(str(name).strip().casefold().split())


def truncate_text(value: Any, max_chars: int = MAX_TEXT_FIELD_CHARS) -> str:
    text = "" if value is None else str(value).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 15].rstrip() + " ... [truncated]"


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: Any, *, pretty: bool = False) -> None:
    ensure_parent_dir(path)
    with path.open("w", encoding="utf-8") as handle:
        if pretty:
            json.dump(data, handle, indent=2, ensure_ascii=False)
        else:
            json.dump(data, handle, ensure_ascii=False, separators=(",", ":"))


def compact_card_record(use_entry: dict[str, Any]) -> dict[str, Any] | None:
    card = use_entry.get("card") or {}
    name = card.get("name")
    if not name:
        return None

    record: dict[str, Any] = {
        "name": name,
        "n": normalize_card_name(name),
    }

    # Keep only compact identifiers and rules-relevant fields.
    if card.get("id") is not None:
        record["card_id"] = card.get("id")
    if card.get("oracleId"):
        record["oracle_id"] = card.get("oracleId")
    if use_entry.get("quantity", 1) != 1:
        record["quantity"] = use_entry.get("quantity")
    if use_entry.get("mustBeCommander", False):
        record["must_be_commander"] = True
    if card.get("spoiler", False):
        record["card_spoiler"] = True

    zones = use_entry.get("zoneLocations") or []
    if zones:
        record["zones"] = zones

    # Preserve unusual state requirements, but omit empty strings.
    state_map = {
        "battlefield": use_entry.get("battlefieldCardState", ""),
        "exile": use_entry.get("exileCardState", ""),
        "library": use_entry.get("libraryCardState", ""),
        "graveyard": use_entry.get("graveyardCardState", ""),
    }
    states = {key: truncate_text(value, 250) for key, value in state_map.items() if str(value).strip()}
    if states:
        record["states"] = states

    return record


def compact_template_requirement(require_entry: dict[str, Any]) -> dict[str, Any]:
    template = require_entry.get("template") or {}
    record: dict[str, Any] = {}
    if template.get("id") is not None:
        record["template_id"] = template.get("id")
    if template.get("name"):
        record["name"] = template.get("name")
    if template.get("scryfallQuery"):
        record["scryfall_query"] = truncate_text(template.get("scryfallQuery"), 300)
    if require_entry.get("quantity", 1) != 1:
        record["quantity"] = require_entry.get("quantity")
    if require_entry.get("mustBeCommander", False):
        record["must_be_commander"] = True
    zones = require_entry.get("zoneLocations") or []
    if zones:
        record["zones"] = zones
    state_map = {
        "battlefield": require_entry.get("battlefieldCardState", ""),
        "exile": require_entry.get("exileCardState", ""),
        "library": require_entry.get("libraryCardState", ""),
        "graveyard": require_entry.get("graveyardCardState", ""),
    }
    states = {key: truncate_text(value, 250) for key, value in state_map.items() if str(value).strip()}
    if states:
        record["states"] = states
    return record


def compact_produce_name(produce_entry: dict[str, Any]) -> str:
    feature = produce_entry.get("feature") or {}
    return feature.get("name") or ""


def is_commander_legal(variant: dict[str, Any]) -> bool:
    legalities = variant.get("legalities") or {}
    return bool(legalities.get("commander", False))


@dataclass
class BuildStats:
    source_variants: int = 0
    indexed_variants: int = 0
    skipped_non_ok_status: int = 0
    skipped_non_commander_legal: int = 0
    skipped_spoiler: int = 0
    skipped_missing_card_names: int = 0
    indexed_spoiler_tagged: int = 0
    indexed_must_be_commander: int = 0
    indexed_with_template_requirements: int = 0


def build_combo_index(raw_data: dict[str, Any], *, commander_legal_only: bool = COMMANDER_LEGAL_ONLY) -> tuple[dict[str, Any], BuildStats, dict[str, Counter]]:
    variants = raw_data.get("variants") or []
    stats = BuildStats(source_variants=len(variants))
    indexed_combos: list[dict[str, Any]] = []
    counters = {
        "status": Counter(),
        "bracket_tag": Counter(),
        "combo_size": Counter(),
        "produces": Counter(),
        "identity": Counter(),
    }

    for variant in variants:
        status = variant.get("status") or ""
        counters["status"][status] += 1

        if status not in ALLOWED_STATUS_VALUES:
            stats.skipped_non_ok_status += 1
            continue
        if commander_legal_only and not is_commander_legal(variant):
            stats.skipped_non_commander_legal += 1
            continue

        variant_spoiler = bool(variant.get("spoiler", False))
        if variant_spoiler and not KEEP_SPOILER_TAGGED_IN_INDEX:
            stats.skipped_spoiler += 1
            continue

        cards = []
        for use_entry in variant.get("uses") or []:
            card_record = compact_card_record(use_entry)
            if card_record:
                cards.append(card_record)
        if not cards:
            stats.skipped_missing_card_names += 1
            continue

        card_names = [card["name"] for card in cards]
        normalized_card_names = [card["n"] for card in cards]
        must_be_commander_card_names = [card["name"] for card in cards if card.get("must_be_commander")]

        template_requirements = [
            compact_template_requirement(require_entry)
            for require_entry in (variant.get("requires") or [])
        ]
        template_requirements = [entry for entry in template_requirements if entry]

        produce_names = [
            name for name in (compact_produce_name(entry) for entry in (variant.get("produces") or [])) if name
        ]

        combo = {
            "id": variant.get("id"),
            "status": status,
            "bracket_tag": variant.get("bracketTag") or "",
            "spoiler": variant_spoiler,
            "identity": variant.get("identity") or "",
            "card_count": len(card_names),
            "card_names": card_names,
            "normalized_card_names": normalized_card_names,
            "cards": cards,
            "must_be_commander_card_names": must_be_commander_card_names,
            "has_must_be_commander": bool(must_be_commander_card_names),
            "template_requirements": template_requirements,
            "has_template_requirements": bool(template_requirements),
            "produce_names": produce_names,
            "mana_needed": variant.get("manaNeeded") or "",
            "mana_value_needed": variant.get("manaValueNeeded") or 0,
            "easy_prerequisites": truncate_text(variant.get("easyPrerequisites", "")),
            "notable_prerequisites": truncate_text(variant.get("notablePrerequisites", "")),
            "description": truncate_text(variant.get("description", "")),
        }

        if variant.get("notes"):
            combo["notes"] = truncate_text(variant.get("notes"), 400)
        if variant.get("variantCount") is not None:
            combo["variant_count"] = variant.get("variantCount")

        indexed_combos.append(combo)
        stats.indexed_variants += 1
        if variant_spoiler:
            stats.indexed_spoiler_tagged += 1
        if must_be_commander_card_names:
            stats.indexed_must_be_commander += 1
        if template_requirements:
            stats.indexed_with_template_requirements += 1

        counters["bracket_tag"][combo["bracket_tag"]] += 1
        counters["combo_size"][combo["card_count"]] += 1
        counters["identity"][combo["identity"]] += 1
        for produce_name in produce_names:
            counters["produces"][produce_name] += 1

    index = {
        "metadata": {
            "index_schema_version": "0.8.2.3-dev",
            "source": "Commander Spellbook Combo.json",
            "source_version": raw_data.get("version"),
            "source_timestamp": raw_data.get("timestamp"),
            "built_at_utc": datetime.now(timezone.utc).isoformat(),
            "commander_legal_only": commander_legal_only,
            "spoiler_tagged_kept_in_index": KEEP_SPOILER_TAGGED_IN_INDEX,
            "allowed_status_values": sorted(ALLOWED_STATUS_VALUES),
            "stats": stats.__dict__,
            "notes": [
                "Offline local index for future combo awareness.",
                "No API calls are made by this builder.",
                "Card images, prices, and bulky frontend display fields are stripped.",
                "Spoiler-tagged combos are marked for future hide-by-default behavior.",
                "Template requirements are metadata and are not named missing cards.",
            ],
        },
        "combos": indexed_combos,
    }
    return index, stats, counters


def write_summary(path: Path, index_path: Path, stats: BuildStats, counters: dict[str, Counter], source_version: str, source_timestamp: str) -> None:
    ensure_parent_dir(path)
    lines = [
        "# v0.8.7.2.1-dev — Local Combo Index Builder with Data Path Cleanup Summary",
        "",
        "## Scope Guard",
        "",
        "- No API calls were made.",
        "- No app integration was performed.",
        "- `main.py` was not changed.",
        "- UI and report generation were not changed.",
        "- This only builds a compact local combo index from `data/combo.json`.",
        "",
        "## Source Data",
        "",
        f"- Source version: {source_version}",
        f"- Source timestamp: {source_timestamp}",
        f"- Source variants: {stats.source_variants:,}",
        "",
        "## Index Output",
        "",
        f"- Index path: `{index_path}`",
        f"- Indexed variants: {stats.indexed_variants:,}",
        f"- Skipped non-OK status: {stats.skipped_non_ok_status:,}",
        f"- Skipped non-Commander-legal: {stats.skipped_non_commander_legal:,}",
        f"- Skipped spoiler-tagged: {stats.skipped_spoiler:,}",
        f"- Skipped missing card names: {stats.skipped_missing_card_names:,}",
        f"- Spoiler-tagged indexed and marked: {stats.indexed_spoiler_tagged:,}",
        f"- mustBeCommander indexed and marked: {stats.indexed_must_be_commander:,}",
        f"- Combos with template requirements indexed and marked: {stats.indexed_with_template_requirements:,}",
        "",
        "## Top Bracket Tags in Index",
        "",
    ]
    for tag, count in counters["bracket_tag"].most_common(12):
        lines.append(f"- {tag or '(blank)'}: {count:,}")

    lines.extend(["", "## Combo Size Distribution in Index", ""])
    for size, count in sorted(counters["combo_size"].items()):
        lines.append(f"- {size} cards: {count:,}")

    lines.extend(["", "## Top Produced Results in Index", ""])
    for name, count in counters["produces"].most_common(20):
        lines.append(f"- {name}: {count:,}")

    lines.extend([
        "",
        "## Future Use",
        "",
        "This index is meant for later v0.8 combo awareness work:",
        "",
        "1. Detect infinite combos already present in a deck.",
        "2. Detect one-card-away potential infinite combos.",
        "3. Hide spoiler-tagged combos by default at match/report time.",
        "4. Respect commander color identity and must-be-commander rules at match time.",
        "5. Cross-check missing one-card combo pieces against collection files later.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a compact local Commander Spellbook combo index.")
    parser.add_argument("--input", default=str(RAW_COMBO_JSON_PATH), help="Path to local Commander Spellbook combo JSON. Defaults to data/combo.json")
    parser.add_argument("--output", default=str(OUTPUT_INDEX_PATH), help="Path to write combo_index.json")
    parser.add_argument("--summary", default=str(SUMMARY_OUTPUT_PATH), help="Path to write markdown summary")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print output JSON. Larger file, easier to inspect.")
    parser.add_argument(
        "--include-non-commander-legal",
        action="store_true",
        help="Validation/parity mode: include OK variants even when Commander legality is false. Use for comparing against external tools only.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    summary_path = Path(args.summary)

    print("v0.8.7.2.1-dev — Local Combo Index Builder with Data Path Cleanup")
    print("=========================================================")
    print(f"Input Combo JSON: {input_path}")
    print(f"Output index: {output_path}")
    print("Loading local JSON data. No API calls will be made...")

    if not input_path.exists():
        print("\nERROR: data/combo.json was not found.")
        print(f"Expected path: {input_path}")
        return 2

    try:
        with input_path.open("r", encoding="utf-8") as handle:
            raw_data = json.load(handle)
    except json.JSONDecodeError as exc:
        print("\nERROR: data/combo.json could not be parsed as JSON.")
        print(str(exc))
        return 3
    except OSError as exc:
        print("\nERROR: data/combo.json could not be read.")
        print(str(exc))
        return 4

    source_version = raw_data.get("version", "unknown")
    source_timestamp = raw_data.get("timestamp", "unknown")

    commander_legal_only = not args.include_non_commander_legal
    if commander_legal_only:
        print("Building compact strict combo index...")
    else:
        print("Building compact validation/parity combo index including non-Commander-legal OK variants...")
    index, stats, counters = build_combo_index(raw_data, commander_legal_only=commander_legal_only)

    print("Writing combo index...")
    write_json(output_path, index, pretty=args.pretty)
    write_summary(summary_path, output_path, stats, counters, source_version, source_timestamp)

    index_size_mb = output_path.stat().st_size / (1024 * 1024) if output_path.exists() else 0.0

    print("\nIndex Summary")
    print("-------------")
    print(f"Source version: {source_version}")
    print(f"Source timestamp: {source_timestamp}")
    print(f"Source variants: {stats.source_variants:,}")
    print(f"Indexed variants: {stats.indexed_variants:,}")
    print(f"Skipped non-OK status: {stats.skipped_non_ok_status:,}")
    print(f"Skipped non-Commander-legal: {stats.skipped_non_commander_legal:,}")
    print(f"Commander legal only: {commander_legal_only}")
    print(f"Skipped spoiler-tagged: {stats.skipped_spoiler:,}")
    print(f"Skipped missing card names: {stats.skipped_missing_card_names:,}")
    print(f"Spoiler-tagged indexed and marked: {stats.indexed_spoiler_tagged:,}")
    print(f"mustBeCommander indexed and marked: {stats.indexed_must_be_commander:,}")
    print(f"Template-requirement combos indexed and marked: {stats.indexed_with_template_requirements:,}")
    print(f"Index size: {index_size_mb:.2f} MB")
    print(f"Wrote index: {output_path}")
    print(f"Wrote summary: {summary_path}")
    print("\nDone. No app integration was performed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
