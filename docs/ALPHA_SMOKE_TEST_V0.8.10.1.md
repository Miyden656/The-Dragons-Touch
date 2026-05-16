# v0.8.10.1-alpha — Alpha Tester Smoke Test Script

Give testers this simple flow if you want them to verify the build quickly.

## 1. Launch

Open the app from the extracted folder.

Expected result:

- The app opens.
- User-Facing Mode is the default.
- No setup/download prompt is required.

## 2. Run a normal review

- Pick an included decklist.
- Leave Combo Awareness disabled.
- Run Analysis.

Expected result:

- Report Viewer opens after the run.
- No Combo Awareness files are generated.
- No API calls are made.

## 3. Run Combo Awareness report-section mode

- Pick an included decklist.
- Enable Combo Awareness report-section mode.
- Run Analysis.

Expected result:

- The normal deck report includes `## Combo Awareness`.
- The user-guided prompt includes `## Combo Awareness AI Handoff Addendum`.
- The report includes relevant potential combo count.
- The report includes collection-completable count or collection-not-loaded note.
- No separate combo files are needed for AI handoff.

## 4. Report feedback

Ask testers to send:

- What deck they used.
- Whether the app launched without setup.
- Whether Run Analysis completed.
- Whether Report Viewer opened.
- Whether any error appeared.
- Whether the report made sense as a normal player.
