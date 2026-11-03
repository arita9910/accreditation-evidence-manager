$ErrorActionPreference = "Stop"

$systemRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$repositoryRoot = (Resolve-Path (Join-Path $systemRoot "..")).Path
$python = Join-Path $repositoryRoot ".venv\Scripts\python.exe"
$pipStore = Join-Path $systemRoot "almacen\pip"
$npmCache = Join-Path $systemRoot "almacen\npm"

if (-not (Test-Path $python)) {
    $python = "python"
}
if (-not (Test-Path $pipStore)) {
    throw "No existe el almacén Python: ejecuta descargar_paquetes.ps1 con conexión."
}
if (-not (Test-Path $npmCache)) {
    throw "No existe la caché npm: ejecuta descargar_paquetes.ps1 con conexión."
}

& $python -m ensurepip --upgrade
if ($LASTEXITCODE -ne 0) {
    throw "No se pudo preparar pip con ensurepip."
}

& $python -m pip install --no-index --find-links $pipStore -r (Join-Path $systemRoot "backend\requirements.txt")
if ($LASTEXITCODE -ne 0) {
    throw "No se pudieron instalar las dependencias de Python desde el almacén local."
}

Push-Location (Join-Path $systemRoot "frontend")
try {
    npm ci --offline --cache $npmCache
    if ($LASTEXITCODE -ne 0) {
        throw "No se pudieron instalar las dependencias npm desde la caché local."
    }
}
finally {
    Pop-Location
}
