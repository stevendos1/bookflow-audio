from pathlib import Path

from src.adapters.secondary.storage.sqlite_repo import SqliteBookRepository
from src.domain.models import Block, Book, Chapter, Progress


def test_sqlite_repository_full_flow(tmp_path: Path):
    db_file = tmp_path / "test.db"
    repo = SqliteBookRepository(db_file)

    # 1. Preparar datos
    book = Book(id="b1", title="Libro Prueba", authors=["Autor A", "Autor B"])
    ch1 = Chapter(book_id="b1", idx=0, title="Capítulo 1")
    ch2 = Chapter(book_id="b1", idx=1, title="Capítulo 2")

    blk1 = Block(book_id="b1", chapter_idx=0, block_idx=0, text_hash="hash1", text="Texto 1")
    blk2 = Block(book_id="b1", chapter_idx=1, block_idx=0, text_hash="hash2", text="Texto 2")

    # 2. Guardar libro
    repo.save_book(book, [ch1, ch2], [blk1, blk2])

    # 3. Listar libros
    books = repo.list_books()
    assert len(books) == 1
    assert books[0].id == "b1"
    assert books[0].title == "Libro Prueba"
    assert books[0].authors == ["Autor A", "Autor B"]

    # 4. Obtener libro
    b_get = repo.get_book("b1")
    assert b_get is not None
    assert b_get.id == "b1"

    # 5. Progreso inexistente
    assert repo.get_progress("b1") is None

    # 6. Guardar y obtener progreso
    prog = Progress(book_id="b1", chapter_idx=1, block_idx=0, offset=42)
    repo.save_progress(prog)

    p_get = repo.get_progress("b1")
    assert p_get is not None
    assert p_get.book_id == "b1"
    assert p_get.chapter_idx == 1
    assert p_get.block_idx == 0
    assert p_get.offset == 42


def test_sqlite_repository_missing_book_returns_none(tmp_path: Path):
    repo = SqliteBookRepository(tmp_path / "empty.db")
    assert repo.get_book("does_not_exist") is None
