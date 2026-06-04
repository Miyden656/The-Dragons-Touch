"""Deck Coach Workbench — Phase 1 data layer (headless).

Restructures reasoning the engine ALREADY produces — per-card cut tiers, kept /
protected cards, replacement directions + engine-verified add candidates, and the
detected deck plan & synergies — into a single structured *coach view*, narrated
in the chosen philosophy lens's VOICE. The framing is deliberately "a Magic-expert
friend giving you their take: an OPINION you're free to disagree with", never a
verdict.

WHAT THIS IS NOT (guardrails — keep these true):
- It does NOT call the engine, score cards, choose cuts, or change any decision.
- It REUSES the engine's voiced language registries
  (philosophy/cut_explanation_wiring, protected_explanation_wiring,
  replacement_explanation_wiring) and the AI context builders (ai/context/*) — it
  adds no card reasoning of its own.
- The AI prompt pipeline + v1.6 scoring + the capped philosophy bias are untouched.
- Player picks are USER intent (Phase 3); this layer only renders truth + opinion.

It reads, defensively, the SAME analysis dict that main.build_analysis_context
produces (via the ai/context view builders, which use safe_access), so it survives
engine field churn. Output: a CoachView the workbench page renders + the exporter
writes (to_dict / to_text). Phase 1 is fully headless.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from ai.context.cut_context import build_cut_view
from ai.context.deck_context import build_deck_view
from ai.context.replacement_context import build_replacement_view
from ai.context.strategy_context import build_strategy_view

from analysis.deck_building_philosophies import get_philosophy_profile

from philosophy.cut_explanation_wiring import build_philosophy_cut_explanation
from philosophy.protected_explanation_wiring import build_philosophy_protected_explanation
from philosophy.replacement_explanation_wiring import build_philosophy_replacement_explanation
from philosophy.report_section import format_persona_opening
from philosophy.runtime_config_mapping import context_from_runtime_config


# Engine review_direction tokens. The engine also uses "both"; we treat anything
# that is not an explicit build-up signal as cut-down for ordering purposes.
DIRECTION_CUT_DOWN = "cut_down"
DIRECTION_BUILD_UP = "build_up"

# The cut tiers the engine separates, paired with how the coach view labels them.
# Order matters: required first, then optional, then the softer review buckets.
_CUT_TIERS: tuple[tuple[str, str], ...] = (
    ("required_cuts", "required"),
    ("optional_cuts", "optional"),
    ("manual_review", "manual review"),
    ("playtest_first", "playtest first"),
)


@dataclass(frozen=True)
class CoachCard:
    """One card the guide has an opinion about — cut, keep, or add.

    The persona VOICE lives in ``voiced_note``; the engine's own ``engine_reasons``
    are kept verbatim so the opinion stays anchored to verified analysis and the
    user can see the difference between "what the tool found" and "how the guide
    reads it".
    """

    card: str
    section: str  # "cut" | "protect" | "add"
    tier: str  # cut tier, protection level, or replacement category
    voiced_note: str
    engine_reasons: list[str] = field(default_factory=list)
    engine_confidence: str = ""
    engine_label: str = ""  # cut_type / protection_level / replacement_category
    caution: str = ""  # adds only: the engine's "why to be careful"

    def to_dict(self) -> dict[str, Any]:
        return {
            "card": self.card,
            "section": self.section,
            "tier": self.tier,
            "voiced_note": self.voiced_note,
            "engine_reasons": list(self.engine_reasons),
            "engine_confidence": self.engine_confidence,
            "engine_label": self.engine_label,
            "caution": self.caution,
        }


@dataclass(frozen=True)
class CoachDirection:
    """A category-level build-up direction ("more ramp / draw / removal …"),
    voiced through the lens. Distinct from a specific add card so the view keeps
    the engine's own separation of *need* from *named candidate*."""

    category: str
    priority: str
    voiced_note: str
    engine_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "priority": self.priority,
            "voiced_note": self.voiced_note,
            "engine_reason": self.engine_reason,
        }


@dataclass
class CoachView:
    """The full coach surface for one deck, one lens, one direction.

    Carries BOTH directions' data (the engine produces both); ``direction`` only
    governs ordering + framing so the Phase 2 toggle is a re-render, not a rebuild.
    """

    persona: dict[str, Any]
    opening: str
    disclaimer: str
    direction: str
    direction_frame: str
    deck_plan: dict[str, Any]
    cuts: list[CoachCard] = field(default_factory=list)
    protects: list[CoachCard] = field(default_factory=list)
    add_directions: list[CoachDirection] = field(default_factory=list)
    add_cards: list[CoachCard] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    # --- Phase 2: cut-down <-> build-up toggle ----------------------------

    def reframed(self, direction: str) -> "CoachView":
        """Return a copy framed for the other review direction.

        Phase 2's toggle: the cut / protect / add data is direction-INDEPENDENT
        (only section order + the framing line change), so this re-frames WITHOUT
        re-running the engine or the voiced-narration wiring. The Qt page calls
        this on a toggle for an instant flip; lists are shared read-only.
        """
        new_dir = direction if direction in (DIRECTION_CUT_DOWN, DIRECTION_BUILD_UP) else self.direction
        if new_dir == self.direction:
            return self
        guide = self.persona.get("guide_name") or ""
        return CoachView(
            persona=self.persona,
            opening=self.opening,
            disclaimer=self.disclaimer,
            direction=new_dir,
            direction_frame=_build_direction_frame(guide, new_dir),
            deck_plan=self.deck_plan,
            cuts=self.cuts,
            protects=self.protects,
            add_directions=self.add_directions,
            add_cards=self.add_cards,
            meta=self.meta,
        )

    # --- serialization ----------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "persona": dict(self.persona),
            "opening": self.opening,
            "disclaimer": self.disclaimer,
            "direction": self.direction,
            "direction_frame": self.direction_frame,
            "deck_plan": dict(self.deck_plan),
            "cuts": [c.to_dict() for c in self.cuts],
            "protects": [c.to_dict() for c in self.protects],
            "add_directions": [d.to_dict() for d in self.add_directions],
            "add_cards": [c.to_dict() for c in self.add_cards],
            "meta": dict(self.meta),
        }

    # --- readable rendering (checkpoint display + Phase 5 export seed) -----

    def to_text(self) -> str:
        guide = self.persona.get("guide_name") or "your guide"
        lines: list[str] = []
        lines.append(self.opening.rstrip())
        lines.append("")
        lines.append(self.disclaimer)
        lines.append("")
        lines.append(self.direction_frame)
        lines.append("")
        lines.append(self._render_plan(guide))

        cut_block = self._render_cuts(guide)
        keep_block = self._render_protects(guide)
        add_block = self._render_adds(guide)

        # Cut-down leads with what to trim; build-up leads with what to add. The
        # underlying data is identical — only the order + emphasis change.
        if self.direction == DIRECTION_BUILD_UP:
            ordered = [add_block, keep_block, cut_block]
        else:
            ordered = [cut_block, keep_block, add_block]

        for block in ordered:
            if block:
                lines.append("")
                lines.append(block)

        return "\n".join(lines).rstrip() + "\n"

    # --- internal renderers ----------------------------------------------

    def _render_plan(self, guide: str) -> str:
        plan = self.deck_plan
        out = [f"## The plan {guide} sees"]
        commander = plan.get("commander")
        if commander:
            colors = "/".join(plan.get("color_identity") or []) or "—"
            out.append(f"- Commander: {commander} ({colors}), {plan.get('deck_card_count', 0)} cards")
        primary = plan.get("primary_strategy") or "Undetermined"
        secondary = plan.get("secondary_strategy")
        conf = plan.get("confidence") or "unknown"
        plan_line = f"- Plan: {primary}"
        if secondary:
            plan_line += f" (with {secondary})"
        plan_line += f" — confidence {conf}"
        out.append(plan_line)
        packages = plan.get("synergy_packages") or []
        if packages:
            out.append(f"- Synergy packages: {', '.join(packages)}")
        strong = plan.get("strong_synergy_cards") or []
        if strong:
            out.append(f"- Pulling their weight: {', '.join(strong[:12])}")
        off_plan = plan.get("possible_off_plan_cards") or []
        if off_plan:
            names = []
            for entry in off_plan[:8]:
                name = entry.get("card") if isinstance(entry, Mapping) else str(entry)
                if name:
                    names.append(name)
            if names:
                out.append(f"- Maybe off-plan (your call): {', '.join(names)}")
        return "\n".join(out)

    def _render_cuts(self, guide: str) -> str:
        if not self.cuts:
            return ""
        out = [f"## What {guide} would look at cutting"]
        for c in self.cuts:
            header = f"- **{c.card}** ({c.tier}"
            if c.engine_confidence:
                header += f", engine confidence {c.engine_confidence}"
            header += ")"
            out.append(header)
            if c.voiced_note:
                out.append(f"    {c.voiced_note}")
            if c.engine_reasons:
                out.append(f"    Engine's reasons: {'; '.join(c.engine_reasons)}")
        return "\n".join(out)

    def _render_protects(self, guide: str) -> str:
        if not self.protects:
            return ""
        out = [f"## What {guide} would keep"]
        for c in self.protects:
            label = f" ({c.engine_label})" if c.engine_label else ""
            out.append(f"- **{c.card}**{label}")
            if c.voiced_note:
                out.append(f"    {c.voiced_note}")
        return "\n".join(out)

    def _render_adds(self, guide: str) -> str:
        if not self.add_directions and not self.add_cards:
            return ""
        out = [f"## Where {guide} would build up"]
        for d in self.add_directions:
            prio = f" ({d.priority})" if d.priority else ""
            out.append(f"- **{d.category}**{prio}")
            if d.voiced_note:
                out.append(f"    {d.voiced_note}")
        if self.add_cards:
            out.append("")
            out.append(f"### Specific cards {guide} likes for those gaps")
            for c in self.add_cards:
                label = f" ({c.engine_label})" if c.engine_label else ""
                out.append(f"- **{c.card}**{label}")
                if c.voiced_note:
                    out.append(f"    {c.voiced_note}")
                if c.caution:
                    out.append(f"    Careful: {c.caution}")
        return "\n".join(out)


# --- builder --------------------------------------------------------------

def build_coach_view(
    analysis: Optional[dict],
    *,
    philosophy_key: str = "balanced_unknown",
    guide_presentation: str = "either",
    direction: Optional[str] = None,
    guide_style: str = "",
) -> CoachView:
    """Build the coach view from an engine analysis dict.

    Parameters
    ----------
    analysis:
        The dict returned by main.build_analysis_context. Read defensively; a
        missing/garbage dict yields an empty-but-valid view, never an exception.
    philosophy_key:
        A real philosophy lens key (e.g. "pet_card", "competitive_closer"). Drives
        BOTH the voiced narration and the named guide.
    guide_presentation:
        "masculine" | "feminine" | "either" | "no_named_guide" — selects the named
        guide variant for the opinion framing.
    direction:
        "cut_down" | "build_up". Governs section ORDER + framing only. Defaults to
        the analysis's runtime_config.review_direction, else cut-down.
    guide_style:
        Response-style token (recorded in meta; reserved for later verbosity tuning).
    """
    analysis = analysis or {}

    # The voiced-narration wiring takes a plain config Mapping (NOT the engine's
    # RuntimeConfig dataclass). We hand it exactly the lens + guide variant.
    wiring_config: dict[str, Any] = {
        "selected_lens": philosophy_key or "balanced_unknown",
        "guide_presentation": guide_presentation or "either",
    }

    resolved_direction = _resolve_direction(direction, analysis)
    persona = _build_persona(philosophy_key, wiring_config)
    guide_name = persona.get("guide_name") or ""

    try:
        opening = format_persona_opening(context_from_runtime_config(wiring_config))
    except Exception:  # noqa: BLE001 - presentation enrichment, never fatal
        opening = ""

    disclaimer = _build_disclaimer(guide_name, persona.get("label", ""))
    direction_frame = _build_direction_frame(guide_name, resolved_direction)

    deck_plan = _build_deck_plan(analysis)
    cuts = _build_cuts(analysis, wiring_config)
    protects = _build_protects(analysis, wiring_config)
    add_directions, add_cards = _build_adds(analysis, wiring_config)

    meta = {
        "schema": "coach_view/v1",
        "philosophy_key": persona.get("key", philosophy_key),
        "guide_presentation": guide_presentation,
        "guide_style": guide_style,
        "version_label": str(analysis.get("version_label") or "unknown"),
    }

    return CoachView(
        persona=persona,
        opening=opening,
        disclaimer=disclaimer,
        direction=resolved_direction,
        direction_frame=direction_frame,
        deck_plan=deck_plan,
        cuts=cuts,
        protects=protects,
        add_directions=add_directions,
        add_cards=add_cards,
        meta=meta,
    )


# --- builder internals ----------------------------------------------------

def _resolve_direction(direction: Optional[str], analysis: dict) -> str:
    if direction in (DIRECTION_CUT_DOWN, DIRECTION_BUILD_UP):
        return direction
    rc = analysis.get("runtime_config")
    rc_dir = getattr(rc, "review_direction", None) if rc is not None else None
    if rc_dir == DIRECTION_BUILD_UP:
        return DIRECTION_BUILD_UP
    return DIRECTION_CUT_DOWN


def _build_persona(philosophy_key: str, wiring_config: Mapping[str, Any]) -> dict[str, Any]:
    """Persona display info (name, role, tone) — reuse the engine registries; do
    NOT invent persona behavior. Defensive: degrade to Balanced rather than raise."""
    try:
        prof = get_philosophy_profile(philosophy_key)
    except Exception:  # noqa: BLE001
        prof = get_philosophy_profile("balanced_unknown")
    guide_name = ""
    guide_role = ""
    try:
        persona_ctx = context_from_runtime_config(wiring_config).persona_context
        guide_name = str(persona_ctx.get("guide_name") or "")
        guide_role = str(persona_ctx.get("guide_role") or "")
    except Exception:  # noqa: BLE001
        pass
    parent_key = getattr(prof, "parent", None)
    family_tone = ""
    family_label = ""
    if parent_key:
        try:
            parent = get_philosophy_profile(parent_key)
            family_tone = str(getattr(parent, "tone", "") or "")
            family_label = str(getattr(parent, "label", "") or "")
        except Exception:  # noqa: BLE001
            pass
    return {
        "key": getattr(prof, "key", "balanced_unknown"),
        "label": getattr(prof, "label", "Balanced / Unknown"),
        "guide_name": guide_name,
        "guide_role": guide_role,
        "tone": str(getattr(prof, "tone", "") or ""),
        "family_tone": family_tone,
        "family_label": family_label,
    }


def _build_disclaimer(guide_name: str, label: str) -> str:
    who = guide_name or "your guide"
    lens = f" through the {label} lens" if label and label != "Balanced / Unknown" else ""
    return (
        f"This is {who}'s read of your deck{lens} — an opinion, not a verdict. "
        "Engine truth (legality, what's verified) stands; the takes below are a "
        "lens you can disagree with. You know your deck and your table."
    )


def _build_direction_frame(guide_name: str, direction: str) -> str:
    who = guide_name or "Your guide"
    if direction == DIRECTION_BUILD_UP:
        return (
            f"_{who} is in build-up mode: leading with where to add, then what's "
            "already pulling its weight, then anything worth a second look._"
        )
    return (
        f"_{who} is in cut-down mode: leading with what to look at trimming, then "
        "what to keep, then where you could still build up._"
    )


def _build_deck_plan(analysis: dict) -> dict[str, Any]:
    deck_view = build_deck_view(
        analysis.get("parsed_deck"),
        analysis.get("command_zone"),
        analysis.get("role_summary"),
    )
    strategy_view, _ = build_strategy_view(
        analysis.get("strategy_summary"),
        analysis.get("plan_fit_summary"),
    )
    return {
        "commander": deck_view.get("commander", ""),
        "color_identity": deck_view.get("color_identity", []),
        "deck_card_count": deck_view.get("deck_card_count", 0),
        "primary_strategy": strategy_view.get("primary_strategy", "Undetermined"),
        "secondary_strategy": strategy_view.get("secondary_strategy", ""),
        "confidence": strategy_view.get("confidence", "unknown"),
        "synergy_packages": strategy_view.get("synergy_packages", []),
        "strong_synergy_cards": strategy_view.get("strong_synergy_cards", []),
        "possible_off_plan_cards": strategy_view.get("possible_off_plan_cards", []),
    }


def _build_cuts(analysis: dict, wiring_config: Mapping[str, Any]) -> list[CoachCard]:
    cut_view, _ = build_cut_view(
        analysis.get("possible_cuts"),
        analysis.get("protected_cards"),
    )
    out: list[CoachCard] = []
    seen: set[str] = set()
    # Tiers are walked in priority order (required → optional → manual → playtest);
    # a card the engine lists in more than one tier is shown once, at its highest
    # tier, so "what to cut" never repeats a name.
    for tier_key, tier_label in _CUT_TIERS:
        for row in cut_view.get(tier_key, []):
            card = row.get("card")
            if not card or card in seen:
                continue
            seen.add(card)
            reasons = [r for r in (row.get("reasons") or []) if r]
            candidate = {
                "card_name": card,
                "confidence": row.get("confidence", ""),
                "cut_type": row.get("cut_type", ""),
                "reason": "; ".join(reasons),
            }
            note = _safe_note(
                lambda: build_philosophy_cut_explanation(candidate, wiring_config).philosophy_note,
                fallback=candidate["reason"],
            )
            out.append(
                CoachCard(
                    card=card,
                    section="cut",
                    tier=tier_label,
                    voiced_note=note,
                    engine_reasons=reasons,
                    engine_confidence=row.get("confidence", ""),
                    engine_label=row.get("cut_type", ""),
                )
            )
    return out


def _build_protects(analysis: dict, wiring_config: Mapping[str, Any]) -> list[CoachCard]:
    cut_view, _ = build_cut_view(
        analysis.get("possible_cuts"),
        analysis.get("protected_cards"),
    )
    out: list[CoachCard] = []
    seen: set[str] = set()

    def add(card: str, protection_type: str) -> None:
        if not card or card in seen:
            return
        seen.add(card)
        record = {"card_name": card, "protection_type": protection_type}
        note = _safe_note(
            lambda: build_philosophy_protected_explanation(record, wiring_config).philosophy_note,
            fallback="",
        )
        out.append(
            CoachCard(
                card=card,
                section="protect",
                tier=protection_type or "protected",
                voiced_note=note,
                engine_label=protection_type,
            )
        )

    for row in cut_view.get("protected_from_cut", []):
        add(row.get("card", ""), row.get("cut_type", ""))
    for row in cut_view.get("protected_cards", []):
        add(row.get("card", ""), row.get("protection_level", ""))
    return out


def _build_adds(
    analysis: dict, wiring_config: Mapping[str, Any]
) -> tuple[list[CoachDirection], list[CoachCard]]:
    replacement_view, _ = build_replacement_view(
        analysis.get("replacement_needs"),
        analysis.get("replacement_candidates"),
        analysis.get("collection_candidates"),
    )

    directions: list[CoachDirection] = []
    for need in replacement_view.get("need_details", []):
        category = need.get("category")
        if not category:
            continue
        reason = need.get("reason", "")
        record = {"role": category, "priority": need.get("priority", ""), "reason": reason}
        note = _safe_note(
            lambda: build_philosophy_replacement_explanation(record, wiring_config).philosophy_note,
            fallback=reason,
        )
        directions.append(
            CoachDirection(
                category=category,
                priority=need.get("priority", ""),
                voiced_note=note,
                engine_reason=reason,
            )
        )

    add_cards: list[CoachCard] = []
    for cand in replacement_view.get("candidates", []):
        card = cand.get("card")
        if not card:
            continue
        category = cand.get("replacement_category", "")
        why_fits = cand.get("why_it_fits", "")
        record = {"role": category, "reason": why_fits}
        note = _safe_note(
            lambda: build_philosophy_replacement_explanation(record, wiring_config).philosophy_note,
            fallback=why_fits,
        )
        reasons = [why_fits] if why_fits else []
        add_cards.append(
            CoachCard(
                card=card,
                section="add",
                tier=category,
                voiced_note=note,
                engine_reasons=reasons,
                engine_confidence=cand.get("confidence", ""),
                engine_label=category,
                caution=cand.get("why_to_be_careful", ""),
            )
        )

    return directions, add_cards


def _safe_note(producer, *, fallback: str = "") -> str:
    """Run a wiring call defensively. The wiring never raises in practice, but the
    coach view must never crash a report/page on a malformed record."""
    try:
        note = producer()
    except Exception:  # noqa: BLE001
        return fallback
    note = (note or "").strip()
    return note or fallback
