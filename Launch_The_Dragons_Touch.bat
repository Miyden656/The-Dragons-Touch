@echo off
setlocal EnableExtensions

REM The Dragon's Touch Launcher - Developer Fallback Only
REM v0.7.7L.3
REM Primary alpha launch path is Launch_The_Dragons_Touch.pyw.
REM This .bat file may be blocked by Windows Smart App Control.

cd /d "%~dp0"
title The Dragon's Touch Launcher Developer Fallback

echo.
echo ============================================
echo   The Dragon's Touch - Launcher Fallback
echo ============================================
echo.
echo Recommended alpha launch path:
echo   Launch_The_Dragons_Touch.pyw
echo.
echo This batch file is kept only as a developer fallback.
echo If Windows Smart App Control blocks this file, use Launch_The_Dragons_Touch.pyw instead.
echo.

if exist "Launch_The_Dragons_Touch.pyw" (
    start "" "Launch_The_Dragons_Touch.pyw"
    exit /b 0
)

if exist "Launch_The_Dragons_Touch.py" (
    py -3 "Launch_The_Dragons_Touch.py"
    if %ERRORLEVEL%==0 exit /b 0
    python "Launch_The_Dragons_Touch.py"
    exit /b %ERRORLEVEL%
)

echo ERROR: Could not find Launch_The_Dragons_Touch.pyw or Launch_The_Dragons_Touch.py.
echo.
pause
exit /b 1
