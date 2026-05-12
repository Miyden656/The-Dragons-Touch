# Patch v0.6.8.2.1 — Restore Unique Timestamped Output Folder Routing

## Purpose
Restore the locked v0.6.7.9.17 backend output-folder behavior after the v0.6.8.2 wording patch regressed single-deck runs back to plain commander-name output folders.

## Fix
- Single-deck runs now create a unique per-run output folder.
- Parser-only runs also use the same unique per-run output folder route.
- Output folder names preserve:
  - commander identity
  - source deck filename distinction
  - run timestamp
- Repeated runs of the same commander/deck no longer merge into one plain commander-name folder.

## Expected output folder style
```text
Outputs/
- v0.6.8.2.1/
  - Miirym_Sentinel_Wyrm_3_Miirym_Sentinel_Wyrm_run_20260511_123800/
    - normal/
    - debug/
```

## Preserved
- v0.6.8.2 prompt wording cleanup.
- v0.6.8.2 report wording cleanup.
- Guarded main.py workflow.
- Report Viewer behavior.
- Commander Spellbook/API disabled boundary.

## Not changed
- No legality logic changes.
- No strategy scoring changes.
- No cut scoring changes.
- No replacement scoring changes.
- No collection matching changes.
- No UI feature changes.
