# tests/

Smoke-test scripts that verify the v1.5 scoring chain and bucket fill behavior. These are not pytest tests — they're standalone scripts that print PASS/FAIL per assertion and exit 0 on success / 1 on failure.

## Run all

From the project root:

```powershell
py -3 tests/run_all.py
```

## Run one

```powershell
py -3 tests/test_combo_scorer.py
py -3 tests/test_role_tag_overrides.py
py -3 tests/test_strategy_profile_differentiation.py
py -3 tests/test_bucket_fill_end_to_end.py
```

## Prerequisites

Some tests need local runtime data and will print `SKIP` then exit 0 if the data is missing:

- `data/scryfall_cards.json` — required by role-tag and end-to-end tests
- `data/commander_spellbook/combo_index.json` — required by the combo scorer test
- `collection/*.txt` — required by the end-to-end test

Run **Settings → Data Setup** inside the app first to populate these, or run the tools manually:

```powershell
py -3 tools/data_setup.py
```

## What's covered

| Test | Verifies |
|---|---|
| `test_combo_scorer.py` | Item 5 — combo index loads, reachable Grixis combos detected, persona orientation correct, score modifier caps at ±6.0 |
| `test_role_tag_overrides.py` | Item 6 Phase A — shroud→protection, narrowed board_wipe (Demonic Consultation, anthems), 51-card override module (LED, Underworld Breach, Phyrexian Altar, etc.) |
| `test_strategy_profile_differentiation.py` | Item 6 Phase B — curated profiles return strategy-specific tags, Combo/Voltron differ, placeholder filter strips utility tags, utility-defining strategies keep their utility tags |
| `test_bucket_fill_end_to_end.py` | Combined — Obeka Combo and Voltron both hit 10/10/7/3/25/7 buckets with zero missing; Combo Strategy picks differ from Voltron Strategy picks by 30+ cards; Baylen Tempo + non-curated Kingmaker secondary still fills all buckets (the v1.5.46 regression fix) |

## Why no pytest?

Keeping it dependency-free. These scripts use only the standard library. If you want to fold them into a pytest suite later, the helper functions in `_test_helpers.py` would translate cleanly to pytest fixtures.

## Adding a new test

1. Create `tests/test_<feature>.py`
2. Import `from _test_helpers import TestRun` and `load_scryfall_or_skip` / `load_combo_index_or_skip` / `load_owned_collection` as needed
3. Inside `main()`, create `t = TestRun("test_<feature>")`, call `t.eq` / `t.in_set` / `t.true` per assertion, end with `t.report_and_exit()`
4. `run_all.py` will pick it up automatically
