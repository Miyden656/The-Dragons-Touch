# The Dragon's Touch v0.12.2 — First-Run Troubleshooting Guide

This guide is for testers using the **source-run beta** package.

Use it when a tester cannot install requirements, launch the app, complete Settings → Data Setup, run analysis, or open a report.

This guide does **not** ask testers to disable Windows security. It does **not** point testers toward an EXE.

---

## What to send back if anything fails

Ask the tester to capture these details:

- What step failed.
- What command they ran, if any.
- What button they clicked, if any.
- What they expected to happen.
- What actually happened.
- Any copied error text.
- A screenshot, if possible.
- Their Windows version, if known.
- Their Python version, if known.
- The deck file name, if the failure happened during deck loading or analysis.
- Whether Settings → Data Setup had already been completed.

---

## 1. Python is not installed

**What the tester sees**

PowerShell says Python is not recognized, or Windows opens the Microsoft Store when they run `py`.

**Likely cause**

Python is not installed, or the Windows Python launcher is not available.

**What to try**

Install a current Python 3 version for Windows, then close and reopen PowerShell.

After installing, test with:

```powershell
py --version
```

**What to report back if it still fails**

Send a screenshot or copied text from PowerShell after running `py --version`.

---

## 2. `py` command not found

**What the tester sees**

PowerShell says:

```text
py is not recognized as the name of a cmdlet, function, script file, or operable program
```

**Likely cause**

The Windows Python launcher is missing or Python was installed without launcher support.

**What to try**

Try:

```powershell
python --version
```

If that works, use `python` instead of `py` for the tester commands.

Example:

```powershell
python -m pip install -r requirements.txt
python desktop_ui_launcher.py
```

**What to report back if it still fails**

Send the result of both:

```powershell
py --version
python --version
```

---

## 3. Dependency install fails

**What the tester sees**

This command fails:

```powershell
py -m pip install -r requirements.txt
```

**Likely cause**

PowerShell is not opened in the project folder, Python/pip is not ready, internet access is blocked, or a package install failed.

**What to try**

Confirm PowerShell is open in the folder that contains `requirements.txt`.

Then run:

```powershell
py -m pip --version
py -m pip install -r requirements.txt
```

**What to report back if it still fails**

Copy the last 20-40 lines of the install error, especially anything mentioning PySide6, permission denied, SSL, network, or no matching distribution.

---

## 4. PySide6 is missing

**What the tester sees**

The app does not open and an error mentions:

```text
ModuleNotFoundError: No module named 'PySide6'
```

**Likely cause**

Requirements were not installed successfully or PowerShell is using a different Python installation than expected.

**What to try**

Run:

```powershell
py -m pip install -r requirements.txt
py -c "import PySide6; print('PySide6 import works')"
```

**What to report back if it still fails**

Send the full error from the import test above.

---

## 5. App window does not open

**What the tester sees**

This command runs but no desktop window appears:

```powershell
py desktop_ui_launcher.py
```

**Likely cause**

Dependency issue, wrong folder, launcher issue, or an early UI startup error.

**What to try**

First try the fallback launch:

```powershell
py ui\dragons_touch_pyside6_workstation.py
```

If fallback works, report that the main launcher failed but the fallback launcher worked.

If neither works, run the command again and copy any PowerShell output.

**What to report back if it still fails**

Send which launcher was used and any visible error text.

---

## 6. Settings → Data Setup is missing or confusing

**What the tester sees**

The app opens, but the tester cannot find where to download/update Scryfall data, download/update Combo data, or build the Combo Index.

**Likely cause**

The tester is on the wrong page, the app window is too small, or the current UI wording is unclear.

**What to try**

Open the Settings page and look for **Data Setup**.

The expected setup order is:

```text
1. Download / Update Scryfall
2. Download / Update Combo Data
3. Build Combo Index
```

**What to report back if it still fails**

Send a screenshot of the Settings page.

---

## 7. Scryfall download fails

**What the tester sees**

The Scryfall setup button fails, stalls, or reports an error.

**Likely cause**

Internet/network issue, file permission issue, or download/runtime path issue.

**What to try**

Refresh Data Status, confirm the app is in the extracted project folder, then try the Scryfall action once more.

Do not repeatedly spam the button.

**What to report back if it still fails**

Send the error text, a screenshot of Data Setup, and whether a file appeared at:

```text
data\scryfall_cards.json
```

---

## 8. Combo download fails

**What the tester sees**

The Combo data setup button fails, stalls, or reports an error.

**Likely cause**

Internet/network issue, Commander Spellbook data download issue, file permission issue, or runtime path issue.

**What to try**

Refresh Data Status and try the Combo data action once more.

**What to report back if it still fails**

Send the error text, a screenshot of Data Setup, and whether a file appeared at:

```text
data\combo.json
```

---

## 9. Build Combo Index fails

**What the tester sees**

Download worked, but Build Combo Index fails.

**Likely cause**

Combo bulk data is missing, incomplete, or not where the app expects it.

**What to try**

Run the setup order again:

```text
1. Download / Update Combo Data
2. Build Combo Index
```

Then refresh Data Status.

**What to report back if it still fails**

Send the error text and whether these files exist:

```text
data\combo.json
data\commander_spellbook\combo_index.json
```

---

## 10. Deck file does not load

**What the tester sees**

The deck cannot be selected, previewed, or parsed.

**Likely cause**

Unsupported decklist format, blank file, unusual card formatting, sideboard/category text, or file location issue.

**What to try**

Try a simple decklist from the `Decklists` folder if one is included.

If the tester used their own decklist, ask them to send the deck file or the first 20 lines of it.

**What to report back if it still fails**

Send the deck file name, format/source, and the visible error text.

---

## 11. Run Analysis fails

**What the tester sees**

The app launches and a deck loads, but Run Analysis crashes, stops, or never produces output.

**Likely cause**

Missing data, deck parsing edge case, runtime path issue, or analysis bug.

**What to try**

Confirm Settings → Data Setup status first.

Then try running analysis with a known simple decklist.

**What to report back if it still fails**

Send:

- deck file name
- selected Review Setup options
- whether Scryfall data was ready
- whether Combo Index was ready
- copied error text or screenshot

---

## 12. Report Viewer has no report

**What the tester sees**

Analysis appears to finish, but Report Viewer is empty or does not show the new report.

**Likely cause**

Report detection issue, output folder issue, or the analysis did not actually complete.

**What to try**

Open the `Outputs` folder and check whether report files were created.

Look for files ending in:

```text
_deck_report.md
_user_guided_prompt.md
```

**What to report back if it still fails**

Send a screenshot or list of the file names in `Outputs`.

---

## 13. Outputs folder not created

**What the tester sees**

The app runs, but there is no `Outputs` folder after analysis.

**Likely cause**

Analysis did not complete, the app could not write files, or PowerShell/app was launched from the wrong folder.

**What to try**

Confirm the tester launched the app from the project root folder.

Then create an empty `Outputs` folder manually and try again.

**What to report back if it still fails**

Send the project folder path, deck file name, and error text.

---

## 14. Antivirus or Windows security warning

**What the tester sees**

Windows or antivirus warns about the ZIP, Python script, or unknown files.

**Likely cause**

Local security policy, downloaded ZIP warning, or antivirus caution around scripts.

**What to try**

Do not ask testers to disable Windows security.

The expected beta path is source-run Python, not EXE execution. If their system blocks the package, ask them to stop and report the warning.

**What to report back if it still fails**

Send a screenshot of the warning and the exact file it mentions.

---

## 15. Tester does not know what to send back

Send this minimum report:

```text
Step that failed:
Command or button used:
What I expected:
What happened:
Error text or screenshot:
Deck file tested:
Did Settings → Data Setup complete? Yes / No / Not sure
Did the main launcher or fallback launcher work? Main / Fallback / Neither
```

---

## v0.12.2 Lock Criteria

v0.12.2 is lockable when:

- This troubleshooting guide exists.
- README_START_HERE.txt points testers to this guide.
- The guide covers common first-run failures.
- Each issue includes what the tester sees, likely cause, what to try, and what to report back.
- The guide does not ask testers to disable Windows security.
- The guide does not redirect testers to the EXE path.
- No app behavior changes are required.
