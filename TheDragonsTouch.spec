# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for The Dragon's Touch — community-release EXE bundle.

Builds a one-folder distributable that includes:
  - The PySide6 desktop UI launcher
  - All Python modules (ui/, analysis/, build_from_collection/, reports/, etc.)
  - The active strategy_knowledge JSON profiles (archive subfolder excluded)
  - Small static data files (data/combo.json)

Intentionally NOT bundled (user downloads or stages these inside the app):
  - data/scryfall_cards.json — too large (~100 MB), changes weekly. The app's
    Settings → Data Setup → Download Scryfall button fetches it on first run.
  - data/combo_index.json — built locally via Settings → Build Combo Index.
  - collection/ — the user's own card collection lives outside the EXE bundle.
  - Outputs/ — generated per-run, written next to the EXE at runtime.
  - tests/, docs/, archive subfolders — not needed in distribution.

Build from project root:
    pip install pyinstaller
    pyinstaller TheDragonsTouch.spec

Output:
    dist/TheDragonsTouch/  ← copy this whole folder to distribute
        TheDragonsTouch.exe   ← double-click to launch
        ... (DLLs, Python interpreter, bundled modules)
"""
from pathlib import Path

# SPECPATH is provided by PyInstaller; it's the directory containing this spec.
PROJECT_ROOT = Path(SPECPATH).resolve()

# ---------------------------------------------------------------------------
# Data files to bundle. Format: (source_path_on_disk, dest_path_inside_bundle)
# ---------------------------------------------------------------------------
datas = []

# Bundle strategy_knowledge .json files, skipping archive/ (memory-only history).
for jsonfile in PROJECT_ROOT.glob("strategy_knowledge/**/*.json"):
    if "archive" in jsonfile.parts:
        continue
    rel_dir = jsonfile.relative_to(PROJECT_ROOT).parent
    datas.append((str(jsonfile), str(rel_dir)))

# Small static data files used by the app.
combo_static = PROJECT_ROOT / "data" / "combo.json"
if combo_static.exists():
    datas.append((str(combo_static), "data"))

# Bundle the LEGAL.md and README.md so they ship with the EXE.
for doc in ("LEGAL.md", "README.md", "CHANGELOG.md", "VERSION"):
    p = PROJECT_ROOT / doc
    if p.exists():
        datas.append((str(p), "."))

# ---------------------------------------------------------------------------
# Hidden imports — PySide6 sometimes needs explicit submodule declarations
# when PyInstaller's static analyzer can't follow dynamic imports.
# ---------------------------------------------------------------------------
hiddenimports = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
]

# ---------------------------------------------------------------------------
# Things to explicitly exclude from the build (saves size, avoids confusion).
# ---------------------------------------------------------------------------
excludes = [
    "tests",
    "tkinter",  # Not used; PySide6 is the UI toolkit.
    "matplotlib",
    "numpy",
    "pandas",
]

a = Analysis(
    ["Launch_The_Dragons_Touch.pyw"],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TheDragonsTouch",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI app — no console window.
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon="dragon_icon.ico",  # Uncomment when an .ico is added to the repo.
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="TheDragonsTouch",
)
