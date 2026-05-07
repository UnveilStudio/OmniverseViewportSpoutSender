@echo off
rem One-shot installer for kit109.viewport_spout — see install.ps1 for details.
rem Drop this repo INSIDE your kit-app-template root (next to repo.bat) or as a
rem sibling of it, then double-click install.bat or run from a terminal.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
echo.
pause
