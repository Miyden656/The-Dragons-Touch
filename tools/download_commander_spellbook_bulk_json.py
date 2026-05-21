#!/usr/bin/env python3
r"""
Download Commander Spellbook bulk combo JSON for The Dragon's Touch.

Default behavior:
- Downloads https://json.commanderspellbook.com/variants.json
- Saves it as data/combo.json
- Does not load the full JSON into memory
- Does not create a manifest file
- Does not modify git or commit anything

Usage from project root:
    py tools\download_commander_spellbook_bulk_json.py --overwrite
"""

from __future__ import annotations

import argparse
import shutil
import tempfile
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_URL = "https://json.commanderspellbook.com/variants.json"
DEFAULT_DEST_DIR = PROJECT_ROOT / "data"
DEFAULT_DEST_NAME = "combo.json"


def quick_json_sanity_check(path: Path) -> None:
    """
    Lightweight JSON sanity check.

    This intentionally does not fully parse the file because the Commander
    Spellbook bulk JSON can be large.
    """
    if not path.exists():
        raise FileNotFoundError(f"Downloaded file does not exist: {path}")

    if not path.is_file():
        raise ValueError(f"Downloaded path is not a file: {path}")

    if path.stat().st_size <= 0:
        raise ValueError(f"Downloaded file is empty: {path}")

    with path.open("rb") as f:
        first = f.read(1)

    if first not in (b"{", b"["):
        raise ValueError(
            "Downloaded file does not appear to be JSON. "
            "Expected first character to be '{' or '['."
        )


def download_file(url: str, temp_path: Path, chunk_size: int = 1024 * 1024 * 8) -> None:
    """Download a file in chunks to avoid loading the full file into memory."""
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "The-Dragons-Touch/0.11 Commander Spellbook bulk importer"
        },
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        status = getattr(response, "status", None)
        if status and status >= 400:
            raise RuntimeError(f"Download failed with HTTP status {status}")

        total = response.headers.get("Content-Length")
        total_bytes = int(total) if total and total.isdigit() else None

        downloaded = 0
        with temp_path.open("wb") as f:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break

                f.write(chunk)
                downloaded += len(chunk)

                if total_bytes:
                    percent = downloaded / total_bytes * 100
                    print(
                        f"\rDownloading... {downloaded:,}/{total_bytes:,} bytes ({percent:.1f}%)",
                        end="",
                    )
                else:
                    print(f"\rDownloading... {downloaded:,} bytes", end="")

    print()


def download_commander_spellbook_bulk_json(
    *,
    url: str,
    dest_dir: Path,
    dest_name: str,
    overwrite: bool,
) -> Path:
    """Download Commander Spellbook bulk JSON and store it locally."""
    dest_dir = dest_dir.expanduser().resolve()
    dest_path = dest_dir / dest_name

    dest_dir.mkdir(parents=True, exist_ok=True)

    if dest_path.exists() and not overwrite:
        raise FileExistsError(
            f"Destination already exists: {dest_path}\n"
            "Use --overwrite if you intentionally want to replace it."
        )

    with tempfile.TemporaryDirectory() as tmp:
        temp_path = Path(tmp) / dest_name

        print("Downloading Commander Spellbook bulk combo JSON")
        print(f"Source URL:  {url}")
        print(f"Destination: {dest_path}")

        download_file(url, temp_path)
        quick_json_sanity_check(temp_path)

        shutil.copy2(temp_path, dest_path)

    print("Download complete.")
    print(f"Saved file: {dest_path}")
    print(f"Size:       {dest_path.stat().st_size:,} bytes")

    return dest_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Download Commander Spellbook bulk combo JSON into "
            "The Dragon's Touch data folder."
        )
    )

    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"Commander Spellbook bulk JSON endpoint. Default: {DEFAULT_URL}",
    )

    parser.add_argument(
        "--dest-dir",
        default=str(DEFAULT_DEST_DIR),
        help=f"Destination folder. Default: {DEFAULT_DEST_DIR}",
    )

    parser.add_argument(
        "--dest-name",
        default=DEFAULT_DEST_NAME,
        help=f"Destination file name. Default: {DEFAULT_DEST_NAME}",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace the existing destination file if it already exists.",
    )

    args = parser.parse_args()

    try:
        download_commander_spellbook_bulk_json(
            url=args.url,
            dest_dir=Path(args.dest_dir),
            dest_name=args.dest_name,
            overwrite=args.overwrite,
        )
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
