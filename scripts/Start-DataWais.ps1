param(
  [string]$PythonExe = '',
  [string]$Pm2Command = 'pm2',
  [string]$CloudflaredExe = '',
  [string]$DependencyFolder = '',
  [string]$Pm2Script = ''
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
if ($Pm2Script) {
  $env:DATAWAIS_PM2_SCRIPT = (Resolve-Path -LiteralPath $Pm2Script).Path
} else {
  $resolvedPm2 = (Get-Command $Pm2Command -ErrorAction Stop).Source
  $pm2NodeScript = Join-Path (Split-Path -Parent $resolvedPm2) 'node_modules\pm2\bin\pm2'
  if (-not (Test-Path -LiteralPath $pm2NodeScript)) { $pm2NodeScript = Join-Path (Split-Path -Parent $resolvedPm2) '..\pm2\bin\pm2' }
  if (-not (Test-Path -LiteralPath $pm2NodeScript)) { throw 'Pass -Pm2Script with the pm2 Node entrypoint path.' }
  $env:DATAWAIS_PM2_SCRIPT = (Resolve-Path -LiteralPath $pm2NodeScript).Path
}
if (Test-Path -LiteralPath '.runtime\public-host.txt') { $env:DATAWAIS_PUBLIC_HOST = (Get-Content -LiteralPath '.runtime\public-host.txt' -Raw).Trim() }
$rawManaged = & $Pm2Command jlist | Out-String
$managed = $rawManaged | & $PythonExe -c "import json,sys; text=sys.stdin.read(); start=text.find('[{'); start=start if start>=0 else text.find('[]'); data=json.loads(text[start:]); print(json.dumps([{'name':p['name'],'status':p['pm2_env']['status']} for p in data]))" | ConvertFrom-Json
$tunnelStartUtc = $null
foreach ($name in @('datawais-server','datawais-tunnel')) {
  if ($name -eq 'datawais-tunnel' -and -not $CloudflaredExe) { continue }
  $entry = $managed | Where-Object { $_.name -eq $name }
  if (-not $entry) {
    if ($name -eq 'datawais-tunnel') { $tunnelStartUtc = [DateTime]::UtcNow }
    & $Pm2Command start ecosystem.config.cjs --only $name
  }
  elseif ($entry.status -ne 'online') {
    if ($name -eq 'datawais-tunnel') { $tunnelStartUtc = [DateTime]::UtcNow }
    & $Pm2Command restart $name --update-env
  }
  if ($LASTEXITCODE -ne 0) { throw "Could not start $name" }
}
if ($CloudflaredExe) {
  $ready = $false
  for ($attempt = 0; $attempt -lt 30; $attempt++) {
    if (Test-Path -LiteralPath '.runtime\public-url.txt') {
      $url = (Get-Content -LiteralPath '.runtime\public-url.txt' -Raw).Trim()
      try {
        # Startup checks local service readiness. Public DNS may have a router
        # negative-cache entry while a new quick-tunnel hostname propagates.
        $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8765/healthz' -TimeoutSec 2
        $currentUrl = (-not $tunnelStartUtc) -or ((Get-Item -LiteralPath '.runtime\public-url.txt').LastWriteTimeUtc -ge $tunnelStartUtc)
        if ($health.status -eq 'ok' -and $currentUrl) { $ready = $true; break }
      } catch { }
    }
    Start-Sleep -Seconds 1
  }
  if (-not $ready) { throw 'Public endpoint not ready. Inspect .runtime/tunnel.err.log.' }
  Write-Output "Authenticated MCP endpoint: $url"
}
& $Pm2Command save
Write-Output 'DataWais is running under pm2.'
