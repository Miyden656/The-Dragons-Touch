"""Deck Coach Workbench — Phase 3: the steering wheel (selection + feedback).

Models the user's picks from the coach view — which cards they want to KEEP, plan
to CUT, or are considering to ADD — as their TARGET, and translates those picks
back into the EXISTING user-intent channels so they steer both:

  (a) the Commander Guide, via CommanderAIRequest.pet_cards / .constraints
      (the only place user-named pet cards + constraints already enter the prompt);
  (b) a refined analysis run, via the runtime-config intake aliases
      protected_cards / declared_constraints.

WHY THIS SHAPE (guardrails — keep these true):
- The AI prompt FORMAT never changes. Picks enter exactly where pet cards and
  user constraints already enter; the serializer already merges them into
  ctx.pet_cards / ctx.user_constraints. No new prompt field, no new schema.
- Picks are USER INTENT — they STEER, they do not override legality or engine
  truth. "Keep" becomes PROTECTED (honest protection, like a declared pet card),
  not a forced keep. "Cut"/"Add" become DECLARED intent (free-text constraints /
  notes), not forced engine mutations — the user, not the engine, removes a card.
- Pure data translation: no engine call, no model call, never raises.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from ai.schemas.ai_context import ALL_MODES, MODE_COMMANDER_REVIEW, CommanderAIRequest


# Runtime-config intake aliases recognised by
# philosophy.runtime_config_mapping (PROTECTED_CARDS_KEYS / DECLARED_CONSTRAINTS_KEYS)
# and analysis.pilot_intent — so a refined analysis run reads the picks as intent.
_OVERLAY_PROTECTED_KEY = "protected_cards"
_OVERLAY_CONSTRAINTS_KEY = "declared_constraints"

# How cut/add intent is phrased as a free-text constraint. Plain English so the
# grounded prompt + the model read it as the user's stated plan.
_CUT_PREFIX = "Planning to cut: "
_ADD_PREFIX = "Considering adding: "


@dataclass
class CoachPicks:
    """The user's steering picks over a coach view.

    keep / cut / add are card NAMES the user selected. note is a freeform steering
    line ("lean more aristocrats", "keep it budget"). Everything is optional; an
    empty CoachPicks is a valid no-op.
    """

    keep: list[str] = field(default_factory=list)
    cut: list[str] = field(default_factory=list)
    add: list[str] = field(default_factory=list)
    note: str = ""

    def is_empty(self) -> bool:
        return not (self.keep or self.cut or self.add or (self.note or "").strip())

    def to_dict(self) -> dict[str, Any]:
        return {
            "keep": list(self.keep),
            "cut": list(self.cut),
            "add": list(self.add),
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> "CoachPicks":
        data = data or {}
        return cls(
            keep=_clean_names(data.get("keep")),
            cut=_clean_names(data.get("cut")),
            add=_clean_names(data.get("add")),
            note=str(data.get("note") or "").strip(),
        )


# --- translation into the existing intent channels ------------------------

def picks_to_request_inputs(picks: CoachPicks) -> dict[str, tuple[str, ...]]:
    """Translate picks into CommanderAIRequest fields (pet_cards + constraints).

    Returns {"pet_cards": (...), "constraints": (...)} — the exact channels the
    serializer already merges into ctx.pet_cards / ctx.user_constraints, so the
    Commander Guide sees the user's target with no prompt-format change.
    """
    return {
        "pet_cards": tuple(_dedup(picks.keep)),
        "constraints": tuple(_intent_constraints(picks)),
    }


def build_request(
    picks: CoachPicks,
    *,
    user_text: str = "",
    mode: str = MODE_COMMANDER_REVIEW,
    guide_style: str = "",
) -> CommanderAIRequest:
    """Build a ready-to-serialize CommanderAIRequest carrying the picks as intent."""
    inputs = picks_to_request_inputs(picks)
    resolved_mode = mode if mode in ALL_MODES else MODE_COMMANDER_REVIEW
    return CommanderAIRequest(
        user_text=user_text,
        mode=resolved_mode,
        pet_cards=inputs["pet_cards"],
        constraints=inputs["constraints"],
        guide_style=guide_style,
    )


def picks_to_runtime_overlay(picks: CoachPicks) -> dict[str, Any]:
    """Translate picks into a runtime-config OVERLAY for a refined analysis run.

    Returns {"protected_cards": [...], "declared_constraints": [...]} keyed by the
    intake aliases runtime_config_mapping/pilot_intent recognise. The page MERGES
    this onto the existing RuntimeConfig before re-running build_analysis_context;
    keeps are protected from cuts, cut/add ride along as declared intent. Legality
    and engine truth still win — picks steer, never override.
    """
    overlay: dict[str, Any] = {}
    keep = _dedup(picks.keep)
    constraints = _intent_constraints(picks)
    if keep:
        overlay[_OVERLAY_PROTECTED_KEY] = keep
    if constraints:
        overlay[_OVERLAY_CONSTRAINTS_KEY] = constraints
    return overlay


# --- internals ------------------------------------------------------------

def _intent_constraints(picks: CoachPicks) -> list[str]:
    """The cut / add / note picks as plain-English constraint lines."""
    out: list[str] = []
    cut = _dedup(picks.cut)
    add = _dedup(picks.add)
    if cut:
        out.append(_CUT_PREFIX + ", ".join(cut))
    if add:
        out.append(_ADD_PREFIX + ", ".join(add))
    note = (picks.note or "").strip()
    if note:
        out.append(note)
    return out


def _clean_names(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        items: Iterable[Any] = [value]
    else:
        try:
            items = list(value)
        except TypeError:
            items = [value]
    return _dedup(items)


def _dedup(names: Iterable[Any]) -> list[str]:
    """Trimmed, de-duplicated, order-preserving card-name list."""
    out: list[str] = []
    seen: set[str] = set()
    for raw in names or []:
        name = str(raw).strip()
        if name and name not in seen:
            seen.add(name)
            out.append(name)
    return out
