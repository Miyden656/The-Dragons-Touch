"""Response schema for the Commander AI layer.

CommanderAIResponse is what the service returns and the UI/CLI consume. It
carries the human-readable answer, safety results, a typed error channel, and
(Phase 6b) an optional STRUCTURED view parsed from a trailing JSON block the
model emits after its prose (design §7). The prose stays primary; structured
fields are a bonus the app can read. Parsing never fails the response: a
malformed block leaves `structured=None` and `parse_failed=True`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

CONFIDENCE_VALUES = ("low", "medium", "high")


@dataclass(frozen=True)
class CommanderAIStructured:
    """Machine-readable mirror of the model's prose (design §7).

    Every field is optional; the model fills only what its mode warrants. Lists
    of dicts use a fixed key set so the UI can render them without guessing.
    """

    summary: str = ""
    primary_recommendation: str = ""
    confidence: str = ""        # one of CONFIDENCE_VALUES, or "" if unstated/invalid
    persona_notes: str = ""
    possible_cuts: tuple = ()        # {card, reason, confidence, cut_type, replacement_category}
    protected_cards: tuple = ()      # {card, reason}
    replacement_needs: tuple = ()    # list[str]
    warnings: tuple = ()             # list[str]
    follow_up_questions: tuple = ()  # list[str]

    def is_empty(self) -> bool:
        return not any(
            (
                self.summary, self.primary_recommendation, self.confidence,
                self.persona_notes, self.possible_cuts, self.protected_cards,
                self.replacement_needs, self.warnings, self.follow_up_questions,
            )
        )

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "primary_recommendation": self.primary_recommendation,
            "confidence": self.confidence,
            "persona_notes": self.persona_notes,
            "possible_cuts": [dict(c) for c in self.possible_cuts],
            "protected_cards": [dict(c) for c in self.protected_cards],
            "replacement_needs": list(self.replacement_needs),
            "warnings": list(self.warnings),
            "follow_up_questions": list(self.follow_up_questions),
        }


@dataclass(frozen=True)
class CommanderAIResponse:
    ok: bool
    text: str = ""              # answer to show the user (safety-annotated in strict mode)
    raw_text: str = ""          # the model's original text, before safety annotation
    mode: str = ""
    guide_style: str = ""
    model: str = ""
    error: str = ""             # friendly message when ok is False
    error_kind: str = ""        # machine kind: "offline"|"timeout"|"model_missing"|...
    safety_ok: bool = True      # False if the claim-checker flagged anything
    safety_flags: tuple = ()    # tuple of {kind, card, note} dicts
    structured: CommanderAIStructured | None = None  # parsed JSON view, if present
    parse_failed: bool = False  # True if a JSON block was present but unparseable
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "text": self.text,
            "raw_text": self.raw_text,
            "mode": self.mode,
            "guide_style": self.guide_style,
            "model": self.model,
            "error": self.error,
            "error_kind": self.error_kind,
            "safety_ok": self.safety_ok,
            "safety_flags": list(self.safety_flags),
            "structured": self.structured.to_dict() if self.structured else None,
            "parse_failed": self.parse_failed,
            "meta": dict(self.meta),
        }

    @classmethod
    def from_error(cls, *, error: str, kind: str, mode: str = "", model: str = "") -> "CommanderAIResponse":
        # The friendly error also becomes the visible text so a UI can render one field.
        return cls(ok=False, text=error, error=error, error_kind=kind, mode=mode, model=model)
