#!/usr/bin/env bash
# Запуск VLauncher на macOS и Linux.
set -euo pipefail

cd "$(dirname "$0")"

PYTHON=""
for cmd in python3.12 python3.11 python3.10 python3; do
  if command -v "$cmd" >/dev/null 2>&1; then
    ver="$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    major="${ver%%.*}"
    minor="${ver#*.}"
    if (( major > 3 || (major == 3 && minor >= 10) )); then
      PYTHON="$cmd"
      break
    fi
  fi
done

if [[ -z "$PYTHON" ]]; then
  echo "Python 3.10+ не найден."
  echo "macOS:  brew install python@3.12"
  echo "Linux:  sudo apt install python3 python3-venv python3-pip"
  echo "Или:    https://www.python.org/downloads/"
  exit 1
fi

if ! command -v git >/dev/null 2>&1; then
  echo "Git не найден."
  echo "macOS:  xcode-select --install  или  brew install git"
  echo "Linux:  sudo apt install git"
  exit 1
fi

if [[ ! -d .venv ]]; then
  echo "Создание виртуального окружения (.venv)..."
  "$PYTHON" -m venv .venv
fi

VENV_PY=".venv/bin/python3"
if [[ ! -x "$VENV_PY" ]]; then
  VENV_PY=".venv/bin/python"
fi

echo "Установка зависимостей..."
"$VENV_PY" -m pip install -q --upgrade pip
"$VENV_PY" -m pip install -q -r requirements.txt

echo "Запуск VLauncher..."
nohup "$VENV_PY" main.py >/dev/null 2>&1 &
disown -h 2>/dev/null || true
