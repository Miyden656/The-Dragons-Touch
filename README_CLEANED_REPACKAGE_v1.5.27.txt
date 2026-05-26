The Dragon's Touch — v1.5.27 Best Option Cleaned Repackage Candidate

This candidate uses the active-import-closure approach.

Key change:
- Active reports root stays clean.
- Historical report support modules that are still required by active imports are retained under reports/legacy/.
- Active imports were updated to reports.legacy.* where needed.

Validation performed by ChatGPT:
- Active Python syntax compile pass.
- Critical backend/report imports pass.
- reports.smoke_baseline reports pass.

Start by reviewing:
- docs/project_reference/cleanup/BEST_OPTION_FULL_REPACKAGE_v1.5.27.md
- docs/project_reference/cleanup/BEST_OPTION_FULL_REPACKAGE_VALIDATION_v1.5.27.md
