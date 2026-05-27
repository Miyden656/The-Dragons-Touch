# v1.4 Full Regression / Lock Candidate — v1.4.27

Status: **LOCK_CANDIDATE_PASS**

## Regression Checks

- Module compile passed: True
- Artifact presence passed: True
- Tool smoke tests passed: True
- Final chain passed: True

## Replacement State

- Strategy Knowledge preferred path enabled: True
- Final deck export enabled: True
- Old strategy system deprecated: True
- Old strategy system removed: False
- Legacy pipeline still available: True
- Rollback supported: True

## Boundary

- This regression patch does not delete old strategy files.
- This regression patch does not disable legacy fallback.
- This regression patch does not remove rollback support.
- This regression patch does not change `main.py`.
