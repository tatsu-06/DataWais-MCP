param([string]$Pm2Command = 'pm2')
$projectRoot = Split-Path -Parent $PSScriptRoot
$env:PM2_HOME = Join-Path $projectRoot '.runtime\pm2'
& $Pm2Command stop datawais-server
& $Pm2Command stop datawais-tunnel
