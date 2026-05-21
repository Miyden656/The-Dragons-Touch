# The Dragon's Touch v0.12.0 — Source-Run Beta Smoke Test Checklist

**Patch:** v0.12.0  
**Track:** v0.12-dev — Source-Run Beta Handoff Polish  
**Purpose:** Verify that a clean source-run beta ZIP can be extracted, launched, set up, used to run one deck analysis, and checked for report output.

This checklist is meant for you or a tester using a freshly extracted copy of the project. It does **not** require an EXE. It does **not** require a BAT file. It does **not** require disabling Windows security.

---

## 0. Tester Info

Fill this out before starting.

- Tester name or nickname:
- Date:
- Windows version:
- Python version, if known:
- Project ZIP/file name tested:
- Deck tested:
- Did you test Combo Awareness? Yes / No

---

## 1. Clean ZIP / Folder Check

Goal: Confirm the tester is starting from a clean source-run package.

- [ ] The ZIP extracts successfully.
- [ ] The extracted folder opens normally.
- [ ] `README_START_HERE.txt` is present.
- [ ] `README.md` is present.
- [ ] `requirements.txt` is present.
- [ ] `desktop_ui_launcher.py` is present.
- [ ] `main.py` is present.
- [ ] `config.py` is present.
- [ ] `ui/` folder is present.
- [ ] `tools/` folder is present.
- [ ] `Decklists/` folder is present.
- [ ] `collection/` folder is present or can be created.
- [ ] `Outputs/` folder is present or can be created.
- [ ] `settings/` folder is present or can be created.

Expected result: The folder looks like a Python source-run project, not an EXE installer package.

---

## 2. Forbidden Handoff Files Check

Goal: Confirm the source-run beta ZIP does not contain old build artifacts or huge local data files.

- [ ] No `.exe` files are present.
- [ ] No `.bat` files are present.
- [ ] No `dist/` folder is present.
- [ ] No `build/` folder is present.
- [ ] No `build_specs/` folder is present.
- [ ] No `_internal/` folder is present.
- [ ] No `MockUP` files or folders are present.
- [ ] No old alpha ZIPs are present.
- [ ] No `__pycache__/` folders are present.
- [ ] No `.pyc` files are present.
- [ ] No huge bundled `scryfall_cards.json` file is present.
- [ ] No huge bundled `combo.json` file is present.
- [ ] No prebuilt huge combo index files are bundled unless intentionally approved.

Expected result: The ZIP is clean and source-run only.

---

## 3. Dependency Install Check

Goal: Confirm dependencies install from `requirements.txt`.

From the project root folder, run:

```powershell
py -m pip install -r requirements.txt
```

Mark results:

- [ ] Command starts successfully.
- [ ] Requirements install completes.
- [ ] No missing `requirements.txt` error.
- [ ] No fatal PySide6 install error.
- [ ] No permission error blocks installation.

Expected result: Dependencies install successfully.

If this fails, capture:

- The full error text.
- Whether Python is installed.
- Whether the `py` command works.
- A screenshot if possible.

---

## 4. Primary Launch Check

Goal: Confirm the normal source-run launcher opens the desktop UI.

From the project root folder, run:

```powershell
py desktop_ui_launcher.py
```

Mark results:

- [ ] Command starts successfully.
- [ ] The Dragon's Touch desktop UI opens.
- [ ] The app opens in User Mode by default.
- [ ] No EXE is required.
- [ ] No BAT file is required.
- [ ] No Windows Application Control EXE block appears.

Expected result: The desktop UI opens normally.

If this fails, capture:

- The full PowerShell error.
- Whether a window briefly opened and closed.
- Screenshot if possible.

---

## 5. Fallback Launch Check

Goal: Confirm the fallback launch path still works if the primary launcher fails.

From the project root folder, run:

```powershell
py ui\dragons_touch_pyside6_workstation.py
```

Mark results:

- [ ] Command starts successfully.
- [ ] The desktop UI opens.
- [ ] The app reaches the same main interface as the primary launch path.

Expected result: The fallback command opens the app.

If this fails, capture the full PowerShell output.

---

## 6. Settings → Data Setup Check

Goal: Confirm the tester can find the data setup area.

Inside the app:

- [ ] Open **Settings**.
- [ ] Find **Data Setup**.
- [ ] Data Setup shows runtime/data status.
- [ ] Data Setup shows Scryfall readiness.
- [ ] Data Setup shows Combo Awareness / combo index readiness.
- [ ] Data Setup explains what is missing if data is not ready.

Expected result: The tester can clearly see what data setup steps are needed.

---

## 7. Scryfall Data Setup Check

Goal: Confirm card data can be downloaded or updated.

Inside **Settings → Data Setup**:

- [ ] Click **Download / Update Scryfall**.
- [ ] Confirm the action if prompted.
- [ ] Wait for the action to complete.
- [ ] Refresh status if needed.
- [ ] Scryfall/card data status changes to ready or present.

Expected result: Basic card data becomes ready.

If this fails, capture:

- Any popup text.
- Any PowerShell output.
- Whether internet was available.
- Whether security software blocked anything.

---

## 8. Combo Data Setup Check

Goal: Confirm Commander Spellbook combo bulk data can be downloaded or updated.

Inside **Settings → Data Setup**:

- [ ] Click **Download / Update Combo Data**.
- [ ] Confirm the action if prompted.
- [ ] Wait for the action to complete.
- [ ] Refresh status if needed.
- [ ] Combo bulk data status changes to ready or present.

Expected result: Combo data download completes.

If this fails, capture the error text and whether the internet connection was active.

---

## 9. Build Combo Index Check

Goal: Confirm local Combo Awareness index can be built from downloaded combo data.

Inside **Settings → Data Setup**:

- [ ] Click **Build Combo Index**.
- [ ] Confirm the action if prompted.
- [ ] Wait for the action to complete.
- [ ] Refresh status if needed.
- [ ] Combo index status changes to ready or present.
- [ ] No parity/developer-only combo build action is required from the tester.

Expected result: Combo Awareness index builds successfully.

If this fails, capture:

- Popup text.
- PowerShell output.
- Whether combo data downloaded successfully first.

---

## 10. Deck Selection Check

Goal: Confirm a deck can be selected for analysis.

Inside the app:

- [ ] Open the deck selection area.
- [ ] Select a deck file from `Decklists/`.
- [ ] Confirm the deck preview loads.
- [ ] Confirm the commander/deck name appears if expected.
- [ ] Confirm the deck count/preview does not look obviously broken.

Expected result: A deck is selected and ready for review setup.

If this fails, capture:

- The deck file name.
- Whether the file is `.txt`, `.dek`, `.csv`, or another format.
- Screenshot of the deck selection screen.

---

## 11. Review Setup Check

Goal: Confirm review settings can be staged without confusion.

Inside the app:

- [ ] Open Review Setup / Review Settings.
- [ ] Select intended bracket if available.
- [ ] Select review direction.
- [ ] Select cut depth.
- [ ] Select guide presentation.
- [ ] Select collection mode/source if applicable.
- [ ] Confirm the run settings summary updates.
- [ ] Confirm the setup can be staged or accepted.

Expected result: Review setup is understandable and does not block the tester.

---

## 12. Run Analysis Check

Goal: Confirm analysis can run from the desktop UI.

Inside the app:

- [ ] Open Run Analysis.
- [ ] Confirm Runtime Data Readiness is visible.
- [ ] Confirm missing data warnings are understandable if present.
- [ ] Start analysis.
- [ ] Analysis completes without crashing.
- [ ] The app does not require internet during analysis except for earlier data setup steps.
- [ ] No EXE-specific path error appears.

Expected result: Analysis completes and creates report output.

If this fails, capture:

- Full PowerShell output.
- Screenshot of the Run Analysis page.
- The deck file used.
- The selected settings.

---

## 13. Output Folder Check

Goal: Confirm report files are created.

After analysis:

- [ ] `Outputs/` folder exists.
- [ ] A new report file appears.
- [ ] A user guided prompt file appears if expected.
- [ ] Output filenames include the deck/commander name if expected.
- [ ] Files are not empty.

Expected result: Analysis creates readable output files.

---

## 14. Report Detection Check

Goal: Confirm the UI detects the new output report.

Inside the app:

- [ ] Run Analysis shows completed output.
- [ ] The report file is detected by the app.
- [ ] The app does not point to an old report by mistake.
- [ ] The app does not say there is no report when a report exists.

Expected result: The newest report can be found from the UI.

---

## 15. Report Viewer Check

Goal: Confirm the report can be opened and read in the app.

Inside Report Viewer:

- [ ] Open the generated report.
- [ ] Report text loads.
- [ ] Report is readable.
- [ ] Sections appear in a useful order.
- [ ] No major formatting issue prevents use.
- [ ] The tester understands at least the main recommendation/cut sections.

Expected result: The tester can read and understand the generated report.

---

## 16. Combo Awareness Result Check

Only complete this section if Combo Awareness data was set up.

- [ ] Combo Awareness does not crash analysis.
- [ ] The report mentions combo awareness when relevant.
- [ ] The report indicates whether relevant combos were found.
- [ ] If no relevant combos are found, the report says so clearly.
- [ ] The report does not claim combo data is ready if the index was not built.

Expected result: Combo Awareness behaves consistently with local data readiness.

---

## 17. No-Combo / Missing-Combo Data Check

Only complete this section if Combo Awareness was not fully set up.

- [ ] App still explains missing combo data clearly.
- [ ] Basic deck analysis still works if Scryfall/basic card data is ready.
- [ ] The app does not crash because combo data is missing.
- [ ] The report does not pretend combo results are available.

Expected result: Missing combo data produces a warning, not a crash.

---

## 18. Tester Failure Capture Checklist

If anything fails, capture as much of this as possible:

- [ ] What step failed?
- [ ] What button or command was used?
- [ ] What did you expect to happen?
- [ ] What actually happened?
- [ ] Full PowerShell text copied into a note.
- [ ] Screenshot of the app error if possible.
- [ ] Screenshot of the folder path if file-related.
- [ ] Deck file name used.
- [ ] Whether Data Setup was completed.
- [ ] Whether Combo Awareness was enabled or expected.
- [ ] Windows version.
- [ ] Python version if known.

---

## 19. Final Tester Result

Choose one:

- [ ] PASS — Clean source-run beta test completed.
- [ ] PASS WITH NOTES — App works, but something was confusing or rough.
- [ ] PARTIAL PASS — App launched, but analysis/report flow did not fully complete.
- [ ] FAIL — App could not launch or could not be meaningfully tested.

Notes:

```text
Write notes here.
```

---

## v0.12.0 Lock Criteria

This checklist supports locking v0.12.0 when:

- [ ] The checklist exists at `docs/source_run_beta_smoke_test_checklist_v0.12.0.md`.
- [ ] The checklist can be followed from a clean extracted source-run package.
- [ ] The checklist covers extraction, dependency install, launch, Data Setup, deck selection, run analysis, output detection, and report viewing.
- [ ] The checklist tells testers what to capture when something fails.
- [ ] No app behavior was changed for v0.12.0.
