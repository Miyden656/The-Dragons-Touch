"""Commander Discovery / Build-From-Collection CLI runner (subprocess worker).

The PySide6 UI launches this as a SUBPROCESS (QProcess) for the collection scan
and the three deck generators. Running them in a thread did not stop the UI
freezing — the work is CPU-bound pure Python, so the GIL blocks the Qt event
loop. A separate process has its own interpreter/GIL, so the UI stays responsive.

Contract:
    py tools/commander_discovery_cli.py --op <op> --input <in.json> --output <out.json>

  op = scan | owned_by_role | rough_shell | full_draft
  <in.json>  : parameters (collection source, selected commander, build prefs)
  <out.json> : results written here for the UI to read back

This calls the SAME engine/build functions the in-process path used; only the
execution context (a child process) changed. It never imports PySide6.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from dataclasses import asdict
from pathlib import Path

# Run as `py tools/commander_discovery_cli.py` from the repo root: ensure the
# repo root (this file's parent's parent) is importable.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


class _State:
    """Duck-typed stand-in for the UI AppState (only the attrs the loaders read)."""

    def __init__(self, data: dict):
        self.collection_source_mode = data.get("collection_source_mode", "Entire collection folder")
        self.selected_collection_files = data.get("selected_collection_files", []) or []
        self.collection_folder = data.get("collection_folder", "") or ""
        self.report_output_folder = data.get("report_output_folder", "Outputs") or "Outputs"


def _commander_name(candidate: dict) -> str:
    return (
        candidate.get("commander_name")
        or candidate.get("card_name")
        or "Selected commander"
    )


def _run_scan(data: dict) -> dict:
    from commander_discovery.ui_scan_path import run_guarded_commander_discovery_scan
    result = run_guarded_commander_discovery_scan(_State(data))
    return {"kind": "scan", "result": asdict(result)}


def _run_owned_by_role(data: dict) -> dict:
    from commander_discovery.ui_scan_path import load_owned_collection_for_role_bucketing
    from build_from_collection.owned_cards_by_role_output import create_owned_cards_by_role_output
    from build_from_collection.owned_cards_by_role_report_writer import write_owned_cards_by_role_output

    candidate = data.get("commander_candidate") or {}
    prefs = data.get("prefs") or {}
    name = _commander_name(candidate)
    owned = load_owned_collection_for_role_bucketing(_State(data))
    output = create_owned_cards_by_role_output(
        owned_cards=owned,
        selected_commander=name,
        primary_strategy=(prefs.get("primary_strategy") or "Not selected yet"),
        secondary_strategy=(prefs.get("secondary_strategy") or "None"),
    )
    result = write_owned_cards_by_role_output(output, output_root=_State(data).report_output_folder)
    rd = result.to_dict() if hasattr(result, "to_dict") else {}
    od = output.to_dict() if hasattr(output, "to_dict") else {}
    grouped = od.get("grouped_by_role", {}) or {}
    grouped_count = sum(len(v) for v in grouped.values()) if isinstance(grouped, dict) else 0
    preview = "\n".join([
        "Owned Cards By Role Output written.",
        "This is depth-C Build From Collection output: possible owned-card role fits only.",
        "",
        f"Commander: {od.get('selected_commander') or name}",
        f"Possible role-fit entries: {grouped_count}",
        "",
        "Files written:",
        f"- Human-readable report: {rd.get('human_report_path')}",
        f"- AI handoff prompt: {rd.get('ai_handoff_prompt_path')}",
        f"- Manifest: {rd.get('manifest_path')}",
        "",
        "No exact card selection.",
        "No final deck inclusion decisions.",
        "No deck generation.",
    ])
    return {
        "kind": "generator",
        "preview_text": preview,
        "outputs": {
            "commander_discovery_owned_cards_by_role_output": od,
            "commander_discovery_owned_cards_by_role_write_result": rd,
        },
    }


def _run_rough_shell(data: dict) -> dict:
    from build_from_collection.rough_shell_output import create_rough_shell_output_model
    from build_from_collection.rough_shell_report_writer import write_rough_shell_output
    from build_from_collection.rough_shell_guidance import build_rough_shell_markdown

    candidate = data.get("commander_candidate") or {}
    prefs = data.get("prefs") or {}
    name = _commander_name(candidate)
    color_identity = candidate.get("color_identity_text") or candidate.get("color_identity_key") or "Unknown"
    primary = prefs.get("primary_strategy") or ""
    secondary = prefs.get("secondary_strategy") or ""
    main_phi = prefs.get("main_philosophy") or ""
    sub_phi = prefs.get("sub_philosophy") or ""
    bracket = prefs.get("bracket_preference") or ""
    collection_first = prefs.get("collection_first_preference") or "Collection-first (prefer owned cards)"

    model = create_rough_shell_output_model()
    result = write_rough_shell_output(model, selected_commander=name, output_root=_State(data).report_output_folder)
    guidance_md = build_rough_shell_markdown(
        commander_name=name,
        color_identity=color_identity,
        primary_strategy=primary,
        secondary_strategy=secondary,
        main_philosophy=main_phi,
        sub_philosophy=sub_phi,
        bracket_preference=bracket,
        collection_first_preference=collection_first,
    )
    rd = result.to_dict() if hasattr(result, "to_dict") else {}
    human_report_path = rd.get("human_report_path")
    if human_report_path:
        try:
            Path(str(human_report_path)).write_text(guidance_md, encoding="utf-8")
        except Exception:
            pass
    preview = (
        f"Rough Shell guidance written for {name}.\n"
        f"\nStrategy: {primary or '(not selected)'} + {secondary or 'no secondary'}"
        f"\nPhilosophy: {main_phi or '(not selected)'} — {sub_phi or '(none)'}"
        f"\nBracket: {bracket or '(not selected)'}"
        f"\n\nFiles written:\n"
        f"- Human-readable report: {rd.get('human_report_path')}\n"
        f"- AI handoff prompt: {rd.get('ai_handoff_prompt_path')}\n"
        f"- Manifest: {rd.get('manifest_path')}\n"
        f"\nThis is guidance only. No exact card selection, no deck generation."
    )
    return {
        "kind": "generator",
        "preview_text": preview,
        "outputs": {
            "commander_discovery_rough_shell_output": (model.to_dict() if hasattr(model, "to_dict") else {}),
            "commander_discovery_rough_shell_write_result": rd,
        },
    }


def _run_full_draft(data: dict) -> dict:
    from commander_discovery.ui_scan_path import load_owned_collection_for_role_bucketing
    from data.scryfall_loader import load_scryfall_lookup
    from build_from_collection.full_100_card_draft_output import create_full_100_card_draft_output_model
    from build_from_collection.full_100_card_draft_report_writer import write_full_100_card_draft_output
    from build_from_collection.full_100_card_draft_builder import (
        build_full_100_card_draft,
        render_full_100_card_draft_markdown,
        render_full_100_card_draft_plain_decklist,
    )

    candidate = data.get("commander_candidate") or {}
    prefs = data.get("prefs") or {}
    name = _commander_name(candidate)
    owned = load_owned_collection_for_role_bucketing(_State(data))
    _cards, scryfall_lookup = load_scryfall_lookup()
    result = build_full_100_card_draft(
        commander_candidate=candidate,
        owned_cards=owned,
        scryfall_lookup=scryfall_lookup,
        primary_strategy=(prefs.get("primary_strategy") or ""),
        secondary_strategy=(prefs.get("secondary_strategy") or ""),
        bracket_preference=(prefs.get("bracket_preference") or ""),
        sub_philosophy=(prefs.get("sub_philosophy") or ""),
    )
    markdown = render_full_100_card_draft_markdown(result)
    model = create_full_100_card_draft_output_model(selected_commander=name)
    write_result = write_full_100_card_draft_output(model, selected_commander=name, output_root=_State(data).report_output_folder)
    wrd = write_result.to_dict() if hasattr(write_result, "to_dict") else {}
    human_report_path = wrd.get("human_report_path")
    if human_report_path:
        try:
            Path(str(human_report_path)).write_text(markdown, encoding="utf-8")
        except Exception:
            pass
    plain_decklist = render_full_100_card_draft_plain_decklist(result)
    color_identity = getattr(result, "color_identity", []) or []
    preview = (
        f"Full 100-Card Draft written for {name}.\n"
        f"\nStrategy: {(prefs.get('primary_strategy') or '(not selected)')}"
        f" + {(prefs.get('secondary_strategy') or 'no secondary')}"
        f"\nTotal cards: {getattr(result, 'total_cards', '?')}/100"
        f"\nColor identity: {'/'.join(color_identity) if color_identity else 'Colorless'}"
        f"\n\nFiles written:\n"
        f"- Human-readable + copy-paste decklist: {wrd.get('human_report_path')}\n"
        f"- AI handoff prompt: {wrd.get('ai_handoff_prompt_path')}\n"
        f"- Manifest: {wrd.get('manifest_path')}\n"
        f"\n--- Copy-paste decklist (also in the human-readable file) ---\n\n"
        f"{plain_decklist}\n"
    )
    return {
        "kind": "generator",
        "preview_text": preview,
        "outputs": {
            "commander_discovery_full_100_card_draft_output": (result.to_dict() if hasattr(result, "to_dict") else {}),
            "commander_discovery_full_100_card_draft_write_result": wrd,
        },
    }


_OPS = {
    "scan": _run_scan,
    "owned_by_role": _run_owned_by_role,
    "rough_shell": _run_rough_shell,
    "full_draft": _run_full_draft,
}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Commander Discovery / build-from-collection subprocess runner.")
    parser.add_argument("--op", required=True, choices=sorted(_OPS))
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)

    try:
        data = json.loads(Path(args.input).read_text(encoding="utf-8-sig"))
    except Exception as exc:
        data = {}
        result = {"kind": "error", "error": f"Could not read input: {exc}"}
        Path(args.output).write_text(json.dumps(result), encoding="utf-8")
        return 0

    try:
        result = _OPS[args.op](data)
    except Exception as exc:
        result = {
            "kind": "error",
            "op": args.op,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }

    try:
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:
        # Last resort: emit to stdout so the UI can still surface something.
        print(json.dumps({"kind": "error", "error": f"Could not write output: {exc}"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
