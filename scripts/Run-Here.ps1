# Restart the verified local build on this computer, or a normal .venv install.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimeFile = Join-Path $projectRoot '.runtime\local-runtime.json'
if (Test-Path -LiteralPath $runtimeFile) {
  $runtime = Get-Content -LiteralPath $runtimeFile -Raw | ConvertFrom-Json
  & (Join-Path $PSScriptRoot 'Start-DataWais.ps1') -PythonExe $runtime.python -Pm2Command $runtime.pm2 -DependencyFolder $runtime.dependencies -CloudflaredExe $runtime.cloudflared -Pm2Script $runtime.pm2_script
} else {
  & (Join-Path $PSScriptRoot 'Start-DataWais.ps1')
}
