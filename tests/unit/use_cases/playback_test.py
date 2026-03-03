import pytest

from src.application.use_cases.playback import PlaybackManager
from src.domain.exceptions import DomainError
from src.domain.models import Block, Book, Chapter, Progress
from tests.fakes.repository import FakeBookRepository
from tests.fakes.tts import FakeTtsEngine


@pytest.fixture
def repo_and_tts() -> tuple[FakeBookRepository, FakeTtsEngine]:
    repo = FakeBookRepository()
    tts = FakeTtsEngine()

    # Datos semilla
    book = Book(id="b1", title="Sample")
    ch1 = Chapter(book_id="b1", idx=0, title="Cap 1")
    ch2 = Chapter(book_id="b1", idx=1, title="Cap 2")

    blk1 = Block(book_id="b1", chapter_idx=0, block_idx=0, text_hash="h1", text="uno")
    blk2 = Block(book_id="b1", chapter_idx=0, block_idx=1, text_hash="h2", text="dos")
    blk3 = Block(book_id="b1", chapter_idx=1, block_idx=0, text_hash="h3", text="tres")

    repo.save_book(book, [ch1, ch2], [blk1, blk2, blk3])

    return repo, tts


def test_playback_play_starts_at_zero_if_no_progress(repo_and_tts):
    repo, tts = repo_and_tts
    pm = PlaybackManager(repo, tts)

    pm.play("b1")

    # Debe guardar (0,0)
    prog = repo.get_progress("b1")
    assert prog is not None
    assert prog.chapter_idx == 0
    assert prog.block_idx == 0

    # Debe hablar bloque 0, 0
    assert tts.spoken == ["uno"]


def test_playback_play_resumes_from_saved_progress(repo_and_tts):
    repo, tts = repo_and_tts
    pm = PlaybackManager(repo, tts)

    repo.save_progress(Progress(book_id="b1", chapter_idx=1, block_idx=0))
    pm.play("b1")

    assert tts.spoken == ["tres"]


def test_playback_play_fails_on_missing_book(repo_and_tts):
    repo, tts = repo_and_tts
    pm = PlaybackManager(repo, tts)

    with pytest.raises(DomainError):
        pm.play("missing")


def test_playback_next_block_advances(repo_and_tts):
    repo, tts = repo_and_tts
    pm = PlaybackManager(repo, tts)

    pm.play("b1")  # Lee "uno", (0,0)
    assert tts.spoken == ["uno"]

    pm.next_block("b1")  # Pausa, lee "dos", (0,1)
    assert tts.paused is True
    assert tts.spoken == ["uno", "dos"]

    prog = repo.get_progress("b1")
    assert prog.block_idx == 1

    pm.next_block("b1")  # Pausa, cambia a cap 1, lee "tres", (1,0)
    assert tts.spoken == ["uno", "dos", "tres"]

    prog = repo.get_progress("b1")
    assert prog.chapter_idx == 1
    assert prog.block_idx == 0


def test_playback_prev_block_rewinds(repo_and_tts):
    repo, tts = repo_and_tts
    pm = PlaybackManager(repo, tts)

    # Arrancar desde el último bloque
    repo.save_progress(Progress(book_id="b1", chapter_idx=1, block_idx=0))
    pm.play("b1")  # "tres"

    pm.prev_block("b1")  # Debe ir a cap 0, blk 1 ("dos")
    assert tts.paused is True
    assert tts.spoken == ["tres", "dos"]

    prog = repo.get_progress("b1")
    assert prog.chapter_idx == 0
    assert prog.block_idx == 1

    pm.prev_block("b1")  # Debe ir a cap 0, blk 0 ("uno")
    assert tts.spoken == ["tres", "dos", "uno"]


def test_playback_set_configuration(repo_and_tts):
    repo, tts = repo_and_tts
    pm = PlaybackManager(repo, tts)

    pm.set_rate(250)
    pm.set_voice("voz_x")

    assert tts.rate == 250
    assert tts.voice_id == "voz_x"


def test_playback_prefetches_block_window(repo_and_tts):
    repo, tts = repo_and_tts
    pm = PlaybackManager(repo, tts)

    pm.play("b1")

    assert len(tts.prefetched) == 1
    assert tts.prefetched[0] == ["uno", "dos"]


def test_playback_prefetch_window_is_configurable(repo_and_tts):
    repo, tts = repo_and_tts
    pm = PlaybackManager(repo, tts)
    pm.set_prefetch_window(1)

    pm.play("b1")

    assert tts.prefetched[0] == ["uno"]
