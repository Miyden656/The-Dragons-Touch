"""One-time patch tool archiver for The Dragon's Touch.

This helper keeps the active tools folder cleaner by moving completed one-time
apply/verify scripts into the project's existing archival area.

Default archive folder:
    Old Do not use/One-time patch tools/<version>/

This module is intentionally small and dependency-free so future patch scripts
can import it safely.
"""

from __future__ import annotations

from pathlib import Path
import shutil
from typing import Iterable, List, Sequence, Tuple


DEFAULT_ARCHIVE_ROOT = Path("Old Do not use") / "One-time patch tools"


def project_root_from_tools_file(tools_file: str | Path) -> Path:
    """Return the project root when given a file inside the tools folder."""
    path = Path(tools_file).resolve()
    if path.parent.name.lower() == "tools":
        return path.parent.parent
    return path.parents[1]


def archive_patch_tools(
    root: str | Path,
    *,
    version: str,
    tool_names: Sequence[str],
    archive_root: str | Path = DEFAULT_ARCHIVE_ROOT,
    overwrite: bool = True,
) -> List[Tuple[str, str]]:
    """Move one-time patch tool files into the archive.

    Parameters
    ----------
    root:
        Project root.
    version:
        Version/archive bucket name, such as "v1.1.3".
    tool_names:
        File names inside tools/ to move.
    archive_root:
        Archive root relative to project root.
    overwrite:
        If True, replaces same-named archived files.

    Returns
    -------
    list[tuple[str, str]]
        Pairs of source and destination paths for files that were moved.

    Notes
    -----
    Missing files are ignored. This lets the helper be safely reused after a
    partial cleanup or repeated verifier run from the archive.
    """
    root_path = Path(root)
    archive_dir = root_path / archive_root / version
    archive_dir.mkdir(parents=True, exist_ok=True)

    moved: List[Tuple[str, str]] = []

    for name in tool_names:
        source = root_path / "tools" / name
        if not source.exists():
            continue

        destination = archive_dir / name
        if destination.exists():
            if overwrite:
                destination.unlink()
            else:
                continue

        shutil.move(str(source), str(destination))
        moved.append((str(source), str(destination)))

    return moved


def archive_versioned_apply_verify_tools(
    root: str | Path,
    *,
    version: str,
    archive_root: str | Path = DEFAULT_ARCHIVE_ROOT,
    overwrite: bool = True,
) -> List[Tuple[str, str]]:
    """Archive apply/verify tools for a specific version prefix.

    Example:
        version="v1.1.3" archives files matching:
        - tools/apply_v1.1.3*.py
        - tools/verify_v1.1.3*.py
    """
    root_path = Path(root)
    tools_dir = root_path / "tools"
    if not tools_dir.exists():
        return []

    names = sorted(
        {
            path.name
            for pattern in (f"apply_{version}*.py", f"verify_{version}*.py")
            for path in tools_dir.glob(pattern)
        }
    )

    return archive_patch_tools(
        root_path,
        version=version,
        tool_names=names,
        archive_root=archive_root,
        overwrite=overwrite,
    )


def archive_multiple_versions(
    root: str | Path,
    *,
    versions: Iterable[str],
    archive_root: str | Path = DEFAULT_ARCHIVE_ROOT,
    overwrite: bool = True,
) -> List[Tuple[str, str]]:
    """Archive apply/verify tools for multiple version prefixes."""
    all_moved: List[Tuple[str, str]] = []
    for version in versions:
        all_moved.extend(
            archive_versioned_apply_verify_tools(
                root,
                version=version,
                archive_root=archive_root,
                overwrite=overwrite,
            )
        )
    return all_moved
