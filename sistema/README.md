# Sistema SEA-CU 2025

## Requisitos previos

Entorno objetivo: Windows 10 de 64 bits, sin Docker ni WSL2. Instala y comprueba estas versiones antes de empezar:

- Python 3.12.16: [descarga oficial](https://www.python.org/downloads/release/python-31216/).
- uv: [instalación oficial](https://docs.astral.sh/uv/getting-started/installation/). En Windows con WinGet: `winget install --id astral-sh.uv --exact`.
- Node.js v24.22.1: [distribución oficial](https://nodejs.org/dist/v24.22.1/).
- npm 11.19.1. Si la instalación de Node incluye otra versión, ejecuta `npm install --global npm@11.19.1`.
- Git 2.56.0: [Git for Windows](https://git-scm.com/download/win).

En PowerShell:

```powershell
node --version
npm --version
git --version
uv --version
```

La comprobación esperada es `Python 3.12.16`, `v24.22.1`, `11.19.1` y `git version 2.56.0` (Git for Windows puede añadir el sufijo `.windows.N`).

## Preparación desde un checkout limpio

Clona el repositorio y ejecuta los comandos desde su raíz:

```powershell
git clone https://github.com/arita9910/accreditation-evidence-manager.git
Set-Location .\accreditation-evidence-manager
```

Instala la versión requerida de Python administrada por uv y crea el entorno virtual del proyecto:

```powershell
uv python install 3.12.16
$python312 = uv python find 3.12.16
& $python312 --version
uv venv --python 3.12
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m ensurepip --upgrade
```

El último comando prepara pip desde la distribución de Python incluida; `uv venv` no necesariamente instala pip. Instala las dependencias del backend fijadas en `sistema/backend/requirements.txt`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\sistema\backend\requirements.txt
```

Instala las dependencias exactas del frontend desde el lockfile:

```powershell
Push-Location .\sistema\frontend
npm ci
Pop-Location
```

## Arranque en desarrollo

El módulo de desarrollo usa SQLite y no necesita PostgreSQL. En una ventana de PowerShell, desde la raíz:

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.ajustes.desarrollo"
Set-Location .\sistema\backend
& ..\..\.venv\Scripts\python.exe manage.py migrate
& ..\..\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

En una segunda ventana:

```powershell
Set-Location .\sistema\frontend
npm run dev -- --host 127.0.0.1
```

Abre la URL que Vite indique (por defecto `http://127.0.0.1:5173/`). Mantén ambos procesos en ejecución en ventanas separadas.

## Variables de producción

`.env.ejemplo` es una plantilla de nombres y valores ilustrativos; Django no carga archivos `.env` automáticamente. La configuración de producción exige `SECRET_KEY`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` y `DB_HOST`; `DB_PORT` usa `5432` si no se define. Selecciona `config.ajustes.produccion` mediante `DJANGO_SETTINGS_MODULE` y exporta los valores al entorno del proceso. No guardes claves ni contraseñas reales en Git. La configuración fija `DEBUG=False` y usa PostgreSQL; requiere una instancia PostgreSQL disponible para migraciones o consultas.

## Instalación sin conexión

La preparación se ejecuta una vez con conexión a internet y después puede repetirse en un equipo sin red. Crea antes `.venv` como se indica arriba. Los paquetes Python se guardan en `sistema/almacen/pip/` y la caché npm en `sistema/almacen/npm/`; ambos directorios son locales y están excluidos de Git.

En Windows PowerShell, desde la raíz del repositorio:

```powershell
.\sistema\scripts\descargar_paquetes.ps1
.\sistema\scripts\instalar_sin_conexion.ps1
```

En un shell POSIX:

```sh
sh sistema/scripts/descargar_paquetes.sh
sh sistema/scripts/instalar_sin_conexion.sh
```

La instalación sin conexión usa `pip --no-index` y `npm ci --offline`, por lo que no descarga paquetes de la red. npm instala las versiones reproducibles del `package-lock.json`; Python usa las versiones fijadas en `backend/requirements.txt`. `ensurepip` prepara pip usando la distribución incluida con Python. Prepara el almacén en una máquina con el mismo sistema operativo y arquitectura que el equipo sin conexión.
