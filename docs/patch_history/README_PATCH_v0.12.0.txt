# The Dragon's Touch v0.12.0 — Source-Run Smoke Tests Patch

Drop-in patch contents:

- docs/source_run_beta_smoke_test_checklist_v0.12.0.md
- tools/apply_v0.12.0_source_run_smoke_test_checklist.py
- tools/verify_v0.12.0_source_run_smoke_test_checklist.py

## How to use

1. Extract this ZIP into the root folder of The Dragon's Touch.
2. Allow it to merge the `docs` and `tools` folders.
3. Run:

```powershell
py tools\apply_v0.12.0_source_run_smoke_test_checklist.py
py tools\verify_v0.12.0_source_run_smoke_test_checklist.py
```

## Expected result

The verifier should end with:

```text
RESULT — PASS
v0.12.0 smoke test checklist is present and lockable.
```

This patch is documentation-only and does not change app behavior.
