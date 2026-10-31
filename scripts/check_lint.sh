#!/bin/sh
set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project_root"

if [ ! -x .venv/bin/ruff ]; then
    echo "Install development tools: .venv/bin/python -m pip install -r requirements-dev.txt" >&2
    exit 1
fi

exec .venv/bin/ruff check .
