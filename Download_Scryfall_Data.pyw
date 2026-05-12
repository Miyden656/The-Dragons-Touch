"""No-console Scryfall data downloader for alpha testers.

This recreates data/scryfall_cards.json without requiring Visual Studio Code.
It uses the same Scryfall bulk-data endpoint as download_scryfall_data.py.
"""
from __future__ import annotations

import json
import os
import sys
import traceback
import urllib.request
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import messagebox
except Exception:  # pragma: no cover - fallback for unusual Python installs
    tk = None
    messagebox = None

ROOT_DIR = Path(__file__).resolve().parent
DATA_FOLDER = ROOT_DIR / "data"
SCRYFALL_BULK_DATA_URL = "https://api.scryfall.com/bulk-data"
OUTPUT_FILE = DATA_FOLDER / "scryfall_cards.json"

HEADERS = {
    "User-Agent": "The-Dragons-Touch-v0.7-alpha (personal community project)",
    "Accept": "application/json;q=0.9,*/*;q=0.8",
}


def _message(title: str, body: str, kind: str = "info") -> None:
    if messagebox is None or tk is None:
        print(f"{title}\n{body}", file=sys.stderr if kind == "error" else sys.stdout)
        return
    root = tk.Tk()
    root.withdraw()
    if kind == "error":
        messagebox.showerror(title, body)
    else:
        messagebox.showinfo(title, body)
    root.destroy()


def _download_json(url: str) -> dict:
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def _download_file(url: str, output_path: Path) -> None:
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request) as response:
        data = response.read()
    output_path.write_bytes(data)


def main() -> int:
    os.chdir(ROOT_DIR)
    proceed = True
    if messagebox is not None and tk is not None:
        root = tk.Tk()
        root.withdraw()
        proceed = messagebox.askokcancel(
            "Download Scryfall Data",
            "This will download the Scryfall default_cards bulk data and save it as:\n\n"
            f"{OUTPUT_FILE}\n\n"
            "It requires an internet connection and may take a little while."
        )
        root.destroy()

    if not proceed:
        return 0

    try:
        DATA_FOLDER.mkdir(exist_ok=True)
        bulk_data = _download_json(SCRYFALL_BULK_DATA_URL)
        default_cards = None
        for item in bulk_data.get("data", []):
            if item.get("type") == "default_cards":
                default_cards = item
                break

        if default_cards is None or not default_cards.get("download_uri"):
            _message(
                "Scryfall Download Failed",
                "Could not find Scryfall default_cards bulk data.",
                kind="error",
            )
            return 1

        _download_file(default_cards["download_uri"], OUTPUT_FILE)
        _message(
            "Scryfall Data Download Complete",
            "Saved Scryfall card data to:\n\n"
            f"{OUTPUT_FILE}\n\n"
            "You can now launch The Dragon's Touch again."
        )
        return 0
    except Exception:
        _message(
            "Scryfall Download Failed",
            "The Scryfall data download failed.\n\n"
            "Make sure you have an internet connection.\n\n"
            "Details:\n" + traceback.format_exc(),
            kind="error",
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
