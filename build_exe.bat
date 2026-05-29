@echo off
REM ============================================================================
REM Build The Dragon's Touch as a standalone Windows EXE bundle.
REM
REM What this does:
REM   1. Verifies PyInstaller is installed (installs it if missing)
REM   2. Cleans any previous build artifacts
REM   3. Runs PyInstaller against TheDragonsTouch.spec
REM   4. Reports where the finished EXE lives
REM
REM Usage:
REM   Double-click this file, OR run from a terminal in the project root:
REM       build_exe.bat
REM
REM After a successful build, the distributable folder is:
REM       dist\TheDragonsTouch\
REM
REM To distribute: zip that folder and share the zip. Users extract it and
REM double-click TheDragonsTouch.exe to launch.
REM ============================================================================

setlocal

echo.
echo === The Dragon's Touch — EXE build ===
echo.

REM Step 1 — make sure pyinstaller is available.
py -3 -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing it now...
    py -3 -m pip install pyinstaller
    if errorlevel 1 (
        echo.
        echo ERROR: Could not install PyInstaller. Check your Python/pip setup.
        pause
        exit /b 1
    )
)

REM Step 2 — clean previous artifacts.
echo.
echo Cleaning previous build artifacts...
if exist build (
    rmdir /s /q build
)
if exist dist (
    rmdir /s /q dist
)

REM Step 3 — run PyInstaller with the spec file.
echo.
echo Running PyInstaller (this takes ~1-3 minutes)...
echo.
py -3 -m PyInstaller TheDragonsTouch.spec --noconfirm
if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller build failed. Scroll up for details.
    pause
    exit /b 1
)

REM Step 4 — report success.
echo.
echo === BUILD COMPLETE ===
echo.
echo Distributable folder: dist\TheDragonsTouch\
echo Launch the EXE: dist\TheDragonsTouch\TheDragonsTouch.exe
echo.
echo To distribute:
echo   1. Zip the entire dist\TheDragonsTouch\ folder
echo   2. Share the zip
echo   3. Users extract and double-click TheDragonsTouch.exe
echo.
echo First-run note for end users:
echo   Windows SmartScreen will warn about an "unknown publisher" because
echo   the EXE is not yet code-signed. Tell users to click "More info"
echo   then "Run anyway." See LEGAL.md for the code-signing roadmap.
echo.
pause
endlocal
