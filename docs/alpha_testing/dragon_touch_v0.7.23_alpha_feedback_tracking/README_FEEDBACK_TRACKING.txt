The Dragon's Touch Alpha Feedback Tracking
v0.7.23-dev support packet for v0.7.22 alpha tester feedback

Purpose
-------
This folder is for collecting feedback from testers using the locked build:

  The Dragon's Touch (Modular Alpha) v0.7.22 Alpha Tester Handoff Candidate.zip

Do not put these feedback files back into the locked app ZIP.
Do not modify the locked tester ZIP after sending it.
Use this folder to keep tester results, reports, screenshots, notes, and triage decisions separate from the app itself.

Golden Rule
-----------
The tested build stays fixed.
Feedback is collected separately.
Future fixes happen in v0.7.23-dev or later.

Recommended Feedback Folder Structure
-------------------------------------
The Dragon's Touch Alpha Feedback - v0.7.22/
  README_FEEDBACK_TRACKING.txt

  Tester_01/
    smoke_test_checklist.txt
    tester_notes.txt
    generated_reports/
    ai_followup_results/
    screenshots/
    decklists_tested/
    collection_files_tested/

  Tester_02/
    smoke_test_checklist.txt
    tester_notes.txt
    generated_reports/
    ai_followup_results/
    screenshots/
    decklists_tested/
    collection_files_tested/

  triage/
    bugs_to_fix.txt
    confusing_steps.txt
    report_quality_notes.txt
    decklist_format_issues.txt
    collection_issues.txt
    feature_requests.txt
    deferred_scope.txt

What Testers Should Send Back
-----------------------------
Ask each tester to send back a separate ZIP/folder containing:

1. Completed smoke test checklist.
2. Generated normal report.
3. Generated user-guided prompt.
4. Debug reports if output mode was both/debug.
5. AI follow-up review result.
6. Screenshots of errors or confusing screens.
7. Decklist file tested, if they are comfortable sharing it.
8. Collection file tested, if they used their own and are comfortable sharing it.
9. Short notes explaining what felt confusing, useful, broken, or missing.

Suggested Feedback ZIP Names
----------------------------
AlphaTester01_v0.7.22_Feedback.zip
AlphaTester02_v0.7.22_Feedback.zip
TesterName_v0.7.22_DragonsTouchFeedback.zip

Triage Categories
-----------------
Use the triage files to sort feedback into:

- Bug
- Confusing step
- Bad report wording
- Decklist parsing issue
- Collection issue
- UI issue
- AI follow-up issue
- Feature request
- Deferred scope

Version Tracking
----------------
Every feedback entry should include:

Build tested: v0.7.22 Alpha Tester Handoff Candidate
Feedback logged in: v0.7.23-dev feedback tracking
Tester: <name or tester number>
Date received: <date>
Deck tested: <deck name>
Collection tested: Yes/No
AI follow-up completed: Yes/No

Do not mix feedback from different builds without labeling the build tested.
