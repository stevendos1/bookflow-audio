# agent.md
# Reglas del Agente de IA (Arquitectura Hexagonal + Calidad + MVP)
# Objetivo: que la IA NO rompa la arquitectura ni degrade calidad.

## 0) Rol y alcance
- Eres un agente de desarrollo. Produces cambios mínimos y verificables.
- Tu prioridad es: Correctitud > Arquitectura > Test > Simplicidad > Perf.
- No inventes APIs ni dependencias. Si falta algo, propón y agrega con cuidado.
- No escribas "TODO" sin ticket o tarea concreta en docs/backlog.md.

## 1) Principios no negociables
- Arquitectura HEXAGONAL (Ports & Adapters). Dominio aislado.
- Clean Code, SOLID, DRY, KISS, YAGNI.
- Determinismo: misma entrada -> misma salida. Evita estados ocultos.
- Seguridad por defecto (no ejecutar/abrir archivos inseguros, no shell-injection).
- Observabilidad: logs estructurados, errores con contexto.

## 2) Presupuestos de complejidad (obligatorio)
- Complejidad ciclomática por función: objetivo <= 2. Máximo permitido <= 4.
- Longitud por función: objetivo <= 40 líneas. Máximo permitido <= 100 líneas.
- Longitud por archivo: objetivo <= 250 líneas. Máximo permitido <= 400 líneas.
- Complejidad temporal:
  - Evita algoritmos peores que O(n^2). Si O(n^2) es inevitable, justifica.
  - Prefiere O(n log n) u O(n) y cacheo de resultados cuando aplique.
- Complejidad espacial:
  - Evita cargar libros completos si no es necesario. Trabaja por "chunks".

## 3) Diseño de carpetas (propuesto, no romper)
- src/
  - domain/                # Entidades y reglas puras (sin IO, sin libs externas)
  - application/           # Casos de uso (orquestación) + puertos (interfaces)
  - adapters/
    - primary/             # Entradas: CLI, tray, UI (controladores)
    - secondary/           # Salidas: parsers, TTS, audio, repositorios
  - infrastructure/        # Wiring: config, DI, logging setup, main
- tests/
  - unit/                  # domain + application
  - integration/           # adapters + infra
- docs/                    # ADRs, MVP, decisiones

## 4) Reglas de dependencias (hexagonal)
- domain/ NO depende de nada fuera de domain/.
- application/ puede depender de domain/ y de puertos (Protocols) en application/.
- adapters/ implementan puertos. Pueden depender de application/ y domain/.
- infrastructure/ arma el "composition root" (inyección, config).
- Prohibido: domain -> adapters/infrastructure.
- Prohibido: application -> infrastructure.
- Permitido: infrastructure -> todo (solo para wiring).

## 5) Puertos (Ports) obligatorios (ejemplos)
- BookRepository: persistencia de libros + progreso (SQLite local).
- BookParser: parsea archivos (EPUB/PDF/TXT) a modelo común.
- TtsEngine: convierte texto a audio o lo reproduce.
- AudioPlayer: reproduce audio (si TTS genera WAV/PCM).
- Clock: tiempo (para métricas, guardado periódico).
- FileSystem: operaciones de archivos (para tests y seguridad).

## 6) Modelo de dominio (guía)
- Entidades simples, inmutables cuando sea posible.
- Preferir dataclasses(frozen=True) o NamedTuple si aplica.
- Errores de dominio: excepciones propias (DomainError) sin stack "ruidoso".
- No meter lógica de parsing ni SQL en el dominio.

## 7) Estándares de código (Python)
- Python 3.11+.
- Typing estricto:
  - type hints en todo.
  - Protocols en puertos.
  - mypy/pyright recomendado.
- Formato:
  - black + ruff (o ruff format).
  - isort si no usas ruff.
- Docstrings cortas estilo Google o reST.
- Nombres:
  - funciones/vars: snake_case
  - clases: PascalCase
  - constantes: UPPER_SNAKE_CASE

## 8) Manejo de errores (sin caos)
- No uses "except Exception" sin re-lanzar con contexto o log.
- Cada error debe tener:
  - causa original,
  - contexto (book_id, ruta, capítulo/bloque),
  - mensaje accionable.
- En UI/CLI: mostrar mensajes amigables; log con detalle técnico.

## 9) Logging y telemetría local
- Logging estructurado (dict) si es posible; si no, logs consistentes.
- Niveles:
  - INFO: eventos de usuario (play, pause, import).
  - DEBUG: chunking, latencias.
  - WARNING: degradaciones (voz no disponible).
  - ERROR: fallos (IO, parse, DB).
- No loguear contenido completo del libro. Solo hashes/IDs.

## 10) Persistencia (SQLite) - reglas
- SQL parametrizado SIEMPRE.
- Migraciones versionadas.
- Transacciones para operaciones multi-paso.
- Nunca bloquear UI: IO/DB en worker thread o async.
- Progreso guardado:
  - al cambiar de bloque,
  - cada N segundos (configurable),
  - al pausar/salir.

## 11) Parsing de libros (calidad de texto)
- TXT: lectura segura (encoding detect / fallback utf-8).
- EPUB:
  - extraer capítulos (spine),
  - HTML -> texto (BeautifulSoup),
  - preservar saltos de párrafo.
- PDF:
  - usar extracción por páginas (no cargar todo),
  - limpiar cortes de línea y guiones (heurísticas),
  - detectar repetición de header/footer (heurística simple).
- PDF escaneado:
  - no se hace en MVP.
  - si se implementa: Tesseract como adapter separado.

## 12) Chunking (clave para audiolibro)
- Convertir texto a bloques "speakables":
  - tamaño objetivo 500–1200 chars.
  - cortar en puntuación (.,;:!?).
  - nunca cortar en medio de palabra.
- Cada bloque tiene ID estable:
  - (book_id, chapter_idx, block_idx, text_hash).
- Permitir reanudar exacto:
  - chapter_idx + block_idx + offset (si aplica).

## 13) Concurrencia y UX "mientras trabajo"
- No bloquear el hilo principal por TTS/parsing.
- Pre-cargar:
  - generar o preparar el próximo bloque en background.
- Controles mínimos:
  - play/pause, next/prev block,
  - rate +/-,
  - select voice,
  - stop + guardar progreso.
- Modo "headless": CLI + tray sin ventana grande.

## 14) SSR (si aplica)
- Solo aplica si hay UI web (Tauri/Electron/web app).
- Si hay UI web:
  - SSR para pantallas estáticas, si mejora carga/SEO.
  - No mezclar lógica de dominio en UI; usar API local.

## 15) Testing (obligatorio)
- Unit tests:
  - dominio: reglas, chunking, normalización.
  - application: casos de uso con fakes de puertos.
- Integration:
  - SQLite real en temp file.
  - parser EPUB/PDF con fixtures pequeños.
- Reglas:
  - tests deterministas (sin red).
  - sin sleeps frágiles (usar Clock fake).
  - coverage objetivo: 80%+ en domain+application.

## 16) Calidad de PR (checklist)
Antes de entregar cambios:
- [ ] Compila / corre.
- [ ] Formateado (black/ruff).
- [ ] Tests pasan.
- [ ] No se violan dependencias de capas.
- [ ] Funciones <= 100 líneas, complejidad <= 4.
- [ ] Docs actualizadas (si cambia contrato o CLI).
- [ ] No hay secretos, rutas hardcoded, ni logs de contenido.

## 17) Protocolo de implementación (cómo trabajas)
- Cambios pequeños, en commits lógicos (si aplica).
- Primero escribe el contrato (puerto) y tests.
- Luego implementa adapter.
- Finalmente wiring en infrastructure/.
- Si hay decisión grande: crear ADR en docs/adr/.

## 18) Anti-patrones prohibidos
- "God objects" (ReaderManager con 20 responsabilidades).
- Inyección global oculta (singletons sin control).
- Importar sqlite3 en application/ o domain/.
- Mezclar parsing con TTS.
- Mezclar CLI/tray con dominio.
- Meter lógica de chunking en UI.

## 19) Entregables mínimos por iteración
- Feature con:
  - contrato claro,
  - tests,
  - docs y ejemplo de uso,
  - manejo de errores.

## 20) Si hay ambigüedad
- Elige la opción más simple y modular.
- Documenta supuestos en docs/mvp.md o un ADR corto.