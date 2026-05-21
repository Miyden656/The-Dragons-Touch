The Dragon's Touch v0.12.6.1 Patch
===================================

Clean Handoff Staging / Verifier Scope Hotfix

Why this exists
---------------
The v0.12.3-v0.12.6 roll-up verifier passed, but the clean beta package verifier
correctly failed when run against a full development/archive folder containing old
historical folders such as Retired UI, Old Do Not Use, exe tests, dist, and build.

That is not a failure of the app. It means the package audit verifier was scanning
too broad of a folder.

This hotfix adds a staging helper:

tools/create_source_run_beta_staging.py

It copies only active source-run handoff files/folders into:

_handoff_staging/The Dragon's Touch v0.12 Source-Run Beta

Then you run the package verifier inside that staging folder.

Apply commands
--------------
py toolspply_v0.12.6.1_clean_handoff_staging_scope_hotfix.py
py toolserify_v0.12.6.1_clean_handoff_staging_scope_hotfix.py

Create clean staging folder
---------------------------
py tools\create_source_run_beta_staging.py --overwrite

Verify clean staged package
---------------------------
cd "_handoff_staging\The Dragon's Touch v0.12 Source-Run Beta"
py toolserify_source_run_beta_package.py

Expected result
---------------
The historical folders can stay in your development area, but they should not be
inside the final beta handoff ZIP. The clean staging folder is the folder to ZIP
for beta handoff.
