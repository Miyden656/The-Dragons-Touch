"""Run the Commander AI eval set against one or more local models (headless).

Scores each model on the built-in eval cases (legality accuracy via our grounded
safety net, non-empty answers, structured-output emission) so you can compare
base models head-to-head before investing in a fine-tune.

    py -3 -m ai.cli.run_eval                          # current configured model
    py -3 -m ai.cli.run_eval --models qwen2.5:7b,llama3.1
    py -3 -m ai.cli.run_eval --models qwen2.5:7b --verbose

Needs Ollama running and the named models installed; needs Scryfall data for the
legality checks. Pure-logic scoring lives in ai/training/eval.py and is tested
without Ollama.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from ai.commander_ai_config import from_settings  # noqa: E402
from ai.commander_ai_service import CommanderAIService  # noqa: E402
from ai.ollama_client import OllamaClient  # noqa: E402
from ai.training.eval import (  # noqa: E402
    DEFAULT_EVAL_CASES,
    AggregateReport,
    EvalReport,
    aggregate_reports,
    run_eval,
)


def _load_config():
    try:
        from ui.services.user_settings import load_app_settings
        return from_settings(load_app_settings())
    except Exception:  # noqa: BLE001
        return from_settings({})


def _print_report(report: EvalReport, *, verbose: bool) -> None:
    print(f"\n=== {report.model} ===")
    print(f"  cases fully passed : {report.cases_passed}/{len(report.cases)}")
    print(f"  checks passed      : {report.checks_passed}/{report.checks_total} "
          f"({report.pass_rate() * 100:.0f}%)")
    if report.avg_latency_s:
        print(f"  avg latency        : {report.avg_latency_s:.1f}s")
    for case in report.cases:
        if not case.ok:
            print(f"    ✗ {case.case_id}: ERROR — {case.error}")
            continue
        mark = "✓" if case.all_passed else "✗"
        print(f"    {mark} {case.case_id}: {case.passed}/{case.total} "
              f"({case.latency_s:.1f}s)")
        if verbose or not case.all_passed:
            for chk in case.checks:
                if verbose or not chk.passed:
                    cm = "·" if chk.passed else "✗"
                    print(f"        {cm} {chk.kind}{(' — ' + chk.detail) if chk.detail else ''}")


def _print_aggregate(agg: AggregateReport) -> None:
    print(f"\n=== {agg.model} (x{agg.runs} runs) ===")
    print(f"  consistency  : {agg.consistent_cases()}/{agg.num_cases} cases passed in ALL runs")
    print(f"  checks passed: {agg.checks_passed}/{agg.checks_total} "
          f"({agg.overall_rate() * 100:.0f}% across runs)")
    flaky = agg.flaky_cases()
    if flaky:
        print("  flaky (some runs failed):")
        for cid, fp, n in flaky:
            print(f"    ~ {cid}: passed {fp}/{n}")
    never = agg.never_passed()
    if never:
        print("  never passed:")
        for cid in never:
            print(f"    ✗ {cid}")
    if not flaky and not never:
        print("  no flakiness — every case passed every run ✅")


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass

    parser = argparse.ArgumentParser(description="Run the Commander AI eval set")
    parser.add_argument("--models", type=str, default="", help="Comma-separated models to compare (default: configured model)")
    parser.add_argument("--verbose", action="store_true", help="Show every check, not just failures")
    parser.add_argument("--repeat", type=int, default=1, metavar="N", help="Run each case N times and report consistency (default 1)")
    args = parser.parse_args(argv)
    repeat = max(1, args.repeat)

    base_config = _load_config()

    import main as app_main
    _cards, lookup, err = app_main.load_scryfall_or_none()
    if err or not lookup:
        print(f"WARNING: Scryfall data not loaded ({err}); legality checks will be unreliable.")
        lookup = lookup or {}

    models = [m.strip() for m in args.models.split(",") if m.strip()] or [base_config.model]
    suffix = f" (x{repeat} runs each)" if repeat > 1 else ""
    print(f"Running {len(DEFAULT_EVAL_CASES)} eval cases against: {', '.join(models)}{suffix}")

    single_reports: list[EvalReport] = []   # for the 1-run comparison summary
    aggregates: list[AggregateReport] = []  # for the multi-run consistency summary
    for model in models:
        config = replace(base_config, model=model, enabled=True)
        client = OllamaClient(config)
        avail = client.is_available()
        if not avail.ok:
            print(f"\n=== {model} === SKIPPED ({avail.message})")
            continue
        service = CommanderAIService(config, client=client, scryfall_lookup=lookup)
        runs = [
            run_eval(DEFAULT_EVAL_CASES, service=service, scryfall_lookup=lookup, model=model)
            for _ in range(repeat)
        ]
        if repeat == 1:
            single_reports.append(runs[0])
            _print_report(runs[0], verbose=args.verbose)
        else:
            agg = aggregate_reports(runs)
            aggregates.append(agg)
            _print_aggregate(agg)

    if len(single_reports) > 1:
        print("\n=== summary ===")
        for r in sorted(single_reports, key=lambda r: r.pass_rate(), reverse=True):
            print(f"  {r.pass_rate() * 100:5.0f}%  {r.checks_passed}/{r.checks_total}  "
                  f"avg {r.avg_latency_s:.1f}s  {r.model}")
    if len(aggregates) > 1:
        print("\n=== consistency summary ===")
        for a in sorted(aggregates, key=lambda a: (a.consistent_cases(), a.overall_rate()), reverse=True):
            print(f"  {a.consistent_cases()}/{a.num_cases} stable · "
                  f"{a.overall_rate() * 100:.0f}% checks · {a.model}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
