"""Training-corpus tooling tests (Phase: training track, step 1).

Pure logic over an in-memory/temp JSONL file — no Ollama, no engine scoring.
Verifies tolerant loading, record validation, de-duplication, stats, and the
clean-export pipeline. Run via tests/run_all.py.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from _test_helpers import TestRun

from ai.training.corpus import (
    clean_corpus,
    corpus_stats,
    dedupe,
    is_usable,
    load_corpus,
    merge_records,
    persona_coverage,
    record_key,
    validate_record,
    write_corpus,
)


def _rec(**over) -> dict:
    base = {
        "commander": "Krenko, Mob Boss",
        "mode": "cut_review",
        "persona": "pet_card",
        "guide_style": "adventurer",
        "question": "What should I cut?",
        "answer": "Consider trimming redundant ramp.",
        "context": json.dumps({"commander": {"commander": "Krenko, Mob Boss"}}),
        "approved": True,
    }
    base.update(over)
    return base


def main() -> None:
    t = TestRun("ai_corpus")

    # --- validation: a good record is usable ---
    t.eq("good record validates", validate_record(_rec()), [])
    t.true("good record is_usable", is_usable(_rec()))

    # --- validation catches problems ---
    t.true("missing field flagged", any("commander" in p for p in validate_record(_rec(commander=None))))
    t.true("empty question flagged", any("question" in p for p in validate_record(_rec(question="   "))))
    t.true("unknown mode flagged", any("mode" in p for p in validate_record(_rec(mode="bogus_mode"))))
    t.true("unknown style flagged", any("guide_style" in p for p in validate_record(_rec(guide_style="zzz"))))
    t.true("unknown persona flagged", any("persona" in p for p in validate_record(_rec(persona="not_a_persona"))))
    t.true("bad context json flagged", any("context" in p for p in validate_record(_rec(context="{not json"))))
    t.eq("empty/missing context is allowed", validate_record(_rec(context="")), [])

    # --- record_key + dedupe ---
    a, b = _rec(), _rec()
    t.eq("identical records share a key", record_key(a), record_key(b))
    diff = _rec(question="Different question?")
    t.true("different question -> different key", record_key(a) != record_key(diff))
    unique, removed = dedupe([a, b, diff])
    t.eq("dedupe removes the duplicate", removed, 1)
    t.eq("dedupe keeps the distinct two", len(unique), 2)

    # --- load_corpus: tolerant of a missing file and bad lines ---
    missing = load_corpus(Path(tempfile.gettempdir()) / "definitely_not_here_corpus.jsonl")
    t.eq("missing file -> exists False", missing.exists, False)
    t.eq("missing file -> no records", len(missing), 0)

    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "corpus.jsonl"
        lines = [
            json.dumps(_rec()),
            "this is not json",
            json.dumps(_rec(question="Q2?")),
            json.dumps([1, 2, 3]),  # valid json but not an object
            "",                      # blank line ignored
            json.dumps(_rec(mode="bogus_mode")),  # parses, but invalid record
        ]
        p.write_text("\n".join(lines), encoding="utf-8")
        loaded = load_corpus(p)
        t.eq("parsed the object lines", len(loaded.records), 3)
        t.eq("recorded two parse errors", len(loaded.parse_errors), 2)

        # --- stats ---
        s = corpus_stats(loaded)
        t.eq("stats total", s["total_records"], 3)
        t.eq("stats valid (one has bogus mode)", s["valid_records"], 2)
        t.eq("stats invalid", s["invalid_records"], 1)
        t.in_set("stats by_mode has cut_review", "cut_review", s["by_mode"])

        # --- clean export: drop invalid, keep approved+valid+unique ---
        clean, report = clean_corpus(loaded.records, approved_only=True)
        t.eq("clean keeps the 2 valid approved", len(clean), 2)
        t.eq("clean dropped the invalid one", report["dropped_invalid"], 1)

        # round-trips through write/read
        out = Path(d) / "clean.jsonl"
        write_corpus(out, clean)
        reread = load_corpus(out)
        t.eq("written clean corpus rereads", len(reread.records), 2)

    # --- clean export respects approved_only ---
    mixed = [_rec(), _rec(question="Q2?", approved=False), _rec(question="Q3?")]
    clean_app, rep_app = clean_corpus(mixed, approved_only=True)
    t.eq("approved-only drops unapproved", rep_app["dropped_unapproved"], 1)
    t.eq("approved-only kept 2", len(clean_app), 2)
    clean_all, _rep_all = clean_corpus(mixed, approved_only=False)
    t.eq("include-unapproved keeps all 3", len(clean_all), 3)

    # --- merge_records: pool two people's corpora, dedupe overlap ---
    mine = [_rec(question="Q1"), _rec(question="Q2")]
    buddy = [_rec(question="Q2"), _rec(question="Q3")]  # Q2 overlaps
    merged, mreport = merge_records([mine, buddy])
    t.eq("merge inputs counted", mreport["inputs"], 2)
    t.eq("merge total before dedupe", mreport["total"], 4)
    t.eq("merge removed the overlap", mreport["removed_duplicate"], 1)
    t.eq("merge kept 3 distinct", len(merged), 3)
    t.eq("merge empty -> empty", merge_records([])[0], [])

    # --- persona_coverage: shows zeros for unused personas, flags below-target ---
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "cov.jsonl"
        recs = [_rec(persona="pet_card"), _rec(persona="pet_card", question="Q2?"),
                _rec(persona="spike", question="Q3?")]
        write_corpus(p, recs)
        cov = persona_coverage(load_corpus(p), target=3)
        t.eq("pet_card counted twice", cov["counts"].get("pet_card"), 2)
        t.eq("spike counted once", cov["counts"].get("spike"), 1)
        t.true("an unused persona is shown as zero", cov["counts"].get("balanced_unknown") == 0)
        t.true("below-target includes the unused baseline", "balanced_unknown" in cov["below_target"])
        t.true("below-target includes pet_card (2 < 3)", "pet_card" in cov["below_target"])
        t.true("coverage spans all known personas", len(cov["counts"]) >= 22)

    t.report_and_exit()


if __name__ == "__main__":
    main()
