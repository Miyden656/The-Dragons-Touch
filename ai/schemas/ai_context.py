"""Request and context schemas for the Commander AI layer.

CommanderAIRequest  — what the user/UI asks for (the only place free-text and
                      user-named pet cards / constraints enter the system).
CommanderAIContext  — the compact, engine-verified payload handed to the model.

The context is intentionally NESTED (commander / strategy / cuts / ...) rather
than one flat 30-field bag. It carries the same information as the design's
context object but groups it by responsibility so each sub-builder owns one
section. `to_payload()` flattens it to a plain JSON-safe dict for the prompt.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field


# --- Interaction modes (one per design §5.3) ------------------------------
MODE_COMMANDER_REVIEW = "commander_review"
MODE_BUILD_FROM_COLLECTION = "build_from_collection"
MODE_CUT_REVIEW = "cut_review"
MODE_REPLACEMENT = "replacement"
MODE_STRATEGY_TUTOR = "strategy_tutor"
MODE_PERSONA_COACHING = "persona_coaching"

ALL_MODES = (
    MODE_COMMANDER_REVIEW,
    MODE_BUILD_FROM_COLLECTION,
    MODE_CUT_REVIEW,
    MODE_REPLACEMENT,
    MODE_STRATEGY_TUTOR,
    MODE_PERSONA_COACHING,
)


@dataclass(frozen=True)
class CommanderAIRequest:
    """A single ask from the user/UI.

    pet_cards and constraints are USER-PROVIDED only. The engine never infers a
    pet card; the user names it. This keeps persona protection honest.
    """

    user_text: str = ""
    mode: str = MODE_COMMANDER_REVIEW
    pet_cards: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    guide_style: str = ""  # optional per-request override of the configured style

    def normalized_mode(self) -> str:
        return self.mode if self.mode in ALL_MODES else MODE_COMMANDER_REVIEW


@dataclass
class CommanderAIContext:
    """Compact, engine-verified context for one model turn.

    Every nested value is already a plain JSON-safe type (str/int/bool/list/dict)
    produced by the ai/context builders. `to_payload()` / `to_json()` are the
    only things the prompt layer needs.
    """

    user_request: str = ""
    mode: str = MODE_COMMANDER_REVIEW

    commander: dict = field(default_factory=dict)
    legality: dict = field(default_factory=dict)
    decklist: list = field(default_factory=list)
    strategy: dict = field(default_factory=dict)
    bracket: dict = field(default_factory=dict)
    multiplayer: dict = field(default_factory=dict)   # 4-player pod value facts
    political: dict = field(default_factory=dict)     # Section-3 political archetypes
    cuts: dict = field(default_factory=dict)          # ONLY removable candidates
    protected: dict = field(default_factory=dict)     # KEEPs — never cuttable
    replacements: dict = field(default_factory=dict)  # ADDs — never cuttable
    collection: dict = field(default_factory=dict)
    combo: dict = field(default_factory=dict)

    persona: dict = field(default_factory=dict)
    guide_style: str = "adventurer"
    pet_cards: list = field(default_factory=list)
    user_constraints: list = field(default_factory=list)
    rescue_cards: list = field(default_factory=list)       # weird card(s) being rescued
    hybrid_themes: list = field(default_factory=list)      # two themes to bridge
    theme_intent: str = ""                                 # the pilot's stated theme/vibe

    win_conditions: list = field(default_factory=list)
    uncertainties: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    def to_payload(self) -> dict:
        """Plain JSON-safe dict for embedding in the prompt."""
        return asdict(self)

    def to_json(self, *, indent: int | None = 2) -> str:
        return json.dumps(self.to_payload(), indent=indent, ensure_ascii=False, default=str)

    @classmethod
    def from_payload(cls, payload: dict) -> "CommanderAIContext":
        """Rebuild a context from a to_payload()/to_json() dict (e.g. a stored
        training record). Unknown keys are ignored; missing keys take defaults."""
        import dataclasses

        if not isinstance(payload, dict):
            return cls()
        valid = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in payload.items() if k in valid})

    def all_card_names(self) -> set[str]:
        """Every card name that appears anywhere in this context.

        Used by tests (and later by the safety layer) to assert the serializer
        never introduced a name that wasn't in the engine data.
        """
        names: set[str] = set()

        for entry in self.decklist:
            name = (entry or {}).get("name") if isinstance(entry, dict) else None
            if name:
                names.add(str(name))

        def _collect(container: dict, list_keys: tuple[str, ...]) -> None:
            for key in list_keys:
                for item in container.get(key, []) or []:
                    if isinstance(item, dict):
                        for nk in ("card", "card_name", "name"):
                            if item.get(nk):
                                names.add(str(item[nk]))
                                break
                    elif isinstance(item, str):
                        names.add(item)

        _collect(self.cuts, ("required_cuts", "optional_cuts", "manual_review", "playtest_first"))
        _collect(self.protected, ("protected_from_cut", "protected_cards"))
        _collect(self.replacements, ("candidates", "collection_candidates"))
        _collect(self.strategy, ("strong_synergy_cards", "possible_off_plan_cards"))
        _collect(self.bracket, ("pressure_cards",))
        # Multiplayer example cards are grouped by dimension (a dict of name-lists);
        # every entry is an engine card name, so include them in the guard set.
        for example_list in (self.multiplayer.get("example_cards") or {}).values():
            for n in example_list or []:
                if n:
                    names.add(str(n))
        # Political archetype example cards (per detected archetype) are engine
        # card names too — include them so the no-invention guard holds.
        def _political_examples(block: dict) -> None:
            if isinstance(block, dict):
                for n in block.get("example_cards", []) or []:
                    if n:
                        names.add(str(n))
        _political_examples(self.political.get("primary") or {})
        _political_examples(self.political.get("secondary") or {})
        for d in self.political.get("detected", []) or []:
            _political_examples(d if isinstance(d, dict) else {})
        for n in self.win_conditions:
            if n:
                names.add(str(n))
        return names
