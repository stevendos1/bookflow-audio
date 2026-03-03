"""Composite BookParser: despacha al adaptador correcto según la extensión del archivo."""

from pathlib import Path

from src.application.ports import BookParser
from src.domain.exceptions import DomainError
from src.domain.models import Chapter


class MultiFormatParser:
    """Enruta el parseo al adaptador registrado para cada extensión de archivo."""

    def __init__(self, parsers: dict[str, BookParser]) -> None:
        self._parsers = parsers

    def parse_to_chapters(self, file_path: Path, book_id: str) -> list[tuple[Chapter, str]]:
        """Selecciona el parser por extensión y delega el parseo."""
        ext = file_path.suffix.lower()
        parser = self._parsers.get(ext)
        if parser is None:
            supported = ", ".join(sorted(self._parsers))
            raise DomainError(
                f"Formato '{ext}' no soportado. Formatos disponibles: {supported}",
                {"file_path": str(file_path), "extension": ext},
            )
        return parser.parse_to_chapters(file_path, book_id)
