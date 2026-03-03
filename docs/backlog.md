# docs/backlog.md
# Backlog (orden sugerido) - Audiolibro local

## Fase 0: Base del proyecto
1. Estructura hexagonal (carpetas + reglas) + tooling (ruff/black/tests).
2. Modelo de dominio: Book/Chapter/Block/Progress.
3. Normalización + chunking con tests unitarios.

## Fase 1: Persistencia
4. Puerto BookRepository + fake in-memory (tests).
5. Adapter sqlite (schema + migración v1).
6. Use case: guardar y cargar progreso.

## Fase 2: Importación
7. Puerto BookParser.
8. Adapter TXT parser (encoding robusto).
9. Adapter EPUB parser (ebooklib + bs4).
10. Adapter PDF parser (PyMuPDF) para texto.
11. Use case ImportBook (genera bloques o indexa).

## Fase 3: Reproducción (MVP)
12. Puerto TtsEngine (contrato estable).
13. Adapter TTS: pyttsx3 (Windows + Linux).
14. Motor de reproducción:
    - cola de bloques,
    - pre-carga del siguiente bloque,
    - eventos play/pause/next/prev,
    - persistencia de progreso.
15. CLI primary adapter con comandos del MVP.
16. Logs + manejo de errores.

## Fase 4: Calidad + empaquetado
17. Tests integración: sqlite + fixtures pequeños.
18. PyInstaller Windows.
19. Linux: script + instrucciones (fase 1), AppImage (fase 2).

## Fase 5 (mejora de voz)
20. Adapter TTS: Piper (opcional) + selección en config.
21. Cache de audio por bloque (opcional).

## Fase 6 (post-MVP)
22. System tray (pystray).
23. Hotkeys globales (según entorno).
24. OCR (Tesseract) como adapter separado para PDF escaneado.

## Bugs / deuda técnica
- Mantener ADRs por decisiones importantes.
- Reducir complejidad y duplicación.