from pathlib import Path

from src.application.ports import BookParser, BookRepository, Clock, TtsEngine
from src.domain.models import Block, Book, Chapter, Progress
from tests.fakes.clock import FakeClock
from tests.fakes.parser import FakeBookParser
from tests.fakes.repository import FakeBookRepository
from tests.fakes.tts import FakeTtsEngine


def test_fake_repository_implements_protocol():
    repo: BookRepository = FakeBookRepository()

    book = Book(id="1", title="Test")
    chapter = Chapter(book_id="1", idx=0, title="Ch1")
    block = Block(book_id="1", chapter_idx=0, block_idx=0, text_hash="hash", text="text")
    progress = Progress(book_id="1", chapter_idx=0, block_idx=0)

    repo.save_book(book, [chapter], [block])
    repo.save_progress(progress)

    assert repo.get_book("1") == book
    assert repo.get_progress("1") == progress
    assert len(repo.list_books()) == 1


def test_fake_parser_implements_protocol():
    parser: BookParser = FakeBookParser()
    fake_path = Path("dummy.txt")

    # El fake permite inyectar el setup que esperamos de parse_to_chapters
    chapter = Chapter(book_id="1", idx=0, title="Ch1")
    parser.given_chapters(fake_path, [(chapter, "raw text")])  # type: ignore

    result = parser.parse_to_chapters(fake_path, "1")
    assert len(result) == 1
    assert result[0][0] == chapter
    assert result[0][1] == "raw text"


def test_fake_tts_implements_protocol():
    tts: TtsEngine = FakeTtsEngine()
    tts.start()
    tts.speak("hola")
    tts.stop()

    # el tipado asegura que los fake devuelven / exponen atributos útiles
    assert tts.started  # type: ignore
    assert tts.stopped  # type: ignore
    assert tts.spoken == ["hola"]  # type: ignore


def test_fake_clock_implements_protocol():
    clock: Clock = FakeClock(initial_time=100.0)
    assert clock.now() == 100.0

    clock.advance(5.0)  # type: ignore
    assert clock.now() == 105.0
