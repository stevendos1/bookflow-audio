# docs/coding_standards.md
# Coding Standards (Python) - Hexagonal + Clean Code

## 1) Objetivo
Este documento define reglas de estilo y diseño para mantener:
- Arquitectura hexagonal (Ports & Adapters) consistente.
- Código legible, testeable, mantenible.
- Cambios pequeños, verificables y con bajo acoplamiento.

## 2) Estructura de capas (regla de oro)
- domain/: puro, sin IO, sin librerías externas, sin SQLite, sin TTS.
- application/: casos de uso + puertos (interfaces/Protocols), orquesta dominio.
- adapters/: implementaciones concretas de puertos (sqlite, parsers, tts, cli).
- infrastructure/: composition root (inyección, config, logging, main).

Prohibido:
- domain -> adapters/infrastructure
- application -> infrastructure
- application -> sqlite3 / tts libs / parsers concretos

## 3) Convenciones de nombres
- Paquetes y módulos: snake_case
- Clases: PascalCase
- Funciones y variables: snake_case
- Constantes: UPPER_SNAKE_CASE
- Protocols (puertos): Nombre + "Port" o nombre del servicio (ej: BookRepository)

Ejemplos:
- BookRepository (Protocol)
- SqliteBookRepository (adapter)
- ImportBook (use case)
- import_book_cli (primary adapter helper)

## 4) Tipado y contratos
- Todas las funciones públicas: type hints.
- Puertos: typing.Protocol + métodos mínimos necesarios.
- Preferir tipos del dominio (BookId, ChapterIndex, BlockIndex) para claridad.
- Evitar Any; si es inevitable, encapsular y documentar.

## 5) Estilo y formato
- Ruff para lint.
- Black o ruff format para formato.
- Imports ordenados (ruff/isort).
- Docstrings cortas:
  - Qué hace.
  - Parámetros importantes.
  - Errores relevantes.

## 6) Presupuestos de complejidad
- Complejidad ciclomática objetivo <= 2 (máximo <= 4).
- Funciones objetivo <= 40 líneas (máximo <= 100).
- Archivos objetivo <= 100 líneas (máximo <= 200).
Si se supera:
- Extraer funciones.
- Simplificar control de flujo.
- Aplicar patrón estrategia o tablas de dispatch.

## 7) Errores (pattern)
- Definir errores por capa:
  - domain: DomainError
  - application: AppError
  - adapters: AdapterError (wrap de libs externas)
- No atrapar Exception sin re-lanzar con contexto.
- Mensajes para usuario:
  - cortos, accionables, sin stacktrace.
- Logs:
  - con contexto (book_id, path, chapter_idx, block_idx)
  - sin texto completo del libro.

## 8) Logging
- Logger único configurado en infrastructure.
- application y adapters reciben logger o usan getLogger(__name__).
- No loguear contenido del libro:
  - usar hash del bloque o IDs.

## 9) Pureza del dominio
- domain no lee archivos, no usa sqlite, no habla con TTS.
- domain solo contiene:
  - entidades (Book, Chapter, Block, Progress)
  - reglas (chunking, normalización)
  - validaciones y decisiones puras

## 10) Use cases (application)
- Un use case = una intención del usuario.
- Entrada y salida explícitas (DTOs simples si aplica).
- No usar print() en use cases.
- No levantar threads en use cases:
  - si es necesario, encapsular en un puerto (JobRunner) o en adapter.

## 11) Adapters
### 11.1 Primary adapters (CLI/tray/UI)
- Parsean argumentos y llaman use cases.
- No implementan lógica de dominio.
- Manejan errores para mostrar al usuario.

### 11.2 Secondary adapters (sqlite/parsers/tts)
- Implementan puertos con librerías externas.
- Convierten errores de librería a AdapterError con contexto.
- Son intercambiables (ej: pyttsx3 vs piper).

## 12) Configuración
- Config en infrastructure:
  - archivo local (toml/yaml/json) o env vars.
- application no lee env vars directamente.
- Valores por defecto seguros.

## 13) IO y performance
- Evitar cargar libros completos si no es necesario.
- Procesar por capítulos/páginas/bloques.
- Cache opcional para audio por bloque.
- Evitar O(n^2); si se requiere, documentar en ADR.

## 14) Revisión de cambios (checklist)
- ¿Se rompió una dependencia entre capas?
- ¿Se añadieron librerías innecesarias?
- ¿Hay funciones largas o con ifs anidados?
- ¿Hay tests?
- ¿Se actualizó docs (mvp/backlog/adr)?

## 15) Plantillas de código (mini)
### Puerto (application/ports)
- Protocol con métodos mínimos.
- Documentar expectativas (sin hablar de sqlite ni libs concretas).

### Adapter (adapters/secondary)
- Implementación concreta.
- Manejo de errores.
- Tests de integración si toca IO real.