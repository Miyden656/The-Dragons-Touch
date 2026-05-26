"""Replacement and deck-completion helper modules."""

# v1.5.11 Replacement Engine service boundary exports
try:
    from .service_boundary import (
        ReplacementReviewRequest,
        ReplacementEngineService,
        ReplacementEngineStatus,
        service_health,
    )
except Exception:
    # Keep package import tolerant for legacy replacement paths.
    ReplacementReviewRequest = None
    ReplacementEngineService = None
    ReplacementEngineStatus = None
    service_health = None

