"""Philosophy + Bracket Build Preference Preview for Build From Collection v1.3.15.

This module records player-facing philosophy/persona and bracket preferences so
Commander’s Call can later narrow deck building by how the user wants the deck
to feel and play.

Marker: Philosophy + Bracket Build Preference UI.
Marker: main_philosophy.
Marker: sub_philosophy.
Marker: persona.
Marker: bracket_preference.
Marker: philosophy selection carried into setup summary.
Marker: bracket preference carried into setup summary.
Marker: No exact card selection.
Marker: No role-count target generation.
Marker: No mana-base generation.
Marker: No land insertion.
Marker: No shell generation.
Marker: No deck generation.
Marker: Basic lands are assumed available.
Marker: Nonbasic lands remain collection-first unless outside-collection upgrades are allowed by the user.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

MAIN_PHILOSOPHY_OPTIONS: tuple[str, ...] = (
    "No Philosophy / Adventurer Guide",
    "Timmy/Tammy",
    "Johnny/Jenny",
    "Spike",
    "Hybrid / Mixed",
)

SUB_PHILOSOPHY_OPTIONS: tuple[str, ...] = (
    "No Persona / Not Sure Yet",
    "Big Moment — Michael / Michelle",
    "Big Creature / Stompy — Alexander / Alexandria",
    "Theme / Vibe — Benjamin / Bethany",
    "Pet Card — Milo / Mia",
    "Let Me Do My Thing — William / Willow",
    "Battlecruiser — Aaron / Ariana",
    "Engine Builder — Brad / Bria",
    "Commander Exploiter — Kyle / Katie",
    "Weird Card Rescuer — Elund / Emily",
    "Theme Mechanic Inventor — Brandon / Brenda",
    "Self-Imposed Constraint Builder — Clark / Clarissa",
    "Combo Builder — Jasper / Jennifer",
    "Consistency Maximizer — Avery",
    "Efficiency Optimizer — Jordan",
    "Curve and Mana Discipline — River",
    "Competitive Closer — Charlie",
    "Power-Level Calibrator — Kai",
    "Interaction Controller — Riley",
)

BRACKET_PREFERENCE_OPTIONS: tuple[str, ...] = (
    "Not Sure Yet",
    "Bracket 1 — Low Power / Precon-Friendly",
    "Bracket 2 — Casual Upgraded",
    "Bracket 3 — Strong Casual",
    "Bracket 4 — High Power",
    "Bracket 5 — cEDH / Competitive",
)


def _clean(value: str | None) -> str:
    return str(value or "").strip()


def philosophy_main_options() -> tuple[str, ...]:
    """Return available main philosophy options for Commander’s Call."""
    return MAIN_PHILOSOPHY_OPTIONS


def philosophy_sub_options() -> tuple[str, ...]:
    """Return available sub-philosophy/persona options for Commander’s Call."""
    return SUB_PHILOSOPHY_OPTIONS


def bracket_preference_options() -> tuple[str, ...]:
    """Return available bracket preference options for Commander’s Call."""
    return BRACKET_PREFERENCE_OPTIONS


def normalize_philosophy_choice(value: str | None) -> str:
    """Normalize a philosophy UI value without changing the user-facing label."""
    cleaned = _clean(value)
    return cleaned or "No Philosophy / Adventurer Guide"


def normalize_sub_philosophy_choice(value: str | None) -> str:
    """Normalize a sub-philosophy/persona UI value."""
    cleaned = _clean(value)
    return cleaned or "No Persona / Not Sure Yet"


def normalize_bracket_preference(value: str | None) -> str:
    """Normalize a bracket preference UI value."""
    cleaned = _clean(value)
    return cleaned or "Not Sure Yet"


@dataclass(slots=True)
class PhilosophyBracketBuildPreferencePreview:
    """Preview-only philosophy/persona/bracket preference payload."""

    main_philosophy: str = "No Philosophy / Adventurer Guide"
    sub_philosophy: str = "No Persona / Not Sure Yet"
    persona: str = "No Persona / Not Sure Yet"
    bracket_preference: str = "Not Sure Yet"
    user_override_allowed: bool = True
    preference_source: str = "user-selected setup preference"
    preview_name: str = "Philosophy + Bracket Build Preference UI"
    preview_version: str = "v1.3.15"
    preview_only: bool = True
    exact_card_selection: bool = False
    role_count_target_generated: bool = False
    mana_base_generated: bool = False
    land_inserted: bool = False
    shell_generated: bool = False
    deck_generated: bool = False
    deferred_behavior: tuple[str, ...] = field(default_factory=lambda: (
        "No exact card selection",
        "No role-count target generation",
        "No mana-base generation",
        "No land insertion",
        "No shell generation",
        "No deck generation",
        "No normal deck review changes",
        "Philosophy preference narrows future deck-building choices only",
        "Bracket preference narrows future power-level expectations only",
    ))

    def to_dict(self) -> dict[str, Any]:
        return {
            "preview_name": self.preview_name,
            "preview_version": self.preview_version,
            "preview_only": self.preview_only,
            "main_philosophy": self.main_philosophy,
            "sub_philosophy": self.sub_philosophy,
            "persona": self.persona,
            "bracket_preference": self.bracket_preference,
            "user_override_allowed": self.user_override_allowed,
            "preference_source": self.preference_source,
            "exact_card_selection": self.exact_card_selection,
            "role_count_target_generated": self.role_count_target_generated,
            "mana_base_generated": self.mana_base_generated,
            "land_inserted": self.land_inserted,
            "shell_generated": self.shell_generated,
            "deck_generated": self.deck_generated,
            "deferred_behavior": list(self.deferred_behavior),
            "v1_3_15_boundary": (
                "Philosophy + Bracket Build Preference UI records user-selected playstyle and bracket context only. "
                "It does not select exact cards, create role-count targets, generate a mana base, insert lands, generate a shell, generate a deck, score cards, recommend cuts, or change normal deck review behavior. "
                "Basic lands are assumed available; nonbasic lands remain collection-first unless outside-collection upgrades are allowed by the user."
            ),
        }


def create_philosophy_bracket_build_preference_preview(
    *,
    main_philosophy: str = "No Philosophy / Adventurer Guide",
    sub_philosophy: str = "No Persona / Not Sure Yet",
    persona: str = "",
    bracket_preference: str = "Not Sure Yet",
    user_override_allowed: bool = True,
) -> PhilosophyBracketBuildPreferencePreview:
    """Create a preview-only philosophy/bracket payload without generating cards."""
    normalized_sub = normalize_sub_philosophy_choice(sub_philosophy or persona)
    return PhilosophyBracketBuildPreferencePreview(
        main_philosophy=normalize_philosophy_choice(main_philosophy),
        sub_philosophy=normalized_sub,
        persona=normalize_sub_philosophy_choice(persona or normalized_sub),
        bracket_preference=normalize_bracket_preference(bracket_preference),
        user_override_allowed=user_override_allowed,
    )


def philosophy_bracket_preview_lines(preview: PhilosophyBracketBuildPreferencePreview) -> tuple[str, ...]:
    """Return concise UI/report lines for philosophy and bracket preferences."""
    data = preview.to_dict()
    return (
        "Philosophy + Bracket Build Preference Preview created.",
        "This is player-preference setup context only; it does not build the deck.",
        f"Main philosophy: {data.get('main_philosophy') or 'Not selected yet'}",
        f"Sub-philosophy/persona: {data.get('sub_philosophy') or data.get('persona') or 'Not selected yet'}",
        f"Bracket preference: {data.get('bracket_preference') or 'Not Sure Yet'}",
        "Philosophy and bracket preferences will narrow future deck-building choices.",
        "No exact card selection.",
        "No role-count target generation.",
        "No mana-base generation.",
        "No land insertion.",
        "No shell generation.",
        "No deck generation.",
    )
