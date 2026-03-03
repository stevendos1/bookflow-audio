# Security Policy

## Supported Versions

Este proyecto sigue un flujo simple de soporte:

- `main`: rama soportada y activa.
- ramas antiguas o forks: sin soporte de seguridad garantizado.

## Scope

Este proceso aplica a vulnerabilidades relacionadas con:

- parseo de archivos (`.epub`, `.txt`, `.pdf`),
- ejecucion de motores TTS y subprocess,
- almacenamiento local y manejo de datos,
- configuracion CI/CD y supply chain del repositorio.

## Reporting Channel (GitHub)

Canal oficial de reporte: este mismo repositorio en GitHub.

1. No publiques detalles sensibles en un issue abierto.
2. Usa GitHub **Report a vulnerability** (Private vulnerability reporting).
3. Si no puedes usar ese flujo, abre un issue con el minimo detalle y pide canal privado.

## What to Include

Incluye como minimo:

- pasos para reproducir,
- comportamiento esperado vs actual,
- impacto potencial,
- version/rama/commit afectado,
- entorno (SO, version de Python, motor TTS),
- evidencia (logs, capturas, PoC minima sin datos sensibles).

## Response Times

Objetivo de respuesta:

- acuse de recibo inicial: entre 1 dia y 7 dias,
- triage inicial (severidad y alcance): entre 1 dia y 7 dias desde el reporte,
- actualizaciones de estado: periodicas en el mismo hilo de GitHub.

Los tiempos pueden variar por complejidad o falta de datos para reproducir.

## Responsible Disclosure

- No publiques exploit o detalles tecnicos antes de que exista mitigacion razonable.
- Da tiempo a validar y corregir antes de divulgacion publica.
- Cuando se cierre el caso, se documentara en GitHub (advisory/changelog segun aplique).

## Security Notes for Users

- El programa procesa archivos locales (`.epub`, `.txt`, `.pdf`).
- El motor `edge-tts` usa internet para sintetizar voz.
- Los motores `espeak` y `piper` son locales.
- El progreso se guarda en SQLite local (`~/.lector_libros_mvp.db`).
- Evita abrir libros de fuentes no confiables.
