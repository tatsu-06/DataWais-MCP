param([ValidateSet('inspector','cleaner','admin')][string]$Role = 'cleaner')
# Authentication helper: only the MCP host should capture this output.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$credentials = Get-Content -LiteralPath (Join-Path $projectRoot '.runtime\secrets.json') -Raw | ConvertFrom-Json
@{ Authorization = 'Bearer ' + $credentials.tokens.$Role } | ConvertTo-Json -Compress
