The Dragon's Touch — v0.12.1 README Quickstart Polish Patch

Purpose:
- Bring the clean v0.11 source-run beta ZIP up to the current v0.12 testing/polish language.
- Include the v0.12.0 Source-Run Beta Smoke Test Checklist.
- Update README_START_HERE.txt and README.md for the protected source-run beta path.
- Avoid app behavior changes.

How to use:
1. Extract this ZIP into the root folder of The Dragon's Touch.
2. Let it merge/overwrite README_START_HERE.txt, README.md, docs, and tools files.
3. Open PowerShell in the project root.
4. Run:

   py tools\apply_v0.12.0_source_run_smoke_test_checklist.py
   py tools\verify_v0.12.0_source_run_smoke_test_checklist.py
   py tools\apply_v0.12.1_readme_quickstart_polish.py
   py tools\verify_v0.12.1_readme_quickstart_polish.py

Expected result:
- v0.12.0 verifier: RESULT — PASS
- v0.12.1 verifier: RESULT — PASS

Scope:
- Documentation/testing polish only.
- No UI behavior changes.
- No backend analysis changes.
- No EXE path changes.
