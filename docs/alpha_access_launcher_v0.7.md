# The Dragon's Touch v0.7 Alpha Access / Launcher Track

## Current Launcher Decision

v0.7.7L added a `.bat` launcher, but Windows Smart App Control blocked that path during testing.

v0.7.7L.1 added Python launchers. The `.pyw` launcher successfully opened the desktop UI without Visual Studio Code.

v0.7.7L.2 tried to retarget shortcut creation to `.pyw`, but the Desktop shortcut path was also blocked by Smart App Control during testing.

v0.7.7L.3 corrects the scope:

```text
Supported v0.7 alpha launch path:  Launch_The_Dragons_Touch.pyw
Desktop shortcut support:           Deferred / experimental only
Developer fallback only:            Launch_The_Dragons_Touch.bat
Experimental/developer only:        Create_Desktop_Shortcut.pyw / .py / .bat
```

Do not ask alpha testers to disable Smart App Control.

## Purpose

v0.7 alpha hardening should make the app easier for trusted testers to open without Visual Studio Code while avoiding a premature packaging/installer detour.

The app is still in launcher-based alpha access mode. It is not packaged as an executable yet and does not have a supported installer yet.

## Supported Launcher Flow

```text
Double-click Launch_The_Dragons_Touch.pyw
-> PySide6 UI opens
-> user selects deck/settings
-> user clicks Run Analysis
-> guarded confirmation appears
-> UI runs main.py
-> backend creates output folder
-> UI detects report
-> Report Viewer loads plain text
```

## Deferred Desktop Shortcut Flow

Desktop shortcut support is deferred until the packaging/installer track because Smart App Control blocked the shortcut path during testing.

Do not make shortcut creation a required alpha tester step.

If shortcut helper files remain in the project, they are developer-only experiments and should not be treated as the supported access path.

## Scope Guard

Allowed:

- Open the desktop UI without Visual Studio Code.
- Use `.pyw` as the supported v0.7 alpha path.
- Preserve the project root as the working directory.
- Keep shortcut helper files only as experimental/developer artifacts.
- Preserve the long-term installer/shortcut goal for later roadmap phases.

Not allowed:

- Do not run deck analysis automatically.
- Do not bypass guarded confirmation.
- Do not bypass main.py.
- Do not create a second backend workflow.
- Do not change output folder behavior.
- Do not introduce packaging/installer complexity yet.
- Do not ask testers to disable Smart App Control.
- Do not present Desktop shortcut creation as a supported v0.7 alpha requirement.

## Future Path

Recommended progression:

```text
v0.7: Python .pyw launcher / alpha access
-> v0.8-v0.9: packaged executable spike
-> v0.9-v1.0: installer candidate
-> v1.0+: signed release path
```

The installer remains the long-term user-friendly goal, but it should come after the v0.7 alpha workflow is stable.

## v0.7.17 Clean Setup Note

The supported alpha launch path remains:

```text
Launch_The_Dragons_Touch.pyw
```

The clean ZIP may omit the large local Scryfall cache file:

```text
data/scryfall_cards.json
```

If the file is missing, recreate it from the project root:

```text
python download_scryfall_data.py
```

This requires internet access.
