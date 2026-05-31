"""Bulk candidate generator — turn a folder of decklists into training candidates.

The corpus problem ("I need hundreds of examples") is solved by automation, not
by hand-authoring: run every deck through a handful of question types with the
local model, AUTO-DISCARD anything the safety net flags (hallucinated ownership,
wrong legality, unverified combos) or that fails to produce structured output
where it should, and write the survivors as *unapproved candidates*. A human
then only has to skim and approve — they never write from scratch.

Candidates are written in the exact corpus record shape the Commander Guide
panel uses, with approved=False. They stay out of the training set until a human
flips approved=True (prepare_dataset is approved-only by default), so generation
can be liberal and curation stays the quality gate.

This module is engine-aware (it builds real analysis per deck) but the QUALITY
GATE (`keep_candidate`) and record shaping are pure and unit-tested.
"""

from __future__ import annotations

from pathlib import Path

from ai.commander_ai_prompts import STRUCTURED_MODES

# (mode, question) asked of every deck. Generic enough to apply to any commander.
DEFAULT_PROMPT_PLAN: list[tuple[str, str]] = [
    ("commander_review", "What is this deck trying to do, and how does it win?"),
    ("cut_review", "What are the weakest cards I could cut, and why?"),
    ("replacement", "What kinds of upgrades would most improve this deck?"),
    ("strategy_tutor", "How should I pilot this deck in a typical game?"),
]


def keep_candidate(response, mode: str) -> tuple[bool, str]:
    """The quality gate. Returns (keep, reason_if_dropped). Pure + testable.

    Keep only answers that: came back ok, passed the safety net (no fabricated
    ownership/legality/combo), and — for modes that should — emitted structured
    output. Everything else is dropped before it can pollute the corpus."""
    if response is None or not getattr(response, "ok", False):
        return False, "model error / no answer"
    if not getattr(response, "safety_ok", False):
        return False, "safety flags (possible hallucination)"
    if mode in STRUCTURED_MODES and getattr(response, "structured", None) is None:
        return False, "no structured output"
    if not (getattr(response, "raw_text", "") or "").strip():
        return False, "empty answer"
    return True, ""


def candidate_record(*, commander, mode, persona, guide_style, question, answer, context_json) -> dict:
    """Shape one corpus record (approved=False) — same schema the panel writes."""
    return {
        "commander": commander,
        "mode": mode,
        "persona": persona,
        "guide_style": guide_style,
        "question": question,
        "answer": answer,
        "context": context_json,
        "approved": False,   # candidate — a human approves later
        "source": "auto-generated",
    }


def generate_for_deck(
    deck_path,
    *,
    service,
    scryfall_lookup,
    persona: str,
    prompt_plan: list[tuple[str, str]],
    on_event=None,
) -> tuple[list[dict], dict]:
    """Generate (and gate) candidates for one deck across the prompt plan.

    Returns (kept_records, stats). Never raises for a single bad prompt; a deck
    that can't be parsed/analyzed raises to the caller to record as an error."""
    import main
    from config import RuntimeConfig
    from parsing.deck_parser import parse_deck_file
    from ai.schemas.ai_context import CommanderAIRequest

    parsed = parse_deck_file(Path(deck_path), scryfall_lookup=scryfall_lookup)
    runtime = RuntimeConfig(
        output_mode="normal", review_direction="both", build_up_config={},
        cut_depth_config={}, prompt_interaction_mode="guided",
        philosophy_key=persona, guide_preference="either",
        intended_bracket="Bracket 3", collection_mode="none",
    )
    analysis = main.build_analysis_context(parsed, runtime, scryfall_lookup, None)

    kept: list[dict] = []
    stats = {"generated": 0, "kept": 0, "dropped": 0}
    for mode, question in prompt_plan:
        request = CommanderAIRequest(user_text=question, mode=mode)
        try:
            ctx, _ = service.build(request, analysis)
            response = service.answer(request, analysis)
        except Exception as exc:  # noqa: BLE001 - one prompt failing must not abort the deck
            stats["dropped"] += 1
            if on_event:
                on_event("drop", deck=str(deck_path), mode=mode, reason=f"error: {exc!r}")
            continue
        stats["generated"] += 1
        keep, reason = keep_candidate(response, mode)
        if not keep:
            stats["dropped"] += 1
            if on_event:
                on_event("drop", deck=str(deck_path), mode=mode, reason=reason)
            continue
        kept.append(candidate_record(
            commander=ctx.commander.get("commander", "") if isinstance(ctx.commander, dict) else "",
            mode=mode, persona=ctx.persona.get("key", persona) if isinstance(ctx.persona, dict) else persona,
            guide_style=ctx.guide_style, question=question,
            answer=response.raw_text, context_json=ctx.to_json(),
        ))
        stats["kept"] += 1
        if on_event:
            on_event("keep", deck=str(deck_path), mode=mode)
    return kept, stats


def append_candidates(path, records: list[dict]) -> int:
    """Append candidate records to a corpus JSONL. Returns count written."""
    import json

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return len(records)
