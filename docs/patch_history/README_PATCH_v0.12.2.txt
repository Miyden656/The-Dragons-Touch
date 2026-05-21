# The Dragon's Touch v0.12.2 — First-Run Troubleshooting Patch

Drop this ZIP into the root folder of The Dragon's Touch and extract it there.

This patch adds:

```text
README_START_HERE.txt
docs/first_run_troubleshooting_v0.12.2.md
tools/apply_v0.12.2_first_run_troubleshooting.py
tools/verify_v0.12.2_first_run_troubleshooting.py
```

Run from PowerShell in the project root:

```powershell
py tools\apply_v0.12.2_first_run_troubleshooting.py
py tools\verify_v0.12.2_first_run_troubleshooting.py
```

This is a documentation-only polish patch.

It does not change app behavior, backend analysis, Combo Awareness logic, deck parsing, or UI code.

Expected lock result:

```text
v0.12.2 — First-Run Troubleshooting Section: PASS / LOCKED
```
