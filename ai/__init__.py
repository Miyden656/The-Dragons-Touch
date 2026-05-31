"""The Dragon's Touch — Commander AI layer (v1.7.x).

A local-first, Ollama-backed Commander guide that sits ON TOP of the existing
deck engine. This package is a *consumer* of engine outputs, never an author of
card facts, legality, strategy, combos, or persona priorities.

Layering rule (do not break this):
    UI  ->  ai/  ->  engine (analysis, data, legality, combo, philosophy)
The engine must never import from `ai/`. Deleting `ai/` must leave the v1.6
deck-analysis behavior completely intact.

See COMMANDER_AI_DESIGN.md at the project root for the full design and roadmap.

Phase 2 (this milestone) ships:
    - ai/commander_ai_config.py : typed config + defaults (single source of truth)
    - ai/ollama_client.py       : stdlib-only HTTP client with offline safety
    - ai/cli/ask_commander_guide.py : headless connectivity / smoke harness
Later phases add context serialization, prompts, safety, service, and UI hooks.
"""

from __future__ import annotations

__all__ = ["commander_ai_config", "ollama_client"]
