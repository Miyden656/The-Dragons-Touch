"""Service helpers for The Dragon's Touch desktop UI.

Services keep non-visual helper logic out of the PySide6 page/main-window file.
They must not replace main.py or perform deck analysis.
"""
from . import user_settings

# v1.5.14 UI backend boundary exports
try:
    from .backend_boundary import (
        BackendServiceStatus,
        UIBackendBoundaryService,
        service_health,
    )
except Exception:
    # Keep package import tolerant for existing UI paths.
    BackendServiceStatus = None
    UIBackendBoundaryService = None
    service_health = None

