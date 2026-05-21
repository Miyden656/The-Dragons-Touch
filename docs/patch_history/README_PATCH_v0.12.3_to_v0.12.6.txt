The Dragon's Touch v0.12.3-v0.12.6 Source-Run Beta Handoff Polish Roll-Up
============================================================================

Purpose:
This is a single roll-up patch for all v0.12 work from v0.12.3 through v0.12.6.

It adds:
- v0.12.3 Dependency / Environment Check Helper
- v0.12.4 Tester Feedback Form / Response Template
- v0.12.5 Clean Beta ZIP Audit Verifier
- v0.12.6 v0.12 Beta Handoff Lock Notes / Final Checklist

This patch does not change deck-building engine behavior.
This patch does not add EXE packaging.
This patch does not add installer behavior.
This patch does not add new Commander/deck analysis features.

How to apply:
1. Extract this ZIP into the root folder of The Dragon's Touch.
2. Open PowerShell in the project root.
3. Run:

   py tools\apply_v0.12.3_to_v0.12.6_source_run_beta_rollup.py
   py tools\verify_v0.12.3_to_v0.12.6_source_run_beta_rollup.py

Optional helper commands after applying:

   py tools\check_source_run_environment.py
   py tools\verify_source_run_beta_package.py

Expected lock status after PASS:

v0.12.3-v0.12.6 — Source-Run Beta Handoff Polish Roll-Up: PASS / LOCKED
