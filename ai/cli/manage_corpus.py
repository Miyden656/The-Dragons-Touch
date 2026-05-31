"""Inspect and curate the Commander AI training corpus (headless).

The Commander Guide panel appends approved answers to
Outputs/commander_ai_training_data.jsonl. This tool is how you look after that
file on the way to a fine-tune — no Ollama or engine scoring involved.

    py -3 -m ai.cli.manage_corpus                         # stats (default)
    py -3 -m ai.cli.manage_corpus --validate              # list problem records
    py -3 -m ai.cli.manage_corpus --show 5                # print first 5 records
    py -3 -m ai.cli.manage_corpus --dedupe                # rewrite without dupes (keeps a .bak)
    py -3 -m ai.cli.manage_corpus --export-clean train.jsonl   # valid+deduped+approved subset
    py -3 -m ai.cli.manage_corpus --path some/other.jsonl ...  # operate on another file
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from ai.training.corpus import (  # noqa: E402
    clean_corpus,
    corpus_stats,
    dedupe,
    default_corpus_path,
    load_corpus,
    validate_record,
    write_corpus,
)


def _truncate(text: str, width: int = 70) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= width else text[: width - 1] + "…"


def _print_table(title: str, counts: dict, limit: int = 12) -> None:
    if not counts:
        return
    print(f"  {title}:")
    for i, (key, n) in enumerate(counts.items()):
        if i >= limit:
            print(f"      … and {len(counts) - limit} more")
            break
        print(f"      {n:>4}  {key}")


def _cmd_stats(loaded) -> int:
    s = corpus_stats(loaded)
    print(f"Corpus: {s['path']}")
    if not s["exists"]:
        print("  (file does not exist yet — use the Commander Guide's "
              "'Save as training example' button to start building it.)")
        return 0
    print(f"  total records   : {s['total_records']}")
    print(f"  valid (usable)  : {s['valid_records']}")
    print(f"  invalid         : {s['invalid_records']}")
    print(f"  approved        : {s['approved_records']}")
    print(f"  duplicates      : {s['duplicate_records']}")
    if s["parse_errors"]:
        print(f"  unparseable lines: {s['parse_errors']}  (run --validate to see them)")
    print()
    _print_table("by mode", s["by_mode"])
    _print_table("by persona", s["by_persona"])
    _print_table("by guide style", s["by_guide_style"])
    _print_table("by commander", s["by_commander"])
    return 0


def _cmd_validate(loaded) -> int:
    problems_found = 0
    for line_no, msg in loaded.parse_errors:
        print(f"  line {line_no}: {msg}")
        problems_found += 1
    for idx, rec in enumerate(loaded.records, start=1):
        problems = validate_record(rec)
        if problems:
            problems_found += 1
            q = _truncate(rec.get("question", ""), 50)
            print(f"  record {idx} (\"{q}\"): {'; '.join(problems)}")
    if not problems_found:
        print(f"  All {len(loaded.records)} records are valid. ✅")
    else:
        print(f"\n  {problems_found} problem(s) found.")
    return 0


def _cmd_show(loaded, n: int) -> int:
    if not loaded.records:
        print("  (no records)")
        return 0
    for idx, rec in enumerate(loaded.records[:n], start=1):
        print(f"--- record {idx} ---")
        print(f"  commander : {rec.get('commander', '')}")
        print(f"  mode      : {rec.get('mode', '')}   persona: {rec.get('persona', '')}   "
              f"style: {rec.get('guide_style', '')}   approved: {rec.get('approved')}")
        print(f"  question  : {_truncate(rec.get('question', ''), 100)}")
        print(f"  answer    : {_truncate(rec.get('answer', ''), 100)}")
        issues = validate_record(rec)
        if issues:
            print(f"  ⚠ issues : {'; '.join(issues)}")
        print()
    return 0


def _cmd_dedupe(loaded) -> int:
    unique, removed = dedupe(loaded.records)
    if removed == 0:
        print(f"  No duplicates found among {len(loaded.records)} records.")
        return 0
    backup = loaded.path.with_suffix(loaded.path.suffix + ".bak")
    write_corpus(backup, loaded.records)
    write_corpus(loaded.path, unique)
    print(f"  Removed {removed} duplicate(s). {len(unique)} records remain.")
    print(f"  Backup of the original written to: {backup}")
    return 0


def _cmd_export_clean(loaded, out_path: str, approved_only: bool) -> int:
    clean, report = clean_corpus(loaded.records, approved_only=approved_only)
    if not clean:
        print("  Nothing to export — no records survived cleaning.")
        print(f"  {report}")
        return 0
    written = write_corpus(out_path, clean)
    print(f"  Exported {report['kept']} clean record(s) -> {written}")
    print(f"    dropped unapproved: {report['dropped_unapproved']}")
    print(f"    dropped invalid   : {report['dropped_invalid']}")
    print(f"    dropped duplicate : {report['dropped_duplicate']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass

    parser = argparse.ArgumentParser(description="Inspect/curate the Commander AI training corpus")
    parser.add_argument("--path", type=str, default="", help="Corpus file (default: Outputs/commander_ai_training_data.jsonl)")
    parser.add_argument("--validate", action="store_true", help="List parse errors and invalid records")
    parser.add_argument("--show", type=int, default=0, metavar="N", help="Print the first N records")
    parser.add_argument("--dedupe", action="store_true", help="Rewrite the file with duplicates removed (keeps a .bak)")
    parser.add_argument("--export-clean", type=str, default="", metavar="OUT", help="Write valid+deduped+approved records to OUT")
    parser.add_argument("--include-unapproved", action="store_true", help="With --export-clean, keep unapproved records too")
    args = parser.parse_args(argv)

    path = Path(args.path) if args.path else default_corpus_path()
    loaded = load_corpus(path)

    if not loaded.exists and not args.export_clean:
        return _cmd_stats(loaded)

    if args.validate:
        return _cmd_validate(loaded)
    if args.show:
        return _cmd_show(loaded, args.show)
    if args.dedupe:
        return _cmd_dedupe(loaded)
    if args.export_clean:
        return _cmd_export_clean(loaded, args.export_clean, approved_only=not args.include_unapproved)
    return _cmd_stats(loaded)


if __name__ == "__main__":
    raise SystemExit(main())
