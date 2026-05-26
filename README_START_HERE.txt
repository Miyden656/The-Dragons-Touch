# The Dragon's Touch — v0.12.2 Source-Run Beta Quickstart

Welcome to **The Dragon's Touch**, a free community Magic: The Gathering Commander deck-building support tool.

This package is a **source-run beta**.

That means:

- There is no Windows installer.
- There is no EXE handoff.
- You run the app locally with Python.
- First-time data setup happens inside the app under **Settings → Data Setup**.

This v0.12.2 polish is built on the locked v0.11 source-run beta path and the v0.12.0/v0.12.1 tester documentation updates.

---

## Fastest setup path

Open PowerShell in this folder.

Install requirements:

```powershell
py -m pip install -r requirements.txt
```

Launch the app:

```powershell
py desktop_ui_launcher.py
```

Fallback launch if the main launcher does not work:

```powershell
py ui\dragons_touch_pyside6_workstation.py
```

---

## First-time app setup

Inside the app, go to:

```text
Settings → Data Setup
```

Run these in order:

```text
1. Download / Update Scryfall
2. Download / Update Combo Data
3. Build Combo Index
```

Then continue through:

```text
Deck Selection → Review Setup → Run Analysis → Report Viewer
```

---

## Smoke test checklist

Use this if you are testing the beta from a clean extracted folder:

```text
docs\source_run_beta_smoke_test_checklist_v0.12.0.md
```

That checklist walks through extraction, installation, launch, data setup, deck selection, analysis, output creation, report detection, and Report Viewer testing.

---

## First-run troubleshooting

If anything fails, open:

```text
docs\user_docs\first_run_troubleshooting_v0.12.2.md
```

The troubleshooting guide covers:

- Python not installed
- `py` command not found
- dependency install failure
- PySide6 missing
- app window does not open
- Settings → Data Setup confusion
- Scryfall download failure
- Combo download failure
- Combo Index build failure
- deck file loading failure
- Run Analysis failure
- Report Viewer showing no report
- Outputs folder not created
- antivirus or Windows security warning
- what error text or screenshot to send back

---

## What to send back if something fails

Please send:

```text
Step that failed:
Command or button used:
What you expected:
What actually happened:
Error text or screenshot:
Deck file tested:
Did Settings → Data Setup complete? Yes / No / Not sure
Did the main launcher or fallback launcher work? Main / Fallback / Neither
```

---

## Important beta note

This beta is intentionally source-run only.

Do not look for an EXE. Do not look for an installer. The EXE path is paused because unsigned EXE files can be blocked by Windows security on some systems.

Use:

```powershell
py desktop_ui_launcher.py
```

or the fallback:

```powershell
py ui\dragons_touch_pyside6_workstation.py
```

---

## Current status

```text
v0.11 Stable — Source-Run Beta Handoff Lock: PASS / LOCKED
v0.12.0 — Source-Run Beta Smoke Test Checklist: PASS / LOCKED
v0.12.1 — README Quickstart Polish: PASS / LOCKED
v0.12.2 — First-Run Troubleshooting Section: PATCHED / VERIFY BEFORE LOCK
```
