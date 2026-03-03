#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

info() { printf "[INFO] %s\n" "$*"; }
warn() { printf "[WARN] %s\n" "$*"; }
fail() { printf "[ERROR] %s\n" "$*"; exit 1; }

ensure_brew() {
  if command -v brew >/dev/null 2>&1; then
    return
  fi
  info "Homebrew no encontrado. Intentando instalar..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  if [[ -x /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [[ -x /usr/local/bin/brew ]]; then
    eval "$(/usr/local/bin/brew shellenv)"
  fi
  command -v brew >/dev/null 2>&1 || fail "No se pudo instalar Homebrew."
}

ensure_python() {
  if command -v python3 >/dev/null 2>&1; then
    return
  fi
  info "Python3 no encontrado. Intentando instalar con Homebrew..."
  brew install python
  command -v python3 >/dev/null 2>&1 || fail "No se pudo instalar Python3."
}

echo "== Instalador macOS =="
echo "Proyecto: $ROOT_DIR"

ensure_brew
ensure_python

info "Instalando mpg123..."
brew install mpg123 || warn "No se pudo instalar mpg123 automaticamente."

if [[ ! -d .venv ]]; then
  info "Creando entorno virtual..."
  python3 -m venv .venv
fi

VENV_PY=".venv/bin/python"
[[ -x "$VENV_PY" ]] || fail "No existe el Python del entorno virtual: $VENV_PY"

info "Instalando dependencias Python..."
"$VENV_PY" -m pip install --upgrade pip
"$VENV_PY" -m pip install -r requirements.txt
"$VENV_PY" -m pip install edge-tts

echo ""
echo "Instalacion terminada."
read -r -p "Quieres abrir la app ahora? [S/n]: " OPEN_APP
OPEN_APP="${OPEN_APP:-S}"
if [[ "$OPEN_APP" =~ ^[sS]$ ]]; then
  "$VENV_PY" -m src.infrastructure.gui_main
fi
