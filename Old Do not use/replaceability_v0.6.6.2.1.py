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


@dataclass(slots=True)
class ReplaceabilityEntry:
    card_name: str
    quantity: int
    score: int
    cut_confidence: str
    cut_type: str
    reasons: list[str] = field(default_factory=list)
    protected: bool = False


def _confidence_from_score(score: int, protected: bool) -> str:
    if protected:
        return "Low"
    if score >= 8:
        return "High"
    if score >= 4:
        return "Medium"
    return "Low"


def _protected_label(tags: set[str], plan_entry: CardPlanFitEntry | None) -> str:
    if plan_entry and plan_entry.supports_primary:
        return "Protected primary-plan support"
    if plan_entry and plan_entry.supports_secondary:
        return "Protected secondary-plan support"
    if tags & {"commander_protection", "commander_defined_support"}:
        return "Protected commander-engine support"
    if tags & INFRASTRUCTURE_TAGS:
        return "Protected infrastructure"
    if tags & HIGH_PRESSURE_TAGS:
        return "Context-dependent keep"
    if tags & SYNERGY_TAGS:
        return "Context-dependent keep"
    return "Playtest-only watch card"


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


def _cut_type_from_reasons(reasons: list[str], tags: set[str], plan_entry: CardPlanFitEntry | None, protected: bool) -> str:
    if protected:
        return _protected_label(tags, plan_entry)

    joined = " ".join(reasons).lower()

    if tags & HIGH_PRESSURE_TAGS:
        return "Possible Bracket Pressure Cut"
    if "manual" in joined or tags & LOW_IMPACT_REVIEW_TAGS:
        return "Possible Manual Review"
    if not tags or tags == {"manual_review"}:
        return "Possible Role-Uncertain Cut"
    if "redundant" in joined:
        return "Possible Redundancy Cut"
    if "role-balance" in joined or "overfilled" in joined:
        return "Possible Role-Balance Cut"
    if "wrong shell" in joined:
        return "Possible Wrong-Shell Card"
    if "off-plan" in joined or "low-synergy" in joined:
        return "Possible Off-Plan Cut"
    return "Possible Low-Impact Cut"


def _is_functional_infrastructure(tags: set[str]) -> bool:
    return bool(tags & INFRASTRUCTURE_TAGS)


def _is_land_aura_ramp(tags: set[str]) -> bool:
    return bool(tags & {"land_aura_ramp", "enchant_land_ramp"})


def _is_context_synergy(tags: set[str]) -> bool:
    return bool(tags & SYNERGY_TAGS)


def _has_meaningful_plan_support(plan_entry: CardPlanFitEntry | None) -> bool:
    if not plan_entry:
        return False
    return plan_entry.supports_primary or plan_entry.supports_secondary or plan_entry.plan_fit in {
        "Support / infrastructure",
        "Commander / command-zone engine",
        "Primary plan support",
        "Secondary plan support",
    }



PHILOSOPHY_PROTECT_ROLE_TAGS = {
    "primary_plan_support": set(),
    "commander_synergy": {"synergy_piece", "commander_defined_support"},
    "essential_infrastructure": INFRASTRUCTURE_TAGS,
    "declared_user_intent": set(),
    "declared_theme": {"typal_density_piece", "tribal_payoff", "typal_payoff", "typal_support", "creature_type_present"},
    "typal_piece": {"typal_density_piece", "tribal_payoff", "typal_payoff", "typal_support", "creature_type_present"},
    "flavor_with_function": SYNERGY_TAGS | INFRASTRUCTURE_TAGS,
    "identity_preserving_card": SYNERGY_TAGS,
    "declared_pet_card": set(),
    "personal_attachment_card": set(),
    "commander_text_synergy": {"synergy_piece", "go_tall_support", "counter_synergy", "mana_sink", "cost_reducer", "spell_payoff", "cast_trigger", "noncreature_spell_payoff", "cast_copy_synergy", "copy_clone_value"},
    "commander_scaling": {"go_tall_support", "counter_synergy", "equipment_synergy", "aura_synergy", "mana_sink", "x_spell", "toughness_payoff", "high_toughness"},
    "commander_protection": {"protection", "commander_protection", "board_protection", "counterspell"},
    "ability_enabler": {"synergy_piece", "activated_ability_synergy", "cast_trigger", "noncreature_spell_payoff", "spell_payoff", "counter_synergy"},
    "resource_converter": {"ramp", "mana_dork", "mana_rock", "treasure_synergy", "artifact_token_synergy", "card_draw", "card_advantage", "mana_sink"},
    "commander_specific_payoff": {"spell_payoff", "noncreature_spell_payoff", "cast_trigger", "cast_copy_synergy", "copy_amplifier", "trigger_amplifier", "commander_payoff_amplifier", "win_condition", "combo_piece_possible"},
    "engine_piece": {"synergy_piece", "spell_payoff", "artifact_payoff", "sacrifice_outlet", "recursion", "blink_flicker", "etb_value", "trigger_amplifier", "etb_amplifier", "copy_amplifier", "commander_payoff_amplifier", "landfall", "lands_matter"},
    "connector_card": {"synergy_piece", "card_selection", "tutor", "recursion", "graveyard_enabler", "mana_sink"},
    "enabler": {"synergy_piece", "ramp", "card_selection", "card_draw", "token_maker", "sacrifice_outlet"},
    "payoff_bridge": {"spell_payoff", "noncreature_spell_payoff", "win_condition_possible", "combo_piece_possible", "copy_clone_value", "copy_amplifier", "trigger_amplifier", "commander_payoff_amplifier"},
    "weak_alone_strong_in_context": SYNERGY_TAGS,
    "combo_piece": {"combo_piece_possible", "manual_review", "cast_copy_synergy", "win_condition"},
    "combo_tutor": {"tutor", "card_selection"},
    "combo_protection": {"protection", "counterspell", "stack_interaction"},
    "combo_enabler": {"synergy_piece", "mana_dork", "ramp", "cost_reducer", "recursion"},
    "combo_payoff": {"combo_piece_possible", "win_condition", "spell_payoff"},
    "efficient_ramp": {"ramp", "mana_rock", "mana_dork", "mana_source"},
    "cheap_interaction": {"targeted_removal", "counterspell", "stack_interaction", "protection"},
    "curve_smoothing": {"card_selection", "card_draw", "ramp", "mana_source"},
    "mana_fixing": {"mana_fixing", "fixing", "mana_source"},
    "low_curve_enabler": {"card_selection", "ramp", "protection", "synergy_piece"},
    "table_fit_card": HIGH_PRESSURE_TAGS | INFRASTRUCTURE_TAGS,
    "bracket_appropriate_interaction": {"targeted_removal", "counterspell", "board_wipe", "protection"},
    "power_limit_respecting_card": set(),
    "flexible_interaction": {"targeted_removal", "counterspell", "board_wipe", "stack_interaction"},
    "synergy_interaction": {"targeted_removal", "counterspell", "spell_payoff", "cast_trigger", "synergy_piece"},
    "board_control_piece": {"board_wipe", "repeatable_removal", "targeted_removal"},
    "efficient_draw": {"card_draw", "card_advantage", "card_selection"},
    "reliable_mana": {"mana_source", "ramp", "mana_rock", "mana_dork", "fixing", "mana_fixing"},
    "clean_finisher": {"win_condition", "win_condition_possible", "spell_payoff", "combat_synergy"},
    "declared_big_moment_card": {"win_condition", "win_condition_possible", "big_moment_enabler", "commander_payoff_amplifier", "copy_amplifier", "trigger_amplifier", "etb_amplifier"},
    "big_moment_enabler": {"big_moment_enabler", "cheat_into_play", "copy_amplifier", "trigger_amplifier", "etb_amplifier", "commander_payoff_amplifier", "copy_clone_value", "dragon_copy_value"},
    "splashy_finisher": {"win_condition", "win_condition_possible", "combat_synergy", "dragon_typal", "dragon_copy_value", "big_moment_enabler"},
    "x_spell": {"x_spell", "mana_sink", "win_condition_possible"},
    "doublers": {"copy_amplifier", "trigger_amplifier", "etb_amplifier", "commander_payoff_amplifier", "copy_clone_value"},
    "payoff_ramp": {"ramp", "mana_rock", "mana_dork", "mana_source", "treasure_synergy", "cheat_into_play"},
    "payoff_protection": {"protection", "commander_protection", "board_protection", "counterspell"},
    "large_central_creature": {"creature", "combat_synergy", "high_toughness", "dragon_typal", "typal_density_piece"},
    "ramp_into_threats": {"ramp", "mana_rock", "mana_dork", "mana_source", "cheat_into_play"},
    "power_toughness_payoff": {"go_tall_support", "counter_synergy", "high_toughness", "combat_synergy"},
}

PHILOSOPHY_REVIEW_ROLE_TAGS = {
    "off_plan": set(),
    "unsupported_package": {"minor_package_card", "manual_review_package_card", "tribal_dependency", "narrow_payoff"},
    "role_imbalance": set(),
    "user_intent_conflict": set(),
    "flavor_only_low_function": set(),
    "identity_clashing_staple": set(),
    "low_impact_theme_card": {"typal_density_piece", "creature_type_present"},
    "surrounding_shell_weakness": set(),
    "support_piece_not_helping_pet_card": set(),
    "generic_goodstuff": INFRASTRUCTURE_TAGS,
    "commander_ignoring_card": set(),
    "unused_ability_support": {"activated_ability_synergy", "equipment_synergy", "aura_synergy"},
    "color_fit_plan_miss": set(),
    "unsupported_engine_piece": {"manual_review", "minor_package_card", "manual_review_package_card"},
    "disconnected_package": {"tribal_dependency", "narrow_payoff", "manual_review_package_card"},
    "cute_but_unconnected_card": {"manual_review"},
    "partial_combo_without_support": {"combo_piece_possible", "manual_review"},
    "unwanted_combo_pressure": {"combo_piece_possible"},
    "dead_combo_piece": {"combo_piece_possible"},
    "overcosted_effect": set(),
    "curve_clog": set(),
    "clunky_top_end": set(),
    "mana_intensive_card": {"mana_sink"},
    "bracket_pressure": HIGH_PRESSURE_TAGS,
    "table_mismatch": HIGH_PRESSURE_TAGS,
    "unwanted_fast_mana": {"fast_mana"},
    "unwanted_tutor": {"efficient_tutor", "tutor"},
    "unwanted_combo": {"combo_piece_possible"},
    "narrow_answer": {"targeted_removal", "counterspell"},
    "dead_interaction": {"targeted_removal", "counterspell"},
    "threat_mismatch": {"targeted_removal", "counterspell", "board_wipe"},
    "uninteractive_payoff": {"win_condition", "spell_payoff", "combat_synergy"},
    "low_impact_card": set(),
    "win_more": {"win_condition_possible", "combo_piece_possible"},
    "narrow_card": {"manual_review", "tribal_dependency", "narrow_payoff"},
    "unsupported_haymaker": {"manual_review"},
    "expensive_no_payoff": set(),
    "clunky_unrelated_card": set(),
    "large_creature_no_impact": {"creature"},
    "redundant_top_end": set(),
    "ramp_light_expensive_hand": set(),
    "small_value_dilution": set(),
}


def _role_matches_bias(role_names: list[str], tags: set[str], mapping: dict[str, set[str]], plan_entry: CardPlanFitEntry | None, role_entry: CardRoleEntry | None = None) -> list[str]:
    """Return bias role names that appear to match this card's known tags/context."""
    matches: list[str] = []
    for role_name in role_names or []:
        role_key = str(role_name).strip()
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
    """Record lightweight diagnostics for v0.6.6.2.1 without changing review behavior."""
    if not philosophy_context:
        return
    stats = philosophy_context.setdefault("cut_bias_runtime_stats", {
        "evaluated": 0,
        "applied": 0,
        "protected_adjustments": 0,
        "review_adjustments": 0,
        "no_match": 0,
        "example_applied_cards": [],
        "example_no_match_cards": [],
    })
    stats[event] = int(stats.get(event, 0)) + 1
    if card_name:
        if event in {"applied", "protected_adjustments", "review_adjustments"}:
            examples = stats.setdefault("example_applied_cards", [])
            if card_name not in examples and len(examples) < 12:
                examples.append(card_name)
        elif event == "no_match":
            examples = stats.setdefault("example_no_match_cards", [])
            if card_name not in examples and len(examples) < 12:
                examples.append(card_name)


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
        reasons.append(f"v0.6.6.2.1 philosophy adjustment: lowered optional cut pressure for {lens} because this card matches protect-biased role(s): {', '.join(protect_matches[:4])}.")

    if review_matches:
        # If a card is already supported by the primary plan, do not pile on a large philosophy penalty.
        if plan_entry and plan_entry.supports_primary:
            _record_philosophy_bias_event(philosophy_context, "applied", role_entry.card_name)
            _record_philosophy_bias_event(philosophy_context, "review_adjustments", role_entry.card_name)
            reasons.append(f"v0.6.6.2.1 philosophy note: {lens} would normally review role(s) {', '.join(review_matches[:4])}, but primary-plan support keeps this as a light watch point.")
        else:
            delta += review_nudge
            _record_philosophy_bias_event(philosophy_context, "applied", role_entry.card_name)
            _record_philosophy_bias_event(philosophy_context, "review_adjustments", role_entry.card_name)
            reasons.append(f"v0.6.6.2.1 philosophy adjustment: raised optional review pressure for {lens} because this card matches review-biased role(s): {', '.join(review_matches[:4])}.")

    return delta, reasons, protected_by_bias

def build_replaceability_review(
    card_roles: list[CardRoleEntry],
    plan_fit_summary: PlanFitSummary,
    protected_cards: list[ProtectedCardEntry],
    philosophy_context: dict | None = None,
) -> list[ReplaceabilityEntry]:
    plan_fit_by_name: dict[str, CardPlanFitEntry] = {entry.card_name: entry for entry in plan_fit_summary.entries}
    protected_names = {entry.card_name for entry in protected_cards if entry.protection_level in {"core", "high", "medium"}}
    entries: list[ReplaceabilityEntry] = []

    for role_entry in card_roles:
        tags = set(role_entry.detected_roles)
        plan_entry = plan_fit_by_name.get(role_entry.card_name)
        score = 0
        reasons: list[str] = []
        protected = role_entry.card_name in protected_names
        is_infrastructure = _is_functional_infrastructure(tags)
        is_land_aura_ramp = _is_land_aura_ramp(tags)
        is_context_synergy = _is_context_synergy(tags)
        has_plan_support = _has_meaningful_plan_support(plan_entry)

        # Protection and positive plan fit should strongly reduce cut pressure.
        if protected:
            score -= 6
            reasons.append("Protected/core or strong plan-support card; do not treat as a normal cut.")
        if plan_entry and plan_entry.supports_primary:
            score -= 5
            reasons.append("Supports primary strategy.")
        elif plan_entry and plan_entry.supports_secondary:
            score -= 2
            reasons.append("Supports secondary strategy.")

        # Off-plan pressure should not hit infrastructure/synergy cards as hard.
        if plan_entry and plan_entry.possible_off_plan:
            if is_land_aura_ramp:
                score -= 1
                reasons.append("Initial flag: possible off-plan, but this is land-aura ramp/mana infrastructure.")
            elif is_infrastructure:
                score += 1
                reasons.append("Initial flag: possible off-plan, but this card fills a Commander infrastructure role.")
            elif is_context_synergy:
                score += 3
                reasons.append("Possible off-plan or low-synergy, but this card has context-dependent synergy tags and should be reviewed carefully.")
            else:
                score += 6
                reasons.append("Possible off-plan or low-synergy based on current primary/secondary strategy read.")

        if "manual_review" in tags:
            score += 1 if (is_infrastructure or is_context_synergy or has_plan_support) else 2
            reasons.append("Manual-review card or role-uncertain card.")

        if tags & HIGH_PRESSURE_TAGS:
            score += 2
            reasons.append("Bracket pressure; review for table fit, not automatic cut.")

        if is_land_aura_ramp:
            score -= 4
            reasons.append("Land-aura ramp is mana infrastructure; do not treat as off-plan unless the mana package is intentionally being reduced.")
        elif is_infrastructure:
            score -= 2 if has_plan_support else 1
            reasons.append("Fills infrastructure role; cut only if overfilled or replaced by a better role match.")

        if is_context_synergy:
            score -= 2
            reasons.append("Has synergy/engine tags that may be important in context.")

        if not tags or tags == {"manual_review"}:
            score += 4
            reasons.append("No clear parsed role beyond manual review.")

        bias_delta, bias_reasons, philosophy_protected = _philosophy_bias_delta(tags, plan_entry, role_entry, philosophy_context)
        if bias_delta:
            score += bias_delta
        if bias_reasons:
            reasons.extend(bias_reasons)
        if philosophy_protected and not protected and score <= 3 and (plan_entry and (plan_entry.possible_off_plan or plan_entry.supports_primary or plan_entry.supports_secondary)):
            # Do not turn every philosophy-supported card into Protected From Cut.
            # This only downgrades marginal optional cuts into playtest/watch status.
            protected = True
            reasons.append("v0.6.6.2.1 final philosophy verdict: treat as a playtest-only watch card, not a normal cut, unless pilot intent says otherwise.")

        cut_type = _cut_type_from_reasons(reasons, tags, plan_entry, protected)

        # Protected entries should read like keep guidance even if the report formatter
        # still uses a generic "Cut type" label.
        if protected:
            initial_flag = _initial_flag_from_reasons(reasons, tags)
            protected_label = _protected_label(tags, plan_entry)
            philosophy_reasons = [reason for reason in reasons if "philosophy" in reason.lower()]
            other_reasons = [reason for reason in reasons if not reason.startswith("Initial flag:") and reason not in philosophy_reasons]
            reasons = [
                f"Protected Label: {protected_label}",
                f"Initial flag: {initial_flag}",
                "Final verdict: Not currently a cut. Keep unless playtesting or user intent says otherwise.",
            ] + philosophy_reasons[:3] + other_reasons[:2]

        entries.append(ReplaceabilityEntry(
            card_name=role_entry.card_name,
            quantity=role_entry.quantity,
            score=score,
            cut_confidence=_confidence_from_score(score, protected),
            cut_type=cut_type,
            reasons=reasons or ["No special cut/protection reason detected."],
            protected=protected,
        ))

    return sorted(entries, key=lambda entry: entry.score, reverse=True)
