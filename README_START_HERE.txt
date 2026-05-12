The Dragon's Touch - Start Here
v0.7.22 Alpha Tester Feedback Packet

Purpose
-------
This is the v0.7 Modular Alpha checkpoint of The Dragon's Touch.

This folder is meant to be opened and tested without Visual Studio Code. The
supported alpha launch path is:

  Launch_The_Dragons_Touch.pyw

Double-click that file to open the desktop app.

Current Stable Boundary
-----------------------
The stable v0.6.8.5 backend workflow is preserved. The v0.7 work modularized
and hardened the desktop UI; it did not replace the backend.

Preserved workflow:

  UI staged state
  -> guarded confirmation
  -> subprocess/main.py
  -> CLI input bridge
  -> backend output folder
  -> report detection
  -> Report Viewer plain-text load

Do not bypass main.py.
Do not silently execute backend commands.
Do not create a second backend workflow.

Quick Start
-----------
1. Open this project folder.
2. If data/scryfall_cards.json is missing, double-click:

     Download_Scryfall_Data.pyw

3. Double-click:

     Launch_The_Dragons_Touch.pyw

4. On Deck Selection, choose one Commander deck file.
5. On Review Setup, choose the review direction, prompt mode, intended bracket,
   and budget note.
6. On Philosophy Lens, choose how the review should frame the deck.
7. On Collection Source, choose whether collection data should be used.
8. Go to Run Analysis.
9. Click Run main.py with Guarded Confirmation.
10. Read the guarded run message before confirming.
11. After the run completes, open the generated report in Report Viewer.
12. Copy or save the generated report.
13. Run the generated report through an AI follow-up review using:

     docs/alpha_ai_followup_prompt_v0.7.22.md

14. Send feedback using:

     docs/alpha_tester_feedback_packet_v0.7.22.md

Required Alpha Tester Flow
--------------------------
Alpha testing is not just opening the app.

Please complete the full test path:

  Extract ZIP
  -> Download Scryfall data if needed
  -> Launch app with Launch_The_Dragons_Touch.pyw
  -> Select deck
  -> Stage Review Setup
  -> Stage Philosophy Lens
  -> Stage Collection Source
  -> Run Analysis with guarded confirmation
  -> Confirm report appears in Report Viewer
  -> Run the generated report through AI follow-up review
  -> Send feedback and screenshots/errors if anything fails

AI Follow-Up Review Requirement
-------------------------------
After generating a Dragon's Touch report, alpha testers should run the report
through an AI follow-up review. This helps test whether the generated report is
clear, useful, and strong enough to support a guided deck conversation.

Use this prompt file:

  docs/alpha_ai_followup_prompt_v0.7.22.md

The AI follow-up should:

  Confirm receipt of the generated report
  Summarize the report
  Identify commander, deck status, strategy read, and review candidates
  Ask for pilot intent one section at a time
  Correct the strategy read if the pilot says the deck is trying to do something else
  Treat all cuts/replacements as guidance, not automatic deck edits
  Respect legality, budget, collection mode, color identity, table power, and pilot intent

Scryfall Data
-------------
The clean ZIP does not need to include the large local card database file:

  data/scryfall_cards.json

If that file is missing, recreate it from the project root by double-clicking:

  Download_Scryfall_Data.pyw

Command-line fallback:

  python download_scryfall_data.py

This requires an internet connection. The downloader recreates:

  data/scryfall_cards.json

Keep these files in the root project folder:

  download_scryfall_data.py
  Download_Scryfall_Data.pyw

Requirements
------------
You do not need Visual Studio Code.

Visual Studio Code is only a development editor. Alpha testers should be able to
launch the app with Launch_The_Dragons_Touch.pyw and recreate Scryfall data with
Download_Scryfall_Data.pyw.

For this alpha setup, you do need:

  Python 3
  PySide6
  Internet connection for the Scryfall download step

If PySide6 is missing, install it from the project folder with:

  python -m pip install PySide6

If the project later includes requirements.txt, use:

  python -m pip install -r requirements.txt

Launcher Decision
-----------------
Supported v0.7 alpha launch path:

  Launch_The_Dragons_Touch.pyw

Developer fallback only:

  Launch_The_Dragons_Touch.py
  Launch_The_Dragons_Touch.bat

Desktop shortcut support is deferred. Windows Smart App Control blocked the
shortcut/batch path during testing, so shortcut creation is not a supported
v0.7 alpha requirement.

Do not disable Smart App Control just to run this tool.

Sample Decklists
----------------
This alpha package includes a small set of sample decklists in the Decklists folder.

These are not meant to be the only decks you can test. They are included as known test cases so you can quickly confirm the app workflow works from start to finish.

Current sample deck purposes:

1. Miirym Duplicate Legality Test
   - Tests illegal duplicate reporting.
   - Includes 2 copies of Life Finds a Way.
   - Useful for confirming duplicate legality fixes appear before ordinary cut candidates.

2. Phelia Bracket 2 Test
   - Tests lower-power / bracket-sensitive review behavior.
   - Useful for checking whether the report respects a more casual intended table.

3. Voja Build-Up Test
   - Tests an incomplete deck that needs 3 more cards to become legal.
   - Useful for checking build-up / incomplete deck handling.

4. Inga & Esika Companion Test
   - Tests companion or companion-style restriction handling.
   - Useful for checking whether companion context survives preview, setup, and report generation.

5. Toggo / Keskit Partner Test
   - Tests partner commander handling.
   - Useful for checking landfall, artifact, token, and sacrifice package recognition.

You may also add your own Commander decklists to the Decklists folder.

Decklist File Format
--------------------
The current sample decklists were created as plain text files exported from Archidekt.

They were made either by:
- copying and pasting the Archidekt text export into a .txt file, or
- downloading/exporting the deck as a .txt file from Archidekt.

You are welcome to test decklist .txt exports from other deckbuilding sites too.

If you want to test your own deck:

1. Export or copy the decklist as plain text.
2. Save it as a .txt file.
3. Put it in the Decklists folder.
4. Open The Dragon's Touch.
5. Choose that deck file from Deck Selection.

Trying other deckbuilding sites is encouraged. If a site exports a format that The Dragon's Touch does not understand, that is useful alpha feedback.

Please report:
- which deckbuilding site the file came from,
- whether it was copied/pasted or downloaded,
- whether The Dragon's Touch loaded it correctly,
- and what went wrong if it failed.

Collection Files
----------------
The collection files included in this alpha package are from my personal collection data.

You do not have to use them.

If you want to test your own collection data, you may add your own collection files and select them from the Collection Source page.

For alpha testing, useful feedback includes:
- whether your collection file loads,
- whether the app recognizes the selected collection source,
- whether collection-only or collection-preferred behavior seems clear,
- and whether the report respects the collection mode you selected.

Breaking the System Is Useful
-----------------------------
This is an alpha test. You are encouraged to try normal use, but also to try things that might break the workflow.

Useful tests include:
- using one of the included sample decks,
- using your own Commander deck,
- trying a decklist exported from another deckbuilding site,
- trying your own collection file,
- testing missing or unusual deck sections,
- testing partner commanders,
- testing companion decks,
- testing incomplete decks,
- testing illegal duplicates,
- and reporting anything confusing, broken, or unclear.

If something breaks, that is good feedback. Please send screenshots, the decklist file if you are comfortable sharing it, and a short description of what you were trying to do.

Current Active Scope
--------------------
Active in this alpha checkpoint:

  Single-deck review
  UI-staged settings
  Guarded main.py execution
  CLI input bridge
  Timestamped backend output folders
  Report detection
  Plain-text Report Viewer
  AI-assisted follow-up review after report generation

Future/deferred:

  Commander Spellbook/API integration
  Batch / Aggregate real workflow
  Replacement Candidate Engine
  Deep markdown rendering
  Packaged executable / installer
  Desktop shortcut support
  Automatic deck edits

Clean ZIP Notes
---------------
For a clean share/checkpoint ZIP, keep:

  main.py
  config.py
  download_scryfall_data.py
  Download_Scryfall_Data.pyw
  Launch_The_Dragons_Touch.pyw
  README_START_HERE.txt
  README.md
  ui/
  docs/
  rules/
  data/ code files

Do not include unless intentionally making a full offline personal backup:

  data/scryfall_cards.json

Safe to remove before zipping:

  __pycache__/
  *.pyc
  old patch ZIPs
  old generated output runs
  .git/ for share/checkpoint ZIPs
  .bat launchers from tester ZIPs
  shortcut helper files from tester ZIPs

Troubleshooting
---------------
If the app does not open:

1. Confirm Python is installed.
2. Confirm PySide6 is installed.
3. Confirm you are launching from the project folder.
4. Double-click Launch_The_Dragons_Touch.pyw again.
5. If a visible error appears, take a screenshot and send it with feedback.

If card lookup seems broken or the app reports missing Scryfall data, run:

  Download_Scryfall_Data.pyw

or:

  python download_scryfall_data.py

What To Send Back To The Developer
----------------------------------
After testing, send:

  Whether the ZIP extracted cleanly
  Whether Scryfall data downloaded
  Whether Launch_The_Dragons_Touch.pyw opened the app
  Whether one full deck review completed
  Whether a report appeared in Report Viewer
  The generated report file
  The AI follow-up review result
  Any screenshots of errors
  Any confusing steps or wording
  Any feature requests or quality concerns
