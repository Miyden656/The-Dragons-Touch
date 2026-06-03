import os
import sys
from pathlib import Path
import subprocess
from datetime import datetime
"""Settings page for The Dragon's Touch.

v0.10.5.1-dev:
Settings controls app-wide defaults.
Review Setup controls the current run.

v0.10.5.7-dev:
Guide Presentation is confirmed as an app-wide Settings control, not a Philosophy Lens control.
"""

try:
    from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot
    from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QApplication, QMessageBox

    from ui.constants import (
        INTERFACE_MODE_OPTIONS,
        GUIDE_PRESENTATION_OPTIONS,
        APP_COLLECTION_SOURCE_DEFAULT_OPTIONS,
        UI_DENSITY_OPTIONS,
    )
    from ui.styles.theme import ADVENTURERS_MAP, DRAGON_FORGE
    from ui.widgets import add_shadow, ReportCard, TexturedPanel
    from data.data_setup_service import get_data_setup_status, download_scryfall_cards, download_commander_spellbook_combo_bulk
except ImportError:
    from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot
    from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QApplication, QMessageBox

    from constants import (
        INTERFACE_MODE_OPTIONS,
        GUIDE_PRESENTATION_OPTIONS,
        APP_COLLECTION_SOURCE_DEFAULT_OPTIONS,
        UI_DENSITY_OPTIONS,
    )
    from styles.theme import ADVENTURERS_MAP, DRAGON_FORGE
    from widgets import add_shadow, ReportCard, TexturedPanel
    from data.data_setup_service import get_data_setup_status, download_scryfall_cards, download_commander_spellbook_combo_bulk


def _row(label_text, widget, note_text=None):
    row = QHBoxLayout()
    label = QLabel(label_text)
    label.setObjectName("helperText")
    label.setMinimumWidth(185)
    row.addWidget(label)
    row.addWidget(widget, stretch=1)
    return row


def _combo(window, values, current):
    combo = QComboBox()
    combo.addItems(values)
    combo.setCurrentText(current if current in values else values[0])
    combo.setMinimumWidth(260)
    window.configure_combo_popup(combo)
    return combo

class _DataSetupWorker(QObject):
    """Run one long Data Setup action without blocking the Settings UI."""

    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, action):
        super().__init__()
        self._action = action

    def run(self):
        try:
            self.finished.emit(self._action())
        except Exception as exc:  # noqa: BLE001 - surfaced to user dialog.
            self.failed.emit(str(exc))


class _DataSetupCompletionBridge(QObject):
    """Handle worker completion on the Qt/UI side and release refs safely."""

    def __init__(self, status_widget, action_button, original_text):
        super().__init__()
        self.status_widget = status_widget
        self.action_button = action_button
        self.original_text = original_text

    @Slot()
    def restore_button(self):
        if self.action_button is not None:
            self.action_button.setEnabled(True)
            self.action_button.setText(self.original_text)

    @Slot(object)
    def on_scryfall_finished(self, path):
        _refresh_data_setup_status_widget(self.status_widget)
        self.restore_button()
        _show_data_setup_message(
            "Scryfall Data Updated",
            f"Scryfall default_cards data was downloaded successfully.\n\n{path}",
        )

    @Slot(str)
    def on_scryfall_failed(self, message):
        _refresh_data_setup_status_widget(self.status_widget)
        self.restore_button()
        _show_data_setup_message(
            "Scryfall Download Failed",
            message,
            error=True,
        )

    @Slot()
    def release_worker_refs(self):
        if self.action_button is not None:
            self.action_button._data_setup_thread = None
            self.action_button._data_setup_worker = None
            self.action_button._data_setup_bridge = None


def _append_status_note(status_widget, note):
    """Show a temporary progress note without requiring a custom progress widget."""
    try:
        base_text = _format_data_setup_status_text()
    except Exception:
        base_text = "Runtime Data Setup"
    _set_text_widget_value(status_widget, f"{base_text}\n\n{note}")


def _run_scryfall_download_in_worker(status_widget, action_button):
    """Download Scryfall data in a background Qt worker thread."""
    original_text = action_button.text() if action_button is not None else "Download / Update Scryfall"

    if action_button is not None:
        action_button.setEnabled(False)
        action_button.setText("Downloading Scryfall...")

    _append_status_note(
        status_widget,
        "Scryfall download is running. The app should remain responsive. "
        "This can take several minutes for default_cards.",
    )

    thread = QThread()
    worker = _DataSetupWorker(lambda: download_scryfall_cards(overwrite=True))
    bridge = _DataSetupCompletionBridge(status_widget, action_button, original_text)
    worker.moveToThread(thread)

    worker.finished.connect(bridge.on_scryfall_finished)
    worker.failed.connect(bridge.on_scryfall_failed)
    worker.finished.connect(thread.quit)
    worker.failed.connect(thread.quit)
    thread.started.connect(worker.run)
    thread.finished.connect(worker.deleteLater)
    thread.finished.connect(bridge.release_worker_refs)
    thread.finished.connect(thread.deleteLater)

    # Keep references alive until the worker thread has fully finished.
    if action_button is not None:
        action_button._data_setup_thread = thread
        action_button._data_setup_worker = worker
        action_button._data_setup_bridge = bridge

    thread.start()

def _format_data_file_status(item):
    """Format one runtime data file status line for the Settings Data Setup card."""
    mark = "READY" if getattr(item, "exists", False) else "MISSING"
    size = getattr(item, "size_bytes", 0)
    size_text = f"{size:,} bytes" if size else "0 bytes"
    label = getattr(item, "label", "Runtime data file")
    path = getattr(item, "path", "")
    return f"{mark} — {label} ({size_text})\n  {path}"


def _human_size(num_bytes):
    """Human-readable file size for the Data Setup checklist."""
    n = float(num_bytes or 0)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{int(n)} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} GB"


def _data_setup_checklist_line(item, optional=False):
    """One checklist row: ✓/—/•  Label — size — ready DATE (or a 'missing' hint)."""
    ready = bool(getattr(item, "exists", False))
    label = getattr(item, "label", "Data file")
    if ready:
        size = _human_size(getattr(item, "size_bytes", 0))
        mtime = getattr(item, "last_modified", 0.0) or 0.0
        try:
            when = datetime.fromtimestamp(mtime).strftime("%b %d, %Y") if mtime else "ready"
        except Exception:
            when = "ready"
        return f"✓  {label} — {size} — ready {when}"
    if optional:
        return f"•  {label} — optional (developer validation), not built"
    return f"—  {label} — not downloaded yet"


def _format_data_setup_checklist(dev_mode=False):
    """Compact, user-friendly Data Setup checklist.

    In User Mode the dev-only parity combo index row is hidden (it's optional
    developer validation and only confused testers).
    """
    try:
        status = get_data_setup_status()
    except Exception as exc:
        return f"Data setup status could not be loaded.\nError: {exc}"
    lines = [
        "Data files",
        "----------",
        _data_setup_checklist_line(status.scryfall_cards),
        _data_setup_checklist_line(status.commander_spellbook_bulk),
        _data_setup_checklist_line(status.combo_index),
    ]
    if dev_mode:
        lines.append(_data_setup_checklist_line(status.combo_index_parity, optional=True))
    lines.extend([
        "",
        ("✓  Ready for deck analysis" if status.ready_for_basic_analysis
         else "—  Deck analysis needs Scryfall card data"),
        ("✓  Ready for combo analysis" if status.ready_for_combo_analysis
         else "—  Combo analysis needs combo data + combo index"),
    ])
    return "\n".join(lines)


def _format_data_setup_first_run_guidance(status):
    """Return first-run guidance for missing runtime data."""
    guidance = ["", "First-run setup guidance:"]

    if status.ready_for_basic_analysis and status.ready_for_combo_analysis:
        return [
            "",
            "First-run setup guidance:",
            "- Runtime data is ready. You can run deck analysis and Combo Awareness.",
            "- Use the guarded buttons below only when you want to update local data.",
        ]

    if not status.scryfall_cards.exists:
        guidance.append("- Step 1: Click Download / Update Scryfall to enable basic card lookup and deck analysis.")
    else:
        guidance.append("- Step 1: Scryfall data is ready.")

    if not status.commander_spellbook_bulk.exists:
        guidance.append("- Step 2: Click Download / Update Combo Data to fetch Commander Spellbook combo data.")
    else:
        guidance.append("- Step 2: Commander Spellbook combo data is ready.")

    if not status.combo_index.exists:
        if status.commander_spellbook_bulk.exists:
            guidance.append("- Step 3: Click Build Combo Index to enable report-ready combo analysis.")
        else:
            guidance.append("- Step 3: Build Combo Index after Combo Data has been downloaded.")
    else:
        guidance.append("- Step 3: Normal combo index is ready.")

    if not status.ready_for_basic_analysis:
        guidance.append("- Basic analysis is not ready yet. Scryfall data is required.")

    if not status.ready_for_combo_analysis:
        guidance.append("- Combo analysis is not ready yet. Combo data and the normal combo index are required.")

    guidance.append("- No setup action runs automatically; each download/build button requires confirmation.")

    return guidance

def _format_data_setup_status_text():
    """Return compact Settings-friendly runtime data setup status text."""
    try:
        status = get_data_setup_status()
    except Exception as exc:
        return (
            "Data setup status could not be loaded.\n\n"
            f"Error: {exc}\n\n"
            "Run from PowerShell:\n"
            "py tools\\data_setup.py --status"
        )

    basic_ready = "Yes" if status.ready_for_basic_analysis else "No"
    combo_ready = "Yes" if status.ready_for_combo_analysis else "No"

    lines = [
        "Runtime Data Setup",
        "==================",
        f"Basic analysis ready: {basic_ready}",
        f"Combo analysis ready: {combo_ready}",
        "",
        "Runtime folders:",
        f"- Root: {status.runtime_root}",
        f"- Data: {status.data_dir}",
        "",
        "Data files:",
        _format_data_file_status(status.scryfall_cards),
        _format_data_file_status(status.commander_spellbook_bulk),
        _format_data_file_status(status.combo_index),
        _format_data_file_status(status.combo_index_parity),
    ]

    if status.next_steps:
        lines.extend(["", "Next steps:"])
        lines.extend(f"- {step}" for step in status.next_steps)
    else:
        lines.extend(["", "Status: All required runtime data currently appears ready."])

    lines.extend(_format_data_setup_first_run_guidance(status))

    lines.extend([
        "",
        "PowerShell setup commands:",
        "- py tools\\data_setup.py --status",
        "- py tools\\data_setup.py --download-scryfall --overwrite",
        "- py tools\\data_setup.py --download-combos --overwrite",
        "- py tools\\data_setup.py --commands",
        "",
        "Note: Safe actions are local. Download/build actions are guarded and require confirmation.",
    ])

    return "\n".join(lines)


def _data_setup_commands_text():
    """Return copy-ready PowerShell data setup commands."""
    return "\n".join([
        "py tools\\data_setup.py --status",
        "py tools\\data_setup.py --download-scryfall --overwrite",
        "py tools\\data_setup.py --download-combos --overwrite",
        "py tools\\data_setup.py --commands",
    ])


def _set_text_widget_value(widget, text):
    """Best-effort text update for QLabel/QTextEdit/QPlainTextEdit style widgets."""
    for method_name in ("setPlainText", "setText"):
        method = getattr(widget, method_name, None)
        if callable(method):
            method(text)
            return True
    return False


def _refresh_data_setup_status_widget(widget):
    """Refresh the Settings Data Setup status text."""
    return _set_text_widget_value(widget, _format_data_setup_status_text())


class _DataSetupRefreshProxy:
    """A stand-in 'widget' for the guarded data actions.

    The guarded download/build helpers push verbose status text into whatever
    widget they're handed. We don't want that dumped into the compact checklist,
    so this proxy treats any text update as a signal to re-render the checklist
    (and dev details) from fresh on-disk status — which is exactly what we want
    after a download/build completes (fixes the 'combo index didn't update').
    """

    def __init__(self, on_refresh):
        self._on_refresh = on_refresh

    def setPlainText(self, _text=""):
        try:
            self._on_refresh()
        except Exception:
            pass

    def setText(self, _text=""):
        self.setPlainText(_text)


def _open_runtime_data_folder():
    """Open the active runtime data folder in the OS file browser."""
    status = get_data_setup_status()
    data_dir = status.data_dir
    try:
        os.startfile(data_dir)
    except Exception as exc:
        print(f"Could not open data folder: {exc}")


def _copy_data_setup_commands_to_clipboard():
    """Copy data setup commands to the system clipboard."""
    try:
        QApplication.clipboard().setText(_data_setup_commands_text())
    except Exception as exc:
        print(f"Could not copy data setup commands: {exc}")


def _make_data_setup_button(label, callback):
    """Create a small Settings Data Setup action button."""
    button = QPushButton(label)
    button.clicked.connect(callback)
    return button


def _show_data_setup_message(title, message, *, error=False):
    """Show a small Settings Data Setup message dialog."""
    try:
        icon = QMessageBox.Icon.Critical if error else QMessageBox.Icon.Information
        box = QMessageBox()
        box.setIcon(icon)
        box.setWindowTitle(title)
        box.setText(message)
        box.exec()
    except Exception as exc:
        print(f"{title}: {message}")
        print(f"Could not show message dialog: {exc}")


def _confirm_data_setup_action(title, message):
    """Always-confirm data setup actions.

    Category A (popup removal 2026-05-29): the user clicked a Download/Update
    button — that IS the confirmation. We don't ask a second time. The
    title/message stay in the function signature for status-text logging
    (callers print them to the status widget).
    """
    print(f"{title}: {message}")
    return True


def _download_scryfall_data_guarded(status_widget, action_button=None):
    """Download/update Scryfall card data after explicit user confirmation."""
    if not _confirm_data_setup_action(
        "Download / Update Scryfall Data",
        "This will download or replace the local Scryfall default_cards data file. "
        "The download is large and may take several minutes. "
        "The Settings page should remain responsive while it runs.\n\n"
        "Continue?",
    ):
        return

    _run_scryfall_download_in_worker(status_widget, action_button)


def _download_combo_data_guarded(status_widget):
    """Download/update Commander Spellbook combo data after explicit user confirmation."""
    if not _confirm_data_setup_action(
        "Download / Update Combo Data",
        "This will download or replace the local Commander Spellbook combo data file. "
        "The download is large and the app may appear busy until it finishes.\n\n"
        "This does not build combo indexes yet. Continue?",
    ):
        return

    try:
        path = download_commander_spellbook_combo_bulk(overwrite=True)
        _refresh_data_setup_status_widget(status_widget)
        _show_data_setup_message(
            "Combo Data Updated",
            f"Commander Spellbook combo data was downloaded successfully.\n\n{path}\n\n"
            "Next step: build the combo index.",
        )
    except Exception as exc:
        _refresh_data_setup_status_widget(status_widget)
        _show_data_setup_message(
            "Combo Data Download Failed",
            str(exc),
            error=True,
        )


def _build_combo_index_guarded(status_widget):
    """Build the normal Commander Spellbook combo index after explicit user confirmation."""
    if not _confirm_data_setup_action(
        "Build Combo Index",
        "This will rebuild the local Commander Spellbook combo index used by Combo Awareness. "
        "The app may appear busy until it finishes.\n\n"
        "This builds the normal user-facing combo_index.json only, not the parity index. Continue?",
    ):
        return

    try:
        import runpy
        import subprocess
        import sys
        from pathlib import Path

        status = get_data_setup_status()

        if not status.commander_spellbook_bulk.exists:
            _show_data_setup_message(
                "Combo Index Build Blocked",
                "Commander Spellbook combo bulk data is missing.\n\n"
                "Run Download / Update Combo Data first.",
                error=True,
            )
            _refresh_data_setup_status_widget(status_widget)
            return

        project_root = Path(status.runtime_root)
        internal_root = project_root / "_internal"
        meipass_root = Path(getattr(sys, "_MEIPASS", internal_root))

        build_script_candidates = [
            project_root / "tools" / "build_combo_index.py",
            internal_root / "tools" / "build_combo_index.py",
            meipass_root / "tools" / "build_combo_index.py",
        ]

        build_script = next((candidate for candidate in build_script_candidates if candidate.exists()), None)

        if build_script is None:
            candidate_text = "\n".join(str(candidate) for candidate in build_script_candidates)
            _show_data_setup_message(
                "Combo Index Build Blocked",
                "Could not find combo index builder script in any expected runtime location:\n\n"
                f"{candidate_text}",
                error=True,
            )
            _refresh_data_setup_status_widget(status_widget)
            return

        output_path = Path(status.combo_index.path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        command_args = [
            str(build_script),
            "--input",
            status.commander_spellbook_bulk.path,
            "--output",
            str(output_path),
        ]

        if getattr(sys, "frozen", False):
            old_argv = sys.argv[:]
            try:
                sys.argv = command_args[:]
                try:
                    runpy.run_path(str(build_script), run_name="__main__")
                    return_code = 0
                except SystemExit as exc:
                    return_code = exc.code if isinstance(exc.code, int) else 0
            finally:
                sys.argv = old_argv

            _refresh_data_setup_status_widget(status_widget)

            if return_code not in (0, None):
                _show_data_setup_message(
                    "Combo Index Build Failed",
                    f"Combo index builder exited with code {return_code}.\n\nScript:\n{build_script}",
                    error=True,
                )
                return
        else:
            command = [sys.executable] + command_args
            result = subprocess.run(
                command,
                cwd=str(project_root),
                capture_output=True,
                text=True,
            )

            _refresh_data_setup_status_widget(status_widget)

            if result.returncode != 0:
                details = "\n".join([
                    "Combo index build failed.",
                    "",
                    "Command:",
                    " ".join(command),
                    "",
                    "STDOUT:",
                    result.stdout or "(none)",
                    "",
                    "STDERR:",
                    result.stderr or "(none)",
                ])
                _show_data_setup_message(
                    "Combo Index Build Failed",
                    details,
                    error=True,
                )
                return

        _show_data_setup_message(
            "Combo Index Built",
            f"Combo index was built successfully.\n\n{output_path}",
        )
    except Exception as exc:
        _refresh_data_setup_status_widget(status_widget)
        _show_data_setup_message(
            "Combo Index Build Failed",
            str(exc),
            error=True,
        )


# --- Local Commander AI (v1.7 Phase 5a) -----------------------------------

COMMANDER_AI_GUIDE_STYLE_DISPLAY = ["Adventurer", "Archivist", "Strategist", "Minimal"]
COMMANDER_AI_TEMPERATURE_PRESETS = ["0.2", "0.4", "0.7", "1.0"]

# Short, plain-English definitions shown under each dropdown so the user knows
# what they picked (requested feedback).
COMMANDER_AI_GUIDE_STYLE_NOTES = {
    "Adventurer": "Warm, encouraging, story-flavored coaching — friendly and motivating.",
    "Archivist": "Structured and thorough — headers, lists, and record-friendly detail.",
    "Strategist": "Direct and analytical — prioritized, decision-focused advice.",
    "Minimal": "Short and to the point — just the essentials, little elaboration.",
}
COMMANDER_AI_TEMPERATURE_NOTES = {
    "0.2": "Most focused and consistent — sticks closely to the engine data, least creative.",
    "0.4": "Balanced (recommended) — reliable, with a little flexibility in wording.",
    "0.7": "More creative and varied phrasing — occasionally more speculative.",
    "1.0": "Most free-wheeling — least predictable and more likely to wander off the data.",
}


def _installed_ollama_models(window) -> list:
    """Best-effort list of installed Ollama models for the dropdown. Short
    timeout + never raises so opening Settings can't hang if Ollama is down."""
    try:
        from ai.commander_ai_config import from_settings
        from ai.ollama_client import OllamaClient

        return list(OllamaClient(from_settings(window.app_settings)).list_models(timeout=2.0))
    except Exception:  # noqa: BLE001 - Settings must always open.
        return []


def _user_settings_module():
    try:
        from ui.services import user_settings
    except ImportError:
        from services import user_settings
    return user_settings


def _save_ai_setting(window, key, value):
    """Persist one commander_ai_* setting into the shared app settings store."""
    window.app_settings[key] = value
    _user_settings_module().save_app_settings(window.app_settings)
    window.state.status = f"Commander AI setting saved: {key}"


def _current_ai_guide_style_display(window):
    token = str(window.app_settings.get("commander_ai_guide_style", "adventurer")).strip().lower()
    display = token.capitalize()
    return display if display in COMMANDER_AI_GUIDE_STYLE_DISPLAY else "Adventurer"


def _current_ai_temperature_display(window):
    value = str(window.app_settings.get("commander_ai_temperature", "0.4")).strip()
    return value if value in COMMANDER_AI_TEMPERATURE_PRESETS else "0.4"


class _CommanderAITestBridge(QObject):
    """Handle Commander AI connection-test completion on the Qt/UI side."""

    def __init__(self, status_widget, button, original_text):
        super().__init__()
        self.status_widget = status_widget
        self.button = button
        self.original_text = original_text

    def _restore(self):
        if self.button is not None:
            self.button.setEnabled(True)
            self.button.setText(self.original_text)

    @Slot(object)
    def on_finished(self, availability):
        ok = bool(getattr(availability, "ok", False))
        message = getattr(availability, "message", "") or ""
        prefix = "Connected. " if ok else "Not reachable. "
        _set_text_widget_value(self.status_widget, prefix + message)
        self._restore()

    @Slot(str)
    def on_failed(self, message):
        _set_text_widget_value(self.status_widget, f"Test failed: {message}")
        self._restore()

    @Slot()
    def release_refs(self):
        if self.button is not None:
            self.button._ai_test_thread = None
            self.button._ai_test_worker = None
            self.button._ai_test_bridge = None


def _run_commander_ai_test(window, status_widget, button):
    """Check Ollama availability in a background worker so Settings stays responsive."""
    try:
        from ai.commander_ai_config import from_settings
        from ai.ollama_client import OllamaClient
    except Exception as exc:  # noqa: BLE001 - never crash Settings.
        _set_text_widget_value(status_widget, f"Commander AI module unavailable: {exc}")
        return

    config = from_settings(window.app_settings)
    original_text = button.text()
    button.setEnabled(False)
    button.setText("Testing...")
    _set_text_widget_value(
        status_widget,
        f"Contacting Ollama at {config.base_url} (model: {config.model})...",
    )

    thread = QThread()
    worker = _DataSetupWorker(lambda: OllamaClient(config).is_available())
    bridge = _CommanderAITestBridge(status_widget, button, original_text)
    worker.moveToThread(thread)

    worker.finished.connect(bridge.on_finished)
    worker.failed.connect(bridge.on_failed)
    worker.finished.connect(thread.quit)
    worker.failed.connect(thread.quit)
    thread.started.connect(worker.run)
    thread.finished.connect(worker.deleteLater)
    thread.finished.connect(bridge.release_refs)
    thread.finished.connect(thread.deleteLater)

    # Keep refs alive until the thread fully finishes.
    button._ai_test_thread = thread
    button._ai_test_worker = worker
    button._ai_test_bridge = bridge
    thread.start()


def build_commander_ai_settings_card(window):
    """Build the Local Commander AI settings card (Off by default, fully local)."""
    card = ReportCard("Local Commander AI", window.theme, badges=[("Beta", "primary"), ("Local", "manual")])
    card.body.addWidget(window.default_note(
        "Optional local AI guide powered by Ollama. It runs entirely on your machine and is "
        "off by default. When enabled, the Commander Guide can explain your deck, cuts, and "
        "replacements using The Dragon's Touch analysis as the source of truth."
    ))

    enable_combo = _combo(window, ["Off", "On"], "On" if window.app_settings.get("commander_ai_enabled") else "Off")
    enable_combo.currentTextChanged.connect(lambda v: _save_ai_setting(window, "commander_ai_enabled", v == "On"))
    card.body.addLayout(_row("Enable local AI", enable_combo))

    # How the guide appears on Report Viewer / The Commander's Call (read live by
    # the "Ask the Commander Guide" trigger — no restart needed).
    _us = _user_settings_module()
    display_mode_current = _us.normalize_commander_ai_display_mode(window.app_settings.get("commander_ai_display_mode"))
    display_mode_combo = _combo(window, _us.COMMANDER_AI_DISPLAY_OPTIONS, display_mode_current)
    display_mode_combo.currentTextChanged.connect(lambda v: _save_ai_setting(window, "commander_ai_display_mode", v))
    card.body.addLayout(_row("Guide display", display_mode_combo))
    card.body.addWidget(window.default_note(
        "Slide-in panel opens the guide over the page; Embedded panel shows it inline "
        "below the 'Ask the Commander Guide' button."
    ))

    # Editable dropdown of installed models (still type-able for models not yet
    # pulled or when Ollama is offline).
    current_model = str(window.app_settings.get("commander_ai_model", "llama3.1"))
    model_combo = QComboBox()
    model_combo.setEditable(True)
    model_combo.setMinimumWidth(260)
    window.configure_combo_popup(model_combo)
    model_items = [current_model] if current_model else []
    for name in _installed_ollama_models(window):
        if name not in model_items:
            model_items.append(name)
    model_combo.addItems(model_items)
    model_combo.setCurrentText(current_model)

    def _save_model():
        _save_ai_setting(window, "commander_ai_model", model_combo.currentText().strip() or "llama3.1")

    model_combo.lineEdit().editingFinished.connect(_save_model)
    model_combo.activated.connect(lambda _i: _save_model())
    card.body.addLayout(_row("Ollama model", model_combo))

    url_edit = QLineEdit(str(window.app_settings.get("commander_ai_base_url", "http://localhost:11434")))
    url_edit.setMinimumWidth(260)
    url_edit.editingFinished.connect(
        lambda: _save_ai_setting(window, "commander_ai_base_url", url_edit.text().strip() or "http://localhost:11434")
    )
    card.body.addLayout(_row("Ollama base URL", url_edit))

    current_style = _current_ai_guide_style_display(window)
    style_combo = _combo(window, COMMANDER_AI_GUIDE_STYLE_DISPLAY, current_style)
    style_note = QLabel(COMMANDER_AI_GUIDE_STYLE_NOTES.get(current_style, ""))
    style_note.setObjectName("mutedText")
    style_note.setWordWrap(True)
    style_combo.currentTextChanged.connect(
        lambda v: (
            _save_ai_setting(window, "commander_ai_guide_style", v.strip().lower()),
            style_note.setText(COMMANDER_AI_GUIDE_STYLE_NOTES.get(v, "")),
        )
    )
    card.body.addLayout(_row("Response style", style_combo))
    card.body.addWidget(style_note)

    current_temp = _current_ai_temperature_display(window)
    temp_combo = _combo(window, COMMANDER_AI_TEMPERATURE_PRESETS, current_temp)
    temp_note = QLabel(COMMANDER_AI_TEMPERATURE_NOTES.get(current_temp, ""))
    temp_note.setObjectName("mutedText")
    temp_note.setWordWrap(True)
    temp_combo.currentTextChanged.connect(
        lambda v: (
            _save_ai_setting(window, "commander_ai_temperature", float(v)),
            temp_note.setText(COMMANDER_AI_TEMPERATURE_NOTES.get(v, "")),
        )
    )
    card.body.addLayout(_row("Creativity (temperature)", temp_combo))
    card.body.addWidget(temp_note)

    strict_combo = _combo(window, ["On", "Off"], "On" if window.app_settings.get("commander_ai_strict_fact_check", True) else "Off")
    strict_combo.currentTextChanged.connect(
        lambda v: _save_ai_setting(window, "commander_ai_strict_fact_check", v == "On")
    )
    card.body.addLayout(_row("Strict fact-check", strict_combo))

    test_status = window.make_text(
        "Click Test Connection to check whether Ollama is running and the selected model is installed.",
        paper=True,
    )
    test_button = QPushButton("Test Connection")
    test_button.setObjectName("utilityButton")
    test_button.clicked.connect(lambda: _run_commander_ai_test(window, test_status, test_button))
    card.body.addWidget(test_button)
    card.body.addWidget(test_status)

    card.body.addWidget(window.default_note(
        "Response style sets the AI's tone (Adventurer / Archivist / Strategist / Minimal) and is "
        "separate from the Guide Presentation voice above. Strict fact-check appends a transparent "
        "note whenever the AI makes a card-ownership, ban-status, or combo claim the engine can't confirm."
    ))
    return card


def build_settings_content(window):
    """Build the Settings content (scroll area) for hosting in the slide-over drawer.

    Returns the scroll widget only — the drawer provides its own title + Close
    header, so there's no page_container wrapper here.
    """
    scroll, content = window.scroll_content()
    body = TexturedPanel(window.theme, kind="iron", glow=False)
    add_shadow(body, blur=24, y=8)

    b_layout = QVBoxLayout(body)
    b_layout.setContentsMargins(22, 22, 22, 22)
    b_layout.setSpacing(16)

    # Developer mode banner.
    if window.is_dev_mode():
        dev_banner = TexturedPanel(window.theme, kind="iron_2", glow=True)
        banner_layout = QHBoxLayout(dev_banner)
        banner_layout.setContentsMargins(16, 12, 16, 12)
        banner = QLabel("Developer Mode Enabled")
        banner.setObjectName("sectionTitle")
        detail = QLabel("Development, diagnostics, raw reports, and testing controls may be visible.")
        detail.setObjectName("defaultNote")
        detail.setWordWrap(True)
        banner_layout.addWidget(banner)
        banner_layout.addWidget(detail, stretch=1)
        b_layout.addWidget(dev_banner)

    # Interface Mode.
    interface_card = ReportCard("Interface Mode", window.theme, badges=[("Persistent", "primary")])
    interface_combo = _combo(window, INTERFACE_MODE_OPTIONS, window.interface_mode_display_text())
    window.interface_mode_combo = interface_combo
    interface_combo.currentTextChanged.connect(window.stage_interface_mode)
    interface_card.body.addLayout(_row("Mode", interface_combo))
    interface_card.body.addWidget(window.default_note(
        "User Mode is the clean default for normal deck reviews. Developer Mode is enabled here only and exposes testing/diagnostic tools."
    ))
    if window.is_dev_mode():
        interface_card.body.addWidget(window.default_note("Developer Mode Enabled. Remember to switch back to User Mode before handing the app to a normal tester."))
    b_layout.addWidget(interface_card)

    # Appearance.
    appearance_card = ReportCard("Appearance", window.theme, badges=[("Visual", "primary")])
    theme_row = QHBoxLayout()
    dark = QPushButton("Dragon Forge")
    dark.setObjectName("primaryButton" if window.theme()["name"] == "Dragon Forge" else "utilityButton")
    dark.clicked.connect(lambda: window.set_theme(DRAGON_FORGE))
    light = QPushButton("Adventurer's Map")
    light.setObjectName("primaryButton" if window.theme()["name"] == "Adventurer's Map" else "utilityButton")
    light.clicked.connect(lambda: window.set_theme(ADVENTURERS_MAP))
    window.settings_theme_buttons = [(dark, "Dragon Forge"), (light, "Adventurer's Map")]
    theme_row.addWidget(dark)
    theme_row.addWidget(light)
    theme_row.addStretch(1)
    appearance_card.body.addLayout(theme_row)

    density_combo = _combo(window, UI_DENSITY_OPTIONS, getattr(window.state, "ui_density", "Normal"))
    density_combo.currentTextChanged.connect(window.stage_ui_density)
    appearance_card.body.addLayout(_row("UI density", density_combo))
    appearance_card.body.addWidget(window.default_note("Density is persisted now. Layout-specific density tuning will expand in later cleanup passes."))
    b_layout.addWidget(appearance_card)

    # Guide Presentation.
    guide_card = ReportCard("Guide Presentation", window.theme, badges=[("Persistent", "primary")])
    guide_combo = _combo(window, GUIDE_PRESENTATION_OPTIONS, window.state.guide_presentation)
    guide_combo.currentTextChanged.connect(window.stage_guide_presentation)
    guide_card.body.addLayout(_row("Guide style", guide_combo))
    guide_card.body.addWidget(window.default_note(
        "This controls the gendered or neutral guide voice used for Timmy/Tammy, Johnny/Jenny, and Spike-style guidance. It is independent from Philosophy Lens, so No Philosophy still keeps the selected guide presentation."
    ))
    b_layout.addWidget(guide_card)

    # Local Commander AI (Ollama) — off by default; fully local.
    b_layout.addWidget(build_commander_ai_settings_card(window))

    # Collection Defaults.
    collection_card = ReportCard("Collection Defaults", window.theme, badges=[("App default", "manual")])
    collection_default = window.collection_source_default_display_text()
    collection_combo = _combo(window, APP_COLLECTION_SOURCE_DEFAULT_OPTIONS, collection_default)
    collection_combo.currentTextChanged.connect(window.stage_collection_source_default)
    collection_card.body.addLayout(_row("Default source", collection_combo))

    folder_row = QHBoxLayout()
    folder_label = QLabel("Local path")
    folder_label.setObjectName("helperText")
    folder_label.setMinimumWidth(185)
    folder_value = QLabel(window.state.collection_folder or "collection")
    folder_value.setObjectName("defaultNote")
    folder_value.setWordWrap(True)
    window.settings_collection_folder_label = folder_value
    choose_folder = QPushButton("Choose Collection Folder")
    choose_folder.setObjectName("utilityButton")
    choose_folder.clicked.connect(window.choose_collection_folder)
    choose_files = QPushButton("Choose Collection Files")
    choose_files.setObjectName("utilityButton")
    choose_files.clicked.connect(window.choose_collection_files)
    folder_row.addWidget(folder_label)
    folder_row.addWidget(folder_value, stretch=1)
    folder_row.addWidget(choose_folder)
    folder_row.addWidget(choose_files)
    collection_card.body.addLayout(folder_row)
    collection_card.body.addWidget(window.default_note(
        "Collection source is an app-wide default. Collection Mode will move to Review Setup because it is a current-run choice."
    ))
    b_layout.addWidget(collection_card)

    # Report Folder.
    report_card = ReportCard("Report Folder", window.theme, badges=[("Persistent", "primary")])
    report_row = QHBoxLayout()
    report_label = QLabel("Output folder")
    report_label.setObjectName("helperText")
    report_label.setMinimumWidth(185)
    report_value = QLabel(getattr(window.state, "report_output_folder", "Outputs") or "Outputs")
    report_value.setObjectName("defaultNote")
    report_value.setWordWrap(True)
    window.settings_report_folder_label = report_value
    choose_report = QPushButton("Choose Report Folder")
    choose_report.setObjectName("utilityButton")
    choose_report.clicked.connect(window.choose_report_output_folder)
    report_row.addWidget(report_label)
    report_row.addWidget(report_value, stretch=1)
    report_row.addWidget(choose_report)
    report_card.body.addLayout(report_row)
    report_card.body.addWidget(window.default_note(
        "User Mode Report Viewer will use this folder as the default place to find the latest user-facing handoff."
    ))
    b_layout.addWidget(report_card)


    # Data Setup — compact checklist (both modes); verbose details dev-only.
    data_setup_card = ReportCard("Data Setup", window.theme, badges=[("Runtime", "manual")])
    data_setup_card.body.addWidget(window.default_note(
        "Local data this install needs. ✓ = ready (with size + date); — = still needed."
    ))

    # Compact checklist — the user-facing view (parity row only in Developer Mode).
    _dev = window.is_dev_mode()
    data_setup_checklist_widget = window.make_text(_format_data_setup_checklist(dev_mode=_dev), paper=True)
    data_setup_card.body.addWidget(data_setup_checklist_widget)

    # Verbose folders / next-steps / first-run guidance / PowerShell — Developer Mode only.
    data_setup_details_widget = None
    if window.is_dev_mode():
        details_label = QLabel("Developer details")
        details_label.setObjectName("helperText")
        data_setup_card.body.addWidget(details_label)
        data_setup_details_widget = window.make_text(_format_data_setup_status_text(), paper=True)
        data_setup_card.body.addWidget(data_setup_details_widget)

    def _refresh_data_setup_views():
        _set_text_widget_value(data_setup_checklist_widget, _format_data_setup_checklist(dev_mode=_dev))
        if data_setup_details_widget is not None:
            _set_text_widget_value(data_setup_details_widget, _format_data_setup_status_text())

    data_setup_safe_actions = QHBoxLayout()
    data_setup_safe_actions.addWidget(_make_data_setup_button(
        "Refresh Status",
        _refresh_data_setup_views,
    ))
    data_setup_safe_actions.addWidget(_make_data_setup_button(
        "Open Data Folder",
        _open_runtime_data_folder,
    ))
    if window.is_dev_mode():
        data_setup_safe_actions.addWidget(_make_data_setup_button(
            "Copy Setup Commands",
            _copy_data_setup_commands_to_clipboard,
        ))
    data_setup_card.body.addLayout(data_setup_safe_actions)

    # The guarded download/build actions refresh the checklist on completion, so
    # the "✓ ready" line and date/size update without a manual Refresh click.
    data_setup_guarded_actions = QHBoxLayout()
    scryfall_download_button = _make_data_setup_button("Download / Update Scryfall", lambda: None)
    scryfall_download_button.clicked.connect(
        lambda: _download_scryfall_data_guarded(_DataSetupRefreshProxy(_refresh_data_setup_views), scryfall_download_button)
    )
    data_setup_guarded_actions.addWidget(scryfall_download_button)
    data_setup_guarded_actions.addWidget(_make_data_setup_button(
        "Download / Update Combo Data",
        lambda: _download_combo_data_guarded(_DataSetupRefreshProxy(_refresh_data_setup_views)),
    ))
    data_setup_guarded_actions.addWidget(_make_data_setup_button(
        "Build Combo Index",
        lambda: _build_combo_index_guarded(_DataSetupRefreshProxy(_refresh_data_setup_views)),
    ))
    data_setup_card.body.addLayout(data_setup_guarded_actions)
    b_layout.addWidget(data_setup_card)

    # Developer settings status — Developer Mode only (tester: keep dev-only).
    if window.is_dev_mode():
        dev_card = ReportCard("Developer Settings", window.theme, badges=[("Settings only", "manual")])
        dev_card.body.addWidget(window.make_text(
            "Developer Mode is intentionally controlled from Settings only. No quick switch should be added elsewhere.\n\n"
            f"Current mode: {window.interface_mode_display_text()}\n"
            f"Developer Report Viewer last view: {getattr(window.state, 'developer_report_viewer_last_view', 'User View')}\n"
            f"Settings file: {window.user_settings_path_text()}",
            paper=True,
        ))
        reset_btn = QPushButton("Reset Settings to Defaults")
        reset_btn.setObjectName("utilityButton")
        reset_btn.clicked.connect(window.reset_user_settings_to_defaults)
        dev_card.body.addWidget(reset_btn)
        b_layout.addWidget(dev_card)

    b_layout.addStretch(1)
    content.layout().addWidget(body)
    return scroll
