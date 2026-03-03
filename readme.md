# Lector de Libros

Aplicación para abrir libros (`.epub`, `.txt`, `.pdf`) y escucharlos como audio.

## Qué hace el programa

- Importa un archivo de libro.
- Lo divide en bloques de texto.
- Lee en voz alta con controles de reproducción.
- Permite cambiar voz, velocidad y prefetch.
- Guarda progreso para continuar después.

## 1) Instalacion rapida (1 click)

En la carpeta [installers](/home/steven/Documents/lector de libros/installers) tienes:

- `install-linux.sh`
- `install-mac.command`
- `install-win.bat`

Usa el archivo de tu sistema y dale doble click.

Si Linux/macOS no lo abre al primer intento, ejecuta una vez:

```bash
chmod +x installers/install-linux.sh installers/install-mac.command
```

Estos instaladores intentan:
- instalar Python si no existe,
- instalar dependencias de audio del sistema,
- crear `.venv` e instalar dependencias Python,
- abrir la app al final.

## 2) Instalacion manual (opcional)

### Requisitos

- Python 3.11 o superior.
- `pip`.

### Dependencias de audio por sistema

#### Linux (Ubuntu / Debian / Kali)

```bash
sudo apt update
sudo apt install -y mpg123 espeak-ng pulseaudio-utils
```

#### macOS

```bash
brew install mpg123
```

#### Windows

- Instala `mpg123` y agrégalo al `PATH`.

### Instalar el proyecto

#### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install edge-tts
```

#### Windows (PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
pip install edge-tts
```

## 3) Abrir la aplicación (GUI)

#### Linux / macOS

```bash
python -m src.infrastructure.gui_main
```

#### Windows

```powershell
py -m src.infrastructure.gui_main
```

## 4) Cómo usar (GUI)

1. Pulsa **Importar libro** y elige un archivo (`.epub`, `.txt`, `.pdf`).
2. Elige motor de voz:
   - `Edge TTS`: voz más natural (requiere internet).
   - `espeak`: local (sin internet), más robótico.
   - `Piper`: local neural (si está instalado).
3. Ajusta:
   - **Velocidad** (palabras por minuto).
   - **Prefetch** (bloques en caché para navegación más fluida).
4. Pulsa **Reproducir**.
5. Usa **Pausar**, **Siguiente**, **Anterior** o haz clic en un párrafo para saltar.

## 5) Uso por terminal (opcional)

Comando base:

```bash
python -m src.infrastructure.main <comando>
```

Comandos:

```bash
python -m src.infrastructure.main import <ruta>
python -m src.infrastructure.main list
python -m src.infrastructure.main play <book_id>
python -m src.infrastructure.main pause
python -m src.infrastructure.main next <book_id>
python -m src.infrastructure.main prev <book_id>
python -m src.infrastructure.main rate <velocidad>
python -m src.infrastructure.main voice list
python -m src.infrastructure.main voice set <voice_id>
python -m src.infrastructure.main status
```

## 6) Problemas comunes

- Error `ModuleNotFoundError: edge_tts`:
  - Ejecuta `pip install edge-tts`.

- Error `FileNotFoundError: mpg123`:
  - Instala `mpg123` y verifica que esté en `PATH`.
