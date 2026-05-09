"""
analysis/deck_building_philosophies.py

Philosophy and persona guide data for The Dragon's Touch.

This module is designed for the v0.6.2 CLEANUP layout, which uses top-level
packages such as analysis, cuts, reports, app_io, and rules.

Design rules:
- Strategy detection remains primary.
- The philosophy/subtype key is the rules object.
- The persona name is the user-facing guide.
- This module should not perform strategy detection.
- Reports, cut logic, replacement logic, and prompt generation can consume this module.

v0.6.5.3 adds report-facing subtype summaries. These summaries are still
non-scoring guidance: they help humans and reviewing AIs understand what the
selected lens means without changing legality, strategy detection, cuts, or
collection matching.

v0.6.5.4 adds prompt-facing showcase polish so generated guided prompts explain
philosophy lenses consistently across subtypes.

v0.6.6.1 adds the foundation for philosophy-aware cut/replacement bias.
v0.6.6.2 turns on a light optional-cut scoring nudge while leaving strategy detection, legality, and collection matching unchanged.
v0.6.6.4.1 adds replacement-bias visibility counters and role-alias cleanup while preserving collection honesty and all quality gates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from random import choice
from typing import Dict, List, Literal, Optional


GuidePreference = Literal["masculine", "feminine", "either", "random", "none"]


@dataclass(frozen=True)
class Persona:
    role: str
    core_question: str
    masculine: Optional[str] = None
    feminine: Optional[str] = None
    neutral: Optional[str] = None

    def resolve_name(self, preference: GuidePreference = "either") -> Optional[str]:
        """Resolve the user-facing guide name from the preferred presentation style."""
        if preference == "none":
            return None

        if self.neutral:
            return self.neutral

        if preference == "masculine":
            return self.masculine or self.feminine
        if preference == "feminine":
            return self.feminine or self.masculine
        if preference in {"either", "random"}:
            options = [name for name in [self.masculine, self.feminine] if name]
            return choice(options) if options else None

        return self.masculine or self.feminine or self.neutral


@dataclass(frozen=True)
class PhilosophyProfile:
    key: str
    label: str
    parent: Optional[str]
    persona: Persona
    core_philosophy: str
    rules_summary: str
    protect_bias: List[str] = field(default_factory=list)
    review_bias: List[str] = field(default_factory=list)
    replacement_bias: List[str] = field(default_factory=list)
    cut_pressure_notes: List[str] = field(default_factory=list)
    # v0.6.6.1 bias foundation fields. These are exposed for diagnostics and
    # future cut/replacement logic. In v0.6.6.4.1 the cut-side profile, replacement-side candidate nudge, and replacement-bias visibility cleanup are active.
    cut_bias_protect_roles: List[str] = field(default_factory=list)
    cut_bias_review_roles: List[str] = field(default_factory=list)
    replacement_bias_roles: List[str] = field(default_factory=list)
    bias_strength: str = "guidance"
    bias_warning: str = "v0.6.6.4.1 applies light optional-cut and replacement-candidate bias with visibility counters and role-alias cleanup. It must not override legality, required cuts, pilot-protected cards, color identity, companion restrictions, collection mode, quality gates, or explicit pilot intent."
    tone: str = "balanced, clear, and supportive"
    example_language: str = ""


PHILOSOPHY_PROFILES: Dict[str, PhilosophyProfile] = {
    "balanced_unknown": PhilosophyProfile(
        key="balanced_unknown",
        label="Balanced / Unknown",
        parent=None,
        persona=Persona(
            neutral="Rowan",
            role="The Trail Guide",
            core_question="What path does this deck naturally want to follow?",
        ),
        core_philosophy="Explore the deck's natural direction without strong assumptions.",
        rules_summary="Use a balanced exploratory lens and avoid subtype-specific protection unless the user chooses a philosophy.",
        protect_bias=["clear commander synergy", "primary strategy support", "needed role-fillers", "declared user constraints"],
        review_bias=["off-plan cards", "unsupported packages", "role imbalance", "cards that conflict with user intent"],
        replacement_bias=["role balance", "strategy support", "mana consistency", "clear deck identity"],
        cut_pressure_notes=[
            "Keep optional cut pressure moderate.",
            "Do not make strong philosophy assumptions.",
            "May report possible philosophy lean without applying it as a hard rule.",
        ],
        tone="curious, exploratory, practical, and encouraging",
        example_language="No specific philosophy was selected, so this review maps the deck's natural direction before applying strong assumptions.",
    ),
    "timmy_tammy": PhilosophyProfile(
        key="timmy_tammy",
        label="Timmy / Tammy",
        parent=None,
        persona=Persona(
            masculine="Timmy",
            feminine="Tammy",
            role="The Heart Guide",
            core_question="What kind of memorable game is this deck trying to create?",
        ),
        core_philosophy="The deck is judged by the experience it creates: spectacle, theme, emotion, favorite cards, and memorable stories.",
        rules_summary="Protect the deck's intended experience while still improving the support needed to make that experience happen.",
        protect_bias=["declared pet cards", "theme-defining cards", "splashy finishers", "big payoff cards", "cards that create the desired experience"],
        review_bias=["big cards that are not meaningful", "theme cards that prevent function", "unsupported haymakers", "generic upgrades that erase identity"],
        replacement_bias=["experience-preserving upgrades", "support for the desired moment", "theme-compatible role-fillers", "protection for important payoffs"],
        cut_pressure_notes=[
            "Lower cut pressure for cards that create the intended experience.",
            "Increase cut pressure for cards that delay or distract from the intended experience.",
        ],
        tone="warm, enthusiastic, emotionally validating, and honest about function",
        example_language="This card is not the most efficient option, but it strongly supports the deck's intended experience.",
    ),
    "johnny_jenny": PhilosophyProfile(
        key="johnny_jenny",
        label="Johnny / Jenny",
        parent=None,
        persona=Persona(
            masculine="Johnny",
            feminine="Jenny",
            role="The Inventor Guide",
            core_question="What idea is this deck trying to prove?",
        ),
        core_philosophy="The deck is judged by whether it expresses and supports a specific idea, engine, interaction, combo, constraint, or unusual concept.",
        rules_summary="Protect context-dependent cards that make the deck's idea work while challenging unsupported cleverness.",
        protect_bias=["engine pieces", "combo pieces", "connector cards", "declared build-arounds", "weak-alone but strong-in-context cards"],
        review_bias=["unsupported build-arounds", "disconnected packages", "partial combos with no support", "weird cards that are just weird"],
        replacement_bias=["engine support", "redundancy", "bridge cards", "commander-specific synergy", "constraint-preserving upgrades"],
        cut_pressure_notes=[
            "Lower cut pressure for weak-alone cards with clear context.",
            "Increase cut pressure for clever-looking cards that do not actually connect.",
        ],
        tone="curious, analytical, inventive, and puzzle-oriented",
        example_language="This card looks weak by generic standards, but it may be a key connector in the deck's engine.",
    ),
    "spike": PhilosophyProfile(
        key="spike",
        label="Spike",
        parent=None,
        persona=Persona(
            neutral="Spike",
            role="The Performance Guide",
            core_question="What is preventing this deck from performing better at its intended table?",
        ),
        core_philosophy="The deck is judged by how well its choices convert into consistency, efficiency, interaction, win conversion, resilience, and appropriate power.",
        rules_summary="Increase performance scrutiny while respecting user intent, budget, power level, and table expectations.",
        protect_bias=["efficient ramp", "efficient draw", "flexible interaction", "clean role-fillers", "reliable mana", "clear finishers"],
        review_bias=["overcosted effects", "narrow cards", "unsupported payoffs", "win-more cards", "clunky top-end", "low-impact cards"],
        replacement_bias=["consistency upgrades", "efficient role-fillers", "better interaction", "clearer finishers", "role compression", "table-appropriate power"],
        cut_pressure_notes=[
            "Increase optional cut pressure for inefficient or low-impact cards.",
            "Do not apply cEDH assumptions unless requested.",
        ],
        tone="direct, practical, performance-focused, and respectful",
        example_language="This card is playable, but it has high replaceability because it does not justify its slot compared to alternatives.",
    ),
}


def _add_subtype(profile: PhilosophyProfile) -> None:
    PHILOSOPHY_PROFILES[profile.key] = profile


# Timmy / Tammy subtypes
_add_subtype(PhilosophyProfile(
    key="big_moment",
    label="Big Moment",
    parent="timmy_tammy",
    persona=Persona(masculine="Michael", feminine="Michelle", role="The Big Moment Mentor", core_question="What is the unforgettable play this deck wants to create?"),
    core_philosophy="The player wants the deck to create one unforgettable, table-shaking payoff moment.",
    rules_summary="Protect cards that create, support, protect, or amplify the deck's biggest payoff moment.",
    protect_bias=["declared big-moment cards", "splashy finishers", "X-spells", "doublers", "payoff ramp", "payoff protection"],
    review_bias=["unsupported haymakers", "expensive cards with no meaningful payoff", "win-more cards", "clunky unrelated cards"],
    replacement_bias=["better ramp", "payoff support", "protection", "haste/evasion/trample", "copy or doubling effects", "draw to find payoff"],
    cut_pressure_notes=["Lower cut pressure on central payoff cards.", "Increase cut pressure on expensive cards unrelated to the big moment."],
    tone="enthusiastic, protective of spectacle, still honest about support",
    example_language="This card is expensive, but it supports the deck's Big Moment philosophy because it creates the table-shaking payoff the pilot wants.",
))

_add_subtype(PhilosophyProfile(
    key="big_creature_stompy",
    label="Big Creature / Stompy",
    parent="timmy_tammy",
    persona=Persona(masculine="Alexander", feminine="Alexandria", role="The Stompy Mentor", core_question="How does this deck turn huge creatures into overwhelming battlefield pressure?"),
    core_philosophy="The player wants to cast huge threats, dominate combat, and win through overwhelming board presence.",
    rules_summary="Protect large threats and support that helps cast, protect, enhance, or win through massive creatures.",
    protect_bias=["large central creatures", "ramp into threats", "trample/haste/evasion", "creature protection", "power/toughness payoffs"],
    review_bias=["large creatures with no impact", "redundant top-end", "ramp-light expensive hands", "small value cards that dilute stompy"],
    replacement_bias=["ramp", "creature-based draw", "trample/evasion/haste", "protection", "impactful top-end", "size-to-value payoffs"],
    cut_pressure_notes=["Do not cut expensive cards solely for being expensive if the deck has the infrastructure to support them."],
    tone="bold, combat-focused, and practical",
    example_language="This card fits the deck's Big Creature / Stompy philosophy because it turns mana into visible board pressure.",
))

_add_subtype(PhilosophyProfile(
    key="theme_vibe",
    label="Theme / Vibe",
    parent="timmy_tammy",
    persona=Persona(masculine="Benjamin", feminine="Bethany", role="The Theme Mentor", core_question="Does this card make the deck feel more like itself?"),
    core_philosophy="The player wants the deck to feel like a specific story, aesthetic, tribe, character, joke, or emotional concept.",
    rules_summary="Protect cards that preserve identity while challenging theme cards that prevent the deck from functioning.",
    protect_bias=["declared theme cards", "lore cards", "typal pieces", "flavor cards with function", "identity-preserving cards"],
    review_bias=["flavor-only nonfunctional cards", "vague theme inclusions", "low-impact theme cards in key slots", "identity-clashing staples"],
    replacement_bias=["on-theme role-fillers", "flavorful removal/draw/ramp", "vibe-preserving upgrades", "theme-matching finishers"],
    cut_pressure_notes=["Lower cut pressure for theme-defining cards, especially when they also have mechanical relevance."],
    tone="identity-focused, respectful, and supportive",
    example_language="This card may be below rate, but it strongly supports the deck's Theme / Vibe philosophy.",
))

_add_subtype(PhilosophyProfile(
    key="pet_card",
    label="Pet Card",
    parent="timmy_tammy",
    persona=Persona(masculine="Milo", feminine="Mia", role="The Pet Card Mentor", core_question="How can this deck make room for the cards that matter personally?"),
    core_philosophy="The player wants specific beloved cards protected because they matter personally, even if they are not optimal.",
    rules_summary="Protect explicitly declared pet cards from normal cut pressure while honestly noting performance cost.",
    protect_bias=["declared pet cards", "cards the pilot refuses to cut", "cards with personal value", "intentional pet-card support"],
    review_bias=["unsupported undeclared pet-looking cards", "pet-card packages with high slot cost", "support pieces weak everywhere else"],
    replacement_bias=["improve surrounding shell", "support the pet card if requested", "cut unrelated cards first", "label performance costs gently"],
    cut_pressure_notes=["Declared pet cards should be protected from normal cut recommendations.", "Only recommend cutting declared pet cards if the user asks for no-mercy optimization."],
    tone="respectful, honest, and emotionally safe",
    example_language="This is a declared pet card, so I would not treat it as a normal cut candidate.",
))

_add_subtype(PhilosophyProfile(
    key="let_me_do_my_thing",
    label="Let Me Do My Thing",
    parent="timmy_tammy",
    persona=Persona(masculine="William", feminine="Willow", role="The Experience Mentor", core_question="What helps this deck actually do the thing it was built to do?"),
    core_philosophy="The player wants the deck to reliably reach and execute the experience it was built to create.",
    rules_summary="Protect practical infrastructure that lets the deck's intended experience happen.",
    protect_bias=["core enablers", "ramp", "card draw", "protection", "redundancy", "focused setup", "survival interaction"],
    review_bias=["off-plan cards", "cute distractions", "unrelated splashy cards", "payoffs without enablers", "distracting packages"],
    replacement_bias=["reliable enablers", "ramp/draw/protection", "commander support", "redundancy", "participation-focused interaction"],
    cut_pressure_notes=["Increase cut pressure on cards that delay or distract from the deck's stated thing."],
    tone="supportive, focused, and practical",
    example_language="This card supports the Let Me Do My Thing philosophy because it helps the deck reach its intended experience more often.",
))

_add_subtype(PhilosophyProfile(
    key="battlecruiser",
    label="Battlecruiser",
    parent="timmy_tammy",
    persona=Persona(masculine="Aaron", feminine="Ariana", role="The Battlecruiser Mentor", core_question="How does this deck create a big, dramatic, fully developed Commander game?"),
    core_philosophy="The player wants longer, larger Commander games with big boards, powerful spells, and dramatic late-game turns.",
    rules_summary="Protect big, fair, late-game Commander experiences while challenging slow cards that are not impactful.",
    protect_bias=["big mana engines", "late-game payoffs", "splashy fair finishers", "scalable spells", "recovery tools", "resilient threats"],
    review_bias=["fast combos that bypass the experience", "oppressive locks", "slow low-impact cards", "too much top-end without ramp"],
    replacement_bias=["better ramp", "late-game draw", "fair finishers", "board-based wins", "recovery tools", "splashy functional interaction"],
    cut_pressure_notes=["Slow by design is acceptable; slow without meaningful impact is not."],
    tone="grand, table-aware, and honest about pacing",
    example_language="This card is slow by optimized standards, but it supports the deck's Battlecruiser philosophy by creating a large-scale late-game Commander experience.",
))

# Johnny / Jenny subtypes
_add_subtype(PhilosophyProfile(
    key="engine_builder",
    label="Engine Builder",
    parent="johnny_jenny",
    persona=Persona(masculine="Brad", feminine="Bria", role="The Engine Mentor", core_question="What keeps this deck's machine turning?"),
    core_philosophy="The player wants a repeatable machine where resources convert into value, inevitability, or a win.",
    rules_summary="Protect engine pieces and connector cards while challenging disconnected synergy.",
    protect_bias=["core engine pieces", "repeatable enablers", "repeatable payoffs", "resource converters", "sacrifice outlets", "recursion", "engine connectors"],
    review_bias=["one-shot effects that do not feed engine", "payoffs without enablers", "enablers without payoffs", "unusable resources", "surface-level synergy"],
    replacement_bias=["engine redundancy", "lower-cost enablers", "repeatable effects", "bridge cards", "protection/recursion", "engine-native finishers"],
    cut_pressure_notes=["Lower cut pressure for low-power cards that serve a clear engine role."],
    tone="system-focused, curious, and careful with context",
    example_language="This card may look low-impact by itself, but it acts as an engine connector.",
))

_add_subtype(PhilosophyProfile(
    key="commander_exploiter",
    label="Commander Exploiter",
    parent="johnny_jenny",
    persona=Persona(masculine="Kyle", feminine="Katie", role="The Commander Mentor", core_question="What can this commander do that other commanders cannot?"),
    core_philosophy="The player wants to push the commander's specific text, wording, ability, restriction, or unusual angle.",
    rules_summary="Protect cards that directly exploit the commander's unique abilities while challenging generic cards that ignore the commander.",
    protect_bias=["commander-text synergy", "trigger amplifiers", "ability enablers", "commander protection", "copy/untap/blink/recursion when relevant", "resource converters"],
    review_bias=["generic staples ignoring commander text", "color-fit but plan-miss cards", "unused ability support", "commander dependence without backup"],
    replacement_bias=["commander synergy", "commander protection", "redundancy for commander effects", "trigger/ability multiplication", "backup engines"],
    cut_pressure_notes=["Do not mark commander-specific cards off-plan just because they differ from stock archetype builds."],
    tone="commander-centered, clever, and precise",
    example_language="This card supports the Commander Exploiter philosophy because it interacts with the commander's specific text.",
))

_add_subtype(PhilosophyProfile(
    key="weird_card_rescuer",
    label="Weird Card Rescuer",
    parent="johnny_jenny",
    persona=Persona(masculine="Elund", feminine="Emily", role="The Weird Card Mentor", core_question="Can this strange card become meaningful in this shell?"),
    core_philosophy="The player wants to make an overlooked, strange, bad-looking, or dismissed card meaningful in the right shell.",
    rules_summary="Protect declared weird-card experiments while challenging unsupported oddities.",
    protect_bias=["declared weird build-arounds", "unique effects with support", "low-power contextual role cards", "commander-specific oddities", "declared experiments"],
    review_bias=["weird cards with no support", "unusual cards that do not advance plan", "too-much-support build-arounds", "clever-looking nonfunctional cards"],
    replacement_bias=["support for rescued card", "role redundancy", "protection/recursion", "bridge cards", "experiment-preserving replacements"],
    cut_pressure_notes=["Low generic power is not enough reason to cut a declared weird-card experiment."],
    tone="curious, gentle, experimental, and honest",
    example_language="This card looks weak by normal Commander standards, but it appears to be part of the deck's Weird Card Rescuer philosophy.",
))

_add_subtype(PhilosophyProfile(
    key="theme_mechanic_inventor",
    label="Theme Mechanic Inventor",
    parent="johnny_jenny",
    persona=Persona(masculine="Brandon", feminine="Brenda", role="The Hybrid Theme Mentor", core_question="How do these mechanics overlap into one coherent deck?"),
    core_philosophy="The player wants to combine mechanics, archetypes, or themes that do not normally go together and make the overlap work.",
    rules_summary="Protect bridge cards and hybrid payoffs while challenging isolated packages.",
    protect_bias=["bridge cards", "hybrid payoffs", "flexible enablers", "multi-package cards", "commander-justified blend cards", "coherence support"],
    review_bias=["isolated mini-packages", "one-half-only support", "competing themes", "unsupported payoffs", "ornamental themes", "two-half-deck patterns"],
    replacement_bias=["dual-theme cards", "bridge payoffs", "overlap enablers", "flexible role-fillers", "theme dilution reducers"],
    cut_pressure_notes=["Cards that look off-plan in one archetype may be correct if they connect the hybrid identity."],
    tone="inventive, coherence-focused, and density-aware",
    example_language="This card is valuable because it bridges the deck's two mechanical themes.",
))

_add_subtype(PhilosophyProfile(
    key="constraint_builder",
    label="Self-Imposed Constraint Builder",
    parent="johnny_jenny",
    persona=Persona(masculine="Clark", feminine="Clarissa", role="The Constraint Mentor", core_question="What is the best version of this deck inside the chosen rule?"),
    core_philosophy="The player wants the deck to succeed while obeying a chosen restriction, budget, card pool, or deck-building rule.",
    rules_summary="Optimize within the premise rather than erasing the premise.",
    protect_bias=["constraint-compliant role-fillers", "scarce legal options", "limitation-required choices", "premise-preserving cards", "restricted-pool functional substitutes"],
    review_bias=["restriction violations", "recommendations ignoring constraint", "technical fits with no function", "weaker legal role-fillers when better legal options exist"],
    replacement_bias=["legal upgrades", "creative substitutes", "constraint-compliant ramp/draw/removal/fixing", "honest constraint weakness notes"],
    cut_pressure_notes=["Do not compare restricted cards unfairly against unrestricted illegal options."],
    tone="puzzle-focused, respectful of constraints, and practical",
    example_language="This card is weaker than the unrestricted best-in-slot option, but it satisfies the deck's constraint while filling a necessary role.",
))

_add_subtype(PhilosophyProfile(
    key="combo_builder",
    label="Combo Builder",
    parent="johnny_jenny",
    persona=Persona(masculine="Jasper", feminine="Jennifer", role="The Combo Mentor", core_question="What role does this card play in the combo line?"),
    core_philosophy="The player wants to assemble specific card interactions, loops, or packages that produce a planned payoff.",
    rules_summary="Protect defined combo pieces while challenging unsupported fragments and combo packages that violate user tolerance.",
    protect_bias=["declared combo pieces", "combo enablers", "allowed tutors", "combo redundancy", "combo protection", "recursion", "weak-alone role players", "combo win outlets"],
    review_bias=["unsupported combo fragments", "dead narrow pieces", "slot-heavy packages", "tolerance-violating combos", "off-plan combo pulls", "nonfunctional pseudo-combos"],
    replacement_bias=["missing combo pieces", "redundancy", "power-appropriate tutors", "protection", "recursion", "lower-cost enablers", "clear win outlets"],
    cut_pressure_notes=["Respect user combo tolerance, especially no-infinites or only 3+ card infinites."],
    tone="precise, line-aware, and tolerance-respecting",
    example_language="This card has low standalone impact, but it appears to be a required combo role-player.",
))

# Spike subtypes
_add_subtype(PhilosophyProfile(
    key="consistency_maximizer",
    label="Consistency Maximizer",
    parent="spike",
    persona=Persona(neutral="Avery", role="The Consistency Mentor", core_question="How often does this deck actually do what it is supposed to do?"),
    core_philosophy="The player wants the deck to do its intended thing more often by reducing non-games, dead draws, awkward hands, unsupported packages, and high variance.",
    rules_summary="Protect functional infrastructure and challenge cards that create inconsistency.",
    protect_bias=["role-fillers", "ramp/fixing", "draw/selection", "redundant enablers", "backup effects", "flexible interaction", "fail-state reducers"],
    review_bias=["high-variance cards", "unsupported payoffs", "ideal-board-only cards", "bad-from-behind cards", "narrow dead cards", "isolated packages"],
    replacement_bias=["redundancy", "draw/selection", "reliable ramp/fixing", "lower-curve setup", "flexible interaction", "higher-floor cards"],
    cut_pressure_notes=["Increase pressure on cards that produce nonfunctional hands or unsupported dreams."],
    tone="diagnostic, probability-minded, and practical",
    example_language="This card is powerful when everything lines up, but it creates consistency pressure because the deck does not have enough support to make that scenario happen often.",
))

_add_subtype(PhilosophyProfile(
    key="efficiency_optimizer",
    label="Efficiency Optimizer",
    parent="spike",
    persona=Persona(neutral="Jordan", role="The Efficiency Mentor", core_question="Is this card worth its slot compared to the alternatives?"),
    core_philosophy="The player wants every card to justify its slot through strong rate, low opportunity cost, flexibility, clean role fulfillment, and meaningful contribution.",
    rules_summary="Protect efficient role-fillers and challenge high-opportunity-cost cards.",
    protect_bias=["efficient ramp", "efficient draw", "flexible removal", "role compression", "low-cost enablers", "strong-floor cards", "efficient synergy"],
    review_bias=["overcosted effects", "narrow cards", "win-more cards", "low-impact haymakers", "setup-heavy low-payoff cards", "weaker role versions"],
    replacement_bias=["lower mana value", "flexible effects", "better rate", "role compression", "cheaper interaction", "efficient card advantage"],
    cut_pressure_notes=["Playable but replaceable cards should receive higher optional cut pressure."],
    tone="direct, slot-conscious, and practical",
    example_language="This card is playable, but it has high replaceability because it costs more mana than comparable effects.",
))

_add_subtype(PhilosophyProfile(
    key="curve_mana_discipline",
    label="Curve and Mana Discipline",
    parent="spike",
    persona=Persona(neutral="River", role="The Mana Mentor", core_question="Can this deck cast its cards on time and use its mana well?"),
    core_philosophy="The player wants the deck's mana base, ramp, curve, and sequencing to support the plan cleanly.",
    rules_summary="Protect mana infrastructure and challenge curve, color, and sequencing pressure.",
    protect_bias=["lands/fixing", "curve-matching ramp", "early setup", "cheap role-fillers", "curve bridges", "supported mana sinks", "cost reducers", "mana infrastructure"],
    review_bias=["too much 5+ mana", "redundant expensive payoffs", "low land counts", "mismatched ramp", "color strain", "tapped-land pressure", "empty early turns"],
    replacement_bias=["correct land count", "better fixing", "appropriate ramp", "curve smoothing", "early interaction/setup", "color cleanup", "top-end reduction"],
    cut_pressure_notes=["Do not overcut top-end in decks intentionally built to ramp into big threats; check ramp support first."],
    tone="structural, diagnostic, and sequencing-aware",
    example_language="This card may be powerful, but it adds pressure to an already crowded mana value.",
))

_add_subtype(PhilosophyProfile(
    key="competitive_closer",
    label="Competitive Closer",
    parent="spike",
    persona=Persona(neutral="Charlie", role="The Closing Mentor", core_question="How does this deck actually end the game?"),
    core_philosophy="The player wants the deck to convert advantage into a decisive win rather than endlessly generating value.",
    rules_summary="Protect finishers and challenge cards that produce value without helping close.",
    protect_bias=["clear finishers", "allowed compact win packages", "resource-to-lethal conversion", "combat closers", "inevitability", "actual payoff outlets"],
    review_bias=["value without payoff", "redundant setup", "game-prolonging nonfinishers", "slow win conditions", "unrealistic payoff states", "tolerance-conflicting closers"],
    replacement_bias=["clearer finishers", "resource-to-victory payoffs", "compact outlets", "combat finishers", "evasion/haste/trample", "fewer pure value cards"],
    cut_pressure_notes=["Increase pressure on cards that add value without helping the deck end games once ahead."],
    tone="decisive, win-conversion focused, and table-aware",
    example_language="The deck appears able to generate resources, but this card adds more value without helping convert that value into a win.",
))

_add_subtype(PhilosophyProfile(
    key="power_level_calibrator",
    label="Power-Level Calibrator",
    parent="spike",
    persona=Persona(neutral="Kai", role="The Table-Fit Mentor", core_question="Is this deck the correct strength for where it is actually played?"),
    core_philosophy="The player wants the deck to land at the correct strength for the intended table, not simply become as strong as possible.",
    rules_summary="Protect table-fit cards and challenge cards that overshoot or undershoot the desired environment.",
    protect_bias=["target-power cards", "fair effective wins", "table-appropriate interaction", "identity-preserving cards", "pod-aligned cards"],
    review_bias=["too-weak cards", "too-strong cards", "tolerance-violating combos", "socially mismatched lock/stax", "overshooting fast mana/tutors", "too-slow cards for fast pods"],
    replacement_bias=["power-appropriate upgrades", "synergy/consistency over raw power when requested", "table-speed interaction", "tolerance-fit finishers", "non-overshooting upgrades"],
    cut_pressure_notes=["Stronger is not always better; judge by intended table fit."],
    tone="balanced, table-aware, and precise",
    example_language="This card is powerful, but it may push the deck above the stated table expectation.",
))

_add_subtype(PhilosophyProfile(
    key="interaction_controller",
    label="Interaction Controller",
    parent="spike",
    persona=Persona(neutral="Riley", role="The Interaction Mentor", core_question="What can this deck currently not answer?"),
    core_philosophy="The player wants the deck to survive, answer threats, protect its plan, and avoid losing to preventable problems.",
    rules_summary="Protect appropriate answers and challenge exposed or overreactive builds.",
    protect_bias=["efficient removal", "flexible answers", "protection", "appropriate wipes", "relevant graveyard hate", "artifact/enchantment answers", "stack interaction", "synergy-friendly interaction"],
    review_bias=["too little interaction", "narrow answers without meta reason", "expensive removal", "sorcery-speed issues", "unprotected commander dependence", "common-threat vulnerability", "overreactive bloat"],
    replacement_bias=["flexible removal", "efficient protection", "color-appropriate answers", "strategy-supporting interaction", "beneficial wipes", "resilience tools"],
    cut_pressure_notes=["Do not turn every deck into control; protect enough interaction to prevent avoidable losses."],
    tone="practical, threat-aware, and proactive-plan respectful",
    example_language="This deck is proactive, but it currently has limited ways to answer opposing engines once they resolve.",
))


SUBTYPE_KEYS: List[str] = [
    "big_moment",
    "big_creature_stompy",
    "theme_vibe",
    "pet_card",
    "let_me_do_my_thing",
    "battlecruiser",
    "engine_builder",
    "commander_exploiter",
    "weird_card_rescuer",
    "theme_mechanic_inventor",
    "constraint_builder",
    "combo_builder",
    "consistency_maximizer",
    "efficiency_optimizer",
    "curve_mana_discipline",
    "competitive_closer",
    "power_level_calibrator",
    "interaction_controller",
]


PHILOSOPHY_NUMBER_ALIASES = {
    "1": "big_moment",
    "2": "big_creature_stompy",
    "3": "theme_vibe",
    "4": "pet_card",
    "5": "let_me_do_my_thing",
    "6": "battlecruiser",
    "7": "engine_builder",
    "8": "commander_exploiter",
    "9": "weird_card_rescuer",
    "10": "theme_mechanic_inventor",
    "11": "constraint_builder",
    "12": "combo_builder",
    "13": "consistency_maximizer",
    "14": "efficiency_optimizer",
    "15": "curve_mana_discipline",
    "16": "competitive_closer",
    "17": "power_level_calibrator",
    "18": "interaction_controller",
}


def normalize_philosophy_key(key: Optional[str]) -> str:
    """Normalize user/env/config input into a known philosophy key."""
    if not key:
        return "balanced_unknown"

    normalized = str(key).strip().lower()
    if not normalized:
        return "balanced_unknown"

    if normalized in PHILOSOPHY_NUMBER_ALIASES:
        return PHILOSOPHY_NUMBER_ALIASES[normalized]

    normalized = normalized.replace(" / ", "_").replace("/", "_").replace("-", "_").replace(" ", "_")

    aliases = {
        "balanced": "balanced_unknown",
        "unknown": "balanced_unknown",
        "balanced_unknown": "balanced_unknown",
        "rowan": "balanced_unknown",
        "timmy": "timmy_tammy",
        "tammy": "timmy_tammy",
        "timmy_tammy": "timmy_tammy",
        "johnny": "johnny_jenny",
        "jenny": "johnny_jenny",
        "johnny_jenny": "johnny_jenny",
        "big_creature": "big_creature_stompy",
        "stompy": "big_creature_stompy",
        "theme": "theme_vibe",
        "vibe": "theme_vibe",
        "self_imposed_constraint_builder": "constraint_builder",
        "constraint": "constraint_builder",
        "combo": "combo_builder",
        "mana_discipline": "curve_mana_discipline",
        "curve": "curve_mana_discipline",
        "interaction": "interaction_controller",
    }
    return aliases.get(normalized, normalized)


def get_philosophy_profile(key: Optional[str]) -> PhilosophyProfile:
    """Return a philosophy profile. Defaults safely to Balanced / Unknown."""
    normalized = normalize_philosophy_key(key)
    return PHILOSOPHY_PROFILES.get(normalized, PHILOSOPHY_PROFILES["balanced_unknown"])


def resolve_persona_name(key: Optional[str], preference: GuidePreference = "either") -> Optional[str]:
    """Resolve the display name for the selected philosophy/subtype."""
    return get_philosophy_profile(key).persona.resolve_name(preference)




def _dedupe_preserve_order(values: list[str]) -> list[str]:
    """Return unique, non-empty strings while preserving first-seen order."""
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        cleaned = str(value).strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        output.append(cleaned)
    return output


def _build_bias_profile(profile: PhilosophyProfile) -> dict:
    """Build v0.6.6.1 philosophy bias foundation data.

    This exposes the *shape* of future cut/replacement bias without applying it.
    Cut logic and collection candidate logic consume these fields as light nudges. They remain diagnostics/report context for legality, strategy detection, required cuts, and collection mode boundaries.
    """
    # Explicit profile fields win if a future profile supplies them. Otherwise,
    # map existing human-facing philosophy guidance into role-like buckets that
    # later logic can consume.
    protect_roles = list(profile.cut_bias_protect_roles)
    review_roles = list(profile.cut_bias_review_roles)
    replacement_roles = list(profile.replacement_bias_roles)

    key_specific: dict[str, dict[str, list[str] | str]] = {
        "balanced_unknown": {
            "protect": ["primary_plan_support", "commander_synergy", "essential_infrastructure", "declared_user_intent"],
            "review": ["off_plan", "unsupported_package", "role_imbalance", "user_intent_conflict"],
            "replacement": ["role_balance", "strategy_support", "mana_consistency", "clear_deck_identity"],
            "strength": "neutral",
        },
        "big_moment": {
            "protect": ["declared_big_moment_card", "big_moment_enabler", "splashy_finisher", "x_spell", "doublers", "payoff_ramp", "payoff_protection"],
            "review": ["unsupported_haymaker", "expensive_no_payoff", "win_more", "clunky_unrelated_card"],
            "replacement": ["better_ramp", "payoff_support", "protection", "haste_evasion_trample", "copy_or_doubling_effect", "draw_to_find_payoff"],
            "strength": "light",
        },
        "big_creature_stompy": {
            "protect": ["large_central_creature", "ramp_into_threats", "haste_evasion_trample", "creature_protection", "power_toughness_payoff"],
            "review": ["large_creature_no_impact", "redundant_top_end", "ramp_light_expensive_hand", "small_value_dilution"],
            "replacement": ["ramp", "creature_based_draw", "trample_evasion_haste", "protection", "impactful_top_end", "size_to_value_payoff"],
            "strength": "light",
        },
        "theme_vibe": {
            "protect": ["declared_theme", "typal_piece", "flavor_with_function", "identity_preserving_card"],
            "review": ["flavor_only_low_function", "identity_clashing_staple", "low_impact_theme_card"],
            "replacement": ["on_theme_role_filler", "flavorful_removal", "flavorful_draw", "vibe_preserving_upgrade"],
            "strength": "light",
        },
        "pet_card": {
            "protect": ["declared_pet_card", "personal_attachment_card", "build_around_memory_card"],
            "review": ["surrounding_shell_weakness", "support_piece_not_helping_pet_card"],
            "replacement": ["pet_card_support", "shell_consistency", "protection_for_pet_card"],
            "strength": "light",
        },
        "commander_exploiter": {
            "protect": ["commander_text_synergy", "commander_scaling", "commander_protection", "ability_enabler", "resource_converter", "commander_specific_payoff"],
            "review": ["generic_goodstuff", "commander_ignoring_card", "unused_ability_support", "color_fit_plan_miss"],
            "replacement": ["commander_synergy", "commander_protection", "ability_multiplier", "redundancy_for_commander_effect", "backup_engine"],
            "strength": "light",
        },
        "engine_builder": {
            "protect": ["engine_piece", "connector_card", "enabler", "payoff_bridge", "weak_alone_strong_in_context"],
            "review": ["unsupported_engine_piece", "disconnected_package", "cute_but_unconnected_card"],
            "replacement": ["engine_redundancy", "connector_piece", "enabler_density", "payoff_support"],
            "strength": "light",
        },
        "combo_builder": {
            "protect": ["combo_piece", "combo_tutor", "combo_protection", "combo_enabler", "combo_payoff"],
            "review": ["partial_combo_without_support", "unwanted_combo_pressure", "dead_combo_piece"],
            "replacement": ["combo_consistency", "combo_protection", "cleaner_enabler", "backup_plan"],
            "strength": "light",
        },
        "curve_mana_discipline": {
            "protect": ["efficient_ramp", "cheap_interaction", "curve_smoothing", "mana_fixing", "low_curve_enabler"],
            "review": ["overcosted_effect", "curve_clog", "clunky_top_end", "mana_intensive_card"],
            "replacement": ["lower_curve", "efficient_role_filler", "better_mana", "cheap_card_selection"],
            "strength": "medium",
        },
        "power_level_calibrator": {
            "protect": ["table_fit_card", "bracket_appropriate_interaction", "power_limit_respecting_card"],
            "review": ["bracket_pressure", "table_mismatch", "unwanted_fast_mana", "unwanted_tutor", "unwanted_combo"],
            "replacement": ["table_fit_upgrade", "bracket_appropriate_answer", "power_matched_role_filler"],
            "strength": "medium",
        },
        "interaction_controller": {
            "protect": ["flexible_interaction", "synergy_interaction", "board_control_piece", "commander_protection"],
            "review": ["narrow_answer", "dead_interaction", "threat_mismatch", "uninteractive_payoff"],
            "replacement": ["better_interaction", "role_compression", "table_specific_answer", "protective_interaction"],
            "strength": "medium",
        },
        "spike": {
            "protect": ["efficient_ramp", "efficient_draw", "flexible_interaction", "reliable_mana", "clean_finisher"],
            "review": ["overcosted_effect", "low_impact_card", "win_more", "narrow_card", "clunky_top_end"],
            "replacement": ["efficiency_upgrade", "consistency_upgrade", "role_compression", "better_interaction"],
            "strength": "medium",
        },
    }

    data = key_specific.get(profile.key)
    if data:
        protect_roles.extend(data.get("protect", []))
        review_roles.extend(data.get("review", []))
        replacement_roles.extend(data.get("replacement", []))
        strength = str(data.get("strength", profile.bias_strength or "guidance"))
    else:
        # Safe default for profiles that do not yet have explicit bias maps.
        protect_roles.extend(profile.protect_bias)
        review_roles.extend(profile.review_bias)
        replacement_roles.extend(profile.replacement_bias)
        if profile.parent == "spike":
            strength = "medium"
        elif profile.parent in {"timmy_tammy", "johnny_jenny"}:
            strength = "light"
        else:
            strength = profile.bias_strength or "guidance"

    return {
        "philosophy_bias_foundation_active": True,
        "philosophy_bias_foundation_version": "v0.6.6.4.1",
        "bias_scoring_active": True,
        "cut_bias_scoring_active": True,
        "replacement_bias_scoring_active": True,
        "bias_strength": strength,
        "bias_warning": profile.bias_warning,
        "cut_bias_protect_roles": _dedupe_preserve_order(protect_roles),
        "cut_bias_review_roles": _dedupe_preserve_order(review_roles),
        "replacement_bias_roles": _dedupe_preserve_order(replacement_roles),
    }

def build_philosophy_context(
    key: Optional[str] = None,
    guide_preference: GuidePreference = "either",
) -> dict:
    """Build a serializable context object for reports, prompts, and analysis."""
    profile = get_philosophy_profile(key)
    guide_name = profile.persona.resolve_name(guide_preference)

    parent_label = None
    if profile.parent:
        parent_label = PHILOSOPHY_PROFILES[profile.parent].label
    elif profile.key == "balanced_unknown":
        parent_label = "Balanced / Unknown"

    summary_fields = _summaries_for_profile(profile)
    bias_fields = _build_bias_profile(profile)

    return {
        "key": profile.key,
        "label": profile.label,
        "parent_key": profile.parent,
        "parent_label": parent_label,
        "guide_name": guide_name,
        "guide_role": profile.persona.role,
        "core_question": profile.persona.core_question,
        "core_philosophy": profile.core_philosophy,
        "rules_summary": profile.rules_summary,
        "protect_bias": list(profile.protect_bias),
        "review_bias": list(profile.review_bias),
        "replacement_bias": list(profile.replacement_bias),
        "cut_pressure_notes": list(profile.cut_pressure_notes),
        "tone": profile.tone,
        "example_language": profile.example_language,
        "named_guide_enabled": guide_preference != "none",
        **summary_fields,
        **bias_fields,
    }


def _guide_display_name(context: dict) -> str:
    """Return the best user-facing name for the selected guide/lens."""
    if context.get("named_guide_enabled", True) and context.get("guide_name"):
        return str(context["guide_name"])
    return str(context.get("label", "Balanced / Unknown"))



def _comma_list(values: list[str], limit: int = 6) -> str:
    """Render a short comma-separated list for report guidance."""
    cleaned = [str(value).strip() for value in values if str(value).strip()]
    return ", ".join(cleaned[:limit]) if cleaned else "None listed"


def _sentence_list(values: list[str], limit: int = 5) -> str:
    """Render short guidance values as a readable comma list."""
    return _comma_list(values, limit=limit)


def _build_short_lens_summary(profile: PhilosophyProfile) -> str:
    """Return one concise at-a-glance sentence for the selected lens."""
    if profile.key == "balanced_unknown":
        return "Use this lens to discover the deck's natural identity before making strong philosophy assumptions."

    parent = PHILOSOPHY_PROFILES.get(profile.parent).label if profile.parent and profile.parent in PHILOSOPHY_PROFILES else profile.label
    if parent == "Timmy / Tammy":
        return f"Use this lens to preserve the deck's intended experience while checking that the support structure actually lets that experience happen."
    if parent == "Johnny / Jenny":
        return f"Use this lens to protect the deck's idea, engine, constraint, or clever interaction while challenging pieces that do not actually connect."
    if parent == "Spike":
        return f"Use this lens to improve performance at the intended table without assuming cEDH or overriding the pilot's power goal."
    return profile.rules_summary


def _build_report_guidance_summary(profile: PhilosophyProfile) -> str:
    """Return a report-facing explanation of how to read cards through this lens."""
    if profile.key == "theme_vibe":
        return "Judge cards by whether they make the deck feel more like its intended story, creature type, joke, table experience, or aesthetic. Theme cards get extra respect when they also perform a useful role; flavor-only cards can still be challenged if they weaken function."
    if profile.key == "pet_card":
        return "Declared pet cards should be protected from normal optimization pressure, while the surrounding shell should be improved so those cards can matter in games."
    if profile.key == "combo_builder":
        return "Evaluate whether each card finds, protects, enables, or cleanly supports the intended combo or interaction chain without adding unwanted combo pressure."
    if profile.key == "commander_exploiter":
        return "Prioritize cards that specifically exploit the commander's rules text over generic good cards that do not strengthen the commander's unique plan."
    if profile.key == "curve_mana_discipline":
        return "Evaluate whether the mana curve, land count, ramp, and color requirements let the deck actually execute its plan on time."
    if profile.key == "power_level_calibrator":
        return "Evaluate whether the deck is matched to the target table experience; stronger is not automatically better if it violates the intended bracket."
    if profile.key == "balanced_unknown":
        return "Use the report to identify the deck's likely plan, tensions, and possible philosophy lean without applying subtype-specific assumptions yet."
    return profile.rules_summary


def _summaries_for_profile(profile: PhilosophyProfile) -> dict:
    """Build v0.6.5.3 summary fields from the existing philosophy profile."""
    protect = _sentence_list(profile.protect_bias, 6)
    question = _sentence_list(profile.review_bias, 6)
    prefer = _sentence_list(profile.replacement_bias, 6)
    return {
        "short_lens_summary": _build_short_lens_summary(profile),
        "report_guidance_summary": _build_report_guidance_summary(profile),
        "protect_summary": protect,
        "question_summary": question,
        "prefer_summary": prefer,
        "pilot_override_note": "Pilot-stated intent overrides this lens whenever the two conflict.",
        "subtype_summary_active": True,
        "subtype_summary_version": "v0.6.5.3",
    }


def render_philosophy_report_guidance(context: dict) -> str:
    """Render v0.6.5.3 report-facing philosophy guidance.

    This is intentionally guidance text only. It does not change scoring,
    legality, strategy detection, collection matching, or required cuts.
    """
    label = context.get("label", "Balanced / Unknown")
    key = context.get("key", "balanced_unknown")
    guide = _guide_display_name(context)
    parent = context.get("parent_label") or label
    protect = context.get("protect_summary") or _comma_list(context.get("protect_bias", []), 6)
    review = context.get("question_summary") or _comma_list(context.get("review_bias", []), 6)
    replacement = context.get("prefer_summary") or _comma_list(context.get("replacement_bias", []), 6)

    lines = [
        "**v0.6.5.3 Philosophy Subtype Report Summary:** This block explains how to read this report through the selected lens. It is still guidance only and does not change legality, deck size, color identity, strategy detection, required cuts, collection matching, cut scores, or replacement scores.",
        "",
        "**At-a-glance lens summary:**",
        f"- {context.get('short_lens_summary') or context.get('rules_summary', 'Use the selected lens as review framing only.')}",
        "",
        "**How to read cards through this lens:**",
        f"- {context.get('report_guidance_summary') or context.get('rules_summary', 'Use this lens to shape explanation style and review priorities.')}",
        "",
        "**Protect / Question / Prefer:**",
        f"- Protect: {protect}.",
        f"- Question: {review}.",
        f"- Prefer replacements that support: {replacement}.",
        "",
        "**Review boundaries:**",
        "- Treat all philosophy language as review framing, not as a hard mechanical override.",
        "- If the pilot's stated intent conflicts with this lens, the pilot's stated intent wins.",
        "- Required legality fixes still outrank philosophy preference.",
    ]

    if key == "balanced_unknown":
        lines.extend([
            "- Balanced / Unknown should avoid strong assumptions, identify possible philosophy lean, and recommend choosing a deeper lens only when it would materially improve the review.",
        ])
    elif parent in {"Timmy / Tammy", "Johnny / Jenny", "Spike"}:
        lines.append(f"- Because this is under {parent}, preserve the deck's chosen style while still checking whether the support structure actually works.")

    if context.get("example_language"):
        lines.extend(["", "**Example review language:**", f"> {context.get('example_language')}"])

    if context.get("named_guide_enabled", True):
        lines.extend([
            "",
            "**Guide presentation note:**",
            f"- {guide} should be used as a concise mentor frame, not as heavy roleplay or a separate character speaking in first person.",
        ])
    else:
        lines.extend([
            "",
            "**Guide presentation note:**",
            "- Named guide presentation is disabled; use philosophy labels only.",
        ])

    return "\n".join(lines)

def render_guide_introduction_instruction(context: dict) -> str:
    """Render prompt instructions for the AI that will use the generated user-guided prompt.

    This is intentionally instruction text, not roleplay. The guide should be introduced
    briefly after the deck report is received, then the review should move directly into
    the numbered intake flow.
    """
    guide = _guide_display_name(context)
    lens = context.get("label", "Balanced / Unknown")
    role = context.get("guide_role", "Guide")
    question = context.get("core_question", "What does this deck want to do?")
    named_enabled = context.get("named_guide_enabled", True)

    if named_enabled and context.get("guide_name"):
        opening = f"After receiving the deck report, briefly introduce {guide} as the {role}."
    else:
        opening = f"After receiving the deck report, briefly introduce the {lens} philosophy lens."

    return "\n".join([
        opening,
        f"Use this guide question to frame the review: {question}",
        "Keep the introduction to 2-4 sentences, then immediately ask Section 1.",
        "The guide/persona is a mentor framing device only; it must not override legality, deck size, strategy detection, budget, combo tolerance, bracket goals, collection mode, or user answers.",
    ])


def render_philosophy_prompt_showcase_block(context: dict) -> str:
    """Render v0.6.5.4 prompt-facing philosophy QA / showcase guidance.

    This block is meant for the AI that receives the generated user-guided prompt.
    It keeps guide/persona behavior consistent across lenses and remains
    guidance-only: no scoring, legality, strategy, or collection logic changes.
    """
    if not context:
        return ""

    guide = _guide_display_name(context)
    lens = context.get("label", "Balanced / Unknown")
    role = context.get("guide_role", "Guide")
    question = context.get("core_question", "What does this deck want to do?")
    short_summary = context.get("short_lens_summary") or context.get("rules_summary", "Use this lens as review framing only.")
    report_guidance = context.get("report_guidance_summary") or context.get("rules_summary", "Use this lens to shape review language and priorities.")
    protect = context.get("protect_summary") or _comma_list(context.get("protect_bias", []), 6)
    review = context.get("question_summary") or _comma_list(context.get("review_bias", []), 6)
    prefer = context.get("prefer_summary") or _comma_list(context.get("replacement_bias", []), 6)
    pilot_override = context.get("pilot_override_note") or "Pilot-stated intent beats the philosophy lens when they conflict."

    lines = [
        "## v0.6.5.4 Philosophy Prompt QA / Showcase Polish",
        "",
        f"- Lens: {lens}",
        f"- Guide frame: {guide} — {role}",
        f"- Guiding question: {question}",
        f"- One-sentence lens summary: {short_summary}",
        "",
        "Use this lens in the guided review as follows:",
        f"1. Read cards through this lens: {report_guidance}",
        f"2. Protect or lower cut pressure for: {protect}.",
        f"3. Question or review more carefully: {review}.",
        f"4. Prefer recommendations that support: {prefer}.",
        f"5. Pilot override rule: {pilot_override}",
        "6. Introduce the guide/lens once after the deck report, then continue as a practical deck-review assistant.",
        "7. Do not use the guide as a roleplay character, speaking persona, or substitute for strategy evidence.",
        "8. If the pilot gives a partial section answer, ask only for the missing or unclear items from that section before moving on.",
    ]

    return "\n".join(lines)


def render_philosophy_guide_section(context: dict) -> str:
    """Render the Philosophy Guide report section.

    v0.6.5.1 expands this from a simple label block into a report guidance
    checkpoint while keeping philosophy as non-scoring guidance.
    """
    selected_lens = context.get("label", "Balanced / Unknown")
    parent_label = context.get("parent_label")
    guide_name = context.get("guide_name")
    named_enabled = context.get("named_guide_enabled", True)

    lines = ["## Philosophy Guide", ""]
    lines.append(f"**Selected Lens:** {selected_lens}")

    if named_enabled and guide_name:
        lines.append(f"**Guide:** {guide_name}")
        lines.append(f"**Guide Role:** {context.get('guide_role', 'Guide')}")
    else:
        lines.append("**Guide:** No named guide selected")

    if parent_label and parent_label != selected_lens:
        lines.append(f"**Parent Philosophy:** {parent_label}")

    lines.append(f"**Primary Question:** {context.get('core_question', 'What does this deck want to do?')}")
    lines.append("")
    lines.append(context.get("rules_summary", "Use a balanced exploratory lens."))
    lines.append("")
    lines.append("**Boundary:** This philosophy is a review lens. It does not replace strategy detection, legality, deck-size rules, color identity, budget, combo tolerance, bracket goals, collection limits, or user-stated intent.")
    lines.append("")

    if context.get("short_lens_summary"):
        lines.append("**Lens Summary:** " + context.get("short_lens_summary", ""))
        lines.append("")

    if context.get("report_guidance_summary"):
        lines.append("**How to Use This Lens:** " + context.get("report_guidance_summary", ""))
        lines.append("")

    if context.get("core_philosophy"):
        lines.append("**Core Philosophy:** " + context.get("core_philosophy", ""))
        lines.append("")

    if context.get("protect_bias"):
        lines.append("**What this lens tends to protect:** " + ", ".join(context["protect_bias"][:6]))
        lines.append("")

    if context.get("review_bias"):
        lines.append("**What this lens tends to challenge:** " + ", ".join(context["review_bias"][:6]))
        lines.append("")

    if context.get("replacement_bias"):
        lines.append("**Replacement Bias:** " + ", ".join(context["replacement_bias"][:6]))
        lines.append("")

    if context.get("cut_pressure_notes"):
        lines.append("**Cut-Pressure Notes:**")
        for note in context["cut_pressure_notes"][:4]:
            lines.append(f"- {note}")
        lines.append("")

    lines.append(render_philosophy_report_guidance(context).rstrip())
    lines.append("")

    return "\n".join(lines)

def render_philosophy_prompt_questions(context: dict) -> str:
    """Render philosophy guidance for the user-guided prompt.

    This function intentionally does not replace the main seven-section workflow.
    It gives the reviewing AI a concise guide/persona frame and a few optional
    philosophy-specific clarifying questions.
    """
    guide = _guide_display_name(context)
    key = context.get("key", "balanced_unknown")

    base = [
        "### Philosophy Guide Context",
        f"Selected lens: {context.get('label', 'Balanced / Unknown')}",
        f"Guide: {guide}",
        f"Guide role: {context.get('guide_role', 'Guide')}",
        f"Primary question: {context.get('core_question', 'What does this deck want to do?')}",
        "",
        "Guide introduction instruction:",
        render_guide_introduction_instruction(context),
        "",
        "Philosophy boundary:",
        "Use this philosophy as a review lens only. Strategy detection, legality, deck size, color identity, budget, combo tolerance, bracket goals, and user answers take priority.",
        "",
        "Optional later philosophy clarification questions if needed; do not ask these before Section 1:",
    ]

    question_map = {
        "balanced_unknown": [
            "1. Do you want to stay Balanced / Unknown, or choose Timmy/Tammy, Johnny/Jenny, Spike, or a subtype?",
            "2. Are you trying to discover the deck's identity, refine it, or optimize it?",
            "3. What kind of experience do you want this deck to create?",
        ],
        "big_moment": [
            "1. What is the one unforgettable play this deck wants to create?",
            "2. Is that moment supposed to win the game, or is a memorable story enough?",
            "3. Which cards directly create, protect, or amplify that moment?",
        ],
        "pet_card": [
            "1. Which cards are protected because they matter personally?",
            "2. Are those cards protected permanently, or only until they create the desired moment once?",
            "3. How much performance cost are you willing to accept for those cards?",
        ],
        "commander_exploiter": [
            "1. What specific commander text are you trying to exploit?",
            "2. Which cards look weak generally but become important because of the commander?",
            "3. Should generic good cards lose priority if they do not support the commander’s specific plan?",
        ],
        "combo_builder": [
            "1. Are there known combos you want to include?",
            "2. Are infinite combos welcome, restricted, or unwanted?",
            "3. Should the combo be the main win condition or a backup plan?",
            "4. Do you prefer compact combos or multi-piece interaction chains?",
        ],
        "power_level_calibrator": [
            "1. What kind of table is this deck meant for?",
            "2. Are infinites, tutors, fast mana, or stax acceptable?",
            "3. Should the deck be stronger, softer, or better matched?",
            "4. Are there cards you want to avoid because they create bad table experiences?",
        ],
        "interaction_controller": [
            "1. What types of threats does your table usually present?",
            "2. What does this deck currently struggle to answer?",
            "3. Should interaction be proactive and synergy-friendly, or are pure answers acceptable?",
        ],
    }

    questions = question_map.get(key, [
        f"1. Through the {context.get('label', 'selected')} lens, what matters most to preserve?",
        "2. What kinds of cards should receive lower cut pressure?",
        "3. What kinds of cards should be reviewed more aggressively?",
    ])

    return "\n".join(base + questions)


def render_philosophy_diagnostics_section(context: dict) -> str:
    """Render a detailed debug section for the selected philosophy/persona."""
    guide = _guide_display_name(context)
    lines = [
        "## Philosophy / Persona Context",
        f"- Selected lens: {context.get('label', 'Balanced / Unknown')}",
        f"- Philosophy key: {context.get('key', 'balanced_unknown')}",
        f"- Parent philosophy: {context.get('parent_label') or 'None'}",
        f"- Named guide enabled: {context.get('named_guide_enabled', True)}",
        f"- Resolved guide: {guide}",
        f"- Guide role: {context.get('guide_role', 'Guide')}",
        f"- Primary question: {context.get('core_question', 'What does this deck want to do?')}",
        f"- Tone: {context.get('tone', 'balanced, clear, and supportive')}",
        "- Boundary: Philosophy/persona is guidance only; it does not alter legality, deck size, color identity, strategy detection, required cuts, or collection matching in v0.6.5.x.",
        "- v0.6.5.1 report guidance active: Yes",
        "- v0.6.5.3 subtype report summary active: Yes",
        f"- Report guidance summary available: {'Yes' if context.get('report_guidance_summary') else 'No'}",
        f"- Protect / Question / Prefer summaries available: {'Yes' if context.get('protect_summary') and context.get('question_summary') and context.get('prefer_summary') else 'No'}",
        "- Guidance scope: normal report framing and diagnostics; v0.6.6.4.1 applies light optional-cut and replacement-candidate nudges with visibility counters while preserving legality, strategy, collection mode, and quality gates.",
        f"- v0.6.6.4.1 philosophy cut/replacement bias active: {'Yes' if context.get('philosophy_bias_foundation_active') else 'No'}",
        f"- Bias profile available: {'Yes' if context.get('cut_bias_protect_roles') or context.get('cut_bias_review_roles') or context.get('replacement_bias_roles') else 'No'}",
        f"- Bias strength: {context.get('bias_strength', 'guidance')}",
        f"- Bias currently applied to cut scoring: {'Yes' if context.get('cut_bias_scoring_active') else 'No'}",
        f"- Bias currently applied to replacement scoring: {'Yes' if context.get('replacement_bias_scoring_active') else 'No'}",
    ]

    if context.get("short_lens_summary"):
        lines.append("- Short lens summary: " + str(context.get("short_lens_summary")))
    if context.get("report_guidance_summary"):
        lines.append("- Report guidance summary: " + str(context.get("report_guidance_summary")))

    if context.get("protect_bias"):
        lines.append("- Protect bias: " + ", ".join(context["protect_bias"][:8]))
    if context.get("review_bias"):
        lines.append("- Review bias: " + ", ".join(context["review_bias"][:8]))
    if context.get("replacement_bias"):
        lines.append("- Replacement bias: " + ", ".join(context["replacement_bias"][:8]))
    if context.get("cut_pressure_notes"):
        lines.append("- Cut-pressure notes:")
        for note in context["cut_pressure_notes"][:5]:
            lines.append(f"  - {note}")

    if context.get("philosophy_bias_foundation_active"):
        lines.extend([
            "",
            "## v0.6.6.1 Philosophy Bias Foundation",
            "- v0.6.6.1 bias foundation active: Yes",
            "- v0.6.6.4.1 optional-cut and replacement-candidate bias active: Yes",
            f"- Bias profile version: {context.get('philosophy_bias_foundation_version', 'v0.6.6.4.1')}",
            f"- Bias strength: {context.get('bias_strength', 'guidance')}",
            f"- Bias currently applied to cut scoring: {'Yes' if context.get('cut_bias_scoring_active') else 'No'}",
        f"- Bias currently applied to replacement scoring: {'Yes' if context.get('replacement_bias_scoring_active') else 'No'}",
            "- Scope: cut-side bias is now a small optional nudge. Replacement bias remains profile data only.",
            f"- Protect-biased roles available: {'Yes' if context.get('cut_bias_protect_roles') else 'No'}",
            f"- Review-biased roles available: {'Yes' if context.get('cut_bias_review_roles') else 'No'}",
            f"- Replacement-biased roles available: {'Yes' if context.get('replacement_bias_roles') else 'No'}",
        ])
        if context.get("cut_bias_protect_roles"):
            lines.append("- Protect-biased roles: " + ", ".join(context["cut_bias_protect_roles"][:10]))
        if context.get("cut_bias_review_roles"):
            lines.append("- Review-biased roles: " + ", ".join(context["cut_bias_review_roles"][:10]))
        if context.get("replacement_bias_roles"):
            lines.append("- Replacement-biased roles: " + ", ".join(context["replacement_bias_roles"][:10]))
        if context.get("bias_warning"):
            lines.append("- Bias warning: " + str(context.get("bias_warning")))

    return "\n".join(lines)


def get_grouped_selection_menu() -> str:
    """Return a user-facing philosophy subtype menu grouped by parent philosophy."""
    return """Choose philosophy depth:
1. Balanced / Unknown
2. Big 3 philosophy only
3. Specific philosophy subtype

Big 3 Philosophy:
- Timmy / Tammy
- Johnny / Jenny
- Spike

Timmy / Tammy — Experience, spectacle, theme, and personal joy
1. Big Moment
2. Big Creature / Stompy
3. Theme / Vibe
4. Pet Card
5. Let Me Do My Thing
6. Battlecruiser

Johnny / Jenny — Synergy, invention, engines, and clever concepts
7. Engine Builder
8. Commander Exploiter
9. Weird Card Rescuer
10. Theme Mechanic Inventor
11. Self-Imposed Constraint Builder
12. Combo Builder

Spike — Performance, consistency, efficiency, and table fit
13. Consistency Maximizer
14. Efficiency Optimizer
15. Curve and Mana Discipline
16. Competitive Closer
17. Power-Level Calibrator
18. Interaction Controller
"""


def get_cut_modifier_hints(key: Optional[str]) -> dict:
    """
    Return lightweight hints for cut logic.

    Existing cut logic can consume these hints without needing persona names.
    MVP implementation should label cards first before changing numeric scoring.
    """
    profile = get_philosophy_profile(key)
    bias = _build_bias_profile(profile)
    return {
        "philosophy_key": profile.key,
        "protect_bias": list(profile.protect_bias),
        "review_bias": list(profile.review_bias),
        "cut_pressure_notes": list(profile.cut_pressure_notes),
        "philosophy_bias_foundation_active": bias["philosophy_bias_foundation_active"],
        "bias_scoring_active": bias["bias_scoring_active"],
        "bias_strength": bias["bias_strength"],
        "cut_bias_scoring_active": bias.get("cut_bias_scoring_active", False),
        "replacement_bias_scoring_active": bias.get("replacement_bias_scoring_active", False),
        "cut_bias_protect_roles": list(bias["cut_bias_protect_roles"]),
        "cut_bias_review_roles": list(bias["cut_bias_review_roles"]),
    }


def get_replacement_bias(key: Optional[str]) -> List[str]:
    """Return preferred replacement categories for the selected philosophy."""
    return list(get_philosophy_profile(key).replacement_bias)


def get_replacement_bias_roles(key: Optional[str]) -> List[str]:
    """Return v0.6.6.1 replacement-bias role buckets for future candidate logic."""
    profile = get_philosophy_profile(key)
    return list(_build_bias_profile(profile)["replacement_bias_roles"])


if __name__ == "__main__":
    # Smoke test:
    # From project root, run:
    # python -m analysis.deck_building_philosophies
    context = build_philosophy_context("big_moment", "masculine")
    print(render_philosophy_guide_section(context))
