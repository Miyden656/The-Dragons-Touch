# Live Strategy Profile Frontmatter Normalization / Count Recovery Hotfix — v1.4.32.1

## Result

- Runtime behavior changed: True
- Live layers modified: True
- Frontmatter normalization performed: True
- Indexing performed: False
- Scoring wiring performed: False
- Report behavior changed: False
- main.py changed: False

## Counts

- Live markdown files before: 249
- Valid live profile count before: 5
- Normalized profiles: 244
- Already-valid profiles preserved: 5
- Live markdown files after: 249
- Valid live profile count after: 249

## Gate Checks

- live_layers_exist: True
- live_markdown_file_count_is_249: True
- valid_live_profile_count_before_was_5: True
- normalized_244_profiles: True
- already_valid_5_profiles_preserved: True
- valid_live_profile_count_after_is_249: True
- indexing_not_performed: True
- scoring_wiring_not_performed: True
- report_behavior_not_changed: True
- main_py_not_changed: True

## Boundary

- This hotfix normalizes live strategy markdown frontmatter so copied files count as live profiles.
- It preserves existing valid profiles.
- It does not index all 249 into scoring yet.
- It does not change report wording yet.
- It does not change `main.py`.

## Next Safe Step

v1.4.33 — Strategy Knowledge Live Profile Count / Loader Report Correction
