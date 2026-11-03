#!/usr/bin/env sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
system_root=$(CDPATH= cd -- "$script_dir/.." && pwd)
repository_root=$(CDPATH= cd -- "$system_root/.." && pwd)
pip_store="$system_root/almacen/pip"
npm_cache="$system_root/almacen/npm"

if [ -x "$repository_root/.venv/Scripts/python.exe" ]; then
    python="$repository_root/.venv/Scripts/python.exe"
elif [ -x "$repository_root/.venv/bin/python" ]; then
    python="$repository_root/.venv/bin/python"
else
    python=${PYTHON:-python3}
fi

mkdir -p "$pip_store" "$npm_cache"
"$python" -m ensurepip --upgrade
"$python" -m pip download --dest "$pip_store" -r "$system_root/backend/requirements.txt"
npm --prefix "$system_root/frontend" ci --cache "$npm_cache"
