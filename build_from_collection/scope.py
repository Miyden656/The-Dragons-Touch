"""v1.3 Build From Collection scope boundary helpers."""

from __future__ import annotations

V1_3_SCOPE_BOUNDARY = {
    "version": "v1.3.0",
    "feature": "Build From Collection / Commander Shell Foundation",
    "answers_v1_2": "What commanders do I already own?",
    "answers_v1_3": "What can I build from what I own?",
    "v1_3_0_starting_point": "Selected commander handoff and scope baseline only.",
    "allowed_now": [
        "Define selected-commander handoff data shape",
        "Preserve selected commander context for future build-start logic",
        "Document collection-first shell planning boundaries",
        "Create safe module shell for later v1.3 patches",
    ],
    "deferred": [
        "Full 100-card deck generation",
        "Automatic final decklist creation",
        "Archidekt integration",
        "Account login",
        "Normal deck review replacement",
        "Scoring/cut/replacement behavior changes",
        "Combo matching behavior changes",
    ],
}


def describe_v1_3_scope() -> str:
    """Return a human-readable v1.3.0 boundary summary."""
    allowed = "\n".join(f"- {item}" for item in V1_3_SCOPE_BOUNDARY["allowed_now"])
    deferred = "\n".join(f"- {item}" for item in V1_3_SCOPE_BOUNDARY["deferred"])
    return (
        "v1.3.0 — Commander Selection Handoff / Build Scope Baseline\n\n"
        "Allowed now:\n"
        f"{allowed}\n\n"
        "Deferred / not changed:\n"
        f"{deferred}"
    )
