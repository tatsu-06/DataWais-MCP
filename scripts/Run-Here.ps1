# Restart the verified local build on this computer, or a normal .venv install.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimeFile = Join-Path $projectRoot '.runtime\local-runtime.json'
$transcribing = $false
try {
  New-Item -ItemType Directory -Force -Path (Join-Path $projectRoot '.runtime') | Out-Null
  Start-Transcript -Path (Join-Path $projectRoot '.runtime\last-startup.log') -Force | Out-Null
  $transcribing = $true
  if (Test-Path -LiteralPath $runtimeFile) {
    $runtime = Get-Content -LiteralPath $runtimeFile -Raw | ConvertFrom-Json
    & (Join-Path $PSScriptRoot 'Start-DataWais.ps1') -PythonExe $runtime.python -Pm2Command $runtime.pm2 -DependencyFolder $runtime.dependencies -CloudflaredExe $runtime.cloudflared -Pm2Script $runtime.pm2_script
  } else {
    $environmentPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $environmentPython)) {
      throw 'This copy contains source code but has not been set up. Open the original configured DataWais folder or complete the README installation steps for this copy.'
    }
    & (Join-Path $PSScriptRoot 'Start-DataWais.ps1')
  }
  if ($LASTEXITCODE -ne 0) { throw 'A startup command failed. Read the messages above.' }
  Write-Host 'STARTUP COMPLETE - DataWais has passed its local health check.' -ForegroundColor Green
} catch {
  Write-Host ('STARTUP FAILED: ' + $_.Exception.Message) -ForegroundColor Red
  Write-Host ('Log: ' + (Join-Path $projectRoot '.runtime\last-startup.log'))
  exit 1
} finally {
  if ($transcribing) { Stop-Transcript | Out-Null }
}
