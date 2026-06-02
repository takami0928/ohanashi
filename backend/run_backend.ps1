param(
    [string]$ListenHost = "127.0.0.1",
    [int]$Port = 8000
)

$backendRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $backendRoot ".venv\Scripts\python.exe"
$anacondaSqliteBin = "C:\ProgramData\Anaconda3\Library\bin"

if (!(Test-Path $venvPython)) {
    throw "backend\.venv\Scripts\python.exe was not found. Create the backend venv first."
}

if ((Test-Path $anacondaSqliteBin) -and ($env:PATH -notlike "*$anacondaSqliteBin*")) {
    $env:PATH = $anacondaSqliteBin + ";" + $env:PATH
}

Set-Location $backendRoot
& $venvPython -m uvicorn app.main:app --host $ListenHost --port $Port
