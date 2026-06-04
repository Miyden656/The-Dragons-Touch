"""Deck Coach Workbench backend (headless).

A presentation/restructuring layer that narrates reasoning the engine ALREADY
produces through the chosen philosophy lens's voice. It adds no reasoning of its
own and never touches the v1.6 scoring chain or the AI prompt pipeline.
"""

from ai.coach.coach_view import (
    CoachCard,
    CoachDirection,
    CoachView,
    build_coach_view,
)

__all__ = [
    "CoachCard",
    "CoachDirection",
    "CoachView",
    "build_coach_view",
]
