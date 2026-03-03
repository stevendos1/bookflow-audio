import sys
from io import StringIO
from pathlib import Path

import pytest

from src.adapters.primary.cli import CliApp
from src.adapters.secondary.parsers.txt_parser import TxtParser
from src.adapters.secondary.storage.sqlite_repo import SqliteBookRepository
from src.adapters.secondary.tts.pyttsx3_engine import Pyttsx3Engine
from src.application.use_cases.import_book import ImportBook
from src.application.use_cases.playback import PlaybackManager


@pytest.fixture
def run_cli_in_temp_db(tmp_path: Path):
    db_path = tmp_path / "test.db"

    repo = SqliteBookRepository(db_path)
    parser = TxtParser()
    tts = Pyttsx3Engine()
    tts.start()

    import_book_uc = ImportBook(parser=parser, repository=repo)
    playback_manager = PlaybackManager(repo=repo, tts=tts)

    cli = CliApp(repo, import_book_uc, playback_manager)

    def _run(args: list[str]) -> str:
        # Redirigir stdout para capturar la salida
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            exit_code = cli.run(args)
            assert exit_code == 0
            return sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

    yield _run

    tts.stop()


def test_e2e_import_and_list_flow(run_cli_in_temp_db):
    fixture_path = Path("tests/fixtures/tiny.txt")
    assert fixture_path.exists()

    # 1. Importar el fixture de prueba
    out_import = run_cli_in_temp_db(["import", str(fixture_path)])
    assert "Libro importado con ID:" in out_import

    book_id = out_import.strip().split()[-1]

    # 2. Listar la base de datos
    out_list = run_cli_in_temp_db(["list"])
    assert book_id in out_list
    assert "tiny.txt" in out_list  # ImportBook asigna el nombre del archivo al libro por defecto


def test_e2e_play_pause(run_cli_in_temp_db):
    fixture_path = Path("tests/fixtures/tiny.txt")
    out_import = run_cli_in_temp_db(["import", str(fixture_path)])
    book_id = out_import.strip().split()[-1]

    out_play = run_cli_in_temp_db(["play", book_id])
    assert f"Reproduciendo libro {book_id}" in out_play

    out_pause = run_cli_in_temp_db(["pause"])
    assert "Reproducción pausada." in out_pause
