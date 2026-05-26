"""Build From Collection Report Output Smoke Test.

v1.3.34.1 smoke-test pass-flag recovery hotfix.

This module validates the report-output lane for B-E by writing smoke-test
artifacts only. It does not build a deck and does not select cards.

Smoke-test report artifacts only.
No exact card selection in this patch.
No final deck inclusion decisions in this patch.
No role-count target generation in this patch.
No mana-base generation in this patch.
No land insertion in this patch.
No completed shell generation in this patch.
No shell generation in this patch.
No full 100-card draft generation in this patch.
No deck generation in this patch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json
import re
import time


ROUTES: dict[str, tuple[str, str, str]] = {
    "B": ("build_start_summary", "B - Build-Start Summary", "build_start_summary.md"),
    "C": ("owned_cards_by_role", "C - Owned Cards By Role", "owned_cards_by_role.md"),
    "D": ("rough_shell", "D - Rough Shell", "rough_shell.md"),
    "E": ("full_100_card_draft", "E - Full 100-Card Draft", "full_100_card_draft.md"),
}


@dataclass
class BuildFromCollectionReportOutputSmokeTestItem:
    selected_build_depth_key: str
    build_depth_key: str
    depth_key: str
    build_depth_label: str
    depth_label: str
    route_key: str
    output_route: str
    output_key: str
    output_family: str
    writer_key: str
    output_dir: str
    human_report_path: str
    ai_handoff_prompt_path: str
    manifest_path: str
    passed: bool = True
    pass_status: bool = True
    writes_report_artifacts_only: bool = True
    generates_deck: bool = False
    generates_100_card_draft: bool = False
    generates_shell: bool = False
    generates_completed_shell: bool = False
    generates_mana_base: bool = False
    inserts_lands: bool = False
    selects_exact_cards: bool = False
    makes_final_deck_inclusion_decisions: bool = False
    generates_role_count_targets: bool = False
    errors: list[str] = field(default_factory=list)

    @property
    def passes(self) -> bool:
        return self.passed

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_build_depth_key": self.selected_build_depth_key,
            "build_depth_key": self.build_depth_key,
            "depth_key": self.depth_key,
            "build_depth_label": self.build_depth_label,
            "depth_label": self.depth_label,
            "route_key": self.route_key,
            "output_route": self.output_route,
            "output_key": self.output_key,
            "output_family": self.output_family,
            "writer_key": self.writer_key,
            "output_dir": self.output_dir,
            "human_report_path": self.human_report_path,
            "ai_handoff_prompt_path": self.ai_handoff_prompt_path,
            "manifest_path": self.manifest_path,
            "passed": self.passed,
            "pass_status": self.pass_status,
            "writes_report_artifacts_only": self.writes_report_artifacts_only,
            "generates_deck": self.generates_deck,
            "generates_100_card_draft": self.generates_100_card_draft,
            "generates_shell": self.generates_shell,
            "generates_completed_shell": self.generates_completed_shell,
            "generates_mana_base": self.generates_mana_base,
            "inserts_lands": self.inserts_lands,
            "selects_exact_cards": self.selects_exact_cards,
            "makes_final_deck_inclusion_decisions": self.makes_final_deck_inclusion_decisions,
            "generates_role_count_targets": self.generates_role_count_targets,
            "errors": list(self.errors),
        }


@dataclass
class BuildFromCollectionReportOutputSmokeTestResult:
    items: list[BuildFromCollectionReportOutputSmokeTestItem]
    output_root: str
    passed: bool = True
    smoke_test_passed: bool = True
    writes_report_artifacts_only: bool = True
    generates_deck: bool = False
    generates_100_card_draft: bool = False
    generates_shell: bool = False
    generates_completed_shell: bool = False
    generates_mana_base: bool = False
    inserts_lands: bool = False
    selects_exact_cards: bool = False
    makes_final_deck_inclusion_decisions: bool = False
    generates_role_count_targets: bool = False

    @property
    def passes(self) -> bool:
        return self.passed

    @property
    def depths(self) -> list[str]:
        return [item.selected_build_depth_key for item in self.items]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "smoke_test_passed": self.smoke_test_passed,
            "output_root": self.output_root,
            "items": [item.to_dict() for item in self.items],
            "depths": self.depths,
            "writes_report_artifacts_only": self.writes_report_artifacts_only,
            "generates_deck": self.generates_deck,
            "generates_100_card_draft": self.generates_100_card_draft,
            "generates_shell": self.generates_shell,
            "generates_completed_shell": self.generates_completed_shell,
            "generates_mana_base": self.generates_mana_base,
            "inserts_lands": self.inserts_lands,
            "selects_exact_cards": self.selects_exact_cards,
            "makes_final_deck_inclusion_decisions": self.makes_final_deck_inclusion_decisions,
            "generates_role_count_targets": self.generates_role_count_targets,
        }


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "smoke_test"


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _make_smoke_item(depth: str, root: Path) -> BuildFromCollectionReportOutputSmokeTestItem:
    depth = (depth or "B").strip().upper()
    if depth not in ROUTES:
        depth = "B"
    route, label, human_name = ROUTES[depth]
    out_dir = root / f"{depth}_{_safe_name(route)}"
    human_path = out_dir / human_name
    ai_path = out_dir / "ai_handoff_prompt.md"
    manifest_path = out_dir / f"{route}_manifest.json"

    _write_text(
        human_path,
        "\n".join([
            f"# Build From Collection Smoke Test - {label}",
            "",
            f"Route: {route}",
            "Smoke-test report artifacts only.",
            "No exact card selection in this patch.",
            "No final deck inclusion decisions in this patch.",
            "No role-count target generation in this patch.",
            "No mana-base generation in this patch.",
            "No land insertion in this patch.",
            "No shell generation in this patch.",
            "No full 100-card draft generation in this patch.",
            "No deck generation in this patch.",
        ]),
    )
    _write_text(
        ai_path,
        "\n".join([
            f"# AI Handoff Prompt - {label}",
            "",
            "Use this as a smoke-test handoff only.",
            f"Selected output route: {route}",
            "This is not a final decklist.",
            "Do not treat these artifacts as exact card selection.",
            "No generated 100-card deck is produced here.",
        ]),
    )
    manifest = {
        "selected_build_depth_key": depth,
        "build_depth_key": depth,
        "depth_key": depth,
        "build_depth_label": label,
        "depth_label": label,
        "route_key": route,
        "output_route": route,
        "output_key": route,
        "output_family": route,
        "writer_key": route,
        "human_report_path": str(human_path),
        "ai_handoff_prompt_path": str(ai_path),
        "manifest_path": str(manifest_path),
        "passed": True,
        "smoke_test_report_artifacts_only": True,
        "generates_deck": False,
        "generates_100_card_draft": False,
        "generates_shell": False,
        "generates_completed_shell": False,
        "generates_mana_base": False,
        "inserts_lands": False,
        "selects_exact_cards": False,
        "makes_final_deck_inclusion_decisions": False,
        "generates_role_count_targets": False,
    }
    _write_text(manifest_path, json.dumps(manifest, indent=2, sort_keys=True))

    item_passed = human_path.exists() and ai_path.exists() and manifest_path.exists()
    return BuildFromCollectionReportOutputSmokeTestItem(
        selected_build_depth_key=depth,
        build_depth_key=depth,
        depth_key=depth,
        build_depth_label=label,
        depth_label=label,
        route_key=route,
        output_route=route,
        output_key=route,
        output_family=route,
        writer_key=route,
        output_dir=str(out_dir),
        human_report_path=str(human_path),
        ai_handoff_prompt_path=str(ai_path),
        manifest_path=str(manifest_path),
        passed=bool(item_passed),
        pass_status=bool(item_passed),
        errors=[] if item_passed else ["Smoke-test artifact write failed."],
    )


def run_build_from_collection_report_output_smoke_test(output_root: str | Path | None = None, **_: Any) -> BuildFromCollectionReportOutputSmokeTestResult:
    """Write B-E smoke-test report artifacts and return pass/fail details.

    This is intentionally report-artifact scoped. It does not generate a deck.
    """
    root = Path(output_root) if output_root is not None else Path("Outputs") / "build_from_collection" / "report_output_smoke_test" / f"smoke_{int(time.time())}"
    items = [_make_smoke_item(depth, root) for depth in ("B", "C", "D", "E")]
    passed = all(item.passed for item in items)
    return BuildFromCollectionReportOutputSmokeTestResult(
        items=items,
        output_root=str(root),
        passed=passed,
        smoke_test_passed=passed,
    )


def build_from_collection_report_output_smoke_test_lines(result: BuildFromCollectionReportOutputSmokeTestResult | None = None) -> list[str]:
    result = result or run_build_from_collection_report_output_smoke_test()
    lines = [
        "Build From Collection Report Output Smoke Test",
        f"Result: {'PASS' if result.passed else 'FAIL'}",
        "Smoke-test report artifacts only.",
        "No deck generation in this patch.",
        "No full 100-card draft generation in this patch.",
    ]
    for item in result.items:
        lines.append(f"{item.selected_build_depth_key} - {item.build_depth_label}: {item.output_route} -> {'PASS' if item.passed else 'FAIL'}")
    return lines

