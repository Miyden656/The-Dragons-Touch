# Known Issues / Watch List

Build tested: v0.7.22 Alpha Tester Handoff Candidate  
Tracking version: v0.7.23-dev  

---

## Confirmed Known Issues

No confirmed tester-reported issues yet.

---

## Watch Items

These are not necessarily bugs, but testers should watch for them.

1. Decklist export differences
   - Archidekt text exports are known-good sample format.
   - Other deckbuilding site `.txt` exports may reveal parser gaps.

2. Collection file format differences
   - Included collection files are based on the developer's personal collection.
   - Tester-owned collection exports may reveal collection parser gaps.

3. Strategy read mismatch
   - The report may identify a mechanically correct strategy that does not match pilot intent.
   - This is why AI follow-up review must ask for pilot intent.

4. Collection recommendations
   - Collection candidates are review candidates, not automatic upgrades.
   - Strong/Possible/Shakeup labels should remain clear.

5. Report length
   - Reports may be long.
   - Test whether the Report Viewer remains usable and whether the AI handoff remains practical.

6. Launcher / Windows behavior
   - `.pyw` launcher is the supported alpha path.
   - Desktop shortcuts and `.bat` files are deferred because Smart App Control previously blocked those paths.

---

## Deferred Scope — Not Bugs in v0.7.22

The following are intentionally not active in v0.7.22:

- Commander Spellbook/API combo lookup
- Real Batch / Aggregate workflow
- Replacement Candidate Engine
- Deep markdown rendering
- Packaged installer
- Supported desktop shortcut creation
- Automatic deck edits

Tester feedback about these can be logged as feature requests, but they should not be treated as v0.7.22 bugs.
