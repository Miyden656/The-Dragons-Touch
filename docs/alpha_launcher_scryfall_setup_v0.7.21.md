# v0.7.21 Alpha Launcher / Scryfall Setup Repair

## Purpose

This patch fixes the clean tester handoff path after the `.pyw` launcher did nothing in the cleaned ZIP.

## Root Cause

The previous `Launch_The_Dragons_Touch.pyw` file imported `Launch_The_Dragons_Touch.py`. During cleanup, the `.py` fallback was removed from the tester ZIP. Because `.pyw` files run without a console, the missing import could look like nothing happened.

## Fix

`Launch_The_Dragons_Touch.pyw` is now self-contained. It directly resolves and runs:

```text
ui/dragons_touch_pyside6_workstation.py
```

It also shows a message box if the UI cannot be opened.

## Visual Studio Code Requirement

Alpha testers do not need Visual Studio Code. VS Code is only a development editor.

They do need:

```text
Python 3
PySide6
```

## Scryfall Data Setup

The clean ZIP may omit the large file:

```text
data/scryfall_cards.json
```

If missing, testers can recreate it by double-clicking:

```text
Download_Scryfall_Data.pyw
```

Command-line fallback:

```text
python download_scryfall_data.py
```

## Preserved Boundary

This patch does not change backend behavior. The preserved workflow remains:

```text
UI staged state
-> guarded confirmation
-> subprocess/main.py
-> CLI input bridge
-> backend output folder
-> report detection
-> Report Viewer plain-text load
```
