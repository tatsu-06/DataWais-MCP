@echo off
setlocal
cd /d "%~dp0"
title DataWais MCP Startup
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Run-Here.ps1"
set "DATAWAIS_START_EXIT=%ERRORLEVEL%"
echo.
if "%DATAWAIS_START_EXIT%"=="0" (
  echo DataWais is running in the background.
  echo Closing this window will NOT stop the server.
  echo Open DOCUMENTATION.cmd to view server diagnostics.
) else (
  echo DataWais did not finish starting.
  echo Read the error above. A startup log is saved in .runtime\last-startup.log.
)
echo.
if /I "%~1"=="--no-pause" goto finish
pause
:finish
exit /b %DATAWAIS_START_EXIT%
