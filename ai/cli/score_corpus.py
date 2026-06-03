"""Score + triage the corpus so you don't hand-review thousands of candidates.

Every candidate already passed the generation safety net (safety-flagged answers
were dropped), so grounding/legality is already guaranteed. What VARIES — and what
this scorer measures — is:

  * VALIDITY   : structured modes emitted a parseable JSON block; the answer isn't
                 truncated/too short.
  * VOICE      : how many of the persona's signature-vocabulary phrases appear
                 (from ai/prompts/persona_voices.md), minus any "Avoid" phrases.

It buckets every candidate:
  weak    = not valid (malformed JSON where expected, or too short) -> drop these
  strong  = valid AND >= STRONG_VOICE distinct voice phrases AND no avoid phrase
            -> bulk-approve / spot-check only
  review  = valid but low voice -> the only band you actually need to eyeball

Usage:
  py -3 -m ai.cli.score_corpus                          # print the breakdown + samples
  py -3 -m ai.cli.score_corpus --export-strong strong.jsonl
  py -3 -m ai.cli.score_corpus --export-bucket review review.jsonl
  py -3 -m ai.cli.score_corpus --top 5                 # also list top-5 per persona x mode

$0, no model calls, deterministic.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from ai.commander_ai_parsing import parse_structured_response
from ai.commander_ai_personas import _load_voice_profiles

DEFAULT_PATH = Path("Outputs") / "commander_ai_training_data.jsonl"
STRUCTURED_MODES = {"commander_review", "cut_review", "replacement", "build_from_collection"}
MIN_LEN = 150          # chars; shorter answers are usually thin/truncated
STRONG_VOICE = 2       # distinct signature phrases for the "strong" band


def _voice_terms(persona: str) -> tuple[list[str], list[str]]:
    prof = _load_voice_profiles().get(persona, {})
    vocab = [t.strip().lower() for t in str(prof.get("vocabulary", "")).split(",") if t.strip()]
    avoid = [t.strip().lower().strip('"') for t in str(prof.get("avoid", "")).split(";") if t.strip()]
    return vocab, avoid


def score_record(rec: dict) -> dict:
    answer = str(rec.get("answer", "") or "")
    low = answer.lower()
    mode = rec.get("mode", "")
    persona = rec.get("persona", "")

    # validity
    long_enough = len(answer.strip()) >= MIN_LEN
    if mode in STRUCTURED_MODES:
        _, structured, _ = parse_structured_response(answer)
        structured_ok = structured is not None
    else:
        structured_ok = True  # conversational modes don't require a JSON block
    valid = long_enough and structured_ok

    # voice
    vocab, avoid = _voice_terms(persona)
    voice_hits = sum(1 for t in vocab if t and t in low)
    avoid_hit = any(a and a in low for a in avoid)

    if not valid:
        bucket = "weak"
    elif voice_hits >= STRONG_VOICE and not avoid_hit:
        bucket = "strong"
    else:
        bucket = "review"

    return {
        "bucket": bucket, "valid": valid, "structured_ok": structured_ok,
        "long_enough": long_enough, "voice_hits": voice_hits, "avoid_hit": avoid_hit,
        "persona": persona, "mode": mode, "len": len(answer.strip()),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Score + triage corpus candidates ($0, no model).")
    ap.add_argument("--path", default=str(DEFAULT_PATH))
    ap.add_argument("--include-approved", action="store_true",
                    help="Score approved records too (default: only unapproved candidates).")
    ap.add_argument("--export-strong", metavar="OUT", default="",
                    help="Write the strong band to OUT (jsonl) for bulk approval.")
    ap.add_argument("--export-bucket", nargs=2, metavar=("BUCKET", "OUT"), default=None,
                    help="Write one bucket (weak|review|strong) to OUT.")
    ap.add_argument("--top", type=int, default=0, metavar="N",
                    help="Also list the top-N by voice per persona x mode.")
    ap.add_argument("--samples", type=int, default=2, metavar="N",
                    help="Print N sample answers per bucket (default 2).")
    args = ap.parse_args(argv)

    path = Path(args.path)
    recs = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not args.include_approved:
        recs = [r for r in recs if not r.get("approved")]
    if not recs:
        print("No candidates to score.")
        return 0

    scored = [(r, score_record(r)) for r in recs]
    buckets: dict[str, list] = defaultdict(list)
    for r, s in scored:
        buckets[s["bucket"]].append((r, s))

    n = len(scored)
    print(f"Scored {n} candidates from {path.name}\n")
    print("BUCKETS (the only band you must eyeball is 'review'):")
    for b in ("strong", "review", "weak"):
        c = len(buckets[b])
        print(f"  {b:7s} {c:5d}  ({100*c/n:4.1f}%)")
    valid = sum(1 for _, s in scored if s["valid"])
    voiced = sum(1 for _, s in scored if s["voice_hits"] > 0)
    print(f"\n  valid (well-formed)     : {valid}/{n} ({100*valid/n:.1f}%)")
    print(f"  any voice phrase present: {voiced}/{n} ({100*voiced/n:.1f}%)")

    # per persona x mode
    cell = defaultdict(lambda: {"n": 0, "strong": 0, "voice": 0, "valid": 0})
    for r, s in scored:
        k = (s["persona"], s["mode"])
        cell[k]["n"] += 1
        cell[k]["strong"] += 1 if s["bucket"] == "strong" else 0
        cell[k]["voice"] += s["voice_hits"]
        cell[k]["valid"] += 1 if s["valid"] else 0
    print("\nPER PERSONA x MODE  (n | %strong | %valid | avg voice hits):")
    for (persona, mode), d in sorted(cell.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        print(f"  {persona:24s} {mode:18s} {d['n']:4d} | "
              f"{100*d['strong']/d['n']:5.0f}% | {100*d['valid']/d['n']:5.0f}% | "
              f"{d['voice']/d['n']:.2f}")

    # samples
    if args.samples:
        for b in ("strong", "review", "weak"):
            print(f"\n----- {b.upper()} samples -----")
            for r, s in buckets[b][: args.samples]:
                print(f"[{s['persona']}/{s['mode']} | voice={s['voice_hits']} "
                      f"valid={s['valid']} avoid={s['avoid_hit']}]")
                print("  " + str(r.get("answer", ""))[:300].replace("\n", "\n  "))
                print()

    if args.top:
        print(f"\nTOP {args.top} BY VOICE PER PERSONA x MODE:")
        by_cell = defaultdict(list)
        for r, s in scored:
            by_cell[(s["persona"], s["mode"])].append((s["voice_hits"], r))
        for k in sorted(by_cell):
            top = sorted(by_cell[k], key=lambda x: -x[0])[: args.top]
            print(f"  {k[0]}/{k[1]}: " + ", ".join(f"v{v}" for v, _ in top))

    # exports
    def _write(records, out):
        Path(out).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records),
                             encoding="utf-8")
        print(f"\nWrote {len(records)} records -> {out}")

    if args.export_strong:
        _write([r for r, _ in buckets["strong"]], args.export_strong)
    if args.export_bucket:
        b, out = args.export_bucket
        _write([r for r, _ in buckets.get(b, [])], out)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
