"""
The Dragon's Touch - Python Launcher
v0.7.7L.1

Primary alpha-access launcher.

This opens the PySide6 desktop UI only. It does not run deck analysis,
does not bypass guarded confirmation, and does not replace main.py.
"""
from __future__ import annotations

import os
import runpy
import sys
import traceback
from pathlib import Path

APP_NAME = "The Dragon's Touch"
UI_RELATIVE_PATH = Path("ui") / "dragons_touch_pyside6_workstation.py"


def _show_message(title: str, message: str) -> None:
    """Show a Windows message box when possible, otherwise print to console."""
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, message, title, 0x10)
    except Exception:
        print(f"{title}\n{'=' * len(title)}\n{message}")
        try:
            input("\nPress Enter to close...")
        except Exception:
            pass


def _project_root() -> Path:
    return Path(__file__).resolve().parent


def _verify_environment(project_root: Path) -> Path | None:
    ui_script = project_root / UI_RELATIVE_PATH
    if not ui_script.exists():
        _show_message(
            f"{APP_NAME} Launcher Error",
            "Could not find the desktop UI script.\n\n"
            f"Expected path:\n{ui_script}\n\n"
            "Make sure this launcher is in the project root folder, beside main.py and the ui folder.",
        )
        return None

    try:
        import PySide6  # noqa: F401
    except ModuleNotFoundError:
        _show_message(
            f"{APP_NAME} Launcher Error",
            "PySide6 is not installed for this Python environment.\n\n"
            "You do not need Visual Studio Code, but Python and PySide6 must be installed.\n\n"
            "From the project folder, run:\n"
            "python -m pip install PySide6\n\n"
            "If the project later includes requirements.txt, use:\n"
            "python -m pip install -r requirements.txt",
        )
        return None
    except Exception as exc:
        _show_message(
            f"{APP_NAME} Launcher Error",
            "Python found PySide6, but importing it produced an unexpected error.\n\n"
            f"Error:\n{exc}",
        )
        return None

    return ui_script


def main() -> int:
    project_root = _project_root()
    ui_script = _verify_environment(project_root)
    if ui_script is None:
        return 1

    os.chdir(project_root)
    project_root_text = str(project_root)
    if project_root_text not in sys.path:
        sys.path.insert(0, project_root_text)

    try:
        runpy.run_path(str(ui_script), run_name="__main__")
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 0
        return code
    except Exception:
        details = traceback.format_exc()
        _show_message(
            f"{APP_NAME} Launcher Error",
            "The desktop UI could not be opened.\n\n"
            "The launcher did not run deck analysis; this failed while opening the UI.\n\n"
            f"Details:\n{details[-3500:]}",
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
