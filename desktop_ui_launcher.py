#!/usr/bin/env python3
"""Desktop UI launcher for The Dragon's Touch beta EXE.

This launcher exists so the packaged EXE starts at the PySide6 workstation UI
instead of the backend/main.py deck-selection flow.
"""

from __future__ import annotations

from pathlib import Path
import runpy
import sys
import traceback


# PyInstaller visibility imports.
# These imports make PyInstaller collect PySide6 even though the real UI is
# launched dynamically through runpy.
try:
    from PySide6.QtCore import Qt  # noqa: F401
    from PySide6.QtGui import QIcon  # noqa: F401
    from PySide6.QtWidgets import QApplication  # noqa: F401
except Exception:
    # Source environments without PySide6 should still produce a clear runtime
    # error from the UI launcher rather than failing while importing this file.
    pass

def runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def main() -> int:
    root = runtime_root()
    ui_script = root / "ui" / "dragons_touch_pyside6_workstation.py"

    if not ui_script.exists():
        source_fallback = Path(__file__).resolve().parent / "ui" / "dragons_touch_pyside6_workstation.py"
        if source_fallback.exists():
            ui_script = source_fallback

    if not ui_script.exists():
        print("The Dragon's Touch launcher could not find the desktop UI script.")
        print(f"Expected: {ui_script}")
        return 1

    try:
        runpy.run_path(str(ui_script), run_name="__main__")
        return 0
    except Exception:
        print("The Dragon's Touch desktop UI failed to open.")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
