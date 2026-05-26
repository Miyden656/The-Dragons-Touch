'''Strategy Knowledge package.'''

# v1.5.12 Strategy Knowledge adapter boundary exports
try:
    from .adapter_boundary import (
        StrategyKnowledgeAdapter,
        StrategyKnowledgeStatus,
        service_health,
    )
except Exception:
    # Keep package import tolerant for legacy Strategy Knowledge paths.
    StrategyKnowledgeAdapter = None
    StrategyKnowledgeStatus = None
    service_health = None

