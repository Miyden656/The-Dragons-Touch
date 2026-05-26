"""Run report output smoke baseline checks for v1.5.23.1."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import hashlib
import json


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_report_output_smoke_baseline(root: Path | None = None) -> Dict[str, Any]:
    """Run passive report/postprocessor smoke checks.

    This does not execute the full analysis pipeline. It imports report modules,
    runs controlled postprocessor text fixtures, and verifies key symbols exist.
    """

    from reports import report_builder
    from reports import report_postprocessors
    from reports.smoke_fixtures import (
        make_dragon_gate_smoke_report,
        make_postprocessor_smoke_report,
        make_smoke_context,
    )

    context = make_smoke_context()
    context_payload = context.as_dict()

    post_input = make_postprocessor_smoke_report()
    post_output = report_postprocessors.apply_normal_report_postprocessors(post_input)

    dragon_input = make_dragon_gate_smoke_report()

    checks = {
        "fixture_uses_real_newlines": "\\n" not in post_input and "\n" in post_input,
        "post_input_has_replacement_heading": "## Replacement / Addition Needs" in post_input,
        "post_input_has_fallback_heading": "### Fallback Categories to Explore Later" in post_input,
        "build_normal_report_exists": hasattr(report_builder, "build_normal_report"),
        "write_normal_report_exists": hasattr(report_builder, "write_normal_report"),
        "apply_normal_report_postprocessors_exists": hasattr(report_postprocessors, "apply_normal_report_postprocessors"),
        "postprocessor_removed_dataclass_noise": "ReplacementNeedSummary" not in post_output,
        "postprocessor_mapped_board_protection": "More protection — triggered by: board protection" in post_output,
        "postprocessor_mapped_interaction": "More targeted interaction — triggered by: table-stabilizing interaction" in post_output,
        "postprocessor_added_need_aligned_addendum": "Need-Aligned Exact Preview Addendum" in post_output,
        "postprocessor_preserved_safety_boundary": "### Exact Preview Safety Boundaries" in post_output,
        "dragon_gate_fixture_contains_dragon_terms": "Dragon" in dragon_input and "strong owned" in dragon_input,
        "smoke_context_has_cards": len(context_payload.get("cards", [])) >= 3,
        "smoke_context_has_replacement_needs": len(context_payload.get("replacement_needs", [])) >= 2,
    }

    failed_checks = [name for name, passed in checks.items() if not passed]

    return {
        "service": "report_output_smoke_baseline",
        "service_version": "v1.5.23.1",
        "status": "pass" if all(checks.values()) else "fail",
        "behavior_changed": False,
        "launch_executed": False,
        "analysis_executed": False,
        "data_download_executed": False,
        "checks": checks,
        "failed_checks": failed_checks,
        "context_payload": context_payload,
        "postprocessor_input_sha256": sha256_text(post_input),
        "postprocessor_output_sha256": sha256_text(post_output),
        "dragon_gate_fixture_sha256": sha256_text(dragon_input),
        "postprocessor_input_excerpt": post_input[:1200],
        "postprocessor_output_excerpt": post_output[:1500],
    }


if __name__ == "__main__":
    print(json.dumps(run_report_output_smoke_baseline(), indent=2))
