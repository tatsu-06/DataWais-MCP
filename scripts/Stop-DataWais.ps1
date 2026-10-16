param([string]$Pm2Command = '')
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $Pm2Command) {
  $runtimeFile = Join-Path $projectRoot '.runtime\local-runtime.json'
  if (Test-Path -LiteralPath $runtimeFile) { $Pm2Command = (Get-Content -LiteralPath $runtimeFile -Raw | ConvertFrom-Json).pm2 }
  else { $Pm2Command = 'pm2' }
}
$env:PM2_HOME = Join-Path $projectRoot '.runtime\pm2'
& $Pm2Command stop datawais-server
& $Pm2Command stop datawais-tunnel
