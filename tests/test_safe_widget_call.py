"""Stale-reference safety smoke test.

Catches the bug class that caused the long-standing "navigate-away-and-back"
issue: refresh functions calling methods on stale shiboken widget references
that throw `RuntimeError: libshiboken: Internal C++ object already deleted`.

The fix landed 2026-05-29: `_safe_widget_call` / `_safe_set_enabled` /
`_safe_set_visible` in commander_discovery_page.py wrap method calls in
try/except RuntimeError. These tests verify that contract holds — the
helpers silently no-op on stale references instead of propagating the
exception up to break the calling code path.

If PySide6 isn't installed, the test SKIPs (the helpers live inside a
module that imports PySide6 at module load).
"""
from __future__ import annotations

from _test_helpers import TestRun


def _skip_if_no_pyside6() -> None:
    """If PySide6 isn't installed, print a skip message and exit 0."""
    import sys
    try:
        import PySide6  # noqa: F401
    except ImportError:
        print("SKIP: PySide6 not installed. Install with `pip install PySide6` to run UI safety tests.")
        sys.exit(0)


class _StaleStub:
    """Stub that mimics a shiboken-deleted widget: every method raises
    RuntimeError with the libshiboken message."""

    def __getattr__(self, name):
        def _raise(*args, **kwargs):
            raise RuntimeError(
                "libshiboken: Internal C++ object (PySide6.QtWidgets.QPushButton) already deleted."
            )
        return _raise


class _RecordingStub:
    """Stub that records method calls so the test can verify they happened.

    Uses __getattr__ to accept any method name — that way new methods added
    to the refresh functions (e.g. setToolTip) don't break the test stubs.
    """

    def __init__(self):
        self.calls: list[tuple[str, tuple, dict]] = []

    def __getattr__(self, name):
        # __getattr__ is only called for attributes not found normally, so
        # self.calls (set in __init__) won't recurse here.
        def _recording_method(*args, **kwargs):
            self.calls.append((name, args, kwargs))
        return _recording_method


def main() -> None:
    _skip_if_no_pyside6()

    from ui.pages.commander_discovery_page import (
        _safe_widget_call,
        _safe_set_enabled,
        _safe_set_visible,
        _refresh_build_start_preview_controls,
        _refresh_random_commander_button,
    )

    run = TestRun("test_safe_widget_call")

    # ---------- _safe_widget_call contract ----------
    run.true("_safe_widget_call(None, ...) is a silent no-op", _safe_widget_call(None, "setEnabled", True) is None)

    stale = _StaleStub()
    try:
        _safe_widget_call(stale, "setEnabled", True)
        run.true("_safe_widget_call catches RuntimeError from stale shiboken stub", True)
    except RuntimeError:
        run.true("_safe_widget_call catches RuntimeError from stale shiboken stub", False,
                 "RuntimeError leaked out — _safe_widget_call did not catch it")

    rec = _RecordingStub()
    _safe_widget_call(rec, "setEnabled", True)
    run.eq("_safe_widget_call forwards args to a real (non-stale) widget", rec.calls, [("setEnabled", (True,), {})])

    # ---------- _safe_set_enabled / _safe_set_visible thin-wrapper contract ----------
    rec2 = _RecordingStub()
    _safe_set_enabled(rec2, False)
    run.eq("_safe_set_enabled forwards setEnabled", rec2.calls, [("setEnabled", (False,), {})])

    rec3 = _RecordingStub()
    _safe_set_visible(rec3, True)
    run.eq("_safe_set_visible forwards setVisible", rec3.calls, [("setVisible", (True,), {})])

    # Stale variants do not leak the RuntimeError.
    try:
        _safe_set_enabled(_StaleStub(), True)
        _safe_set_visible(_StaleStub(), False)
        run.true("_safe_set_enabled / _safe_set_visible swallow stale-reference errors", True)
    except RuntimeError:
        run.true("_safe_set_enabled / _safe_set_visible swallow stale-reference errors", False)

    # ---------- _refresh_build_start_preview_controls survives stale refs ----------
    # This was the ORIGINAL bug surface. The function reads ~8 widget references
    # off the window object. Today's fix wraps each call so a stale reference
    # silently no-ops instead of breaking the post-scan flow.
    class _MockWindow:
        # Mix of valid stubs, stale stubs, and missing attrs — exactly the
        # situation after a page rebuild that didn't recreate every dev-mode
        # widget the previous build had.
        commander_discovery_start_build_preview_button = _StaleStub()
        commander_discovery_build_setup_panel_preview_button = _RecordingStub()
        commander_discovery_commander_preference_handoff_preview_button = _StaleStub()
        commander_discovery_shell_skeleton_preview_button = None
        commander_discovery_setup_summary_preview_button = _RecordingStub()
        commander_discovery_strategy_selection_override_preview_button = _StaleStub()
        commander_discovery_primary_strategy_combo = _RecordingStub()
        commander_discovery_secondary_strategy_combo = _StaleStub()
        commander_discovery_build_depth_selection_buttons = [_StaleStub(), _RecordingStub(), None]
        # No candidate selected for the build-from-collection preview, so
        # is_enabled should be False for all the live widgets.
        commander_discovery_selected_candidate_summary = None

    mock_window = _MockWindow()
    try:
        _refresh_build_start_preview_controls(mock_window)
        run.true("_refresh_build_start_preview_controls survives mixed stale/valid widget refs", True)
    except RuntimeError as exc:
        run.true("_refresh_build_start_preview_controls survives mixed stale/valid widget refs", False,
                 f"RuntimeError leaked out: {exc}")

    # Each valid Recording stub should have received setEnabled(False) since
    # no candidate is selected. Stale stubs raise internally but are swallowed
    # by _safe_set_enabled. The refactored function ALSO calls setToolTip on
    # each widget (Category C tooltip pattern) — accept either, just verify
    # setEnabled(False) appears in each valid widget's call list.
    for valid_widget in (
        mock_window.commander_discovery_build_setup_panel_preview_button,
        mock_window.commander_discovery_setup_summary_preview_button,
        mock_window.commander_discovery_primary_strategy_combo,
    ):
        run.true(
            f"valid widget received setEnabled(False): {valid_widget.calls}",
            ("setEnabled", (False,), {}) in valid_widget.calls,
        )

    # ---------- _refresh_random_commander_button survives stale random button ----------
    class _MockWindowStaleRandomButton:
        commander_discovery_random_button = _StaleStub()
        commander_discovery_candidate_summaries: list = []
        commander_discovery_all_candidate_summaries: list = []

    try:
        _refresh_random_commander_button(_MockWindowStaleRandomButton())
        run.true("_refresh_random_commander_button survives stale random_button", True)
    except RuntimeError as exc:
        run.true("_refresh_random_commander_button survives stale random_button", False, str(exc))

    run.report_and_exit()


if __name__ == "__main__":
    main()
