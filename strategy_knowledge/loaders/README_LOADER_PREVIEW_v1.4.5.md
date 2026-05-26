# Strategy Knowledge Loader Preview v1.4.5

This folder contains the read-only loader-preview contract for the Strategy Knowledge Base.

## Purpose

The loader preview proves that The Dragon's Touch can read validated strategy files from:

```text
strategy_knowledge/strategy_index.json
strategy_knowledge/layers/**/*.md
```

without changing runtime behavior.

## Important Boundary

The loader preview does not replace the current strategy system.
It does not change strategy scoring.
It does not generate decks.
It does not make card selections.
It does not produce final deck inclusion decisions.

## Output

Running:

```powershell
py tools\load_strategy_knowledge_preview.py
```

writes:

```text
strategy_knowledge/loader_previews/strategy_loader_preview_v1.4.5.json
```

The preview includes strategy IDs, aliases, role buckets, signal tags, cut-protection tags, replacement-priority tags, and short previews of key markdown sections.
