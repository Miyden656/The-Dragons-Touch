# Post-Alpha Triage Plan

Tracking version: v0.7.23-dev  
Tester build: v0.7.22 Alpha Tester Handoff Candidate  

---

## Purpose

Use this plan after receiving feedback from the first 1-2 trusted alpha testers.

The goal is to decide what must be fixed before wider testing and what should remain deferred.

---

## Triage Order

Review feedback in this order:

1. Launch blockers
2. Scryfall setup blockers
3. Deck selection / parsing blockers
4. Run Analysis / guarded execution blockers
5. Output folder / report detection blockers
6. Report Viewer blockers
7. AI follow-up prompt confusion
8. Report quality issues
9. Collection behavior issues
10. Nice-to-have UI polish
11. Feature requests
12. Deferred scope requests

---

## Severity Guide

Critical:
- App does not launch.
- Scryfall setup cannot run.
- Run Analysis cannot generate a report.
- Report Viewer cannot load any report.

High:
- A common decklist export format fails.
- Collection setup is confusing enough to block testing.
- The app silently fails without visible explanation.

Medium:
- Report wording is misleading.
- Strategy read is often wrong in a way the AI follow-up cannot easily correct.
- Tester can complete workflow but is confused by several steps.

Low:
- Minor UI wording issue.
- Cosmetic issue.
- Documentation could be clearer.

Nice-to-have:
- Feature request.
- Quality-of-life improvement.
- Future workflow idea.

---

## Fix Rules

Fix immediately in v0.7.23-dev if:
- It blocks launch.
- It blocks report generation.
- It blocks Scryfall setup.
- It causes silent failure.
- It confuses both testers in the same place.

Wait for more evidence if:
- Only one tester reports it and it may be user-specific.
- It involves an unusual deck export format.
- It is a preference rather than a bug.

Defer if:
- It is Commander Spellbook/API.
- It is real Batch/Aggregate workflow.
- It is Replacement Candidate Engine.
- It is installer/desktop shortcut support.
- It is deep markdown rendering.
- It is automatic deck editing.

---

## Post-Feedback Output

After reviewing tester feedback, produce:

1. Alpha feedback summary.
2. Confirmed bugs list.
3. Confusing steps list.
4. Report-quality issues list.
5. Decklist/collection parser issues list.
6. Deferred feature requests list.
7. Recommended v0.7.23 fix plan.

---

## Version Decision

After feedback is triaged, choose one:

1. v0.7.23 hotfix needed before more testers.
2. v0.7.23 polish patch only.
3. v0.7.22 is good enough for the next trusted tester.
4. Pause feature development until a blocking issue is fixed.
