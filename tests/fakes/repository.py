from src.domain.models import Block, Book, Chapter, Progress


class FakeBookRepository:
    def __init__(self) -> None:
        self.books: dict[str, Book] = {}
        self.chapters: dict[str, list[Chapter]] = {}
        self._blocks: dict[str, list[Block]] = {}
        self.progresses: dict[str, Progress] = {}

    def save_book(self, book: Book, chapters: list[Chapter], blocks: list[Block]) -> None:
        self.books[book.id] = book
        self.chapters[book.id] = chapters
        self._blocks[book.id] = blocks

    def get_book(self, book_id: str) -> Book | None:
        return self.books.get(book_id)

    def list_books(self) -> list[Book]:
        return list(self.books.values())

    def save_progress(self, progress: Progress) -> None:
        self.progresses[progress.book_id] = progress

    def get_progress(self, book_id: str) -> Progress | None:
        return self.progresses.get(book_id)

    def get_chapters(self, book_id: str) -> list[Chapter]:
        return self.chapters.get(book_id, [])

    def get_blocks(self, book_id: str, chapter_idx: int) -> list[Block]:
        all_blocks = self._blocks.get(book_id, [])
        return [b for b in all_blocks if b.chapter_idx == chapter_idx]
