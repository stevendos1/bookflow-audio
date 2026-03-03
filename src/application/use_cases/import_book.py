import uuid
from pathlib import Path

from src.application.ports import BookParser, BookRepository
from src.domain.models import Block, Book, Chapter, Progress
from src.domain.text import chunk_text, normalize_text


class ImportBook:
    def __init__(self, parser: BookParser, repository: BookRepository) -> None:
        self._parser = parser
        self._repository = repository

    def handle(self, file_path: str) -> str:
        """
        Importa un libro desde su ruta.
        Parsea los capítulos, normaliza el texto, lo divide en bloques y guarda el progreso inicial.
        Retorna el ID del libro generado.
        """
        path = Path(file_path)
        book_id = uuid.uuid4().hex

        # 1. Parsear archivo usando el puerto correspondiente
        raw_chapters: list[tuple[Chapter, str]] = self._parser.parse_to_chapters(path, book_id)

        chapters: list[Chapter] = []
        all_blocks: list[Block] = []

        # 2. Iterar capítulos: extraer, normalizar y chunkear
        for chapter, raw_text in raw_chapters:
            chapters.append(chapter)

            normalized = normalize_text(raw_text)
            blocks = chunk_text(normalized, book_id=book_id, chapter_idx=chapter.idx)

            all_blocks.extend(blocks)

        # 3. Guardar el libro y sus partes de forma atómica (lógica en el adapter)
        # Por ahora usamos el nombre del archivo como título rudimentario
        book = Book(id=book_id, title=path.name)
        self._repository.save_book(book, chapters, all_blocks)

        # 4. Establecer progreso inicial
        initial_progress = Progress(book_id=book_id, chapter_idx=0, block_idx=0, offset=0)
        self._repository.save_progress(initial_progress)

        return book_id
