param(
    [string]$PythonVersion = ""
)

$ErrorActionPreference = "Stop"

$backendRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvDir = Join-Path $backendRoot ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"
$requirementsPath = Join-Path $backendRoot "requirements.txt"
$pyLauncher = (Get-Command "py.exe" -ErrorAction SilentlyContinue).Source

if (-not $pyLauncher) {
    throw "py.exe was not found. Install Python Launcher for Windows."
}

function Write-Step([string]$message) {
    Write-Host ""
    Write-Host "==> $message"
}

function Resolve-PythonCommand {
    $launcherList = & $pyLauncher -0p 2>$null
    $entries = @()

    foreach ($line in $launcherList) {
        $trimmed = $line.Trim()
        if (-not $trimmed) {
            continue
        }
        if ($trimmed -match '^(?<tag>-V:[^\s]+|\-[0-9.]+)\s+\*?\s*(?<path>.+)$') {
            $entries += [pscustomobject]@{
                LauncherArg = $matches.tag
                Path = $matches.path.Trim()
            }
        }
    }

    if ($PythonVersion) {
        $exact = $entries | Where-Object {
            $_.LauncherArg -eq "-$PythonVersion" -or $_.LauncherArg -eq "-V:$PythonVersion"
        } | Select-Object -First 1
        if ($exact) {
            try {
                $probe = & $pyLauncher $exact.LauncherArg -c "import sys; print(sys.executable)" 2>$null
                if ($LASTEXITCODE -eq 0 -and $probe) {
                    return @{
                        Version = $PythonVersion
                        LauncherArgs = @($exact.LauncherArg)
                        Executable = ($probe | Select-Object -First 1).Trim()
                    }
                }
            } catch {
            }
        }
        throw "Requested Python version was not found: $PythonVersion"
    }

    $preferredPatterns = @(
        'PythonSoftwareFoundation.*3\.12',
        'PythonSoftwareFoundation.*3\.11',
        'PythonSoftwareFoundation.*3\.10',
        'PythonSoftwareFoundation.*3\.9',
        'Anaconda',
        'ContinuumAnalytics'
    )

    $ordered = New-Object System.Collections.Generic.List[object]
    foreach ($pattern in $preferredPatterns) {
        foreach ($entry in ($entries | Where-Object { $_.Path -match $pattern -or $_.LauncherArg -match $pattern })) {
            if (-not ($ordered | Where-Object { $_.LauncherArg -eq $entry.LauncherArg })) {
                $ordered.Add($entry)
            }
        }
    }

    foreach ($entry in $entries) {
        if (-not ($ordered | Where-Object { $_.LauncherArg -eq $entry.LauncherArg })) {
            $ordered.Add($entry)
        }
    }

    foreach ($entry in $ordered) {
        try {
            $probe = & $pyLauncher $entry.LauncherArg -c "import sys; print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0 -and $probe) {
                return @{
                    Version = $entry.LauncherArg
                    LauncherArgs = @($entry.LauncherArg)
                    Executable = ($probe | Select-Object -First 1).Trim()
                }
            }
        } catch {
        }
    }

    $fallback = $entries | Select-Object -First 1
    if ($fallback -and $fallback.Path) {
        return @{
            Version = $fallback.LauncherArg
            LauncherArgs = @($fallback.LauncherArg)
            Executable = $fallback.Path
        }
    }

    throw @"
No usable Python interpreter was found.

Recommended:
  1. Install official Python 3.10 - 3.12
  2. Run: py -0p
  3. Re-run:
     powershell -ExecutionPolicy Bypass -File backend\setup_backend.ps1
"@
}

function Add-AnacondaDllPathIfNeeded([string]$pythonExe) {
    $pythonDir = Split-Path -Parent $pythonExe
    $candidates = @(
        (Join-Path $pythonDir "Library\bin"),
        (Join-Path (Split-Path -Parent $pythonDir) "Library\bin")
    )
    foreach ($anacondaBin in $candidates) {
        if ((Test-Path $anacondaBin) -and ($env:PATH -notlike "*$anacondaBin*")) {
            $env:PATH = $anacondaBin + ";" + $env:PATH
            Write-Host "Added Anaconda DLL path: $anacondaBin"
            break
        }
    }
}

function Test-PythonModules([string]$pythonExe) {
    $code = "import ssl, sqlite3; print('OPENSSL=' + ssl.OPENSSL_VERSION); print('SQLITE=' + sqlite3.sqlite_version)"
    $output = & $pythonExe -c $code 2>&1
    return @{
        Success = ($LASTEXITCODE -eq 0)
        Output = $output
    }
}

function Ensure-Venv([string]$pythonExe) {
    if (Test-Path $venvPython) {
        Write-Host "backend\.venv already exists."
        return
    }

    Write-Step "Creating backend\.venv"
    & $pythonExe -m venv $venvDir
    if (!(Test-Path $venvPython)) {
        throw "Failed to create backend\.venv."
    }
}

function Ensure-PipAndRequirements {
    Write-Step "Upgrading pip"
    & $venvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        throw @"
Failed to upgrade pip.

If you saw 'ssl module in Python is not available':
  - The selected Python cannot make HTTPS requests
  - Anaconda Python 3.8 is not recommended here
  - Install official Python 3.10 - 3.12 and recreate backend\.venv
"@
    }

    Write-Step "Installing backend requirements"
    & $venvPython -m pip install -r $requirementsPath
    if ($LASTEXITCODE -ne 0) {
        throw @"
Failed to install requirements.txt.

Common causes:
  - Python SSL is broken
  - Network access is blocked

Check:
  py -0p
  py -3.12 -c "import ssl, sqlite3; print(ssl.OPENSSL_VERSION); print(sqlite3.sqlite_version)"
"@
    }
}

Write-Step "Detecting Python"
$pythonInfo = Resolve-PythonCommand
Write-Host "Python executable: $($pythonInfo.Executable)"
Write-Host "Python version: $($pythonInfo.Version)"

Add-AnacondaDllPathIfNeeded -pythonExe $pythonInfo.Executable

Write-Step "Checking ssl and sqlite3"
$moduleCheck = Test-PythonModules -pythonExe $pythonInfo.Executable
if (-not $moduleCheck.Success) {
    $outputText = ($moduleCheck.Output | Out-String).Trim()
    throw @"
The selected Python failed the ssl/sqlite3 check.

$outputText

Recommended:
  - Prefer official Python 3.10 - 3.12
  - Run: py -0p
  - Example:
    py -3.12 -c "import ssl, sqlite3; print(ssl.OPENSSL_VERSION); print(sqlite3.sqlite_version)"
"@
}

$moduleCheck.Output | ForEach-Object { Write-Host $_ }

Ensure-Venv -pythonExe $pythonInfo.Executable
Ensure-PipAndRequirements

Write-Step "Final check"
& $venvPython -c "import ssl, sqlite3; print('OPENSSL=' + ssl.OPENSSL_VERSION); print('SQLITE=' + sqlite3.sqlite_version)"

Write-Host ""
Write-Host "Backend setup is complete."
Write-Host "Start the backend with:"
Write-Host "  powershell -ExecutionPolicy Bypass -File backend\run_backend.ps1"
