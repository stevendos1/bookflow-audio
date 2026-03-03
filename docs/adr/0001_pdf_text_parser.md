# ADR 0001: Parser de PDF con texto (no OCR)

## Estado
Aceptado — 2026-03-02

## Contexto
El MVP requiere soportar PDF con texto (no escaneado). Se necesita una librería
que extraiga texto página por página, sea rápida y tenga wheel precompilado para
Python 3.13 en Linux (Kali/Ubuntu) y Windows.

Restricciones:
- Sin red, 100 % offline.
- Sin OCR (scope fuera del MVP).
- Complejidad máxima CC <= 4 por función.
- El adapter debe ser intercambiable mediante el puerto `BookParser`.

## Decisión
**Usar PyMuPDF (import fitz, versión 1.27.1).**

- Wheel `cp310-abi3-manylinux_2_28_x86_64` disponible → instala en Python 3.13.
- API: `fitz.open(path)` → `doc[n].get_text("text")` por página.
- Extracción por páginas: granularidad de progreso fina (1 capítulo por página).
- Soporta Unicode (á, é, ñ…) con la fuente interna WinAnsiEncoding.
- Manejo de PDF sin texto: detección explícita → `DomainError` con mensaje claro.

## Alternativas consideradas

### A) pdfminer.six
- Pros: puro Python, sin compilado nativo.
- Contras: API más verbosa, más lenta, mantenimiento reducido en 2025-2026.
  No tiene wheel para Python 3.13 aún (requiere compilar).

### B) pypdf (antes PyPDF2)
- Pros: puro Python, licencia MIT.
- Contras: extracción de texto menos robusta para layouts complejos; sin wheel
  nativo. Suficiente para texto simple pero inferior a PyMuPDF en calidad.

### C) stdlib + regex sobre PDF crudo
- Pros: cero deps.
- Contras: PDF es binario complejo; parsear manualmente es frágil y arriesgado.

## Consecuencias

| Aspecto | Impacto |
|---|---|
| Dependencia nueva | `pymupdf` (~25 MB wheel) — añadir a `requirements.txt` |
| Rendimiento | Extracción en O(n páginas), sin cargar todo en RAM |
| Portabilidad | Wheels para Linux x86_64, Windows, macOS (arm64 + x86_64) |
| Seguridad | No ejecuta JS embebido; extracción de texto puro |
| PDF escaneado | Devuelve error claro; no hay OCR en MVP |
| Mantenimiento | PyMuPDF activo, releases frecuentes |

## Notas de implementación
- Módulo: `src/adapters/secondary/parsers/pdf_parser.py`
- `fitz` solo importado en ese archivo; domain y application lo tienen prohibido.
- `architecture_rules_test.py` verifica que `fitz`/`pymupdf` no aparezcan fuera
  del adapter.
- Fixture de test: PDF generado inline con `fitz` → base64 embebido en test →
  decodificado a `tmp_path/tiny.pdf` en runtime. No se guarda binario en repo.
