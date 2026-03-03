# docs/security.md
# Security - Offline Reader (Local First)

## 1) Principios
- Local-first: sin red por defecto.
- Menor privilegio: leer archivos solo cuando el usuario los importa.
- No ejecutar nada del contenido (EPUB/PDF pueden contener cosas raras).
- Sanitización y defensas contra path traversal y shell injection.

## 2) Amenazas principales
- Archivos maliciosos:
  - EPUB con HTML/scripts
  - PDF con contenido extraño
- Rutas manipuladas:
  - symlinks, traversal, rutas UNC
- Inyección por shell:
  - si se usa piper/ffmpeg via subprocess

## 3) Reglas para manejo de archivos
- Resolver rutas a absolutas y normalizadas.
- Validar existencia y permisos antes de abrir.
- No seguir symlinks si no es necesario (opcional configurable).
- No leer fuera del path indicado por el usuario (cuando aplica).

## 4) EPUB / HTML
- Extraer solo texto.
- Ignorar scripts, estilos y tags peligrosos.
- No renderizar HTML sin sanitizar.
- Si se muestra texto en UI, escapar contenido.

## 5) PDF
- Usar librería segura y conocida (PyMuPDF/MuPDF).
- No ejecutar JS embebido (no aplica a extracción normal).
- Evitar OCR en MVP (reduce superficie y complejidad).

## 6) Subprocess (si se usa piper)
- Nunca construir comandos concatenando strings con input del usuario.
- Usar lista de args en subprocess:
  - subprocess.run([bin, "--model", model, ...], check=True)
- Validar rutas de binarios y modelos.
- No permitir flags arbitrarios del usuario sin whitelist.

## 7) Persistencia
- SQLite con parámetros siempre.
- Migraciones controladas.
- No guardar texto completo del libro en logs.
- Si guardas caches, usar directorio dedicado con permisos correctos.

## 8) Privacidad
- No enviar telemetría.
- Logs locales: sin contenido del libro.
- Opcional:
  - configuración para desactivar logs o bajar nivel.

## 9) Dependencias
- Minimizar dependencias.
- Pin de versiones razonable.
- Revisar licencias y mantenimiento.
- Evitar librerías abandonadas para parsing/tts.

## 10) Política de errores
- Mensajes al usuario sin stacktrace.
- Guardar stacktrace solo en logs debug.
- Incluir contexto mínimo: ids y rutas, no contenido.

## 11) Checklist por feature
- ¿Se abrió un archivo? ¿validación de ruta y manejo de encoding?
- ¿Se ejecutó subprocess? ¿args seguros?
- ¿Se guardó algo? ¿parametrizado? ¿sin datos sensibles?
- ¿Se logueó? ¿sin texto del libro?