"""Structured-output parsing (design §7).

We ask the model to append a fenced ```json block AFTER its prose. This module
splits that response into (clean prose, structured view), defensively:

  - the prose shown to the user has the JSON fence stripped out (clean reading);
  - the JSON is parsed and every field coerced into a CommanderAIStructured;
  - a malformed / missing block never raises — the caller gets the prose intact
    and falls back to text-only.

The contract is "prose is primary, JSON is a bonus": nothing here can break a
response, it can only enrich one.
"""

from __future__ import annotations

import json
import re

from ai.schemas.ai_response import CONFIDENCE_VALUES, CommanderAIStructured

# A fenced JSON block: ```json ... ```  (also tolerates a bare ``` fence whose
# body starts with a brace). We take the LAST such block — the model is told to
# put it after the prose, and a stray earlier fence shouldn't win.
_FENCE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.IGNORECASE | re.DOTALL)

_CUT_KEYS = ("card", "reason", "confidence", "cut_type", "replacement_category")
_PROTECTED_KEYS = ("card", "reason")


def parse_structured_response(text: str) -> tuple[str, CommanderAIStructured | None, bool]:
    """Split a model response into (prose, structured, parse_failed).

    - No JSON fence present       -> (text, None, False)
    - Fence present and parses     -> (prose_without_fence, structured, False)
    - Fence present but unparseable-> (text, None, True)
    """
    raw = text or ""
    matches = list(_FENCE.finditer(raw))
    if not matches:
        return raw.strip(), None, False

    m = matches[-1]
    prose = (raw[: m.start()] + raw[m.end():]).strip()
    try:
        data = json.loads(m.group(1))
    except (json.JSONDecodeError, ValueError):
        # A block was clearly intended but is broken — keep the full text as
        # prose so the user still sees everything, and flag the failure.
        return raw.strip(), None, True

    if not isinstance(data, dict):
        return raw.strip(), None, True

    structured = _coerce(data)
    # If the model emitted an empty/irrelevant object, treat as "no structure"
    # rather than an attached-but-empty view.
    if structured.is_empty():
        return prose, None, False
    return prose, structured, False


# --- coercion (every field defensive; bad input -> sensible empty) ---------

def _coerce(data: dict) -> CommanderAIStructured:
    return CommanderAIStructured(
        summary=_str(data.get("summary")),
        primary_recommendation=_str(data.get("primary_recommendation")),
        confidence=_confidence(data.get("confidence")),
        persona_notes=_str(data.get("persona_notes")),
        possible_cuts=_dict_list(data.get("possible_cuts"), _CUT_KEYS),
        protected_cards=_dict_list(data.get("protected_cards"), _PROTECTED_KEYS),
        replacement_needs=_str_list(data.get("replacement_needs")),
        warnings=_str_list(data.get("warnings")),
        follow_up_questions=_str_list(data.get("follow_up_questions")),
    )


def _str(value: object) -> str:
    if value is None or isinstance(value, (dict, list)):
        return ""
    return str(value).strip()


def _confidence(value: object) -> str:
    v = str(value or "").strip().lower()
    return v if v in CONFIDENCE_VALUES else ""


def _str_list(value: object) -> tuple:
    if not isinstance(value, list):
        return ()
    out = []
    for item in value:
        if isinstance(item, (dict, list)):
            continue
        s = str(item).strip()
        if s:
            out.append(s)
    return tuple(out)


def _dict_list(value: object, keys: tuple) -> tuple:
    if not isinstance(value, list):
        return ()
    out = []
    for item in value:
        if not isinstance(item, dict):
            continue
        entry = {}
        for k in keys:
            if k in item and item[k] is not None and not isinstance(item[k], (dict, list)):
                cleaned = str(item[k]).strip()
                if cleaned:
                    entry[k] = cleaned
        # keep only entries that name a card — a cut/protected row without a
        # card is noise.
        if entry.get("card"):
            out.append(entry)
    return tuple(out)
