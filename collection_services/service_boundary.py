"""Collection service boundary.

v1.5.9 establishes a backend service boundary for collection-related workflows
while preserving the existing `collection/` user-data folder.
"""

from __future__ import annotations

from typing import Dict

from .collection_paths import CollectionPaths, get_collection_paths
from .collection_manifest import CollectionManifest, scan_collection_manifest


class CollectionService:
    """Safe collection service facade for future discovery/build/replacement/combo workflows."""

    service_version = "v1.5.9"

    def __init__(self, paths: CollectionPaths | None = None) -> None:
        self.paths = paths or get_collection_paths()

    def ensure_ready(self) -> CollectionPaths:
        """Ensure the collection user-data folder exists without modifying files."""

        self.paths.ensure_collection_dir()
        return self.paths

    def manifest(self) -> CollectionManifest:
        """Return a collection file manifest without parsing or mutating user data."""

        self.ensure_ready()
        return scan_collection_manifest(self.paths.collection_dir)

    def status(self) -> Dict[str, object]:
        """Return a JSON-safe service status payload."""

        manifest = self.manifest()
        return {
            "service": "collection_services",
            "service_version": self.service_version,
            "collection_dir": str(self.paths.collection_dir),
            "collection_file_count": manifest.file_count,
            "behavior_changed": False,
            "status": "foundation_ready",
        }


def service_health() -> Dict[str, object]:
    """Return lightweight package health without requiring collection files."""

    service = CollectionService()
    return service.status()
