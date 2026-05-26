# v0.10.6.2 combo always-on CLI cleanup: no Disabled combo mode defaults.
"""CLI input bridge helpers for The Dragon's Touch desktop UI.

This module maps staged UI values into the known main.py interactive answers.
It does not run the backend and does not perform deck analysis. It only prepares
stdin text and user-readable bridge summaries for the existing guarded UI path.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CLIInputPayload:
    input_text: str
    sent_summary: str
    input_lines: list[str]
    sent_parts: list[str]


def output_mode_input_value(state) -> str:
    mapping = {"Normal User Mode": "1", "Debug / Stress-Test Mode": "2", "Both": "3"}
    return mapping.get(state.output_mode, "1")


def review_direction_input_value(state) -> str:
    mapping = {"Build up": "1", "Cut down": "2", "Auto batch": "3"}
    return mapping.get(state.review_direction, "2")


def build_up_mode_input_value(state) -> str:
    mapping = {
        "Build from Scratch — Commander(s) only": "1",
        "Point me in the right direction — 30+ cards needed": "2",
        "Help me get there — 11 to 30 cards needed": "3",
        "Finalize — 10 or fewer cards needed": "4",
    }
    if state.build_up_mode in mapping:
        return mapping[state.build_up_mode]
    intensity_fallback = {"Light": "4", "Normal": "3", "Strict": "2", "Brutal / Deep Review": "2", "Rebuild": "1"}
    return intensity_fallback.get(state.cut_depth, "4")


def review_intensity_input_value(state) -> str:
    mapping = {"Light": "1", "Normal": "2", "Strict": "3", "Brutal / Deep Review": "4", "Rebuild": "5"}
    return mapping.get(state.cut_depth, "2")


def prompt_mode_input_value(state) -> str:
    mapping = {"Interactive AI chat": "1", "One-shot worksheet": "2"}
    return mapping.get(state.prompt_mode, "1")


def should_send_prompt_mode_input(state) -> bool:
    return state.review_direction in {"Build up", "Cut down", "Auto batch"}


def philosophy_lens_input_value(state) -> str:
    if state.philosophy_subtype != "None / top-level only":
        return "5"
    mapping = {"Balanced / Unknown": "1", "Timmy / Tammy": "2", "Johnny / Jenny": "3", "Spike": "4"}
    return mapping.get(state.selected_philosophy, "1")


def philosophy_subtype_input_value(state) -> str:
    mapping = {
        "Michael / Michelle — Big Moment": "1",
        "Alexander / Alexandria — Big Creature / Stompy": "2",
        "Benjamin / Bethany — Theme / Vibe": "3",
        "Milo / Mia — Pet Card": "4",
        "William / Willow — Let Me Do My Thing": "5",
        "Aaron / Ariana — Battlecruiser": "6",
        "Brad / Bria — Engine Builder": "7",
        "Kyle / Katie — Commander Exploiter": "8",
        "Elund / Emily — Weird Card Rescuer": "9",
        "Brandon / Brenda — Theme Mechanic Inventor": "10",
        "Clark / Clarissa — Self-Imposed Constraint Builder": "11",
        "Jasper / Jennifer — Combo Builder": "12",
        "Avery — Consistency Maximizer": "13",
        "Jordan — Efficiency Optimizer": "14",
        "River — Curve and Mana Discipline": "15",
        "Charlie — Competitive Closer": "16",
        "Kai — Power-Level Calibrator": "17",
        "Riley — Interaction Controller": "18",
    }
    return mapping.get(state.philosophy_subtype, "")


def should_send_philosophy_subtype_input(state) -> bool:
    return state.philosophy_subtype != "None / top-level only"


def should_send_philosophy_lens_input(state) -> bool:
    return should_send_prompt_mode_input(state)


def guide_presentation_input_value(state) -> str:
    mapping = {"Masculine guide": "1", "Feminine guide": "2", "Either / random": "3", "No named guide, just philosophy labels": "4"}
    return mapping.get(state.guide_presentation, "3")


def should_send_guide_presentation_input(state) -> bool:
    return should_send_philosophy_lens_input(state)


def collection_mode_input_value(state) -> str:
    # v0.10.5.4 keeps the UI user-facing while preserving the existing CLI bridge.
    # Existing backend prompt mapping:
    # 1 = no collection preference, 2 = prefer collection first,
    # 3 = collection only, 4 = collection shakeup.
    mapping = {
        "Collection first, then full card pool": "2",
        "Collection only": "3",
        "Full card pool only": "1",
        "No replacement suggestions": "1",
        # Legacy compatibility:
        "No collection": "1",
        "Prefer collection first": "2",
        "Collection shakeup": "4",
    }
    return mapping.get(state.collection_mode, "2")


def should_send_collection_mode_input(state) -> bool:
    return should_send_guide_presentation_input(state)


def collection_source_input_value(state) -> str:
    mapping = {"Entire collection folder": "1", "Select collection files": "2"}
    return mapping.get(state.collection_source_mode, "1")


def should_send_collection_source_input(state) -> bool:
    collection_disabled = state.collection_mode in {"No collection", "Full card pool only", "No replacement suggestions"}
    return should_send_collection_mode_input(state) and not collection_disabled


def collection_source_detail_answered(state) -> bool:
    if state.collection_mode in {"No collection", "Full card pool only", "No replacement suggestions"}:
        return True
    if state.collection_source_mode == "Entire collection folder":
        return bool(str(state.collection_folder).strip())
    if state.collection_source_mode == "Select collection files":
        return bool(state.selected_collection_files)
    return False


def collection_source_detail_preview_text(state) -> str:
    if state.collection_mode in {"No collection", "Full card pool only", "No replacement suggestions"}:
        return "not required because Collection Mode is No collection"
    if state.collection_source_mode == "Entire collection folder":
        folder = str(state.collection_folder).strip() or "not staged"
        return f"folder={folder}; txt_count_preview={state.collection_txt_file_count}"
    if state.collection_source_mode == "Select collection files":
        if not state.selected_collection_files:
            return "selected_files=0; no file payload staged"
        examples = "; ".join(Path(path).name for path in state.selected_collection_files[:3])
        if len(state.selected_collection_files) > 3:
            examples += f"; ...and {len(state.selected_collection_files) - 3} more"
        return f"selected_files={len(state.selected_collection_files)}; examples={examples}"
    return "unknown collection source mode"


def build_cli_input_payload(state) -> CLIInputPayload:
    input_lines: list[str] = []
    sent_parts: list[str] = []
    if state.selected_deck_path != "No deck file selected":
        sent_parts.append(f"handed selected deck to main.py via MTG_DECK_FILE: {state.selected_deck_path}")
    combo_mode = getattr(state, "combo_awareness_mode", "Always included")
    sent_parts.append(f"combo awareness environment handoff staged by QProcess: {combo_mode}")
    output_value = output_mode_input_value(state)
    input_lines.append(output_value)
    sent_parts.append(f"sent output-mode answer {output_value} for UI Output Mode: {state.output_mode}")
    direction_value = review_direction_input_value(state)
    input_lines.append(direction_value)
    sent_parts.append(f"sent review-direction answer {direction_value} for UI Review Direction: {state.review_direction}")
    if state.review_direction == "Build up":
        build_up_value = build_up_mode_input_value(state)
        input_lines.append(build_up_value)
        sent_parts.append(f"sent build-up-mode answer {build_up_value} for UI Build-Up Mode: {state.build_up_mode}")
    elif state.review_direction in {"Cut down", "Auto batch"}:
        intensity_value = review_intensity_input_value(state)
        input_lines.append(intensity_value)
        sent_parts.append(f"sent review-intensity/cut-strictness answer {intensity_value} for UI Review Intensity: {state.cut_depth}")
    else:
        sent_parts.append("no mode-specific answer sent because Review Direction was not recognized")
    if should_send_prompt_mode_input(state):
        prompt_value = prompt_mode_input_value(state)
        input_lines.append(prompt_value)
        sent_parts.append(f"sent prompt-mode answer {prompt_value} for UI Prompt Mode: {state.prompt_mode}")
    else:
        sent_parts.append("prompt-mode answer not sent until prior prompts are mapped for this review direction")
    if should_send_philosophy_lens_input(state):
        philosophy_value = philosophy_lens_input_value(state)
        input_lines.append(philosophy_value)
        sent_parts.append(f"sent philosophy-lens answer {philosophy_value} for UI Philosophy Lens: {state.selected_philosophy}")
        if should_send_philosophy_subtype_input(state):
            subtype_value = philosophy_subtype_input_value(state)
            if subtype_value:
                input_lines.append(subtype_value)
                sent_parts.append(f"sent philosophy-subtype answer {subtype_value} for UI Philosophy Subtype: {state.philosophy_subtype}")
            else:
                sent_parts.append(f"philosophy-subtype answer not sent because subtype mapping was unavailable for: {state.philosophy_subtype}")
    else:
        sent_parts.append("philosophy-lens answer not sent until prompt mode is safely bridged for this direction")
    if should_send_guide_presentation_input(state):
        guide_value = guide_presentation_input_value(state)
        input_lines.append(guide_value)
        sent_parts.append(f"sent guide-presentation answer {guide_value} for UI Guide Presentation: {state.guide_presentation}")
    else:
        sent_parts.append("guide-presentation answer not sent until philosophy lens is safely bridged")
    if should_send_collection_mode_input(state):
        collection_value = collection_mode_input_value(state)
        input_lines.append(collection_value)
        sent_parts.append(f"sent collection-mode answer {collection_value} for UI Collection Mode: {state.collection_mode}")
    else:
        sent_parts.append("collection-mode answer not sent until guide presentation is safely bridged")
    if should_send_collection_source_input(state):
        collection_source_value = collection_source_input_value(state)
        input_lines.append(collection_source_value)
        sent_parts.append(f"sent collection-source answer {collection_source_value} for UI Collection Source: {state.collection_source_mode}")
        if state.collection_source_mode == "Entire collection folder":
            sent_parts.append(f"using entire collection folder detail: {state.collection_folder}; selected-file payload not sent")
        elif state.collection_source_mode == "Select collection files" and state.selected_collection_files:
            file_payload = ";".join(str(Path(path)) for path in state.selected_collection_files)
            input_lines.append(file_payload)
            sent_parts.append(f"sent selected-collection-file path payload for {len(state.selected_collection_files)} file(s)")
        elif state.collection_source_mode == "Select collection files":
            sent_parts.append("selected collection files source was active but no files were staged; no file payload sent")
    else:
        sent_parts.append("collection-source answer not sent because collection mode is No collection or not safely bridged yet")
    return CLIInputPayload(input_text="\n".join(input_lines) + "\n", sent_summary="; ".join(sent_parts), input_lines=input_lines, sent_parts=sent_parts)


def cli_input_bridge_preview_text(state) -> str:
    build_up_answer = build_up_mode_input_value(state) if state.review_direction == "Build up" else "not sent unless Review Direction is Build up"
    cut_depth_answer = review_intensity_input_value(state) if state.review_direction in {"Cut down", "Auto batch"} else "not sent unless Review Direction is Cut down or Auto batch"
    prompt_mode_answer = prompt_mode_input_value(state) if should_send_prompt_mode_input(state) else "not sent until prior prompts are mapped for this review direction"
    philosophy_answer = philosophy_lens_input_value(state) if should_send_philosophy_lens_input(state) else "not sent until prompt mode is safely bridged"
    subtype_answer = philosophy_subtype_input_value(state) if should_send_philosophy_subtype_input(state) else "not sent unless Specific philosophy subtype is selected"
    guide_answer = guide_presentation_input_value(state) if should_send_guide_presentation_input(state) else "not sent until philosophy lens is safely bridged"
    collection_answer = collection_mode_input_value(state) if should_send_collection_mode_input(state) else "not sent until guide presentation is safely bridged"
    collection_source_answer = collection_source_input_value(state) if should_send_collection_source_input(state) else "not sent unless collection mode is enabled and safely bridged"
    selected_file_preview = "None selected"
    if state.selected_collection_files:
        selected_file_preview = "; ".join(str(Path(path)) for path in state.selected_collection_files[:3])
        if len(state.selected_collection_files) > 3:
            selected_file_preview += f"; ...and {len(state.selected_collection_files) - 3} more"
    return (
        "Full CLI Bridge Gap Pass\n"
        "- bridge_scope -> Build-up, Cut-down, Auto-batch defaults, top-level/subtype philosophy, guide presentation, collection mode, and collection source\n"
        "- strategy -> send staged UI answers in the same order main.py asks for them, then capture any unexpected prompt/error\n"
        f"- selected_deck_handoff -> MTG_DECK_FILE={state.selected_deck_path if state.selected_deck_path != 'No deck file selected' else 'not staged'}\n"
        f"- combo_awareness_env_handoff -> {getattr(state, 'combo_awareness_mode', 'Always included')}\n"
        "- known_prompt_1 -> Output mode [1=Normal]:\n"
        f"- ui_output_mode -> {state.output_mode}\n"
        f"- output_mode_stdin_value_to_send -> {output_mode_input_value(state)}\n"
        "- known_prompt_2 -> Review direction [2=Cut down]:\n"
        f"- ui_review_direction -> {state.review_direction}\n"
        f"- review_direction_stdin_value_to_send -> {review_direction_input_value(state)}\n"
        "- mode_specific_prompt_when_build_up -> Build-up mode [4=Finalize]:\n"
        f"- ui_build_up_mode -> {state.build_up_mode}\n"
        f"- build_up_mode_stdin_value_to_send -> {build_up_answer}\n"
        "- mode_specific_prompt_when_cut_down_or_auto_batch -> Review Intensity / Cut Strictness:\n"
        f"- ui_review_intensity -> {state.cut_depth}\n"
        f"- review_intensity_stdin_value_to_send -> {cut_depth_answer}\n"
        "- known_prompt_prompt_mode -> Prompt interaction mode [1=Interactive]:\n"
        f"- ui_prompt_mode -> {state.prompt_mode}\n"
        f"- prompt_mode_stdin_value_to_send -> {prompt_mode_answer}\n"
        f"- prompt_mode_bridge_active_for_this_direction -> {should_send_prompt_mode_input(state)}\n"
        "- known_prompt_philosophy -> Philosophy lens [1=Balanced / Unknown]:\n"
        f"- ui_philosophy_lens -> {state.selected_philosophy}\n"
        f"- ui_philosophy_subtype -> {state.philosophy_subtype}\n"
        f"- philosophy_lens_stdin_value_to_send -> {philosophy_answer}\n"
        f"- philosophy_subtype_stdin_value_to_send -> {subtype_answer}\n"
        f"- philosophy_subtype_bridge_active -> {should_send_philosophy_subtype_input(state)}\n"
        "- known_prompt_guide -> Guide presentation [3=Either/random]:\n"
        f"- ui_guide_presentation -> {state.guide_presentation}\n"
        f"- guide_presentation_stdin_value_to_send -> {guide_answer}\n"
        "- known_prompt_collection_mode -> Collection mode [1=No]:\n"
        f"- ui_collection_mode -> {state.collection_mode}\n"
        f"- collection_mode_stdin_value_to_send -> {collection_answer}\n"
        "- known_prompt_collection_source -> Collection source [1=Entire collection folder]:\n"
        f"- ui_collection_source_mode -> {state.collection_source_mode}\n"
        f"- collection_source_stdin_value_to_send -> {collection_source_answer}\n"
        f"- collection_source_bridge_active_for_this_run -> {should_send_collection_source_input(state)}\n"
        f"- collection_folder_or_file_path_answered -> {collection_source_detail_answered(state)}\n"
        f"- active_collection_source_detail -> {collection_source_detail_preview_text(state)}\n"
        f"- collection_folder_preview -> {state.collection_folder}\n"
        f"- selected_collection_files_preview -> {selected_file_preview}\n"
        "- active_source_payload_rule -> Entire folder uses folder/default backend behavior; selected files sends file payload only when files are staged\n"
        "- selected_file_path_handoff -> best-effort only if backend asks for typed paths; unexpected prompts are captured safely\n"
        "- stdin_closed_after_known_answers -> True\n"
        "- unknown_future_prompts_answered -> False\n"
        "- safety_note -> this patch attempts all known gaps, but still captures surprises instead of hiding them\n"
    )


def combo_awareness_enabled(state) -> bool:
    # v0.10.6.2: Combo awareness is always on / Always included.
    return True

def combo_artifact_input_value(state) -> str:
    # v0.10.6.2: Always request both combo-aware outputs/artifacts.
    return "both"
