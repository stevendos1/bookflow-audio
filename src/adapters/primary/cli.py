import argparse
import sys

from src.application.ports import BookRepository
from src.application.use_cases.import_book import ImportBook
from src.application.use_cases.playback import PlaybackManager


class CliApp:
    def __init__(
        self,
        repo: BookRepository,
        import_book_uc: ImportBook,
        playback_manager: PlaybackManager,
    ) -> None:
        self.repo = repo
        self.import_book_uc = import_book_uc
        self.playback_manager = playback_manager

    def create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description="Lector de Libros CLI")
        subparsers = parser.add_subparsers(dest="command", required=True)

        idx_import = subparsers.add_parser("import", help="Importar un libro")
        idx_import.add_argument("path", type=str, help="Ruta al archivo (TXT, EPUB, PDF)")

        subparsers.add_parser("list", help="Listar libros importados")

        play = subparsers.add_parser("play", help="Reproducir un libro")
        play.add_argument("book_id", type=str, help="ID del libro")

        subparsers.add_parser("pause", help="Pausar la reproducción")

        nxt = subparsers.add_parser("next", help="Avanzar al siguiente bloque")
        nxt.add_argument("book_id", type=str, help="ID del libro")

        prev = subparsers.add_parser("prev", help="Retroceder al bloque anterior")
        prev.add_argument("book_id", type=str, help="ID del libro")

        rate = subparsers.add_parser("rate", help="Configurar velocidad de TTS")
        rate.add_argument("speed", type=int, help="Velocidad (p.ej. 150)")

        voice = subparsers.add_parser("voice", help="Comandos de Voz")
        voice_subs = voice.add_subparsers(dest="voice_cmd", required=True)
        voice_subs.add_parser("list", help="Listar voces disponibles")
        vset = voice_subs.add_parser("set", help="Establecer una voz por defecto")
        vset.add_argument("voice_id", type=str, help="ID de la voz a usar")

        subparsers.add_parser("status", help="Mostrar progreso de todos los libros")

        return parser

    def run(self, args: list[str]) -> int:
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)
        cmd = parsed_args.command

        handlers = {
            "import": self._cmd_import,
            "list": self._cmd_list,
            "play": self._cmd_play,
            "pause": self._cmd_pause,
            "next": self._cmd_next,
            "prev": self._cmd_prev,
            "rate": self._cmd_rate,
            "voice": self._cmd_voice,
            "status": self._cmd_status,
        }

        try:
            handler = handlers.get(cmd)
            if handler:
                handler(parsed_args)
            return 0
        except Exception as e:
            print(f"Error ({type(e).__name__}): {e}", file=sys.stderr)
            return 1

    def _cmd_import(self, args: argparse.Namespace) -> None:
        book_id = self.import_book_uc.handle(args.path)
        print(f"Libro importado con ID: {book_id}")

    def _cmd_list(self, args: argparse.Namespace) -> None:
        books = self.repo.list_books()
        if not books:
            print("No hay libros disponibles.")
            return
        for b in books:
            authors = ", ".join(b.authors) if b.authors else "Desconocido"
            print(f"[{b.id}] {b.title} - {authors}")

    def _cmd_play(self, args: argparse.Namespace) -> None:
        self.playback_manager.play(args.book_id)
        print(f"Reproduciendo libro {args.book_id}")

    def _cmd_pause(self, args: argparse.Namespace) -> None:
        self.playback_manager.pause()
        print("Reproducción pausada.")

    def _cmd_next(self, args: argparse.Namespace) -> None:
        self.playback_manager.next_block(args.book_id)
        print("Bloque siguiente.")

    def _cmd_prev(self, args: argparse.Namespace) -> None:
        self.playback_manager.prev_block(args.book_id)
        print("Bloque anterior.")

    def _cmd_rate(self, args: argparse.Namespace) -> None:
        self.playback_manager.set_rate(args.speed)
        print(f"Velocidad ajustada a {args.speed}")

    def _cmd_voice(self, args: argparse.Namespace) -> None:
        vcmd = args.voice_cmd
        if vcmd == "list":
            for v_id, v_name in self.playback_manager.tts.list_voices():
                print(f"[{v_id}] {v_name}")
        elif vcmd == "set":
            self.playback_manager.set_voice(args.voice_id)
            print(f"Voz ajustada a {args.voice_id}")

    def _cmd_status(self, args: argparse.Namespace) -> None:  # noqa: ARG002
        books = self.repo.list_books()
        if not books:
            print("No hay libros importados.")
            return
        for book in books:
            progress = self.repo.get_progress(book.id)
            if progress:
                print(
                    f"[{book.id[:8]}] {book.title}"
                    f" — cap {progress.chapter_idx}, blq {progress.block_idx}"
                )
            else:
                print(f"[{book.id[:8]}] {book.title} — sin progreso")
