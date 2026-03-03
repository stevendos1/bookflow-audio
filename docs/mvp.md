# docs/mvp.md
# MVP: Lector tipo audiolibro (Windows + Ubuntu/Kali) - Offline

## 1) Objetivo del MVP
- Reproducir libros como audio mientras el usuario trabaja.
- 100% local (sin nube).
- Soportar: EPUB, TXT, PDF con texto (no escaneado).
- Recordar progreso y reanudar exacto.

## 2) No objetivos (MVP)
- OCR para PDF escaneado.
- Sincronización entre dispositivos.
- Biblioteca con metadata perfecta (ISBN, covers).
- UI compleja tipo Kindle.

## 3) Flujos principales
### 3.1 Importar libro
- Entrada: ruta local (archivo).
- Output:
  - book_id creado,
  - capítulos y bloques generados (o indexados),
  - metadata mínima (título/autores best-effort),
  - progreso inicial en 0.

### 3.2 Reproducir / Pausar
- Play:
  - inicia en el bloque del progreso.
  - si no hay progreso: inicio del libro.
- Pause:
  - detiene audio,
  - guarda progreso inmediatamente.

### 3.3 Navegación
- Next/Prev block.
- Seek por capítulo (opcional en MVP, deseable).
- Rate +/- (velocidad).

### 3.4 Persistencia de progreso
- Guardar:
  - al finalizar cada bloque,
  - al pausar,
  - cada N segundos (config).

## 4) Requisitos no funcionales
- No bloquear UI/CLI por IO.
- Manejo robusto de errores (archivos faltantes, parse fallido).
- Logs locales sin filtrar texto del libro.
- Config local (archivo config, env vars o flags).

## 5) Arquitectura (hexagonal)
- domain/:
  - Book, Chapter, Block, Progress.
  - Chunking + normalización (reglas puras).
- application/:
  - Use cases:
    - ImportBook
    - PlayBook
    - Pause
    - NextBlock / PrevBlock
    - SetRate / SetVoice
  - Ports:
    - BookRepository
    - BookParser
    - TtsEngine
    - AudioPlayer (si aplica)
    - Clock / FileSystem
- adapters/:
  - primary:
    - CLI
    - tray (opcional)
  - secondary:
    - parsers: epub/pdf/txt
    - storage: sqlite
    - tts: pyttsx3 (MVP) + piper (opcional)
- infrastructure/:
  - DI / composition root
  - config + logging
  - main entrypoints

## 6) CLI mínima (MVP)
- commands:
  - import <path>
  - list
  - play <book_id>
  - pause
  - next / prev
  - rate <value>
  - voice list / voice set <id>
  - status
- salida humana + opción JSON (futuro).

## 7) Tray (post-MVP o fase 2)
- Icono con:
  - Play/Pause
  - Next/Prev
  - Rate +/-
  - Exit
- Mostrar libro actual + progreso (tooltip).

## 8) Definición de éxito (MVP)
- Importa EPUB/TXT/PDF con texto y lee sin trabarse.
- Play/Pause/Next funcionan.
- Reanuda donde quedó tras cerrar y abrir.
- Instalación simple en Windows y Ubuntu/Kali.

## 9) Decisiones Técnicas (MVP)
- **Reglas de Arquitectura**: Para mantener las dependencias al mínimo (solo `ruff` y `pytest`), la validación de importaciones prohibidas entre capas (`domain`, `application`, etc.) se efectúa mediante un script (`tests/unit/architecture_rules_test.py`) que parsea el AST de Python. Se optó por la simplicidad sobre el uso de herramientas de terceros más pesadas como `import-linter`.
- **EPUB Parser (stdlib-only)**: `EpubParser` usa `zipfile` + `xml.etree.ElementTree` + `html.parser` (todos stdlib). Supuesto: los EPUBs siguen la estructura estándar EPUB2/3 (container.xml + OPF + spine de XHTML). No se agrega `ebooklib` ni `bs4` para no introducir dependencias nuevas. Si en el futuro se necesita soporte de EPUBs no estándar o extracción de metadata compleja, evaluar `ebooklib` con ADR.
- **MultiFormatParser**: Composite adapter en `adapters/secondary/parsers/` que despacha a `TxtParser` o `EpubParser` según la extensión del archivo. La lógica de routing vive en adapters (implementa puerto `BookParser`). El composition root (`infrastructure/main.py`) registra los parsers disponibles.
- **PDF Parser**: Pendiente (backlog). Se usará `pymupdf` (fitz) como adapter separado. No agrega dependencias hasta que se cree el ADR correspondiente.