"""No-console launcher for The Dragon's Touch.

Supported v0.7 alpha launch path.
This file is intentionally self-contained so the tester ZIP does not need a
separate Launch_The_Dragons_Touch.py helper file.
"""
from __future__ import annotations

import os
import runpy
import sys
import traceback
from pathlib import Path


def _show_error(message: str) -> None:
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("The Dragon's Touch Launcher Error", message)
        root.destroy()
    except Exception:
        # Last-resort fallback for environments where tkinter is unavailable.
        print(message, file=sys.stderr)


def main() -> int:
    root_dir = Path(__file__).resolve().parent
    ui_script = root_dir / "ui" / "dragons_touch_pyside6_workstation.py"

    if not ui_script.exists():
        _show_error(
            "The desktop UI could not be found.\n\n"
            f"Expected file:\n{ui_script}"
        )
        return 1

    os.chdir(root_dir)
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))

    try:
        runpy.run_path(str(ui_script), run_name="__main__")
    except ModuleNotFoundError as exc:
        if exc.name == "PySide6":
            _show_error(
                "The desktop UI could not be opened because PySide6 is missing.\n\n"
                "Install it from this project folder with:\n\n"
                "python -m pip install PySide6"
            )
        else:
            _show_error(
                "The desktop UI could not be opened because a Python module is missing.\n\n"
                f"Missing module: {exc.name}\n\n"
                "Details:\n" + traceback.format_exc()
            )
        return 1
    except Exception:
        _show_error(
            "The desktop UI could not be opened.\n\n"
            "The launcher did not run deck analysis; this failed while opening the UI.\n\n"
            "Details:\n" + traceback.format_exc()
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
