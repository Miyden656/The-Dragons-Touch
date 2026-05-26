"""Collection path helpers.

The project keeps user collection data in `collection/`. This service package
keeps application code separate from that user-data folder.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CollectionPaths:
    """Resolved collection-related paths."""

    project_root: Path
    collection_dir: Path

    def ensure_collection_dir(self) -> Path:
        """Create the user-data collection folder if needed and return it."""

        self.collection_dir.mkdir(parents=True, exist_ok=True)
        return self.collection_dir


def get_collection_paths(project_root: Path | None = None) -> CollectionPaths:
    """Return canonical collection paths without importing UI code."""

    root = project_root or Path(__file__).resolve().parents[1]
    return CollectionPaths(project_root=root, collection_dir=root / "collection")
