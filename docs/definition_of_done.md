# docs/definition_of_done.md
# Definition of Done (DoD)

## Feature lista cuando:
- Tiene tests (unit o integración) que cubren el comportamiento clave.
- No viola arquitectura hexagonal:
  - domain aislado,
  - application sin infraestructura,
  - adapters implementan puertos.
- Cumple presupuestos:
  - función <= 100 líneas,
  - complejidad ciclomática <= 4 (objetivo 2),
  - sin algoritmos peores que O(n^2) sin justificación.
- Manejo de errores:
  - mensajes accionables,
  - logs sin contenido del libro.
- Documentación actualizada:
  - mvp.md si cambia UX o comandos,
  - ADR si cambia arquitectura/decisión relevante.
- Formato y lint pasan (ruff/black).
- No rompe compatibilidad Windows + Ubuntu/Kali (si aplica).

## Checklist rápida
- [ ] Tests OK
- [ ] Lint/format OK
- [ ] Logs OK
- [ ] Docs OK
- [ ] Arquitectura OK
- [ ] UX OK (play/pause/next)