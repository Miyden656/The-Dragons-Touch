# v0.10.5-dev Implementation Notes

## Current Screenshots Reviewed

The provided screenshots show:

- Philosophy Lens still contains Guide Presentation, which should move to Settings.
- Report Viewer currently has User View/Dev View behavior but has suffered stale-mode bugs.
- Review Setup is too large and should be compacted.
- Running Analysis animation looks good and should be preserved.
- Settings is still dev-note-heavy and needs to become real user preferences.
- Run Analysis User Mode still exposes too much dev wording/output.
- Batch Tools is a placeholder and should be removed from navigation.
- Collection Source is currently a separate page but should be moved into Settings/Review Setup.
- Deck Selection works but needs a major tabbed upgrade.

## User Questionnaire Decisions

- Brand-new default: User Mode.
- Developer Mode visible indicator: Yes.
- Developer Mode access: Settings only.
- Guide options:
  - Adventurer Guide
  - Archivist Guide
  - Strategist Guide
  - Minimal Guide
- Guide persists: Yes.
- No Philosophy still allows guide presentation: Yes, this is Adventurer Guide behavior.
- Collection sources in Settings:
  - Local collection folder with specific file selection
  - CardMill CSV/export placeholder
  - Moxfield export placeholder
  - Future source placeholder
- Collection source persists: Yes.
- Collection Mode belongs in Review Setup: Yes.
- Deck Selection uses tabs.
- Pasted decklists ask before saving.
- Saved pasted decklists go into Decklist Folder using next available number.
- Report Viewer User Mode should show latest user-facing handoff automatically.
- User must still be able to select report/output folder in Settings.
- Developer Report Viewer defaults to last-used Developer view.
- Visual/theme settings should be included if feasible.
- Running Analysis animation should happen every time.

## Decklist Folder Naming Observed

Current decklist names include:

```text
1.Witherbloom, The Balancer.txt
2. Braulios of Pheres Band.txt
3. Miirym, Sentinel Wyrm.txt
4. Partner Commander.txt
4.1 Partner commander Plater defined categories.txt
10. Silverquill, the Disputant.txt
```

Numbering should scan leading numeric prefixes and choose the next integer greater than the highest integer prefix. Decimal-like names such as `4.1` should not be treated as the next main integer deck number unless explicitly desired later.

Recommended next-number behavior:

- Highest leading integer prefix among files = 28 in the screenshot.
- New saved pasted deck should become `29. User Deck Name.txt`.

## Key Risk

The most dangerous bug class right now is stale page state:

- User switches modes.
- Page layout remains from previous mode.
- Hidden widgets persist.
- Report Viewer gets stuck showing Developer elements in User Mode.

Mitigation:

- Rebuild pages on mode change.
- Prefer separate user/developer page builders.
- Avoid hiding/showing many widgets inside one mixed page.
