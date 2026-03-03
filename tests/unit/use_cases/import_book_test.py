from pathlib import Path

from src.application.use_cases.import_book import ImportBook
from src.domain.models import Chapter
from tests.fakes.parser import FakeBookParser
from tests.fakes.repository import FakeBookRepository


def test_import_book_success():
    # Arrange
    fake_parser = FakeBookParser()
    fake_repo = FakeBookRepository()

    use_case = ImportBook(parser=fake_parser, repository=fake_repo)

    # Preparar el stub del parser
    file_path_str = "mi_libro.txt"
    file_path = Path(file_path_str)

    # Generamos un capítulo simulado
    # El use_case pasará un book_id aleatorio al parser, el parser idealmente
    # en el Fake usa el file_path para identificar qué devolver.
    # En FakeBookParser, la key es file_path.

    chapter_draft = Chapter(book_id="TEMP", idx=0, title="Capítulo 1")
    raw_text = "Hola mundo.\n\nEste es un texto largo que será procesado. " * 30

    fake_parser.given_chapters(file_path, [(chapter_draft, raw_text)])

    # Act
    book_id = use_case.handle(file_path_str)

    # Assert
    assert book_id is not None
    assert len(book_id) > 0

    # Verificar que el libro se guardó
    saved_book = fake_repo.get_book(book_id)
    assert saved_book is not None
    assert saved_book.id == book_id
    assert saved_book.title == "mi_libro.txt"

    # Verificar que los capítulos guardados corresponden
    saved_chapters = fake_repo.chapters.get(book_id)
    assert saved_chapters is not None
    assert len(saved_chapters) == 1
    assert saved_chapters[0] == chapter_draft

    # Verificar que los bloques se generaron y guardaron
    saved_blocks = fake_repo._blocks.get(book_id)
    assert saved_blocks is not None
    assert len(saved_blocks) > 0

    # Validar que todos los bloques tienen el book_id correcto
    # y los indices generados por chunk_text
    for idx, block in enumerate(saved_blocks):
        assert block.book_id == book_id
        assert block.chapter_idx == chapter_draft.idx
        assert block.block_idx == idx

    # Verificar progreso inicial
    progress = fake_repo.get_progress(book_id)
    assert progress is not None
    assert progress.book_id == book_id
    assert progress.chapter_idx == 0
    assert progress.block_idx == 0
    assert progress.offset == 0


def test_import_book_empty_file():
    # Arrange
    fake_parser = FakeBookParser()
    fake_repo = FakeBookRepository()
    use_case = ImportBook(parser=fake_parser, repository=fake_repo)

    fake_parser.given_chapters(Path("vacio.txt"), [])

    # Act
    book_id = use_case.handle("vacio.txt")

    # Assert
    assert book_id is not None

    saved_book = fake_repo.get_book(book_id)
    assert saved_book is not None

    # Chapters y Blocks vacíos
    assert fake_repo.chapters.get(book_id) == []
    assert fake_repo._blocks.get(book_id) == []

    progress = fake_repo.get_progress(book_id)
    assert progress is not None
    assert progress.chapter_idx == 0
    assert progress.block_idx == 0
