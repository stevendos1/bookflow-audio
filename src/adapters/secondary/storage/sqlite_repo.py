import json
import sqlite3
from pathlib import Path

from src.application.ports import BookRepository
from src.domain.exceptions import DomainError
from src.domain.models import Block, Book, Chapter, Progress


class SqliteBookRepository(BookRepository):
    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self._setup_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=10.0,
            isolation_level=None,  # Mode autocommit management para usar transacciones explícitas
        )
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
        # Diccionario para filas
        conn.row_factory = sqlite3.Row
        return conn

    def _setup_db(self) -> None:
        schema_path = Path(__file__).parent / "schema_v1.sql"
        if not schema_path.exists():
            raise DomainError(f"Schema not found: {schema_path}")

        with self._get_connection() as conn:
            conn.executescript(schema_path.read_text("utf-8"))

    def save_book(self, book: Book, chapters: list[Chapter], blocks: list[Block]) -> None:
        with self._get_connection() as conn:
            with conn:  # Transacción atómica
                conn.execute(
                    "INSERT OR REPLACE INTO books (id, title, authors) VALUES (?, ?, ?)",
                    (book.id, book.title, json.dumps(book.authors)),
                )

                # Chapters
                conn.executemany(
                    "INSERT OR REPLACE INTO chapters (book_id, idx, title) VALUES (?, ?, ?)",
                    [(ch.book_id, ch.idx, ch.title) for ch in chapters],
                )

                # Blocks
                conn.executemany(
                    "INSERT OR REPLACE INTO blocks "
                    "(book_id, chapter_idx, block_idx, text_hash, content) "
                    "VALUES (?, ?, ?, ?, ?)",
                    [(b.book_id, b.chapter_idx, b.block_idx, b.text_hash, b.text) for b in blocks],
                )

    def get_book(self, book_id: str) -> Book | None:
        with self._get_connection() as conn:
            query = "SELECT id, title, authors FROM books WHERE id = ?"
            row = conn.execute(query, (book_id,)).fetchone()
            if not row:
                return None

            authors = json.loads(row["authors"]) if row["authors"] else []
            return Book(id=row["id"], title=row["title"], authors=authors)

    def list_books(self) -> list[Book]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT id, title, authors FROM books").fetchall()
            return [
                Book(
                    id=r["id"],
                    title=r["title"],
                    authors=json.loads(r["authors"]) if r["authors"] else [],
                )
                for r in rows
            ]

    def get_chapters(self, book_id: str) -> list[Chapter]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT book_id, idx, title FROM chapters WHERE book_id = ? ORDER BY idx",
                (book_id,),
            ).fetchall()
            return [Chapter(book_id=r["book_id"], idx=r["idx"], title=r["title"]) for r in rows]

    def get_blocks(self, book_id: str, chapter_idx: int) -> list[Block]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT book_id, chapter_idx, block_idx, text_hash, content "
                "FROM blocks WHERE book_id = ? AND chapter_idx = ? ORDER BY block_idx",
                (book_id, chapter_idx),
            ).fetchall()
            return [
                Block(
                    book_id=r["book_id"],
                    chapter_idx=r["chapter_idx"],
                    block_idx=r["block_idx"],
                    text_hash=r["text_hash"],
                    text=r["content"],
                )
                for r in rows
            ]

    def save_progress(self, progress: Progress) -> None:
        with self._get_connection() as conn:
            with conn:  # Transactorial
                conn.execute(
                    "INSERT OR REPLACE INTO progress "
                    "(book_id, chapter_idx, block_idx, offset) "
                    "VALUES (?, ?, ?, ?)",
                    (progress.book_id, progress.chapter_idx, progress.block_idx, progress.offset),
                )

    def get_progress(self, book_id: str) -> Progress | None:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT book_id, chapter_idx, block_idx, offset FROM progress WHERE book_id = ?",
                (book_id,),
            ).fetchone()

            if not row:
                return None

            return Progress(
                book_id=row["book_id"],
                chapter_idx=row["chapter_idx"],
                block_idx=row["block_idx"],
                offset=row["offset"],
            )
