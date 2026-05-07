"""Runtime configuration for MTG Commander Deck Helper.

Round 2 cleanup goal:
- Move constants and user-choice helpers out of the legacy single-file script.
- Preserve v0.6.2.6 behavior as closely as possible.
- Do not add new deck-analysis behavior here.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

SCRYFALL_FILE = Path("data/scryfall_cards.json")
OUTPUT_FOLDER = Path("outputs")
COLLECTION_FOLDER = Path("collection")
DEFAULT_COLLECTION_FILE = COLLECTION_FOLDER / "Cards in Phyrexian Bundle Box at Desk.txt"
MAX_OUTPUT_STEM_LENGTH = 72
MAX_OUTPUT_FILENAME_LENGTH = 96

# v0.5.7 cut pressure settings.
# Normal mode gives a conservative tuning list. Strict mode challenges more cards.
CUT_STRICTNESS = "normal"
NORMAL_OPTIONAL_CUT_TARGET = 5
STRICT_OPTIONAL_CUT_TARGET = 10
DEFAULT_OPTIONAL_CUT_TARGET = 8

# v0.5.7 possible cut review settings.
POSSIBLE_CUT_REVIEW_TARGET = 10
RECOMMENDED_CUT_TARGET = 5
PLAYTEST_FIRST_TARGET = 8
PROTECTED_REVIEW_TARGET = 12

REPLACEMENT_CATEGORIES = [
    "More ramp",
    "More card draw",
    "More targeted removal",
    "More board wipes",
    "More sacrifice outlets",
    "More recursion",
    "More finishers",
    "More protection",
    "More lands",
    "Lower mana curve",
    "More commander synergy",
    "More token production",
    "More graveyard setup",
    "More primary-plan support",
    "More secondary strategy support",
    "Better fixing",
    "More lifegain payoffs",
    "More lifegain enablers",
    "More artifact support",
    "More enchantment support",
    "More instant/sorcery density",
    "More creature density",
    "More toughness-matters payoffs",
    "More defender support",
    "More tribal density",
    "More evasion",
    "More combat finishers",
    "More mana sinks",
    "More utility lands",
    "More bracket-appropriate interaction",
    "Fewer bracket-escalating cards",
    "More role compression",
    "More primary-plan enablers",
    "More primary-plan payoffs",
    "More engine density",
    "More bridge cards",
    "More conversion points",
    "More commander-specific enablers",
    "More on-type creatures",
    "More typal payoff",
    "More activated ability support",
    "More pod-chain support",
    "More equipment/aura support",
    "More adventure/modal support",
    "More bracket-appropriate alternatives",
    "More table-friendly interaction",
    "Addition: reach 100 cards before cutting",
    "Build / complete deck to 100",
]

OUTPUT_MODE_LABELS = {
    "1": "normal",
    "2": "debug",
    "3": "both",
    "normal": "normal",
    "debug": "debug",
    "both": "both",
}

CUT_DEPTH_LABELS = {
    "1": "light",
    "2": "normal",
    "3": "strict",
    "4": "brutal",
    "5": "rebuild",
    "6": "custom",
    "light": "light",
    "normal": "normal",
    "strict": "strict",
    "brutal": "brutal",
    "deep": "brutal",
    "custom": "custom",
}

REVIEW_DIRECTION_LABELS = {
    "1": "build_up",
    "2": "cut_down",
    "3": "batch_auto",
    "auto": "batch_auto",
    "batch": "batch_auto",
    "batch auto": "batch_auto",
    "auto batch": "batch_auto",
    "batch_auto": "batch_auto",
    "build": "build_up",
    "build up": "build_up",
    "build_up": "build_up",
    "complete": "build_up",
    "add": "build_up",
    "additions": "build_up",
    "cut": "cut_down",
    "cut down": "cut_down",
    "cut_down": "cut_down",
    "trim": "cut_down",
    "review": "cut_down",
}

BUILD_UP_MODE_LABELS = {
    "1": "build_from_scratch",
    "2": "point_direction_30_plus",
    "3": "help_get_there_11_to_30",
    "4": "finalize_10_or_less",
    "scratch": "build_from_scratch",
    "build from scratch": "build_from_scratch",
    "from scratch": "build_from_scratch",
    "commander only": "build_from_scratch",
    "point": "point_direction_30_plus",
    "point me in the right direction": "point_direction_30_plus",
    "30+": "point_direction_30_plus",
    "30 plus": "point_direction_30_plus",
    "help": "help_get_there_11_to_30",
    "help me get there": "help_get_there_11_to_30",
    "11-30": "help_get_there_11_to_30",
    "30-11": "help_get_there_11_to_30",
    "finalize": "finalize_10_or_less",
    "10 or less": "finalize_10_or_less",
    "finish": "finalize_10_or_less",
}

PROMPT_INTERACTION_MODE_LABELS = {
    "1": "interactive",
    "2": "worksheet",
    "interactive": "interactive",
    "guided": "interactive",
    "guided chat": "interactive",
    "paid": "interactive",
    "worksheet": "worksheet",
    "one shot": "worksheet",
    "one-shot": "worksheet",
    "limited": "worksheet",
    "free": "worksheet",
    "copy paste": "worksheet",
    "copy-paste": "worksheet",
}

PROMPT_INTERACTION_MODE_DISPLAY = {
    "interactive": "Interactive AI chat — asks one section at a time",
    "worksheet": "One-shot worksheet — asks all questions at once for limited/free AI use",
}

PHILOSOPHY_MODE_LABELS = {
    "1": "balanced_unknown",
    "2": "timmy_tammy",
    "3": "johnny_jenny",
    "4": "spike",
    "balanced": "balanced_unknown",
    "unknown": "balanced_unknown",
    "balanced_unknown": "balanced_unknown",
    "timmy": "timmy_tammy",
    "tammy": "timmy_tammy",
    "timmy_tammy": "timmy_tammy",
    "johnny": "johnny_jenny",
    "jenny": "johnny_jenny",
    "johnny_jenny": "johnny_jenny",
    "spike": "spike",
}

PHILOSOPHY_SUBTYPE_LABELS = {
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

GUIDE_PREFERENCE_LABELS = {
    "1": "masculine",
    "2": "feminine",
    "3": "either",
    "4": "none",
    "masculine": "masculine",
    "male": "masculine",
    "feminine": "feminine",
    "female": "feminine",
    "either": "either",
    "random": "random",
    "none": "none",
    "no": "none",
}

COLLECTION_MODE_LABELS = {
    "0": "none",
    "1": "none",
    "2": "prefer",
    "3": "only",
    "4": "shakeup",
    "none": "none",
    "no": "none",
    "off": "none",
    "false": "none",
    "prefer": "prefer",
    "preferred": "prefer",
    "collection first": "prefer",
    "prefer collection first": "prefer",
    "only": "only",
    "collection only": "only",
    "shakeup": "shakeup",
    "shake up": "shakeup",
    "best available": "shakeup",
}

COLLECTION_MODE_DISPLAY = {
    "none": "No collection/card-pool file loaded",
    "prefer": "Prefer collection first — owned cards may be suggested when they are a real fit",
    "only": "Collection only — do not suggest outside cards",
    "shakeup": "Collection shakeup — show best available owned experiment candidates, clearly labeled",
}


@dataclass(frozen=True)
class RuntimeConfig:
    """User/runtime choices gathered before deck processing begins."""

    output_mode: str
    review_direction: str
    build_up_config: dict
    cut_depth_config: dict
    prompt_interaction_mode: str
    philosophy_key: str = "balanced_unknown"
    guide_preference: str = "either"
    collection_mode: str = "none"
    collection_file: str = ""



def yes_no_to_bool(value: object, default: bool = False) -> bool:
    text = str(value or "").strip().lower()
    if not text:
        return default
    return text in {"y", "yes", "true", "1"}



def get_output_mode_from_user() -> str:
    env_mode = os.environ.get("MTG_OUTPUT_MODE", "").strip().lower()
    if env_mode in OUTPUT_MODE_LABELS:
        return OUTPUT_MODE_LABELS[env_mode]

    print()
    print("Choose output mode:")
    print("1. Normal User Mode")
    print("2. Debug / Stress-Test Mode")
    print("3. Both")
    choice = input("Output mode [1=Normal]: ").strip().lower()
    return OUTPUT_MODE_LABELS.get(choice, "normal")



def get_review_direction_from_user() -> str:
    env_mode = os.environ.get("MTG_REVIEW_DIRECTION", "").strip().lower()
    if env_mode in REVIEW_DIRECTION_LABELS:
        return REVIEW_DIRECTION_LABELS[env_mode]

    print()
    print("Choose review direction:")
    print("1. Build up / complete a deck to 100 cards")
    print("2. Cut down / tune an existing deck or card pool")
    print("3. Auto batch mode — detect from deck size and use default choices")
    print("   Note: under 100 cards = build-up; 100+ cards = cut-down; defaults are used automatically.")
    choice = input("Review direction [2=Cut down]: ").strip().lower()
    return REVIEW_DIRECTION_LABELS.get(choice, "cut_down")



def get_build_up_mode_from_user() -> dict:
    env_mode = os.environ.get("MTG_BUILD_UP_MODE", "").strip().lower()
    mode = BUILD_UP_MODE_LABELS.get(env_mode)
    if not mode:
        print()
        print("Choose build-up mode:")
        print("1. Build from Scratch — Commander(s) only")
        print("2. Point me in the right direction — 30+ cards needed")
        print("3. Help me get there — 11 to 30 cards needed")
        print("4. Finalize — 10 or fewer cards needed")
        choice = input("Build-up mode [4=Finalize]: ").strip().lower()
        mode = BUILD_UP_MODE_LABELS.get(choice, "finalize_10_or_less")

    labels = {
        "build_from_scratch": "Build from Scratch — Commander(s) only",
        "point_direction_30_plus": "Point me in the right direction — 30+ cards needed",
        "help_get_there_11_to_30": "Help me get there — 11 to 30 cards needed",
        "finalize_10_or_less": "Finalize — 10 or fewer cards needed",
    }
    return {
        "mode": mode,
        "label": labels.get(mode, mode),
        "alpha": False,
    }



def get_prompt_interaction_mode_from_user() -> str:
    env_mode = os.environ.get("MTG_PROMPT_INTERACTION_MODE", "").strip().lower()
    if env_mode in PROMPT_INTERACTION_MODE_LABELS:
        return PROMPT_INTERACTION_MODE_LABELS[env_mode]

    print()
    print("Choose prompt interaction mode:")
    print("1. Interactive AI chat — best quality; asks one section at a time")
    print("2. One-shot worksheet — best for limited-message/free AI use; asks all questions at once")
    choice = input("Prompt interaction mode [1=Interactive]: ").strip().lower()
    return PROMPT_INTERACTION_MODE_LABELS.get(choice, "interactive")



def get_default_cut_depth_config_for_build_up() -> dict:
    return {
        "mode": "build_up",
        "optional_cut_target": 0,
        "include_low_confidence": False,
        "include_bracket_pressure": False,
        "include_removal": False,
        "include_manual_review": True,
        "include_playable_replaceable": False,
    }



def get_cut_strictness_from_user() -> dict:
    env_mode = os.environ.get("MTG_CUT_DEPTH_MODE", "").strip().lower()
    mode = CUT_DEPTH_LABELS.get(env_mode)
    if not mode:
        print()
        print("Choose cut depth mode:")
        print("1. Light — only obvious problems and severe off-plan cards")
        print("2. Normal — practical tuning, about 5 optional candidates")
        print("3. Strict — serious optimization, about 10 optional candidates")
        print("4. Brutal / Deep Review — large pools or very overfilled decks, about 15 candidates")
        print("5. Rebuild — treat the list as a rough card pool and rebuild toward the stated plan")
        print("6. Custom")
        choice = input("Cut depth [2=Normal]: ").strip().lower()
        mode = CUT_DEPTH_LABELS.get(choice, "normal")

    config = {
        "mode": mode,
        "optional_cut_target": 5,
        "include_low_confidence": False,
        "include_bracket_pressure": False,
        "include_removal": False,
        "include_manual_review": True,
        "include_playable_replaceable": True,
    }
    if mode == "light":
        config.update({
            "optional_cut_target": 3,
            "include_low_confidence": False,
            "include_bracket_pressure": False,
            "include_removal": False,
            "include_manual_review": True,
            "include_playable_replaceable": False,
        })
    elif mode == "strict":
        config.update({
            "optional_cut_target": 10,
            "include_low_confidence": False,
            "include_bracket_pressure": True,
            "include_removal": True,
            "include_manual_review": True,
            "include_playable_replaceable": True,
        })
    elif mode == "brutal":
        config.update({
            "optional_cut_target": 15,
            "include_low_confidence": True,
            "include_bracket_pressure": True,
            "include_removal": True,
            "include_manual_review": True,
            "include_playable_replaceable": True,
        })
    elif mode == "rebuild":
        config.update({
            "optional_cut_target": 25,
            "include_low_confidence": True,
            "include_bracket_pressure": True,
            "include_removal": True,
            "include_manual_review": True,
            "include_playable_replaceable": True,
        })
    elif mode == "custom":
        env_target = os.environ.get("MTG_OPTIONAL_CUT_TARGET")
        if env_target and env_target.isdigit():
            target = int(env_target)
        else:
            raw = input("How many optional cut candidates should be shown? [5]: ").strip()
            target = int(raw) if raw.isdigit() else 5
        config.update({
            "optional_cut_target": max(0, target),
            "include_low_confidence": yes_no_to_bool(
                os.environ.get("MTG_INCLUDE_LOW_CONFIDENCE") or input("Include low-confidence cuts? [n]: "),
                False,
            ),
            "include_bracket_pressure": yes_no_to_bool(
                os.environ.get("MTG_INCLUDE_BRACKET_PRESSURE") or input("Include bracket-pressure cuts? [n]: "),
                False,
            ),
            "include_removal": yes_no_to_bool(
                os.environ.get("MTG_INCLUDE_REMOVAL_CUTS") or input("Include removal as possible cuts? [n]: "),
                False,
            ),
            "include_manual_review": yes_no_to_bool(
                os.environ.get("MTG_INCLUDE_MANUAL_REVIEW") or input("Include manual-review candidates? [y]: "),
                True,
            ),
            "include_playable_replaceable": yes_no_to_bool(
                os.environ.get("MTG_INCLUDE_PLAYABLE_REPLACEABLE") or input("Include playable-but-replaceable cards? [y]: "),
                True,
            ),
        })
    return config



def get_default_cut_depth_config_normal() -> dict:
    return {
        "mode": "normal",
        "optional_cut_target": 5,
        "include_low_confidence": False,
        "include_bracket_pressure": False,
        "include_removal": False,
        "include_manual_review": True,
        "include_playable_replaceable": True,
    }


def auto_build_up_config_for_deck_size(deck_card_count: int) -> dict:
    cards_needed = max(0, 100 - int(deck_card_count or 0))
    if deck_card_count <= 1 or cards_needed >= 99:
        mode = "build_from_scratch"
    elif cards_needed >= 30:
        mode = "point_direction_30_plus"
    elif cards_needed >= 11:
        mode = "help_get_there_11_to_30"
    else:
        mode = "finalize_10_or_less"
    labels = {
        "build_from_scratch": "Build from Scratch — Commander(s) only",
        "point_direction_30_plus": "Point me in the right direction — 30+ cards needed",
        "help_get_there_11_to_30": "Help me get there — 11 to 30 cards needed",
        "finalize_10_or_less": "Finalize — 10 or fewer cards needed",
    }
    return {"mode": mode, "label": labels[mode], "alpha": False, "auto_selected": True}


def resolve_runtime_config_for_deck_size(runtime_config: RuntimeConfig, deck_card_count: int) -> RuntimeConfig:
    if runtime_config.review_direction != "batch_auto":
        return runtime_config
    if deck_card_count < 100:
        return RuntimeConfig(
            output_mode=runtime_config.output_mode,
            review_direction="build_up",
            build_up_config=auto_build_up_config_for_deck_size(deck_card_count),
            cut_depth_config=get_default_cut_depth_config_for_build_up(),
            prompt_interaction_mode=runtime_config.prompt_interaction_mode,
            philosophy_key=runtime_config.philosophy_key,
            guide_preference=runtime_config.guide_preference,
            collection_mode=runtime_config.collection_mode,
            collection_file=runtime_config.collection_file,
        )
    return RuntimeConfig(
        output_mode=runtime_config.output_mode,
        review_direction="cut_down",
        build_up_config={"mode": "not_applicable", "label": "Not applicable", "alpha": False},
        cut_depth_config=get_default_cut_depth_config_normal(),
        prompt_interaction_mode=runtime_config.prompt_interaction_mode,
        philosophy_key=runtime_config.philosophy_key,
        guide_preference=runtime_config.guide_preference,
        collection_mode=runtime_config.collection_mode,
        collection_file=runtime_config.collection_file,
    )




def get_philosophy_selection_from_user(review_direction: str) -> tuple[str, str]:
    """Return selected philosophy key and guide presentation preference.

    Auto batch intentionally defaults to Balanced / Unknown unless MTG_PHILOSOPHY
    is supplied. This keeps batch runs non-interactive.
    """
    env_key = os.environ.get("MTG_PHILOSOPHY", "").strip().lower()
    env_pref = os.environ.get("MTG_GUIDE_PREFERENCE", "").strip().lower()

    if env_key:
        # Specific subtypes and aliases are normalized later by the philosophy module.
        philosophy_key = PHILOSOPHY_MODE_LABELS.get(env_key) or PHILOSOPHY_SUBTYPE_LABELS.get(env_key) or env_key
        guide_preference = GUIDE_PREFERENCE_LABELS.get(env_pref, env_pref or "either")
        return philosophy_key, guide_preference

    if review_direction == "batch_auto":
        return "balanced_unknown", GUIDE_PREFERENCE_LABELS.get(env_pref, env_pref or "either")

    print()
    print("Choose deck-building philosophy lens:")
    print("1. Balanced / Unknown — default exploratory lens")
    print("2. Timmy / Tammy — experience, spectacle, theme, and personal joy")
    print("3. Johnny / Jenny — synergy, engines, invention, and clever concepts")
    print("4. Spike — performance, consistency, efficiency, and table fit")
    print("5. Specific philosophy subtype")
    choice = input("Philosophy lens [1=Balanced / Unknown]: ").strip().lower()

    if choice == "5":
        print()
        print("Choose specific philosophy subtype:")
        print("Timmy / Tammy — Experience, spectacle, theme, and personal joy")
        print("1. Big Moment")
        print("2. Big Creature / Stompy")
        print("3. Theme / Vibe")
        print("4. Pet Card")
        print("5. Let Me Do My Thing")
        print("6. Battlecruiser")
        print()
        print("Johnny / Jenny — Synergy, invention, engines, and clever concepts")
        print("7. Engine Builder")
        print("8. Commander Exploiter")
        print("9. Weird Card Rescuer")
        print("10. Theme Mechanic Inventor")
        print("11. Self-Imposed Constraint Builder")
        print("12. Combo Builder")
        print()
        print("Spike — Performance, consistency, efficiency, and table fit")
        print("13. Consistency Maximizer")
        print("14. Efficiency Optimizer")
        print("15. Curve and Mana Discipline")
        print("16. Competitive Closer")
        print("17. Power-Level Calibrator")
        print("18. Interaction Controller")
        subtype = input("Subtype [1=Big Moment]: ").strip().lower()
        philosophy_key = PHILOSOPHY_SUBTYPE_LABELS.get(subtype, "big_moment")
    else:
        philosophy_key = PHILOSOPHY_MODE_LABELS.get(choice, "balanced_unknown")

    if env_pref:
        guide_preference = GUIDE_PREFERENCE_LABELS.get(env_pref, env_pref)
    else:
        print()
        print("Choose guide presentation:")
        print("1. Masculine guide")
        print("2. Feminine guide")
        print("3. Either / random")
        print("4. No named guide, just philosophy labels")
        pref_choice = input("Guide presentation [3=Either/random]: ").strip().lower()
        guide_preference = GUIDE_PREFERENCE_LABELS.get(pref_choice, "either")

    return philosophy_key, guide_preference



def get_collection_settings_from_user(review_direction: str) -> tuple[str, str]:
    """Return collection mode and file path.

    v0.6.4.1 only loads and summarizes the collection. Later patches consume
    this setting for collection candidates and collection-only behavior.
    Batch auto remains non-interactive unless MTG_COLLECTION_MODE is set.
    """
    env_mode = os.environ.get("MTG_COLLECTION_MODE", "").strip().lower()
    env_file = os.environ.get("MTG_COLLECTION_FILE", "").strip()

    if env_mode:
        mode = COLLECTION_MODE_LABELS.get(env_mode, "none")
        file_path = env_file or str(DEFAULT_COLLECTION_FILE)
        return mode, file_path

    if review_direction == "batch_auto":
        return "none", env_file or str(DEFAULT_COLLECTION_FILE)

    print()
    print("Use collection/card pool for future recommendations?")
    print("1. No — ignore collection for this run")
    print("2. Prefer collection first — owned cards only if they are a real fit")
    print("3. Collection only — do not suggest outside cards later")
    print("4. Collection shakeup — show best available owned experiments later, clearly labeled")
    choice = input("Collection mode [1=No]: ").strip().lower()
    mode = COLLECTION_MODE_LABELS.get(choice, "none")

    file_path = env_file or str(DEFAULT_COLLECTION_FILE)
    if mode != "none":
        raw_path = input(f"Collection file [{file_path}]: ").strip()
        if raw_path:
            file_path = raw_path

    return mode, file_path


def get_runtime_config() -> RuntimeConfig:
    output_mode = get_output_mode_from_user()
    review_direction = get_review_direction_from_user()

    if review_direction == "batch_auto":
        print()
        print("Auto batch mode selected. Using default choices and routing each deck by deck size.")
        print("- Output mode: " + output_mode)
        print("- Prompt interaction mode: interactive")
        print("- Cut depth for 100+ card decks: normal")
        print("- Build-up level for under-100 decks: auto-selected by cards missing")
        build_up_config = {"mode": "auto_by_deck_size", "label": "Auto-selected by deck size", "alpha": False}
        cut_depth_config = get_default_cut_depth_config_normal()
        prompt_interaction_mode = "interactive"
    elif review_direction == "build_up":
        build_up_config = get_build_up_mode_from_user()
        cut_depth_config = get_default_cut_depth_config_for_build_up()
        prompt_interaction_mode = get_prompt_interaction_mode_from_user()
    else:
        build_up_config = {"mode": "not_applicable", "label": "Not applicable", "alpha": False}
        cut_depth_config = get_cut_strictness_from_user()
        prompt_interaction_mode = get_prompt_interaction_mode_from_user()

    philosophy_key, guide_preference = get_philosophy_selection_from_user(review_direction)
    collection_mode, collection_file = get_collection_settings_from_user(review_direction)

    return RuntimeConfig(
        output_mode=output_mode,
        review_direction=review_direction,
        build_up_config=build_up_config,
        cut_depth_config=cut_depth_config,
        prompt_interaction_mode=prompt_interaction_mode,
        philosophy_key=philosophy_key,
        guide_preference=guide_preference,
        collection_mode=collection_mode,
        collection_file=collection_file,
    )



def print_runtime_config_summary(runtime_config: RuntimeConfig) -> None:
    print(f"Output mode: {runtime_config.output_mode}")
    print(f"Review direction: {runtime_config.review_direction}")
    print(
        "Prompt interaction mode: "
        f"{PROMPT_INTERACTION_MODE_DISPLAY.get(runtime_config.prompt_interaction_mode, runtime_config.prompt_interaction_mode)}"
    )
    print(f"Philosophy lens: {runtime_config.philosophy_key}")
    print(f"Guide preference: {runtime_config.guide_preference}")
    print(f"Collection mode: {COLLECTION_MODE_DISPLAY.get(runtime_config.collection_mode, runtime_config.collection_mode)}")
    if runtime_config.collection_mode != "none":
        print(f"Collection file: {runtime_config.collection_file}")
    if runtime_config.review_direction == "build_up":
        print(f"Build-up mode: {runtime_config.build_up_config['label']}")
    elif runtime_config.review_direction == "batch_auto":
        print("Batch auto: deck size selects build-up vs cut-down; defaults used")
    else:
        print(
            f"Cut depth mode: {runtime_config.cut_depth_config['mode']} "
            f"(target {runtime_config.cut_depth_config['optional_cut_target']})"
        )
