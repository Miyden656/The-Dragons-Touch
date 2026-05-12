# PATCH NOTES — v0.7.22

## Patch Name

Alpha Tester Feedback Packet

## Type

Documentation / alpha handoff checklist

## Purpose

Create a complete alpha tester instruction packet so testers do not have to guess what to do. This patch adds a dictated end-to-end checklist covering clean ZIP extraction, Scryfall data setup, app launch, deck review smoke test, report viewing, and required AI follow-up review.

## Files Added

- `docs/alpha_tester_feedback_packet_v0.7.22.md`
- `docs/alpha_ai_followup_prompt_v0.7.22.md`
- `PATCH_NOTES_v0.7.22.md`

## What Changed

- Added a full alpha tester checklist.
- Added required AI follow-up review instructions.
- Added an AI follow-up prompt testers can paste into ChatGPT.
- Added feedback questions for testers.
- Added clear pass/fail standards for the alpha attempt.

## What Did Not Change

No runtime code changed.

This patch does not alter:

- `main.py`
- PySide6 UI behavior
- launcher behavior
- Scryfall downloader behavior
- guarded confirmation
- CLI bridge behavior
- output folder behavior
- report detection
- Report Viewer behavior
- Commander Spellbook/API status
- Batch/Aggregate status
- Replacement Candidate Engine status

## Test Checklist

- Pass/Fail: `docs/alpha_tester_feedback_packet_v0.7.22.md` exists.
- Pass/Fail: `docs/alpha_ai_followup_prompt_v0.7.22.md` exists.
- Pass/Fail: `PATCH_NOTES_v0.7.22.md` exists.
- Pass/Fail: Feedback packet includes ZIP extraction instructions.
- Pass/Fail: Feedback packet includes Scryfall setup instructions.
- Pass/Fail: Feedback packet includes app launch instructions.
- Pass/Fail: Feedback packet includes full app smoke test checklist.
- Pass/Fail: Feedback packet includes AI follow-up requirement.
- Pass/Fail: Feedback packet includes tester feedback questions.
- Pass/Fail: Feedback packet includes what to send back to developer.

## Status

Ready for documentation-only application and review.
