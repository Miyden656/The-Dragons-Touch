# v0.10.6.2 combo always-on backend cleanup: local combo awareness is always enabled.
"""Guarded backend runner helpers for The Dragon's Touch desktop UI.

This module is intentionally small and non-visual. It does not start QProcess by
itself and it does not replace main.py. The PySide6 UI still owns guarded
confirmation, process lifetime, signals, messages, and report-viewer handoff.

Locked workflow boundary:
UI staged state -> guarded confirmation -> subprocess/main.py -> CLI input bridge
-> backend output folder -> report detection -> plain-text Report Viewer.
"""

from pathlib import Path


COMBO_AWARENESS_ARTIFACT_BY_MODE = {
    "Always included": "both",
    "Yes": "both",
    "Enabled": "both",
    "Both": "both",
    "both": "both",
}


def backend_entrypoint_path(state) -> Path:
    """Resolve the backend entrypoint relative to the staged working directory."""
    return Path(state.backend_working_directory) / state.backend_entrypoint


def combo_awareness_enabled(state) -> bool:
    """Combo awareness mode is Always included as of v0.10.6.2."""
    return True

def combo_awareness_artifact_value(state) -> str:
    """Always request both combo-aware outputs/artifacts."""
    return "both"

def guarded_command_preview(state) -> str:
    """Build the visible command preview for the guarded bridge."""
    deck_path = state.selected_deck_path if state.selected_deck_path != "No deck file selected" else "No UI deck selected; main.py may prompt interactively"
    combo_note = "combo awareness always included"
    if combo_awareness_enabled(state):
        combo_note = f"combo awareness={combo_awareness_artifact_value(state)}"
    return f'py {state.backend_entrypoint}  # guarded run; MTG_DECK_FILE="{deck_path}"; {combo_note}'


def guarded_command_parts(state) -> list[str]:
    """Return the actual guarded command as a list. Never use shell=True."""
    return ["py", state.backend_entrypoint]


def environment_values(state) -> dict[str, str]:
    """Return environment values passed to the guarded main.py process."""
    values = {
        "MTG_DECK_FILE": state.selected_deck_path,
        "MTG_BUDGET_NOTE": state.budget_note,
        "MTG_INTENDED_BRACKET": state.intended_bracket,
        "MTG_COMBO_AWARENESS_ENABLED": "1" if combo_awareness_enabled(state) else "0",
        "MTG_COMBO_AWARENESS_ARTIFACT": combo_awareness_artifact_value(state),
        # Pilot-intent intake (from the per-guide windows). Lists are pipe-delimited
        # because card names contain commas (e.g. "Krenko, Mob Boss"). config.py reads
        # these back via _env_pipe_list into the RuntimeConfig intent fields.
        "MTG_PET_CARDS": "|".join(getattr(state, "pet_cards", None) or []),
        "MTG_DECLARED_CONSTRAINTS": getattr(state, "declared_constraints", "") or "",
        "MTG_RESCUE_CARDS": "|".join(getattr(state, "rescue_cards", None) or []),
        "MTG_HYBRID_THEMES": "|".join(getattr(state, "hybrid_themes", None) or []),
        "MTG_THEME_INTENT": getattr(state, "theme_intent", "") or "",
    }
    return values


def trim_process_output(text: str, limit: int = 6000) -> str:
    """Trim captured process output while keeping the most recent text."""
    text = text or ""
    if len(text) <= limit:
        return text
    return text[-limit:] + "\n\n... output truncated to the most recent captured text ..."

def combo_artifact_input_value(state) -> str:
    """Compatibility alias: always request both combo-aware outputs/artifacts."""
    return "both"
