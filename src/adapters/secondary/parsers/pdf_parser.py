"""PDF parser usando PyMuPDF (import fitz).

ADR: docs/adr/0001_pdf_text_parser.md
Estrategia: 1 capítulo por página con texto → progreso granular.
PDFs escaneados (sin texto) → DomainError explícito, sin OCR.
"""

from pathlib import Path

import fitz  # PyMuPDF

from src.domain.exceptions import DomainError
from src.domain.models import Chapter


class PdfParser:
    """Parsea PDFs con texto extrayendo una página por capítulo."""

    def parse_to_chapters(self, file_path: Path, book_id: str) -> list[tuple[Chapter, str]]:
        """Extrae capítulos de un PDF de texto página a página."""
        self._validate_path(file_path)
        try:
            return self._parse(file_path, book_id)
        except DomainError:
            raise
        except Exception as exc:
            raise DomainError(
                f"Error al parsear PDF '{file_path.name}': {exc}",
                {"file_path": str(file_path)},
            ) from exc

    # ------------------------------------------------------------------ #
    # Helpers privados                                                     #
    # ------------------------------------------------------------------ #

    def _validate_path(self, file_path: Path) -> None:
        if not file_path.exists():
            raise DomainError(
                f"El archivo {file_path} no existe.",
                {"file_path": str(file_path)},
            )

    def _parse(self, file_path: Path, book_id: str) -> list[tuple[Chapter, str]]:
        doc = fitz.open(str(file_path))
        try:
            return self._extract_chapters(doc, book_id, file_path)
        finally:
            doc.close()

    def _extract_chapters(
        self,
        doc: fitz.Document,
        book_id: str,
        file_path: Path,
    ) -> list[tuple[Chapter, str]]:
        chapters: list[tuple[Chapter, str]] = []
        for page_num in range(len(doc)):
            text = doc[page_num].get_text("text")
            if text.strip():
                chapter = Chapter(
                    book_id=book_id,
                    idx=len(chapters),
                    title=f"Página {page_num + 1}",
                )
                chapters.append((chapter, text))
        if not chapters:
            raise DomainError(
                "PDF sin texto extraíble (posible PDF escaneado o solo imágenes).",
                {"file_path": str(file_path)},
            )
        return chapters
