param(
    [string]$Host = "0.0.0.0",
    [int]$Port = 5173
)

$ErrorActionPreference = "Stop"

$frontendRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$npmCmd = Get-Command "npm.cmd" -ErrorAction SilentlyContinue

if (-not $npmCmd) {
    throw @"
npm.cmd was not found.

On Windows, PowerShell can block npm.ps1 because of Execution Policy.
This project uses npm.cmd instead.

After installing Node.js, run:
  cd frontend
  npm.cmd install
  npm.cmd run dev -- --host 0.0.0.0
"@
}

$nodeModules = Join-Path $frontendRoot "node_modules"
if (-not (Test-Path $nodeModules)) {
    Write-Host "node_modules was not found. Running npm.cmd install..."
    Set-Location $frontendRoot
    & $npmCmd.Source install
    if ($LASTEXITCODE -ne 0) {
        throw "npm.cmd install failed."
    }
}

Set-Location $frontendRoot
& $npmCmd.Source run dev -- --host $Host --port $Port
