"""Facade que orquesta los casos de uso para clientes no-CLI (GUI, etc.)."""

from dataclasses import dataclass
from pathlib import Path

from src.adapters.secondary.parsers.epub_parser import EpubParser
from src.adapters.secondary.parsers.multi_format_parser import MultiFormatParser
from src.adapters.secondary.parsers.pdf_parser import PdfParser
from src.adapters.secondary.parsers.txt_parser import TxtParser
from src.adapters.secondary.storage.sqlite_repo import SqliteBookRepository
from src.adapters.secondary.tts.edge_tts_engine import EdgeTtsEngine
from src.adapters.secondary.tts.espeak_engine import EspeakEngine
from src.adapters.secondary.tts.piper_engine import PiperEngine
from src.application.ports import BookParser, BookRepository, TtsEngine
from src.application.use_cases.import_book import ImportBook
from src.application.use_cases.playback import PlaybackManager

# Registro de motores disponibles: id → (label, factory)
_ENGINE_REGISTRY: dict[str, tuple[str, type]] = {
    "espeak": ("espeak (local, robótico)", EspeakEngine),
    "edge-tts": (EdgeTtsEngine.ENGINE_LABEL, EdgeTtsEngine),
    "piper": (PiperEngine.ENGINE_LABEL, PiperEngine),
}


def available_engines() -> list[tuple[str, str]]:
    """Retorna [(engine_id, label)] de los motores disponibles en este sistema."""
    from src.adapters.secondary.tts.piper_engine import PiperEngine as _Piper

    engines = [
        ("espeak", "espeak (local, robótico)"),
        ("edge-tts", EdgeTtsEngine.ENGINE_LABEL),
    ]
    if _Piper.is_available():
        engines.append(("piper", PiperEngine.ENGINE_LABEL))
    return engines


def _set_default_voice(tts: TtsEngine) -> None:
    """Establece español latinoamericano como voz por defecto si está disponible."""
    # espeak 1.48 → "es-la"; espeak-ng → "roa/es-419"
    es_la = next(
        (v_id for v_id, _ in tts.list_voices() if "es-la" in v_id or "es-419" in v_id),
        None,
    )
    if es_la:
        tts.set_voice(es_la)


@dataclass(frozen=True)
class BookStatus:
    book_id: str
    title: str
    chapter_idx: int
    block_idx: int


class ReaderApp:
    """Facade de alto nivel para importar y reproducir libros.

    Acepta dependencias opcionales para facilitar las pruebas unitarias sin
    levantar SQLite, espeak ni parsers reales.
    """

    def __init__(
        self,
        _repo: BookRepository | None = None,
        _tts: TtsEngine | None = None,
        _parser: BookParser | None = None,
    ) -> None:
        if _repo is None:
            _repo = SqliteBookRepository(Path.home() / ".lector_libros_mvp.db")
        if _tts is None:
            _tts = EdgeTtsEngine()
        if _parser is None:
            _parser = MultiFormatParser(
                {
                    ".txt": TxtParser(),
                    ".epub": EpubParser(),
                    ".pdf": PdfParser(),
                }
            )
        self._repo = _repo
        self._tts = _tts
        self._import_book = ImportBook(parser=_parser, repository=_repo)
        self._playback = PlaybackManager(repo=_repo, tts=_tts)
        self._current_book_id: str | None = self._restore_last_book(_repo)
        self._playing = False
        self._rate = 150
        self._prefetch_window = 10
        _tts.start()
        _set_default_voice(_tts)
        self._playback.set_rate(self._rate)
        self._playback.set_prefetch_window(self._prefetch_window)

    @staticmethod
    def _restore_last_book(repo: BookRepository) -> str | None:
        """Devuelve el ID del último libro con progreso guardado, o None."""
        for book in repo.list_books():
            if repo.get_progress(book.id):
                return book.id
        return None

    def import_file(self, path: str) -> str:
        """Importa un libro y lo establece como libro actual. Retorna su ID."""
        book_id = self._import_book.handle(path)
        self._current_book_id = book_id
        return book_id

    def list_books(self) -> list[tuple[str, str]]:
        """Retorna lista de (book_id, title) de todos los libros importados."""
        return [(b.id, b.title) for b in self._repo.list_books()]

    def play(self, book_id: str | None = None) -> None:
        """Inicia la reproducción. Si se omite book_id, usa el libro actual."""
        if book_id is not None:
            self._current_book_id = book_id
        if self._current_book_id is None:
            return
        self._playing = True
        self._playback.play(self._current_book_id)

    def pause(self) -> None:
        self._playing = False
        self._playback.pause()

    def next(self) -> None:
        if self._current_book_id:
            self._playback.next_block(self._current_book_id)

    def prev(self) -> None:
        if self._current_book_id:
            self._playback.prev_block(self._current_book_id)

    def set_rate(self, rate: int) -> None:
        self._rate = rate
        self._playback.set_rate(rate)

    def set_prefetch_window(self, size: int) -> None:
        self._prefetch_window = size
        self._playback.set_prefetch_window(size)

    def get_prefetch_window(self) -> int:
        return self._prefetch_window

    def list_voices(self) -> list[tuple[str, str]]:
        """Retorna lista de (voice_id, voice_name) disponibles en el motor TTS."""
        return self._tts.list_voices()

    def set_voice(self, voice_id: str) -> None:
        self._playback.set_voice(voice_id)

    def get_chapter_blocks(self) -> list[tuple[int, int, str]]:
        """Retorna [(chapter_idx, block_idx, text)] del capítulo en progreso."""
        if self._current_book_id is None:
            return []
        progress = self._repo.get_progress(self._current_book_id)
        if progress is None:
            return []
        blocks = self._repo.get_blocks(self._current_book_id, progress.chapter_idx)
        return [(b.chapter_idx, b.block_idx, b.text) for b in blocks]

    def jump(self, chapter_idx: int, block_idx: int) -> None:
        """Salta a un bloque específico del libro actual e inicia la reproducción."""
        if self._current_book_id is None:
            return
        self._playback.jump_to_block(self._current_book_id, chapter_idx, block_idx)

    def get_chapters(self) -> list[tuple[int, str]]:
        """Retorna [(chapter_idx, title)] del libro actual."""
        if self._current_book_id is None:
            return []
        return [(c.idx, c.title) for c in self._repo.get_chapters(self._current_book_id)]

    def jump_to_chapter(self, chapter_idx: int) -> None:
        """Salta al primer bloque del capítulo indicado."""
        if self._current_book_id is None:
            return
        self._playback.jump_to_block(self._current_book_id, chapter_idx, 0)

    def restart(self) -> None:
        """Reinicia desde el inicio del libro (capítulo 0, bloque 0)."""
        if self._current_book_id is None:
            return
        self._playback.jump_to_block(self._current_book_id, 0, 0)

    def status(self) -> BookStatus | None:
        """Estado de progreso del libro actual, o None si no hay ninguno activo."""
        if self._current_book_id is None:
            return None
        book = self._repo.get_book(self._current_book_id)
        progress = self._repo.get_progress(self._current_book_id)
        if book is None or progress is None:
            return None
        return BookStatus(
            book_id=book.id,
            title=book.title,
            chapter_idx=progress.chapter_idx,
            block_idx=progress.block_idx,
        )

    def is_playing(self) -> bool:
        """True si el usuario ha iniciado la reproducción y no ha pausado."""
        return self._playing

    def is_tts_speaking(self) -> bool:
        """True si el motor TTS está sintetizando o reproduciendo audio."""
        return self._tts.is_speaking()

    def set_engine(self, engine_id: str) -> None:
        """Cambia el motor TTS en caliente. engine_id: 'espeak', 'edge-tts', 'piper'."""
        if engine_id not in _ENGINE_REGISTRY:
            return
        self._playing = False
        self._tts.stop()
        _, factory = _ENGINE_REGISTRY[engine_id]
        self._tts = factory()  # type: ignore[call-arg]
        self._playback = PlaybackManager(repo=self._repo, tts=self._tts)
        self._tts.start()
        self._playback.set_rate(self._rate)
        self._playback.set_prefetch_window(self._prefetch_window)

    def shutdown(self) -> None:
        """Detiene el motor TTS. Llamar al cerrar la aplicación."""
        self._tts.stop()
