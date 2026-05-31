"""Turn the curated corpus into a fine-tune-ready dataset.

The whole point of grounding the model also governs how we train it: each
training example must mirror the EXACT prompt the live layer produces at
inference — system (identity + guardrails + mode + persona + guide style) and
user (verified context JSON + warnings + uncertainties + mode focus + the user's
question) — paired with the approved answer. Train on anything less and the
fine-tune won't transfer to the grounded inference path.

We can rebuild that triple from a saved corpus record because the record stores
the serialized CommanderAIContext (`context`), which round-trips back through
CommanderAIContext.from_payload() into the same build_system_prompt /
build_user_prompt the service uses.

Output = chat-format JSONL, one object per line:
    {"messages": [ {role: system}, {role: user}, {role: assistant} ]}
which is what Unsloth / Axolotl / LLaMA-Factory consume with a chat template.
"""

from __future__ import annotations

import json

from ai.commander_ai_prompts import build_messages
from ai.commander_ai_tools import render_card_facts_block, resolve_facts_for_text
from ai.schemas.ai_context import CommanderAIContext
from ai.training.corpus import clean_corpus


def _facts_for(ctx: CommanderAIContext, scryfall_lookup) -> str:
    """Reproduce the service's verified-facts block (cards the user named)."""
    if not scryfall_lookup:
        return ""
    text = " ".join(
        [ctx.user_request or ""]
        + [str(x) for x in (ctx.pet_cards or [])]
        + [str(x) for x in (ctx.user_constraints or [])]
    )
    return render_card_facts_block(resolve_facts_for_text(text, scryfall_lookup))


def record_to_example(record: dict, *, scryfall_lookup=None) -> dict | None:
    """One corpus record -> a {"messages": [...]} training example.

    Returns None if the record can't be rebuilt (missing/invalid context or
    answer) — the caller skips it rather than emitting a broken example.
    """
    if not isinstance(record, dict):
        return None
    answer = str(record.get("answer", "")).strip()
    raw_ctx = record.get("context")
    if not answer or not isinstance(raw_ctx, str) or not raw_ctx.strip():
        return None
    try:
        payload = json.loads(raw_ctx)
    except (json.JSONDecodeError, ValueError):
        return None

    ctx = CommanderAIContext.from_payload(payload)
    messages = build_messages(ctx, verified_card_facts=_facts_for(ctx, scryfall_lookup))
    messages.append({"role": "assistant", "content": answer})
    return {"messages": messages}


def corpus_to_dataset(
    records: list[dict],
    *,
    scryfall_lookup=None,
    approved_only: bool = True,
) -> tuple[list[dict], dict]:
    """Clean the corpus (valid + deduped + approved), then convert to examples.

    Returns (examples, report) where report explains what was dropped at each
    stage so the maintainer can see why the dataset is the size it is.
    """
    cleaned, clean_report = clean_corpus(records, approved_only=approved_only)
    examples: list[dict] = []
    skipped = 0
    for rec in cleaned:
        ex = record_to_example(rec, scryfall_lookup=scryfall_lookup)
        if ex is None:
            skipped += 1
            continue
        examples.append(ex)
    report = dict(clean_report)
    report["dropped_unbuildable"] = skipped
    report["examples"] = len(examples)
    return examples, report


def write_dataset(path, examples: list[dict]):
    from pathlib import Path

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        for ex in examples:
            fh.write(json.dumps(ex, ensure_ascii=False) + "\n")
    return p
