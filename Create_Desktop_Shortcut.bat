@echo off
setlocal EnableExtensions

REM The Dragon's Touch Shortcut Creator - Deferred / Developer Fallback Only
REM v0.7.7L.3
REM Desktop shortcut support is deferred because Smart App Control blocked the shortcut path.
REM Supported v0.7 alpha path: double-click Launch_The_Dragons_Touch.pyw.

cd /d "%~dp0"
title The Dragon's Touch Shortcut Deferred

echo.
echo ============================================
echo   The Dragon's Touch - Shortcut Deferred
echo ============================================
echo.
echo Desktop shortcut support is deferred for v0.7 alpha.
echo Windows Smart App Control blocked the shortcut path during testing.
echo.
echo Supported alpha launch path:
echo   Launch_The_Dragons_Touch.pyw
echo.
echo Do not disable Smart App Control just to create a shortcut.
echo.
pause
exit /b 0
