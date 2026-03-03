"""Tests unitarios para ReaderApp — sin Qt, SQLite ni pyttsx3 reales."""

from pathlib import Path

import src.infrastructure.reader_app as reader_app_module
from src.domain.models import Chapter
from src.infrastructure.reader_app import BookStatus, ReaderApp
from tests.fakes.parser import FakeBookParser
from tests.fakes.repository import FakeBookRepository
from tests.fakes.tts import FakeTtsEngine

# ───────────────────────────── helpers ───────────────────────────── #


def _make_app():
    repo = FakeBookRepository()
    tts = FakeTtsEngine()
    parser = FakeBookParser()
    app = ReaderApp(_repo=repo, _tts=tts, _parser=parser)
    return app, repo, tts, parser


def _import_fake_book(app, parser, tmp_path: Path, content: str = "Texto de prueba.") -> str:
    fake_path = tmp_path / "book.txt"
    fake_path.write_text(content)
    ch = Chapter(book_id="dummy", idx=0, title="Capítulo 1")
    parser.given_chapters(fake_path, [(ch, content)])
    return app.import_file(str(fake_path))


# ──────────────────────────── init ───────────────────────────────── #


def test_tts_started_on_init():
    _, _, tts, _ = _make_app()
    assert tts.started


# ─────────────────────────── import ──────────────────────────────── #


def test_import_file_returns_non_empty_book_id(tmp_path: Path):
    app, _, _, parser = _make_app()
    book_id = _import_fake_book(app, parser, tmp_path)
    assert book_id


def test_import_file_persists_book(tmp_path: Path):
    app, repo, _, parser = _make_app()
    book_id = _import_fake_book(app, parser, tmp_path)
    assert repo.get_book(book_id) is not None


def test_import_file_sets_current_book(tmp_path: Path):
    app, _, _, parser = _make_app()
    book_id = _import_fake_book(app, parser, tmp_path)
    st = app.status()
    assert st is not None
    assert st.book_id == book_id


# ──────────────────────────── list ───────────────────────────────── #


def test_list_books_empty_initially():
    app, _, _, _ = _make_app()
    assert app.list_books() == []


def test_list_books_returns_id_and_title(tmp_path: Path):
    app, _, _, parser = _make_app()
    book_id = _import_fake_book(app, parser, tmp_path)
    books = app.list_books()
    assert len(books) == 1
    assert books[0][0] == book_id
    assert books[0][1] == "book.txt"


# ─────────────────────────── play ────────────────────────────────── #


def test_play_with_book_id_calls_tts(tmp_path: Path):
    app, _, tts, parser = _make_app()
    book_id = _import_fake_book(app, parser, tmp_path)
    app.play(book_id)
    assert len(tts.spoken) > 0


def test_play_without_args_uses_current_book(tmp_path: Path):
    app, _, tts, parser = _make_app()
    book_id = _import_fake_book(app, parser, tmp_path)
    app.play(book_id)
    spoken_after_first = len(tts.spoken)
    app.play()
    assert len(tts.spoken) > spoken_after_first


def test_play_without_current_book_does_not_crash():
    app, _, tts, _ = _make_app()
    app.play()
    assert len(tts.spoken) == 0


# ─────────────────────────── pause ───────────────────────────────── #


def test_pause_delegates_to_tts():
    app, _, tts, _ = _make_app()
    app.pause()
    assert tts.paused


# ─────────────────────────── rate / voice ────────────────────────── #


def test_set_rate_propagates_to_tts():
    app, _, tts, _ = _make_app()
    app.set_rate(200)
    assert tts.rate == 200


def test_set_prefetch_window_propagates_to_playback():
    app, _, _, _ = _make_app()
    app.set_prefetch_window(30)
    assert app.get_prefetch_window() == 30
    assert app._playback.get_prefetch_window() == 30  # type: ignore[attr-defined]


def test_list_voices_returns_non_empty_list():
    app, _, _, _ = _make_app()
    voices = app.list_voices()
    assert len(voices) >= 1
    assert isinstance(voices[0], tuple)


def test_set_voice_propagates_to_tts():
    app, _, tts, _ = _make_app()
    app.set_voice("voice2")
    assert tts.voice_id == "voice2"


def test_set_engine_keeps_last_rate(monkeypatch):
    class _NewFakeTts(FakeTtsEngine):
        pass

    app, _, _, _ = _make_app()
    app.set_rate(240)

    monkeypatch.setitem(reader_app_module._ENGINE_REGISTRY, "fake-new", ("fake", _NewFakeTts))
    app.set_engine("fake-new")

    assert isinstance(app._tts, _NewFakeTts)  # type: ignore[attr-defined]
    assert app._tts.rate == 240  # type: ignore[attr-defined]


def test_set_engine_keeps_last_prefetch_window(monkeypatch):
    class _NewFakeTts(FakeTtsEngine):
        pass

    app, _, _, _ = _make_app()
    app.set_prefetch_window(40)

    monkeypatch.setitem(reader_app_module._ENGINE_REGISTRY, "fake-new", ("fake", _NewFakeTts))
    app.set_engine("fake-new")

    assert app.get_prefetch_window() == 40
    assert app._playback.get_prefetch_window() == 40  # type: ignore[attr-defined]


# ─────────────────────────── status ──────────────────────────────── #


def test_status_none_without_any_play():
    app, _, _, _ = _make_app()
    assert app.status() is None


def test_status_returns_book_status_after_play(tmp_path: Path):
    app, _, _, parser = _make_app()
    book_id = _import_fake_book(app, parser, tmp_path)
    app.play(book_id)
    st = app.status()
    assert isinstance(st, BookStatus)
    assert st.book_id == book_id
    assert st.chapter_idx == 0
    assert st.block_idx == 0


# ─────────────────────────── shutdown ────────────────────────────── #


def test_shutdown_stops_tts():
    app, _, tts, _ = _make_app()
    app.shutdown()
    assert tts.stopped
