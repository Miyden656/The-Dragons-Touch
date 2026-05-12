# Patch Notes — v0.7.7.2

## Guarded Execution Preview Restore

This hotfix restores the missing `MainWindow.guarded_execution_preview_text()` method that is called while building the Run Analysis page.

The previous v0.7.7.1 hotfix did not actually restore the method body, so the .pyw launcher still failed at startup.

## Scope

No backend behavior changed. No UI workflow changed. No report/output behavior changed. This is a startup regression fix only.

## Expected result

- `Launch_The_Dragons_Touch.pyw` opens the UI.
- Run Analysis page builds successfully.
- Guarded Execution preview text displays.
- Guarded confirmation and main.py execution remain unchanged.
