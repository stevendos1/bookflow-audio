from pathlib import Path

from src.domain.models import Chapter


class FakeBookParser:
    def __init__(self) -> None:
        self.fake_chapters: dict[Path, list[tuple[Chapter, str]]] = {}

    def given_chapters(self, file_path: Path, chapters: list[tuple[Chapter, str]]) -> None:
        self.fake_chapters[file_path] = chapters

    def parse_to_chapters(self, file_path: Path, book_id: str) -> list[tuple[Chapter, str]]:
        return self.fake_chapters.get(file_path, [])
