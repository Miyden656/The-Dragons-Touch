"""Master context serializer.

serialize_context(analysis, request, *, guide_style, combo_summary) takes the
engine's analysis dict (the value returned by main.build_analysis_context) plus
a CommanderAIRequest and returns a compact, engine-verified CommanderAIContext.

It NEVER calls the engine and NEVER invents data. It only reads, defensively,
from the objects the engine already produced — so it is decoupled from which
build_analysis_context produced the dict and resilient to field churn.
"""

from __future__ import annotations

from typing import Any

from ai.commander_ai_config import DEFAULT_GUIDE_STYLE, normalize_guide_style
from ai.context.bracket_context import build_bracket_view
from ai.context.collection_context import build_collection_view
from ai.context.combo_context import build_combo_view
from ai.context.cut_context import build_cut_view
from ai.context.deck_context import (
    build_deck_view,
    build_legality_view,
    win_conditions_from_roles,
)
from ai.context.multiplayer_context import build_multiplayer_view
from ai.context.political_context import build_political_view
from ai.context.replacement_context import build_replacement_view
from ai.context.safe_access import as_list, as_str, attr
from ai.context.strategy_context import build_strategy_view
from ai.schemas.ai_context import CommanderAIContext, CommanderAIRequest


def serialize_context(
    analysis: dict | None,
    request: CommanderAIRequest | None = None,
    *,
    guide_style: str = DEFAULT_GUIDE_STYLE,
    combo_summary: Any | None = None,
) -> CommanderAIContext:
    analysis = analysis or {}
    request = request or CommanderAIRequest()

    parsed_deck = analysis.get("parsed_deck")
    command_zone = analysis.get("command_zone")
    legality = analysis.get("legality")
    role_summary = analysis.get("role_summary")
    strategy_summary = analysis.get("strategy_summary")
    plan_fit_summary = analysis.get("plan_fit_summary")
    bracket_summary = analysis.get("bracket_summary")
    multiplayer_summary = analysis.get("multiplayer_summary")
    political_summary = analysis.get("political_summary")
    possible_cuts = analysis.get("possible_cuts")
    protected_cards = analysis.get("protected_cards")
    replacement_needs = analysis.get("replacement_needs")
    replacement_candidates = analysis.get("replacement_candidates")
    collection_candidates = analysis.get("collection_candidates")
    collection_summary = analysis.get("collection_summary")
    philosophy_context = analysis.get("philosophy_context") or {}
    runtime_config = analysis.get("runtime_config")

    truncation: dict[str, int] = {}

    deck_view = build_deck_view(parsed_deck, command_zone, role_summary)
    legality_view = build_legality_view(parsed_deck, legality)
    strategy_view, d = build_strategy_view(strategy_summary, plan_fit_summary)
    truncation.update(d)
    bracket_view, d = build_bracket_view(bracket_summary, runtime_config)
    truncation.update(d)
    multiplayer_view, d = build_multiplayer_view(multiplayer_summary)
    truncation.update(d)
    political_view, d = build_political_view(political_summary)
    truncation.update(d)
    cut_view, d = build_cut_view(possible_cuts, protected_cards)
    truncation.update(d)
    # Move KEEP cards OUT of the `cuts` block into their own top-level `protected`
    # section. Nesting protected cards under a key named "cuts" caused small models
    # to list them (even the commander) as cuts. Now `cuts` holds only removables.
    protected_view = {
        "protected_from_cut": cut_view.pop("protected_from_cut", []),
        "protected_cards": cut_view.pop("protected_cards", []),
    }
    replacement_view, d = build_replacement_view(
        replacement_needs, replacement_candidates, collection_candidates
    )
    truncation.update(d)
    collection_view = build_collection_view(collection_summary)
    combo_view, combo_available = build_combo_view(combo_summary)

    persona_view = _build_persona_view(philosophy_context)
    resolved_style = normalize_guide_style(request.guide_style or guide_style)

    # Pilot intent: user-declared inputs from the run config (intake windows) merged
    # with anything passed on the chat request. Lets the guide see pet cards, the
    # self-imposed rule, rescue targets, and theme/vibe even outside a chat turn.
    from analysis.pilot_intent import pilot_intent_from_runtime_config

    intent = pilot_intent_from_runtime_config(runtime_config)

    def _merge(primary: Any, extra: tuple) -> list[str]:
        out: list[str] = []
        for item in [as_str(p) for p in as_list(primary)] + [as_str(e) for e in extra]:
            if item and item not in out:
                out.append(item)
        return out

    win_conditions = win_conditions_from_roles(role_summary)

    ctx = CommanderAIContext(
        user_request=as_str(request.user_text),
        mode=request.normalized_mode(),
        commander={k: deck_view[k] for k in deck_view if k != "decklist"},
        legality=legality_view,
        decklist=deck_view.get("decklist", []),
        strategy=strategy_view,
        bracket=bracket_view,
        multiplayer=multiplayer_view,
        political=political_view,
        cuts=cut_view,
        protected=protected_view,
        replacements=replacement_view,
        collection=collection_view,
        combo=combo_view,
        persona=persona_view,
        guide_style=resolved_style,
        pet_cards=_merge(request.pet_cards, intent.pet_cards),
        user_constraints=_merge(request.constraints, intent.constraints),
        rescue_cards=list(intent.rescue_cards),
        hybrid_themes=list(intent.hybrid_themes),
        theme_intent=intent.theme_intent,
        win_conditions=win_conditions,
        uncertainties=[],
        warnings=[],
        meta={
            "version_label": as_str(analysis.get("version_label"), "unknown"),
            "schema": "commander_ai_context/v1",
            "truncation": truncation,
        },
    )

    ctx.warnings = _collect_warnings(legality_view, bracket_view)
    ctx.uncertainties = _collect_uncertainties(
        analysis_present=bool(analysis),
        legality_view=legality_view,
        strategy_view=strategy_view,
        collection_view=collection_view,
        combo_available=combo_available,
        win_conditions=win_conditions,
        truncation=truncation,
    )
    return ctx


def serialize_to_payload(*args, **kwargs) -> dict:
    """Convenience: serialize and return the plain JSON-safe dict."""
    return serialize_context(*args, **kwargs).to_payload()


# --- persona --------------------------------------------------------------

def _build_persona_view(philosophy_context: dict) -> dict:
    """Reuse the engine's persona bias lists — do not invent persona behavior."""
    pc = philosophy_context or {}
    key = as_str(pc.get("key"), "balanced_unknown")
    own_tone, family_tone, family_label = _persona_tones(key, pc)
    return {
        "key": key,
        "label": as_str(pc.get("label"), "Balanced / Unknown"),
        "guide_name": as_str(pc.get("guide_name")),
        # Which named-guide variant the user picked; the voice layer uses this to
        # select a gendered voice variant (falls back to the general voice).
        "guide_presentation": as_str(pc.get("guide_presentation"), "either"),
        "guide_role": as_str(pc.get("guide_role"), "Guide"),
        "core_question": as_str(pc.get("core_question"), "What does this deck want to do?"),
        "rules_summary": as_str(pc.get("rules_summary")),
        # Voice axis: the persona's OWN tone, layered over its family register, so
        # picking a philosophy shifts how the guide speaks (see render_persona_block).
        "tone": own_tone,
        "family_tone": family_tone,
        "family_label": family_label,
        "protect_bias": [as_str(x) for x in as_list(pc.get("protect_bias"))],
        "review_bias": [as_str(x) for x in as_list(pc.get("review_bias"))],
        "replacement_bias": [as_str(x) for x in as_list(pc.get("replacement_bias"))],
    }


def _persona_tones(key: str, pc: dict) -> tuple[str, str, str]:
    """(own_tone, family_tone, family_label) for a persona.

    Each philosophy profile carries its own `tone`; sub-personas also inherit a
    FAMILY register from their parent archetype (Timmy/Johnny/Spike). We surface
    both so the voice blends "same family, own way of speaking". Prefers the
    philosophy_context dict; falls back to the engine profile registry. Defensive
    — any failure degrades to empty strings, never raises."""
    own = as_str(pc.get("tone"))
    family_tone = ""
    family_label = ""
    try:
        from analysis.deck_building_philosophies import (
            PHILOSOPHY_PROFILES,
            get_philosophy_profile,
        )
        prof = get_philosophy_profile(key)
        if not own:
            own = as_str(getattr(prof, "tone", ""))
        parent_key = getattr(prof, "parent", None)
        if parent_key and parent_key in PHILOSOPHY_PROFILES:
            parent = PHILOSOPHY_PROFILES[parent_key]
            family_tone = as_str(getattr(parent, "tone", ""))
            family_label = as_str(getattr(parent, "label", ""))
    except Exception:  # noqa: BLE001 - tone is enrichment, never break serialization
        pass
    return own, family_tone, family_label


# --- diagnostics ----------------------------------------------------------

def _collect_warnings(legality_view: dict, bracket_view: dict) -> list[str]:
    """Hard facts worth surfacing prominently (engine-verified)."""
    out: list[str] = []
    if legality_view.get("banned_cards"):
        out.append(
            "Engine flagged banned card(s): " + ", ".join(legality_view["banned_cards"][:10])
        )
    if legality_view.get("banned_commanders"):
        out.append(
            "Engine flagged banned commander(s): "
            + ", ".join(legality_view["banned_commanders"][:5])
        )
    if not legality_view.get("deck_size_legal", True):
        out.append(
            f"Deck size is not legal: {legality_view.get('deck_card_count')} of "
            f"{legality_view.get('expected_deck_size')} expected."
        )
    if legality_view.get("color_identity_violations"):
        out.append(
            "Color-identity violation(s): "
            + ", ".join(legality_view["color_identity_violations"][:10])
        )
    return out


def _collect_uncertainties(
    *,
    analysis_present: bool,
    legality_view: dict,
    strategy_view: dict,
    collection_view: dict,
    combo_available: bool,
    win_conditions: list,
    truncation: dict,
) -> list[str]:
    """What the model should treat as 'needs checking', stated plainly."""
    out: list[str] = []
    if not analysis_present:
        out.append("No analysis context was provided; treat all deck claims as unverified.")
    if legality_view.get("cards_not_found"):
        out.append(
            f"{len(legality_view['cards_not_found'])} card name(s) were not found in the local "
            "card database; their facts are unverified."
        )
    conf = (strategy_view.get("confidence") or "").lower()
    if conf in {"low", "unknown", ""}:
        out.append(
            f"Strategy confidence is {conf or 'unknown'}; the detected plan may be tentative."
        )
    if not collection_view.get("loaded"):
        out.append(
            "No collection was loaded; cannot speak to what the user owns or build-from-collection."
        )
    if not combo_available:
        out.append("Combo awareness was not run; do not claim the deck has or lacks combos.")
    if not win_conditions:
        out.append(
            "No card was explicitly role-tagged as a win condition; infer win paths cautiously."
        )
    if truncation:
        total = sum(truncation.values())
        out.append(
            f"{total} item(s) across {len(truncation)} list(s) were truncated for length; "
            "ask to see more if needed."
        )
    return out
