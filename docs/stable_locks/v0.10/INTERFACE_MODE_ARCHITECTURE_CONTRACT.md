# The Dragon's Touch v0.10.5-dev — Interface Mode Architecture Contract

## Purpose

v0.10.5-dev is an architecture and UI cleanup pass.

The goal is to stop treating User Mode and Developer Mode as small visibility toggles on the same crowded pages. Instead, the app should have a persistent global settings system and clear page-level behavior:

- **User Mode** is the clean player-facing workflow.
- **Developer Mode** is intentionally enabled from Settings and exposes diagnostics, raw reports, bridges, and development tools.
- **Settings controls app-wide defaults.**
- **Review Setup controls the current run.**

Current Deck Context is working well and must remain. It needs stable spacing between each section with no overspill.

---

## Core Rules

1. Settings controls app-wide defaults.
2. Review Setup controls current-run choices.
3. Brand-new users start in User Mode.
4. Developer Mode can only be enabled from Settings.
5. Developer Mode must show an obvious “Developer Mode Enabled” indicator.
6. User Mode must not show dev/debug/backend/breakdown/diagnostic language.
7. Running Analysis transition and animation must stay and should happen every time.
8. Current Deck Context must remain stable and visible.
9. Collection Source page should be removed from navigation.
10. Batch Tools page should be removed from navigation.
11. No Philosophy must still allow Adventurer Guide behavior.

---

## Persistent Settings Required

The app must remember these across restarts:

- Interface Mode
- Guide Presentation
- Collection Source default
- Report/output folder
- Visual settings if implemented
- Developer Report Viewer last-used view, but only for Developer Mode

Recommended storage:

```text
ui/user_settings.json
```

A missing or deleted settings file should reset safely to defaults.

Default settings:

```json
{
  "interface_mode": "User Mode",
  "guide_presentation": "Adventurer Guide",
  "collection_source_default": "Local collection folder",
  "collection_source_path": "",
  "report_output_folder": "Outputs",
  "theme": "Dragon Forge",
  "ui_density": "Normal",
  "developer_report_viewer_last_view": "User View"
}
```

---

## Interface Mode

Options:

- User Mode
- Developer Mode

Rules:

- Default is User Mode.
- Developer Mode is enabled only from Settings.
- No quick switch elsewhere.
- Developer Mode persists once enabled.
- Developer Mode shows a visible global banner/status indicator.
- Interface Mode controls visibility across the app.

User Mode should not show:

- Dev View
- Dev-Facing
- debug
- diagnostics
- backend
- breakdown reports
- bridge/runtime contracts
- raw report status tools
- detected report file diagnostics

Developer Mode may show these intentionally.

---

## Settings Page

Settings must become a real user-focused settings page, not a dev explanation page.

Recommended page name:

```text
Settings
```

Recommended sections:

1. Interface
2. Guide Presentation
3. Collection Defaults
4. Report Folder
5. Appearance
6. Developer Mode Status

### Interface

Controls:

- Interface Mode: User Mode / Developer Mode

Behavior:

- Persists across restarts.
- Developer Mode enabled from here only.
- Shows “Developer Mode Enabled” indicator when active.

### Guide Presentation

Move Guide Presentation out of Philosophy Lens and into Settings.

Options:

- Adventurer Guide
- Archivist Guide
- Strategist Guide
- Minimal Guide

Rules:

- Persists across restarts.
- No Philosophy must still allow guide presentation.
- No Philosophy defaults to or still works with Adventurer Guide.
- No Philosophy must not erase or disable Guide Presentation.

### Collection Source Defaults

Move Collection Source default into Settings.

Options:

- Local collection folder, with specific file selection if feasible
- CardMill CSV/export placeholder
- Moxfield export placeholder
- Future source placeholder

Rules:

- Persists across restarts.
- Collection Source page removed from navigation.
- Collection source is app-wide, not a per-run page.

### Report Folder Setting

Add/preserve output/report folder setting.

Rules:

- Persists across restarts.
- User Mode Report Viewer loads latest user-facing handoff from selected folder.
- Developer Mode can expose detected report files and diagnostics.

### Visual Settings

Include if feasible:

- Theme / visual mode
- Font size
- UI density / compact spacing

Running Analysis animation must not be optional.

---

## Navigation Cleanup

Remove from navigation:

- Collection Source
- Batch Tools

These may remain in code temporarily, but should not appear in normal navigation.

Recommended eventual status:

```text
Retired UI / hidden dev-only code path until rebuilt intentionally
```

Keep:

- Deck Selection
- Review Setup
- Philosophy Lens
- Run Analysis
- Report Viewer
- Settings

---

## Deck Selection

Deck Selection needs a major upgrade.

Required tabs:

- Select File
- Paste Decklist
- Import Link

### Select File

Must keep current deck file selection behavior.

### Paste Decklist

Requirements:

- User can paste a decklist into the app.
- App asks whether to save pasted decklist.
- If yes, save directly into Decklist Folder.
- File format should use next available number followed by user-provided deck name.
- Do not overwrite existing decklists.
- After paste/import/select, Current Deck Context updates cleanly.

Filename pattern:

```text
1. User Deck Name.txt
2. Another Deck Name.txt
3. Another Deck Name.txt
```

Existing numbering should account for current patterns such as:

```text
1.Witherbloom, The Balancer.txt
10. Silverquill, the Disputant.txt
4.1 Partner commander Plater defined categories.txt
```

### Import Link

Placeholder only for v0.10.5-dev.

Recommended behavior:

- Disabled or clickable with “Coming soon.”
- No actual link import required yet.

---

## Current Deck Context

Must remain.

Requirements:

- Stable spacing between sections.
- No overspill.
- No unreadable compression.
- Works with selected deck files and pasted decklists.
- Maintains useful deck, commander, deck size, bracket, warnings, and status fields.

---

## Review Setup

Review Setup should be compact.

Current problem:

- Cards are visually nice but too large.
- Simple dropdowns should not take full large cards.

User-facing layout:

- Parchment style remains.
- Use compact list/dropdown rows.
- Easy to scan.

Review Setup contains current-run settings only:

- Review direction
- Cut depth / review intensity
- Output mode
- Intended bracket
- Budget note
- Collection Mode
- Prompt mode if still run-specific
- Combo awareness if user-visible for v0.10.5

Collection Mode moves here from Collection Source.

Collection Mode options:

- Collection first, then full card pool
- Collection only
- Full card pool only
- No replacement suggestions

---

## Philosophy Lens

Keep this page.

Purpose:

- Deckbuilding philosophy only.
- Prepare for deeper future persona system.
- Do not overbuild persona system in v0.10.5.

Changes:

- Move Guide Presentation to Settings.
- No Philosophy must still work.
- No Philosophy must not break Adventurer Guide.
- Philosophy Lens should not control guide presentation.
- Layout should prepare for future deeper philosophy/persona content, possibly including bust images later.

---

## Run Analysis

### User Mode

Show only:

- Run Analysis button
- Current Run Summary
- Ready to Run checklist

Rename:

```text
Quick Readiness -> Ready to Run
```

Ready to Run checklist:

- Green checkmark if met.
- Red X if missing.
- Simple, readable, user-facing.

Do not show:

- Latest Run Output
- Bridge Status
- Runtime Contract
- CLI handoff
- stdout/stderr
- backend details
- diagnostic dropdowns

### Developer Mode

Show User Mode content plus:

- Latest Run Output
- Bridge Status
- Run Analysis Detail View
- Detail dropdown

Run Analysis Detail View dropdown options:

- Runtime Contract: Backend Runtime Config Contract Preview
- Bridge Preview: Safe Backend Bridge Preview
- Combo Tracker: Optional Combo Awareness
- Guarded Execution: Guarded Execution Bridge
- Run Output / Result: Report Output Detection
- Safety Boundary: Safety Boundary and Future Stages

Running Analysis behavior:

- Do not change current running analysis transition.
- Running analysis animation happens every time.
- Both User Mode and Developer Mode transition cleanly.

---

## Report Viewer

### User Mode

Show only:

- User View / AI Handoff
- Copy User Prompt
- Copy Deck Report
- Open User Prompt
- Open Deck Report
- Copy Current Section
- Copy All User View Summary
- Copy AI Handoff Package
- Section buttons:
  - Handoff
  - Summary
  - Owned
  - Examples
  - Review
  - Combos
  - Safety

Do not show:

- Detected Report Files
- Dev View
- Report File Preview
- Loaded Report Status
- backend/debug/report detection diagnostics
- raw markdown unless opening generated prompt/report is explicitly chosen

User Mode should automatically load the latest user-facing AI handoff from selected report/output folder when available.

### Developer Mode

Allow:

- User View
- Dev View
- Detected Report Files
- normal report/debug report detection
- raw Report File Preview
- Loaded Report Status / Actions
- report detection diagnostics

Developer Mode should remember last used report view.

User Mode always defaults to User View only.

Structural recommendation:

```python
def build_report_viewer_page(window):
    if window.is_user_mode():
        return build_user_report_viewer_page(window)
    return build_developer_report_viewer_page(window)
```

Avoid mixed pages with hidden widgets.

---

## Batch Tools

Remove this page from UI/navigation for v0.10.5-dev.

Batch and stress testing remain outside the UI.

---

## Collection Source

Remove this page from UI/navigation.

Move:

- Collection Mode -> Review Setup
- Collection Source default -> Settings

---

## Success Criteria

- Brand-new app opens in User Mode.
- Developer Mode is only enabled from Settings.
- Developer Mode shows visible “Developer Mode Enabled” indicator.
- User Mode Run Analysis is clean and shows only Run button, Current Run Summary, and Ready to Run checklist.
- Developer Mode Run Analysis shows diagnostics and detail dropdown.
- Quick Readiness renamed Ready to Run.
- Ready to Run uses green checks and red Xs.
- Report Viewer in User Mode only shows latest User View AI Handoff.
- Report Viewer in User Mode does not show Detected Report Files.
- Developer Mode Report Viewer can switch between User View and Dev View.
- Collection Source page is gone.
- Batch Tools page is gone.
- Collection Mode is in Review Setup.
- Collection Source default is in Settings.
- Guide Presentation is in Settings.
- No Philosophy still supports Adventurer Guide.
- Deck Selection supports Select File and Paste Decklist, with Import Link as placeholder.
- Pasted decklists can be saved into Decklist Folder using next-number naming.
- Current Deck Context remains stable with no overspill.
- Review Setup is compact and uses list/dropdown rows instead of oversized blocks.
- Running Analysis transition and animation continue working.
