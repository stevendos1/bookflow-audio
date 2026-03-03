# docs/performance.md
# Performance - Audiobook Local

## 1) Objetivo
- Lectura fluida sin "silencios" entre bloques.
- Importación razonable en libros largos.
- Bajo consumo mientras trabajas.

## 2) Reglas
- No cargar todo el libro a memoria si no es necesario.
- Procesar por capítulos/páginas/bloques.
- IO y TTS fuera del hilo principal.

## 3) Chunking
- Bloques de 500-1200 chars (configurable).
- Cortar por puntuación para pausas naturales.
- Pre-cargar el siguiente bloque en background.

## 4) Pipeline recomendado
1) Obtener texto (parser) -> 2) normalizar -> 3) chunking -> 4) speak -> 5) play
- Cada etapa debe poder:
  - fallar con error claro
  - reintentar si procede
  - ser testeable aislada

## 5) Cache de audio (opcional)
- Cache por bloque:
  - key: book_id + chapter_idx + block_idx + text_hash + voice + rate
- Beneficio:
  - reanudar rápido
  - menos CPU
- Costo:
  - almacenamiento local
- Política:
  - LRU o limpieza por tamaño total.

## 6) SQLite
- Indices:
  - books(path)
  - progress(book_id)
  - blocks(book_id, chapter_idx, block_idx)
- Transacciones para writes batched.
- Evitar commits por cada pequeño write si hay bursts.
- Guardado de progreso:
  - en cambio de bloque
  - y cada N segundos (N=10-30 sugerido)

## 7) PDF
- Extracción por páginas.
- Heurísticas de limpieza con costo lineal O(n).
- Evitar reconstrucciones O(n^2) concatenando strings:
  - usar listas y "".join()

## 8) Concurrencia
- Un worker para parsing/importación.
- Un worker para TTS/audio.
- Cola de mensajes:
  - Play/Pause/Next/Prev como eventos
- Cancelación:
  - al pausar o cambiar de bloque, cancelar generación del bloque anterior.

## 9) Métricas locales (solo debug)
- Tiempo de import por capítulo.
- Latencia de "speak" por bloque.
- Bloques en cola (backpressure).

## 10) Perfilado
- cProfile para hotspots.
- Medir con fixtures grandes.
- Optimizar solo si duele (YAGNI).