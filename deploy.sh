#!/bin/bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv}"
BUILD_ONLY=false

if [[ "${1:-}" == "--build-only" ]]; then
  BUILD_ONLY=true
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  python3 -m venv "$VENV_DIR"
fi

PYTHON_BIN="$VENV_DIR/bin/python"

"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install --upgrade build twine

rm -rf "$ROOT_DIR/dist"
"$PYTHON_BIN" -m build

if [[ "$BUILD_ONLY" == true ]]; then
  echo "Build completed. Skipping upload because --build-only was provided."
  exit 0
fi

"$PYTHON_BIN" -m twine upload "$ROOT_DIR"/dist/*
