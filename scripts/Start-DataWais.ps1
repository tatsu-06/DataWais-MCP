param(
  [string]$PythonExe = '',
  [string]$Pm2Command = 'pm2',
  [string]$CloudflaredExe = '',
  [string]$DependencyFolder = ''
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if (-not $PythonExe) { $PythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe' }
if (-not (Test-Path -LiteralPath $PythonExe)) { throw 'Python environment missing. Follow README installation first.' }
if (-not (Test-Path -LiteralPath '.runtime\secrets.json')) {
  & $PythonExe scripts\init_demo.py
  if ($LASTEXITCODE -ne 0) { throw 'Workspace initialization failed.' }
}
$env:PM2_HOME = Join-Path $projectRoot '.runtime\pm2'
$env:DATAWAIS_PYTHON = (Resolve-Path -LiteralPath $PythonExe).Path
$env:DATAWAIS_DEPS = $DependencyFolder
if ($CloudflaredExe) { $env:DATAWAIS_CLOUDFLARED = (Resolve-Path -LiteralPath $CloudflaredExe).Path }
$savedHost = Join-Path $projectRoot '.runtime\public-host.txt'
if (Test-Path -LiteralPath $savedHost) { $env:DATAWAIS_PUBLIC_HOST = (Get-Content -LiteralPath $savedHost -Raw).Trim() }
& $Pm2Command start ecosystem.config.cjs
if ($LASTEXITCODE -ne 0) { throw 'Process manager could not start DataWais.' }
if ($CloudflaredExe) {
  $hostName = $null
  for ($attempt = 0; $attempt -lt 30; $attempt++) {
    Start-Sleep -Seconds 1
    if (Test-Path -LiteralPath '.runtime\tunnel.err.log') {
      $text = Get-Content -LiteralPath '.runtime\tunnel.err.log' -Raw
      $matchesFound = [regex]::Matches($text, 'https://([a-z0-9-]+\.trycloudflare\.com)')
      if ($matchesFound.Count) { $hostName = $matchesFound[$matchesFound.Count-1].Groups[1].Value; break }
    }
  }
  if (-not $hostName) { throw 'Tunnel URL unavailable. Inspect .runtime/tunnel.err.log.' }
  $hostName | Set-Content -LiteralPath $savedHost -NoNewline
  "https://$hostName/mcp" | Set-Content -LiteralPath '.runtime\public-url.txt' -NoNewline
  $env:DATAWAIS_PUBLIC_HOST = $hostName
  & $Pm2Command restart datawais-server --update-env
  Write-Output "Authenticated MCP endpoint: https://$hostName/mcp"
}
& $Pm2Command save
Write-Output 'DataWais is managed by pm2. Keep the computer awake for the demo; tokens are in .runtime/secrets.json.'
