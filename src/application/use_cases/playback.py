from src.application.ports import BookRepository, TtsEngine
from src.domain.exceptions import DomainError
from src.domain.models import Progress

_DEFAULT_PREFETCH_WINDOW = 10
_MIN_PREFETCH_WINDOW = 1
_MAX_PREFETCH_WINDOW = 50


class PlaybackManager:
    """Orquestador de los casos de uso de reproducción de audiolibros."""

    def __init__(self, repo: BookRepository, tts: TtsEngine):
        self.repo = repo
        self.tts = tts
        self._prefetch_window = _DEFAULT_PREFETCH_WINDOW

    def play(self, book_id: str) -> None:
        """Inicia o reanuda la reproducción desde el progreso guardado."""
        book = self.repo.get_book(book_id)
        if not book:
            raise DomainError(f"Libro {book_id} no encontrado")

        progress = self.repo.get_progress(book_id)
        if not progress:
            progress = Progress(book_id=book_id, chapter_idx=0, block_idx=0)

        self._start_playback(book_id, progress.chapter_idx, progress.block_idx)

    def pause(self) -> None:
        """Pausa el TTS nativo de forma asíncrona."""
        self.tts.pause()

    def stop(self) -> None:
        self.tts.stop()

    def next_block(self, book_id: str) -> None:
        """Avanza al siguiente bloque guardando el progreso."""
        self.tts.pause()

        progress = self.repo.get_progress(book_id)
        if not progress:
            return

        blocks = self.repo.get_blocks(book_id, progress.chapter_idx)
        current_idx = progress.block_idx

        if current_idx + 1 < len(blocks):
            # Aún quedan bloques en este capítulo
            self._start_playback(book_id, progress.chapter_idx, current_idx + 1)
        else:
            # Fin del capítulo, intentar avanzar al próximo
            next_ch_idx = progress.chapter_idx + 1
            next_blocks = self.repo.get_blocks(book_id, next_ch_idx)
            if next_blocks:
                self._start_playback(book_id, next_ch_idx, 0)

    def prev_block(self, book_id: str) -> None:
        """Retrocede al bloque anterior o al final del capítulo previo."""
        self.tts.pause()

        progress = self.repo.get_progress(book_id)
        if not progress:
            return

        current_idx = progress.block_idx
        ch_idx = progress.chapter_idx

        if current_idx > 0:
            self._start_playback(book_id, ch_idx, current_idx - 1)
        else:
            self._go_to_prev_chapter(book_id, ch_idx)

    def _go_to_prev_chapter(self, book_id: str, current_chapter_idx: int) -> None:
        if current_chapter_idx > 0:
            prev_ch_idx = current_chapter_idx - 1
            prev_blocks = self.repo.get_blocks(book_id, prev_ch_idx)
            if prev_blocks:
                self._start_playback(book_id, prev_ch_idx, len(prev_blocks) - 1)
            else:
                self._start_playback(book_id, prev_ch_idx, 0)
        else:
            # Principio del libro, no hay previo
            self._start_playback(book_id, 0, 0)

    def jump_to_block(self, book_id: str, chapter_idx: int, block_idx: int) -> None:
        """Interrumpe lo actual y salta directamente a un bloque específico."""
        self.tts.pause()
        self._start_playback(book_id, chapter_idx, block_idx)

    def set_rate(self, rate: int) -> None:
        self.tts.set_rate(rate)

    def set_voice(self, voice_id: str) -> None:
        self.tts.set_voice(voice_id)

    def set_prefetch_window(self, size: int) -> None:
        self._prefetch_window = max(_MIN_PREFETCH_WINDOW, min(_MAX_PREFETCH_WINDOW, size))

    def get_prefetch_window(self) -> int:
        return self._prefetch_window

    def _start_playback(self, book_id: str, ch_idx: int, blk_idx: int) -> None:
        blocks = self.repo.get_blocks(book_id, ch_idx)
        if not blocks:
            return

        # Actualizando DB
        new_progress = Progress(book_id=book_id, chapter_idx=ch_idx, block_idx=blk_idx)
        self.repo.save_progress(new_progress)

        # Enviando texto a motor
        target_block = next((b for b in blocks if b.block_idx == blk_idx), None)
        if target_block:
            self.tts.speak(target_block.text)
            self._prefetch_blocks(book_id, ch_idx, blk_idx)

    def _prefetch_blocks(self, book_id: str, chapter_idx: int, block_idx: int) -> None:
        prefetch = getattr(self.tts, "prefetch", None)
        if not callable(prefetch):
            return
        texts = self._window_texts(book_id, chapter_idx, block_idx)
        if texts:
            prefetch(texts)

    def _window_texts(self, book_id: str, chapter_idx: int, block_idx: int) -> list[str]:
        blocks = self.repo.get_blocks(book_id, chapter_idx)
        if not blocks:
            return []
        look_back = min(4, self._prefetch_window - 1)
        start = max(0, block_idx - look_back)
        end = min(len(blocks), start + self._prefetch_window)
        start = max(0, end - self._prefetch_window)
        return [b.text for b in blocks[start:end]]
