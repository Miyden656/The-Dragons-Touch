"""Guarded backend runner helpers for The Dragon's Touch desktop UI.

This module is intentionally small and non-visual. It does not start QProcess by
itself and it does not replace main.py. The PySide6 UI still owns guarded
confirmation, process lifetime, signals, messages, and report-viewer handoff.

Locked workflow boundary:
UI staged state -> guarded confirmation -> subprocess/main.py -> CLI input bridge
-> backend output folder -> report detection -> plain-text Report Viewer.
"""

from pathlib import Path


def backend_entrypoint_path(state) -> Path:
    """Resolve the backend entrypoint relative to the staged working directory."""
    return Path(state.backend_working_directory) / state.backend_entrypoint


def guarded_command_preview(state) -> str:
    """Build the visible command preview for the guarded bridge."""
    deck_path = state.selected_deck_path if state.selected_deck_path != "No deck file selected" else "No UI deck selected; main.py may prompt interactively"
    return f'py {state.backend_entrypoint}  # guarded run; MTG_DECK_FILE="{deck_path}"'


def guarded_command_parts(state) -> list[str]:
    """Return the actual guarded command as a list. Never use shell=True."""
    return ["py", state.backend_entrypoint]


def environment_values(state) -> dict[str, str]:
    """Return environment values passed to the guarded main.py process."""
    return {
        "MTG_DECK_FILE": state.selected_deck_path,
        "MTG_BUDGET_NOTE": state.budget_note,
        "MTG_INTENDED_BRACKET": state.intended_bracket,
    }


def trim_process_output(text: str, limit: int = 6000) -> str:
    """Trim captured process output while keeping the most recent text."""
    text = text or ""
    if len(text) <= limit:
        return text
    return text[-limit:] + "\n\n... output truncated to the most recent captured text ..."
