# docs/testing_strategy.md
# Testing Strategy - Offline Audiobook Reader

## 1) Objetivos
- Evitar regresiones.
- Garantizar contratos de puertos y casos de uso.
- Mantener determinismo (sin red, sin tiempo real, sin sleeps frágiles).

## 2) Pirámide de pruebas
1) Unit tests (rápidos, mayoría):
- domain/
- application/ (use cases con fakes)

2) Integration tests (moderados):
- sqlite adapter real (DB temporal)
- parsers con fixtures pequeños (epub/pdf/txt)
- tts engine: preferir fake, o smoke test opcional

3) E2E (pocos):
- CLI commands básicos con entorno temporal
- No obligatorio en MVP, pero deseable.

## 3) Qué testear (dominio)
- Normalización de texto:
  - unir líneas rotas
  - remover guiones de corte de palabra (heurística)
  - preservar párrafos
- Chunking:
  - tamaño objetivo (500-1200 chars)
  - corte en puntuación
  - no cortar palabras
  - estabilidad de IDs/hash
- Progreso:
  - avanzar bloque
  - retroceder bloque
  - reanudar con offset (si aplica)

## 4) Qué testear (application)
- ImportBook:
  - llama parser
  - guarda book + capítulos/bloques
  - guarda progreso inicial
- PlayBook:
  - carga progreso
  - produce secuencia de bloques
  - dispara TTS/Player (por puerto)
- Pause:
  - guarda progreso
- Next/Prev:
  - cambia bloque y guarda

Todos con fakes:
- FakeBookRepository
- FakeParser
- FakeTtsEngine / FakeAudioPlayer
- FakeClock (sin sleeps)

## 5) Qué testear (adapters)
### SQLite
- Crear schema v1
- Insertar y leer books
- Guardar y recuperar progreso
- Transacciones (consistencia)
- SQL parametrizado

### Parsers
- TXT: encoding + newline handling
- EPUB: capítulos + extracción de texto
- PDF: extracción por páginas, normalización básica

### TTS
- MVP: usar fake por defecto en tests.
- Smoke test opcional (marcado):
  - valida que el engine se inicializa y "speak" no revienta.

## 6) Fixtures
- tests/fixtures/
  - tiny.txt
  - tiny.epub (capítulos cortos)
  - tiny.pdf (texto simple)
- Mantener fixtures pequeños para velocidad.

## 7) Naming y estructura
- tests/unit/test_chunking.py
- tests/unit/test_normalize.py
- tests/unit/test_import_use_case.py
- tests/integration/test_sqlite_repo.py
- tests/integration/test_epub_parser.py

## 8) Reglas de calidad de tests
- AAA: Arrange, Act, Assert.
- Una razón de falla por test.
- Mensajes claros.
- Sin flakiness:
  - no sleeps
  - no depender del sistema
- Correr rápido:
  - unit < 2s ideal
  - integración < 10s ideal

## 9) Herramientas recomendadas
- pytest
- pytest-cov
- freezegun (si necesitas tiempo) o FakeClock propio
- hypothesis (opcional) para chunking properties

## 10) Gates (CI local)
- ruff
- format
- pytest
- cobertura objetivo:
  - domain+application >=100%