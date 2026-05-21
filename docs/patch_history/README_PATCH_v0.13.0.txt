# The Dragon's Touch v0.13.0 Patch

## Beta Feedback Intake Form

This patch adds a tester feedback form and feedback summary tracker.

## Files Added

- docs/v0.13_beta_tester_feedback_form.md
- docs/v0.13_beta_feedback_summary_tracker.md
- tools/apply_v0.13.0_beta_feedback_form.py
- tools/verify_v0.13.0_beta_feedback_form.py

## Scope

Documentation / tester feedback only.

This patch does not change:

- deck analysis behavior
- Commander logic
- Combo Awareness logic
- replacement logic
- UI behavior
- source-run launch flow

## Apply

Run from the project root:

```powershell
py tools\apply_v0.13.0_beta_feedback_form.py
py tools\verify_v0.13.0_beta_feedback_form.py
```

## Lock Status

After the verifier passes:

```text
v0.13.0 — Beta Feedback Intake Form: PASS / LOCKED
```
