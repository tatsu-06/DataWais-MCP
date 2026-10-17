param([string]$Section = '')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$settings = Join-Path $projectRoot '.runtime\local-runtime.json'
if (Test-Path -LiteralPath $settings) {
  $runtime = Get-Content -LiteralPath $settings -Raw | ConvertFrom-Json
  $pythonExe = $runtime.python
  $env:DATAWAIS_DEPS = $runtime.dependencies
} else {
  $pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
}
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Complete README setup before opening the documentation helper.' }
if ($Section) { & $pythonExe scripts\bootstrap.py datawais.documentation --section $Section }
else { & $pythonExe scripts\bootstrap.py datawais.documentation }
if ($LASTEXITCODE -ne 0) { throw 'Documentation check failed; start the server and check its status.' }
