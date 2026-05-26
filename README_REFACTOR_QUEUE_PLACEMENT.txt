# Refactor Queue Placement Package

This ZIP contains:

- `project_files_to_place/` — uploaded queue files placed into their expected current project paths.
- `docs/REFACTOR_QUEUE_PLACEMENT_AND_BREAKDOWN_v1.5.md` — human-readable placement and split plan.
- `docs/REFACTOR_QUEUE_PLACEMENT_AND_BREAKDOWN_v1.5.json` — machine-readable map.

Recommended use:
1. Do not blindly overwrite a working project without a backup.
2. Compare `project_files_to_place/` against the active project.
3. Use the markdown breakdown to plan v1.5.30+ split patches.
4. Preserve old facade paths when splitting modules.
