#!/usr/bin/env python3
"""v0.8.10-dev — optional guarded main.py hook for combo awareness.

Scope guard:
- No API calls.
- Combo awareness is off by default.
- Runs only when RuntimeConfig explicitly enables it.
- Writes separate artifacts and can append the concise combo section to the normal report and user-guided prompt when the user opts into report-section mode.
- Does not make combo recommendations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app_io.output_writer import get_unique_output_path, write_text_file
from config import RuntimeConfig
from ui.services.app_paths import get_runtime_paths

from .collection_loader import read_csv_collection_file, read_text_collection_file
from .combo_matcher import (
    build_combo_breakdown_markdown,
    build_combo_report_section_markdown,
    infer_commander_identity,
    load_combo_index,
    match_deck_to_combo_index,
    parse_decklist,
)
from .models import CollectionIndex
from .normalization import canonical_identity, normalize_card_name
from .reporting import build_combo_ai_handoff_prompt_addendum

# v0.11.3-dev: resolve combo indexes from the active runtime data folder.
_RUNTIME_PATHS = get_runtime_paths()
COMBO_INDEX_PATH = _RUNTIME_PATHS.combo_index_json
COMBO_PARITY_INDEX_PATH = _RUNTIME_PATHS.combo_index_parity_json


def _safe_int(value: object, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _identity_map_from_main_scryfall_lookup(scryfall_lookup: dict[str, dict[str, Any]] | None) -> dict[str, set[str]]:
    identity_by_name: dict[str, set[str]] = {}
    for name, card in (scryfall_lookup or {}).items():
        if not isinstance(card, dict):
            continue
        card_name = card.get("name") or name
        identity = card.get("color_identity")
        if identity is None:
            identity = card.get("colorIdentity")
        if identity is None:
            identity = card.get("identity")
        identity_by_name[normalize_card_name(card_name)] = canonical_identity(identity)
    return identity_by_name


def _load_runtime_collection_index(runtime_config: RuntimeConfig) -> tuple[CollectionIndex | None, bool]:
    """Load combo-awareness collection data from the current runtime config.

    This intentionally mirrors the user's collection choice instead of always
    scanning collection/. If no collection mode is selected, collection matching
    is disabled for the combo artifact.
    """
    if getattr(runtime_config, "collection_mode", "none") == "none":
        return None, False

    collection = CollectionIndex()
    selected_files = tuple(getattr(runtime_config, "collection_files", ()) or ())
    if selected_files:
        for raw_path in selected_files:
            path = Path(raw_path)
            if not path.exists() or not path.is_file():
                continue
            try:
                if path.suffix.lower() in {".csv", ".tsv"}:
                    read_csv_collection_file(path, collection)
                else:
                    read_text_collection_file(path, collection)
            except Exception:
                # Optional combo awareness should never break the main report run.
                continue
        return collection, bool(collection.cards_by_normalized_name)

    collection_folder = Path(getattr(runtime_config, "collection_file", "") or "collection")
    if collection_folder.exists() and collection_folder.is_dir():
        for path in sorted(collection_folder.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".txt", ".csv", ".tsv"}:
                continue
            try:
                if path.suffix.lower() in {".csv", ".tsv"}:
                    read_csv_collection_file(path, collection)
                else:
                    read_text_collection_file(path, collection)
            except Exception:
                continue
    return collection, bool(collection.cards_by_normalized_name)


def _build_combo_summaries(
    *,
    deck_file: Path,
    runtime_config: RuntimeConfig,
    include_breakdown: bool,
    scryfall_lookup: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    deck = parse_decklist(deck_file)
    combo_index = load_combo_index(COMBO_INDEX_PATH)
    scryfall_identity_by_name = _identity_map_from_main_scryfall_lookup(scryfall_lookup)
    commander_identity = infer_commander_identity(deck, scryfall_identity_by_name)
    collection, collection_loaded = _load_runtime_collection_index(runtime_config)

    strict_summary = match_deck_to_combo_index(
        deck,
        combo_index,
        commander_identity=commander_identity,
        collection=collection,
        include_spoilers=False,
        strict_color_identity=True,
        hide_invalid_must_be_commander=True,
    )

    result: dict[str, Any] = {
        "deck": deck,
        "commander_identity": commander_identity,
        "combo_index": combo_index,
        "strict_summary": strict_summary,
        "collection_loaded": collection_loaded,
        "parity_summary": None,
        "raw_summary": None,
        "parity_index": None,
    }

    if include_breakdown:
        parity_index = combo_index
        if COMBO_PARITY_INDEX_PATH.exists():
            parity_index = load_combo_index(COMBO_PARITY_INDEX_PATH)

        parity_summary = match_deck_to_combo_index(
            deck,
            parity_index,
            commander_identity=commander_identity,
            collection=collection,
            include_spoilers=False,
            strict_color_identity=True,
            hide_invalid_must_be_commander=False,
        )
        raw_summary = match_deck_to_combo_index(
            deck,
            parity_index,
            commander_identity=None,
            collection=collection,
            include_spoilers=True,
            strict_color_identity=False,
            hide_invalid_must_be_commander=False,
        )
        result.update({
            "parity_summary": parity_summary,
            "raw_summary": raw_summary,
            "parity_index": parity_index,
        })

    return result


def _append_combo_section_to_normal_report(normal_report_path: Path | None, markdown: str) -> None:
    """Append the concise combo section to the normal deck report when available.

    This is intentionally append-only for v0.8.10-dev. It avoids changing the
    normal report builder and keeps the feature fully opt-in through the existing
    Combo Awareness report-section modes.
    """
    if normal_report_path is None:
        return
    path = Path(normal_report_path)
    if not path.exists() or not path.is_file():
        return
    existing = path.read_text(encoding="utf-8")
    combined = existing.rstrip() + "\n\n" + markdown.strip() + "\n"
    path.write_text(combined, encoding="utf-8")



def _append_combo_ai_handoff_to_user_prompt(user_prompt_path: Path | None, markdown: str) -> None:
    """Append Combo Awareness guidance to the generated AI prompt when available.

    This makes opted-in Combo Awareness self-contained for the normal interactive
    AI handoff. Separate combo artifacts remain optional support/dev files.
    """
    if user_prompt_path is None:
        return
    path = Path(user_prompt_path)
    if not path.exists() or not path.is_file():
        return
    existing = path.read_text(encoding="utf-8")
    combined = existing.rstrip() + "\n\n" + markdown.strip() + "\n"
    path.write_text(combined, encoding="utf-8")

def write_optional_combo_awareness_artifacts(
    *,
    deck_file: Path,
    runtime_config: RuntimeConfig,
    normal_folder: Path,
    debug_folder: Path,
    scryfall_lookup: dict[str, dict[str, Any]] | None = None,
    normal_report_path: Path | None = None,
    user_prompt_path: Path | None = None,
) -> list[Path]:
    """Write optional combo awareness artifacts for one backend run.

    Returns written artifact paths. If combo awareness is disabled, returns an empty list.
    Report-section modes also append a concise Combo Awareness section to the
    normal deck report and a Combo Awareness handoff note to the generated
    user-guided prompt when those files exist. Any failure is caught and written as a
    small diagnostic artifact so this optional feature cannot break normal
    Dragon's Touch output generation.
    """
    if not getattr(runtime_config, "combo_awareness_enabled", False):
        return []

    artifact_mode = str(getattr(runtime_config, "combo_awareness_artifact", "report_section") or "report_section").strip().lower()
    if artifact_mode not in {"report_section", "breakdown", "both"}:
        artifact_mode = "report_section"

    write_report_section = artifact_mode in {"report_section", "both"}
    write_breakdown = artifact_mode in {"breakdown", "both"}
    written: list[Path] = []

    try:
        summaries = _build_combo_summaries(
            deck_file=deck_file,
            runtime_config=runtime_config,
            include_breakdown=write_breakdown,
            scryfall_lookup=scryfall_lookup,
        )
        deck = summaries["deck"]
        commander_identity = summaries["commander_identity"]
        strict_summary = summaries["strict_summary"]
        collection_loaded = summaries["collection_loaded"]

        if write_report_section:
            report_limit = _safe_int(getattr(runtime_config, "combo_report_section_potential_limit", 10), 10)
            complete_limit = _safe_int(getattr(runtime_config, "combo_report_section_complete_limit", 10), 10)
            markdown = build_combo_report_section_markdown(
                deck=deck,
                strict_summary=strict_summary,
                commander_identity=commander_identity,
                collection_loaded=collection_loaded,
                max_complete=complete_limit,
                max_collection_potential=report_limit,
                standalone_artifact=True,
            )
            path = get_unique_output_path(normal_folder, "combo_awareness_report_section", ".md")
            written.append(write_text_file(path, markdown))

            embedded_markdown = build_combo_report_section_markdown(
                deck=deck,
                strict_summary=strict_summary,
                commander_identity=commander_identity,
                collection_loaded=collection_loaded,
                max_complete=complete_limit,
                max_collection_potential=report_limit,
                standalone_artifact=False,
            )
            _append_combo_section_to_normal_report(normal_report_path, embedded_markdown)

            ai_handoff_markdown = build_combo_ai_handoff_prompt_addendum(
                deck=deck,
                strict_summary=strict_summary,
                commander_identity=commander_identity,
                collection_loaded=collection_loaded,
            )
            _append_combo_ai_handoff_to_user_prompt(user_prompt_path, ai_handoff_markdown)

        if write_breakdown:
            breakdown_limit = _safe_int(getattr(runtime_config, "combo_breakdown_potential_limit", 25), 25)
            markdown = build_combo_breakdown_markdown(
                deck=deck,
                strict_summary=strict_summary,
                commander_identity=commander_identity,
                index_metadata=summaries["combo_index"].get("metadata", {}),
                collection_loaded=collection_loaded,
                parity_summary=summaries["parity_summary"],
                raw_summary=summaries["raw_summary"],
                parity_index_metadata=(summaries["parity_index"] or {}).get("metadata", {}) if summaries["parity_index"] else {},
                max_complete=0,
                max_potential=breakdown_limit,
            )
            path = get_unique_output_path(debug_folder, "combo_awareness_breakdown", ".md")
            written.append(write_text_file(path, markdown))

    except Exception as exc:  # noqa: BLE001 - optional hook must never break main reports.
        lines = [
            "# v0.8.10-dev — Optional Combo Awareness Hook Error",
            "",
            "Combo awareness was explicitly enabled, but the optional artifact could not be written.",
            "Normal Dragon's Touch report generation was allowed to continue.",
            "",
            f"- Deck file: `{deck_file}`",
            f"- Error: `{type(exc).__name__}: {exc}`",
            "",
            "Scope guard: no API calls were made and normal report / AI prompt generation was allowed to continue.",
        ]
        path = get_unique_output_path(debug_folder, "combo_awareness_error", ".md")
        written.append(write_text_file(path, "\n".join(lines)))

    return written
