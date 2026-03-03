import sys
from pathlib import Path

from src.adapters.primary.cli import CliApp
from src.adapters.secondary.parsers.epub_parser import EpubParser
from src.adapters.secondary.parsers.multi_format_parser import MultiFormatParser
from src.adapters.secondary.parsers.pdf_parser import PdfParser
from src.adapters.secondary.parsers.txt_parser import TxtParser
from src.adapters.secondary.storage.sqlite_repo import SqliteBookRepository
from src.adapters.secondary.tts.espeak_engine import EspeakEngine
from src.application.use_cases.import_book import ImportBook
from src.application.use_cases.playback import PlaybackManager


def get_default_db_path() -> Path:
    return Path.home() / ".lector_libros_mvp.db"


def main(args: list[str]) -> int:
    # 1. Adaptadores Secundarios
    db_path = get_default_db_path()
    repo = SqliteBookRepository(db_path)
    parser = MultiFormatParser(
        {
            ".txt": TxtParser(),
            ".epub": EpubParser(),
            ".pdf": PdfParser(),
        }
    )
    tts = EspeakEngine()

    tts.start()

    # 2. Casos de Uso (Application)
    import_book_uc = ImportBook(parser=parser, repository=repo)
    playback_manager = PlaybackManager(repo=repo, tts=tts)

    # 3. Adaptador Primario (CLI)
    cli_app = CliApp(
        repo=repo,
        import_book_uc=import_book_uc,
        playback_manager=playback_manager,
    )

    try:
        return cli_app.run(args)
    finally:
        tts.stop()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
