# Strategy Loader Contract

Future loader behavior should:

1. Read `strategy_index.json`.
2. Resolve every indexed path.
3. Parse YAML frontmatter from each markdown file.
4. Validate frontmatter against `strategy_schema.json`.
5. Confirm filename matches `strategy_id`.
6. Confirm folder layer matches frontmatter `layer`.
7. Confirm required markdown sections exist.
8. Return structured metadata without relying on prose parsing.

The loader should not use strategy prose as a direct deck construction command.
Strategy files inform scoring, role classification, cut protection, replacement guidance, and report language.
