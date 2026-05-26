"""Collection Services package boundary.

This package is the backend-owned home for collection loading/indexing helpers.
The runtime/user-data folder remains `collection/` and is intentionally not
converted into an application-code package.
"""

from .collection_paths import CollectionPaths, get_collection_paths
from .collection_manifest import CollectionFileRecord, CollectionManifest, scan_collection_manifest
from .service_boundary import CollectionService, service_health

__all__ = [
    "CollectionPaths",
    "get_collection_paths",
    "CollectionFileRecord",
    "CollectionManifest",
    "scan_collection_manifest",
    "CollectionService",
    "service_health",
]
