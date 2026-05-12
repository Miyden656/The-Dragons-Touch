# v0.7.19 — Small UI User-Facing Polish Pass

Purpose: make the modular alpha build clearer for a first alpha tester without changing runtime behavior.

## Updated UI messaging

- The visible app version now reads `v0.7.19`.
- The phase label now reads `Modular Alpha / User-Facing Polish`.
- Header/footer language emphasizes single-deck alpha review, guarded runs, and no automatic deck edits.
- Page subtitles now clarify what each page does in the active alpha workflow.
- Run Analysis now says `main.py` is active through guarded confirmation, not merely a disconnected future preview.
- Batch / Aggregate is clearly labeled `Future / Not Active Yet`.
- Settings/checkpoint language now points to the v0.7 modular alpha checkpoint rather than only the older v0.6.7 foundation lock.

## Boundaries preserved

This patch does not change backend execution, report generation, output folders, the CLI bridge, report detection, the Report Viewer, Commander Spellbook/API status, Batch/Aggregate behavior, or replacement logic.

The preserved workflow remains:

```text
UI staged state
-> guarded confirmation
-> subprocess/main.py
-> CLI input bridge
-> backend output folder
-> report detection
-> Report Viewer plain-text load
```

## Tester-facing rule

A first alpha tester should be able to understand:

- launch with `Launch_The_Dragons_Touch.pyw`
- select one Commander deck file
- stage Review Setup / Philosophy Lens / Collection Source
- run only through guarded confirmation
- read generated reports in plain text
- expect future features to be labeled as placeholders, not active tools
