# v0.7.7.3 — Run Analysis Missing Wrapper Restore Hotfix

Restores the Run Analysis/report-output wrapper methods that were unintentionally dropped during the v0.7.7 service extraction hotfix sequence.

Restored methods include guarded_run_result_text plus report-output detection/open-folder wrapper methods used by the existing UI call sites.

No backend behavior, main.py execution, report generation, CLI bridge mapping, output folder naming, Commander Spellbook/API behavior, Batch/Aggregate behavior, or Report Viewer plain-text behavior is changed.
