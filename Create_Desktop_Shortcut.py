"""
The Dragon's Touch - Desktop Shortcut Creator
v0.7.7L.3

Desktop shortcut creation is deferred for v0.7 alpha because the shortcut path
was blocked by Windows Smart App Control during testing.

This helper is intentionally kept as an experimental/developer-only file. It no
longer creates a shortcut automatically. Use Launch_The_Dragons_Touch.pyw as the
supported v0.7 alpha launch path.
"""
from __future__ import annotations


def _show_message(title: str, message: str) -> None:
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, message, title, 0x40)
    except Exception:
        print(f"{title}\n{'=' * len(title)}\n{message}")
        try:
            input("\nPress Enter to close...")
        except Exception:
            pass


def main() -> int:
    _show_message(
        "The Dragon's Touch Shortcut Deferred",
        "Desktop shortcut support is deferred for v0.7 alpha.\n\n"
        "Windows Smart App Control blocked the shortcut path during testing.\n\n"
        "Supported alpha launch path:\n"
        "  Double-click Launch_The_Dragons_Touch.pyw\n\n"
        "Do not disable Smart App Control just to create a shortcut.\n\n"
        "Long-term plan: packaged app -> signed release -> installer -> shortcut.",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
