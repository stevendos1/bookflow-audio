#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

info() { printf "[INFO] %s\n" "$*"; }
warn() { printf "[WARN] %s\n" "$*"; }
fail() { printf "[ERROR] %s\n" "$*"; exit 1; }

detect_pkg_manager() {
  if command -v apt-get >/dev/null 2>&1; then
    echo "apt"
  elif command -v dnf >/dev/null 2>&1; then
    echo "dnf"
  elif command -v pacman >/dev/null 2>&1; then
    echo "pacman"
  elif command -v zypper >/dev/null 2>&1; then
    echo "zypper"
  else
    echo "unknown"
  fi
}

install_python_linux() {
  local pm="$1"
  case "$pm" in
    apt)
      sudo apt-get update
      sudo apt-get install -y python3 python3-venv python3-pip
      ;;
    dnf)
      sudo dnf install -y python3 python3-pip
      ;;
    pacman)
      sudo pacman -Sy --noconfirm python python-pip
      ;;
    zypper)
      sudo zypper --non-interactive install python3 python3-pip
      ;;
    *)
      fail "No se pudo detectar gestor de paquetes para instalar Python automaticamente."
      ;;
  esac
}

install_audio_linux() {
  local pm="$1"
  case "$pm" in
    apt)
      sudo apt-get update
      sudo apt-get install -y mpg123 espeak-ng pulseaudio-utils
      ;;
    dnf)
      sudo dnf install -y mpg123 espeak-ng pulseaudio-utils
      ;;
    pacman)
      sudo pacman -Sy --noconfirm mpg123 espeak-ng pulseaudio
      ;;
    zypper)
      sudo zypper --non-interactive install mpg123 espeak-ng pulseaudio-utils
      ;;
    *)
      warn "Instala manualmente: mpg123, espeak-ng y utilidades de PulseAudio."
      ;;
  esac
}

ensure_python() {
  if command -v python3 >/dev/null 2>&1; then
    return
  fi
  info "Python3 no encontrado. Intentando instalarlo..."
  install_python_linux "$PKG_MANAGER"
  command -v python3 >/dev/null 2>&1 || fail "No se pudo instalar Python3."
}

ensure_venv() {
  if [[ -d .venv ]]; then
    return
  fi
  info "Creando entorno virtual..."
  if ! python3 -m venv .venv; then
    warn "Fallo creando venv. Intentando instalar modulo venv..."
    if [[ "$PKG_MANAGER" == "apt" ]]; then
      sudo apt-get install -y python3-venv
      python3 -m venv .venv
    else
      fail "No se pudo crear entorno virtual."
    fi
  fi
}

echo "== Instalador Linux =="
echo "Proyecto: $ROOT_DIR"

PKG_MANAGER="$(detect_pkg_manager)"
info "Gestor detectado: $PKG_MANAGER"

ensure_python
info "Instalando dependencias de audio..."
install_audio_linux "$PKG_MANAGER"

ensure_venv

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
