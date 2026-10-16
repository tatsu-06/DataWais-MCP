$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$task = Get-ScheduledTask -TaskName 'DataWais MCP (PT1)' -ErrorAction SilentlyContinue
if ($task -and ($task.Actions.Arguments -like "*$projectRoot*")) {
  Disable-ScheduledTask -TaskName 'DataWais MCP (PT1)' | Out-Null
  Write-Output 'DataWais automatic startup disabled. Running processes can be stopped separately.'
}
