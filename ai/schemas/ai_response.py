"""Response schema for the Commander AI layer.

CommanderAIResponse is what the service returns and the UI/CLI consume. Phase 4.5
carries the human-readable answer plus safety results and a typed error channel.
The richer STRUCTURED fields (parsed cuts/replacements/etc., design §7) are added
in Phase 6 — kept out of here until the JSON-output path exists so we don't ship
fields nothing populates.
"""

from __future__ import annotations

from dataclasses import dataclass, field


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
            "meta": dict(self.meta),
        }

    @classmethod
    def from_error(cls, *, error: str, kind: str, mode: str = "", model: str = "") -> "CommanderAIResponse":
        # The friendly error also becomes the visible text so a UI can render one field.
        return cls(ok=False, text=error, error=error, error_kind=kind, mode=mode, model=model)
