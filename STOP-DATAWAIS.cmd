@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Stop-DataWais.ps1"
if errorlevel 1 pause
