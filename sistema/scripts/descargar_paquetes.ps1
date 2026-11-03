$ErrorActionPreference = "Stop"

$systemRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$repositoryRoot = (Resolve-Path (Join-Path $systemRoot "..")).Path
$python = Join-Path $repositoryRoot ".venv\Scripts\python.exe"
$pipStore = Join-Path $systemRoot "almacen\pip"
$npmCache = Join-Path $systemRoot "almacen\npm"

if (-not (Test-Path $python)) {
    $python = "python"
}

New-Item -ItemType Directory -Force -Path $pipStore, $npmCache | Out-Null
& $python -m ensurepip --upgrade
if ($LASTEXITCODE -ne 0) {
    throw "No se pudo preparar pip con ensurepip."
}

& $python -m pip download --dest $pipStore -r (Join-Path $systemRoot "backend\requirements.txt")
if ($LASTEXITCODE -ne 0) {
    throw "No se pudieron descargar las dependencias de Python."
}

Push-Location (Join-Path $systemRoot "frontend")
try {
    npm ci --cache $npmCache
    if ($LASTEXITCODE -ne 0) {
        throw "No se pudieron preparar las dependencias y la caché npm."
    }
}
finally {
    Pop-Location
}
