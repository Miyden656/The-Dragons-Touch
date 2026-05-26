"""Replaceability scoring for possible cut review.

Round 6 cleanup goal:
- Rank review candidates by replaceability, not raw card quality.
- Keep the output cautious: possible cuts are not guaranteed cuts.

Patch Batch 4 cleanup:
- Do not let basic infrastructure become off-theme cut pressure too easily.
- Reduce overuse of "Possible Off-Theme Cut".
- Give protected entries keep-oriented labels so protected sections do not read like cut lists.

v0.6.6.2:
- Apply small philosophy-aware optional-cut nudges.
- Do not override legality, required cuts, protected cards, or pilot intent.
- Keep all philosophy adjustments visible in the reasons list.

v0.6.6.2.1:
- Improve philosophy-bias visibility and trigger/copy-amplifier support.
- Track when bias was evaluated, applied, or missed for diagnostics.
- Preserve philosophy-adjustment reasons when cards move to protected/watch status.

v0.6.6.2.2:
- Count unique adjusted cards separately from total bias hits.
- Suppress review-pressure wording on protected mana-base infrastructure.

v0.6.6.3:
- Improve protected/watch-card language when philosophy bias changes a verdict.
- Use clearer Initial flag / Philosophy adjustment / Final verdict / Why this matters / Review instruction wording.

v0.6.6.3.1:
- Ensure Why this matters and Review instruction fields are surfaced in normal report output.
- Strip old raw v0.6.6.2.2 final-verdict wording from philosophy adjustment text.

v0.6.6.6 lock note:
- Make Balanced / Unknown more neutral before v0.6.6 lock.
- Suppress Balanced philosophy notes on normal infrastructure, primary-plan support, and context-synergy cards.
- Suppress philosophy bias on normal mana-base infrastructure.
- Require stronger evidence for broad Commander Exploiter, Engine Builder, and Power-Level Calibrator aliases.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from analysis.plan_fit import CardPlanFitEntry, PlanFitSummary
from analysis.role_tags import CardRoleEntry
from cuts.protected_cards import ProtectedCardEntry

HIGH_PRESSURE_TAGS = {"bracket_pressure", "high_bracket_pressure", "game_changer"}

# Cards with these roles are functional infrastructure first. They can still be
# reviewed when the role is overfilled, but they should not become off-theme cuts
# only because they are not part of the narrow archetype label.
INFRASTRUCTURE_TAGS = {
    "ramp", "land_ramp", "mana_rock", "mana_dork", "mana_source", "cost_reducer",
    "card_draw", "repeatable_card_draw", "card_advantage", "card_selection", "tutor",
    "targeted_removal", "repeatable_removal", "board_wipe", "counterspell", "stack_interaction",
    "protection", "commander_protection", "board_protection", "recursion", "land_recursion",
    "extra_land_play", "land_aura_ramp", "enchant_land_ramp", "mana_infrastructure", "fixing", "mana_fixing", "evasion",
}

# Strategy and package cards are context-sensitive. They should usually become
# manual/playtest review before becoming confident off-theme cuts.
SYNERGY_TAGS = {
    "token_maker", "creature_token_maker", "copy_token_maker", "sacrifice_outlet",
    "recursion", "reanimation", "graveyard_enabler", "self_mill", "discard_outlet",
    "landfall", "lands_matter", "landfall_support", "lands_matter_support",
    "spell_payoff", "noncreature_spell_payoff", "tribal_payoff", "typal_payoff",
    "typal_support", "typal_density", "typal_density_piece", "tribal_dependency",
    "dragon_typal", "dragon_copy_value", "copy_clone_value", "copy_amplifier", "trigger_amplifier", "etb_amplifier", "commander_payoff_amplifier", "big_moment_enabler", "cheat_into_play", "blink_flicker", "blink",
    "etb_value", "ETB_synergy", "toughness_payoff", "defender_payoff",
    "death_trigger_payoff", "aristocrat_payoff", "counter_synergy", "go_tall_support",
    "combat_synergy", "attack_trigger_payoff", "equipment_synergy", "artifact_combat",
    "attachment_synergy", "win_condition", "win_condition_possible", "combo_piece_possible",
}

LOW_IMPACT_REVIEW_TAGS = {"manual_review", "minor_package_card", "manual_review_package_card"}
HIGH_PRESSURE_TAGS = {"bracket_pressure", "high_bracket_pressure", "game_changer"}
INFRASTRUCTURE_TAGS = {
    "ramp", "land_ramp", "mana_rock", "mana_dork", "mana_source", "cost_reducer",
    "card_draw", "repeatable_card_draw", "card_advantage", "card_selection", "tutor",
    "targeted_removal", "repeatable_removal", "board_wipe", "counterspell", "stack_interaction",
    "protection", "commander_protection", "board_protection", "recursion", "land_recursion",
    "extra_land_play", "land_aura_ramp", "enchant_land_ramp", "mana_infrastructure", "fixing", "mana_fixing", "evasion",
}
SYNERGY_TAGS = {
    "token_maker", "creature_token_maker", "copy_token_maker", "sacrifice_outlet",
    "recursion", "reanimation", "graveyard_enabler", "self_mill", "discard_outlet",
    "landfall", "lands_matter", "landfall_support", "lands_matter_support",
    "spell_payoff", "noncreature_spell_payoff", "tribal_payoff", "typal_payoff",
    "typal_support", "typal_density", "typal_density_piece", "tribal_dependency",
    "dragon_typal", "dragon_copy_value", "copy_clone_value", "copy_amplifier", "trigger_amplifier", "etb_amplifier", "commander_payoff_amplifier", "big_moment_enabler", "cheat_into_play", "blink_flicker", "blink",
    "etb_value", "ETB_synergy", "toughness_payoff", "defender_payoff",
    "death_trigger_payoff", "aristocrat_payoff", "counter_synergy", "go_tall_support",
    "combat_synergy", "attack_trigger_payoff", "equipment_synergy", "artifact_combat",
    "attachment_synergy", "win_condition", "win_condition_possible", "combo_piece_possible",
}
LOW_IMPACT_REVIEW_TAGS = {"manual_review", "minor_package_card", "manual_review_package_card"}

def _initial_flag_from_reasons(reasons: list[str], tags: set[str]) -> str:
    joined = " ".join(reasons).lower()
    if tags & HIGH_PRESSURE_TAGS:
        return "Possible Bracket Pressure Cut"
    if "off-plan" in joined or "low-synergy" in joined:
        return "Possible Off-Plan Review"
    if "manual" in joined or tags & LOW_IMPACT_REVIEW_TAGS:
        return "Possible Manual Review"
    if "infrastructure" in joined:
        return "Possible Role-Balance Review"
    if not tags or tags == {"manual_review"}:
        return "Possible Role-Uncertain Review"
    return "Possible Low-Impact Review"

def _clean_philosophy_reason(reason: str) -> str:
    """Convert raw v0.6.6.x adjustment text into report-facing language.

    v0.6.6.5 preserves the duplicated-label cleanup and QA visibility for philosophy bias such as
    "Philosophy adjustment: Philosophy adjustment: ..." when protected/watch
    entries are rebuilt by the report formatter.
    """
    text = str(reason).strip()
    prefixes = (
        "v0.6.6.2.2 philosophy adjustment:",
        "v0.6.6.2.1 philosophy adjustment:",
        "v0.6.6.2 philosophy adjustment:",
        "v0.6.6.2.2 philosophy note:",
        "v0.6.6.2.1 philosophy note:",
        "v0.6.6.2 philosophy note:",
        "philosophy adjustment:",
        "philosophy note:",
    )
    changed = True
    while changed:
        changed = False
        lowered = text.lower()
        for prefix in prefixes:
            if lowered.startswith(prefix):
                text = text[len(prefix):].strip()
                changed = True
                break
    return text

def _watch_card_why_this_matters(tags: set[str], protected_label: str, philosophy_context: dict | None) -> str:
    """Explain why a protected/watch verdict matters in deck-building terms."""
    lens = "the selected philosophy"
    if philosophy_context:
        lens = str(philosophy_context.get("label") or lens)

    if tags & {"trigger_amplifier", "etb_amplifier", "copy_amplifier", "commander_payoff_amplifier"}:
        return f"This card may look replaceable in a generic deck review, but under {lens} it can amplify the commander's payoff pattern or the deck's core engine."
    if tags & {"big_moment_enabler", "cheat_into_play"}:
        return f"This card may be part of the deck's payoff setup rather than a generic value slot, so it deserves playtest review before cutting."
    if tags & {"commander_protection", "protection", "board_protection"}:
        return f"This card helps preserve the commander or the payoff turn, which can matter more than raw rate in this shell."
    if tags & {"typal_density_piece", "tribal_payoff", "typal_payoff", "dragon_typal", "creature_type_present"}:
        return f"This card contributes to the deck's creature-type or identity structure, so the cut decision should account for density as well as raw power."
    if tags & INFRASTRUCTURE_TAGS:
        return "This card fills a support role. Review it by role pressure and redundancy, not by whether it is flashy."
    if tags & SYNERGY_TAGS:
        return f"This card has context-dependent synergy. It should be judged by whether the surrounding shell actually uses it."
    if "Protected" in protected_label:
        return "This card is currently treated as part of the deck's support structure, not as a normal cut candidate."
    return "This card needs playtest context before becoming a confident cut."

def _watch_card_review_instruction(tags: set[str], protected_label: str, initial_flag: str, philosophy_context: dict | None) -> str:
    """Give the pilot a concrete review instruction for protected/watch cards."""
    lens = "the selected philosophy"
    if philosophy_context:
        lens = str(philosophy_context.get("label") or lens)

    if tags & {"trigger_amplifier", "etb_amplifier", "copy_amplifier", "commander_payoff_amplifier"}:
        return "Do not cut this as generic artifact/enchantment filler; only revisit it if it fails to create meaningful commander or payoff amplification in actual games."
    if tags & {"big_moment_enabler", "cheat_into_play"}:
        return "Playtest whether this reliably enables the deck's payoff turn; cut only if it is too slow, stranded, or redundant with better enablers."
    if tags & {"typal_density_piece", "tribal_payoff", "typal_payoff", "dragon_typal", "creature_type_present"}:
        return "Before cutting, check whether removing it weakens typal density, commander triggers, or the deck's intended identity."
    if tags & INFRASTRUCTURE_TAGS:
        return "Review this only against the same role slot; replace it with a better support piece rather than cutting support density blindly."
    if tags & SYNERGY_TAGS:
        return "Keep it on a watch list; cut only if the pilot confirms the synergy package is not important or it repeatedly underperforms."
    return f"Treat this as a watch card under {lens}; ask the pilot whether it actually supports the intended game experience before cutting."

def _lens_key(philosophy_context: dict | None) -> str:
    if not philosophy_context:
        return ""
    return str(philosophy_context.get("key") or "").strip().lower()

def _filter_overbroad_philosophy_matches(
    protect_matches: list[str],
    review_matches: list[str],
    tags: set[str],
    plan_entry: CardPlanFitEntry | None,
    role_entry: CardRoleEntry,
    philosophy_context: dict | None,
) -> tuple[list[str], list[str]]:
    """Trim philosophy-bias matches that proved too broad in v0.6.6.5 QA.

    Normal plan-fit and infrastructure protection still run elsewhere. This only
    controls whether the *philosophy layer* adds extra score changes and visible
    philosophy notes.
    """
    key = _lens_key(philosophy_context)

    # Mana-base infrastructure should be protected by normal mana-base/support
    # logic, not by philosophy-specific aliases. This prevents high-power and
    # engine lenses from adjusting every dual/fetch/basic land.
    if _is_mana_base_infrastructure(tags):
        return [], []

    if key == "balanced_unknown":
        # v0.6.6.6 lock note: Balanced / Unknown is the neutral/default lens. It should
        # not create extra philosophy-protection notes for normal primary-plan,
        # commander, role-filler, or infrastructure cards; the normal protection
        # system already handles those. Balanced only adds review pressure to
        # *clear* off-plan cards that lack synergy/infrastructure context.
        protect_matches = [m for m in protect_matches if m == "declared_user_intent"]
        if "declared_user_intent" not in protect_matches:
            protect_matches = []

        review_matches = [m for m in review_matches if m in {"off_plan", "user_intent_conflict"}]
        if not (plan_entry and plan_entry.possible_off_plan):
            review_matches = []
        elif tags & (INFRASTRUCTURE_TAGS | SYNERGY_TAGS):
            # Cards with real infrastructure/synergy tags should be handled by
            # normal context/manual-review rules instead of receiving an extra
            # Balanced philosophy penalty.
            review_matches = []
        return protect_matches, review_matches

    if key == "commander_exploiter":
        # Commander Exploiter should care about commander text, not every generic
        # ramp/draw/removal support card. Broad resource_converter matches need
        # direct plan support or commander-specific payoff evidence.
        specific_tags = {
            "commander_payoff_amplifier", "trigger_amplifier", "copy_amplifier",
            "etb_amplifier", "copy_clone_value", "dragon_copy_value",
            "commander_protection", "activated_ability_synergy", "cast_trigger",
            "noncreature_spell_payoff", "spell_payoff", "go_tall_support",
            "counter_synergy", "mana_sink", "x_spell",
        }
        if "resource_converter" in protect_matches and not ((plan_entry and (plan_entry.supports_primary or plan_entry.supports_secondary)) or (tags & specific_tags)):
            protect_matches = [m for m in protect_matches if m != "resource_converter"]
        if "generic_goodstuff" in review_matches and (plan_entry and (plan_entry.supports_primary or plan_entry.supports_secondary)):
            review_matches = [m for m in review_matches if m != "generic_goodstuff"]
        return protect_matches, review_matches

    if key == "engine_builder":
        # Engine Builder can be active, but generic landfall/lands_matter or
        # normal infrastructure should not make every support card look like an
        # engine piece. Require a real engine connector/payoff tag or plan support.
        engine_specific_tags = {
            "sacrifice_outlet", "free_sacrifice_outlet", "sacrifice_payoff",
            "artifact_payoff", "artifact_token_synergy", "treasure_synergy",
            "death_trigger_payoff", "aristocrat_payoff", "recursion",
            "graveyard_enabler", "discard_outlet", "trigger_amplifier",
            "etb_amplifier", "copy_amplifier", "commander_payoff_amplifier",
            "landfall_payoff", "token_maker", "card_selection", "tutor",
            "mana_sink",
        }
        if not ((tags & engine_specific_tags) or (plan_entry and (plan_entry.supports_primary or plan_entry.supports_secondary))):
            protect_matches = [m for m in protect_matches if m not in {"engine_piece", "connector_card", "enabler", "weak_alone_strong_in_context"}]
        return protect_matches, review_matches

    if key == "power_level_calibrator":
        # Power-Level Calibrator should focus on bracket/table-fit evidence, not
        # treat every normal support role as a table-fit adjustment.
        if not (tags & HIGH_PRESSURE_TAGS):
            protect_matches = [m for m in protect_matches if m not in {"table_fit_card"}]
            review_matches = [m for m in review_matches if m not in {"bracket_pressure", "table_mismatch", "unwanted_fast_mana", "unwanted_tutor", "unwanted_combo"}]
        return protect_matches, review_matches

    return protect_matches, review_matches

def _role_matches_bias(role_names: list[str], tags: set[str], mapping: dict[str, set[str]], plan_entry: CardPlanFitEntry | None, role_entry: CardRoleEntry | None = None) -> list[str]:
    """Return bias role names that appear to match this card's known tags/context."""
    matches: list[str] = []
    for role_name in role_names or []:
        role_key = str(role_name).strip()

        # v0.6.6.5 preserves v0.6.6.4.2 precision cleanup: Big Creature / Stompy should not
        # treat every small typal creature as a large central creature. These
        # aliases require actual top-end size or substantial big-creature payoff
        # evidence. Small typal pieces can still be protected through
        # typal_commander_support or normal plan-support rules.
        if role_key in {"large_central_creature", "impactful_large_creature"}:
            try:
                mv = float(role_entry.mana_value) if role_entry and role_entry.mana_value is not None else 0.0
            except (TypeError, ValueError):
                mv = 0.0
            if (
                mv >= 5
                and "creature" in tags
                and (tags & {"combat_synergy", "go_tall_support", "high_toughness", "win_condition", "big_moment_enabler", "dragon_typal"})
            ):
                matches.append(role_key)
            continue

        if role_key == "large_creature_no_impact":
            try:
                mv = float(role_entry.mana_value) if role_entry and role_entry.mana_value is not None else 0.0
            except (TypeError, ValueError):
                mv = 0.0
            if (
                mv >= 6
                and "creature" in tags
                and not (plan_entry and (plan_entry.supports_primary or plan_entry.supports_secondary))
                and not (tags & {"combat_synergy", "go_tall_support", "high_toughness", "win_condition", "big_moment_enabler", "card_advantage", "card_draw", "protection"})
            ):
                matches.append(role_key)
            continue

        mapped_tags = mapping.get(role_key, set())
        if mapped_tags and tags & mapped_tags:
            matches.append(role_key)
            continue
        if role_key in {"primary_plan_support", "clear_commander_synergy"} and plan_entry and plan_entry.supports_primary:
            matches.append(role_key)
            continue
        if role_key == "off_plan" and plan_entry and plan_entry.possible_off_plan:
            matches.append(role_key)
            continue
        if role_key in {"overcosted_effect", "curve_clog", "clunky_top_end"} and role_entry and role_entry.mana_value is not None:
            try:
                if float(role_entry.mana_value) >= 5:
                    matches.append(role_key)
                    continue
            except (TypeError, ValueError):
                pass
        if role_key in {"low_impact_card", "flavor_only_low_function", "commander_ignoring_card", "color_fit_plan_miss"} and plan_entry and plan_entry.possible_off_plan and not (tags & (INFRASTRUCTURE_TAGS | SYNERGY_TAGS)):
            matches.append(role_key)
            continue
    return matches

def _record_philosophy_bias_event(philosophy_context: dict | None, event: str, card_name: str | None = None) -> None:
    """Record lightweight diagnostics for v0.6.6.2.2 without changing review behavior.

    The original v0.6.6.2.1 counters counted every role-hit event, so a card
    with both protect-side and review-side matches could make "applied" exceed
    the number of evaluated cards. v0.6.6.2.2 keeps unique-card counters for
    readable diagnostics while also preserving total hit counts.
    """
    if not philosophy_context:
        return
    stats = philosophy_context.setdefault("cut_bias_runtime_stats", {
        "evaluated": 0,
        "applied": 0,
        "protected_adjustments": 0,
        "review_adjustments": 0,
        "no_match": 0,
        "total_bias_hits": 0,
        "suppressed_infrastructure_review": 0,
        "suppressed_overbroad_bias": 0,
        "_evaluated_cards": set(),
        "_applied_cards": set(),
        "_protected_adjusted_cards": set(),
        "_review_adjusted_cards": set(),
        "_no_match_cards": set(),
        "_suppressed_infrastructure_review_cards": set(),
        "_suppressed_overbroad_bias_cards": set(),
        "example_applied_cards": [],
        "example_no_match_cards": [],
        "example_suppressed_infrastructure_review_cards": [],
        "example_suppressed_overbroad_bias_cards": [],
        "watch_language_entries": 0,
        "example_watch_language_cards": [],
    })

    if event in {"applied", "protected_adjustments", "review_adjustments"}:
        stats["total_bias_hits"] = int(stats.get("total_bias_hits", 0)) + 1

    if card_name:
        set_key_by_event = {
            "evaluated": "_evaluated_cards",
            "applied": "_applied_cards",
            "protected_adjustments": "_protected_adjusted_cards",
            "review_adjustments": "_review_adjusted_cards",
            "no_match": "_no_match_cards",
            "suppressed_infrastructure_review": "_suppressed_infrastructure_review_cards",
            "suppressed_overbroad_bias": "_suppressed_overbroad_bias_cards",
            "watch_language_entries": "_watch_language_cards",
        }
        set_key = set_key_by_event.get(event)
        if set_key:
            card_set = stats.setdefault(set_key, set())
            if not isinstance(card_set, set):
                card_set = set(card_set)
                stats[set_key] = card_set
            card_set.add(card_name)
            stats[event] = len(card_set)
        else:
            stats[event] = int(stats.get(event, 0)) + 1

        if event in {"applied", "protected_adjustments", "review_adjustments"}:
            examples = stats.setdefault("example_applied_cards", [])
            if card_name not in examples and len(examples) < 12:
                examples.append(card_name)
        elif event == "no_match":
            examples = stats.setdefault("example_no_match_cards", [])
            if card_name not in examples and len(examples) < 12:
                examples.append(card_name)
        elif event == "suppressed_infrastructure_review":
            examples = stats.setdefault("example_suppressed_infrastructure_review_cards", [])
            if card_name not in examples and len(examples) < 12:
                examples.append(card_name)
        elif event == "suppressed_overbroad_bias":
            examples = stats.setdefault("example_suppressed_overbroad_bias_cards", [])
            if card_name not in examples and len(examples) < 12:
                examples.append(card_name)
        elif event == "watch_language_entries":
            examples = stats.setdefault("example_watch_language_cards", [])
            if card_name not in examples and len(examples) < 12:
                examples.append(card_name)
    else:
        stats[event] = int(stats.get(event, 0)) + 1

def _philosophy_bias_delta(tags: set[str], plan_entry: CardPlanFitEntry | None, role_entry: CardRoleEntry, philosophy_context: dict | None) -> tuple[int, list[str], bool]:
    """Apply v0.6.6.2 light optional-cut bias.

    Returns (score_delta, reasons, protected_by_bias). Negative score lowers cut pressure;
    positive score increases cut pressure. This is deliberately small and never
    overrides normal protected-card logic or required legality fixes.
    """
    if not philosophy_context:
        return 0, [], False
    if not philosophy_context.get("cut_bias_scoring_active") and not philosophy_context.get("bias_scoring_active"):
        return 0, [], False

    protect_roles = list(philosophy_context.get("cut_bias_protect_roles") or [])
    review_roles = list(philosophy_context.get("cut_bias_review_roles") or [])
    _record_philosophy_bias_event(philosophy_context, "evaluated", role_entry.card_name)
    protect_matches = _role_matches_bias(protect_roles, tags, PHILOSOPHY_PROTECT_ROLE_TAGS, plan_entry, role_entry)
    review_matches = _role_matches_bias(review_roles, tags, PHILOSOPHY_REVIEW_ROLE_TAGS, plan_entry, role_entry)

    original_protect_matches = list(protect_matches)
    original_review_matches = list(review_matches)
    protect_matches, review_matches = _filter_overbroad_philosophy_matches(
        protect_matches=protect_matches,
        review_matches=review_matches,
        tags=tags,
        plan_entry=plan_entry,
        role_entry=role_entry,
        philosophy_context=philosophy_context,
    )
    if (original_protect_matches or original_review_matches) and not (protect_matches or review_matches):
        _record_philosophy_bias_event(philosophy_context, "suppressed_overbroad_bias", role_entry.card_name)

    # v0.6.6.2.2/v0.6.6.6 lock note: a normal fixing land should not receive a visible
    # philosophy review/protect pressure note. Keep normal mana-base/protected
    # infrastructure logic intact; suppress only philosophy-layer nudges.
    if (review_matches or protect_matches) and _is_mana_base_infrastructure(tags):
        protect_matches = []
        review_matches = []
        _record_philosophy_bias_event(philosophy_context, "suppressed_infrastructure_review", role_entry.card_name)

    if not protect_matches and not review_matches:
        _record_philosophy_bias_event(philosophy_context, "no_match", role_entry.card_name)

    delta = 0
    reasons: list[str] = []
    protected_by_bias = False
    lens = str(philosophy_context.get("label") or philosophy_context.get("key") or "selected philosophy")
    strength = str(philosophy_context.get("bias_strength") or "light").lower()
    protect_nudge = -2 if strength in {"light", "guidance", "neutral"} else -3
    review_nudge = 1 if strength in {"light", "guidance", "neutral"} else 2

    if protect_matches:
        delta += protect_nudge
        protected_by_bias = True
        _record_philosophy_bias_event(philosophy_context, "applied", role_entry.card_name)
        _record_philosophy_bias_event(philosophy_context, "protected_adjustments", role_entry.card_name)
        reasons.append(f"Philosophy adjustment: lowered optional cut pressure for {lens} because this card matches protect-biased role(s): {', '.join(protect_matches[:4])}.")

    if review_matches:
        # If a card is already supported by the primary plan, do not pile on a large philosophy penalty.
        if plan_entry and plan_entry.supports_primary:
            _record_philosophy_bias_event(philosophy_context, "applied", role_entry.card_name)
            _record_philosophy_bias_event(philosophy_context, "review_adjustments", role_entry.card_name)
            reasons.append(f"Philosophy note: {lens} would normally review role(s) {', '.join(review_matches[:4])}, but primary-plan support keeps this as a light watch point.")
        else:
            delta += review_nudge
            _record_philosophy_bias_event(philosophy_context, "applied", role_entry.card_name)
            _record_philosophy_bias_event(philosophy_context, "review_adjustments", role_entry.card_name)
            reasons.append(f"Philosophy adjustment: raised optional review pressure for {lens} because this card matches review-biased role(s): {', '.join(review_matches[:4])}.")

    return delta, reasons, protected_by_bias
