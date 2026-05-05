"""Deck file selection helpers."""

from __future__ import annotations

import os
from pathlib import Path


def select_deck_files(initialdir: str = "decklists") -> list[Path]:
    """Open a tkinter file picker and return selected decklist paths."""
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()

    selected_files = filedialog.askopenfilenames(
        title="Select one or more Commander decklist files",
        initialdir=initialdir,
        filetypes=[
            ("Text files", "*.txt"),
            ("All files", "*.*"),
        ],
    )

    root.destroy()

    if not selected_files:
        print("No deck files selected.")
        raise SystemExit(0)

    return [Path(selected_file) for selected_file in selected_files]



def get_deck_files_from_environment() -> list[Path] | None:
    deck_file_from_environment = os.environ.get("MTG_DECK_FILE")
    if deck_file_from_environment:
        return [Path(deck_file_from_environment)]
    return None



def resolve_deck_files() -> list[Path]:
    """Resolve one or more deck files from environment or file picker."""
    env_files = get_deck_files_from_environment()
    if env_files:
        return env_files
    return select_deck_files()
