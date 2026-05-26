# Old Strategy System Deprecation / Fallback Cleanup — v1.4.26

Strategy Knowledge is now the preferred strategy export path.

## Boundary

- Strategy Knowledge preferred path: enabled.
- Old strategy system: deprecated fallback.
- Old strategy system deletion: disabled.
- Legacy fallback removal: disabled.
- Rollback support: preserved.
- main.py changed in this patch: no.

## Policy

- Preferred path: Strategy Knowledge live bridge + final deck export artifacts
- Old path status: deprecated_fallback_only
- Checked strategy export count: 5

## Fallback Rules
- Use Strategy Knowledge export artifacts when the live bridge is explicitly enabled.
- Keep the old strategy system available as fallback until v1.4 lock/regression passes.
- Do not delete old strategy files in this patch.
- Do not remove legacy fallback in this patch.
- Do not alter main.py in this patch.
