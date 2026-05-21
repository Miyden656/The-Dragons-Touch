"""
v0.11.4.2-dev — First-run data setup service for The Dragon's Touch.

Purpose:
- Provide a backend/service foundation for future Settings/Data Setup UI.
- Detect whether required runtime data exists.
- Download Scryfall default_cards data to data/scryfall_cards.json.
- Download Commander Spellbook combo data to data/combo.json.
- Provide clear next-step guidance for building combo indexes.

Hotfix:
- Use cleaner API request headers for Scryfall.
- Select Scryfall default_cards from the bulk-data endpoint.
- Print useful HTTP error bodies instead of opaque tracebacks.

This module does not run automatically on app startup.
It is safe for the UI or tools to call intentionally.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ui.services.app_paths import ensure_runtime_folders, get_runtime_paths


SCRYFALL_BULK_DATA_API = "https://api.scryfall.com/bulk-data"
SCRYFALL_DEFAULT_CARDS_BULK_TYPE = "default_cards"
COMMANDER_SPELLBOOK_VARIANTS_URL = "https://json.commanderspellbook.com/variants.json"

USER_AGENT = "The-Dragons-Touch/0.11"
ACCEPT_JSON = "application/json;q=0.9,*/*;q=0.8"


@dataclass(frozen=True)
class RuntimeDataFileStatus:
    label: str
    path: str
    exists: bool
    size_bytes: int
    required_for: str


@dataclass(frozen=True)
class RuntimeDataSetupStatus:
    runtime_root: str
    data_dir: str
    scryfall_cards: RuntimeDataFileStatus
    commander_spellbook_bulk: RuntimeDataFileStatus
    combo_index: RuntimeDataFileStatus
    combo_index_parity: RuntimeDataFileStatus
    ready_for_basic_analysis: bool
    ready_for_combo_analysis: bool
    next_steps: list[str]


def _file_status(label: str, path: Path, required_for: str) -> RuntimeDataFileStatus:
    exists = path.exists() and path.is_file()
    return RuntimeDataFileStatus(
        label=label,
        path=str(path),
        exists=exists,
        size_bytes=path.stat().st_size if exists else 0,
        required_for=required_for,
    )


def get_data_setup_status() -> RuntimeDataSetupStatus:
    """Return current runtime data status for tools or future UI."""
    paths = ensure_runtime_folders()

    scryfall = _file_status(
        "Scryfall card data",
        paths.scryfall_cards_json,
        "legality, card lookup, strategy detection, cuts, replacements, reports",
    )
    combo_bulk = _file_status(
        "Commander Spellbook bulk combo data",
        paths.commander_spellbook_bulk_json,
        "building local combo indexes",
    )
    combo_index = _file_status(
        "Commander Spellbook combo index",
        paths.combo_index_json,
        "combo analysis in reports",
    )
    combo_parity = _file_status(
        "Commander Spellbook parity combo index",
        paths.combo_index_parity_json,
        "developer validation and parity checks",
    )

    next_steps: list[str] = []
    if not scryfall.exists:
        next_steps.append("Download Scryfall card data.")
    if not combo_bulk.exists:
        next_steps.append("Download Commander Spellbook combo data.")
    if combo_bulk.exists and not combo_index.exists:
        next_steps.append("Build Commander Spellbook combo index.")
    if combo_bulk.exists and not combo_parity.exists:
        next_steps.append("Build parity combo index if Developer Mode validation is needed.")

    return RuntimeDataSetupStatus(
        runtime_root=str(paths.root),
        data_dir=str(paths.data_dir),
        scryfall_cards=scryfall,
        commander_spellbook_bulk=combo_bulk,
        combo_index=combo_index,
        combo_index_parity=combo_parity,
        ready_for_basic_analysis=scryfall.exists,
        ready_for_combo_analysis=scryfall.exists and combo_index.exists,
        next_steps=next_steps,
    )


def status_to_dict(status: RuntimeDataSetupStatus | None = None) -> dict[str, Any]:
    """Return data setup status as a plain dictionary."""
    return asdict(status or get_data_setup_status())


def write_data_setup_status_json(path: Path | None = None) -> Path:
    """Write current data setup status to a JSON file for diagnostics."""
    paths = ensure_runtime_folders()
    output_path = path or (paths.settings_dir / "runtime_data_setup_status.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(status_to_dict(), indent=2), encoding="utf-8")
    return output_path


def _make_request(url: str, *, accept: str = ACCEPT_JSON) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": accept,
        },
    )


def _read_http_error_body(exc: urllib.error.HTTPError, limit: int = 2000) -> str:
    try:
        body = exc.read(limit)
    except Exception:
        return ""

    try:
        return body.decode("utf-8", errors="replace")
    except Exception:
        return repr(body)


def _open_url(request: urllib.request.Request, *, timeout: int):
    try:
        return urllib.request.urlopen(request, timeout=timeout)
    except urllib.error.HTTPError as exc:
        body = _read_http_error_body(exc)
        message = f"HTTP Error {exc.code}: {exc.reason}"
        if body:
            message += f"\nResponse body:\n{body}"
        raise RuntimeError(message) from exc


def _download_file(url: str, destination: Path, *, overwrite: bool = False, chunk_size: int = 1024 * 1024 * 8) -> Path:
    """
    Download a file in chunks.

    The final destination is only replaced after a successful temporary download
    and a lightweight JSON sanity check.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists() and not overwrite:
        raise FileExistsError(
            f"Destination already exists: {destination}\n"
            "Use overwrite=True if you intentionally want to replace it."
        )

    with tempfile.TemporaryDirectory() as tmp:
        temp_path = Path(tmp) / destination.name

        request = _make_request(url, accept="application/json,*/*;q=0.8")

        with _open_url(request, timeout=180) as response:
            with temp_path.open("wb") as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)

        _quick_json_sanity_check(temp_path)
        shutil.copy2(temp_path, destination)

    return destination


def _quick_json_sanity_check(path: Path) -> None:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Downloaded file does not exist: {path}")

    if path.stat().st_size <= 0:
        raise ValueError(f"Downloaded file is empty: {path}")

    with path.open("rb") as f:
        first = f.read(1)

    if first not in (b"{", b"["):
        raise ValueError(
            "Downloaded file does not appear to be JSON. "
            "Expected first character to be '{' or '['."
        )


def _load_json_url(url: str) -> dict[str, Any]:
    request = _make_request(url, accept="application/json")
    with _open_url(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def _get_scryfall_default_cards_download_uri_from_bulk_list() -> str:
    payload = _load_json_url(SCRYFALL_BULK_DATA_API)

    for item in payload.get("data", []):
        if item.get("type") == SCRYFALL_DEFAULT_CARDS_BULK_TYPE:
            uri = item.get("download_uri")
            if not uri:
                raise RuntimeError("Scryfall default_cards entry did not include download_uri.")
            return str(uri)

    raise RuntimeError("Could not find default_cards in Scryfall bulk-data response.")


def _get_scryfall_default_cards_download_uri() -> str:
    """
    Return the current Scryfall default_cards download URI.

    Path:
      https://api.scryfall.com/bulk-data
      then select type == default_cards.
    """
    try:
        return _get_scryfall_default_cards_download_uri_from_bulk_list()
    except Exception as exc:
        raise RuntimeError(
            "Could not resolve Scryfall default_cards download URI.\n"
            "The Download / Update Scryfall action expects Scryfall bulk-data "
            "type == default_cards."
        ) from exc

def download_scryfall_cards(*, overwrite: bool = False) -> Path:
    """
    Download Scryfall default_cards bulk data into the runtime data folder.

    Output:
      data/scryfall_cards.json
    """
    paths = ensure_runtime_folders()
    print("Downloading Scryfall default_cards bulk data...")
    download_uri = _get_scryfall_default_cards_download_uri()
    output = _download_file(download_uri, paths.scryfall_cards_json, overwrite=overwrite)
    print(f"Saved Scryfall default_cards to {output}")
    write_data_setup_status_json()
    return output


def download_commander_spellbook_combo_bulk(*, overwrite: bool = False) -> Path:
    """
    Download Commander Spellbook combo variants into the runtime data folder.

    Output:
      data/combo.json
    """
    paths = ensure_runtime_folders()
    output = _download_file(COMMANDER_SPELLBOOK_VARIANTS_URL, paths.commander_spellbook_bulk_json, overwrite=overwrite)
    write_data_setup_status_json()
    return output


def combo_index_build_commands() -> dict[str, str]:
    """
    Return command guidance for building local combo indexes.

    The actual build process remains in tools/build_combo_index.py for now.
    Later v0.11 work can call the builder directly or expose UI buttons.
    """
    paths = ensure_runtime_folders()

    normal = (
        f'py tools\\build_combo_index.py '
        f'--input "{paths.commander_spellbook_bulk_json}" '
        f'--output "{paths.combo_index_json}"'
    )

    parity = (
        f'py tools\\build_combo_index.py '
        f'--input "{paths.commander_spellbook_bulk_json}" '
        f'--output "{paths.combo_index_parity_json}" '
        f'--include-non-commander-legal'
    )

    return {
        "normal_combo_index": normal,
        "parity_combo_index": parity,
    }


def print_data_setup_status() -> None:
    """Console-friendly status print for source or EXE smoke testing."""
    status = get_data_setup_status()

    print("The Dragon's Touch Data Setup Status")
    print("====================================")
    print(f"Runtime root: {status.runtime_root}")
    print(f"Data folder:  {status.data_dir}")
    print(f"Ready for basic analysis: {status.ready_for_basic_analysis}")
    print(f"Ready for combo analysis: {status.ready_for_combo_analysis}")
    print()

    for item in [
        status.scryfall_cards,
        status.commander_spellbook_bulk,
        status.combo_index,
        status.combo_index_parity,
    ]:
        print(f"{item.label}:")
        print(f"  path: {item.path}")
        print(f"  exists: {item.exists}")
        print(f"  size: {item.size_bytes:,} bytes")
        print(f"  required for: {item.required_for}")
        print()

    if status.next_steps:
        print("Next steps:")
        for step in status.next_steps:
            print(f"- {step}")
        print()

    commands = combo_index_build_commands()
    print("Combo index build commands:")
    for label, command in commands.items():
        print(f"- {label}: {command}")
