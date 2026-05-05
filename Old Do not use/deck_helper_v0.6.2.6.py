
print("RUNNING MTG DECK HELPER v0.6.2.6 - WORKSHEET GUARDRAIL HOTFIX")

from pathlib import Path
from collections import Counter, defaultdict
import json
import re
import os
import sys
import subprocess
import tkinter as tk
from tkinter import filedialog

SCRYFALL_FILE = Path("data/scryfall_cards.json")
OUTPUT_FOLDER = Path("outputs")
COLLECTION_FOLDER = Path("collections")
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


def select_deck_files():
    root = tk.Tk()
    root.withdraw()

    selected_files = filedialog.askopenfilenames(
        title="Select one or more Commander decklist files",
        initialdir="decklists",
        filetypes=[
            ("Text files", "*.txt"),
            ("All files", "*.*"),
        ],
    )

    root.destroy()

    if not selected_files:
        print("No deck files selected.")
        exit()

    return [Path(selected_file) for selected_file in selected_files]


# ==============================
# v0.5.7 Output Mode / Cut Depth Helpers
# ==============================
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
    "build": "build_up",
    "build up": "build_up",
    "build_up": "build_up",
    "complete": "build_up",
    "add": "build_up",
    "additions": "build_up",
    "2": "cut_down",
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


def sanitize_filename(name, max_length=120):
    safe = str(name or "Unknown_Deck").strip()
    for ch in '<>:"/\\|?*':
        safe = safe.replace(ch, "_")
    safe = re.sub(r"\s+", "_", safe)
    safe = re.sub(r"_+", "_", safe).strip("._ ")
    if not safe:
        safe = "Unknown_Deck"
    return safe[:max_length].rstrip("._ ") or "Unknown_Deck"


def get_output_mode_from_user():
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


def yes_no_to_bool(value, default=False):
    text = str(value or "").strip().lower()
    if not text:
        return default
    return text in {"y", "yes", "true", "1"}


def get_review_direction_from_user():
    env_mode = os.environ.get("MTG_REVIEW_DIRECTION", "").strip().lower()
    if env_mode in REVIEW_DIRECTION_LABELS:
        return REVIEW_DIRECTION_LABELS[env_mode]

    print()
    print("Choose review direction:")
    print("1. Build up / complete a deck to 100 cards")
    print("2. Cut down / tune an existing deck or card pool")
    choice = input("Review direction [2=Cut down]: ").strip().lower()
    return REVIEW_DIRECTION_LABELS.get(choice, "cut_down")


def get_build_up_mode_from_user():
    env_mode = os.environ.get("MTG_BUILD_UP_MODE", "").strip().lower()
    mode = BUILD_UP_MODE_LABELS.get(env_mode)
    if not mode:
        print()
        print("Choose build-up mode:")
        print("1. Build from Scratch — commander only; Alpha feature, may not be ready yet")
        print("2. Point me in the right direction — 30+ cards needed")
        print("3. Help me get there — 11 to 30 cards needed")
        print("4. Finalize — 10 or fewer cards needed")
        choice = input("Build-up mode [4=Finalize]: ").strip().lower()
        mode = BUILD_UP_MODE_LABELS.get(choice, "finalize_10_or_less")

    if mode == "build_from_scratch":
        print()
        print("Alpha warning: Build from Scratch is experimental. It can create a direction and role plan, but the final 99-card list still needs human review and color-identity checks.")

    labels = {
        "build_from_scratch": "Build from Scratch — commander only (Alpha)",
        "point_direction_30_plus": "Point me in the right direction — 30+ cards needed",
        "help_get_there_11_to_30": "Help me get there — 11 to 30 cards needed",
        "finalize_10_or_less": "Finalize — 10 or fewer cards needed",
    }
    return {
        "mode": mode,
        "label": labels.get(mode, mode),
        "alpha": mode == "build_from_scratch",
    }



def get_prompt_interaction_mode_from_user():
    env_mode = os.environ.get("MTG_PROMPT_INTERACTION_MODE", "").strip().lower()
    if env_mode in PROMPT_INTERACTION_MODE_LABELS:
        return PROMPT_INTERACTION_MODE_LABELS[env_mode]

    print()
    print("Choose prompt interaction mode:")
    print("1. Interactive AI chat — best quality; asks one section at a time")
    print("2. One-shot worksheet — best for limited-message/free AI use; asks all questions at once")
    choice = input("Prompt interaction mode [1=Interactive]: ").strip().lower()
    return PROMPT_INTERACTION_MODE_LABELS.get(choice, "interactive")


def get_default_cut_depth_config_for_build_up():
    return {
        "mode": "build_up",
        "optional_cut_target": 0,
        "include_low_confidence": False,
        "include_bracket_pressure": False,
        "include_removal": False,
        "include_manual_review": True,
        "include_playable_replaceable": False,
    }


def get_cut_strictness_from_user():
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
            "include_low_confidence": yes_no_to_bool(os.environ.get("MTG_INCLUDE_LOW_CONFIDENCE") or input("Include low-confidence cuts? [n]: "), False),
            "include_bracket_pressure": yes_no_to_bool(os.environ.get("MTG_INCLUDE_BRACKET_PRESSURE") or input("Include bracket-pressure cuts? [n]: "), False),
            "include_removal": yes_no_to_bool(os.environ.get("MTG_INCLUDE_REMOVAL_CUTS") or input("Include removal as possible cuts? [n]: "), False),
            "include_manual_review": yes_no_to_bool(os.environ.get("MTG_INCLUDE_MANUAL_REVIEW") or input("Include manual-review candidates? [y]: "), True),
            "include_playable_replaceable": yes_no_to_bool(os.environ.get("MTG_INCLUDE_PLAYABLE_REPLACEABLE") or input("Include playable-but-replaceable cards? [y]: "), True),
        })
    return config


def create_deck_output_folder(deck_name, output_root, subfolder=None):
    base = output_root / shorten_output_stem(deck_name)
    if subfolder:
        base = base / subfolder
    folder = base
    counter = 1
    while folder.exists() and any(folder.iterdir()):
        counter += 1
        folder = base.parent / f"{base.name}_{counter:02d}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def write_text_file(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(content).rstrip() + "\n", encoding="utf-8")
    return path


def merge_debug_reports(deck_folder, deck_name, debug_file_paths):
    merged_path = get_unique_output_path(Path(deck_folder), f"{shorten_output_stem(deck_name)}_full_debug_report")
    section_titles = [
        "01 - LEGALITY REPORT",
        "02 - STRATEGY REPORT",
        "03 - BRACKET REPORT",
        "04 - CUT PRESSURE REPORT",
        "05 - REPLACEMENT PROMPT",
        "06 - DIAGNOSTICS",
    ]
    parts = []
    for title, file_path in zip(section_titles, debug_file_paths):
        file_path = Path(file_path)
        parts.append("=" * 50)
        parts.append(title)
        parts.append("=" * 50)
        parts.append(file_path.read_text(encoding="utf-8") if file_path.exists() and file_path != merged_path else "[Missing debug section]")
        parts.append("")
    write_text_file(merged_path, "\n".join(parts))
    return merged_path


def resolve_deck_file():
    deck_file_from_environment = os.environ.get("MTG_DECK_FILE")

    if deck_file_from_environment:
        return Path(deck_file_from_environment)

    selected_deck_files = select_deck_files()

    if len(selected_deck_files) == 1:
        return selected_deck_files[0]

    print()
    print(f"Batch mode: {len(selected_deck_files)} deck files selected.")
    output_mode = get_output_mode_from_user()
    review_direction = get_review_direction_from_user()
    if review_direction == "build_up":
        build_up_config = get_build_up_mode_from_user()
        cut_config = get_default_cut_depth_config_for_build_up()
    else:
        build_up_config = {"mode": "not_applicable", "label": "Not applicable", "alpha": False}
        cut_config = get_cut_strictness_from_user()
    prompt_interaction_mode = get_prompt_interaction_mode_from_user()
    print(f"Output mode: {output_mode}")
    print(f"Review direction: {review_direction}")
    print(f"Prompt interaction mode: {PROMPT_INTERACTION_MODE_DISPLAY.get(prompt_interaction_mode, prompt_interaction_mode)}")
    if review_direction == "build_up":
        print(f"Build-up mode: {build_up_config['label']}")
    else:
        print(f"Cut depth mode: {cut_config['mode']} (target {cut_config['optional_cut_target']})")
    print()

    batch_summary = []
    for selected_deck_file in selected_deck_files:
        print(f"Running deck helper for: {selected_deck_file}")

        child_environment = os.environ.copy()
        child_environment["MTG_DECK_FILE"] = str(selected_deck_file)
        child_environment["MTG_OUTPUT_MODE"] = output_mode
        child_environment["MTG_REVIEW_DIRECTION"] = review_direction
        child_environment["MTG_BUILD_UP_MODE"] = build_up_config.get("mode", "not_applicable")
        child_environment["MTG_CUT_DEPTH_MODE"] = cut_config["mode"]
        child_environment["MTG_OPTIONAL_CUT_TARGET"] = str(cut_config["optional_cut_target"])
        child_environment["MTG_INCLUDE_LOW_CONFIDENCE"] = "1" if cut_config.get("include_low_confidence") else "0"
        child_environment["MTG_INCLUDE_BRACKET_PRESSURE"] = "1" if cut_config.get("include_bracket_pressure") else "0"
        child_environment["MTG_INCLUDE_REMOVAL_CUTS"] = "1" if cut_config.get("include_removal") else "0"
        child_environment["MTG_INCLUDE_MANUAL_REVIEW"] = "1" if cut_config.get("include_manual_review") else "0"
        child_environment["MTG_INCLUDE_PLAYABLE_REPLACEABLE"] = "1" if cut_config.get("include_playable_replaceable") else "0"
        child_environment["MTG_PROMPT_INTERACTION_MODE"] = prompt_interaction_mode

        result = subprocess.run(
            [sys.executable, __file__],
            env=child_environment,
            check=False,
        )
        batch_summary.append((selected_deck_file, result.returncode))
        print()

    print("Batch run complete.")
    print("Final Summary:")
    print(f"- Decks processed: {len(batch_summary)}")
    print(f"- Output mode used: {output_mode}")
    print(f"- Review direction used: {review_direction}")
    if review_direction == "build_up":
        print(f"- Build-up mode used: {build_up_config['label']}")
    else:
        print(f"- Cut depth mode used: {cut_config['mode']}")
    print(f"- Prompt interaction mode used: {PROMPT_INTERACTION_MODE_DISPLAY.get(prompt_interaction_mode, prompt_interaction_mode)}")
    print(f"- Successes: {sum(1 for _, code in batch_summary if code == 0)}")
    print(f"- Failures: {sum(1 for _, code in batch_summary if code != 0)}")
    for path, code in batch_summary:
        status = "succeeded" if code == 0 else f"failed with code {code}"
        print(f"  - {path.name}: {status}")
    exit()


DECK_FILE = resolve_deck_file()
ATTRIBUTE_RULES_FILE = Path("rules") / "card_attribute_rules.md"
STRATEGY_RULES_FILE = Path("rules") / "strategy_archetype_rules.md"
CUT_RULES_FILE = Path("rules") / "cut_replacement_rules.md"
BRACKET_RULES_FILE = Path("rules") / "bracket_rules.md"
INTENDED_BRACKET = os.environ.get("MTG_INTENDED_BRACKET", "Unknown").strip() or "Unknown"
OUTPUT_MODE = os.environ.get("MTG_OUTPUT_MODE", "").strip().lower()
if OUTPUT_MODE not in {"normal", "debug", "both"}:
    OUTPUT_MODE = get_output_mode_from_user()
REVIEW_DIRECTION = os.environ.get("MTG_REVIEW_DIRECTION", "").strip().lower()
if REVIEW_DIRECTION not in {"build_up", "cut_down"}:
    REVIEW_DIRECTION = get_review_direction_from_user()
if REVIEW_DIRECTION == "build_up":
    BUILD_UP_CONFIG = get_build_up_mode_from_user()
    CUT_DEPTH_CONFIG = get_default_cut_depth_config_for_build_up()
else:
    BUILD_UP_CONFIG = {"mode": "not_applicable", "label": "Not applicable", "alpha": False}
    CUT_DEPTH_CONFIG = get_cut_strictness_from_user()
PROMPT_INTERACTION_MODE = os.environ.get("MTG_PROMPT_INTERACTION_MODE", "").strip().lower()
if PROMPT_INTERACTION_MODE not in {"interactive", "worksheet"}:
    PROMPT_INTERACTION_MODE = get_prompt_interaction_mode_from_user()
CUT_STRICTNESS = CUT_DEPTH_CONFIG.get("mode", "normal")
OPTIONAL_CUT_TARGET = int(CUT_DEPTH_CONFIG.get("optional_cut_target", 5))
POSSIBLE_CUT_REVIEW_TARGET = max(POSSIBLE_CUT_REVIEW_TARGET, OPTIONAL_CUT_TARGET)

SECTION_HEADERS = {
    "commander": "Commander", "commanders": "Commander", "background": "Commander", "backgrounds": "Commander",
    "companion": "Companion", "companions": "Companion",
    "deck": "Deck", "mainboard": "Deck", "main deck": "Deck",
    "creature": "Creatures", "creatures": "Creatures",
    "artifact": "Artifacts", "artifacts": "Artifacts",
    "enchantment": "Enchantments", "enchantments": "Enchantments",
    "instant": "Instants", "instants": "Instants",
    "sorcery": "Sorceries", "sorceries": "Sorceries",
    "land": "Lands", "lands": "Lands",
    "planeswalker": "Planeswalkers", "planeswalkers": "Planeswalkers",
    "battle": "Battles", "battles": "Battles",
    "mana base": "Lands", "manabase": "Lands", "ramp": "Custom: Ramp", "removal": "Custom: Removal", "interaction": "Custom: Interaction",
    "card draw": "Custom: Card Draw", "card advantage": "Custom: Card Advantage", "recursion": "Custom: Recursion", "token generation": "Custom: Token Generation",
    "tokens": "Custom: Tokens", "token generation": "Custom: Token Generation", "win cons": "Custom: Win Conditions", "win conditions": "Custom: Win Conditions",
}
SECTION_ORDER = ["Commander","Companion","Creatures","Artifacts","Enchantments","Battles","Instants","Sorceries","Planeswalkers","Lands","Unknown / Needs Review"]

NON_MAINBOARD_SECTION_HEADERS = {
    "cut", "cuts", "cutboard", "removed", "remove", "maybe", "maybeboard", "sideboard",
    "side board", "considering", "consider", "wishlist", "wish list", "not owned",
    "outside the game", "lessons", "lesson", "attractions", "attraction", "stickers",
    "sticker", "planes", "planechase", "schemes", "scheme", "contraptions", "contraption",
}

REFERENCE_ONLY_SECTION_HEADERS = {
    "token cards", "generated tokens", "tokens & extras", "tokens and extras", "extras", "extra cards",
    "helper cards", "token helpers", "generated token cards", "emblems", "emblem",
}

NON_MAINBOARD_PREFIXES = (
    "custom: cut", "custom: cuts", "custom: maybe", "custom: maybeboard", "custom: sideboard",
    "custom: considering", "custom: token cards", "custom: generated tokens",
)
MAJOR_CARD_TYPES = ["Artifact","Battle","Creature","Enchantment","Instant","Land","Planeswalker","Sorcery"]
MANUAL_SECTION_EXPECTED_TYPES = {
    "Artifacts":{"Artifact"}, "Battles":{"Battle"}, "Creatures":{"Creature"}, "Enchantments":{"Enchantment"},
    "Instants":{"Instant"}, "Lands":{"Land"}, "Planeswalkers":{"Planeswalker"}, "Sorceries":{"Sorcery"},
}
ROLE_TAGS = [
    "ramp","card_draw","card_advantage","targeted_removal","board_wipe","recursion","graveyard_enabler",
    "discard_outlet","sacrifice_outlet","free_sacrifice_outlet","death_trigger_payoff","token_maker","anthem",
    "protection","tutor","counterspell","cost_reducer","mana_doubler","tribal_payoff","tribal_dependency",
    "synergy_piece","extra_combat","combat_synergy","attack_trigger_payoff","damage_payoff","sacrifice_payoff","artifact_payoff",
    "counter_synergy","equipment_synergy","aura_synergy","go_tall_support","spell_payoff",
    "free_interaction","stack_interaction","commander_online_protection","spell_redirection",
    "bounce_engine","self_bounce","cast_trigger","creature_cast_trigger",
    "activated_ability_synergy","mana_sink","power_matters","topdeck_manipulation",
    "adventure_synergy","modal_spell_synergy","creature_spell_hybrid",
    "clue_synergy","food_synergy","treasure_synergy","artifact_token_synergy","investigate_synergy",
    "eldrazi_synergy","colorless_matters","big_mana_payoff","cast_copy_synergy","high_mv_payoff","devoid_awareness",
    "historic_synergy","legendary_synergy","doctor_synergy","time_travel_synergy","suspend_synergy","cascade_synergy",
    "token_resource_engine","tap_token_value","rabbit_typal","go_wide_token_engine",
    "card_selection","self_mill","copy_clone_value",
    "wheel_effect","pillowfort","stax_piece","cost_cheat","free_casting",
    "self_bounce_creature","redirection_protection","mass_removal","draw_fixed_number",
    "alternate_cost_interaction","mana_source","playable_replaceable_utility",
    "permanent_type_value","permanent_density","creature_cost_reduction","creature_combo_value","shell_support",
    "dragon_typal","dragon_copy_value","token_copy_value",
    "blink_flicker","etb_value","ltb_value","exile_return",
    "amass_synergy","army_typal","noncreature_spell_payoff","suspend_big_spell",
    "defender_payoff","toughness_payoff","toughness_combat","wall_typal","high_toughness",
    "forced_draw","draw_punisher","opponent_draw_payoff","group_slug",
    "lifegain_payoff","lifedrain_payoff","life_total_manipulation",
    "tribal_anthem","tribal_protection","combat_reset","attack_safety","mass_blink",
    "landfall","landfall_payoff","extra_land_play","lands_matter","land_token",
    "commander_created_package","rock_token_synergy","artifact_sacrifice",
    "fast_mana","ritual","efficient_tutor","combo_tutor","tutor_chain",
    "turbo_combo","dragonstorm_combo","silence_effect","free_counterspell","combo_protection",
    "high_bracket_pressure","game_changer","bracket_pressure",
    "elf_typal","dwarf_typal","five_color_value","legendary_cascade",
    "artifact_treasure_tutor_chain","artifact_token_economy","treasure_tutor_chain",
    "ramp_control","big_mana_value","mana_rock","mana_dork","mana_fixing",
    "utility_land","true_fast_mana","true_ritual","combo_pressure",
    "combo_piece_possible","commander_synergy_possible","win_condition","manual_review",
    "direct_commander_support","commander_enabler","commander_payoff","commander_protection","commander_resource_support",
    "primary_plan_support","secondary_plan_support","incidental_support","activated_ability_source",
    "activated_ability_payoff","activated_ability_cost_reduction","activated_ability_engine","mana_ability_only",
    "utility_activated_ability","creature_type_present","typal_density_piece","typal_payoff","typal_enabler",
    "typal_lord","typal_token_maker","incidental_creature_type","extra_turn","ritual_or_mana_burst",
    "power_boost","commander_damage_support","spell_recursion_possible","artifact_tutor","saga",
    "slow_alt_win_condition","high_power_value_piece","true_turbo_combo","pilot_intent_needed",
    "mutate", "mutate_payoff", "mutate_enabler", "cast_from_outside_hand", "nonhand_casting", "foretell", "plot",
]
NON_TRIBAL_REFERENCE_WORDS = {"time","times","turn","turns","phase","phases","combat","card","cards","spell","spells","token","tokens","counter","counters","damage","life","mana","artifact","creature","permanent","opponent","player","construct"}

KNOWN_CREATURE_TYPES = set("""
advisor aetherborn ally angel antelope ape archer archon army artificer assassin assembly-worker avatar badger barbarian bard basilisk bat bear beast berserker bird boar cat centaur cleric construct crab crocodile cyclops demon detective devil dinosaur djinn dog dragon drake drone druid dryad dwarf elder eldrazi elemental elephant elf elk faerie fish fox fractal frog fungus giant gnome goat goblin god golem gorgon gremlin griffin halfling horror horse human hydra illusion imp incarnation inkling insect knight kobold kor kraken leviathan lizard masticore merfolk minion minotaur mole monk monkey mouse mutant myr mystic naga nightmare ninja noble octopus ogre ooze orc otter ouphe ox pegasus pest phoenix phyrexian pirate plant rabbit raccoon ranger rat rebel rhino robot rogue salamander samurai saproling satyr scarecrow scout scorpion serpent servo shade shaman shapeshifter shark skeleton sliver snake soldier spawn specter sphinx spider spirit squirrel survivor thopter thrull tiefling treefolk troll turtle unicorn vampire vedalken warrior weird werewolf whale wizard wolf worm wraith wurm zombie doctor time lord
""".split())

def make_safe_filename(name):
    safe = name
    for ch in [" ", ",", "'", '"', "/", "\\", ":", ";", "?", "!", "."]:
        safe = safe.replace(ch, "_")
    while "__" in safe:
        safe = safe.replace("__", "_")
    return safe.strip("_")

def normalize_text(text):
    return " ".join(str(text).lower().replace("\n", " ").split())

def format_color_identity(color_identity):
    if not color_identity:
        return "Colorless"
    return "/".join([c for c in ["W","U","B","R","G"] if c in color_identity])

def detect_command_zone_rule(commander_cards_scryfall, companion_names=None):
    companion_names = companion_names or []
    if companion_names:
        return "Companion present / companion legality not fully checked"

    if not commander_cards_scryfall:
        return "Unknown / manual review"

    texts = [normalize_text(get_full_oracle_text(card) + " " + card.get("type_line", "")) for card in commander_cards_scryfall]
    joined = " ".join(texts)

    if len(commander_cards_scryfall) == 1:
        return "Single commander"

    if "doctor's companion" in joined or "doctor’s companion" in joined:
        return "Doctor's companion"
    if "friends forever" in joined:
        return "Friends forever"
    if "choose a background" in joined or "background" in joined:
        return "Background"
    if "partner with" in joined:
        return "Partner with"
    if "partner" in joined:
        return "Partner"

    return "Multiple command-zone cards / manual review"


def companion_legality_note(companion_names):
    if companion_names:
        return "Companion detected. Companion legality is reported but not fully validated in v0.5.7."
    return "No companion detected. Companion legality check not applicable."


def section_is_non_mainboard(section_name):
    lowered = normalize_text(section_name.replace("Custom:", "").strip())
    if lowered == "companion" or lowered in NON_MAINBOARD_SECTION_HEADERS or lowered in REFERENCE_ONLY_SECTION_HEADERS:
        return True
    lowered_full = normalize_text(section_name)
    return any(lowered_full.startswith(prefix) for prefix in NON_MAINBOARD_PREFIXES)


LIKELY_TOKEN_OR_HELPER_NAMES = {
    "copy", "treasure", "food", "clue", "blood", "incubator", "map", "junk",
    "beast", "bird", "cat", "dog", "dinosaur", "dragon", "elf warrior",
    "goblin", "human", "human soldier", "insect", "rabbit", "saproling",
    "soldier", "spirit", "thopter", "zombie", "construct", "elemental",
    "rhino", "rhino warrior", "warrior", "plant", "fungus", "squirrel", "servo",
    "phyrexian", "incubator phyrexian", "monarch", "initiative",
}

def is_likely_token_or_helper_name(card_name):
    cleaned = normalize_text(card_name.replace("//", " ").strip())
    if cleaned in LIKELY_TOKEN_OR_HELPER_NAMES:
        return True
    if len(cleaned.split()) <= 3 and any(word in cleaned.split() for word in ["token", "emblem"]):
        return True
    return False

def should_ignore_card_from_tokens_section(card_name, scryfall_lookup=None):
    # v0.5.7: Token/helper sections should not count normal token names as mainboard,
    # even if Scryfall recognizes a token object with that name. This fixes decks that
    # export Food, Beast, Insect, Rhino Warrior, Saproling, etc. as generated tokens.
    return is_likely_token_or_helper_name(card_name)


def is_token_helper_section(section_name):
    cleaned = normalize_text(section_name.replace("Custom:", "").replace("Reference:", "").strip())
    if cleaned in {
        "tokens", "token", "token cards", "generated tokens", "tokens & extras", "tokens and extras",
        "extras", "helper cards", "token helpers", "generated token cards", "emblems", "emblem",
    }:
        return True
    if "token" in cleaned and any(word in cleaned for word in ["extra", "generated", "helper", "card"]):
        return True
    return False


def get_card_faces(card):
    faces = card.get("card_faces", []) or []
    if faces:
        return faces
    return [{
        "name": card.get("name", "Unknown"),
        "type_line": card.get("type_line", ""),
        "oracle_text": card.get("oracle_text", ""),
        "cmc": card.get("cmc", 0),
        "mana_cost": card.get("mana_cost", ""),
    }]

def get_full_oracle_text(card):
    parts = []
    if card.get("oracle_text"):
        parts.append(card.get("oracle_text", ""))
    for face in card.get("card_faces", []) or []:
        face_parts = []
        for key in ["name", "type_line", "oracle_text"]:
            if face.get(key):
                face_parts.append(face[key])
        if face_parts:
            parts.append("\n".join(face_parts))
    return "\n\n".join(parts)

def is_basic_land(card):
    return "Basic" in card.get("type_line","") and "Land" in card.get("type_line","")

def get_duplicate_exception_limit(card):
    text = normalize_text(get_full_oracle_text(card))
    if "a deck can have any number of cards named" in text:
        return "unlimited"
    words = {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10,"eleven":11,"twelve":12}
    for word, num in words.items():
        if f"a deck can have up to {word} cards named" in text:
            return num
    match = re.search(r"a deck can have up to (\d+) cards named", text)
    return int(match.group(1)) if match else None

def parse_mana_cost_value(mana_cost):
    """Estimate mana value from a Scryfall mana_cost string.

    This avoids using whole-card combined CMC for split/adventure/room-style faces
    when the face itself has a mana_cost but not a face-level cmc.
    """
    if not mana_cost:
        return None

    total = 0
    symbols = re.findall(r"\{([^}]+)\}", mana_cost)

    for symbol in symbols:
        symbol = symbol.upper()

        # X has mana value 0 except while the spell is on the stack.
        if symbol in {"X", "Y", "Z"}:
            continue

        # Numeric generic mana: {3}, {10}, etc.
        if symbol.isdigit():
            total += int(symbol)
            continue

        # Hybrid two-brid symbols such as {2/G} have mana value 2.
        if symbol.startswith("2/"):
            total += 2
            continue

        # Normal colored, hybrid, phyrexian, snow, and similar symbols count as 1.
        total += 1

    return float(total)


def get_face_mana_values(card):
    values = []
    whole_card_cmc = card.get("cmc", 0)

    for face in get_card_faces(card):
        face_name = face.get("name", card.get("name", "Unknown"))
        face_type = face.get("type_line", "")
        if "Land" in face_type:
            continue

        mana_cost = face.get("mana_cost", "")
        parsed_cmc = parse_mana_cost_value(mana_cost)

        if parsed_cmc is not None:
            cmc = parsed_cmc
            source = "face mana_cost"
        else:
            face_cmc = face.get("cmc")
            if face_cmc is not None:
                cmc = face_cmc
                source = "face cmc"
            else:
                cmc = whole_card_cmc
                source = "whole-card cmc fallback"

        values.append((face_name, cmc, face_type, source))

    return values


def get_representative_nonland_mana_value(card):
    values = get_face_mana_values(card)
    if not values:
        return None
    # Use cheapest castable nonland face for deck-average MV.
    return min(cmc for _, cmc, _, _ in values)


def format_face_mana_summary(card):
    values = get_face_mana_values(card)
    if not values:
        return "Land or no nonland mana value"
    return "; ".join(f"{name}: {cmc}" for name, cmc, _, _ in values)

def has_type_on_any_face(card, card_type):
    target = card_type.lower()
    for face in get_card_faces(card):
        if target in face.get("type_line", "").lower():
            return True
    return target in card.get("type_line", "").lower()

def get_face_aware_major_types(card):
    found = set()
    for face in get_card_faces(card):
        face_type = face.get("type_line", "")
        for card_type in MAJOR_CARD_TYPES:
            if card_type in face_type:
                found.add(card_type)
    if not found:
        for card_type in MAJOR_CARD_TYPES:
            if card_type in card.get("type_line", ""):
                found.add(card_type)
    return found

def is_mana_ability_only_text(text):
    """Approximation: pure mana/fixing text should not define activated-ability strategy."""
    cleaned = normalize_text(text)
    if not cleaned:
        return False

    mana_phrases = [
        "add {", "add one mana", "add two mana", "add three mana", "add mana",
        "mana of any color", "mana of any one color", "mana of any type",
        "enters the battlefield tapped", "as this land enters", "cycling", "basic landcycling",
        "search your library for a basic land", "search your library for a land",
    ]
    non_mana_value_phrases = [
        "destroy", "exile target", "damage", "draw", "create", "put a +1/+1 counter",
        "target creature", "target player", "each opponent", "return target",
        "copy", "gain control", "activated abilities cost", "activate abilities",
        "equipped creature", "enchanted creature", "you win the game", "scry",
        "surveil", "mill", "fight", "proliferate",
    ]

    has_mana = any(phrase in cleaned for phrase in mana_phrases)
    has_non_mana_value = any(phrase in cleaned for phrase in non_mana_value_phrases)
    return has_mana and not has_non_mana_value


def has_non_mana_activated_value(text):
    cleaned = normalize_text(text)
    return any(phrase in cleaned for phrase in [
        "activated abilities cost", "activated ability", "activate abilities", "copy target activated ability",
        "put a +1/+1 counter", "draw a card", "create", "deals", "damage", "destroy",
        "exile target", "return target", "gain control", "target creature gets", "each opponent",
        "you may cast", "look at the top", "scry", "surveil", "mill", "fight", "proliferate",
        "equip ", "crew ",
    ])


def infer_card_type_tags(card):
    return sorted(t.lower() for t in get_face_aware_major_types(card))

def singularize(word):
    word = word.strip("()[]{}.,:;").lower()
    if word.endswith("ies"):
        return word[:-3] + "y"
    if word.endswith("s"):
        return word[:-1]
    return word

def get_creature_subtypes(type_line):
    subtypes = set()
    for face in type_line.split("//"):
        face = face.strip()
        if "Creature" not in face or "—" not in face:
            continue
        for subtype in face.split("—", 1)[1].strip().split():
            if subtype.strip():
                subtypes.add(subtype.strip())
    return subtypes

def get_referenced_creature_types(oracle_text):
    refs = set()
    for word in normalize_text(oracle_text).split():
        singular = singularize(word)
        if singular in KNOWN_CREATURE_TYPES and singular not in NON_TRIBAL_REFERENCE_WORDS:
            refs.add(singular.title())
    return refs

def get_tribal_dependency_types(oracle_text):
    text = normalize_text(oracle_text)
    found = set()
    for ctype in get_referenced_creature_types(oracle_text):
        lower = ctype.lower()
        plural = lower + "s"
        phrases = [
            f"control a {lower}", f"control an {lower}", f"control another {lower}",
            f"as long as you control a {lower}", f"as long as you control an {lower}",
            f"control one or more {plural}", f"{plural} you control", f"{lower}s you control",
            f"other {plural}", f"other {lower}s", f"whenever a {lower}", f"whenever another {lower}",
            f"whenever one or more {plural}", f"for each {lower}", f"for each {plural}",
        ]
        if any(p in text for p in phrases):
            found.add(ctype)
    return found

def get_tribal_payoff_types(oracle_text):
    text = normalize_text(oracle_text)
    found = set()
    for ctype in get_referenced_creature_types(oracle_text):
        lower = ctype.lower()
        plural = lower + "s"
        phrases = [
            f"{plural} you control get", f"{lower}s you control get",
            f"other {plural} you control", f"other {lower}s you control",
            f"whenever a {lower} you control", f"whenever another {lower}",
            f"whenever one or more {plural}", f"for each {lower}", f"for each {plural}",
            "chosen type", "creature type",
        ]
        if any(p in text for p in phrases):
            found.add(ctype)
    return found

def infer_card_role_tags(card, commander_cards=None):
    tags = set()
    type_line = card.get("type_line", "")
    tl = type_line.lower()
    oracle = get_full_oracle_text(card)
    text = normalize_text(type_line + "\n" + oracle)
    is_land = "land" in tl
    is_only_land = is_land and all(t not in tl for t in ["creature","artifact","enchantment","instant","sorcery","battle","planeswalker"])
    if is_land:
        tags.add("mana_source")

    if "dragon" in tl or "dragon" in text:
        tags.add("dragon_typal")

    # v0.5.7: Bracket/turbo-combo role repair pack.
    # Tightened to avoid false positives from normal utility lands, big rocks,
    # sacrifice-draw spells, token makers, burn spells, and ordinary ramp.
    card_name_text = normalize_text(card.get("name", ""))
    mv = card.get("cmc", 0) or 0
    is_land_card = "land" in tl
    produces_mana_text = (
        "add {" in text
        or "add one mana" in text
        or "add two mana" in text
        or "add three mana" in text
        or "add four mana" in text
    )
    true_zero_one_mana_accel = (
        not is_land_card
        and mv <= 1
        and produces_mana_text
        and ("artifact" in tl or "sacrifice" in text or "exile" in text)
        and not any(p in text for p in ["enters the battlefield tapped", "cycling", "draw a card", "create"])
    )
    if true_zero_one_mana_accel:
        tags.update(["fast_mana", "true_fast_mana", "high_bracket_pressure", "bracket_pressure"])
    true_ritual_text = any(p in text for p in [
        "add {b}{b}{b}", "add {r}{r}{r}", "add {r}{r}", "add {b}{b}",
        "add three mana", "add four mana", "add five mana", "add an amount of",
    ])
    if true_ritual_text and ("instant" in tl or "sorcery" in tl or "sacrifice" in text or "exile" in text):
        tags.update(["ritual", "true_ritual", "fast_mana", "high_bracket_pressure", "bracket_pressure"])
    if "search your library for a card" in text and "basic land" not in text:
        tags.update(["efficient_tutor", "combo_tutor", "tutor", "tutor_chain", "high_bracket_pressure", "bracket_pressure"])
    if ("search your library" in text and "dragon" in text) or ("dragon cards" in text and "reveal" in text):
        tags.update(["combo_tutor", "tutor_chain", "dragonstorm_combo", "dragon_typal", "high_bracket_pressure", "bracket_pressure"])
    if "storm" in text and "dragon" in text:
        tags.update(["dragonstorm_combo", "turbo_combo", "combo_piece_possible", "win_condition", "high_bracket_pressure", "bracket_pressure"])
    if any(p in text for p in ["your opponents can't cast spells this turn", "opponents can't cast spells this turn", "players can't cast spells this turn", "can't cast spells this turn"]):
        tags.update(["silence_effect", "combo_protection", "protection", "high_bracket_pressure", "bracket_pressure"])
    if "counter target" in text and ("without paying" in text or "rather than pay" in text or "if you control your commander" in text):
        tags.update(["free_counterspell", "combo_protection", "free_interaction", "stack_interaction", "high_bracket_pressure", "bracket_pressure"])
    if any(p in text for p in ["win the game", "each opponent loses the game", "loses the game"]):
        tags.update(["turbo_combo", "combo_piece_possible", "win_condition", "high_bracket_pressure", "bracket_pressure"])

    # v0.5.7 edge-case role repair pack.
    if "devoid" in text:
        tags.add("devoid_awareness")
    if "eldrazi" in tl or "eldrazi" in text:
        tags.update(["eldrazi_synergy", "colorless_matters"])
    if "colorless" in text or "{" + "c" + "}" in text:
        tags.add("colorless_matters")
    if any(p in text for p in ["whenever you cast a colorless spell", "whenever you cast an eldrazi spell", "whenever you cast a spell with mana value 7", "whenever you cast a spell with mana value 6", "whenever you cast a spell with mana value 5"]):
        tags.update(["cast_trigger", "eldrazi_synergy", "big_mana_payoff", "high_mv_payoff"])
    if any(p in text for p in ["copy target spell", "copy that spell", "copy it", "copy each spell", "copy target activated ability", "copy target triggered ability"]):
        tags.update(["cast_copy_synergy", "combo_piece_possible", "synergy_piece"])

    if "adventure" in text or "adventurer" in text or "on an adventure" in text:
        tags.update(["adventure_synergy", "modal_spell_synergy", "creature_spell_hybrid"])
    if "//" in card.get("name", "") or len(card.get("card_faces", []) or []) > 1:
        tags.add("modal_spell_synergy")
        face_types = " ".join(face.get("type_line", "") for face in get_card_faces(card)).lower()
        if "creature" in face_types and ("instant" in face_types or "sorcery" in face_types):
            tags.add("creature_spell_hybrid")

    # v0.5.7: Blink/Flicker and ETB/LTB value support.
    if any(p in text for p in [
        "exile target creature you control, then return",
        "exile target permanent you control, then return",
        "exile another target creature you control, then return",
        "exile another target permanent you control, then return",
        "exile any number of target creatures you control",
        "exile any number of target nonland permanents",
        "return that card to the battlefield",
        "return it to the battlefield under its owner's control",
        "blink",
        "flicker",
    ]):
        tags.update(["blink_flicker", "exile_return", "synergy_piece", "commander_synergy_possible"])
    if any(p in text for p in [
        "enters the battlefield",
        "enter the battlefield",
        "when this creature enters",
        "when this permanent enters",
        "whenever another creature enters",
        "whenever a creature enters",
        "whenever one or more creatures enter",
    ]):
        tags.add("etb_value")
    if any(p in text for p in [
        "leaves the battlefield",
        "when this creature leaves",
        "when this permanent leaves",
        "when it dies",
        "dies",
    ]):
        tags.add("ltb_value")

    # v0.5.7: Additional card-attribute repair pack from rules files.
    if any(p in text for p in [
        "exile any number of creatures you control", "exile all creatures you control",
        "exile each creature you control", "return those cards to the battlefield",
        "return them to the battlefield", "at the beginning of the next end step, return them"
    ]):
        tags.update(["mass_blink", "blink_flicker", "exile_return", "protection", "synergy_piece", "commander_synergy_possible"])

    if any(p in text for p in [
        "creatures with defender", "defender creatures you control", "walls you control",
        "whenever a wall", "whenever a creature with defender", "for each creature with defender",
        "can attack as though it didn't have defender", "can attack as though they didn't have defender",
        "defender can attack"
    ]):
        tags.update(["defender_payoff", "wall_typal", "synergy_piece"])
    if "defender" in text or "wall" in tl:
        tags.update(["wall_typal"])
    if any(p in text for p in [
        "assigns combat damage equal to its toughness", "assign combat damage equal to their toughness",
        "equal to its toughness", "greatest toughness", "life total becomes", "you gain life equal to its toughness",
        "power becomes equal to toughness", "switch target creature's power and toughness"
    ]):
        tags.update(["toughness_payoff", "toughness_combat", "synergy_piece"])
    # High toughness bodies can matter in defender/toughness decks. Use conservative stat parsing.
    pt_match = re.search(r"(\d+)\s*/\s*(\d+)", card.get("power", "") + "/" + card.get("toughness", "")) if card.get("power") and card.get("toughness") else None
    try:
        toughness_value = int(card.get("toughness", ""))
        power_value = int(card.get("power", "0")) if str(card.get("power", "0")).isdigit() else 0
        if toughness_value >= 4 and toughness_value > power_value:
            tags.add("high_toughness")
    except Exception:
        pass

    if any(p in text for p in [
        "whenever an opponent draws", "whenever one or more opponents draw", "each opponent draws",
        "opponent draws a card", "draws a card, ", "draws cards"
    ]) and any(p in text for p in ["loses", "damage", "deals", "life"]):
        tags.update(["draw_punisher", "opponent_draw_payoff", "group_slug", "damage_payoff", "win_condition"])
    if any(p in text for p in [
        "each player discards their hand", "each player shuffles their hand", "discard their hand, then draw",
        "discard your hand, then draw", "draw seven cards", "then draws seven cards", "wheel",
        "each player draws", "each player draws a card", "at the beginning of each player's draw step",
        "put the cards from their hand on the bottom", "then draws that many cards", "draws that many cards"
    ]):
        tags.update(["wheel_effect", "forced_draw", "graveyard_enabler", "card_draw", "discard_outlet"])
    if any(p in text for p in ["each opponent loses", "opponents lose", "loses that much life", "lose life equal", "opponent loses life", "whenever an opponent loses life"]):
        tags.update(["lifedrain_payoff", "lifegain_payoff", "damage_payoff", "combo_piece_possible"] if "you gain that much life" in text else ["lifedrain_payoff", "damage_payoff"])
    if any(p in text for p in [
        "whenever you gain life", "if you would gain life", "gain twice that much life",
        "you gain twice that much life", "whenever you gain life, put", "if you gained life this turn"
    ]):
        tags.update(["lifegain_payoff", "lifegain", "synergy_piece"])
    if any(p in text for p in [
        "exchange life totals", "life total becomes", "your life total becomes", "each player's life total becomes",
        "half your life total", "pay life", "lose half your life"
    ]):
        tags.update(["life_total_manipulation", "combo_piece_possible", "manual_review"])
    if any(p in text for p in [
        "creatures you control of the chosen type get", "creatures of the chosen type get",
        "creatures you control get +1/+1", "other creatures you control get", "choose a creature type"
    ]):
        tags.update(["anthem", "tribal_anthem", "tribal_payoff", "synergy_piece"])
    if any(p in text for p in [
        "creatures you control of the chosen type have", "creatures of the chosen type have",
        "have vigilance", "have ward", "have indestructible", "have hexproof"
    ]) and ("creature type" in text or "chosen type" in text):
        tags.update(["tribal_protection", "tribal_payoff", "protection", "attack_safety"])
    if any(p in text for p in [
        "remove target attacking creature from combat", "remove target attacking creature you control from combat",
        "untap all creatures you control", "untap target attacking creature", "untap it",
        "prevent all combat damage", "prevent all combat damage that would be dealt to and dealt by",
        "attacking doesn't cause", "at end of combat, untap", "creatures you control gain vigilance"
    ]):
        tags.update(["combat_reset", "attack_safety", "protection", "combat_synergy"])

    if any(p in text for p in [
        "landfall", "whenever a land enters", "whenever one or more lands enter", "land enters the battlefield under your control"
    ]):
        tags.update(["landfall", "landfall_payoff", "lands_matter", "synergy_piece"])
    if any(p in text for p in ["you may play an additional land", "play an additional land", "play lands from your graveyard", "land card from your graveyard"]):
        tags.update(["extra_land_play", "lands_matter", "landfall", "ramp"])
    if any(p in text for p in ["create a colorless rock artifact token", "rock artifact token", "artifact token named rock"]):
        tags.update(["rock_token_synergy", "land_token", "artifact_token_synergy", "landfall", "landfall_payoff", "token_maker", "commander_created_package"])
    if "sacrifice an artifact" in text or "sacrifice a treasure" in text or "sacrifice a clue" in text or "sacrifice a food" in text:
        tags.update(["artifact_sacrifice", "artifact_payoff", "sacrifice_outlet"])

    # v0.5.7: Amass/Army and noncreature spell-token payoff support.
    if "amass" in text or "army" in tl or "army token" in text or "orc army" in text:
        tags.update(["amass_synergy", "army_typal", "token_maker", "counter_synergy", "synergy_piece"])
    if any(p in text for p in [
        "whenever you cast a noncreature spell",
        "whenever you cast an instant or sorcery spell",
        "whenever you cast or copy an instant or sorcery",
        "whenever you cast your second spell",
        "magecraft",
    ]):
        tags.update(["noncreature_spell_payoff", "spell_payoff", "cast_trigger", "synergy_piece"])

    if "investigate" in text or "clue token" in text or "clues" in text:
        tags.update(["clue_synergy", "artifact_token_synergy"])
    if "food token" in text or "foods" in text:
        tags.update(["food_synergy", "artifact_token_synergy"])
    if "treasure token" in text or "treasures" in text:
        tags.update(["treasure_synergy", "artifact_token_synergy", "ramp"])
        if "search your library" in text or "sacrifice" in text or "artifact" in text:
            tags.update(["artifact_treasure_tutor_chain", "treasure_tutor_chain"])

    if "historic" in text or "legendary spell" in text or "legendary spells" in text or "legendary permanent" in text or "legendary permanents" in text:
        tags.update(["historic_synergy", "legendary_synergy", "permanent_type_value"])
    if ("legendary spell" in text or "legendary spells" in text) and ("exile cards from the top" in text or "without paying" in text or "lesser mana value" in text):
        tags.update(["legendary_cascade", "five_color_value", "cast_trigger", "free_casting", "cost_cheat"])
    if any(p in text for p in ["shares a card type", "card type with", "permanent card", "permanent spell", "nonland permanent", "permanents you control", "different card types"]):
        tags.update(["permanent_type_value", "permanent_density"])
    if "legendary" in tl and "creature" in tl:
        tags.add("legendary_synergy")
    if "doctor" in tl or "time lord" in tl or "doctor" in text or "time lord" in text:
        tags.add("doctor_synergy")
    if "time travel" in text or "time counter" in text or "suspend" in text:
        tags.update(["time_travel_synergy", "suspend_synergy", "counter_synergy"])
        if any(p in text for p in ["without paying its mana cost", "time counter", "suspend"]):
            tags.update(["suspend_big_spell", "alternate_cost_interaction", "cost_cheat"])
    if "cascade" in text:
        tags.update(["cascade_synergy", "cast_trigger", "card_advantage", "alternate_cost_interaction", "cost_cheat", "free_casting"])
    if "improvise" in text:
        tags.update(["artifact_payoff", "artifact_token_synergy", "cost_reducer", "ramp", "synergy_piece"])

    if is_mana_ability_only_text(text):
        tags.add("mana_source")
    if (
        "activated abilities" in text
        or "activated ability" in text
        or "activate abilities" in text
        or "activate an ability" in text
        or "abilities cost" in text
        or ((re.search(r"\{t\}\s*:", text) or re.search(r"\{q\}\s*:", text)) and has_non_mana_activated_value(text))
    ):
        tags.add("activated_ability_synergy")
    if "power" in text and ("activate" in text or "activated ability" in text or "tap" in text or "becomes" in text):
        tags.add("power_matters")
    if any(p in text for p in ["mana sink", "spend this mana", "{x}", "x is", "x cards", "x damage", "+x/+x"]):
        tags.add("mana_sink")

    if any(p in text for p in ["look at the top", "scry", "surveil", "reveal the top", "top card of your library", "play with the top card"]):
        tags.update(["topdeck_manipulation", "card_selection"])
        if any(p in text for p in ["permanent", "creature", "artifact", "enchantment", "land"]):
            tags.update(["permanent_type_value", "permanent_density"])

    if any(p in text for p in ["return target creature you control", "return another target creature you control", "return a creature you control", "return target permanent you control", "return another permanent you control", "return a nonland permanent you control"]):
        tags.update(["bounce_engine", "self_bounce", "combo_piece_possible", "creature_combo_value"])
    if "clone" in text or "copy of target creature" in text or "copy target creature" in text or "token that's a copy" in text or "enters as a copy" in text or "may have this enter as a copy" in text:
        tags.update(["copy_clone_value", "combo_piece_possible", "synergy_piece"])
        if "token that's a copy" in text or "token copy" in text or ("create" in text and "token" in text and "copy" in text):
            tags.update(["token_copy_value"])
        if "dragon" in text or "dragon" in tl:
            tags.update(["dragon_copy_value", "dragon_typal"])

    land_ramp = (
        "search your library for a basic land" in text or "search your library for a basic forest" in text or
        "search your library for a forest" in text or "search your library for a land card" in text or
        ("put" in text and "land" in text and "onto the battlefield" in text)
    )

    if not is_only_land and ("add {" in text or "add one mana" in text or "add two mana" in text or "add three mana" in text or "add mana" in text or "treasure token" in text):
        tags.add("ramp")
    if land_ramp or "you may play an additional land" in text or "untap all lands" in text:
        tags.add("ramp")
    if "artifact" in tl and produces_mana_text:
        tags.add("mana_rock")
    if "creature" in tl and produces_mana_text:
        tags.add("mana_dork")
    if produces_mana_text and any(p in text for p in ["any color", "any one color", "any type"]):
        tags.add("mana_fixing")

    if any(p in text for p in ["double that mana","doubles that mana","triple that mana","triples that mana","produces twice","produces three times","add an additional","adds one additional","add one mana of any type that land produced"]):
        tags.update(["mana_doubler", "ramp"])

    if any(p in text for p in ["draw a card","draw cards","draw that many cards","draw x cards", "draw two cards", "draw three cards", "draw seven cards"]):
        tags.add("card_draw")
    if any(p in text for p in ["look at the top", "scry", "surveil", "reveal the top", "choose one", "choose two", "factor fiction", "separate them into two piles"]):
        tags.add("card_selection")
    if (("look at the top" in text and "library" in text) or ("from your graveyard" in text and ("cast" in text or "play" in text)) or ("exile the top" in text and "you may play" in text) or ("you may cast" in text and "from among them" in text) or ("suspend" in text and "without paying its mana cost" in text)):
        tags.add("card_advantage")

    # v0.5.7 missing pattern repair.
    if any(p in text for p in ["draw three cards", "draw two cards", "draw four cards", "draw seven cards"]):
        tags.update(["card_draw", "draw_fixed_number"])

    if any(p in text for p in ["each player discards their hand", "each player discards", "discard your hand, then draw", "then draws seven cards", "then draw seven cards", "draw seven cards", "wheel"]):
        tags.update(["wheel_effect", "card_draw", "discard_outlet", "graveyard_enabler"])

    if any(p in text for p in ["creatures can't attack you", "can't attack you unless", "for each creature that's attacking you", "attack you or a planeswalker you control"]):
        tags.update(["pillowfort", "protection"])

    if any(p in text for p in ["players can't", "each player can't", "spells cost", "activated abilities can't", "creatures enter the battlefield tapped", "skip", "doesn't untap"]):
        tags.add("stax_piece")

    if any(p in text for p in ["without paying its mana cost", "rather than pay", "trap", "if an opponent cast", "if your commander"]):
        tags.update(["alternate_cost_interaction"])
        if "without paying its mana cost" in text:
            tags.update(["free_casting", "cost_cheat"])

    if any(p in text for p in ["you may cast spells from your hand without paying their mana costs", "you may cast spells without paying their mana costs"]):
        tags.update(["cost_cheat", "free_casting", "big_mana_payoff", "high_mv_payoff", "win_condition"])

    if any(p in text for p in ["for each creature, its controller chooses", "destroy all creatures", "destroy all", "exile all", "each creature", "all creatures get", "return all"]):
        tags.update(["board_wipe", "mass_removal"])

    if any(p in text for p in ["change the target", "choose new targets", "becomes the target of a spell or ability", "target of target spell or ability"]):
        tags.update(["redirection_protection", "protection", "stack_interaction"])

    if any(p in text for p in ["return it to its owner's hand", "return this creature to its owner's hand", "return this permanent to its owner's hand"]):
        tags.update(["self_bounce", "self_bounce_creature", "combo_piece_possible", "creature_combo_value"])

    if "search your library" in text:
        tags.add("ramp" if land_ramp else "tutor")

    if (("destroy target" in text) or ("exile target" in text) or ("return target" in text and "to its owner's hand" in text) or ("damage to target" in text) or ("fight target" in text) or ("fights target" in text)):
        tags.add("targeted_removal")

    # Broader single-card answer patterns: tuck, bounce, shrink, and fight variants.
    # Important: do not treat every "target creature gets..." effect as removal,
    # because pump lands like Skarrg, the Rage Pits use that wording too.
    if (
        ("owner of target permanent shuffles it into" in text)
        or ("target permanent" in text and "shuffles it into" in text)
        or ("target permanent" in text and "owner shuffles" in text)
        or ("target creature gets" in text and "-1/-1" in text)
        or ("target creature gets" in text and "-2/-2" in text)
        or ("target creature gets" in text and "-3/-3" in text)
        or ("target creature gets" in text and "-4/-4" in text)
        or ("target creature gets" in text and "-5/-5" in text)
        or ("target creature gets" in text and "-6/-6" in text)
        or ("target creature gets" in text and "-7/-7" in text)
        or ("target creature gets" in text and "-8/-8" in text)
        or ("target creature gets" in text and "-9/-9" in text)
        or ("target creature gets" in text and "-10/-10" in text)
        or ("target creature gets" in text and "-11/-11" in text)
        or ("target creature gets" in text and "-12/-12" in text)
        or ("target creature gets" in text and "-13/-13" in text)
        or ("target creature gets" in text and "-x/-x" in text)
        or ("target artifact" in text and ("destroy" in text or "exile" in text))
        or ("target enchantment" in text and ("destroy" in text or "exile" in text))
        or ("target nonland permanent" in text and ("destroy" in text or "exile" in text or "return" in text))
    ):
        tags.add("targeted_removal")

    if any(p in text for p in ["counter target spell","counter target noncreature spell","counter target creature spell","counter target activated","counter target triggered","counter target ability", "counter target instant", "counter target sorcery", "exile any number of target spells", "exile target spell"]):
        tags.update(["counterspell", "stack_interaction"])
    if "if you control your commander" in text and ("you may cast this spell without paying" in text or "rather than pay this spell's mana cost" in text):
        tags.update(["free_interaction", "commander_online_protection"])
        if "counter target" in text:
            tags.update(["counterspell", "stack_interaction"])
        if "change the target" in text or "choose new targets" in text:
            tags.update(["spell_redirection", "stack_interaction"])
    if "change the target" in text or "choose new targets" in text:
        tags.update(["spell_redirection", "stack_interaction"])


    if (
        ("destroy all" in text) or ("exile all" in text) or ("all creatures get" in text) or
        ("each creature gets" in text) or ("damage to each creature" in text) or
        ("each creature" in text and "sacrifice" in text) or
        ("exile each creature" in text) or ("destroy each creature" in text)
    ):
        tags.add("board_wipe")

    if (("return target" in text and "from your graveyard" in text) or ("return" in text and "from your graveyard to your hand" in text) or ("return" in text and "from your graveyard to the battlefield" in text) or ("cast" in text and "from your graveyard" in text) or ("play" in text and "from your graveyard" in text) or "escape" in text or "flashback" in text):
        tags.add("recursion")
    if any(p in text for p in ["mill", "surveil", "discard a card", "discard your hand", "put the top", "into your graveyard"]):
        tags.update(["graveyard_enabler", "self_mill"] if ("mill" in text or "into your graveyard" in text) else ["graveyard_enabler"])
    if any(p in text for p in ["discard a card:", "discard a card,", "discard your hand:", "discard a creature card", "discard a land card"]):
        tags.update(["discard_outlet", "graveyard_enabler"])

    if any(p in text for p in ["sacrifice a creature:", "sacrifice another creature:", "sacrifice a permanent:", "sacrifice another permanent:", "sacrifice an artifact:", "sacrifice a token:"]):
        tags.update(["sacrifice_outlet", "free_sacrifice_outlet"])
    elif any(p in text for p in ["sacrifice a creature", "sacrifice another creature", "sacrifice a permanent", "sacrifice another permanent", "sacrifice an artifact"]):
        tags.add("sacrifice_outlet")

    if any(p in text for p in ["whenever a creature dies","whenever another creature dies","whenever one or more creatures die","whenever a creature you control dies","whenever another creature you control dies","whenever a creature is put into a graveyard","whenever you sacrifice","whenever a permanent you control is put into a graveyard"]):
        tags.add("death_trigger_payoff")

    if "create" in text and "token" in text:
        tags.add("token_maker")
        if "copy" in text or "token that's a copy" in text:
            tags.update(["token_copy_value", "copy_clone_value", "synergy_piece", "combo_piece_possible"])
        if "dragon" in text or "dragon" in tl:
            tags.update(["dragon_typal"])
            if "copy" in text or "token that's a copy" in text:
                tags.update(["dragon_copy_value"])
        if "rabbit" in text:
            tags.update(["rabbit_typal", "go_wide_token_engine"])
        if "clue" in text:
            tags.update(["clue_synergy", "artifact_token_synergy", "investigate_synergy"])
        if "food" in text:
            tags.update(["food_synergy", "artifact_token_synergy"])
        if "treasure" in text:
            tags.update(["treasure_synergy", "artifact_token_synergy", "ramp"])
    if "tap" in text and "untapped token" in text:
        tags.update(["token_resource_engine", "tap_token_value"])


    if any(p in text for p in ["creatures you control get","creature tokens you control get","put a +1/+1 counter on each","put +1/+1 counters on each","creatures you control have"]):
        tags.add("anthem")

    # +1/+1 counter and go-tall support. This helps v0.4 distinguish counter/combat decks
    # from generic artifact or landfall reads.
    if (
        "+1/+1 counter" in text
        or "+1/+1 counters" in text
        or "double the number of counters" in text
        or "move any number of counters" in text
        or "proliferate" in text
    ):
        tags.update(["counter_synergy", "synergy_piece"])

    if (
        "base power and toughness" in text
        or ("power and toughness" in text and "equal to" in text)
        or "gets +x/+x" in text
        or "gets +1/+1 for each" in text
        or "gets +2/+2" in text
        or "gets +3/+3" in text
        or "equipped creature gets" in text
        or "enchanted creature gets" in text
    ):
        tags.update(["go_tall_support", "combat_synergy"])

    if (
        "equipment" in tl
        or "equip " in text
        or "equipped creature" in text
        or "for mirrodin!" in text
    ):
        tags.add("equipment_synergy")
        if "creature" in text:
            tags.add("go_tall_support")

    if any(p in text for p in [
        "you may cast aura and equipment spells as though they had flash",
        "whenever an equipment enters the battlefield under your control, you may attach it",
        "attach target equipment",
        "attach target aura",
        "equip abilities you activate cost",
        "equipment spells you cast cost",
    ]):
        tags.update(["equipment_synergy", "aura_synergy", "go_tall_support", "synergy_piece", "commander_synergy_possible"])

    if (
        "aura" in tl
        or "enchant creature" in text
        or "enchanted creature" in text
    ):
        tags.add("aura_synergy")
        if "creature" in text:
            tags.add("go_tall_support")

    if "whenever you cast" in text:
        tags.add("cast_trigger")
        if "creature spell" in text or "creature" in text:
            tags.update(["creature_cast_trigger", "creature_combo_value"])
    if (
        "whenever you cast an instant or sorcery" in text
        or "whenever you cast or copy an instant or sorcery" in text
        or "whenever you cast a noncreature spell" in text
        or "whenever you cast your second spell" in text
        or "magecraft" in text
        or "storm" in text
        or "copy target instant or sorcery" in text
        or "copy target spell" in text
    ):
        tags.update(["spell_payoff", "synergy_piece"])

    if any(p in text for p in ["hexproof","indestructible","protection from","can't be countered","phase out","prevent all damage","gain protection","gains protection"]):
        tags.add("protection")
    if any(p in text for p in ["costs {1} less","costs {2} less","costs one less","costs less"]) or ("spells you cast cost" in text and "less" in text):
        tags.update(["cost_reducer", "ramp"])
        if "creature" in text or "creature spell" in text or "creature spells" in text:
            tags.update(["creature_cost_reduction", "creature_combo_value"])

    # Extra-combat and combat plan support.
    if (
        "additional combat phase" in text
        or "additional combat phases" in text
        or "after this phase, there is an additional combat" in text
        or "after this main phase, there is an additional combat" in text
        or "untap all creatures that attacked" in text
        or "untap each creature that attacked" in text
    ):
        tags.update(["extra_combat", "combat_synergy", "synergy_piece", "combo_piece_possible"])

    if (
        "whenever you attack" in text
        or "whenever a creature attacks" in text
        or "whenever one or more creatures attack" in text
        or "whenever another creature attacks" in text
        or "whenever equipped creature attacks" in text
        or "whenever this creature attacks" in text
        or "when this creature attacks" in text
        or "whenever" in text and "attacks" in text
    ):
        tags.update(["attack_trigger_payoff", "combat_synergy"])

    if (
        "combat damage to a player" in text
        or "combat damage to one of your opponents" in text
        or "whenever this creature deals combat damage" in text
        or "whenever a creature you control deals combat damage" in text
        or "can't be blocked" in text
        or "double strike" in text
        or ("trample" in text and "creature" in tl)
        or ("target creature gets" in text and "trample" in text)
        or ("target creature gets" in text and "+1/+1" in text)
        or ("target creature gets" in text and "+2/+2" in text)
        or ("target creature gets" in text and "+3/+3" in text)
        or ("target creature gets" in text and "+x/+x" in text)
        or ("target creature" in text and "can't be blocked" in text)
    ):
        tags.add("combat_synergy")

    # Artifact/death/drain damage payoff patterns common in artifact aristocrats decks.
    if (
        "whenever an artifact" in text
        or "whenever one or more artifacts" in text
        or "artifact enters" in text
        or "artifact you control" in text
        or "artifacts you control" in text
        or "artifact is put into a graveyard" in text
        or "artifact you control is put into a graveyard" in text
        or "sacrifice an artifact" in text
    ):
        tags.update(["artifact_payoff", "synergy_piece"])

    if (
        "whenever you sacrifice" in text
        or "whenever a player sacrifices" in text
        or "whenever one or more players sacrifice" in text
        or "whenever another creature dies" in text
        or "whenever a creature dies" in text
        or "whenever a permanent is put into a graveyard" in text
        or "whenever a permanent you control is put into a graveyard" in text
        or "whenever an artifact you control is put into a graveyard" in text
        or "deals 1 damage to each opponent" in text
        or "deals 1 damage to target opponent" in text
        or "deals 1 damage to any target" in text
        or "deals 1 damage to each player" in text
        or "each opponent loses 1 life" in text
        or "opponent loses 1 life" in text
        or "whenever a source you control deals" in text
        or ("whenever a permanent" in text and "deals 1 damage" in text)
        or ("sacrifices a permanent" in text and "deals 1 damage" in text)
    ):
        tags.update(["damage_payoff", "sacrifice_payoff", "synergy_piece"])

    # Equipment / aura protection and evasion.
    if (
        "equipped creature has haste" in text
        or "equipped creature has shroud" in text
        or "equipped creature has hexproof" in text
        or "equipped creature can't be blocked" in text
        or "equipped creature has protection" in text
    ):
        tags.update(["protection", "equipment_synergy", "go_tall_support"])

    if (
        "trigger an additional time" in text or "triggers an additional time" in text or
        "copy target triggered ability" in text or "copy target activated ability" in text or
        "if a triggered ability" in text or "whenever a creature enters" in text or
        "whenever another creature enters" in text or "whenever one or more creatures enter" in text or
        "whenever a dragon you control" in text or "whenever another dragon" in text or
        "whenever one or more dragons" in text or "whenever another nontoken dragon" in text or
        ("enters the battlefield" in text and "dragon" in text) or
        ("enters the battlefield" in text and "additional time" in text) or
        "double the number" in text or "twice that many" in text
    ):
        tags.add("synergy_piece")
        if "dragon" in text:
            tags.add("dragon_typal")
        if "dragon" in text and ("copy" in text or "token that's a copy" in text or "token copy" in text):
            tags.update(["dragon_copy_value", "token_copy_value", "copy_clone_value", "combo_piece_possible"])

    dependency_types = get_tribal_dependency_types(oracle)
    token_only_types = set()
    for dep_type in list(dependency_types):
        lower_dep = dep_type.lower()
        if ("create" in text and f"{lower_dep} token" in text) and not any(p in text for p in [f"{lower_dep}s you control", f"other {lower_dep}s", f"whenever a {lower_dep} you control", f"for each {lower_dep}"]):
            token_only_types.add(dep_type)
    dependency_types = dependency_types - token_only_types
    if dependency_types:
        tags.add("tribal_dependency")
    if get_tribal_payoff_types(oracle):
        tags.update(["tribal_payoff", "synergy_piece"])
    if "elf" in tl or "elves" in text or "elf " in text:
        tags.add("elf_typal")
        if "token" in text or "create" in text:
            tags.update(["token_maker", "go_wide_token_engine"])
        if any(p in text for p in ["each opponent loses", "you gain", "lose life", "gain life"]):
            tags.update(["lifedrain_payoff", "lifegain_payoff"])
    if "dwarf" in tl or "dwarves" in text or "dwarf " in text:
        tags.add("dwarf_typal")
        if "treasure" in text or "artifact" in text:
            tags.update(["artifact_treasure_tutor_chain", "treasure_tutor_chain", "artifact_token_synergy"])

    if card.get("cmc", 0) >= 6:
        if "eldrazi" in tl or "colorless" in text or "annihilator" in text or "when you cast" in text or "whenever you cast" in text:
            tags.update(["big_mana_payoff", "high_mv_payoff"])
        elif any(p in text for p in ["you win the game", "each opponent", "destroy all", "exile all", "draw", "create"]):
            tags.add("high_mv_payoff")

    if (("untap" in text and ("add {" in text or "add mana" in text)) or ("copy" in text and ("spell" in text or "activated ability" in text or "triggered ability" in text)) or ("from your graveyard" in text and ("cast" in text or "play" in text)) or ("sacrifice" in text and "return" in text) or ("create" in text and "token" in text and "whenever" in text)):
        tags.add("combo_piece_possible")
    if ("each opponent loses" in text or "you win the game" in text or ("creatures you control get" in text and "trample" in text) or "creatures you control get +x/+x" in text):
        tags.add("win_condition")

    for commander in (commander_cards or []):
        c_text = normalize_text(get_full_oracle_text(commander))
        c_type = commander.get("type_line", "").lower()
        c_mv = commander.get("cmc", 0)

        # v0.4.1: commander synergy should mean a detected connection to the commander's
        # actual game text, not merely "this is ramp in a creature commander deck."
        if "protection" in tags and "creature" in c_type:
            tags.add("commander_synergy_possible")
        if c_mv >= 6 and ("ramp" in tags or "cost_reducer" in tags):
            tags.add("commander_synergy_possible")
        if "token" in c_text and "token_maker" in tags:
            tags.add("commander_synergy_possible")
        if ("artifact" in c_text or "treasure" in c_text or "clue" in c_text or "food" in c_text) and ("artifact_payoff" in tags or "token_maker" in tags or "sacrifice_outlet" in tags or "clue_synergy" in tags or "food_synergy" in tags or "treasure_synergy" in tags or "artifact_token_synergy" in tags):
            tags.add("commander_synergy_possible")
        if ("sacrifice" in c_text or "dies" in c_text or "graveyard" in c_text) and ("sacrifice_outlet" in tags or "recursion" in tags or "death_trigger_payoff" in tags or "sacrifice_payoff" in tags):
            tags.add("commander_synergy_possible")
        if ("instant" in c_text or "sorcery" in c_text or "spell" in c_text or "cast" in c_text) and ("spell_payoff" in tags or "cost_reducer" in tags or "recursion" in tags or "card_advantage" in tags or "cast_trigger" in tags or "cascade_synergy" in tags or "suspend_synergy" in tags):
            tags.add("commander_synergy_possible")
        if ("attack" in c_text or "combat" in c_text) and ("extra_combat" in tags or "attack_trigger_payoff" in tags or "combat_synergy" in tags or "go_tall_support" in tags):
            tags.add("commander_synergy_possible")
        if ("counter" in c_text or "+1/+1" in c_text or "base power and toughness" in c_text or "power" in c_text or "activated ability" in c_text) and ("counter_synergy" in tags or "go_tall_support" in tags or "combat_synergy" in tags or "activated_ability_synergy" in tags or "power_matters" in tags or "mana_sink" in tags):
            tags.add("commander_synergy_possible")
        if "whenever" in c_text and (
            "copy" in text
            or "cast_trigger" in tags
            or "creature_cast_trigger" in tags
            or "counter_synergy" in tags
            or "spell_payoff" in tags
            or "noncreature_spell_payoff" in tags
            or (("token" in c_text or "rabbit" in c_text) and ("token_maker" in tags or "go_wide_token_engine" in tags or "rabbit_typal" in tags))
        ):
            tags.add("commander_synergy_possible")
        if ("exile" in c_text and "return" in c_text) and tags.intersection({"blink_flicker", "etb_value", "ltb_value", "exile_return"}):
            tags.add("commander_synergy_possible")
        if ("amass" in c_text or "army" in c_text or "orc" in c_text) and tags.intersection({"amass_synergy", "army_typal", "token_maker", "counter_synergy", "spell_payoff", "noncreature_spell_payoff"}):
            tags.add("commander_synergy_possible")
        if ("dragon" in c_text or "dragon" in c_type or "eldrazi" in c_text or "eldrazi" in c_type or "rabbit" in c_text or "rabbit" in c_type or "doctor" in c_text or "doctor" in c_type) and ("tribal_payoff" in tags or "tribal_dependency" in tags or "synergy_piece" in tags or "token_maker" in tags or "eldrazi_synergy" in tags or "rabbit_typal" in tags or "doctor_synergy" in tags):
            tags.add("commander_synergy_possible")
        if ("copy" in c_text or "when you cast" in c_text or "whenever you cast" in c_text) and ("cast_copy_synergy" in tags or "cast_trigger" in tags or "eldrazi_synergy" in tags or "big_mana_payoff" in tags or "copy_clone_value" in tags or "token_copy_value" in tags):
            tags.add("commander_synergy_possible")
        if ("legendary" in c_text or "legendary" in c_type) and tags.intersection({"legendary_synergy", "historic_synergy", "legendary_cascade", "five_color_value", "mana_fixing", "ramp"}):
            tags.add("commander_synergy_possible")
        if ("elf" in c_text or "elf" in c_type) and tags.intersection({"elf_typal", "token_maker", "tribal_payoff", "tribal_anthem", "lifedrain_payoff", "lifegain_payoff", "go_wide_token_engine"}):
            tags.add("commander_synergy_possible")
        if ("treasure" in c_text or "artifact" in c_text or "dwarf" in c_text) and tags.intersection({"treasure_synergy", "artifact_token_synergy", "artifact_treasure_tutor_chain", "treasure_tutor_chain", "dwarf_typal", "artifact_payoff", "artifact_sacrifice"}):
            tags.add("commander_synergy_possible")
        if ("dragon" in c_text or "dragon" in c_type) and ("dragon_typal" in tags or "dragon_copy_value" in tags or "token_copy_value" in tags or "copy_clone_value" in tags or "tribal_payoff" in tags or "token_maker" in tags):
            tags.add("commander_synergy_possible")
        if ("token" in c_text or "tap two untapped tokens" in c_text or "tap three untapped tokens" in c_text) and ("token_resource_engine" in tags or "tap_token_value" in tags or "go_wide_token_engine" in tags):
            tags.add("commander_synergy_possible")

        if (("land enters" in c_text or "landfall" in c_text or "rock artifact token" in c_text or "create a colorless rock" in c_text)
            and tags.intersection({"landfall", "landfall_payoff", "extra_land_play", "lands_matter", "ramp", "land_token", "rock_token_synergy", "artifact_token_synergy", "artifact_payoff", "artifact_sacrifice", "sacrifice_outlet", "token_maker"})):
            tags.update(["commander_synergy_possible", "commander_created_package"])

    # v0.5.7 cleanup: lands and pure mana-only sources should not define activated-ability strategy.
    if is_only_land or (is_mana_ability_only_text(text) and not has_non_mana_activated_value(text)):
        tags.discard("activated_ability_synergy")
        tags.discard("commander_synergy_possible")
        tags.add("mana_source")

    # Generic colorless production should not imply a colorless/Eldrazi strategy.
    if "colorless_matters" in tags and "eldrazi_synergy" not in tags and "big_mana_payoff" not in tags and "cast_copy_synergy" not in tags and "devoid_awareness" not in tags:
        if is_land or "mana_source" in tags:
            tags.discard("colorless_matters")

    # v0.5.7 bracket false-positive cleanup.
    if is_land:
        tags.discard("fast_mana")
        tags.discard("true_fast_mana")
        tags.discard("ritual")
        tags.discard("true_ritual")
        tags.add("utility_land")
        if "game_changer" in tags:
            tags.update(["bracket_pressure", "high_bracket_pressure"])
        elif not tags.intersection({"combo_tutor", "tutor_chain", "turbo_combo", "dragonstorm_combo"}):
            tags.discard("bracket_pressure")
            tags.discard("high_bracket_pressure")

    if not produces_mana_text:
        tags.discard("ritual")
        tags.discard("true_ritual")
        tags.discard("fast_mana")
        tags.discard("true_fast_mana")
        if not tags.intersection({"game_changer", "efficient_tutor", "combo_tutor", "tutor_chain", "turbo_combo", "dragonstorm_combo", "silence_effect", "free_counterspell", "combo_protection", "win_condition"}):
            tags.discard("bracket_pressure")
            tags.discard("high_bracket_pressure")

    if mv >= 3 and not tags.intersection({"game_changer", "efficient_tutor", "combo_tutor", "tutor_chain", "turbo_combo", "dragonstorm_combo", "silence_effect", "free_counterspell", "combo_protection"}):
        tags.discard("fast_mana")
        tags.discard("true_fast_mana")
        tags.discard("ritual")
        tags.discard("true_ritual")
        tags.discard("high_bracket_pressure")
        if "bracket_pressure" in tags and "win_condition" not in tags:
            tags.discard("bracket_pressure")


    # v0.5.7 card-attribute relevance and no-role repair tags.
    if is_mana_ability_only_text(text):
        tags.add("mana_ability_only")
        tags.add("shell_support")
    elif has_non_mana_activated_value(text):
        tags.add("activated_ability_source")
        if any(p in text for p in ["activated abilities cost", "activate abilities", "copy target activated ability", "abilities cost"]):
            tags.update(["activated_ability_payoff", "activated_ability_engine"])
        else:
            tags.add("utility_activated_ability")
    if any(p in text for p in ["take an extra turn", "extra turn after this one", "additional turn"]):
        tags.update(["extra_turn", "high_power_value_piece", "bracket_pressure"])
        tags.discard("manual_review")
    if any(p in text for p in ["until end of turn, whenever a player taps an island for mana", "add an additional", "add that much", "add {u}"]):
        if "instant" in tl or "sorcery" in tl:
            tags.update(["ritual_or_mana_burst", "mana_engine_support", "bracket_pressure"])
    if any(p in text for p in ["counter target activated or triggered ability", "counter target spell unless", "counter each spell", "counter all"]):
        tags.update(["counterspell", "stack_interaction"])
    if "buyback" in text and any(p in text for p in ["gets +", "+x/+", "+3/+0", "+1/+0"]):
        tags.update(["power_boost", "spell_recursion_possible", "combat_synergy"])
    if "urza's saga" in card_name_text or ("saga" in tl and "search your library" in text and "artifact card" in text):
        tags.update(["saga", "artifact_tutor", "utility_land", "artifact_payoff", "artifact_token_synergy"])
        tags.discard("tribal_dependency")
    if "create" in text and " token" in text:
        tags.update(["typal_token_maker", "token_typal_density"] if "token_typal_density" in ROLE_TAGS else ["typal_token_maker"])
    if any(p in tl for p in ["creature", "kindred"]):
        tags.add("creature_type_present")
        # actual density is decided in deck context; do not let this alone imply typal primary.
        tags.add("incidental_creature_type")
    if tags.intersection({"tribal_payoff", "tribal_anthem", "tribal_protection"}):
        tags.update(["typal_payoff", "typal_density_piece"])
    if tags.intersection({"bracket_pressure", "high_bracket_pressure", "game_changer"}) and not tags.intersection({"combo_piece_possible", "win_condition", "tutor_chain", "dragonstorm_combo"}):
        tags.add("high_power_value_piece")
    if tags.intersection({"win_condition", "life_total_manipulation"}) and not tags.intersection({"true_fast_mana", "true_ritual", "tutor_chain", "combo_tutor"}):
        tags.add("slow_alt_win_condition")
        tags.discard("turbo_combo")

    return sorted(tags)

def get_role_tag_explanations(tags):
    explanation_map = {
        "recursion": "has recursion or graveyard-cast/play text",
        "tribal_dependency": "depends on a creature type being present",
        "tribal_payoff": "appears to reward a creature type or tribe",
        "sacrifice_outlet": "can sacrifice creatures/permanents",
        "free_sacrifice_outlet": "appears to be a repeatable/free sacrifice outlet",
        "death_trigger_payoff": "rewards creatures dying or permanents going to the graveyard",
        "graveyard_enabler": "helps put cards into the graveyard",
        "discard_outlet": "can discard cards for value or setup",
        "token_maker": "creates tokens",
        "ramp": "helps produce or develop mana",
        "card_draw": "draws cards",
        "card_advantage": "creates card advantage or card access",
        "targeted_removal": "answers specific opposing cards",
        "board_wipe": "can clear multiple creatures/permanents",
        "protection": "protects cards, spells, or the commander",
        "synergy_piece": "amplifies a common deck action such as ETB triggers, tribal triggers, copying, or doubling",
        "combo_piece_possible": "has engine/loop-like text patterns that need manual review; not confirmed combo detection",
        "commander_synergy_possible": "appears to support the commander through role-based patterns",
        "extra_combat": "creates or supports additional combat steps",
        "combat_synergy": "supports attacking, combat damage, evasion, or combat-trigger plans",
        "attack_trigger_payoff": "rewards attacking or attack triggers",
        "damage_payoff": "turns damage, sacrifice, artifacts, or death events into pressure",
        "artifact_payoff": "rewards artifacts entering, leaving, being sacrificed, or being controlled",
        "counter_synergy": "uses, doubles, distributes, or rewards counters, especially +1/+1 counters",
        "equipment_synergy": "uses Equipment, equip text, or equipped-creature bonuses",
        "aura_synergy": "uses Auras or enchanted-creature bonuses",
        "go_tall_support": "supports one large creature, commander damage, or power/toughness scaling",
        "spell_payoff": "rewards casting, copying, or chaining instants/sorceries/noncreature spells",
        "free_interaction": "can be cast for free or reduced cost in commander-relevant conditions",
        "stack_interaction": "interacts with spells or abilities on the stack",
        "commander_online_protection": "becomes free or stronger when the commander is online",
        "spell_redirection": "can redirect spells or choose new targets",
        "bounce_engine": "returns your own permanents/creatures and may enable loops",
        "self_bounce": "can repeatedly return your own creature/permanent",
        "cast_trigger": "rewards or cares about casting spells",
        "creature_cast_trigger": "rewards casting creature spells",
        "activated_ability_synergy": "cares about activated abilities or helps use them",
        "mana_sink": "can convert excess mana into value or pressure",
        "power_matters": "cares about creature power",
        "topdeck_manipulation": "manipulates or uses the top of the library",
        "adventure_synergy": "supports Adventure cards or Adventure spells",
        "modal_spell_synergy": "supports modal, split, Adventure, or multi-face card use",
        "creature_spell_hybrid": "acts as both creature and spell support",
        "clue_synergy": "creates or rewards Clues",
        "food_synergy": "creates or rewards Food",
        "treasure_synergy": "creates or rewards Treasures",
        "artifact_token_synergy": "creates or rewards artifact tokens",
        "eldrazi_synergy": "supports Eldrazi cards or typal/colorless Eldrazi game plans",
        "colorless_matters": "cares about colorless spells, permanents, or mana",
        "big_mana_payoff": "is a payoff for large mana production",
        "cast_copy_synergy": "copies spells/triggers or rewards copying cast triggers",
        "high_mv_payoff": "expensive card with payoff text that may justify its mana value",
        "historic_synergy": "supports artifacts, legendaries, or Sagas/historic cards",
        "legendary_synergy": "supports legendary permanents/spells",
        "doctor_synergy": "supports Doctor/Time Lord style typal or commander shells",
        "time_travel_synergy": "uses time counters or time travel",
        "suspend_synergy": "uses suspend or time-counter casting",
        "cascade_synergy": "uses or rewards cascade",
        "token_resource_engine": "turns tokens into mana/cards/counters/resources",
        "tap_token_value": "uses tapping tokens as a resource",
        "rabbit_typal": "supports Rabbit typal density",
        "go_wide_token_engine": "supports a go-wide token plan",
        "card_selection": "filters or selects cards without necessarily drawing",
        "self_mill": "puts your own cards into the graveyard",
        "copy_clone_value": "copies creatures/permanents or makes clone-style value",
        "wheel_effect": "draws/discards hands or wheels multiple players",
        "pillowfort": "discourages attacks or taxes attackers",
        "stax_piece": "taxes or restricts opposing actions/resources",
        "cost_cheat": "lets spells be cast for free or for reduced/alternate costs",
        "free_casting": "allows casting without paying mana costs",
        "self_bounce_creature": "creature can return itself or your creatures to hand",
        "redirection_protection": "redirects spells/abilities or protects by changing targets",
        "mass_removal": "removes or restricts multiple opposing permanents/creatures",
        "draw_fixed_number": "draws a fixed number of cards",
        "alternate_cost_interaction": "uses alternate cost or trap-style interaction",
        "mana_source": "produces mana or functions as mana base; not automatically strategy-defining",
        "playable_replaceable_utility": "useful card that may still be replaceable in tighter lists",
        "permanent_type_value": "rewards or cares about permanent card types/topdeck permanent reveals",
        "permanent_density": "supports high permanent count or multiple permanent types",
        "creature_cost_reduction": "reduces creature costs or rewards creature spells becoming cheaper",
        "creature_combo_value": "supports creature-loop, creature-cast, or creature-bounce combo/value lines",
        "shell_support": "supports the deck shell but is not direct commander text support",
        "dragon_typal": "supports Dragon typal density or cares about Dragons",
        "dragon_copy_value": "copies Dragons or rewards Dragon copies/Dragon ETB value",
        "token_copy_value": "creates token copies or rewards token-copy effects",
        "blink_flicker": "exiles and returns permanents to reuse ETB/LTB triggers or protect pieces",
        "etb_value": "has or rewards enters-the-battlefield value",
        "ltb_value": "has or rewards leaves-the-battlefield/death value",
        "exile_return": "uses exile-and-return patterns common to blink/flicker decks",
        "amass_synergy": "creates or improves an Army through amass-style effects",
        "army_typal": "supports Army/Orc Army typal or token payoff plans",
        "noncreature_spell_payoff": "rewards casting noncreature, instant, or sorcery spells",
        "suspend_big_spell": "uses suspend/time counters to cheat large spells or delayed payoffs",
        "defender_payoff": "rewards defenders, Walls, or creatures with defender",
        "toughness_payoff": "uses high toughness as a payoff, resource, or win condition",
        "toughness_combat": "turns toughness into combat damage or lets defenders attack",
        "wall_typal": "supports Wall/defender typal density",
        "high_toughness": "has high toughness relative to power",
        "forced_draw": "forces multiple players/opponents to draw cards",
        "draw_punisher": "punishes opponents for drawing cards",
        "opponent_draw_payoff": "rewards or punishes opponent card draw",
        "group_slug": "pressures all opponents through symmetrical or repeated damage/life loss",
        "lifegain_payoff": "turns life gain into counters, cards, tokens, drain, or another payoff",
        "lifedrain_payoff": "drains opponents or rewards life loss/life gain loops",
        "life_total_manipulation": "sets, exchanges, doubles, pays, or weaponizes life totals",
        "tribal_anthem": "boosts a tribe or chosen creature type",
        "tribal_protection": "protects or grants combat safety to a tribe/chosen type",
        "combat_reset": "untaps/removes/prevents combat damage so attackers can be reused or protected",
        "attack_safety": "makes attacking safer through vigilance, untapping, prevention, or protection",
        "mass_blink": "blinks multiple permanents/creatures for protection or ETB reuse",
        "landfall": "cares about lands entering the battlefield",
        "landfall_payoff": "converts land drops into tokens, damage, counters, cards, or other value",
        "extra_land_play": "allows extra land plays or land reuse",
        "lands_matter": "uses lands as an engine beyond basic mana production",
        "land_token": "creates tokens from land drops or landfall",
        "commander_created_package": "supports a package created by the commander even if deckwide density is modest",
        "rock_token_synergy": "supports Toggo-style Rock artifact tokens or artifact-token landfall output",
        "artifact_sacrifice": "uses artifacts as sacrifice fodder or payoff fuel",
        "fast_mana": "accelerates mana ahead of normal curve and can create bracket pressure",
        "ritual": "temporary burst mana that can enable early combo or explosive starts",
        "efficient_tutor": "efficiently searches for flexible or high-impact cards",
        "combo_tutor": "finds combo pieces or a compressed win line",
        "tutor_chain": "supports repeated/tutor-chain assembly of a win condition",
        "turbo_combo": "supports a fast combo plan trying to win very early",
        "dragonstorm_combo": "supports Dragonstorm/Tiamat-style Dragon tutor or storm combo lines",
        "silence_effect": "protects a combo turn by limiting opponent spellcasting",
        "free_counterspell": "free or alternate-cost stack interaction that protects high-power lines",
        "combo_protection": "protects the deck's combo or decisive turn",
        "high_bracket_pressure": "signals speed, consistency, or power that may push the deck into a higher bracket",
        "game_changer": "listed as a Commander Game Changer in the bracket rules",
        "bracket_pressure": "may affect bracket estimate or intended power-level fit",
        "elf_typal": "supports Elf typal density, Elf tokens, or Elf-count payoffs",
        "dwarf_typal": "supports Dwarf typal density or Dwarf/Treasure engines",
        "five_color_value": "supports five-color value shells through fixing, legends, or multicolor payoffs",
        "legendary_cascade": "supports Jodah-style legendary cast/cascade value",
        "artifact_treasure_tutor_chain": "supports artifact/Treasure tutor-chain engines",
        "artifact_token_economy": "uses artifact tokens as mana, cards, sacrifice fodder, or payoff material",
        "treasure_tutor_chain": "uses Treasures as fuel for tutor-chain or artifact-combo plans",
        "ramp_control": "supports a ramp-control plan using ramp, wipes, removal, and big payoffs",
        "big_mana_value": "turns high mana production into large value or finishers",
        "mana_rock": "artifact-based mana source",
        "mana_dork": "creature-based mana source",
        "mana_fixing": "helps fix colors, especially in multicolor decks",
        "utility_land": "land with utility; not automatically fast mana or bracket pressure",
        "true_fast_mana": "low-cost acceleration that can create true early-speed bracket pressure",
        "true_ritual": "temporary burst mana that directly produces extra mana",
        "combo_pressure": "supports compact or high-speed combo pressure",
        "win_condition": "has text that can directly close a game",
    }
    return [explanation_map[tag] for tag in tags if tag in explanation_map]

def load_card_attribute_rules():
    if not ATTRIBUTE_RULES_FILE.exists():
        return (
            "WARNING: rules/card_attribute_rules.md was not found. "
            "Use generalized role-based card evaluation. "
            "Do not use exact card-name keep/cut rules."
        )

    return ATTRIBUTE_RULES_FILE.read_text(encoding="utf-8")


def load_strategy_archetype_rules():
    if not STRATEGY_RULES_FILE.exists():
        return (
            "WARNING: rules/strategy_archetype_rules.md was not found. "
            "Use role-tag based strategy evaluation only."
        )

    return STRATEGY_RULES_FILE.read_text(encoding="utf-8")


def load_cut_replacement_rules():
    if not CUT_RULES_FILE.exists():
        return (
            "WARNING: rules/cut_replacement_rules.md was not found. "
            "Use built-in v0.5 cautious cut/replacement policy only."
        )

    return CUT_RULES_FILE.read_text(encoding="utf-8")


def load_bracket_rules():
    if not BRACKET_RULES_FILE.exists():
        return (
            "WARNING: rules/bracket_rules.md was not found. "
            "Use built-in v0.5 bracket estimate only."
        )
    return BRACKET_RULES_FILE.read_text(encoding="utf-8")


def extract_game_changers_from_rules(bracket_rules_text):
    game_changers = set()
    start = bracket_rules_text.find("# Current Game Changers List")
    end = bracket_rules_text.find("# Bracket Pressure Evaluation")
    if start == -1:
        return game_changers
    section = bracket_rules_text[start:end if end != -1 else len(bracket_rules_text)]
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            name = stripped[2:].strip()
            if name and not name.startswith("`") and len(name) > 1:
                game_changers.add(normalize_text(name))
    return game_changers


def normalize_intended_bracket(value):
    text = normalize_text(value or "Unknown")
    if text in {"1", "bracket 1", "b1", "exhibition"}:
        return "Bracket 1 — Exhibition"
    if text in {"2", "bracket 2", "b2", "core"}:
        return "Bracket 2 — Core"
    if text in {"3", "bracket 3", "b3", "upgraded"}:
        return "Bracket 3 — Upgraded"
    if text in {"4", "bracket 4", "b4", "optimized"}:
        return "Bracket 4 — Optimized"
    if text in {"5", "bracket 5", "b5", "cedh", "competitive"}:
        return "Bracket 5 — cEDH"
    return "Unknown"


def bracket_number(bracket_label):
    text = normalize_text(bracket_label)
    match = re.search(r"bracket\s*(\d)", text)
    if match:
        return int(match.group(1))
    return None


# ==============================
# v0.4 Strategy / Archetype Logic
# ==============================
# These definitions intentionally use generalized tags and types instead of exact card names.
# The goal is strategy awareness, not perfect competitive deck evaluation.

ARCHETYPE_DEFINITIONS = {
    "Aristocrats": {
        "anchor_tags": {"sacrifice_outlet", "free_sacrifice_outlet", "death_trigger_payoff", "sacrifice_payoff"},
        "core_tags": {"sacrifice_outlet": 5, "free_sacrifice_outlet": 6, "death_trigger_payoff": 6, "sacrifice_payoff": 6, "damage_payoff": 3, "token_maker": 2, "recursion": 2, "graveyard_enabler": 1, "win_condition": 2},
        "engine": "Creatures/tokens/permanents are sacrificed or die, then death and sacrifice payoffs convert them into cards, damage, drain, mana, or recursion.",
        "finishers": "Drain/damage payoffs, death-trigger loops, sacrifice turns, recursive sacrifice engines.",
    },
    "Sacrifice": {
        "anchor_tags": {"sacrifice_outlet", "free_sacrifice_outlet", "sacrifice_payoff"},
        "core_tags": {"sacrifice_outlet": 6, "free_sacrifice_outlet": 6, "sacrifice_payoff": 6, "artifact_payoff": 3, "token_maker": 2, "recursion": 2, "damage_payoff": 3},
        "engine": "Permanents become resources to sacrifice for value, mana, damage, cards, or recursion.",
        "finishers": "Sacrifice payoffs, artifact death triggers, recursive sacrifice loops, token sacrifice engines.",
    },
    "Tokens": {
        "anchor_tags": {"token_maker"},
        "core_tags": {"token_maker": 6, "anthem": 3, "sacrifice_outlet": 2, "death_trigger_payoff": 2, "damage_payoff": 2, "combat_synergy": 2, "attack_trigger_payoff": 2},
        "engine": "The deck creates extra bodies or artifact tokens, then turns quantity into pressure, sacrifice fodder, mana, cards, or payoff triggers.",
        "finishers": "Anthems, go-wide attacks, token drain/damage payoffs, sacrifice engines.",
    },
    "Artifacts": {
        "anchor_tags": {"artifact_payoff"},
        "core_tags": {"artifact_payoff": 7, "sacrifice_outlet": 2, "token_maker": 1, "synergy_piece": 1, "combo_piece_possible": 1},
        "type_tags": {"artifact": 1},
        "engine": "Artifacts and artifact tokens act as the deck's main resource for mana, sacrifice, recursion, count-based payoffs, and damage/drain effects.",
        "finishers": "Artifact damage/drain payoffs, artifact combo pieces, Construct/token scaling, Treasure or artifact sacrifice turns.",
    },
    "Spellslinger": {
        "anchor_tags": {"spell_payoff", "cost_reducer"},
        "core_tags": {"spell_payoff": 7, "cost_reducer": 6, "card_draw": 2, "card_advantage": 2, "recursion": 2, "counterspell": 2, "combo_piece_possible": 2, "damage_payoff": 2},
        "type_tags": {"instant": 2, "sorcery": 2},
        "engine": "Instants and sorceries become repeatable value sources, generating cards, mana, copied effects, recursion, or damage.",
        "finishers": "Copied big spells, storm-like turns, X-spells, repeated burn/damage triggers, spell-recursion loops.",
    },
    "Graveyard Recursion": {
        "anchor_tags": {"recursion", "graveyard_enabler", "discard_outlet"},
        "core_tags": {"recursion": 6, "graveyard_enabler": 5, "discard_outlet": 4, "sacrifice_outlet": 2, "card_advantage": 2, "combo_piece_possible": 1},
        "engine": "The graveyard functions as an extension of the hand. Cards are discarded, milled, sacrificed, or traded off, then reused.",
        "finishers": "Recursive value loops, repeated reanimation/return effects, sacrifice-recursion engines, graveyard-based combo turns.",
    },
    "Reanimator": {
        "anchor_tags": {"recursion", "graveyard_enabler", "discard_outlet"},
        "core_tags": {"recursion": 6, "graveyard_enabler": 5, "discard_outlet": 5, "sacrifice_outlet": 2, "combo_piece_possible": 1},
        "engine": "The deck sets up the graveyard, then returns high-impact creatures or permanents for less mana than normal.",
        "finishers": "Reanimated threats, repeated ETB/value loops, mass recursion, sacrifice/reanimate engines.",
    },
    "Go-Wide Combat": {
        "anchor_tags": {"token_maker", "anthem"},
        "core_tags": {"token_maker": 5, "anthem": 5, "combat_synergy": 3, "attack_trigger_payoff": 3, "extra_combat": 2, "protection": 1},
        "engine": "The deck builds a wide board and converts creature count into combat pressure.",
        "finishers": "Anthems, mass pump, extra combats, evasive swarm attacks.",
    },
    "Voltron": {
        "anchor_tags": {"go_tall_support", "equipment_synergy", "aura_synergy"},
        "core_tags": {"go_tall_support": 6, "equipment_synergy": 5, "aura_synergy": 5, "protection": 3, "combat_synergy": 3, "attack_trigger_payoff": 3, "extra_combat": 2, "anthem": 1},
        "engine": "One creature, usually the commander, is built into a protected and evasive threat.",
        "finishers": "Commander damage, double strike, extra combat, evasion plus power boosts.",
    },
    "Lifegain": {
        "anchor_tags": set(),
        "core_tags": {"card_draw": 1, "damage_payoff": 1, "win_condition": 2},
        "engine": "Life gain becomes a resource when converted into cards, counters, tokens, drain, or alternate wins.",
        "finishers": "Life-drain effects, lifegain payoffs, alternate wins, large lifegain-based threats.",
    },
    "+1/+1 Counters": {
        "anchor_tags": {"counter_synergy"},
        "core_tags": {"counter_synergy": 7, "go_tall_support": 4, "combat_synergy": 2, "synergy_piece": 2, "anthem": 2, "token_maker": 1},
        "engine": "Counters scale creatures beyond normal stats and turn small bodies into threats or engines.",
        "finishers": "Large counter-scaled creatures, teamwide counters, trample/overrun effects, commander damage.",
    },
    "Enchantress": {
        "anchor_tags": set(),
        "core_tags": {"aura_synergy": 4, "card_draw": 2, "synergy_piece": 1, "protection": 1},
        "type_tags": {"enchantment": 1},
        "engine": "Enchantments become value engines through cast/ETB triggers, constellation-style payoffs, Auras, or pillowfort pieces.",
        "finishers": "Constellation value, enchantment token/drain payoffs, Voltron Auras, pillowfort inevitability.",
    },
    "Landfall": {
        "anchor_tags": {"ramp"},
        "core_tags": {"ramp": 3, "token_maker": 2, "damage_payoff": 1, "recursion": 1},
        "type_tags": {"land": 0},
        "engine": "Land drops become triggers. Ramp, fetches, and land recursion repeatedly enable payoffs.",
        "finishers": "Landfall token swarms, landfall damage, big mana payoffs, huge creatures.",
    },
    "Blink/Flicker": {
        "anchor_tags": {"synergy_piece"},
        "core_tags": {"synergy_piece": 3, "token_maker": 1, "card_draw": 1, "targeted_removal": 1, "protection": 2},
        "engine": "ETB effects become repeatable through blink, copying, bouncing, or trigger-doubling effects.",
        "finishers": "Repeated ETB value, copied ETB threats, ETB drain/damage, value overwhelm.",
    },
    "Ramp into Big Threats": {
        "anchor_tags": {"ramp", "mana_doubler"},
        "core_tags": {"ramp": 4, "mana_doubler": 6, "cost_reducer": 2, "win_condition": 4, "go_tall_support": 2, "combat_synergy": 1},
        "engine": "The deck accelerates mana to cast high-impact threats or large spells ahead of curve.",
        "finishers": "Large creatures, big X-spells, huge token production, overwhelming board states.",
    },
    "Control": {
        "anchor_tags": {"counterspell", "targeted_removal", "board_wipe"},
        "core_tags": {"counterspell": 6, "targeted_removal": 4, "board_wipe": 6, "card_draw": 2, "card_advantage": 2, "protection": 1, "recursion": 1},
        "engine": "The deck slows the game, answers threats, draws cards, and wins later with inevitability.",
        "finishers": "Protected win condition, planeswalkers, combo finish, large X-spell, inevitability engine.",
    },
    "Combo-adjacent Value": {
        "anchor_tags": {"combo_piece_possible", "synergy_piece"},
        "core_tags": {"combo_piece_possible": 4, "synergy_piece": 3, "tutor": 3, "cost_reducer": 2, "recursion": 2, "card_advantage": 2},
        "engine": "The deck uses overlapping engine pieces that may not be deterministic combos yet, but can create explosive value or loop-like turns.",
        "finishers": "Copied effects, recursive engines, high-output mana/value, payoff triggers.",
    },
    "Tribal": {
        "anchor_tags": {"tribal_payoff", "tribal_dependency"},
        "core_tags": {"tribal_payoff": 7, "tribal_dependency": 4, "anthem": 2, "token_maker": 1, "combat_synergy": 1},
        "engine": "Creature-type density turns lords, cost reducers, attack triggers, and type-specific payoffs into engines.",
        "finishers": "Typal anthem swarm, type-specific combo, mass reanimation, combat damage triggers.",
    },
    "Burn / Direct Damage": {
        "anchor_tags": {"damage_payoff", "spell_payoff"},
        "core_tags": {"damage_payoff": 6, "spell_payoff": 4, "win_condition": 3, "combo_piece_possible": 1, "card_draw": 1},
        "engine": "The deck uses direct damage or repeated noncombat damage triggers to pressure opponents.",
        "finishers": "Large X-spells, repeated damage triggers, damage doublers, burn engines.",
    },
    "Extra Combat": {
        "anchor_tags": {"extra_combat", "attack_trigger_payoff"},
        "core_tags": {"extra_combat": 7, "attack_trigger_payoff": 5, "combat_synergy": 4, "go_tall_support": 2, "token_maker": 1},
        "engine": "Additional combat phases multiply attack triggers, commander damage, or go-wide pressure.",
        "finishers": "Repeated combat damage, attack-trigger snowball, commander damage, token swarm attacks.",
    },
    "Adventure / Modal Value": {
        "anchor_tags": {"adventure_synergy", "modal_spell_synergy", "creature_spell_hybrid"},
        "core_tags": {"adventure_synergy": 7, "modal_spell_synergy": 5, "creature_spell_hybrid": 5, "spell_payoff": 2, "card_advantage": 2, "cost_reducer": 2, "cast_trigger": 2},
        "engine": "Modal, Adventure, split, or multi-face cards give the deck flexible creature/spell value and repeated card access.",
        "finishers": "Adventure-copy value, flexible modal threats, spell-creature engines, and value overwhelm.",
    },
    "Activated Abilities": {
        "anchor_tags": {"activated_ability_synergy", "mana_sink", "power_matters"},
        "core_tags": {"activated_ability_synergy": 7, "mana_sink": 4, "power_matters": 5, "ramp": 1, "counter_synergy": 2, "go_tall_support": 2},
        "engine": "The deck turns activated abilities, power scaling, and mana sinks into repeatable value or pressure.",
        "finishers": "Large activated abilities, pingers, mana-sink creatures, and power-scaling threats.",
    },
    "Eldrazi / Colorless Big Mana": {
        "anchor_tags": {"eldrazi_synergy", "colorless_matters", "big_mana_payoff", "cast_copy_synergy"},
        "core_tags": {"eldrazi_synergy": 8, "colorless_matters": 2, "big_mana_payoff": 7, "cast_copy_synergy": 6, "high_mv_payoff": 5, "ramp": 2, "cost_reducer": 3, "token_maker": 1, "attack_trigger_payoff": 2, "combat_synergy": 1},
        "engine": "The deck ramps into expensive colorless/Eldrazi threats and multiplies cast triggers, annihilator-like pressure, or huge board impact.",
        "finishers": "Huge Eldrazi, cast-copy turns, annihilator/combat pressure, and colorless payoff engines.",
    },
    "Clues / Food / Treasure": {
        "anchor_tags": {"clue_synergy", "food_synergy", "treasure_synergy", "artifact_token_synergy"},
        "core_tags": {"clue_synergy": 6, "food_synergy": 5, "treasure_synergy": 5, "artifact_token_synergy": 5, "artifact_payoff": 3, "token_maker": 2, "sacrifice_outlet": 2, "card_draw": 1, "ramp": 1},
        "engine": "Artifact tokens such as Clues, Food, and Treasures become cards, mana, sacrifice fodder, or payoff triggers.",
        "finishers": "Artifact-token drain/damage, sacrifice payoffs, Manufactor-style engines, and value snowballing.",
    },
    "Historic / Legends Matter": {
        "anchor_tags": {"historic_synergy", "legendary_synergy"},
        "core_tags": {"historic_synergy": 6, "legendary_synergy": 5, "artifact_payoff": 1, "card_advantage": 2, "cast_trigger": 2, "protection": 1},
        "engine": "Artifacts, legendary permanents, and Sagas/historic cards trigger value engines and support a legends-matter plan.",
        "finishers": "Legendary value engines, historic cast triggers, and stacked permanent-based advantage.",
    },
    "Doctor / Time Travel Value": {
        "anchor_tags": {"doctor_synergy", "time_travel_synergy", "suspend_synergy", "cascade_synergy"},
        "core_tags": {"doctor_synergy": 6, "time_travel_synergy": 5, "suspend_synergy": 5, "cascade_synergy": 4, "historic_synergy": 2, "legendary_synergy": 2, "card_advantage": 2, "ramp": 1},
        "engine": "Doctor/Time Lord, time counter, suspend, cascade, and legendary-value pieces generate delayed or repeated card advantage.",
        "finishers": "Cascade/suspend value chains, legendary Doctor payoffs, time-counter engines, and value overwhelm.",
    },
    "Token Resource Engine": {
        "anchor_tags": {"token_resource_engine", "tap_token_value", "go_wide_token_engine", "token_maker"},
        "core_tags": {"token_resource_engine": 7, "tap_token_value": 6, "go_wide_token_engine": 5, "token_maker": 4, "anthem": 2, "card_draw": 2, "ramp": 2, "counter_synergy": 2, "combat_synergy": 1, "rabbit_typal": 3},
        "engine": "Tokens are not just attackers; they become mana, cards, counters, or other resources.",
        "finishers": "Token swarms, token-powered mana/card engines, anthem combat, and commander-driven token conversion.",
    },
    "Copy / Clone Value": {
        "anchor_tags": {"copy_clone_value", "cast_copy_synergy"},
        "core_tags": {"copy_clone_value": 6, "cast_copy_synergy": 5, "combo_piece_possible": 2, "synergy_piece": 2, "card_advantage": 1, "token_maker": 1},
        "engine": "Copy and clone effects duplicate the deck's best creatures, artifacts, spells, or triggered abilities.",
        "finishers": "Copied threats, copied triggers, clone value chains, and combo-adjacent copy engines.",
    },
    "Cascade / Big Mana Value": {
        "anchor_tags": {"cascade_synergy", "cost_cheat", "free_casting"},
        "core_tags": {
            "cascade_synergy": 10,
            "cast_trigger": 4,
            "alternate_cost_interaction": 4,
            "cost_cheat": 5,
            "free_casting": 5,
            "high_mv_payoff": 4,
            "big_mana_payoff": 4,
            "ramp": 2,
            "topdeck_manipulation": 2,
            "card_advantage": 2,
            "combo_piece_possible": 1,
        },
        "engine": "The deck ramps into cascade or free-cast turns, using high-mana-value spells and cast triggers to snowball value.",
        "finishers": "Cascade chains, free-cast big spells, high-impact permanents, extra turns, and overwhelming value turns.",
    },
    "Suspend / Big Spell Cheat": {
        "anchor_tags": {"suspend_synergy", "time_travel_synergy", "suspend_big_spell"},
        "core_tags": {
            "suspend_synergy": 9,
            "time_travel_synergy": 8,
            "suspend_big_spell": 8,
            "counter_synergy": 3,
            "alternate_cost_interaction": 4,
            "cost_cheat": 5,
            "free_casting": 5,
            "high_mv_payoff": 4,
            "big_mana_payoff": 3,
            "card_advantage": 2,
        },
        "engine": "The deck cheats expensive spells through suspend/time counters and manipulates those counters to release large effects ahead of schedule.",
        "finishers": "Suspended haymakers, extra turns, Eldrazi or big-spell payoffs, and free-cast value turns.",
    },
    "Graveyard Self-Mill / Recursion": {
        "anchor_tags": {"self_mill", "graveyard_enabler", "recursion"},
        "core_tags": {
            "self_mill": 8,
            "graveyard_enabler": 7,
            "recursion": 7,
            "sacrifice_outlet": 2,
            "death_trigger_payoff": 2,
            "card_selection": 2,
            "token_maker": 1,
            "combo_piece_possible": 2,
            "high_mv_payoff": 1,
        },
        "engine": "The deck fills its graveyard, then turns the graveyard into repeatable card access, recursion, and value.",
        "finishers": "Recursive threats, graveyard loops, self-mill payoffs, and value engines that reuse creatures or permanents.",
    },
    "Blink/Flicker / ETB Value": {
        "anchor_tags": {"blink_flicker", "exile_return"},
        "core_tags": {
            "blink_flicker": 10,
            "exile_return": 8,
            "etb_value": 5,
            "ltb_value": 3,
            "token_copy_value": 2,
            "copy_clone_value": 2,
            "protection": 2,
            "card_draw": 2,
            "targeted_removal": 2,
            "permanent_density": 1,
            "synergy_piece": 2,
        },
        "engine": "The deck repeatedly exiles and returns permanents to reuse ETB/LTB triggers, protect key pieces, or generate incremental value.",
        "finishers": "Repeated ETB value, blink loops, protected board advantage, token-copy value, and attrition through recurring effects.",
    },
    "Spellslinger / Amass Army": {
        "anchor_tags": {"amass_synergy", "army_typal", "noncreature_spell_payoff", "spell_payoff"},
        "core_tags": {
            "amass_synergy": 10,
            "army_typal": 8,
            "noncreature_spell_payoff": 7,
            "spell_payoff": 6,
            "cast_trigger": 4,
            "token_maker": 3,
            "counter_synergy": 3,
            "targeted_removal": 2,
            "counterspell": 2,
            "board_wipe": 2,
            "card_draw": 2,
            "card_advantage": 2,
            "win_condition": 3,
        },
        "engine": "The deck casts noncreature spells to build or grow an Army/token threat while controlling the board and triggering spell payoffs.",
        "finishers": "Large Army tokens, spell payoff damage, copied/big spells, token pressure, and control-backed value turns.",
    },
    "Toughness Matters / Defender": {
        "anchor_tags": {"defender_payoff", "toughness_payoff", "toughness_combat", "wall_typal"},
        "core_tags": {
            "defender_payoff": 10,
            "toughness_payoff": 9,
            "toughness_combat": 9,
            "wall_typal": 6,
            "high_toughness": 4,
            "ramp": 1,
            "lifegain_payoff": 2,
            "life_total_manipulation": 2,
            "combat_synergy": 2,
            "protection": 1,
            "win_condition": 3,
        },
        "type_tags": {"creature": 1},
        "engine": "The deck uses defenders, Walls, and high-toughness creatures as mana, defense, combat pressure, lifegain/drain tools, or alternate win conditions.",
        "finishers": "Defenders attacking, toughness-as-damage effects, high-toughness payoffs, defender mana engines, and toughness/life-total finishers.",
    },
    "Wheels / Draw-Punisher / Group Slug": {
        "anchor_tags": {"wheel_effect", "forced_draw", "draw_punisher", "opponent_draw_payoff", "group_slug"},
        "core_tags": {
            "wheel_effect": 10,
            "forced_draw": 8,
            "draw_punisher": 10,
            "opponent_draw_payoff": 8,
            "group_slug": 5,
            "damage_payoff": 3,
            "spell_payoff": 2,
            "card_draw": 2,
            "discard_outlet": 2,
            "graveyard_enabler": 1,
            "win_condition": 3,
        },
        "engine": "The deck forces draws or wheels, then converts opponent card draw/discard into damage, drain, disruption, or group-slug pressure.",
        "finishers": "Wheel chains, draw-punisher damage, forced draw into life loss, discard/draw loops, and group-slug pressure.",
    },
    "Commander-Created Landfall / Artifact Token Engine": {
        "anchor_tags": {"commander_created_package", "rock_token_synergy", "landfall", "land_token"},
        "core_tags": {
            "commander_created_package": 10,
            "rock_token_synergy": 10,
            "landfall": 5,
            "landfall_payoff": 5,
            "land_token": 7,
            "extra_land_play": 4,
            "lands_matter": 3,
            "ramp": 2,
            "artifact_token_synergy": 5,
            "artifact_payoff": 4,
            "artifact_sacrifice": 4,
            "sacrifice_outlet": 3,
            "token_maker": 2,
            "damage_payoff": 2,
        },
        "engine": "The commander creates a relevant package from land drops, such as Toggo-style artifact Rock tokens. Landfall may be modest by density but still central because the commander turns lands into artifacts, fodder, damage, or sacrifice resources.",
        "finishers": "Artifact-token sacrifice payoffs, Rock/token damage, sacrifice value, land-drop resource loops, and commander-created token economy.",
    },
    "Legends Matter / Legendary Cascade": {
        "anchor_tags": {"legendary_synergy", "historic_synergy", "legendary_cascade", "five_color_value"},
        "core_tags": {
            "legendary_synergy": 8,
            "historic_synergy": 6,
            "legendary_cascade": 10,
            "five_color_value": 6,
            "cast_trigger": 4,
            "creature_cast_trigger": 2,
            "free_casting": 4,
            "cost_cheat": 3,
            "mana_fixing": 3,
            "ramp": 2,
            "protection": 2,
            "combat_synergy": 1,
            "high_mv_payoff": 2,
        },
        "engine": "The deck ramps and fixes mana, then casts legendary spells to generate Jodah-style cascade/value triggers and build overwhelming legendary board presence.",
        "finishers": "Legendary cast chains, legendary board snowball, haste-enabled alpha strikes, and five-color legendary value payoffs.",
    },
    "Elf Typal / Token Lifedrain": {
        "anchor_tags": {"elf_typal", "tribal_payoff", "tribal_anthem", "lifedrain_payoff"},
        "core_tags": {
            "elf_typal": 9,
            "tribal_payoff": 6,
            "tribal_anthem": 5,
            "tribal_dependency": 3,
            "token_maker": 4,
            "go_wide_token_engine": 3,
            "lifedrain_payoff": 6,
            "lifegain_payoff": 2,
            "combat_synergy": 2,
            "activated_ability_synergy": 2,
            "recursion": 1,
            "protection": 1,
        },
        "engine": "The deck develops Elf bodies and tokens, scales them through typal payoffs, then wins through go-wide combat or commander/lifedrain pressure.",
        "finishers": "Elf token swarms, tribal overrun effects, commander lifedrain, drain-gain payoffs, and go-wide alpha strikes.",
    },
    "Artifact/Treasure Tutor Chain": {
        "anchor_tags": {"artifact_treasure_tutor_chain", "treasure_tutor_chain", "treasure_synergy", "dwarf_typal"},
        "core_tags": {
            "artifact_treasure_tutor_chain": 10,
            "treasure_tutor_chain": 10,
            "treasure_synergy": 7,
            "artifact_token_synergy": 5,
            "artifact_payoff": 4,
            "dwarf_typal": 5,
            "tutor_chain": 4,
            "combo_tutor": 3,
            "sacrifice_outlet": 2,
            "artifact_sacrifice": 3,
            "ramp": 2,
            "combo_piece_possible": 2,
        },
        "engine": "The deck creates Treasures/artifact tokens and converts them through the commander or artifact synergies into tutor access, burst mana, or compact win lines.",
        "finishers": "Tutored artifact/Dragon finishers, Treasure-fueled combo turns, artifact sacrifice loops, and commander-driven tutor chains.",
    },
    "Ramp-Control / Big Mana Value": {
        "anchor_tags": {"ramp", "board_wipe", "mass_removal", "big_mana_payoff", "mana_doubler"},
        "core_tags": {
            "ramp": 4,
            "mana_source": 1,
            "mana_rock": 1,
            "mana_dork": 1,
            "mana_doubler": 6,
            "board_wipe": 7,
            "mass_removal": 6,
            "targeted_removal": 3,
            "recursion": 3,
            "tutor": 3,
            "big_mana_payoff": 5,
            "high_mv_payoff": 4,
            "card_advantage": 3,
            "mana_sink": 3,
            "win_condition": 2,
        },
        "engine": "The deck ramps early, stabilizes through removal and wipes, then converts a large mana advantage into high-impact threats, recursion, and big-mana finishers.",
        "finishers": "Large threats, mana-sink commander turns, high-impact X spells, mana-doubler payoffs, and recursion-backed haymakers.",
    },
    "Treasure / Artifact Token Engine": {
        "anchor_tags": {"treasure_synergy", "artifact_token_synergy", "artifact_token_economy"},
        "core_tags": {
            "treasure_synergy": 7,
            "artifact_token_synergy": 6,
            "artifact_token_economy": 6,
            "artifact_payoff": 4,
            "artifact_sacrifice": 3,
            "token_maker": 3,
            "sacrifice_outlet": 2,
            "ramp": 2,
            "card_draw": 1,
        },
        "engine": "The deck uses artifact tokens as mana, sacrifice fodder, artifact count, card access, or payoff material.",
        "finishers": "Artifact-token drain/damage, sacrifice loops, explosive Treasure turns, and artifact-count payoffs.",
    },
    "Turbo Combo / Fast Tutor Chain": {
        "anchor_tags": {"turbo_combo", "fast_mana", "ritual", "efficient_tutor", "combo_tutor", "tutor_chain"},
        "core_tags": {
            "turbo_combo": 10,
            "fast_mana": 8,
            "ritual": 8,
            "efficient_tutor": 7,
            "combo_tutor": 8,
            "tutor_chain": 7,
            "combo_protection": 5,
            "silence_effect": 5,
            "free_counterspell": 5,
            "combo_piece_possible": 4,
            "win_condition": 4,
            "high_bracket_pressure": 3,
            "bracket_pressure": 2,
        },
        "engine": "The deck uses fast mana, rituals, efficient tutors, compact combo pieces, and protection to assemble a decisive win line quickly.",
        "finishers": "Fast protected combo turns, tutor-chain wins, compact deterministic lines, and early high-pressure win attempts.",
    },
    "Dragonstorm / Tiamat Tutor Chain": {
        "anchor_tags": {"dragonstorm_combo", "tutor_chain", "combo_tutor", "dragon_typal"},
        "core_tags": {
            "dragonstorm_combo": 10,
            "tutor_chain": 8,
            "combo_tutor": 8,
            "dragon_typal": 3,
            "fast_mana": 5,
            "ritual": 5,
            "combo_protection": 4,
            "silence_effect": 4,
            "free_counterspell": 4,
            "efficient_tutor": 4,
            "win_condition": 4,
            "high_bracket_pressure": 3,
        },
        "engine": "The deck uses Tiamat/Dragonstorm-style tutor chains and fast mana to assemble Dragon-based combo wins rather than normal Dragon value.",
        "finishers": "Dragonstorm lines, Tiamat tutor chains, Broodlord-style combo compression, protected fast combo turns, and Dragon-based deterministic wins.",
    },
    "Dragon Copy / Token-Copy Value": {
        "anchor_tags": {"dragon_copy_value", "dragon_typal"},
        "core_tags": {
            "dragon_copy_value": 10,
            "dragon_typal": 6,
            "token_copy_value": 3,
            "copy_clone_value": 3,
            "token_maker": 1,
            "tribal_payoff": 4,
            "tribal_dependency": 2,
            "high_mv_payoff": 3,
            "big_mana_payoff": 2,
            "ramp": 1,
            "combat_synergy": 1,
            "attack_trigger_payoff": 1,
            "combo_piece_possible": 1,
            "synergy_piece": 1,
        },
        "type_tags": {"creature": 1},
        "engine": "Dragons and Dragon-copy effects multiply high-impact bodies, ETB triggers, combat pressure, and token-copy payoffs.",
        "finishers": "Copied Dragons, duplicated Dragon ETB/combat triggers, token-copy engines, and ramped high-impact Dragon threats.",
    },
    "Topdeck / Permanent-Type Value": {
        "anchor_tags": {"topdeck_manipulation", "permanent_type_value", "permanent_density"},
        "core_tags": {
            "topdeck_manipulation": 7,
            "permanent_type_value": 7,
            "permanent_density": 5,
            "card_selection": 3,
            "card_advantage": 3,
            "legendary_synergy": 2,
            "historic_synergy": 2,
            "modal_spell_synergy": 1,
            "creature_spell_hybrid": 1,
        },
        "type_tags": {"creature": 1, "artifact": 1, "enchantment": 1},
        "engine": "The deck uses topdeck manipulation, reveal effects, and permanent-type density to convert each permanent into card advantage or value.",
        "finishers": "Value overwhelm from repeated topdeck/permanent reveals, permanent-based engines, and protected board advantage.",
    },
    "Creature Cost-Reduction / Creature Combo Value": {
        "anchor_tags": {"creature_cost_reduction", "creature_cast_trigger", "bounce_engine", "self_bounce", "creature_combo_value"},
        "core_tags": {
            "creature_cost_reduction": 8,
            "creature_cast_trigger": 6,
            "creature_combo_value": 6,
            "bounce_engine": 6,
            "self_bounce": 6,
            "self_bounce_creature": 5,
            "cost_reducer": 3,
            "cast_trigger": 2,
            "combo_piece_possible": 3,
            "high_mv_payoff": 2,
            "eldrazi_synergy": 1,
            "big_mana_payoff": 1,
        },
        "type_tags": {"creature": 1},
        "engine": "The deck turns creature cost reduction, creature-cast triggers, and bounce/self-bounce lines into cheap threats, repeated triggers, or combo-adjacent value.",
        "finishers": "Creature loops, bounced/self-bounced creatures, free or reduced giant threats, and combo-value turns.",
    },
}

GENERIC_UTILITY_TAGS = {"ramp", "targeted_removal", "board_wipe", "counterspell", "protection", "tutor", "card_draw", "card_advantage", "card_selection", "stack_interaction", "free_interaction", "mass_removal", "pillowfort", "stax_piece", "wheel_effect", "shell_support"}
ESSENTIAL_UTILITY_TAGS = {"ramp", "targeted_removal", "board_wipe", "counterspell", "protection", "tutor", "card_draw", "card_advantage", "card_selection", "stack_interaction", "free_interaction", "mass_removal", "pillowfort", "stax_piece", "wheel_effect", "shell_support"}
LOW_RAW_POWER_CONTEXT_TAGS = {"token_maker", "sacrifice_outlet", "free_sacrifice_outlet", "recursion", "graveyard_enabler", "discard_outlet", "artifact_payoff", "damage_payoff", "sacrifice_payoff", "tribal_dependency", "tribal_payoff", "cost_reducer", "counter_synergy", "equipment_synergy", "aura_synergy", "go_tall_support", "spell_payoff", "adventure_synergy", "modal_spell_synergy", "clue_synergy", "food_synergy", "treasure_synergy", "artifact_token_synergy", "eldrazi_synergy", "colorless_matters", "cast_copy_synergy", "historic_synergy", "legendary_synergy", "doctor_synergy", "time_travel_synergy", "suspend_synergy", "cascade_synergy", "token_resource_engine", "tap_token_value", "rabbit_typal", "go_wide_token_engine", "activated_ability_synergy", "mana_sink", "power_matters", "bounce_engine", "self_bounce", "copy_clone_value", "high_mv_payoff", "cost_cheat", "free_casting", "wheel_effect", "pillowfort", "stax_piece", "mass_removal", "self_bounce_creature", "redirection_protection", "permanent_type_value", "permanent_density", "creature_cost_reduction", "creature_combo_value", "shell_support", "dragon_typal", "dragon_copy_value", "token_copy_value", "blink_flicker", "etb_value", "ltb_value", "exile_return", "amass_synergy", "army_typal", "noncreature_spell_payoff", "suspend_big_spell"}
HIGH_SYNERGY_LOW_RAW_POWER_TAGS = {"synergy_piece", "sacrifice_outlet", "free_sacrifice_outlet", "tribal_payoff", "tribal_dependency", "token_maker", "cost_reducer", "artifact_payoff", "graveyard_enabler", "discard_outlet", "counter_synergy", "equipment_synergy", "aura_synergy", "go_tall_support", "spell_payoff", "adventure_synergy", "modal_spell_synergy", "clue_synergy", "food_synergy", "treasure_synergy", "artifact_token_synergy", "eldrazi_synergy", "colorless_matters", "big_mana_payoff", "cast_copy_synergy", "historic_synergy", "legendary_synergy", "doctor_synergy", "time_travel_synergy", "suspend_synergy", "cascade_synergy", "token_resource_engine", "tap_token_value", "rabbit_typal", "go_wide_token_engine", "activated_ability_synergy", "mana_sink", "power_matters", "bounce_engine", "self_bounce", "copy_clone_value", "high_mv_payoff", "cost_cheat", "free_casting", "wheel_effect", "pillowfort", "stax_piece", "mass_removal", "self_bounce_creature", "redirection_protection", "permanent_type_value", "permanent_density", "creature_cost_reduction", "creature_combo_value", "shell_support", "dragon_typal", "dragon_copy_value", "token_copy_value", "blink_flicker", "etb_value", "ltb_value", "exile_return", "amass_synergy", "army_typal", "noncreature_spell_payoff", "suspend_big_spell"}


def capped_count(value, cap=12):
    return min(value, cap)



def get_commander_role_tag_counter(commander_cards):
    commander_tags = Counter()
    for commander in commander_cards or []:
        for tag in infer_card_role_tags(commander, commander_cards):
            commander_tags[tag] += 1
        for tag in infer_card_type_tags(commander):
            commander_tags[tag] += 1
    return commander_tags


def commander_has_any_tag(commander_tags, tags):
    return any(commander_tags.get(tag, 0) > 0 for tag in tags)


def get_true_topdeck_density(role_counts):
    # permanent_density/permanent_type_value can appear on many normal permanents.
    # topdeck_manipulation and card_selection are the better signs of a true topdeck engine.
    return (
        role_counts.get("topdeck_manipulation", 0)
        + role_counts.get("card_selection", 0)
        + min(role_counts.get("permanent_type_value", 0), 8)
    )


def get_creature_cost_reduction_density(role_counts):
    return (
        role_counts.get("creature_cost_reduction", 0)
        + role_counts.get("creature_cast_trigger", 0)
        + role_counts.get("creature_combo_value", 0)
        + role_counts.get("bounce_engine", 0)
        + role_counts.get("self_bounce", 0)
        + role_counts.get("self_bounce_creature", 0)
    )


def get_token_resource_density(role_counts):
    return (
        role_counts.get("token_resource_engine", 0)
        + role_counts.get("tap_token_value", 0)
        + role_counts.get("go_wide_token_engine", 0)
        + role_counts.get("rabbit_typal", 0)
        + min(role_counts.get("token_maker", 0), 25)
    )


def get_agatha_style_density(role_counts):
    return (
        role_counts.get("activated_ability_synergy", 0)
        + role_counts.get("mana_sink", 0)
        + role_counts.get("power_matters", 0)
        + role_counts.get("counter_synergy", 0)
        + role_counts.get("go_tall_support", 0)
        + role_counts.get("combat_synergy", 0)
    )


def get_cascade_big_mana_density(role_counts):
    return (
        role_counts.get("cascade_synergy", 0) * 3
        + role_counts.get("alternate_cost_interaction", 0) * 2
        + role_counts.get("cost_cheat", 0) * 2
        + role_counts.get("free_casting", 0) * 2
        + role_counts.get("cast_trigger", 0)
        + role_counts.get("high_mv_payoff", 0)
        + role_counts.get("big_mana_payoff", 0)
        + min(role_counts.get("ramp", 0), 20)
    )


def get_suspend_big_spell_density(role_counts):
    return (
        role_counts.get("suspend_synergy", 0) * 3
        + role_counts.get("time_travel_synergy", 0) * 3
        + role_counts.get("suspend_big_spell", 0) * 3
        + role_counts.get("counter_synergy", 0)
        + role_counts.get("cost_cheat", 0) * 2
        + role_counts.get("free_casting", 0) * 2
        + role_counts.get("high_mv_payoff", 0)
        + role_counts.get("big_mana_payoff", 0)
    )


def get_blink_flicker_density(role_counts):
    return (
        role_counts.get("blink_flicker", 0) * 4
        + role_counts.get("exile_return", 0) * 4
        + role_counts.get("etb_value", 0) * 2
        + role_counts.get("ltb_value", 0)
        + role_counts.get("token_copy_value", 0)
        + role_counts.get("copy_clone_value", 0)
        + role_counts.get("permanent_density", 0)
    )


def get_graveyard_self_mill_density(role_counts):
    return (
        role_counts.get("graveyard_enabler", 0) * 3
        + role_counts.get("self_mill", 0) * 3
        + role_counts.get("recursion", 0) * 3
        + role_counts.get("sacrifice_outlet", 0)
        + role_counts.get("death_trigger_payoff", 0)
        + role_counts.get("card_selection", 0)
    )


def get_amass_spellslinger_density(role_counts):
    return (
        role_counts.get("amass_synergy", 0) * 5
        + role_counts.get("army_typal", 0) * 4
        + role_counts.get("noncreature_spell_payoff", 0) * 4
        + role_counts.get("spell_payoff", 0) * 3
        + role_counts.get("cast_trigger", 0) * 2
        + role_counts.get("token_maker", 0)
        + role_counts.get("counter_synergy", 0)
        + role_counts.get("targeted_removal", 0)
        + role_counts.get("counterspell", 0)
    )



def get_legends_cascade_density(role_counts):
    return (
        role_counts.get("legendary_synergy", 0) * 3
        + role_counts.get("historic_synergy", 0) * 3
        + role_counts.get("legendary_cascade", 0) * 8
        + role_counts.get("five_color_value", 0) * 4
        + role_counts.get("cast_trigger", 0) * 2
        + role_counts.get("free_casting", 0) * 2
        + role_counts.get("cost_cheat", 0) * 2
        + role_counts.get("mana_fixing", 0)
        + min(role_counts.get("ramp", 0), 20)
    )


def get_elf_lifedrain_density(role_counts):
    return (
        role_counts.get("elf_typal", 0) * 5
        + role_counts.get("tribal_payoff", 0) * 3
        + role_counts.get("tribal_anthem", 0) * 3
        + role_counts.get("tribal_dependency", 0) * 2
        + role_counts.get("token_maker", 0) * 2
        + role_counts.get("go_wide_token_engine", 0) * 2
        + role_counts.get("lifedrain_payoff", 0) * 4
        + role_counts.get("lifegain_payoff", 0) * 2
        + role_counts.get("combat_synergy", 0)
        + role_counts.get("activated_ability_synergy", 0)
    )


def get_artifact_treasure_tutor_density(role_counts):
    return (
        role_counts.get("artifact_treasure_tutor_chain", 0) * 8
        + role_counts.get("treasure_tutor_chain", 0) * 8
        + role_counts.get("treasure_synergy", 0) * 4
        + role_counts.get("artifact_token_synergy", 0) * 3
        + role_counts.get("artifact_payoff", 0) * 3
        + role_counts.get("dwarf_typal", 0) * 3
        + role_counts.get("tutor_chain", 0) * 4
        + role_counts.get("combo_tutor", 0) * 3
        + role_counts.get("sacrifice_outlet", 0)
        + role_counts.get("artifact_sacrifice", 0) * 2
        + role_counts.get("ramp", 0)
    )


def get_ramp_control_density(role_counts):
    return (
        min(role_counts.get("ramp", 0), 30) * 2
        + role_counts.get("mana_doubler", 0) * 5
        + role_counts.get("mana_rock", 0)
        + role_counts.get("mana_dork", 0)
        + role_counts.get("board_wipe", 0) * 5
        + role_counts.get("mass_removal", 0) * 4
        + role_counts.get("targeted_removal", 0) * 2
        + role_counts.get("recursion", 0) * 2
        + role_counts.get("tutor", 0) * 2
        + role_counts.get("big_mana_payoff", 0) * 4
        + role_counts.get("high_mv_payoff", 0) * 3
        + role_counts.get("card_advantage", 0) * 2
        + role_counts.get("mana_sink", 0) * 2
    )


def get_turbo_combo_density(role_counts):
    return (
        role_counts.get("turbo_combo", 0) * 7
        + role_counts.get("true_fast_mana", 0) * 7
        + role_counts.get("true_ritual", 0) * 7
        + role_counts.get("fast_mana", 0) * 2
        + role_counts.get("ritual", 0) * 2
        + role_counts.get("efficient_tutor", 0) * 5
        + role_counts.get("combo_tutor", 0) * 6
        + role_counts.get("tutor_chain", 0) * 5
        + role_counts.get("combo_protection", 0) * 4
        + role_counts.get("silence_effect", 0) * 4
        + role_counts.get("free_counterspell", 0) * 4
        + role_counts.get("win_condition", 0) * 2
    )


def get_dragonstorm_tiamat_density(role_counts):
    return (
        role_counts.get("dragonstorm_combo", 0) * 10
        + min(role_counts.get("tutor_chain", 0), role_counts.get("dragon_typal", 0)) * 4
        + min(role_counts.get("combo_tutor", 0), role_counts.get("dragon_typal", 0)) * 4
        + role_counts.get("dragon_typal", 0)
        + role_counts.get("true_fast_mana", 0) * 3
        + role_counts.get("true_ritual", 0) * 3
        + role_counts.get("combo_protection", 0) * 3
        + role_counts.get("win_condition", 0) * 2
    )


def get_toughness_defender_density(role_counts):
    return (
        role_counts.get("defender_payoff", 0) * 4
        + role_counts.get("toughness_payoff", 0) * 4
        + role_counts.get("toughness_combat", 0) * 5
        + role_counts.get("wall_typal", 0) * 3
        + role_counts.get("high_toughness", 0) * 2
        + role_counts.get("life_total_manipulation", 0)
        + role_counts.get("lifegain_payoff", 0)
    )


def get_wheel_draw_punisher_density(role_counts):
    return (
        role_counts.get("wheel_effect", 0) * 5
        + role_counts.get("forced_draw", 0) * 4
        + role_counts.get("draw_punisher", 0) * 6
        + role_counts.get("opponent_draw_payoff", 0) * 5
        + role_counts.get("group_slug", 0) * 3
        + role_counts.get("damage_payoff", 0)
        + role_counts.get("spell_payoff", 0)
    )


def get_commander_landfall_package_density(role_counts):
    return (
        role_counts.get("commander_created_package", 0) * 8
        + role_counts.get("rock_token_synergy", 0) * 8
        + role_counts.get("land_token", 0) * 6
        + role_counts.get("landfall", 0) * 3
        + role_counts.get("landfall_payoff", 0) * 3
        + role_counts.get("extra_land_play", 0) * 3
        + role_counts.get("artifact_token_synergy", 0) * 2
        + role_counts.get("artifact_payoff", 0) * 2
        + role_counts.get("artifact_sacrifice", 0) * 2
        + role_counts.get("sacrifice_outlet", 0)
    )


def get_dragon_copy_density(role_counts):
    # v0.5.7: token_maker and generic copy effects should not make a deck "Dragon Copy"
    # unless there is meaningful Dragon evidence.
    dragon_typal = role_counts.get("dragon_typal", 0)
    dragon_copy = role_counts.get("dragon_copy_value", 0)
    token_copy = role_counts.get("token_copy_value", 0)
    copy_clone = role_counts.get("copy_clone_value", 0)

    if dragon_typal < 5 and dragon_copy == 0:
        return 0

    return (
        dragon_copy * 3
        + dragon_typal * 2
        + min(token_copy, max(0, dragon_typal)) * 2
        + min(copy_clone, max(0, dragon_typal)) 
        + role_counts.get("tribal_payoff", 0)
        + role_counts.get("high_mv_payoff", 0)
        + role_counts.get("big_mana_payoff", 0)
    )


def has_real_dragon_copy_evidence(role_counts, commander_tags=None):
    commander_tags = commander_tags or Counter()
    commander_dragon_copy = commander_is_dragon_copy_engine(commander_tags)
    dragon_typal = role_counts.get("dragon_typal", 0)
    dragon_copy = role_counts.get("dragon_copy_value", 0)
    token_copy = role_counts.get("token_copy_value", 0)
    copy_clone = role_counts.get("copy_clone_value", 0)

    return (
        commander_dragon_copy
        or dragon_copy > 0
        or dragon_typal >= 8
        or (dragon_typal >= 5 and (token_copy + copy_clone) >= 3)
    )


def commander_is_dragon_copy_engine(commander_tags):
    return (
        commander_tags.get("dragon_typal", 0) > 0
        and (
            commander_tags.get("dragon_copy_value", 0) > 0
            or commander_tags.get("token_copy_value", 0) > 0
            or commander_tags.get("copy_clone_value", 0) > 0
            or commander_tags.get("token_maker", 0) > 0
        )
    )



# ==============================
# v0.5.7 Strategy Gate / Reconciliation Helpers
# ==============================
BROAD_ARCHETYPES_V057 = {
    "Ramp-Control / Big Mana Value", "Go-Wide / Go-Tall Token Combat", "Go-Wide Combat",
    "Activated Abilities / Power-Reduction Engine", "Activated Abilities",
    "Artifact Engine / Artifact Tap / Artifact Mana", "Artifact/Treasure Tutor Chain",
    "Treasure / Artifact Token Engine", "Tokens", "Artifacts", "Control",
}


def v057_clean_evidence(evidence):
    cleaned = []
    seen = set()
    for item in evidence or []:
        text = str(item)
        # Collapse old stacked priority notes into a single user-readable note.
        if "priority correction" in text or "gate" in text:
            key = re.sub(r"v0\.5\.\d+(?:hotfix)?\s*", "", text)
        else:
            key = text
        if key not in seen:
            seen.add(key)
            cleaned.append(text)
    return cleaned[:12]


def can_be_primary_token_combat_v057(role_counts, commander_tags):
    commander_support = commander_has_any_tag(commander_tags, {"attack_trigger_payoff", "combat_synergy", "token_maker", "go_wide_token_engine", "counter_synergy"})
    token_count = role_counts.get("token_maker", 0)
    combat_package = role_counts.get("combat_synergy", 0) + role_counts.get("anthem", 0) + role_counts.get("counter_synergy", 0) + role_counts.get("attack_trigger_payoff", 0)
    finisher_count = role_counts.get("win_condition", 0) + role_counts.get("extra_combat", 0) + role_counts.get("anthem", 0)
    return (commander_support and token_count >= 6 and combat_package >= 8) or (token_count >= 10 and finisher_count >= 2)


def can_be_primary_activated_v057(role_counts, commander_tags):
    commander_support = commander_has_any_tag(commander_tags, {"activated_ability_payoff", "activated_ability_cost_reduction", "activated_ability_engine", "power_matters", "mana_sink"})
    real_activated = role_counts.get("activated_ability_payoff", 0) + role_counts.get("activated_ability_cost_reduction", 0) + role_counts.get("activated_ability_engine", 0)
    payoff = role_counts.get("win_condition", 0) + role_counts.get("damage_payoff", 0) + role_counts.get("card_draw", 0)
    return commander_support or (real_activated >= 8 and role_counts.get("mana_sink", 0) >= 3 and payoff >= 2)


def can_be_primary_artifact_engine_v057(role_counts, commander_tags):
    commander_support = commander_has_any_tag(commander_tags, {"artifact_payoff", "artifact_token_synergy", "artifact_sacrifice", "treasure_synergy", "clue_synergy", "food_synergy"})
    artifact_payoff = role_counts.get("artifact_payoff", 0) + role_counts.get("artifact_sacrifice", 0) + role_counts.get("artifact_token_synergy", 0)
    token_economy = role_counts.get("treasure_synergy", 0) + role_counts.get("clue_synergy", 0) + role_counts.get("food_synergy", 0)
    return artifact_payoff >= 8 and (commander_support or token_economy >= 6 or role_counts.get("artifact_sacrifice", 0) >= 4)


def can_be_primary_treasure_tutor_v057(role_counts, commander_tags):
    signals = 0
    if commander_has_any_tag(commander_tags, {"artifact_treasure_tutor_chain", "treasure_tutor_chain", "treasure_synergy", "artifact_token_synergy", "dwarf_typal"}):
        signals += 1
    if role_counts.get("treasure_synergy", 0) + role_counts.get("artifact_token_synergy", 0) >= 10:
        signals += 1
    if role_counts.get("artifact_sacrifice", 0) + role_counts.get("artifact_payoff", 0) >= 6:
        signals += 1
    if role_counts.get("tutor_chain", 0) + role_counts.get("combo_tutor", 0) >= 5:
        signals += 1
    if role_counts.get("win_condition", 0) >= 2 and role_counts.get("treasure_tutor_chain", 0) >= 1:
        signals += 1
    return signals >= 2


def commander_has_pod_effect_v057(commander_cards):
    for c in commander_cards or []:
        txt = normalize_text(get_full_oracle_text(c))
        if "sacrifice" in txt and "search your library" in txt and "creature card" in txt:
            return True
    return False




def can_be_primary_pod_toolbox_quality_gate(role_counts, commander_cards):
    """Quality gate for Pod / Creature Toolbox.

    The deck helper was over-promoting Pod/Toolbox from generic creature density, ETB value,
    and a few tutors. For primary strategy, require actual pod/chain/tutor-package evidence
    or commander text that explicitly supports creature upgrade/tutor lines.
    """
    if commander_has_pod_effect_v057(commander_cards):
        return True

    pod_core = (
        role_counts.get("pod_effect", 0) * 3
        + role_counts.get("creature_tutor", 0) * 2
        + role_counts.get("creature_chain", 0) * 2
        + role_counts.get("sacrifice_as_cost", 0)
    )
    toolbox_value = role_counts.get("etb_toolbox", 0) + role_counts.get("etb_value", 0) + role_counts.get("recursion", 0)

    # Real pod/toolbox decks need more than creatures + ETB cards.
    if role_counts.get("pod_effect", 0) >= 2:
        return True
    if role_counts.get("creature_tutor", 0) >= 4 and role_counts.get("creature_chain", 0) >= 2:
        return True
    if pod_core >= 10 and toolbox_value >= 6:
        return True
    return False

def commander_has_dragon_tutor_v057(commander_cards):
    for c in commander_cards or []:
        txt = normalize_text(get_full_oracle_text(c))
        typ = normalize_text(c.get("type_line", ""))
        if "dragon" in typ and "search your library" in txt and "dragon" in txt:
            return True
    return False


def v057_apply_gates_and_reconcile(scores, role_counts, commander_cards):
    commander_tags = get_commander_role_tag_counter(commander_cards)
    result = {name: dict(data) for name, data in scores.items()}
    diagnostics = []

    def suppress(name, multiplier, reason):
        if name in result:
            old = result[name].get("score", 0)
            result[name]["raw_score"] = result[name].get("raw_score", old)
            result[name]["score"] = int(old * multiplier)
            result[name]["gate_passed"] = False
            result[name]["gate_failed_reason"] = reason
            result[name]["suppression_reason"] = reason
            evidence = result[name].get("evidence", [])
            evidence.append(reason)
            result[name]["evidence"] = v057_clean_evidence(evidence)
            diagnostics.append(f"{name}: {old} -> {result[name]['score']} ({reason})")

    # Stronger gates for overfiring candidates.
    if not can_be_primary_ramp_control(role_counts, commander_tags):
        suppress("Ramp-Control / Big Mana Value", 0.45, "Failed ramp-control gate: ramp alone is not enough without control density and big-mana payoff density.")
    if not can_be_primary_elf_typal(role_counts, commander_tags):
        suppress("Elf Typal / Token Lifedrain", 0.25, "Failed Elf typal gate: not enough Elf commander/density/payoff support.")
    if not can_be_primary_treasure_tutor_v057(role_counts, commander_tags):
        suppress("Artifact/Treasure Tutor Chain", 0.45, "Failed artifact/Treasure tutor-chain gate: artifact/Treasure signals are not central enough.")
    if not can_be_primary_token_combat_v057(role_counts, commander_tags):
        for name in ["Go-Wide / Go-Tall Token Combat", "Go-Wide Combat"]:
            suppress(name, 0.65, "Failed token-combat gate: token/combat signals look like support, not primary identity.")
    if not can_be_primary_activated_v057(role_counts, commander_tags):
        for name in ["Activated Abilities / Power-Reduction Engine", "Activated Abilities"]:
            suppress(name, 0.55, "Failed activated-ability gate: incidental or mana-only activated abilities excluded from primary strategy.")
    if not can_be_primary_artifact_engine_v057(role_counts, commander_tags):
        suppress("Artifact Engine / Artifact Tap / Artifact Mana", 0.50, "Failed artifact-engine gate: mana rocks/artifact tokens alone are not enough for primary artifact identity.")

    if not can_be_primary_pod_toolbox_quality_gate(role_counts, commander_cards):
        suppress("Pod / Creature Toolbox / Creature Chain", 0.40, "Failed Pod/Toolbox gate: generic creature density, ETB value, and a few tutors are not enough for primary Pod identity.")

    # Specific commander-defined priority corrections.
    if commander_has_pod_effect_v057(commander_cards) and "Pod / Creature Toolbox / Creature Chain" in result:
        pod_score = result["Pod / Creature Toolbox / Creature Chain"].get("score", 0)
        activated_score = max(result.get("Activated Abilities", {}).get("score", 0), result.get("Activated Abilities / Power-Reduction Engine", {}).get("score", 0))
        result["Pod / Creature Toolbox / Creature Chain"]["score"] = max(pod_score, activated_score + 25)
        result["Pod / Creature Toolbox / Creature Chain"]["gate_passed"] = True
        result["Pod / Creature Toolbox / Creature Chain"]["primary_eligible"] = True
        result["Pod / Creature Toolbox / Creature Chain"]["suppression_reason"] = "Commander has pod-style creature tutor text; creature toolbox takes priority over generic activated abilities."
    if commander_has_dragon_tutor_v057(commander_cards) and "Dragonstorm / Tiamat Tutor Chain" in result:
        best_other = max((data.get("score",0) for name,data in result.items() if name != "Dragonstorm / Tiamat Tutor Chain"), default=0)
        result["Dragonstorm / Tiamat Tutor Chain"]["score"] = max(result["Dragonstorm / Tiamat Tutor Chain"].get("score",0), best_other + 10)
        result["Dragonstorm / Tiamat Tutor Chain"]["gate_passed"] = True
        result["Dragonstorm / Tiamat Tutor Chain"]["primary_eligible"] = True
        result["Dragonstorm / Tiamat Tutor Chain"]["suppression_reason"] = "Dragon tutor commander detected; Dragon tutor-chain takes priority when package exists."

    for data in result.values():
        data.setdefault("raw_score", data.get("score", 0))
        data.setdefault("adjusted_score", data.get("score", 0))
        data.setdefault("gate_passed", True)
        data.setdefault("gate_failed_reason", "")
        data.setdefault("strategy_layer", "scored_candidate")
        data.setdefault("primary_eligible", data.get("score", 0) > 0)
        data["evidence"] = v057_clean_evidence(data.get("evidence", []))
    result["__v057_diagnostics__"] = {"suppression_rules_triggered": diagnostics}
    return result

def score_archetypes(role_counts, type_counts, commander_cards):
    scores = {}
    commander_tags = get_commander_role_tag_counter(commander_cards)

    for archetype, definition in ARCHETYPE_DEFINITIONS.items():
        score = 0
        evidence = []
        anchor_tags = set(definition.get("anchor_tags", set()))

        anchor_hits = sum(role_counts.get(tag, 0) for tag in anchor_tags)
        commander_anchor_hits = sum(commander_tags.get(tag, 0) for tag in anchor_tags)

        for tag, weight in definition.get("core_tags", {}).items():
            count = role_counts.get(tag, 0)
            if not count:
                continue

            effective_count = capped_count(count)

            if tag in {"ramp", "card_draw", "card_advantage", "token_maker", "combo_piece_possible", "synergy_piece", "protection"}:
                if anchor_hits == 0 and commander_anchor_hits == 0:
                    effective_count = min(effective_count, 3)
                    weight = max(1, weight - 2)
                elif tag in {"ramp", "card_draw", "card_advantage"}:
                    weight = max(1, weight - 1)

            score += effective_count * weight
            evidence.append(f"{tag}: {count}")

            commander_count = commander_tags.get(tag, 0)
            if commander_count:
                commander_weight = 4 if tag in anchor_tags else 2
                score += commander_count * commander_weight
                evidence.append(f"commander {tag}")

        for tag, weight in definition.get("type_tags", {}).items():
            count = type_counts.get(tag, 0)
            if not count or weight <= 0:
                continue

            if anchor_hits == 0 and commander_anchor_hits == 0:
                effective_count = min(count, 4)
                score += effective_count * max(1, weight - 1)
            else:
                effective_count = min(count, 12)
                score += effective_count * weight

            evidence.append(f"{tag} type count: {count}")

        if anchor_hits:
            score += min(anchor_hits, 10) * 6
            evidence.append(f"anchor hits: {anchor_hits}")
        if commander_anchor_hits:
            score += commander_anchor_hits * 8
            evidence.append(f"commander anchor hits: {commander_anchor_hits}")

        if not anchor_hits and not commander_anchor_hits:
            score = int(score * 0.55)
            evidence.append("no anchor tags; score dampened")

        # v0.5.7 calibration: prevent generic token/combat/ramp piles from drowning out
        # more specific commander/archetype signatures.
        if archetype == "Go-Wide Combat" and (role_counts.get("eldrazi_synergy", 0) >= 8 or role_counts.get("big_mana_payoff", 0) >= 8):
            score = int(score * 0.72)
            evidence.append("Eldrazi/big-mana density; go-wide score dampened")
        if archetype == "+1/+1 Counters" and role_counts.get("token_maker", 0) >= 25 and role_counts.get("token_resource_engine", 0) + role_counts.get("tap_token_value", 0) + role_counts.get("go_wide_token_engine", 0) >= 4:
            score = int(score * 0.80)
            evidence.append("large token-resource density; counters score dampened")
        if archetype == "Spellslinger" and role_counts.get("adventure_synergy", 0) >= 5:
            score = int(score * 0.70)
            evidence.append("adventure/modal density; generic spellslinger dampened")
        if archetype == "Landfall" and role_counts.get("ramp", 0) >= 20 and role_counts.get("token_maker", 0) < 5 and role_counts.get("damage_payoff", 0) < 3:
            score = int(score * 0.65)
            evidence.append("ramp without landfall payoff density; landfall dampened")

        if archetype == "Activated Abilities":
            true_activated = max(0, role_counts.get("activated_ability_synergy", 0) - min(role_counts.get("mana_source", 0), role_counts.get("activated_ability_synergy", 0)))
            if true_activated < 8 and role_counts.get("mana_source", 0) >= 20:
                score = int(score * 0.55)
                evidence.append("many mana sources but low non-mana activated support; activated score dampened")

        if archetype == "Eldrazi / Colorless Big Mana":
            true_eldrazi = role_counts.get("eldrazi_synergy", 0) + role_counts.get("big_mana_payoff", 0) + role_counts.get("high_mv_payoff", 0) + role_counts.get("cast_copy_synergy", 0)
            if true_eldrazi < 8 and role_counts.get("colorless_matters", 0) >= 8:
                score = int(score * 0.50)
                evidence.append("colorless support mostly from generic sources; Eldrazi/colorless score dampened")
            if role_counts.get("creature_cost_reduction", 0) + role_counts.get("creature_combo_value", 0) + role_counts.get("bounce_engine", 0) >= 8:
                score = int(score * 0.82)
                evidence.append("creature cost-reduction/combo density; Eldrazi score slightly dampened")

        if archetype == "Combo-adjacent Value" and (role_counts.get("topdeck_manipulation", 0) + role_counts.get("permanent_type_value", 0) >= 8):
            score = int(score * 0.78)
            evidence.append("topdeck/permanent-type density; generic combo-value score dampened")

        if archetype == "Dragon Copy / Token-Copy Value":
            real_dragon_copy = has_real_dragon_copy_evidence(role_counts, commander_tags)
            dragon_typal = role_counts.get("dragon_typal", 0)
            dragon_copy = role_counts.get("dragon_copy_value", 0)
            token_density = get_token_resource_density(role_counts)

            if not real_dragon_copy:
                score = int(score * 0.25)
                evidence.append("not enough real Dragon evidence; Dragon Copy score heavily dampened")
            elif not commander_is_dragon_copy_engine(commander_tags) and dragon_typal < 8:
                score = int(score * 0.45)
                evidence.append("Dragon evidence present but not enough for primary Dragon Copy; score dampened")
            if token_density >= 35 and role_counts.get("token_maker", 0) >= 25 and dragon_typal < 8:
                score = int(score * 0.25)
                evidence.append("large non-Dragon token-resource density; Dragon Copy score heavily dampened")
            if dragon_typal < 5 and dragon_copy == 0:
                score = int(score * 0.20)
                evidence.append("generic token/copy effects without Dragon density; Dragon Copy score suppressed")

        if archetype == "Copy / Clone Value" and get_dragon_copy_density(role_counts) >= 24:
            score = int(score * 0.88)
            evidence.append("dragon copy density detected; generic copy/clone score slightly dampened")

        if archetype == "Creature Cost-Reduction / Creature Combo Value":
            creature_density = get_creature_cost_reduction_density(role_counts)
            cascade_density = get_cascade_big_mana_density(role_counts)
            amass_density = get_amass_spellslinger_density(role_counts)
            true_creature_cost_engine = (
                commander_has_any_tag(commander_tags, {"creature_cost_reduction", "creature_cast_trigger", "creature_combo_value", "cost_reducer", "bounce_engine", "self_bounce"})
                or role_counts.get("creature_cost_reduction", 0) >= 4
                or role_counts.get("bounce_engine", 0) + role_counts.get("self_bounce", 0) + role_counts.get("self_bounce_creature", 0) >= 4
            )
            if not true_creature_cost_engine and creature_density < 24:
                score = int(score * 0.55)
                evidence.append("no true commander/cost-reduction creature engine; Creature Cost-Reduction score dampened")
            if cascade_density >= 55 and role_counts.get("cascade_synergy", 0) >= 6:
                score = int(score * 0.45)
                evidence.append("cascade/big-mana density detected; Creature Cost-Reduction score heavily dampened")
            if amass_density >= 45 and role_counts.get("noncreature_spell_payoff", 0) + role_counts.get("spell_payoff", 0) >= 6:
                score = int(score * 0.55)
                evidence.append("amass/spellslinger density detected; Creature Cost-Reduction score dampened")

        if archetype == "Topdeck / Permanent-Type Value":
            commander_topdeck = commander_has_any_tag(commander_tags, {"topdeck_manipulation", "permanent_type_value", "permanent_density"})
            true_topdeck_density = get_true_topdeck_density(role_counts)
            token_density = get_token_resource_density(role_counts)
            creature_combo_density = get_creature_cost_reduction_density(role_counts)
            agatha_density = get_agatha_style_density(role_counts)

            # Topdeck/permanent-type value should be primary for Amareth-style commanders,
            # not merely because a deck contains many permanents or card-selection effects.
            if not commander_topdeck and true_topdeck_density < 22:
                score = int(score * 0.55)
                evidence.append("no commander topdeck/permanent-type text and modest true topdeck density; Topdeck score dampened")

            # Do not let topdeck value steal primary from obvious token-resource decks.
            if token_density >= 35 and role_counts.get("token_maker", 0) >= 25:
                score = int(score * 0.50)
                evidence.append("large token-resource density; Topdeck score heavily dampened")

            # Do not let topdeck value steal primary from Animar-style creature-cost/bounce engines.
            if commander_has_any_tag(commander_tags, {"creature_cost_reduction", "creature_cast_trigger", "creature_combo_value", "cost_reducer"}) and creature_combo_density >= 12:
                score = int(score * 0.65)
                evidence.append("commander creature-cost/combo engine detected; Topdeck score dampened")

            # Do not let topdeck value steal primary from Agatha-style activated/counter/power decks.
            if commander_has_any_tag(commander_tags, {"activated_ability_synergy", "mana_sink", "power_matters"}) and agatha_density >= 35:
                score = int(score * 0.60)
                evidence.append("commander activated/counter/power engine detected; Topdeck score dampened")

            # Do not let topdeck value steal primary from Miirym-style Dragon copy/token-copy decks.
            if commander_is_dragon_copy_engine(commander_tags) and get_dragon_copy_density(role_counts) >= 24:
                score = int(score * 0.50)
                evidence.append("commander Dragon copy/token-copy engine detected; Topdeck score heavily dampened")

            # v0.5.7: do not let generic permanent density steal graveyard/self-mill or blink/flicker decks.
            if get_graveyard_self_mill_density(role_counts) >= 65 and not commander_topdeck:
                score = int(score * 0.45)
                evidence.append("graveyard/self-mill density detected; Topdeck score heavily dampened")
            if get_blink_flicker_density(role_counts) >= 18 and not commander_topdeck:
                score = int(score * 0.50)
                evidence.append("blink/flicker ETB density detected; Topdeck score heavily dampened")

        if archetype == "Spellslinger / Amass Army" and role_counts.get("amass_synergy", 0) + role_counts.get("army_typal", 0) < 4:
            score = int(score * 0.45)
            evidence.append("insufficient Amass/Army density; Spellslinger / Amass score dampened")
        if archetype == "Toughness Matters / Defender" and get_toughness_defender_density(role_counts) >= 35:
            score += min(get_toughness_defender_density(role_counts), 100)
            evidence.append("toughness/defender density bonus")
        if archetype == "Wheels / Draw-Punisher / Group Slug" and get_wheel_draw_punisher_density(role_counts) >= 24:
            score += min(get_wheel_draw_punisher_density(role_counts), 100)
            evidence.append("wheel/draw-punisher density bonus")
        if archetype == "Commander-Created Landfall / Artifact Token Engine" and get_commander_landfall_package_density(role_counts) >= 20:
            score += min(get_commander_landfall_package_density(role_counts), 90)
            evidence.append("commander-created landfall/artifact-token package bonus")
        if archetype == "Dragonstorm / Tiamat Tutor Chain":
            real_tiamat_package = (
                commander_has_any_tag(commander_tags, {"dragonstorm_combo"})
                or role_counts.get("dragonstorm_combo", 0) >= 2
                or (role_counts.get("dragon_typal", 0) >= 10 and role_counts.get("tutor_chain", 0) >= 4 and role_counts.get("combo_tutor", 0) >= 3)
            )
            if not real_tiamat_package:
                score = int(score * 0.35)
                evidence.append("not enough real Tiamat/Dragonstorm package evidence; Dragonstorm score dampened")
            elif get_dragonstorm_tiamat_density(role_counts) >= 24:
                score += min(get_dragonstorm_tiamat_density(role_counts), 130)
                evidence.append("Dragonstorm / Tiamat tutor-chain density bonus")

        if archetype == "Turbo Combo / Fast Tutor Chain":
            high_quality_turbo = (
                role_counts.get("true_fast_mana", 0) + role_counts.get("true_ritual", 0) >= 2
                and role_counts.get("combo_tutor", 0) + role_counts.get("tutor_chain", 0) >= 3
            ) or role_counts.get("turbo_combo", 0) >= 2
            if not high_quality_turbo:
                score = int(score * 0.55)
                evidence.append("not enough high-quality fast mana/tutor/combo signals; Turbo score dampened")
            elif get_turbo_combo_density(role_counts) >= 45:
                score += min(get_turbo_combo_density(role_counts), 140)
                evidence.append("turbo combo / fast tutor-chain density bonus")

        if archetype == "Legends Matter / Legendary Cascade" and get_legends_cascade_density(role_counts) >= 70:
            score += min(get_legends_cascade_density(role_counts), 140)
            evidence.append("legendary/cascade density bonus")
        if archetype == "Elf Typal / Token Lifedrain" and get_elf_lifedrain_density(role_counts) >= 35:
            score += min(get_elf_lifedrain_density(role_counts), 130)
            evidence.append("Elf typal/token/lifedrain density bonus")
        if archetype == "Artifact/Treasure Tutor Chain" and get_artifact_treasure_tutor_density(role_counts) >= 35:
            score += min(get_artifact_treasure_tutor_density(role_counts), 130)
            evidence.append("artifact/Treasure tutor-chain density bonus")
        if archetype == "Ramp-Control / Big Mana Value" and get_ramp_control_density(role_counts) >= 80:
            score += min(get_ramp_control_density(role_counts), 150)
            evidence.append("ramp-control/big-mana value density bonus")

        if archetype == "Voltron" and get_elf_lifedrain_density(role_counts) >= 35 and role_counts.get("equipment_synergy", 0) + role_counts.get("aura_synergy", 0) < 8:
            score = int(score * 0.55)
            evidence.append("Elf/token/lifedrain density with low Equipment/Aura density; Voltron score dampened")
        if archetype == "Creature Cost-Reduction / Creature Combo Value" and get_legends_cascade_density(role_counts) >= 70:
            score = int(score * 0.50)
            evidence.append("legendary/cascade density detected; Creature Cost-Reduction score dampened")
        if archetype == "Graveyard Self-Mill / Recursion" and get_ramp_control_density(role_counts) >= 80 and role_counts.get("self_mill", 0) < 8:
            score = int(score * 0.55)
            evidence.append("ramp-control density with modest self-mill; Graveyard Self-Mill score dampened")
        if archetype == "Commander-Created Landfall / Artifact Token Engine":
            commander_landfall_anchor = commander_has_any_tag(commander_tags, {"commander_created_package", "rock_token_synergy", "land_token"})
            if not commander_landfall_anchor:
                score = int(score * 0.25)
                evidence.append("commander does not create/reward landfall artifact-token package; commander-created landfall score suppressed")

        scores[archetype] = {
            "score": score,
            "anchor_hits": anchor_hits,
            "commander_anchor_hits": commander_anchor_hits,
            "evidence": evidence[:10],
            "engine": definition.get("engine", "Unclear resource engine."),
            "finishers": definition.get("finishers", "Finishers unclear from current tags."),
        }

    return v057_apply_gates_and_reconcile(scores, role_counts, commander_cards)



def apply_strategy_priority_corrections(archetype_scores, role_counts, commander_cards):
    """v0.5.7 final pass: if a commander-defined engine is very close to Topdeck,
    prefer the commander-defined engine as primary.
    """
    commander_tags = get_commander_role_tag_counter(commander_cards)
    corrected = {name: dict(data) for name, data in archetype_scores.items()}

    topdeck_score = corrected.get("Topdeck / Permanent-Type Value", {}).get("score", 0)
    if topdeck_score <= 0:
        return corrected

    token_score = corrected.get("Token Resource Engine", {}).get("score", 0)
    creature_score = corrected.get("Creature Cost-Reduction / Creature Combo Value", {}).get("score", 0)
    counter_score = corrected.get("+1/+1 Counters", {}).get("score", 0)
    activated_score = corrected.get("Activated Abilities", {}).get("score", 0)
    voltron_score = corrected.get("Voltron", {}).get("score", 0)
    dragon_copy_score = corrected.get("Dragon Copy / Token-Copy Value", {}).get("score", 0)
    cascade_score = corrected.get("Cascade / Big Mana Value", {}).get("score", 0)
    suspend_score = corrected.get("Suspend / Big Spell Cheat", {}).get("score", 0)
    graveyard_self_mill_score = corrected.get("Graveyard Self-Mill / Recursion", {}).get("score", 0)
    blink_score = corrected.get("Blink/Flicker / ETB Value", {}).get("score", 0)
    amass_score = corrected.get("Spellslinger / Amass Army", {}).get("score", 0)
    toughness_score = corrected.get("Toughness Matters / Defender", {}).get("score", 0)
    wheels_score = corrected.get("Wheels / Draw-Punisher / Group Slug", {}).get("score", 0)
    commander_landfall_score = corrected.get("Commander-Created Landfall / Artifact Token Engine", {}).get("score", 0)
    turbo_score = corrected.get("Turbo Combo / Fast Tutor Chain", {}).get("score", 0)
    dragonstorm_score = corrected.get("Dragonstorm / Tiamat Tutor Chain", {}).get("score", 0)
    legends_score = corrected.get("Legends Matter / Legendary Cascade", {}).get("score", 0)
    elf_score = corrected.get("Elf Typal / Token Lifedrain", {}).get("score", 0)
    treasure_tutor_score = corrected.get("Artifact/Treasure Tutor Chain", {}).get("score", 0)
    ramp_control_score = corrected.get("Ramp-Control / Big Mana Value", {}).get("score", 0)

    token_density = get_token_resource_density(role_counts)
    creature_density = get_creature_cost_reduction_density(role_counts)
    agatha_density = get_agatha_style_density(role_counts)
    dragon_copy_density = get_dragon_copy_density(role_counts)
    cascade_density = get_cascade_big_mana_density(role_counts)
    suspend_density = get_suspend_big_spell_density(role_counts)
    graveyard_density = get_graveyard_self_mill_density(role_counts)
    blink_density = get_blink_flicker_density(role_counts)
    amass_density = get_amass_spellslinger_density(role_counts)
    toughness_density = get_toughness_defender_density(role_counts)
    wheels_density = get_wheel_draw_punisher_density(role_counts)
    commander_landfall_density = get_commander_landfall_package_density(role_counts)
    turbo_density = get_turbo_combo_density(role_counts)
    dragonstorm_density = get_dragonstorm_tiamat_density(role_counts)
    legends_density = get_legends_cascade_density(role_counts)
    elf_density = get_elf_lifedrain_density(role_counts)
    treasure_tutor_density = get_artifact_treasure_tutor_density(role_counts)
    ramp_control_density = get_ramp_control_density(role_counts)

    # v0.5.7: narrow commander-defined identities should beat broad fallback labels.
    if legends_density >= 70 and role_counts.get("legendary_synergy", 0) >= 20 and "Legends Matter / Legendary Cascade" in corrected:
        floor_score = max(creature_score, topdeck_score, corrected.get("Historic / Legends Matter", {}).get("score", 0)) + 20
        corrected["Legends Matter / Legendary Cascade"]["score"] = max(legends_score, floor_score)
        corrected["Legends Matter / Legendary Cascade"]["evidence"] = corrected["Legends Matter / Legendary Cascade"].get("evidence", []) + ["v0.5.7 priority correction: high legendary/cascade density preferred over generic creature-cost/topdeck labels"]
        for broad in ["Creature Cost-Reduction / Creature Combo Value", "Topdeck / Permanent-Type Value", "Go-Wide Combat"]:
            if broad in corrected:
                corrected[broad]["score"] = int(corrected[broad]["score"] * 0.70)

    if elf_density >= 35 and "Elf Typal / Token Lifedrain" in corrected:
        floor_score = max(voltron_score, corrected.get("Tribal", {}).get("score", 0), corrected.get("Tokens", {}).get("score", 0)) + 18
        corrected["Elf Typal / Token Lifedrain"]["score"] = max(elf_score, floor_score)
        corrected["Elf Typal / Token Lifedrain"]["evidence"] = corrected["Elf Typal / Token Lifedrain"].get("evidence", []) + ["v0.5.7 priority correction: Elf/token/lifedrain density preferred over generic Voltron"]
        if "Voltron" in corrected:
            corrected["Voltron"]["score"] = int(corrected["Voltron"]["score"] * 0.60)

    if treasure_tutor_density >= 35 and "Artifact/Treasure Tutor Chain" in corrected:
        floor_score = max(corrected.get("Clues / Food / Treasure", {}).get("score", 0), corrected.get("Dragonstorm / Tiamat Tutor Chain", {}).get("score", 0)) + 16
        corrected["Artifact/Treasure Tutor Chain"]["score"] = max(treasure_tutor_score, floor_score)
        corrected["Artifact/Treasure Tutor Chain"]["evidence"] = corrected["Artifact/Treasure Tutor Chain"].get("evidence", []) + ["v0.5.7 priority correction: artifact/Treasure tutor-chain preferred over generic artifact-token or Dragonstorm labels"]
        if "Dragonstorm / Tiamat Tutor Chain" in corrected and role_counts.get("dragonstorm_combo", 0) < 2:
            corrected["Dragonstorm / Tiamat Tutor Chain"]["score"] = int(corrected["Dragonstorm / Tiamat Tutor Chain"]["score"] * 0.45)

    if ramp_control_density >= 85 and "Ramp-Control / Big Mana Value" in corrected:
        floor_score = max(graveyard_self_mill_score, corrected.get("Control", {}).get("score", 0), corrected.get("Ramp into Big Threats", {}).get("score", 0)) + 16
        corrected["Ramp-Control / Big Mana Value"]["score"] = max(ramp_control_score, floor_score)
        corrected["Ramp-Control / Big Mana Value"]["evidence"] = corrected["Ramp-Control / Big Mana Value"].get("evidence", []) + ["v0.5.7 priority correction: ramp-control/big-mana density preferred over self-mill/control fallback"]
        if "Graveyard Self-Mill / Recursion" in corrected and role_counts.get("self_mill", 0) < 8:
            corrected["Graveyard Self-Mill / Recursion"]["score"] = int(corrected["Graveyard Self-Mill / Recursion"]["score"] * 0.65)

    # v0.5.7: Turbo/high-power combo should beat normal value-dragon or graveyard fallback reads.
    if turbo_density >= 55 and (role_counts.get("true_fast_mana", 0) + role_counts.get("true_ritual", 0) >= 2 or role_counts.get("turbo_combo", 0) >= 2) and "Turbo Combo / Fast Tutor Chain" in corrected:
        floor_score = max(topdeck_score, dragon_copy_score, graveyard_self_mill_score, corrected.get("Combo-adjacent Value", {}).get("score", 0)) + 22
        corrected["Turbo Combo / Fast Tutor Chain"]["score"] = max(turbo_score, floor_score)
        corrected["Turbo Combo / Fast Tutor Chain"]["evidence"] = corrected["Turbo Combo / Fast Tutor Chain"].get("evidence", []) + ["v0.5.7 priority correction: fast mana/tutor/protection density preferred over normal value fallback"]
        for broad_name in ["Dragon Copy / Token-Copy Value", "Graveyard Self-Mill / Recursion", "Topdeck / Permanent-Type Value"]:
            if broad_name in corrected:
                corrected[broad_name]["score"] = int(corrected[broad_name]["score"] * 0.72)
    if dragonstorm_density >= 35 and (role_counts.get("dragonstorm_combo", 0) >= 2 or (role_counts.get("dragon_typal", 0) >= 10 and role_counts.get("tutor_chain", 0) >= 4)) and "Dragonstorm / Tiamat Tutor Chain" in corrected:
        floor_score = max(corrected.get("Dragon Copy / Token-Copy Value", {}).get("score", 0), corrected.get("Tribal", {}).get("score", 0)) + 18
        corrected["Dragonstorm / Tiamat Tutor Chain"]["score"] = max(dragonstorm_score, floor_score)
        corrected["Dragonstorm / Tiamat Tutor Chain"]["evidence"] = corrected["Dragonstorm / Tiamat Tutor Chain"].get("evidence", []) + ["v0.5.7 priority correction: Dragonstorm/Tiamat tutor-chain package preferred over normal Dragon value"]

    # v0.5.7: specific archetypes should beat broad fallback buckets when their density is clear.
    if cascade_density >= 70 and role_counts.get("cascade_synergy", 0) >= 5 and "Cascade / Big Mana Value" in corrected:
        floor_score = max(topdeck_score, creature_score) + 18
        corrected["Cascade / Big Mana Value"]["score"] = max(cascade_score, floor_score)
        corrected["Cascade / Big Mana Value"]["evidence"] = corrected["Cascade / Big Mana Value"].get("evidence", []) + ["v0.5.7 priority correction: cascade/big-mana engine preferred over broad fallback archetypes"]
        if "Creature Cost-Reduction / Creature Combo Value" in corrected:
            corrected["Creature Cost-Reduction / Creature Combo Value"]["score"] = int(corrected["Creature Cost-Reduction / Creature Combo Value"]["score"] * 0.65)
        if "Topdeck / Permanent-Type Value" in corrected:
            corrected["Topdeck / Permanent-Type Value"]["score"] = int(corrected["Topdeck / Permanent-Type Value"]["score"] * 0.75)

    if suspend_density >= 55 and role_counts.get("suspend_synergy", 0) >= 5 and "Suspend / Big Spell Cheat" in corrected:
        floor_score = max(topdeck_score, corrected.get("Doctor / Time Travel Value", {}).get("score", 0)) + 14
        corrected["Suspend / Big Spell Cheat"]["score"] = max(suspend_score, floor_score)
        corrected["Suspend / Big Spell Cheat"]["evidence"] = corrected["Suspend / Big Spell Cheat"].get("evidence", []) + ["v0.5.7 priority correction: suspend/time-counter big-spell engine preferred over generic time-value label"]

    if graveyard_density >= 90 and role_counts.get("recursion", 0) >= 8 and role_counts.get("graveyard_enabler", 0) + role_counts.get("self_mill", 0) >= 15 and "Graveyard Self-Mill / Recursion" in corrected:
        floor_score = max(topdeck_score, corrected.get("Graveyard Recursion", {}).get("score", 0)) + 15
        corrected["Graveyard Self-Mill / Recursion"]["score"] = max(graveyard_self_mill_score, floor_score)
        corrected["Graveyard Self-Mill / Recursion"]["evidence"] = corrected["Graveyard Self-Mill / Recursion"].get("evidence", []) + ["v0.5.7 priority correction: graveyard/self-mill density preferred over generic Topdeck value"]
        if "Topdeck / Permanent-Type Value" in corrected:
            corrected["Topdeck / Permanent-Type Value"]["score"] = int(corrected["Topdeck / Permanent-Type Value"]["score"] * 0.60)

    if blink_density >= 18 and role_counts.get("blink_flicker", 0) + role_counts.get("exile_return", 0) >= 1 and "Blink/Flicker / ETB Value" in corrected:
        floor_score = max(topdeck_score, corrected.get("Token Resource Engine", {}).get("score", 0)) + 12
        corrected["Blink/Flicker / ETB Value"]["score"] = max(blink_score, floor_score)
        corrected["Blink/Flicker / ETB Value"]["evidence"] = corrected["Blink/Flicker / ETB Value"].get("evidence", []) + ["v0.5.7 priority correction: blink/flicker commander or ETB density preferred over generic Topdeck value"]
        if "Topdeck / Permanent-Type Value" in corrected:
            corrected["Topdeck / Permanent-Type Value"]["score"] = int(corrected["Topdeck / Permanent-Type Value"]["score"] * 0.70)

    if amass_density >= 55 and role_counts.get("spell_payoff", 0) + role_counts.get("noncreature_spell_payoff", 0) >= 8 and "Spellslinger / Amass Army" in corrected:
        floor_score = max(creature_score, corrected.get("Spellslinger", {}).get("score", 0)) + 14
        corrected["Spellslinger / Amass Army"]["score"] = max(amass_score, floor_score)
        corrected["Spellslinger / Amass Army"]["evidence"] = corrected["Spellslinger / Amass Army"].get("evidence", []) + ["v0.5.7 priority correction: amass/noncreature spell payoff engine preferred over generic creature-cost label"]
        if "Creature Cost-Reduction / Creature Combo Value" in corrected:
            corrected["Creature Cost-Reduction / Creature Combo Value"]["score"] = int(corrected["Creature Cost-Reduction / Creature Combo Value"]["score"] * 0.65)

    if toughness_density >= 45 and "Toughness Matters / Defender" in corrected:
        floor_score = max(topdeck_score, counter_score, corrected.get("Control", {}).get("score", 0)) + 18
        corrected["Toughness Matters / Defender"]["score"] = max(toughness_score, floor_score)
        corrected["Toughness Matters / Defender"]["evidence"] = corrected["Toughness Matters / Defender"].get("evidence", []) + ["v0.5.7 priority correction: toughness/defender density preferred over counters/control fallback"]
        if "Topdeck / Permanent-Type Value" in corrected:
            corrected["Topdeck / Permanent-Type Value"]["score"] = int(corrected["Topdeck / Permanent-Type Value"]["score"] * 0.70)
        if "+1/+1 Counters" in corrected:
            corrected["+1/+1 Counters"]["score"] = int(corrected["+1/+1 Counters"]["score"] * 0.78)

    if wheels_density >= 30 and "Wheels / Draw-Punisher / Group Slug" in corrected:
        floor_score = max(graveyard_self_mill_score, corrected.get("Reanimator", {}).get("score", 0), corrected.get("Spellslinger", {}).get("score", 0)) + 18
        corrected["Wheels / Draw-Punisher / Group Slug"]["score"] = max(wheels_score, floor_score)
        corrected["Wheels / Draw-Punisher / Group Slug"]["evidence"] = corrected["Wheels / Draw-Punisher / Group Slug"].get("evidence", []) + ["v0.5.7 priority correction: wheel/draw-punisher density preferred over graveyard/reanimator fallback"]
        if "Graveyard Self-Mill / Recursion" in corrected:
            corrected["Graveyard Self-Mill / Recursion"]["score"] = int(corrected["Graveyard Self-Mill / Recursion"]["score"] * 0.70)
        if "Reanimator" in corrected:
            corrected["Reanimator"]["score"] = int(corrected["Reanimator"]["score"] * 0.70)

    if commander_landfall_density >= 24 and commander_has_any_tag(commander_tags, {"commander_created_package", "rock_token_synergy", "land_token"}) and "Commander-Created Landfall / Artifact Token Engine" in corrected:
        # Keep sacrifice/artifact primary if stronger, but make the commander-created package visible as at least a serious secondary contender.
        floor_score = max(corrected.get("Landfall", {}).get("score", 0), corrected.get("Clues / Food / Treasure", {}).get("score", 0)) + 12
        corrected["Commander-Created Landfall / Artifact Token Engine"]["score"] = max(commander_landfall_score, floor_score)
        corrected["Commander-Created Landfall / Artifact Token Engine"]["evidence"] = corrected["Commander-Created Landfall / Artifact Token Engine"].get("evidence", []) + ["v0.5.7 priority correction: commander-created landfall/artifact-token package is relevant even at modest density"]

    # Miirym-style: Dragon copy/token-copy density should beat generic permanent/topdeck value when close,
    # but only when real Dragon evidence exists.
    if has_real_dragon_copy_evidence(role_counts, commander_tags) and commander_is_dragon_copy_engine(commander_tags) and dragon_copy_density >= 24 and dragon_copy_score >= topdeck_score * 0.55:
        corrected["Dragon Copy / Token-Copy Value"]["score"] = max(dragon_copy_score, topdeck_score + 18)
        corrected["Dragon Copy / Token-Copy Value"]["evidence"] = corrected["Dragon Copy / Token-Copy Value"].get("evidence", []) + ["v0.5.7 priority correction: Dragon copy/token-copy commander engine preferred over generic Topdeck value"]
        corrected["Topdeck / Permanent-Type Value"]["score"] = int(topdeck_score * 0.70)
        corrected["Topdeck / Permanent-Type Value"]["evidence"] = corrected["Topdeck / Permanent-Type Value"].get("evidence", []) + ["v0.5.7 priority correction: Topdeck moved behind Dragon copy/token-copy primary"]

    # Baylen-style: token resource density should beat generic permanent/topdeck or generic Dragon Copy value when close.
    if token_density >= 35 and role_counts.get("token_maker", 0) >= 25 and token_score >= topdeck_score * 0.75:
        corrected["Token Resource Engine"]["score"] = max(token_score, topdeck_score + 12)
        corrected["Token Resource Engine"]["evidence"] = corrected["Token Resource Engine"].get("evidence", []) + ["v0.5.7 priority correction: token-resource density preferred over generic Topdeck value"]
        corrected["Topdeck / Permanent-Type Value"]["score"] = int(topdeck_score * 0.80)
        corrected["Topdeck / Permanent-Type Value"]["evidence"] = corrected["Topdeck / Permanent-Type Value"].get("evidence", []) + ["v0.5.7 priority correction: Topdeck moved behind token-resource primary"]

    # Baylen-style extra guard: non-Dragon token resource decks should beat Dragon Copy if Dragon evidence is weak.
    if token_density >= 35 and role_counts.get("token_maker", 0) >= 25 and role_counts.get("dragon_typal", 0) < 8 and "Token Resource Engine" in corrected and "Dragon Copy / Token-Copy Value" in corrected:
        if corrected["Token Resource Engine"].get("score", 0) >= corrected["Dragon Copy / Token-Copy Value"].get("score", 0) * 0.55:
            corrected["Token Resource Engine"]["score"] = max(corrected["Token Resource Engine"]["score"], corrected["Dragon Copy / Token-Copy Value"]["score"] + 15)
            corrected["Token Resource Engine"]["evidence"] = corrected["Token Resource Engine"].get("evidence", []) + ["v0.5.7 priority correction: non-Dragon token-resource density preferred over Dragon Copy"]
            corrected["Dragon Copy / Token-Copy Value"]["score"] = int(corrected["Dragon Copy / Token-Copy Value"]["score"] * 0.45)
            corrected["Dragon Copy / Token-Copy Value"]["evidence"] = corrected["Dragon Copy / Token-Copy Value"].get("evidence", []) + ["v0.5.7 priority correction: Dragon Copy moved behind non-Dragon token-resource primary"]

    # Animar-style: commander creature-cost engine should beat generic permanent/topdeck value when close.
    if commander_has_any_tag(commander_tags, {"creature_cost_reduction", "creature_cast_trigger", "creature_combo_value", "cost_reducer"}) and creature_density >= 12 and creature_score >= topdeck_score * 0.70:
        corrected["Creature Cost-Reduction / Creature Combo Value"]["score"] = max(creature_score, corrected.get("Topdeck / Permanent-Type Value", {}).get("score", topdeck_score) + 12)
        corrected["Creature Cost-Reduction / Creature Combo Value"]["evidence"] = corrected["Creature Cost-Reduction / Creature Combo Value"].get("evidence", []) + ["v0.5.7 priority correction: commander creature-cost/combo engine preferred over generic Topdeck value"]
        corrected["Topdeck / Permanent-Type Value"]["score"] = int(corrected["Topdeck / Permanent-Type Value"]["score"] * 0.82)
        corrected["Topdeck / Permanent-Type Value"]["evidence"] = corrected["Topdeck / Permanent-Type Value"].get("evidence", []) + ["v0.5.7 priority correction: Topdeck moved behind creature-cost primary"]

    # Agatha-style: activated/counter/power package should beat generic permanent/topdeck value when close.
    if commander_has_any_tag(commander_tags, {"activated_ability_synergy", "mana_sink", "power_matters"}) and agatha_density >= 35:
        best_agatha_name, best_agatha_score = max(
            [
                ("+1/+1 Counters", counter_score),
                ("Activated Abilities", activated_score),
                ("Voltron", voltron_score),
            ],
            key=lambda item: item[1],
        )
        if best_agatha_score >= topdeck_score * 0.70 and best_agatha_name in corrected:
            corrected[best_agatha_name]["score"] = max(best_agatha_score, corrected.get("Topdeck / Permanent-Type Value", {}).get("score", topdeck_score) + 12)
            corrected[best_agatha_name]["evidence"] = corrected[best_agatha_name].get("evidence", []) + ["v0.5.7 priority correction: commander activated/counter/power engine preferred over generic Topdeck value"]
            corrected["Topdeck / Permanent-Type Value"]["score"] = int(corrected["Topdeck / Permanent-Type Value"]["score"] * 0.82)
            corrected["Topdeck / Permanent-Type Value"]["evidence"] = corrected["Topdeck / Permanent-Type Value"].get("evidence", []) + ["v0.5.7 priority correction: Topdeck moved behind activated/counter primary"]

    return corrected


def get_strategy_confidence(score, top_score, anchor_hits=0, commander_anchor_hits=0):
    if score <= 0:
        return "None"
    if anchor_hits == 0 and commander_anchor_hits == 0:
        if score >= 90:
            return "Medium"
        if score >= 35:
            return "Low"
        return "Very Low"
    if score >= 160 and (anchor_hits >= 8 or commander_anchor_hits > 0):
        return "High"
    if score >= 80 and (anchor_hits >= 4 or commander_anchor_hits > 0):
        return "Medium"
    if score >= 30:
        return "Low"
    return "Very Low"


def get_strategy_confidence_warning(primary_strategy, secondary_strategy, primary_data, secondary_data, role_counts):
    warnings = []
    generic_total = sum(role_counts.get(tag, 0) for tag in ["ramp", "card_draw", "card_advantage", "token_maker", "combat_synergy", "synergy_piece", "combo_piece_possible"])
    anchor_hits = primary_data.get("anchor_hits", 0)
    commander_anchor_hits = primary_data.get("commander_anchor_hits", 0)
    secondary_score = secondary_data.get("score", 0) if isinstance(secondary_data, dict) else 0
    primary_score = primary_data.get("score", 0) if isinstance(primary_data, dict) else 0
    if primary_score and secondary_score and abs(primary_score - secondary_score) <= max(8, primary_score * 0.04):
        warnings.append("Primary and secondary strategy scores are very close; ask the pilot to confirm the intended primary plan before making aggressive cuts.")
    if primary_data.get("score", 0) >= 150 and commander_anchor_hits == 0 and anchor_hits < 6:
        warnings.append("Primary confidence may be inflated because commander anchor support is low.")
    if generic_total >= 60:
        warnings.append("Strategy confidence may be inflated by broad ramp/card-draw/token/combat/value tags.")
    if primary_strategy in {"Go-Wide Combat", "+1/+1 Counters"} and role_counts.get("token_maker", 0) >= 25:
        warnings.append("High token density detected; consider Tokens or Token Resource Engine as a primary strategy if commander text supports it.")
    if role_counts.get("eldrazi_synergy", 0) >= 8 or role_counts.get("big_mana_payoff", 0) >= 8:
        warnings.append("Eldrazi/colorless big-mana density detected; avoid over-reading this deck as generic combat.")
    if primary_strategy == "Topdeck / Permanent-Type Value" and primary_data.get("commander_anchor_hits", 0) == 0:
        warnings.append("Topdeck/Permanent-Type Value is primary without commander anchor support; review whether it is a support package instead.")
    if primary_strategy == "Topdeck / Permanent-Type Value" and get_dragon_copy_density(role_counts) >= 24:
        warnings.append("Dragon copy/token-copy density detected; review whether Topdeck is only a support package.")
    if primary_strategy == "Dragon Copy / Token-Copy Value" and role_counts.get("dragon_typal", 0) < 8 and role_counts.get("dragon_copy_value", 0) == 0:
        warnings.append("Dragon Copy / Token-Copy is primary without enough Dragon evidence; review as likely scoring overreach.")
    if primary_strategy == "Creature Cost-Reduction / Creature Combo Value" and get_cascade_big_mana_density(role_counts) >= 70:
        warnings.append("Creature Cost-Reduction may be over-reading a cascade/big-mana deck; review Cascade / Big Mana Value.")
    if primary_strategy == "Creature Cost-Reduction / Creature Combo Value" and get_amass_spellslinger_density(role_counts) >= 55:
        warnings.append("Creature Cost-Reduction may be over-reading a spellslinger/amass deck; review Spellslinger / Amass Army.")
    if primary_strategy == "Topdeck / Permanent-Type Value" and get_graveyard_self_mill_density(role_counts) >= 90:
        warnings.append("Topdeck may be over-reading a graveyard/self-mill deck; review Graveyard Self-Mill / Recursion.")
    if primary_strategy == "Topdeck / Permanent-Type Value" and get_blink_flicker_density(role_counts) >= 18:
        warnings.append("Topdeck may be over-reading a blink/flicker deck; review Blink/Flicker / ETB Value.")
    if primary_strategy in {"+1/+1 Counters", "Control"} and get_toughness_defender_density(role_counts) >= 45:
        warnings.append("Toughness/defender density detected; review Toughness Matters / Defender before making cuts.")
    if primary_strategy in {"Graveyard Self-Mill / Recursion", "Reanimator"} and get_wheel_draw_punisher_density(role_counts) >= 30:
        warnings.append("Wheel/draw-punisher density detected; review Wheels / Draw-Punisher / Group Slug before making cuts.")
    if get_commander_landfall_package_density(role_counts) >= 24:
        warnings.append("Commander-created landfall/artifact-token package detected; do not dismiss landfall support solely because deckwide density is modest.")
    return warnings


def dampen_display_confidence(confidence, warnings):
    if not warnings:
        return confidence
    if confidence == "High":
        return "Medium-High"
    if confidence == "Medium":
        return "Medium-Low"
    return confidence


def choose_primary_secondary_strategy(archetype_scores):
    ordered = sorted([(k,v) for k,v in archetype_scores.items() if not str(k).startswith("__")], key=lambda item: item[1]["score"], reverse=True)
    primary_name, primary_data = ordered[0] if ordered else ("Unclear", {"score": 0, "anchor_hits": 0, "commander_anchor_hits": 0})
    secondary_name, secondary_data = ("Unclear", {"score": 0, "anchor_hits": 0, "commander_anchor_hits": 0})

    for name, data in ordered[1:]:
        has_real_evidence = data.get("anchor_hits", 0) >= 2 or data.get("commander_anchor_hits", 0) > 0
        close_enough = data["score"] >= max(35, primary_data["score"] * 0.45)
        if has_real_evidence and close_enough:
            secondary_name, secondary_data = name, data
            break

    return primary_name, primary_data, secondary_name, secondary_data, ordered


def get_commander_game_plan(commander_cards, primary_strategy, secondary_strategy):
    if not commander_cards:
        return "Commander not found or unclear."

    plan_fragments = []
    for commander in commander_cards:
        commander_name = commander.get("name", "Unknown Commander")
        tags = set(infer_card_role_tags(commander, commander_cards))
        type_line = commander.get("type_line", "")

        if tags:
            plan_fragments.append(f"{commander_name} appears to provide/support: {', '.join(sorted(tags))}.")
        else:
            plan_fragments.append(f"{commander_name} has no clear v0.4 role tags yet; review commander text manually.")

        if "Creature" in type_line:
            plan_fragments.append(f"{commander_name} is a creature commander, so protection/ramp/combat or engine support may matter.")

    plan_fragments.append(f"Current strategy read points toward {primary_strategy} with {secondary_strategy} as secondary support.")
    return " ".join(plan_fragments)


def get_commander_support_level(card_plan_fit_buckets=None, role_counts=None, total_nonland_count=0, primary_overlap_count=0):
    if card_plan_fit_buckets is not None:
        direct_support_count = len(card_plan_fit_buckets.get("Commander Support", []))
        enabler_count = len(card_plan_fit_buckets.get("Commander Enabler", []))
        primary_count = len(card_plan_fit_buckets.get("Primary Plan Support", []))
        context_count = len(card_plan_fit_buckets.get("High Synergy / Low Raw Power", [])) + len(card_plan_fit_buckets.get("Weak Alone / Strong in Context", []))
        weighted_support_count = direct_support_count + (enabler_count * 0.35) + (min(primary_count, 25) * 0.12) + (context_count * 0.2)
        if direct_support_count >= 8 or weighted_support_count >= 12:
            return "High"
        if direct_support_count >= 4 or weighted_support_count >= 6:
            return "Moderate"
        if direct_support_count >= 2 or weighted_support_count >= 3:
            return "Low"
        return "Unclear"

    commander_support_count = role_counts.get("commander_synergy_possible", 0) if role_counts else 0
    if total_nonland_count <= 0:
        return "Unclear"
    ratio = commander_support_count / max(1, total_nonland_count)
    if commander_support_count >= 18 or ratio >= 0.30:
        return "High"
    if commander_support_count >= 10 or ratio >= 0.18:
        return "Moderate"
    if commander_support_count >= 4 or ratio >= 0.08:
        return "Low"
    return "Unclear"


def get_commander_support_reason(card_plan_fit_buckets):
    direct_support_count = len(card_plan_fit_buckets.get("Commander Support", []))
    enabler_count = len(card_plan_fit_buckets.get("Commander Enabler", []))
    primary_count = len(card_plan_fit_buckets.get("Primary Plan Support", []))
    secondary_count = len(card_plan_fit_buckets.get("Secondary Plan Support", []))
    shell_count = len(card_plan_fit_buckets.get("Shell Support", []))
    return (
        f"{direct_support_count} direct commander support card(s), "
        f"{enabler_count} commander enabler(s), "
        f"{shell_count} shell support card(s), "
        f"{primary_count} primary-plan support card(s), "
        f"{secondary_count} secondary-plan support card(s)."
    )

def get_core_synergy_packages(role_counts):
    package_definitions = {
        "Sacrifice Engine": ["sacrifice_outlet", "free_sacrifice_outlet", "sacrifice_payoff", "death_trigger_payoff"],
        "Token Production": ["token_maker"],
        "Artifact Payoffs": ["artifact_payoff"],
        "Damage / Drain Pressure": ["damage_payoff", "sacrifice_payoff", "win_condition"],
        "Graveyard / Recursion": ["recursion", "graveyard_enabler", "discard_outlet"],
        "Spell Engine": ["spell_payoff", "card_draw", "card_advantage", "cost_reducer", "counterspell"],
        "Counter / Go-Tall Engine": ["counter_synergy", "go_tall_support", "equipment_synergy", "aura_synergy"],
        "Combat Pressure": ["combat_synergy", "attack_trigger_payoff", "extra_combat", "anthem", "go_tall_support"],
        "Protection / Resilience": ["protection", "recursion"],
        "Interaction": ["targeted_removal", "board_wipe", "counterspell"],
        "Combo-Adjacent Pieces": ["combo_piece_possible", "synergy_piece", "tutor"],
        "Typal / Kindred": ["tribal_payoff", "tribal_dependency", "anthem"],
        "Ramp / Mana Development": ["ramp", "mana_doubler", "cost_reducer"],
        "Adventure / Modal Value": ["adventure_synergy", "modal_spell_synergy", "creature_spell_hybrid"],
        "Activated Ability Engine": ["activated_ability_synergy", "mana_sink", "power_matters"],
        "Artifact Token Economy": ["clue_synergy", "food_synergy", "treasure_synergy", "artifact_token_synergy", "investigate_synergy"],
        "Eldrazi / Colorless Big Mana": ["eldrazi_synergy", "colorless_matters", "big_mana_payoff", "cast_copy_synergy", "high_mv_payoff"],
        "Historic / Doctor / Time": ["historic_synergy", "legendary_synergy", "doctor_synergy", "time_travel_synergy", "suspend_synergy", "cascade_synergy"],
        "Token Resource Engine": ["token_resource_engine", "tap_token_value", "go_wide_token_engine", "rabbit_typal"],
        "Copy / Clone Value": ["copy_clone_value", "cast_copy_synergy"],
        "Turbo Combo / Fast Tutor Chain": ["turbo_combo", "fast_mana", "ritual", "efficient_tutor", "combo_tutor", "tutor_chain", "combo_protection"],
        "Dragonstorm / Tiamat Tutor Chain": ["dragonstorm_combo", "tutor_chain", "combo_tutor", "dragon_typal", "fast_mana", "ritual", "combo_protection"],
        "Dragon Copy / Token-Copy Value": ["dragon_copy_value", "token_copy_value", "copy_clone_value", "dragon_typal", "token_maker", "tribal_payoff"],
        "Legends Matter / Legendary Cascade": ["legendary_synergy", "historic_synergy", "legendary_cascade", "five_color_value", "cast_trigger"],
        "Elf Typal / Token Lifedrain": ["elf_typal", "tribal_payoff", "tribal_anthem", "token_maker", "lifedrain_payoff"],
        "Artifact/Treasure Tutor Chain": ["artifact_treasure_tutor_chain", "treasure_tutor_chain", "treasure_synergy", "artifact_token_synergy", "tutor_chain"],
        "Ramp-Control / Big Mana Value": ["ramp", "board_wipe", "mass_removal", "targeted_removal", "big_mana_payoff", "high_mv_payoff"],
        "Treasure / Artifact Token Engine": ["treasure_synergy", "artifact_token_synergy", "artifact_payoff", "artifact_sacrifice"],
        "Topdeck / Permanent-Type Value": ["topdeck_manipulation", "permanent_type_value", "permanent_density", "card_selection"],
        "Cascade / Big Mana Value": ["cascade_synergy", "alternate_cost_interaction", "cost_cheat", "free_casting", "high_mv_payoff", "big_mana_payoff"],
        "Suspend / Big Spell Cheat": ["suspend_synergy", "time_travel_synergy", "suspend_big_spell", "counter_synergy", "cost_cheat", "free_casting"],
        "Graveyard Self-Mill / Recursion": ["graveyard_enabler", "self_mill", "recursion", "sacrifice_outlet"],
        "Blink/Flicker / ETB Value": ["blink_flicker", "exile_return", "etb_value", "ltb_value", "copy_clone_value"],
        "Spellslinger / Amass Army": ["amass_synergy", "army_typal", "noncreature_spell_payoff", "spell_payoff", "token_maker"],
        "Toughness Matters / Defender": ["defender_payoff", "toughness_payoff", "toughness_combat", "wall_typal", "high_toughness"],
        "Wheels / Draw-Punisher / Group Slug": ["wheel_effect", "forced_draw", "draw_punisher", "opponent_draw_payoff", "group_slug"],
        "Commander-Created Landfall / Artifact Token Engine": ["commander_created_package", "rock_token_synergy", "landfall", "land_token", "artifact_token_synergy", "artifact_sacrifice"],
        "Creature Cost-Reduction / Creature Combo Value": ["creature_cost_reduction", "creature_cast_trigger", "creature_combo_value", "bounce_engine", "self_bounce"],
    }
    packages = []
    for package_name, tags in package_definitions.items():
        count = sum(role_counts.get(tag, 0) for tag in tags)
        if count > 0:
            packages.append((package_name, count, tags))
    packages.sort(key=lambda item: item[1], reverse=True)
    return packages


def get_primary_secondary_tag_sets(primary_strategy, secondary_strategy):
    primary_tags = set(ARCHETYPE_DEFINITIONS.get(primary_strategy, {}).get("core_tags", {}).keys())
    secondary_tags = set(ARCHETYPE_DEFINITIONS.get(secondary_strategy, {}).get("core_tags", {}).keys())
    return primary_tags, secondary_tags


def is_direct_commander_support(card, tags, commander_cards):
    if not card:
        return False

    tags = set(tags)

    for commander in commander_cards or []:
        commander_text = normalize_text(commander.get("type_line", "") + " " + get_full_oracle_text(commander))
        commander_type = commander.get("type_line", "").lower()
        commander_mv = commander.get("cmc", 0)

        # Generic ramp/protection is handled as Commander Enabler in v0.4.5,
        # not direct commander support.
        if ("artifact" in commander_text or "treasure" in commander_text or "clue" in commander_text or "food" in commander_text) and tags.intersection({"artifact_payoff", "sacrifice_outlet", "clue_synergy", "food_synergy", "treasure_synergy", "artifact_token_synergy", "investigate_synergy"}):
            return True
        if ("sacrifice" in commander_text or "dies" in commander_text or "graveyard" in commander_text) and tags.intersection({"sacrifice_outlet", "sacrifice_payoff", "death_trigger_payoff", "recursion", "graveyard_enabler"}):
            return True
        if ("instant" in commander_text or "sorcery" in commander_text or "spell" in commander_text or "cast" in commander_text) and tags.intersection({"spell_payoff", "noncreature_spell_payoff", "cost_reducer", "cast_trigger", "cast_copy_synergy", "cascade_synergy", "suspend_synergy", "suspend_big_spell", "adventure_synergy", "modal_spell_synergy", "amass_synergy", "army_typal"}):
            return True
        if ("attack" in commander_text or "combat" in commander_text) and tags.intersection({"extra_combat", "attack_trigger_payoff", "combat_synergy", "go_tall_support", "equipment_synergy", "aura_synergy"}):
            return True
        if ("counter" in commander_text or "+1/+1" in commander_text or "base power and toughness" in commander_text or "activated ability" in commander_text or "power" in commander_text) and tags.intersection({"counter_synergy", "go_tall_support", "combat_synergy", "equipment_synergy", "aura_synergy", "activated_ability_synergy", "mana_sink", "power_matters"}):
            return True
        if ("dragon" in commander_text or "dragon" in commander_type or "eldrazi" in commander_text or "eldrazi" in commander_type or "rabbit" in commander_text or "rabbit" in commander_type or "doctor" in commander_text or "doctor" in commander_type or "time lord" in commander_text or "time lord" in commander_type) and tags.intersection({"tribal_payoff", "tribal_dependency", "token_maker", "synergy_piece", "eldrazi_synergy", "rabbit_typal", "doctor_synergy", "time_travel_synergy", "dragon_typal", "dragon_copy_value", "token_copy_value", "copy_clone_value"}):
            return True
        if ("copy" in commander_text or "when you cast" in commander_text or "whenever you cast" in commander_text) and tags.intersection({"cast_copy_synergy", "cast_trigger", "eldrazi_synergy", "big_mana_payoff", "copy_clone_value", "token_copy_value", "dragon_copy_value"}):
            return True
        if ("tap two untapped tokens" in commander_text or "tap three untapped tokens" in commander_text) and tags.intersection({"token_resource_engine", "tap_token_value", "go_wide_token_engine", "token_maker"}):
            return True
        if ("land enters" in commander_text or "landfall" in commander_text or "rock artifact token" in commander_text or "create a colorless rock" in commander_text) and tags.intersection({"landfall", "landfall_payoff", "extra_land_play", "lands_matter", "land_token", "rock_token_synergy", "artifact_token_synergy", "artifact_payoff", "artifact_sacrifice", "sacrifice_outlet", "token_maker"}):
            return True
        if ("toughness" in commander_text or "defender" in commander_text or "wall" in commander_text) and tags.intersection({"defender_payoff", "toughness_payoff", "toughness_combat", "wall_typal", "high_toughness"}):
            return True
        if ("draw" in commander_text and ("opponent" in commander_text or "each player" in commander_text)) and tags.intersection({"wheel_effect", "forced_draw", "draw_punisher", "opponent_draw_payoff", "group_slug"}):
            return True
        if "token" in commander_text and ("rabbit" in commander_text or "tap two untapped tokens" in commander_text or "tap three untapped tokens" in commander_text) and tags.intersection({"token_resource_engine", "tap_token_value", "go_wide_token_engine", "token_maker", "rabbit_typal"}):
            return True
        if ("exile" in commander_text and "return" in commander_text) and tags.intersection({"blink_flicker", "exile_return", "etb_value", "ltb_value"}):
            return True
        if ("amass" in commander_text or "army" in commander_text or "orc" in commander_text) and tags.intersection({"amass_synergy", "army_typal", "spell_payoff", "noncreature_spell_payoff", "token_maker", "counter_synergy"}):
            return True
        if "whenever" in commander_text and tags.intersection({"spell_payoff", "noncreature_spell_payoff", "counter_synergy", "cast_trigger", "creature_cast_trigger", "etb_value"}):
            return True

    return False


def is_commander_enabler(card, tags, commander_cards):
    """Cards that help deploy or protect the commander, but do not directly match the commander's engine text."""
    if not card:
        return False
    tags = set(tags)
    for commander in commander_cards or []:
        commander_type = commander.get("type_line", "").lower()
        commander_mv = commander.get("cmc", 0)
        if commander_mv >= 6 and ("ramp" in tags or "cost_reducer" in tags):
            return True
        if "creature" in commander_type and "protection" in tags:
            return True
    return False


def is_shell_support(card, tags, primary_strategy, secondary_strategy):
    """Broader support for the shell that should not be overstated as direct commander support."""
    if not card:
        return False
    tags = set(tags)
    shell_tags = {
        "topdeck_manipulation", "permanent_type_value", "permanent_density",
        "creature_cost_reduction", "creature_combo_value", "bounce_engine", "self_bounce",
        "historic_synergy", "legendary_synergy", "copy_clone_value",
        "dragon_typal", "dragon_copy_value", "token_copy_value",
        "blink_flicker", "etb_value", "ltb_value", "exile_return",
        "amass_synergy", "army_typal", "noncreature_spell_payoff", "suspend_big_spell",
        "defender_payoff", "toughness_payoff", "toughness_combat", "wall_typal", "high_toughness",
        "wheel_effect", "forced_draw", "draw_punisher", "opponent_draw_payoff", "group_slug",
        "lifegain_payoff", "lifedrain_payoff", "life_total_manipulation",
        "tribal_anthem", "tribal_protection", "combat_reset", "attack_safety", "mass_blink",
        "landfall", "landfall_payoff", "extra_land_play", "lands_matter", "land_token", "commander_created_package", "rock_token_synergy", "artifact_sacrifice",
        "card_selection", "card_advantage", "cost_cheat", "free_casting",
    }
    if tags.intersection(shell_tags):
        return True
    if primary_strategy == "Creature Cost-Reduction / Creature Combo Value" and tags.intersection({"tutor", "cost_reducer", "card_advantage", "protection", "free_interaction", "stack_interaction"}):
        return True
    if primary_strategy == "Topdeck / Permanent-Type Value" and tags.intersection({"topdeck_manipulation", "permanent_type_value", "permanent_density", "card_selection", "card_advantage", "legendary_synergy", "historic_synergy"}):
        return True
    return False




def is_strong_direct_commander_support(card, tags, commander_cards):
    """Return True only for commander support that should be displayed as direct support.

    This separates real commander-text/commander-plan support from generic shell support
    such as normal ramp, card draw, removal, lands, combat bodies, or incidental creature types.
    """
    if not card:
        return False
    tags = set(tags)
    generic_only = {
        "mana_source", "ramp", "mana_rock", "mana_dork", "mana_fixing", "utility_land",
        "card_draw", "card_advantage", "card_selection", "targeted_removal", "board_wipe",
        "mass_removal", "counterspell", "protection", "shell_support", "macro_archetype_support",
        "creature_type_present", "incidental_creature_type", "attack_body", "sacrifice_body",
        "activated_ability_source", "utility_activated_ability", "mana_ability_only",
        "commander_synergy_possible", "typal_support"
    }
    meaningful_tags = tags - generic_only
    if not meaningful_tags:
        return False

    strong_tags = {
        "sacrifice_outlet", "sacrifice_payoff", "death_trigger_payoff", "recursion", "graveyard_enabler",
        "artifact_payoff", "artifact_token_synergy", "artifact_sacrifice", "treasure_synergy", "clue_synergy", "food_synergy",
        "spell_payoff", "noncreature_spell_payoff", "cast_trigger", "cast_copy_synergy", "cascade_synergy", "suspend_synergy",
        "attack_trigger_payoff", "extra_combat", "go_tall_support", "equipment_synergy", "aura_synergy",
        "counter_synergy", "activated_ability_synergy", "activated_ability_payoff", "activated_ability_cost_reduction",
        "mana_sink", "power_matters", "token_resource_engine", "tap_token_value", "go_wide_token_engine",
        "blink_flicker", "exile_return", "etb_value", "ltb_value", "mass_blink",
        "wheel_effect", "forced_draw", "draw_punisher", "opponent_draw_payoff", "group_slug",
        "landfall", "landfall_payoff", "extra_land_play", "lands_matter", "rock_token_synergy", "commander_created_package",
        "legendary_cascade", "historic_synergy", "legendary_synergy", "five_color_value",
        "dragon_copy_value", "dragon_typal", "token_copy_value", "copy_clone_value",
        "defender_payoff", "toughness_payoff", "toughness_combat", "wall_typal",
        "amass_synergy", "army_typal", "rabbit_typal", "tribal_payoff", "typal_payoff", "tribal_anthem"
    }
    return bool(meaningful_tags.intersection(strong_tags))

def classify_card_plan_fit(card_name, card, tags, primary_strategy, secondary_strategy, primary_tags, secondary_tags, is_command_zone_card, commander_cards=None):
    tags = set(tags)

    if is_command_zone_card:
        return "Commander Support", "Command-zone card; evaluate as part of the commander game plan."

    if "manual_review" in tags:
        return "Manual Review", "Missing or unclear Scryfall data."

    direct_commander_support = is_direct_commander_support(card, tags, commander_cards)
    commander_enabler = is_commander_enabler(card, tags, commander_cards)
    shell_support = is_shell_support(card, tags, primary_strategy, secondary_strategy)

    # v0.5.7: lands and pure mana-only sources are mana base, not proof of a strategy.
    if card and has_type_on_any_face(card, "Land"):
        return "Generic Utility", "Mana base card; not counted as primary strategy support unless manually reviewed."

    if "mana_source" in tags and not (tags - {"mana_source", "ramp", "commander_synergy_possible"}):
        return "Generic Utility", "Mana source; useful but not strategy-defining by itself."

    # v0.5.7 priority: true commander-text support comes before plan buckets,
    # but generic shell/utility cards should not be overstated as direct commander support.
    if direct_commander_support and is_strong_direct_commander_support(card, tags, commander_cards):
        return "Commander Support", "Directly supports the commander's text or commander-defined game plan."

    if direct_commander_support:
        return "Shell Support", "Touches the commander plan, but appears to be broader shell support rather than direct commander-text support."

    if tags.intersection(primary_tags):
        return "Primary Plan Support", f"Supports the likely primary strategy: {primary_strategy}."

    if secondary_strategy != "Unclear" and tags.intersection(secondary_tags):
        return "Secondary Plan Support", f"Supports the likely secondary strategy: {secondary_strategy}."

    if shell_support:
        return "Shell Support", "Supports the broader deck shell or primary value engine, but is not direct commander-text support."

    if commander_enabler:
        return "Commander Enabler", "Helps cast, protect, or enable an expensive/creature commander but is not direct engine support."

    if tags.intersection(GENERIC_UTILITY_TAGS):
        return "Generic Utility", "Useful interaction, mana, protection, or card flow even if not strategy-defining."

    if tags.intersection(HIGH_SYNERGY_LOW_RAW_POWER_TAGS):
        return "High Synergy / Low Raw Power", "Narrow or low-raw-power card that may matter because of specific synergy tags."

    if tags.intersection(LOW_RAW_POWER_CONTEXT_TAGS):
        return "Weak Alone / Strong in Context", "May look modest by raw power, but has tags that can support an engine."

    if not tags:
        if card and has_type_on_any_face(card, "Land"):
            return "Generic Utility", "Land/mana base card."
        if card and has_type_on_any_face(card, "Creature"):
            return "Manual Review", "Creature has no clear functional role tags; review stats, type, keywords, and commander fit."
        return "Possible Off-Plan", "No clear connection to commander, primary plan, secondary plan, or generic utility was detected."

    return "Possible Off-Plan", "Has role tags, but they do not clearly align with the commander or likely strategy read."


def build_card_plan_fit(unique_cards, scryfall_lookup, card_role_tags_by_card, commander_name_set, primary_strategy, secondary_strategy, commander_cards=None):
    primary_tags, secondary_tags = get_primary_secondary_tag_sets(primary_strategy, secondary_strategy)
    buckets = {
        "Commander Support": [],
        "Commander Enabler": [],
        "Shell Support": [],
        "Primary Plan Support": [],
        "Secondary Plan Support": [],
        "Generic Utility": [],
        "Possible Off-Plan": [],
        "Weak Alone / Strong in Context": [],
        "High Synergy / Low Raw Power": [],
        "Manual Review": [],
    }
    for card_name in sorted(unique_cards):
        card = scryfall_lookup.get(card_name.lower())
        tags = set(card_role_tags_by_card.get(card_name, []))
        bucket, reason = classify_card_plan_fit(card_name, card, tags, primary_strategy, secondary_strategy, primary_tags, secondary_tags, card_name in commander_name_set, commander_cards)
        buckets[bucket].append((card_name, reason, sorted(tags)))
    return buckets


def pick_strong_synergy_cards(card_plan_fit_buckets, limit=12):
    strong = []
    for bucket_name in ["Commander Support", "Commander Enabler", "Shell Support", "Primary Plan Support", "Secondary Plan Support", "Weak Alone / Strong in Context", "High Synergy / Low Raw Power"]:
        for card_name, reason, tags in card_plan_fit_buckets.get(bucket_name, []):
            if len(strong) >= limit:
                return strong
            relevant_tags = [tag for tag in tags if tag not in {"commander_synergy_possible"}]
            tag_text = ", ".join(relevant_tags[:5]) if relevant_tags else "commander support"
            strong.append((card_name, f"{reason} Tags: {tag_text}"))
    return strong


def pick_possible_off_plan_cards(card_plan_fit_buckets, limit=12):
    possible = []
    for card_name, reason, tags in card_plan_fit_buckets.get("Possible Off-Plan", []):
        if len(possible) >= limit:
            break
        tag_text = ", ".join(tags) if tags else "no clear role tags"
        possible.append((card_name, f"{reason} Tags: {tag_text}"))
    return possible


def get_optional_cut_target(cut_strictness):
    if cut_strictness == "brutal":
        return max(15, OPTIONAL_CUT_TARGET)
    if cut_strictness == "strict":
        return max(10, OPTIONAL_CUT_TARGET)
    if cut_strictness == "custom":
        return OPTIONAL_CUT_TARGET
    if cut_strictness == "normal":
        return max(5, OPTIONAL_CUT_TARGET)
    return OPTIONAL_CUT_TARGET


def get_plan_fit_bucket_for_card(card_name, card_plan_fit_buckets):
    for bucket_name, entries in card_plan_fit_buckets.items():
        for entry_card_name, reason, tags in entries:
            if entry_card_name == card_name:
                return bucket_name, reason
    return "Manual Review", "Card was not found in Card Plan Fit buckets."


def is_land_card(card):
    if not card:
        return False
    return has_type_on_any_face(card, "Land")


def get_replaceability_category(score, reasons, bucket, tags):
    tags = set(tags)
    reason_text = " ".join(reasons).lower()
    if "manual review" in bucket.lower():
        return "Manual Review / Needs Context"
    if "tribal_dependency" in tags and "unsupported tribal" in reason_text:
        return "Unsupported Tribal / Synergy Dependency"
    if "generic utility" in bucket.lower():
        return "Playable But Replaceable Utility"
    if "possible off-plan" in bucket.lower():
        return "Good Card, Wrong Shell" if tags.intersection(GENERIC_UTILITY_TAGS) else "Wrong Card for This Deck"
    if "high mana value" in reason_text:
        return "Too Expensive for Effect"
    if "no clear role tags" in reason_text or "no clear functional role" in reason_text:
        return "Low Synergy"
    if "duplicate role pressure" in reason_text:
        return "Redundant"
    if score >= 40:
        return "Replaceable but Playable"
    return "Low Synergy"


def get_replaceability_score(card_name, card, tags, bucket, bucket_reason, primary_tags, secondary_tags, role_tag_counts, tribal_support_flags, average_nonland_mana_value):
    tags = set(tags)
    reasons = []
    score = 0
    if not card:
        return 999, ["Unknown/custom card; manual review needed before deciding whether it is replaceable."], "Manual Review"
    if is_land_card(card):
        return -999, ["Land/mana base card; do not cut unless land count or fixing is being intentionally adjusted."], "Protected"

    representative_mv = get_representative_nonland_mana_value(card) or 0

    if bucket == "Possible Off-Plan":
        score += 35
        reasons.append("No clear connection to commander, primary plan, secondary plan, or generic utility was detected.")
    elif bucket == "Manual Review":
        score += 10
        reasons.append("Needs manual review; uncertainty alone is not enough to make it a cut.")
    elif bucket == "Generic Utility":
        score += 12
        reasons.append("Generic utility card; playable, but may be replaceable if it does not advance the main engine.")
    elif bucket == "Shell Support":
        score -= 14
        reasons.append("Supports the broader shell or value engine, but is not direct commander support.")
    elif bucket == "Commander Enabler":
        score -= 8
        reasons.append("Helps enable the commander, but is not direct engine support.")
    elif bucket in {"Commander Support", "Primary Plan Support"}:
        score -= 35
        reasons.append("Strongly aligned with commander or primary plan; lower replaceability.")
    elif bucket == "Secondary Plan Support":
        score -= 10
        reasons.append("Supports the secondary plan; only cut if that package is being reduced.")
    elif bucket == "High Synergy / Low Raw Power":
        score -= 25
        reasons.append("Looks modest by raw power, but has high-synergy tags.")
    elif bucket == "Weak Alone / Strong in Context":
        score -= 15
        reasons.append("May look weak alone but can belong if the deck reliably supports its role.")

    if not tags:
        score += 10
        reasons.append("No clear role tags detected; review before cutting instead of assuming it is bad.")
    if tags == {"commander_synergy_possible"}:
        score += 20
        reasons.append("Only commander_synergy_possible was detected; no concrete functional role tag was found.")
    if tags.intersection(primary_tags):
        score -= 25
        reasons.append("Matches primary strategy tags.")
    if tags.intersection(secondary_tags):
        score -= 10
        reasons.append("Matches secondary strategy tags.")
    if tags.intersection({"win_condition", "mana_doubler", "tutor", "board_wipe", "high_mv_payoff", "big_mana_payoff", "mass_removal", "cost_cheat", "free_casting"}):
        score -= 12
        reasons.append("Potential key payoff, finisher, tutor, or board reset.")
    if tags.intersection({"sacrifice_outlet", "free_sacrifice_outlet", "recursion", "graveyard_enabler", "artifact_payoff", "damage_payoff", "sacrifice_payoff", "counter_synergy", "spell_payoff", "extra_combat"}):
        score -= 10
        reasons.append("Has synergy-engine tags that may be important in context.")

    if representative_mv >= 7 and not tags.intersection({"win_condition", "board_wipe", "mana_doubler", "card_draw", "card_advantage", "recursion", "protection", "synergy_piece", "combo_piece_possible", "extra_combat", "high_mv_payoff", "big_mana_payoff", "eldrazi_synergy", "cast_trigger", "cast_copy_synergy"}):
        score += 25
        reasons.append(f"High mana value ({representative_mv}) without a clear payoff/protection/card-advantage tag.")
    elif representative_mv >= 6 and bucket in {"Possible Off-Plan", "Manual Review", "Generic Utility"}:
        score += 12
        reasons.append(f"High mana value ({representative_mv}) increases replaceability if it is not central to the plan.")

    if "tribal_dependency" in tags:
        unsupported_flags = [flag for flag in tribal_support_flags if flag["card_name"] == card_name]
        if unsupported_flags:
            flag = unsupported_flags[0]
            score += 30
            reasons.append(f"Unsupported tribal dependency: references {flag['referenced_type']}s but only {flag['support_count']} detected.")
        else:
            reasons.append("Tribal dependency should be reviewed against actual creature-type density.")

    for tag in ["ramp", "token_maker", "card_draw", "targeted_removal", "combat_synergy", "synergy_piece", "combo_piece_possible"]:
        if tag in tags and role_tag_counts.get(tag, 0) >= 15 and bucket not in {"Commander Support", "Primary Plan Support"}:
            score += 6
            reasons.append(f"Duplicate role pressure: deck already has many {tag} cards.")

    if bucket == "Possible Off-Plan" and not tags.intersection(GENERIC_UTILITY_TAGS | HIGH_SYNERGY_LOW_RAW_POWER_TAGS):
        score += 10
        reasons.append("Low detected board impact or narrow role for this shell.")

    category = get_replaceability_category(score, reasons, bucket, tags)
    return score, reasons, category


def build_cut_pressure_review(cards, unique_cards, scryfall_lookup, card_role_tags_by_card, card_plan_fit_buckets, commander_name_set, primary_strategy, secondary_strategy, role_tag_counts, tribal_support_flags, average_nonland_mana_value, cut_strictness="normal"):
    required_cuts = max(0, len(cards) - 100)
    optional_cut_target = get_optional_cut_target(cut_strictness)
    primary_tags, secondary_tags = get_primary_secondary_tag_sets(primary_strategy, secondary_strategy)
    candidates = []
    context_dependent = []
    protected = []

    for card_name in sorted(unique_cards):
        if card_name in commander_name_set:
            protected.append((card_name, "Command-zone card; do not treat as a normal cut."))
            continue
        card = scryfall_lookup.get(card_name.lower())
        tags = set(card_role_tags_by_card.get(card_name, []))
        bucket, bucket_reason = get_plan_fit_bucket_for_card(card_name, card_plan_fit_buckets)
        score, reasons, category = get_replaceability_score(
            card_name, card, tags, bucket, bucket_reason, primary_tags, secondary_tags,
            role_tag_counts, tribal_support_flags, average_nonland_mana_value
        )
        if card and is_land_card(card):
            continue

        candidate = {
            "card_name": card_name,
            "score": score,
            "category": category,
            "bucket": bucket,
            "tags": sorted(tags),
            "reasons": reasons,
        }

        if tags.intersection({"tribal_dependency", "sacrifice_outlet", "free_sacrifice_outlet", "recursion", "graveyard_enabler", "artifact_payoff", "damage_payoff", "sacrifice_payoff", "counter_synergy", "spell_payoff", "synergy_piece", "combo_piece_possible"}):
            if bucket in {"Manual Review", "Possible Off-Plan", "High Synergy / Low Raw Power", "Weak Alone / Strong in Context", "Secondary Plan Support"} or "tribal_dependency" in tags:
                context_dependent.append({
                    "card_name": card_name,
                    "questionable": "May look replaceable by generic standards or because its role is narrow/contextual.",
                    "might_belong": "May belong if the deck reliably supports its synergy role: " + (", ".join(sorted(tags)) if tags else "unclear tags"),
                })

        if bucket in {"Commander Support", "Shell Support", "Primary Plan Support", "High Synergy / Low Raw Power", "Weak Alone / Strong in Context"}:
            protected_reason = {
                "Commander Support": "Supports the commander directly.",
                "Shell Support": "Supports the broader shell or value engine.",
                "Primary Plan Support": f"Supports the primary strategy: {primary_strategy}.",
                "High Synergy / Low Raw Power": "Looks low-power by raw standards but carries important synergy tags.",
                "Weak Alone / Strong in Context": "May be weak alone but supports a contextual engine.",
            }.get(bucket, "Supports the deck plan.")
            protected.append((card_name, protected_reason))
        elif tags.intersection({"win_condition", "mana_doubler", "board_wipe", "tutor"}) and bucket != "Possible Off-Plan":
            protected.append((card_name, "Potential key payoff, finisher, tutor, or essential reset."))
        elif tags.intersection({"ramp", "targeted_removal", "counterspell", "protection", "card_draw", "card_advantage"}) and bucket in {"Generic Utility", "Commander Enabler"}:
            protected.append((card_name, "Provides essential utility such as ramp/fixing, interaction, protection, or card flow."))

        if score > 0:
            candidates.append(candidate)

    candidates.sort(key=lambda item: item["score"], reverse=True)
    required_cuts_list = candidates[:required_cuts] if required_cuts > 0 else []

    # v0.5.7 guarantee: if a deck is over 100, the Required Cuts list must reach
    # required_cuts whenever enough noncommander nonland cards exist.
    if required_cuts > len(required_cuts_list):
        already = {item["card_name"] for item in required_cuts_list}
        fallback_pool = []
        for card_name in sorted(unique_cards):
            if card_name in already or card_name in commander_name_set:
                continue
            card = scryfall_lookup.get(card_name.lower())
            if card and is_land_card(card):
                continue
            tags = set(card_role_tags_by_card.get(card_name, []))
            bucket, bucket_reason = get_plan_fit_bucket_for_card(card_name, card_plan_fit_buckets)
            fallback_score = -50
            if bucket in {"Manual Review", "Possible Off-Plan", "Generic Utility"}:
                fallback_score = 5
            if not tags:
                fallback_score += 5
            fallback_pool.append({
                "card_name": card_name,
                "score": fallback_score,
                "category": "Required Cut Fallback",
                "bucket": bucket,
                "tags": sorted(tags),
                "reasons": ["Required cut fallback used because required cuts exceeded positive replaceability candidates."],
            })
        fallback_pool.sort(key=lambda item: item["score"], reverse=True)
        for item in fallback_pool:
            if len(required_cuts_list) >= required_cuts:
                break
            if item["card_name"] not in already:
                required_cuts_list.append(item)
                already.add(item["card_name"])

    used_required = {item["card_name"] for item in required_cuts_list}
    optional_candidates = [candidate for candidate in candidates if candidate["card_name"] not in used_required]
    optional_cuts_list = optional_candidates[:optional_cut_target]
    optional_cut_names = {item["card_name"] for item in optional_cuts_list}

    # Prevent contradictions: a card recommended as an optional cut should not also appear
    # in "Cards I Would Not Cut." If conflicted, treat it as playable but replaceable utility.
    protected = [(card_name, reason) for card_name, reason in protected if card_name not in optional_cut_names]

    seen_context = set()
    compact_context = []
    for item in context_dependent:
        if item["card_name"] in seen_context:
            continue
        seen_context.add(item["card_name"])
        compact_context.append(item)
        if len(compact_context) >= 12:
            break

    seen_protected = set()
    compact_protected = []
    for card_name, reason in protected:
        if card_name in seen_protected:
            continue
        seen_protected.add(card_name)
        compact_protected.append((card_name, reason))
        if len(compact_protected) >= 18:
            break

    protected_names = {name for name, _ in compact_protected}
    conflict_cut_names = set()
    for item in list(required_cuts_list) + list(optional_cuts_list):
        if item.get("card_name") in protected_names:
            conflict_cut_names.add(item.get("card_name"))

    conflict_manual_review = []
    if conflict_cut_names:
        protected_reason_map = dict(compact_protected)
        by_name = {item.get("card_name"): item for item in list(required_cuts_list) + list(optional_cuts_list)}
        for name in sorted(conflict_cut_names):
            item = by_name.get(name, {})
            conflict_manual_review.append({
                "card_name": name,
                "cut_pressure": item.get("category", "Cut candidate"),
                "protection_pressure": protected_reason_map.get(name, "Protected/core card signal."),
                "why_cuttable": "; ".join(item.get("reasons", [])[:3]) or "Replaceability scoring found cut pressure.",
                "why_belongs": protected_reason_map.get(name, "The card may support the commander, primary plan, essential role, or core engine."),
                "how_to_decide": "Playtest or manually review this slot; do not cut automatically.",
                "current_recommendation": "Conflict / Manual Review — do not present as a final cut.",
            })
        required_cuts_list = [item for item in required_cuts_list if item.get("card_name") not in conflict_cut_names]
        optional_cuts_list = [item for item in optional_cuts_list if item.get("card_name") not in conflict_cut_names]
        # v0.5.7 display cleanup: once a card moves to Conflict / Manual Review,
        # do not also display it as Protected From Cut.
        compact_protected = [(name, reason) for name, reason in compact_protected if name not in conflict_cut_names]

    confident_required_found = len(required_cuts_list)
    additional_required_needed = max(0, required_cuts - confident_required_found)

    return {
        "required_cuts": required_cuts,
        "optional_cut_target": optional_cut_target,
        "cut_strictness": cut_strictness,
        "required_cuts_list": required_cuts_list,
        "optional_cuts_list": optional_cuts_list,
        "context_dependent": compact_context,
        "protected": compact_protected,
        "protected_core_engine": [(name, reason) for name, reason in compact_protected if "primary strategy" in reason or "commander" in reason.lower()],
        "protected_essential_utility": [(name, reason) for name, reason in compact_protected if "essential utility" in reason or "ramp/fixing" in reason],
        "protected_high_synergy": [(name, reason) for name, reason in compact_protected if "low-power" in reason or "contextual" in reason.lower() or "synergy" in reason.lower()],
        "required_cut_shortfall": additional_required_needed,
        "additional_required_cuts_needed": additional_required_needed,
        "conflict_manual_review": conflict_manual_review,
    }


def format_cut_candidate(candidate):
    tags = ", ".join(candidate["tags"]) if candidate["tags"] else "no role tags"
    reason_text = "; ".join(candidate["reasons"][:4])
    return f"{candidate['card_name']} — {candidate['category']}. Replaceability score {candidate['score']}. {reason_text} Tags: {tags}"


# ==============================
# v0.5 Possible Cut Review Logic
# ==============================
# This layer intentionally does not replace v0.4 cut pressure. It refines it into
# careful review language: recommended cuts, possible cuts, playtest-first cards,
# protected cards, confidence, cut type, and replacement categories.

BRACKET_PRESSURE_TAGS = {
    "game_changer", "bracket_pressure", "high_bracket_pressure", "fast_mana", "ritual",
    "efficient_tutor", "combo_tutor", "tutor_chain", "turbo_combo", "dragonstorm_combo",
    "silence_effect", "free_counterspell", "combo_protection",
    "combo_piece_possible", "tutor", "free_interaction", "mana_doubler",
    "extra_combat", "win_condition", "cost_cheat", "free_casting",
}


CONTEXT_DEPENDENT_PROTECTION_TAGS = {
    "sacrifice_outlet", "free_sacrifice_outlet", "recursion", "graveyard_enabler",
    "death_trigger_payoff", "sacrifice_payoff", "artifact_payoff", "damage_payoff",
    "token_maker", "tribal_payoff", "tribal_dependency", "counter_synergy",
    "spell_payoff", "synergy_piece", "combo_piece_possible", "bounce_engine",
    "self_bounce", "creature_combo_value", "dragon_copy_value", "token_copy_value",
    "token_resource_engine", "tap_token_value", "go_wide_token_engine",
    "adventure_synergy", "modal_spell_synergy", "permanent_type_value",
    "blink_flicker", "etb_value", "ltb_value", "exile_return",
    "amass_synergy", "army_typal", "noncreature_spell_payoff", "suspend_big_spell",
    "high_mv_payoff", "big_mana_payoff", "win_condition",
    "defender_payoff", "toughness_payoff", "toughness_combat", "wall_typal", "high_toughness",
    "wheel_effect", "forced_draw", "draw_punisher", "opponent_draw_payoff", "group_slug",
    "lifegain_payoff", "lifedrain_payoff", "life_total_manipulation",
    "tribal_anthem", "tribal_protection", "combat_reset", "attack_safety", "mass_blink",
    "landfall", "landfall_payoff", "extra_land_play", "lands_matter", "land_token",
    "commander_created_package", "rock_token_synergy", "artifact_sacrifice",
}

CORE_PROTECTION_BUCKETS = {
    "Commander Support", "Primary Plan Support", "High Synergy / Low Raw Power",
    "Weak Alone / Strong in Context",
}


def get_game_changers_in_deck(unique_cards, game_changer_names):
    found = []
    for card_name in sorted(unique_cards):
        if normalize_text(card_name) in game_changer_names:
            found.append(card_name)
    return found


def estimate_bracket_read(unique_cards, card_role_tags_by_card, primary_strategy, secondary_strategy, role_tag_counts, game_changer_names, intended_bracket="Unknown"):
    intended = normalize_intended_bracket(intended_bracket)
    game_changers = get_game_changers_in_deck(unique_cards, game_changer_names)
    gc_count = len(game_changers)
    pressure_cards = []
    pressure_tags = {"fast_mana", "ritual", "efficient_tutor", "combo_tutor", "tutor_chain", "turbo_combo", "dragonstorm_combo", "silence_effect", "free_counterspell", "combo_protection", "high_bracket_pressure", "bracket_pressure", "game_changer"}
    for card_name in sorted(unique_cards):
        tags = set(card_role_tags_by_card.get(card_name, []))
        if normalize_text(card_name) in game_changer_names:
            tags.add("game_changer")
        if tags.intersection(pressure_tags):
            pressure_cards.append((card_name, sorted(tags.intersection(pressure_tags))))

    turbo_density = get_turbo_combo_density(role_tag_counts)
    dragonstorm_density = get_dragonstorm_tiamat_density(role_tag_counts)
    fast_count = role_tag_counts.get("fast_mana", 0) + role_tag_counts.get("ritual", 0)
    tutor_count = role_tag_counts.get("efficient_tutor", 0) + role_tag_counts.get("combo_tutor", 0) + role_tag_counts.get("tutor_chain", 0)
    protection_count = role_tag_counts.get("silence_effect", 0) + role_tag_counts.get("free_counterspell", 0) + role_tag_counts.get("combo_protection", 0)

    estimated_num = 2
    reasons = []
    confidence = "Low"
    if gc_count > 3:
        estimated_num = max(estimated_num, 4)
        reasons.append(f"{gc_count} Game Changer(s), which exceeds Bracket 3's normal cap.")
    elif 1 <= gc_count <= 3:
        estimated_num = max(estimated_num, 3)
        reasons.append(f"{gc_count} Game Changer(s), which is Bracket 3+ pressure.")
    if turbo_density >= 55 or primary_strategy == "Turbo Combo / Fast Tutor Chain":
        estimated_num = max(estimated_num, 4)
        confidence = "Medium"
        reasons.append("Fast mana/tutor/protection density suggests a turbo or high-power combo shell.")
    if dragonstorm_density >= 35 or primary_strategy == "Dragonstorm / Tiamat Tutor Chain":
        estimated_num = max(estimated_num, 4)
        confidence = "Medium"
        reasons.append("Dragonstorm/Tiamat tutor-chain package suggests optimized combo pressure.")
    if fast_count >= 5 and tutor_count >= 4:
        estimated_num = max(estimated_num, 4)
        reasons.append("Fast mana plus tutor density increases speed and consistency.")
    if protection_count >= 3 and tutor_count >= 3:
        estimated_num = max(estimated_num, 4)
        reasons.append("Combo protection plus tutors can support protected early win attempts.")
    if estimated_num == 2 and primary_strategy not in {"Unclear", "Control"} and sum(role_tag_counts.values()) > 120:
        estimated_num = 3
        reasons.append("Focused strategy and synergy density suggest tuned casual/upgraded play.")
    if estimated_num >= 4 and turbo_density >= 80 and protection_count >= 4 and tutor_count >= 5:
        if bracket_number(intended) == 5:
            estimated_num = 5
            confidence = "Medium"
            reasons.append("User intended Bracket 5 and the deck has cEDH-like speed/consistency signals.")
        else:
            reasons.append("This may approach cEDH speed, but Bracket 5 should usually require explicit cEDH intent.")
    if not reasons:
        reasons.append("No major bracket-pressure package was detected; estimate is based on general strategy coherence.")

    estimated = {1: "Bracket 1 — Exhibition", 2: "Bracket 2 — Core", 3: "Bracket 3 — Upgraded", 4: "Bracket 4 — Optimized", 5: "Bracket 5 — cEDH"}[estimated_num]
    if confidence == "Low" and (gc_count or fast_count >= 3 or tutor_count >= 3):
        confidence = "Medium"
    return {
        "intended_bracket": intended,
        "estimated_bracket": estimated,
        "confidence": confidence,
        "game_changers": game_changers,
        "game_changer_count": gc_count,
        "pressure_cards": pressure_cards[:20],
        "reasons": reasons,
        "turbo_density": turbo_density,
        "dragonstorm_density": dragonstorm_density,
        "fast_count": fast_count,
        "tutor_count": tutor_count,
        "protection_count": protection_count,
    }


def bracket_pressure_applies(tags, intended_bracket, estimated_bracket):
    tags = set(tags)
    intended_num = bracket_number(normalize_intended_bracket(intended_bracket))
    estimated_num = bracket_number(estimated_bracket)
    if not tags.intersection({"game_changer", "fast_mana", "ritual", "efficient_tutor", "combo_tutor", "tutor_chain", "turbo_combo", "dragonstorm_combo", "silence_effect", "free_counterspell", "combo_protection", "high_bracket_pressure", "bracket_pressure"}):
        return False
    if intended_num in {1, 2}:
        return True
    if intended_num == 3 and ("game_changer" in tags or tags.intersection({"turbo_combo", "dragonstorm_combo", "fast_mana", "ritual", "combo_tutor", "tutor_chain"})):
        return True
    if intended_num is None and estimated_num and estimated_num >= 4:
        return True
    return False


def is_zero_mana_creature(card):
    if not card:
        return False
    mv = get_representative_nonland_mana_value(card)
    return mv == 0 and has_type_on_any_face(card, "Creature")


def is_creature_cost_reduction_strategy(primary_strategy, secondary_strategy, role_tag_counts):
    return (
        primary_strategy == "Creature Cost-Reduction / Creature Combo Value"
        or secondary_strategy == "Creature Cost-Reduction / Creature Combo Value"
        or role_tag_counts.get("creature_cost_reduction", 0) > 0
        or role_tag_counts.get("creature_cast_trigger", 0) >= 3
    )


def get_deck_role_needs(role_tag_counts, scryfall_land_count, average_nonland_mana_value, primary_strategy):
    needs = []

    if role_tag_counts.get("ramp", 0) < 8:
        needs.append("More ramp")
    if role_tag_counts.get("card_draw", 0) + role_tag_counts.get("card_advantage", 0) < 8:
        needs.append("More card draw")
    if role_tag_counts.get("targeted_removal", 0) < 6:
        needs.append("More targeted removal")
    if role_tag_counts.get("board_wipe", 0) < 2 and primary_strategy in {"Control", "Reanimator", "Graveyard Recursion"}:
        needs.append("More board wipes")
    if scryfall_land_count < 35:
        needs.append("More lands")
    if average_nonland_mana_value >= 3.8:
        needs.append("Lower mana curve")

    if primary_strategy in {"Aristocrats", "Sacrifice"}:
        if role_tag_counts.get("sacrifice_outlet", 0) + role_tag_counts.get("free_sacrifice_outlet", 0) < 6:
            needs.append("More sacrifice outlets")
        if role_tag_counts.get("recursion", 0) < 4:
            needs.append("More recursion")
    if primary_strategy in {"Graveyard Recursion", "Reanimator", "Graveyard Self-Mill / Recursion"}:
        if role_tag_counts.get("graveyard_enabler", 0) + role_tag_counts.get("self_mill", 0) < 6:
            needs.append("More graveyard setup")
        if role_tag_counts.get("recursion", 0) < 6:
            needs.append("More recursion")
    if primary_strategy in {"Tokens", "Go-Wide Combat", "Token Resource Engine"}:
        if role_tag_counts.get("token_maker", 0) < 10:
            needs.append("More token production")
    if primary_strategy == "Toughness Matters / Defender":
        if role_tag_counts.get("defender_payoff", 0) + role_tag_counts.get("toughness_payoff", 0) < 6:
            needs.append("More toughness-matters payoffs")
        if role_tag_counts.get("wall_typal", 0) + role_tag_counts.get("high_toughness", 0) < 12:
            needs.append("More defender support")
    if primary_strategy == "Wheels / Draw-Punisher / Group Slug":
        if role_tag_counts.get("wheel_effect", 0) + role_tag_counts.get("forced_draw", 0) < 6:
            needs.append("More card draw")
        if role_tag_counts.get("draw_punisher", 0) + role_tag_counts.get("opponent_draw_payoff", 0) < 5:
            needs.append("More finishers")
    if primary_strategy == "Commander-Created Landfall / Artifact Token Engine":
        needs.extend(["More artifact support", "More utility lands"])
        if role_tag_counts.get("sacrifice_outlet", 0) < 6:
            needs.append("More sacrifice outlets")
    if primary_strategy not in {"Unclear", "Control"}:
        needs.append("More commander synergy")
        needs.append("More primary-plan support")

    seen = set()
    ordered_needs = []
    for need in needs:
        if need not in seen:
            seen.add(need)
            ordered_needs.append(need)
    return ordered_needs


def determine_possible_cut_type(candidate, card, tags, bucket, required=False, intended_bracket="Unknown", estimated_bracket="Unknown"):
    tags = set(tags)
    reasons = " ".join(candidate.get("reasons", [])).lower()
    category = candidate.get("category", "")
    mv = get_representative_nonland_mana_value(card) if card else None

    if required:
        return "Required Legality Cut"
    if bracket_pressure_applies(tags, intended_bracket, estimated_bracket):
        return "Possible Bracket Pressure Cut"
    if card and has_type_on_any_face(card, "Land"):
        return "Possible Mana Base Concern"
    if "unsupported tribal" in category.lower() or "unsupported tribal" in reasons:
        return "Possible Unsupported Tribal Card"
    if "unsupported subtheme" in category.lower() or "unsupported package" in reasons:
        return "Possible Unsupported Subtheme Card"
    if tags.intersection({"tribal_payoff", "tribal_anthem", "tribal_protection"}) and "unsupported" in reasons:
        return "Possible Unsupported Tribal Card"
    if tags.intersection({"lifegain_payoff", "lifedrain_payoff", "defender_payoff", "toughness_payoff", "landfall_payoff"}) and bucket in {"Manual Review", "Possible Off-Plan"}:
        return "Possible Narrow Payoff"
    if mv is not None and mv >= 6 and ("high mana value" in reasons or "curve" in reasons):
        return "Possible Curve Cut"
    if "duplicate role pressure" in reasons or "redundant" in category.lower():
        return "Possible Redundancy Cut"
    if bucket == "Possible Off-Plan" or "wrong shell" in category.lower() or "wrong card" in category.lower():
        return "Possible Wrong-Shell Card"
    if bucket == "Manual Review" or "manual review" in category.lower():
        return "Possible Manual Review"
    if bucket == "Generic Utility" or "playable but replaceable" in category.lower():
        return "Possible Efficiency Cut"
    if "no clear role" in reasons or "low detected board impact" in reasons or "low synergy" in category.lower():
        return "Possible Low-Impact Cut"
    return "Possible Efficiency Cut"


def determine_cut_confidence(candidate, tags, bucket, required=False):
    tags = set(tags)
    score = candidate.get("score", 0)
    category = candidate.get("category", "")
    reasons = " ".join(candidate.get("reasons", [])).lower()

    if required:
        return "High"

    if bucket in CORE_PROTECTION_BUCKETS or tags.intersection(CONTEXT_DEPENDENT_PROTECTION_TAGS):
        if score >= 65 and ("unsupported tribal" in reasons or "possible off-plan" in bucket.lower()):
            return "Medium"
        return "Low"

    if "manual review" in category.lower() or bucket == "Manual Review":
        return "Low"

    if score >= 60 and bucket in {"Possible Off-Plan", "Generic Utility"}:
        return "High"
    if score >= 35:
        return "Medium"
    if score >= 15:
        return "Low"
    return "Low"


def determine_replacement_categories(candidate, card, tags, cut_type, primary_strategy, secondary_strategy, role_tag_counts, deck_needs):
    tags = set(tags)
    categories = []
    mv = get_representative_nonland_mana_value(card) if card else None

    if cut_type == "Possible Curve Cut" or (mv is not None and mv >= 6):
        categories.append("Lower mana curve")
    if cut_type in {"Possible Off-Theme Cut", "Possible Low-Impact Cut", "Possible Manual Review"}:
        categories.extend(["More commander synergy", "More primary-plan support"])
    if cut_type == "Possible Redundancy Cut":
        categories.append("More primary-plan support")
    if cut_type == "Possible Mana Base Concern":
        categories.append("More lands")
    if cut_type == "Possible Bracket Pressure Cut":
        categories.extend(["More primary-plan support", "More commander synergy", "Fewer bracket-escalating cards"])
    if cut_type in {"Possible Unsupported Tribal Card"}:
        categories.append("More tribal density")
    if cut_type in {"Possible Unsupported Subtheme Card", "Possible Narrow Payoff"}:
        categories.append("More primary-plan support")

    # If the card being reviewed fills a staple utility role, replacing it should preserve the role
    # unless the deck is clearly saturated elsewhere.
    if "ramp" in tags and role_tag_counts.get("ramp", 0) < 10:
        categories.append("More ramp")
    if tags.intersection({"card_draw", "card_advantage", "card_selection"}) and role_tag_counts.get("card_draw", 0) + role_tag_counts.get("card_advantage", 0) < 10:
        categories.append("More card draw")
    if "targeted_removal" in tags and role_tag_counts.get("targeted_removal", 0) < 8:
        categories.append("More targeted removal")
    if "board_wipe" in tags and role_tag_counts.get("board_wipe", 0) < 3:
        categories.append("More board wipes")
    if "protection" in tags and role_tag_counts.get("protection", 0) < 5:
        categories.append("More protection")
    if tags.intersection({"defender_payoff", "toughness_payoff", "toughness_combat", "wall_typal"}):
        categories.extend(["More toughness-matters payoffs", "More defender support"])
    if tags.intersection({"lifegain_payoff", "lifedrain_payoff"}):
        categories.extend(["More lifegain payoffs", "More lifegain enablers"])
    if tags.intersection({"landfall", "landfall_payoff", "extra_land_play", "lands_matter"}):
        categories.extend(["More ramp", "More utility lands"])
    if tags.intersection({"artifact_payoff", "artifact_token_synergy", "artifact_sacrifice", "rock_token_synergy"}):
        categories.append("More artifact support")

    # Strategy-specific role needs.
    if primary_strategy in {"Aristocrats", "Sacrifice"}:
        categories.extend(["More sacrifice outlets", "More recursion"])
    if primary_strategy in {"Graveyard Recursion", "Reanimator", "Graveyard Self-Mill / Recursion"}:
        categories.extend(["More recursion", "More graveyard setup"])
    if primary_strategy in {"Tokens", "Go-Wide Combat", "Token Resource Engine"}:
        categories.append("More token production")
    if primary_strategy in {"Voltron", "+1/+1 Counters", "Dragon Copy / Token-Copy Value", "Ramp into Big Threats", "Cascade / Big Mana Value", "Suspend / Big Spell Cheat", "Spellslinger / Amass Army"}:
        categories.append("More finishers")
    if primary_strategy == "Creature Cost-Reduction / Creature Combo Value":
        categories.extend(["More commander synergy", "More primary-plan support", "Lower mana curve", "More protection"])
    if primary_strategy == "Dragon Copy / Token-Copy Value":
        categories.extend(["More commander synergy", "More primary-plan support", "More ramp", "More protection"])
    if primary_strategy == "Legends Matter / Legendary Cascade":
        categories.extend(["Better fixing", "More protection", "More primary-plan support"])
    if primary_strategy == "Elf Typal / Token Lifedrain":
        categories.extend(["More tribal density", "More token production", "More protection"])
    if primary_strategy == "Artifact/Treasure Tutor Chain":
        categories.extend(["More artifact support", "More primary-plan support", "More protection"])
    if primary_strategy == "Ramp-Control / Big Mana Value":
        categories.extend(["More ramp", "More board wipes", "More finishers", "More card draw"])
    if primary_strategy == "Blink/Flicker / ETB Value":
        categories.extend(["More commander synergy", "More primary-plan support", "More protection"])
    if primary_strategy == "Spellslinger / Amass Army":
        categories.extend(["More card draw", "More targeted removal", "More token production"])
    if primary_strategy == "Toughness Matters / Defender":
        categories.extend(["More toughness-matters payoffs", "More defender support", "More protection"])
    if primary_strategy == "Wheels / Draw-Punisher / Group Slug":
        categories.extend(["More card draw", "More instant/sorcery density", "More finishers"])
    if primary_strategy == "Commander-Created Landfall / Artifact Token Engine":
        categories.extend(["More artifact support", "More ramp", "More utility lands", "More sacrifice outlets"])
    if primary_strategy == "Control":
        categories.extend(["More card draw", "More targeted removal", "More board wipes"])

    categories.extend(deck_needs[:4])

    # Deduplicate while preserving order and only keep known replacement categories.
    seen = set()
    result = []
    for category in categories:
        if category in REPLACEMENT_CATEGORIES and category not in seen:
            seen.add(category)
            result.append(category)
    return result[:3] if result else ["More primary-plan support"]


def should_playtest_before_cut(candidate, tags, bucket, confidence):
    tags = set(tags)
    if confidence == "Low":
        return True
    if bucket in {"Weak Alone / Strong in Context", "High Synergy / Low Raw Power", "Secondary Plan Support", "Shell Support"}:
        return True
    if tags.intersection(CONTEXT_DEPENDENT_PROTECTION_TAGS):
        return True
    if "manual review" in candidate.get("category", "").lower():
        return True
    return False


def summarize_candidate_reason(candidate, cut_type, confidence):
    reasons = candidate.get("reasons", [])[:3]
    if not reasons:
        reasons = ["Worth reviewing based on replaceability, plan fit, and role balance."]
    reason_text = "; ".join(reasons)
    if confidence == "Low":
        reason_text += " This is a cautious review flag, not a recommendation to cut automatically."
    return reason_text


def make_possible_cut_entry(candidate, card, primary_strategy, secondary_strategy, role_tag_counts, deck_needs, required=False, intended_bracket="Unknown", estimated_bracket="Unknown"):
    tags = set(candidate.get("tags", []))
    bucket = candidate.get("bucket", "Manual Review")
    cut_type = determine_possible_cut_type(candidate, card, tags, bucket, required=required, intended_bracket=intended_bracket, estimated_bracket=estimated_bracket)
    confidence = determine_cut_confidence(candidate, tags, bucket, required=required)
    replacement_categories = determine_replacement_categories(candidate, card, tags, cut_type, primary_strategy, secondary_strategy, role_tag_counts, deck_needs)
    return {
        "card_name": candidate.get("card_name", "Unknown Card"),
        "reason": summarize_candidate_reason(candidate, cut_type, confidence),
        "confidence": confidence,
        "cut_type": cut_type,
        "replacement_categories": replacement_categories,
        "exact_replacement_note": "Not suggested automatically in v0.5.8; verify color identity, budget, bracket, and deck plan first.",
        "score": candidate.get("score", 0),
        "bucket": bucket,
        "tags": sorted(tags),
        "playtest_first": should_playtest_before_cut(candidate, tags, bucket, confidence),
    }


def build_possible_cut_review(cut_pressure_review, unique_cards, scryfall_lookup, card_role_tags_by_card, card_plan_fit_buckets, primary_strategy, secondary_strategy, role_tag_counts, scryfall_land_count, average_nonland_mana_value, bracket_read=None):
    deck_needs = get_deck_role_needs(role_tag_counts, scryfall_land_count, average_nonland_mana_value, primary_strategy)
    bracket_read = bracket_read or {"intended_bracket": "Unknown", "estimated_bracket": "Unknown"}
    intended_bracket = bracket_read.get("intended_bracket", "Unknown")
    estimated_bracket = bracket_read.get("estimated_bracket", "Unknown")

    recommended = []
    possible = []
    playtest = []
    protected_from_cut = []
    conflict_manual_review = list(cut_pressure_review.get("conflict_manual_review", []))
    conflict_names = {item.get("card_name") for item in conflict_manual_review}
    used_names = set(conflict_names)

    # Required cuts are legality/size cuts first, not optional optimization advice.
    for candidate in cut_pressure_review.get("required_cuts_list", []):
        card_name = candidate.get("card_name")
        card = scryfall_lookup.get(card_name.lower()) if card_name else None
        entry = make_possible_cut_entry(candidate, card, primary_strategy, secondary_strategy, role_tag_counts, deck_needs, required=True, intended_bracket=intended_bracket, estimated_bracket=estimated_bracket)
        entry["reason"] = "Required because the deck is over Commander deck size. " + entry["reason"]
        recommended.append(entry)
        used_names.add(card_name)

    # Optional cuts become recommended only with sufficient confidence and non-contextual status.
    for candidate in cut_pressure_review.get("optional_cuts_list", []):
        card_name = candidate.get("card_name")
        if card_name in used_names:
            continue
        card = scryfall_lookup.get(card_name.lower()) if card_name else None
        entry = make_possible_cut_entry(candidate, card, primary_strategy, secondary_strategy, role_tag_counts, deck_needs, required=False, intended_bracket=intended_bracket, estimated_bracket=estimated_bracket)
        if entry["confidence"] == "High" and not entry["playtest_first"] and len(recommended) < RECOMMENDED_CUT_TARGET:
            recommended.append(entry)
        else:
            possible.append(entry)
        used_names.add(card_name)

    # Add broader possible cuts from all positive replaceability candidates, but keep it conservative.
    primary_tags, secondary_tags = get_primary_secondary_tag_sets(primary_strategy, secondary_strategy)
    additional_candidates = []
    for card_name in sorted(unique_cards):
        if card_name in used_names:
            continue
        card = scryfall_lookup.get(card_name.lower())
        if not card or is_land_card(card):
            continue
        tags = set(card_role_tags_by_card.get(card_name, []))
        bucket, bucket_reason = get_plan_fit_bucket_for_card(card_name, card_plan_fit_buckets)
        if is_zero_mana_creature(card) and is_creature_cost_reduction_strategy(primary_strategy, secondary_strategy, role_tag_counts):
            # In Animar-style shells, zero-mana creatures can be engine pieces even when they look weak.
            continue
        if bucket in CORE_PROTECTION_BUCKETS:
            continue
        score, reasons, category = get_replaceability_score(
            card_name, card, tags, bucket, bucket_reason, primary_tags, secondary_tags,
            role_tag_counts, tribal_support_flags, average_nonland_mana_value
        )
        if score <= 0:
            continue
        additional_candidates.append({
            "card_name": card_name,
            "score": score,
            "category": category,
            "bucket": bucket,
            "tags": sorted(tags),
            "reasons": reasons,
        })
    additional_candidates.sort(key=lambda item: item["score"], reverse=True)
    for candidate in additional_candidates:
        if len(possible) >= POSSIBLE_CUT_REVIEW_TARGET:
            break
        card_name = candidate.get("card_name")
        if card_name in used_names:
            continue
        card = scryfall_lookup.get(card_name.lower()) if card_name else None
        entry = make_possible_cut_entry(candidate, card, primary_strategy, secondary_strategy, role_tag_counts, deck_needs, required=False, intended_bracket=intended_bracket, estimated_bracket=estimated_bracket)
        if entry["confidence"] == "High" and not entry["playtest_first"] and len(recommended) < RECOMMENDED_CUT_TARGET:
            recommended.append(entry)
        else:
            possible.append(entry)
        used_names.add(card_name)

    # Playtest-first cards: include context-dependent items plus low-confidence possible cuts.
    seen_playtest = set()

    # v0.5.7: zero-mana creatures in Animar-style creature-cost decks are often weak alone
    # but strong in context because they help chain creature casts/counters.
    if is_creature_cost_reduction_strategy(primary_strategy, secondary_strategy, role_tag_counts):
        for card_name in sorted(unique_cards):
            card = scryfall_lookup.get(card_name.lower())
            if card and is_zero_mana_creature(card):
                seen_playtest.add(card_name)
                playtest.append({
                    "card_name": card_name,
                    "why_questionable": "Zero-mana creature may look low-impact by generic standards.",
                    "why_might_belong": "In a creature cost-reduction / creature-cast deck, it can help chain creature casts, build commander counters, or enable combo-value turns.",
                    "what_to_watch": "Track whether it meaningfully advances creature chains or is just a low-impact body.",
                })
                if len(playtest) >= PLAYTEST_FIRST_TARGET:
                    break

    for item in cut_pressure_review.get("context_dependent", []):
        card_name = item.get("card_name")
        if not card_name or card_name in seen_playtest:
            continue
        seen_playtest.add(card_name)
        playtest.append({
            "card_name": card_name,
            "why_questionable": item.get("questionable", "May look narrow or low-impact by generic standards."),
            "why_might_belong": item.get("might_belong", "May support the deck's actual engine."),
            "what_to_watch": "Track whether this card advances the commander, primary engine, or win condition in real games.",
        })
        if len(playtest) >= PLAYTEST_FIRST_TARGET:
            break

    for entry in possible:
        if len(playtest) >= PLAYTEST_FIRST_TARGET:
            break
        if entry.get("playtest_first") and entry["card_name"] not in seen_playtest:
            seen_playtest.add(entry["card_name"])
            playtest.append({
                "card_name": entry["card_name"],
                "why_questionable": entry["reason"],
                "why_might_belong": "It has contextual or low-confidence signals, so it may still belong depending on playtesting.",
                "what_to_watch": "Watch whether it is dead in hand, redundant, too slow, or actually part of the deck's resource engine.",
            })

    seen_protected = set()
    for card_name, reason in cut_pressure_review.get("protected", []):
        if card_name in conflict_names:
            continue
        if card_name in seen_protected:
            continue
        seen_protected.add(card_name)
        protected_from_cut.append({"card_name": card_name, "reason": reason})
        if len(protected_from_cut) >= PROTECTED_REVIEW_TARGET:
            break

    additional_required_needed = cut_pressure_review.get("additional_required_cuts_needed", 0)

    return {
        "deck_needs": deck_needs,
        "recommended_cuts": recommended[:RECOMMENDED_CUT_TARGET],
        "possible_cuts": possible[:POSSIBLE_CUT_REVIEW_TARGET],
        "playtest_before_cutting": playtest[:PLAYTEST_FIRST_TARGET],
        "protected_from_cut": protected_from_cut[:PROTECTED_REVIEW_TARGET],
        "conflict_manual_review": conflict_manual_review[:12],
        "additional_required_cuts_needed": additional_required_needed,
    }


def format_replacement_categories(categories):
    return ", ".join(categories) if categories else "More primary-plan support"


def add_section(lines, title):
    lines.append("")
    lines.append(title)
    lines.append("-" * 30)



# ==============================
# v0.5.7 Patch: Archetype Gates, Role Repairs, and Cut Review Cleanup
# ==============================
# This block intentionally overrides/wraps selected v0.5.7 functions instead of
# rewriting the whole file. It uses the updated v0.5.7 rules markdowns as the
# design target: stop broad archetypes from stealing primary strategy, add missing
# role tags, gate commander-created landfall warnings, and improve refined/over-limit cut output.

V056_ADDED_ROLE_TAGS = [
    "untap_ramp", "land_untapper", "permanent_untapper", "artifact_untapper", "mana_engine_support",
    "tribal_body", "typal_density", "token_body", "sacrifice_body", "attack_body",
    "goblin_typal", "vampire_typal", "sphinx_typal", "human_typal", "soldier_typal", "wizard_typal", "zombie_typal",
    "pod_effect", "creature_tutor", "creature_chain", "sacrifice_as_cost", "etb_toolbox", "curve_chain_piece",
    "activated_ability_payoff", "activated_ability_cost_reduction", "power_based_cost_reduction", "pinger", "repeatable_removal", "tap_ability_engine",
    "equipment_payoff", "aura_payoff", "equip_cost_reduction", "attachment_synergy", "commander_damage_support", "voltron_protection", "artifact_combat",
    "adventure_spell", "adventure_payoff", "modal_value", "cast_from_exile", "alternate_face_value", "spell_permanent_hybrid",
    "slow_alt_win_condition", "high_power_value_piece", "compact_combo_piece", "fast_combo_enabler", "true_turbo_combo",
    "bracket_pressure_possible", "minor_package_support", "suppressed_broad_archetype",
]
for _tag in V056_ADDED_ROLE_TAGS:
    if _tag not in ROLE_TAGS:
        ROLE_TAGS.append(_tag)
LOW_RAW_POWER_CONTEXT_TAGS.update({
    "untap_ramp", "land_untapper", "permanent_untapper", "artifact_untapper", "mana_engine_support",
    "tribal_body", "typal_density", "token_body", "sacrifice_body", "attack_body",
    "pod_effect", "creature_tutor", "creature_chain", "sacrifice_as_cost", "etb_toolbox",
    "activated_ability_payoff", "activated_ability_cost_reduction", "power_based_cost_reduction", "pinger", "tap_ability_engine",
    "equipment_payoff", "aura_payoff", "equip_cost_reduction", "attachment_synergy", "commander_damage_support",
    "adventure_spell", "adventure_payoff", "modal_value", "cast_from_exile", "spell_permanent_hybrid",
})
HIGH_SYNERGY_LOW_RAW_POWER_TAGS.update(LOW_RAW_POWER_CONTEXT_TAGS)

V056_NON_TRIBAL_WORDS = {
    "time", "times", "turn", "turns", "phase", "phases", "combat", "card", "cards",
    "spell", "spells", "token", "tokens", "counter", "counters", "damage", "life",
    "mana", "artifact", "creature", "creatures", "permanent", "permanents", "opponent", "opponents",
    "player", "players", "library", "graveyard", "hand", "battlefield", "target", "source", "type", "types",
}

# Add narrower archetypes from strategy_archetype_rules.md v0.5.7.
ARCHETYPE_DEFINITIONS.update({
    "Go-Wide / Go-Tall Token Combat": {
        "anchor_tags": {"attack_trigger_payoff", "token_maker", "combat_synergy"},
        "core_tags": {"attack_trigger_payoff": 7, "token_maker": 5, "combat_synergy": 4, "counter_synergy": 3, "anthem": 3, "power_matters": 3, "go_tall_support": 2, "extra_combat": 2, "protection": 1},
        "engine": "The deck creates tokens or large combat bodies, attacks to scale board presence, then converts counters, anthems, power-matters effects, or combat triggers into lethal pressure.",
        "finishers": "Go-wide alpha strike, go-tall token combat, extra combats, overrun effects, anthem-backed combat, or power-matters damage/draw.",
    },
    "Goblin Typal / Go-Wide Tokens": {
        "anchor_tags": {"goblin_typal", "token_maker", "tribal_payoff"},
        "core_tags": {"goblin_typal": 8, "token_maker": 5, "typal_density": 4, "tribal_body": 3, "tribal_payoff": 4, "anthem": 3, "sacrifice_outlet": 2, "damage_payoff": 3, "haste_enabler": 2, "go_wide_token_engine": 3},
        "engine": "Goblin bodies and Goblin tokens become combat pressure, sacrifice fuel, mana, or direct damage.",
        "finishers": "Goblin swarm attacks, sacrifice/drain turns, damage payoffs, haste-backed token explosions.",
    },
    "Vampire Tokens / Aristocrats / Drain": {
        "anchor_tags": {"vampire_typal", "token_maker", "death_trigger_payoff", "lifedrain_payoff"},
        "core_tags": {"vampire_typal": 8, "token_maker": 4, "typal_density": 3, "tribal_payoff": 3, "sacrifice_outlet": 4, "death_trigger_payoff": 5, "lifedrain_payoff": 5, "aristocrat_payoff": 5, "recursion": 2, "blood_maker": 2},
        "engine": "Vampire bodies, sacrifice outlets, and death/lifedrain payoffs turn creature deaths into opponent life loss and board pressure.",
        "finishers": "Aristocrats drain, Vampire token swarm, death-trigger loops, repeated lifedrain.",
    },
    "Pod / Creature Toolbox / Creature Chain": {
        "anchor_tags": {"pod_effect", "creature_tutor", "creature_chain", "sacrifice_as_cost"},
        "core_tags": {"pod_effect": 10, "creature_tutor": 7, "creature_chain": 7, "sacrifice_as_cost": 4, "etb_toolbox": 4, "etb_value": 2, "untap_ramp": 2, "permanent_untapper": 2, "haste_enabler": 2, "recursion": 2, "creature_combo_value": 3},
        "type_tags": {"creature": 1},
        "engine": "The deck sacrifices or upgrades creatures into toolbox pieces, ETB value, untap chains, or creature-based win lines.",
        "finishers": "Creature chain combo, tutored finisher, ETB value snowball, toolbox lock, or overwhelming board.",
    },
    "Activated Abilities / Power-Reduction Engine": {
        "anchor_tags": {"activated_ability_cost_reduction", "power_based_cost_reduction", "activated_ability_payoff", "tap_ability_engine"},
        "core_tags": {"activated_ability_cost_reduction": 9, "power_based_cost_reduction": 10, "activated_ability_payoff": 6, "activated_ability_synergy": 4, "mana_sink": 4, "pinger": 4, "power_matters": 4, "untap_ramp": 3, "permanent_untapper": 3, "tap_ability_engine": 4, "repeatable_removal": 3},
        "engine": "The commander or engine reduces or rewards activated abilities, turning power, untaps, pingers, and mana sinks into repeatable value.",
        "finishers": "Discounted X abilities, pinger loops, repeated activated value, mana-sink finishers, or untap/ability snowballs.",
    },
    "Equipment / Aura Voltron": {
        "anchor_tags": {"equipment_payoff", "aura_payoff", "attachment_synergy", "commander_damage_support"},
        "core_tags": {"equipment_payoff": 7, "aura_payoff": 7, "equipment_synergy": 5, "aura_synergy": 5, "equip_cost_reduction": 5, "attachment_synergy": 5, "commander_damage_support": 5, "go_tall_support": 3, "combat_damage_trigger": 3, "protection": 3, "voltron_protection": 4, "evasion": 2},
        "engine": "Equipment and/or Auras turn one primary attacker, often the commander, into a protected evasive threat or combat-value engine.",
        "finishers": "Commander damage, double strike, evasive Voltron attacks, combat-damage triggers, or extra-combat lethal.",
    },
    "Artifact Combat": {
        "anchor_tags": {"artifact_combat", "artifact_payoff", "equipment_synergy"},
        "core_tags": {"artifact_combat": 8, "artifact_payoff": 4, "artifact_token_synergy": 3, "equipment_synergy": 3, "token_maker": 2, "anthem": 2, "combat_synergy": 3, "artifact_creature": 3},
        "engine": "Artifacts, artifact creatures, Equipment, and modified/combat tools create board pressure across multiple attackers rather than only one Voltron threat.",
        "finishers": "Artifact creature combat, modified/equipment payoffs, artifact-token attacks, combat-trigger value.",
    },
    "Artifact Engine / Artifact Tap / Artifact Mana": {
        "anchor_tags": {"artifact_payoff", "artifact_untapper", "mana_engine_support"},
        "core_tags": {"artifact_payoff": 6, "artifact_token_synergy": 5, "artifact_untapper": 5, "mana_engine_support": 4, "mana_rock": 2, "artifact_ramp": 3, "card_advantage": 2, "token_maker": 2, "untap_ramp": 3, "combo_piece_possible": 2},
        "type_tags": {"artifact": 1},
        "engine": "Artifact density and artifact tap/mana/card-advantage tools become the deck's resource engine.",
        "finishers": "Construct/artifact combat, artifact mana explosion, artifact payoff engine, combo-adjacent artifact loops.",
    },
    "Big Mana / Mana Storage": {
        "anchor_tags": {"mana_doubler", "mana_sink", "big_mana_payoff"},
        "core_tags": {"ramp": 4, "land_ramp": 3, "mana_doubler": 6, "mana_sink": 5, "big_mana_payoff": 6, "high_mv_payoff": 4, "untap_ramp": 4, "land_untapper": 4, "x_spell": 3, "large_creature": 2, "power_matters": 2},
        "engine": "The deck stores, multiplies, or repeatedly generates mana, then converts it into large threats, X spells, or mana-sink finishers without necessarily being a control deck.",
        "finishers": "Huge creatures, giant X spells, mana-sink activations, oversized commander combat, big-mana overrun turns.",
    },
    "Sphinx Typal / Topdeck Cost Reduction": {
        "anchor_tags": {"sphinx_typal", "topdeck_manipulation", "cost_reducer"},
        "core_tags": {"sphinx_typal": 8, "typal_density": 3, "cost_reducer": 5, "topdeck_manipulation": 4, "card_selection": 4, "etb_value": 3, "blink_flicker": 2, "copy_clone_value": 2, "high_mv_payoff": 2},
        "engine": "Sphinx density, cost reduction, and topdeck/fact-or-fiction style card selection chain large flying threats into card advantage.",
        "finishers": "Large Sphinx combat, repeated ETB/fact-or-fiction piles, blink/copy value, overwhelming cards.",
    },
})

# Keep these aliases visible in reports by allowing stronger/new names to share older buckets.
V056_BROAD_ARCHETYPES = {
    "Ramp-Control / Big Mana Value", "Elf Typal / Token Lifedrain", "Artifact/Treasure Tutor Chain",
    "Commander-Created Landfall / Artifact Token Engine", "Turbo Combo / Fast Tutor Chain", "Dragonstorm / Tiamat Tutor Chain",
}


def _v056_card_text(card):
    return normalize_text((card.get("type_line", "") if card else "") + "\n" + (get_full_oracle_text(card) if card else ""))


def _v056_type_line(card):
    return (card.get("type_line", "") if card else "").lower()


def _v056_has_creature_type(card, ctype):
    tl = _v056_type_line(card)
    text = _v056_card_text(card)
    return ctype in tl or f"{ctype} " in text or f"{ctype}s" in text


def _v056_get_referenced_creature_types(oracle_text):
    refs = set()
    for raw in normalize_text(oracle_text).split():
        singular = singularize(raw)
        if singular in V056_NON_TRIBAL_WORDS:
            continue
        if singular in KNOWN_CREATURE_TYPES and singular not in NON_TRIBAL_REFERENCE_WORDS:
            refs.add(singular.title())
    return refs


def get_referenced_creature_types(oracle_text):
    return _v056_get_referenced_creature_types(oracle_text)


def get_tribal_dependency_types(oracle_text):
    text = normalize_text(oracle_text)
    found = set()
    for ctype in _v056_get_referenced_creature_types(oracle_text):
        lower = ctype.lower()
        plural = lower + "s"
        if lower in V056_NON_TRIBAL_WORDS:
            continue
        patterns = [
            rf"\b{plural}\s+you\s+control\b",
            rf"\bother\s+{plural}\b",
            rf"\bwhenever\s+(a|another|one\s+or\s+more)\s+{lower}",
            rf"\bfor\s+each\s+{lower}",
            rf"\bfor\s+each\s+{plural}",
            rf"\bequipped\s+{lower}\b",
            rf"\b{lower}\s+spells\s+you\s+cast\b",
            rf"\bcreate\s+.*\b{lower}\b.*token",
            rf"\bchoose\s+a\s+creature\s+type\b",
            rf"\bcreatures\s+of\s+the\s+chosen\s+type\b",
        ]
        if any(re.search(pattern, text) for pattern in patterns):
            found.add(ctype)
    return found


def get_tribal_payoff_types(oracle_text):
    text = normalize_text(oracle_text)
    found = set()
    for ctype in _v056_get_referenced_creature_types(oracle_text):
        lower = ctype.lower()
        plural = lower + "s"
        if lower in V056_NON_TRIBAL_WORDS:
            continue
        patterns = [
            rf"\b{plural}\s+you\s+control\s+get\b",
            rf"\bother\s+{plural}\s+you\s+control\b",
            rf"\bwhenever\s+(a|another|one\s+or\s+more)\s+{lower}",
            rf"\bfor\s+each\s+{lower}",
            rf"\bfor\s+each\s+{plural}",
            rf"\b{lower}\s+spells\s+you\s+cast\b",
            rf"\bcreatures\s+of\s+the\s+chosen\s+type\b",
            rf"\bchosen\s+type\b",
        ]
        if any(re.search(pattern, text) for pattern in patterns):
            found.add(ctype)
    return found


_v055_infer_card_role_tags = infer_card_role_tags

def infer_card_role_tags(card, commander_cards=None):
    tags = set(_v055_infer_card_role_tags(card, commander_cards))
    text = _v056_card_text(card)
    tl = _v056_type_line(card)
    name_text = normalize_text(card.get("name", "") if card else "")
    commander_text = normalize_text(" ".join(get_full_oracle_text(c) + " " + c.get("type_line", "") for c in (commander_cards or [])))

    # Untap-ramp and tap-engine support.
    if any(p in text for p in ["untap target land", "untap up to one target land", "untap all lands", "untap each land"]):
        tags.update(["untap_ramp", "land_untapper", "mana_engine_support", "ramp"])
    if any(p in text for p in ["untap target permanent", "untap another target permanent", "untap each permanent", "untap up to"]):
        tags.update(["untap_ramp", "permanent_untapper", "mana_engine_support"])
    if any(p in text for p in ["untap target artifact", "untap all artifacts", "untap another target artifact"]):
        tags.update(["untap_ramp", "artifact_untapper", "artifact_payoff", "mana_engine_support"])
    if any(p in text for p in ["tap an untapped artifact", "tap two untapped artifacts", "tap three untapped artifacts", "tap an untapped token", "tap two untapped tokens", "tap three untapped tokens"]):
        tags.update(["tap_ability_engine", "mana_engine_support"])

    # Creature body context and typal body tags. These reduce no-role false positives in typal/sacrifice/combat decks.
    if "creature" in tl:
        subtypes = {s.lower() for s in get_creature_subtypes(card.get("type_line", ""))}
        for subtype in subtypes:
            if subtype in {"goblin", "vampire", "sphinx", "dragon", "dwarf", "zombie", "human", "soldier", "wizard", "elf"}:
                tags.update([f"{subtype}_typal", "tribal_body", "typal_density"])
        if any(p in commander_text for p in ["whenever you attack", "whenever one or more creatures attack", "tap two untapped", "tap three untapped", "sacrifice", "dies", "creature token", "creatures you control"]):
            tags.add("attack_body")
        if any(p in commander_text for p in ["sacrifice", "dies", "creature dies", "whenever you sacrifice"]):
            tags.add("sacrifice_body")

    # Pod / creature-chain support.
    if any(p in text for p in ["sacrifice another creature: search your library", "sacrifice a creature: search your library", "mana value equal to 1 plus", "mana value equal to one plus", "birthing pod"]):
        tags.update(["pod_effect", "creature_tutor", "creature_chain", "sacrifice_as_cost", "sacrifice_outlet", "etb_toolbox"])
    if "search your library for a creature card" in text or "search your library for a creature" in text:
        tags.update(["creature_tutor", "creature_chain"])
    if "as an additional cost" in text and "sacrifice" in text:
        tags.update(["sacrifice_as_cost", "graveyard_enabler"])
    if "when" in text and "enters" in text and "creature" in tl:
        tags.add("etb_toolbox")

    # Activated ability / Agatha-style support.
    if "activated abilities" in text or "activated ability" in text or re.search(r"\{t\}\s*:", text):
        tags.add("activated_ability_payoff")
    if "activated abilities of creatures you control cost" in text or "abilities of creatures you control cost" in text or "activated abilities cost" in text:
        tags.update(["activated_ability_cost_reduction", "activated_ability_payoff"])
    if "cost less to activate" in text and "power" in text:
        tags.update(["power_based_cost_reduction", "power_matters", "activated_ability_cost_reduction"])
    if any(p in text for p in ["deals 1 damage to any target", "deals 1 damage to each opponent", "deals 1 damage to target", "pinger"]):
        tags.update(["pinger", "damage_payoff", "activated_ability_payoff"])
    if any(p in text for p in ["destroy target", "exile target", "deals damage to target", "fight target"]) and re.search(r"\{t\}\s*:", text):
        tags.update(["repeatable_removal", "activated_ability_payoff"])

    # Equipment / Aura / Voltron / Artifact combat.
    if "equipment" in tl or "equipped creature" in text or "equip " in text:
        tags.update(["equipment_payoff", "attachment_synergy", "equipment_synergy"])
        if any(p in text for p in ["commander", "combat damage", "double strike", "can't be blocked", "trample", "hexproof", "indestructible"]):
            tags.update(["commander_damage_support", "voltron_protection", "combat_damage_trigger"])
    if "aura" in tl or "enchanted creature" in text or "enchant creature" in text:
        tags.update(["aura_payoff", "attachment_synergy", "aura_synergy"])
        if any(p in text for p in ["commander", "combat damage", "can't be blocked", "trample", "hexproof", "indestructible"]):
            tags.update(["commander_damage_support", "voltron_protection"])
    if "artifact creature" in tl or ("artifact" in tl and "combat damage" in text):
        tags.update(["artifact_combat", "artifact_payoff"])

    # Adventure / modal value.
    if "adventure" in text or "on an adventure" in text or "adventurer" in text:
        tags.update(["adventure_spell", "adventure_payoff", "adventure_synergy", "modal_value", "spell_permanent_hybrid"])
    if "you may cast" in text and "from exile" in text:
        tags.update(["cast_from_exile", "adventure_payoff", "card_advantage"])
    if "//" in (card.get("name", "") if card else "") or len(card.get("card_faces", []) or []) > 1:
        tags.update(["modal_value", "alternate_face_value"])

    # Better bracket/combo split: slow alt wins and big haymakers should not be true turbo by default.
    mv = card.get("cmc", 0) or 0 if card else 0
    has_win_text = any(p in text for p in ["you win the game", "each opponent loses the game", "loses the game"])
    fast_context = bool(tags.intersection({"true_fast_mana", "true_ritual", "efficient_tutor", "combo_tutor", "tutor_chain", "combo_protection", "compact_combo_piece", "fast_combo_enabler"}))
    if has_win_text:
        if mv >= 4 and not fast_context:
            tags.update(["slow_alt_win_condition", "bracket_pressure_possible", "win_condition"])
            tags.discard("turbo_combo")
            tags.discard("true_turbo_combo")
        elif fast_context:
            tags.update(["compact_combo_piece", "true_turbo_combo", "bracket_pressure"])
    if mv >= 6 and tags.intersection({"card_advantage", "win_condition", "high_mv_payoff", "big_mana_payoff"}) and not fast_context:
        tags.update(["high_power_value_piece", "bracket_pressure_possible"])
        tags.discard("turbo_combo")

    # Commander-specific context promotion for new archetypes.
    if any(p in commander_text for p in ["activated abilities", "cost less to activate", "power"]):
        if tags.intersection({"activated_ability_payoff", "activated_ability_cost_reduction", "power_based_cost_reduction", "mana_sink", "pinger", "untap_ramp"}):
            tags.add("commander_synergy_possible")
    if any(p in commander_text for p in ["adventure", "on an adventure"]):
        if tags.intersection({"adventure_spell", "adventure_payoff", "modal_value", "spell_permanent_hybrid"}):
            tags.add("commander_synergy_possible")
    if any(p in commander_text for p in ["equipment", "aura", "equipped", "attached"]):
        if tags.intersection({"equipment_payoff", "aura_payoff", "attachment_synergy", "commander_damage_support"}):
            tags.add("commander_synergy_possible")
    if any(p in commander_text for p in ["sacrifice another creature", "search your library for a creature", "mana value equal"]):
        if tags.intersection({"pod_effect", "creature_tutor", "creature_chain", "sacrifice_as_cost", "etb_toolbox"}):
            tags.add("commander_synergy_possible")

    return sorted(tags)


# v0.5.7 density and gate helpers.
def v056_count_any(role_counts, tags):
    return sum(role_counts.get(tag, 0) for tag in tags)


def can_be_primary_ramp_control(role_counts, commander_tags):
    ramp_count = role_counts.get("ramp", 0) + role_counts.get("mana_doubler", 0) + role_counts.get("mana_rock", 0) + role_counts.get("mana_dork", 0)
    control_count = role_counts.get("board_wipe", 0) + role_counts.get("mass_removal", 0) + role_counts.get("targeted_removal", 0) + role_counts.get("counterspell", 0)
    payoff_count = role_counts.get("big_mana_payoff", 0) + role_counts.get("high_mv_payoff", 0) + role_counts.get("mana_sink", 0) + role_counts.get("win_condition", 0)
    commander_support = commander_has_any_tag(commander_tags, {"ramp_control", "big_mana_value", "mana_doubler", "big_mana_payoff", "high_mv_payoff", "mana_sink"})
    return ramp_count >= 10 and control_count >= 6 and payoff_count >= 4 and (commander_support or control_count >= 8)


def can_be_primary_elf_typal(role_counts, commander_tags):
    elf_count = role_counts.get("elf_typal", 0)
    elf_payoff_count = min(role_counts.get("tribal_payoff", 0), elf_count) + min(role_counts.get("tribal_anthem", 0), elf_count)
    commander_elf = commander_has_any_tag(commander_tags, {"elf_typal"})
    return commander_elf or elf_count >= 8 or (elf_count >= 5 and elf_payoff_count >= 3)


def can_be_primary_artifact_treasure_tutor_chain(role_counts, commander_tags):
    commander_artifact_treasure = commander_has_any_tag(commander_tags, {"artifact_treasure_tutor_chain", "treasure_tutor_chain", "treasure_synergy", "artifact_token_synergy", "dwarf_typal"})
    hard_chain = role_counts.get("artifact_treasure_tutor_chain", 0) + role_counts.get("treasure_tutor_chain", 0)
    artifact_token_density = role_counts.get("treasure_synergy", 0) + role_counts.get("artifact_token_synergy", 0) + role_counts.get("artifact_sacrifice", 0)
    tutor_density = role_counts.get("tutor_chain", 0) + role_counts.get("combo_tutor", 0)
    return (commander_artifact_treasure and artifact_token_density >= 4) or hard_chain >= 3 or (artifact_token_density >= 12 and tutor_density >= 3)


def can_be_primary_commander_created_landfall(role_counts, commander_tags):
    commander_landfall = commander_has_any_tag(commander_tags, {"commander_created_package", "rock_token_synergy", "land_token"})
    support_density = role_counts.get("landfall", 0) + role_counts.get("landfall_payoff", 0) + role_counts.get("extra_land_play", 0) + role_counts.get("artifact_token_synergy", 0)
    return commander_landfall and support_density >= 3


def can_be_primary_turbo_combo(role_counts, commander_tags):
    fast_count = role_counts.get("true_fast_mana", 0) + role_counts.get("true_ritual", 0)
    tutor_count = role_counts.get("efficient_tutor", 0) + role_counts.get("combo_tutor", 0) + role_counts.get("tutor_chain", 0)
    combo_count = role_counts.get("true_turbo_combo", 0) + role_counts.get("compact_combo_piece", 0) + role_counts.get("turbo_combo", 0)
    protection_count = role_counts.get("combo_protection", 0) + role_counts.get("free_counterspell", 0) + role_counts.get("silence_effect", 0)
    commander_fast = commander_has_any_tag(commander_tags, {"true_turbo_combo", "fast_combo_enabler", "combo_tutor", "tutor_chain"})
    return combo_count >= 2 and tutor_count >= 3 and (fast_count >= 2 or protection_count >= 2 or commander_fast)


def can_be_primary_dragonstorm_tiamat(role_counts, commander_tags):
    commander_dragon = commander_has_any_tag(commander_tags, {"dragon_typal", "dragonstorm_combo"})
    dragon_count = role_counts.get("dragon_typal", 0)
    tutor_chain = role_counts.get("dragonstorm_combo", 0) + min(role_counts.get("tutor_chain", 0), dragon_count) + min(role_counts.get("combo_tutor", 0), dragon_count)
    return role_counts.get("dragonstorm_combo", 0) >= 1 or (commander_dragon and dragon_count >= 8 and tutor_chain >= 3)


def has_narrower_commander_defined_strategy(role_counts, commander_tags):
    narrow_checks = [
        commander_has_any_tag(commander_tags, {"legendary_cascade", "five_color_value"}) and role_counts.get("legendary_synergy", 0) >= 10,
        commander_has_any_tag(commander_tags, {"token_resource_engine", "tap_token_value"}) and get_token_resource_density(role_counts) >= 20,
        commander_has_any_tag(commander_tags, {"attack_trigger_payoff", "token_maker"}) and role_counts.get("token_maker", 0) >= 8 and role_counts.get("combat_synergy", 0) >= 6,
        commander_has_any_tag(commander_tags, {"commander_created_package", "rock_token_synergy", "land_token"}) and role_counts.get("landfall", 0) >= 2,
        commander_has_any_tag(commander_tags, {"activated_ability_cost_reduction", "power_based_cost_reduction", "activated_ability_synergy", "power_matters"}) and get_agatha_style_density(role_counts) >= 18,
        commander_has_any_tag(commander_tags, {"adventure_synergy", "adventure_spell", "adventure_payoff"}) and role_counts.get("adventure_spell", 0) + role_counts.get("adventure_synergy", 0) >= 4,
        commander_has_any_tag(commander_tags, {"equipment_payoff", "aura_payoff", "attachment_synergy", "equipment_synergy", "aura_synergy"}) and role_counts.get("equipment_synergy", 0) + role_counts.get("aura_synergy", 0) >= 6,
        commander_has_any_tag(commander_tags, {"pod_effect", "creature_tutor", "creature_chain"}) and role_counts.get("creature_tutor", 0) + role_counts.get("pod_effect", 0) >= 2,
        get_toughness_defender_density(role_counts) >= 35,
        get_wheel_draw_punisher_density(role_counts) >= 30,
        get_graveyard_self_mill_density(role_counts) >= 65 and role_counts.get("self_mill", 0) >= 5,
        get_blink_flicker_density(role_counts) >= 18 and role_counts.get("blink_flicker", 0) + role_counts.get("exile_return", 0) >= 1,
        get_dragon_copy_density(role_counts) >= 20 and commander_has_any_tag(commander_tags, {"dragon_typal", "dragon_copy_value", "token_copy_value"}),
    ]
    return any(narrow_checks)


def v056_suppress_score(scores, archetype, reason, multiplier=0.18, ceiling=34):
    if archetype in scores:
        original = scores[archetype].get("score", 0)
        scores[archetype]["score"] = min(int(original * multiplier), ceiling)
        scores[archetype]["evidence"] = scores[archetype].get("evidence", []) + [f"v0.5.7 gate: {reason}"]


def v056_apply_archetype_gates(scores, role_counts, commander_cards):
    commander_tags = get_commander_role_tag_counter(commander_cards)

    if not can_be_primary_ramp_control(role_counts, commander_tags):
        v056_suppress_score(scores, "Ramp-Control / Big Mana Value", "suppressed because ramp/control/payoff gate was not met", 0.22, 42)
    elif has_narrower_commander_defined_strategy(role_counts, commander_tags):
        v056_suppress_score(scores, "Ramp-Control / Big Mana Value", "narrower commander-defined strategy exists; moved toward minor package", 0.45, 70)

    if not can_be_primary_elf_typal(role_counts, commander_tags):
        v056_suppress_score(scores, "Elf Typal / Token Lifedrain", "suppressed because real Elf commander support/density/payoff gate was not met", 0.12, 28)

    if not can_be_primary_artifact_treasure_tutor_chain(role_counts, commander_tags):
        v056_suppress_score(scores, "Artifact/Treasure Tutor Chain", "suppressed because artifact/Treasure tutor-chain gate was not met", 0.16, 35)

    if not can_be_primary_commander_created_landfall(role_counts, commander_tags):
        v056_suppress_score(scores, "Commander-Created Landfall / Artifact Token Engine", "suppressed because commander does not create/reward landfall artifact-token package", 0.10, 24)

    if not can_be_primary_turbo_combo(role_counts, commander_tags):
        v056_suppress_score(scores, "Turbo Combo / Fast Tutor Chain", "suppressed because true turbo combo gate was not met", 0.16, 36)

    if not can_be_primary_dragonstorm_tiamat(role_counts, commander_tags):
        v056_suppress_score(scores, "Dragonstorm / Tiamat Tutor Chain", "suppressed because Dragonstorm/Tiamat tutor-chain gate was not met", 0.18, 38)

    # Promote narrow v0.5.7 archetypes when they clearly fit.
    if role_counts.get("token_maker", 0) >= 8 and role_counts.get("combat_synergy", 0) >= 6 and commander_has_any_tag(commander_tags, {"attack_trigger_payoff", "token_maker", "combat_synergy"}):
        if "Go-Wide / Go-Tall Token Combat" in scores:
            floor = max(scores.get("Ramp-Control / Big Mana Value", {}).get("score", 0), scores.get("Go-Wide Combat", {}).get("score", 0)) + 20
            scores["Go-Wide / Go-Tall Token Combat"]["score"] = max(scores["Go-Wide / Go-Tall Token Combat"].get("score", 0), floor)
            scores["Go-Wide / Go-Tall Token Combat"]["evidence"] = scores["Go-Wide / Go-Tall Token Combat"].get("evidence", []) + ["v0.5.7 priority: commander attack/token/combat plan beats broad Ramp-Control"]

    if role_counts.get("goblin_typal", 0) >= 5 and "Goblin Typal / Go-Wide Tokens" in scores:
        floor = max(scores.get("Elf Typal / Token Lifedrain", {}).get("score", 0), scores.get("Tokens", {}).get("score", 0)) + 20
        scores["Goblin Typal / Go-Wide Tokens"]["score"] = max(scores["Goblin Typal / Go-Wide Tokens"].get("score", 0), floor)
        scores["Goblin Typal / Go-Wide Tokens"]["evidence"] = scores["Goblin Typal / Go-Wide Tokens"].get("evidence", []) + ["v0.5.7 priority: real Goblin typal density beats Elf/generic token labels"]

    if role_counts.get("vampire_typal", 0) >= 4 and (role_counts.get("lifedrain_payoff", 0) + role_counts.get("death_trigger_payoff", 0) + role_counts.get("sacrifice_outlet", 0) >= 5) and "Vampire Tokens / Aristocrats / Drain" in scores:
        floor = max(scores.get("Elf Typal / Token Lifedrain", {}).get("score", 0), scores.get("Aristocrats", {}).get("score", 0)) + 18
        scores["Vampire Tokens / Aristocrats / Drain"]["score"] = max(scores["Vampire Tokens / Aristocrats / Drain"].get("score", 0), floor)
        scores["Vampire Tokens / Aristocrats / Drain"]["evidence"] = scores["Vampire Tokens / Aristocrats / Drain"].get("evidence", []) + ["v0.5.7 priority: Vampire death/drain package beats Elf/Ramp-Control labels"]

    if can_be_primary_pod_toolbox_quality_gate(role_counts, commander_cards) and "Pod / Creature Toolbox / Creature Chain" in scores:
        floor = max(scores.get("Elf Typal / Token Lifedrain", {}).get("score", 0), scores.get("Creature Cost-Reduction / Creature Combo Value", {}).get("score", 0)) + 14
        scores["Pod / Creature Toolbox / Creature Chain"]["score"] = max(scores["Pod / Creature Toolbox / Creature Chain"].get("score", 0), floor)
        scores["Pod / Creature Toolbox / Creature Chain"]["evidence"] = scores["Pod / Creature Toolbox / Creature Chain"].get("evidence", []) + ["v0.5.7 priority: pod/creature-chain evidence beats broad creature/Elf labels"]

    if get_agatha_style_density(role_counts) >= 25 and commander_has_any_tag(commander_tags, {"activated_ability_synergy", "activated_ability_cost_reduction", "power_based_cost_reduction", "power_matters"}) and "Activated Abilities / Power-Reduction Engine" in scores:
        floor = max(scores.get("Ramp-Control / Big Mana Value", {}).get("score", 0), scores.get("Activated Abilities", {}).get("score", 0)) + 18
        scores["Activated Abilities / Power-Reduction Engine"]["score"] = max(scores["Activated Abilities / Power-Reduction Engine"].get("score", 0), floor)
        scores["Activated Abilities / Power-Reduction Engine"]["evidence"] = scores["Activated Abilities / Power-Reduction Engine"].get("evidence", []) + ["v0.5.7 priority: commander activated ability/power-reduction engine beats Ramp-Control"]

    if (role_counts.get("equipment_synergy", 0) + role_counts.get("aura_synergy", 0) + role_counts.get("equipment_payoff", 0) + role_counts.get("aura_payoff", 0) >= 8) and "Equipment / Aura Voltron" in scores:
        floor = max(scores.get("Ramp-Control / Big Mana Value", {}).get("score", 0), scores.get("Voltron", {}).get("score", 0)) + 14
        scores["Equipment / Aura Voltron"]["score"] = max(scores["Equipment / Aura Voltron"].get("score", 0), floor)
        scores["Equipment / Aura Voltron"]["evidence"] = scores["Equipment / Aura Voltron"].get("evidence", []) + ["v0.5.7 priority: equipment/aura density beats broad Ramp-Control/Legends labels"]

    if (role_counts.get("adventure_spell", 0) + role_counts.get("adventure_synergy", 0) + role_counts.get("adventure_payoff", 0) >= 5) and "Adventure / Modal Value" in scores:
        floor = max(scores.get("Ramp-Control / Big Mana Value", {}).get("score", 0), scores.get("Spellslinger", {}).get("score", 0)) + 14
        scores["Adventure / Modal Value"]["score"] = max(scores["Adventure / Modal Value"].get("score", 0), floor)
        scores["Adventure / Modal Value"]["evidence"] = scores["Adventure / Modal Value"].get("evidence", []) + ["v0.5.7 priority: adventure/modal density beats Ramp-Control"]

    if (role_counts.get("artifact_untapper", 0) + role_counts.get("mana_engine_support", 0) + role_counts.get("artifact_payoff", 0) + role_counts.get("artifact_token_synergy", 0) >= 10) and "Artifact Engine / Artifact Tap / Artifact Mana" in scores:
        floor = max(scores.get("Ramp-Control / Big Mana Value", {}).get("score", 0), scores.get("Artifacts", {}).get("score", 0)) + 12
        scores["Artifact Engine / Artifact Tap / Artifact Mana"]["score"] = max(scores["Artifact Engine / Artifact Tap / Artifact Mana"].get("score", 0), floor)
        scores["Artifact Engine / Artifact Tap / Artifact Mana"]["evidence"] = scores["Artifact Engine / Artifact Tap / Artifact Mana"].get("evidence", []) + ["v0.5.7 priority: artifact tap/mana engine beats generic Ramp-Control"]

    if (role_counts.get("sphinx_typal", 0) >= 4 and role_counts.get("topdeck_manipulation", 0) + role_counts.get("card_selection", 0) >= 4) and "Sphinx Typal / Topdeck Cost Reduction" in scores:
        floor = max(scores.get("Topdeck / Permanent-Type Value", {}).get("score", 0), scores.get("Ramp-Control / Big Mana Value", {}).get("score", 0)) + 12
        scores["Sphinx Typal / Topdeck Cost Reduction"]["score"] = max(scores["Sphinx Typal / Topdeck Cost Reduction"].get("score", 0), floor)
        scores["Sphinx Typal / Topdeck Cost Reduction"]["evidence"] = scores["Sphinx Typal / Topdeck Cost Reduction"].get("evidence", []) + ["v0.5.7 priority: Sphinx typal/topdeck package beats generic Topdeck/Ramp-Control"]

    if (role_counts.get("mana_sink", 0) + role_counts.get("big_mana_payoff", 0) + role_counts.get("mana_doubler", 0) + role_counts.get("untap_ramp", 0) >= 10) and not can_be_primary_ramp_control(role_counts, commander_tags) and "Big Mana / Mana Storage" in scores:
        floor = max(scores.get("Ramp-Control / Big Mana Value", {}).get("score", 0), scores.get("Ramp into Big Threats", {}).get("score", 0)) + 12
        scores["Big Mana / Mana Storage"]["score"] = max(scores["Big Mana / Mana Storage"].get("score", 0), floor)
        scores["Big Mana / Mana Storage"]["evidence"] = scores["Big Mana / Mana Storage"].get("evidence", []) + ["v0.5.7 priority: big mana/mana-sink engine beats control when control gate fails"]

    return scores


_v055_score_archetypes = score_archetypes


# ==============================
# v0.5.7 Strategy Gate / Reconciliation Helpers
# ==============================
BROAD_ARCHETYPES_V057 = {
    "Ramp-Control / Big Mana Value", "Go-Wide / Go-Tall Token Combat", "Go-Wide Combat",
    "Activated Abilities / Power-Reduction Engine", "Activated Abilities",
    "Artifact Engine / Artifact Tap / Artifact Mana", "Artifact/Treasure Tutor Chain",
    "Treasure / Artifact Token Engine", "Tokens", "Artifacts", "Control",
}


def v057_clean_evidence(evidence):
    cleaned = []
    seen = set()
    for item in evidence or []:
        text = str(item)
        # Collapse old stacked priority notes into a single user-readable note.
        if "priority correction" in text or "gate" in text:
            key = re.sub(r"v0\.5\.\d+(?:hotfix)?\s*", "", text)
        else:
            key = text
        if key not in seen:
            seen.add(key)
            cleaned.append(text)
    return cleaned[:12]


def can_be_primary_token_combat_v057(role_counts, commander_tags):
    commander_support = commander_has_any_tag(commander_tags, {"attack_trigger_payoff", "combat_synergy", "token_maker", "go_wide_token_engine", "counter_synergy"})
    token_count = role_counts.get("token_maker", 0)
    combat_package = role_counts.get("combat_synergy", 0) + role_counts.get("anthem", 0) + role_counts.get("counter_synergy", 0) + role_counts.get("attack_trigger_payoff", 0)
    finisher_count = role_counts.get("win_condition", 0) + role_counts.get("extra_combat", 0) + role_counts.get("anthem", 0)
    return (commander_support and token_count >= 6 and combat_package >= 8) or (token_count >= 10 and finisher_count >= 2)


def can_be_primary_activated_v057(role_counts, commander_tags):
    commander_support = commander_has_any_tag(commander_tags, {"activated_ability_payoff", "activated_ability_cost_reduction", "activated_ability_engine", "power_matters", "mana_sink"})
    real_activated = role_counts.get("activated_ability_payoff", 0) + role_counts.get("activated_ability_cost_reduction", 0) + role_counts.get("activated_ability_engine", 0)
    payoff = role_counts.get("win_condition", 0) + role_counts.get("damage_payoff", 0) + role_counts.get("card_draw", 0)
    return commander_support or (real_activated >= 8 and role_counts.get("mana_sink", 0) >= 3 and payoff >= 2)


def can_be_primary_artifact_engine_v057(role_counts, commander_tags):
    commander_support = commander_has_any_tag(commander_tags, {"artifact_payoff", "artifact_token_synergy", "artifact_sacrifice", "treasure_synergy", "clue_synergy", "food_synergy"})
    artifact_payoff = role_counts.get("artifact_payoff", 0) + role_counts.get("artifact_sacrifice", 0) + role_counts.get("artifact_token_synergy", 0)
    token_economy = role_counts.get("treasure_synergy", 0) + role_counts.get("clue_synergy", 0) + role_counts.get("food_synergy", 0)
    return artifact_payoff >= 8 and (commander_support or token_economy >= 6 or role_counts.get("artifact_sacrifice", 0) >= 4)


def can_be_primary_treasure_tutor_v057(role_counts, commander_tags):
    signals = 0
    if commander_has_any_tag(commander_tags, {"artifact_treasure_tutor_chain", "treasure_tutor_chain", "treasure_synergy", "artifact_token_synergy", "dwarf_typal"}):
        signals += 1
    if role_counts.get("treasure_synergy", 0) + role_counts.get("artifact_token_synergy", 0) >= 10:
        signals += 1
    if role_counts.get("artifact_sacrifice", 0) + role_counts.get("artifact_payoff", 0) >= 6:
        signals += 1
    if role_counts.get("tutor_chain", 0) + role_counts.get("combo_tutor", 0) >= 5:
        signals += 1
    if role_counts.get("win_condition", 0) >= 2 and role_counts.get("treasure_tutor_chain", 0) >= 1:
        signals += 1
    return signals >= 2


def commander_has_pod_effect_v057(commander_cards):
    for c in commander_cards or []:
        txt = normalize_text(get_full_oracle_text(c))
        if "sacrifice" in txt and "search your library" in txt and "creature card" in txt:
            return True
    return False




def can_be_primary_pod_toolbox_quality_gate(role_counts, commander_cards):
    """Quality gate for Pod / Creature Toolbox.

    The deck helper was over-promoting Pod/Toolbox from generic creature density, ETB value,
    and a few tutors. For primary strategy, require actual pod/chain/tutor-package evidence
    or commander text that explicitly supports creature upgrade/tutor lines.
    """
    if commander_has_pod_effect_v057(commander_cards):
        return True

    pod_core = (
        role_counts.get("pod_effect", 0) * 3
        + role_counts.get("creature_tutor", 0) * 2
        + role_counts.get("creature_chain", 0) * 2
        + role_counts.get("sacrifice_as_cost", 0)
    )
    toolbox_value = role_counts.get("etb_toolbox", 0) + role_counts.get("etb_value", 0) + role_counts.get("recursion", 0)

    # Real pod/toolbox decks need more than creatures + ETB cards.
    if role_counts.get("pod_effect", 0) >= 2:
        return True
    if role_counts.get("creature_tutor", 0) >= 4 and role_counts.get("creature_chain", 0) >= 2:
        return True
    if pod_core >= 10 and toolbox_value >= 6:
        return True
    return False

def commander_has_dragon_tutor_v057(commander_cards):
    for c in commander_cards or []:
        txt = normalize_text(get_full_oracle_text(c))
        typ = normalize_text(c.get("type_line", ""))
        if "dragon" in typ and "search your library" in txt and "dragon" in txt:
            return True
    return False


def v057_apply_gates_and_reconcile(scores, role_counts, commander_cards):
    commander_tags = get_commander_role_tag_counter(commander_cards)
    result = {name: dict(data) for name, data in scores.items()}
    diagnostics = []

    def suppress(name, multiplier, reason):
        if name in result:
            old = result[name].get("score", 0)
            result[name]["raw_score"] = result[name].get("raw_score", old)
            result[name]["score"] = int(old * multiplier)
            result[name]["gate_passed"] = False
            result[name]["gate_failed_reason"] = reason
            result[name]["suppression_reason"] = reason
            evidence = result[name].get("evidence", [])
            evidence.append(reason)
            result[name]["evidence"] = v057_clean_evidence(evidence)
            diagnostics.append(f"{name}: {old} -> {result[name]['score']} ({reason})")

    # Stronger gates for overfiring candidates.
    if not can_be_primary_ramp_control(role_counts, commander_tags):
        suppress("Ramp-Control / Big Mana Value", 0.45, "Failed ramp-control gate: ramp alone is not enough without control density and big-mana payoff density.")
    if not can_be_primary_elf_typal(role_counts, commander_tags):
        suppress("Elf Typal / Token Lifedrain", 0.25, "Failed Elf typal gate: not enough Elf commander/density/payoff support.")
    if not can_be_primary_treasure_tutor_v057(role_counts, commander_tags):
        suppress("Artifact/Treasure Tutor Chain", 0.45, "Failed artifact/Treasure tutor-chain gate: artifact/Treasure signals are not central enough.")
    if not can_be_primary_token_combat_v057(role_counts, commander_tags):
        for name in ["Go-Wide / Go-Tall Token Combat", "Go-Wide Combat"]:
            suppress(name, 0.65, "Failed token-combat gate: token/combat signals look like support, not primary identity.")
    if not can_be_primary_activated_v057(role_counts, commander_tags):
        for name in ["Activated Abilities / Power-Reduction Engine", "Activated Abilities"]:
            suppress(name, 0.55, "Failed activated-ability gate: incidental or mana-only activated abilities excluded from primary strategy.")
    if not can_be_primary_artifact_engine_v057(role_counts, commander_tags):
        suppress("Artifact Engine / Artifact Tap / Artifact Mana", 0.50, "Failed artifact-engine gate: mana rocks/artifact tokens alone are not enough for primary artifact identity.")

    if not can_be_primary_pod_toolbox_quality_gate(role_counts, commander_cards):
        suppress("Pod / Creature Toolbox / Creature Chain", 0.40, "Failed Pod/Toolbox gate: generic creature density, ETB value, and a few tutors are not enough for primary Pod identity.")

    # Specific commander-defined priority corrections.
    if commander_has_pod_effect_v057(commander_cards) and "Pod / Creature Toolbox / Creature Chain" in result:
        pod_score = result["Pod / Creature Toolbox / Creature Chain"].get("score", 0)
        activated_score = max(result.get("Activated Abilities", {}).get("score", 0), result.get("Activated Abilities / Power-Reduction Engine", {}).get("score", 0))
        result["Pod / Creature Toolbox / Creature Chain"]["score"] = max(pod_score, activated_score + 25)
        result["Pod / Creature Toolbox / Creature Chain"]["gate_passed"] = True
        result["Pod / Creature Toolbox / Creature Chain"]["primary_eligible"] = True
        result["Pod / Creature Toolbox / Creature Chain"]["suppression_reason"] = "Commander has pod-style creature tutor text; creature toolbox takes priority over generic activated abilities."
    if commander_has_dragon_tutor_v057(commander_cards) and "Dragonstorm / Tiamat Tutor Chain" in result:
        best_other = max((data.get("score",0) for name,data in result.items() if name != "Dragonstorm / Tiamat Tutor Chain"), default=0)
        result["Dragonstorm / Tiamat Tutor Chain"]["score"] = max(result["Dragonstorm / Tiamat Tutor Chain"].get("score",0), best_other + 10)
        result["Dragonstorm / Tiamat Tutor Chain"]["gate_passed"] = True
        result["Dragonstorm / Tiamat Tutor Chain"]["primary_eligible"] = True
        result["Dragonstorm / Tiamat Tutor Chain"]["suppression_reason"] = "Dragon tutor commander detected; Dragon tutor-chain takes priority when package exists."

    for data in result.values():
        data.setdefault("raw_score", data.get("score", 0))
        data.setdefault("adjusted_score", data.get("score", 0))
        data.setdefault("gate_passed", True)
        data.setdefault("gate_failed_reason", "")
        data.setdefault("strategy_layer", "scored_candidate")
        data.setdefault("primary_eligible", data.get("score", 0) > 0)
        data["evidence"] = v057_clean_evidence(data.get("evidence", []))
    result["__v057_diagnostics__"] = {"suppression_rules_triggered": diagnostics}
    return result

def score_archetypes(role_counts, type_counts, commander_cards):
    scores = _v055_score_archetypes(role_counts, type_counts, commander_cards)
    return v056_apply_archetype_gates(scores, role_counts, commander_cards)


_v055_apply_strategy_priority_corrections = apply_strategy_priority_corrections

def apply_strategy_priority_corrections(archetype_scores, role_counts, commander_cards):
    corrected = _v055_apply_strategy_priority_corrections(archetype_scores, role_counts, commander_cards)
    return v056_apply_archetype_gates(corrected, role_counts, commander_cards)


_v055_get_strategy_confidence_warning = get_strategy_confidence_warning

def get_strategy_confidence_warning(primary_strategy, secondary_strategy, primary_data, secondary_data, role_counts):
    warnings = list(_v055_get_strategy_confidence_warning(primary_strategy, secondary_strategy, primary_data, secondary_data, role_counts))
    if primary_strategy in V056_BROAD_ARCHETYPES:
        warnings.append("v0.5.7 gate check: primary strategy is a broad/high-pressure archetype; verify gates and suppression evidence before cuts.")
    if primary_strategy == "Ramp-Control / Big Mana Value":
        warnings.append("Ramp-Control should be primary only when ramp, real control density, and big-mana payoffs are all present.")
    if primary_strategy == "Elf Typal / Token Lifedrain":
        warnings.append("Elf Typal should be primary only with real Elf commander support, Elf density, or Elf payoffs.")
    return warnings


def get_strategy_minor_packages(ordered_archetypes, primary_strategy, secondary_strategy):
    packages = []
    for name, data in ordered_archetypes:
        if name in {primary_strategy, secondary_strategy}:
            continue
        score = data.get("score", 0)
        evidence = "; ".join(data.get("evidence", [])[:3]) if data.get("evidence") else "limited evidence"
        if 25 <= score <= 90 or "v0.5.7 gate" in evidence or "suppressed" in evidence.lower():
            packages.append((name, score, evidence))
        if len(packages) >= 6:
            break
    return packages


_v055_build_cut_pressure_review = build_cut_pressure_review

def build_cut_pressure_review(cards, unique_cards, scryfall_lookup, card_role_tags_by_card, card_plan_fit_buckets, commander_name_set, primary_strategy, secondary_strategy, role_tag_counts, tribal_support_flags, average_nonland_mana_value, cut_strictness="normal"):
    review = _v055_build_cut_pressure_review(cards, unique_cards, scryfall_lookup, card_role_tags_by_card, card_plan_fit_buckets, commander_name_set, primary_strategy, secondary_strategy, role_tag_counts, tribal_support_flags, average_nonland_mana_value, cut_strictness)
    deck_size = len(cards)
    deck_short_count = max(0, 100 - deck_size)
    review["deck_short_count"] = deck_short_count
    review["deck_is_underfilled"] = deck_size < 100
    review["deck_is_overfilled"] = deck_size > 100

    # Do not present fallback candidates as normal required cuts in massively over-limit decks.
    manual_required_review = []
    confident_required = []
    for item in review.get("required_cuts_list", []):
        if item.get("category") == "Required Cut Fallback" or item.get("score", 0) <= 0:
            manual_required_review.append({
                **item,
                "manual_review_reason": "Deck is over 100 cards, but this is not a confident cut. Review manually before removing.",
            })
        else:
            confident_required.append(item)
    review["required_cuts_list"] = confident_required
    review["required_cuts_requiring_manual_review"] = manual_required_review[:12]
    review["additional_required_cuts_needed"] = max(0, review.get("required_cuts", 0) - len(confident_required) - len(manual_required_review[:12]))
    review["required_cut_shortfall"] = review["additional_required_cuts_needed"]

    if deck_short_count > 0:
        review["required_cuts"] = 0
        review["required_cuts_list"] = []
        review["required_cuts_requiring_manual_review"] = []
        review["additional_required_cuts_needed"] = 0
        review["required_cut_shortfall"] = 0

    # Underfilled decks should prioritize additions rather than cut pressure.
    if deck_short_count > 0:
        addition_needs = []
        land_count = role_tag_counts.get("land", 0)
        if land_count and land_count < 35:
            addition_needs.append("More lands")
        if role_tag_counts.get("ramp", 0) < 10:
            addition_needs.append("More ramp")
        if role_tag_counts.get("card_draw", 0) + role_tag_counts.get("card_advantage", 0) < 10:
            addition_needs.append("More card draw")
        if role_tag_counts.get("targeted_removal", 0) < 8:
            addition_needs.append("More targeted removal")
        if role_tag_counts.get("commander_synergy_possible", 0) < 8:
            addition_needs.append("More commander synergy")
        if not addition_needs:
            addition_needs.append("More primary-plan support")
        review["addition_needs"] = addition_needs
    else:
        review["addition_needs"] = []

    return review


_v055_build_possible_cut_review = build_possible_cut_review

def build_possible_cut_review(cut_pressure_review, unique_cards, scryfall_lookup, card_role_tags_by_card, card_plan_fit_buckets, primary_strategy, secondary_strategy, role_tag_counts, scryfall_land_count, average_nonland_mana_value, bracket_read=None):
    review = _v055_build_possible_cut_review(cut_pressure_review, unique_cards, scryfall_lookup, card_role_tags_by_card, card_plan_fit_buckets, primary_strategy, secondary_strategy, role_tag_counts, scryfall_land_count, average_nonland_mana_value, bracket_read)

    if cut_pressure_review.get("deck_is_underfilled"):
        # Underfilled decks can still show possible review flags, but should not turn them into recommended cuts.
        review["recommended_cuts"] = []
        review["deck_needs"] = list(dict.fromkeys(cut_pressure_review.get("addition_needs", []) + review.get("deck_needs", [])))

    no_cuts_found = (
        cut_pressure_review.get("required_cuts", 0) == 0
        and not review.get("recommended_cuts")
        and not review.get("possible_cuts")
        and not cut_pressure_review.get("optional_cuts_list")
        and not cut_pressure_review.get("deck_is_underfilled")
    )
    refined_candidates = []
    if no_cuts_found:
        seen = set()
        sources = []
        for item in cut_pressure_review.get("context_dependent", []):
            sources.append((item.get("card_name"), item.get("questionable", "Context-dependent card."), item.get("might_belong", "May support a hidden or narrow synergy role.")))
        for entry in review.get("playtest_before_cutting", []):
            sources.append((entry.get("card_name"), entry.get("why_questionable", "Playtest-first card."), entry.get("why_might_belong", "May still belong based on deck context.")))
        # If still empty, pull from protected utility with wording that these are watch cards, not cuts.
        for entry in review.get("protected_from_cut", []):
            sources.append((entry.get("card_name"), "Protected card, but watch whether this role is redundant in practice.", entry.get("reason", "Supports the deck plan.")))
        for card_name, why_watch, why_belongs in sources:
            if not card_name or card_name in seen:
                continue
            seen.add(card_name)
            refined_candidates.append({
                "card_name": card_name,
                "label": "Playtest-first review candidate",
                "why_to_watch": why_watch,
                "why_it_may_belong": why_belongs,
                "watch_for": "Does this card meaningfully affect games when drawn, or does it sit behind stronger engine pieces?",
            })
            if len(refined_candidates) >= 5:
                break
    review["refined_deck_review_candidates"] = refined_candidates
    return review



# ==============================
# v0.5.7 HOTFIX: layered strategy scoring + bracket separation
# ==============================
HOTFIX_VERSION = "v0.5.7"

HOTFIX_EXTRA_TAGS = [
    # strategy layers
    "macro_archetype_support","micro_archetype_support","typal_support","niche_theme_support",
    "fringe_theme_support","emergent_theme_support","commander_defined_support",
    "support_package_card","minor_package_card","manual_review_package_card","bracket_modifier","power_signal",
    # typal roles
    "typal_lord","typal_cost_reducer","typal_token_maker","typal_tutor","typal_card_draw",
    "typal_recursion","typal_reanimation","typal_sacrifice_payoff","typal_combat_payoff",
    "typal_counter_payoff","typal_lifegain_payoff","typal_artifact_payoff","typal_etb_payoff",
    "typal_death_payoff","typal_attack_trigger","typal_damage_trigger","typal_protection",
    "typal_changeling_support","typal_multiple_copy_exception","typal_density_piece","typal_bridge_card",
    "token_typal_density","incidental_creature_type","sliver_typal","merfolk_typal","angel_typal",
    "demon_typal","dinosaur_typal","spirit_typal","myr_typal","artifact_creature_typal",
    # politics/table-fit
    "political_card","group_draw","group_ramp","gift_resource","tablewide_acceleration","table_damage",
    "punisher","spell_punisher","attack_punisher","goad","forced_attack","attack_elsewhere_incentive",
    "combat_restriction","rattlesnake","revenge_trigger","voting","monarch","initiative","bounty",
    "curse","negotiated_removal","threat_redistribution","donate_bad_gift","resource_redistribution",
    "symmetrical_rule","table_police","soft_lock","board_reset","villain_pressure","reputation_pressure",
    "kingmaker_risk","table_dependency","salt_risk","stall_risk",
    # niche/fringe/emergent
    "energy_generator","energy_payoff","food_generator","food_payoff","blood_generator","blood_payoff",
    "clue_generator","clue_payoff","dice_roll","dice_payoff","coin_flip","coin_flip_payoff","mutate",
    "venture","repeatable_venture","dungeon_payoff","initiative_enabler","initiative_payoff","vehicle",
    "crew_enabler","pilot_token","gate","gate_payoff","shrine","shrine_payoff","opponent_mill",
    "repeatable_mill","infect","toxic","corrupted_payoff","poison_payoff","foretell","suspend",
    "discover","exile_payoff","rule_zero_only","nonstandard_legality","outside_game_component",
    "acorn_card","silver_border","attractions","stickers","contraptions","social_contract_pressure",
    "meta_dependent_hate","self_synergy_conflict_possible","flavor_first_piece","package_dependency_piece",
    "color_hate","life_exchange","hellbent","level_up","class_enchantment","cave","locus","splice_arcane",
    "clash","fateseal","adamant","renown","bloodthirst","commander_defined_engine","resource_conversion",
    "conversion_point","bridge_card","high_synergy_low_power","generically_good_wrong_shell",
    "token_combat_hybrid","go_wide_go_tall_hybrid","crime_trigger","crime_enabler","outlaw_typal","plot",
    "offspring","gift","forage","expend","room","eerie","manifest_dread","face_down_support","survival",
    "tapped_creature_payoff","artifact_treasure_combo_value","visible_win_condition",
    "protected_setup_required","high_power_value_not_turbo","not_turbo_combo"
]
for _hotfix_tag in HOTFIX_EXTRA_TAGS:
    if _hotfix_tag not in ROLE_TAGS:
        ROLE_TAGS.append(_hotfix_tag)

LOW_RAW_POWER_CONTEXT_TAGS.update({
    "typal_density_piece","typal_bridge_card","typal_token_maker","typal_cost_reducer",
    "commander_defined_engine","commander_defined_support","bridge_card","conversion_point",
    "resource_conversion","high_synergy_low_power","political_card","niche_theme_support",
    "fringe_theme_support","emergent_theme_support","manual_review_package_card"
})
HIGH_SYNERGY_LOW_RAW_POWER_TAGS.update(LOW_RAW_POWER_CONTEXT_TAGS)

HOTFIX_BROAD_PRIMARY_RISK = set(V056_BROAD_ARCHETYPES) | {
    "Aggro","Midrange / Value","Control","Ramp / Big Mana","Ramp-Control / Big Mana Value",
    "Engine / Synergy Value","Combo-adjacent Value","Combo","Goodstuff","Generic Tokens",
    "Generic Artifacts","Generic Goodstuff","Generic Value","Generic Control","Generic Ramp",
    "Ramp into Big Threats","Turbo Combo / Fast Tutor Chain"
}
HOTFIX_ARCHETYPE_LAYER = {
    "Commander-Created Landfall / Artifact Token Engine":"commander_defined_emergent",
    "Go-Wide / Go-Tall Token Combat":"commander_defined_emergent",
    "Token Resource Engine":"commander_defined_emergent",
    "Treasure Tutor Chain":"commander_defined_emergent",
    "Artifact/Treasure Tutor Chain":"commander_defined_emergent",
    "Dragonstorm / Tiamat Tutor Chain":"commander_defined_emergent",
    "Activated Abilities / Power-Reduction Engine":"commander_defined_emergent",
    "Artifact Engine / Artifact Tap / Artifact Mana":"commander_defined_emergent",
    "Big Mana / Mana Storage":"commander_defined_emergent",
    "Aristocrats":"mechanical_micro_archetype","Sacrifice":"mechanical_micro_archetype",
    "Voltron":"mechanical_micro_archetype","Equipment / Aura Voltron":"mechanical_micro_archetype",
    "Artifact Combat":"mechanical_micro_archetype","Spellslinger":"mechanical_micro_archetype",
    "Spellslinger / Amass Army":"mechanical_micro_archetype","Blink/Flicker / ETB Value":"mechanical_micro_archetype",
    "Landfall":"mechanical_micro_archetype","Reanimator":"mechanical_micro_archetype",
    "Graveyard Recursion":"mechanical_micro_archetype","Graveyard Self-Mill / Recursion":"mechanical_micro_archetype",
    "Artifacts":"mechanical_micro_archetype","Enchantress":"mechanical_micro_archetype","Tokens":"mechanical_micro_archetype",
    "+1/+1 Counters":"mechanical_micro_archetype","Lifegain":"mechanical_micro_archetype",
    "Wheels / Draw-Punisher / Group Slug":"mechanical_micro_archetype",
    "Pod / Creature Toolbox / Creature Chain":"mechanical_micro_archetype",
    "Adventure / Modal Value":"mechanical_micro_archetype",
    "Creature Cost-Reduction / Creature Combo Value":"mechanical_micro_archetype",
    "Cascade / Big Mana Value":"mechanical_micro_archetype",
    "Suspend / Big Spell Cheat":"mechanical_micro_archetype",
    "Topdeck / Permanent-Type Value":"mechanical_micro_archetype",
    "Copy / Clone Value":"mechanical_micro_archetype",
    "Dragon Copy / Token-Copy Value":"mechanical_micro_archetype",
    "Toughness Matters / Defender":"mechanical_micro_archetype",
    "Eldrazi / Colorless Big Mana":"mechanical_micro_archetype",
    "Elf Typal / Token Lifedrain":"typal_strategy_shape",
    "Goblin Typal / Go-Wide Tokens":"typal_strategy_shape",
    "Vampire Tokens / Aristocrats / Drain":"typal_strategy_shape",
    "Dragon Typal":"typal_strategy_shape",
    "Sphinx Typal / Topdeck Cost Reduction":"typal_strategy_shape",
    "Legends Matter / Legendary Cascade":"typal_strategy_shape",
    "Politics":"political_strategy","Group Hug":"political_strategy","Group Slug":"political_strategy",
    "Pillowfort":"political_strategy","Forced Combat / Goad":"political_strategy",
    "Aikido / Judo":"political_strategy","Table Police":"political_strategy","Stax / Prison":"political_strategy",
}
HOTFIX_LAYER_PRIORITY = {
    "commander_defined_emergent":0,"mechanical_micro_archetype":1,"typal_strategy_shape":2,
    "political_strategy":3,"niche_theme":4,"fringe_theme":5,"macro_archetype":6,"manual_review":7
}
HOTFIX_BRACKET_ONLY_TAGS = {
    "game_changer","bracket_pressure","high_bracket_pressure","bracket_pressure_possible","fast_mana",
    "true_fast_mana","free_interaction","free_counterspell","efficient_tutor","mass_land_denial",
    "social_contract_pressure","salt_risk","reputation_pressure","archenemy_pressure","bracket_modifier","power_signal"
}

def hotfix_get_layer(archetype_name):
    if archetype_name in HOTFIX_ARCHETYPE_LAYER:
        return HOTFIX_ARCHETYPE_LAYER[archetype_name]
    if archetype_name in HOTFIX_BROAD_PRIMARY_RISK:
        return "macro_archetype"
    return "mechanical_micro_archetype"

def hotfix_commander_text(commander_cards):
    return normalize_text(" ".join(get_full_oracle_text(c) + " " + c.get("type_line", "") for c in (commander_cards or [])))

def hotfix_commander_has_landfall_engine(commander_cards):
    text = hotfix_commander_text(commander_cards)
    return any(p in text for p in [
        "whenever a land enters","whenever one or more lands enter","land enters the battlefield under your control",
        "landfall","create a colorless rock artifact token","rock artifact token","artifact token named rock",
        "whenever you play a land"
    ])

def hotfix_true_turbo_combo_gate(role_counts):
    return (
        role_counts.get("true_fast_mana", 0) + role_counts.get("fast_mana", 0) >= 3
        and role_counts.get("efficient_tutor", 0) + role_counts.get("combo_tutor", 0) >= 3
        and role_counts.get("compact_combo_piece", 0) + role_counts.get("combo_piece_possible", 0) + role_counts.get("true_turbo_combo", 0) >= 1
        and role_counts.get("combo_protection", 0) + role_counts.get("silence_effect", 0) + role_counts.get("free_counterspell", 0) >= 2
    )

def hotfix_can_be_primary_politics(role_counts, commander_tags):
    political_signal_count = sum(role_counts.get(t,0) for t in [
        "group_draw","group_ramp","gift_resource","table_damage","punisher","spell_punisher",
        "draw_punisher","attack_punisher","goad","forced_attack","attack_elsewhere_incentive",
        "pillowfort","attack_tax","combat_prevention","rattlesnake","voting","monarch","initiative",
        "bounty","curse","negotiated_removal","threat_redistribution","table_police"
    ])
    political_payoff_count = sum(role_counts.get(t,0) for t in [
        "political_payoff","asymmetrical_payoff","damage_payoff","draw_punisher","lifedrain_payoff",
        "table_damage","win_condition","alternate_win_condition"
    ])
    commander_support = commander_has_any_tag(commander_tags, set(HOTFIX_EXTRA_TAGS))
    has_win_path = political_payoff_count >= 2 or role_counts.get("win_condition",0) >= 1
    return political_signal_count >= 6 and political_payoff_count >= 2 and (commander_support or political_signal_count >= 9) and has_win_path

def hotfix_suppress_score(scores, archetype, reason, multiplier=0.10, ceiling=24):
    if archetype in scores:
        original = scores[archetype].get("score", 0)
        scores[archetype]["score"] = min(int(original * multiplier), ceiling)
        scores[archetype]["evidence"] = scores[archetype].get("evidence", []) + [f"v0.5.7 gate: {reason}"]


def get_commander_role_tags(commander_cards):
    """Return inferred command-zone role tags as a Counter-like mapping.

    v0.5.7 support helper:
    The existing commander_has_any_tag() helper expects a mapping with .get(tag, 0),
    so this must return Counter rather than a set.
    """
    combined_tags = Counter()
    for commander_card in commander_cards or []:
        try:
            inferred = infer_card_role_tags(commander_card, commander_cards=[])
        except TypeError:
            inferred = infer_card_role_tags(commander_card)
        except Exception:
            inferred = ["manual_review"]

        for tag in inferred:
            combined_tags[tag] += 1

    return combined_tags


def commander_has_any_tag_from_cards(commander_cards, wanted_tags):
    commander_tags = get_commander_role_tags(commander_cards)
    return any(commander_tags.get(tag, 0) > 0 for tag in set(wanted_tags))

def hotfix_gate_and_suppress_scores(scores, role_counts, commander_cards):
    commander_tags = get_commander_role_tags(commander_cards)
    landfall_commander = hotfix_commander_has_landfall_engine(commander_cards)
    if "Ramp-Control / Big Mana Value" in scores and not can_be_primary_ramp_control(role_counts, commander_tags):
        hotfix_suppress_score(scores, "Ramp-Control / Big Mana Value", "Ramp-Control failed layered gate; ramp alone is not a primary strategy", 0.06, 18)
    if "Elf Typal / Token Lifedrain" in scores:
        elf_density = role_counts.get("elf_typal",0) + role_counts.get("typal_density",0)
        elf_payoff = role_counts.get("tribal_payoff",0)+role_counts.get("typal_lord",0)+role_counts.get("typal_token_maker",0)+role_counts.get("lifedrain_payoff",0)
        elf_commander = commander_has_any_tag(commander_tags, {"elf_typal","tribal_payoff","lifedrain_payoff"})
        if not ((elf_density >= 18 and elf_payoff >= 4) or (elf_commander and elf_density >= 12 and elf_payoff >= 3)):
            hotfix_suppress_score(scores, "Elf Typal / Token Lifedrain", "Elf Typal failed effective typal density/payoff gate", 0.05, 16)
    if "Artifact/Treasure Tutor Chain" in scores and not can_be_primary_artifact_treasure_tutor_chain(role_counts, commander_tags):
        hotfix_suppress_score(scores, "Artifact/Treasure Tutor Chain", "artifact/treasure tutor-chain gate failed; artifacts and Treasures appear to be support or bracket signals", 0.07, 20)
    if "Commander-Created Landfall / Artifact Token Engine" in scores and not landfall_commander:
        hotfix_suppress_score(scores, "Commander-Created Landfall / Artifact Token Engine", "commander text does not directly create or reward a landfall artifact-token package", 0.03, 12)
    if "Turbo Combo / Fast Tutor Chain" in scores and not hotfix_true_turbo_combo_gate(role_counts):
        hotfix_suppress_score(scores, "Turbo Combo / Fast Tutor Chain", "true turbo combo gate failed; bracket pressure or slow alternate wins do not equal turbo", 0.04, 14)
    if "Dragonstorm / Tiamat Tutor Chain" in scores and not can_be_primary_dragonstorm_tiamat(role_counts, commander_tags):
        hotfix_suppress_score(scores, "Dragonstorm / Tiamat Tutor Chain", "Dragon tutor-chain gate failed; treat as Dragon support or bracket review instead of primary", 0.12, 28)
    for political_name in ["Politics","Group Hug","Group Slug","Pillowfort","Forced Combat / Goad","Aikido / Judo","Table Police"]:
        if political_name in scores and not hotfix_can_be_primary_politics(role_counts, commander_tags):
            hotfix_suppress_score(scores, political_name, "political strategy failed incentive/protection/payoff/inevitability gate", 0.20, 34)
    bracket_density = sum(role_counts.get(t,0) for t in HOTFIX_BRACKET_ONLY_TAGS)
    if bracket_density >= 4:
        for broad_name in ["Turbo Combo / Fast Tutor Chain","Ramp-Control / Big Mana Value","Control","Combo","Combo-adjacent Value"]:
            if broad_name in scores:
                scores[broad_name]["evidence"] = scores[broad_name].get("evidence", []) + ["v0.5.7 note: bracket/power tags are report modifiers and should not independently define primary strategy"]
    return scores

_hotfix_prev_score_archetypes = score_archetypes

# ==============================
# v0.5.7 Strategy Gate / Reconciliation Helpers
# ==============================
BROAD_ARCHETYPES_V057 = {
    "Ramp-Control / Big Mana Value", "Go-Wide / Go-Tall Token Combat", "Go-Wide Combat",
    "Activated Abilities / Power-Reduction Engine", "Activated Abilities",
    "Artifact Engine / Artifact Tap / Artifact Mana", "Artifact/Treasure Tutor Chain",
    "Treasure / Artifact Token Engine", "Tokens", "Artifacts", "Control",
}


def v057_clean_evidence(evidence):
    cleaned = []
    seen = set()
    for item in evidence or []:
        text = str(item)
        # Collapse old stacked priority notes into a single user-readable note.
        if "priority correction" in text or "gate" in text:
            key = re.sub(r"v0\.5\.\d+(?:hotfix)?\s*", "", text)
        else:
            key = text
        if key not in seen:
            seen.add(key)
            cleaned.append(text)
    return cleaned[:12]


def can_be_primary_token_combat_v057(role_counts, commander_tags):
    commander_support = commander_has_any_tag(commander_tags, {"attack_trigger_payoff", "combat_synergy", "token_maker", "go_wide_token_engine", "counter_synergy"})
    token_count = role_counts.get("token_maker", 0)
    combat_package = role_counts.get("combat_synergy", 0) + role_counts.get("anthem", 0) + role_counts.get("counter_synergy", 0) + role_counts.get("attack_trigger_payoff", 0)
    finisher_count = role_counts.get("win_condition", 0) + role_counts.get("extra_combat", 0) + role_counts.get("anthem", 0)
    return (commander_support and token_count >= 6 and combat_package >= 8) or (token_count >= 10 and finisher_count >= 2)


def can_be_primary_activated_v057(role_counts, commander_tags):
    commander_support = commander_has_any_tag(commander_tags, {"activated_ability_payoff", "activated_ability_cost_reduction", "activated_ability_engine", "power_matters", "mana_sink"})
    real_activated = role_counts.get("activated_ability_payoff", 0) + role_counts.get("activated_ability_cost_reduction", 0) + role_counts.get("activated_ability_engine", 0)
    payoff = role_counts.get("win_condition", 0) + role_counts.get("damage_payoff", 0) + role_counts.get("card_draw", 0)
    return commander_support or (real_activated >= 8 and role_counts.get("mana_sink", 0) >= 3 and payoff >= 2)


def can_be_primary_artifact_engine_v057(role_counts, commander_tags):
    commander_support = commander_has_any_tag(commander_tags, {"artifact_payoff", "artifact_token_synergy", "artifact_sacrifice", "treasure_synergy", "clue_synergy", "food_synergy"})
    artifact_payoff = role_counts.get("artifact_payoff", 0) + role_counts.get("artifact_sacrifice", 0) + role_counts.get("artifact_token_synergy", 0)
    token_economy = role_counts.get("treasure_synergy", 0) + role_counts.get("clue_synergy", 0) + role_counts.get("food_synergy", 0)
    return artifact_payoff >= 8 and (commander_support or token_economy >= 6 or role_counts.get("artifact_sacrifice", 0) >= 4)


def can_be_primary_treasure_tutor_v057(role_counts, commander_tags):
    signals = 0
    if commander_has_any_tag(commander_tags, {"artifact_treasure_tutor_chain", "treasure_tutor_chain", "treasure_synergy", "artifact_token_synergy", "dwarf_typal"}):
        signals += 1
    if role_counts.get("treasure_synergy", 0) + role_counts.get("artifact_token_synergy", 0) >= 10:
        signals += 1
    if role_counts.get("artifact_sacrifice", 0) + role_counts.get("artifact_payoff", 0) >= 6:
        signals += 1
    if role_counts.get("tutor_chain", 0) + role_counts.get("combo_tutor", 0) >= 5:
        signals += 1
    if role_counts.get("win_condition", 0) >= 2 and role_counts.get("treasure_tutor_chain", 0) >= 1:
        signals += 1
    return signals >= 2


def commander_has_pod_effect_v057(commander_cards):
    for c in commander_cards or []:
        txt = normalize_text(get_full_oracle_text(c))
        if "sacrifice" in txt and "search your library" in txt and "creature card" in txt:
            return True
    return False




def can_be_primary_pod_toolbox_quality_gate(role_counts, commander_cards):
    """Quality gate for Pod / Creature Toolbox.

    The deck helper was over-promoting Pod/Toolbox from generic creature density, ETB value,
    and a few tutors. For primary strategy, require actual pod/chain/tutor-package evidence
    or commander text that explicitly supports creature upgrade/tutor lines.
    """
    if commander_has_pod_effect_v057(commander_cards):
        return True

    pod_core = (
        role_counts.get("pod_effect", 0) * 3
        + role_counts.get("creature_tutor", 0) * 2
        + role_counts.get("creature_chain", 0) * 2
        + role_counts.get("sacrifice_as_cost", 0)
    )
    toolbox_value = role_counts.get("etb_toolbox", 0) + role_counts.get("etb_value", 0) + role_counts.get("recursion", 0)

    # Real pod/toolbox decks need more than creatures + ETB cards.
    if role_counts.get("pod_effect", 0) >= 2:
        return True
    if role_counts.get("creature_tutor", 0) >= 4 and role_counts.get("creature_chain", 0) >= 2:
        return True
    if pod_core >= 10 and toolbox_value >= 6:
        return True
    return False

def commander_has_dragon_tutor_v057(commander_cards):
    for c in commander_cards or []:
        txt = normalize_text(get_full_oracle_text(c))
        typ = normalize_text(c.get("type_line", ""))
        if "dragon" in typ and "search your library" in txt and "dragon" in txt:
            return True
    return False


def v057_apply_gates_and_reconcile(scores, role_counts, commander_cards):
    commander_tags = get_commander_role_tag_counter(commander_cards)
    result = {name: dict(data) for name, data in scores.items()}
    diagnostics = []

    def suppress(name, multiplier, reason):
        if name in result:
            old = result[name].get("score", 0)
            result[name]["raw_score"] = result[name].get("raw_score", old)
            result[name]["score"] = int(old * multiplier)
            result[name]["gate_passed"] = False
            result[name]["gate_failed_reason"] = reason
            result[name]["suppression_reason"] = reason
            evidence = result[name].get("evidence", [])
            evidence.append(reason)
            result[name]["evidence"] = v057_clean_evidence(evidence)
            diagnostics.append(f"{name}: {old} -> {result[name]['score']} ({reason})")

    # Stronger gates for overfiring candidates.
    if not can_be_primary_ramp_control(role_counts, commander_tags):
        suppress("Ramp-Control / Big Mana Value", 0.45, "Failed ramp-control gate: ramp alone is not enough without control density and big-mana payoff density.")
    if not can_be_primary_elf_typal(role_counts, commander_tags):
        suppress("Elf Typal / Token Lifedrain", 0.25, "Failed Elf typal gate: not enough Elf commander/density/payoff support.")
    if not can_be_primary_treasure_tutor_v057(role_counts, commander_tags):
        suppress("Artifact/Treasure Tutor Chain", 0.45, "Failed artifact/Treasure tutor-chain gate: artifact/Treasure signals are not central enough.")
    if not can_be_primary_token_combat_v057(role_counts, commander_tags):
        for name in ["Go-Wide / Go-Tall Token Combat", "Go-Wide Combat"]:
            suppress(name, 0.65, "Failed token-combat gate: token/combat signals look like support, not primary identity.")
    if not can_be_primary_activated_v057(role_counts, commander_tags):
        for name in ["Activated Abilities / Power-Reduction Engine", "Activated Abilities"]:
            suppress(name, 0.55, "Failed activated-ability gate: incidental or mana-only activated abilities excluded from primary strategy.")
    if not can_be_primary_artifact_engine_v057(role_counts, commander_tags):
        suppress("Artifact Engine / Artifact Tap / Artifact Mana", 0.50, "Failed artifact-engine gate: mana rocks/artifact tokens alone are not enough for primary artifact identity.")

    if not can_be_primary_pod_toolbox_quality_gate(role_counts, commander_cards):
        suppress("Pod / Creature Toolbox / Creature Chain", 0.40, "Failed Pod/Toolbox gate: generic creature density, ETB value, and a few tutors are not enough for primary Pod identity.")

    # Specific commander-defined priority corrections.
    if commander_has_pod_effect_v057(commander_cards) and "Pod / Creature Toolbox / Creature Chain" in result:
        pod_score = result["Pod / Creature Toolbox / Creature Chain"].get("score", 0)
        activated_score = max(result.get("Activated Abilities", {}).get("score", 0), result.get("Activated Abilities / Power-Reduction Engine", {}).get("score", 0))
        result["Pod / Creature Toolbox / Creature Chain"]["score"] = max(pod_score, activated_score + 25)
        result["Pod / Creature Toolbox / Creature Chain"]["gate_passed"] = True
        result["Pod / Creature Toolbox / Creature Chain"]["primary_eligible"] = True
        result["Pod / Creature Toolbox / Creature Chain"]["suppression_reason"] = "Commander has pod-style creature tutor text; creature toolbox takes priority over generic activated abilities."
    if commander_has_dragon_tutor_v057(commander_cards) and "Dragonstorm / Tiamat Tutor Chain" in result:
        best_other = max((data.get("score",0) for name,data in result.items() if name != "Dragonstorm / Tiamat Tutor Chain"), default=0)
        result["Dragonstorm / Tiamat Tutor Chain"]["score"] = max(result["Dragonstorm / Tiamat Tutor Chain"].get("score",0), best_other + 10)
        result["Dragonstorm / Tiamat Tutor Chain"]["gate_passed"] = True
        result["Dragonstorm / Tiamat Tutor Chain"]["primary_eligible"] = True
        result["Dragonstorm / Tiamat Tutor Chain"]["suppression_reason"] = "Dragon tutor commander detected; Dragon tutor-chain takes priority when package exists."

    for data in result.values():
        data.setdefault("raw_score", data.get("score", 0))
        data.setdefault("adjusted_score", data.get("score", 0))
        data.setdefault("gate_passed", True)
        data.setdefault("gate_failed_reason", "")
        data.setdefault("strategy_layer", "scored_candidate")
        data.setdefault("primary_eligible", data.get("score", 0) > 0)
        data["evidence"] = v057_clean_evidence(data.get("evidence", []))
    result["__v057_diagnostics__"] = {"suppression_rules_triggered": diagnostics}
    return result

def score_archetypes(role_counts, type_counts, commander_cards):
    scores = _hotfix_prev_score_archetypes(role_counts, type_counts, commander_cards)
    return hotfix_gate_and_suppress_scores(scores, role_counts, commander_cards)

_hotfix_prev_apply_strategy_priority_corrections = apply_strategy_priority_corrections
def apply_strategy_priority_corrections(archetype_scores, role_counts, commander_cards):
    corrected = _hotfix_prev_apply_strategy_priority_corrections(archetype_scores, role_counts, commander_cards)
    return hotfix_gate_and_suppress_scores(corrected, role_counts, commander_cards)

_hotfix_prev_choose_primary_secondary_strategy = choose_primary_secondary_strategy
def choose_primary_secondary_strategy(archetype_scores):
    ordered = sorted(archetype_scores.items(), key=lambda item: item[1].get("score",0), reverse=True)
    if not ordered:
        return "Unclear", {"score":0}, "Unclear", {"score":0}, []
    for name, data in ordered:
        data["strategy_layer"] = hotfix_get_layer(name)
        data["is_broad_primary_risk"] = name in HOTFIX_BROAD_PRIMARY_RISK
    top_score = ordered[0][1].get("score",0)
    viable = [(n,d) for n,d in ordered if d.get("score",0) >= max(24, top_score*0.22)]
    layered = []
    for name, data in viable:
        score = data.get("score",0)
        layer = hotfix_get_layer(name)
        ev = " ".join(data.get("evidence", []))
        suppressed = ("suppressed" in ev.lower() or "failed" in ev.lower()) and name in HOTFIX_BROAD_PRIMARY_RISK
        if suppressed:
            continue
        if name in HOTFIX_BROAD_PRIMARY_RISK and any(hotfix_get_layer(n)!="macro_archetype" and dd.get("score",0)>=max(30, score*0.38) for n,dd in viable):
            continue
        priority = HOTFIX_LAYER_PRIORITY.get(layer,6)
        adjusted = score + ((7-priority)*3) - (18 if name in HOTFIX_BROAD_PRIMARY_RISK else 0)
        layered.append((priority, -adjusted, -score, name, data))
    if layered:
        layered.sort()
        primary_name, primary_data = layered[0][3], layered[0][4]
    else:
        primary_name, primary_data = ordered[0]
    secondary_name, secondary_data = "Unclear", {"score":0}
    for name, data in ordered:
        if name == primary_name:
            continue
        if data.get("score",0) < max(22, primary_data.get("score",0)*0.25):
            continue
        if name in HOTFIX_BROAD_PRIMARY_RISK and hotfix_get_layer(primary_name)!="macro_archetype" and data.get("score",0) < primary_data.get("score",0)*0.85:
            continue
        secondary_name, secondary_data = name, data
        break
    if secondary_name == "Unclear":
        for name, data in ordered:
            if name != primary_name:
                secondary_name, secondary_data = name, data
                break
    return primary_name, primary_data, secondary_name, secondary_data, ordered

_hotfix_prev_infer_card_role_tags = infer_card_role_tags
def infer_card_role_tags(card, commander_cards=None):
    tags = set(_hotfix_prev_infer_card_role_tags(card, commander_cards))
    type_line = card.get("type_line","") or ""
    tl = type_line.lower()
    text = normalize_text(type_line + "\n" + get_full_oracle_text(card))
    commander_text = hotfix_commander_text(commander_cards or [])
    if tags.intersection({"ramp","card_draw","targeted_removal","board_wipe","counterspell","stax_piece","tutor","mana_sink","big_mana_payoff"}):
        tags.add("macro_archetype_support")
    if tags.intersection({"sacrifice_outlet","death_trigger_payoff","blink_flicker","landfall","reanimation","artifact_payoff","token_maker","lifegain_payoff","spell_payoff","equipment_synergy","aura_synergy"}):
        tags.add("micro_archetype_support")
    if any(p in text for p in ["untap target land","untap up to one target land","untap all lands","untap each land"]):
        tags.update({"untap_ramp","land_untapper","mana_engine_support","micro_archetype_support"})
    if any(p in text for p in ["untap target permanent","untap another target permanent","untap each permanent","untap all permanents"]):
        tags.update({"untap_ramp","permanent_untapper","mana_engine_support","micro_archetype_support"})
    if any(p in text for p in ["untap target artifact","untap all artifacts","untap each artifact"]):
        tags.update({"untap_ramp","artifact_untapper","mana_engine_support","artifact_payoff"})
    if "activated abilities" in text or "activated ability" in text or "abilities cost" in text or "cost less to activate" in text:
        tags.update({"activated_ability_payoff","activated_ability_cost_reduction","micro_archetype_support"})
    if "power" in text and ("activated" in text or "activate" in text or "cost" in text):
        tags.update({"power_based_cost_reduction","power_matters","emergent_theme_support"})
    if "sacrifice" in text and "search your library" in text and "creature" in text:
        tags.update({"pod_effect","creature_tutor","creature_chain","sacrifice_as_cost","micro_archetype_support"})
    if "search your library for a creature" in text:
        tags.update({"creature_tutor","creature_chain"})
    if "equipment" in tl or "equip" in text or "equipped creature" in text:
        tags.update({"equipment_payoff","attachment_synergy","equipment_synergy","micro_archetype_support"})
    if "aura" in tl or "enchant creature" in text or "enchanted creature" in text:
        tags.update({"aura_payoff","attachment_synergy","aura_synergy","micro_archetype_support"})
    if any(p in text for p in ["equip abilities","equip costs","attach target equipment","attach an equipment"]):
        tags.update({"equip_cost_reduction","equipment_payoff"})
    if "adventure" in text or "adventurer" in text or "on an adventure" in text:
        tags.update({"adventure_spell","adventure_payoff","modal_value","cast_from_exile","spell_permanent_hybrid","niche_theme_support"})
    if "cast from exile" in text or "you may play that card for as long as it remains exiled" in text or "you may cast that card for as long as it remains exiled" in text:
        tags.update({"cast_from_exile","exile_payoff","niche_theme_support"})
    creature_subtypes = {s.lower() for s in get_creature_subtypes(type_line)}
    if "creature" in tl and creature_subtypes:
        tags.update({"tribal_body","typal_density"})
        for subtype in creature_subtypes:
            specific = f"{subtype}_typal"
            if specific in ROLE_TAGS:
                tags.add(specific)
    if "choose a creature type" in text or "creature type" in text:
        tags.update({"typal_support","typal_bridge_card"})
    if any(p in text for p in ["creatures you control get","other creatures you control get","creatures of the chosen type get","creatures you control of the chosen type"]):
        tags.update({"typal_lord","typal_combat_payoff","tribal_payoff","typal_support"})
    if "create" in text and "token" in text:
        for tribe in ["goblin","vampire","zombie","soldier","spirit","dragon","elf","sphinx","human","rabbit","thopter","saproling","squirrel","bat"]:
            if tribe in text:
                tags.update({"typal_token_maker","token_typal_density","typal_support"})
                specific = f"{tribe}_typal"
                if specific in ROLE_TAGS:
                    tags.add(specific)
    for tribe in ["dragon","goblin","vampire","sphinx","zombie","elf","human","soldier","wizard"]:
        if tribe in text or tribe in tl:
            specific = f"{tribe}_typal"
            if specific in ROLE_TAGS:
                tags.update({specific,"typal_support"})
    if any(p in text for p in ["each player draws","each opponent draws","players draw","opponent draws"]):
        tags.update({"political_card","group_draw"})
    if any(p in text for p in ["each player may put a land","each player may search","each player adds"]):
        tags.update({"political_card","group_ramp","tablewide_acceleration"})
    if "goad" in text or "attacks a player other than you" in text or "must attack" in text:
        tags.update({"political_card","goad","forced_attack","attack_elsewhere_incentive"})
    if any(p in text for p in ["can't attack you","unless their controller pays","prevent all combat damage","creatures can't attack"]):
        tags.update({"political_card","pillowfort","attack_tax"})
    if "vote" in text or "council" in text:
        tags.update({"political_card","voting"})
    if "monarch" in text:
        tags.update({"political_card","monarch"})
    if "curse" in tl or "enchanted player" in text:
        tags.update({"political_card","curse"})
    if "energy" in text:
        tags.update({"energy_generator" if "get" in text or "you get" in text else "energy_payoff","niche_theme_support"})
    if "food" in text:
        tags.update({"food_generator" if "create" in text else "food_payoff","niche_theme_support"})
    if "blood token" in text or "blood tokens" in text:
        tags.update({"blood_generator" if "create" in text else "blood_payoff","niche_theme_support"})
    if "clue" in text or "investigate" in text:
        tags.update({"clue_generator","niche_theme_support"})
    if ("roll" in text and "die" in text) or "d20" in text:
        tags.update({"dice_roll","niche_theme_support"})
    if "coin flip" in text or "flip a coin" in text:
        tags.update({"coin_flip","niche_theme_support"})
    if "mutate" in text:
        tags.update({"mutate","niche_theme_support"})
    if "venture into the dungeon" in text:
        tags.update({"venture","dungeon_payoff","niche_theme_support"})
    if "take the initiative" in text:
        tags.update({"initiative_enabler","initiative","political_card","niche_theme_support"})
    if "vehicle" in tl or "crew" in text:
        tags.update({"vehicle","crew_enabler","niche_theme_support"})
    if "gate" in tl:
        tags.update({"gate","niche_theme_support"})
    if "shrine" in tl:
        tags.update({"shrine","niche_theme_support"})
    if "attraction" in text or "sticker" in text or "contraption" in text or "acorn" in text:
        tags.update({"fringe_theme_support","rule_zero_only","outside_game_component","manual_review_package_card"})
    if "destroy all lands" in text or "lands don't untap" in text:
        tags.update({"social_contract_pressure","mass_land_denial","bracket_modifier","pregame_discussion_piece"})
    if hotfix_commander_has_landfall_engine(commander_cards or []) and tags.intersection({"landfall","lands_matter","land_ramp","extra_land_play","rock_token_synergy","artifact_token_synergy","token_maker","ramp"}):
        tags.update({"commander_defined_support","commander_defined_engine","emergent_theme_support"})
    if tags.intersection({"token_maker","anthem","combat_synergy","power_matters","attack_trigger_payoff"}) and any(p in commander_text for p in ["attacks","attacking","create","token","power"]):
        tags.update({"token_combat_hybrid","go_wide_go_tall_hybrid","emergent_theme_support"})
    if "committed a crime" in text or "commit a crime" in text:
        tags.update({"crime_trigger","crime_enabler","emergent_theme_support"})
    if any(t in tl for t in ["assassin","mercenary","pirate","rogue","warlock"]):
        tags.update({"outlaw_typal","typal_support"})
    if "plot" in text:
        tags.update({"plot","cast_from_exile","emergent_theme_support"})
    if "offspring" in text:
        tags.update({"offspring","token_maker","etb_value","emergent_theme_support"})
    if "gift" in text and "promised" in text:
        tags.update({"gift","political_card","gift_resource","emergent_theme_support"})
    if "forage" in text:
        tags.update({"forage","food_payoff","graveyard_enabler","emergent_theme_support"})
    if "expend" in text:
        tags.update({"expend","mana_sink","emergent_theme_support"})
    if "room" in tl or "unlock" in text or "eerie" in text:
        tags.update({"room","eerie","enchantress","emergent_theme_support"})
    if "manifest dread" in text:
        tags.update({"manifest_dread","face_down_support","graveyard_enabler","emergent_theme_support"})
    if "survival" in text and "second main phase" in text:
        tags.update({"survival","tapped_creature_payoff","emergent_theme_support"})
    if tags.intersection(HOTFIX_BRACKET_ONLY_TAGS):
        tags.update({"bracket_modifier","power_signal"})
    if any(p in text for p in ["you win the game","wins the game","can't lose the game"]):
        tags.update({"slow_alt_win_condition","visible_win_condition","protected_setup_required","not_turbo_combo","bracket_modifier"})
        tags.discard("turbo_combo")
    if "creature" in tl and len(tags.intersection({"card_draw","ramp","targeted_removal","board_wipe","token_maker","recursion","protection","tribal_body","typal_density"})) == 0:
        tags.update({"tribal_body","attack_body","manual_review_package_card"})
    return tags

HOTFIX_NON_TRIBAL_WORDS = V056_NON_TRIBAL_WORDS | {"time","times","turn","turns","phase","phases","combat","card","cards","spell","spells","token","tokens","counter","counters","damage","life","mana","artifact","creature","creatures","permanent","permanents","opponent","opponents","player","players"}

_hotfix_prev_get_referenced_creature_types = get_referenced_creature_types
def get_referenced_creature_types(oracle_text):
    return {ref for ref in _hotfix_prev_get_referenced_creature_types(oracle_text) if ref.lower() not in HOTFIX_NON_TRIBAL_WORDS}

def get_tribal_dependency_types(oracle_text):
    text = normalize_text(oracle_text)
    found = set()
    for ctype in get_referenced_creature_types(oracle_text):
        lower = ctype.lower()
        if lower in HOTFIX_NON_TRIBAL_WORDS:
            continue
        plural = lower + "s"
        patterns = [
            rf"\b{lower}\s+you\s+control\b", rf"\b{plural}\s+you\s+control\b",
            rf"\bother\s+{plural}\b", rf"\bother\s+{lower}s\b",
            rf"\bwhenever\s+a\s+{lower}\b", rf"\bwhenever\s+another\s+{lower}\b",
            rf"\bwhenever\s+one\s+or\s+more\s+{plural}\b", rf"\bequipped\s+{lower}\b",
            rf"\b{lower}\s+spells\s+you\s+cast\b", rf"\bchoose\s+a\s+creature\s+type\b",
            rf"\bcreate\s+(a|one\s+or\s+more).*{lower}.*token\b",
        ]
        if any(re.search(p, text) for p in patterns):
            found.add(ctype)
    return found

def get_tribal_payoff_types(oracle_text):
    text = normalize_text(oracle_text)
    found = set()
    for ctype in get_referenced_creature_types(oracle_text):
        lower = ctype.lower()
        if lower in HOTFIX_NON_TRIBAL_WORDS:
            continue
        plural = lower + "s"
        patterns = [
            rf"\b{plural}\s+you\s+control\s+get\b", rf"\b{lower}s\s+you\s+control\s+get\b",
            rf"\bother\s+{plural}\s+you\s+control\b", rf"\bother\s+{lower}s\s+you\s+control\b",
            rf"\bwhenever\s+a\s+{lower}\s+you\s+control\b", rf"\bwhenever\s+another\s+{lower}\b",
            rf"\bwhenever\s+one\s+or\s+more\s+{plural}\b", rf"\bfor\s+each\s+{lower}\b",
            rf"\bfor\s+each\s+{plural}\b", rf"\bchoose\s+a\s+creature\s+type\b", rf"\bchosen\s+type\b",
        ]
        if any(re.search(p, text) for p in patterns):
            found.add(ctype)
    return found

_hotfix_prev_get_strategy_confidence_warning = get_strategy_confidence_warning
def get_strategy_confidence_warning(primary_strategy, secondary_strategy, primary_data, secondary_data, role_counts):
    warnings = list(_hotfix_prev_get_strategy_confidence_warning(primary_strategy, secondary_strategy, primary_data, secondary_data, role_counts))
    primary_layer = primary_data.get("strategy_layer", hotfix_get_layer(primary_strategy)) if isinstance(primary_data, dict) else hotfix_get_layer(primary_strategy)
    secondary_layer = secondary_data.get("strategy_layer", hotfix_get_layer(secondary_strategy)) if isinstance(secondary_data, dict) else hotfix_get_layer(secondary_strategy)
    if primary_strategy in HOTFIX_BROAD_PRIMARY_RISK:
        warnings.append("v0.5.7: Primary strategy is still broad. Treat it as fallback unless no commander-defined, micro, typal, political, niche, fringe, or emergent plan passed gates.")
    if primary_layer == "macro_archetype" and secondary_layer != "macro_archetype" and secondary_data.get("score",0) >= primary_data.get("score",0)*0.35:
        warnings.append(f"v0.5.7: {secondary_strategy} is a narrower layer than {primary_strategy}; review whether broad primary should be suppressed.")
    if role_counts.get("bracket_modifier",0) + role_counts.get("power_signal",0) >= 4:
        warnings.append("v0.5.7: Bracket/power tags detected. They should be reported as table-fit modifiers, not archetype evidence by themselves.")
    return list(dict.fromkeys(warnings))

_hotfix_prev_estimate_bracket_read = estimate_bracket_read
def estimate_bracket_read(unique_cards, card_role_tags_by_card, primary_strategy, secondary_strategy, role_tag_counts, game_changer_names, intended_bracket="Unknown"):
    bracket_read = _hotfix_prev_estimate_bracket_read(unique_cards, card_role_tags_by_card, primary_strategy, secondary_strategy, role_tag_counts, game_changer_names, intended_bracket)
    bracket_read["combo_centrality"] = (
        "true_turbo_combo" if hotfix_true_turbo_combo_gate(role_tag_counts) else
        "combo_primary_or_high_pressure" if role_tag_counts.get("combo_piece_possible",0) >= 2 and role_tag_counts.get("efficient_tutor",0) >= 2 else
        "combo_adjacent_value" if role_tag_counts.get("combo_piece_possible",0) >= 2 else
        "possible_combo_piece_manual_review" if role_tag_counts.get("combo_piece_possible",0) == 1 else
        "no_combo_detected"
    )
    bracket_read["true_turbo_combo_gate_passed"] = hotfix_true_turbo_combo_gate(role_tag_counts)
    bracket_read["political_salt_risk_count"] = sum(role_tag_counts.get(t,0) for t in ["salt_risk","social_contract_pressure","mass_land_denial","stax_piece","reputation_pressure"])
    bracket_read["rule_zero_review_count"] = sum(role_tag_counts.get(t,0) for t in ["rule_zero_only","outside_game_component","nonstandard_legality","attractions","stickers","contraptions"])
    bracket_read["hotfix_note"] = "Bracket pressure is a table-fit modifier, not primary strategy evidence and not an automatic cut."
    return bracket_read

_hotfix_prev_determine_replacement_categories = determine_replacement_categories
def determine_replacement_categories(candidate, card, tags, cut_type, primary_strategy, secondary_strategy, role_tag_counts, deck_needs):
    categories = list(_hotfix_prev_determine_replacement_categories(candidate, card, tags, cut_type, primary_strategy, secondary_strategy, role_tag_counts, deck_needs))
    if tags.intersection({"typal_support","typal_density","typal_token_maker","tribal_payoff"}):
        categories.extend(["More typal density","More typal payoff"])
    if tags.intersection({"political_card","table_dependency","kingmaker_risk"}):
        categories.extend(["More political payoff","More asymmetrical payoff","More table-friendly interaction"])
    if tags.intersection({"niche_theme_support"}):
        categories.extend(["More niche enablers","More niche payoffs"])
    if tags.intersection({"fringe_theme_support","rule_zero_only","outside_game_component"}):
        categories.extend(["Commander-legal alternatives","Theme-preserving replacements"])
    if tags.intersection({"bracket_modifier","bracket_pressure","high_bracket_pressure","game_changer"}):
        categories.extend(["More bracket-appropriate alternatives","Pregame discussion note"])
    if tags.intersection({"commander_defined_engine","bridge_card","conversion_point","resource_conversion"}):
        categories.extend(["More commander-specific enablers","More bridge cards","More conversion points"])
    return list(dict.fromkeys([c for c in categories if c]))[:5]


# ==============================
# v0.5.7 Cut Depth / Role Balance / Attribute Relevance Helpers
# ==============================
def compute_role_balance_v057(role_counts, land_count):
    counts = {
        "lands": land_count,
        "ramp": role_counts.get("ramp", 0),
        "card_draw": role_counts.get("card_draw", 0) + role_counts.get("card_advantage", 0),
        "targeted_removal": role_counts.get("targeted_removal", 0),
        "board_wipes": role_counts.get("board_wipe", 0) + role_counts.get("mass_removal", 0),
        "protection": role_counts.get("protection", 0),
        "recursion": role_counts.get("recursion", 0),
        "finishers": role_counts.get("win_condition", 0) + role_counts.get("high_mv_payoff", 0),
        "tutors": role_counts.get("tutor", 0) + role_counts.get("efficient_tutor", 0),
        "graveyard_setup": role_counts.get("graveyard_enabler", 0) + role_counts.get("self_mill", 0),
        "token_production": role_counts.get("token_maker", 0),
        "sacrifice_outlets": role_counts.get("sacrifice_outlet", 0) + role_counts.get("free_sacrifice_outlet", 0),
        "mana_fixing": role_counts.get("mana_fixing", 0),
    }
    floors = {"ramp": 8, "card_draw": 8, "targeted_removal": 6, "board_wipes": 2, "protection": 3}
    underfilled = [role for role, floor in floors.items() if counts.get(role, 0) < floor]
    healthy = [role for role, floor in floors.items() if floor <= counts.get(role, 0) <= max(floor + 4, floor * 2)]
    overfilled = [role for role, floor in floors.items() if counts.get(role, 0) > max(floor + 4, floor * 2)]
    return {"counts": counts, "underfilled": underfilled, "healthy": healthy, "overfilled": overfilled}


def entry_is_removal_v057(entry, card_role_tags_by_card):
    tags = set(entry.get("tags", [])) or set(card_role_tags_by_card.get(entry.get("card_name", ""), []))
    return bool(tags.intersection({"targeted_removal", "board_wipe", "mass_removal", "counterspell", "stack_interaction"}))


def apply_cut_depth_and_removal_protection_v057(review, card_role_tags_by_card, role_counts, land_count, deck_count, strategy_confidence="Medium"):
    balance = compute_role_balance_v057(role_counts, land_count)
    mode = CUT_DEPTH_CONFIG.get("mode", "normal")
    target = int(CUT_DEPTH_CONFIG.get("optional_cut_target", 5))
    review["cut_depth_mode"] = mode
    review["optional_cut_target"] = target
    review["role_balance"] = balance
    review.setdefault("diagnostic_warnings", [])

    # Underfilled decks are addition-first.
    if deck_count < 100:
        review["recommended_cuts"] = []
        review["underfilled_addition_first_note"] = "This deck is short cards. Do not remove cards unless intentionally rebuilding; prioritize additions first."
        review["possible_cuts"] = [e for e in review.get("possible_cuts", []) if not entry_is_removal_v057(e, card_role_tags_by_card)][:min(3, target)]
        review["deck_needs"] = ["Addition: reach 100 cards before cutting"] + review.get("deck_needs", [])
        return review

    interaction_low = "targeted_removal" in balance["underfilled"] or "board_wipes" in balance["underfilled"]
    removal_moved = []
    kept_recommended = []
    for entry in review.get("recommended_cuts", []):
        if entry_is_removal_v057(entry, card_role_tags_by_card) and (interaction_low or strategy_confidence in {"Low", "Manual Review Recommended"}) and mode == "normal":
            entry["confidence"] = "Low"
            entry["reason"] = "This is a possible review candidate only if the deck has enough interaction elsewhere. It does not strongly advance the main synergy plan, but removal is still a necessary deck function."
            removal_moved.append(entry)
        else:
            kept_recommended.append(entry)
    if removal_moved:
        review["recommended_cuts"] = kept_recommended
        review["possible_cuts"] = removal_moved + review.get("possible_cuts", [])
        review["diagnostic_warnings"].append("Removal protection moved one or more interaction cuts from recommended to possible review.")

    # If too many candidates are interaction, warn.
    candidates = review.get("recommended_cuts", []) + review.get("possible_cuts", [])
    if candidates:
        removal_count = sum(1 for e in candidates if entry_is_removal_v057(e, card_role_tags_by_card))
        if removal_count / max(1, len(candidates)) > 0.30:
            review["diagnostic_warnings"].append("Warning: Cut candidate list may be over-targeting interaction. Review removal protection and role balance before final recommendations.")

    # Respect cut-depth target without forcing weak candidates.
    review["possible_cuts"] = review.get("possible_cuts", [])[:target]
    review["actual_responsible_cut_candidates_found"] = len(review.get("recommended_cuts", [])) + len(review.get("possible_cuts", []))
    if review["actual_responsible_cut_candidates_found"] < target:
        review["target_shortfall_note"] = f"Only {review['actual_responsible_cut_candidates_found']} responsible optional/recommended cut candidates were found, even though {mode} mode requested {target}. Do not force weak cuts."
    return review


def classify_attribute_relevance_v057(card_name, raw_tags, primary_tags, secondary_tags, role_counts):
    raw_tags = sorted(set(raw_tags or []))
    relevant, ignored, manual = [], [], []
    direct_tags = set(primary_tags) | set(secondary_tags) | ESSENTIAL_UTILITY_TAGS | {"win_condition", "manual_review", "bracket_pressure", "high_bracket_pressure", "game_changer"}
    for tag in raw_tags:
        if tag in direct_tags:
            relevant.append(tag)
        elif tag in {"creature_type_present", "incidental_creature_type", "typal_density_piece", "elf_typal", "dwarf_typal", "dragon_typal"}:
            ignored.append((tag, "Technically true, but typal relevance requires deckwide density or commander support."))
        elif tag in {"mana_rock", "mana_source", "utility_land", "mana_ability_only"}:
            ignored.append((tag, "Mana-base or shell support; not strategy evidence by itself."))
        elif tag in {"pilot_intent_needed", "manual_review", "slow_alt_win_condition", "life_total_manipulation"}:
            manual.append(tag)
            relevant.append(tag)
        else:
            ignored.append((tag, "Raw tag not used in user-facing reasoning unless the deck context supports it."))
    return {"card_name": card_name, "raw": raw_tags, "relevant": relevant, "ignored": ignored[:8], "manual_review": manual}

_hotfix_prev_build_possible_cut_review = build_possible_cut_review
def build_possible_cut_review(cut_pressure_review, unique_cards, scryfall_lookup, card_role_tags_by_card, card_plan_fit_buckets, primary_strategy, secondary_strategy, role_tag_counts, scryfall_land_count, average_nonland_mana_value, bracket_read=None):
    review = _hotfix_prev_build_possible_cut_review(cut_pressure_review, unique_cards, scryfall_lookup, card_role_tags_by_card, card_plan_fit_buckets, primary_strategy, secondary_strategy, role_tag_counts, scryfall_land_count, average_nonland_mana_value, bracket_read)
    if cut_pressure_review.get("deck_is_underfilled"):
        review["recommended_cuts"] = []
        review["possible_cuts"] = review.get("possible_cuts", [])[:5]
        review["hotfix_underfilled_note"] = "Deck is short cards. No required cuts; prioritize addition categories before removal."
    intended_bracket = bracket_read.get("intended_bracket","Unknown") if bracket_read else "Unknown"
    if intended_bracket == "Unknown":
        moved, kept = [], []
        for entry in review.get("recommended_cuts", []):
            card_name = entry.get("card_name")
            tags = set(card_role_tags_by_card.get(card_name, []))
            if tags.intersection({"bracket_modifier","bracket_pressure","high_bracket_pressure","game_changer"}) and not tags.intersection({"generically_good_wrong_shell","no_role","off_plan"}):
                entry["current_recommendation"] = "Manual bracket review; intended bracket unknown."
                entry["how_to_decide"] = "Decide based on intended bracket and table expectations, not raw power alone."
                moved.append(entry)
            else:
                kept.append(entry)
        review["recommended_cuts"] = kept
        review["conflict_manual_review"] = review.get("conflict_manual_review", []) + moved[:6]
    if not review.get("refined_deck_review_candidates") and not review.get("recommended_cuts") and not review.get("possible_cuts") and cut_pressure_review.get("required_cuts",0) == 0 and not cut_pressure_review.get("deck_is_underfilled"):
        candidates = []
        for card_name, tags in card_role_tags_by_card.items():
            tagset = set(tags)
            if tagset.intersection({"minor_package_card","manual_review_package_card","bracket_modifier","political_card","fringe_theme_support","niche_theme_support","generically_good_wrong_shell"}):
                candidates.append({
                    "card_name": card_name,
                    "label": "Playtest-first review candidate",
                    "why_to_watch": "Hotfix layered review found this as a minor/manual/bracket/table-dependent package card, not a confident cut.",
                    "why_it_may_belong": "It may still support a theme, bracket choice, or user-intent package.",
                    "watch_for": "Track whether it advances the commander, primary plan, or win condition often enough.",
                })
            if len(candidates) >= 5:
                break
        review["refined_deck_review_candidates"] = candidates
    strategy_confidence_for_cuts = "Medium"
    try:
        strategy_confidence_for_cuts = globals().get("v057_strategy_confidence", "Medium")
    except Exception:
        pass
    review = apply_cut_depth_and_removal_protection_v057(
        review,
        card_role_tags_by_card,
        role_tag_counts,
        scryfall_land_count,
        sum(unique_cards.values()),
        strategy_confidence_for_cuts,
    )
    return review




def startup_self_check_v057():
    required_helpers = [
        "get_commander_role_tag_counter", "commander_has_any_tag", "v057_apply_gates_and_reconcile",
        "compute_role_balance_v057", "apply_cut_depth_and_removal_protection_v057",
    ]
    missing = [name for name in required_helpers if name not in globals()]
    if missing:
        print("Startup self-check failed. Missing helper(s): " + ", ".join(missing))
        sys.exit(1)
    OUTPUT_FOLDER.mkdir(exist_ok=True)
    try:
        test_path = OUTPUT_FOLDER / ".write_test"
        test_path.write_text("ok", encoding="utf-8")
        test_path.unlink(missing_ok=True)
    except Exception as exc:
        print(f"Startup self-check failed. Output folder is not writable: {exc}")
        sys.exit(1)



# ==============================
# v0.5.7 fixv3 — Debug extraction, strategy reconciliation, tag filtering, cut distribution
# ==============================

def clean_reason_text(reason):
    """Clean report/diagnostic reason text for polished v0.5.8 output."""
    text = str(reason or "").strip()
    if not text:
        return ""
    text = re.sub(r"v0\.5\.\d+(?:v\d+|\s*hotfix|hotfix)?\s*(?:gate|note|priority correction)?:?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip(" -;:")
    text = re.sub(r"([.!?]){2,}$", r"\1", text)
    text = re.sub(r"\.\s*\.$", ".", text)
    text = text.rstrip(" .")
    if text:
        text += "."
    return text


def dedupe_reasons(reasons, max_reasons=2):
    cleaned = []
    seen = set()
    for reason in reasons or []:
        text = clean_reason_text(reason)
        if not text:
            continue
        key = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
        if not key:
            continue
        if any(key == existing or key in existing or existing in key for existing in seen):
            continue
        seen.add(key)
        cleaned.append(text)
        if len(cleaned) >= max_reasons:
            break
    return cleaned


def is_mana_only_activated_card(card):
    type_line = card.get("type_line", "") or ""
    text = normalize_text(type_line + "\n" + get_full_oracle_text(card))
    tl = type_line.lower()
    likely_mana_source = (
        "land" in tl
        or ("artifact" in tl and any(p in text for p in ["add {", "add one mana", "add two mana", "add three mana", "add mana"]))
        or ("creature" in tl and any(p in text for p in ["add {", "add one mana", "add two mana", "add three mana", "add mana"]))
    )
    if not likely_mana_source:
        return False
    value_phrases = [
        "destroy", "exile target", "return target", "draw a card", "draw cards", "create",
        "deals", "damage", "copy", "gain control", "mill", "surveil", "scry",
        "put a +1/+1 counter", "target creature gets", "proliferate", "fight", "you win the game",
        "activated abilities cost", "copy target activated ability", "equip ", "crew ",
    ]
    if any(p in text for p in value_phrases):
        if "land" in tl and not any(p in text for p in ["copy target activated ability", "activated abilities cost", "you win the game"]):
            return True
        return False
    return any(p in text for p in ["add {", "add one mana", "add two mana", "add three mana", "add mana", "mana of any color", "mana of any one color"])


def clean_inflated_activated_ability_tags(card, tags):
    tags = set(tags or [])
    if is_mana_only_activated_card(card):
        for tag in [
            "activated_ability_payoff", "activated_ability_synergy", "activated_ability_engine",
            "activated_ability_cost_reduction", "primary_plan_support", "commander_synergy_possible",
            "direct_commander_support",
        ]:
            tags.discard(tag)
        tags.update({"mana_source", "shell_support", "mana_ability_only"})
        if "land" in (card.get("type_line", "") or "").lower():
            tags.add("utility_land")
    return tags


def clean_inflated_typal_tags(card, tags):
    tags = set(tags or [])
    typal_payoff_tags = {
        "tribal_payoff", "tribal_dependency", "tribal_anthem", "tribal_protection",
        "typal_payoff", "typal_enabler", "typal_lord", "typal_token_maker",
        "changeling", "type_granter",
    }
    if "creature" in (card.get("type_line", "") or "").lower():
        tags.add("creature_type_present")
        tags.add("incidental_creature_type")
    if not tags.intersection(typal_payoff_tags):
        tags.discard("typal_density")
        tags.discard("tribal_body")
        tags.discard("typal_density_piece")
    else:
        tags.add("typal_density_piece")
    return tags


_fixv3_prev_infer_card_role_tags = infer_card_role_tags
def infer_card_role_tags(card, commander_cards=None):
    tags = set(_fixv3_prev_infer_card_role_tags(card, commander_cards))
    type_line = card.get("type_line", "") or ""
    text = normalize_text(type_line + "\n" + get_full_oracle_text(card))

    if (
        ("becomes a copy of target creature card in your graveyard" in text)
        or ("copy of target creature card in your graveyard" in text)
        or ("graveyard" in text and "becomes a copy" in text)
        or ("graveyard" in text and "copy" in text and "except its name" in text)
    ):
        tags.update({
            "graveyard_copy_form", "copy_clone_value", "activated_ability_source",
            "graveyard_enabler", "commander_defined_support", "emergent_theme_support",
            "protected_setup_required",
        })
        tags.discard("activated_ability_payoff")

    tags = clean_inflated_activated_ability_tags(card, tags)
    tags = clean_inflated_typal_tags(card, tags)

    if "create" in text and " token" in text:
        tags.add("typal_token_maker")
        tags.add("token_typal_density")
        if not any(p in text for p in ["you control get", "other ", "whenever a", "for each"]):
            tags.discard("tribal_dependency")

    return sorted(tags)


def commander_has_graveyard_copy_text(commander_cards):
    for commander in commander_cards or []:
        text = normalize_text(get_full_oracle_text(commander))
        if (
            "becomes a copy of target creature card in your graveyard" in text
            or "copy of target creature card in your graveyard" in text
            or ("graveyard" in text and "becomes a copy" in text)
            or ("graveyard" in text and "copy" in text and "except its name" in text)
        ):
            return True
    return False


def get_graveyard_copy_form_density(role_counts):
    return (
        role_counts.get("graveyard_copy_form", 0) * 12
        + role_counts.get("graveyard_enabler", 0) * 2
        + role_counts.get("self_mill", 0) * 2
        + role_counts.get("discard_outlet", 0) * 2
        + role_counts.get("card_selection", 0)
        + role_counts.get("copy_clone_value", 0) * 3
        + role_counts.get("activated_ability_source", 0)
        + role_counts.get("protected_setup_required", 0)
    )


def can_be_primary_graveyard_copy_form(role_counts, commander_cards):
    setup_count = role_counts.get("graveyard_enabler", 0) + role_counts.get("self_mill", 0) + role_counts.get("discard_outlet", 0) + role_counts.get("card_selection", 0)
    return commander_has_graveyard_copy_text(commander_cards) and setup_count >= 8 and (role_counts.get("copy_clone_value", 0) >= 1 or role_counts.get("graveyard_copy_form", 0) >= 1)


def actual_wheel_primary_gate(role_counts):
    actual_wheel_count = role_counts.get("wheel_effect", 0)
    draw_punisher_count = role_counts.get("draw_punisher", 0)
    opponent_draw_payoff_count = role_counts.get("opponent_draw_payoff", 0)
    return actual_wheel_count >= 4 or (actual_wheel_count >= 2 and draw_punisher_count >= 2 and opponent_draw_payoff_count >= 1)


def can_score_typal_archetype(creature_type, role_counts, commander_tags=None, minor=False):
    commander_tags = commander_tags or Counter()
    type_tag = f"{creature_type.lower()}_typal"
    type_count = role_counts.get(type_tag, 0)
    payoff_count = (
        role_counts.get("typal_payoff", 0)
        + role_counts.get("tribal_payoff", 0)
        + role_counts.get("tribal_anthem", 0)
        + role_counts.get("typal_lord", 0)
        + role_counts.get("typal_enabler", 0)
    )
    commander_typal_support = commander_tags.get(type_tag, 0) > 0 or commander_tags.get("tribal_payoff", 0) > 0
    if minor:
        return type_count >= 6 and payoff_count >= 1
    return (type_count >= 12 and payoff_count >= 3) or (commander_typal_support and type_count >= 8 and payoff_count >= 2)


ARCHETYPE_DEFINITIONS["Graveyard Copy-Form Engine"] = {
    "anchor_tags": {"graveyard_copy_form"},
    "core_tags": {
        "graveyard_copy_form": 12,
        "graveyard_enabler": 4,
        "self_mill": 4,
        "discard_outlet": 4,
        "looter": 3,
        "card_selection": 2,
        "copy_clone_value": 4,
        "activated_ability_source": 1,
        "mana_sink": 1,
        "protected_setup_required": 2,
        "combo_piece_possible": 1,
    },
    "engine": "The deck sets up the graveyard, then uses a copy-form commander or effects to become/copy selected creature cards from the graveyard.",
    "finishers": "Graveyard setup into copy-form threats, evasive commander damage, protected combo-like forms, and value bodies chosen for the situation.",
}


_fixv3_prev_score_archetypes = score_archetypes
def score_archetypes(role_counts, type_counts, commander_cards):
    scores = _fixv3_prev_score_archetypes(role_counts, type_counts, commander_cards)
    commander_tags = get_commander_role_tag_counter(commander_cards)

    if can_be_primary_graveyard_copy_form(role_counts, commander_cards):
        density = get_graveyard_copy_form_density(role_counts)
        base_score = max(scores.get("Graveyard Self-Mill / Recursion", {}).get("score", 0), scores.get("Activated Abilities", {}).get("score", 0)) + 35
        scores["Graveyard Copy-Form Engine"] = {
            "score": max(base_score, density),
            "raw_score": max(base_score, density),
            "adjusted_score": max(base_score, density),
            "anchor_hits": role_counts.get("graveyard_copy_form", 0) or 1,
            "commander_anchor_hits": 1,
            "gate_passed": True,
            "primary_eligible": True,
            "strategy_layer": "commander_defined_emergent",
            "primary_priority_reason": "Commander text copies or becomes creature cards from the graveyard, and the deck has graveyard setup/discard/self-mill support.",
            "evidence": dedupe_reasons([
                "commander graveyard-copy text detected",
                f"graveyard/copy setup density: {density}",
                "copy-form package takes priority over generic activated-ability labels",
            ], 3),
            "engine": ARCHETYPE_DEFINITIONS["Graveyard Copy-Form Engine"]["engine"],
            "finishers": ARCHETYPE_DEFINITIONS["Graveyard Copy-Form Engine"]["finishers"],
        }
        for broad in ["Activated Abilities", "Activated Abilities / Power-Reduction Engine", "Wheels / Draw-Punisher / Group Slug", "Topdeck / Permanent-Type Value", "Goblin Typal / Go-Wide Tokens"]:
            if broad in scores:
                scores[broad]["score"] = int(scores[broad].get("score", 0) * 0.55)
                scores[broad]["suppression_reason"] = "Downgraded because a commander-defined Graveyard Copy-Form Engine passed its primary gate."
                scores[broad]["gate_failed_reason"] = scores[broad].get("gate_failed_reason", scores[broad]["suppression_reason"])
                scores[broad]["evidence"] = dedupe_reasons(scores[broad].get("evidence", []) + [scores[broad]["suppression_reason"]], 3)

    if "Wheels / Draw-Punisher / Group Slug" in scores and not actual_wheel_primary_gate(role_counts):
        scores["Wheels / Draw-Punisher / Group Slug"]["score"] = int(scores["Wheels / Draw-Punisher / Group Slug"].get("score", 0) * 0.35)
        scores["Wheels / Draw-Punisher / Group Slug"]["suppression_reason"] = "Failed wheels gate: generic card draw/discard does not equal a primary wheels/draw-punisher plan. Treat as Wheels / Discard / Draw-Refill minor package."
        scores["Wheels / Draw-Punisher / Group Slug"]["evidence"] = dedupe_reasons(scores["Wheels / Draw-Punisher / Group Slug"].get("evidence", []) + [scores["Wheels / Draw-Punisher / Group Slug"]["suppression_reason"]], 3)

    typal_checks = {
        "Goblin Typal / Go-Wide Tokens": "goblin",
        "Elf Typal / Token Lifedrain": "elf",
        "Vampire Tokens / Aristocrats / Drain": "vampire",
    }
    for archetype_name, ctype in typal_checks.items():
        if archetype_name in scores and not can_score_typal_archetype(ctype, role_counts, commander_tags, minor=False):
            scores[archetype_name]["score"] = int(scores[archetype_name].get("score", 0) * 0.25)
            scores[archetype_name]["suppression_reason"] = f"Failed {ctype} typal gate: incidental creature types do not create a typal primary strategy."
            scores[archetype_name]["evidence"] = dedupe_reasons(scores[archetype_name].get("evidence", []) + [scores[archetype_name]["suppression_reason"]], 3)

    for data in scores.values():
        if isinstance(data, dict):
            data["evidence"] = dedupe_reasons(data.get("evidence", []), 3)
            data.setdefault("raw_score", data.get("score", 0))
            data["adjusted_score"] = data.get("score", 0)
    return scores


_fixv3_prev_choose_primary_secondary_strategy = choose_primary_secondary_strategy
def choose_primary_secondary_strategy(archetype_scores):
    ordered = sorted([(k, v) for k, v in archetype_scores.items() if not str(k).startswith("__")], key=lambda item: item[1].get("score", 0), reverse=True)
    if not ordered:
        return "Unclear", {"score": 0}, "Unclear", {"score": 0}, []

    if "Graveyard Copy-Form Engine" in archetype_scores and archetype_scores["Graveyard Copy-Form Engine"].get("gate_passed", True):
        primary_name = "Graveyard Copy-Form Engine"
        primary_data = archetype_scores[primary_name]
        secondary_name, secondary_data = "Unclear", {"score": 0}
        for name, data in ordered:
            if name == primary_name:
                continue
            if name in {"Activated Abilities", "Activated Abilities / Power-Reduction Engine", "Graveyard Self-Mill / Recursion"}:
                secondary_name, secondary_data = name, data
                break
        if secondary_name == "Unclear" and len(ordered) > 1:
            secondary_name, secondary_data = next((n, d) for n, d in ordered if n != primary_name)
        primary_data["primary_priority_reason"] = primary_data.get("primary_priority_reason") or "Commander-defined graveyard copy-form gate passed."
        return primary_name, primary_data, secondary_name, secondary_data, ordered

    primary_name, primary_data = ordered[0]
    secondary_name, secondary_data = (ordered[1] if len(ordered) > 1 else ("Unclear", {"score": 0}))

    if secondary_data.get("score", 0) > primary_data.get("score", 0) * 1.25:
        reason = primary_data.get("primary_priority_reason") or primary_data.get("suppression_reason") or ""
        if not reason or reason.lower() in {"after v0.5.7 gate checks", "commander-defined package priority", "broad-archetype suppression"}:
            primary_name, secondary_name = secondary_name, primary_name
            primary_data, secondary_data = secondary_data, primary_data
            primary_data["primary_priority_reason"] = "Promoted because it had a significantly higher adjusted score and no specific layer/gate reason justified the lower-scoring primary."
        else:
            primary_data["primary_priority_reason"] = reason

    return primary_name, primary_data, secondary_name, secondary_data, ordered


_fixv3_prev_build_possible_cut_review = build_possible_cut_review
def is_interaction_cut_entry(entry, card_role_tags_by_card):
    card_name = entry.get("card_name") if isinstance(entry, dict) else None
    tags = set(card_role_tags_by_card.get(card_name, []))
    return bool(tags.intersection({"counterspell", "targeted_removal", "board_wipe", "mass_removal", "stack_interaction", "protection"}))


def apply_cut_role_distribution_caps_to_review(review, card_role_tags_by_card):
    mode = CUT_DEPTH_CONFIG.get("mode", "normal")
    target = max(1, int(CUT_DEPTH_CONFIG.get("optional_cut_target", 5)))
    if mode == "strict":
        cap = max(2, int(target * 0.30))
    elif mode == "brutal":
        cap = max(3, int(target * 0.35))
    else:
        cap = max(1, int(target * 0.25))

    moved = []
    for key in ["possible_cuts", "recommended_cuts"]:
        kept = []
        interaction_seen = 0
        for entry in review.get(key, []) or []:
            if is_interaction_cut_entry(entry, card_role_tags_by_card):
                interaction_seen += 1
                if entry.get("confidence") == "High":
                    entry["confidence"] = "Medium"
                if interaction_seen > cap:
                    moved.append({
                        "card_name": entry.get("card_name", "Unknown"),
                        "why_questionable": "Interaction cut distribution cap moved this out of normal cut candidates.",
                        "why_might_belong": "Removal, counterspells, stack interaction, and protection are necessary deck functions unless clearly overrepresented.",
                        "what_to_watch": "Only cut this if the deck still has enough interaction after changes or this answer is narrow/inefficient/redundant.",
                    })
                    continue
            kept.append(entry)
        review[key] = kept

    if moved:
        review["playtest_before_cutting"] = (review.get("playtest_before_cutting", []) or []) + moved[:10]
        review.setdefault("diagnostic_warnings", [])
        review["diagnostic_warnings"].append("Warning: Cut candidate list may be over-targeting interaction. Review removal protection and role balance before final recommendations.")
    return review


def build_possible_cut_review(cut_pressure_review, unique_cards, scryfall_lookup, card_role_tags_by_card, card_plan_fit_buckets, primary_strategy, secondary_strategy, role_tag_counts, scryfall_land_count, average_nonland_mana_value, bracket_read=None):
    review = _fixv3_prev_build_possible_cut_review(cut_pressure_review, unique_cards, scryfall_lookup, card_role_tags_by_card, card_plan_fit_buckets, primary_strategy, secondary_strategy, role_tag_counts, scryfall_land_count, average_nonland_mana_value, bracket_read)
    return apply_cut_role_distribution_caps_to_review(review, card_role_tags_by_card)


def clean_user_facing_role_tags_v057(report_text, attribute_relevance):
    start_marker = "==============================\n16. Card Role Tags by Card"
    end_marker = "==============================\n17. Tag-Based Review Notes"
    start = report_text.find(start_marker)
    end = report_text.find(end_marker, start + len(start_marker)) if start != -1 else -1
    if start == -1 or end == -1:
        return report_text
    lines = ["==============================", "16. Card Role Tags by Card", "------------------------------", "User-facing filtered view. Raw tags are available in diagnostics."]
    for item in attribute_relevance:
        relevant = item.get("relevant", [])
        manual = item.get("manual_review", [])
        if relevant:
            lines.append(f"- {item['card_name']}: Relevant roles: {', '.join(relevant)}")
        elif manual:
            lines.append(f"- {item['card_name']}: Relevant roles: none confirmed. Manual review: {', '.join(manual)}")
        else:
            lines.append(f"- {item['card_name']}: Relevant roles: none confirmed. Ignored raw tags available in diagnostics.")
    replacement = "\n".join(lines) + "\n\n"
    return report_text[:start] + replacement + report_text[end:]



# ==============================
# v0.5.8 cleanup patch — report boundaries, score display, filtered user-facing tags
# ==============================

def final_score_v057v4(data):
    """Use the post-gate adjusted score for display when a gate/suppression lowered a candidate."""
    if not isinstance(data, dict):
        return 0
    score = int(data.get("score", 0) or 0)
    adjusted = int(data.get("adjusted_score", score) or 0)
    reason = str(data.get("suppression_reason", "") or data.get("gate_failed_reason", "")).lower()
    if reason and adjusted < score:
        return adjusted
    return score


def finalize_archetype_scores_v057v4(scores, role_counts, commander_cards):
    """Final consistency pass after priority corrections.

    v3 correctly identified Lazav-style Graveyard Copy-Form, but later priority code could
    leave stale display scores on gated candidates. This pass keeps the analysis result and
    the visible score table aligned.
    """
    cleaned = {name: (dict(data) if isinstance(data, dict) else data) for name, data in scores.items()}

    # Wheels must not display as a high strategy score when the primary wheel gate failed.
    if "Wheels / Draw-Punisher / Group Slug" in cleaned and not actual_wheel_primary_gate(role_counts):
        data = cleaned["Wheels / Draw-Punisher / Group Slug"]
        raw = int(data.get("raw_score", data.get("score", 0)) or 0)
        gated = min(int(data.get("adjusted_score", data.get("score", 0)) or 0), int(raw * 0.35))
        data["score"] = gated
        data["adjusted_score"] = gated
        data["gate_passed"] = False
        data["primary_eligible"] = False
        data["suppression_reason"] = "Failed wheels gate: only actual wheel/draw-punisher density can make this a primary or high secondary strategy; treat as a minor Wheels / Discard / Draw-Refill package."
        data["evidence"] = dedupe_reasons(data.get("evidence", []) + [data["suppression_reason"]], 2)

    # Generic rule: if a candidate has a failed gate and adjusted_score is lower than score,
    # show the adjusted score rather than the stale pre-correction score.
    for name, data in list(cleaned.items()):
        if not isinstance(data, dict) or str(name).startswith("__"):
            continue
        data.setdefault("raw_score", data.get("score", 0))
        data.setdefault("adjusted_score", data.get("score", 0))
        reason = str(data.get("suppression_reason", "") or data.get("gate_failed_reason", ""))
        if reason and int(data.get("adjusted_score", data.get("score", 0)) or 0) < int(data.get("score", 0) or 0):
            data["score"] = int(data.get("adjusted_score", 0) or 0)
        data["evidence"] = dedupe_reasons(data.get("evidence", []), 2)

    # Rebuild diagnostics from final visible scores.
    diagnostics = []
    for name, data in cleaned.items():
        if isinstance(data, dict) and data.get("suppression_reason"):
            diagnostics.append(f"{name}: raw={data.get('raw_score', data.get('score', 0))} -> adjusted={data.get('score', 0)} ({data.get('suppression_reason')})")
    cleaned["__v057_diagnostics__"] = {"suppression_rules_triggered": diagnostics}
    return cleaned


def format_suppressed_archetype_v057v4(name, data):
    score = final_score_v057v4(data)
    evidence = dedupe_reasons(data.get("evidence", []), 2)
    reason = data.get("suppression_reason") or data.get("gate_failed_reason") or (evidence[0] if evidence else "Gate or suppression rule reduced this candidate.")
    reason = clean_reason_text(dedupe_reasons([reason], 1)[0] if reason else "Gate or suppression rule reduced this candidate.")
    gate_result = "Failed" if not data.get("gate_passed", True) else "Suppressed / Downgraded"
    lower_reason = reason.lower()
    if "minor" in lower_reason:
        final_handling = "minor package"
    elif "support" in lower_reason:
        final_handling = "support package"
    elif "manual" in lower_reason:
        final_handling = "manual review"
    else:
        final_handling = "ignored as primary strategy"
    return [
        f"- {name} (score {score})",
        f"  Gate result: {gate_result}",
        f"  Reason: {reason}",
        f"  Final handling: {final_handling}.",
    ]


def get_primary_selection_reason_v057v4(primary_name, secondary_name, primary_data, secondary_data):
    primary_score = final_score_v057v4(primary_data)
    secondary_score = final_score_v057v4(secondary_data)
    priority_reason = primary_data.get("primary_priority_reason", "")
    if primary_score >= secondary_score:
        return f"{primary_name} was selected because its final gated score ({primary_score}) is higher than {secondary_name}'s final gated score ({secondary_score})."
    if priority_reason:
        return f"{primary_name} remained primary despite a lower final score because {priority_reason}"
    return f"{secondary_name} should be promoted if it remains more than 25% higher after gating; no specific priority reason was recorded."


def build_reconciliation_lines_v057v4(primary_name, secondary_name, primary_data, secondary_data, ordered_archetypes):
    highest = ordered_archetypes[0] if ordered_archetypes else ("Unclear", {"score": 0})
    return [
        "Primary/Secondary Reconciliation:",
        f"- Highest final adjusted score: {highest[0]} ({final_score_v057v4(highest[1])})",
        f"- Selected primary: {primary_name} ({final_score_v057v4(primary_data)})",
        f"- Selected secondary: {secondary_name} ({final_score_v057v4(secondary_data)})",
        f"- Why selected primary won: {get_primary_selection_reason_v057v4(primary_name, secondary_name, primary_data, secondary_data)}",
        f"- Was a higher-scoring candidate suppressed? {'Yes' if any((not d.get('gate_passed', True) or d.get('suppression_reason')) and final_score_v057v4(d) > final_score_v057v4(primary_data) for _, d in ordered_archetypes) else 'No'}",
    ]


def build_strategy_confidence_diagnostics_lines_v057v4(primary_name, secondary_name, primary_data, secondary_data, ordered_archetypes, warnings):
    highest_raw = max(((name, int(data.get("raw_score", data.get("score", 0)) or 0)) for name, data in ordered_archetypes), key=lambda x: x[1], default=("Unclear", 0))
    highest_adjusted = max(((name, final_score_v057v4(data)) for name, data in ordered_archetypes), key=lambda x: x[1], default=("Unclear", 0))
    return [
        "Strategy Confidence Diagnostics:",
        f"- Primary selected by: {'commander-defined gate' if primary_data.get('strategy_layer') == 'commander_defined_emergent' else 'score / gate reconciliation'}",
        f"- Highest raw score: {highest_raw[0]} ({highest_raw[1]})",
        f"- Highest adjusted score: {highest_adjusted[0]} ({highest_adjusted[1]})",
        f"- Suppressed high-scoring candidates: {', '.join(name for name, data in ordered_archetypes if data.get('suppression_reason') and int(data.get('raw_score', data.get('score', 0)) or 0) >= 100) or 'None'}",
        f"- Broad tags excluded from primary scoring: mana-only activated abilities, incidental creature types, mana rocks, normal lands, and broad macro support tags",
        f"- Bracket/power tags excluded from primary scoring: bracket_pressure, high_bracket_pressure, power_signal, game_changer unless separately supported by strategy density",
        f"- Warning: strategy may be inflated by generic role tags: {'Yes' if warnings else 'No'}",
    ]


MAX_USER_RELEVANT_ROLES = 5


def get_relevance_lookup_v057v5(attribute_relevance):
    return {item.get("card_name"): item for item in attribute_relevance or [] if item.get("card_name")}


def relevant_roles_text_v057v5(card_name, relevance_lookup):
    item = relevance_lookup.get(card_name, {})
    relevant = list(dict.fromkeys(item.get("relevant", []) or []))
    manual = list(dict.fromkeys(item.get("manual_review", []) or []))
    if relevant:
        return "Relevant roles: " + ", ".join(relevant[:MAX_USER_RELEVANT_ROLES])
    if manual:
        return "Relevant roles: none confirmed. Manual review: " + ", ".join(manual[:MAX_USER_RELEVANT_ROLES])
    return "Relevant roles: none confirmed. Manual review: raw tags exist, but none were relevant enough to use in strategy scoring."


def clean_inline_tags_in_user_facing_sections_v057v5(report_text, attribute_relevance):
    """Replace huge raw tag lists in polished report sections with filtered relevant roles."""
    lookup = get_relevance_lookup_v057v5(attribute_relevance)
    known_names = sorted([name for name in lookup if name], key=len, reverse=True)
    marker = "==============================\n16. Card Role Tags by Card"
    split_at = report_text.find(marker)
    head = report_text if split_at == -1 else report_text[:split_at]
    tail = "" if split_at == -1 else report_text[split_at:]
    new_lines = []
    for line in head.splitlines():
        if "Tags:" in line:
            before, after = line.split("Tags:", 1)
            matched = None
            searchable = before.strip()
            for name in known_names:
                if name in searchable:
                    matched = name
                    break
            if matched:
                line = before.rstrip() + " " + relevant_roles_text_v057v5(matched, lookup)
            else:
                line = before.rstrip() + " Relevant roles: see diagnostics for raw tag details."
        new_lines.append(line)
    return "\n".join(new_lines) + ("\n" if tail else "") + tail


# Backward-compatible aliases for previous helper names.
get_relevance_lookup_v057v4 = get_relevance_lookup_v057v5
relevant_roles_text_v057v4 = relevant_roles_text_v057v5
clean_inline_tags_in_user_facing_sections_v057v4 = clean_inline_tags_in_user_facing_sections_v057v5

startup_self_check_v057()

# Load files
if not DECK_FILE.exists():
    print(f"Could not find selected deck file: {DECK_FILE}")
    exit()
if not SCRYFALL_FILE.exists():
    print("Could not find data/scryfall_cards.json")
    print("Run this first: py download_scryfall_data.py")
    exit()

OUTPUT_FOLDER.mkdir(exist_ok=True)


# ==============================
# v0.5.8 Strategy Gate Stabilization Patch
# ==============================
# This patch intentionally stays narrow. It stabilizes the v0.5.7 infrastructure by
# correcting copy-form overclassification, score reconciliation, normal/debug report
# separation, token-created tribal warnings, and inflated bracket diagnostics.

def v058_commander_has_true_graveyard_copy_text(commander_cards):
    """Only commander text can make Graveyard Copy-Form a commander-defined primary.

    A support card with graveyard/copy text should be a minor/manual-review package,
    not proof that the deck's primary identity is Graveyard Copy-Form.
    """
    for commander in commander_cards or []:
        text = normalize_text(get_full_oracle_text(commander))
        exact_patterns = [
            "becomes a copy of target creature card in your graveyard",
            "becomes a copy of a creature card in your graveyard",
            "copy of target creature card in your graveyard",
            "copy of a creature card in your graveyard",
            "target creature card in your graveyard, except",
        ]
        if any(pattern in text for pattern in exact_patterns):
            return True
        if "graveyard" in text and "becomes a copy" in text and "creature card" in text:
            return True
        if "graveyard" in text and "copy" in text and "creature card" in text and "except its name" in text:
            return True
    return False


def v058_graveyard_copy_setup_count(role_counts):
    return (
        role_counts.get("graveyard_enabler", 0)
        + role_counts.get("self_mill", 0)
        + role_counts.get("discard_outlet", 0)
        + role_counts.get("card_selection", 0)
    )


def can_be_primary_graveyard_copy_form(role_counts, commander_cards):
    """v0.5.8 hard gate.

    Primary Graveyard Copy-Form requires commander text plus graveyard setup. Deck-only
    copy effects are handled as minor/manual-review signals by the report, not primary.
    """
    if not v058_commander_has_true_graveyard_copy_text(commander_cards):
        return False
    setup_count = v058_graveyard_copy_setup_count(role_counts)
    real_copy_support = role_counts.get("copy_clone_value", 0) + role_counts.get("graveyard_copy_form", 0)
    return setup_count >= 8 and real_copy_support >= 1


def get_tribal_dependency_types(oracle_text):
    """v0.5.8: token creation is not unsupported tribal dependency by itself."""
    text = normalize_text(oracle_text)
    found = set()
    for ctype in get_referenced_creature_types(oracle_text):
        lower = ctype.lower()
        if lower in globals().get("HOTFIX_NON_TRIBAL_WORDS", set()):
            continue
        plural = lower + "s"
        token_creation_only = bool(re.search(rf"\bcreate\b.*\b{lower}\b.*\btoken", text) or re.search(rf"\bcreate\b.*\b{plural}\b.*\btoken", text))
        requires_existing_type = any(re.search(pattern, text) for pattern in [
            rf"\b{lower}\s+you\s+control\b",
            rf"\b{plural}\s+you\s+control\b",
            rf"\bother\s+{plural}\b",
            rf"\bother\s+{lower}s\b",
            rf"\bwhenever\s+a\s+{lower}\s+you\s+control\b",
            rf"\bwhenever\s+another\s+{lower}\b",
            rf"\bfor\s+each\s+{lower}\b",
            rf"\bfor\s+each\s+{plural}\b",
            rf"\b{lower}\s+spells\s+you\s+cast\b",
            rf"\b{plural}\s+spells\s+you\s+cast\b",
            rf"\bequipped\s+{lower}\b",
        ])
        # Choosing a type is a typal/manual-review signal, but not a token-created dependency.
        chooses_type = "choose a creature type" in text or "chosen type" in text
        if requires_existing_type or chooses_type:
            found.add(ctype)
        elif token_creation_only:
            # Token maker only; explicitly do not flag unsupported tribal dependency.
            continue
    return found


def v058_real_turbo_density(role_counts):
    return (
        role_counts.get("true_fast_mana", 0) * 5
        + role_counts.get("true_ritual", 0) * 5
        + role_counts.get("efficient_tutor", 0) * 3
        + role_counts.get("combo_tutor", 0) * 4
        + role_counts.get("tutor_chain", 0) * 3
        + role_counts.get("combo_protection", 0) * 3
        + role_counts.get("silence_effect", 0) * 3
        + role_counts.get("free_counterspell", 0) * 2
        + role_counts.get("turbo_combo", 0) * 6
        + role_counts.get("true_turbo_combo", 0) * 8
    )


def v058_real_dragonstorm_density(role_counts):
    dragon_combo = role_counts.get("dragonstorm_combo", 0)
    dragon_typal = role_counts.get("dragon_typal", 0)
    true_chain = min(role_counts.get("tutor_chain", 0) + role_counts.get("combo_tutor", 0), max(0, dragon_typal))
    return dragon_combo * 10 + true_chain * 3 + role_counts.get("true_ritual", 0) * 2 + role_counts.get("true_fast_mana", 0) * 2


_v058_prev_estimate_bracket_read = estimate_bracket_read
def estimate_bracket_read(unique_cards, card_role_tags_by_card, primary_strategy, secondary_strategy, role_tag_counts, game_changer_names, intended_bracket="Unknown"):
    bracket_read = _v058_prev_estimate_bracket_read(unique_cards, card_role_tags_by_card, primary_strategy, secondary_strategy, role_tag_counts, game_changer_names, intended_bracket)
    bracket_read["turbo_density"] = v058_real_turbo_density(role_tag_counts)
    bracket_read["dragonstorm_density"] = v058_real_dragonstorm_density(role_tag_counts)
    # Keep bracket pressure separate from strategy and add a diagnostic note if old broad counters were likely inflated.
    if bracket_read["turbo_density"] < 20 and role_tag_counts.get("modal_spell_synergy", 0) + role_tag_counts.get("adventure_synergy", 0) >= 10:
        bracket_read.setdefault("reasons", []).append("v0.5.8 note: broad modal/adventure/alternate-cost tags were excluded from turbo density.")
    if bracket_read["dragonstorm_density"] < 20 and role_tag_counts.get("dragonstorm_combo", 0) == 0:
        bracket_read.setdefault("reasons", []).append("v0.5.8 note: Dragonstorm/Tiamat density only counts true Dragon tutor-chain/combo signals.")
    return bracket_read


_v058_prev_score_archetypes = score_archetypes
def score_archetypes(role_counts, type_counts, commander_cards):
    scores = _v058_prev_score_archetypes(role_counts, type_counts, commander_cards)

    has_copy_commander = v058_commander_has_true_graveyard_copy_text(commander_cards)
    setup_count = v058_graveyard_copy_setup_count(role_counts)
    real_copy_support = role_counts.get("copy_clone_value", 0) + role_counts.get("graveyard_copy_form", 0)

    if "Graveyard Copy-Form Engine" in scores:
        data = scores["Graveyard Copy-Form Engine"]
        if not has_copy_commander:
            original = int(data.get("score", 0) or 0)
            data["raw_score"] = data.get("raw_score", original)
            data["score"] = 0
            data["adjusted_score"] = 0
            data["gate_passed"] = False
            data["primary_eligible"] = False
            data["suppression_reason"] = "Failed v0.5.8 Graveyard Copy-Form gate: no commander graveyard-copy text. Deck-only copy effects are minor/manual-review support."
            data["primary_priority_reason"] = ""
            data["evidence"] = dedupe_reasons(data.get("evidence", []) + [data["suppression_reason"]], 2)
        elif setup_count < 8 or real_copy_support < 1:
            original = int(data.get("score", 0) or 0)
            data["raw_score"] = data.get("raw_score", original)
            data["score"] = min(original, 40)
            data["adjusted_score"] = data["score"]
            data["gate_passed"] = False
            data["primary_eligible"] = False
            data["suppression_reason"] = "Failed v0.5.8 Graveyard Copy-Form gate: commander text exists, but graveyard setup/copy support is not dense enough for primary."
            data["evidence"] = dedupe_reasons(data.get("evidence", []) + [data["suppression_reason"]], 2)
        else:
            data["gate_passed"] = True
            data["primary_eligible"] = True
            data["strategy_layer"] = "commander_defined_emergent"
            data["primary_priority_reason"] = "Commander has true graveyard-copy text and the deck has enough graveyard setup plus copy-form support."

    # If Adventure / Modal Value legitimately outscored a false copy-form candidate, keep it visible.
    if "Adventure / Modal Value" in scores and scores.get("Graveyard Copy-Form Engine", {}).get("score", 0) <= 0:
        scores["Adventure / Modal Value"].setdefault("primary_eligible", True)
        scores["Adventure / Modal Value"].setdefault("gate_passed", True)

    for name, data in scores.items():
        if isinstance(data, dict) and not str(name).startswith("__"):
            data.setdefault("raw_score", data.get("score", 0))
            data["adjusted_score"] = int(data.get("score", 0) or 0)
            data["evidence"] = dedupe_reasons(data.get("evidence", []), 2)
    return scores


_v058_prev_choose_primary_secondary_strategy = choose_primary_secondary_strategy
def choose_primary_secondary_strategy(archetype_scores):
    primary_name, primary_data, secondary_name, secondary_data, ordered = _v058_prev_choose_primary_secondary_strategy(archetype_scores)
    ordered = sorted([(k, v) for k, v in archetype_scores.items() if not str(k).startswith("__")], key=lambda item: int(item[1].get("score", 0) or 0), reverse=True)
    if not ordered:
        return primary_name, primary_data, secondary_name, secondary_data, ordered

    # Never keep Graveyard Copy-Form primary if its hard gate failed or score was suppressed to zero.
    if primary_name == "Graveyard Copy-Form Engine" and (not primary_data.get("gate_passed", True) or int(primary_data.get("score", 0) or 0) <= 0):
        for name, data in ordered:
            if name != "Graveyard Copy-Form Engine" and data.get("primary_eligible", True) and int(data.get("score", 0) or 0) > 0:
                primary_name, primary_data = name, data
                break

    # If the visible highest final score is not selected and there is no specific, valid priority reason, promote it.
    highest_name, highest_data = ordered[0]
    highest_score = int(highest_data.get("score", 0) or 0)
    primary_score = int(primary_data.get("score", 0) or 0)
    priority_reason = str(primary_data.get("primary_priority_reason", "") or "").strip()
    vague_reasons = {"after v0.5.7 gate checks", "commander-defined package priority", "broad-archetype suppression", "commander-defined graveyard copy-form gate passed."}
    valid_copy_reason = primary_name == "Graveyard Copy-Form Engine" and primary_data.get("gate_passed", False) and v058_commander_has_true_graveyard_copy_text(globals().get("commander_cards_scryfall", []))
    if highest_name != primary_name and highest_score > primary_score * 1.25:
        if not priority_reason or priority_reason.lower() in vague_reasons or not (valid_copy_reason or primary_data.get("strategy_layer") == "commander_defined_emergent"):
            secondary_name, secondary_data = primary_name, primary_data
            primary_name, primary_data = highest_name, highest_data
            primary_data["primary_priority_reason"] = "Promoted by v0.5.8 reconciliation because it had the highest valid final score and the lower-scoring primary had no specific valid priority reason."

    # Re-pick secondary from the remaining highest scoring candidate.
    for name, data in ordered:
        if name != primary_name and int(data.get("score", 0) or 0) > 0:
            secondary_name, secondary_data = name, data
            break
    return primary_name, primary_data, secondary_name, secondary_data, ordered


# Override normal report role-tag section handling: raw role-tag dumps belong in debug only.
def clean_user_facing_role_tags_v057(report_text, attribute_relevance):
    start_marker = "==============================\n16. Card Role Tags by Card"
    next_marker = "==============================\n18. Possible Cut Flags"
    start = report_text.find(start_marker)
    end = report_text.find(next_marker, start + len(start_marker)) if start != -1 else -1
    if start == -1 or end == -1:
        return report_text
    replacement = "\n".join([
        "==============================",
        "16. Diagnostic Role Tags",
        "------------------------------",
        "Raw card role tags and tag-based review notes are hidden from Normal User Mode and preserved in debug diagnostics.",
        "Use Debug / Stress-Test Mode for full raw per-card tags, ignored tags, and relevance-filtering explanations.",
        "",
    ])
    return report_text[:start] + replacement + report_text[end:]


def clean_reason_text(reason):
    text = str(reason or "").strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(v0\.5\.7v?\d*\s+)*(v0\.5\.8\s+)?", lambda m: m.group(0), text)
    text = re.sub(r"([.!?]){2,}$", r"\1", text)
    if text and text[-1] not in ".!?:)":
        text += "."
    return text




# ==============================
# v0.5.8 stabilization patch — commander-defined priority, normal/debug separation,
# infrastructure cut caps, and strategy-specific replacement categories
# ==============================

V058_STABILIZATION_VERSION = "v0.5.8"


def v058s_commander_text_blob(commander_cards):
    return normalize_text(" ".join((get_full_oracle_text(c) + " " + c.get("type_line", "")) for c in (commander_cards or [])))


def v058s_commander_is_topdeck_permanent_value(commander_cards):
    text = v058s_commander_text_blob(commander_cards)
    return (
        ("top card of your library" in text or "look at the top card" in text)
        and ("shares a card type" in text or "card type" in text)
        and ("permanent" in text or "enters the battlefield" in text)
        and ("put it into your hand" in text or "put that card into your hand" in text or "reveal" in text)
    )


def v058s_commander_is_token_resource_engine(commander_cards):
    text = v058s_commander_text_blob(commander_cards)
    has_token_or_creature_tap = any(p in text for p in [
        "tap two untapped tokens", "tap three untapped tokens", "tap an untapped token",
        "tap two untapped creatures", "tap three untapped creatures", "tap an untapped creature",
        "tap two untapped artifacts", "tap three untapped artifacts",
    ])
    has_resource_output = any(p in text for p in [
        "add ", "draw a card", "put a +1/+1 counter", "create", "mana of any color",
        "gain life", "deals", "damage", "cards", "counter on",
    ])
    return has_token_or_creature_tap and has_resource_output


def v058s_commander_is_power_reduction_engine(commander_cards):
    text = v058s_commander_text_blob(commander_cards)
    return (
        ("activated abilities" in text or "activate abilities" in text or "abilities you activate" in text)
        and ("cost" in text and "less" in text)
        and ("power" in text or "+1/+1 counter" in text or "counters" in text)
    )


def v058s_get_candidate(scores, *names):
    for name in names:
        if name in scores and isinstance(scores[name], dict):
            return name, scores[name]
    return None, None


def v058s_force_score(scores, name, floor_score, reason, layer="commander_defined_package"):
    if name not in scores or not isinstance(scores[name], dict):
        return
    data = scores[name]
    old = int(data.get("score", 0) or 0)
    data.setdefault("raw_score", old)
    data["score"] = max(old, int(floor_score))
    data["adjusted_score"] = data["score"]
    data["final_score"] = data["score"]
    data["gate_passed"] = True
    data["primary_eligible"] = True
    data["strategy_layer"] = layer
    data["primary_priority_reason"] = clean_reason_text(reason)
    data["evidence"] = dedupe_reasons(data.get("evidence", []) + [reason], 3)


def v058s_dampen_score(scores, name, multiplier, reason):
    if name not in scores or not isinstance(scores[name], dict):
        return
    data = scores[name]
    old = int(data.get("score", 0) or 0)
    data.setdefault("raw_score", old)
    data["score"] = int(old * multiplier)
    data["adjusted_score"] = data["score"]
    data["final_score"] = data["score"]
    data["suppression_reason"] = clean_reason_text(reason)
    data["evidence"] = dedupe_reasons(data.get("evidence", []) + [reason], 2)


_v058s_prev_apply_strategy_priority_corrections = apply_strategy_priority_corrections

def apply_strategy_priority_corrections(archetype_scores, role_counts, commander_cards):
    corrected = _v058s_prev_apply_strategy_priority_corrections(archetype_scores, role_counts, commander_cards)
    corrected = {name: (dict(data) if isinstance(data, dict) else data) for name, data in corrected.items()}

    topdeck_commander = v058s_commander_is_topdeck_permanent_value(commander_cards)
    token_resource_commander = v058s_commander_is_token_resource_engine(commander_cards)
    power_reduction_commander = v058s_commander_is_power_reduction_engine(commander_cards)

    highest_non_meta = max((int(d.get("score", 0) or 0) for n, d in corrected.items() if isinstance(d, dict) and not str(n).startswith("__")), default=0)

    # Amareth-style: topdeck/permanent-type commander text should beat Legends Matter unless real legendary payoff density dominates.
    if topdeck_commander and "Topdeck / Permanent-Type Value" in corrected:
        legends_density = get_legends_cascade_density(role_counts)
        legendary_payoff = role_counts.get("legendary_cascade", 0) + role_counts.get("historic_synergy", 0)
        v058s_force_score(
            corrected,
            "Topdeck / Permanent-Type Value",
            highest_non_meta + 18,
            "Commander topdeck/permanent-type text detected; Topdeck / Permanent-Type Value has commander-defined priority over generic Legends Matter.",
            "commander_defined_package",
        )
        if "Legends Matter / Legendary Cascade" in corrected and not (role_counts.get("legendary_synergy", 0) >= 18 and legendary_payoff >= 6 and legends_density >= 90):
            v058s_dampen_score(
                corrected,
                "Legends Matter / Legendary Cascade",
                0.45,
                "Downgraded because the commander-defined topdeck/permanent-type engine is stronger than incidental legendary density.",
            )
        if "Historic / Legends Matter" in corrected and role_counts.get("historic_synergy", 0) < 10:
            v058s_dampen_score(corrected, "Historic / Legends Matter", 0.65, "Downgraded behind commander-defined topdeck/permanent-type value.")

    # Baylen-style: token-to-resource commanders should beat Blink/Flicker unless blink is heavily commander-anchored.
    if token_resource_commander and "Token Resource Engine" in corrected:
        token_density = get_token_resource_density(role_counts)
        blink_density = get_blink_flicker_density(role_counts)
        floor = highest_non_meta + 16 if token_density >= 25 else highest_non_meta + 8
        v058s_force_score(
            corrected,
            "Token Resource Engine",
            floor,
            "Commander converts tapped tokens/creatures/artifacts into resources; Token Resource Engine has commander-defined priority.",
            "commander_defined_package",
        )
        blink_commander_anchor = get_commander_role_tag_counter(commander_cards).get("blink_flicker", 0) + get_commander_role_tag_counter(commander_cards).get("exile_return", 0)
        if "Blink/Flicker / ETB Value" in corrected and not (blink_commander_anchor and blink_density > token_density * 1.2):
            v058s_dampen_score(
                corrected,
                "Blink/Flicker / ETB Value",
                0.55,
                "Downgraded because blink/ETB value is not more commander-anchored than the token-resource engine.",
            )
        for broad in ["Go-Wide Combat", "Go-Wide / Go-Tall Token Combat", "Tokens"]:
            if broad in corrected and corrected["Token Resource Engine"].get("score", 0) >= corrected[broad].get("score", 0):
                v058s_dampen_score(corrected, broad, 0.75, "Downgraded behind commander-defined token-resource engine.")

    # Agatha-style: activated ability cost-reduction based on power should beat Voltron unless equipment/aura density truly dominates.
    if power_reduction_commander:
        activated_name, _ = v058s_get_candidate(corrected, "Activated Abilities / Power-Reduction Engine", "Activated Abilities")
        if activated_name:
            equipment_aura_density = role_counts.get("equipment_synergy", 0) + role_counts.get("aura_synergy", 0) + role_counts.get("attachment_synergy", 0)
            v058s_force_score(
                corrected,
                activated_name,
                highest_non_meta + 15,
                "Commander reduces activated ability costs based on power; Activated Abilities / Power-Reduction is the commander-defined engine.",
                "commander_defined_package",
            )
            if "Voltron" in corrected and equipment_aura_density < 14:
                v058s_dampen_score(
                    corrected,
                    "Voltron",
                    0.58,
                    "Downgraded because equipment/aura density is not high enough to beat the commander-defined activated-ability engine.",
                )
            if "Equipment / Aura Voltron" in corrected and equipment_aura_density < 14:
                v058s_dampen_score(
                    corrected,
                    "Equipment / Aura Voltron",
                    0.58,
                    "Downgraded because equipment/aura density is not high enough to beat the commander-defined activated-ability engine.",
                )

    # Keep all final score fields synchronized for diagnostics and selection.
    for name, data in corrected.items():
        if isinstance(data, dict) and not str(name).startswith("__"):
            score = int(data.get("score", 0) or 0)
            data.setdefault("raw_score", score)
            data["adjusted_score"] = score
            data["final_score"] = score
            data["evidence"] = dedupe_reasons(data.get("evidence", []), 3)
    return corrected


# Re-run primary/secondary selection after the new commander-defined priority rules. If a low-confidence
# primary is beaten by a commander-defined secondary, promote the commander-defined package.
_v058s_prev_choose_primary_secondary_strategy = choose_primary_secondary_strategy

def choose_primary_secondary_strategy(archetype_scores):
    primary_name, primary_data, secondary_name, secondary_data, ordered = _v058s_prev_choose_primary_secondary_strategy(archetype_scores)
    candidates = [(n, d) for n, d in archetype_scores.items() if isinstance(d, dict) and not str(n).startswith("__") and int(d.get("score", 0) or 0) > 0]
    candidates.sort(key=lambda item: int(item[1].get("score", 0) or 0), reverse=True)
    if not candidates:
        return primary_name, primary_data, secondary_name, secondary_data, ordered

    highest_name, highest_data = candidates[0]
    highest_score = int(highest_data.get("score", 0) or 0)
    primary_score = int(primary_data.get("score", 0) or 0)
    specific_reason = str(primary_data.get("primary_priority_reason", "") or "").strip()
    if highest_name != primary_name and highest_score > primary_score * 1.10 and not specific_reason:
        secondary_name, secondary_data = primary_name, primary_data
        primary_name, primary_data = highest_name, highest_data
        primary_data["primary_priority_reason"] = "Promoted by v0.5.8 stabilization because it had the highest final score and no specific reason justified the lower-scoring primary."

    # If a commander-defined package is close and the current primary reports low anchor confidence, prefer the commander-defined package.
    for name, data in candidates:
        if name == primary_name:
            continue
        if data.get("strategy_layer") == "commander_defined_package" and int(data.get("score", 0) or 0) >= max(40, int(primary_data.get("score", 0) or 0) * 0.85):
            secondary_name, secondary_data = primary_name, primary_data
            primary_name, primary_data = name, data
            break

    # Pick secondary cleanly from remaining highest score.
    for name, data in candidates:
        if name != primary_name:
            secondary_name, secondary_data = name, data
            break
    return primary_name, primary_data, secondary_name, secondary_data, candidates


# Infrastructure cut cap: Strict/Brutal can review infrastructure, but should not fill the list with ramp/draw/interaction.
_v058s_prev_apply_cut_role_distribution_caps_to_review = apply_cut_role_distribution_caps_to_review

def v058s_cut_entry_roles(entry, card_role_tags_by_card):
    name = entry.get("card_name", "") if isinstance(entry, dict) else ""
    return set(card_role_tags_by_card.get(name, []))


def v058s_role_bucket(tags):
    if tags.intersection({"counterspell", "targeted_removal", "board_wipe", "mass_removal", "stack_interaction", "protection", "free_interaction"}):
        return "interaction"
    if tags.intersection({"ramp", "mana_rock", "mana_dork", "mana_fixing", "mana_source"}):
        return "ramp"
    if tags.intersection({"card_draw", "card_advantage", "card_selection"}):
        return "card_advantage"
    return "other"


def apply_cut_role_distribution_caps_to_review(review, card_role_tags_by_card):
    review = _v058s_prev_apply_cut_role_distribution_caps_to_review(review, card_role_tags_by_card)
    mode = str(CUT_DEPTH_CONFIG.get("mode", "normal"))
    target = int(CUT_DEPTH_CONFIG.get("optional_cut_target", 5) or 5)
    caps = {
        "normal": {"interaction": max(1, int(target * 0.25)), "ramp": max(1, int(target * 0.25)), "card_advantage": max(1, int(target * 0.25))},
        "strict": {"interaction": max(2, int(target * 0.30)), "ramp": max(2, int(target * 0.30)), "card_advantage": max(2, int(target * 0.30))},
        "brutal": {"interaction": max(3, int(target * 0.35)), "ramp": max(3, int(target * 0.35)), "card_advantage": max(3, int(target * 0.35))},
    }.get(mode, {"interaction": max(1, int(target * 0.25)), "ramp": max(1, int(target * 0.25)), "card_advantage": max(1, int(target * 0.25))})

    moved = []
    for key in ["possible_cuts", "recommended_cuts"]:
        seen = Counter()
        kept = []
        for entry in review.get(key, []) or []:
            tags = v058s_cut_entry_roles(entry, card_role_tags_by_card)
            bucket = v058s_role_bucket(tags)
            if bucket in caps:
                seen[bucket] += 1
                if seen[bucket] > caps[bucket]:
                    moved.append({
                        "card_name": entry.get("card_name", "Unknown"),
                        "why_questionable": f"Moved out of normal cut candidates by {bucket} role-balance cap.",
                        "why_might_belong": "Ramp, card advantage, interaction, and protection are necessary deck functions unless clearly overrepresented.",
                        "what_to_watch": "Only cut this after confirming the deck still has enough of this role and the card is narrow, inefficient, or redundant.",
                    })
                    continue
            kept.append(entry)
        review[key] = kept
    if moved:
        review["playtest_before_cutting"] = (review.get("playtest_before_cutting", []) or []) + moved[:12]
        review.setdefault("diagnostic_warnings", [])
        review["diagnostic_warnings"].append("Warning: Infrastructure cut candidates were capped so ramp/card draw/interaction do not dominate the review list.")
    review["actual_responsible_cut_candidates"] = len(review.get("recommended_cuts", []) or []) + len(review.get("possible_cuts", []) or [])
    return review




# v0.6.1.2 quality cleanup: remove contradictory replacement needs.
_quality_prev_get_deck_role_needs = get_deck_role_needs

def get_deck_role_needs(role_tag_counts, scryfall_land_count, average_nonland_mana_value, primary_strategy):
    needs = list(_quality_prev_get_deck_role_needs(role_tag_counts, scryfall_land_count, average_nonland_mana_value, primary_strategy))

    overfilled = set()
    if role_tag_counts.get("card_draw", 0) + role_tag_counts.get("card_advantage", 0) >= 14:
        overfilled.add("More card draw")
    if role_tag_counts.get("ramp", 0) >= 16:
        overfilled.add("More ramp")
    if role_tag_counts.get("targeted_removal", 0) >= 8:
        overfilled.add("More targeted removal")
    if role_tag_counts.get("board_wipe", 0) >= 4:
        overfilled.add("More board wipes")
    if role_tag_counts.get("token_maker", 0) >= 14:
        overfilled.add("More token production")
    if role_tag_counts.get("recursion", 0) >= 7:
        overfilled.add("More recursion")
    if role_tag_counts.get("graveyard_enabler", 0) + role_tag_counts.get("self_mill", 0) >= 12:
        overfilled.add("More graveyard setup")

    filtered = [need for need in needs if need not in overfilled]

    # Strategy-specific wording correction: wheels decks may need the right kind of draw,
    # not simply more raw card draw.
    if primary_strategy == "Wheels / Draw-Punisher / Group Slug":
        if "More card draw" in needs and "More card draw" in overfilled:
            filtered.append("Better wheel/forced-draw density")

    seen = set()
    result = []
    for need in filtered:
        if need not in seen:
            seen.add(need)
            result.append(need)
    return result

# Strategy-specific replacement categories. Keep exact-card replacement disabled; make categories more useful.
_v058s_prev_determine_replacement_categories = determine_replacement_categories

def determine_replacement_categories(candidate, card, tags, cut_type, primary_strategy, secondary_strategy, role_tag_counts, deck_needs):
    categories = list(_v058s_prev_determine_replacement_categories(candidate, card, tags, cut_type, primary_strategy, secondary_strategy, role_tag_counts, deck_needs))
    overfilled_replacement_categories = set()
    if role_tag_counts.get("card_draw", 0) + role_tag_counts.get("card_advantage", 0) >= 14:
        overfilled_replacement_categories.add("More card draw")
    if role_tag_counts.get("ramp", 0) >= 16:
        overfilled_replacement_categories.add("More ramp")
    if role_tag_counts.get("targeted_removal", 0) >= 8:
        overfilled_replacement_categories.add("More targeted removal")
    if role_tag_counts.get("board_wipe", 0) >= 4:
        overfilled_replacement_categories.add("More board wipes")
    if role_tag_counts.get("token_maker", 0) >= 14:
        overfilled_replacement_categories.add("More token production")
    if role_tag_counts.get("recursion", 0) >= 7:
        overfilled_replacement_categories.add("More recursion")
    if role_tag_counts.get("graveyard_enabler", 0) + role_tag_counts.get("self_mill", 0) >= 12:
        overfilled_replacement_categories.add("More graveyard setup")
    categories = [cat for cat in categories if cat not in overfilled_replacement_categories]
    strategy_text = f"{primary_strategy} {secondary_strategy}".lower()
    specific = []
    if "adventure" in strategy_text or "modal" in strategy_text:
        specific.extend(["More adventure/modal support", "More primary-plan enablers", "More primary-plan payoffs"])
    if "token resource" in strategy_text:
        specific.extend(["More token production", "More commander-specific enablers", "More engine density"])
    if "activated" in strategy_text or "power-reduction" in strategy_text or "power reduction" in strategy_text:
        specific.extend(["More activated ability support", "More mana sinks", "More commander-specific enablers"])
    if "topdeck" in strategy_text or "permanent-type" in strategy_text:
        specific.extend(["More topdeck manipulation", "More permanent-type value", "More primary-plan enablers"])
    if "creature cost" in strategy_text or "pod" in strategy_text or "toolbox" in strategy_text:
        specific.extend(["More pod-chain support", "More creature density", "More creature-based interaction"])
    if "graveyard" in strategy_text or "recursion" in strategy_text:
        specific.extend(["More graveyard setup", "More recursion", "More primary-plan enablers"])
    if "blink" in strategy_text or "flicker" in strategy_text or "etb" in strategy_text:
        specific.extend(["More blink/flicker support", "More ETB payoffs", "More protection"])

    combined = []
    for item in specific + categories:
        # Keep known categories, but also allow a few new useful strategy-specific phrases.
        if item in overfilled_replacement_categories:
            continue
        if item not in combined:
            combined.append(item)
    return combined[:4] if combined else ["More primary-plan support"]


# Hide debug/developer sections from normal report while preserving debug diagnostics files.
_v058s_prev_clean_user_facing_role_tags_v057 = clean_user_facing_role_tags_v057

def clean_user_facing_role_tags_v057(report_text, attribute_relevance):
    report_text = _v058s_prev_clean_user_facing_role_tags_v057(report_text, attribute_relevance)
    # Replace remaining developer-heavy blocks if they leak into normal report.
    patterns = [
        (r"\n=+\n16\. Diagnostic Role Tags\n-+\n.*?(?=\n=+\n18\. Possible Cut Flags|\n=+\n18\.|\Z)", "\n==============================\n16. Diagnostic Role Tags\n------------------------------\nRaw card role tags and tag-based review notes are hidden from Normal User Mode and preserved in debug diagnostics.\n"),
        (r"\n=+\n16\. Card Role Tags by Card\n-+\n.*?(?=\n=+\n18\. Possible Cut Flags|\n=+\n18\.|\Z)", "\n==============================\n16. Diagnostic Role Tags\n------------------------------\nRaw card role tags and tag-based review notes are hidden from Normal User Mode and preserved in debug diagnostics.\n"),
        (r"\n=+\n17\. Tag-Based Review Notes\n-+\n.*?(?=\n=+\n18\. Possible Cut Flags|\n=+\n18\.|\Z)", ""),
    ]
    for pattern, repl in patterns:
        report_text = re.sub(pattern, repl, report_text, flags=re.DOTALL)
    # User-facing version-label cleanup only.
    report_text = report_text.replace("v0.5.7", "v0.5.8")
    return report_text




# ==============================
# v0.5.8 final readiness patch — stable analysis base preserved for v0.6.2.6 User-Guided Review Prompt
# ==============================

def v06r_card_text(card):
    return normalize_text((card.get("name", "") if card else "") + " " + (card.get("type_line", "") if card else "") + " " + (get_full_oracle_text(card) if card else ""))


def v06r_commander_rewards_creature_etb_copy(commander_cards):
    text = v058s_commander_text_blob(commander_cards)
    return (
        ("create" in text and "token" in text and "copy" in text and ("enters" in text or "enters the battlefield" in text))
        or ("whenever" in text and "dragon" in text and "nontoken" in text and "copy" in text)
        or ("token that's a copy" in text and ("dragon" in text or "creature" in text))
    )


def v06r_is_true_tiamat_or_dragonstorm_commander(commander_cards):
    text = v058s_commander_text_blob(commander_cards)
    return (
        "dragonstorm" in text
        or ("enters the battlefield" in text and "search your library" in text and "dragon card" in text)
        or ("search your library" in text and "five dragon" in text)
        or ("search your library" in text and "dragon cards" in text and "put them into your hand" in text)
    )


def v06r_has_true_dragonstorm_package(role_counts, commander_cards):
    if v06r_is_true_tiamat_or_dragonstorm_commander(commander_cards):
        return True
    dragonstorm = role_counts.get("dragonstorm_combo", 0)
    dragon_typal = role_counts.get("dragon_typal", 0)
    tutor_chain = role_counts.get("tutor_chain", 0)
    combo_tutor = role_counts.get("combo_tutor", 0)
    true_speed = role_counts.get("true_fast_mana", 0) + role_counts.get("true_ritual", 0) + role_counts.get("combo_protection", 0)
    # Normal dragon tutor/card-selection effects should not become Dragonstorm/Tiamat primary.
    return (
        dragonstorm >= 2
        or (dragonstorm >= 1 and tutor_chain >= 3 and combo_tutor >= 2)
        or (dragon_typal >= 12 and tutor_chain >= 5 and combo_tutor >= 4 and true_speed >= 1)
    )


def v06r_apply_creature_cheat_role_repair(card_name, card, tags, commander_cards):
    tags = set(tags or [])
    text = v06r_card_text(card)
    if not card:
        return sorted(tags)
    creature_cheat = (
        ("put a creature card from your hand onto the battlefield" in text)
        or ("put target creature card from your hand onto the battlefield" in text)
        or ("put a creature card" in text and "onto the battlefield" in text and "from your hand" in text)
        or ("sneak attack" in normalize_text(card_name))
    )
    if creature_cheat:
        tags.update({"creature_cheat", "temporary_creature_cheat", "etb_setup", "haste_deployment", "high_power_value_piece"})
        if v06r_commander_rewards_creature_etb_copy(commander_cards):
            tags.update({"commander_synergy_possible", "direct_commander_support", "primary_plan_support", "dragon_copy_value", "etb_value", "synergy_piece"})
    return sorted(tags)


def v06r_apply_role_repairs(unique_cards, scryfall_lookup, card_role_tags_by_card, commander_cards):
    changed = False
    for card_name in sorted(unique_cards):
        card = scryfall_lookup.get(card_name.lower())
        old_tags = set(card_role_tags_by_card.get(card_name, []))
        new_tags = set(v06r_apply_creature_cheat_role_repair(card_name, card, old_tags, commander_cards))
        if new_tags != old_tags:
            card_role_tags_by_card[card_name] = sorted(new_tags)
            changed = True
    return changed


def v06r_rebuild_role_counts(card_role_tags_by_card, unique_cards):
    counts = Counter()
    for card_name, quantity in unique_cards.items():
        for tag in card_role_tags_by_card.get(card_name, []):
            counts[tag] += quantity
    return counts


def v06r_apply_strategy_readiness_patch(archetype_scores, role_counts, commander_cards):
    scores = {name: (dict(data) if isinstance(data, dict) else data) for name, data in archetype_scores.items()}
    dragon_copy_name = "Dragon Copy / Token-Copy Value"
    dragonstorm_name = "Dragonstorm / Tiamat Tutor Chain"
    copy_commander = v06r_commander_rewards_creature_etb_copy(commander_cards)
    true_dragonstorm = v06r_has_true_dragonstorm_package(role_counts, commander_cards)

    if dragonstorm_name in scores and isinstance(scores[dragonstorm_name], dict) and not true_dragonstorm:
        data = scores[dragonstorm_name]
        old = int(data.get("score", 0) or 0)
        data.setdefault("raw_score", old)
        data["score"] = min(int(old * 0.28), 95)
        data["adjusted_score"] = data["score"]
        data["final_score"] = data["score"]
        data["gate_passed"] = False
        data["primary_eligible"] = False
        reason = "Failed v0.5.8 final Dragonstorm/Tiamat gate: normal Dragon tutors and Dragon typal support are not enough without true Dragonstorm, Tiamat-style commander text, compact tutor-chain combo evidence, or fast protected combo structure."
        data["suppression_reason"] = reason
        data["gate_failed_reason"] = reason
        data["evidence"] = dedupe_reasons(data.get("evidence", []) + [reason], 3)

    if copy_commander and dragon_copy_name in scores and isinstance(scores[dragon_copy_name], dict):
        data = scores[dragon_copy_name]
        old = int(data.get("score", 0) or 0)
        best_competing = max((int(d.get("score", 0) or 0) for n, d in scores.items() if isinstance(d, dict) and not str(n).startswith("__") and n != dragon_copy_name), default=0)
        data.setdefault("raw_score", old)
        data["score"] = max(old, best_competing + 20, 180)
        data["adjusted_score"] = data["score"]
        data["final_score"] = data["score"]
        data["gate_passed"] = True
        data["primary_eligible"] = True
        data["strategy_layer"] = "commander_defined_package"
        data["primary_priority_reason"] = "Commander creates token copies from creature/Dragon ETB patterns, so Dragon Copy / Token-Copy Value is the commander-defined engine."
        data["evidence"] = dedupe_reasons(data.get("evidence", []) + [data["primary_priority_reason"]], 3)
    return scores


def v06r_same_strategy_family(a, b):
    a = normalize_text(a)
    b = normalize_text(b)
    families = [
        {"go-wide / go-tall token combat", "go-wide combat", "tokens", "token resource engine"},
        {"dragon copy / token-copy value", "copy / clone value"},
        {"historic / legends matter", "legends matter / legendary cascade"},
        {"graveyard recursion", "graveyard self-mill / recursion", "reanimator"},
        {"activated abilities", "activated abilities / power-reduction engine"},
    ]
    return any(a in fam and b in fam for fam in families)


_v06r_prev_choose_primary_secondary_strategy = choose_primary_secondary_strategy

def choose_primary_secondary_strategy(archetype_scores):
    primary_name, primary_data, secondary_name, secondary_data, ordered = _v06r_prev_choose_primary_secondary_strategy(archetype_scores)
    candidates = [(n, d) for n, d in archetype_scores.items() if isinstance(d, dict) and not str(n).startswith("__") and int(d.get("score", 0) or 0) > 0 and d.get("primary_eligible", True)]
    candidates.sort(key=lambda item: int(item[1].get("score", 0) or 0), reverse=True)
    if not candidates:
        return primary_name, primary_data, secondary_name, secondary_data, ordered
    primary_name, primary_data = candidates[0]
    secondary_name, secondary_data = "No distinct secondary strategy detected", {"score": 0, "anchor_hits": 0, "commander_anchor_hits": 0, "evidence": []}
    for name, data in candidates[1:]:
        if not v06r_same_strategy_family(primary_name, name):
            secondary_name, secondary_data = name, data
            break
    return primary_name, primary_data, secondary_name, secondary_data, candidates


def v06r_build_illegal_duplicate_required_cut_entries(illegal_duplicate_cards, required_cuts, card_role_tags_by_card):
    entries = []
    for duplicate in illegal_duplicate_cards or []:
        if len(entries) >= required_cuts:
            break
        card_name = duplicate.get("card_name", "Unknown")
        extra_copies = max(1, int(duplicate.get("quantity", 2) or 2) - 1)
        entries.append({
            "card_name": card_name,
            "score": 1000,
            "category": "Illegal Duplicate / Required Legality Fix",
            "bucket": "Required Legality Fix",
            "tags": sorted(card_role_tags_by_card.get(card_name, [])),
            "reasons": [
                f"Remove {min(extra_copies, required_cuts - len(entries))} extra copy of {card_name} before making strategy-based cuts.",
                "Commander singleton legality takes priority over normal replaceability scoring.",
                "This duplicate-removal fix can also satisfy the required over-100-card cut count."
            ],
            "legality_fix": True,
        })
    return entries


def v06r_apply_legality_first_required_cuts(cut_pressure_review, illegal_duplicate_cards, card_role_tags_by_card):
    required_cuts = int(cut_pressure_review.get("required_cuts", 0) or 0)
    if required_cuts <= 0:
        return cut_pressure_review
    duplicate_entries = v06r_build_illegal_duplicate_required_cut_entries(illegal_duplicate_cards, required_cuts, card_role_tags_by_card)
    if not duplicate_entries:
        return cut_pressure_review
    duplicate_names = {entry["card_name"] for entry in duplicate_entries}
    previous_required = [entry for entry in cut_pressure_review.get("required_cuts_list", []) if entry.get("card_name") not in duplicate_names]
    new_required = (duplicate_entries + previous_required)[:required_cuts]
    cut_pressure_review["required_cuts_list"] = new_required
    cut_pressure_review["additional_required_cuts_needed"] = max(0, required_cuts - len(new_required))
    cut_pressure_review["required_cut_shortfall"] = cut_pressure_review["additional_required_cuts_needed"]
    # Do not show the duplicate legality fix as protected/context-dependent at the same time.
    for key in ["optional_cuts_list", "context_dependent"]:
        cut_pressure_review[key] = [entry for entry in cut_pressure_review.get(key, []) if entry.get("card_name") not in duplicate_names]
    for key in ["protected", "protected_core_engine", "protected_essential_utility", "protected_high_synergy"]:
        cut_pressure_review[key] = [(name, reason) for name, reason in cut_pressure_review.get(key, []) if name not in duplicate_names]
    return cut_pressure_review


def v06r_clean_required_cut_entry_text(entry):
    if not isinstance(entry, dict):
        return entry
    if entry.get("legality_fix"):
        entry["cut_type"] = "Required Legality Fix"
        entry["confidence"] = "High"
        entry["reason"] = "; ".join(entry.get("reasons", []))
        entry["replacement_categories"] = []
        entry["exact_replacement_note"] = "No replacement needed if removing the extra duplicate brings the deck to legal size."
    return entry


_v06r_prev_make_possible_cut_entry = make_possible_cut_entry

def make_possible_cut_entry(candidate, card, primary_strategy, secondary_strategy, role_tag_counts, deck_needs, required=False, intended_bracket="Unknown", estimated_bracket="Unknown"):
    entry = _v06r_prev_make_possible_cut_entry(candidate, card, primary_strategy, secondary_strategy, role_tag_counts, deck_needs, required, intended_bracket, estimated_bracket)
    if isinstance(candidate, dict) and candidate.get("legality_fix"):
        entry.update({
            "confidence": "High",
            "cut_type": "Required Legality Fix",
            "reason": "; ".join(candidate.get("reasons", [])),
            "replacement_categories": [],
            "exact_replacement_note": "No replacement needed if this duplicate removal brings the deck to legal size.",
        })
    return entry


_v06r_prev_format_cut_candidate = format_cut_candidate

def format_cut_candidate(candidate):
    if isinstance(candidate, dict) and candidate.get("legality_fix"):
        reason_text = "; ".join(candidate.get("reasons", [])[:3])
        return f"{candidate['card_name']} — Illegal Duplicate / Required Legality Fix. {reason_text}"
    return _v06r_prev_format_cut_candidate(candidate)



# ==============================
# v0.6.1 Collection / Card Pool Helpers
# ==============================
def find_collection_file():
    """Find an optional local collection/card-pool file without interrupting normal runs."""
    env_path = os.environ.get("MTG_COLLECTION_FILE") or os.environ.get("MTG_CARD_POOL_FILE")
    if env_path:
        candidate = Path(env_path)
        return candidate if candidate.exists() else candidate

    candidates = [
        COLLECTION_FOLDER / "collection.txt",
        COLLECTION_FOLDER / "card_pool.txt",
        COLLECTION_FOLDER / "collection.csv",
        COLLECTION_FOLDER / "card_pool.csv",
        Path("collection.txt"),
        Path("card_pool.txt"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def clean_collection_card_name(raw_name):
    name = str(raw_name or "").strip().strip('"').strip("'")
    name = re.sub(r"\s+", " ", name)
    # Remove common deck-export suffixes like "(SET) 123" or collector numbers.
    name = re.sub(r"\s+\([A-Za-z0-9]{2,6}\)\s*\d*[A-Za-z]?\s*$", "", name).strip()
    name = re.sub(r"\s+\[[A-Za-z0-9]{2,6}\]\s*\d*[A-Za-z]?\s*$", "", name).strip()
    return name


def parse_collection_line(line):
    line = str(line or "").strip()
    if not line or line.startswith("#") or line.startswith("//"):
        return None

    lowered = normalize_text(line)
    if lowered in SECTION_HEADERS or lowered in NON_MAINBOARD_SECTION_HEADERS or lowered in REFERENCE_ONLY_SECTION_HEADERS:
        return None
    if lowered in {"name", "card", "cards", "quantity,name", "name,quantity", "count,name", "qty,name"}:
        return None

    # CSV-ish formats: quantity,name or name,quantity.
    if "," in line:
        parts = [p.strip().strip('"').strip("'") for p in line.split(",")]
        if len(parts) >= 2:
            if parts[0].isdigit():
                return int(parts[0]), clean_collection_card_name(parts[1])
            if parts[1].isdigit():
                return int(parts[1]), clean_collection_card_name(parts[0])

    # Text decklist formats: "1 Sol Ring", "1x Sol Ring", "1x, Sol Ring".
    match = re.match(r"^\s*(\d+)\s*x?\s+(.+?)\s*$", line, flags=re.IGNORECASE)
    if match:
        return int(match.group(1)), clean_collection_card_name(match.group(2))

    # Plain card name means one available copy.
    if any(ch.isalpha() for ch in line):
        return 1, clean_collection_card_name(line)

    return None


def load_collection_card_pool(collection_file):
    pool = Counter()
    ignored = []
    if not collection_file:
        return pool, ignored, "No collection/card-pool file found."
    collection_file = Path(collection_file)
    if not collection_file.exists():
        return pool, [str(collection_file)], "Collection/card-pool file path was provided but not found."

    for original_line in collection_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        parsed = parse_collection_line(original_line)
        if parsed is None:
            continue
        quantity, card_name = parsed
        if quantity <= 0 or not card_name:
            ignored.append(original_line)
            continue
        pool[card_name] += quantity
    return pool, ignored, f"Loaded collection/card-pool file: {collection_file}"


def card_is_legal_for_commander_color(card, commander_color_identity_set):
    if not card:
        return False
    if not commander_color_identity_set and commander_color_identity_text != "Colorless":
        return True
    return set(card.get("color_identity", [])).issubset(set(commander_color_identity_set))


def normalize_card_name_key(name):
    return normalize_text(str(name or "").split("//", 1)[0].strip())


def get_existing_deck_name_keys(unique_cards):
    keys = set()
    for raw_name in (unique_cards or {}).keys():
        keys.add(normalize_card_name_key(raw_name))
        keys.add(normalize_text(raw_name))
        lookup_card = globals().get("scryfall_lookup", {}).get(str(raw_name).lower()) if isinstance(globals().get("scryfall_lookup", {}), dict) else None
        if lookup_card:
            keys.add(normalize_card_name_key(lookup_card.get("name", raw_name)))
            keys.add(normalize_text(lookup_card.get("name", raw_name)))
            for face in lookup_card.get("card_faces", []) or []:
                keys.add(normalize_card_name_key(face.get("name", "")))
    return {key for key in keys if key}


def card_already_in_deck(card, unique_cards):
    if not card:
        return False
    existing_keys = get_existing_deck_name_keys(unique_cards)
    names_to_check = {
        normalize_card_name_key(card.get("name", "")),
        normalize_text(card.get("name", "")),
    }
    for face in card.get("card_faces", []) or []:
        names_to_check.add(normalize_card_name_key(face.get("name", "")))
        names_to_check.add(normalize_text(face.get("name", "")))
    return any(name and name in existing_keys for name in names_to_check)


def replacement_category_to_tags(category):
    mapping = {
        "More ramp": {"ramp", "mana_rock", "mana_dork", "mana_fixing", "extra_land_play"},
        "More card draw": {"card_draw", "card_advantage", "card_selection"},
        "More targeted removal": {"targeted_removal", "stack_interaction", "counterspell"},
        "More board wipes": {"board_wipe", "mass_removal"},
        "More sacrifice outlets": {"sacrifice_outlet", "free_sacrifice_outlet", "artifact_sacrifice"},
        "More recursion": {"recursion", "graveyard_enabler"},
        "More finishers": {"win_condition", "damage_payoff", "big_mana_payoff", "high_mv_payoff", "combat_synergy"},
        "More protection": {"protection", "stack_interaction", "free_interaction", "redirection_protection"},
        "More lands": {"mana_source", "utility_land", "landfall", "extra_land_play", "lands_matter"},
        "Lower mana curve": {"ramp", "cost_reducer", "card_selection", "targeted_removal"},
        "More commander synergy": {"commander_synergy_possible", "direct_commander_support", "commander_enabler", "commander_payoff", "commander_protection"},
        "More token production": {"token_maker", "go_wide_token_engine", "token_resource_engine"},
        "More graveyard setup": {"graveyard_enabler", "self_mill", "discard_outlet"},
        "More primary-plan support": set(get_primary_secondary_tag_sets(globals().get("primary_strategy", ""), globals().get("secondary_strategy", ""))[0]),
        "More secondary strategy support": set(get_primary_secondary_tag_sets(globals().get("primary_strategy", ""), globals().get("secondary_strategy", ""))[1]),
        "Better fixing": {"mana_fixing", "ramp", "mana_rock", "mana_dork", "mana_source"},
        "More artifact support": {"artifact_payoff", "artifact_token_synergy", "artifact_sacrifice", "treasure_synergy"},
        "More enchantment support": {"aura_synergy", "permanent_type_value"},
        "More instant/sorcery density": {"spell_payoff", "noncreature_spell_payoff", "card_draw", "targeted_removal", "counterspell"},
        "More creature density": {"creature_type_present", "etb_value", "ltb_value"},
        "More tribal density": {"typal_density_piece", "typal_enabler", "typal_payoff", "tribal_payoff"},
        "More evasion": {"combat_synergy", "go_tall_support", "attack_safety"},
        "More combat finishers": {"combat_synergy", "attack_trigger_payoff", "extra_combat", "anthem", "go_tall_support"},
        "More mana sinks": {"mana_sink", "activated_ability_synergy", "power_matters"},
        "More utility lands": {"utility_land", "mana_source", "lands_matter"},
        "More role compression": {"card_advantage", "targeted_removal", "ramp", "protection", "synergy_piece"},
        "More primary-plan enablers": set(get_primary_secondary_tag_sets(globals().get("primary_strategy", ""), globals().get("secondary_strategy", ""))[0]),
        "More primary-plan payoffs": set(get_primary_secondary_tag_sets(globals().get("primary_strategy", ""), globals().get("secondary_strategy", ""))[0]) | {"win_condition"},
        "More engine density": {"synergy_piece", "card_advantage", "commander_synergy_possible"},
        "More bridge cards": {"synergy_piece", "commander_synergy_possible", "primary_plan_support", "secondary_plan_support"},
        "More commander-specific enablers": {"commander_synergy_possible", "commander_enabler", "direct_commander_support"},
        "More activated ability support": {"activated_ability_synergy", "activated_ability_source", "activated_ability_payoff", "mana_sink"},
    }
    return set(mapping.get(category, set()))


def build_collection_replacement_candidates(collection_pool, collection_ignored_lines, scryfall_lookup, unique_cards, commander_color_identity_set, deck_needs, primary_strategy, secondary_strategy):
    result = {
        "status": "No collection/card-pool file loaded.",
        "loaded": False,
        "total_cards": 0,
        "unique_cards": 0,
        "not_found": [],
        "ignored_lines": collection_ignored_lines[:20],
        "candidates_by_need": {},
        "general_candidates": [],
    }
    if not collection_pool:
        return result

    result["loaded"] = True
    result["total_cards"] = sum(collection_pool.values())
    result["unique_cards"] = len(collection_pool)
    result["status"] = "Collection/card-pool file loaded. Candidates below are color-identity legal and appear available beyond the current decklist."

    primary_tags, secondary_tags = get_primary_secondary_tag_sets(primary_strategy, secondary_strategy)
    strategy_tags = set(primary_tags) | set(secondary_tags)
    scored_general = []

    for card_name, owned_qty in collection_pool.items():
        card = scryfall_lookup.get(card_name.lower())
        if not card:
            result["not_found"].append(card_name)
            continue
        if card_already_in_deck(card, unique_cards):
            continue
        if card_already_in_deck(card, unique_cards):
            continue
        deck_qty = unique_cards.get(card_name, 0)
        available_qty = owned_qty - deck_qty
        if available_qty <= 0:
            continue
        if not card_is_legal_for_commander_color(card, commander_color_identity_set):
            continue
        tags = set(infer_card_role_tags(card, commander_cards_scryfall))
        if not tags:
            continue
        strategy_overlap = tags.intersection(strategy_tags)
        utility_overlap = tags.intersection({"ramp", "card_draw", "card_advantage", "targeted_removal", "board_wipe", "counterspell", "protection", "mana_fixing"})
        score = len(strategy_overlap) * 3 + len(utility_overlap) * 2
        representative_mv = get_representative_nonland_mana_value(card)
        if representative_mv is not None and representative_mv <= 3:
            score += 1
        if score > 0:
            scored_general.append({
                "card_name": card.get("name", card_name),
                "owned_qty": owned_qty,
                "available_qty": available_qty,
                "mana_value": representative_mv,
                "roles": sorted(tags)[:12],
                "matched_roles": sorted(strategy_overlap | utility_overlap)[:8],
                "score": score,
            })

    for need in deck_needs or []:
        need_tags = replacement_category_to_tags(need)
        if not need_tags:
            continue
        scored = []
        for item in scored_general:
            tags = set(item["roles"])
            overlap = tags.intersection(need_tags)
            if not overlap:
                continue
            scored.append({**item, "matched_roles": sorted(overlap)[:8], "need": need})
        scored.sort(key=lambda item: (-item["score"], item["mana_value"] if item["mana_value"] is not None else 99, item["card_name"]))
        if scored:
            result["candidates_by_need"][need] = scored[:8]

    scored_general.sort(key=lambda item: (-item["score"], item["mana_value"] if item["mana_value"] is not None else 99, item["card_name"]))
    result["general_candidates"] = scored_general[:20]
    result["not_found"] = sorted(result["not_found"])[:50]
    return result


print("Loading Scryfall card data...")
scryfall_cards = json.loads(SCRYFALL_FILE.read_text(encoding="utf-8"))
scryfall_lookup = {card["name"].lower(): card for card in scryfall_cards if card.get("name")}

# Parse decklist
cards = []
reference_cards = []
cards_by_section = defaultdict(list)
reference_cards_by_section = defaultdict(list)
card_manual_sections = defaultdict(set)
ignored_lines = []
input_hygiene_warnings = []
ignored_sections = Counter()
current_section = "Unknown / Needs Review"
current_section_is_reference = False

for original_line in DECK_FILE.read_text(encoding="utf-8").splitlines():
    line = original_line.strip()

    if not line:
        continue

    # Optional: ignore common comment lines
    if line.startswith("#") or line.startswith("//"):
        continue

    lower_line = line.lower()

    if lower_line in NON_MAINBOARD_SECTION_HEADERS or lower_line in REFERENCE_ONLY_SECTION_HEADERS:
        current_section = f"Reference: {line}"
        current_section_is_reference = True
        ignored_sections[current_section] += 0
        continue

    if lower_line in SECTION_HEADERS:
        current_section = SECTION_HEADERS[lower_line]
        current_section_is_reference = section_is_non_mainboard(current_section)
        continue

    if line[0].isdigit():
        parts = line.split(" ", 1)

        if len(parts) == 2:
            quantity_text = parts[0]
            card_name = parts[1].strip()

            try:
                quantity = int(quantity_text)
            except ValueError:
                ignored_lines.append(original_line)
                continue

            target_is_reference = current_section_is_reference or section_is_non_mainboard(current_section)

            # v0.5.7: A section named "Tokens" is ambiguous.
            # If it contains real Scryfall cards, count them as maindeck.
            # If it contains token/helper names, ignore those entries as reference-only.
            is_tokens_category = is_token_helper_section(current_section)
            if is_tokens_category and should_ignore_card_from_tokens_section(card_name, scryfall_lookup):
                reference_section = f"Reference: {current_section}"
                for _ in range(quantity):
                    reference_cards.append(card_name)
                    reference_cards_by_section[reference_section].append(card_name)
                ignored_sections[reference_section] += quantity
                continue

            if target_is_reference:
                for _ in range(quantity):
                    reference_cards.append(card_name)
                    reference_cards_by_section[current_section].append(card_name)
                ignored_sections[current_section] += quantity
                continue

            for _ in range(quantity):
                cards.append(card_name)
                cards_by_section[current_section].append(card_name)
                card_manual_sections[card_name].add(current_section)
        else:
            ignored_lines.append(original_line)
    else:
        # v0.4.5 input hygiene:
        # Treat unknown non-card lines as custom/player-defined category headers,
        # but exclude known non-mainboard/reference-only sections from the real deck.
        normalized_header = normalize_text(line)
        if normalized_header in NON_MAINBOARD_SECTION_HEADERS or normalized_header in REFERENCE_ONLY_SECTION_HEADERS:
            current_section = f"Reference: {line}"
            current_section_is_reference = True
        else:
            current_section = f"Custom: {line}"
            current_section_is_reference = section_is_non_mainboard(current_section)
        continue

unique_cards = Counter(cards)

# Command zone: supports partner commanders, backgrounds, "choose a Background", Doctor's companion, etc.
commander_cards = cards_by_section.get("Commander", [])
companion_cards = cards_by_section.get("Companion", []) + reference_cards_by_section.get("Reference: Companion", []) + reference_cards_by_section.get("Reference: companion", [])
commander_names = list(dict.fromkeys(commander_cards))
companion_names = list(dict.fromkeys(companion_cards))
commander_name_set = set(commander_names)
commander_name = " + ".join(commander_names) if commander_names else "Unknown_Commander"
safe_commander_name = make_safe_filename(commander_name)
commander_cards_scryfall = []
commander_cards_not_found = []
for name in commander_names:
    c = scryfall_lookup.get(name.lower())
    if c:
        commander_cards_scryfall.append(c)
    else:
        commander_cards_not_found.append(name)
commander_found = bool(commander_names) and not commander_cards_not_found
if commander_cards_scryfall:
    commander_type_line = " + ".join(f"{c.get('name','Unknown')}: {c.get('type_line','Unknown')}" for c in commander_cards_scryfall)
    order = ["W","U","B","R","G"]
    commander_color_identity = sorted(set().union(*(set(c.get("color_identity", [])) for c in commander_cards_scryfall)), key=lambda c: order.index(c) if c in order else 99)
    commander_color_identity_text = format_color_identity(commander_color_identity)
else:
    commander_type_line = "Unknown"
    commander_color_identity = []
    commander_color_identity_text = "Unknown"
commander_color_identity_set = set(commander_color_identity)
command_zone_rule_detected = detect_command_zone_rule(commander_cards_scryfall, companion_names)
companion_note = companion_legality_note(companion_names)

# Optional collection/card-pool loading for v0.6.1 replacement support
COLLECTION_FILE = find_collection_file()
collection_pool, collection_ignored_lines, collection_status_note = load_collection_card_pool(COLLECTION_FILE)

# Validation
cards_not_found = [name for name in unique_cards if name.lower() not in scryfall_lookup]

# Legality checks
color_identity_violations = []
manual_review_color_identity = []
for card_name, quantity in unique_cards.items():
    card = scryfall_lookup.get(card_name.lower())
    if not card:
        manual_review_color_identity.append(card_name)
        continue
    if card_name in commander_name_set:
        continue
    card_ci = set(card.get("color_identity", []))
    if not card_ci.issubset(commander_color_identity_set):
        color_identity_violations.append({
            "card_name": card_name, "quantity": quantity,
            "card_color_identity": format_color_identity(card_ci),
            "commander_color_identity": commander_color_identity_text,
        })

banned_cards = []
banned_commanders = []
manual_review_banned_cards = []
for card_name, quantity in unique_cards.items():
    card = scryfall_lookup.get(card_name.lower())
    if not card:
        manual_review_banned_cards.append(card_name)
        continue
    if card.get("legalities", {}).get("commander", "unknown") == "banned":
        entry = {"card_name": card_name, "quantity": quantity}
        if card_name in commander_name_set:
            banned_commanders.append(entry)
        else:
            banned_cards.append(entry)

allowed_duplicate_cards = []
illegal_duplicate_cards = []
manual_review_duplicate_cards = []
for card_name, quantity in unique_cards.items():
    if quantity <= 1:
        continue
    card = scryfall_lookup.get(card_name.lower())
    if not card:
        manual_review_duplicate_cards.append({"card_name": card_name, "quantity": quantity, "reason": "Card was not found in Scryfall, so duplicate legality needs manual review."})
        continue
    limit = get_duplicate_exception_limit(card)
    if is_basic_land(card):
        allowed_duplicate_cards.append({"card_name": card_name, "quantity": quantity, "reason": "Basic land duplicates are allowed in Commander."})
    elif limit == "unlimited":
        allowed_duplicate_cards.append({"card_name": card_name, "quantity": quantity, "reason": "Oracle text allows any number of cards with this name."})
    elif isinstance(limit, int):
        if quantity <= limit:
            allowed_duplicate_cards.append({"card_name": card_name, "quantity": quantity, "reason": f"Oracle text allows up to {limit} copies."})
        else:
            illegal_duplicate_cards.append({"card_name": card_name, "quantity": quantity, "reason": f"Oracle text allows up to {limit} copies, but this deck has {quantity}."})
    else:
        illegal_duplicate_cards.append({"card_name": card_name, "quantity": quantity, "reason": "Commander singleton rule allows only one copy unless an exception applies."})

# Math and role tags
nonland_mana_values = []
high_mana_value_cards = []
face_mana_value_notes = []
scryfall_creature_count = 0
scryfall_instant_sorcery_count = 0
scryfall_land_count = 0
scryfall_nonland_count = 0
card_type_tags_by_card = {}
card_role_tags_by_card = {}
type_tag_counts = Counter()
role_tag_counts = Counter()
for card_name, quantity in unique_cards.items():
    card = scryfall_lookup.get(card_name.lower())
    if not card:
        card_type_tags_by_card[card_name] = []
        card_role_tags_by_card[card_name] = ["manual_review"]
        role_tag_counts["manual_review"] += quantity
        continue
    type_line = card.get("type_line", "")
    representative_mv = get_representative_nonland_mana_value(card)
    face_summary = format_face_mana_summary(card)
    if has_type_on_any_face(card, "Land") and representative_mv is None:
        scryfall_land_count += quantity
    elif "Land" in type_line and not any(t in type_line for t in ["Creature","Artifact","Enchantment","Instant","Sorcery","Battle","Planeswalker"]):
        scryfall_land_count += quantity
    else:
        if has_type_on_any_face(card, "Land"):
            scryfall_land_count += quantity
        scryfall_nonland_count += quantity
        if representative_mv is not None:
            nonland_mana_values.extend([representative_mv] * quantity)
    if has_type_on_any_face(card, "Creature"):
        scryfall_creature_count += quantity
    if has_type_on_any_face(card, "Instant") or has_type_on_any_face(card, "Sorcery"):
        scryfall_instant_sorcery_count += quantity
    face_values = get_face_mana_values(card)
    if len(face_values) > 1:
        face_mana_value_notes.append(f"{card_name}: {face_summary}")
    if any(mv >= 6 for _, mv, _, _ in face_values):
        high_mana_value_cards.append((card_name, face_summary))
    type_tags = infer_card_type_tags(card)
    role_tags = infer_card_role_tags(card, commander_cards_scryfall)
    card_type_tags_by_card[card_name] = type_tags
    card_role_tags_by_card[card_name] = role_tags
    for tag in type_tags:
        type_tag_counts[tag] += quantity
    for tag in role_tags:
        role_tag_counts[tag] += quantity
average_nonland_mana_value = sum(nonland_mana_values) / len(nonland_mana_values) if nonland_mana_values else 0

# Mismatches
manual_creature_count = len(cards_by_section.get("Creatures", []))
manual_instant_sorcery_count = len(cards_by_section.get("Instants", [])) + len(cards_by_section.get("Sorceries", []))
type_mismatch_notes = []
if manual_creature_count != scryfall_creature_count:
    type_mismatch_notes.append("Creature count differs between your decklist sections and Scryfall type data.")
if manual_instant_sorcery_count != scryfall_instant_sorcery_count:
    type_mismatch_notes.append("Instant/Sorcery count differs between your decklist sections and Scryfall type data.")

type_mismatch_details = []
for card_name in unique_cards:
    card = scryfall_lookup.get(card_name.lower())
    if not card:
        continue
    type_line = card.get("type_line", "")
    scryfall_types = get_face_aware_major_types(card)
    for manual_section in card_manual_sections.get(card_name, set()):
        expected = MANUAL_SECTION_EXPECTED_TYPES.get(manual_section)
        if not expected:
            continue
        # Cards can have multiple types/faces. Only flag a true mismatch when the expected type is absent.
        if not expected.intersection(scryfall_types):
            type_mismatch_details.append({"card_name": card_name, "manual_section": manual_section, "type_line": type_line, "scryfall_types": sorted(scryfall_types)})

# Tribal support
creature_type_counts = Counter()
tribal_support_flags = []
for card_name, quantity in unique_cards.items():
    card = scryfall_lookup.get(card_name.lower())
    if not card:
        continue
    for ctype in get_creature_subtypes(card.get("type_line", "")):
        creature_type_counts[ctype] += quantity
for card_name, quantity in unique_cards.items():
    card = scryfall_lookup.get(card_name.lower())
    if not card:
        continue
    for dependency_type in get_tribal_dependency_types(get_full_oracle_text(card)):
        support_count = creature_type_counts.get(dependency_type, 0)
        if support_count < 5:
            tribal_support_flags.append({"card_name": card_name, "referenced_type": dependency_type, "support_count": support_count})

# Tag review and cut flags
possible_cut_flags = {}
manual_review_items = []
tag_based_review_notes = []
for card_name in cards_not_found:
    manual_review_items.append(f"{card_name}: Card was not found in Scryfall. Treat as manual review, not bad.")
for ignored in ignored_lines:
    manual_review_items.append(f"{ignored}: Decklist line was ignored during import.")

for card_name, quantity in unique_cards.items():
    tags = set(card_role_tags_by_card.get(card_name, []))
    card = scryfall_lookup.get(card_name.lower())

    # Command-zone cards can still receive role tags and review notes,
    # but they should not be treated as ordinary possible cuts.
    is_command_zone_card = card_name in commander_name_set

    if "manual_review" in tags:
        manual_review_items.append(f"{card_name}: Unknown/custom card or missing Scryfall data.")
        if not is_command_zone_card:
            possible_cut_flags[card_name] = "Manual review only. Unknown/custom cards are not automatically bad."
        continue
    if not card:
        continue
    type_line = card.get("type_line", "")
    representative_mv = get_representative_nonland_mana_value(card)
    useful_tags = tags - {"commander_synergy_possible", "combo_piece_possible"}
    if "Land" not in type_line and not useful_tags:
        if has_type_on_any_face(card, "Creature"):
            tag_based_review_notes.append(f"{card_name}: Creature with no functional role tags detected. Use card_attribute_rules.md to review tribe, keywords, stats, ETB/death/combat triggers, and commander fit before cutting.")
        else:
            tag_based_review_notes.append(f"{card_name}: No functional role tags detected. Review manually before making cuts.")
    if "tribal_dependency" in tags:
        for flag in tribal_support_flags:
            if flag["card_name"] == card_name:
                if not is_command_zone_card:
                    possible_cut_flags[card_name] = f"Has tribal_dependency but only {flag['support_count']} {flag['referenced_type']} creature(s) were detected."
                tag_based_review_notes.append(f"{card_name}: Has tribal_dependency. Review whether the deck supports the referenced tribe.")
    if representative_mv is not None and representative_mv >= 6 and "Land" not in type_line:
        payoff_tags = {"win_condition","board_wipe","mana_doubler","token_maker","card_draw","card_advantage","tutor","recursion","protection","commander_synergy_possible","combo_piece_possible","synergy_piece","tribal_payoff","extra_combat","combat_synergy","attack_trigger_payoff","damage_payoff","artifact_payoff"}
        if not tags.intersection(payoff_tags) and not is_command_zone_card:
            possible_cut_flags[card_name] = f"High mana value ({representative_mv}) with no clear payoff/protection/card-advantage/synergy tag detected."
    if {"recursion", "tribal_dependency"}.issubset(tags):
        tag_based_review_notes.append(f"{card_name}: Has recursion and tribal_dependency. Review as a synergy piece, not an automatic cut.")
    explanations = get_role_tag_explanations(tags)
    if explanations and tags.intersection({"sacrifice_outlet","death_trigger_payoff","token_maker","graveyard_enabler","discard_outlet","recursion","synergy_piece","tribal_payoff","extra_combat","combat_synergy","attack_trigger_payoff","damage_payoff","artifact_payoff"}):
        tag_based_review_notes.append(f"{card_name}: " + "; ".join(explanations) + ".")

attribute_rules_text = load_card_attribute_rules()
strategy_rules_text = load_strategy_archetype_rules()
cut_rules_text = load_cut_replacement_rules()
bracket_rules_text = load_bracket_rules()
game_changer_names = extract_game_changers_from_rules(bracket_rules_text)

# v0.5.7: Apply bracket/Game Changer tags before strategy and cut review.
for card_name in sorted(unique_cards):
    if normalize_text(card_name) in game_changer_names:
        existing_tags = set(card_role_tags_by_card.get(card_name, []))
        existing_tags.update({"game_changer", "bracket_pressure", "high_bracket_pressure"})
        card_role_tags_by_card[card_name] = sorted(existing_tags)
# v0.5.8 final readiness: repair creature-cheat/ETB-copy roles before final counts.
v06r_apply_role_repairs(unique_cards, scryfall_lookup, card_role_tags_by_card, commander_cards_scryfall)


# ==============================
# v0.6.2 Strategy Quality Gates + Completion Helpers
# ==============================
def v062_commander_text_contains(commander_cards, *needles):
    text = " ".join(normalize_text(get_full_oracle_text(c) + " " + c.get("type_line", "")) for c in commander_cards or [])
    return any(str(n).lower() in text for n in needles)


def v062_strategy_score_value(data):
    try:
        return int(data.get("score", 0) or 0)
    except Exception:
        return 0


def v062_suppress_strategy(scores, name, multiplier, reason):
    if name not in scores or not isinstance(scores.get(name), dict):
        return
    data = scores[name]
    old = v062_strategy_score_value(data)
    data["raw_score"] = data.get("raw_score", old)
    data["score"] = int(old * multiplier)
    data["adjusted_score"] = data["score"]
    data["gate_passed"] = False
    data["primary_eligible"] = False
    data["gate_failed_reason"] = reason
    data["suppression_reason"] = reason
    evidence = list(data.get("evidence", []) or [])
    evidence.append(reason)
    data["evidence"] = v057_clean_evidence(evidence)


def v062_boost_strategy(scores, name, floor_score, reason):
    if name not in scores or not isinstance(scores.get(name), dict):
        return
    data = scores[name]
    old = v062_strategy_score_value(data)
    data["score"] = max(old, int(floor_score))
    data["adjusted_score"] = data["score"]
    data["gate_passed"] = True
    data["primary_eligible"] = True
    evidence = list(data.get("evidence", []) or [])
    evidence.append(reason)
    data["evidence"] = v057_clean_evidence(evidence)


def get_mutate_density(role_counts):
    return (
        role_counts.get("mutate", 0) * 5
        + role_counts.get("mutate_payoff", 0) * 4
        + role_counts.get("mutate_enabler", 0) * 4
        + role_counts.get("creature_cast_trigger", 0) * 2
        + role_counts.get("creature_cost_reduction", 0) * 2
        + role_counts.get("creature_combo_value", 0)
        + role_counts.get("counter_synergy", 0)
        + role_counts.get("protection", 0)
    )


def get_nonhand_casting_density(role_counts):
    return (
        role_counts.get("cast_from_outside_hand", 0) * 5
        + role_counts.get("nonhand_casting", 0) * 5
        + role_counts.get("foretell", 0) * 4
        + role_counts.get("plot", 0) * 4
        + role_counts.get("suspend_synergy", 0) * 3
        + role_counts.get("cast_from_exile", 0) * 4
        + role_counts.get("adventure_synergy", 0) * 2
        + role_counts.get("alternate_cost_interaction", 0) * 2
        + role_counts.get("cost_cheat", 0) * 2
        + role_counts.get("free_casting", 0) * 2
        + role_counts.get("card_draw", 0)
    )


def v062_prev_infer_card_role_tags_wrapper(card, commander_cards=None):
    return _v062_prev_infer_card_role_tags(card, commander_cards)

# Add missing text-role detection without rewriting the whole tagger.
_v062_prev_infer_card_role_tags = infer_card_role_tags
def infer_card_role_tags(card, commander_cards=None):
    tags = set(_v062_prev_infer_card_role_tags(card, commander_cards))
    text = normalize_text(card.get("type_line", "") + "\n" + get_full_oracle_text(card))
    if "mutate" in text or "mutates" in text or "mutated" in text:
        tags.update(["mutate", "creature_cast_trigger", "creature_combo_value", "synergy_piece"])
        if any(p in text for p in ["whenever this creature mutates", "whenever this creature mutates," , "when this creature mutates"]):
            tags.add("mutate_payoff")
        if any(p in text for p in ["costs {1} less to mutate", "mutate cost", "mutate ability", "non-human creature"]):
            tags.add("mutate_enabler")
    if any(p in text for p in ["cast a spell from anywhere other than your hand", "cast a spell from exile", "cast from exile", "cast it from exile", "you may cast", "you may play"]):
        if any(p in text for p in ["exile", "graveyard", "top of your library", "foretell", "plot", "suspend", "adventure"]):
            tags.update(["cast_from_outside_hand", "nonhand_casting", "card_advantage"])
    if "foretell" in text:
        tags.update(["foretell", "cast_from_outside_hand", "nonhand_casting", "alternate_cost_interaction"])
    if "plot" in text:
        tags.update(["plot", "cast_from_outside_hand", "nonhand_casting", "alternate_cost_interaction"])
    return sorted(tags)

# Add two commander-defined strategy buckets without disturbing older definitions.
ARCHETYPE_DEFINITIONS.setdefault("Mutate / Creature Stack Value", {
    "anchor_tags": {"mutate", "mutate_payoff", "mutate_enabler"},
    "core_tags": {
        "mutate": 10,
        "mutate_payoff": 8,
        "mutate_enabler": 7,
        "creature_cast_trigger": 4,
        "creature_cost_reduction": 4,
        "creature_combo_value": 3,
        "counter_synergy": 2,
        "protection": 2,
        "card_draw": 1,
        "targeted_removal": 1,
    },
    "type_tags": {"creature": 1},
    "engine": "The deck stacks mutate creatures onto protected bodies, using creature-cast/cost-reduction support and mutate triggers to generate value while growing one or more threats.",
    "finishers": "Large mutated threat stacks, repeated mutate triggers, evasive or protected commander damage, and creature-value snowball turns.",
})

ARCHETYPE_DEFINITIONS.setdefault("Cast From Outside Hand Value", {
    "anchor_tags": {"cast_from_outside_hand", "nonhand_casting", "foretell", "plot", "suspend_synergy", "adventure_synergy"},
    "core_tags": {
        "cast_from_outside_hand": 10,
        "nonhand_casting": 9,
        "foretell": 7,
        "plot": 7,
        "suspend_synergy": 6,
        "adventure_synergy": 5,
        "alternate_cost_interaction": 4,
        "cost_cheat": 3,
        "free_casting": 3,
        "card_draw": 2,
        "card_advantage": 2,
        "counterspell": 1,
        "targeted_removal": 1,
    },
    "engine": "The deck casts spells from exile, foretell, suspend, plot, Adventure, graveyard, or the top of the library to trigger commander/value payoffs and maintain card flow.",
    "finishers": "Repeated non-hand casting value, free/discounted spell chains, protected value engines, and payoff creatures that reward unusual casting zones.",
})

_v062_prev_score_archetypes = score_archetypes
def score_archetypes(role_counts, type_counts, commander_cards):
    scores = _v062_prev_score_archetypes(role_counts, type_counts, commander_cards)
    commander_tags = get_commander_role_tag_counter(commander_cards)

    # Mutate should be visible for Animar shells or mutate-heavy piles, but stay color-safe at recommendation time.
    mutate_density = get_mutate_density(role_counts)
    if "Mutate / Creature Stack Value" in scores:
        if mutate_density >= 24 or (role_counts.get("mutate", 0) >= 6 and commander_has_any_tag(commander_tags, {"creature_cost_reduction", "creature_cast_trigger", "creature_combo_value", "counter_synergy"})):
            floor = max(scores.get("Creature Cost-Reduction / Creature Combo Value", {}).get("score", 0), scores["Mutate / Creature Stack Value"].get("score", 0)) + 10
            v062_boost_strategy(scores, "Mutate / Creature Stack Value", floor, "v0.6.2: mutate density/Animar-style creature-cost support makes Mutate a real deck-plan candidate.")
        elif role_counts.get("mutate", 0) < 4:
            v062_suppress_strategy(scores, "Mutate / Creature Stack Value", 0.40, "Failed mutate gate: not enough mutate density for primary strategy.")

    # Vega-style non-hand casting should not collapse into broad Ramp-Control when commander text supports it.
    nonhand_density = get_nonhand_casting_density(role_counts)
    if "Cast From Outside Hand Value" in scores:
        commander_nonhand = v062_commander_text_contains(commander_cards, "anywhere other than your hand", "from exile", "foretell", "suspend", "plot")
        if commander_nonhand and nonhand_density >= 18:
            floor = max(scores.get("Ramp-Control / Big Mana Value", {}).get("score", 0), scores.get("Legends Matter / Legendary Cascade", {}).get("score", 0)) + 12
            v062_boost_strategy(scores, "Cast From Outside Hand Value", floor, "v0.6.2: commander non-hand casting text and support density beat broad ramp/control or legends fallback.")
        elif nonhand_density < 12:
            v062_suppress_strategy(scores, "Cast From Outside Hand Value", 0.45, "Failed non-hand casting gate: not enough outside-hand casting density.")

    # Tighten blink overfires: one flicker card plus ETB value is not a primary strategy.
    blink_real = role_counts.get("blink_flicker", 0) + role_counts.get("exile_return", 0) + role_counts.get("mass_blink", 0)
    commander_blink = v062_commander_text_contains(commander_cards, "exile", "return it to the battlefield", "return those cards to the battlefield")
    if blink_real < 3 and not commander_blink:
        v062_suppress_strategy(scores, "Blink/Flicker / ETB Value", 0.35, "Failed blink/flicker gate: primary blink needs commander blink text or at least three real blink/exile-return effects.")

    # Tighten Voltron: equipment/aura count alone is not enough without commander combat/damage/go-tall context.
    voltron_cards = role_counts.get("equipment_synergy", 0) + role_counts.get("aura_synergy", 0) + role_counts.get("equipment_payoff", 0) + role_counts.get("aura_payoff", 0)
    commander_combat = commander_has_any_tag(commander_tags, {"attack_trigger_payoff", "combat_synergy", "commander_damage_support", "voltron_protection", "go_tall_support", "extra_combat"})
    deck_combat_payoffs = role_counts.get("commander_damage_support", 0) + role_counts.get("combat_damage_trigger", 0) + role_counts.get("voltron_protection", 0) + role_counts.get("extra_combat", 0)
    if not commander_combat and not (voltron_cards >= 8 and deck_combat_payoffs >= 5):
        for name in ["Voltron", "Equipment / Aura Voltron"]:
            v062_suppress_strategy(scores, name, 0.40, "Failed Voltron gate: equipment/aura or go-tall tags are not enough without commander combat/damage context or dense Voltron payoff support.")

    # Tighten Legends: a legendary commander is not a Legends Matter deck.
    legends_density = get_legends_cascade_density(role_counts)
    commander_legends_payoff = v062_commander_text_contains(commander_cards, "legendary spell", "legendary spells", "legendary permanent", "legendary permanents", "historic", "lesser mana value")
    if not commander_legends_payoff and role_counts.get("legendary_synergy", 0) < 16 and role_counts.get("legendary_cascade", 0) == 0:
        for name in ["Legends Matter / Legendary Cascade", "Historic / Legends Matter"]:
            v062_suppress_strategy(scores, name, 0.35, "Failed Legends Matter gate: legendary commander/incidental legendary bodies are not enough without deckwide legendary payoff density.")
    elif commander_legends_payoff and legends_density >= 55:
        v062_boost_strategy(scores, "Legends Matter / Legendary Cascade", scores.get("Legends Matter / Legendary Cascade", {}).get("score", 0), "v0.6.2: commander has real legends/historic/cascade payoff text.")

    # Urza-style artifact tap/mana engine should outrank generic Voltron/combat when artifacts are the real engine.
    commander_artifact_tap = v062_commander_text_contains(commander_cards, "artifact creatures", "untapped artifact", "tap an untapped artifact", "add {u}", "artifacts you control")
    artifact_engine_density = role_counts.get("artifact_payoff", 0) + role_counts.get("artifact_token_synergy", 0) + role_counts.get("mana_engine_support", 0) + role_counts.get("tap_ability_engine", 0) + role_counts.get("mana_rock", 0)
    if commander_artifact_tap and artifact_engine_density >= 18:
        best_broad = max(scores.get("Equipment / Aura Voltron", {}).get("score", 0), scores.get("Voltron", {}).get("score", 0), scores.get("Artifact Combat", {}).get("score", 0))
        v062_boost_strategy(scores, "Artifact Engine / Artifact Tap / Artifact Mana", best_broad + 18, "v0.6.2: commander artifact/tap/mana text and artifact density beat generic Voltron/combat labels.")
        for name in ["Equipment / Aura Voltron", "Voltron"]:
            if name in scores:
                scores[name]["score"] = int(scores[name].get("score", 0) * 0.55)
                scores[name]["adjusted_score"] = scores[name]["score"]
                scores[name].setdefault("evidence", []).append("v0.6.2: moved behind commander artifact/tap/mana engine.")

    # Tiamat close-call handling: Tiamat/Dragonstorm should not be displaced by artifact/Treasure chain on a tiny margin.
    if commander_has_dragon_tutor_v057(commander_cards) and "Dragonstorm / Tiamat Tutor Chain" in scores and "Artifact/Treasure Tutor Chain" in scores:
        dragon_score = scores["Dragonstorm / Tiamat Tutor Chain"].get("score", 0)
        treasure_score = scores["Artifact/Treasure Tutor Chain"].get("score", 0)
        if treasure_score >= dragon_score and treasure_score <= max(1, dragon_score) * 1.10:
            v062_boost_strategy(scores, "Dragonstorm / Tiamat Tutor Chain", treasure_score + 12, "v0.6.2: Tiamat commander close-call correction; Dragon/Tiamat tutor-chain remains primary unless artifact/Treasure package clearly exceeds it.")

    return scores

_v062_prev_get_strategy_confidence_warning = get_strategy_confidence_warning
def get_strategy_confidence_warning(primary_strategy, secondary_strategy, primary_data, secondary_data, role_counts):
    warnings = list(_v062_prev_get_strategy_confidence_warning(primary_strategy, secondary_strategy, primary_data, secondary_data, role_counts))
    primary_score = int(primary_data.get("score", 0) or 0) if isinstance(primary_data, dict) else 0
    secondary_score = int(secondary_data.get("score", 0) or 0) if isinstance(secondary_data, dict) else 0
    if primary_score and secondary_score and secondary_score >= primary_score * 0.90:
        warnings.append("Primary and secondary strategy scores are within 10%; treat this as a pilot-confirmation point before making aggressive cuts or additions.")
    if primary_strategy == "Mutate / Creature Stack Value" and role_counts.get("mutate", 0) < 6:
        warnings.append("Mutate is being considered with modest density; confirm whether mutate is the intended main plan before filling many slots.")
    if primary_strategy == "Cast From Outside Hand Value" and get_nonhand_casting_density(role_counts) < 24:
        warnings.append("Outside-hand casting support is present but may need more density before it can carry the deck alone.")
    # Only show Toggo-style warning when the commander actually has that package.
    if get_commander_landfall_package_density(role_counts) >= 24 and not role_counts.get("commander_created_package", 0):
        warnings = [w for w in warnings if "Commander-created landfall/artifact-token package" not in w]
    return list(dict.fromkeys(warnings))


# Rebuild role counts after adding bracket tags and readiness role repairs.
role_tag_counts = v06r_rebuild_role_counts(card_role_tags_by_card, unique_cards)

# v0.4 Strategy and synergy analysis
archetype_scores = score_archetypes(role_tag_counts, type_tag_counts, commander_cards_scryfall)
archetype_scores = apply_strategy_priority_corrections(archetype_scores, role_tag_counts, commander_cards_scryfall)
archetype_scores = finalize_archetype_scores_v057v4(archetype_scores, role_tag_counts, commander_cards_scryfall)
archetype_scores = v06r_apply_strategy_readiness_patch(archetype_scores, role_tag_counts, commander_cards_scryfall)
primary_strategy, primary_strategy_data, secondary_strategy, secondary_strategy_data, ordered_archetypes = choose_primary_secondary_strategy(archetype_scores)
commander_game_plan = get_commander_game_plan(commander_cards_scryfall, primary_strategy, secondary_strategy)
core_synergy_packages = get_core_synergy_packages(role_tag_counts)
card_plan_fit_buckets = build_card_plan_fit(
    unique_cards,
    scryfall_lookup,
    card_role_tags_by_card,
    commander_name_set,
    primary_strategy,
    secondary_strategy,
    commander_cards_scryfall,
)
commander_support_level = get_commander_support_level(card_plan_fit_buckets=card_plan_fit_buckets)
commander_support_reason = get_commander_support_reason(card_plan_fit_buckets)
strategy_confidence_warnings = get_strategy_confidence_warning(primary_strategy, secondary_strategy, primary_strategy_data, secondary_strategy_data, role_tag_counts)
strong_synergy_cards = pick_strong_synergy_cards(card_plan_fit_buckets)
possible_off_plan_cards = pick_possible_off_plan_cards(card_plan_fit_buckets)
bracket_read = estimate_bracket_read(unique_cards, card_role_tags_by_card, primary_strategy, secondary_strategy, role_tag_counts, game_changer_names, INTENDED_BRACKET)
cut_pressure_review = build_cut_pressure_review(
    cards,
    unique_cards,
    scryfall_lookup,
    card_role_tags_by_card,
    card_plan_fit_buckets,
    commander_name_set,
    primary_strategy,
    secondary_strategy,
    role_tag_counts,
    tribal_support_flags,
    average_nonland_mana_value,
    CUT_STRICTNESS,
)
cut_pressure_review = v06r_apply_legality_first_required_cuts(cut_pressure_review, illegal_duplicate_cards, card_role_tags_by_card)
possible_cut_review = build_possible_cut_review(
    cut_pressure_review,
    unique_cards,
    scryfall_lookup,
    card_role_tags_by_card,
    card_plan_fit_buckets,
    primary_strategy,
    secondary_strategy,
    role_tag_counts,
    scryfall_land_count,
    average_nonland_mana_value,
    bracket_read,
)


def normalize_possible_cut_review_v057v5(review):
    """Final v0.5.8 cut-bucket normalization.

    Goals:
    - every card appears in exactly one final cut-output bucket unless moved to Conflict / Manual Review
    - actual cut count equals final Recommended + Possible lists
    - replacement need signals come from the final printable candidates when possible
    """
    if not isinstance(review, dict):
        return review

    list_keys = [
        "recommended_cuts", "possible_cuts", "playtest_before_cutting",
        "conflict_manual_review", "protected_from_cut", "manual_review_cuts",
        "refined_deck_review_candidates", "deck_needs", "diagnostic_warnings",
    ]
    for key in list_keys:
        value = review.get(key)
        if value is None:
            review[key] = []
        elif not isinstance(value, list):
            review[key] = [value]

    def entry_name(entry):
        if isinstance(entry, dict):
            return str(entry.get("card_name", "") or "").strip()
        return str(entry or "").strip()

    def dedupe_entries(entries):
        seen = set()
        result = []
        for entry in entries or []:
            name = entry_name(entry)
            key = name.lower()
            if not name or key in seen:
                continue
            seen.add(key)
            result.append(entry)
        return result

    for key in ["recommended_cuts", "possible_cuts", "playtest_before_cutting", "conflict_manual_review", "protected_from_cut", "manual_review_cuts", "refined_deck_review_candidates"]:
        review[key] = dedupe_entries(review.get(key, []))

    protected_names = {entry_name(e).lower() for e in review.get("protected_from_cut", []) if entry_name(e)}
    conflict_names = {entry_name(e).lower() for e in review.get("conflict_manual_review", []) if entry_name(e)}

    # A protected card that also appears as a cut becomes Conflict / Manual Review, not both.
    conflict_additions = []
    for key in ["recommended_cuts", "possible_cuts"]:
        kept = []
        for entry in review.get(key, []):
            name = entry_name(entry)
            lname = name.lower()
            if lname in protected_names and lname not in conflict_names:
                conflict_additions.append({
                    "card_name": name,
                    "cut_pressure": entry.get("reason", "Cut review found replaceability pressure."),
                    "protection_pressure": "Protected/core-card signal also found.",
                    "why_cuttable": entry.get("reason", "Replaceability scoring found cut pressure."),
                    "why_belongs": "The card appeared in Protected From Cut, so it should not be presented as a normal cut.",
                    "how_to_decide": "Review manually; only cut if the protection reason is no longer true for the pilot's intended plan.",
                    "current_recommendation": "Conflict / Manual Review — do not cut automatically.",
                })
                conflict_names.add(lname)
                continue
            if lname in conflict_names:
                continue
            kept.append(entry)
        review[key] = kept
    if conflict_additions:
        review["conflict_manual_review"] = dedupe_entries(review.get("conflict_manual_review", []) + conflict_additions)

    # Enforce single final bucket priority.
    final_seen = set()
    for key in ["recommended_cuts", "possible_cuts", "playtest_before_cutting", "manual_review_cuts", "refined_deck_review_candidates"]:
        kept = []
        for entry in review.get(key, []):
            name = entry_name(entry)
            lname = name.lower()
            if not name or lname in final_seen or lname in conflict_names or lname in protected_names:
                continue
            final_seen.add(lname)
            kept.append(entry)
        review[key] = kept

    # Protected list should also be unique and should not duplicate conflicts.
    review["protected_from_cut"] = [e for e in review.get("protected_from_cut", []) if entry_name(e).lower() not in conflict_names]

    actual = len(review.get("recommended_cuts", [])) + len(review.get("possible_cuts", []))
    review["actual_responsible_cut_candidates_found"] = actual
    review["actual_responsible_cut_candidates"] = actual

    try:
        target = int(CUT_DEPTH_CONFIG.get("optional_cut_target", review.get("optional_cut_target", 5)) or 5)
    except Exception:
        target = 5
    mode = str(CUT_DEPTH_CONFIG.get("mode", review.get("cut_depth_mode", "normal")) or "normal")
    if actual < target:
        review["target_shortfall_note"] = (
            f"Only {actual} responsible optional/recommended cut candidates were found, even though {mode} mode requested {target}. "
            "The remaining cards were role-important, commander-relevant, protected by interaction/ramp/draw role balance, "
            "or require pilot input before cutting."
        )
    else:
        review.pop("target_shortfall_note", None)

    # Make the high-level replacement signal specific by using the final printed candidates first.
    specific_needs = []
    for entry in (review.get("recommended_cuts", []) + review.get("possible_cuts", [])):
        for category in entry.get("replacement_categories", []) if isinstance(entry, dict) else []:
            if category and category not in specific_needs:
                specific_needs.append(category)
    if not specific_needs:
        strategy_text = f"{globals().get('primary_strategy', '')} {globals().get('secondary_strategy', '')}".lower()
        if "adventure" in strategy_text or "modal" in strategy_text:
            specific_needs.extend(["More adventure/modal support", "More primary-plan enablers", "More primary-plan payoffs"])
        elif "token resource" in strategy_text:
            specific_needs.extend(["More token production", "More commander-specific enablers", "More engine density"])
        elif "topdeck" in strategy_text or "permanent-type" in strategy_text:
            specific_needs.extend(["More topdeck manipulation", "More permanent-type value", "More primary-plan enablers"])
        elif "activated" in strategy_text or "power-reduction" in strategy_text:
            specific_needs.extend(["More activated ability support", "More mana sinks", "More commander-specific enablers"])
        elif "pod" in strategy_text or "toolbox" in strategy_text or "creature cost" in strategy_text:
            specific_needs.extend(["More pod-chain support", "More creature density", "More creature-based interaction"])
    generic_only = {"More commander synergy", "More primary-plan support", "More secondary strategy support"}
    if specific_needs:
        merged = []
        for item in specific_needs + [n for n in review.get("deck_needs", []) if n not in generic_only]:
            if item and item not in merged:
                merged.append(item)
        review["deck_needs"] = merged[:6]

    review["diagnostic_warnings"] = list(dict.fromkeys(review.get("diagnostic_warnings", [])))
    return review

possible_cut_review = normalize_possible_cut_review_v057v5(possible_cut_review)

collection_replacement_review = build_collection_replacement_candidates(
    collection_pool,
    collection_ignored_lines,
    scryfall_lookup,
    unique_cards,
    commander_color_identity_set,
    possible_cut_review.get("deck_needs", []),
    primary_strategy,
    secondary_strategy,
)


def v062_card_pool_candidate_score(card, tags, need_tags, strategy_tags, current_land_count, deck_size):
    score = 0
    matched = set()
    for tag in tags.intersection(strategy_tags):
        score += 4
        matched.add(tag)
    for tag in tags.intersection(need_tags):
        score += 3
        matched.add(tag)
    for tag in tags.intersection({"ramp", "card_draw", "card_advantage", "targeted_removal", "counterspell", "protection", "mana_fixing"}):
        score += 2
        matched.add(tag)
    if "mutate" in strategy_tags and "mutate" in tags:
        score += 8
        matched.add("mutate")
    if "creature_cost_reduction" in strategy_tags and tags.intersection({"creature_cast_trigger", "creature_combo_value", "creature_cost_reduction", "mutate"}):
        score += 4
    mv = get_representative_nonland_mana_value(card)
    if mv is not None:
        if mv <= 2:
            score += 2
        elif mv <= 4:
            score += 1
        elif mv >= 7 and "high_mv_payoff" not in tags and "big_mana_payoff" not in tags:
            score -= 2
    if "land" in infer_card_type_tags(card) and current_land_count < 36:
        score += 2
    return score, sorted(matched)


def build_deck_completion_review(collection_pool, scryfall_lookup, unique_cards, commander_color_identity_set, deck_needs, primary_strategy, secondary_strategy, cards, scryfall_land_count):
    needed = max(0, 100 - len(cards))
    result = {
        "enabled": needed > 0,
        "cards_needed": needed,
        "status": "Deck is already at or above 100 cards; deck-completion mode is not needed.",
        "addition_priorities": [],
        "collection_candidates": [],
        "full_pool_candidates": [],
        "warnings": [],
    }
    if needed <= 0:
        return result

    result["status"] = f"Deck is underfilled by {needed} card(s). Treat this as build/addition work before normal cutting unless the pilot explicitly wants a rebuild."
    primary_tags, secondary_tags = get_primary_secondary_tag_sets(primary_strategy, secondary_strategy)
    strategy_tags = set(primary_tags) | set(secondary_tags)
    if "Mutate" in primary_strategy or role_tag_counts.get("mutate", 0) >= 6:
        strategy_tags.update({"mutate", "mutate_payoff", "mutate_enabler", "creature_cast_trigger", "creature_cost_reduction", "protection"})
    if "Cast From Outside Hand" in primary_strategy or primary_strategy == "Cast From Outside Hand Value":
        strategy_tags.update({"cast_from_outside_hand", "nonhand_casting", "foretell", "plot", "suspend_synergy", "adventure_synergy"})

    priorities = []
    if scryfall_land_count < 34 and needed > 0:
        priorities.append("Add lands/fixing until the mana base is functional.")
    if role_tag_counts.get("ramp", 0) < 10:
        priorities.append("Add ramp or cost-reduction so the deck can deploy its plan on time.")
    if role_tag_counts.get("card_draw", 0) + role_tag_counts.get("card_advantage", 0) < 10:
        priorities.append("Add card draw or card-advantage engines so the incomplete shell does not run out of gas.")
    if role_tag_counts.get("targeted_removal", 0) + role_tag_counts.get("counterspell", 0) < 8:
        priorities.append("Add interaction that fits the colors and does not dilute the primary plan.")
    if strategy_tags:
        priorities.append(f"Add cards that reinforce the confirmed/provisional primary plan: {primary_strategy}.")
    if role_tag_counts.get("mutate", 0) >= 6:
        priorities.append("For the Animar/mutate shell, prioritize Temur-color mutate creatures, cheap non-Human bodies, creature-cost support, protection, and creature-based card advantage.")
    result["addition_priorities"] = priorities[:8]

    need_tags = set()
    for need in deck_needs:
        need_tags.update(replacement_category_to_tags(need))
    if not need_tags:
        need_tags.update({"ramp", "card_draw", "card_advantage", "targeted_removal", "protection"})

    # Collection candidates: already quantity-aware and color-filtered; rescore for deck completion.
    collection_scored = []
    for card_name, owned_qty in (collection_pool or {}).items():
        card = scryfall_lookup.get(str(card_name).lower())
        if not card or not card_is_legal_for_commander_color(card, commander_color_identity_set):
            continue
        deck_qty = unique_cards.get(card_name, 0)
        available_qty = owned_qty - deck_qty
        if available_qty <= 0:
            continue
        tags = set(infer_card_role_tags(card, commander_cards_scryfall))
        score, matched = v062_card_pool_candidate_score(card, tags, need_tags, strategy_tags, scryfall_land_count, len(cards))
        if score <= 0:
            continue
        collection_scored.append({
            "card_name": card.get("name", card_name),
            "score": score,
            "available_qty": available_qty,
            "owned_qty": owned_qty,
            "mana_value": get_representative_nonland_mana_value(card),
            "matched_roles": matched[:10],
            "source": "collection",
        })
    collection_scored.sort(key=lambda x: (x["score"], -(x.get("mana_value") or 99)), reverse=True)
    result["collection_candidates"] = collection_scored[:max(20, min(60, needed * 2))]

    # Full database candidates: color-identity legal and not already in deck. Kept capped for readability.
    full_scored = []
    seen_names = get_existing_deck_name_keys(unique_cards)
    for card in scryfall_lookup.values():
        name = card.get("name", "")
        if not name or normalize_card_name_key(name) in seen_names or card_already_in_deck(card, unique_cards):
            continue
        if card.get("layout") in {"token", "emblem", "art_series"}:
            continue
        if not card_is_legal_for_commander_color(card, commander_color_identity_set):
            continue
        if card.get("legalities", {}).get("commander") == "banned":
            continue
        tags = set(infer_card_role_tags(card, commander_cards_scryfall))
        score, matched = v062_card_pool_candidate_score(card, tags, need_tags, strategy_tags, scryfall_land_count, len(cards))
        if score <= 2:
            continue
        full_scored.append({
            "card_name": name,
            "score": score,
            "mana_value": get_representative_nonland_mana_value(card),
            "matched_roles": matched[:10],
            "source": "full card pool",
        })
    full_scored.sort(key=lambda x: (x["score"], -(x.get("mana_value") or 99)), reverse=True)
    result["full_pool_candidates"] = full_scored[:max(25, min(80, needed * 2))]

    if not commander_color_identity_set and commander_color_identity_text != "Colorless":
        result["warnings"].append("Commander color identity could not be verified; exact completion suggestions may need manual color review.")
    else:
        result["warnings"].append(f"All listed exact completion candidates were filtered to commander color identity: {commander_color_identity_text}.")
    return result


deck_completion_review = build_deck_completion_review(
    collection_pool,
    scryfall_lookup,
    unique_cards,
    commander_color_identity_set,
    possible_cut_review.get("deck_needs", []),
    primary_strategy,
    secondary_strategy,
    cards,
    scryfall_land_count,
)



# Report
report_lines = []
report_lines.append("Commander Deck Report")
report_lines.append("=" * 30)
report_lines.append("Version: v0.6.2.6 — Worksheet Guardrail Hotfix")
report_lines.append("Build: v0.6.2.6 adds worksheet guardrails: dynamic deck-size/addition-count rules, answer fields, and final validation checks for limited/free AI use. It preserves the v0.6.2.4 stable interactive behavior.")
report_lines.append(f"Review Direction: {REVIEW_DIRECTION}")
report_lines.append(f"Prompt Interaction Mode: {PROMPT_INTERACTION_MODE_DISPLAY.get(PROMPT_INTERACTION_MODE, PROMPT_INTERACTION_MODE)}")
if REVIEW_DIRECTION == "build_up":
    report_lines.append(f"Build-Up Mode: {BUILD_UP_CONFIG.get('label', 'Not applicable')}")
else:
    report_lines.append(f"Cut-Down Mode: {CUT_DEPTH_CONFIG.get('mode', 'normal')}")

add_section(report_lines, "1. Deck Import Summary")
report_lines.append(f"Deck file analyzed: {DECK_FILE}")
report_lines.append(f"Cards found: {len(cards)}")
report_lines.append(f"Unique cards found: {len(unique_cards)}")
report_lines.append(f"Reference/non-mainboard cards ignored: {len(reference_cards)}")
report_lines.append(f"Card attribute rules file: {ATTRIBUTE_RULES_FILE}")
report_lines.append(f"Strategy archetype rules file: {STRATEGY_RULES_FILE}")
report_lines.append(f"Cut/replacement rules file: {CUT_RULES_FILE}")
report_lines.append(f"Bracket rules file: {BRACKET_RULES_FILE}")
report_lines.append(f"Collection/card-pool file: {COLLECTION_FILE if COLLECTION_FILE else 'None loaded'}")
report_lines.append(f"Collection/card-pool status: {collection_status_note}")
if len(cards) == 100:
    report_lines.append("Commander deck size: 100 cards")
elif len(cards) < 100:
    report_lines.append(f"Commander deck size warning: short by {100 - len(cards)} card(s)")
else:
    report_lines.append(f"Commander deck size warning: over by {len(cards) - 100} card(s)")
report_lines.append("Ignored decklist lines: None" if not ignored_lines else "Ignored decklist lines:")
for ignored in ignored_lines:
    report_lines.append(f"- {ignored}")

add_section(report_lines, "1B. Input Hygiene")
report_lines.append(f"Mainboard cards counted: {len(cards)}")
report_lines.append(f"Reference/non-mainboard cards ignored: {len(reference_cards)}")
if ignored_sections:
    report_lines.append("Ignored/reference sections:")
    for section, count in sorted(ignored_sections.items()):
        if count:
            report_lines.append(f"- {section}: {count}")
else:
    report_lines.append("Ignored/reference sections: None detected")
if len(reference_cards) > 0:
    report_lines.append("Parser warning: reference/non-mainboard cards were excluded from deck size, legality, strategy scoring, and cut pressure.")
    report_lines.append("Tokens-section note: v0.5.8 counts real Scryfall cards in Tokens categories as mainboard and only ignores likely token/helper entries.")
else:
    report_lines.append("Parser warnings: None")

add_section(report_lines, "2. Commander Identification")
report_lines.append(f"Commander card(s): {commander_name}")
report_lines.append(f"Command zone rule detected: {command_zone_rule_detected}")
report_lines.append(f"Companion status: {companion_note}")
report_lines.append(f"Command zone cards found in Scryfall: {'Yes' if commander_found else 'No'}")
if commander_cards_not_found:
    report_lines.append("Commander cards not found in Scryfall:")
    for missing in commander_cards_not_found:
        report_lines.append(f"- {missing}")
report_lines.append(f"Type Line(s): {commander_type_line}")
report_lines.append(f"Combined Color Identity: {commander_color_identity_text}")

add_section(report_lines, "3. Card Validation")
report_lines.append(f"Cards checked: {len(cards)}")
report_lines.append(f"Unique cards checked: {len(unique_cards)}")
if not cards_not_found:
    report_lines.append("All cards were found in Scryfall.")
else:
    report_lines.append("Cards not found in Scryfall:")
    for card_name in cards_not_found:
        report_lines.append(f"- {card_name}")

add_section(report_lines, "4. Commander Legality Check")
report_lines.append("Deck Size: Legal" if len(cards) == 100 else f"Deck Size: Not legal for Commander ({len(cards)} cards found; expected 100).")
if not commander_found:
    report_lines.append("Color Identity: Manual review needed because one or more command zone cards were not found in Scryfall.")
elif not color_identity_violations:
    report_lines.append("Color Identity: Legal")
else:
    report_lines.append("Color Identity: Issues found")
    report_lines.append("Cards outside combined commander color identity:")
    for v in color_identity_violations:
        report_lines.append(f"- {v['card_name']} ({v['card_color_identity']}) is outside commander identity ({v['commander_color_identity']})")
if manual_review_color_identity:
    report_lines.append("Color Identity Manual Review:")
    for card_name in manual_review_color_identity:
        report_lines.append(f"- {card_name}: could not verify color identity.")
report_lines.append("Banned Cards: None found" if not banned_cards and not banned_commanders else "Banned Cards: Issues found")
if banned_commanders:
    report_lines.append("Banned Commander / Command Zone Card:")
    for b in banned_commanders:
        report_lines.append(f"- {b['card_name']}")
if banned_cards:
    report_lines.append("Banned Cards in Deck:")
    for b in banned_cards:
        report_lines.append(f"- {b['card_name']}")
if manual_review_banned_cards:
    report_lines.append("Banned Cards Manual Review:")
    for card_name in manual_review_banned_cards:
        report_lines.append(f"- {card_name}: could not verify Commander legality.")
report_lines.append("Singleton / Duplicate Check: Legal" if not illegal_duplicate_cards and not manual_review_duplicate_cards else "Singleton / Duplicate Check: Issues found")
if allowed_duplicate_cards:
    report_lines.append("Allowed Duplicates:")
    for d in allowed_duplicate_cards:
        report_lines.append(f"- {d['card_name']}: {d['quantity']} copies. {d['reason']}")
if illegal_duplicate_cards:
    report_lines.append("Illegal Duplicates:")
    for d in illegal_duplicate_cards:
        report_lines.append(f"- {d['card_name']}: {d['quantity']} copies. {d['reason']}")
if manual_review_duplicate_cards:
    report_lines.append("Duplicate Manual Review:")
    for d in manual_review_duplicate_cards:
        report_lines.append(f"- {d['card_name']}: {d['quantity']} copies. {d['reason']}")

add_section(report_lines, "5. Deck Math")
report_lines.append(f"Total Cards: {len(cards)}")
report_lines.append(f"Unique Cards: {len(unique_cards)}")
report_lines.append(f"Scryfall Land Count: {scryfall_land_count}")
report_lines.append(f"Scryfall Nonland Count: {scryfall_nonland_count}")
report_lines.append(f"Average Nonland Mana Value: {average_nonland_mana_value:.2f}")
report_lines.append("Average Nonland Mana Value is face-aware: split/adventure/MDFC-style cards use parsed face mana_cost where available, then face CMC, then whole-card CMC fallback.")
report_lines.append(f"Scryfall Creature Count: {scryfall_creature_count}")
report_lines.append(f"Face-Inclusive Scryfall Instant/Sorcery Count: {scryfall_instant_sorcery_count}")

add_section(report_lines, "6. Card Type Breakdown")
report_lines.append("Manual Category Counts:")
shown_sections = set()

for section in SECTION_ORDER:
    section_cards = cards_by_section.get(section, [])
    if section_cards:
        report_lines.append(f"- {section}: {len(section_cards)}")
        shown_sections.add(section)

custom_sections = [
    section for section in cards_by_section
    if section not in shown_sections and section != "Unknown / Needs Review"
]

if custom_sections:
    report_lines.append("")
    report_lines.append("Custom / Player-Defined Category Counts:")
    for section in sorted(custom_sections):
        report_lines.append(f"- {section}: {len(cards_by_section[section])}")
report_lines.append("")
report_lines.append("Scryfall Type Counts:")
if type_tag_counts:
    for tag, count in type_tag_counts.most_common():
        report_lines.append(f"- {tag}: {count}")
else:
    report_lines.append("- No Scryfall-inferred card types found.")

add_section(report_lines, "7. High Mana Value Cards")
if high_mana_value_cards:
    for card_name, summary in high_mana_value_cards:
        report_lines.append(f"- {card_name}: {summary}")
else:
    report_lines.append("No high mana value nonland faces found.")
if face_mana_value_notes:
    report_lines.append("")
    report_lines.append("Face-Aware Mana Value Notes:")
    for note in face_mana_value_notes:
        report_lines.append(f"- {note}")

add_section(report_lines, "8. Manual Category / Type Mismatches")
report_lines.append(f"Manual Creatures: {manual_creature_count}")
report_lines.append(f"Scryfall Creatures: {scryfall_creature_count}")
report_lines.append(f"Manual Instants + Sorceries: {manual_instant_sorcery_count}")
report_lines.append(f"Face-Inclusive Scryfall Instants/Sorceries: {scryfall_instant_sorcery_count}")
if type_mismatch_notes:
    report_lines.append("Mismatch Notes:")
    for note in type_mismatch_notes:
        report_lines.append(f"- {note}")
else:
    report_lines.append("No major type count mismatches found.")
if type_mismatch_details:
    report_lines.append("Type Mismatch Details:")
    for m in type_mismatch_details:
        report_lines.append(f"- {m['card_name']} — listed under {m['manual_section']}, but no expected type for that section was found. Scryfall types: {', '.join(m['scryfall_types'])}. Type line: {m['type_line']}")
else:
    report_lines.append("No card-specific type mismatches found.")
report_lines.append("Note: v0.3 no longer treats extra types on a card as mismatches by themselves. Enchantment creatures, artifact creatures, battles with creature backs, adventures, and MDFCs can naturally have multiple types.")

add_section(report_lines, "9. Card Role Tag Summary")
if role_tag_counts:
    for tag, count in role_tag_counts.most_common():
        report_lines.append(f"- {tag}: {count}")
else:
    report_lines.append("No role tags detected.")

add_section(report_lines, "10. Strategy Read")
top_score = primary_strategy_data.get("score", 0)
primary_confidence_raw = get_strategy_confidence(primary_strategy_data.get("score", 0), top_score, primary_strategy_data.get("anchor_hits", 0), primary_strategy_data.get("commander_anchor_hits", 0))
secondary_confidence_raw = get_strategy_confidence(secondary_strategy_data.get("score", 0), top_score, secondary_strategy_data.get("anchor_hits", 0), secondary_strategy_data.get("commander_anchor_hits", 0))
primary_confidence = dampen_display_confidence(primary_confidence_raw, strategy_confidence_warnings)
secondary_confidence = dampen_display_confidence(secondary_confidence_raw, strategy_confidence_warnings)
report_lines.append(f"Likely Primary Strategy: {primary_strategy} ({primary_confidence} confidence, score {primary_strategy_data.get('score', 0)})")
report_lines.append(f"Likely Secondary Strategy: {secondary_strategy} ({secondary_confidence} confidence, score {secondary_strategy_data.get('score', 0)})")
report_lines.append(f"Commander Game Plan: {commander_game_plan}")
report_lines.append(f"Commander Support Level: {commander_support_level}")
report_lines.append(f"Commander Support Reason: {commander_support_reason}")
report_lines.append(f"Main Resource Engine: {primary_strategy_data.get('engine', 'Unclear')}")
report_lines.append(f"Likely Finishers: {primary_strategy_data.get('finishers', 'Unclear')}")
minor_packages = get_strategy_minor_packages(ordered_archetypes, primary_strategy, secondary_strategy)
report_lines.append("Possible Minor Packages:")
if minor_packages:
    for package_name, package_score, package_evidence in minor_packages:
        report_lines.append(f"- {package_name} (score {package_score}) — {package_evidence}")
else:
    report_lines.append("- None clearly identified.")
report_lines.append("Broad Archetype Suppression:")
_suppression_notes = []
for _name, _data in ordered_archetypes:
    if _data.get('suppression_reason') or _data.get('gate_failed_reason') or not _data.get('gate_passed', True):
        _suppression_notes.append((_name, _data))
if _suppression_notes:
    for _name, _data in _suppression_notes[:8]:
        report_lines.extend(format_suppressed_archetype_v057v4(_name, _data))
else:
    report_lines.append("- No broad archetype suppression notes triggered.")
report_lines.append("Why Primary Beat Secondary:")
report_lines.append(f"- {get_primary_selection_reason_v057v4(primary_strategy, secondary_strategy, primary_strategy_data, secondary_strategy_data)}")
for _line in build_reconciliation_lines_v057v4(primary_strategy, secondary_strategy, primary_strategy_data, secondary_strategy_data, ordered_archetypes):
    report_lines.append(_line)
for _line in build_strategy_confidence_diagnostics_lines_v057v4(primary_strategy, secondary_strategy, primary_strategy_data, secondary_strategy_data, ordered_archetypes, strategy_confidence_warnings):
    report_lines.append(_line)
report_lines.append("Scoring Note: v0.5.8 displays final gated scores after suppression and reconciliation.")
if strategy_confidence_warnings:
    report_lines.append("Strategy Confidence Warning:")
    for warning in strategy_confidence_warnings:
        report_lines.append(f"- {warning}")


add_section(report_lines, "10B. Bracket Read")
report_lines.append(f"User's intended bracket: {bracket_read['intended_bracket']}")
if bracket_read['intended_bracket'] == "Unknown":
    report_lines.append("No intended bracket was provided. General recommendation is based on bracket rules, visible Game Changers, win speed signals, combo pressure, and overall deck intent.")
report_lines.append(f"Estimated bracket: {bracket_read['estimated_bracket']}")
report_lines.append(f"Confidence: {bracket_read['confidence']}")
report_lines.append(f"Total Game Changers: {bracket_read['game_changer_count']}")
if bracket_read['game_changers']:
    report_lines.append("Game Changers Found:")
    for card_name in bracket_read['game_changers']:
        report_lines.append(f"- {card_name}")
else:
    report_lines.append("Game Changers Found: None")
report_lines.append("Why this bracket estimate fits:")
for reason in bracket_read['reasons']:
    report_lines.append(f"- {reason}")
report_lines.append("Bracket Pressure Signals:")
report_lines.append(f"- Turbo density: {bracket_read['turbo_density']}")
report_lines.append(f"- Dragonstorm/Tiamat density: {bracket_read['dragonstorm_density']}")
report_lines.append(f"- Fast mana/ritual count: {bracket_read['fast_count']}")
report_lines.append(f"- Tutor/tutor-chain count: {bracket_read['tutor_count']}")
report_lines.append(f"- Combo protection count: {bracket_read['protection_count']}")
if bracket_read['pressure_cards']:
    report_lines.append("Cards Creating Bracket Pressure:")
    for card_name, tags in bracket_read['pressure_cards']:
        report_lines.append(f"- {card_name} — {', '.join(tags)}")
else:
    report_lines.append("Cards Creating Bracket Pressure: None detected")
report_lines.append("Pregame Conversation Note: Based on the visible list, tell the table about the estimated bracket, Game Changers, fast mana/tutor density, and any bracket-pressure packages before the game starts.")

add_section(report_lines, "10C. Synergy Snapshot")
if strong_synergy_cards:
    report_lines.append("")
    report_lines.append("Strong Synergy Cards:")
    for card_name, reason in strong_synergy_cards:
        report_lines.append(f"- {card_name}: {reason}")
else:
    report_lines.append("")
    report_lines.append("Strong Synergy Cards: None clearly identified.")

if possible_off_plan_cards:
    report_lines.append("")
    report_lines.append("Possible Off-Plan Cards:")
    for card_name, reason in possible_off_plan_cards:
        report_lines.append(f"- {card_name}: {reason}")
else:
    report_lines.append("")
    report_lines.append("Possible Off-Plan Cards: None clearly identified.")

add_section(report_lines, "11. Archetype Score Summary")
for archetype, data in ordered_archetypes[:12]:
    display_score = final_score_v057v4(data)
    if display_score <= 0:
        continue
    evidence = "; ".join(dedupe_reasons(data.get("evidence", []), 2)) if data.get("evidence") else "No specific evidence listed."
    confidence = dampen_display_confidence(get_strategy_confidence(display_score, top_score, data.get("anchor_hits", 0), data.get("commander_anchor_hits", 0)), strategy_confidence_warnings)
    report_lines.append(f"- {archetype}: {display_score} ({confidence}) — {evidence}")

add_section(report_lines, "12. Core Synergy Packages")
if core_synergy_packages:
    for package_name, count, tags in core_synergy_packages:
        report_lines.append(f"- {package_name}: {count} relevant tag hit(s) [{', '.join(tags)}]")
else:
    report_lines.append("No clear synergy packages detected.")

add_section(report_lines, "13. Card Plan Fit")
for bucket_name, entries in card_plan_fit_buckets.items():
    report_lines.append(f"{bucket_name} ({len(entries)})")
    if entries:
        for card_name, reason, tags in entries[:25]:
            tag_text = ", ".join(tags) if tags else "no role tags"
            report_lines.append(f"- {card_name}: {reason} Tags: {tag_text}")
        if len(entries) > 25:
            report_lines.append(f"- ...and {len(entries) - 25} more")
    else:
        report_lines.append("- None")
    report_lines.append("")

add_section(report_lines, "14. Cut Pressure Review")
report_lines.append("Deck Size Status:")
report_lines.append(f"- Current deck size: {len(cards)}")
report_lines.append(f"- Required cuts: {cut_pressure_review['required_cuts']}")
report_lines.append(f"- Optional optimization cuts reviewed: {cut_pressure_review['optional_cut_target']}")
report_lines.append(f"- Cut strictness: {cut_pressure_review['cut_strictness']}")
if cut_pressure_review.get('deck_is_underfilled'):
    report_lines.append(f"- Deck is short: {cut_pressure_review.get('deck_short_count', 0)} card(s).")
    report_lines.append("- No cuts required. Prioritize addition/replacement categories before removing cards.")
    if cut_pressure_review.get('addition_needs'):
        report_lines.append("- Addition needs: " + ', '.join(cut_pressure_review.get('addition_needs', [])))
if cut_pressure_review["required_cuts"] > 0:
    report_lines.append(f"- Deck is currently illegal. Required cuts: {cut_pressure_review['required_cuts']}.")
    if cut_pressure_review.get("additional_required_cuts_needed", 0) > 0:
        report_lines.append(f"- The deck still needs {cut_pressure_review['additional_required_cuts_needed']} more cut(s), but the tool cannot identify those cuts confidently without risking core synergy pieces. Review Conflict / Manual Review before deciding.")
else:
    if cut_pressure_review.get("deck_is_underfilled"):
        report_lines.append("- No required cuts because the deck is under 100 cards; this is an addition problem first, not a cut problem.")
    else:
        report_lines.append("- No required cuts. Deck is already at or below Commander deck size.")
report_lines.append("- Legal deck does not mean optimized deck. Optional cuts are tuning suggestions, not legality requirements.")

report_lines.append("")
report_lines.append("Required Cuts:")
if cut_pressure_review["required_cuts_list"]:
    for idx, candidate in enumerate(cut_pressure_review["required_cuts_list"], 1):
        report_lines.append(f"{idx}. {format_cut_candidate(candidate)}")
    if cut_pressure_review.get("additional_required_cuts_needed", 0) > 0:
        report_lines.append(f"Additional Required Cut Candidates Needed: {cut_pressure_review['additional_required_cuts_needed']} more cut(s) are required, but not identified confidently.")
else:
    if cut_pressure_review["required_cuts"] > 0:
        report_lines.append(f"Additional Required Cut Candidates Needed: {cut_pressure_review['required_cuts']} cut(s) are required, but the current scoring cannot identify them confidently without risking protected/core cards.")
    else:
        report_lines.append("No required cuts. Deck is already at or below Commander deck size.")

report_lines.append("")
report_lines.append("Required Cuts Requiring Manual Review:")
if cut_pressure_review.get("required_cuts_requiring_manual_review"):
    for idx, candidate in enumerate(cut_pressure_review.get("required_cuts_requiring_manual_review", []), 1):
        report_lines.append(f"{idx}. {candidate['card_name']} — Manual review required. {candidate.get('manual_review_reason', 'Not a confident cut.')} Tags: {', '.join(candidate.get('tags', [])) if candidate.get('tags') else 'no role tags'}")
else:
    report_lines.append("None identified.")
report_lines.append("")
report_lines.append("Protected/Core Cards Not Forced Into Cuts:")
if cut_pressure_review.get("additional_required_cuts_needed", 0) > 0:
    report_lines.append("The remaining cuts should not be forced from protected/core cards. Review manual candidates through the deck's intended strategy before cutting deeper.")
else:
    report_lines.append("No unresolved required-cut shortfall after confident/manual-review triage.")
report_lines.append("")
report_lines.append("Initial Review Pool — Pre-Final Filtering:")
if cut_pressure_review["optional_cuts_list"]:
    report_lines.append("These were the initial replaceability flags before final role-balance, protection, and cut-bucket normalization. The authoritative final list is in section 15.")
    for idx, candidate in enumerate(cut_pressure_review["optional_cuts_list"], 1):
        report_lines.append(f"{idx}. {format_cut_candidate(candidate)}")
else:
    report_lines.append("No initial optional review candidates were identified by the current replaceability rules.")

report_lines.append("")
report_lines.append("Context-Dependent Cards to Review Manually:")
if cut_pressure_review["context_dependent"]:
    for idx, item in enumerate(cut_pressure_review["context_dependent"], 1):
        report_lines.append(f"{idx}. {item['card_name']}")
        report_lines.append(f"   Why it looks questionable: {item['questionable']}")
        report_lines.append(f"   Why it might still belong: {item['might_belong']}")
else:
    report_lines.append("No context-dependent cards were identified by the current rules.")

report_lines.append("")
report_lines.append("Cards I Would Not Cut:")
if cut_pressure_review["protected"]:
    report_lines.append("Core Engine / Commander Support:")
    core_items = cut_pressure_review.get("protected_core_engine", [])[:8]
    if core_items:
        for idx, (card_name, reason) in enumerate(core_items, 1):
            report_lines.append(f"{idx}. {card_name} — {reason}")
    else:
        report_lines.append("- None identified")
    report_lines.append("Essential Utility:")
    utility_items = cut_pressure_review.get("protected_essential_utility", [])[:8]
    if utility_items:
        for idx, (card_name, reason) in enumerate(utility_items, 1):
            report_lines.append(f"{idx}. {card_name} — {reason}")
    else:
        report_lines.append("- None identified")
    report_lines.append("High-Synergy / Low-Raw-Power:")
    synergy_items = cut_pressure_review.get("protected_high_synergy", [])[:8]
    if synergy_items:
        for idx, (card_name, reason) in enumerate(synergy_items, 1):
            report_lines.append(f"{idx}. {card_name} — {reason}")
    else:
        report_lines.append("- None identified")
else:
    report_lines.append("No protected cards were identified by the current rules.")

add_section(report_lines, "15. Possible Cut Review")
report_lines.append("These are not guaranteed cuts. These are the cards most worth reviewing based on curve, synergy, redundancy, role balance, and the deck's actual plan.")
report_lines.append("The goal is careful recommendations: separate legality fixes, recommended cuts, possible cuts, bracket-pressure cuts, playtest-first cards, and protected/core cards.")
report_lines.append(f"Cut Depth Mode: {CUT_DEPTH_CONFIG.get('mode', 'normal')}")
report_lines.append(f"Optional Cut Target: {CUT_DEPTH_CONFIG.get('optional_cut_target', 5)}")
report_lines.append(f"Actual responsible cut candidates found: {len(possible_cut_review.get('recommended_cuts', [])) + len(possible_cut_review.get('possible_cuts', []))}")
if possible_cut_review.get("target_shortfall_note"):
    report_lines.append(possible_cut_review.get("target_shortfall_note"))
if possible_cut_review.get("diagnostic_warnings"):
    report_lines.append("Cut Review Warnings:")
    for _warning in possible_cut_review.get("diagnostic_warnings", []):
        report_lines.append(f"- {_warning}")
report_lines.append("")
report_lines.append("Current Replacement Need Signals:")
if possible_cut_review["deck_needs"]:
    for need in possible_cut_review["deck_needs"]:
        report_lines.append(f"- {need}")
else:
    report_lines.append("- No major replacement category gaps detected from current role counts.")

report_lines.append("")
report_lines.append("Recommended Cuts:")
if possible_cut_review["recommended_cuts"]:
    for idx, entry in enumerate(possible_cut_review["recommended_cuts"], 1):
        report_lines.append(f"{idx}. Possible Cut: {entry['card_name']}")
        report_lines.append(f"   Reason: {entry['reason']}")
        report_lines.append(f"   Confidence: {entry['confidence']}")
        report_lines.append(f"   Cut Type: {entry['cut_type']}")
        report_lines.append(f"   Replacement Need: {format_replacement_categories(entry['replacement_categories'])}")
        report_lines.append(f"   Exact Replacement: {entry['exact_replacement_note']}")
else:
    report_lines.append("None identified.")

report_lines.append("")
report_lines.append("Possible Cuts to Review:")
if possible_cut_review["possible_cuts"]:
    for idx, entry in enumerate(possible_cut_review["possible_cuts"], 1):
        report_lines.append(f"{idx}. Possible Cut: {entry['card_name']}")
        report_lines.append(f"   Reason: {entry['reason']}")
        report_lines.append(f"   Confidence: {entry['confidence']}")
        report_lines.append(f"   Cut Type: {entry['cut_type']}")
        report_lines.append(f"   Replacement Need: {format_replacement_categories(entry['replacement_categories'])}")
        report_lines.append(f"   Exact Replacement: {entry['exact_replacement_note']}")
else:
    report_lines.append("No responsible optional cuts remained after role-balance, commander-support, and interaction-protection filtering.")
    if possible_cut_review.get("playtest_before_cutting"):
        report_lines.append("Some candidates were moved to Playtest Before Cutting due to role-balance or interaction protection.")
    if possible_cut_review.get("conflict_manual_review"):
        report_lines.append("Some candidates were moved to Manual Review / Pilot Intent Needed.")

report_lines.append("")
report_lines.append("Manual Review / Pilot Intent Needed:")
if possible_cut_review.get("conflict_manual_review"):
    for idx, entry in enumerate(possible_cut_review["conflict_manual_review"], 1):
        report_lines.append(f"{idx}. Conflict / Manual Review: {entry['card_name']}")
        report_lines.append(f"   Cut Pressure: {entry.get('cut_pressure', 'Unknown')}")
        report_lines.append(f"   Protection Pressure: {entry.get('protection_pressure', 'Unknown')}")
        report_lines.append(f"   Why it looked cuttable: {entry.get('why_cuttable', 'Replaceability scoring found cut pressure.')}")
        report_lines.append(f"   Why it may belong: {entry.get('why_belongs', 'Protected/core card signal found.')}")
        report_lines.append(f"   How to decide: {entry.get('how_to_decide', 'Review manually before cutting.')}")
        report_lines.append(f"   Current Recommendation: {entry.get('current_recommendation', 'Playtest first; do not cut automatically.')}")
else:
    report_lines.append("None identified.")

if possible_cut_review.get("additional_required_cuts_needed", 0) > 0:
    report_lines.append(f"Additional Required Cut Candidates Needed: {possible_cut_review['additional_required_cuts_needed']} more required cut(s) remain unresolved. Do not force protected/core cards into cuts just to fill the quota.")

report_lines.append("")
report_lines.append("Refined Deck Review Candidates:")
if possible_cut_review.get("refined_deck_review_candidates"):
    report_lines.append("No confident cuts found. This appears refined. The cards below are not recommended cuts; they are the only cards worth watching through playtesting.")
    for idx, entry in enumerate(possible_cut_review.get("refined_deck_review_candidates", []), 1):
        report_lines.append(f"{idx}. {entry['card_name']}")
        report_lines.append(f"   Label: {entry.get('label', 'Playtest-first review candidate')}")
        report_lines.append(f"   Why to watch: {entry.get('why_to_watch', 'Context-dependent or minor-package card.')}")
        report_lines.append(f"   Why it may belong: {entry.get('why_it_may_belong', 'May still support the deck plan.')}")
        report_lines.append(f"   Watch For: {entry.get('watch_for', 'Track whether it advances the commander, primary plan, or win condition.')}")
else:
    report_lines.append("No refined-deck fallback candidates needed.")
report_lines.append("")
report_lines.append("Playtest Before Cutting:")
if possible_cut_review["playtest_before_cutting"]:
    for idx, entry in enumerate(possible_cut_review["playtest_before_cutting"], 1):
        report_lines.append(f"{idx}. {entry['card_name']}")
        report_lines.append(f"   Why it is questionable: {entry['why_questionable']}")
        report_lines.append(f"   Why it might still belong: {entry['why_might_belong']}")
        report_lines.append(f"   What to watch for: {entry['what_to_watch']}")
else:
    report_lines.append("None identified.")

report_lines.append("")
report_lines.append("Protected From Cut:")
if possible_cut_review["protected_from_cut"]:
    for idx, entry in enumerate(possible_cut_review["protected_from_cut"], 1):
        report_lines.append(f"{idx}. Protected From Cut: {entry['card_name']}")
        report_lines.append(f"   Reason: {entry['reason']}")
else:
    report_lines.append("None identified.")


add_section(report_lines, "15A. Deck Completion / Addition Review")
report_lines.append(deck_completion_review.get("status", "Deck completion review unavailable."))
if deck_completion_review.get("enabled"):
    report_lines.append(f"Cards needed to reach 100: {deck_completion_review.get('cards_needed', 0)}")
    report_lines.append("Completion rule: do not make normal cuts from an underfilled deck unless the pilot explicitly chooses rebuild mode.")
    report_lines.append("Color identity safety: exact addition candidates in this section are filtered through commander color identity before being listed.")
    report_lines.append("")
    report_lines.append("Addition Priorities:")
    for idx, priority in enumerate(deck_completion_review.get("addition_priorities", []) or ["Add cards that support the confirmed deck plan and fill role gaps."], 1):
        report_lines.append(f"{idx}. {priority}")
    if deck_completion_review.get("warnings"):
        report_lines.append("")
        report_lines.append("Completion Warnings:")
        for warning in deck_completion_review.get("warnings", []):
            report_lines.append(f"- {warning}")
    report_lines.append("")
    report_lines.append("Collection/Card-Pool Completion Candidates:")
    if deck_completion_review.get("collection_candidates"):
        for idx, item in enumerate(deck_completion_review.get("collection_candidates", [])[:30], 1):
            mv_text = "unknown MV" if item.get("mana_value") is None else f"MV {item.get('mana_value')}"
            matched = ", ".join(item.get("matched_roles", [])) if item.get("matched_roles") else "role match"
            report_lines.append(f"{idx}. {item['card_name']} — available {item.get('available_qty', '?')} / owned {item.get('owned_qty', '?')}; {mv_text}; matches: {matched}")
    else:
        report_lines.append("No collection/card-pool completion candidates found or no collection file loaded.")
    report_lines.append("")
    report_lines.append("Full Magic Card Pool Completion Candidates:")
    if deck_completion_review.get("full_pool_candidates"):
        for idx, item in enumerate(deck_completion_review.get("full_pool_candidates", [])[:35], 1):
            mv_text = "unknown MV" if item.get("mana_value") is None else f"MV {item.get('mana_value')}"
            matched = ", ".join(item.get("matched_roles", [])) if item.get("matched_roles") else "role match"
            report_lines.append(f"{idx}. {item['card_name']} — {mv_text}; matches: {matched}")
    else:
        report_lines.append("No full-pool candidates found after color identity and role filtering.")
else:
    report_lines.append("No completion candidates shown because this deck is not underfilled.")

add_section(report_lines, "15B. Collection / Card Pool Replacement Candidates")
report_lines.append(collection_replacement_review.get("status", "No collection/card-pool file loaded."))
if collection_replacement_review.get("loaded"):
    report_lines.append(f"Collection cards parsed: {collection_replacement_review.get('total_cards', 0)} total / {collection_replacement_review.get('unique_cards', 0)} unique")
    if collection_replacement_review.get("not_found"):
        report_lines.append("Collection cards not found in Scryfall, first 50:")
        for card_name in collection_replacement_review.get("not_found", [])[:50]:
            report_lines.append(f"- {card_name}")
    report_lines.append("")
    report_lines.append("Candidates by Current Replacement Need:")
    if collection_replacement_review.get("candidates_by_need"):
        for need, candidates in collection_replacement_review.get("candidates_by_need", {}).items():
            report_lines.append(f"{need}:")
            for idx, item in enumerate(candidates, 1):
                mv_text = "unknown MV" if item.get("mana_value") is None else f"MV {item.get('mana_value')}"
                matched = ", ".join(item.get("matched_roles", [])) if item.get("matched_roles") else "role match"
                report_lines.append(f"{idx}. {item['card_name']} — available {item['available_qty']} / owned {item['owned_qty']}; {mv_text}; matches: {matched}")
    else:
        report_lines.append("No collection candidates matched the current replacement need categories.")
    report_lines.append("")
    report_lines.append("General Collection Candidates That Fit Strategy or Role Balance:")
    if collection_replacement_review.get("general_candidates"):
        for idx, item in enumerate(collection_replacement_review.get("general_candidates", [])[:20], 1):
            mv_text = "unknown MV" if item.get("mana_value") is None else f"MV {item.get('mana_value')}"
            matched = ", ".join(item.get("matched_roles", [])) if item.get("matched_roles") else "strategy/utility role"
            report_lines.append(f"{idx}. {item['card_name']} — available {item['available_qty']} / owned {item['owned_qty']}; {mv_text}; matches: {matched}")
    else:
        report_lines.append("No general collection candidates found after color identity and availability filtering.")
else:
    report_lines.append("To enable this section, place a file at collections/collection.txt, collections/card_pool.txt, collection.txt, or set MTG_COLLECTION_FILE / MTG_CARD_POOL_FILE.")
    report_lines.append("Accepted simple formats include: '1 Sol Ring', '1x Sol Ring', 'Sol Ring', '1,Sol Ring', or 'Sol Ring,1'.")

add_section(report_lines, "16. Card Role Tags by Card")
for card_name in sorted(unique_cards):
    tags = card_role_tags_by_card.get(card_name, [])
    report_lines.append(f"- {card_name}: {', '.join(tags) if tags else 'no_role_tags_detected'}")

add_section(report_lines, "17. Tag-Based Review Notes")
if tag_based_review_notes:
    for note in sorted(set(tag_based_review_notes)):
        report_lines.append(f"- {note}")
else:
    report_lines.append("No tag-based review notes generated.")

add_section(report_lines, "18. Possible Cut Flags")
if possible_cut_flags:
    for card_name, reason in possible_cut_flags.items():
        report_lines.append(f"- {card_name}: {reason}")
else:
    report_lines.append("No obvious conservative cut flags found.")

add_section(report_lines, "19. Manual Review Items")
if manual_review_items:
    for item in manual_review_items:
        report_lines.append(f"- {clean_reason_text(item)}")
else:
    report_lines.append("No manual review items found.")

add_section(report_lines, "Developer Diagnostics")
report_lines.append("Tribal Support Check:")
if creature_type_counts:
    report_lines.append("Creature Type Counts:")
    for ctype, count in creature_type_counts.most_common():
        if count >= 2:
            report_lines.append(f"- {ctype}: {count}")
if tribal_support_flags:
    report_lines.append("Potential Unsupported Tribal Cards:")
    for flag in tribal_support_flags:
        report_lines.append(f"- {flag['card_name']} — references {flag['referenced_type']}s, but the deck only has {flag['support_count']} {flag['referenced_type']} creature(s).")
else:
    report_lines.append("No obvious unsupported tribal references found.")


# v0.5.7 strategy confidence, attribute relevance, and compact diagnostics.
primary_tags_v057, secondary_tags_v057 = get_primary_secondary_tag_sets(primary_strategy, secondary_strategy)
confidence_warnings_v057 = get_strategy_confidence_warning(primary_strategy, secondary_strategy, primary_strategy_data, secondary_strategy_data, role_tag_counts)
if confidence_warnings_v057 or len(confidence_warnings_v057) >= 2:
    v057_strategy_confidence = "Low" if len(confidence_warnings_v057) >= 3 else "Medium"
elif primary_strategy_data.get("commander_anchor_hits", 0) > 0 or primary_strategy_data.get("anchor_hits", 0) >= 6:
    v057_strategy_confidence = "High"
else:
    v057_strategy_confidence = "Medium"
attribute_relevance_v057 = [
    classify_attribute_relevance_v057(card_name, card_role_tags_by_card.get(card_name, []), primary_tags_v057, secondary_tags_v057, role_tag_counts)
    for card_name in sorted(unique_cards)
]
role_balance_v057 = compute_role_balance_v057(role_tag_counts, scryfall_land_count)
add_section(report_lines, "v0.5.8 Developer Diagnostics Summary")
report_lines.append(f"Strategy Confidence: {v057_strategy_confidence}")
report_lines.append("Confidence Reason: " + ("; ".join(confidence_warnings_v057[:3]) if confidence_warnings_v057 else "Commander, role tags, and scored packages point toward a stable primary read."))
report_lines.append(f"Cut Depth Mode: {CUT_DEPTH_CONFIG.get('mode', 'normal')}")
report_lines.append(f"Optional Cut Target: {CUT_DEPTH_CONFIG.get('optional_cut_target', 5)}")
report_lines.append(f"Output Mode: {OUTPUT_MODE}")
report_lines.append(f"Role Balance Counts: {role_balance_v057['counts']}")
report_lines.append(f"Roles Underfilled: {', '.join(role_balance_v057['underfilled']) if role_balance_v057['underfilled'] else 'None'}")
report_lines.append(f"Roles Overfilled: {', '.join(role_balance_v057['overfilled']) if role_balance_v057['overfilled'] else 'None'}")
if archetype_scores.get("__v057_diagnostics__"):
    report_lines.append("Suppression Rules Triggered:")
    for item in archetype_scores["__v057_diagnostics__"].get("suppression_rules_triggered", [])[:12]:
        report_lines.append(f"- {clean_reason_text(item)}")
else:
    report_lines.append("Suppression Rules Triggered: None recorded.")
report_lines.append("SUMMARY_PRIMARY: " + str(primary_strategy))
report_lines.append("SUMMARY_SECONDARY: " + str(secondary_strategy))
report_lines.append("SUMMARY_DECK_SIZE: " + str(len(cards)))
report_lines.append("SUMMARY_REQUIRED_CUTS: " + str(cut_pressure_review.get('required_cuts', 0)))
report_lines.append("SUMMARY_UNRESOLVED_CUTS: " + str(possible_cut_review.get('additional_required_cuts_needed', 0)))
report_lines.append("SUMMARY_BRACKET: " + str(bracket_read.get('estimated_bracket', 'Unknown')))
report_lines.append("SUMMARY_WARNINGS: " + ("; ".join(confidence_warnings_v057[:3]) if confidence_warnings_v057 else "None"))

def strip_debug_heavy_sections_for_normal_v058(report_text):
    """Keep Normal User Mode clean while preserving raw diagnostics for debug files."""
    summary_lines = [line.replace("v0.5.7", "v0.5.8") for line in report_text.splitlines() if line.startswith("SUMMARY_")]

    # Remove raw tag dump / tag explanation blocks from normal output.
    report_text = clean_inline_tags_in_user_facing_sections_v057v5(report_text, attribute_relevance_v057)
    report_text = clean_user_facing_role_tags_v057(report_text, attribute_relevance_v057)
    report_text = report_text.replace("v0.5.7", "v0.5.8")

    # Remove raw per-card role sections and developer diagnostics from polished normal output.
    raw_start_match = re.search(r"\n=+\n16\. (?:Card Role Tags by Card|Diagnostic Role Tags)\n-+", report_text)
    if raw_start_match:
        raw_start = raw_start_match.start()
        keep_start = report_text.find("\n==============================\n18. Possible Cut Flags", raw_start)
        if keep_start != -1:
            report_text = report_text[:raw_start].rstrip() + report_text[keep_start:]
    dev_marker = "==============================\nDeveloper Diagnostics"
    dev_start = report_text.find(dev_marker)
    if dev_start != -1:
        report_text = report_text[:dev_start].rstrip()

    if summary_lines:
        compact = [
            "", "==============================", "20. Batch QA Summary", "------------------------------",
            "Compact grep-friendly lines are included for batch QA; raw diagnostics are in Debug / Stress-Test Mode.",
        ]
        compact.extend(summary_lines)
        report_text = report_text.rstrip() + "\n" + "\n".join(compact)
    return report_text.rstrip() + "\n"


debug_source_report_text = "\n".join(report_lines)
normal_report_text = strip_debug_heavy_sections_for_normal_v058(debug_source_report_text)
report_text = normal_report_text

# ==============================
# v0.5.7 Output Generation
# ==============================
def shorten_output_stem(name, max_length=MAX_OUTPUT_STEM_LENGTH):
    stem = sanitize_filename(name or "Unknown_Deck", max_length=max_length)
    return stem or "Unknown_Deck"


def safe_output_filename(base_name, extension=".txt", max_length=MAX_OUTPUT_FILENAME_LENGTH):
    ext = extension if extension.startswith(".") else f".{extension}"
    safe_base = sanitize_filename(base_name or "output", max_length=max(12, max_length - len(ext)))
    return f"{safe_base}{ext}"


def get_unique_output_path(folder, base_name, extension=".txt"):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    output_path = folder / safe_output_filename(base_name, extension)
    counter = 2
    while output_path.exists():
        suffix = f"_{counter}"
        max_base = max(12, MAX_OUTPUT_FILENAME_LENGTH - len(extension) - len(suffix))
        safe_base = sanitize_filename(base_name or "output", max_length=max_base)
        output_path = folder / f"{safe_base}{suffix}{extension}"
        counter += 1
    return output_path


def trim_rules_for_prompt(text, max_chars=3500):
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n\n[Rules file trimmed in prompt for size. Use the full rules file in /rules for complete guidance.]"


def make_cut_replacement_prompt_v057(report_text):
    """Build the standalone user-guided review prompt.

    v0.6.2.4 intentionally does NOT embed the deck report in the prompt.
    The reviewing AI must ask the user to upload/paste the generated deck report
    text file before beginning the staged intake. The intake must proceed one
    section at a time and must produce a User Intent Summary before final review.
    """
    deck_count = len(cards) if 'cards' in globals() else 0
    if deck_count > 100:
        deck_size_status = f"Over 100 cards — required cuts: {deck_count - 100}"
    elif deck_count == 100:
        deck_size_status = "Exactly 100 cards — required cuts: 0"
    elif deck_count > 0:
        deck_size_status = f"Under 100 cards — short by {100 - deck_count}; addition-first unless rebuilding"
    else:
        deck_size_status = "Unknown deck size — determine from uploaded deck report"

    reported_primary_strategy = globals().get('primary_strategy', 'Unknown / read from uploaded report')
    reported_secondary_strategy = globals().get('secondary_strategy', 'Unknown / read from uploaded report')
    strategy_confidence = globals().get('v057_strategy_confidence', 'Medium')
    review_direction = globals().get('REVIEW_DIRECTION', 'cut_down')
    build_up_config = globals().get('BUILD_UP_CONFIG', {'mode': 'not_applicable', 'label': 'Not applicable', 'alpha': False})
    build_up_label = build_up_config.get('label', 'Not applicable')
    alpha_note = "This is an Alpha build-from-scratch workflow. It may not be ready for fully automated 99-card deck construction, so every exact card suggestion must be treated as a draft for human review." if build_up_config.get('alpha') else "Not applicable."
    prompt_interaction_mode = globals().get('PROMPT_INTERACTION_MODE', 'interactive')
    prompt_interaction_label = PROMPT_INTERACTION_MODE_DISPLAY.get(prompt_interaction_mode, prompt_interaction_mode)
    command_zone_count = len(globals().get('commander_names', []))
    commander_list_text = ' + '.join(globals().get('commander_names', [])) if globals().get('commander_names', []) else commander_name
    cards_needed_to_100 = max(0, 100 - deck_count)
    detected_deck_size_rule = (
        f"Current deck size from script/report: {deck_count}.\n"
        f"Command-zone cards detected: {command_zone_count} ({commander_list_text}).\n"
        f"Cards needed to reach 100: {cards_needed_to_100}.\n"
        f"Required addition list size: exactly {cards_needed_to_100} card(s)."
    )

    universal_safety_rules = f"""
Universal recommendation safety rules:
1. Use the uploaded deck report's deck size as the source of truth for build-up math. Do not assume 98 additions unless the report says the current deck has exactly 2 cards.
2. All exact card suggestions must be legal within the commander's color identity.
3. Do not recommend a card outside the commander's color identity, even if it strongly supports the deck's theme.
4. If a theme card is outside color identity, mention only that it is off-color and cannot be used, then suggest an in-color category or alternative.
5. Do not recommend any card already listed in the deck report unless it is a basic land, it has an explicit legal duplicate exception, or the user specifically asks whether to add more legal copies.
6. Before finalizing recommendations, check whether each recommended card already appears in the deck report. If it already appears and is not a legal duplicate exception, remove it and use a different legal candidate or a replacement/addition category instead.
7. Combo questions are preference questions only. Do not claim confirmed infinite combo detection unless the uploaded report explicitly contains a confirmed combo section from a future combo module.
8. Do not research combos, add combo databases, or recommend combo-completion cards unless the user explicitly asks and the needed information is available.
9. Do not use combo preference as automatic cut pressure in v0.6.
10. Keep bracket pressure separate from legality. Game Changers are not automatic cuts in v0.6.
11. This is a decision-support tool, not an end-all-be-all deck authority. Aim for a playable 70% solution; final tuning, pet-card choices, meta calls, and final cut/add decisions belong to the player.
12. Treat removal and interaction as important default deck infrastructure. Do not cut interaction at a high rate unless it is clearly overrepresented, off-plan, or the user asked to reduce it.
13. Do not assume traditional defender payoffs, typal payoffs, or stock archetype staples fit the pilot's playstyle if the user says those cards are too clunky or slow.
14. Timing-sensitive buffs matter. If a commander checks power/toughness at end step before end-of-turn effects wear off, temporary power/toughness or toughness boosts can be real synergy and should be manual-review/protect candidates, not automatic cuts.
15. Use numbered lists instead of bullets.
16. If the user says casual, avoid banned cards, cEDH staples, excess fast mana, and loading the deck with Game Changers unless the user explicitly asks for them.
17. If a budget is provided, treat it as a hard target; when prices are uncertain, avoid likely expensive staples or mark them as optional upgrades instead of main-list includes.
""".strip()

    if prompt_interaction_mode == 'worksheet' and review_direction == 'build_up':
        return f"""
You are an experienced Magic: The Gathering Commander deck builder helping the deck's pilot build up or complete a Commander deck.

Prompt version: v0.6.2.6 — Worksheet Guardrail Hotfix
The command zone card(s): {commander_name}
Prompt Interaction Mode: One-shot worksheet — asks all questions at once for limited/free AI use

This is the BUILD-UP worksheet workflow, not the cut-down workflow. The generated deck report is intentionally NOT included in this prompt.

Before beginning, check whether the user has uploaded or pasted the generated deck report txt file in the current chat.

If the deck report txt file is NOT available:
1. Ask the user to upload or paste the generated deck report txt file.
2. Explain that once the report is available, you will provide the full build-up worksheet in one message.
3. Then stop.

If the deck report txt file IS available:
1. Read the report enough to identify commander, color identity, deck size, reported primary strategy, reported secondary strategy, collection/card-pool status, and Deck Completion / Addition Review section.
2. Provide the full worksheet below in one message.
3. Ask the user to fill it out in one reply.
4. Stop and wait.
5. After the user answers, produce the Build-Up User Intent Summary, then either ask for confirmation or continue if the user already gave permission.
6. Only after that should you produce the final build-up plan.

Script context, for defaults only:
1. Review Direction from script: Build up / complete deck.
2. Build-Up Mode from script: {build_up_label}
3. Deck Size Status from script: {deck_size_status}
4. Reported Primary Strategy from script: {reported_primary_strategy}
5. Reported Secondary Strategy from script: {reported_secondary_strategy}
6. Strategy Confidence from script: {strategy_confidence}
7. Collection/Card Pool File from script: {COLLECTION_FILE if COLLECTION_FILE else 'None loaded'}
8. Collection/Card Pool Status from script: {collection_status_note}
9. Alpha Warning: {alpha_note}

{universal_safety_rules}

==================================================
HARD BUILD-UP DECK-SIZE RULES
==================================================

{detected_deck_size_rule}

1. Use the uploaded deck report's Total Cards / Current deck size as the source of truth.
2. Do not calculate additions from the number of commanders alone.
3. Single-commander-only lists usually need 99 additions, but only if the report says the current deck has exactly 1 card.
4. Partner/background/two-command-zone-card lists usually need 98 additions, but only if the report says the current deck has exactly 2 cards.
5. Partial shells must use the actual current deck size from the report.
6. Before finalizing, count the addition list and confirm the total deck size after additions is exactly 100.

Worksheet mode rules:
1. Show all questions at once after the report is available.
2. Do not give final additions, full decklists, replacements, or cuts before the user answers the worksheet.
3. The user may write short answers, default, N/A, or proceed with defaults.
4. If a missing answer is not critical, proceed with a labeled assumption.
5. This mode is for limited-message/free AI workflows where the user wants to answer everything in one reply.

==================================================
BUILD-UP WORKSHEET — ANSWER ALL SECTIONS IN ONE REPLY
==================================================

Fill in the Answer line under each question. Short answers, default, or N/A are allowed. Do not delete the question labels; they help the AI keep your answers matched to the right constraint.

Section 1 — Build-Up Context
1. Is the selected build-up mode correct: {build_up_label}?
Answer:

2. Optional if Question 1 is correct: choose the best build-up mode if this needs changing:
   1. Build from Scratch — I only have the commander. Alpha feature; may not be ready yet.
   2. Point me in the right direction — I need 30+ cards.
   3. Help me get there — I need 11 to 30 cards.
   4. Finalize — I need 10 or fewer cards.
Answer:

3. Should the current cards be treated as:
   1. A committed shell.
   2. A flexible starting point.
   3. An inspiration pool.
   4. A commander-only concept.
Answer:

Section 2 — Commander Plan / Deck Identity
1. What do you want this commander or deck to do when it is working correctly?
Answer:

2. Is the reported primary strategy correct: {reported_primary_strategy}? If not, what should it be?
Answer:

3. Is the reported secondary strategy correct: {reported_secondary_strategy}? If not, what should it be?
Answer:

4. Are there specific mechanics, themes, packages, or play patterns you want to build around?
Answer:

5. For Build from Scratch only: describe the desired deck identity in plain language.
Answer:

Section 3 — Power / Table / Playstyle Intent
1. What kind of table is this deck meant for: casual, upgraded casual, high-power, optimized, cEDH-adjacent, or something else?
Answer:

2. Do you want the deck to be theme-first, synergy-first, consistency-first, power-first, budget-first, or table-friendly?
Answer:

3. Are infinite combos or near-combos welcome, acceptable but not preferred, or unwanted?
Answer:

4. Should the deck avoid accidentally becoming stronger than the playgroup expects?
Answer:

5. What playstyle do you prefer: proactive, reactive, grindy, explosive, combat-focused, engine-focused, political, or something else?
Answer:

Section 4 — Card Pool / Budget / Restrictions
1. Should additions come from:
   1. Full Magic card database.
   2. Collection/card-pool candidates shown in the report.
   3. A separate uploaded/pasted collection file.
   4. Both full card pool and collection, with collection preferred.
   5. Categories only, no exact card names.
Answer:

2. Are there budget limits, availability limits, pet-card restrictions, or color/theme restrictions?
Answer:

3. Should the build prioritize:
   1. Synergy.
   2. Consistency.
   3. Lower curve.
   4. Interaction.
   5. Ramp.
   6. Card advantage.
   7. Table friendliness.
   8. Power.
   9. Theme/flavor.
Answer:

4. Should additions avoid adding or completing combos unless you explicitly want that?
Answer:

Section 5 — Desired Build Output
1. What build-up output style do you want?
   1. Directional build plan.
   2. Exact additions list.
   3. Category-only additions.
   4. Prioritized action plan.
   5. Playtest checklist.
   6. Full diagnostic build plan.
   7. Prompt/report suitable for another AI chat.
   8. Downloadable/copy-paste addition list txt.
Answer:

2. Do you want the final build plan to include role targets, such as number of lands, ramp, draw, removal, protection, synergy pieces, and finishers?
Answer:

3. Should the final output separate must-add categories, strong suggestions, optional ideas, and playtest notes?
Answer:

Default assumptions if skipped:
1. Build-Up Mode: {build_up_label}.
2. Current cards: flexible starting point unless commander-only.
3. Deck plan: use the report's strategy read as provisional evidence.
4. Table intent: casual/upgraded casual unless stated otherwise.
5. Additions: use collection/card-pool if present; otherwise full Magic card database.
6. Budget/restrictions: unknown.
7. Output style: prioritized action plan with role targets and playtest notes.

==================================================
REQUIRED BUILD-UP USER INTENT SUMMARY BEFORE FINAL BUILD PLAN
==================================================

After the user answers, show:

Build-Up User Intent Summary
------------------------------
Build-Up Mode:
Current Deck Status:
Cards Needed to Reach 100:
Commander Plan:
Primary Strategy:
Secondary Strategy:
Theme / Package Intent:
Power / Table Intent:
Card Pool Source:
Budget / Availability Limits:
Color / Theme Restrictions:
Protected / Must-Keep Cards:
Cards to Build Around:
Desired Addition Style:
Requested Output Style:
Assumptions / Unknowns:

Then ask: "Does this summary look right? If yes, I’ll continue to the final build plan. If not, tell me what to correct."
If the user already gave permission to proceed, continue without asking again.

Final build-up rules:
1. Put Deck Identity first, then immediately provide Section 2 — Draft XX-Card Addition List.
2. The Draft XX-Card Addition List must use one card per line in this format: 1x Card Name.
3. If downloadable file creation is supported, create a .txt file containing only that addition list. Otherwise provide a clean copy/paste text block labeled addition_list.txt.
4. For Build from Scratch, calculate the exact number of additions needed from the report. Do not assume 98 additions unless the report says the current deck has exactly 2 cards; a single-commander-only list usually needs 99, and partial shells need 100 minus the current deck size.
5. Do not create cut pressure for underfilled decks unless rebuild/trim is requested.
""".strip()

    if prompt_interaction_mode == 'worksheet' and review_direction != 'build_up':
        return f"""
You are an experienced Magic: The Gathering Commander deck builder helping the deck's pilot review, cut down, or tune a Commander deck.

Prompt version: v0.6.2.6 — Worksheet Guardrail Hotfix
The command zone card(s): {commander_name}
Prompt Interaction Mode: One-shot worksheet — asks all questions at once for limited/free AI use

This is the CUT-DOWN worksheet workflow, not the build-up workflow. The generated deck report is intentionally NOT included in this prompt.

Before beginning, check whether the user has uploaded or pasted the generated deck report txt file in the current chat.

If the deck report txt file is NOT available:
1. Ask the user to upload or paste the generated deck report txt file.
2. Explain that once the report is available, you will provide the full cut-down worksheet in one message.
3. Then stop.

If the deck report txt file IS available:
1. Read the report enough to identify commander, color identity, deck size, required cuts, reported primary strategy, reported secondary strategy, collection/card-pool status, and cut pressure sections.
2. Provide the full worksheet below in one message.
3. Ask the user to fill it out in one reply.
4. Stop and wait.
5. After the user answers, produce the User Intent Summary, then either ask for confirmation or continue if the user already gave permission.
6. Only after that should you produce the final review.

Script context, for defaults only:
1. Review Direction from script: Cut down / tune.
2. Cut Depth Mode from script: {CUT_DEPTH_CONFIG.get('mode', 'normal')}
3. Deck Size Status from script: {deck_size_status}
4. Reported Primary Strategy from script: {reported_primary_strategy}
5. Reported Secondary Strategy from script: {reported_secondary_strategy}
6. Strategy Confidence from script: {strategy_confidence}
7. Collection/Card Pool File from script: {COLLECTION_FILE if COLLECTION_FILE else 'None loaded'}
8. Collection/Card Pool Status from script: {collection_status_note}

{universal_safety_rules}

==================================================
HARD BUILD-UP DECK-SIZE RULES
==================================================

{detected_deck_size_rule}

1. Use the uploaded deck report's Total Cards / Current deck size as the source of truth.
2. Do not calculate additions from the number of commanders alone.
3. Single-commander-only lists usually need 99 additions, but only if the report says the current deck has exactly 1 card.
4. Partner/background/two-command-zone-card lists usually need 98 additions, but only if the report says the current deck has exactly 2 cards.
5. Partial shells must use the actual current deck size from the report.
6. Before finalizing, count the addition list and confirm the total deck size after additions is exactly 100.

Worksheet mode rules:
1. Show all questions at once after the report is available.
2. Do not give final cuts, replacements, or additions before the user answers the worksheet.
3. The user may write short answers, default, N/A, or proceed with defaults.
4. If a missing answer is not critical, proceed with a labeled assumption.
5. This mode is for limited-message/free AI workflows where the user wants to answer everything in one reply.

==================================================
CUT-DOWN WORKSHEET — ANSWER ALL SECTIONS IN ONE REPLY
==================================================

Section 1 — Main Review Goal
1. Choose one or more review goals:
   1. Get the deck down to a legal 100-card list.
   2. Optimize an already legal 100-card deck.
   3. Improve strategy focus.
   4. Improve mana curve.
   5. Improve ramp/draw/removal balance.
   6. Tune for a target power level.
   7. General full review.
   8. Cut-only review.
   9. Replacement-focused review.
   10. Playtest-focused review.
   11. Mana base review.
   12. Strategy/synergy review.
   13. Batch QA / bug-finding review.

Section 2 — Deck Plan
1. What is the deck supposed to do when it is working correctly?
2. What is the ideal play pattern?
3. Is the reported primary strategy correct: {reported_primary_strategy}? If not, what should it be?
4. Is the reported secondary strategy correct: {reported_secondary_strategy}? If not, what should it be?
5. What is the theme, if there is one? It is okay if there is no theme beyond the strategy.
6. What cards, packages, or play patterns matter most to the deck's identity?

Section 3 — Commander Role
1. What role should the commander play?
   1. Main engine.
   2. Finisher.
   3. Value piece.
   4. Support piece.
   5. Color identity only.
   6. Not sure.

Section 4 — Protected / Pet / Build-Around Intent
Heads up: this section asks the same topic in two forms on purpose. Question 1 is the plain-language answer. Question 2 is the copy/paste structure.
1. Are there any cards, packages, or play patterns that are emotionally or strategically important to keep, including pet cards, theme cards, political cards, or local-meta cards that should not be cut unless absolutely necessary?
2. If yes, copy/paste and fill out any fields that matter. If no, write "not applicable":
   1. Cards you refuse to cut:
   2. Pet cards you want protected:
   3. Cards you want to build around:
   4. Cards you are uncertain about:
   5. Cards you specifically want reviewed:

Section 5 — Power / Bracket / Table Intent
1. What kind of table is this deck meant for: casual, upgraded casual, high-power, optimized, cEDH-adjacent, or something else?
2. Should Game Changers, fast mana, tutors, free interaction, stax, mass land denial, or salt-risk cards be reduced for table fit?
3. Should bracket pressure be treated as a real possible cut reason, or only as a pregame conversation note?
4. Are infinite combos or near-combos welcome, acceptable but not preferred, or unwanted?
5. Should the deck avoid accidentally becoming stronger than the playgroup expects?

Section 6 — Cut Philosophy
1. How aggressive should the cuts be?
   1. Light.
   2. Normal.
   3. Strict.
   4. Brutal.
   5. Rebuild.
   6. Custom.
2. Are you trying to make required cuts to reach 100, optimize a legal 100-card deck, or rebuild the deck more heavily?
3. Should low-confidence possible cuts be shown, or only stronger candidates?
4. Should interaction, ramp, and card draw be protected unless clearly overrepresented?
5. Should the final answer separate Recommended Cuts, Possible Cuts, Playtest Before Cutting, Manual Review, and Protected Cards?

Section 7 — Replacement Philosophy and Output
1. What replacement style do you want?
   1. No replacements.
   2. Replacement categories only.
   3. Exact replacement cards only when obvious.
   4. Exact replacement cards welcome.
   5. Exact replacements only from my collection/card pool.
   6. Replacement suggestions later.
2. Should exact replacement or addition suggestions assume:
   1. Full Magic card pool.
   2. Collection/card-pool candidates shown in the uploaded report.
   3. A separate uploaded/pasted collection file.
   4. Both full card pool and collection, with collection preferred.
3. Are there budget limits, availability limits, pet-card restrictions, or color/theme restrictions?
4. Should replacements prioritize synergy, lower curve, more interaction, more consistency, table friendliness, or power?
5. Should replacements avoid adding or completing combos unless you explicitly want that?
6. If the deck is underfilled, should additions come from the full Magic card pool, your collection/card-pool, or both? If you are only cutting down an overfilled deck, answer N/A.
7. What final output style do you want?
   1. Short prioritized cut list.
   2. Full diagnostic report.
   3. Strategy-focused review.
   4. Cut-only review.
   5. Replacement-focused review.
   6. Playtest notes.
   7. Prompt/report suitable for another AI chat.
   8. Batch QA / bug-finding review.

Default assumptions if skipped:
1. Review Goal: General full review.
2. Deck Plan: Use the report's strategy read as provisional evidence.
3. Commander Role: Main engine if commander support is high; otherwise Not sure.
4. Protected Cards: None provided.
5. Bracket Pressure: Pregame conversation note only, not automatic cut reason.
6. Cut Aggression: {CUT_DEPTH_CONFIG.get('mode', 'normal')}.
7. Replacement Mode: Replacement categories first; exact cards only when obvious and safe.
8. Output Style: Full diagnostic report.

==================================================
REQUIRED USER INTENT SUMMARY BEFORE FINAL REVIEW
==================================================

After the user answers, show:

User Intent Summary
------------------------------
Review Goal:
Deck Plan:
Commander Role:
Primary Strategy:
Secondary Strategy:
Theme / Package Intent:
Cut Depth:
Deck Size Status:
Power / Table Intent:
Replacement Preference:
Collection / Card Pool Restriction:
Cards Refused for Cuts:
Pet Cards / Protected Cards:
Cards to Build Around:
Cards User Is Uncertain About:
Cards Specifically Requested for Review:
Requested Output Style:
Assumptions / Unknowns:

Then ask: "Does this summary look right? If yes, I’ll continue to the final review. If not, tell me what to correct."
If the user already gave permission to proceed, continue without asking again.

Final review rules:
1. Separate required cuts from optional optimization cuts.
2. Do not force cut pressure on legal or underfilled decks.
3. Protect refused/pet/build-around cards from normal cut pressure.
4. Respect replacement and output-style preferences.
5. Do not recommend cards already in the deck unless a legal duplicate exception applies.
6. Keep bracket pressure separate from legality and automatic cuts.
""".strip()

    if review_direction == 'build_up':
        return f"""
You are an experienced Magic: The Gathering Commander deck builder helping the deck's pilot build up or complete a Commander deck.

Prompt version: v0.6.2.6 — Worksheet Guardrail Hotfix
The command zone card(s): {commander_name}
Prompt Interaction Mode: {prompt_interaction_label}

This is the BUILD-UP workflow, not the cut-down workflow. The generated deck report is intentionally NOT included in this prompt.

Before beginning the intake, check whether the user has also uploaded or pasted the generated deck report txt file in the current chat.

If the deck report txt file is NOT available:
1. Do not start Section 1 yet.
2. Do not ask build questions yet.
3. Ask the user to upload or paste the generated deck report txt file.
4. Explain that once the report is available, you will begin Section 1 and proceed one section at a time.
5. Then stop.

If the deck report txt file IS available:
1. Read the report enough to identify the commander, color identity, deck size, reported primary strategy, reported secondary strategy, collection/card-pool status, and Deck Completion / Addition Review section.
2. Begin Section 1 only.
3. Stop and wait for the user's Section 1 answer.

Script context, for defaults only:
1. Review Direction from script: Build up / complete deck.
2. Build-Up Mode from script: {build_up_label}
3. Deck Size Status from script: {deck_size_status}
4. Reported Primary Strategy from script: {reported_primary_strategy}
5. Reported Secondary Strategy from script: {reported_secondary_strategy}
6. Strategy Confidence from script: {strategy_confidence}
7. Collection/Card Pool File from script: {COLLECTION_FILE if COLLECTION_FILE else 'None loaded'}
8. Collection/Card Pool Status from script: {collection_status_note}
9. Alpha Warning: {alpha_note}

{universal_safety_rules}

Hard build-up rules:
1. This workflow is for adding cards, completing the deck, or building a shell. Do not turn this into a cut review unless the user explicitly asks to rebuild or trim.
2. If the player wants collection-limited additions and no collection/card-pool data is available, say that collection-limited additions require collection data.
3. If Build from Scratch is selected, warn that it is an Alpha feature and ask enough intent questions before suggesting a full shell.
4. Build from Scratch must not pretend to create a perfect final optimized 99-card list. Treat it as an Alpha draft shell requiring human review.
5. Use the uploaded report as evidence, not final truth. User-stated intent overrides the report.
6. Ask exactly one unlocked section per assistant turn, then stop and wait.
7. In the final build-up plan, put the complete Draft XX-Card Addition List directly after the Deck Identity section.
8. The Draft XX-Card Addition List must be easy to copy into deckbuilding sites and should use one card per line in this format: 1x Card Name.
9. If your interface supports downloadable files, provide a downloadable .txt file containing only the final addition list. If not, provide a clean copy/paste text block labeled "addition_list.txt".
10. For Build from Scratch, calculate the exact number of additions needed from the report. Do not assume 98 additions unless the report says the current deck has exactly 2 cards; a single-commander-only list usually needs 99, and partial shells need 100 minus the current deck size.

==================================================
REQUIRED BUILD-UP CONVERSATION LOOP
==================================================

Use this exact workflow:

1. Confirm the deck report is available.
2. Ask Section 1 questions only, then stop and wait.
3. After the user answers Section 1, summarize Section 1, state how you will use it, ask Section 2 questions only, then stop and wait.
4. After the user answers Section 2, summarize Section 2, state how you will use it, ask Section 3 questions only, then stop and wait.
5. After the user answers Section 3, summarize Section 3, state how you will use it, ask Section 4 questions only, then stop and wait.
6. After the user answers Section 4, summarize Section 4, state how you will use it, ask Section 5 questions only, then stop and wait.
7. After the user answers Section 5, summarize Section 5, state how you will use it, produce the Build-Up User Intent Summary, and ask for confirmation unless the user already gave permission to proceed.
8. After confirmation or permission to proceed, give the final build-up recommendations. The final build-up plan must put Deck Identity first, then immediately provide Section 2 — Draft XX-Card Addition List with one card per line formatted as "1x Card Name". If downloadable file creation is supported, create a .txt file containing only that addition list; otherwise provide a clean code block that can be copied into a deckbuilding site.

Absolute output rules:
1. Ask exactly one section per assistant turn.
2. After asking a section, stop.
3. Do not display future sections.
4. Do not give final additions, full decklists, replacements, or cuts during intake.
5. Do not ask cut-depth questions unless the user changes the task to cut-down or rebuild.
6. If the user already answered a question, do not ask it again.
7. If a missing detail is not critical, proceed with a labeled assumption.
8. If the user says "proceed with defaults," use defaults and continue.

==================================================
FIRST RESPONSE RULE
==================================================

If no deck report is available, respond only with:

Please upload or paste the generated deck report txt file for this deck. This build-up prompt no longer includes the full report, so I need the report file before I can begin.

Once the report is available, I’ll start with Section 1 — Build-Up Context, then I’ll wait for your answer before moving to Section 2.

If the deck report is available, respond only with Section 1 below and then stop.

==================================================
SECTION 1 — BUILD-UP CONTEXT
==================================================

1. Is the selected build-up mode correct: {build_up_label}?
2. Optional if Question 1 is correct: choose the best build-up mode if this needs changing:
   1. Build from Scratch — I only have the commander. Alpha feature; may not be ready yet.
   2. Point me in the right direction — I need 30+ cards.
   3. Help me get there — I need 11 to 30 cards.
   4. Finalize — I need 10 or fewer cards.
3. Should the current cards be treated as:
   1. A committed shell.
   2. A flexible starting point.
   3. An inspiration pool.
   4. A commander-only concept.

Section 1 default if skipped:
1. Build-Up Mode: Use script-selected mode: {build_up_label}.
2. Existing Cards: Treat current list as a flexible starting point unless it is commander-only.

You can answer briefly, skip unknowns, say "use defaults for this section," or say "proceed with defaults." Defaulting is allowed, but exact additions will be weaker if card pool, playstyle, and power target are unknown.

==================================================
LOCKED LATER SECTIONS — DO NOT DISPLAY UNTIL UNLOCKED
==================================================

When Section 1 is answered or defaulted, summarize it, state how it will guide the build, then ask only Section 2.

Section 2 — Commander Plan / Deck Identity
1. What do you want this commander or deck to do when it is working correctly?
2. Is the reported primary strategy correct: {reported_primary_strategy}? If not, what should it be?
3. Is the reported secondary strategy correct: {reported_secondary_strategy}? If not, what should it be?
4. Are there specific mechanics, themes, packages, or play patterns you want to build around?
5. For Build from Scratch only: describe the desired deck identity in plain language, such as value engine, combat deck, mutate stack, spellslinger, graveyard deck, artifact engine, casual theme deck, optimized shell, or something else.

Section 2 default if skipped:
1. Deck Plan: Use the uploaded report's strategy read as provisional evidence.
2. Primary Strategy: Confirm the reported primary strategy.
3. Secondary Strategy: Confirm the reported secondary strategy.
4. Theme / Package Intent: None provided.

When Section 2 is answered or defaulted, summarize it, state how it will guide the build, then ask only Section 3.

Section 3 — Power / Table / Playstyle Intent
1. What kind of table is this deck meant for: casual, upgraded casual, high-power, optimized, cEDH-adjacent, or something else?
2. Do you want the deck to be more theme-first, synergy-first, consistency-first, power-first, budget-first, or table-friendly?
3. Are infinite combos or near-combos welcome, acceptable but not preferred, or unwanted?
4. Should the deck avoid accidentally becoming stronger than the playgroup expects?
5. What playstyle do you prefer: proactive, reactive, grindy, explosive, combat-focused, engine-focused, political, or something else?

Section 3 default if skipped:
1. Table Intent: Casual / upgraded casual unless the report or user indicates otherwise.
2. Build Priority: Synergy and consistency first.
3. Combo Preference: Unknown; do not add combo-completion cards unless explicitly requested.
4. Playstyle: Use the confirmed commander/deck plan.

When Section 3 is answered or defaulted, summarize it, state how it will guide the build, then ask only Section 4.

Section 4 — Card Pool / Budget / Restrictions
1. Should additions come from:
   1. Full Magic card database.
   2. Collection/card-pool candidates shown in the report.
   3. A separate uploaded/pasted collection file.
   4. Both full card pool and collection, with collection preferred.
   5. Categories only, no exact card names.
2. Are there budget limits, availability limits, pet-card restrictions, or color/theme restrictions?
3. Should the build prioritize:
   1. Synergy.
   2. Consistency.
   3. Lower curve.
   4. Interaction.
   5. Ramp.
   6. Card advantage.
   7. Table friendliness.
   8. Power.
   9. Theme/flavor.
4. Should additions avoid adding or completing combos unless you explicitly want that?

Section 4 default if skipped:
1. Addition Source: Use collection/card-pool candidates if present; otherwise full Magic card database.
2. Budget / Restrictions: Unknown.
3. Build Priority: Synergy, consistency, and role balance.
4. Combo Addition Policy: Avoid adding or completing combos unless explicitly requested.

When Section 4 is answered or defaulted, summarize it, state how it will guide the build, then ask only Section 5.

Section 5 — Desired Build Output
1. What build-up output style do you want?
   1. Directional build plan.
   2. Exact additions list.
   3. Category-only additions.
   4. Prioritized action plan.
   5. Playtest checklist.
   6. Full diagnostic build plan.
   7. Prompt/report suitable for another AI chat.
   8. Downloadable/copy-paste addition list txt.
2. Do you want the final build plan to include a role target, such as number of lands, ramp, draw, removal, protection, synergy pieces, and finishers?
3. Should the final output separate must-add categories, strong suggestions, optional ideas, and playtest notes?

Section 5 default if skipped:
1. Output Style: Prioritized action plan.
2. Role Targets: Yes.
3. Output Sections: Separate must-add categories, strong suggestions, optional ideas, and playtest notes.

==================================================
REQUIRED BUILD-UP USER INTENT SUMMARY BEFORE FINAL BUILD PLAN
==================================================

Before final build-up recommendations, show this section:

Build-Up User Intent Summary
------------------------------
Build-Up Mode:
Current Deck Status:
Cards Needed to Reach 100:
Commander Plan:
Primary Strategy:
Secondary Strategy:
Theme / Package Intent:
Power / Table Intent:
Card Pool Source:
Budget / Availability Limits:
Color / Theme Restrictions:
Protected / Must-Keep Cards:
Cards to Build Around:
Desired Addition Style:
Requested Output Style:
Assumptions / Unknowns:

After showing the Build-Up User Intent Summary, ask:
"Does this summary look right? If yes, I’ll continue to the final build plan. If not, tell me what to correct."

If the user already gave permission to proceed, continue without asking again.

==================================================
FINAL BUILD-UP VALIDATION
==================================================

Before presenting the final build plan, validate:
1. Current deck size from report: {deck_count}.
2. Command-zone cards detected: {command_zone_count}.
3. Required addition list size: exactly {cards_needed_to_100} card(s).
4. Addition list actually provided: count it before finalizing.
5. Total deck size after additions: must be exactly 100.
6. Off-color cards: none.
7. Banned cards: none.
8. Duplicate nonbasic cards: none.
9. Cards already in the deck: none, unless legal duplicate exception applies.
10. Budget/table-intent concerns: identify clearly if any remain.

==================================================
FINAL BUILD-UP RULES
==================================================

1. Underfilled decks are addition-first. Do not create cut pressure unless the user requests rebuild or trim.
2. Build from Scratch is Alpha. Provide a direction and draft shell guidance, not a guaranteed optimized 99-card final list.
3. If exact additions are allowed, every exact card must be color-identity legal and not already in the deck unless a legal duplicate exception applies.
4. If category-only additions are requested, do not name exact cards.
5. If collection-only additions are requested and no collection/card-pool data exists, say collection-only exact additions cannot be made and provide categories instead.
6. If both full card pool and collection are allowed, prefer collection/card-pool candidates when they fit the confirmed plan.
7. Use the uploaded Deck Completion / Addition Review section first, then supplement with color-identity-safe suggestions only if allowed.
8. Respect theme, budget, table intent, and protected/must-keep cards.

Internal final self-check before finalizing:
1. Did I follow the Build-Up User Intent Summary?
2. Did I avoid re-asking questions already answered?
3. Did I respect the requested output style?
4. Did I respect the addition/replacement source preference?
5. Did I avoid exact card names when the user requested categories only?
6. Did I avoid recommendations outside commander color identity?
7. Did I avoid recommending cards already in the deck?
8. Did I avoid cut pressure for underfilled decks unless rebuild was requested?
9. Did I keep bracket pressure separate from legality?
10. Did I avoid making Game Changers automatic cuts?
11. Did I treat combo questions as preference-only, not confirmed combo detection?
12. Did I label assumptions and unknowns?
""".strip()

    return f"""
You are an experienced Magic: The Gathering Commander deck builder helping the deck's pilot make a user-guided deck review.

Prompt version: v0.6.2.6 — Worksheet Guardrail Hotfix
The command zone card(s): {commander_name}

This is the CUT-DOWN / TUNING workflow. The generated deck report is intentionally NOT included in this prompt.

Before beginning the intake, check whether the user has also uploaded or pasted the generated deck report txt file in the current chat.

If the deck report txt file is NOT available:
1. Do not start Section 1 yet.
2. Do not ask review questions yet.
3. Ask the user to upload or paste the generated deck report txt file.
4. Explain that once the report is available, you will begin Section 1 and proceed one section at a time.
5. Then stop.

If the deck report txt file IS available:
1. Read the report enough to identify commander, color identity, deck size, reported primary strategy, reported secondary strategy, cut pressure, replacement candidates, collection/card-pool status, and protected/core-card warnings.
2. Begin Section 1 only.
3. Stop and wait for the user's Section 1 answer.

Script context, for defaults only:
1. Review Direction from script: Cut down / tune.
2. Cut Depth Mode from script: {CUT_DEPTH_CONFIG.get('mode', 'normal')}.
3. Optional Cut Target from script: {CUT_DEPTH_CONFIG.get('optional_cut_target', 5)}.
4. Deck Size Status from script: {deck_size_status}.
5. Reported Primary Strategy from script: {reported_primary_strategy}.
6. Reported Secondary Strategy from script: {reported_secondary_strategy}.
7. Strategy Confidence from script: {strategy_confidence}.
8. Collection/Card Pool File from script: {COLLECTION_FILE if COLLECTION_FILE else 'None loaded'}.
9. Collection/Card Pool Status from script: {collection_status_note}.

{universal_safety_rules}

==================================================
REQUIRED CUT-DOWN CONVERSATION LOOP
==================================================

Use this exact workflow:

1. Confirm the deck report is available.
2. Ask Section 1 questions only, then stop and wait.
3. After the user answers Section 1, summarize Section 1, state how you will use it, ask Section 2 questions only, then stop and wait.
4. After the user answers Section 2, summarize Section 2, state how you will use it, ask Section 3 questions only, then stop and wait.
5. After the user answers Section 3, summarize Section 3, state how you will use it, ask Section 4 questions only, then stop and wait.
6. After the user answers Section 4, summarize Section 4, state how you will use it, ask Section 5 questions only, then stop and wait.
7. After the user answers Section 5, summarize Section 5, state how you will use it, ask Section 6 questions only, then stop and wait.
8. After the user answers Section 6, summarize Section 6, state how you will use it, ask Section 7 questions only, then stop and wait.
9. After the user answers Section 7, summarize Section 7, state how you will use it, then either ask a short Section 8 only if a critical contradiction remains or produce the User Intent Summary.
10. After showing the User Intent Summary, ask for confirmation unless the user already gave permission to proceed.
11. After confirmation or permission to proceed, give the final review.

Absolute output rules:
1. Ask exactly one section per assistant turn.
2. After asking a section, stop.
3. Do not display future sections.
4. Do not give final cuts, additions, or replacements during intake.
5. Do not ask future sections early.
6. If the user already answered a question, do not ask it again.
7. If a missing detail is not critical, proceed with a labeled assumption.
8. If the user says "proceed with defaults," use defaults and continue.

==================================================
FIRST RESPONSE RULE
==================================================

If no deck report is available, respond only with:

Please upload or paste the generated deck report txt file for this deck. This user-guided review prompt no longer includes the full report, so I need the report file before I can begin.

Once the report is available, I’ll start with Section 1 — Main Review Goal, then I’ll wait for your answer before moving to Section 2.

If the deck report is available, respond only with Section 1 below and then stop.

==================================================
SECTION 1 — MAIN REVIEW GOAL
==================================================

1. What is your main review goal? Choose one or more:
   1. Get the deck down to a legal 100-card list.
   2. Optimize an already legal 100-card deck.
   3. Improve strategy focus.
   4. Improve mana curve.
   5. Improve ramp/draw/removal balance.
   6. Tune for a target power level.
   7. General full review.
   8. Cut-only review.
   9. Replacement-focused review.
   10. Playtest-focused review.
   11. Mana base review.
   12. Strategy/synergy review.
   13. Batch QA / bug-finding review.
   14. Build / complete deck to 100, if the uploaded report shows the deck is underfilled.

Section 1 default if skipped:
1. Review Goal: General full review.

You can answer briefly, skip unknowns, say "use defaults for this section," or say "proceed with defaults." Defaulting is allowed, but the review will be less accurate if deck intent, protected cards, replacement limits, and table expectations are unknown.

==================================================
LOCKED LATER SECTIONS — DO NOT DISPLAY UNTIL UNLOCKED
==================================================

When Section 1 is answered or defaulted, summarize it, state how it will guide the review, then ask only Section 2.

Section 2 — Deck Plan
1. What is the deck supposed to do when it is working correctly?
2. What is the ideal play pattern?
3. Is the reported primary strategy correct: {reported_primary_strategy}? If not, what should the primary strategy be?
4. Is the reported secondary strategy correct: {reported_secondary_strategy}? If not, what should the secondary strategy be?
5. What is the theme, if there is one? Note: it is okay if there is no theme beyond the deck's strategy.
6. What cards, packages, or play patterns matter most to the deck's identity?

Section 2 default if skipped:
1. Deck Plan: Use the uploaded report's strategy read as provisional evidence.
2. Primary Strategy: Confirm the reported primary strategy.
3. Secondary Strategy: Confirm the reported secondary strategy.
4. Theme / Package Intent: None provided.

When Section 2 is answered or defaulted, summarize it, state how it will guide the review, then ask only Section 3.

Section 3 — Commander Role
1. What role should the commander play?
   1. Main engine.
   2. Finisher.
   3. Value piece.
   4. Support piece.
   5. Color identity only.
   6. Not sure.

Section 3 default if skipped:
1. Commander Role: Main engine if commander support is high in the uploaded report; otherwise Not sure.

When Section 3 is answered or defaulted, summarize it, state how it will guide the review, then ask only Section 4.

Section 4 — Protected / Pet / Build-Around Intent
Heads up: this section asks the same topic in two forms on purpose. Question 1 is the plain-language answer. Question 2 is the copy/paste structure that turns your answer into clear review constraints.
1. Are there any cards, packages, or play patterns that are emotionally or strategically important to keep, including pet cards, theme cards, political cards, or local-meta cards that should not be cut unless absolutely necessary?
2. If the answer above is yes, copy/paste and fill out any fields that matter. If the answer is no, write "not applicable" and these fields will be treated as blank:
   1. Cards you refuse to cut:
   2. Pet cards you want protected:
   3. Cards you want to build around:
   4. Cards you are uncertain about:
   5. Cards you specifically want reviewed:

Section 4 default if skipped:
1. Protected Cards: None provided.
2. Cards to Build Around: Commander and strategy-defining cards from the uploaded report only.
3. Cards Specifically Requested for Review: None.

When Section 4 is answered or defaulted, summarize it, state how it will guide the review, then ask only Section 5.

Section 5 — Power / Bracket / Table Intent Questions
1. What kind of table is this deck meant for: casual, upgraded casual, high-power, optimized, cEDH-adjacent, or something else?
2. Should Game Changers, fast mana, tutors, free interaction, stax, mass land denial, or salt-risk cards be reduced for table fit?
3. Should bracket pressure be treated as a real possible cut reason, or only as a pregame conversation note?
4. Are infinite combos or near-combos welcome, acceptable but not preferred, or unwanted?
5. Should the deck avoid accidentally becoming stronger than the playgroup expects?

Section 5 default if skipped:
1. Table Intent: Use the uploaded report's bracket/power read as context only.
2. Bracket Pressure: Pregame conversation note only, not an automatic cut reason.
3. Game Changers: Not automatic cuts.
4. Combo Preference: Unknown; do not add or complete combos unless explicitly requested.
5. Power Drift: Avoid making the deck stronger than the pilot's stated goal.

When Section 5 is answered or defaulted, summarize it, state how it will guide the review, then ask only Section 6.

Section 6 — Cut Philosophy Questions
1. How aggressive should the cuts be?
   1. Light — only obvious issues, illegal cards, severe off-plan cards, and very low-fit cards.
   2. Normal — practical tuning, reasonable cut candidates, protects synergy cards.
   3. Strict — more willing to pressure redundant, off-plan, low-impact, or replaceable cards, but still protects core engine cards.
   4. Brutal — useful for large card pools or very overfilled decks; focuses on reaching a functional 100-card shell; still explains replaceability.
   5. Rebuild — treats the list as a rough card pool and rebuilds toward the stated plan; does not pretend the list is a finished deck.
   6. Custom.
2. Are you trying to make required cuts to reach 100, optimize a legal 100-card deck, or rebuild the deck more heavily?
3. Should low-confidence possible cuts be shown, or only stronger candidates?
4. Should interaction, ramp, and card draw be protected unless clearly overrepresented?
5. Should the final answer separate Recommended Cuts, Possible Cuts, Playtest Before Cutting, Manual Review, and Protected Cards?

Section 6 default if skipped:
1. Cut Aggression: Use script cut-depth mode: {CUT_DEPTH_CONFIG.get('mode', 'normal')}.
2. Deck Size Context: Use the uploaded report's deck-size status.
3. Low Confidence Cuts: Show only if strict/brutal/rebuild mode or useful as manual review.
4. Protect Ramp/Draw/Interaction: Yes, unless clearly overrepresented or off-plan.
5. Final Cut Categories: Separate recommended, possible, playtest-first, manual review, and protected cards.

When Section 6 is answered or defaulted, summarize it, state how it will guide the review, then ask only Section 7.

Section 7 — Replacement Philosophy and Output Questions
1. What replacement style do you want?
   1. No replacements.
   2. Replacement categories only.
   3. Exact replacement cards only when obvious.
   4. Exact replacement cards welcome.
   5. Exact replacements only from my collection/card pool.
   6. Replacement suggestions later.
2. Should exact replacement or addition suggestions assume:
   1. Full Magic card pool.
   2. Collection/card-pool candidates shown in the uploaded report.
   3. A separate uploaded/pasted collection file.
   4. Both full card pool and collection, with collection preferred.
3. Are there budget limits, availability limits, pet-card restrictions, or color/theme restrictions?
4. Should replacements prioritize synergy, lower curve, more interaction, more consistency, table friendliness, or power?
5. Should replacements avoid adding or completing combos unless you explicitly want that?
6. If the deck is underfilled, should additions come from the full Magic card pool, your collection/card-pool, or both? If you are only cutting down an overfilled deck, answer N/A.
7. What final output style do you want?
   1. Short prioritized cut list.
   2. Full diagnostic report.
   3. Strategy-focused review.
   4. Cut-only review.
   5. Replacement-focused review.
   6. Playtest notes.
   7. Prompt/report suitable for another AI chat.
   8. Batch QA / bug-finding review.

Section 7 replacement behavior rules:
1. If the user chooses no replacements, do not include replacement suggestions.
2. If the user chooses replacement categories only, do not name exact cards. Suggest only categories like more ramp, lower curve, more protection, more commander synergy, etc.
3. If the user chooses exact replacement cards only when obvious, suggest exact cards only when color identity, strategy fit, deck role, and replacement reason are clear.
4. If the user chooses exact replacement cards welcome, exact suggestions are allowed, but they still must obey color identity, deck plan, budget, and duplicate-card rules.
5. If the user chooses exact replacements only from collection/card pool, only use cards shown in the collection/card-pool candidate section of the report or a provided collection file. If no collection/card-pool data exists, state that exact collection-only suggestions cannot be made and provide categories instead.
6. If the user chooses replacement suggestions later, do not include replacements in the current final review.

Section 7 output style behavior rules:
1. If short prioritized cut list, keep final answer concise and ranked.
2. If full diagnostic report, include strategy, synergy, cuts, protected cards, replacement needs, playtest notes, and assumptions.
3. If strategy-focused review, prioritize primary/secondary strategy, commander support, synergy packages, off-plan cards, and plan-fit cards.
4. If cut-only review, focus on recommended cuts, possible cuts, manual review, playtest-before-cutting, and protected cards. Keep replacement discussion minimal or omit it based on replacement preference.
5. If replacement-focused review, emphasize replacement categories or exact replacements according to the user's replacement preference.
6. If playtest notes, focus on what the pilot should observe in games: mana, pacing, dead cards, overperformers, underperformers, win conditions, protection needs, and table-fit concerns.
7. If prompt/report suitable for another AI chat, use clean copy/paste formatting with clear headings and avoid relying on hidden context.
8. If batch QA / bug-finding review, do not treat merged files as one deck. Look for repeated patterns, bugs, false positives, false negatives, overflagging, underflagging, prompt issues, and report inconsistencies across multiple reports.

Section 7 default if skipped:
1. Replacement Mode: Replacement categories first; exact cards only when obvious and safe.
2. Card Pool: Use collection/card-pool candidates if they appear in the uploaded report; otherwise use the full Magic card pool.
3. Budget / Availability: Unknown.
4. Replacement Priority: Strategy fit, role balance, lower curve where needed, and table friendliness.
5. Combo Replacement Policy: Avoid adding or completing combos unless the user explicitly wants that.
6. Addition Source for Underfilled Decks: Both full Magic card pool and collection/card-pool candidates when available.
7. Output Style: Full diagnostic report.

After Section 7 is answered or defaulted, summarize it and then either ask Section 8 only if there is a critical contradiction, or produce the User Intent Summary.

Optional Section 8 — Final Clarification, only if needed
Use only one to three questions, and only when a missing answer would materially change the review.

==================================================
REQUIRED USER INTENT SUMMARY BEFORE FINAL REVIEW
==================================================

Before final recommendations, show this section:

User Intent Summary
------------------------------
Review Goal:
Deck Plan:
Commander Role:
Primary Strategy:
Secondary Strategy:
Theme / Package Intent:
Cut Depth:
Deck Size Status:
Power / Table Intent:
Replacement Preference:
Collection / Card Pool Restriction:
Cards Refused for Cuts:
Pet Cards / Protected Cards:
Cards to Build Around:
Cards User Is Uncertain About:
Cards Specifically Requested for Review:
Requested Output Style:
Assumptions / Unknowns:

After showing the User Intent Summary, ask:
"Does this summary look right? If yes, I’ll continue to the final review. If not, tell me what to correct."

If the user already gave permission to proceed, continue without asking again.

==================================================
FINAL REVIEW RULES
==================================================

1. Over 100 cards: required_cuts = max(0, deck_card_count - 100). Required cuts are mandatory, required cuts and optional cuts must be separated, and the review should prioritize reaching 100.
2. Exactly 100 cards: required_cuts = 0. No mandatory cuts. Optional optimization cuts are allowed only if requested or useful.
3. Under 100 cards: no cut pressure unless rebuilding. Focus on additions, role gaps, shell completion, and construction needs.
4. Large card pool / inspiration pool: treat as trimming/building exercise, not a finished legal deck. Brutal or rebuild mode may be appropriate.
5. Do not put user-protected cards in normal recommended cuts.
6. If a protected card has a real issue, place it in a separate protected concern section.
7. Do not call cards bad just because they are low-power, narrow, political, fringe, unusual, or not part of a stock archetype.
8. Do not cut removal, ramp, or draw just because they are not synergy pieces. Interaction is important in most Commander decks unless the user says otherwise.
9. A cut recommendation is a review aid, not a final verdict. State clearly that the player makes the final decision and that this tool is meant to reach a playable 70% solution before human tuning.
9. If the report's strategy read conflicts with the player's intent, use the player's intent as the primary lens and explain the difference.
10. Target power level is preference context only in v0.6.
11. Do not enforce brackets, treat Game Changers as automatic cuts, or treat bracket pressure as a legality failure.
12. Banned cards and Game Changers are distinct.
13. Power-level notes do not override strategy/cut logic unless the user explicitly asks to tune down or tune up for table fit.
14. For Batch QA / bug-finding review, do not analyze merged files as one deck. Identify repeated issues across reports: overflagging, underflagging, overfiring, aggressive vs non-aggressive behavior, noisy tags, functionally overpresent tags, logic that should stay isolated, prompt compliance issues, import/legality issues, and replacement/card-pool issues.

Internal final self-check before finalizing:
1. Did I follow the User Intent Summary?
2. Did I avoid re-asking questions already answered?
3. Did I respect the requested output style?
4. Did I respect replacement preference?
5. Did I avoid exact card names when the user requested categories only?
6. Did I avoid recommendations outside commander color identity?
7. Did I avoid recommending cards already in the deck?
8. Did I separate required cuts from optional optimization cuts?
9. Did I avoid cut pressure for underfilled decks unless rebuild was requested?
10. Did I protect refused/pet/build-around cards from normal cut pressure?
11. Did I keep bracket pressure separate from legality?
12. Did I avoid making Game Changers automatic cuts?
13. Did I treat combo questions as preference-only, not confirmed combo detection?
14. Did I label assumptions and unknowns?
15. Did I make clear that recommendations are a 70% solution and the player makes the final decisions?
16. Did I avoid over-cutting interaction/removal unless the user or deck context justified it?
""".strip()

def extract_sections_by_headings(full_text, heading_groups):
    """Extract report sections using current or legacy headings."""
    lines = full_text.splitlines()
    results = []

    def find_heading(candidates):
        for candidate in candidates:
            c = str(candidate).strip().lower()
            for idx, line in enumerate(lines):
                stripped = line.strip().lower()
                if stripped == c or stripped.startswith(c) or c in stripped:
                    return idx
        return None

    def section_bounds(idx):
        start = idx
        if idx > 0 and set(lines[idx - 1].strip()) == {"="}:
            start = idx - 1
        end = len(lines)
        for j in range(idx + 1, len(lines)):
            stripped = lines[j].strip()
            if set(stripped) == {"="} and j + 1 < len(lines):
                end = j
                break
            if re.match(r"^\d+[A-Z]?\.\s+", stripped) and j != idx:
                end = j - 1 if j > 0 and set(lines[j - 1].strip()) == {"="} else j
                break
        return start, end

    for group in heading_groups:
        candidates = group if isinstance(group, (list, tuple)) else [group]
        idx = find_heading(candidates)
        if idx is None:
            results.append("No matching section found.\nHeadings tried:\n" + "\n".join(f"- {h}" for h in candidates))
            continue
        start, end = section_bounds(idx)
        results.append("\n".join(lines[start:end]).strip())
    return "\n\n".join(part for part in results if part).strip()


def section_between(text, start_label, end_labels):
    return extract_sections_by_headings(text, [[start_label]])


def build_debug_sections_v057(report_text, prompt_text):
    legality = "\n".join(["v0.6.2.6 Legality Report", "", extract_sections_by_headings(report_text, [
        ["1. Deck Import Summary"], ["1B. Input Hygiene", "1. Input Hygiene"], ["2. Commander Identification", "Commander Identification"],
        ["3. Card Validation"], ["4. Commander Legality Check", "Commander Legality Check"], ["5. Deck Math"],
        ["6. Card Type Breakdown"], ["8. Manual Category / Type Mismatches", "Manual Category / Type Mismatches"],
    ])])
    strategy = "\n".join(["v0.6.2.6 Strategy Report", "", extract_sections_by_headings(report_text, [
        ["9. Card Role Tag Summary", "Card Role Tag Summary"],
        ["10. Strategy Read", "Strategy Read"],
        ["11. Archetype Score Summary", "Archetype Score Summary"],
        ["12. Core Synergy Packages", "Core Synergy Packages"],
        ["13. Card Plan Fit", "Card Plan Fit"],
        ["v0.5.8 Developer Diagnostics Summary", "v0.5.7 Developer Diagnostics Summary", "Developer Diagnostics Summary"],
    ])])
    bracket = "\n".join(["v0.6.2.6 Bracket Report", "Bracket pressure is a power/table-fit modifier, not a primary strategy label and not an automatic cut reason.", "", extract_sections_by_headings(report_text, [
        ["10B. Bracket Read", "Bracket Read"],
    ])])
    cut_pressure = "\n".join(["v0.6.2.6 Cut Pressure Report", f"Cut Depth Mode: {CUT_DEPTH_CONFIG.get('mode', 'normal')}", f"Optional Cut Target: {CUT_DEPTH_CONFIG.get('optional_cut_target', 5)}", "", extract_sections_by_headings(report_text, [
        ["14. Cut Pressure Review", "Cut Pressure Review"],
        ["15. Possible Cut Review", "Possible Cut Review"],
        ["15A. Deck Completion / Addition Review", "Deck Completion / Addition Review"],
        ["15B. Collection / Card Pool Replacement Candidates", "Collection / Card Pool Replacement Candidates"],
        ["v0.5.8 Developer Diagnostics Summary", "v0.5.7 Developer Diagnostics Summary", "Developer Diagnostics Summary"],
    ])])
    replacement = "\n".join(["v0.6.2.6 User-Guided Review Prompt", "Replacement suggestions should be role/category based unless exact replacement safety is clear.", "Collection-aware instruction: when collection/card-pool data exists and the player wants collection-limited replacements, prefer those candidates first.", "", prompt_text])
    diag_lines = ["v0.6.2.6 Diagnostics", "Raw role tag counts:", str(role_tag_counts), "", "Raw type tag counts:", str(type_tag_counts), "", "Archetype scores after suppression:"]
    for name, data in sorted([(k,v) for k,v in archetype_scores.items() if not str(k).startswith('__')], key=lambda item: final_score_v057v4(item[1]), reverse=True)[:25]:
        _raw_score = data.get('raw_score', data.get('score', 0))
        _pre_final = data.get('pre_final_adjusted_score', data.get('adjusted_score', data.get('score', 0)))
        _final = final_score_v057v4(data)
        _reason = clean_reason_text(data.get('suppression_reason', '') or data.get('gate_failed_reason', ''))
        diag_lines.append(f"- {name}:")
        diag_lines.append(f"  raw_score={_raw_score}")
        diag_lines.append(f"  pre_final_adjusted_score={_pre_final}")
        diag_lines.append(f"  final_score={_final}")
        diag_lines.append(f"  gate_passed={data.get('gate_passed', True)}")
        diag_lines.append(f"  reason={_reason if _reason else 'None'}")
    diag_lines.extend(["", "Commander tag detection:", str(get_commander_role_tag_counter(commander_cards_scryfall)), "", "Filtered attribute relevance samples:"])
    for item in attribute_relevance_v057[:80]:
        diag_lines.append(f"Card: {item['card_name']}")
        diag_lines.append(f"  Raw attributes: {', '.join(item['raw']) if item['raw'] else 'None'}")
        diag_lines.append(f"  Relevant attributes used: {', '.join(item['relevant']) if item['relevant'] else 'None'}")
        if item['ignored']:
            diag_lines.append("  Ignored attributes:")
            for tag, reason in item['ignored'][:5]:
                diag_lines.append(f"    - {tag}: {reason}")
        if item['manual_review']:
            diag_lines.append(f"  Manual review: {', '.join(item['manual_review'])}")
    diag_lines.extend(["", "Role balance warnings:", str(possible_cut_review.get('diagnostic_warnings', [])), "", "Cut candidate distribution by role:", str(possible_cut_review.get('cut_candidate_distribution_by_role', 'Not recorded')), "", "Strategy confidence calculation notes:", str(confidence_warnings_v057 if 'confidence_warnings_v057' in globals() else []), "", "Manual-review triggers:", str([item for item in attribute_relevance_v057 if item.get('manual_review')][:20]), "", "Fallback logic used:", str(possible_cut_review.get('target_shortfall_note', 'None'))])
    return [legality, strategy, bracket, cut_pressure, replacement, "\n".join(diag_lines)]


prompt_text = make_cut_replacement_prompt_v057(normal_report_text)
prompt_kind = "build_up_review_prompt" if REVIEW_DIRECTION == "build_up" else "user_guided_review_prompt"
prompt_debug_name = "build_up_review_prompt" if REVIEW_DIRECTION == "build_up" else "user_guided_review_prompt"

OUTPUT_FOLDER.mkdir(exist_ok=True)
written_files = []
base_deck_name_raw = safe_commander_name if safe_commander_name and safe_commander_name != "Unknown_Commander" else sanitize_filename(DECK_FILE.stem)
base_deck_name = shorten_output_stem(base_deck_name_raw)

try:
    if OUTPUT_MODE == "normal":
        report_file = get_unique_output_path(OUTPUT_FOLDER, f"{base_deck_name}_deck_report")
        prompt_file = get_unique_output_path(OUTPUT_FOLDER, f"{base_deck_name}_{prompt_kind}")
        written_files.append(write_text_file(report_file, normal_report_text))
        written_files.append(write_text_file(prompt_file, prompt_text))
    elif OUTPUT_MODE == "debug":
        deck_folder = create_deck_output_folder(base_deck_name, OUTPUT_FOLDER)
        debug_sections = build_debug_sections_v057(debug_source_report_text, prompt_text)
        names = [
            f"01_{base_deck_name}_legality_report.txt",
            f"02_{base_deck_name}_strategy_report.txt",
            f"03_{base_deck_name}_bracket_report.txt",
            f"04_{base_deck_name}_cut_pressure_report.txt",
            f"05_{base_deck_name}_{prompt_debug_name}.txt",
            f"06_{base_deck_name}_diagnostics.txt",
        ]
        debug_paths = [write_text_file(get_unique_output_path(deck_folder, Path(name).stem), content) for name, content in zip(names, debug_sections)]
        written_files.extend(debug_paths)
        written_files.append(merge_debug_reports(deck_folder, base_deck_name, debug_paths))
    else:  # both
        deck_folder = create_deck_output_folder(base_deck_name, OUTPUT_FOLDER)
        normal_folder = deck_folder / "normal"
        debug_folder = deck_folder / "debug"
        report_file = get_unique_output_path(normal_folder, f"{base_deck_name}_deck_report")
        prompt_file = get_unique_output_path(normal_folder, f"{base_deck_name}_{prompt_kind}")
        written_files.append(write_text_file(report_file, normal_report_text))
        written_files.append(write_text_file(prompt_file, prompt_text))
        debug_sections = build_debug_sections_v057(debug_source_report_text, prompt_text)
        names = [
            f"01_{base_deck_name}_legality_report.txt",
            f"02_{base_deck_name}_strategy_report.txt",
            f"03_{base_deck_name}_bracket_report.txt",
            f"04_{base_deck_name}_cut_pressure_report.txt",
            f"05_{base_deck_name}_{prompt_debug_name}.txt",
            f"06_{base_deck_name}_diagnostics.txt",
        ]
        debug_paths = [write_text_file(get_unique_output_path(debug_folder, Path(name).stem), content) for name, content in zip(names, debug_sections)]
        written_files.extend(debug_paths)
        written_files.append(merge_debug_reports(debug_folder, base_deck_name, debug_paths))
except Exception as exc:
    print(f"Output generation failed for {DECK_FILE}: {type(exc).__name__}: {exc}")
    raise

print(normal_report_text)
print()
print("v0.6.2.4 output generation complete.")
print(f"Output mode: {OUTPUT_MODE}")
print(f"Review direction: {REVIEW_DIRECTION}")
if REVIEW_DIRECTION == "build_up":
    print(f"Build-up mode: {BUILD_UP_CONFIG.get('label', 'Not applicable')}")
else:
    print(f"Cut depth mode: {CUT_DEPTH_CONFIG.get('mode', 'normal')} (target {CUT_DEPTH_CONFIG.get('optional_cut_target', 5)})")
for path in written_files:
    print(f"Saved: {path}")
