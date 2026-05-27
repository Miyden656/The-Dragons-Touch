# Strategy Knowledge Import Batches

This folder is reserved for future batch import manifests.

v1.4.3 does not import the full 249-file strategy set.
It only creates the planning contract and tooling needed to import batches safely.

Recommended batch behavior:

1. Copy candidate strategy markdown files into the correct `strategy_knowledge/layers/<layer>/` folder.
2. Add them to `strategy_knowledge/strategy_index.json`.
3. Run `py tools\validate_strategy_knowledge_base.py`.
4. Review `strategy_knowledge/strategy_quality_audit.json`.
5. Fix failed files before moving on.
6. Review warnings manually before runtime integration.
