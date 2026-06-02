param(
    [string]$ListenHost = "127.0.0.1",
    [int]$Port = 8000
)

$backendRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $backendRoot ".venv\Scripts\python.exe"
$anacondaSqliteBin = "C:\ProgramData\Anaconda3\Library\bin"
$setupScript = Join-Path $backendRoot "setup_backend.ps1"

if (!(Test-Path $venvPython)) {
    throw @"
backend\.venv was not found.
Run the first-time setup.

  powershell -ExecutionPolicy Bypass -File backend\setup_backend.ps1

README:
  See README.md and backend/README.md
"@
}

if ((Test-Path $anacondaSqliteBin) -and ($env:PATH -notlike "*$anacondaSqliteBin*")) {
    $env:PATH = $anacondaSqliteBin + ";" + $env:PATH
}

Set-Location $backendRoot

try {
    & $venvPython -c "import uvicorn" | Out-Null
} catch {
    throw @"
uvicorn was not found.
requirements.txt may not be installed yet.

Run:
  powershell -ExecutionPolicy Bypass -File backend\setup_backend.ps1

Or:
  .\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
"@
}

& $venvPython -m uvicorn app.main:app --host $ListenHost --port $Port
