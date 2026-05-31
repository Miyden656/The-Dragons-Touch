"""Context assembly for the Commander AI layer (Phase 3).

These modules turn the engine's analysis dict (the value returned by
main.build_analysis_context) into a compact, JSON-safe CommanderAIContext that
is small enough to fit a local model's context window and contains ONLY
engine-verified data.

Design rules:
    - Read-only: builders consume engine objects, never call the engine.
    - Defensive: every attribute read goes through safe access, so a changed or
      missing field degrades to a default instead of crashing. This is what lets
      the AI layer survive ongoing Commander's Call / engine churn.
    - No invention: a card name only appears in the output if it appeared in an
      engine object. Builders never synthesize card facts.
    - Disclosed truncation: long lists are capped and the drop is recorded in
      meta.truncation — never silently cut.
"""
