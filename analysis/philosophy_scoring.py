# v1.1.20 LEGACY PHILOSOPHY DIAGNOSTICS CLEANUP
"""
analysis/deck_building_philosophies.py

Philosophy and persona guide data for The Dragon's Touch.

This module is designed for the v0.6.2 CLEANUP layout, which uses top-level
packages such as analysis, cuts, reports, app_io, and rules.

Design rules:
- Strategy detection remains primary.
- The philosophy/subtype key is the rules object.
- The persona name is the user-facing guide.
- This module should not perform strategy detection.
- Reports, cut logic, replacement logic, and prompt generation can consume this module.

v0.6.5.3 adds report-facing subtype summaries. These summaries are still
non-scoring guidance: they help humans and reviewing AIs understand what the
selected lens means without changing legality, strategy detection, cuts, or
collection matching.

v0.6.5.4 adds prompt-facing showcase polish so generated guided prompts explain
philosophy lenses consistently across subtypes.

v0.6.6.1 adds the foundation for philosophy-aware cut/replacement bias.
v0.6.6.2 turns on a light optional-cut scoring nudge while leaving strategy detection, legality, and collection matching unchanged.
v0.6.6.5 adds a philosophy-bias QA / stress-test checkpoint while preserving the v0.6.6.4.2 replacement-bias behavior and all quality gates.
v0.6.6.6 locks the v0.6.6 philosophy-bias milestone and documents its scope, boundaries, and QA expectations. The v0.6.6.5.2 balanced-neutrality and companion-review cleanup remains active.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from random import choice
from typing import Dict, List, Literal, Optional


GuidePreference = Literal["masculine", "feminine", "either", "random", "none"]
GuidePreference = Literal["masculine", "feminine", "either", "random", "none"]

def resolve_persona_name(key: Optional[str], preference: GuidePreference = "either") -> Optional[str]:
    """Resolve the display name for the selected philosophy/subtype."""
    return get_philosophy_profile(key).persona.resolve_name(preference)

def get_grouped_selection_menu() -> str:
    """Return a user-facing philosophy subtype menu grouped by parent philosophy."""
    return """Choose philosophy depth:
1. Balanced / Unknown
2. Big 3 philosophy only
3. Specific philosophy subtype

Big 3 Philosophy:
- Timmy / Tammy
- Johnny / Jenny
- Spike

Timmy / Tammy — Experience, spectacle, theme, and personal joy
1. Big Moment
2. Big Creature / Stompy
3. Theme / Vibe
4. Pet Card
5. Let Me Do My Thing
6. Battlecruiser

Johnny / Jenny — Synergy, invention, engines, and clever concepts
7. Engine Builder
8. Commander Exploiter
9. Weird Card Rescuer
10. Theme Mechanic Inventor
11. Self-Imposed Constraint Builder
12. Combo Builder

Spike — Performance, consistency, efficiency, and table fit
13. Consistency Maximizer
14. Efficiency Optimizer
15. Curve and Mana Discipline
16. Competitive Closer
17. Power-Level Calibrator
18. Interaction Controller
"""
